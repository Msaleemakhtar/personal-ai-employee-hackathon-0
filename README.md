# Personal AI Employee — Hackathon 0 (Bronze)

A **local-first, fully autonomous assistant** built with:
- **Obsidian vault** as the dashboard + long-term memory
- **Python watchers** (watchdog + uv) for file detection
- **Claude Code Agent Skills** for AI reasoning + execution
- **PM2** for process supervision
- **Cron** for scheduled automation

## Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ and npm
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude --version`)

### 1. Install Dependencies

```bash
cd /home/salim/Desktop/hackathon0

# Install PM2 globally
npm install -g pm2

# Install Node dependencies (for PM2 config)
cd ops && npm install && cd ..

# Install Python dependencies
cd apps/ai_employee && uv sync && cd ../..
```

### 2. Start the System

```bash
# Start all processes with PM2
pm2 start ops/pm2/ecosystem.config.cjs

# Check status
pm2 list

# Save for persistence
pm2 save
```

### 3. Test It

```bash
# Drop a file into the Inbox
echo "Write a haiku about coding" > AI_EMPLOYEE_VAULT/Inbox/haiku.txt

# Check that a Needs_Action note was created (wait 2-3 seconds)
ls AI_EMPLOYEE_VAULT/Needs_Action/

# Run processing manually OR wait for cron (every 30 min)
./ops/scripts/process_queue.sh

# Check results
ls AI_EMPLOYEE_VAULT/Done/
```

### 4. Persist Across Reboots

```bash
pm2 save
pm2 startup
# Run the command PM2 outputs (requires sudo)
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PM2 Supervisor                                  │
│                         (keeps processes alive 24/7)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                              │
                    ▼                              ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│   Filesystem Watcher        │    │      Orchestrator           │
│   (watchdog)                │    │      (watchdog)             │
│                             │    │                             │
│   Monitors: Inbox/          │    │   Monitors: Needs_Action/   │
│   Creates: Needs_Action/    │    │   Logs new items            │
└─────────────────────────────┘    └─────────────────────────────┘
              │                                   │
              ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Obsidian Vault                                     │
