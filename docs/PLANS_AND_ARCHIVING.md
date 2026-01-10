# Plans Folder & Archiving Reference

## Plans Folder Usage

### When Plans Are Created
The **create-plan** skill automatically creates plans for complex tasks that meet any of these criteria:
- Requires more than 3 steps
- Needs external actions (email sending, API calls, payments)
- Involves multiple decisions or branches
- Requires human approval for any step
- Complex enough that a checklist would help

### Plan Creation Flow
1. **triage-needs-action** skill analyzes Needs_Action/ items
2. Detects complexity based on content and requirements
3. Calls **create-plan** skill to generate detailed plan
4. Plan saved to: `AI_EMPLOYEE_VAULT/Plans/PLAN_{original_filename}.md`
5. Original item updated with `status: planned` and plan link

### Plan Structure
Each plan contains:
- **Objective**: Clear statement of goal
- **Context**: Background from original item
- **Steps**: Markdown checklist of required steps
- **External Actions Required**: Actions needing approval
- **Expected Outcome**: Success criteria
- **Dependencies**: Prerequisites or blockers

### Current Implementation Status
- ✅ **Plan creation**: Fully working
- ⚠️ **Plan execution**: Partially implemented
  - execute-task skill has `type: plan` detection (line 72)
  - Handler marked as "not implemented yet"
  - Plans currently require manual review in Obsidian

### Future Work Needed
To complete plan execution:
1. Implement plan parser in execute-task skill
2. Add step-by-step execution logic
3. Handle mixed steps (vault-internal + approval-required)
4. Update plan checklist as steps complete
5. Move completed plans to Done/

---

## Archiving System

### Fully Automated ✅
- **Script**: `ops/scripts/archive_old.sh`
- **Schedule**: Daily at midnight (00:00)
- **Cron**: Already configured and active

### Archive Rules

#### Done/ Items (7-day retention)
- Items older than 7 days → `Archive/YYYY-MM/`
- Example: `Done/EMAIL_abc123.md` → `Archive/2026-01/EMAIL_abc123.md`
- Organized by month for easy browsing

#### Inbox/ Cleanup (1-day retention)
- Processed files older than 1 day are deleted
- Only deletes if corresponding Needs_Action or Done item exists
- Keeps unprocessed files (safety measure)

### Archive Structure
```
AI_EMPLOYEE_VAULT/
├── Archive/
│   ├── 2026-01/       # January 2026 archives
│   ├── 2026-02/       # February 2026 archives
│   └── ...
```

### Monitoring
```bash
# Check archive log
cat AI_EMPLOYEE_VAULT/Logs/archive.log

# View archived items
ls -lh AI_EMPLOYEE_VAULT/Archive/$(date +%Y-%m)/
```

---

## Implementation Status Summary

| Feature | Status | Automation Level |
|---------|--------|------------------|
| File Processing | ✅ Complete | Automatic (24/7) |
| Email Detection | ✅ Complete | Automatic (2-min polling) |
| Plan Creation | ✅ Complete | Automatic (during triage) |
| Plan Execution | ⚠️ Partial | Manual trigger needed |
| Archiving | ✅ Complete | Automatic (daily cron) |
| Approval Workflow | ✅ Complete | Semi-automatic (human approval required) |

---

## Related Files
- **create-plan skill**: `.claude/skills/create-plan/SKILL.md`
- **execute-task skill**: `.claude/skills/execute-task/SKILL.md`
- **Archive script**: `ops/scripts/archive_old.sh`
- **Orchestrator**: `apps/ai_employee/src/ai_employee/orchestrator.py`
- **Handbook**: `AI_EMPLOYEE_VAULT/Company_Handbook.md` (Section 8: Archival Policy)
