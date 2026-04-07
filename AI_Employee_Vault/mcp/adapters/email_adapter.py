"""
Email Adapter for MCP Server

Sends emails via Gmail API using OAuth2 (same token as gmail_watcher.py).
No app password needed - reuses existing token.pickle.
"""

import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .base_adapter import BaseAdapter


class EmailAdapter(BaseAdapter):
    """Email adapter for sending emails via Gmail API with OAuth2."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.signature = config.get('signature', '\n\nBest regards,\nAI Employee')
        
        # Vault paths
        self.vault_path = Path(__file__).parent.parent.parent
        self.token_path = self.vault_path / 'config' / 'gmail' / 'token.pickle'
        
        # Gmail service
        self.service = None
        self.gmail_email = None

    def connect(self) -> bool:
        """Initialize Gmail API service using existing OAuth2 token."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            import pickle

            # Load token (same as gmail_watcher.py uses)
            if not self.token_path.exists():
                print(f"❌ Token file not found: {self.token_path}")
                print("   Your Gmail watcher token exists - will use it for sending!")
                return False

            with open(self.token_path, 'rb') as f:
                creds = pickle.load(f)

            # Refresh if expired
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self.token_path, 'wb') as f:
                    pickle.dump(creds, f)

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Get profile to verify connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.gmail_email = profile['emailAddress']
            
            self.connected = True
            # Use ASCII-safe output for Windows console compatibility
            print(f"[OK] Connected to Gmail: {self.gmail_email}")
            return True

        except Exception as e:
            print(f"[ERROR] Gmail API connection failed: {e}")
            self.connected = False
            return False

    def _create_message(self, to: str, subject: str, body: str,
                        cc: Optional[str] = None) -> dict:
        """Create MIME message for Gmail API."""
        msg = MIMEMultipart()
        msg['From'] = self.gmail_email
        msg['To'] = to
        msg['Subject'] = subject

        if cc:
            msg['Cc'] = cc

        # Add body with signature
        full_body = body + self.signature
        msg.attach(MIMEText(full_body, 'plain'))

        # Encode for Gmail API
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        return {'raw': raw}

    def send_message(self, to: str, subject: str, body: str,
                     cc: Optional[str] = None,
                     attachments: Optional[List[str]] = None) -> dict:
        """
        Send email message via Gmail API.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            cc: CC recipients
            attachments: List of attachment paths (not yet implemented)

        Returns:
            Result dict with success status
        """
        if not self.connected or not self.service:
            if not self.connect():
                return {
                    'success': False,
                    'error': 'Not connected to Gmail API'
                }

        try:
            print(f"[INFO] Sending email:")
            print(f"   From: {self.gmail_email}")
            print(f"   To: {to}")
            print(f"   Subject: {subject}")
            preview = body[:50].replace('\n', ' ')
            print(f"   Body: {preview}...")

            # Create message
            message = self._create_message(to, subject, body, cc)

            # Send via Gmail API
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            print(f"[OK] Email SENT successfully!")
            print(f"   Message ID: {sent_message['id']}")
            print(f"   Thread ID: {sent_message['threadId']}")

            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message['threadId'],
                'status': 'sent'
            }

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Email failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def close(self):
        """Close connection."""
        self.service = None
        self.connected = False
