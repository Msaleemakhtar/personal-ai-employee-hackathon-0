# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-11T02:37 UTC
- Last dashboard update: 2026-01-11T21:33 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 10 |
| Needs Action | 0 |
| Pending Approval | 0 |
| Approved | 0 |
| Done | 22 |

- Inbox: `[[Inbox/]]`
- Needs Action: `[[Needs_Action/]]`
- Done: `[[Done/]]`
- Logs: `[[Logs/]]`

## What to do (Bronze demo flow)
1. Drop a file into `Inbox/`.
2. Filesystem watcher creates a new markdown action item in `Needs_Action/`.
3. Claude Code runs the skill `triage_needs_action` and updates this dashboard.
4. Completed items are marked `status: done` and moved to `Done/`.

## Needs Action (Top 5)
> This section is updated by the `update_dashboard` / `triage_needs_action` skill.

**No items currently in Needs_Action queue.**

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-11 21:33 UTC**: Created email approval request for customer onboarding inquiry. Draft acknowledges request and asks for complete requirements due to truncated email content. Approval request moved to Done after processing.
- **2026-01-11 02:37 UTC**: Triaged 2 items - moved completed vault_analysis to Done, triaged high-priority email about Q1 2026 customer onboarding (requires full content retrieval and response approval)
- **2026-01-11 01:25 UTC**: Executed vault analysis plan - scanned 19 completed items, checked approval folders, reviewed logs. Vault status: HEALTHY ✅
- **2026-01-11 00:00 UTC**: Executed 4 tasks - trigger_test validation, AI agents summary, personal AI employee summary, and coding haiku. All completed successfully and moved to Done.
