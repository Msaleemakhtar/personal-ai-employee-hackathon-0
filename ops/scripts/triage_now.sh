#!/usr/bin/env bash
# Manual triage trigger for Pro plan users
# Run this script whenever you want to process the Needs_Action queue
#
# Usage:
#   ./ops/scripts/triage_now.sh
#
# Or schedule it with cron (example: every 2 hours during work hours):
#   0 9-17/2 * * 1-5 cd /home/salim/Desktop/hackathon0 && ./ops/scripts/triage_now.sh

set -euo pipefail

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Navigate to repo root so Claude can find project skills
cd "$REPO_ROOT"

echo "[triage_now] Starting manual triage..."
echo "[triage_now] Repository root: $REPO_ROOT"
echo "[triage_now] Vault: $REPO_ROOT/AI_EMPLOYEE_VAULT"
echo ""

# Run Claude with the triage skill
# The --add-dir ensures vault files are accessible
# The skill will scan Needs_Action/, triage items, and update the dashboard
# --dangerously-skip-permissions is used because -p mode is non-interactive
# This is safe for local use since we're only writing to the vault directory
claude \
  --add-dir "$REPO_ROOT/AI_EMPLOYEE_VAULT" \
  --dangerously-skip-permissions \
  -p "Use the triage-needs-action Agent Skill to triage all pending items in the vault queue. Only read/write inside the Obsidian vault. Update Dashboard.md and append a brief entry to Logs/decisions-$(date +%Y-%m-%d).md. Follow Company_Handbook.md rules."

echo ""
echo "[triage_now] Triage complete!"
echo "[triage_now] Check AI_EMPLOYEE_VAULT/Dashboard.md for updates"
