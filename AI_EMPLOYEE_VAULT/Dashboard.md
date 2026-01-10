# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-10T22:15 UTC
- Last dashboard update: 2026-01-10T23:05 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 3 |
| Needs Action | 0 |
| Pending Approval | 0 |
| Approved | 0 |
| Done | 11 |

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

**All items completed!** ✅ No pending actions in the queue.

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-10 17:03 UTC**: Task execution - EMAIL_19ba8c6ef5e8457c (Q2 Marketing Campaign) completed, email approval request created; FILE_2026-01-10_165009_edu.md completed 3-line AI employee summary
- **2026-01-10 22:15 UTC**: Triaged 2 items - EMAIL_19ba8c6ef5e8457c (high priority Q2 marketing campaign) and FILE_2026-01-10_165009_edu.md (content creation)
- **2026-01-10 21:30 UTC**: Task execution - FILE_2026-01-10_161253_ai.md completed 3-line AI agents summary, saved to Done/
- **2026-01-10 21:25 UTC**: Triaged FILE_2026-01-10_161253_ai.md - Content creation task (write 3-line summary about AI agents), priority: normal
- **2026-01-10 20:52 UTC**: Task execution - FILE_2026-01-10_154923_haiku.txt completed haiku creation, saved to Done/
