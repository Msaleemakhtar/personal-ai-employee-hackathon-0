# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-09T00:00 UTC
- Last dashboard update: 2026-01-09T01:23 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 19 |
| Needs Action | 0 |
| Done | 41 |

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

*Queue is clear — no pending items.*

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-09T00:00**: Executed timer.txt task; created `Done/RESULT_2026-01-09_scheduled_vs_cron_jobs.md` explaining scheduled jobs vs cron. **Queue cleared!**
- **2026-01-09T00:00**: Triaged 1 item; timer.txt asking about scheduled vs cron jobs (normal priority, knowledge question)
- **2026-01-08T22:00**: Executed 5 tasks; demo4, autonomous detection, queue detection, live test, filesystem watcher tests all completed.
