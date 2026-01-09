"""
Pydantic models for Gmail MCP server tool inputs.

All tool inputs must be validated using these models.
"""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class MessageFormat(str, Enum):
    """Message retrieval format."""
    FULL = "full"        # Complete message with body
    METADATA = "metadata"  # Headers and metadata only
    MINIMAL = "minimal"    # Just ID and thread ID


# ============================================================================
# Message Operation Models
# ============================================================================

class ListMessagesInput(BaseModel):
    """Input for listing Gmail messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: Optional[str] = Field(
        default="",
        description="Gmail search query (e.g., 'is:unread', 'from:user@example.com after:2026/01/01', 'has:attachment')",
        max_length=500
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of messages to return (1-100)",
        ge=1,
        le=100
    )
    include_spam_trash: Optional[bool] = Field(
        default=False,
        description="Include messages in SPAM and TRASH"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data"
    )


class GetMessageInput(BaseModel):
    """Input for getting a specific message."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_id: str = Field(
        ...,
        description="Gmail message ID",
        min_length=1,
        max_length=100
    )
    format: MessageFormat = Field(
        default=MessageFormat.FULL,
        description="Message format: 'full' for complete message, 'metadata' for headers only, 'minimal' for IDs only"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class SendMessageInput(BaseModel):
    """Input for sending a new email."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    to: List[str] = Field(
        ...,
        description="Recipient email addresses (e.g., ['user@example.com', 'team@company.com'])",
        min_items=1,
        max_items=50
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=500
    )
    body: str = Field(
        ...,
        description="Email body content",
        min_length=1
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="CC recipient email addresses",
        max_items=50
    )
    bcc: Optional[List[str]] = Field(
        default=None,
        description="BCC recipient email addresses",
        max_items=50
    )
    html: Optional[bool] = Field(
        default=False,
        description="Whether body is HTML (True) or plain text (False)"
    )

    @field_validator('to', 'cc', 'bcc')
    @classmethod
    def validate_emails(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate email addresses."""
        if v is None:
            return v
        # Basic validation - real validation happens in Gmail API
        for email in v:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email address: {email}")
        return v


class ReplyToMessageInput(BaseModel):
    """Input for replying to a message."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_id: str = Field(
        ...,
        description="ID of message to reply to",
        min_length=1,
        max_length=100
    )
    body: str = Field(
        ...,
        description="Reply body content",
        min_length=1
    )
    reply_all: Optional[bool] = Field(
        default=False,
        description="Reply to all recipients (True) or just sender (False)"
    )
    html: Optional[bool] = Field(
        default=False,
        description="Whether body is HTML (True) or plain text (False)"
    )


class ForwardMessageInput(BaseModel):
    """Input for forwarding a message."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_id: str = Field(
        ...,
        description="ID of message to forward",
        min_length=1,
        max_length=100
    )
    to: List[str] = Field(
        ...,
        description="Forward recipient email addresses",
        min_items=1,
        max_items=50
    )
    body: Optional[str] = Field(
        default="",
        description="Additional message to include before forwarded content"
    )

    @field_validator('to')
    @classmethod
    def validate_emails(cls, v: List[str]) -> List[str]:
        """Validate email addresses."""
        for email in v:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email address: {email}")
        return v


class ModifyLabelsInput(BaseModel):
    """Input for modifying message labels."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_ids: List[str] = Field(
        ...,
        description="List of message IDs to modify",
        min_items=1,
        max_items=100
    )
    add_labels: Optional[List[str]] = Field(
        default=None,
        description="Label IDs to add (e.g., ['INBOX', 'UNREAD', 'Label_123'])"
    )
    remove_labels: Optional[List[str]] = Field(
        default=None,
        description="Label IDs to remove (e.g., ['INBOX', 'UNREAD'])"
    )

    @field_validator('add_labels', 'remove_labels')
    @classmethod
    def validate_labels_not_empty(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure labels list is not empty if provided."""
        if v is not None and len(v) == 0:
            return None
        return v


class TrashMessageInput(BaseModel):
    """Input for moving message to trash."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_id: str = Field(
        ...,
        description="Message ID to move to trash",
        min_length=1,
        max_length=100
    )


class DeleteMessageInput(BaseModel):
    """Input for permanently deleting a message."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_id: str = Field(
        ...,
        description="Message ID to permanently delete (WARNING: Cannot be undone)",
        min_length=1,
        max_length=100
    )


