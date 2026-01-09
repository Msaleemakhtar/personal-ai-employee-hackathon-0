# Gmail MCP Server Implementation Plan

## Overview

Building a production-quality Gmail MCP server using FastMCP (Python) with comprehensive Gmail API coverage.

## Design Decisions

### Server Naming
- **Name**: `gmail_mcp` (following Python convention: `{service}_mcp`)
- **Package**: `gmail_mcp`
- **Entry point**: `gmail-mcp` command

### Transport
- **Primary**: stdio (for Claude Code CLI integration)
- **Reason**: Local-first, subprocess management, simple setup

### Tool Naming Pattern
- Format: `gmail_{action}_{resource}`
- Examples: `gmail_list_messages`, `gmail_send_message`, `gmail_create_draft`

### Response Formats
- Default: Markdown (human-readable)
- Optional: JSON (programmatic processing)
- Controlled via `response_format` parameter

## Tool Categories

### 1. Message Operations (8 tools)
1. `gmail_list_messages` - Search/list messages with query syntax
2. `gmail_get_message` - Get full message details
3. `gmail_send_message` - Send new email
4. `gmail_reply_to_message` - Reply to existing message
5. `gmail_forward_message` - Forward message to recipients
6. `gmail_modify_labels` - Add/remove labels from messages
7. `gmail_trash_message` - Move message to trash
8. `gmail_delete_message` - Permanently delete message

### 2. Draft Operations (5 tools)
9. `gmail_list_drafts` - List all drafts
10. `gmail_get_draft` - Get draft details
11. `gmail_create_draft` - Create new draft
12. `gmail_update_draft` - Update existing draft
13. `gmail_send_draft` - Send draft message

### 3. Label Operations (4 tools)
14. `gmail_list_labels` - List all labels
15. `gmail_create_label` - Create new label
16. `gmail_update_label` - Update label properties
17. `gmail_delete_label` - Delete label

### 4. Organization Tools (2 tools)
18. `gmail_mark_as_read` - Mark messages read/unread
19. `gmail_archive_messages` - Archive messages (remove INBOX label)

**Total**: 19 tools

## Authentication Strategy

### OAuth2 Flow
1. Check for existing credentials at `~/.gmail-mcp/credentials.json`
2. If not found, look for OAuth client config at:
   - `~/.gmail-mcp/oauth-credentials.json`
   - `/home/salim/Desktop/hackathon0/gcp-oauth.keys.json`
3. If credentials expired, refresh automatically
4. If no valid credentials, provide clear instructions for setup

### Required Scopes
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Full access except delete
    'https://www.googleapis.com/auth/gmail.labels',   # Label management
]
```

## Project Structure

```
apps/gmail-mcp-server/
├── src/gmail_mcp/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point with CLI
│   ├── server.py             # Main FastMCP server
│   ├── auth.py               # OAuth2 authentication
│   ├── gmail_client.py       # Gmail API wrapper
│   ├── models.py             # Pydantic input models
│   ├── formatters.py         # Response formatting utilities
│   └── utils.py              # Error handling, helpers
├── tests/
│   ├── test_auth.py
│   ├── test_gmail_client.py
│   └── test_tools.py
├── examples/
│   ├── claude_code_config.json
│   └── usage_examples.md
├── pyproject.toml
├── README.md
└── IMPLEMENTATION_PLAN.md (this file)
```

## Code Organization

### Module Responsibilities

**auth.py**:
- `get_credentials()` - Load/create OAuth2 credentials
- `refresh_if_expired()` - Auto-refresh tokens
- `setup_oauth()` - Interactive OAuth flow

**gmail_client.py**:
- `GmailClient` class wrapping google-api-python-client
- Async methods for all Gmail API operations
- Centralized error handling
- Response parsing and normalization

**models.py**:
- Pydantic models for all tool inputs
- Shared types (ResponseFormat enum, etc.)
- Input validation with Field constraints

**formatters.py**:
- `format_message_markdown()` - Human-readable message format
- `format_message_json()` - Machine-readable format
- `format_draft_markdown()` - Draft formatting
- `format_label_list()` - Label list formatting

**utils.py**:
- `handle_api_error()` - Consistent error formatting
- `parse_email_addresses()` - Email validation
- `create_mime_message()` - MIME message construction

**server.py**:
- FastMCP server initialization
- All tool registrations
- Context injection for logging

## Implementation Phases

### Phase 1: Foundation (2-3 hours)
- [ ] Set up project structure
- [ ] Implement authentication module
- [ ] Create Gmail API client wrapper
- [ ] Write basic tests

### Phase 2: Core Tools (3-4 hours)
- [ ] Implement message operation tools (8 tools)
- [ ] Implement draft operation tools (5 tools)
- [ ] Implement label operation tools (4 tools)
- [ ] Implement organization tools (2 tools)

### Phase 3: Polish (1-2 hours)
- [ ] Add comprehensive error handling
- [ ] Implement response formatting
- [ ] Add CLI with proper arguments
- [ ] Test with MCP Inspector

### Phase 4: Integration & Documentation (1-2 hours)
- [ ] Test with Claude Code CLI
- [ ] Write comprehensive README
- [ ] Create usage examples
- [ ] Document setup process

**Total Time**: 7-11 hours

## Tool Annotations

Following MCP best practices, each tool will have appropriate annotations:

| Tool | readOnly | destructive | idempotent | openWorld |
|------|----------|-------------|------------|-----------|
| list_messages | true | false | true | true |
| get_message | true | false | true | true |
| send_message | false | false | false | true |
| reply_to_message | false | false | false | true |
| forward_message | false | false | false | true |
| modify_labels | false | false | true | false |
| trash_message | false | true | true | false |
| delete_message | false | true | false | false |
| list_drafts | true | false | true | false |
| create_draft | false | false | false | false |
| update_draft | false | false | true | false |
| send_draft | false | false | false | true |
| list_labels | true | false | true | false |
| create_label | false | false | false | false |
| update_label | false | false | true | false |
| delete_label | false | true | false | false |
| mark_as_read | false | false | true | false |
| archive_messages | false | false | true | false |

## Key Design Principles

### 1. Comprehensive API Coverage
Focus on complete Gmail API coverage rather than workflow-specific tools. This gives agents maximum flexibility to compose operations.

### 2. Clear Tool Descriptions
Each tool has:
- Concise summary (1-2 sentences)
- Detailed parameter descriptions with examples
- Complete return value schema
- Use/don't use guidance

### 3. Actionable Errors
Error messages include:
- What went wrong
- Why it happened
- How to fix it
- Alternative approaches

### 4. Efficient Context Usage
- Paginated results (default 20, max 100)
- Markdown format omits verbose metadata
- Human-readable timestamps
- Display names with IDs

### 5. Code Reusability
- Shared Gmail client for all tools
- Common error handling
- Unified formatting functions
- No code duplication

## Example Tool Implementation

```python
# models.py
class ListMessagesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: Optional[str] = Field(
        default="",
        description="Gmail search query (e.g., 'is:unread', 'from:user@example.com after:2026/01/01')",
        max_length=500
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of messages to return",
        ge=1,
        le=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data"
    )

