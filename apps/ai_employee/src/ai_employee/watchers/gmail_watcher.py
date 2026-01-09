from __future__ import annotations

import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ai_employee.vault_io import safe_write_text


# Global observer for signal handling
_service = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _signal_handler(signum: int, frame) -> None:
    """Handle shutdown signals gracefully."""
    print(f"\n[gmail-watcher] Received signal {signum}, shutting down...")
    sys.exit(0)


class GmailWatcher:
    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_root = Path(vault_path)
        self.needs_action_dir = self.vault_root / "Needs_Action"
        self.check_interval = check_interval
        self.processed_ids = set()

        # Load credentials from ~/.gmail-mcp/credentials.json
        creds_path = Path.home() / ".gmail-mcp" / "credentials.json"
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Gmail credentials not found at {creds_path}. "
                "Run: npx @gongrzhe/server-gmail-autoauth-mcp auth"
            )

        self.creds = Credentials.from_authorized_user_file(str(creds_path))
        self.service = build('gmail', 'v1', credentials=self.creds)

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
            print(f"[gmail-watcher] Created: {filepath.name}")
            return filepath
        except Exception as e:
            print(f"[gmail-watcher] Error creating action file: {e}")
            return None

    def run(self):
        """Main loop"""
        import time

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        print(f"[gmail-watcher] Starting...")
        print(f"[gmail-watcher] Checking every {self.check_interval} seconds")
        print(f"[gmail-watcher] Query: is:unread is:important")

        while True:
            try:
                messages = self.check_for_updates()
                if messages:
                    print(f"[gmail-watcher] Found {len(messages)} new email(s)")
                    for msg in messages:
                        self.create_action_file(msg)
                else:
                    # Only print occasionally to reduce log noise
                    pass
            except KeyboardInterrupt:
                print("\n[gmail-watcher] Interrupted, shutting down...")
                break
            except Exception as e:
                print(f"[gmail-watcher] Unexpected error: {e}")

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
