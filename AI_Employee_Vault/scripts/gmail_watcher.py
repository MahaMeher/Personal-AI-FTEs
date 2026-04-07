"""
Gmail Watcher for AI Employee

Monitors Gmail for new important emails and creates action files in Needs_Action folder.
Uses Gmail API to watch for unread, important messages.

Silver Tier Implementation

Usage:
    python scripts/gmail_watcher.py [--interval 120]
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Gmail Watcher - Monitors Gmail for important unread emails.
    
    Creates action files in Needs_Action folder for AI processing.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 120):
        """
        Initialize Gmail Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks (default: 120)
        """
        super().__init__(vault_path, check_interval)
        
        # Gmail configuration
        self.config_dir = self.vault_path / 'config' / 'gmail'
        self.credentials_path = self.config_dir / 'credentials.json'
        self.token_path = self.config_dir / 'token.pickle'
        
        # Keywords that indicate urgent emails
        self.urgent_keywords = ['urgent', 'asap', 'invoice', 'payment', 'contract', 'important']

        # Track processed message IDs - LOAD FROM FILE
        self.processed_ids_file = self.config_dir / 'processed_ids.json'
        self.processed_ids = self._load_processed_ids()

        # Gmail service
        self.service = None

        # Initialize Gmail API
        self._init_gmail()

    def _load_processed_ids(self) -> set:
        """Load processed IDs from file."""
        try:
            import json
            if self.processed_ids_file.exists():
                data = json.loads(self.processed_ids_file.read_text())
                processed = set(data.get('gmail', []))
                self.logger.info(f"Loaded {len(processed)} processed Gmail IDs")
                return processed
        except Exception as e:
            self.logger.debug(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed IDs to file."""
        try:
            import json
            data = {'gmail': list(self.processed_ids)}
            self.processed_ids_file.write_text(json.dumps(data))
            self.logger.debug(f"Saved {len(self.processed_ids)} processed Gmail IDs")
        except Exception as e:
            self.logger.debug(f"Could not save processed IDs: {e}")
        
    def _init_gmail(self):
        """Initialize Gmail API service."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request
            import pickle
            
            # Load token
            if not self.token_path.exists():
                self.logger.error(f"Token file not found: {self.token_path}")
                self.logger.error("Please run: python scripts/gmail_auth.py")
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
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.info(f"Connected to Gmail: {profile['emailAddress']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Gmail initialization failed: {e}")
            return False
    
    def _is_urgent(self, subject: str, snippet: str) -> bool:
        """Check if email contains urgent keywords."""
        text = (subject + ' ' + snippet).lower()
        return any(keyword in text for keyword in self.urgent_keywords)
    
    def _extract_headers(self, headers_list: List[Dict]) -> Dict[str, str]:
        """Extract email headers into dict."""
        headers = {}
        for header in headers_list:
            name = header.get('name', '')
            value = header.get('value', '')
            headers[name] = value
        return headers
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new unread important emails.
        
        Returns:
            List of new messages to process
        """
        if not self.service:
            self._init_gmail()
            if not self.service:
                return []
        
        try:
            # Search for unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            # Filter out already processed
            new_messages = []
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)
                    self.processed_ids.add(msg['id'])
            
            if new_messages:
                self.logger.info(f"Found {len(new_messages)} new email(s)")

            # Save processed IDs
            self._save_processed_ids()

            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []
    
    def create_action_file(self, message: Dict) -> Optional[Path]:
        """
        Create action file for email in Needs_Action folder.
        
        Args:
            message: Gmail message dict
            
        Returns:
            Path to created action file
        """
        try:
            # Get full message
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = self._extract_headers(msg['payload'].get('headers', []))
            
            from_email = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', '')
            
            # Get snippet (preview text)
            snippet = msg.get('snippet', '')
            
            # Determine priority
            priority = 'high' if self._is_urgent(subject, snippet) else 'normal'
            
            # Check if approval needed (new contact, payment, etc.)
            requires_approval = self._check_requires_approval(from_email, subject, snippet)
            
            # Create action file content
            content = f'''---
type: email
from: "{from_email}"
subject: "{subject}"
date: "{date}"
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
message_id: {message['id']}
requires_approval: {str(requires_approval).lower()}
---

# Email Received

**From:** {from_email}  
**Subject:** {subject}  
**Date:** {date}  
**Priority:** {priority.upper()}

## Preview

{snippet}

## Actions Required

'''
            # Add suggested actions based on content
            if self._is_urgent(subject, snippet):
                content += '- [ ] **URGENT**: Respond within 2 hours\n'
            
            if any(kw in snippet.lower() for kw in ['invoice', 'payment', 'pay']):
                content += '- [ ] Process payment request\n'
                content += '- [ ] Create approval request if > $50\n'
            
            if requires_approval:
                content += '- [ ] Get human approval before responding\n'
            
            content += '''
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing

## Notes

*Add notes during processing*

---
*Auto-generated by Gmail Watcher*
'''
            
            # Create action file
            safe_subject = self._sanitize_filename(subject[:50])
            action_file = self.needs_action / f'EMAIL_{message["id"]}_{safe_subject}.md'
            action_file.write_text(content, encoding='utf-8')
            
            # Mark email as READ so we don't process it again
            try:
                self.service.users().messages().modify(
                    userId='me',
                    id=message['id'],
                    body={'addLabelIds': ['READ']}
                ).execute()
                self.logger.info(f"Marked email as READ: {subject[:50]}")
            except Exception as e:
                self.logger.debug(f"Could not mark as read: {e}")
            
            self.logger.info(f"Created action file: {action_file.name}")
            return action_file
            
        except Exception as e:
            self.logger.error(f"Failed to create action file: {e}")
            return None
    
    def _check_requires_approval(self, from_email: str, subject: str, snippet: str) -> bool:
        """
        Check if email requires human approval before responding.
        
        Per Company Handbook:
        - New contacts (first email)
        - Payment/invoice related
        - Contains attachments
        """
        # Payment related
        payment_keywords = ['invoice', 'payment', 'pay', 'money', 'transfer', 'bank']
        text = (subject + ' ' + snippet).lower()
        if any(kw in text for kw in payment_keywords):
            return True
        
        # For now, require approval for all emails (can be refined later)
        return True
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:50]


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('--interval', type=int, default=120,
                       help='Check interval in seconds (default: 120)')
    parser.add_argument('--vault', type=str, default=None,
                       help='Path to vault (default: parent directory)')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault:
        vault_path = args.vault
    else:
        vault_path = str(Path(__file__).parent.parent)
    
    print("=" * 60)
    print("Gmail Watcher - AI Employee (Silver Tier)")
    print("=" * 60)
    print(f"Vault: {vault_path}")
    print(f"Check Interval: {args.interval}s")
    print("=" * 60)
    print("\nMonitoring Gmail for new emails...")
    print("Press Ctrl+C to stop\n")
    
    watcher = GmailWatcher(vault_path, check_interval=args.interval)
    watcher.run()


if __name__ == '__main__':
    main()