# server.py
@mcp.tool(
    name="gmail_list_messages",
    annotations={
        "title": "List Gmail Messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_list_messages(params: ListMessagesInput, ctx: Context) -> str:
    '''Search and list Gmail messages using Gmail query syntax.

    This tool searches through Gmail messages using Google's advanced query
    syntax. It supports filters like sender, date range, labels, attachments, etc.

    Args:
        params (ListMessagesInput): Validated parameters containing:
            - query (Optional[str]): Gmail search query (default: "")
            - limit (Optional[int]): Max results 1-100 (default: 20)
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted message list or error message

    Examples:
        - "is:unread" - List unread messages
        - "from:user@example.com after:2026/01/01" - Messages from user after date
        - "has:attachment subject:invoice" - Messages with attachments containing "invoice"
    '''
    try:
        await ctx.info(f"Searching messages with query: {params.query or '(all)'}")

        client = GmailClient(get_credentials())
        messages = await client.list_messages(
            query=params.query,
            max_results=params.limit
        )

        if not messages:
            return f"No messages found matching '{params.query}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_messages_markdown(messages)
        else:
            return format_messages_json(messages)

    except Exception as e:
        return handle_api_error(e)
```

## Testing Strategy

### Unit Tests
- Authentication flow
- Gmail client methods
- Input validation
- Error handling

### Integration Tests
- Tool execution with mocked Gmail API
- Response formatting
- Error scenarios

### Manual Testing
- MCP Inspector testing
- Claude Code CLI integration
- Real Gmail API operations

## Success Criteria

- [ ] All 19 tools implemented and tested
- [ ] OAuth2 authentication working
- [ ] Credentials auto-refresh
- [ ] Clear error messages
- [ ] Markdown and JSON output formats
- [ ] Pagination working correctly
- [ ] MCP Inspector shows all tools
- [ ] Claude Code can use all tools
- [ ] Comprehensive README with setup instructions
- [ ] No code duplication

## Dependencies

```toml
dependencies = [
    "mcp>=1.0.0",                          # FastMCP framework
    "google-auth>=2.29.0",                 # OAuth2 authentication
    "google-auth-oauthlib>=1.2.0",        # OAuth2 flow
    "google-auth-httplib2>=0.2.0",        # HTTP transport
    "google-api-python-client>=2.126.0",  # Gmail API client
    "pydantic>=2.0.0",                     # Input validation
    "httpx>=0.25.0",                       # Async HTTP (if needed)
]
```

## Next Steps

1. Implement authentication module with credential discovery
2. Create Gmail client wrapper with all API methods
3. Define all Pydantic input models
4. Implement formatters for markdown/JSON output
5. Register all 19 tools with FastMCP
6. Test with MCP Inspector
7. Create comprehensive documentation
