# AI Employee (Hackathon 0) — Bronze Tier

This is the **Python runtime** for the Personal AI Employee Hackathon 0 project.

- Hackathon spec: `../../Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- Vault (Obsidian GUI + memory): `../../AI_EMPLOYEE_VAULT/`

## What this does (Bronze)

Bronze-tier goal: a **local-first, 24/7** pipeline where:
1. A **filesystem watcher** monitors the vault `Inbox/`.
2. When a new file is dropped, it creates a normalized markdown “action item” in `Needs_Action/`.
3. An **orchestrator** detects new `Needs_Action` items and triggers Claude Code to run an **Agent Skill** to triage and update the dashboard.
4. Everything is supervised by **PM2** for restart + always-on operation.

## Architecture (flow)

```mermaid
flowchart LR
  %% Color palette
  classDef source fill:#1f2937,stroke:#111827,color:#ffffff;
  classDef watcher fill:#2563eb,stroke:#1e40af,color:#ffffff;
  classDef vault fill:#10b981,stroke:#047857,color:#052e16;
  classDef orchestrator fill:#f59e0b,stroke:#b45309,color:#451a03;
  classDef claude fill:#8b5cf6,stroke:#6d28d9,color:#ffffff;
  classDef ops fill:#ef4444,stroke:#991b1b,color:#ffffff;

  A[User drops file<br>into Inbox/]:::source --> B[Filesystem Watcher<br>watchdog]:::watcher
  B --> C[Create Needs_Action note<br>FILE_YYYY-MM-DD_HHMMSS_*.md]:::vault
  C --> D[Orchestrator<br>watchdog]:::orchestrator
  D --> E[Claude Code (headless)<br>runs Agent Skill]:::claude
  E --> F[Update Dashboard.md<br>Append decisions log]:::vault

  P[PM2 supervisor]:::ops -. keeps alive .- B
  P -. keeps alive .- D
```

## Repo + Vault layout

- Repo root: `../../`
  - `CLAUDE.md` (Claude Code instructions)
  - `.claude/skills/*/SKILL.md` (Agent Skills)
  - `ops/pm2/ecosystem.config.cjs` (PM2 config)
- Vault root: `../../AI_EMPLOYEE_VAULT/`
  - `Inbox/`
  - `Needs_Action/`
  - `Done/`
  - `Logs/`
  - `Dashboard.md`
  - `Company_Handbook.md`

## How to run

### 0) Prereqs
- Python 3.13+
- `uv`
- Claude Code CLI (`claude --version`)
- Node.js + npm (for PM2)

### 1) Install Python deps (uv)
From this directory:

```bash
cd /home/salim/Desktop/hackathon0/apps/ai_employee
uv venv
uv sync
```

### 2) Run locally (without PM2)
In two terminals:

**Terminal A (watcher):**
```bash
cd /home/salim/Desktop/hackathon0/apps/ai_employee
VAULT_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT \
uv run python -m ai_employee.watchers.filesystem_watcher
```

**Terminal B (orchestrator):**
```bash
cd /home/salim/Desktop/hackathon0/apps/ai_employee
VAULT_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT \
uv run python -m ai_employee.orchestrator
```

Then drop a file:
```bash
echo "hello" > /home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Inbox/demo.txt
```

You should see a new note appear in:
- `/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Needs_Action/`

### 3) Run 24/7 with PM2 (recommended)

Install PM2 (once):
```bash
npm i -g pm2
```

Start processes:
```bash
pm2 start /home/salim/Desktop/hackathon0/ops/pm2/ecosystem.config.cjs
pm2 status
```

Logs:
```bash
pm2 logs ai-employee-filesystem-watcher
pm2 logs ai-employee-orchestrator
```

Persist across reboots:
```bash
pm2 save
pm2 startup
# follow the instructions PM2 prints
```

## Current known limitation (headless Claude auth)

The orchestrator triggers Claude Code using `claude -p ...`. For true autonomy this requires working **non-interactive authentication**.

If `claude -p "hello"` returns `API Error: 400 Bad Request`, then the orchestrator will time out and the dashboard will not update.

### Supported auth options (official)
Pick one:
- Provide `ANTHROPIC_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`) in the environment (PM2-friendly)
- Configure an `apiKeyHelper` script (rotating tokens)
- Use Bedrock/Vertex/Foundry provider auth
- Use an LLM gateway (router) via `ANTHROPIC_BASE_URL` + gateway token

## Tests

```bash
cd /home/salim/Desktop/hackathon0/apps/ai_employee
uv run pytest -q
```

## Security notes
- No secrets should be written into the Obsidian vault.
- Bronze tier performs **no external actions** (no emails/payments).
