"""
Approved Email Executor

Scans Approved/ folder for email approval files and sends them automatically.
Moves processed files to Done/ folder.

Usage:
    python scripts/execute_approved_emails.py
"""

import sys
import re
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'mcp'))

from email_server import send_email as mcp_send_email


class ApprovedEmailExecutor:
    """Execute approved emails from Approved/ folder."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / 'Approved'
        self.done_dir = self.vault_path / 'Done'
        self.logs_dir = self.vault_path / 'Logs'
        
        # Ensure directories exist
        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def find_approved_emails(self) -> list:
        """Find all approved email files in Approved/ folder."""
        approved_files = []
        
        if not self.approved_dir.exists():
            return approved_files
        
        for file_path in self.approved_dir.glob('*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check if it's an email approval file
                if 'type: email' in content or 'type: email_approval' in content:
                    # Extract email details
                    email_data = self.extract_email_data(content, file_path)
                    if email_data:
                        approved_files.append({
                            'file': file_path,
                            'data': email_data
                        })
                        
            except Exception as e:
                print(f"Error reading {file_path.name}: {e}")
        
        return approved_files
    
    def extract_email_data(self, content: str, file_path: Path) -> dict:
        """Extract email data from approval file."""
        data = {
            'to': '',
            'subject': '',
            'body': '',
            'cc': None
        }
        
        # Extract from YAML frontmatter
        to_match = re.search(r'to:\s*["\']?([^"\'\n]+)["\']?', content)
        if to_match:
            data['to'] = to_match.group(1).strip()
        
        subject_match = re.search(r'subject:\s*["\']?([^"\'\n]+)["\']?', content)
        if subject_match:
            data['subject'] = subject_match.group(1).strip()
        
        # Extract body from frontmatter or markdown
        body_match = re.search(r'body:\s*["\']?([^"\'\n]+)["\']?', content)
        if body_match:
            data['body'] = body_match.group(1).strip()
        else:
            # Try to extract from markdown section
            body_section = re.search(r'## Body\s*\n\n(.*?)(?:\n##|\n---|$)', content, re.DOTALL)
            if body_section:
                data['body'] = body_section.group(1).strip()
            else:
                # Try Email Content section
                content_section = re.search(r'## Email Content\s*\n\n(.*?)(?:\n##|\n---|$)', content, re.DOTALL)
                if content_section:
                    data['body'] = content_section.group(1).strip()
        
        # Extract CC if present
        cc_match = re.search(r'cc:\s*["\']?([^"\'\n]+)["\']?', content)
        if cc_match:
            data['cc'] = cc_match.group(1).strip()
        
        # Validate required fields
        if not data['to'] or not data['subject']:
            print(f"⚠️  {file_path.name}: Missing required fields (to/subject)")
            return None
        
        return data
    
    def send_approved_email(self, email_info: dict) -> bool:
        """Send an approved email."""
        file_path = email_info['file']
        data = email_info['data']
        
        print(f"\n{'='*60}")
        print(f"📧 Sending Email from: {file_path.name}")
        print(f"{'='*60}")
        print(f"   To: {data['to']}")
        print(f"   Subject: {data['subject']}")
        print(f"   Body: {data['body'][:100]}...")
        print(f"{'='*60}")
        
        # Send via MCP email server
        success = mcp_send_email(
            to=data['to'],
            subject=data['subject'],
            body=data['body'],
            cc=data['cc']
        )
        
        if success:
            # Update file status
            self.mark_as_sent(file_path)
            
            # Move to Done
            self.move_to_done(file_path)
            
            # Log the action
            self.log_action(file_path, data, True)
            
            return True
        else:
            # Log the failure
            self.log_action(file_path, data, False)
            
            return False
    
    def mark_as_sent(self, file_path: Path):
        """Mark file as sent."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Update status
            content = re.sub(
                r'status:\s*\w+',
                'status: sent',
                content
            )
            
            # Add sent timestamp
            if 'sent_at:' not in content:
                content = content.replace(
                    'status: sent',
                    f'status: sent\nsent_at: {datetime.now().isoformat()}'
                )
            
            file_path.write_text(content, encoding='utf-8')
            
        except Exception as e:
            print(f"Error marking file as sent: {e}")
    
    def move_to_done(self, file_path: Path):
        """Move processed file to Done/ folder."""
        try:
            dest_path = self.done_dir / file_path.name
            
            # Handle duplicate names
            counter = 1
            while dest_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                dest_path = self.done_dir / f'{stem}_{counter}{suffix}'
                counter += 1
            
            shutil.move(str(file_path), str(dest_path))
            print(f"   ✓ Moved to Done/: {dest_path.name}")
            
        except Exception as e:
            print(f"   ⚠️  Error moving to Done: {e}")
    
    def log_action(self, file_path: Path, data: dict, success: bool):
        """Log the email action."""
        log_file = self.logs_dir / f'email_actions_{datetime.now().strftime("%Y%m%d")}.jsonl'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': file_path.name,
            'to': data['to'],
            'subject': data['subject'],
            'success': success
        }
        
        import json
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def execute_all(self) -> dict:
        """Execute all approved emails."""
        print("=" * 60)
        print("AI Employee - Approved Email Executor")
        print("=" * 60)
        
        # Find approved emails
        approved_emails = self.find_approved_emails()
        
        if not approved_emails:
            print("\n✅ No approved emails to process")
            print("=" * 60)
            return {'total': 0, 'sent': 0, 'failed': 0}
        
        print(f"\n📋 Found {len(approved_emails)} approved email(s) to send")
        print("=" * 60)
        
        # Process each email
        results = {'total': len(approved_emails), 'sent': 0, 'failed': 0}
        
        for email_info in approved_emails:
            try:
                if self.send_approved_email(email_info):
                    results['sent'] += 1
                    print(f"   ✅ Sent successfully!")
                else:
                    results['failed'] += 1
                    print(f"   ❌ Failed to send")
            except Exception as e:
                results['failed'] += 1
                print(f"   ❌ Error: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Execution Summary")
        print("=" * 60)
        print(f"   Total: {results['total']}")
        print(f"   Sent: {results['sent']}")
        print(f"   Failed: {results['failed']}")
        print("=" * 60)
        
        return results


def main():
    """Main entry point."""
    # Get vault path
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        vault_path = str(Path(__file__).parent.parent)
    
    executor = ApprovedEmailExecutor(vault_path)
    results = executor.execute_all()
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
