"""
Gmail API client wrapper.

Provides async methods for all Gmail operations used by MCP tools.
"""

import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


class GmailClient:
    """
    Wrapper for Gmail API operations.

    Provides convenient methods for messages, drafts, and labels.
    """

    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail client.

        Args:
            credentials: Valid Google OAuth2 credentials
        """
        self.service = build('gmail', 'v1', credentials=credentials)
        self.user_id = 'me'  # 'me' refers to authenticated user

    # ========================================================================
    # Message Operations
    # ========================================================================

    def list_messages(
        self,
        query: str = "",
        max_results: int = 20,
        include_spam_trash: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List messages matching query.

        Args:
            query: Gmail search query
            max_results: Maximum number of results (1-500)
            include_spam_trash: Include SPAM and TRASH

        Returns:
            List of message objects with basic info
        """
        try:
            params = {
                'userId': self.user_id,
                'q': query,
                'maxResults': max_results,
                'includeSpamTrash': include_spam_trash
            }

            result = self.service.users().messages().list(**params).execute()
            messages = result.get('messages', [])

            # Fetch full details for each message
            detailed_messages = []
            for msg in messages:
                try:
                    detailed = self.get_message(msg['id'], format='metadata')
                    detailed_messages.append(detailed)
                except Exception:
                    # Skip messages we can't fetch
                    continue

            return detailed_messages

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def get_message(
        self,
        message_id: str,
        format: str = 'full'
    ) -> Dict[str, Any]:
        """
        Get a specific message.

        Args:
            message_id: Message ID
            format: 'full', 'metadata', 'minimal', or 'raw'

        Returns:
            Message object
        """
        try:
            message = self.service.users().messages().get(
                userId=self.user_id,
                id=message_id,
                format=format
            ).execute()

            return message

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def send_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send a new email message.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            html: Whether body is HTML (True) or plain text (False)

        Returns:
            Sent message object
        """
        try:
            mime_message = self._create_mime_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html=html
            )

            raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            send_message = self.service.users().messages().send(
                userId=self.user_id,
                body={'raw': raw}
            ).execute()

            return send_message

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def reply_to_message(
        self,
        message_id: str,
        body: str,
        reply_all: bool = False,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Reply to an existing message.

        Args:
            message_id: ID of message to reply to
            body: Reply body content
            reply_all: Reply to all recipients (True) or just sender (False)
            html: Whether body is HTML

        Returns:
            Sent reply message object
        """
        try:
            # Get original message
            original = self.get_message(message_id, format='full')
            headers = {h['name']: h['value'] for h in original['payload']['headers']}

            # Extract reply addresses
            from_addr = headers.get('From', '')
            to_addrs = [from_addr]

            if reply_all:
                # Add original recipients
                if 'To' in headers:
                    to_addrs.extend(self._parse_addresses(headers['To']))
                if 'Cc' in headers:
                    to_addrs.extend(self._parse_addresses(headers['Cc']))

            # Remove duplicates
            to_addrs = list(set(to_addrs))

            # Create reply subject
            subject = headers.get('Subject', '')
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"

            # Create reply message
            mime_message = self._create_mime_message(
                to=to_addrs,
                subject=subject,
                body=body,
                html=html,
                thread_id=original.get('threadId'),
                in_reply_to=headers.get('Message-ID'),
                references=headers.get('References')
            )

            raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            reply_message = self.service.users().messages().send(
                userId=self.user_id,
                body={
                    'raw': raw,
                    'threadId': original.get('threadId')
                }
            ).execute()

            return reply_message

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def forward_message(
        self,
        message_id: str,
        to: List[str],
        body: str = ""
    ) -> Dict[str, Any]:
        """
        Forward a message to new recipients.

        Args:
            message_id: ID of message to forward
            to: List of recipient email addresses
            body: Additional message to include

        Returns:
            Sent forwarded message object
        """
        try:
            # Get original message
            original = self.get_message(message_id, format='full')
            headers = {h['name']: h['value'] for h in original['payload']['headers']}

            # Create forward subject
            subject = headers.get('Subject', '')
            if not subject.startswith('Fwd:'):
                subject = f"Fwd: {subject}"

            # Get original body
            original_body = self._extract_body(original)

            # Combine new body with original
            if body:
                full_body = f"{body}\n\n---------- Forwarded message ---------\n{original_body}"
            else:
                full_body = f"---------- Forwarded message ---------\n{original_body}"

            # Send forward
            return self.send_message(
                to=to,
                subject=subject,
                body=full_body,
                html=False
            )

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def modify_labels(
        self,
        message_ids: List[str],
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Modify labels on messages.

        Args:
            message_ids: List of message IDs
            add_labels: Label IDs to add
            remove_labels: Label IDs to remove

        Returns:
            List of modified message objects
        """
        try:
            results = []
            for message_id in message_ids:
                body = {}
                if add_labels:
                    body['addLabelIds'] = add_labels
                if remove_labels:
                    body['removeLabelIds'] = remove_labels

                result = self.service.users().messages().modify(
                    userId=self.user_id,
                    id=message_id,
                    body=body
                ).execute()

                results.append(result)

            return results

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def trash_message(self, message_id: str) -> Dict[str, Any]:
        """
        Move message to trash.

        Args:
            message_id: Message ID

        Returns:
            Trashed message object
        """
        try:
            result = self.service.users().messages().trash(
                userId=self.user_id,
                id=message_id
            ).execute()

            return result

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def delete_message(self, message_id: str) -> None:
        """
        Permanently delete a message.

        Args:
            message_id: Message ID
        """
        try:
            self.service.users().messages().delete(
                userId=self.user_id,
                id=message_id
            ).execute()

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    # ========================================================================
    # Draft Operations
    # ========================================================================

    def list_drafts(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        List draft messages.

        Args:
            max_results: Maximum number of results

        Returns:
            List of draft objects
        """
        try:
            result = self.service.users().drafts().list(
                userId=self.user_id,
                maxResults=max_results
            ).execute()

            drafts = result.get('drafts', [])

            # Fetch full details for each draft
            detailed_drafts = []
            for draft in drafts:
                try:
                    detailed = self.get_draft(draft['id'])
                    detailed_drafts.append(detailed)
                except Exception:
                    continue

            return detailed_drafts

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Get a specific draft.

        Args:
            draft_id: Draft ID

        Returns:
            Draft object
        """
        try:
            draft = self.service.users().drafts().get(
                userId=self.user_id,
                id=draft_id,
                format='full'
            ).execute()

            return draft

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new draft message.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            html: Whether body is HTML

        Returns:
            Created draft object
        """
        try:
            mime_message = self._create_mime_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html=html
            )

            raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            draft = self.service.users().drafts().create(
                userId=self.user_id,
                body={'message': {'raw': raw}}
            ).execute()

            return draft

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def update_draft(
        self,
        draft_id: str,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Update an existing draft.

        Args:
            draft_id: Draft ID to update
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: List of CC recipients
            bcc: List of BCC recipients
            html: Whether body is HTML

        Returns:
            Updated draft object
        """
        try:
            mime_message = self._create_mime_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html=html
            )

            raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            draft = self.service.users().drafts().update(
                userId=self.user_id,
                id=draft_id,
                body={'message': {'raw': raw}}
            ).execute()

            return draft

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def send_draft(self, draft_id: str) -> Dict[str, Any]:
        """
        Send a draft message.

        Args:
            draft_id: Draft ID to send

        Returns:
            Sent message object
        """
        try:
            sent = self.service.users().drafts().send(
                userId=self.user_id,
                body={'id': draft_id}
            ).execute()

            return sent

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    # ========================================================================
    # Label Operations
    # ========================================================================

    def list_labels(self) -> List[Dict[str, Any]]:
        """
        List all labels.

        Returns:
            List of label objects
        """
        try:
            result = self.service.users().labels().list(
                userId=self.user_id
            ).execute()

            return result.get('labels', [])

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def create_label(
        self,
        name: str,
        label_list_visibility: str = "labelShow",
        message_list_visibility: str = "show"
    ) -> Dict[str, Any]:
        """
        Create a new label.

        Args:
            name: Label name
            label_list_visibility: 'labelShow', 'labelShowIfUnread', or 'labelHide'
            message_list_visibility: 'show' or 'hide'

        Returns:
            Created label object
        """
        try:
            label = self.service.users().labels().create(
                userId=self.user_id,
                body={
                    'name': name,
                    'labelListVisibility': label_list_visibility,
                    'messageListVisibility': message_list_visibility
                }
            ).execute()

            return label

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def update_label(
        self,
        label_id: str,
        name: Optional[str] = None,
        label_list_visibility: Optional[str] = None,
        message_list_visibility: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a label.

        Args:
            label_id: Label ID
            name: New label name
            label_list_visibility: Label list visibility
            message_list_visibility: Message list visibility

        Returns:
            Updated label object
        """
        try:
            body = {}
            if name:
                body['name'] = name
            if label_list_visibility:
                body['labelListVisibility'] = label_list_visibility
            if message_list_visibility:
                body['messageListVisibility'] = message_list_visibility

            label = self.service.users().labels().update(
                userId=self.user_id,
                id=label_id,
                body=body
            ).execute()

            return label

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    def delete_label(self, label_id: str) -> None:
        """
        Delete a label.

        Args:
            label_id: Label ID
        """
        try:
            self.service.users().labels().delete(
                userId=self.user_id,
                id=label_id
            ).execute()

        except HttpError as e:
            raise Exception(f"Gmail API error: {e.reason}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _create_mime_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> MIMEText:
        """Create MIME message for sending."""
        if html:
            message = MIMEText(body, 'html')
        else:
            message = MIMEText(body, 'plain')

        message['to'] = ', '.join(to)
        message['subject'] = subject

        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)

        # Add threading headers for replies
        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
        if references:
            message['References'] = references

        return message

    def _extract_body(self, message: Dict[str, Any]) -> str:
        """Extract body from message payload."""
        if 'payload' not in message:
            return ""

        payload = message['payload']

        # Check for simple body
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        # Check for multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

        # Fallback to snippet
        return message.get('snippet', '')

    def _parse_addresses(self, address_string: str) -> List[str]:
        """Parse comma-separated email addresses."""
        # Simple parsing - could be enhanced
        addresses = [addr.strip() for addr in address_string.split(',')]
        return [addr for addr in addresses if '@' in addr]
