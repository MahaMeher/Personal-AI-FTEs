---
name: email-mcp
description: |
  Email functionality via Universal MCP Server. Send and manage emails through
  the AI Employee system using the universal-mcp skill with email adapter.
  
  NOTE: This functionality is now part of the Universal MCP Server.
  See universal-mcp/SKILL.md for the complete implementation.
---

# Email via Universal MCP

Email functionality is now provided through the **Universal MCP Server** with multiple adapter support.

## Quick Start

See **[universal-mcp/SKILL.md](../universal-mcp/SKILL.md)** for complete documentation.

### Send Email

```bash
# Via Universal MCP Client
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "email",
  "to": "client@example.com",
  "subject": "Invoice #1234",
  "body": "Please find attached invoice...",
  "attachments": ["invoice.pdf"]
}'
```

### Configuration

Edit `config/mcp/adapters.json`:

```json
{
  "adapters": {
    "email": {
      "enabled": true,
      "provider": "gmail",
      "credentials": "config/email/credentials.json",
      "signature": "Best regards,\nAI Employee"
    }
  }
}
```

## Approval Rules

Per Company Handbook:

| Scenario | Approval Required |
|----------|-------------------|
| New contact (first email) | ✅ Yes |
| Reply to existing thread | ❌ No |
| Contains attachment | ✅ Yes |
| Payment/invoice related | ✅ Yes |
| Internal team email | ❌ No |

## Legacy Documentation

The original email-mcp implementation has been merged into the Universal MCP Server for better flexibility and multi-channel support.

### Original Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  AI Employee│────▶│ Email MCP    │────▶│  Gmail API  │
│  (Qwen)     │     │  Server      │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
```

### New Architecture (Universal)

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  AI Employee│────▶│ Universal    │────▶│  Gmail      │
│  (Qwen)     │     │ MCP Server   │     │  Adapter    │
└─────────────┘     └──────┬───────┘     ├─────────────┤
                           │             │  Outlook    │
                           ├────────────▶│  Adapter    │
                           │             ├─────────────┤
                           │             │  SMTP       │
                           │             │  Adapter    │
                           │             └─────────────┘
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  AI Employee│────▶│ Email MCP    │────▶│  Gmail API  │
│  (Qwen)     │     │  Server      │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Approval   │
                    │  Workflow   │
                    └─────────────┘
```

## Setup

### 1. Install Node.js Dependencies

```bash
cd AI_Employee_Vault
npm init -y
npm install @modelcontextprotocol/server-gmail
```

### 2. Create Gmail Credentials

```bash
# Follow Google Cloud Console setup
# Download credentials.json to:
mkdir -p config/email
# Place credentials.json in config/email/
```

### 3. Configure MCP Server

Create `mcp_config.json`:

```json
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": [
        "node_modules/@modelcontextprotocol/server-gmail/dist/index.js"
      ],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "config/email/credentials.json",
        "GMAIL_TOKEN_PATH": "config/email/token.json"
      }
    }
  }
}
```

### 4. Authenticate First Time

```bash
# Run authentication
node scripts/email_auth.js

# Follow browser OAuth flow
# token.json saved to config/email/
```

## Usage

### Send Email (Draft Mode)

```bash
# Create draft email
python scripts/email_draft.py \
  --to "client@example.com" \
  --subject "Invoice #1234" \
  --body "Please find attached invoice..."
```

### Send Email (Approved)

```bash
# After human approval
python scripts/email_send.py \
  --file Approved/EMAIL_draft_001.md
```

## Email Draft Format

```markdown
---
type: email_draft
to: client@example.com
cc: manager@company.com
subject: Invoice #1234 - Payment Due
created: 2026-01-07T10:30:00Z
status: pending_approval
requires_approval: true
reason: New contact (first email)
---

# Email Draft

## Recipients

**To:** client@example.com  
**CC:** manager@company.com  
**Subject:** Invoice #1234 - Payment Due

## Body

Dear Client,

Please find attached invoice #1234 for services rendered.

Amount: $1,500.00
Due Date: January 31, 2026

Best regards,
AI Employee

## Attachments

- [ ] Invoice_1234.pdf

---
**Approval Required:** First time emailing this contact

*To approve: Move this file to /Approved/*
```

