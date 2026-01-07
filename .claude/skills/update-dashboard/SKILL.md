---
name: update-dashboard
description: Recompute and update the Obsidian Dashboard.md counts and links from the vault state. Use when asked to refresh or update the dashboard.
allowed-tools: Read, Edit, Write, Glob
---

# Hackathon Skill: Update Dashboard

## Safety boundaries
- Only operate under `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`
- Never delete files.

## Inputs
- Dashboard: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Dashboard.md`
- Folders:
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Inbox/`
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Needs_Action/`
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Done/`
  - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Logs/`

## Output contract
- Update (minimally edit) `Dashboard.md`:
  - refresh folder counts
  - update “Needs Action (Top 5)” using newest/most urgent items
  - update “Recent Decisions” by reading today’s `Logs/decisions-YYYY-MM-DD.md` if present

## What to tell the user
- counts and which section(s) changed
