#!/usr/bin/env bash
# Archive old items from Done/ folder and clean up processed Inbox files
# This script runs automatically via cron daily at midnight
#
# Usage:
#   ./ops/scripts/archive_old.sh
#
# Cron example (daily at midnight):
#   0 0 * * * /home/salim/Desktop/hackathon0/ops/scripts/archive_old.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULT="$REPO_ROOT/AI_EMPLOYEE_VAULT"
ARCHIVE_BASE="$VAULT/Archive"
LOG_FILE="$VAULT/Logs/archive.log"

# Retention periods (in days)
DONE_RETENTION_DAYS=7      # Move Done items to Archive after 7 days
INBOX_CLEANUP_DAYS=1       # Delete processed Inbox files after 1 day

# Navigate to repo root
cd "$REPO_ROOT"

# Ensure directories exist
mkdir -p "$ARCHIVE_BASE"
mkdir -p "$VAULT/Logs"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
    echo "[$(date -Iseconds)] $1"
}

log "=========================================="
log "Starting archive process..."

# Create archive folder for current month
ARCHIVE_DIR="$ARCHIVE_BASE/$(date +%Y-%m)"
mkdir -p "$ARCHIVE_DIR"
log "Archive folder: $ARCHIVE_DIR"

# Step 1: Archive old Done/ items (older than 7 days)
log "Step 1: Archiving Done/ items older than $DONE_RETENTION_DAYS days..."
ARCHIVED_COUNT=0

if [ -d "$VAULT/Done" ]; then
    while IFS= read -r -d '' file; do
        filename=$(basename "$file")
        mv "$file" "$ARCHIVE_DIR/$filename"
        log "  Archived: $filename"
        ((ARCHIVED_COUNT++)) || true
    done < <(find "$VAULT/Done" -name "*.md" -type f -mtime +$DONE_RETENTION_DAYS -print0 2>/dev/null)
fi

log "Archived $ARCHIVED_COUNT items from Done/"

# Step 2: Clean up old Inbox files (older than 1 day)
# Only delete files that have a corresponding Needs_Action or Done item
log "Step 2: Cleaning up Inbox files older than $INBOX_CLEANUP_DAYS day..."
CLEANED_COUNT=0

if [ -d "$VAULT/Inbox" ]; then
    while IFS= read -r -d '' file; do
        filename=$(basename "$file")
        # Check if there's a corresponding processed item
        if find "$VAULT/Needs_Action" "$VAULT/Done" "$ARCHIVE_DIR" -name "*${filename}*" -type f 2>/dev/null | grep -q .; then
            rm "$file"
            log "  Cleaned: $filename (processed)"
            ((CLEANED_COUNT++)) || true
        else
            log "  Kept: $filename (no processed item found)"
        fi
    done < <(find "$VAULT/Inbox" -type f -mtime +$INBOX_CLEANUP_DAYS -print0 2>/dev/null)
fi

log "Cleaned $CLEANED_COUNT files from Inbox/"

# Step 3: Report final state
INBOX_COUNT=$(find "$VAULT/Inbox" -type f 2>/dev/null | wc -l)
NEEDS_ACTION_COUNT=$(find "$VAULT/Needs_Action" -name "*.md" -type f 2>/dev/null | wc -l)
DONE_COUNT=$(find "$VAULT/Done" -name "*.md" -type f 2>/dev/null | wc -l)
ARCHIVE_COUNT=$(find "$ARCHIVE_DIR" -name "*.md" -type f 2>/dev/null | wc -l)

log "Final state:"
log "  Inbox: $INBOX_COUNT files"
log "  Needs_Action: $NEEDS_ACTION_COUNT items"
log "  Done: $DONE_COUNT items"
log "  Archive ($(date +%Y-%m)): $ARCHIVE_COUNT items"
log "Archive complete!"
log "=========================================="
