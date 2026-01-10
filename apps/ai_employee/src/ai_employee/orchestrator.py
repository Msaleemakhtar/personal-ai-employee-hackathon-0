from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ai_employee.vault_io import safe_write_text

# Global state for graceful shutdown
_observer: Observer | None = None
_shutdown_requested = False
_active_subprocess: subprocess.Popen | None = None


def _repo_root() -> Path:
    # /home/salim/Desktop/hackathon0/apps/ai_employee/src/ai_employee/orchestrator.py
    # -> repo root is 5 levels up
    return Path(__file__).resolve().parents[4]


def _append_text(path: Path, text: str, *, vault_root: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    safe_write_text(path, existing + text, vault_root=vault_root)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RateLimiter:
    """Enforce email sending rate limits per Company_Handbook.md."""

    def __init__(self, hourly_limit: int = 10, daily_limit: int = 50):
        self.hourly_limit = hourly_limit
        self.daily_limit = daily_limit
        self.sends_log: list[datetime] = []  # List of send timestamps

    def can_send(self) -> tuple[bool, str]:
        """Check if sending is allowed. Returns (allowed, reason)."""
        from datetime import timedelta

        now = _utc_now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        # Prune old entries
        self.sends_log = [ts for ts in self.sends_log if ts > one_day_ago]

        # Count recent sends
        hourly_count = sum(1 for ts in self.sends_log if ts > one_hour_ago)
        daily_count = len(self.sends_log)

        if hourly_count >= self.hourly_limit:
            return False, f"Hourly limit reached ({self.hourly_limit}/hour)"

        if daily_count >= self.daily_limit:
            return False, f"Daily limit reached ({self.daily_limit}/day)"

        return True, ""

    def record_send(self) -> None:
        """Record a successful send."""
        self.sends_log.append(_utc_now())


class NeedsActionHandler(FileSystemEventHandler):
    # Memory management: prevent unbounded growth of _seen_files
    MAX_SEEN_FILES = 1000
    PRUNE_THRESHOLD = 800

    def __init__(self, *, vault_root: Path, mode: str = "queue"):
        self.vault_root = vault_root
        self.needs_action_dir = vault_root / "Needs_Action"
        self.logs_dir = vault_root / "Logs"
        self.mode = mode  # "queue" or "auto"
        # Debounce: track recently seen files to avoid retriggering on atomic saves/edits
        self._seen_files: OrderedDict[str, float] = OrderedDict()  # filename -> timestamp
        self._debounce_seconds = 10.0  # ignore same file within 10 seconds

    def _prune_seen_files(self) -> None:
        """Prune old entries from _seen_files to prevent unbounded memory growth."""
        if len(self._seen_files) < self.PRUNE_THRESHOLD:
            return
        num_to_remove = len(self._seen_files) - self.PRUNE_THRESHOLD
        for _ in range(num_to_remove):
            self._seen_files.popitem(last=False)

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.suffix.lower().endswith(".md"):
            return
        if path.name.startswith("."):
            return

        # Ignore common temp file patterns
        if any(path.name.endswith(suffix) for suffix in (".tmp", ".swp", ".part", "~")):
            return
        if path.name.startswith("#") or path.name.startswith("~"):
            return

        # Debounce: ignore if we've seen this file very recently
        now = _utc_now().timestamp()
        if path.name in self._seen_files and now - self._seen_files[path.name] < self._debounce_seconds:
            return  # Skip, too soon
        self._seen_files[path.name] = now
        self._prune_seen_files()  # Prevent memory leak

        if self.mode == "auto":
            # Trigger triage skill automatically (requires API key)
            self.trigger_triage(note_path=path)
        else:
            # Queue mode: just log the new item for manual processing
            self.log_new_item(note_path=path)

    def trigger_triage(self, *, note_path: Path) -> None:
        now = _utc_now()
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        repo_root = _repo_root()

        # Run from repo root so project skills in /home/salim/Desktop/hackathon0/.claude/skills can be discovered.
        # Add vault dir so tools can access it even when CWD is the repo root.
        # Keep prompt minimal and directive to reduce token usage
        cmd = [
            "claude",
            "--add-dir",
            str(self.vault_root),
            "-p",
            "/triage-needs-action",  # Use skill shorthand for minimal token overhead
        ]

        # We do not pass note_path directly yet; the skill should scan Needs_Action.
        # Keep prompt minimal and deterministic. Add a timeout so we don't hang under supervision.
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=180,
            )
            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()
            return_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or "").strip() if isinstance(e.stdout, str) else ""
            stderr = (e.stderr or "").strip() if isinstance(e.stderr, str) else ""
            return_code = 124
        except Exception as e:
            stdout = ""
            stderr = f"orchestrator exception: {e}"
            return_code = 1

        log_name = f"orchestrator-{now.strftime('%Y-%m-%d')}.log"
        log_path = self.logs_dir / log_name
        log_entry = "\n".join(
            [
                f"[{now.isoformat()}] triage-needs-action exit_code={return_code}",
                f"Triggered by: {note_path.name}",
                "--- stdout ---",
                stdout,
                "--- stderr ---",
                stderr,
                "",
            ]
        )
        _append_text(log_path, log_entry, vault_root=self.vault_root)

        # Heartbeat for dashboard consumption
        heartbeat = self.vault_root / "Logs" / "heartbeat-orchestrator.txt"
        safe_write_text(
            heartbeat,
            f"last_run_at={now.isoformat()}\nlast_exit_code={return_code}\n",
            vault_root=self.vault_root,
        )

    def log_new_item(self, *, note_path: Path) -> None:
        """Queue mode: log new items without auto-triaging."""
        now = _utc_now()
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        log_name = f"orchestrator-{now.strftime('%Y-%m-%d')}.log"
        log_path = self.logs_dir / log_name
        log_entry = f"[{now.isoformat()}] NEW ITEM (queue mode): {note_path.name}\n"
        _append_text(log_path, log_entry, vault_root=self.vault_root)

        # Update heartbeat
        heartbeat = self.vault_root / "Logs" / "heartbeat-orchestrator.txt"
        safe_write_text(
            heartbeat,
            f"last_run_at={now.isoformat()}\nmode=queue\nlast_item={note_path.name}\n",
            vault_root=self.vault_root,
        )


