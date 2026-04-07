---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for urgent messages using Playwright browser automation.
  Detects keywords like 'urgent', 'invoice', 'payment', 'asap' and creates
  action files in Needs_Action folder for AI processing.
---

# WhatsApp Watcher Skill

Monitor WhatsApp Web for important messages and create actionable items.

## Architecture

Uses Playwright browser automation to:
1. Log into WhatsApp Web (persistent session)
2. Scan unread messages for urgent keywords
3. Create action files in `Needs_Action/` folder
4. Maintain session across restarts

## Setup

### 1. Install Dependencies

```bash
cd AI_Employee_Vault
uv add playwright
playwright install chromium
```

### 2. Create Session Directory

```bash
mkdir -p config/whatsapp/session
```

### 3. First-Time Login

```bash
# Start WhatsApp watcher (will pause for QR scan)
python scripts/whatsapp_watcher.py

# Scan QR code with WhatsApp mobile app
# Session saved to config/whatsapp/session/
```

## Usage

### Start WhatsApp Watcher

```bash
# Run in background
python scripts/whatsapp_watcher.py

# Or with custom check interval (default: 30 seconds)
python scripts/whatsapp_watcher.py --interval 60
```

### What It Does

1. **Monitors** WhatsApp Web for unread messages
2. **Filters** messages containing urgent keywords
3. **Creates** action files in `Needs_Action/` folder
4. **Maintains** session for persistent login
5. **Tracks** processed messages to avoid duplicates

## Urgent Keywords

Default keywords that trigger action files:
- `urgent`
- `asap`
- `invoice`
- `payment`
- `help`
- `money`
- `call`

Edit in `config/whatsapp/settings.json`:

```json
{
  "keywords": ["urgent", "asap", "invoice", "payment", "help", "money", "call"],
  "check_interval": 30,
  "session_path": "config/whatsapp/session",
  "headless": true
}
```

## Action File Format

```markdown
---
type: whatsapp
from: +1234567890
contact_name: John Doe
received: 2026-01-07T10:30:00Z
priority: high
status: pending
keywords: ["urgent", "payment"]
---

# WhatsApp Message

**From:** John Doe (+1234567890)  
**Received:** 2026-01-07 10:30 AM  
**Keywords Detected:** urgent, payment

## Message Content

"Hey, urgent! Can you send the payment for the invoice?"

## Suggested Actions

- [ ] Reply to message
- [ ] Create payment approval request
- [ ] Forward to accounting
```

## Integration with AI Employee

### Workflow

```
1. WhatsApp Watcher detects urgent message
   ↓
2. Creates action file in Needs_Action/
   ↓
3. Orchestrator triggers Qwen processing
   ↓
4. Qwen reads message, determines action
   ↓
5. If reply needed → drafts response (with approval)
   ↓
6. If payment request → creates approval file
   ↓
7. Moves to Done when complete
```

### Approval Rules

Per Company Handbook:
- **Payment requests >$50** → Create approval request
- **New contacts** → Flag for human review
- **Emotional/conflict messages** → Escalate to human

## Scripts

### `whatsapp_watcher.py`

Main watcher script using Playwright.

### `whatsapp_session.py`

Manage WhatsApp session (login, logout, status).

### `whatsapp_sender.py`

Send WhatsApp messages (requires approval workflow).

## Session Management

### Check Session Status

```bash
python scripts/whatsapp_session.py status
```

### Logout Session

```bash
python scripts/whatsapp_session.py logout
```

### Refresh Session

```bash
# Stop watcher
taskkill /F /IM python.exe

# Clear session
rm -rf config/whatsapp/session/*

# Re-login
python scripts/whatsapp_watcher.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code shows every time | Session not saving - check folder permissions |
| No messages detected | Increase check_interval or check keyword filters |
| WhatsApp Web stuck | Clear session and re-login |
| Browser won't close | Run `bash scripts/stop-server.sh` for Playwright |

## Security

- **Never commit** session files to git
- Add to `.gitignore`:
  ```
  config/whatsapp/session/
  ```
- Session contains authentication tokens - protect like passwords
- Use only on trusted machines

## Testing

```bash
# Send yourself a WhatsApp message with keyword "test"
# Wait for watcher to detect (check_interval seconds)
# Verify action file created in Needs_Action/

# Check logs
tail -f Logs/watcher_*.log
```

## WhatsApp Web Limitations

- Requires phone to be connected to internet
- Session expires after ~30 days of inactivity
- Rate limiting: Don't check more than once per 30 seconds
- Terms of Service: Be aware of WhatsApp's automation policies
