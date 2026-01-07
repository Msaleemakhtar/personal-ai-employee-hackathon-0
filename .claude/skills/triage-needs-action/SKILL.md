---
name: triage-needs-action
description: Triage items in the Obsidian vault Needs_Action queue, update Dashboard.md, and append a decision log entry. Use when asked to triage, process, or review Needs_Action.
allowed-tools: Read, Edit, Write, Glob
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

## What to tell the user
Return a short summary:
- how many items you triaged
- top 1–3 high priority items
- which files were updated
