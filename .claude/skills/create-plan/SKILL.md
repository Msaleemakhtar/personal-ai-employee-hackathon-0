---
name: create-plan
description: Create a Plan.md file for complex tasks that require multiple steps or external actions
allowed-tools: Read, Write, Glob
---

# Create Plan Skill

## Purpose
When a Needs_Action item is complex (requires multiple steps, external actions, or decisions), create a detailed plan in the Plans/ folder.

## Scope
- Read item from `Needs_Action/`
- Analyze complexity and required actions
- Create `Plans/PLAN_{item_name}.md` with step-by-step breakdown
- Identify if external actions (email, payment, etc.) are needed
- Create approval requests if external actions required

## When to Create a Plan
Create a plan when the item:
- Requires more than 3 steps
- Needs external actions (email sending, API calls, payments)
- Involves multiple decisions or branches
- Requires human approval for any step
- Is complex enough that a checklist would help

## Safety Boundaries
- Only read/write within vault: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`
- Never execute external actions directly
- Always create approval requests for external actions
- Never delete original Needs_Action items

## Loop Prevention (CRITICAL)
To prevent infinite loops and skill recursion:

1. **NEVER call send-email-request skill directly**
   - Only create approval files manually with `status: pending_human_approval`
   - Let the orchestrator handle approval workflow

2. **Skip items already being planned**
   - Check frontmatter `status` field before creating plan
   - Skip if status is: `planning`, `awaiting_approval`, `blocked`, or `planned`
   - Only create plans for items with status: `pending` or `in_progress`

3. **Maximum plan depth: 1**
   - Never create a plan for another plan
   - Check if source item `type` is `plan` - if so, skip and log warning

4. **One plan per source item**
   - Before creating plan, check if `Plans/PLAN_{filename}.md` already exists
   - If exists, read and update it instead of creating duplicate

## Process
1. Read the Needs_Action item from `Needs_Action/` folder
2. Analyze the request and determine if it needs a detailed plan
3. If yes, create `Plans/PLAN_{original_filename}.md` with:
   - **Objective**: Clear statement of what we're trying to achieve
   - **Steps**: Markdown checklist of all required steps
   - **External Actions Required**: List any actions needing approval
   - **Expected Outcome**: What success looks like
   - **Dependencies**: Any prerequisites or blockers
4. If external action needed (e.g., email), create corresponding approval request in `Pending_Approval/`
5. Update original Needs_Action item with link to plan: `plan: Plans/PLAN_{filename}.md`
6. Update original item status to `status: planned`

## Plan File Format
```markdown
---
type: plan
created_at: {ISO timestamp}
source_item: {original Needs_Action filename}
status: pending_approval | in_progress | completed
priority: low | normal | high
requires_external_action: true | false
---

# Plan: {Brief title}

## Objective
{Clear 1-2 sentence statement of what we're trying to achieve}

## Context
{Brief background from the original item}

## Steps
- [ ] Step 1: {Description}
- [ ] Step 2: {Description}
- [ ] Step 3: Send email (REQUIRES APPROVAL - see Pending_Approval/)
- [ ] Step 4: {Description}

## External Actions Required
{If any steps require human approval:}
- **Email send** to recipient@example.com
  - See: `Pending_Approval/EMAIL_REPLY_{id}_{timestamp}.md`
  - Reason: {Why this email is needed}

## Expected Outcome
{What success looks like - deliverables, responses, etc.}

## Dependencies
{Any blockers or prerequisites}
```

## Example Scenarios

### Scenario 1: Email Reply Request
**Input**: `Needs_Action/EMAIL_abc123.md` - Client asking about pricing

**Output**:
1. Create `Plans/PLAN_EMAIL_abc123.md`:
```markdown
---
type: plan
created_at: 2026-01-09T10:00:00Z
source_item: EMAIL_abc123.md
status: pending_approval
priority: high
requires_external_action: true
---

# Plan: Reply to Client Pricing Inquiry

## Objective
Respond to potential client's request for pricing information on our consulting services.

## Context
Client (john@clientcorp.com) sent inquiry about our hourly rates and project packages. They mentioned a 3-month project starting in Q1 2026.

## Steps
- [x] Read original email and understand requirements
- [x] Identify client type (new prospect)
- [x] Draft response with standard rate sheet
- [ ] Send email reply (REQUIRES APPROVAL)
- [ ] Schedule follow-up reminder (7 days)
- [ ] Mark original email as processed

## External Actions Required
- **Email send** to john@clientcorp.com
  - See: `Pending_Approval/EMAIL_REPLY_abc123_1736416800.md`
  - Reason: Reply to business inquiry with pricing information

## Expected Outcome
- Client receives our standard rate sheet
- Warm handoff to sales team if interested
- Follow-up scheduled

## Dependencies
None - can proceed once email is approved
```

2. Create `Pending_Approval/EMAIL_REPLY_abc123_{timestamp}.md` (separate action)

### Scenario 2: Multi-Step Task (No External Action)
**Input**: `Needs_Action/FILE_2026-01-09_summary.txt.md` - User wants quarterly report

**Output**: `Plans/PLAN_FILE_2026-01-09_summary.txt.md`:
```markdown
---
type: plan
created_at: 2026-01-09T10:00:00Z
source_item: FILE_2026-01-09_summary.txt.md
status: in_progress
priority: normal
requires_external_action: false
---

# Plan: Create Q4 2025 Summary Report

## Objective
Compile quarterly summary report from December logs and completed tasks.

## Context
User dropped a file requesting "summarize all my Q4 2025 work". Need to aggregate from Done/ folder and Logs/.

## Steps
- [x] Read source file for requirements
- [ ] Scan Done/ folder for Q4 2025 items (Oct-Dec)
- [ ] Extract key accomplishments from each item
- [ ] Scan Logs/ for October, November, December decision logs
- [ ] Create markdown report with sections: Overview, Accomplishments, Metrics, Decisions
- [ ] Save to Done/RESULT_Q4_2025_summary.md
- [ ] Update source item status to done

## External Actions Required
None - all vault-internal work.

## Expected Outcome
Comprehensive Q4 report saved to Done/ folder, ready for user review in Obsidian.

## Dependencies
None
```

## Integration with Other Skills
- **triage-needs-action**: Calls this skill when item is complex
- **send-email-request**: NEVER call directly - create approval files manually instead
- **execute-task**: Uses the plan as guide for execution steps

## Error Handling
- If source item doesn't exist: Log error, create `Needs_Action/ERROR_{timestamp}.md`
- If plan already exists: Append to existing plan with timestamp
- If vault paths are wrong: Fail fast with clear error message

## Success Criteria
Plan is complete when:
- Plan file created in `Plans/` with all required sections
- Original Needs_Action item updated with plan reference
- Any approval requests created in `Pending_Approval/`
- Dashboard.md reflects new plan count
