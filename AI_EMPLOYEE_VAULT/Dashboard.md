# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-08T16:15 UTC
- Last dashboard update: 2026-01-08T16:15 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 18 |
| Needs Action | 10 |
| Done | 19 |

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

1. **[HIGH]** [[FILE_2026-01-08_001924_pipeline_test_864041.txt]] - URGENT pipeline test (saleem)
2. **[HIGH]** [[FILE_2026-01-08_000918_pipeline_test_1767830958.txt]] - URGENT pipeline test
3. [[FILE_2026-01-08_072617_test_drop_1767857177.txt]] - Test file drop verification
4. [[FILE_2026-01-08_001510_live_test_1767831310.txt]] - Live test for real-time processing
5. [[FILE_2026-01-07_221247_queue_test_1767823967.txt]] - Queue detection test

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-08T16:15**: Triage verification; 10 items in queue (2 HIGH priority), all previously triaged
- **2026-01-08T15:55**: Executed 5 tasks; pipeline test (aslam), employee essay, haiku, sales follow-up, e2e test completed
- **2026-01-08T15:47**: Triaged 2 new items (employee.txt, haiku_test.txt); 3 HIGH priority at time
