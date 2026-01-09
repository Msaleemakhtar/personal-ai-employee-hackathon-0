from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ai_employee.vault_io import safe_write_text


# Global observer for signal handling
_observer: Observer | None = None


def _repo_root() -> Path:
    # /home/salim/Desktop/hackathon0/apps/ai_employee/src/ai_employee/orchestrator.py
    # -> repo root is 5 levels up
    return Path(__file__).resolve().parents[4]


def _append_text(path: Path, text: str, *, vault_root: Path) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    safe_write_text(path, existing + text, vault_root=vault_root)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NeedsActionHandler(FileSystemEventHandler):
    def __init__(self, *, vault_root: Path, mode: str = "queue"):
        self.vault_root = vault_root
        self.needs_action_dir = vault_root / "Needs_Action"
        self.logs_dir = vault_root / "Logs"
        self.mode = mode  # "queue" or "auto"
        # Debounce: track recently seen files to avoid retriggering on atomic saves/edits
        self._seen_files: dict[str, float] = {}  # filename -> timestamp
        self._debounce_seconds = 10.0  # ignore same file within 10 seconds

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
        if path.name in self._seen_files:
            if now - self._seen_files[path.name] < self._debounce_seconds:
                return  # Skip, too soon
        self._seen_files[path.name] = now

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
        cmd = [
            "claude",
            "--add-dir",
            str(self.vault_root),
            "-p",
            "Use the triage-needs-action Agent Skill to triage the vault queue. Only read/write inside the Obsidian vault. Update Dashboard.md and append a brief entry to Logs/decisions-YYYY-MM-DD.md. Follow Company_Handbook.md rules.",
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

    def __init__(self, *, vault_root: Path):
        self.vault_root = vault_root
        self.approved_dir = vault_root / "Approved"
        self.done_dir = vault_root / "Done"
        self.logs_dir = vault_root / "Logs"
        # Track processed files to avoid duplicates
        self._processed_files: set[str] = set()

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

        self._processed_files.add(path.name)
        self.execute_approved_action(path)

    def execute_approved_action(self, approval_file: Path) -> None:
        """Parse approval file and execute MCP action via Claude CLI."""
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

        print(f"[approved-handler] Sending email to {to_email}...")

        # Build Claude CLI prompt to use Gmail MCP
        if email_id and email_id != "null":
            # This is a reply
            prompt = f'Use the gmail MCP server to reply to email ID "{email_id}" with the following content:\n\nTo: {to_email}\nSubject: {subject}\n\n{email_body}'
        else:
            # New email
            prompt = f'Use the gmail MCP server to send a new email:\n\nTo: {to_email}\nSubject: {subject}\n\n{email_body}'

        repo_root = _repo_root()

        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=60,
            )

            success = result.returncode == 0
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="success" if success else "failed",
                output=result.stdout,
                error=result.stderr if not success else None,
            )

            if success:
                print(f"[approved-handler] Email sent successfully to {to_email}")
            else:
                print(f"[approved-handler] Email send failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"[approved-handler] Email send timed out")
            self._log_action(
                now=now,
                action_type="email_send",
                target=to_email,
                approval_file=approval_file.name,
                result="timeout",
                error="Command timed out after 60 seconds",
            )
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

        # Move to Done regardless of outcome
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

    def _move_to_done(self, approval_file: Path) -> None:
        """Move approval file to Done/."""
        try:
            done_path = self.done_dir / approval_file.name
            approval_file.rename(done_path)
            print(f"[approved-handler] Moved {approval_file.name} to Done/")
        except Exception as e:
            print(f"[approved-handler] Error moving {approval_file.name} to Done: {e}")


def _signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    global _observer
    print(f"\n[orchestrator] Received signal {signum}, shutting down...")
    if _observer is not None:
        _observer.stop()
    sys.exit(0)


def run_orchestrator(*, vault_path: str, mode: str = "queue") -> None:
    global _observer
    vault_root = Path(vault_path)
    needs_action_dir = vault_root / "Needs_Action"
    approved_dir = vault_root / "Approved"
    needs_action_dir.mkdir(parents=True, exist_ok=True)
    approved_dir.mkdir(parents=True, exist_ok=True)

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

    _observer = Observer()
    _observer.schedule(needs_action_handler, str(needs_action_dir), recursive=False)
    _observer.schedule(approved_handler, str(approved_dir), recursive=False)

    _observer.start()
    try:
        _observer.join()
    except KeyboardInterrupt:
        print("\n[orchestrator] Interrupted, shutting down...")
    finally:
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
