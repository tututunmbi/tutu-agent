"""
Gmail integration â Imani's hands for email.
Uses a service account with domain-wide delegation to impersonate Tutu.
"""
import os
import json
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", "")
TUTU_EMAIL = os.getenv("TUTU_EMAIL", "")


class GmailManager:
    def __init__(self):
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initialize Gmail API service with domain-wide delegation."""
        if not GOOGLE_CREDENTIALS or not TUTU_EMAIL:
            logger.warning("Gmail not configured: GOOGLE_CREDENTIALS or TUTU_EMAIL missing")
            return

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            creds = creds.with_subject(TUTU_EMAIL)

            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail connected for %s", TUTU_EMAIL)
        except Exception as e:
            logger.error("Gmail init error: %s", e)
            self.service = None

    def is_connected(self) -> bool:
        return self.service is not None

    def get_recent_emails(self, max_results: int = 10, query: str = None) -> dict:
        """Get recent emails from Tutu's inbox.

        Args:
            max_results: Number of emails to return (default 10, max 20)
            query: Gmail search query (e.g., 'from:someone@example.com', 'is:unread', 'subject:TDPF')

        Returns:
            Dict with 'success' bool and 'emails' list or 'error' string.
        """
        if not self.service:
            return {"success": False, "error": "Gmail not connected. GOOGLE_CREDENTIALS and TUTU_EMAIL need to be set, and Gmail API + domain delegation must be enabled."}

        try:
            max_results = min(max_results, 20)
            params = {
                "userId": "me",
                "maxResults": max_results,
                "labelIds": ["INBOX"],
            }
            if query:
                params["q"] = query

            results = self.service.users().messages().list(**params).execute()
            messages = results.get("messages", [])

            if not messages:
                return {"success": True, "emails": [], "message": "No emails found matching your query."}

            emails = []
            for msg_ref in messages:
                msg = self.service.users().messages().get(
                    userId="me",
                    id=msg_ref["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()

                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                snippet = msg.get("snippet", "")
                labels = msg.get("labelIds", [])

                emails.append({
                    "id": msg["id"],
                    "thread_id": msg.get("threadId", ""),
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "subject": headers.get("Subject", "(no subject)"),
                    "date": headers.get("Date", ""),
                    "snippet": snippet,
                    "is_unread": "UNREAD" in labels,
                    "is_starred": "STARRED" in labels,
                })

            return {"success": True, "emails": emails, "count": len(emails)}

        except Exception as e:
            logger.error("Gmail get_recent_emails error: %s", e)
            return {"success": False, "error": str(e)}

    def read_email(self, email_id: str) -> dict:
        """Read the full content of a specific email.

        Args:
            email_id: The email ID (from get_recent_emails results)

        Returns:
            Dict with full email content.
        """
        if not self.service:
            return {"success": False, "error": "Gmail not connected."}

        try:
            msg = self.service.users().messages().get(
                userId="me",
                id=email_id,
                format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

            # Extract body text
            body = self._extract_body(msg.get("payload", {}))

            return {
                "success": True,
                "id": msg["id"],
                "thread_id": msg.get("threadId", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "cc": headers.get("Cc", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "date": headers.get("Date", ""),
                "body": body[:5000],  # Limit body length to avoid overwhelming context
                "labels": msg.get("labelIds", []),
            }

        except Exception as e:
            logger.error("Gmail read_email error: %s", e)
            return {"success": False, "error": str(e)}

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from email payload."""
        body_text = ""

        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            body_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        elif payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
                elif part.get("mimeType", "").startswith("multipart/"):
                    body_text = self._extract_body(part)
                    if body_text:
                        break

        # Fallback: try HTML if no plain text
        if not body_text:
            if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
                html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
                # Strip HTML tags roughly
                import re
                body_text = re.sub(r"<[^>]+>", "", html)
                body_text = body_text.strip()
            elif payload.get("parts"):
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                        html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                        import re
                        body_text = re.sub(r"<[^>]+>", "", html)
                        body_text = body_text.strip()
                        break

        return body_text

    def send_email(self, to: str, subject: str, body: str, cc: str = "", reply_to_id: str = None) -> dict:
        """Send an email from Tutu's account.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional CC recipients (comma-separated)
            reply_to_id: Optional message ID to reply to (creates a thread)

        Returns:
            Dict with 'success' bool and sent message info.
        """
        if not self.service:
            return {"success": False, "error": "Gmail not connected."}

        try:
            message = MIMEMultipart()
            message["to"] = to
            message["from"] = TUTU_EMAIL
            message["subject"] = subject
            if cc:
                message["cc"] = cc

            message.attach(MIMEText(body, "plain"))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            send_body = {"raw": raw}

            # If replying, include the thread ID
            if reply_to_id:
                try:
                    original = self.service.users().messages().get(
                        userId="me", id=reply_to_id, format="metadata"
                    ).execute()
                    send_body["threadId"] = original.get("threadId", "")
                except Exception:
                    pass  # Send as new email if thread lookup fails

            sent = self.service.users().messages().send(
                userId="me",
                body=send_body
            ).execute()

            return {
                "success": True,
                "message_id": sent.get("id", ""),
                "thread_id": sent.get("threadId", ""),
                "message": f"Email sent to {to}."
            }

        except Exception as e:
            logger.error("Gmail send_email error: %s", e)
            return {"success": False, "error": str(e)}

    def draft_email(self, to: str, subject: str, body: str, cc: str = "") -> dict:
        """Create a draft email (doesn't send it). Tutu can review and send manually.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional CC recipients

        Returns:
            Dict with 'success' bool and draft info.
        """
        if not self.service:
            return {"success": False, "error": "Gmail not connected."}

        try:
            message = MIMEMultipart()
            message["to"] = to
            message["from"] = TUTU_EMAIL
            message["subject"] = subject
            if cc:
                message["cc"] = cc

            message.attach(MIMEText(body, "plain"))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            draft = self.service.users().drafts().create(
                userId="me",
                body={"message": {"raw": raw}}
            ).execute()

            return {
                "success": True,
                "draft_id": draft.get("id", ""),
                "message": f"Draft created for {to}. Tutu can review and send from Gmail."
            }

        except Exception as e:
            logger.error("Gmail draft_email error: %s", e)
            return {"success": False, "error": str(e)}

    def search_emails(self, query: str, max_results: int = 10) -> dict:
        """Search emails with Gmail query syntax.

        Args:
            query: Gmail search query. Examples:
                - 'from:ejiro@ginger.com'
                - 'subject:TDPF after:2026/03/01'
                - 'is:unread'
                - 'has:attachment filename:pdf'
                - 'nnenna OR koyo'
            max_results: Number of results (default 10, max 20)

        Returns:
            Dict with matching emails.
        """
        return self.get_recent_emails(max_results=max_results, query=query)
