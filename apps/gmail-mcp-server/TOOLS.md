# Gmail MCP Server - Complete Tool Reference

## Tool Summary

| Tool | Read-Only | Destructive | Idempotent | Open World |
|------|-----------|-------------|------------|------------|
| gmail_list_messages | ✓ | ✗ | ✓ | ✓ |
| gmail_get_message | ✓ | ✗ | ✓ | ✓ |
| gmail_send_message | ✗ | ✗ | ✗ | ✓ |
| gmail_reply_to_message | ✗ | ✗ | ✗ | ✓ |
| gmail_forward_message | ✗ | ✗ | ✗ | ✓ |
| gmail_modify_labels | ✗ | ✗ | ✓ | ✗ |
| gmail_trash_message | ✗ | ✓ | ✓ | ✗ |
| gmail_delete_message | ✗ | ✓ | ✗ | ✗ |
| gmail_list_drafts | ✓ | ✗ | ✓ | ✗ |
| gmail_get_draft | ✓ | ✗ | ✓ | ✗ |
| gmail_create_draft | ✗ | ✗ | ✗ | ✗ |
| gmail_update_draft | ✗ | ✗ | ✓ | ✗ |
| gmail_send_draft | ✗ | ✗ | ✗ | ✓ |
| gmail_list_labels | ✓ | ✗ | ✓ | ✗ |
| gmail_create_label | ✗ | ✗ | ✗ | ✗ |
| gmail_update_label | ✗ | ✗ | ✓ | ✗ |
| gmail_delete_label | ✗ | ✓ | ✗ | ✗ |
| gmail_mark_as_read | ✗ | ✗ | ✓ | ✗ |
| gmail_archive_messages | ✗ | ✗ | ✓ | ✗ |

**Total**: 19 tools covering all essential Gmail operations

---

## Detailed Tool Documentation

### 1. gmail_list_messages

**Purpose**: Search and list Gmail messages using Gmail query syntax

**Parameters**:
- `query` (string, optional): Gmail search query (default: "")
- `limit` (integer, optional): Max results 1-100 (default: 20)
- `include_spam_trash` (boolean, optional): Include SPAM/TRASH (default: false)
- `response_format` (enum, optional): "markdown" or "json" (default: "markdown")

**Query Syntax Examples**:
```
"is:unread"                                    # All unread messages
"from:user@example.com after:2026/01/01"      # Messages from user after date
"has:attachment subject:invoice"               # Messages with attachments about invoices
"label:important is:unread"                    # Important unread messages
"to:me cc:manager@company.com"                 # Messages to me CC'd to manager
"-label:inbox"                                  # NOT in inbox (archived)
```

**Use Cases**:
- Finding unread mail
- Searching by sender, recipient, date
- Locating messages by content or labels
- Filtering messages with attachments

**Returns**: List of messages with previews (markdown) or structured data (JSON)

---

### 2. gmail_get_message

**Purpose**: Get full details of a specific Gmail message

**Parameters**:
- `message_id` (string, required): Gmail message ID
- `format` (enum, optional): "full", "metadata", or "minimal" (default: "full")
- `response_format` (enum, optional): "markdown" or "json" (default: "markdown")

**Use Cases**:
- Reading complete email content
- Extracting headers and metadata
- Checking message labels and thread info

**Returns**: Complete message details including headers, body, labels, and metadata

---

### 3. gmail_send_message

**Purpose**: Send a new email message via Gmail

**Parameters**:
- `to` (array of strings, required): Recipient email addresses
- `subject` (string, required): Email subject line
- `body` (string, required): Email body content
- `cc` (array of strings, optional): CC recipients
- `bcc` (array of strings, optional): BCC recipients
- `html` (boolean, optional): Whether body is HTML (default: false)

**Use Cases**:
- Sending new emails
- Starting new conversations
- Broadcasting to multiple recipients

**Returns**: Success message with sent message ID

---

### 4. gmail_reply_to_message

**Purpose**: Reply to an existing Gmail message

**Parameters**:
- `message_id` (string, required): ID of message to reply to
- `body` (string, required): Reply body content
- `reply_all` (boolean, optional): Reply to all recipients (default: false)
- `html` (boolean, optional): Whether body is HTML (default: false)

**Use Cases**:
- Responding to emails
- Continuing conversations in threads
- Replying to multiple recipients

**Returns**: Success message with reply message ID

---

### 5. gmail_forward_message

**Purpose**: Forward an existing Gmail message to new recipients

**Parameters**:
- `message_id` (string, required): ID of message to forward
- `to` (array of strings, required): Forward recipient addresses
- `body` (string, optional): Additional message to include (default: "")

