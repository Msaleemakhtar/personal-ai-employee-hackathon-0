# Claude Code Instructions — Personal AI Employee Hackathon 0

This repository is for **Hackathon 0: Personal AI Employee (Digital FTE)**.
Primary spec: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`.

## Mission
Build a **local-first, Obsidian-driven, 24/7** autonomous assistant:
- **Perception:** Watchers detect events (Bronze: filesystem watcher).
- **Reasoning:** Claude Code reads vault state, decides next steps.
- **Action:** Bronze has **no external actions**. Later tiers add MCP servers with approvals.

## Pro Plan Users (Hybrid Mode)
This system supports **hybrid autonomous mode** for Pro plan users without API keys:
- ✅ **24/7 autonomous**: File detection, note generation, queue monitoring
- 🔧 **Manual/scheduled**: Triage and dashboard updates (run `./ops/scripts/triage_now.sh`)
- See `docs/PRO_PLAN_USAGE.md` for complete guide
- Orchestrator mode controlled by `ORCHESTRATOR_MODE=queue` in `.env`

## Non-negotiable constraints (Hackathon + safety)

### 1) Obsidian vault is the source of truth
Vault path:
- `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT`

Workflow folders MUST live inside the vault:
- `AI_EMPLOYEE_VAULT/Inbox/` — Drop files here for processing
- `AI_EMPLOYEE_VAULT/Needs_Action/` — Items awaiting triage/execution
- `AI_EMPLOYEE_VAULT/Done/` — Completed items
- `AI_EMPLOYEE_VAULT/Logs/` — System logs and decision history

**Silver tier adds:**
- `AI_EMPLOYEE_VAULT/Plans/` — Complex task plans
- `AI_EMPLOYEE_VAULT/Pending_Approval/` — Actions requiring human approval
- `AI_EMPLOYEE_VAULT/Approved/` — Human-approved actions ready for execution
- `AI_EMPLOYEE_VAULT/Rejected/` — Rejected approval requests
- `AI_EMPLOYEE_VAULT/Archive/` — Old Done items (7+ days)

Repo root is for code + ops + config:
- `apps/`, `ops/`, `.claude/`, `pyproject.toml`, etc.

### 2) All AI functionality must be implemented as Agent Skills
- Any “AI logic” must live in skill definitions under:
  - `/home/salim/Desktop/hackathon0/.claude/skills/`
- Orchestrator/watchers may:
  - detect events
  - call Claude to run a skill
  - do mechanical moves (e.g., move done items to `Done/`)
- Orchestrator/watchers must NOT embed business reasoning.

### 3) No secrets in the vault
- Never write API keys/tokens/passwords into `AI_EMPLOYEE_VAULT/`.
- Use `.env` at repo root (and `.gitignore`) or an OS secrets manager.

### 4) 24/7 operation required
- Long-running processes must be supervised by **PM2**.
- They must auto-restart on crash and persist across reboot.

### 5) Bronze = minimal side effects
- Bronze tier must NOT:
  - send emails
  - make payments
  - post externally
- If asked to do anything external, create a `Needs_Action` note requesting explicit approval and defer.

---

## Bronze tier deliverables checklist
- [ ] `AI_EMPLOYEE_VAULT/Dashboard.md` and `AI_EMPLOYEE_VAULT/Company_Handbook.md` populated and used
- [ ] Filesystem watcher works (creates normalized notes in `Needs_Action/`)
- [ ] Claude Code reads/writes vault via Agent Skills
- [ ] PM2 runs watcher + orchestrator 24/7

## Silver tier features (Email integration + Approvals)
Silver tier extends Bronze with **Gmail integration** and **human approval workflow**:

### Perception (Email watcher)
- **Gmail Watcher**: Polls Gmail API every 2 minutes for `is:unread is:important`
- Creates `EMAIL_{message_id}.md` in `Needs_Action/` for each new email
- Persists processed IDs to survive restarts (`.gmail_processed_ids.json`)
- Exponential backoff on API errors (30s → 1 hour max)

### Reasoning (Email-aware skills)
- **create-plan**: Creates detailed plans for complex tasks
- **send-email-request**: Drafts emails and creates approval requests
- Never sends emails directly - all go through approval workflow

### Action (MCP + Approval workflow)
1. Claude creates approval request in `Pending_Approval/`
2. Human reviews and moves to `Approved/` (or `Rejected/`)
3. Orchestrator detects approved file and executes via Gmail MCP
4. Result logged to `Logs/{date}-actions.json`
5. Files moved to `Done/`

### Safety boundaries (Silver)
- Email sending requires explicit human approval
- Approval requests expire after 24 hours
- Rate limits: 10 emails/hour, 50 emails/day
- All external actions logged with full audit trail

---

## Repository structure (intended)
- `apps/ai_employee/` — Python code (watchers + orchestrator)
- `ops/pm2/` — PM2 ecosystem config
- `.claude/skills/` — Agent Skills (the only place for AI logic)
- `AI_EMPLOYEE_VAULT/` — Obsidian vault (UI + memory)

## Python project rules
- Use **uv** for Python dependency management.
- Prefer running Python with `uv run ...`.
- Keep runtime dependencies minimal (watchdog, dotenv, pydantic).

---

## Vault conventions

### Naming
- Needs_Action items should be named:
  - `FILE_<YYYY-MM-DD_HHMMSS>_<safe_name>.md`
  - `EMAIL_<id>.md` (Silver, not Bronze)

### Metadata contract (YAML frontmatter)
Each `Needs_Action/*.md` MUST contain:
- `type`: `file_drop` | `task` | `email` (Silver) | ...
- `created_at`: ISO string
- `status`: `pending` | `in_progress` | `done` | `blocked`
- `priority`: `low` | `normal` | `high`

---

## Claude operating procedure

### Where Claude reads/writes
- Allowed read/write root: `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/`
- Never write outside the vault unless explicitly requested.

### Always consult first
- `AI_EMPLOYEE_VAULT/Company_Handbook.md` (rules of engagement)
- `AI_EMPLOYEE_VAULT/Dashboard.md` (system status)

### Triage workflow (Bronze)
1. Read `Needs_Action/` items.
2. For each item:
   - classify it
   - assign priority
   - propose a small checklist of next steps
3. Update `Dashboard.md` (counts + top items + recent decisions).
4. If an item is complete, set `status: done`.
5. Orchestrator may move done items to `Done/`.

---

## Required Agent Skills

### Bronze tier skills
- `.claude/skills/triage-needs-action/` — Classify and prioritize items
- `.claude/skills/update-dashboard/` — Recompute Dashboard.md
- `.claude/skills/close-item/` — Mark item as done, move to Done/
- `.claude/skills/execute-task/` — Execute pending tasks from queue

### Silver tier skills
- `.claude/skills/create-plan/` — Create detailed plans for complex tasks
- `.claude/skills/send-email-request/` — Draft email and create approval request

Each skill must define:
- Purpose + scope
- Exact inputs (folders/files)
- Exact outputs (files it may write)
- Safety rules (no deletes, vault-only)
- **Loop prevention guards** (see skill docs for details)

---

## Quality rules for changes
- Don’t modify files you haven’t read.
- Keep changes minimal (no refactors unless required).
- Add minimal tests for watcher + vault path guard.
- Prefer deterministic behavior over cleverness.

---

## Demo runbook (expected)
1. Start PM2 processes.
2. Drop a file into `AI_EMPLOYEE_VAULT/Inbox/`.
3. Watcher generates a `Needs_Action` note.
4. Claude skill triages it; dashboard updates.
5. Show PM2 status/logs to prove 24/7 supervision.
