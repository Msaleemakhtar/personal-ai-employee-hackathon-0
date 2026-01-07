# Pro Plan Usage Guide — Hybrid Autonomous Mode

This guide explains how to run the Personal AI Employee system with a **Claude Pro plan** (web-based authentication without API keys).

## Overview: Hybrid Autonomous Architecture

Since Pro plan doesn't provide API keys for headless operation, the system runs in **hybrid mode**:

### ✅ What's Autonomous (24/7)
- **Filesystem watcher**: Monitors `AI_EMPLOYEE_VAULT/Inbox/` for new files
- **Note generation**: Automatically creates structured `Needs_Action` notes
- **Queue monitoring**: Orchestrator watches for new items and logs them
- **System supervision**: PM2 ensures all processes run 24/7 and auto-restart on crash

### 🔧 What's Manual/On-Demand
- **Triage**: You run the triage script whenever you want to process the queue
- **Dashboard updates**: Happens when you run triage
- **Decision logging**: Happens when you run triage

This still achieves **Bronze tier requirements** (24/7 monitoring + detection) while respecting Pro plan constraints.

---

## Quick Start

### 1. Start the 24/7 Watchers

```bash
cd /home/salim/Desktop/hackathon0
pm2 restart all
pm2 save
```

### 2. Drop Files to Process

```bash
# Example: drop a file into Inbox
echo "Review Q4 sales data" > AI_EMPLOYEE_VAULT/Inbox/sales_review.txt
```

The watcher will automatically create a `Needs_Action` note within seconds.

### 3. Run Triage (Manual)

When you're ready to process the queue:

```bash
./ops/scripts/triage_now.sh
```

This will:
- Read all pending items in `Needs_Action/`
- Classify and prioritize them
- Update `Dashboard.md` with counts and top items
- Log decisions to `Logs/decisions-YYYY-MM-DD.md`

### 4. Check Results

Open `AI_EMPLOYEE_VAULT/Dashboard.md` in Obsidian to see the updates.

---

## Scheduling Triage (Optional)

You can schedule automatic triage at convenient times using cron:

```bash
# Edit crontab
crontab -e

# Add this line to run triage every 2 hours during work hours (9am-5pm, Mon-Fri)
0 9-17/2 * * 1-5 cd /home/salim/Desktop/hackathon0 && ./ops/scripts/triage_now.sh >> /tmp/triage.log 2>&1
```

Or create your own schedule:
```bash
# Every morning at 9am
0 9 * * * cd /home/salim/Desktop/hackathon0 && ./ops/scripts/triage_now.sh

# Every 30 minutes during the day
*/30 8-18 * * * cd /home/salim/Desktop/hackathon0 && ./ops/scripts/triage_now.sh
```

---

## Architecture Details

### Queue Mode vs Auto Mode

The system supports two modes controlled by `ORCHESTRATOR_MODE` in `.env`:

#### `queue` mode (Pro plan - default)
- Watchers detect new files → create `Needs_Action` notes
- Orchestrator logs new items but doesn't auto-triage
- You run `./ops/scripts/triage_now.sh` when ready
- No API key required

#### `auto` mode (API access users)
- Same as queue mode, but also auto-triages
- Requires `ANTHROPIC_API_KEY` in `.env`
- Fully autonomous (no manual trigger needed)

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PM2 Supervision (24/7)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌────────────────────────┐   │
│  │ Filesystem Watcher    │      │ Orchestrator           │   │
│  │                       │      │ (queue mode)           │   │
│  │ Watches: Inbox/       │──┬──>│                        │   │
│  │ Creates: Needs_Action/│  │   │ Watches: Needs_Action/ │   │
│  │                       │  │   │ Logs: new items        │   │
│  └──────────────────────┘  │   └────────────────────────┘   │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                              │ File dropped
                              │
