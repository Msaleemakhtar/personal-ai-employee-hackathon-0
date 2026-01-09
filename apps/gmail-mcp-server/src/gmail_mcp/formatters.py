"""
Response formatting functions for Gmail MCP server.

Converts Gmail API responses to markdown or JSON formats.
"""

import json
from typing import List, Dict, Any
from gmail_mcp.utils import (
    get_header_value,
    format_timestamp,
    extract_email_address,
    truncate_text,
    safe_json_dumps
)


# ===========================================================================
# Message Formatting
# ===========================================================================

def format_messages_markdown(messages: List[Dict[str, Any]]) -> str:
    """
    Format list of messages as markdown.

    Args:
        messages: List of message objects from Gmail API

    Returns:
        Markdown-formatted string
    """
    if not messages:
        return "No messages found."

    lines = [f"# Gmail Messages ({len(messages)} messages)", ""]

    for msg in messages:
        msg_id = msg.get('id', 'unknown')
        thread_id = msg.get('threadId', 'unknown')
        snippet = msg.get('snippet', '')
        labels = msg.get('labelIds', [])

        # Extract headers
        headers = msg.get('payload', {}).get('headers', [])
        from_addr = get_header_value(headers, 'From')
        subject = get_header_value(headers, 'Subject')
        date = get_header_value(headers, 'Date')

        # Format internal date
        internal_date = msg.get('internalDate', '')
        if internal_date:
            date = format_timestamp(internal_date)

        lines.append(f"## {subject or '(No Subject)'}")
        lines.append(f"- **From**: {from_addr or 'Unknown'}")
        lines.append(f"- **Date**: {date}")
        lines.append(f"- **ID**: `{msg_id}`")
        if 'UNREAD' in labels:
            lines.append(f"- **Status**: Unread")
        lines.append(f"- **Preview**: {truncate_text(snippet, 200)}")
        lines.append("")

    return "\n".join(lines)


def format_messages_json(messages: List[Dict[str, Any]]) -> str:
    """
    Format list of messages as JSON.

    Args:
        messages: List of message objects from Gmail API

    Returns:
        JSON string
    """
    formatted = []

    for msg in messages:
        headers = msg.get('payload', {}).get('headers', [])

        formatted.append({
            'id': msg.get('id'),
            'threadId': msg.get('threadId'),
            'snippet': msg.get('snippet'),
            'labels': msg.get('labelIds', []),
            'from': get_header_value(headers, 'From'),
            'to': get_header_value(headers, 'To'),
            'subject': get_header_value(headers, 'Subject'),
            'date': get_header_value(headers, 'Date'),
            'internalDate': format_timestamp(msg.get('internalDate', '0'))
        })

    return safe_json_dumps({
        'total': len(formatted),
        'messages': formatted
    })


def format_message_markdown(message: Dict[str, Any]) -> str:
    """
    Format a single message as markdown.

    Args:
        message: Message object from Gmail API

    Returns:
        Markdown-formatted string
    """
    msg_id = message.get('id', 'unknown')
    thread_id = message.get('threadId', 'unknown')
    snippet = message.get('snippet', '')
    labels = message.get('labelIds', [])

    # Extract headers
    headers = message.get('payload', {}).get('headers', [])
    from_addr = get_header_value(headers, 'From')
    to_addr = get_header_value(headers, 'To')
    cc_addr = get_header_value(headers, 'Cc')
    subject = get_header_value(headers, 'Subject')
    date = get_header_value(headers, 'Date')

    # Format internal date
    internal_date = message.get('internalDate', '')
    if internal_date:
        date = format_timestamp(internal_date)

    # Extract body
    body = _extract_message_body(message)

    lines = [
        f"# {subject or '(No Subject)'}",
        "",
        "## Message Details",
        f"- **From**: {from_addr or 'Unknown'}",
        f"- **To**: {to_addr or 'Unknown'}",
    ]

    if cc_addr:
        lines.append(f"- **Cc**: {cc_addr}")

    lines.extend([
        f"- **Date**: {date}",
        f"- **Message ID**: `{msg_id}`",
        f"- **Thread ID**: `{thread_id}`",
    ])

    if 'UNREAD' in labels:
        lines.append("- **Status**: Unread")

    if labels:
        lines.append(f"- **Labels**: {', '.join(labels)}")

    lines.extend([
        "",
        "## Message Body",
        "",
        body or snippet or "(No content available)",
        ""
    ])

    return "\n".join(lines)


