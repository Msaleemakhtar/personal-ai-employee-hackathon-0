"""
Gmail MCP Server - Main server implementation.

Registers all tools and handles Gmail operations via FastMCP.
"""

from mcp.server.fastmcp import FastMCP, Context
from gmail_mcp.auth import get_credentials
from gmail_mcp.gmail_client import GmailClient
from gmail_mcp.models import (
    ResponseFormat,
    ListMessagesInput,
    GetMessageInput,
    SendMessageInput,
    ReplyToMessageInput,
    ForwardMessageInput,
    ModifyLabelsInput,
    TrashMessageInput,
    DeleteMessageInput,
    ListDraftsInput,
    GetDraftInput,
    CreateDraftInput,
    UpdateDraftInput,
    SendDraftInput,
    ListLabelsInput,
    CreateLabelInput,
    UpdateLabelInput,
    DeleteLabelInput,
    MarkAsReadInput,
    ArchiveMessagesInput,
)
from gmail_mcp.formatters import (
    format_messages_markdown,
    format_messages_json,
    format_message_markdown,
    format_message_json,
    format_drafts_markdown,
    format_drafts_json,
    format_draft_markdown,
    format_draft_json,
    format_labels_markdown,
    format_labels_json,
    format_send_success,
    format_draft_created,
    format_label_created,
)
from gmail_mcp.utils import handle_api_error


# Initialize FastMCP server
mcp = FastMCP("gmail_mcp")