**Use Cases**:
- Sharing emails with others
- Distributing information to team
- Forwarding relevant messages

**Returns**: Success message with forwarded message ID

---

### 6. gmail_modify_labels

**Purpose**: Add or remove labels from Gmail messages

**Parameters**:
- `message_ids` (array of strings, required): List of message IDs (1-100)
- `add_labels` (array of strings, optional): Label IDs to add
- `remove_labels` (array of strings, optional): Label IDs to remove

**Common Label IDs**:
- System: `INBOX`, `UNREAD`, `STARRED`, `IMPORTANT`, `SENT`, `DRAFT`, `SPAM`, `TRASH`
- Custom: `Label_xxx` (get from gmail_list_labels)

**Use Cases**:
- Organizing messages
- Marking messages as important/starred
- Moving messages to/from inbox
- Categorizing emails

**Returns**: Success message with count of modified messages

---

### 7. gmail_trash_message

**Purpose**: Move a Gmail message to trash

**Parameters**:
- `message_id` (string, required): Message ID to trash

**Use Cases**:
- Removing unwanted messages
- Cleaning up inbox
- Deleting with recovery option (30 days)

**Returns**: Success message with trashed message ID

**Note**: Messages can be recovered from trash within 30 days

---

### 8. gmail_delete_message

**Purpose**: Permanently delete a Gmail message (CANNOT BE UNDONE)

**Parameters**:
- `message_id` (string, required): Message ID to delete permanently

**Use Cases**:
- Permanently removing sensitive messages
- Complying with data deletion requirements
- Removing information that cannot be recovered

**Returns**: Success message

**Warning**: This operation is permanent and irreversible

---

### 9. gmail_list_drafts

**Purpose**: List all Gmail draft messages

**Parameters**:
- `limit` (integer, optional): Max results 1-100 (default: 20)
- `response_format` (enum, optional): "markdown" or "json" (default: "markdown")

**Use Cases**:
- Viewing saved drafts
- Finding draft to edit or send
- Managing unsent emails

**Returns**: List of drafts with previews

---

### 10. gmail_get_draft

**Purpose**: Get full details of a specific Gmail draft

**Parameters**:
- `draft_id` (string, required): Draft ID
- `response_format` (enum, optional): "markdown" or "json" (default: "markdown")

**Use Cases**:
- Reading draft content before sending
- Getting draft ID for updates
- Reviewing unsent emails

**Returns**: Complete draft details

---

### 11. gmail_create_draft

**Purpose**: Create a new Gmail draft message

**Parameters**:
- `to` (array of strings, required): Recipient addresses
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `cc` (array of strings, optional): CC recipients
- `bcc` (array of strings, optional): BCC recipients
- `html` (boolean, optional): Whether body is HTML (default: false)

**Use Cases**:
- Composing emails for later review
- Preparing emails for scheduled sending
- Creating email templates

**Returns**: Success message with draft ID

---

### 12. gmail_update_draft

**Purpose**: Update an existing Gmail draft message

**Parameters**:
- `draft_id` (string, required): Draft ID to update
- `to` (array of strings, required): Recipient addresses
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `cc` (array of strings, optional): CC recipients
- `bcc` (array of strings, optional): BCC recipients
- `html` (boolean, optional): Whether body is HTML (default: false)

**Use Cases**:
- Editing draft content
- Changing recipients or subject
- Revising message before sending

**Returns**: Success message with draft ID

---

### 13. gmail_send_draft

**Purpose**: Send an existing Gmail draft message

**Parameters**:
- `draft_id` (string, required): Draft ID to send

**Use Cases**:
- Sending prepared drafts
- Completing and sending saved emails
- Sending reviewed messages

**Returns**: Success message with sent message ID

---

### 14. gmail_list_labels

**Purpose**: List all Gmail labels (system and user-created)

**Parameters**:
- `response_format` (enum, optional): "markdown" or "json" (default: "markdown")

**System Labels**: INBOX, UNREAD, STARRED, IMPORTANT, SENT, DRAFT, SPAM, TRASH, CATEGORY_*

**Use Cases**:
- Finding label IDs for other operations
- Discovering available organization categories
- Listing custom labels

**Returns**: List of all labels with IDs and types

---

### 15. gmail_create_label

**Purpose**: Create a new Gmail label

**Parameters**:
- `name` (string, required): Label name
- `label_list_visibility` (enum, optional): "labelShow", "labelShowIfUnread", or "labelHide" (default: "labelShow")
- `message_list_visibility` (enum, optional): "show" or "hide" (default: "show")