def format_message_json(message: Dict[str, Any]) -> str:
    """
    Format a single message as JSON.

    Args:
        message: Message object from Gmail API

    Returns:
        JSON string
    """
    headers = message.get('payload', {}).get('headers', [])
    body = _extract_message_body(message)

    formatted = {
        'id': message.get('id'),
        'threadId': message.get('threadId'),
        'snippet': message.get('snippet'),
        'body': body,
        'labels': message.get('labelIds', []),
        'from': get_header_value(headers, 'From'),
        'to': get_header_value(headers, 'To'),
        'cc': get_header_value(headers, 'Cc'),
        'subject': get_header_value(headers, 'Subject'),
        'date': get_header_value(headers, 'Date'),
        'internalDate': format_timestamp(message.get('internalDate', '0'))
    }

    return safe_json_dumps(formatted)


def _extract_message_body(message: Dict[str, Any]) -> str:
    """Extract full body from message payload."""
    import base64

    if 'payload' not in message:
        return message.get('snippet', '')

    payload = message['payload']

    # Check for simple body
    if 'body' in payload and 'data' in payload['body']:
        try:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        except Exception:
            return message.get('snippet', '')

    # Check for multipart
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                if 'data' in part.get('body', {}):
                    try:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    except Exception:
                        pass

    # Fallback to snippet
    return message.get('snippet', '')


# ===========================================================================
# Draft Formatting
# ===========================================================================

def format_drafts_markdown(drafts: List[Dict[str, Any]]) -> str:
    """
    Format list of drafts as markdown.

    Args:
        drafts: List of draft objects from Gmail API

    Returns:
        Markdown-formatted string
    """
    if not drafts:
        return "No drafts found."

    lines = [f"# Gmail Drafts ({len(drafts)} drafts)", ""]

    for draft in drafts:
        draft_id = draft.get('id', 'unknown')
        message = draft.get('message', {})
        snippet = message.get('snippet', '')

        # Extract headers
        headers = message.get('payload', {}).get('headers', [])
        to_addr = get_header_value(headers, 'To')
        subject = get_header_value(headers, 'Subject')

        lines.append(f"## {subject or '(No Subject)'}")
        lines.append(f"- **To**: {to_addr or 'Not specified'}")
        lines.append(f"- **Draft ID**: `{draft_id}`")
        lines.append(f"- **Preview**: {truncate_text(snippet, 200)}")
        lines.append("")

    return "\n".join(lines)


def format_drafts_json(drafts: List[Dict[str, Any]]) -> str:
    """
    Format list of drafts as JSON.

    Args:
        drafts: List of draft objects from Gmail API

    Returns:
        JSON string
    """
    formatted = []

    for draft in drafts:
        message = draft.get('message', {})
        headers = message.get('payload', {}).get('headers', [])

        formatted.append({
            'id': draft.get('id'),
            'messageId': message.get('id'),
            'snippet': message.get('snippet'),
            'to': get_header_value(headers, 'To'),
            'subject': get_header_value(headers, 'Subject')
        })

    return safe_json_dumps({
        'total': len(formatted),
        'drafts': formatted
    })


def format_draft_markdown(draft: Dict[str, Any]) -> str:
    """
    Format a single draft as markdown.

    Args:
        draft: Draft object from Gmail API

    Returns:
        Markdown-formatted string
    """
    draft_id = draft.get('id', 'unknown')
    message = draft.get('message', {})

    # Extract headers
    headers = message.get('payload', {}).get('headers', [])
    to_addr = get_header_value(headers, 'To')
    cc_addr = get_header_value(headers, 'Cc')
    subject = get_header_value(headers, 'Subject')

    # Extract body
    body = _extract_message_body(message)

    lines = [
        f"# Draft: {subject or '(No Subject)'}",
        "",
        "## Draft Details",
        f"- **To**: {to_addr or 'Not specified'}",
    ]

    if cc_addr:
        lines.append(f"- **Cc**: {cc_addr}")

    lines.extend([
        f"- **Subject**: {subject or '(No Subject)'}",
        f"- **Draft ID**: `{draft_id}`",
        "",
        "## Draft Body",
        "",
        body or message.get('snippet', '(No content)'),
        ""
    ])

    return "\n".join(lines)