# ============================================================================
# Message Operations (8 tools)
# ============================================================================

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
    """
    Search and list Gmail messages using Gmail query syntax.

    This tool searches through Gmail messages using Google's advanced query
    syntax. It supports filters like sender, date range, labels, attachments,
    and more. Results are paginated for efficiency.

    Args:
        params (ListMessagesInput): Validated parameters containing:
            - query (Optional[str]): Gmail search query (default: "")
            - limit (Optional[int]): Max results 1-100 (default: 20)
            - include_spam_trash (Optional[bool]): Include SPAM/TRASH (default: False)
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted message list (markdown or JSON) or error message

    Query Syntax Examples:
        - "is:unread" - All unread messages
        - "from:user@example.com after:2026/01/01" - Messages from user after date
        - "has:attachment subject:invoice" - Messages with attachments about invoices
        - "label:important is:unread" - Important unread messages
        - "to:me cc:manager@company.com" - Messages to me CC'd to manager

    Use when:
        - Searching for specific messages
        - Finding unread mail
        - Locating messages by date, sender, or content

    Don't use when:
        - You have a specific message ID (use gmail_get_message instead)
        - You want to modify messages (use gmail_modify_labels or gmail_mark_as_read)
    """
    try:
        await ctx.info(f"Searching messages: query='{params.query or '(all)'}', limit={params.limit}")

        client = GmailClient(get_credentials())
        messages = client.list_messages(
            query=params.query,
            max_results=params.limit,
            include_spam_trash=params.include_spam_trash
        )

        if not messages:
            return f"No messages found matching query: '{params.query}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_messages_markdown(messages)
        else:
            return format_messages_json(messages)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_get_message",
    annotations={
        "title": "Get Gmail Message Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gmail_get_message(params: GetMessageInput, ctx: Context) -> str:
    """
    Get full details of a specific Gmail message.

    Retrieves complete message information including headers, body, labels,
    and metadata. Useful for reading full email content after searching.

    Args:
        params (GetMessageInput): Validated parameters containing:
            - message_id (str): Gmail message ID
            - format (MessageFormat): Message format (default: full)
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Complete message details or error message

    Use when:
        - Reading full email content
        - Getting message headers and metadata
        - Checking message labels and status

    Don't use when:
        - Searching for messages (use gmail_list_messages)
        - Replying to messages (use gmail_reply_to_message)
    """
    try:
        await ctx.info(f"Fetching message: {params.message_id}")

        client = GmailClient(get_credentials())
        message = client.get_message(params.message_id, format=params.format.value)

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_message_markdown(message)
        else:
            return format_message_json(message)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_send_message",
    annotations={
        "title": "Send Gmail Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_send_message(params: SendMessageInput, ctx: Context) -> str:
    """
    Send a new email message via Gmail.

    Composes and sends a new email to specified recipients. Supports CC, BCC,
    and HTML formatting. This creates a new email thread.

    Args:
        params (SendMessageInput): Validated parameters containing:
            - to (List[str]): Recipient email addresses (required)
            - subject (str): Email subject line (required)
            - body (str): Email body content (required)
            - cc (Optional[List[str]]): CC recipients
            - bcc (Optional[List[str]]): BCC recipients
            - html (Optional[bool]): Whether body is HTML (default: False)

    Returns:
        str: Success message with message ID or error

    Use when:
        - Sending new emails
        - Starting new conversations
        - Sending to multiple recipients with CC/BCC

    Don't use when:
        - Replying to existing messages (use gmail_reply_to_message)
        - Creating drafts for review (use gmail_create_draft)
    """
    try:
        await ctx.info(f"Sending message to {len(params.to)} recipient(s)")

        client = GmailClient(get_credentials())
        result = client.send_message(
            to=params.to,
            subject=params.subject,
            body=params.body,
            cc=params.cc,
            bcc=params.bcc,
            html=params.html
        )

        return format_send_success(result)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_reply_to_message",
    annotations={
        "title": "Reply to Gmail Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_reply_to_message(params: ReplyToMessageInput, ctx: Context) -> str:
    """
    Reply to an existing Gmail message.

    Sends a reply to an existing email thread. Maintains threading and
    includes proper reply headers. Supports reply-all functionality.

    Args:
        params (ReplyToMessageInput): Validated parameters containing:
            - message_id (str): ID of message to reply to (required)
            - body (str): Reply body content (required)
            - reply_all (Optional[bool]): Reply to all recipients (default: False)
            - html (Optional[bool]): Whether body is HTML (default: False)

    Returns:
        str: Success message with reply message ID or error

    Use when:
        - Responding to emails
        - Continuing email conversations
        - Replying to multiple recipients with reply_all=True

    Don't use when:
        - Sending new emails (use gmail_send_message)
        - Forwarding messages (use gmail_forward_message)
    """
    try:
        await ctx.info(f"Replying to message: {params.message_id}")

        client = GmailClient(get_credentials())
        result = client.reply_to_message(
            message_id=params.message_id,
            body=params.body,
            reply_all=params.reply_all,
            html=params.html
        )

        return format_send_success(result)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_forward_message",
    annotations={
        "title": "Forward Gmail Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_forward_message(params: ForwardMessageInput, ctx: Context) -> str:
    """
    Forward an existing Gmail message to new recipients.

    Forwards message content to new recipients with optional additional
    message. Original message is included with "Forwarded message" header.

    Args:
        params (ForwardMessageInput): Validated parameters containing:
            - message_id (str): ID of message to forward (required)
            - to (List[str]): Forward recipient addresses (required)
            - body (Optional[str]): Additional message to include (default: "")

    Returns:
        str: Success message with forwarded message ID or error

    Use when:
        - Sharing emails with others
        - Forwarding information to new recipients
        - Distributing messages to a team

    Don't use when:
        - Replying to the sender (use gmail_reply_to_message)
        - Sending new emails (use gmail_send_message)
    """
    try:
        await ctx.info(f"Forwarding message {params.message_id} to {len(params.to)} recipient(s)")

        client = GmailClient(get_credentials())
        result = client.forward_message(
            message_id=params.message_id,
            to=params.to,
            body=params.body
        )

        return format_send_success(result)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_modify_labels",
    annotations={
        "title": "Modify Message Labels",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_modify_labels(params: ModifyLabelsInput, ctx: Context) -> str:
    """
    Add or remove labels from Gmail messages.

    Modifies labels on one or more messages. Labels control message organization,
    visibility, and categorization. System labels include INBOX, UNREAD, STARRED, etc.

    Args:
        params (ModifyLabelsInput): Validated parameters containing:
            - message_ids (List[str]): List of message IDs to modify (required)
            - add_labels (Optional[List[str]]): Label IDs to add
            - remove_labels (Optional[List[str]]): Label IDs to remove

    Returns:
        str: Success message with count of modified messages or error

    Common Label IDs:
        - System: INBOX, UNREAD, STARRED, IMPORTANT, SENT, DRAFT, SPAM, TRASH
        - Custom: Label_xxx (get from gmail_list_labels)

    Use when:
        - Organizing messages
        - Categorizing emails
        - Marking messages as important/starred
        - Moving messages to/from inbox

    Don't use when:
        - Just marking read/unread (use gmail_mark_as_read)
        - Archiving messages (use gmail_archive_messages)
    """
    try:
        count = len(params.message_ids)
        await ctx.info(f"Modifying labels on {count} message(s)")

        client = GmailClient(get_credentials())
        results = client.modify_labels(
            message_ids=params.message_ids,
            add_labels=params.add_labels,
            remove_labels=params.remove_labels
        )

        return f"✓ Successfully modified labels on {len(results)} message(s)"

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_trash_message",
    annotations={
        "title": "Move Message to Trash",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_trash_message(params: TrashMessageInput, ctx: Context) -> str:
    """
    Move a Gmail message to trash.

    Moves message to TRASH folder. Message can be recovered from trash
    within 30 days before automatic permanent deletion.

    Args:
        params (TrashMessageInput): Validated parameters containing:
            - message_id (str): Message ID to trash (required)

    Returns:
        str: Success message or error

    Use when:
        - Removing unwanted messages
        - Cleaning up inbox
        - Deleting with recovery option

    Don't use when:
        - Permanently deleting (use gmail_delete_message - cannot be undone)
        - Archiving (use gmail_archive_messages)
    """
    try:
        await ctx.info(f"Moving message to trash: {params.message_id}")

        client = GmailClient(get_credentials())
        client.trash_message(params.message_id)

        return f"✓ Message moved to trash: {params.message_id}"

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_delete_message",
    annotations={
        "title": "Permanently Delete Message",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def gmail_delete_message(params: DeleteMessageInput, ctx: Context) -> str:
    """
    Permanently delete a Gmail message.

    WARNING: This operation CANNOT be undone. Message is permanently removed
    from Gmail. For recoverable deletion, use gmail_trash_message instead.

    Args:
        params (DeleteMessageInput): Validated parameters containing:
            - message_id (str): Message ID to delete permanently (required)

    Returns:
        str: Success message or error

    Use when:
        - Permanently removing messages
        - Complying with data deletion requirements
        - Removing sensitive information permanently

    Don't use when:
        - You might need to recover the message (use gmail_trash_message)
        - Just cleaning up inbox (use gmail_archive_messages)
    """
    try:
        await ctx.info(f"Permanently deleting message: {params.message_id}")

        client = GmailClient(get_credentials())
        client.delete_message(params.message_id)

        return f"✓ Message permanently deleted: {params.message_id}"

    except Exception as e:
        return handle_api_error(e)


# ============================================================================
# Draft Operations (5 tools)
# ============================================================================

@mcp.tool(
    name="gmail_list_drafts",
    annotations={
        "title": "List Gmail Drafts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_list_drafts(params: ListDraftsInput, ctx: Context) -> str:
    """
    List all Gmail draft messages.

    Retrieves all draft messages in the account. Drafts are unsent emails
    saved for later completion or sending.

    Args:
        params (ListDraftsInput): Validated parameters containing:
            - limit (Optional[int]): Max results 1-100 (default: 20)
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: List of drafts (markdown or JSON) or error

    Use when:
        - Viewing saved drafts
        - Finding draft to edit or send
        - Managing unsent emails

    Don't use when:
        - You have a specific draft ID (use gmail_get_draft)
        - Creating new drafts (use gmail_create_draft)
    """
    try:
        await ctx.info(f"Listing drafts (limit={params.limit})")

        client = GmailClient(get_credentials())
        drafts = client.list_drafts(max_results=params.limit)

        if not drafts:
            return "No drafts found."

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_drafts_markdown(drafts)
        else:
            return format_drafts_json(drafts)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_get_draft",
    annotations={
        "title": "Get Gmail Draft Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_get_draft(params: GetDraftInput, ctx: Context) -> str:
    """
    Get full details of a specific Gmail draft.

    Retrieves complete draft information including recipients, subject,
    body, and draft ID needed for updating or sending.

    Args:
        params (GetDraftInput): Validated parameters containing:
            - draft_id (str): Draft ID (required)
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Complete draft details or error

    Use when:
        - Reading draft content before sending
        - Getting draft ID for updates
        - Reviewing unsent emails

    Don't use when:
        - Listing all drafts (use gmail_list_drafts)
        - Editing drafts (use gmail_update_draft)
    """
    try:
        await ctx.info(f"Fetching draft: {params.draft_id}")

        client = GmailClient(get_credentials())
        draft = client.get_draft(params.draft_id)

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_draft_markdown(draft)
        else:
            return format_draft_json(draft)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_create_draft",
    annotations={
        "title": "Create Gmail Draft",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def gmail_create_draft(params: CreateDraftInput, ctx: Context) -> str:
    """
    Create a new Gmail draft message.

    Creates an unsent email draft that can be edited and sent later.
    Useful for composing emails that need review or scheduled sending.

    Args:
        params (CreateDraftInput): Validated parameters containing:
            - to (List[str]): Recipient addresses (required)
            - subject (str): Email subject (required)
            - body (str): Email body content (required)
            - cc (Optional[List[str]]): CC recipients
            - bcc (Optional[List[str]]): BCC recipients
            - html (Optional[bool]): Whether body is HTML (default: False)

    Returns:
        str: Success message with draft ID or error

    Use when:
        - Composing emails for later review
        - Preparing emails to send at specific time
        - Creating templates for common responses

    Don't use when:
        - Sending immediately (use gmail_send_message)
        - Updating existing drafts (use gmail_update_draft)
    """
    try:
        await ctx.info(f"Creating draft to {len(params.to)} recipient(s)")

        client = GmailClient(get_credentials())
        draft = client.create_draft(
            to=params.to,
            subject=params.subject,
            body=params.body,
            cc=params.cc,
            bcc=params.bcc,
            html=params.html
        )

        return format_draft_created(draft)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_update_draft",
    annotations={
        "title": "Update Gmail Draft",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_update_draft(params: UpdateDraftInput, ctx: Context) -> str:
    """
    Update an existing Gmail draft message.

    Replaces draft content entirely with new recipients, subject, and body.
    Use this to edit drafts before sending.

    Args:
        params (UpdateDraftInput): Validated parameters containing:
            - draft_id (str): Draft ID to update (required)
            - to (List[str]): Recipient addresses (required)
            - subject (str): Email subject (required)
            - body (str): Email body content (required)
            - cc (Optional[List[str]]): CC recipients
            - bcc (Optional[List[str]]): BCC recipients
            - html (Optional[bool]): Whether body is HTML (default: False)

    Returns:
        str: Success message with draft ID or error

    Use when:
        - Editing draft content
        - Changing recipients or subject
        - Revising message before sending

    Don't use when:
        - Creating new drafts (use gmail_create_draft)
        - Sending drafts (use gmail_send_draft)
    """
    try:
        await ctx.info(f"Updating draft: {params.draft_id}")

        client = GmailClient(get_credentials())
        draft = client.update_draft(
            draft_id=params.draft_id,
            to=params.to,
            subject=params.subject,
            body=params.body,
            cc=params.cc,
            bcc=params.bcc,
            html=params.html
        )

        return f"✓ Draft updated successfully: {draft.get('id')}"

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_send_draft",
    annotations={
        "title": "Send Gmail Draft",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def gmail_send_draft(params: SendDraftInput, ctx: Context) -> str:
    """
    Send an existing Gmail draft message.

    Sends a draft message immediately. Draft is removed from drafts folder
    after sending and appears in Sent folder.

    Args:
        params (SendDraftInput): Validated parameters containing:
            - draft_id (str): Draft ID to send (required)

    Returns:
        str: Success message with sent message ID or error

    Use when:
        - Sending prepared drafts
        - Completing and sending saved emails
        - Sending reviewed messages

    Don't use when:
        - Editing drafts first (use gmail_update_draft)
        - Sending new messages (use gmail_send_message)
    """
    try:
        await ctx.info(f"Sending draft: {params.draft_id}")

        client = GmailClient(get_credentials())
        result = client.send_draft(params.draft_id)

        return format_send_success(result)

    except Exception as e:
        return handle_api_error(e)


# ============================================================================
# Label Operations (4 tools)
# ============================================================================

@mcp.tool(
    name="gmail_list_labels",
    annotations={
        "title": "List Gmail Labels",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_list_labels(params: ListLabelsInput, ctx: Context) -> str:
    """
    List all Gmail labels (system and user-created).

    Retrieves all labels in the account including system labels (INBOX, SENT, etc.)
    and user-created labels. Labels are used to organize and categorize messages.

    Args:
        params (ListLabelsInput): Validated parameters containing:
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: List of all labels with IDs or error

    System Labels:
        INBOX, UNREAD, STARRED, IMPORTANT, SENT, DRAFT, SPAM, TRASH,
        CATEGORY_PERSONAL, CATEGORY_SOCIAL, CATEGORY_PROMOTIONS, etc.

    Use when:
        - Finding label IDs for use with other tools
        - Listing available organization categories
        - Discovering system label names

    Don't use when:
        - Creating labels (use gmail_create_label)
        - Applying labels to messages (use gmail_modify_labels)
    """
    try:
        await ctx.info("Listing all labels")

        client = GmailClient(get_credentials())
        labels = client.list_labels()

        if params.response_format == ResponseFormat.MARKDOWN:
            return format_labels_markdown(labels)
        else:
            return format_labels_json(labels)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_create_label",
    annotations={
        "title": "Create Gmail Label",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def gmail_create_label(params: CreateLabelInput, ctx: Context) -> str:
    """
    Create a new Gmail label.

    Creates a user-defined label for organizing messages. Labels can be
    used to categorize, filter, and organize emails.

    Args:
        params (CreateLabelInput): Validated parameters containing:
            - name (str): Label name (required)
            - label_list_visibility (Optional[str]): Visibility in label list (default: labelShow)
            - message_list_visibility (Optional[str]): Visibility in message list (default: show)

    Returns:
        str: Success message with label ID or error

    Visibility Options:
        - label_list_visibility: "labelShow", "labelShowIfUnread", "labelHide"
        - message_list_visibility: "show", "hide"

    Use when:
        - Creating custom organization categories
        - Setting up project-specific labels
        - Creating tags for message filtering

    Don't use when:
        - Using system labels (they already exist)
        - Applying labels to messages (use gmail_modify_labels)
    """
    try:
        await ctx.info(f"Creating label: {params.name}")

        client = GmailClient(get_credentials())
        label = client.create_label(
            name=params.name,
            label_list_visibility=params.label_list_visibility,
            message_list_visibility=params.message_list_visibility
        )

        return format_label_created(label)

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_update_label",
    annotations={
        "title": "Update Gmail Label",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_update_label(params: UpdateLabelInput, ctx: Context) -> str:
    """
    Update an existing Gmail label's properties.

    Modifies label name or visibility settings. Cannot modify system labels.
    Changing label name updates it everywhere it's used.

    Args:
        params (UpdateLabelInput): Validated parameters containing:
            - label_id (str): Label ID to update (required)
            - name (Optional[str]): New label name
            - label_list_visibility (Optional[str]): Label list visibility
            - message_list_visibility (Optional[str]): Message list visibility

    Returns:
        str: Success message or error

    Use when:
        - Renaming labels
        - Changing label visibility
        - Updating organization structure

    Don't use when:
        - Creating new labels (use gmail_create_label)
        - Deleting labels (use gmail_delete_label)
    """
    try:
        await ctx.info(f"Updating label: {params.label_id}")

        client = GmailClient(get_credentials())
        label = client.update_label(
            label_id=params.label_id,
            name=params.name,
            label_list_visibility=params.label_list_visibility,
            message_list_visibility=params.message_list_visibility
        )

        return f"✓ Label updated successfully: {label.get('name')} ({label.get('id')})"

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_delete_label",
    annotations={
        "title": "Delete Gmail Label",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def gmail_delete_label(params: DeleteLabelInput, ctx: Context) -> str:
    """
    Delete a Gmail label.

    Permanently removes a user-created label. Cannot delete system labels.
    Messages are not deleted, only the label is removed.

    Args:
        params (DeleteLabelInput): Validated parameters containing:
            - label_id (str): Label ID to delete (required)

    Returns:
        str: Success message or error

    Use when:
        - Removing unused labels
        - Cleaning up label organization
        - Removing obsolete categories

    Don't use when:
        - Deleting system labels (not allowed)
        - Just renaming labels (use gmail_update_label)
    """
    try:
        await ctx.info(f"Deleting label: {params.label_id}")

        client = GmailClient(get_credentials())
        client.delete_label(params.label_id)

        return f"✓ Label deleted successfully: {params.label_id}"

    except Exception as e:
        return handle_api_error(e)


# ============================================================================
# Organization Tools (2 tools)
# ============================================================================

@mcp.tool(
    name="gmail_mark_as_read",
    annotations={
        "title": "Mark Messages Read/Unread",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_mark_as_read(params: MarkAsReadInput, ctx: Context) -> str:
    """
    Mark Gmail messages as read or unread.

    Changes the UNREAD label status on one or more messages. Useful for
    managing inbox and marking messages for later attention.

    Args:
        params (MarkAsReadInput): Validated parameters containing:
            - message_ids (List[str]): List of message IDs (required)
            - read (bool): True to mark read, False to mark unread (required)

    Returns:
        str: Success message with count or error

    Use when:
        - Marking messages as read after processing
        - Flagging messages as unread for later attention
        - Batch updating read status

    Don't use when:
        - Modifying other labels (use gmail_modify_labels)
        - Archiving messages (use gmail_archive_messages)
    """
    try:
        count = len(params.message_ids)
        action = "read" if params.read else "unread"
        await ctx.info(f"Marking {count} message(s) as {action}")

        client = GmailClient(get_credentials())

        if params.read:
            # Remove UNREAD label
            client.modify_labels(
                message_ids=params.message_ids,
                remove_labels=['UNREAD']
            )
        else:
            # Add UNREAD label
            client.modify_labels(
                message_ids=params.message_ids,
                add_labels=['UNREAD']
            )

        return f"✓ Marked {count} message(s) as {action}"

    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="gmail_archive_messages",
    annotations={
        "title": "Archive Gmail Messages",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def gmail_archive_messages(params: ArchiveMessagesInput, ctx: Context) -> str:
    """
    Archive Gmail messages (remove from inbox).

    Removes the INBOX label from messages, moving them to "All Mail" archive.
    Messages are still accessible via search and labels but not in inbox.

    Args:
        params (ArchiveMessagesInput): Validated parameters containing:
            - message_ids (List[str]): List of message IDs to archive (required)

    Returns:
        str: Success message with count or error

    Use when:
        - Cleaning up inbox while keeping messages
        - Organizing processed emails
        - Decluttering without deleting

    Don't use when:
        - Deleting messages (use gmail_trash_message or gmail_delete_message)
        - Just marking as read (use gmail_mark_as_read)
    """
    try:
        count = len(params.message_ids)
        await ctx.info(f"Archiving {count} message(s)")

        client = GmailClient(get_credentials())
        client.modify_labels(
            message_ids=params.message_ids,
            remove_labels=['INBOX']
        )

        return f"✓ Archived {count} message(s)"

    except Exception as e:
        return handle_api_error(e)


# Entry point for running the server
if __name__ == "__main__":
    mcp.run()
