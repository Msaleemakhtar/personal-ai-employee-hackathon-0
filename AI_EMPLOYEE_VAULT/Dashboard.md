# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-09T10:05 UTC
- Last dashboard update: 2026-01-09T10:05 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 20 |
| Needs Action | 1 |
| Done | 43 |

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

1. **[[Needs_Action/EMAIL_test_12345|Email: Quick question about the project]]** (high priority)
   - Status: pending
   - From: test@example.com
   - Action: Draft status update response (requires approval)

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-09T10:05**: Triaged 1 item; EMAIL_test_12345 project status inquiry (high priority, email response needed via approval workflow)
- **2026-01-09T09:52**: Executed e2e_test_1767952306.txt task; created `Done/RESULT_2026-01-09_haiku_autonomous_systems.md` with haiku about autonomous systems. **Queue cleared!**
- **2026-01-09T09:52**: Triaged 1 item; e2e_test_1767952306.txt creative writing request (normal priority, haiku about autonomous systems)
- **2026-01-09T00:00**: Executed timer.txt task; created `Done/RESULT_2026-01-09_scheduled_vs_cron_jobs.md` explaining scheduled jobs vs cron. **Queue cleared!**
