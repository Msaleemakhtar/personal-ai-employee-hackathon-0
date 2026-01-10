# Personal AI Employee — Hackathon 0 (Bronze + Silver)

A **local-first, fully autonomous assistant** built with:
- **Obsidian vault** as the dashboard + long-term memory
- **Python watchers** (watchdog + uv) for file detection + Gmail polling
- **Claude Code Agent Skills** for AI reasoning + execution
- **PM2** for process supervision
- **Gmail MCP** for email actions (with human approval)
- **Systemd timers** for scheduled automation (handles suspend/resume)

## Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ and npm
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude --version`)

### Complete Startup Guide

#### 1. Install Dependencies

```bash
cd /home/salim/Desktop/hackathon0

# Install PM2 globally
npm install -g pm2

# Install Node dependencies (for PM2 config)
cd ops && npm install && cd ..

# Install Python dependencies
cd apps/ai_employee && uv sync && cd ../..
```

#### 2. Configure Environment

```bash
# Copy .env template if not exists
cp .env.example .env  # (or create manually)

# Edit .env with your settings:
# ORCHESTRATOR_MODE=queue  (for Pro plan users)
# VAULT_PATH=/home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT
```

#### 3. Start PM2 Processes

```bash
# Start all processes (filesystem-watcher, gmail-watcher, orchestrator)
pm2 start ops/pm2/ecosystem.config.cjs

# Verify all processes are running
pm2 list

# Save PM2 process list for auto-restart
pm2 save

# Setup PM2 to start on system boot (run once)
pm2 startup
# IMPORTANT: Run the command that PM2 outputs (requires sudo)
```

#### 4. Setup Systemd Timer (Queue Processor)

```bash
# Install systemd timer for automated queue processing
./ops/systemd/install-timer.sh

# Enable user services to run even when logged out
sudo loginctl enable-linger $USER

# Verify timer is active
systemctl --user list-timers ai-employee-queue.timer

# Check timer status
systemctl --user status ai-employee-queue.timer
```

#### 5. Silver Tier: Gmail Setup (Optional)

If you want email automation capabilities:

```bash
# Navigate to Gmail MCP server directory
cd apps/gmail-mcp-server

# Install dependencies
uv sync

# Authenticate with Gmail (opens browser)
uv run gmail-mcp --auth

# Verify authentication
uv run gmail-mcp --check-auth

# Return to project root
cd ../..

# Restart Gmail watcher to activate
pm2 restart ai-employee-gmail-watcher
```

**Note**: This uses our custom FastMCP-based Gmail MCP server, not third-party packages.

See `apps/gmail-mcp-server/QUICK_START.md` for detailed setup instructions.

#### 6. Test the System

```bash
# Drop a test file into the Inbox
echo "Write a haiku about coding" > AI_EMPLOYEE_VAULT/Inbox/haiku.txt

# Check that a Needs_Action note was created (wait 2-3 seconds)
ls AI_EMPLOYEE_VAULT/Needs_Action/

# Run processing manually (or wait for systemd timer - every 30 min)
./ops/scripts/process_queue.sh

# Check results in Done folder
ls AI_EMPLOYEE_VAULT/Done/

# View Dashboard
cat AI_EMPLOYEE_VAULT/Dashboard.md
```

### Restart Everything (After Reboot or Code Changes)

```bash
# Restart all PM2 processes
pm2 restart all

# Or restart individual processes
pm2 restart ai-employee-filesystem-watcher
pm2 restart ai-employee-gmail-watcher
pm2 restart ai-employee-orchestrator

# Verify status
pm2 list
pm2 logs --lines 20

# Check systemd timer
systemctl --user status ai-employee-queue.timer
```

### Stop Everything

```bash
# Stop all PM2 processes
pm2 stop all

# Or stop individual processes
pm2 stop ai-employee-filesystem-watcher
pm2 stop ai-employee-gmail-watcher
pm2 stop ai-employee-orchestrator

# Disable systemd timer
systemctl --user stop ai-employee-queue.timer
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PM2 Supervisor                                  │
│                         (keeps processes alive 24/7)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                              │                        │
                    ▼                              ▼                        ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│ Filesystem Watcher   │    │   Orchestrator       │    │   Gmail Watcher      │
