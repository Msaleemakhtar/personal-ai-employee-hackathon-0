"""
Utility functions for Gmail MCP server.

Includes error handling, formatting helpers, and shared utilities.
"""

import json
from typing import Dict, Any
from googleapiclient.errors import HttpError


def handle_api_error(e: Exception) -> str:
    """
    Convert exceptions to user-friendly error messages.

    Args:
        e: Exception from Gmail API or other source

    Returns:
        Formatted error message with guidance
    """
    if isinstance(e, HttpError):
        status_code = e.resp.status
        reason = e.reason if hasattr(e, 'reason') else str(e)

        if status_code == 400:
            return (
                f"Error: Invalid request - {reason}\n\n"
                "Check that all parameters are correctly formatted."
            )
        elif status_code == 401:
            return (
                "Error: Authentication failed.\n\n"
                "Your credentials may have expired. Run: gmail-mcp --auth"
            )
        elif status_code == 403:
            return (
                f"Error: Permission denied - {reason}\n\n"
                "You may not have access to this resource or operation."
            )
        elif status_code == 404:
            return (
                "Error: Resource not found.\n\n"
                "The message, draft, or label ID may be invalid or deleted."
            )
        elif status_code == 429:
            return (
                "Error: Rate limit exceeded.\n\n"
                "Too many requests. Please wait a moment and try again."
            )
        elif status_code >= 500:
            return (
                f"Error: Gmail API server error ({status_code}).\n\n"
                "This is a temporary issue with Gmail. Please try again later."
            )
        else:
            return f"Error: Gmail API error ({status_code}) - {reason}"

    elif "expired" in str(e).lower():
        return (
            "Error: Credentials expired.\n\n"
            "Run: gmail-mcp --auth to re-authenticate"
        )

    else:
        return f"Error: {str(e)}"


def safe_json_dumps(data: Any, indent: int = 2) -> str:
    """
    Safely serialize data to JSON.

    Args:
        data: Data to serialize
        indent: Indentation level

    Returns:
        JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception:
        return json.dumps({"error": "Failed to serialize data"}, indent=indent)


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_email_address(address_string: str) -> str:
    """
    Extract email address from format like "Name <email@example.com>".

    Args:
        address_string: Address string

    Returns:
        Just the email address
    """
    if '<' in address_string and '>' in address_string:
        start = address_string.index('<') + 1
        end = address_string.index('>')
        return address_string[start:end].strip()
    return address_string.strip()


def format_timestamp(timestamp_ms: str) -> str:
    """
    Format Gmail timestamp (milliseconds since epoch) to human-readable.

    Args:
        timestamp_ms: Timestamp in milliseconds

    Returns:
        Formatted timestamp like "2026-01-09 10:30:00 UTC"
    """
    try:
        from datetime import datetime
        timestamp_sec = int(timestamp_ms) / 1000
        dt = datetime.fromtimestamp(timestamp_sec)
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        return timestamp_ms


def get_header_value(headers: list, name: str) -> str:
    """
    Get header value from Gmail message headers list.

    Args:
        headers: List of header dicts from Gmail API
        name: Header name (case-insensitive)

    Returns:
        Header value or empty string
    """
    name_lower = name.lower()
    for header in headers:
        if header.get('name', '').lower() == name_lower:
            return header.get('value', '')
    return ''


def get_label_names(label_ids: list, all_labels: list) -> list:
    """
    Convert label IDs to label names.

    Args:
        label_ids: List of label IDs
        all_labels: List of all label objects from Gmail

    Returns:
        List of label names
    """
    label_map = {label['id']: label.get('name', label['id']) for label in all_labels}
    return [label_map.get(lid, lid) for lid in label_ids]
