# Universal MCP Server

General-purpose Model Context Protocol (MCP) server for the AI Employee system. Supports multiple communication channels and external actions through a unified interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Universal MCP Server                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Email     │  │   WhatsApp   │  │   LinkedIn   │      │
│  │   Adapter    │  │   Adapter    │  │   Adapter    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│  ┌──────▼─────────────────▼─────────────────▼───────┐      │
│  │           MCP Protocol Handler                    │      │
│  └──────────────────────┬────────────────────────────┘      │
│                         │                                    │
│                  ┌──────▼───────┐                            │
│  ┌───────────────┤   Qwen/AI    ├───────────────┐           │
│  │               │   Employee   │               │           │
│  │          ┌────▼──────┐      │          ┌────▼────┐      │
│  │          │ Approved  │      │          │ Pending │      │
│  │          │  Folder   │      │          │Approval │      │
│  │          └───────────┘      │          └─────────┘      │
│  │                                                      │
└─────────────────────────────────────────────────────────────┘
```

## Supported Adapters

| Adapter | Purpose | Status |
|---------|---------|--------|
| **email** | Send emails (Gmail, Outlook, SMTP) | ✅ Ready |
| **whatsapp** | Send WhatsApp messages | ✅ Ready |
| **linkedin** | Post on LinkedIn | ✅ Ready |
| **browser** | Web automation (Playwright) | ✅ Ready |
| **slack** | Send Slack messages | 🔜 Coming |
| **twitter** | Post tweets | 🔜 Coming |
| **odoo** | Accounting operations | 🔜 Coming |

## Setup

### 1. Install Dependencies

```bash
cd AI_Employee_Vault

# Core MCP dependencies
npm init -y
npm install @modelcontextprotocol/sdk

# Adapter dependencies
npm install nodemailer googleapis whatsapp-web.js playwright
```

### 2. Configure Adapters

Create `config/mcp/adapters.json`:

```json
{
  "email": {
    "enabled": true,
    "provider": "gmail",
    "credentials": "config/email/credentials.json"
  },
  "whatsapp": {
    "enabled": true,
    "session_path": "config/whatsapp/session"
  },
  "linkedin": {
    "enabled": true,
    "session_path": "config/linkedin/session"
  },
  "browser": {
    "enabled": true,
    "headless": true
  }
}
```

### 3. Start MCP Server

```bash
# Start server
python scripts/mcp_server.py

# Or with specific adapters
python scripts/mcp_server.py --adapters email,whatsapp,browser
```

## Usage

### Send Email

```python
# Via MCP client
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "email",
  "to": "client@example.com",
  "subject": "Invoice #1234",
  "body": "Please find attached...",
  "attachments": ["invoice.pdf"]
}'
```

### Send WhatsApp Message

```python
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "whatsapp",
  "to": "+1234567890",
  "message": "Hi! Your order is ready for pickup."
}'
```

### Post on LinkedIn

```python
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "linkedin",
  "content": "🚀 Excited to announce our new AI Employee system!",
  "hashtags": ["#AI", "#Automation"]
}'
```

### Browser Automation

```python
python scripts/mcp_client.py call -t browser_action -p '{
  "action": "navigate",
  "url": "https://example.com"
}'

python scripts/mcp_client.py call -t browser_action -p '{
  "action": "click",
  "selector": "#submit-button"
}'
```

## MCP Tools

### `send_message`

Send message via any channel.

**Parameters:**
```json
{
  "channel": "email|whatsapp|linkedin|slack|twitter",
  "to": "recipient@example.com",
  "subject": "Optional subject",
  "body": "Message content",
  "attachments": [],
  "requires_approval": true
}
```

### `browser_action`

Perform browser automation.

**Parameters:**
```json
{
  "action": "navigate|click|type|screenshot|evaluate",
  "url": "https://example.com",
  "selector": "#element-id",
  "text": "Text to type",
  "script": "return document.title"
}
```

### `get_status`

Get adapter status.

**Response:**
```json
{
  "adapters": {
    "email": {"status": "connected", "provider": "gmail"},
    "whatsapp": {"status": "connected"},
    "linkedin": {"status": "disconnected"},
    "browser": {"status": "ready"}
  }
}
```

### `list_contacts`

List contacts from any channel.

**Parameters:**
```json
{
  "channel": "email|whatsapp|linkedin",
  "limit": 50
}
```

## Approval Workflow

All sensitive actions go through approval:

```
1. AI requests action via MCP
   ↓
2. MCP checks if approval required
   ↓
3. If yes → Creates file in Pending_Approval/
   ↓
4. Human moves to Approved/
   ↓