def format_draft_json(draft: Dict[str, Any]) -> str:
    """
    Format a single draft as JSON.

    Args:
        draft: Draft object from Gmail API

    Returns:
        JSON string
    """
    message = draft.get('message', {})
    headers = message.get('payload', {}).get('headers', [])
    body = _extract_message_body(message)

    formatted = {
        'id': draft.get('id'),
        'messageId': message.get('id'),
        'body': body,
        'snippet': message.get('snippet'),
        'to': get_header_value(headers, 'To'),
        'cc': get_header_value(headers, 'Cc'),
        'bcc': get_header_value(headers, 'Bcc'),
        'subject': get_header_value(headers, 'Subject')
    }

    return safe_json_dumps(formatted)


# ===========================================================================
# Label Formatting
# ===========================================================================

def format_labels_markdown(labels: List[Dict[str, Any]]) -> str:
    """
    Format list of labels as markdown.

    Args:
        labels: List of label objects from Gmail API

    Returns:
        Markdown-formatted string
    """
    if not labels:
        return "No labels found."

    # Separate system and user labels
    system_labels = [l for l in labels if l.get('type') == 'system']
    user_labels = [l for l in labels if l.get('type') == 'user']

    lines = [f"# Gmail Labels ({len(labels)} total)", ""]

    if user_labels:
        lines.append("## User Labels")
        lines.append("")
        for label in user_labels:
            name = label.get('name', 'Unknown')
            label_id = label.get('id', 'unknown')
            lines.append(f"- **{name}** (`{label_id}`)")
        lines.append("")

    if system_labels:
        lines.append("## System Labels")
        lines.append("")
        for label in system_labels:
            name = label.get('name', 'Unknown')
            label_id = label.get('id', 'unknown')
            lines.append(f"- **{name}** (`{label_id}`)")
        lines.append("")

    return "\n".join(lines)


def format_labels_json(labels: List[Dict[str, Any]]) -> str:
    """
    Format list of labels as JSON.

    Args:
        labels: List of label objects from Gmail API

    Returns:
        JSON string
    """
    formatted = {
        'total': len(labels),
        'labels': [
            {
                'id': label.get('id'),
                'name': label.get('name'),
                'type': label.get('type'),
                'messageListVisibility': label.get('messageListVisibility'),
                'labelListVisibility': label.get('labelListVisibility')
            }
            for label in labels
        ]
    }

    return safe_json_dumps(formatted)


# ===========================================================================
# Success Messages
# ===========================================================================

def format_send_success(message: Dict[str, Any]) -> str:
    """Format successful send operation."""
    msg_id = message.get('id', 'unknown')
    thread_id = message.get('threadId', 'unknown')

    return (
        "✓ Email sent successfully!\n\n"
        f"- **Message ID**: `{msg_id}`\n"
        f"- **Thread ID**: `{thread_id}`"
    )


def format_draft_created(draft: Dict[str, Any]) -> str:
    """Format successful draft creation."""
    draft_id = draft.get('id', 'unknown')

    return (
        "✓ Draft created successfully!\n\n"
        f"- **Draft ID**: `{draft_id}`\n\n"
        "You can send this draft using gmail_send_draft"
    )


def format_label_created(label: Dict[str, Any]) -> str:
    """Format successful label creation."""
    label_id = label.get('id', 'unknown')
    name = label.get('name', 'Unknown')

    return (
        "✓ Label created successfully!\n\n"
        f"- **Name**: {name}\n"
        f"- **Label ID**: `{label_id}`"
    )
