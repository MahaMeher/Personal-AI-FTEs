#!/usr/bin/env python3
"""
Send test email to infoinc533@gmail.com
This executes the approved action: APPROVAL_Email_Test_Orchestrator_2026-03-16.md
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# Email configuration (from environment or defaults)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Recipient and content (from approved action file)
RECIPIENT = "infoinc533@gmail.com"
SUBJECT = "Test from Orchestrator"
BODY = "Hello, this is a test email to verify the complete workflow is working."

def send_email():
    """Send the test email and return results."""
    
    results = {
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
        "recipient": RECIPIENT,
        "subject": SUBJECT,
        "errors": []
    }
    
    # Check if credentials are configured
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        results["status"] = "skipped"
        results["errors"].append("Email credentials not configured (SENDER_EMAIL/SENDER_PASSWORD)")
        print("⚠️ Email credentials not configured in environment variables")
        print("   Set SENDER_EMAIL and SENDER_PASSWORD to enable email sending")
        return results
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT
        msg['Subject'] = SUBJECT
        msg.attach(MIMEText(BODY, 'plain'))
        
        # Connect and send
        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        print(f"Sending email to: {RECIPIENT}")
        server.send_message(msg)
        server.quit()
        
        results["status"] = "success"
        results["sent_at"] = datetime.now().isoformat()
        print(f"✓ Email sent successfully to {RECIPIENT}")
        
    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(str(e))
        print(f"✗ Failed to send email: {str(e)}")
    
    return results


def main():
    print("=" * 60)
    print("Executing: APPROVAL_Email_Test_Orchestrator_2026-03-16.md")
    print("=" * 60)
    print(f"\nRecipient: {RECIPIENT}")
    print(f"Subject: {SUBJECT}")
    print(f"Body: {BODY}")
    print("\n" + "=" * 60 + "\n")
    
    results = send_email()
    
    # Save execution report
    report_file = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\EMAIL_EXECUTION_REPORT_Test_Orchestrator.md"
    with open(report_file, 'w') as f:
        f.write(f"""---
type: execution_report
action: send_email
executed: {datetime.now().isoformat()}
status: {results['status']}
---

# Email Execution Report

## Approved Action
- **File**: APPROVAL_Email_Test_Orchestrator_2026-03-16.md
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
        import shutil
        src = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Approved\\APPROVAL_Email_Test_Orchestrator_2026-03-16.md"
        dst = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\Done\\APPROVAL_Email_Test_Orchestrator_2026-03-16.md"
        try:
            shutil.move(src, dst)
            print(f"✓ Moved approval file to Done folder")
        except Exception as e:
            print(f"⚠️ Could not move file to Done: {str(e)}")
    
    return results


if __name__ == "__main__":
    main()