class ApprovedActionHandler(FileSystemEventHandler):
    """Watch Approved/ folder and execute MCP actions via Claude CLI."""

    # Memory management: prevent unbounded growth of _processed_files
    MAX_PROCESSED_FILES = 500
    PRUNE_THRESHOLD = 400

    def __init__(self, *, vault_root: Path):
        self.vault_root = vault_root
        self.approved_dir = vault_root / "Approved"
        self.done_dir = vault_root / "Done"
        self.needs_action_dir = vault_root / "Needs_Action"
        self.logs_dir = vault_root / "Logs"
        # Track processed files to avoid duplicates (with memory management)
        self._processed_files: OrderedDict[str, float] = OrderedDict()  # filename -> timestamp
        # Rate limiter for email sends
        self.rate_limiter = RateLimiter(hourly_limit=10, daily_limit=50)

    def _prune_processed_files(self) -> None:
        """Prune old entries from _processed_files to prevent unbounded memory growth."""
        if len(self._processed_files) < self.PRUNE_THRESHOLD:
            return
        num_to_remove = len(self._processed_files) - self.PRUNE_THRESHOLD
        for _ in range(num_to_remove):
            self._processed_files.popitem(last=False)

    def process_existing_files(self) -> None:
        """Process any files already in Approved/ on startup."""
        global _shutdown_requested
        print(f"[approved-handler] Scanning Approved/ for existing files...")

        for approval_file in self.approved_dir.glob("*.md"):
            if approval_file.name.startswith('.'):
                continue

            # Check shutdown flag
            if _shutdown_requested:
                print("[approved-handler] Shutdown requested, stopping file scan")
                return

            # Check if already processed
            if approval_file.name in self._processed_files:
                continue

            print(f"[approved-handler] Found existing approval: {approval_file.name}")

            # Process synchronously on startup
            try:
                content = approval_file.read_text(encoding="utf-8")
                metadata = self._parse_frontmatter(content)
                action = metadata.get("action")

                if action == "send_email":
                    now = _utc_now()
                    self._execute_email_send(approval_file, metadata, content, now)
                    # Mark as processed
                    self._processed_files[approval_file.name] = now.timestamp()

            except Exception as e:
                print(f"[approved-handler] Error processing existing file: {e}")

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.suffix.lower().endswith(".md"):
            return
        if path.name.startswith("."):
            return

        # Avoid reprocessing (check timestamp-based tracking)
        now = _utc_now().timestamp()
        if path.name in self._processed_files:
            return

        self._processed_files[path.name] = now
        self._prune_processed_files()  # Prevent memory leak
        self.execute_approved_action(path)

    def execute_approved_action(self, approval_file: Path) -> None:
        """Parse approval file and execute MCP action via Claude CLI."""
        global _shutdown_requested

        # Don't start new operations if shutdown requested
        if _shutdown_requested:
            print(f"[approved-handler] Shutdown requested, skipping {approval_file.name}")
            return

        now = _utc_now()

        try:
            content = approval_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[approved-handler] Error reading {approval_file.name}: {e}")
            return

        # Parse YAML frontmatter
        metadata = self._parse_frontmatter(content)
        if not metadata:
            print(f"[approved-handler] No frontmatter in {approval_file.name}, skipping")
            return

        action_type = metadata.get("action", "unknown")

        if action_type == "send_email":
            self._execute_email_send(approval_file, metadata, content, now)
        else:
            print(f"[approved-handler] Unknown action type '{action_type}' in {approval_file.name}")
            # Move to Done anyway to avoid reprocessing
            self._move_to_done(approval_file)

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        """Simple YAML frontmatter parser."""
        if not content.startswith("---"):
            return {}

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}

        frontmatter = parts[1].strip()
        metadata = {}
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        return metadata

    def _execute_email_send(
        self, approval_file: Path, metadata: dict, content: str, now: datetime
    ) -> None:
        """Execute email send via Claude CLI + Gmail MCP."""
        to_email = metadata.get("to", "")
        subject = metadata.get("subject", "")
        email_id = metadata.get("email_id", "null")

        if not to_email or not subject:
            print(f"[approved-handler] Missing to/subject in {approval_file.name}")
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="failed",
                error="Missing required fields (to/subject)",
            )
            self._move_to_done(approval_file)
            return

        # Extract email body from content (after frontmatter and before "## Reasoning")
        email_body = self._extract_email_body(content)

        # Check rate limits
        can_send, reason = self.rate_limiter.can_send()
        if not can_send:
            print(f"[approved-handler] Rate limit exceeded: {reason}")
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="rate_limited",
                error=reason,
            )
            # Keep file in Approved for later retry
            return

        print(f"[approved-handler] Sending email to {to_email}...")

        # Build explicit prompt that forces tool use and shows result
        if email_id and email_id != "null":
            # This is a reply - use gmail_reply_to_message tool
            prompt = f'''Call the mcp__gmail__gmail_reply_to_message tool NOW with these exact parameters:

message_id: "{email_id}"
body: """
{email_body}
"""
reply_all: false

After calling the tool, show me the message ID from the result to confirm it was sent.'''
        else:
            # New email - use gmail_send_message tool
            prompt = f'''Call the mcp__gmail__gmail_send_message tool NOW with these exact parameters:

to: ["{to_email}"]
subject: "{subject}"
body: """
{email_body}
"""

After calling the tool, show me the message ID from the result to confirm it was sent.'''

        repo_root = _repo_root()

        try:
            global _active_subprocess
            # Use Popen instead of run to track the subprocess globally
            import os
            proc = subprocess.Popen(
                [
                    "claude",
                    "--dangerously-skip-permissions",  # Safe since we only execute human-approved actions
                    "-p", prompt
                ],
                cwd=str(repo_root),
                stdin=subprocess.DEVNULL,  # Don't wait for stdin input
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy(),  # Pass current environment variables
            )
            _active_subprocess = proc

            # Wait for completion with timeout
            try:
                stdout, stderr = proc.communicate(timeout=300)
                result_returncode = proc.returncode
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    stdout, stderr = proc.communicate()
                raise  # Re-raise TimeoutExpired
            finally:
                _active_subprocess = None

            # Create a result object similar to subprocess.run
            class Result:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            result = Result(result_returncode, stdout, stderr)

            # Verify email was actually sent by checking output for success indicators
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            # DEBUG: Log full output to understand what Claude CLI returns
            print(f"[approved-handler] DEBUG - Return code: {result.returncode}")
            print(f"[approved-handler] DEBUG - STDOUT length: {len(stdout)} chars")
            if stdout:
                print(f"[approved-handler] DEBUG - STDOUT preview (first 500 chars):\n{stdout[:500]}")
            if stderr:
                print(f"[approved-handler] DEBUG - STDERR: {stderr[:500]}")

            # Check for Gmail MCP success indicators
            import re
            gmail_id_pattern = r'[0-9a-f]{16}'  # Gmail IDs are 16-char hex
            email_sent = (
                result.returncode == 0 and
                (re.search(gmail_id_pattern, stdout) or
                 "sent successfully" in stdout.lower() or
                 "message_id" in stdout.lower())
            )

            # Also check for error indicators even if returncode is 0
            has_error = (
                "error" in stdout.lower() or
                "failed" in stdout.lower() or
                "permission" in stdout.lower() or
                len(stderr) > 0
            )

            success = email_sent and not has_error

            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="success" if success else "failed",
                output=stdout,
                error=stderr if stderr else ("Email may not have been sent - no confirmation in output" if not success else None),
            )

            if success:
                print(f"[approved-handler] ✓ Email sent successfully to {to_email}")

                # Record successful send for rate limiting
                self.rate_limiter.record_send()

                # Update source item to mark as done
                source_file = metadata.get("source")
                if source_file:
                    self._update_source_item(source_file, "done", now)

            else:
                print(f"[approved-handler] ✗ Email send failed to {to_email}")
                if stdout:
                    print(f"[approved-handler] Output: {stdout[:200]}")
                if stderr:
                    print(f"[approved-handler] Error: {stderr[:200]}")

                # Mark for retry but keep in Approved/
                self._mark_for_retry(approval_file, "failed", now)
                return  # Don't move to Done

        except subprocess.TimeoutExpired:
            print("[approved-handler] Email send timed out")
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="timeout",
                error="Command timed out after 300 seconds",
            )
            # Mark for retry but keep in Approved/
            self._mark_for_retry(approval_file, "timeout", now)
            return  # Don't move to Done

        except Exception as e:
            print(f"[approved-handler] Error executing email send: {e}")
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="error",
                error=str(e),
            )
            # Mark for retry but keep in Approved/
            self._mark_for_retry(approval_file, "error", now)
            return  # Don't move to Done

        # Only move to Done on success
        self._move_to_done(approval_file)

    def _extract_email_body(self, content: str) -> str:
        """Extract email body from approval file content."""
        # Find "## Email Body" section
        lines = content.split("\n")
        in_body = False
        body_lines = []

        for line in lines:
            if line.strip() == "## Email Body":
                in_body = True
                continue
            if in_body:
                # Stop at next section (## Reasoning, ## Instructions, etc.)
                if line.strip().startswith("## "):
                    break
                body_lines.append(line)

        return "\n".join(body_lines).strip()

    def _log_action(
        self,
        *,
        now: datetime,
        action_type: str,
        target: str,
        approval_file: str,
        result: str,
        output: str | None = None,
        error: str | None = None,
    ) -> None:
        """Append action result to actions log (JSON)."""
        log_file = self.logs_dir / f"{now.strftime('%Y-%m-%d')}-actions.json"

        log_entry = {
            "timestamp": now.isoformat(),
            "action_type": action_type,
            "actor": "claude_code_mcp",
            "target": target,
            "approval_file": approval_file,
            "result": result,
        }

        if output:
            log_entry["output"] = output
        if error:
            log_entry["error"] = error

        # Read existing logs
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text(encoding="utf-8"))
            except Exception:
                logs = []

        logs.append(log_entry)

        # Write back
        safe_write_text(log_file, json.dumps(logs, indent=2), vault_root=self.vault_root)

    def _get_retry_count(self, approval_file: Path) -> int:
        """Get current retry count from approval file."""
        try:
            content = approval_file.read_text(encoding="utf-8")
            import re
            match = re.search(r'^retry_count:\s*(\d+)', content, re.MULTILINE)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 0

    def _mark_for_retry(self, approval_file: Path, error_type: str, timestamp: datetime) -> None:
        """Add retry metadata to failed approval file."""
        try:
            content = approval_file.read_text(encoding="utf-8")

            # Parse existing frontmatter
            lines = content.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == '---':
                    frontmatter_end = i
                    break

            if frontmatter_end > 0:
                # Remove any existing retry metadata
                import re
                lines = [l for l in lines if not re.match(r'^(retry_count|last_error|last_attempt):', l)]

                # Recalculate frontmatter_end after filtering
                frontmatter_end = -1
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() == '---':
                        frontmatter_end = i
                        break

                # Insert new retry metadata before closing ---
                retry_count = self._get_retry_count(approval_file) + 1
                retry_meta = [
                    f'retry_count: {retry_count}',
                    f'last_error: {error_type}',
                    f'last_attempt: {timestamp.isoformat()}'
                ]

                for meta in reversed(retry_meta):
                    lines.insert(frontmatter_end, meta)

                approval_file.write_text('\n'.join(lines), encoding="utf-8")
                print(f"[approved-handler] Marked {approval_file.name} for retry (attempt {retry_count})")

        except Exception as e:
            print(f"[approved-handler] Error marking retry: {e}")

    def _update_source_item(self, source_filename: str, new_status: str, timestamp: datetime) -> bool:
        """Update source item status after approval execution."""
        import re
        source_path = self.needs_action_dir / source_filename

        if not source_path.exists():
            print(f"[approved-handler] Warning: Source item not found: {source_filename}")
            return False

        try:
            content = source_path.read_text(encoding="utf-8")

            # Update status in frontmatter
            updated = re.sub(
                r'^status:\s+\w+',
                f'status: {new_status}',
                content,
                flags=re.MULTILINE
            )

            # Add completion timestamp (insert before closing ---)
            lines = updated.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == '---':
                    frontmatter_end = i
                    break

            if frontmatter_end > 0:
                lines.insert(frontmatter_end, f'completed_at: {timestamp.isoformat()}')
                updated = '\n'.join(lines)

            source_path.write_text(updated, encoding="utf-8")

            # Move to Done
            done_path = self.done_dir / source_filename
            source_path.rename(done_path)
            print(f"[approved-handler] Updated and moved source: {source_filename}")
            return True

        except Exception as e:
            print(f"[approved-handler] Error updating source: {e}")
            return False

    def _move_to_done(self, approval_file: Path) -> None:
        """Move approval file to Done/."""
        try:
            done_path = self.done_dir / approval_file.name
            approval_file.rename(done_path)
            print(f"[approved-handler] Moved {approval_file.name} to Done/")
        except Exception as e:
            print(f"[approved-handler] Error moving {approval_file.name} to Done: {e}")


