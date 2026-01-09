# Gmail MCP Server - Quick Start Guide

**5-Minute Setup for Claude Code Integration**

---

## Prerequisites Check

```bash
# 1. Verify Python version
python3 --version
# Should be 3.10 or higher

# 2. Verify uv is installed
uv --version

# 3. Verify you have Gmail OAuth credentials
ls ~/.gmail-mcp/oauth-credentials.json
# OR
ls /home/salim/Desktop/hackathon0/gcp-oauth.keys.json
```

---

## Step 1: Install Dependencies (30 seconds)

```bash
cd /home/salim/Desktop/hackathon0/apps/gmail-mcp-server
uv sync
```

**Expected output:**
```
✓ Installed 49 packages
```

---

## Step 2: Authenticate (1 minute)

```bash
# Run authentication flow
uv run gmail-mcp --auth
```

**What happens:**
1. Opens browser for Google authentication
2. You authorize Gmail access
3. Credentials saved to `~/.gmail-mcp/credentials.json`
4. Returns to terminal

**Verify:**
```bash
uv run gmail-mcp --check-auth
```

**Expected output:**
```
✓ Credentials found: /home/salim/.gmail-mcp/credentials.json
✓ Credentials are valid
```

---

## Step 3: Configure Claude Code (1 minute)

Create or edit `~/.config/claude/mcp.json`:

```bash
mkdir -p ~/.config/claude
cat > ~/.config/claude/mcp.json << 'EOF'
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/salim/Desktop/hackathon0/apps/gmail-mcp-server",
        "gmail-mcp"
      ]
    }
  }
}
EOF
```

**Verify:**
```bash
cat ~/.config/claude/mcp.json
```

---

## Step 4: Test Integration (2 minutes)

### Test 1: List Available Tools

```bash
claude "List all available gmail tools"
```

**Expected output:**
Should list all 19 Gmail tools (gmail_list_messages, gmail_send_message, etc.)

### Test 2: Search Your Email

```bash
claude "Use gmail to list my 5 most recent unread emails"
```

**Expected output:**
Markdown-formatted list of your recent unread messages

### Test 3: Send a Test Email

```bash
claude "Use gmail to send a test email to yourself at YOUR_EMAIL@gmail.com with subject 'MCP Test' and body 'This is a test from Gmail MCP Server'"
```

**Expected output:**
```
✓ Email sent successfully!
- Message ID: `18d...`
- Thread ID: `18d...`
```

---

## Common Usage Examples

### Search Emails

```bash
# Find unread messages
claude "Use gmail to show my unread messages"

# Search by sender
claude "Use gmail to find all emails from boss@company.com from this week"

# Complex search
claude "Use gmail to find messages with attachments from the last 3 days that are important"
```

### Send Emails

```bash
# Simple send
claude "Use gmail to send an email to team@company.com with subject 'Meeting Notes' and body 'Here are today's action items...'"

# With CC
claude "Use gmail to send an email to user@example.com, CC manager@company.com, subject 'Project Update', body 'Status report...'"
```

### Manage Drafts

```bash
# Create draft
claude "Use gmail to create a draft email to client@example.com about the Q1 proposal"

# List drafts
claude "Use gmail to show all my draft emails"

# Send draft (after getting draft ID)
claude "Use gmail to send draft ID draft_abc123"
```

### Organize Inbox

```bash
# Mark as read
claude "Use gmail to mark all messages from newsletter@company.com as read"

# Archive
claude "Use gmail to archive all messages older than 30 days"

# Apply labels
claude "Use gmail to add the Important label to unread messages from my boss"
```

---

## Troubleshooting

### Problem: "No credentials found"

**Solution:**
```bash
uv run gmail-mcp --auth
```

### Problem: "Authentication failed"

**Solution:**
```bash
# Re-authenticate
rm ~/.gmail-mcp/credentials.json
uv run gmail-mcp --auth
```

### Problem: "Gmail API error"

**Solutions:**
1. Check Gmail API is enabled in Google Cloud Console
2. Verify OAuth credentials are valid
3. Check rate limits (250/sec, 1B/day)

### Problem: Claude doesn't see gmail tools

**Solutions:**
1. Verify mcp.json configuration:
   ```bash
   cat ~/.config/claude/mcp.json
   ```

2. Check server starts:
   ```bash
   uv run gmail-mcp --help
   ```

