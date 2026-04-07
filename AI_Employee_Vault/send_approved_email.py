#!/usr/bin/env python3
"""
Send approved email from APPROVED/TEST_STATUS_FIX.md
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import shutil
import yaml

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Approved action file
APPROVED_FILE = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Approved\\TEST_STATUS_FIX.md"

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown."""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            return yaml.safe_load(parts[1]), parts[2] if len(parts) > 2 else ''
    return {}, content

def send_email(to, subject, body):
    """Send email and return results."""
    results = {
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
        "recipient": to,
        "subject": subject,
        "errors": []
    }

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        results["status"] = "skipped"
        results["errors"].append("Email credentials not configured (SENDER_EMAIL/SENDER_PASSWORD)")
        print("⚠️ Email credentials not configured in environment variables")
        print("   Set SENDER_EMAIL and SENDER_PASSWORD to enable email sending")
        return results

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        print(f"Sending email to: {to}")
        server.send_message(msg)
        server.quit()

        results["status"] = "success"
        results["sent_at"] = datetime.now().isoformat()
        print(f"✓ Email sent successfully to {to}")

    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(str(e))
        print(f"✗ Failed to send email: {str(e)}")

    return results

def main():
    print("=" * 60)
    print("Executing: APPROVED/TEST_STATUS_FIX.md")
    print("=" * 60)

    # Read approved file
    with open(APPROVED_FILE, 'r') as f:
        content = f.read()

    frontmatter, body = parse_frontmatter(content)
    
    to = frontmatter.get('to', '')
    subject = frontmatter.get('subject', '')
    email_body = frontmatter.get('body', '')

    print(f"\nRecipient: {to}")
    print(f"Subject: {subject}")
    print(f"Body: {email_body}")
    print("\n" + "=" * 60 + "\n")

    results = send_email(to, subject, email_body)

    # Save execution report
    report_file = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\EMAIL_EXECUTION_REPORT_TEST_STATUS_FIX.md"
    with open(report_file, 'w') as f:
        f.write(f"""---
type: execution_report
action: send_email
executed: {datetime.now().isoformat()}
status: {results['status']}
---

# Email Execution Report

## Approved Action
- **File**: TEST_STATUS_FIX.md
- **Action**: Send Email
- **Recipient**: {results['recipient']}
- **Subject**: {results['subject']}

## Execution Result

| Field | Value |
|-------|-------|
| **Status** | {results['status']} |
| **Timestamp** | {results['timestamp']} |
| **Sent At** | {results.get('sent_at', 'N/A')} |

## Email Content
```
{email_body}
```

## Errors
{chr(10).join('- ' + e for e in results['errors']) if results['errors'] else 'None'}

---
*Executed by AI Employee per approved action workflow*
""")

    print(f"\nExecution report saved to: {report_file}")

    # Move approved file to Done if successful
    if results["status"] == "success":
        dst = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Done\\TEST_STATUS_FIX.md"
        try:
            shutil.move(APPROVED_FILE, dst)
            print(f"✓ Moved approval file to Done folder")
        except Exception as e:
            print(f"⚠️ Could not move file to Done: {str(e)}")
    elif results["status"] == "skipped":
        print("\n⚠️ File remains in Approved/ - configure credentials to execute")

    return results

if __name__ == "__main__":
    main()