│ (watchdog)           │    │   (watchdog)         │    │ (Gmail API Direct)   │
│                      │    │                      │    │   NOT MCP!           │
│ Monitors: Inbox/     │    │ Monitors:            │    │ Polls: Gmail         │
│ Creates:             │    │  - Needs_Action/     │    │ every 2 min          │
│  Needs_Action/       │    │  - Approved/         │    │ Creates:             │
│                      │    │                      │    │  Needs_Action/       │
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
              │                       │                                │
              ▼                       ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Obsidian Vault                                     │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────────┐  ┌────────┐          │
│  │  Inbox/  │─▶│ Needs_Action/ │─▶│ Pending_Approval/│─▶│  Done/ │          │
│  │ (raw)    │  │ (actionable)  │  │ (awaiting human) │  │ (done) │          │
│  └──────────┘  └───────────────┘  └──────────────────┘  └────────┘          │
│                        │                  │     │             │               │
│                        │                  ▼     ▼             ▼               │
│                        │           Approved  Rejected   ┌─────────┐          │
│                        │             (ready) (no)       │Archive/ │          │
│                        │                  │             │ (old)   │          │
│                        ▼                  ▼             └─────────┘          │
│                  ┌──────────────┐  ┌────────────┐  ┌──────────────┐         │
│                  │Dashboard.md  │  │Plans/      │  │Logs/         │         │
│                  └──────────────┘  └────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Claude Code + Agent Skills                                │
│                                                                              │
│   triage-needs-action  │  execute-task      │  update-dashboard │ close-item│
│   (classify/prioritize)│  (DO THE WORK!)    │  (refresh counts) │ (mark done│
│                                                                              │
│   Gmail MCP Server: Used for ACTIONS (send/reply), NOT for polling          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Systemd Timer Automation                                │
│                    (survives suspend/resume!)                                │
│                                                                              │
│   ai-employee-queue.timer   process_queue.sh   (every 30 min)               │
│   cron: 0 0 * * *           archive_old.sh     (daily at midnight)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Data Flow

```
User drops file     Watcher creates      Systemd timer       Output saved
into Inbox/    ──▶  Needs_Action/   ──▶  runs triage +  ──▶  to Done/
                    note (.md)           execute-task
                    (instant)            (every 30 min)      (fully automatic)
```

---

## Automation Features

### Scheduled Jobs (Automatic)

| Schedule | Script | Method | Purpose |
|----------|--------|--------|---------|
| Every 30 min | `process_queue.sh` | Systemd timer | Triage + Execute (survives suspend) |
| Daily midnight | `archive_old.sh` | Cron | Archive old Done items, cleanup Inbox |

### Agent Skills

#### Bronze Tier
| Skill | Purpose |
|-------|---------|
| `triage-needs-action` | Classify, prioritize, add checklists |
| `execute-task` | **Actually DO the work** (write essays, analyze, etc.) |
| `update-dashboard` | Refresh counts and status |
| `close-item` | Mark done and move to Done/ |

#### Silver Tier (Email + Approvals)
| Skill | Purpose |
|-------|---------|
| `create-plan` | Create detailed plans for complex multi-step tasks |
| `send-email-request` | Draft emails and create approval requests (never sends directly) |

### Silver Tier: Email Approval Workflow

```
Gmail Inbox              Claude Creates         Human Reviews        Orchestrator Executes
(unread+important)  ──▶  Approval Request  ──▶  Move to Approved/ ──▶  Send via Custom Gmail MCP
                         (Pending_Approval/)     (or Rejected/)         (logs to actions.json)
```

**Safety guarantees:**
- ✅ No email sent without explicit human approval
- ✅ All requests expire after 24 hours (auto-rejected)
- ✅ Rate limits: 10 emails/hour, 50 emails/day
- ✅ Full audit trail in `Logs/{date}-actions.json`

**Approval process:**
1. Claude detects email in `Needs_Action/EMAIL_*.md`
2. Claude drafts reply and creates `Pending_Approval/EMAIL_REPLY_{id}.md`
3. Human reviews the draft in Obsidian
4. Human moves to `Approved/` (to send) or `Rejected/` (to cancel)
5. Orchestrator detects approved file and executes via custom Gmail MCP server
6. Result logged, files moved to `Done/`

**Technical implementation:**
- Custom FastMCP-based Gmail MCP server (`apps/gmail-mcp-server/`)
- 19 Gmail tools available via Claude Code CLI
- OAuth 2.0 authentication (credentials in `~/.gmail-mcp/`)
- Setup: `cd apps/gmail-mcp-server && uv run gmail-mcp --auth`

---

## Gmail Watcher Architecture

The Gmail watcher uses a **two-component architecture** that separates perception (polling) from action (email operations):

### Component 1: Gmail Watcher (Polling - NO MCP)

The watcher polls Gmail **directly** using Google's Python client library (`google-api-python-client`):

**Location:** `apps/ai_employee/src/ai_employee/watchers/gmail_watcher.py`

**How it works:**
```python
# Direct Gmail API polling (apps/ai_employee/src/ai_employee/watchers/gmail_watcher.py:132-140)
def check_for_updates(self) -> list:
    results = self.service.users().messages().list(
        userId='me',
        q='is:unread in:inbox'  # Gmail query syntax
    ).execute()
```

**Key features:**
- ✅ **Polling interval**: Every 120 seconds (2 minutes)
- ✅ **Query**: `is:unread in:inbox` - only unread emails in inbox
- ✅ **Authentication**: OAuth2 credentials from `~/.gmail-mcp/credentials.json`
- ✅ **Library**: `google-api-python-client` (NOT MCP)
- ✅ **Supervision**: PM2-managed 24/7 process (`ai-employee-gmail-watcher`)
- ✅ **Output**: Creates `EMAIL_{message_id}.md` in `Needs_Action/`

**State persistence:**

Deduplication is handled via `AI_EMPLOYEE_VAULT/Logs/.gmail_processed_ids.json`:
```json
{
  "processed_ids": {
    "19ba763c95bed08c": 1768039909.562355
  },
  "last_updated": "2026-01-10T10:11:49.562553+00:00",
  "count": 1
}
```

- Tracks processed email IDs with timestamps
- Prevents duplicate processing across restarts
- Auto-prunes IDs older than 30 days to prevent unbounded growth
- Keeps max 10,000 most recent IDs in memory

**Error handling:**
- Exponential backoff: starts at 30s, maxes at 1 hour
- Special handling for OAuth credential errors (long cooldown to prevent spam)
- Graceful shutdown via SIGTERM/SIGINT handlers
- Automatic restart by PM2 on crash

### Component 2: Gmail MCP Server (Actions - Used by Claude)

The Gmail MCP server is a **separate component** that provides tools for Claude Code to take actions:

**Location:** `apps/gmail-mcp-server/src/gmail_mcp/server.py`

**When it's used:**
- ❌ **NOT** used for polling/watching
- ✅ Used when Claude needs to **send emails, reply, forward**, etc.
- ✅ Requires **human approval** (Silver tier approval workflow)
- ✅ Provides 19 MCP tools: `gmail_send_message`, `gmail_reply_to_message`, etc.

**MCP Tools available:**
```
Message Operations: list, get, send, reply, forward, trash, delete
Draft Operations: list, get, create, update, send
Label Operations: list, create, update, delete
Bulk Operations: mark_as_read, archive, modify_labels
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│ Gmail Watcher (Perception - No MCP)                 │
│ ─────────────────────────────────────               │
│ • Direct Gmail API via google-api-python-client     │
│ • Polls every 2 minutes for "is:unread in:inbox"    │
│ • Creates EMAIL_*.md in Needs_Action/               │
│ • PM2-managed 24/7 process                          │
│ • State persisted to .gmail_processed_ids.json      │
│ • NO Claude Code involvement = cheap + fast         │
└─────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│ Gmail MCP Server (Action - Used by Claude)          │
│ ─────────────────────────────────────               │
│ • MCP tools for sending/replying to email           │
│ • Invoked by Claude Code (with human approval)      │
│ • NOT used for polling                              │
│ • 19 tools: send, reply, forward, drafts, labels    │
└─────────────────────────────────────────────────────┘
```

### Why this separation?

**Benefits:**
1. **Cost efficient**: Watcher runs 24/7 without Claude API calls
2. **Low latency**: File detection happens in 2-3 seconds
3. **Resilient**: Watcher can run even if Claude Code is unavailable
4. **Clear responsibilities**: Watcher = perception, MCP = action
5. **Independent scaling**: Can adjust polling frequency without affecting Claude

**Complete flow:**
```
Gmail receives email  Watcher polls every 2 min  Creates EMAIL_*.md   Systemd timer runs
(unread in inbox)  ──▶  (Direct Gmail API)    ──▶  in Needs_Action/ ──▶  triage + execute
                                                    (instant)            (every 30 min)
                                                         │
                                                         ▼
                                           Claude analyzes email with /execute-task
                                                         │
                                                         ▼
                                           Needs to reply? Creates approval request
                                                         │
                                                         ▼
                                           Human approves ──▶ Orchestrator uses Gmail MCP
                                                         │
                                                         ▼
                                                    Email sent!
```

---

## Project Structure

```
hackathon0/
├── AI_EMPLOYEE_VAULT/          # Obsidian vault (UI + memory)
│   ├── Dashboard.md            # System status
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Inbox/                  # Raw file drops
│   ├── Needs_Action/           # Actionable items
│   ├── Plans/                  # Complex task plans (Silver)
│   ├── Pending_Approval/       # Awaiting human review (Silver)
│   ├── Approved/               # Approved actions (Silver)
│   ├── Rejected/               # Rejected requests (Silver)
│   ├── Done/                   # Completed items
│   ├── Archive/                # Old items (7+ days)
│   └── Logs/                   # Decision + process logs
│
├── apps/ai_employee/           # Python runtime
│   ├── src/ai_employee/
│   │   ├── watchers/
│   │   │   ├── filesystem_watcher.py
│   │   │   └── gmail_watcher.py     # Silver: Gmail API polling
│   │   ├── orchestrator.py          # Handles Needs_Action + Approved
│   │   ├── vault_io.py
│   │   ├── frontmatter.py           # YAML parsing
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── schemas.py
│   └── tests/
│
├── .claude/skills/             # Agent Skills (AI logic)
│   ├── triage-needs-action/
│   ├── execute-task/
│   ├── update-dashboard/
│   ├── close-item/
│   ├── create-plan/            # Silver: Complex task planning
│   └── send-email-request/     # Silver: Email draft + approval
│
├── ops/                        # Operations
│   ├── pm2/ecosystem.config.cjs
│   ├── systemd/                # Systemd timer (survives suspend)
│   │   ├── ai-employee-queue.service
│   │   ├── ai-employee-queue.timer
│   │   └── install-timer.sh
│   ├── scripts/
│   │   ├── process_queue.sh    # Triage + Execute (systemd timer)
│   │   └── archive_old.sh      # Cleanup (cron)
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

### Process Management

```bash
# Start everything from scratch
pm2 start ops/pm2/ecosystem.config.cjs
pm2 save
systemctl --user start ai-employee-queue.timer

# Restart all PM2 processes
pm2 restart all

# Restart individual processes
pm2 restart ai-employee-filesystem-watcher
pm2 restart ai-employee-gmail-watcher
pm2 restart ai-employee-orchestrator

# Stop everything
pm2 stop all
systemctl --user stop ai-employee-queue.timer

# Check process status
pm2 list
pm2 status

# View logs
pm2 logs                                      # All processes
pm2 logs ai-employee-filesystem-watcher      # Filesystem watcher
pm2 logs ai-employee-gmail-watcher --lines 50 # Gmail watcher (last 50 lines)
pm2 logs ai-employee-orchestrator            # Orchestrator
```

### Manual Processing

```bash
# Run queue processing manually (don't wait for timer)
./ops/scripts/process_queue.sh

# Run archive cleanup
./ops/scripts/archive_old.sh

# Trigger systemd service manually
systemctl --user start ai-employee-queue.service
```

### Testing & Monitoring

```bash
# Test file drop
echo "Write a poem about AI" > AI_EMPLOYEE_VAULT/Inbox/poem.txt

# Test email (send to yourself with subject/body)
# Then check: ls AI_EMPLOYEE_VAULT/Needs_Action/EMAIL_*.md

# Check vault state
ls AI_EMPLOYEE_VAULT/Inbox/
ls AI_EMPLOYEE_VAULT/Needs_Action/
ls AI_EMPLOYEE_VAULT/Done/

# View Dashboard
cat AI_EMPLOYEE_VAULT/Dashboard.md

# Check systemd timer status
systemctl --user list-timers ai-employee-queue.timer
systemctl --user status ai-employee-queue.timer

# View timer logs
journalctl --user -u ai-employee-queue.service -f
journalctl --user -u ai-employee-queue.service --since "1 hour ago"

# View processing logs
tail -f AI_EMPLOYEE_VAULT/Logs/process-queue.log
tail -f AI_EMPLOYEE_VAULT/Logs/cron.log
tail -f AI_EMPLOYEE_VAULT/Logs/orchestrator-$(date +%Y-%m-%d).log
```

### System Health Check

```bash
# One-command health check
pm2 list && \
systemctl --user list-timers ai-employee-queue.timer && \
echo "=== Dashboard ===" && \
cat AI_EMPLOYEE_VAULT/Dashboard.md
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
# Check systemd timer is active
systemctl --user list-timers ai-employee-queue.timer

# Check service logs
journalctl --user -u ai-employee-queue.service --since "1 hour ago"

# Check processing logs
cat AI_EMPLOYEE_VAULT/Logs/process-queue.log

# Run manually to test
systemctl --user start ai-employee-queue.service
# OR
./ops/scripts/process_queue.sh
```

### Emails not sending from approved folder
```bash
# Check orchestrator logs
pm2 logs ai-employee-orchestrator --lines 50

# Check action log for errors
cat AI_EMPLOYEE_VAULT/Logs/$(date +%Y-%m-%d)-actions.json

# Common issues:
# 1. MCP permissions - orchestrator uses --dangerously-skip-permissions (safe, approval already granted)
# 2. Gmail API credentials - check ~/.gmail-mcp/credentials.json exists
# 3. MCP server not running - verify: claude mcp list

# Test Gmail MCP manually:
claude --dangerously-skip-permissions -p "Use mcp__gmail__gmail_send_message to send test email to your-email@example.com"
```

### PM2 processes keep restarting
```bash
pm2 logs --err --lines 50
```

### Check system health
```bash
pm2 status
systemctl --user list-timers ai-employee-queue.timer
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

## Systemd Timer Setup

The main queue processor uses **systemd timers** instead of cron because:
- Systemd timers with `Persistent=true` catch up on missed runs after suspend/sleep
- Cron does NOT run missed jobs after system wake

### Timer Files (Already Installed)

Located at `~/.config/systemd/user/`:
- `ai-employee-queue.timer` - Triggers every 30 minutes
- `ai-employee-queue.service` - Runs process_queue.sh

### Useful Commands

```bash
# Check timer status and next run
systemctl --user list-timers ai-employee-queue.timer

# View service logs
journalctl --user -u ai-employee-queue.service -f

# Manual trigger
systemctl --user start ai-employee-queue.service

# Reinstall timer (if needed)
./ops/systemd/install-timer.sh
```

### Enable Persistence After Logout

To ensure the timer runs even when logged out:
```bash
sudo loginctl enable-linger $USER
```

### Archive Cron Job

The daily archive job still uses cron (fine for daily tasks):
```cron
0 0 * * * /home/salim/Desktop/hackathon0/ops/scripts/archive_old.sh
```

To verify: `crontab -l`

---

## More Documentation

- [Pro Plan Usage Guide](docs/PRO_PLAN_USAGE.md)
- [PM2 Runbook](ops/runbooks/pm2.md)
- [Company Handbook](AI_EMPLOYEE_VAULT/Company_Handbook.md)
- [Hackathon Spec](docs/Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
