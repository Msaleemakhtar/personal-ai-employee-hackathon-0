---
name: triage-needs-action
description: Triage items in the Obsidian vault Needs_Action queue, update Dashboard.md, and append a decision log entry. Use when asked to triage, process, or review Needs_Action.
allowed-tools: Read, Edit, Write, Glob, Skill
---

# Hackathon Skill: Triage Needs_Action

## Scope
Bronze tier scope only:
- Local-first (Obsidian vault only)
- No external actions (no email sending, no payments, no posting)

## Hard safety boundaries
- You may ONLY read/write under:
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`
- Never write secrets.
- Never delete files.

## Inputs (vault paths)
- Queue folder: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Needs_Action/`
- Handbook: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Company_Handbook.md`
- Dashboard: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Dashboard.md`
- Decisions log (append): `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Logs/decisions-YYYY-MM-DD.md`

## Output contract
When this skill runs you must:
1. Read `Company_Handbook.md` first and follow it.
2. List items in `Needs_Action/` and read the newest up to 10 items.
3. For each item, update the item **in place** by adding:
   - a short summary (1–3 sentences)
   - an explicit checklist of next steps
   - update YAML frontmatter fields if missing (`status`, `priority`)
4. Update `Dashboard.md` sections:
   - Counts for Inbox / Needs_Action / Done
   - “Needs Action (Top 5)” list with links
   - “Recent Decisions” (latest 3)
5. Append a brief entry to today’s decisions log.

## Decision rules (simple + deterministic)
- If the note includes keywords like: urgent/asap/payment/invoice/deadline → `priority: high`
- Otherwise keep `priority: normal`
- Default `status: pending` unless clearly blocked.

## Complexity Detection & Plan Creation (Silver Tier)
After triaging each item, analyze if it requires a detailed plan. Create a plan when the item:
- Has more than 3 next steps in your checklist
- Requires external actions (email sending, API calls, payments)
- Involves multiple decisions or branching logic
- Needs human approval for any step
- Is complex enough that step-by-step planning would help

### How to Create Plans
When complexity criteria are met:
1. Use the Skill tool to invoke: `create-plan` (pass the item filename as context)
2. The create-plan skill will:
   - Create `Plans/PLAN_{filename}.md`
   - Update the original item with plan reference
   - Create approval requests if needed
3. Log the plan creation in your decision log entry

### Loop Prevention (CRITICAL)
- Check item's `status` field before creating plan
- Skip plan creation if status is: `planning`, `planned`, `awaiting_approval`, `blocked`
- Only create plans for: `pending` or `in_progress` items
- Never create a plan for items with `type: plan` (plans don't plan themselves)

## What to tell the user
Return a short summary:
- how many items you triaged
- top 1–3 high priority items
- which files were updated
