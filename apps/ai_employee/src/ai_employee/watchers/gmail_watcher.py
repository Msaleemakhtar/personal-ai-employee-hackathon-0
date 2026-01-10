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

    # Memory management: limit processed IDs in memory
    MAX_PROCESSED_IDS = 10000  # Keep last 10K processed emails
    PRUNE_THRESHOLD = 8000  # Prune when we reach 8K

    # Credentials retry configuration
    MAX_CREDENTIAL_ERRORS = 5  # Max consecutive credential errors before alerting
    CREDENTIAL_ERROR_COOLDOWN = 3600  # 1 hour cooldown after credential errors

    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_root = Path(vault_path)
        self.needs_action_dir = self.vault_root / "Needs_Action"
        self.logs_dir = self.vault_root / "Logs"
        self.check_interval = check_interval
        self.processed_ids_file = self.logs_dir / ".gmail_processed_ids.json"

        # Load persisted processed IDs (with age tracking for cleanup)
        self.processed_ids = self._load_processed_ids()

        # Exponential backoff state
        self.error_count = 0
        self.backoff_seconds = 0
        self.credential_error_count = 0
        self.last_credential_error = 0

        # Load credentials from ~/.gmail-mcp/credentials.json
        creds_path = Path.home() / ".gmail-mcp" / "credentials.json"
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Gmail credentials not found at {creds_path}. "
                "Run: cd apps/gmail-mcp-server && uv run gmail-mcp --auth"
            )

        self.creds = Credentials.from_authorized_user_file(str(creds_path))
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _load_processed_ids(self) -> dict[str, float]:
        """Load processed email IDs from persistent storage with timestamps."""
        if not self.processed_ids_file.exists():
            return {}
        try:
            with open(self.processed_ids_file, encoding='utf-8') as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict)
                if isinstance(data.get('processed_ids'), list):
                    # Migrate from old format: convert list to dict with current timestamp
                    now = _utc_now().timestamp()
                    return {email_id: now for email_id in data['processed_ids']}
                return data.get('processed_ids', {})
        except Exception as e:
            print(f"[gmail-watcher] Error loading processed IDs: {e}")
            return {}

    def _save_processed_ids(self) -> None:
        """Persist processed email IDs to survive restarts."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        try:
            # Prune old IDs before saving (keep IDs from last 30 days)
            self._prune_old_processed_ids()

            data = {
                'processed_ids': self.processed_ids,
                'last_updated': _utc_now().isoformat(),
                'count': len(self.processed_ids)
            }
            with open(self.processed_ids_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[gmail-watcher] Error saving processed IDs: {e}")

    def _prune_old_processed_ids(self) -> None:
        """Remove old processed IDs to prevent unbounded growth."""
        if len(self.processed_ids) < self.PRUNE_THRESHOLD:
            return

        now = _utc_now().timestamp()
        thirty_days_ago = now - (30 * 24 * 3600)

        # Remove IDs older than 30 days
        old_ids = [email_id for email_id, timestamp in self.processed_ids.items()
                   if timestamp < thirty_days_ago]

        for email_id in old_ids:
            del self.processed_ids[email_id]

        if old_ids:
            print(f"[gmail-watcher] Pruned {len(old_ids)} processed IDs older than 30 days")

        # If still over threshold, keep only the most recent MAX_PROCESSED_IDS
        if len(self.processed_ids) > self.MAX_PROCESSED_IDS:
            # Sort by timestamp (descending) and keep newest
            sorted_ids = sorted(self.processed_ids.items(), key=lambda x: x[1], reverse=True)
            self.processed_ids = dict(sorted_ids[:self.MAX_PROCESSED_IDS])
            print(f"[gmail-watcher] Pruned to {self.MAX_PROCESSED_IDS} most recent IDs")

    def check_for_updates(self) -> list:
        """Query for unread important emails only"""
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
            # Track with timestamp for memory management
            self.processed_ids[message['id']] = _utc_now().timestamp()
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
        print("[gmail-watcher] Query: is:unread in:inbox")
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
                error_str = str(e)
                print(f"[gmail-watcher] Error: {e}")

                # Special handling for credential errors - don't spam retries
                if 'deleted_client' in error_str or 'invalid_grant' in error_str or 'invalid_client' in error_str:
                    self.credential_error_count += 1
                    self.last_credential_error = time.time()

                    if self.credential_error_count >= self.MAX_CREDENTIAL_ERRORS:
                        print(f"[gmail-watcher] CRITICAL: {self.credential_error_count} consecutive credential errors.")
                        print("[gmail-watcher] Credentials may be invalid or OAuth client deleted.")
                        print("[gmail-watcher] Entering long cooldown mode (1 hour between retries)")
                        self.backoff_seconds = self.CREDENTIAL_ERROR_COOLDOWN
                    else:
                        # Gradual backoff for credential errors
                        self.backoff_seconds = min(
                            self.INITIAL_BACKOFF * (2 ** self.credential_error_count),
                            self.CREDENTIAL_ERROR_COOLDOWN
                        )
                else:
                    # Regular errors - standard exponential backoff
                    self.credential_error_count = 0  # Reset credential error counter
                    self.error_count += 1
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