## Approval Rules

Per Company Handbook:

| Scenario | Approval Required |
|----------|-------------------|
| New contact (first email) | ✅ Yes |
| Reply to existing thread | ❌ No |
| Contains attachment | ✅ Yes |
| Payment/invoice related | ✅ Yes |
| Internal team email | ❌ No |

## Approval Workflow

```
1. AI composes email draft
   ↓
2. Checks if approval needed (new contact, attachment, etc.)
   ↓
3. Creates draft file in Pending_Approval/
   ↓
4. Human reviews and moves to Approved/
   ↓
5. AI sends email via MCP server
   ↓
6. Logs sent email in Dashboard.md
   ↓
7. Moves to Sent/ folder
```

## MCP Tools

### `gmail_send_email`

Send an email immediately.

```json
{
  "to": ["client@example.com"],
  "subject": "Hello",
  "body": "Email body text",
  "cc": [],
  "bcc": [],
  "attachments": []
}
```

### `gmail_create_draft`

Create a draft without sending.

```json
{
  "to": ["client@example.com"],
  "subject": "Hello",
  "body": "Email body text"
}
```

### `gmail_list_emails`

List recent emails.

```json
{
  "query": "is:unread",
  "maxResults": 10
}
```

### `gmail_reply`

Reply to an email.

```json
{
  "messageId": "abc123",
  "body": "Reply text"
}
```

## Scripts

### `email_draft.py`

Create email drafts with approval workflow.

### `email_send.py`

Send approved emails.

### `email_auth.py`

One-time Gmail authentication.

### `email_templates.py`

Manage email templates for common scenarios.

## Email Templates

### Invoice Template

```markdown
Subject: Invoice #[NUMBER] - Payment Due

Dear [CLIENT],

Please find attached invoice #[NUMBER] for [SERVICES].

**Amount:** $[AMOUNT]
**Due Date:** [DATE]
**Payment Methods:** [METHODS]

Thank you for your business!

Best regards,
AI Employee
```

### Follow-up Template

```markdown
Subject: Following up: [ORIGINAL SUBJECT]

Hi [NAME],

Just following up on my previous email about [TOPIC].

Please let me know if you have any questions.

Best regards,
AI Employee
```

## Integration with AI Employee

### Email Processing Flow

```
1. Gmail Watcher detects new email
   ↓
2. Creates action file in Needs_Action/
   ↓
3. AI determines response needed
   ↓
4. AI drafts reply
   ↓
5. If approval needed → Pending_Approval/
   ↓
6. Human approves → Approved/
   ↓
7. AI sends via Email MCP
   ↓
8. Logs in Dashboard.md
```

### CEO Briefing Integration

Weekly email summary:

```markdown
## Email Activity

| Metric | Count |
|--------|-------|
| Emails Received | 47 |
| Emails Sent | 23 |
| Pending Approval | 2 |
| Response Time (avg) | 4.2 hours |
```

## Configuration

Edit `config/email/settings.json`:

```json
{
  "auto_archive_sent": true,
  "signature": "Best regards,\nAI Employee",
  "default_cc": [],
  "require_approval_new_contacts": true,
  "log_all_emails": true
}
```

## Security

- **Never commit** credentials or tokens to git
- Add to `.gitignore`:
  ```
  config/email/credentials.json
  config/email/token.json
  ```
- Use OAuth 2.0 with minimal scopes
- Review sent emails weekly

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run email_auth.py |
| Email not sending | Check if file in Approved/ |
| Attachment missing | Verify file path exists |
| Rate limited | Wait 24 hours, reduce sending volume |

## Testing

```bash
# Send test email to yourself
python scripts/email_draft.py \
  --to "your.email@gmail.com" \
  --subject "Test Email" \
  --body "This is a test"

# Move draft to Approved/
# Verify email received
```