5. MCP executes action
   ↓
6. Logs result
```

### Approval Rules

| Channel | Approval Required When |
|---------|----------------------|
| email | New contact, attachment, payment |
| whatsapp | New contact, payment request |
| linkedin | All posts (draft approval) |
| browser | Payment portals, sensitive sites |
| slack | External channels |
| twitter | All tweets |

## Adapter Configuration

### Email Adapter

```json
{
  "email": {
    "enabled": true,
    "provider": "gmail",
    "credentials": "config/email/credentials.json",
    "default_signature": "Best regards,\nAI Employee",
    "require_approval_new_contacts": true
  }
}
```

**Supported providers:**
- `gmail` - Gmail via OAuth2
- `outlook` - Outlook/Hotmail via OAuth2
- `smtp` - Generic SMTP

### WhatsApp Adapter

```json
{
  "whatsapp": {
    "enabled": true,
    "session_path": "config/whatsapp/session",
    "headless": true,
    "require_approval_new_contacts": true
  }
}
```

### LinkedIn Adapter

```json
{
  "linkedin": {
    "enabled": true,
    "session_path": "config/linkedin/session",
    "headless": true,
    "require_approval_all_posts": true
  }
}
```

### Browser Adapter

```json
{
  "browser": {
    "enabled": true,
    "headless": true,
    "user_agent": "Mozilla/5.0...",
    "timeout": 30000
  }
}
```

## Scripts

### `mcp_server.py`

Main MCP server that handles all adapters.

### `mcp_client.py`

Client for testing MCP tools.

### `mcp_register_adapter.py`

Register new adapter.

### `mcp_status.py`

Check all adapter statuses.

## Creating Custom Adapters

### Adapter Template

```python
# adapters/base_adapter.py
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        pass
    
    @abstractmethod
    def send_message(self, **kwargs) -> dict:
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        pass
```

### Example: Slack Adapter

```python
# adapters/slack_adapter.py
from .base_adapter import BaseAdapter
from slack_sdk import WebClient

class SlackAdapter(BaseAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.client = WebClient(token=config['bot_token'])
    
    def connect(self) -> bool:
        try:
            self.client.auth_test()
            self.connected = True
            return True
        except Exception as e:
            return False
    
    def send_message(self, channel: str, text: str) -> dict:
        response = self.client.chat_postMessage(
            channel=channel,
            text=text
        )
        return {
            'success': True,
            'message_id': response['ts']
        }
    
    def get_status(self) -> dict:
        return {
            'status': 'connected' if self.connected else 'disconnected',
            'workspace': self.config.get('workspace')
        }
```

## Integration with AI Employee

### Workflow

```
1. AI processes action file in Needs_Action/
   ↓
2. Determines action type (email, whatsapp, etc.)
   ↓
3. Calls appropriate MCP tool
   ↓
4. MCP checks approval requirements
   ↓
5. If approved → executes action
   ↓
6. Returns result to AI
   ↓
7. AI logs in Dashboard.md
```

### Example: Email Processing

```python
# AI Employee calls MCP
result = mcp_client.call(
    tool='send_message',
    arguments={
        'channel': 'email',
        'to': 'client@example.com',
        'subject': 'Re: Invoice',
        'body': 'Dear Client,\n\nPayment received...',
        'requires_approval': True
    }
)

# MCP creates approval if needed
# After approval, sends email
# Returns result
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Adapter not connecting | Check credentials in config/adapters.json |
| Message not sending | Verify approval file moved to Approved/ |
| Browser action fails | Run browser_snapshot first to get refs |
| MCP server won't start | Check if port 8808 is available |

## Security

- **Never commit** credentials to git
- Add to `.gitignore`:
  ```
  config/mcp/credentials/
  config/*/session/
  ```
- Use environment variables for sensitive data
- All actions logged in Logs/mcp_actions.jsonl

## Testing

```bash
# Test email adapter
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "email",
  "to": "your.email@gmail.com",
  "subject": "Test",
  "body": "Test message"
}'

# Test WhatsApp adapter
python scripts/mcp_client.py call -t send_message -p '{
  "channel": "whatsapp",
  "to": "+1234567890",
  "message": "Test message"
}'

# Check status
python scripts/mcp_status.py
```

## Extending the MCP Server

### Add New Channel

1. Create adapter in `adapters/` folder
2. Register in `config/mcp/adapters.json`
3. Add MCP tool handler
4. Update documentation

### Add New Tool

1. Define tool in `mcp_server.py`
2. Implement handler
3. Update client examples
4. Test with `mcp_client.py`

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- [Reference MCP Servers](https://github.com/modelcontextprotocol/servers)