class RejectedActionHandler(FileSystemEventHandler):
    """Handles human rejection of approval requests."""

    def __init__(self, *, vault_root: Path):
        self.vault_root = vault_root
        self.rejected_dir = vault_root / "Rejected"
        self.needs_action_dir = vault_root / "Needs_Action"
        self.done_dir = vault_root / "Done"
        self.logs_dir = vault_root / "Logs"
        self._processed_files: dict[str, float] = {}

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.suffix.lower().endswith(".md"):
            return
        if path.name.startswith("."):
            return

        # Avoid reprocessing
        if path.name in self._processed_files:
            return

        print(f"[rejected-handler] Processing rejection: {path.name}")
        self._process_rejection(path)

    def _process_rejection(self, approval_file: Path) -> None:
        """Process rejected approval request."""
        now = _utc_now()

        try:
            content = approval_file.read_text(encoding="utf-8")
            metadata = self._parse_frontmatter(content)

            source_file = metadata.get("source")

            # Update source item: status → rejected
            if source_file:
                source_path = self.needs_action_dir / source_file
                if source_path.exists():
                    self._update_source_status(source_path, "rejected", now)

            # Log rejection
            self._log_rejection(approval_file.name, metadata, now)

            # Move rejection file to Done (archives it)
            done_path = self.done_dir / approval_file.name
            approval_file.rename(done_path)

            self._processed_files[approval_file.name] = now.timestamp()
            print(f"[rejected-handler] Rejection processed: {approval_file.name}")

        except Exception as e:
            print(f"[rejected-handler] Error processing rejection: {e}")

    def _parse_frontmatter(self, content: str) -> dict[str, str]:
        """Simple YAML frontmatter parser."""
        if not content.startswith("---"):
            return {}

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}

        frontmatter = parts[1].strip()
        metadata = {}
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        return metadata

    def _update_source_status(self, source_path: Path, new_status: str, timestamp: datetime) -> None:
        """Update source item status to rejected."""
        try:
            import re
            content = source_path.read_text(encoding="utf-8")

            # Update status in frontmatter
            updated = re.sub(
                r'^status:\s+\w+',
                f'status: {new_status}',
                content,
                flags=re.MULTILINE
            )

            # Add rejection timestamp
            lines = updated.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == '---':
                    frontmatter_end = i
                    break

            if frontmatter_end > 0:
                lines.insert(frontmatter_end, f'rejected_at: {timestamp.isoformat()}')
                updated = '\n'.join(lines)

            source_path.write_text(updated, encoding="utf-8")
            print(f"[rejected-handler] Updated source status: {source_path.name}")

        except Exception as e:
            print(f"[rejected-handler] Error updating source status: {e}")

    def _log_rejection(self, filename: str, metadata: dict, timestamp: datetime) -> None:
        """Log rejection to actions.json."""
        log_file = self.logs_dir / f"{timestamp.date()}-actions.json"

        entry = {
            "timestamp": timestamp.isoformat(),
            "action_type": "rejection",
            "actor": "human",
            "approval_file": filename,
            "source": metadata.get("source"),
            "result": "rejected"
        }

        # Append to log
        try:
            import json
            existing = json.loads(log_file.read_text()) if log_file.exists() else []
            existing.append(entry)
            safe_write_text(log_file, json.dumps(existing, indent=2), vault_root=self.vault_root)
        except Exception as e:
            print(f"[rejected-handler] Error logging rejection: {e}")


