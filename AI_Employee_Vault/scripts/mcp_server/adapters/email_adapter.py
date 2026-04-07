"""
Email Adapter for MCP Server

Supports multiple email providers:
- Gmail (OAuth2)
- Outlook (OAuth2)
- Generic SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Optional

from .base_adapter import BaseAdapter


class EmailAdapter(BaseAdapter):
    """
    Email adapter supporting Gmail, Outlook, and SMTP.
    """
    
    def __init__(self, config: dict):
        """
        Initialize email adapter.
        
        Args:
            config: Email configuration
                - provider: 'gmail', 'outlook', or 'smtp'
                - credentials: Path to credentials file
                - smtp_host: SMTP server (for smtp provider)
                - smtp_port: SMTP port (for smtp provider)
        """
        super().__init__(config)
        self.provider = config.get('provider', 'smtp')
        self.credentials_path = config.get('credentials')
        self.smtp_host = config.get('smtp_host')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.signature = config.get('signature', '')
        
        # Provider-specific settings
        self.provider_settings = {
            'gmail': {
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587
            },
            'outlook': {
                'smtp_host': 'smtp-mail.outlook.com',
                'smtp_port': 587
            }
        }
        
    def connect(self) -> bool:
        """
        Test email connection.
        
        Returns:
            True if connection successful
        """
        try:
            # Load credentials if file specified
            if self.credentials_path:
                cred_file = Path(self.credentials_path)
                if cred_file.exists():
                    import json
                    creds = json.loads(cred_file.read_text())
                    self.username = creds.get('email', self.username)
                    self.password = creds.get('password', self.password)
                    
            # Get provider settings
            if self.provider in self.provider_settings:
                settings = self.provider_settings[self.provider]
                if not self.smtp_host:
                    self.smtp_host = settings['smtp_host']
                if not self.smtp_port:
                    self.smtp_port = settings['smtp_port']
                    
            # Test connection
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.quit()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Email connection failed: {e}")
            self.connected = False
            return False
            
    def send_message(self, to: str, subject: str, body: str, 
                     cc: Optional[str] = None, 
                     bcc: Optional[str] = None,
                     attachments: Optional[List[str]] = None) -> dict:
        """
        Send email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            attachments: List of file paths to attach
            
        Returns:
            Result dict with success status and message_id
        """
        if not self.connected:
            if not self.connect():
                return {'success': False, 'error': 'Not connected'}
                
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
                
            # Add body with signature
            full_body = body
            if self.signature:
                full_body += f"\n\n{self.signature}"
            msg.attach(MIMEText(full_body, 'plain'))
            
            # Add attachments
            if attachments:
                from email.mime.base import MIMEBase
                from email import encoders
                
                for filepath in attachments:
                    try:
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={Path(filepath).name}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        print(f"Failed to attach {filepath}: {e}")
                        
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
                
            recipients = [to]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))
                
            server.sendmail(self.username, recipients, msg.as_string())
            server.quit()
            
            return {
                'success': True,
                'message_id': f'email_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_status(self) -> dict:
        """Get email adapter status."""
        return {
            'status': 'connected' if self.connected else 'disconnected',
            'provider': self.provider,
            'username': self.username.split('@')[0] + '***' if self.username else None
        }
        
    def close(self):
        """Close email connection."""
        self.connected = False
        
    def requires_approval(self, **kwargs) -> bool:
        """
        Check if email requires approval.
        
        Approval required when:
        - New contact (first time emailing)
        - Has attachments
        - Contains payment/invoice keywords
        """
        to = kwargs.get('to', '')
        attachments = kwargs.get('attachments', [])
        subject = kwargs.get('subject', '')
        body = kwargs.get('body', '')
        
        # Check for attachments
        if attachments:
            return True
            
        # Check for payment keywords
        payment_keywords = ['invoice', 'payment', 'pay', 'money', 'transfer']
        text = (subject + ' ' + body).lower()
        if any(keyword in text for keyword in payment_keywords):
            return True
            
        # Check if new contact (would need to check history)
        # For now, require approval for all
        return True


# Import datetime for message_id
from datetime import datetime
