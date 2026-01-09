from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ai_employee.vault_io import safe_write_text

# Global observer for signal handling
_service = None


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _signal_handler(signum: int, _frame) -> None:
    """Handle shutdown signals gracefully."""
    print(f"\n[gmail-watcher] Received signal {signum}, shutting down...")
    sys.exit(0)


class GmailWatcher:
    # Exponential backoff configuration
    INITIAL_BACKOFF = 30  # seconds
    MAX_BACKOFF = 3600  # 1 hour

    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_root = Path(vault_path)
        self.needs_action_dir = self.vault_root / "Needs_Action"
        self.logs_dir = self.vault_root / "Logs"
        self.check_interval = check_interval
        self.processed_ids_file = self.logs_dir / ".gmail_processed_ids.json"

        # Load persisted processed IDs
        self.processed_ids = self._load_processed_ids()

        # Exponential backoff state
        self.error_count = 0
        self.backoff_seconds = 0

        # Load credentials from ~/.gmail-mcp/credentials.json
        creds_path = Path.home() / ".gmail-mcp" / "credentials.json"
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Gmail credentials not found at {creds_path}. "
                "Run: npx @gongrzhe/server-gmail-autoauth-mcp auth"
            )

        self.creds = Credentials.from_authorized_user_file(str(creds_path))
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _load_processed_ids(self) -> set:
        """Load processed email IDs from persistent storage."""
        if not self.processed_ids_file.exists():
            return set()
        try:
            with open(self.processed_ids_file, encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_ids', []))
        except Exception as e:
            print(f"[gmail-watcher] Error loading processed IDs: {e}")
            return set()

    def _save_processed_ids(self) -> None:
        """Persist processed email IDs to survive restarts."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                'processed_ids': list(self.processed_ids),
                'last_updated': _utc_now().isoformat()
            }
            with open(self.processed_ids_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[gmail-watcher] Error saving processed IDs: {e}")

    def check_for_updates(self) -> list:
        """Query for unread important emails"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important'
            ).execute()
            messages = results.get('messages', [])
            return [m for m in messages if m['id'] not in self.processed_ids]
        except Exception as e:
            print(f"[gmail-watcher] Error checking emails: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """Create EMAIL_*.md in Needs_Action/"""
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id']
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            content = f'''---
type: email
email_id: {message['id']}
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {_utc_now().isoformat()}
priority: high
status: pending
---

# Email from Gmail

**From**: {headers.get('From', 'Unknown')}
**Subject**: {headers.get('Subject', 'No Subject')}
**Date**: {headers.get('Date', 'Unknown')}

## Email Content
{msg.get('snippet', '(No preview available)')}

## Suggested Actions
- [ ] Read full email
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''
            filepath = self.needs_action_dir / f'EMAIL_{message["id"]}.md'
            safe_write_text(filepath, content, vault_root=self.vault_root)
            self.processed_ids.add(message['id'])
            self._save_processed_ids()  # Persist to survive restarts
            print(f"[gmail-watcher] Created: {filepath.name}")
            return filepath
        except Exception as e:
            print(f"[gmail-watcher] Error creating action file: {e}")
            return None

    def run(self):
        """Main loop with exponential backoff on errors"""
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        print("[gmail-watcher] Starting...")
        print(f"[gmail-watcher] Checking every {self.check_interval} seconds")
        print("[gmail-watcher] Query: is:unread is:important")
        print(f"[gmail-watcher] Loaded {len(self.processed_ids)} processed IDs from storage")

        while True:
            try:
                # Apply exponential backoff if we've had recent errors
                if self.backoff_seconds > 0:
                    print(f"[gmail-watcher] Backing off for {self.backoff_seconds}s due to errors")
                    time.sleep(self.backoff_seconds)
                    self.backoff_seconds = 0

                messages = self.check_for_updates()
                if messages:
                    print(f"[gmail-watcher] Found {len(messages)} new email(s)")
                    for msg in messages:
                        self.create_action_file(msg)
                    # Reset error count on successful processing
                    self.error_count = 0
                else:
                    # Only print occasionally to reduce log noise
                    self.error_count = 0  # Reset on successful check (even if empty)
            except KeyboardInterrupt:
                print("\n[gmail-watcher] Interrupted, shutting down...")
                break
            except Exception as e:
                print(f"[gmail-watcher] Error: {e}")
                self.error_count += 1
                # Calculate exponential backoff: 30s, 60s, 120s, ..., max 1 hour
                self.backoff_seconds = min(
                    self.INITIAL_BACKOFF * (2 ** (self.error_count - 1)),
                    self.MAX_BACKOFF
                )
                print(f"[gmail-watcher] Will retry after {self.backoff_seconds}s (error #{self.error_count})")

            time.sleep(self.check_interval)

        print("[gmail-watcher] Stopped.")


def run_gmail_watcher(*, vault_path: str) -> None:
    watcher = GmailWatcher(vault_path)
    watcher.run()


if __name__ == "__main__":
    vault = os.environ.get("VAULT_PATH")
    if not vault:
        raise SystemExit("VAULT_PATH env var is required")
    run_gmail_watcher(vault_path=vault)