**Use Cases**:
- Creating custom organization categories
- Setting up project-specific labels
- Creating tags for filtering

**Returns**: Success message with label ID

---

### 16. gmail_update_label

**Purpose**: Update an existing Gmail label's properties

**Parameters**:
- `label_id` (string, required): Label ID to update
- `name` (string, optional): New label name
- `label_list_visibility` (enum, optional): Label list visibility
- `message_list_visibility` (enum, optional): Message list visibility

**Use Cases**:
- Renaming labels
- Changing label visibility
- Updating organization structure

**Returns**: Success message with updated label name and ID

---

### 17. gmail_delete_label

**Purpose**: Delete a Gmail label

**Parameters**:
- `label_id` (string, required): Label ID to delete

**Use Cases**:
- Removing unused labels
- Cleaning up label organization
- Removing obsolete categories

**Returns**: Success message

**Note**: Cannot delete system labels; messages are not deleted, only the label

---

### 18. gmail_mark_as_read

**Purpose**: Mark Gmail messages as read or unread

**Parameters**:
- `message_ids` (array of strings, required): List of message IDs (1-100)
- `read` (boolean, required): True to mark read, False to mark unread

**Use Cases**:
- Marking messages as read after processing
- Flagging messages as unread for later attention
- Batch updating read status

**Returns**: Success message with count of modified messages

---

### 19. gmail_archive_messages

**Purpose**: Archive Gmail messages (remove from inbox)

**Parameters**:
- `message_ids` (array of strings, required): List of message IDs to archive (1-100)

**Use Cases**:
- Cleaning up inbox while keeping messages
- Organizing processed emails
- Decluttering without deleting

**Returns**: Success message with count of archived messages

**Note**: Messages remain accessible via search and "All Mail" but removed from inbox

---

## Error Handling

All tools return clear, actionable error messages:

### Common Errors

**401 - Authentication Failed**
```
Error: Authentication failed.

Your credentials may have expired. Run: gmail-mcp --auth
```

**404 - Not Found**
```
Error: Resource not found.

The message, draft, or label ID may be invalid or deleted.
```

**429 - Rate Limit**
```
Error: Rate limit exceeded.

Too many requests. Please wait a moment and try again.
```

**403 - Permission Denied**
```
Error: Permission denied - {reason}

You may not have access to this resource or operation.
```

### Gmail API Rate Limits

- 250 quota units per user per second
- 1 billion quota units per day
- Sending: 100 emails/day (new accounts), 2000/day (established accounts)

---

## Advanced Usage Tips

### 1. Complex Queries

Combine multiple Gmail search operators:

```
from:boss@company.com (is:important OR has:attachment) after:2026/01/01 -label:inbox
```

### 2. Batch Operations

Process multiple messages efficiently:

```python
# Get IDs from search
message_ids = get_messages_from_search()

# Batch mark as read
gmail_mark_as_read(message_ids=message_ids, read=True)

# Batch archive
gmail_archive_messages(message_ids=message_ids)
```

### 3. Label Management

Create organizational hierarchy:

```python
# Create project labels
gmail_create_label(name="Project/Alpha")
gmail_create_label(name="Project/Beta")
gmail_create_label(name="Project/Archive")

# Apply to messages
gmail_modify_labels(
    message_ids=[...],
    add_labels=["Label_xxx"],  # Get ID from list_labels
    remove_labels=["INBOX"]
)
```

### 4. Draft Workflows

Prepare and review emails:

```python
# Create draft for review
draft = gmail_create_draft(
    to=["team@company.com"],
    subject="Weekly Update",
    body="..."
)

# Review and update
gmail_update_draft(
    draft_id=draft_id,
    body="Updated content..."
)

# Send when ready
gmail_send_draft(draft_id=draft_id)
```

---

## Output Formats

### Markdown Format (Default)

Human-readable with formatting:
- Headers and sections
- Bullet points and lists
- Truncated previews (200 chars)
- Human-readable timestamps
- Display names with IDs

### JSON Format

Machine-readable structured data:
- Complete field data
- All metadata included
- Consistent field names
- Suitable for parsing and processing

Example:

```json
{
  "total": 5,
  "messages": [
    {
      "id": "18d1234567890",
      "threadId": "18d1234567890",
      "subject": "Meeting follow-up",
      "from": "user@example.com",
      "to": "me@company.com",
      "date": "2026-01-09T10:30:00Z",
      "snippet": "Thanks for the meeting...",
      "labels": ["INBOX", "UNREAD"]
    }
  ]
}
```
