# Gmail MCP Server

> Production-grade MCP server connecting Gmail to Claude Code, Claude Desktop, and any MCP client

Built with FastMCP (Python) following official MCP best practices.

## Features

### 📧 Complete Gmail API Coverage (19 Tools)

**Message Operations** (8 tools)
- List, get, send, reply, forward messages
- Modify labels, trash, and permanently delete
- Full Gmail search query syntax support

**Draft Management** (5 tools)
- List, create, update, send, and get drafts
- Save emails for later review or scheduled sending

**Label Operations** (4 tools)
- List, create, update, and delete custom labels
- Organize and categorize your emails

**Organization Tools** (2 tools)
- Mark messages as read/unread
- Archive messages (remove from inbox)

### 🔒 Security & Reliability

- **OAuth2 Authentication**: Secure Google authentication with automatic token refresh
- **Input Validation**: Pydantic models ensure all inputs are validated
- **Error Handling**: Clear, actionable error messages guide users to solutions
- **Stdio Transport**: Subprocess-managed for clean lifecycle and no network exposure

### 🎯 MCP Best Practices

- **Tool Annotations**: All tools properly annotated (readOnly, destructive, idempotent, openWorld)
- **Dual Output Formats**: Markdown (human-readable) and JSON (machine-readable)
- **Pagination**: Efficient result limiting (default 20, max 100)
- **Comprehensive Docs**: Every tool has detailed docstrings with examples

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Cloud account with Gmail API enabled
- OAuth 2.0 credentials (Desktop application)

### From Source

```bash
cd apps/gmail-mcp-server
uv sync
```

### Check Installation

```bash
uv run gmail-mcp --version
# Output: gmail-mcp 0.1.0

uv run gmail-mcp --help
# Shows all available commands
```

## Setup Guide

### Step 1: Google Cloud Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select existing)
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 Client ID:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop application"
   - Name it "Gmail MCP Server"
   - Download the JSON file
5. Configure OAuth consent screen:
   - Add test users (your Gmail address)
   - Scopes: The server will request appropriate scopes automatically

### Step 2: Authentication

```bash
# Option 1: Place OAuth config in standard location
mkdir -p ~/.gmail-mcp
cp ~/Downloads/client_secret_*.json ~/.gmail-mcp/oauth-credentials.json
uv run gmail-mcp --auth

# Option 2: Use project-specific location
# The server auto-discovers: /home/salim/Desktop/hackathon0/gcp-oauth.keys.json
uv run gmail-mcp --auth
```

This will:
1. Open a browser window for Google authentication
2. Request necessary Gmail permissions
3. Save credentials to `~/.gmail-mcp/credentials.json`
4. Set file permissions to 600 (owner read/write only)

**Verify authentication:**

```bash
uv run gmail-mcp --check-auth
# Output: ✓ Credentials found: /home/salim/.gmail-mcp/credentials.json
#         ✓ Credentials are valid
```

### Step 3: Configure Claude Code

Edit `~/.config/claude/mcp.json` (or create if it doesn't exist):

```json
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
```

**Alternative: System-wide installation**

After publishing to PyPI:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["gmail-mcp"]
    }
  }
}
```

### Step 4: Verify Integration

```bash
# Test with Claude Code CLI
claude "Use the gmail server to list tools"
# Should show all 19 Gmail tools

claude "Use gmail to list my recent unread emails"
# Should return your unread messages
```

## Available Tools

### Message Operations (8 tools)
- `gmail_list_messages` - Search and list messages with Gmail query syntax
- `gmail_get_message` - Get full message content including headers and body
- `gmail_send_message` - Send a new email
- `gmail_reply_to_message` - Reply to an existing message (maintains threading)
- `gmail_forward_message` - Forward a message to new recipients
- `gmail_modify_labels` - Add or remove labels from messages
- `gmail_trash_message` - Move message to trash (recoverable for 30 days)
- `gmail_delete_message` - Permanently delete a message (cannot be undone)

### Draft Operations (5 tools)
- `gmail_list_drafts` - List all draft messages
- `gmail_get_draft` - Get full details of a specific draft
- `gmail_create_draft` - Create a new draft for later review/sending
- `gmail_update_draft` - Modify an existing draft
- `gmail_send_draft` - Send a draft message

### Label Operations (4 tools)
- `gmail_list_labels` - List all Gmail labels (system and custom)
- `gmail_create_label` - Create a new custom label
- `gmail_update_label` - Rename or modify label visibility
- `gmail_delete_label` - Delete a custom label (cannot delete system labels)

### Organization Tools (2 tools)
- `gmail_mark_as_read` - Mark messages as read or unread
- `gmail_archive_messages` - Archive messages (remove from inbox, keep in All Mail)

## Configuration

### Environment Variables

- `GMAIL_MCP_CREDENTIALS_PATH` - Path to OAuth credentials JSON
- `GMAIL_MCP_TOKEN_PATH` - Path to store/load tokens
- `GMAIL_MCP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Command Line Options

```bash
gmail-mcp --help

Options:
  --creds-file PATH    Path to OAuth credentials JSON file
  --token-file PATH    Path to store/load OAuth tokens
  --auth              Run authentication flow only
  --log-level LEVEL   Set logging level (DEBUG, INFO, WARNING, ERROR)
```

## Gmail Search Query Examples

The `list_messages` tool supports full Gmail search syntax:

```
# Unread messages
is:unread

# From specific sender
from:user@example.com

# Date range
after:2026/01/01 before:2026/01/31

# Has attachment
has:attachment

# By subject
subject:"Invoice"

# Complex queries
is:unread from:boss@example.com has:attachment after:2026/01/01
```

## Development

### Setup Development Environment

```bash
cd apps/gmail-mcp-server
uv sync --extra dev
```

### Run Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black src/
uv run ruff check src/
```

### Test with MCP Inspector

```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector uv run gmail-mcp
```

## Security

- **Never commit credentials**: Credentials are stored in `~/.gmail-mcp/` with restricted permissions
- **OAuth2 only**: Uses Google's official OAuth2 flow
- **Token refresh**: Automatically refreshes expired tokens
- **Minimal scopes**: Requests only necessary Gmail API permissions

## Troubleshooting

### Authentication Issues

If you see authentication errors:

```bash
# Re-run authentication flow
uv run gmail-mcp --auth

# Check credentials file exists
ls -la ~/.gmail-mcp/
```

### Rate Limiting

Gmail API has rate limits:
- 250 quota units per user per second
- 1 billion quota units per day
- Sending: 100 emails/day (new accounts), 2000/day (established)

The server implements automatic backoff and retry for rate limit errors.

### Debugging

Enable debug logging:

```bash
gmail-mcp --log-level DEBUG
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

## Support

For issues and questions:
- GitHub Issues: [Project repository]
- Documentation: See `docs/` directory