┌─────────────────────────────┼────────────────────────────────┐
│                             │                                │
│  AI_EMPLOYEE_VAULT/         │                                │
│                             │                                │
│  ┌──────────┐       ┌───────▼─────────┐       ┌──────────┐  │
│  │  Inbox/  │──────>│ Needs_Action/   │<──────│  Done/   │  │
│  └──────────┘       └─────────────────┘       └──────────┘  │
│                             │                                │
│                             │ Manual trigger                 │
│                             │                                │
└─────────────────────────────┼────────────────────────────────┘
                              │
                              ▼
                    ./ops/scripts/triage_now.sh
                              │
                              ▼
                    Claude Code (interactive session)
                    Runs: /triage-needs-action skill
```

---

## Monitoring

### Check PM2 Status
```bash
pm2 status
pm2 logs ai-employee-orchestrator --lines 50
pm2 logs ai-employee-filesystem-watcher --lines 50
```

### Check Orchestrator Heartbeat
```bash
cat AI_EMPLOYEE_VAULT/Logs/heartbeat-orchestrator.txt
```

Shows:
- `last_run_at`: When orchestrator last saw activity
- `mode`: Current mode (queue or auto)
- `last_item`: Last file detected

### Check Orchestrator Logs
```bash
cat AI_EMPLOYEE_VAULT/Logs/orchestrator-$(date +%Y-%m-%d).log
```

---

## Upgrading to Auto Mode (Future)

If you later get API access:

1. Get your API key from: https://console.anthropic.com/settings/keys

2. Update `.env`:
   ```bash
   ORCHESTRATOR_MODE=auto
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
   ```

3. Restart PM2:
   ```bash
   pm2 restart all
   ```

The system will then auto-triage new items without manual intervention.

---

## Troubleshooting

### Watcher not detecting files
```bash
# Check if watcher is running
pm2 status | grep filesystem-watcher

# Check watcher logs
pm2 logs ai-employee-filesystem-watcher --lines 50

# Manually test
echo "test" > AI_EMPLOYEE_VAULT/Inbox/test.txt
ls -la AI_EMPLOYEE_VAULT/Needs_Action/
```

### Triage script fails
```bash
# Make sure you're running from repo root
cd /home/salim/Desktop/hackathon0

# Run with verbose output
bash -x ./ops/scripts/triage_now.sh

# Check if Claude Code is working
claude --version
```

### Dashboard not updating
- Make sure you ran `./ops/scripts/triage_now.sh` (queue mode doesn't auto-update)
- Check `AI_EMPLOYEE_VAULT/Logs/decisions-YYYY-MM-DD.md` for triage logs
- Verify Obsidian is viewing the correct vault path

---

## Demo Workflow

Complete end-to-end demo for Bronze tier:

```bash
# 1. Start PM2
pm2 restart all
pm2 status

# 2. Drop a test file
echo "Research competitor analysis tools" > AI_EMPLOYEE_VAULT/Inbox/research_task.txt

# 3. Verify watcher created the note (within seconds)
ls -la AI_EMPLOYEE_VAULT/Needs_Action/

# 4. Check orchestrator logged it
tail AI_EMPLOYEE_VAULT/Logs/orchestrator-$(date +%Y-%m-%d).log

# 5. Run manual triage
./ops/scripts/triage_now.sh

# 6. View results
cat AI_EMPLOYEE_VAULT/Dashboard.md
cat AI_EMPLOYEE_VAULT/Logs/decisions-$(date +%Y-%m-%d).md

# 7. Show PM2 is supervising 24/7
pm2 status
```

This demonstrates:
- ✅ 24/7 file monitoring (autonomous)
- ✅ Automatic note generation (autonomous)
- ✅ Queue logging (autonomous)
- ✅ Manual triage (on-demand)
- ✅ PM2 supervision (24/7 reliability)

**Bronze tier requirements met!** 🎉

---

## Next Steps (Silver Tier)

For Silver tier, you could:
- Add Gmail watcher (OAuth credentials)
- Implement approval workflow folders
- Add scheduled triage (cron integration)
- Add first MCP server (draft email capability)

But those are future enhancements. Bronze tier is complete with this hybrid setup!