│  ┌──────────┐  ┌───────────────┐  ┌────────┐  ┌─────────┐  ┌──────────────┐ │
│  │  Inbox/  │─▶│ Needs_Action/ │─▶│  Done/ │─▶│ Archive/│  │ Dashboard.md │ │
│  │ (raw)    │  │ (actionable)  │  │(done)  │  │(old)    │  │              │ │
│  └──────────┘  └───────────────┘  └────────┘  └─────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Claude Code + Agent Skills                                │
│                                                                              │
│   triage-needs-action  │  execute-task      │  update-dashboard │ close-item│
│   (classify/prioritize)│  (DO THE WORK!)    │  (refresh counts) │ (mark done│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Cron Automation                                      │
│                                                                              │
│   */30 * * * *  process_queue.sh   (triage + execute every 30 min)          │
│   0 0 * * *     archive_old.sh     (cleanup daily at midnight)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Data Flow

```
User drops file     Watcher creates      Cron runs           Output saved
into Inbox/    ──▶  Needs_Action/   ──▶  triage +       ──▶  to Done/
                    note (.md)           execute-task
                    (instant)            (every 30 min)      (fully automatic)
```

---

## Automation Features

### Cron Jobs (Automatic)

| Schedule | Script | Purpose |
|----------|--------|---------|
| Every 30 min | `process_queue.sh` | Triage new items + Execute pending tasks |
| Daily midnight | `archive_old.sh` | Archive old Done items, cleanup Inbox |

### Agent Skills

| Skill | Purpose |
|-------|---------|
| `triage-needs-action` | Classify, prioritize, add checklists |
| `execute-task` | **Actually DO the work** (write essays, analyze, etc.) |
| `update-dashboard` | Refresh counts and status |
| `close-item` | Mark done and move to Done/ |

---

## Project Structure

```
hackathon0/
├── AI_EMPLOYEE_VAULT/          # Obsidian vault (UI + memory)
│   ├── Dashboard.md            # System status
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Inbox/                  # Raw file drops
│   ├── Needs_Action/           # Actionable items
│   ├── Done/                   # Completed items
│   ├── Archive/                # Old items (7+ days)
│   └── Logs/                   # Decision + process logs
│
├── apps/ai_employee/           # Python runtime
│   ├── src/ai_employee/
│   │   ├── watchers/
│   │   │   └── filesystem_watcher.py
│   │   ├── orchestrator.py
│   │   ├── vault_io.py
│   │   └── schemas.py
│   └── tests/
│
├── .claude/skills/             # Agent Skills (AI logic)
│   ├── triage-needs-action/
│   ├── execute-task/           # NEW: Actually executes tasks
│   ├── update-dashboard/
│   └── close-item/
│
├── ops/                        # Operations
│   ├── pm2/ecosystem.config.cjs
│   ├── scripts/
│   │   ├── process_queue.sh    # Triage + Execute (cron)
│   │   ├── archive_old.sh      # Cleanup (cron)
│   │   └── triage_now.sh       # Manual triage only
│   ├── runbooks/pm2.md
│   ├── node_modules/           # Node dependencies
│   ├── package.json
│   └── package-lock.json
│
├── .env                        # Configuration
├── CLAUDE.md                   # Claude Code instructions
└── README.md
```

---

## Common Commands

```bash
# PM2 process management
pm2 list                        # Show process status
pm2 logs                        # View all logs
pm2 logs ai-employee-filesystem-watcher  # View watcher logs
pm2 restart all                 # Restart all processes
pm2 stop all                    # Stop all processes

# Manual processing (or wait for cron)
./ops/scripts/process_queue.sh  # Triage + Execute pending items
./ops/scripts/triage_now.sh     # Triage only (no execution)
./ops/scripts/archive_old.sh    # Cleanup old items

# Test file drop
echo "Write a poem about AI" > AI_EMPLOYEE_VAULT/Inbox/poem.txt

# Check vault state
ls AI_EMPLOYEE_VAULT/Inbox/
ls AI_EMPLOYEE_VAULT/Needs_Action/
ls AI_EMPLOYEE_VAULT/Done/

# Check cron jobs
crontab -l

# View processing logs
tail -f AI_EMPLOYEE_VAULT/Logs/process-queue.log
tail -f AI_EMPLOYEE_VAULT/Logs/cron.log
```

---

## Troubleshooting

### Watcher not detecting files
```bash
pm2 logs ai-employee-filesystem-watcher --lines 20
pm2 restart ai-employee-filesystem-watcher
```

### Tasks not executing
```bash
# Check cron is running
crontab -l

# Check processing logs
cat AI_EMPLOYEE_VAULT/Logs/process-queue.log

# Run manually to test
./ops/scripts/process_queue.sh
```

### PM2 processes keep restarting
```bash
pm2 logs --err --lines 50
```

### Check system health
```bash
pm2 status
crontab -l
cat AI_EMPLOYEE_VAULT/Dashboard.md
```

---

## Configuration (.env)

```bash
# Mode: "queue" (Pro plan) or "auto" (API key)
ORCHESTRATOR_MODE=queue

# Only needed for auto mode
ANTHROPIC_API_KEY=

# Vault paths
VAULT_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT
INBOX_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Inbox
NEEDS_ACTION_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Needs_Action
DONE_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Done
LOGS_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT/Logs
```

---

## Cron Setup (Already Configured)

The following cron jobs are automatically set up:

```cron
# Process queue every 30 minutes (triage + execute)
*/30 * * * * /home/salim/Desktop/hackathon0/ops/scripts/process_queue.sh

# Archive old items daily at midnight
0 0 * * * /home/salim/Desktop/hackathon0/ops/scripts/archive_old.sh
```

To verify: `crontab -l`

---

## More Documentation

- [Pro Plan Usage Guide](docs/PRO_PLAN_USAGE.md)
- [PM2 Runbook](ops/runbooks/pm2.md)
- [Company Handbook](AI_EMPLOYEE_VAULT/Company_Handbook.md)
- [Hackathon Spec](docs/Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
