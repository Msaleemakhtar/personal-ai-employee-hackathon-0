#!/usr/bin/env bash
# Full pipeline: Triage new items + Execute pending tasks
# This script runs automatically via cron every 30 minutes
#
# Usage:
#   ./ops/scripts/process_queue.sh
#
# Cron example (every 30 minutes):
#   */30 * * * * /home/salim/Desktop/hackathon0/ops/scripts/process_queue.sh

set -euo pipefail

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VAULT="$REPO_ROOT/AI_EMPLOYEE_VAULT"
LOG_FILE="$VAULT/Logs/process-queue.log"

# Navigate to repo root so Claude can find project skills
cd "$REPO_ROOT"

# Ensure log directory exists
mkdir -p "$VAULT/Logs"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
    echo "[$(date -Iseconds)] $1"
}

log "=========================================="
log "Starting queue processing..."
log "Repository root: $REPO_ROOT"
log "Vault: $VAULT"

# Count pending items before processing
PENDING_COUNT=$(find "$VAULT/Needs_Action" -name "*.md" -type f 2>/dev/null | wc -l)
log "Pending items in queue: $PENDING_COUNT"

if [ "$PENDING_COUNT" -eq 0 ]; then
    log "No items to process. Exiting."
    exit 0
fi

# Step 1: Triage new items (classify, prioritize, add checklists)
log "Step 1: Running triage-needs-action skill..."
claude \
  --add-dir "$VAULT" \
  --dangerously-skip-permissions \
  -p "Use the triage-needs-action Agent Skill to triage all pending items in the vault queue. Only read/write inside the Obsidian vault. Update Dashboard.md and append a brief entry to Logs/decisions-$(date +%Y-%m-%d).md. Follow Company_Handbook.md rules." \
  >> "$LOG_FILE" 2>&1 || {
    log "Warning: Triage skill encountered an error (continuing to execution)"
}

log "Triage complete."

# Step 2: Execute pending tasks (do the actual work)
log "Step 2: Running execute-task skill..."
claude \
  --add-dir "$VAULT" \
  --dangerously-skip-permissions \
  -p "Use the execute-task Agent Skill to execute up to 5 pending items from Needs_Action. For each item: read the source file to get instructions, perform the work (write content, analyze, etc.), save output to Done/, update item status to done, and move the completed item to Done/. Follow Company_Handbook.md rules." \
  >> "$LOG_FILE" 2>&1 || {
    log "Warning: Execute-task skill encountered an error"
}

log "Execution complete."

# Step 3: Update dashboard with final counts
log "Step 3: Updating dashboard..."
claude \
  --add-dir "$VAULT" \
  --dangerously-skip-permissions \
  -p "Use the update-dashboard Agent Skill to refresh Dashboard.md with current counts and status." \
  >> "$LOG_FILE" 2>&1 || {
    log "Warning: Dashboard update encountered an error"
}

# Final counts
DONE_COUNT=$(find "$VAULT/Done" -name "*.md" -type f 2>/dev/null | wc -l)
REMAINING=$(find "$VAULT/Needs_Action" -name "*.md" -type f 2>/dev/null | wc -l)

log "Processing complete!"
log "Done folder: $DONE_COUNT items"
log "Remaining in queue: $REMAINING items"
log "=========================================="
