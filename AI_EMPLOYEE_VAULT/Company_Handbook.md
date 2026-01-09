# Company Handbook (Rules of Engagement)

This file defines how the AI Employee should behave.

## 1) Scope (Bronze Tier)
- **Local-first only.** The Obsidian vault is the UI + memory.
- **No external side effects** in Bronze:
  - Do not send emails
  - Do not make payments
  - Do not post to social media
- Work only with files inside the vault:
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`

## 2) Safety Rules (Non-negotiable)
1. **No secrets in the vault.** Never write API keys, tokens, passwords.
2. **Never delete user data.** Prefer:
   - update note status
   - move to `Done/`
3. If uncertain, **ask** by creating a clarifying note in `Needs_Action/`.
4. When writing logs, **avoid copying sensitive content**; log summaries.

## 3) Folder Contracts
- `Inbox/`: raw drops (files or notes).
- `Needs_Action/`: normalized actionable items for triage.
- `Done/`: completed items.
- `Logs/`: operational + decision logs.

## 4) Item Schema (required frontmatter)
Every `Needs_Action/*.md` must include YAML frontmatter:
- `type`: `file_drop` | `task` | `email` (Silver) | ...
- `created_at`: ISO timestamp
- `status`: `pending` | `in_progress` | `done` | `blocked`
- `priority`: `low` | `normal` | `high`

## 5) Prioritization Rules
- **High priority** when:
  - contains "urgent", "asap", "payment", "invoice", "deadline"
  - the user explicitly marks it high
- Default priority: **normal**.

## 6) Output Expectations (for Claude skills)
When triaging an item, the AI should:
1. Summarize what the item is.
2. Propose a small checklist of next steps.
3. Update the dashboard with the latest queue status.
4. If completed, set `status: done` (or mark as ready to archive).

## 7) Task Execution Rules
When executing a task, the AI should:
1. Read the source file (from `Inbox/`) to understand user's instructions.
2. Perform ONLY vault-internal actions:
   - Content creation (essays, summaries, analysis)
   - File organization (moving, renaming within vault)
   - Information gathering (from vault files only)
3. Save output to `Done/` with descriptive filename.
4. Update the original Needs_Action item: `status: done`.
5. Move the completed item from `Needs_Action/` to `Done/`.
6. Log the action in today's decisions log.

**Prohibited Actions (Bronze Tier):**
- No external API calls
- No email sending
- No file operations outside the vault
- No shell command execution
- No payments or transactions

## 8) Archival Policy
- Items in `Done/` older than 7 days: Move to `Archive/YYYY-MM/`
- Processed `Inbox/` files older than 1 day: Delete if corresponding item exists
- Never delete unprocessed files

## 9) Silver Tier Rules (External Actions via MCP)

### External Actions Enabled
- **Email sending** via Gmail MCP (Model Context Protocol)
- All actions require **human approval** (no auto-send in Silver tier)
- Orchestrator calls Claude Code CLI, which uses configured MCP servers

### Approval Workflow
1. AI creates `Pending_Approval/ACTION_{type}_{timestamp}.md` with full details
2. Human reviews content, reasoning, and intent
3. Human moves file to `Approved/` (approve) or `Rejected/` (reject)
4. Orchestrator detects approved file in `Approved/` folder
5. Orchestrator executes: `claude -p "Use gmail MCP to send..."`
6. MCP server executes the approved action
7. Result logged to `Logs/{date}-actions.json`
8. Approval file moved to `Done/`

### Action Thresholds (Silver Tier)
- **All emails**: Require human approval (no exceptions in Silver tier)
- **Approval expiry**: 24 hours (after that, approval request auto-rejected)
- **Rate limits**:
  - Max 10 emails per hour
  - Max 50 emails per day
  - Exceeded limits → defer action and create alert

### Approval Request Format
Each `Pending_Approval/*.md` must include:
- `type`: `approval_request`
- `action`: `send_email` | `schedule_meeting` | ...
- `created_at`: ISO timestamp
- `expires_at`: ISO timestamp (created_at + 24 hours)
- `status`: `pending` | `approved` | `rejected` | `expired`
- `priority`: `low` | `normal` | `high`
- Complete action details (to, subject, body for emails)
- Context explaining why this action is needed

### Known Contacts (Gold Tier Feature)
In Gold tier, the AI may auto-approve replies to known trusted contacts.
**Silver tier**: All contacts require approval (list below is for future Gold tier):
- (Empty for Silver tier - all require approval)