def _signal_handler(signum: int, _frame) -> None:
    """Handle shutdown signals gracefully."""
    global _observer, _shutdown_requested, _active_subprocess
    print(f"\n[orchestrator] Received signal {signum}, initiating graceful shutdown...")
    _shutdown_requested = True

    # Stop observer from accepting new events
    if _observer is not None:
        print("[orchestrator] Stopping file watcher...")
        _observer.stop()

    # Wait for active subprocess to complete (with timeout)
    if _active_subprocess is not None and _active_subprocess.poll() is None:
        print("[orchestrator] Waiting for ongoing operation to complete (max 60s)...")
        try:
            _active_subprocess.wait(timeout=60)
            print("[orchestrator] Operation completed.")
        except subprocess.TimeoutExpired:
            print("[orchestrator] Operation timed out, terminating...")
            _active_subprocess.terminate()
            try:
                _active_subprocess.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _active_subprocess.kill()


def _parse_frontmatter_static(content: str) -> dict[str, str]:
    """Static helper to parse frontmatter (used by expiration checker)."""
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter = parts[1].strip()
    metadata = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def check_expired_approvals(vault_root: Path) -> None:
    """Check Pending_Approval for expired items and auto-reject."""
    pending_dir = vault_root / "Pending_Approval"
    rejected_dir = vault_root / "Rejected"
    now = _utc_now()

    try:
        for approval_file in pending_dir.glob("*.md"):
            try:
                content = approval_file.read_text(encoding="utf-8")
                metadata = _parse_frontmatter_static(content)

                expires_at_str = metadata.get("expires_at")
                if not expires_at_str:
                    continue

                # Parse expiration time
                expires_at_str = expires_at_str.replace('Z', '+00:00')
                expires_at = datetime.fromisoformat(expires_at_str)

                if now > expires_at:
                    print(f"[orchestrator] Expired approval: {approval_file.name}")

                    # Update status to expired
                    import re
                    content = re.sub(
                        r'^status:\s+\w+',
                        f'status: expired',
                        content,
                        flags=re.MULTILINE
                    )

                    # Add expiration timestamp
                    lines = content.split('\n')
                    frontmatter_end = -1
                    for i, line in enumerate(lines):
                        if i > 0 and line.strip() == '---':
                            frontmatter_end = i
                            break

                    if frontmatter_end > 0:
                        lines.insert(frontmatter_end, f'expired_at: {now.isoformat()}')
                        content = '\n'.join(lines)

                    approval_file.write_text(content, encoding="utf-8")

                    # Move to Rejected
                    rejected_path = rejected_dir / approval_file.name
                    approval_file.rename(rejected_path)

                    print(f"[orchestrator] Moved expired to Rejected: {approval_file.name}")

            except Exception as e:
                print(f"[orchestrator] Error checking expiration for {approval_file.name}: {e}")

    except Exception as e:
        print(f"[orchestrator] Error in expiration check: {e}")


