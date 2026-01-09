from __future__ import annotations

import os
import re
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from ai_employee.vault_io import safe_write_text

# Global observer for signal handling
_observer: Observer | None = None


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _safe_slug(name: str) -> str:
    base = name.strip()
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"[^A-Za-z0-9_.-]", "", base)
    return base[:80] or "item"


def render_needs_action_note(*, source_path: Path) -> str:
    now = _utc_now()
    size = source_path.stat().st_size
    original_name = source_path.name

    # Minimal frontmatter contract for Bronze
    frontmatter = "\n".join(
        [
            "---",
            "type: file_drop",
            f"created_at: {now.isoformat()}",
            "status: pending",
            "priority: normal",
            "source: inbox",
            f"source_path: {source_path}",
            f"original_name: {original_name}",
            f"size_bytes: {size}",
            "---",
        ]
    )

    body = "\n".join(
        [
            "",
            "# File dropped for processing",
            "",
            f"**Original file:** `{original_name}`",
            f"**Size:** {size} bytes",
            f"**Detected:** {now.isoformat()}",
            "",
            "## Requested outcome",
            "Describe what you want the AI Employee to do with this file.",
            "",
            "## Suggested next steps",
            "- [ ] Triage and summarize the file",
            "- [ ] Propose action items",
            "- [ ] Update Dashboard",
            "",
        ]
    )

    return frontmatter + body


class InboxHandler(FileSystemEventHandler):
    def __init__(self, *, vault_root: Path, inbox_dir: Path, needs_action_dir: Path):
        self.vault_root = vault_root
        self.inbox_dir = inbox_dir
        self.needs_action_dir = needs_action_dir

    def on_created(self, event):
        if event.is_directory:
            return

        src = Path(event.src_path)
        # Ignore hidden files and temp files
        if src.name.startswith("."):
            return

        # Only react to files created under inbox
        try:
            src.relative_to(self.inbox_dir)
        except ValueError:
            return

        now = _utc_now()
        slug = _safe_slug(src.name)
        out_name = f"FILE_{now.strftime('%Y-%m-%d_%H%M%S')}_{slug}.md"
        out_path = self.needs_action_dir / out_name

        content = render_needs_action_note(source_path=src)
        safe_write_text(out_path, content, vault_root=self.vault_root)


def _signal_handler(signum: int, _frame) -> None:
    """Handle shutdown signals gracefully."""
    global _observer
    print(f"\n[filesystem-watcher] Received signal {signum}, shutting down...")
    if _observer is not None:
        _observer.stop()
    sys.exit(0)


def run_filesystem_watcher(*, vault_path: str) -> None:
    global _observer
    vault_root = Path(vault_path)
    inbox_dir = vault_root / "Inbox"
    needs_action_dir = vault_root / "Needs_Action"

    inbox_dir.mkdir(parents=True, exist_ok=True)
    needs_action_dir.mkdir(parents=True, exist_ok=True)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    print("[filesystem-watcher] Starting...")
    print(f"[filesystem-watcher] Watching: {inbox_dir}")

    handler = InboxHandler(vault_root=vault_root, inbox_dir=inbox_dir, needs_action_dir=needs_action_dir)
    _observer = Observer()
    _observer.schedule(handler, str(inbox_dir), recursive=False)

    _observer.start()
    try:
        _observer.join()
    except KeyboardInterrupt:
        print("\n[filesystem-watcher] Interrupted, shutting down...")
    finally:
        _observer.stop()
        _observer.join()
        print("[filesystem-watcher] Stopped.")


if __name__ == "__main__":
    vault = os.environ.get("VAULT_PATH")
    if not vault:
        raise SystemExit("VAULT_PATH env var is required")
    run_filesystem_watcher(vault_path=vault)
