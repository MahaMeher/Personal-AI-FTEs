"""
MCP Email Server

Sends emails via Gmail API using OAuth2.
Called by Qwen Code when processing approved email actions.

Usage:
    python mcp/email_server.py send --to "test@example.com" --subject "Hello" --body "Hi"
"""

import argparse
import json
import sys
from pathlib import Path

# Add mcp folder to path
sys.path.insert(0, str(Path(__file__).parent))

from adapters.email_adapter import EmailAdapter


def load_config():
    """Load email configuration."""
    vault_path = Path(__file__).parent.parent
    config_file = vault_path / 'config' / 'mcp' / 'adapters.json'

    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            return config.get('adapters', {}).get('email', {})

    # Default config - uses OAuth2 from token.pickle
    return {
        'provider': 'gmail',
        'signature': '\n\nBest regards,\nAI Employee'
    }


def send_email(to: str, subject: str, body: str, cc: str = None):
    """Send email via MCP using Gmail API OAuth2."""
    config = load_config()
    adapter = EmailAdapter(config)

    print("=" * 60)
    print("MCP Email Server")
    print("=" * 60)

    # Connect using OAuth2 (reuses token.pickle from gmail_watcher)
    if not adapter.connect():
        print("❌ Failed to connect to Gmail API")
        print("   Ensure you've run: python scripts/gmail_auth.py")
        return False

    # Send
    result = adapter.send_message(
        to=to,
        subject=subject,
        body=body,
        cc=cc
    )

    adapter.close()

    if result.get('success'):
        print("=" * 60)
        print("✅ Email sent successfully!")
        print(f"   Message ID: {result.get('message_id', 'unknown')}")
        print("=" * 60)
        return True
    else:
        print("=" * 60)
        print(f"❌ Email failed: {result.get('error', 'Unknown error')}")
        print("=" * 60)
        return False


def main():
    parser = argparse.ArgumentParser(description='MCP Email Server')
    parser.add_argument('action', choices=['send', 'test', 'status'],
                       help='Action to perform')
    parser.add_argument('--to', help='Recipient email')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--body-file', help='File containing email body (for complex content)')
    parser.add_argument('--cc', help='CC recipients')

    args = parser.parse_args()

    if args.action == 'send':
        if not all([args.to, args.subject]):
            print("Error: --to, --subject required for send")
            sys.exit(1)
        
        # Get body from file or argument
        body = args.body
        if args.body_file:
            from pathlib import Path
            body = Path(args.body_file).read_text(encoding='utf-8')
        
        if not body:
            print("Error: --body or --body-file required for send")
            sys.exit(1)
            
        success = send_email(args.to, args.subject, body, args.cc)
        sys.exit(0 if success else 1)
    
    elif args.action == 'test':
        config = load_config()
        adapter = EmailAdapter(config)
        print("Testing email connection...")
        if adapter.connect():
            print("✅ Email adapter connected successfully")
        else:
            print("❌ Email adapter connection failed")
        adapter.close()
    
    elif args.action == 'status':
        config = load_config()
        print("Email Server Status:")
        print(f"  Provider: {config.get('provider', 'gmail')}")
        print(f"  SMTP Host: {config.get('smtp_host', 'smtp.gmail.com')}")
        print(f"  SMTP Port: {config.get('smtp_port', 587)}")
        print(f"  Signature: {config.get('signature', 'configured')}")


if __name__ == '__main__':
    main()