def run_orchestrator(*, vault_path: str, mode: str = "queue") -> None:
    global _observer
    vault_root = Path(vault_path)
    needs_action_dir = vault_root / "Needs_Action"
    approved_dir = vault_root / "Approved"
    rejected_dir = vault_root / "Rejected"
    needs_action_dir.mkdir(parents=True, exist_ok=True)
    approved_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print(f"[orchestrator] Starting in {mode.upper()} mode")
    print(f"[orchestrator] Watching Needs_Action: {needs_action_dir}")
    print(f"[orchestrator] Watching Approved: {approved_dir}")
    if mode == "queue":
        print("[orchestrator] Queue mode: new items will be logged, triage via manual script")
    else:
        print("[orchestrator] Auto mode: new items will be auto-triaged")

    # Handler for Needs_Action folder
    needs_action_handler = NeedsActionHandler(vault_root=vault_root, mode=mode)

    # Handler for Approved folder (Silver tier)
    approved_handler = ApprovedActionHandler(vault_root=vault_root)

    # Process any existing files before starting observer
    approved_handler.process_existing_files()

    # Handler for Rejected folder (Silver tier)
    rejected_handler = RejectedActionHandler(vault_root=vault_root)

    _observer = Observer()
    _observer.schedule(needs_action_handler, str(needs_action_dir), recursive=False)
    _observer.schedule(approved_handler, str(approved_dir), recursive=False)
    _observer.schedule(rejected_handler, str(rejected_dir), recursive=False)

    # Start expiration check thread (runs every 10 minutes)
    import threading
    import time

    def expiration_check_loop():
        """Background thread to check for expired approvals."""
        while True:
            try:
                check_expired_approvals(vault_root)
            except Exception as e:
                print(f"[orchestrator] Error in expiration check loop: {e}")
            time.sleep(600)  # 10 minutes

    expiry_thread = threading.Thread(target=expiration_check_loop, daemon=True, name="expiration-checker")
    expiry_thread.start()
    print("[orchestrator] Expiration checker started (10-minute interval)")

    _observer.start()
    try:
        # Wait for observer, but check shutdown flag periodically
        while _observer.is_alive() and not _shutdown_requested:
            _observer.join(timeout=1.0)

        if _shutdown_requested:
            print("[orchestrator] Shutdown requested, stopping...")
    except KeyboardInterrupt:
        print("\n[orchestrator] Interrupted, shutting down...")
    finally:
        if _observer.is_alive():
            _observer.stop()
        _observer.join()
        print("[orchestrator] Stopped.")


if __name__ == "__main__":
    vault = os.environ.get("VAULT_PATH")
    if not vault:
        raise SystemExit("VAULT_PATH env var is required")

    mode = os.environ.get("ORCHESTRATOR_MODE", "queue").lower()
    if mode not in ("queue", "auto"):
        print(f"Warning: Invalid ORCHESTRATOR_MODE '{mode}', defaulting to 'queue'")
        mode = "queue"

    run_orchestrator(vault_path=vault, mode=mode)
