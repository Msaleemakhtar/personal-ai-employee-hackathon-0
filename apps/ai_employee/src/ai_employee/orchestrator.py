from __future__ import annotations

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

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if not path.suffix.lower().endswith(".md"):
            return
        if path.name.startswith("."):
            return

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
    needs_action_dir.mkdir(parents=True, exist_ok=True)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print(f"[orchestrator] Starting in {mode.upper()} mode")
    print(f"[orchestrator] Watching: {needs_action_dir}")
    if mode == "queue":
        print("[orchestrator] Queue mode: new items will be logged, triage via manual script")
    else:
        print("[orchestrator] Auto mode: new items will be auto-triaged")

    handler = NeedsActionHandler(vault_root=vault_root, mode=mode)
    _observer = Observer()
    _observer.schedule(handler, str(needs_action_dir), recursive=False)

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
