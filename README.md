# Personal AI Employee — Hackathon 0 (Bronze)

This repo implements a **local-first Personal AI Employee** using:
- **Obsidian vault** as the dashboard + long-term memory
- **Python watchers/orchestrator** (uv-managed) as the always-on runtime
- **Claude Code Agent Skills** for all AI reasoning
- **PM2** to keep processes running 24/7

Hackathon spec:
- `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`

---

## Key paths

### Obsidian Vault (GUI + memory)
- `AI_EMPLOYEE_VAULT/`
  - `Dashboard.md`
  - `Company_Handbook.md`
  - `Inbox/`
  - `Needs_Action/`
  - `Done/`
  - `Logs/`

### Python runtime (uv project)
- `apps/ai_employee/`
  - `pyproject.toml`, `uv.lock`, `.venv/`
  - `src/ai_employee/watchers/filesystem_watcher.py`
  - `src/ai_employee/orchestrator.py`

### Claude Code instructions + Agent Skills
- `CLAUDE.md` (repo-level Claude Code instructions)
- `.claude/skills/*/SKILL.md` (Agent Skills)

### Ops / process supervision
- `ops/pm2/ecosystem.config.cjs`
- `ops/runbooks/pm2.md`

---

## Bronze flow (overview)

```mermaid
flowchart LR
  classDef source fill:#1f2937,stroke:#111827,color:#ffffff;
  classDef watcher fill:#2563eb,stroke:#1e40af,color:#ffffff;
  classDef vault fill:#10b981,stroke:#047857,color:#052e16;
  classDef orchestrator fill:#f59e0b,stroke:#b45309,color:#451a03;
  classDef claude fill:#8b5cf6,stroke:#6d28d9,color:#ffffff;
  classDef ops fill:#ef4444,stroke:#991b1b,color:#ffffff;

  A[User drops file<br/>into Inbox/]:::source --> B[Filesystem Watcher<br/>watchdog]:::watcher
  B --> C[Create Needs_Action note<br/>FILE_YYYY-MM-DD_HHMMSS_*.md]:::vault
  C --> D[Orchestrator<br/>watchdog]:::orchestrator
  D --> E[Claude Code (headless)<br/>runs Agent Skill]:::claude
  E --> F[Update Dashboard.md<br/>Append decisions log]:::vault

  P[PM2 supervisor]:::ops -. keeps alive .- B
  P -. keeps alive .- D
```

---

## How to run (quickstart)

### 1) Install prerequisites
- Python 3.13+
- `uv`
- Claude Code (`claude --version`)
- Node.js + npm (for PM2)

### 2) Install Python deps (uv)
```bash
cd /home/salim/Desktop/hackathon0/apps/ai_employee
uv venv
uv sync
```

### 3) Run locally (two terminals)
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

Drop a file to trigger the watcher:
```bash
echo "hello" > /home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Inbox/demo.txt
```

### 4) Run 24/7 with PM2 (recommended)
Install PM2 (once):
```bash
npm i -g pm2
```

Start:
```bash
pm2 start /home/salim/Desktop/hackathon0/ops/pm2/ecosystem.config.cjs
pm2 status
```

Logs:
```bash
pm2 logs ai-employee-filesystem-watcher
pm2 logs ai-employee-orchestrator
```

Persist across reboot:
```bash
pm2 save
pm2 startup
# follow the instructions PM2 prints
```

---

## Important: headless Claude authentication (current blocker)

The orchestrator triggers Claude Code using `claude -p ...`. For true autonomy this requires working **non-interactive authentication**.

If `claude -p "hello"` returns `API Error: 400 Bad Request`, then the orchestrator will time out and the dashboard will not update.

### Official auth options for automation
- Provide `ANTHROPIC_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`) in the PM2 environment
- Configure `apiKeyHelper` (rotating token helper)
- Use Bedrock/Vertex/Foundry provider auth
- Use an LLM gateway via `ANTHROPIC_BASE_URL` + gateway token

---

## More detailed docs
- Runtime details: `apps/ai_employee/README.md`
- PM2 runbook: `ops/runbooks/pm2.md`
- Vault rules: `AI_EMPLOYEE_VAULT/Company_Handbook.md`
- Vault dashboard: `AI_EMPLOYEE_VAULT/Dashboard.md`
