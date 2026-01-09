# Gmail MCP Server - Usage Examples

## Basic Operations

### List Recent Unread Messages

```bash
claude "Use gmail to list my unread messages"
```

### Get Full Message Content

```bash
claude "Use gmail to get the full content of message ID abc123xyz"
```

### Send an Email

```bash
claude "Use gmail to send an email to user@example.com with subject 'Meeting Follow-up' and body 'Thanks for the meeting today. Here are the action items we discussed...'"
```

### Reply to an Email

```bash
claude "Use gmail to reply to message ID abc123 with 'Thank you for the information. I'll review and get back to you by Friday.'"
```

## Advanced Search

### Find Messages from Specific Sender

```bash
claude "Use gmail to find all messages from boss@company.com from the last week"
```

### Search with Attachments

```bash
claude "Use gmail to find messages with attachments containing 'invoice' in the subject"
```

### Complex Query

```bash
claude "Use gmail to search for unread messages from manager@company.com after January 1st 2026 that have attachments"
```

## Draft Management

### Create a Draft

```bash
claude "Use gmail to create a draft email to team@company.com about the Q1 planning meeting"
```

### List All Drafts

```bash
claude "Use gmail to show me all my draft emails"
```

### Send a Draft

```bash
claude "Use gmail to send draft ID draft_abc123"
```

## Organization

### Mark Messages as Read

```bash
claude "Use gmail to mark these message IDs as read: msg1, msg2, msg3"
```

### Archive Messages

```bash
claude "Use gmail to archive all messages from newsletter@company.com"
```

### Apply Labels

```bash
claude "Use gmail to add the 'Important' label to message abc123"
```

## Label Management

### List All Labels

```bash
claude "Use gmail to list all my labels"
```

### Create New Label

```bash
claude "Use gmail to create a new label called 'Project Alpha'"
```

### Delete Label

```bash
claude "Use gmail to delete the label 'Old Project'"
```

## Workflow Examples

### Process Inbox

```bash
claude "Use gmail to:
1. List my unread messages
2. For each message from high-priority senders, mark as important
3. Archive all newsletter messages
4. Show me a summary of what needs my attention"
```

### Email Triage

```bash
claude "Use gmail to:
1. Find all unread emails from the last 24 hours
2. Categorize them by sender domain
3. Create drafts responding to any that are from clients
4. Archive the rest"
```

### Cleanup Campaign

```bash
claude "Use gmail to:
1. Find all messages older than 6 months in my inbox
2. Archive messages from automated systems
3. Create a 'Review' label for messages from people
4. Show me statistics on what was cleaned up"
```

## Integration with Orchestrator

### Approval Workflow

When the orchestrator creates an approval request:

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Re: Your inquiry
created_at: 2026-01-09T10:00:00Z
status: pending
---

# Email Send Approval Request

## Details
- **To**: client@example.com
- **Subject**: Re: Your inquiry about services

## Email Body
Hi John,

Thank you for your inquiry about our services...

Best regards,
Your Name

## To Approve
Move this file to `Approved/` folder.
```

After approval, orchestrator executes:

```python
import subprocess

result = subprocess.run(
    ['claude', '-p', 'Use gmail to send email to client@example.com with subject "Re: Your inquiry" and read the body from the approval file'],
    capture_output=True
)
```

## Tips

1. **Use Natural Language**: Claude understands natural requests like "find my important unread emails" or "send a thank you to the team"

2. **Be Specific with IDs**: When working with specific messages, always use the full message ID from previous queries

3. **Batch Operations**: You can perform multiple operations in one request for efficiency

4. **Error Handling**: If an operation fails, Claude will provide actionable error messages with suggestions

5. **Search Syntax**: Gmail's advanced search syntax works:
   - `from:user@example.com`
   - `to:me`
   - `subject:invoice`
   - `has:attachment`
   - `is:unread`
   - `after:2026/01/01`
   - `before:2026/12/31`
   - `-label:inbox` (NOT operator)

6. **Label IDs**: System labels use ALL CAPS (INBOX, UNREAD, STARRED). Custom labels use Label_xxx format. Use `gmail_list_labels` to find exact IDs.
