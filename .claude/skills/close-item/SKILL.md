---
name: close-item
description: Mark a specific Needs_Action markdown item as done and move it to Done. Use when asked to close, complete, or archive an item.
allowed-tools: Read, Edit, Write
---

# Hackathon Skill: Close Item

## Safety boundaries
- Only operate under `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`
- Never delete files.

## Required input from user
You must be given the exact path to the item markdown file inside:
- `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Needs_Action/`

If the user did not provide a path, ask for it.

## Output contract
1. Read the item.
2. Update its frontmatter: set `status: done`.
3. Move the file to:
   - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Done/`
4. Append a one-line entry to today’s decisions log:
   - `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Logs/decisions-YYYY-MM-DD.md`