3. Restart Claude Code CLI

---

## Integration with Orchestrator

### Orchestrator Setup

1. **Add to PM2 ecosystem** (if needed as daemon):
   ```javascript
   // ops/pm2/ecosystem.config.cjs
   {
     name: "gmail-mcp-server",
     script: "uv",
     args: ["run", "gmail-mcp"],
     cwd: "/home/salim/Desktop/hackathon0/apps/gmail-mcp-server",
     autorestart: false,  // Claude spawns as needed
   }
   ```

2. **Orchestrator calls Claude**:
   ```python
   # In orchestrator.py
   import subprocess

   result = subprocess.run(
       ['claude', '-p', 'Use gmail to send email to user@example.com...'],
       capture_output=True,
       text=True,
       timeout=60
   )
   ```

### Approval Workflow

**File**: `Pending_Approval/EMAIL_REPLY_abc123.md`

```markdown
---
type: approval_request
action: send_email
to: client@example.com
subject: Re: Your inquiry
status: pending
---

# Email Send Approval Request

## To Approve
Move this file to `Approved/` folder.

## Email Body
Dear Client,

Thank you for your inquiry...
```

**After approval**, orchestrator executes:
```python
metadata = parse_yaml_frontmatter(approval_file)
body = extract_body(approval_file)

subprocess.run([
    'claude', '-p',
    f'Use gmail to send email to {metadata["to"]} '
    f'with subject "{metadata["subject"]}" and body: {body}'
])
```

---

## Performance Tips

### 1. Batch Operations

Instead of:
```bash
# Slow: Individual operations
claude "Use gmail to mark message1 as read"
claude "Use gmail to mark message2 as read"
```

Do:
```bash
# Fast: Batch operation
claude "Use gmail to mark messages [id1, id2, id3] as read"
```

### 2. Use Limits

```bash
# Default: 20 messages
claude "Use gmail to list unread messages"

# Faster: Get just what you need
claude "Use gmail to list 5 most recent unread messages"
```

### 3. Search Before Bulk Actions

```bash
# Get IDs first
claude "Use gmail to find all newsletter messages and return JSON"

# Then batch process
claude "Use gmail to archive these message IDs: [list]"
```

---

## Advanced Configuration

### Custom Credential Location

Set environment variable:
```bash
export GMAIL_OAUTH_CONFIG=/custom/path/to/credentials.json
uv run gmail-mcp --auth
```

### Multiple Accounts

Use different credential files:
```json
{
  "mcpServers": {
    "gmail-work": {
      "command": "uv",
      "args": ["run", "gmail-mcp"],
      "env": {
        "GMAIL_OAUTH_CONFIG": "/path/to/work-credentials.json"
      }
    },
    "gmail-personal": {
      "command": "uv",
      "args": ["run", "gmail-mcp"],
      "env": {
        "GMAIL_OAUTH_CONFIG": "/path/to/personal-credentials.json"
      }
    }
  }
}
```

### Debug Mode

Enable debug logging:
```bash
# Add to mcp.json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": ["run", "gmail-mcp"],
      "env": {
        "GMAIL_MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

---

## Next Steps

1. ✅ **You're ready to use Gmail MCP!**

2. **Explore all tools**:
   ```bash
   cat TOOLS.md
   ```

3. **Review examples**:
   ```bash
   cat examples/usage_examples.md
   ```

4. **Integrate with orchestrator**:
   - Test approval workflow
   - Add to systemd/PM2
   - Monitor logs

5. **Customize for your needs**:
   - Add custom tools
   - Extend formatters
   - Implement caching

---

## Getting Help

- **Documentation**: See README.md and TOOLS.md
- **Examples**: See examples/usage_examples.md
- **Issues**: Check IMPLEMENTATION_SUMMARY.md troubleshooting
- **Source**: Review src/gmail_mcp/ code with inline comments

---

## Success Checklist

- [ ] Dependencies installed (`uv sync`)
- [ ] Authenticated (`--check-auth` passes)
- [ ] Claude Code configured (mcp.json exists)
- [ ] Can list tools (`claude "List gmail tools"`)
- [ ] Can search email (`claude "Use gmail to list unread"`)
- [ ] Can send email (`claude "Use gmail to send test"`)
- [ ] Orchestrator integration tested (if applicable)

**All checked?** 🎉 **You're ready for Silver tier!**
