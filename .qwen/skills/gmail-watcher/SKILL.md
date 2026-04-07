---
name: gmail-watcher
description: |
  Monitor Gmail for new important emails and create action files in Needs_Action folder.
  Uses Gmail API to watch for unread, important messages and converts them to Markdown
  action files for AI processing.
---

# Gmail Watcher Skill

Monitor Gmail inbox and create actionable items for the AI Employee.

## Setup

### 1. Enable Gmail API

```bash
# Go to Google Cloud Console
https://console.cloud.google.com/apis/library/gmail.googleapis.com

# Enable Gmail API for your project
```

### 2. Create Credentials

```bash
# Create OAuth 2.0 credentials
# Download credentials.json to: AI_Employee_Vault/config/gmail/credentials.json
```

### 3. Install Dependencies

```bash
cd AI_Employee_Vault
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4. Authenticate First Time

```bash
python scripts/gmail_auth.py
# Follow browser flow to authorize
# token.json will be saved in config/gmail/
```

## Usage

### Start Gmail Watcher

```bash
# Run in background
python scripts/gmail_watcher.py

# Or with custom check interval (default: 120 seconds)
python scripts/gmail_watcher.py --interval 60
```

### What It Does

1. **Monitors** Gmail for unread, important messages
2. **Creates** action files in `Needs_Action/` folder
3. **Extracts** sender, subject, content, and attachments
4. **Flags** urgent keywords: `invoice`, `payment`, `urgent`, `asap`, `contract`
5. **Tracks** processed message IDs to avoid duplicates

## Action File Format

```markdown
---
type: email
from: sender@example.com
subject: Urgent: Invoice Required
received: 2026-01-07T10:30:00Z
priority: high
status: pending
message_id: abc123xyz
---

# Email Content

**From:** sender@example.com  
**Subject:** Urgent: Invoice Required  
**Received:** 2026-01-07 10:30 AM

## Body

[Email content here]

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

## Configuration

### Gmail Settings

Edit `config/gmail/settings.json`:

```json
{
  "check_interval": 120,
  "only_unread": true,
  "only_important": true,
  "keywords_flag": ["invoice", "payment", "urgent", "asap", "contract"],
  "auto_archive": false
}
```

## Integration with AI Employee

### Workflow

```
1. Gmail Watcher detects new email
   ↓
2. Creates action file in Needs_Action/
   ↓
3. Orchestrator triggers Qwen processing
   ↓
4. Qwen reads email, determines action
   ↓
5. If reply needed → creates draft or sends (with approval)
   ↓
6. Moves to Done when complete
```

### Approval Rules

Per Company Handbook:
- **Reply to new contacts** → Requires human approval
- **Emails with attachments** → Flag for review
- **Payment/invoice requests** → Create approval request if >$50

## Scripts

### `gmail_watcher.py`

Main watcher script that runs continuously.

### `gmail_auth.py`

One-time authentication to get Gmail API token.

### `gmail_test.py`

Test connection and read recent emails.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run `gmail_auth.py` to refresh token |
| No emails detected | Check if only_unread/only_important filters are too strict |
| Duplicate action files | Check processed_ids in watcher logs |
| API quota exceeded | Increase check_interval to 300+ seconds |

## Security

- **Never commit** `token.json` or `credentials.json` to git
- Add to `.gitignore`:
  ```
  config/gmail/token.json
  config/gmail/credentials.json
  ```
- Use read-only Gmail scope when possible

## Testing

```bash
# Send test email to yourself
# Wait for watcher to detect (check_interval seconds)
# Verify action file created in Needs_Action/

# Check logs
tail -f Logs/watcher_*.log
```
