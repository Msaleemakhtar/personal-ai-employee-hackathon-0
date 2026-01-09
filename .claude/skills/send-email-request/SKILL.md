---
name: send-email-request
description: Draft an email and create approval request (NEVER send directly)
allowed-tools: Read, Write
---

# Send Email Request Skill

## Purpose
Draft email content and create a human-approval request. This skill NEVER sends emails directly - it creates approval requests that require human review before execution.

## Critical Safety Boundaries
- **MUST** create `Pending_Approval/` file for every email
- **NEVER** call MCP directly
- **NEVER** use Gmail API or external services
- **NEVER** send emails without human approval
- All email actions go through approval workflow

## When to Use This Skill
- Replying to an email in `Needs_Action/EMAIL_*.md`
- Sending a new email as part of a plan
- Forwarding information to someone
- Any outbound communication via email

## Process
1. Read the source item (usually `Needs_Action/EMAIL_*.md` or from a plan)
2. Extract context: who we're replying to, what they asked, etc.
3. Draft appropriate email response based on:
   - Original message content
   - Company_Handbook.md guidelines
   - Professional tone and clarity
4. Create approval request in `Pending_Approval/EMAIL_REPLY_{id}_{timestamp}.md`
5. Update source item: `status: awaiting_approval`, add approval reference
6. Log decision in today's decision log

## Approval File Format
```markdown
---
type: approval_request
action: send_email
to: recipient@example.com
subject: {Email subject line}
created_at: {ISO timestamp}
expires_at: {ISO timestamp - created_at + 24 hours}
status: pending
priority: normal | high | low
source: {original Needs_Action filename}
email_id: {if replying to EMAIL_*.md, include the Gmail message ID}
---

# Email Send Approval Request

## Details
- **To**: recipient@example.com
- **Subject**: {Subject line}
- **Type**: reply | new_message | forward
- **Context**: {Brief explanation of why this email is needed}

## Email Body
{Complete email draft with proper formatting}

## Reasoning
{Explain why this response is appropriate, what it accomplishes}

## Instructions for Human Review
1. Review the email content above
2. Check recipient, subject, and tone
3. To **approve**: Move this file to `Approved/` folder
4. To **reject**: Move this file to `Rejected/` folder
5. To **edit**: Modify the email body above, then move to `Approved/`

**Note**: This approval expires in 24 hours. After expiry, it will be auto-rejected.
```

## Example Scenarios

### Scenario 1: Reply to Client Inquiry
**Input**: `Needs_Action/EMAIL_abc123xyz.md` containing:
```markdown
---
type: email
email_id: abc123xyz
from: john@clientcorp.com
subject: Question about your services
---
Client is asking about our consulting rates and availability.
```

**Output**: Create `Pending_Approval/EMAIL_REPLY_abc123xyz_1736416800.md`:
```markdown
---
type: approval_request
action: send_email
to: john@clientcorp.com
subject: Re: Question about your services
created_at: 2026-01-09T12:00:00Z
expires_at: 2026-01-10T12:00:00Z
status: pending
priority: high
source: EMAIL_abc123xyz.md
email_id: abc123xyz
---

# Email Send Approval Request

## Details
- **To**: john@clientcorp.com
- **Subject**: Re: Question about your services
- **Type**: reply
- **Context**: Reply to inquiry about consulting services and rates

## Email Body
Hi John,

Thank you for your inquiry about our consulting services.

Our standard consulting rates are:
- Individual consulting: $150/hour
- Team projects: Custom pricing based on scope
- Retainer packages: Available for ongoing engagements

We currently have availability starting in Q1 2026. I'd be happy to schedule a call to discuss your specific needs and provide a detailed proposal.

Are you available for a brief call next week?

Best regards,
[Your name]

## Reasoning
This is a professional response to a business inquiry. It provides the requested information (rates), shows availability, and offers next steps (call to discuss). The tone is warm and professional, appropriate for a new prospect.

## Instructions for Human Review
1. Review the email content above
2. Check recipient, subject, and tone
3. To **approve**: Move this file to `Approved/` folder
4. To **reject**: Move this file to `Rejected/` folder
5. To **edit**: Modify the email body above, then move to `Approved/`

**Note**: This approval expires in 24 hours. After expiry, it will be auto-rejected.
```

### Scenario 2: New Email (Not a Reply)
**Input**: Plan says "Send introduction email to partner@example.org"

**Output**: Create `Pending_Approval/EMAIL_NEW_partner_1736416900.md`:
```markdown
---
type: approval_request
action: send_email
to: partner@example.org
subject: Introduction - Potential Partnership Opportunity
created_at: 2026-01-09T12:15:00Z
expires_at: 2026-01-10T12:15:00Z
status: pending
priority: normal
source: Plans/PLAN_partnership_outreach.md
email_id: null
---

# Email Send Approval Request

## Details
- **To**: partner@example.org
- **Subject**: Introduction - Potential Partnership Opportunity
- **Type**: new_message
- **Context**: Cold outreach for partnership discussion per plan

## Email Body
Hi [Partner name],

I hope this email finds you well. I'm reaching out to explore a potential partnership between our organizations.

[... email content ...]

Looking forward to connecting.

Best regards,
[Your name]

## Reasoning
This is an introductory outreach email as specified in the partnership plan. It's professional, concise, and includes a clear call-to-action.

## Instructions for Human Review
1. Review the email content above
2. Check recipient, subject, and tone
3. To **approve**: Move this file to `Approved/` folder
4. To **reject**: Move this file to `Rejected/` folder
5. To **edit**: Modify the email body above, then move to `Approved/`

**Note**: This approval expires in 24 hours. After expiry, it will be auto-rejected.
```

## Email Drafting Guidelines

### Tone and Style
- Professional but warm
- Concise and clear
- Proper greeting and sign-off
- Proofread for grammar and spelling

### Content Requirements
- Answer all questions from original email
- Include clear next steps or call-to-action
- Be specific about timelines if mentioned
- Don't make commitments outside our authority

### What NOT to Include
- Confidential information without explicit approval
- Commitments to pricing without human review
- Promises about delivery dates without verification
- Personal opinions on sensitive topics

## Priority Assignment
- **High**: Business inquiries, time-sensitive, important contacts
- **Normal**: General replies, information requests
- **Low**: Newsletters, marketing, non-urgent

## Integration with Other Skills
- **create-plan**: May call this skill as part of a larger plan
- **triage-needs-action**: Routes EMAIL_*.md items to this skill
- **Orchestrator ApprovedActionHandler**: Executes approved email via MCP

## Rate Limiting (Silver Tier)
This skill must check:
- Max 10 email approval requests per hour
- Max 50 email approval requests per day
- If limit exceeded: Create alert in Needs_Action instead

## Error Handling
- If source email doesn't exist: Create error note
- If required fields missing: Request clarification in Needs_Action
- If recipient is invalid: Flag in approval request for human review

## Post-Approval Process (Not This Skill's Job)
After human moves file to `Approved/`:
1. Orchestrator detects the approved file
2. Orchestrator calls: `claude -p "Use gmail MCP to send email from {file}"`
3. MCP executes the send
4. Result logged to `Logs/{date}-actions.json`
5. Original EMAIL_*.md marked as done
6. Approval file moved to Done/

## Success Criteria
Request is complete when:
- Approval file created in `Pending_Approval/`
- Email draft is clear, professional, and complete
- All metadata fields populated correctly
- Source item updated with approval reference
- Decision logged
