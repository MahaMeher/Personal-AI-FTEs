#!/usr/bin/env python3
"""
Send approved email response to Seher Irish (seherirish@gmail.com)
Approval File: APPROVAL_Email_Response_SeherIrish_2026-03-20.md
Response Option: A (Friendly Acknowledgment)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import shutil

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Approved action details
APPROVED_FILE = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Approved\\APPROVAL_Email_Response_SeherIrish_2026-03-20.md"
TO_EMAIL = "seherirish@gmail.com"
TO_NAME = "Seher Irish"
SUBJECT = "Re: How are you?"
BODY = """Hi Seher,

I'm doing well, thank you for asking! I hope you're having a great day too.

Best regards,
AI Employee
"""

def send_email():
    """Send email and return results."""
    results = {
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
        "recipient": TO_EMAIL,
        "subject": SUBJECT,
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
        msg['To'] = TO_EMAIL
        msg['Subject'] = SUBJECT
        msg.attach(MIMEText(BODY, 'plain'))

        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        print(f"Sending email to: {TO_EMAIL}")
        server.send_message(msg)
        server.quit()

        results["status"] = "success"
        results["sent_at"] = datetime.now().isoformat()
        print(f"✓ Email sent successfully to {TO_EMAIL}")

    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(str(e))
        print(f"✗ Failed to send email: {str(e)}")

    return results

def main():
    print("=" * 60)
    print("Executing: APPROVAL_Email_Response_SeherIrish_2026-03-20.md")
    print("=" * 60)
    print(f"\nRecipient: {TO_NAME} <{TO_EMAIL}>")
    print(f"Subject: {SUBJECT}")
    print(f"Response Option: A (Friendly Acknowledgment)")
    print("\n" + "=" * 60 + "\n")

    results = send_email()

    # Save execution report
    report_file = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\EMAIL_EXECUTION_REPORT_SeherIrish_2026-03-20.md"
    with open(report_file, 'w') as f:
        f.write(f"""---
type: execution_report
action: send_email
executed: {datetime.now().isoformat()}
status: {results['status']}
contact: {TO_NAME}
contact_email: {TO_EMAIL}
approval_file: APPROVAL_Email_Response_SeherIrish_2026-03-20.md
response_option: A
---

# Email Execution Report

## Approved Action
- **File**: APPROVAL_Email_Response_SeherIrish_2026-03-20.md
- **Action**: Send Email Response
- **Recipient**: {TO_NAME} <{results['recipient']}>
- **Subject**: {results['subject']}
- **Response Option**: A (Friendly Acknowledgment)

## Execution Result

| Field | Value |
|-------|-------|
| **Status** | {results['status']} |
| **Timestamp** | {results['timestamp']} |
| **Sent At** | {results.get('sent_at', 'N/A')} |

## Email Content
```
{BODY}
```

## Errors
{chr(10).join('- ' + e for e in results['errors']) if results['errors'] else 'None'}

---
*Executed by AI Employee per approved action workflow*
""")

    print(f"\nExecution report saved to: {report_file}")

    # Move approved file to Done if successful
    if results["status"] == "success":
        dst = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Done\\APPROVAL_Email_Response_SeherIrish_2026-03-20.md"
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