# ============================================================================
# Draft Operation Models
# ============================================================================

class ListDraftsInput(BaseModel):
    """Input for listing drafts."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of drafts to return (1-100)",
        ge=1,
        le=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetDraftInput(BaseModel):
    """Input for getting a specific draft."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    draft_id: str = Field(
        ...,
        description="Draft ID",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateDraftInput(BaseModel):
    """Input for creating a new draft."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    to: List[str] = Field(
        ...,
        description="Recipient email addresses",
        min_items=1,
        max_items=50
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=500
    )
    body: str = Field(
        ...,
        description="Email body content",
        min_length=1
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="CC recipient email addresses",
        max_items=50
    )
    bcc: Optional[List[str]] = Field(
        default=None,
        description="BCC recipient email addresses",
        max_items=50
    )
    html: Optional[bool] = Field(
        default=False,
        description="Whether body is HTML (True) or plain text (False)"
    )

    @field_validator('to', 'cc', 'bcc')
    @classmethod
    def validate_emails(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate email addresses."""
        if v is None:
            return v
        for email in v:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email address: {email}")
        return v


class UpdateDraftInput(BaseModel):
    """Input for updating an existing draft."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    draft_id: str = Field(
        ...,
        description="Draft ID to update",
        min_length=1,
        max_length=100
    )
    to: List[str] = Field(
        ...,
        description="Recipient email addresses",
        min_items=1,
        max_items=50
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=500
    )
    body: str = Field(
        ...,
        description="Email body content",
        min_length=1
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="CC recipient email addresses"
    )
    bcc: Optional[List[str]] = Field(
        default=None,
        description="BCC recipient email addresses"
    )
    html: Optional[bool] = Field(
        default=False,
        description="Whether body is HTML"
    )

    @field_validator('to', 'cc', 'bcc')
    @classmethod
    def validate_emails(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate email addresses."""
        if v is None:
            return v
        for email in v:
            if not email or '@' not in email:
                raise ValueError(f"Invalid email address: {email}")
        return v


class SendDraftInput(BaseModel):
    """Input for sending a draft."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    draft_id: str = Field(
        ...,
        description="Draft ID to send",
        min_length=1,
        max_length=100
    )


# ============================================================================
# Label Operation Models
# ============================================================================

class ListLabelsInput(BaseModel):
    """Input for listing labels."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateLabelInput(BaseModel):
    """Input for creating a new label."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: str = Field(
        ...,
        description="Label name (e.g., 'Work', 'Important', 'Project X')",
        min_length=1,
        max_length=100
    )
    label_list_visibility: Optional[str] = Field(
        default="labelShow",
        description="Visibility in label list: 'labelShow', 'labelShowIfUnread', 'labelHide'"
    )
    message_list_visibility: Optional[str] = Field(
        default="show",
        description="Visibility in message list: 'show' or 'hide'"
    )


class UpdateLabelInput(BaseModel):
    """Input for updating a label."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    label_id: str = Field(
        ...,
        description="Label ID to update",
        min_length=1,
        max_length=100
    )
    name: Optional[str] = Field(
        default=None,
        description="New label name",
        max_length=100
    )
    label_list_visibility: Optional[str] = Field(
        default=None,
        description="Label list visibility: 'labelShow', 'labelShowIfUnread', 'labelHide'"
    )
    message_list_visibility: Optional[str] = Field(
        default=None,
        description="Message list visibility: 'show' or 'hide'"
    )


class DeleteLabelInput(BaseModel):
    """Input for deleting a label."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    label_id: str = Field(
        ...,
        description="Label ID to delete (WARNING: Cannot be undone)",
        min_length=1,
        max_length=100
    )


# ============================================================================
# Organization Tool Models
# ============================================================================

class MarkAsReadInput(BaseModel):
    """Input for marking messages as read/unread."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_ids: List[str] = Field(
        ...,
        description="List of message IDs to mark",
        min_items=1,
        max_items=100
    )
    read: bool = Field(
        ...,
        description="True to mark as read, False to mark as unread"
    )


class ArchiveMessagesInput(BaseModel):
    """Input for archiving messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    message_ids: List[str] = Field(
        ...,
        description="List of message IDs to archive",
        min_items=1,
        max_items=100
    )
