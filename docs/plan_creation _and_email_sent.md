Plan: Email-Triggered Plan Creation and Response Test

 Objective

 Design and test the complete Silver tier workflow: incoming email → plan creation → email response, demonstrating the full
 autonomous processing pipeline with human-in-the-loop approvals.

 Context

 The user wants to test the Silver tier email integration where:
 1. An email arrives and creates EMAIL_*.md in Needs_Action/
 2. The system detects this requires a complex response → creates a plan
 3. The plan includes an email send step → creates approval request
 4. Human approves → email gets sent via Gmail MCP

 From exploration:
 - Gmail Watcher: Polls every 120s for is:unread is:important emails
 - create-plan skill: Triggers for multi-step tasks requiring external actions
 - send-email-request skill: Creates approval files in Pending_Approval/
 - ApprovedActionHandler: Executes approved actions via Claude CLI + Gmail MCP
 - Rate limits: 10 emails/hour, 50/day
 - Current mode: Queue mode (Pro plan) - manual triage required

 Test Email Design

 Test Email Specifications

 Recommended Test Email to Send:

 From: Your test email account (e.g., hamzasaleem15793@gmail.com)
 To: Your Gmail account configured with the watcher
 Subject: Request: Q1 2026 Customer Onboarding Process Analysis
 Priority: Important (⭐ mark as important in Gmail)

 Email Body:
 ---
 Hi AI Employee,

 I need your help with a comprehensive analysis of our customer onboarding process for Q1 2026.

 Please analyze our current onboarding workflow and provide:

 1. A detailed assessment of the current process (based on Company_Handbook.md)
 2. Identification of bottlenecks or inefficiencies
 3. Recommendations for improvements with specific action items
 4. A proposed timeline for implementing these changes
 5. Email me back with a summary of your findings and next steps

 This is time-sensitive for our upcoming strategy meeting next week.

 Thanks,
 [Your Name]
 ---

 Why this email will trigger plan creation:
 1. ✅ Multi-step requirement (5 distinct tasks listed)
 2. ✅ Requires external action (email response requested explicitly)
 3. ✅ Complex analysis (needs to read Company_Handbook, analyze processes)
 4. ✅ Explicit request for email reply ("Email me back...")
 5. ✅ Time-sensitive (creates urgency/priority)

 Alternative Test Email (Simpler)

 If you want a lighter test:

 Subject: Quick question: What are our email approval policies?

 Hi,

 Can you review our Company Handbook and send me a summary of:
 - Email approval workflow
 - Rate limits for email sending
 - Who needs to approve what

 Please email me back with a concise summary.

 Thanks!

 This is simpler but still triggers:
 - Plan creation (research + email send)
 - Approval workflow
 - Email response

 Expected Processing Flow

 Phase 1: Email Detection (Automated - 24/7)

 Trigger: Send test email to your Gmail account, mark as important

 Watcher Action (within 2 minutes):
 Gmail Watcher detects new email
   ↓
 Creates: AI_EMPLOYEE_VAULT/Needs_Action/EMAIL_{message_id}.md
   ↓
 File structure:
 ---
 type: email
 email_id: {16-char hex Gmail ID}
 from: hamzasaleem15793@gmail.com
 subject: Request: Q1 2026 Customer Onboarding Process Analysis
 received: {ISO timestamp}
 priority: high
 status: pending
 ---

 # Email from Gmail

 **From**: hamzasaleem15793@gmail.com
 **Subject**: Request: Q1 2026 Customer Onboarding Process Analysis
 **Date**: {email date}

 ## Email Content
 {email snippet from Gmail}

 ## Suggested Actions
 - [ ] Read full email
 - [ ] Reply to sender
 - [ ] Forward to relevant party
 - [ ] Archive after processing

 Verification: Check AI_EMPLOYEE_VAULT/Needs_Action/ for new EMAIL_*.md file

 Phase 2: Triage (Manual - Pro Plan Mode)

 Since orchestrator is in queue mode, you need to manually trigger triage:

 Option A - Using triage script:
 ./ops/scripts/triage_now.sh

 Option B - Using Claude CLI directly:
 cd /home/salim/Desktop/hackathon0
 claude -p "/triage-needs-action"

 Expected Outcome:
 - Email classified as type: email
 - Priority confirmed as high
 - Status updated to in_progress
 - Dashboard.md updated with new item count
 - Decision logged to Logs/decisions-{date}.md

 Phase 3: Plan Creation (Triggered by execute-task or create-plan skill)

 Manual Trigger:
 claude -p "/execute-task Read AI_EMPLOYEE_VAULT/Needs_Action/EMAIL_{message_id}.md and execute the task"

 Expected Outcome: Plan file created at AI_EMPLOYEE_VAULT/Plans/PLAN_EMAIL_{message_id}.md

 Expected Plan Structure:
 ---
 type: plan
 created_at: {ISO timestamp}
 source_item: EMAIL_{message_id}.md
 status: in_progress
 priority: high
 requires_external_action: true
 ---

 # Plan: Q1 2026 Customer Onboarding Process Analysis

 ## Objective
 Analyze current customer onboarding process and provide comprehensive recommendations via email response.

 ## Context
 Email request from {sender} asking for:
 - Process assessment
 - Bottleneck identification
 - Improvement recommendations
 - Implementation timeline
 - Email summary of findings

 ## Steps

 ### Research Phase
 - [ ] Read AI_EMPLOYEE_VAULT/Company_Handbook.md for current onboarding policies
 - [ ] Review Dashboard.md for current system state
 - [ ] Identify documented onboarding workflows

 ### Analysis Phase
 - [ ] Document current onboarding process flow
 - [ ] Identify bottlenecks and inefficiencies
 - [ ] Generate improvement recommendations
 - [ ] Create proposed timeline for implementation

 ### Response Phase
 - [ ] Draft comprehensive email response with findings
 - [ ] Create approval request for email send (REQUIRES HUMAN APPROVAL)
 - [ ] See: `Pending_Approval/EMAIL_REPLY_{message_id}_{timestamp}.md`

 ## External Actions Required

 **Email Send Approval**:
 - **To**: hamzasaleem15793@gmail.com
 - **Type**: Reply to EMAIL_{message_id}.md
 - **Approval File**: `Pending_Approval/EMAIL_REPLY_{message_id}_{timestamp}.md`
 - **Reason**: User explicitly requested email response with findings

 ## Expected Outcome
 Comprehensive analysis delivered via email including:
 - Current process assessment
 - Bottleneck analysis
 - Actionable recommendations
 - Implementation timeline

 ## Dependencies
 - Access to Company_Handbook.md (available)
 - Gmail MCP configured (available)
 - Human approval for email send (required by policy)

 Verification: Check AI_EMPLOYEE_VAULT/Plans/ folder for PLAN_EMAIL_*.md

 Phase 4: Email Draft Creation (Part of Plan Execution)

 When execute-task processes the plan and reaches the "Response Phase" step, it will call send-email-request skill.

 Expected Outcome: Approval file created at AI_EMPLOYEE_VAULT/Pending_Approval/EMAIL_REPLY_{message_id}_{timestamp}.md

 Expected Approval File Structure:
 ---
 type: approval_request
 action: send_email
 to: hamzasaleem15793@gmail.com
 subject: Re: Request: Q1 2026 Customer Onboarding Process Analysis
 created_at: {ISO timestamp}
 expires_at: {ISO timestamp + 24 hours}
 status: pending
 priority: high
 source: EMAIL_{message_id}.md
 email_id: {Gmail message ID for reply threading}
 ---

 # Email Send Approval Request

 ## Details
 - **To**: hamzasaleem15793@gmail.com
 - **Subject**: Re: Request: Q1 2026 Customer Onboarding Process Analysis
 - **Type**: reply
 - **Context**: Responding to analysis request with comprehensive findings

 ## Email Body

 Hi [Name],

 Thank you for your request regarding Q1 2026 customer onboarding process analysis.

 Based on my review of our Company Handbook and current system state, here's a comprehensive analysis:

 **Current Process Assessment:**
 Our onboarding workflow currently follows [describe process from Company_Handbook.md]

 **Bottlenecks Identified:**
 1. [Specific bottleneck with evidence]
 2. [Another bottleneck]

 **Recommendations:**
 1. [Specific improvement with rationale]
 2. [Another improvement]

 **Proposed Timeline:**
 - Week 1-2: [Implementation steps]
 - Week 3-4: [Next steps]

 **Next Steps:**
 I recommend we [specific action items].

 Please let me know if you need clarification on any of these points.

 Best regards,
 AI Employee

 ## Reasoning
 This response addresses all five points requested:
 1. ✓ Detailed assessment of current process
 2. ✓ Bottleneck identification
 3. ✓ Improvement recommendations with action items
 4. ✓ Proposed implementation timeline
 5. ✓ Summary of findings and next steps

 The tone is professional and actionable for the upcoming strategy meeting.

 ## Instructions for Human Review
 1. Review the email content above
 2. Check recipient, subject, and tone
 3. To **approve**: Move this file to `Approved/` folder
 4. To **reject**: Move this file to `Rejected/` folder
 5. To **edit**: Modify the email body above, then move to `Approved/`

 **Note**: This approval expires in 24 hours.

 Verification: Check AI_EMPLOYEE_VAULT/Pending_Approval/ for EMAIL_REPLY_*.md

 Phase 5: Human Approval (Manual)

 Action Required: Review and approve the draft email

 Steps:
 1. Navigate to AI_EMPLOYEE_VAULT/Pending_Approval/
 2. Open EMAIL_REPLY_{message_id}_{timestamp}.md
 3. Review the email body, tone, and content
 4. If acceptable, move the file to AI_EMPLOYEE_VAULT/Approved/

 Commands:
 cd /home/salim/Desktop/hackathon0/AI_EMPLOYEE_VAULT
 mv Pending_Approval/EMAIL_REPLY_*.md Approved/

 Alternative: Edit the email body first, then move to Approved/

 Verification: File should now be in Approved/ folder

 Phase 6: Email Execution (Automated - Orchestrator)

 Trigger: Watchdog detects new file in Approved/

 Orchestrator Action (within seconds):
 ApprovedActionHandler detects new approval file
   ↓
 Read EMAIL_REPLY_{message_id}_{timestamp}.md
   ↓
 Parse metadata: to, subject, email_id, body
   ↓
 Check rate limits (10/hr, 50/day)
   ↓
 Build Claude CLI command:
   claude --dangerously-skip-permissions -p '''
   Call mcp__gmail__gmail_reply_to_message tool NOW with:
   message_id: "{email_id}"
   body: """{email_body}"""
   reply_all: false
   '''
   ↓
 Execute subprocess (300s timeout)
   ↓
 Gmail MCP authenticates and calls Gmail API
   ↓
 Email sent via Gmail
   ↓
 Verify success (check for message ID in output)
   ↓
 Log action to Logs/{date}-actions.json
   ↓
 Update EMAIL_{message_id}.md status: done
   ↓
 Move EMAIL_{message_id}.md to Done/
   ↓
 Move EMAIL_REPLY_{message_id}_{timestamp}.md to Done/

 Verification:
 - Check your Gmail inbox for the reply
 - Check AI_EMPLOYEE_VAULT/Logs/{date}-actions.json for success log entry
 - Check AI_EMPLOYEE_VAULT/Done/ for moved files

 Phase 7: Verification (Manual)

 Check Email Sent:
 1. Open your Gmail account
 2. Find the original test email thread
 3. Verify the reply appears in the thread
 4. Check content matches the approved draft

 Check Logs:
 cat AI_EMPLOYEE_VAULT/Logs/$(date +%Y-%m-%d)-actions.json | jq '.'

 Expected log entry:
 {
   "timestamp": "{ISO timestamp}",
   "action_type": "email_send",
   "actor": "claude_code_mcp",
   "target": "hamzasaleem15793@gmail.com",
   "approval_file": "EMAIL_REPLY_{message_id}_{timestamp}.md",
   "result": "success",
   "output": "Perfect! The email reply has been sent successfully.\n\n**Confirmation:**\n- ✓ Reply sent...\n- **Message ID**:
 `{new_message_id}`..."
 }

 Check Dashboard:
 cat AI_EMPLOYEE_VAULT/Dashboard.md

 Should show updated counts and recent activity.

 Critical Files to Monitor

 During Test Execution
 ┌─────────────────┬───────────────────────────────────────────┬──────────────────────────────────────────┐
 │      Stage      │               File Location               │              What to Check               │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Email Detection │ Needs_Action/EMAIL_*.md                   │ File created with correct metadata       │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Triage          │ Needs_Action/EMAIL_*.md                   │ Status updated, priority confirmed       │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Plan Creation   │ Plans/PLAN_EMAIL_*.md                     │ Plan exists with all required sections   │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Draft Creation  │ Pending_Approval/EMAIL_REPLY_*.md         │ Approval request created with email body │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Approval        │ Approved/EMAIL_REPLY_*.md                 │ File moved from Pending to Approved      │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Execution       │ Logs/{date}-actions.json                  │ Success entry logged                     │
 ├─────────────────┼───────────────────────────────────────────┼──────────────────────────────────────────┤
 │ Completion      │ Done/EMAIL_*.md and Done/EMAIL_REPLY_*.md │ Both files moved to Done                 │
 └─────────────────┴───────────────────────────────────────────┴──────────────────────────────────────────┘
 PM2 Process Logs

 Check orchestrator status:
 pm2 status ai-employee-orchestrator
 pm2 logs ai-employee-orchestrator --lines 50

 Check Gmail watcher status:
 pm2 status ai-employee-gmail-watcher
 pm2 logs ai-employee-gmail-watcher --lines 50

 Troubleshooting

 Issue: Email not detected

 - Check: PM2 process running: pm2 status ai-employee-gmail-watcher
 - Check: Email is marked as important (⭐) in Gmail
 - Check: Email is unread
 - Check: .gmail_processed_ids.json doesn't already contain this email ID
 - Fix: Restart watcher: pm2 restart ai-employee-gmail-watcher

 Issue: Plan not created

 - Check: Triage was run (/triage-needs-action or triage_now.sh)
 - Check: Email complexity (needs to be multi-step or require external action)
 - Check: execute-task was called with correct file path
 - Fix: Manually trigger: claude -p "/execute-task <path_to_email>"

 Issue: Approval file not created

 - Check: send-email-request skill was called during plan execution
 - Check: Pending_Approval/ folder exists and is writable
 - Check: No existing approval request for same source email
 - Fix: Manually trigger: claude -p "/send-email-request <source_file>"

 Issue: Email not sent

 - Check: File was moved to Approved/ (not copied)
 - Check: PM2 orchestrator is running: pm2 status ai-employee-orchestrator
 - Check: Rate limits not exceeded (10/hr, 50/day)
 - Check: Gmail MCP credentials valid: uv run --directory apps/gmail-mcp-server gmail-mcp --auth
 - Check: Logs for errors: pm2 logs ai-employee-orchestrator
 - Fix: Check {date}-actions.json for error details

 Issue: Rate limit exceeded

 - Wait: Hourly limit resets after 1 hour from first send
 - Wait: Daily limit resets at midnight UTC
 - Check: Logs/{date}-actions.json for recent send timestamps
 - Note: File stays in Approved/ and will retry when limit resets

 Success Criteria

 Test is successful when:
 - ✅ Test email detected and normalized to EMAIL_*.md within 2 minutes
 - ✅ Triage completes successfully (status updated, priority set)
 - ✅ Plan created in Plans/ folder with all required sections
 - ✅ Approval request created in Pending_Approval/ with complete email draft
 - ✅ Human approval workflow works (file moves to Approved/)
 - ✅ Email sent successfully via Gmail MCP
 - ✅ Reply appears in original Gmail thread
 - ✅ Success logged to {date}-actions.json
 - ✅ All files moved to Done/ folder
 - ✅ Dashboard.md updated with completion status
 - ✅ No errors in PM2 logs

 Post-Test Cleanup (Optional)

 If you want to reset for another test:

 # Move completed items back to Needs_Action (remove done status)
 # Edit the EMAIL_*.md file: set status: pending, remove completion timestamps

 # Clear processed email IDs to allow re-detection
 # Edit AI_EMPLOYEE_VAULT/Logs/.gmail_processed_ids.json - remove the test email ID

 # Clear action logs (backup first!)
 # mv AI_EMPLOYEE_VAULT/Logs/{date}-actions.json AI_EMPLOYEE_VAULT/Logs/backup/

 Test Timeline Estimate
 ┌─────────────────┬────────────────┬──────────────────────────────────────┐
 │      Phase      │      Time      │                Notes                 │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Send test email │ 1 minute       │ Manual                               │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Email detection │ 0-2 minutes    │ Automated (120s poll interval)       │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Triage          │ 2-3 minutes    │ Manual trigger + LLM processing      │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Plan creation   │ 3-5 minutes    │ Manual trigger + LLM analysis        │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Draft creation  │ 2-3 minutes    │ Automated during plan execution      │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Human approval  │ Variable       │ Human reviews and moves file         │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Email execution │ 10-30 seconds  │ Automated (orchestrator + Gmail MCP) │
 ├─────────────────┼────────────────┼──────────────────────────────────────┤
 │ Total           │ ~10-15 minutes │ Excluding human review time          │
 └─────────────────┴────────────────┴──────────────────────────────────────┘
 Notes

 - Pro Plan Mode: This system runs in queue mode (no API key), so triage and task execution require manual triggering
 - 24/7 Components: Gmail watcher and orchestrator run continuously via PM2
 - Human-in-the-Loop: All external actions (email sends) require explicit human approval
 - Rate Limits: System enforces 10 emails/hour, 50/day to prevent abuse
 - Audit Trail: All actions logged to {date}-actions.json for full traceability
 - Safety: No emails ever sent without human approval + file movement to Approved/
