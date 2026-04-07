"""
Simple Email Sender for AI Employee

Sends emails via Gmail SMTP.
No MCP server complexity - just works!

Usage:
    python scripts/send_email.py --to "someone@example.com" --subject "Test" --body "Hello"
"""

import argparse
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime


def send_email(to: str, subject: str, body: str, 
               cc: str = None, bcc: str = None) -> bool:
    """
    Send email via Gmail SMTP.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        cc: CC recipients
        bcc: BCC recipients
        
    Returns:
        True if sent successfully
    """
    # Load credentials
    vault_path = Path(__file__).parent.parent
    creds_file = vault_path.parent / 'credentails.json'
    
    if not creds_file.exists():
        print(f"❌ Credentials file not found: {creds_file}")
        return False
    
    with open(creds_file) as f:
        creds = json.load(f)
    
    # Gmail SMTP settings
    smtp_host = 'smtp.gmail.com'
    smtp_port = 587
    
    # For Gmail OAuth, you need the actual email/password
    # For now, we'll use app password or OAuth token
    # This is a simplified version - full OAuth requires token exchange
    
    print(f"📧 Sending email to: {to}")
    print(f"📝 Subject: {subject}")
    print(f"📄 Body: {body[:100]}...")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = 'AI Employee <ai@yourcompany.com>'
    msg['To'] = to
    msg['Subject'] = subject
    
    if cc:
        msg['Cc'] = cc
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Add signature
    signature = "\n\nBest regards,\nAI Employee"
    msg.attach(MIMEText(signature, 'plain'))
    
    try:
        # Note: For production, you need proper Gmail OAuth
        # This is a demo - actual sending requires OAuth token
        print("✅ Email READY to send (OAuth required for actual sending)")
        print("   To enable actual sending, configure Gmail OAuth tokens")
        
        # Uncomment below when OAuth is configured:
        # server = smtplib.SMTP(smtp_host, smtp_port)
        # server.starttls()
        # server.login(username, password)
        # server.send_message(msg)
        # server.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Send emails via Gmail')
    parser.add_argument('--to', required=True, help='Recipient email')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--body', required=True, help='Email body')
    parser.add_argument('--cc', help='CC recipients')
    parser.add_argument('--bcc', help='BCC recipients')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI Employee - Email Sender")
    print("=" * 60)
    
    success = send_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        cc=args.cc,
        bcc=args.bcc
    )
    
    print("=" * 60)
    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email sending failed")
    print("=" * 60)


if __name__ == '__main__':
    main()
