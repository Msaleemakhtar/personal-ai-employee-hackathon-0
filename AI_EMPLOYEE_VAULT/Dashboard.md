# Dashboard

Vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

## System Health
- Watcher: **running** (PM2)
- Orchestrator: **running** (queue mode)
- Last triage: 2026-01-08T12:35 UTC
- Last dashboard update: 2026-01-08T15:00 UTC

## Queues
| Queue | Count |
|-------|-------|
| Inbox | 16 |
| Needs Action | 13 |
| Done | 10 |

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

1. **[HIGH]** [[FILE_2026-01-08_075307_pipeline_test_864.txt]] - URGENT pipeline test (aslam)
2. **[HIGH]** [[FILE_2026-01-08_001924_pipeline_test_864041.txt]] - URGENT pipeline test (saleem)
3. **[HIGH]** [[FILE_2026-01-08_000918_pipeline_test_1767830958.txt]] - URGENT pipeline test
4. [[FILE_2026-01-08_114449_sales_reviewt_after.md]] - Sales review follow-up
5. [[FILE_2026-01-08_083655_test_e2e_1767861415.txt]] - End-to-end flow test

## Recent Decisions
> This section is updated from `Logs/decisions-YYYY-MM-DD.md`.

- **2026-01-08T12:35**: Executed 5 tasks; essay, saleem, sales reviews, test verification completed
- **2026-01-08T14:25**: Verified 18 items; all triaged; 3 HIGH priority remain
- **2026-01-08T12:15**: Triaged 1 new item (essay.txt); 3 HIGH priority remain
