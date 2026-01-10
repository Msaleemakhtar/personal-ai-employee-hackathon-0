# AI Employee System - Debugging Summary

**Date**: 2026-01-10
**Status**: In Progress

## Issues Identified

### 1. Signal Handler Issue - ✅ FIXED
**Problem**: Orchestrator received SIGINT signals and immediately terminated with `sys.exit(0)`, interrupting ongoing email sends.

**Root Cause**:
- Signal handler at `orchestrator.py:782-788` called `sys.exit(0)` immediately
- Subprocess email sends were orphaned and killed
- PM2 auto-restarted, creating a cycle of interruptions

**Solution Implemented**:
- Added global `_shutdown_requested` flag
- Added global `_active_subprocess` tracking
- Modified signal handler to:
  - Set shutdown flag instead of immediate exit
  - Wait up to 60s for active subprocess to complete
  - Gracefully terminate if timeout exceeded
- Updated main loop to check shutdown flag periodically
- Prevented new operations when shutdown requested

**Files Modified**:
- `/home/salim/Desktop/hackathon0/apps/ai_employee/src/ai_employee/orchestrator.py`

**Result**: Orchestrator now handles SIGINT gracefully and waits for ongoing operations.

### 2. Email Send Failures - 🔄 IN PROGRESS
**Problem**: Emails fail or timeout when sent from orchestrator, but work when called manually.

**Evidence**:
- Manual test: `claude --dangerously-skip-permissions -p "Use mcp__gmail__gmail_send_message..."` works perfectly
- From orchestrator: "Email send failed - no confirmation in output"
- Action log shows timeouts and failures

**Potential Causes**:
1. Output parsing too strict (looking for hex Gmail ID pattern)
2. Environment differences between manual and subprocess calls
3. Subprocess timeout (300s) not enough for some cases
4. Rate limiting or MCP server state issues

**Next Steps**:
- Test with simplified approval file
- Add more verbose logging to capture exact Claude output
- Adjust success detection logic
- Test with shorter, simpler prompts

### 3. Stopped Watchers - ⏸️ PENDING
**Problem**: Filesystem and Gmail watchers are stopped (PM2 status shows "stopped").

**Impact**:
- Bronze tier: Files dropped in Inbox/ are not detected
- Silver tier: New emails are not detected

**Solution**: Restart watchers with PM2

### 4. File Processing Cache Issue - 🔄 INVESTIGATING
**Problem**: Orchestrator tries to process deleted files (TEST_FRESH_EMAIL.md).

**Symptoms**:
- Logs show "Found existing approval: TEST_FRESH_EMAIL.md" but file doesn't exist
- Error: "[Errno 2] No such file or directory"
- `_processed_files` cache may be persisting incorrectly

**Possible Causes**:
- Filesystem event race condition
- Cache not being properly cleared
- Glob results being cached somewhere

## System State

### Current Configuration
- **Mode**: Queue (Pro plan - manual triage)
- **Orchestrator**: Online, stable (PID 9124)
- **Filesystem Watcher**: Stopped
- **Gmail Watcher**: Stopped

### Files Status
- **Needs_Action/**: 1 file (`EMAIL_19ba763c95bed08c.md`)
- **Approved/**: 1 file (`TEST_DEBUG_EMAIL.md`)
- **Pending_Approval/**: Empty

### PM2 Status
```
ai-employee-orchestrator: online, 0 restarts since last fix
ai-employee-filesystem-watcher: stopped
ai-employee-gmail-watcher: stopped
```

## Progress Summary

### ✅ Completed
1. Identified root cause of SIGINT interruptions
2. Fixed signal handler for graceful shutdown
3. Fixed subprocess stdin/env issues causing email send failures
4. Verified orchestrator stability (no more restart loops)
5. Confirmed Gmail MCP works correctly
6. Restarted stopped watchers (filesystem and gmail)
7. Tested and verified complete Bronze tier workflow (file drop → triage → execution → Done)
8. Tested and verified complete Silver tier workflow (approval → send → Done)

### ✅ Final Resolution
**Email Send Issue**: Subprocess was hanging because stdin was not set. Adding `stdin=subprocess.DEVNULL` and `env=os.environ.copy()` to the Popen call resolved the issue. Emails now send successfully with full output capture.

**System Status**: All three tiers working correctly:
- Bronze: File processing workflow operational
- Silver: Email sending with approval workflow operational
- All processes stable and running under PM2 supervision

## Recommendations

### Immediate Actions
1. Simplify email approval file format
2. Add debug logging to capture Claude CLI output
3. Restart both watchers
4. Test with fresh approval file

### Long-term Improvements
1. Add subprocess output logging to action log
2. Implement health check for MCP server connection
3. Add retry logic with exponential backoff
4. Improve cache management to prevent stale file references
5. Add integration tests for email workflow

## Test Plan

### Bronze Tier Test
1. Start filesystem watcher
2. Drop file in Inbox/
3. Verify note created in Needs_Action/
4. Run process_queue.sh
5. Verify processing and Dashboard update

### Silver Tier Test
1. Start Gmail watcher
2. Send test email to configured address
3. Verify EMAIL_*.md created in Needs_Action/
4. Process via execute-task skill
5. Verify approval request created
6. Human approves (move to Approved/)
7. Verify orchestrator sends email
8. Verify files moved to Done/

## Notes
- The graceful shutdown fix is working well - no more interrupted email sends
- SIGINT signals have stopped appearing frequently (system is stable now)
- Gmail MCP is fully functional when called manually
- Need to identify disconnect between manual and orchestrator email sends
