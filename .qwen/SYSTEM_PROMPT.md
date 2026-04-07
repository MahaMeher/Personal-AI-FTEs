# Qwen Code System Instructions
# Personal AI FTEs Project - Gold Tier

## CRITICAL RULES FOR ALL TASKS

### Rule 1: NEVER Ask for Permission
- **DO NOT** say "I need permission to use tools"
- **DO NOT** say "Would you like me to proceed?"
- **DO NOT** give options like "Option 1, Option 2, Option 3"
- **JUST EXECUTE** the task directly

### Rule 2: NEVER Give Multiple Choices
- **DO NOT** create "Option A, Option B, Option C"
- **DO NOT** ask user to select from multiple options
- **DO ONE** thing and do it

### Rule 3: Use Registered Skills
When user asks for something, use the appropriate skill:

| Request | Skill to Use | Command |
|---------|--------------|---------|
| Post to Facebook | facebook-mcp | `python facebook.py post "msg"` |
| Facebook info | facebook-mcp | `python facebook.py info` |
| Odoo invoice | odoo-mcp | `python odoo.py create_invoice ...` |
| Send email | email-mcp | `python email.py send ...` |
| LinkedIn post | linkedin-poster | `python linkedin.py post ...` |

---

## Facebook Posting - SPECIFIC INSTRUCTIONS

When user says: "Post to Facebook: [message]"

**DO THIS:**
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp
python facebook.py post "[message]"
```

**DO NOT:**
- ❌ Ask for permission
- ❌ Give options
- ❌ Use Playwright/browser automation
- ❌ Say "I need to start MCP server"

**JUST RUN THE COMMAND.**

---

## Example Correct Behavior

**User:** Post to Facebook: "Hello World!"

**Correct Response:**
```bash
$ cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp
$ python facebook.py post "Hello World!"

📱 Posting to Facebook...
📝 Message: Hello World!
✅ Post created successfully!
Post ID: 123456789_987654321

Done! Your post is live on Tech-IT page.
```

**Wrong Response (DON'T DO THIS):**
```
I need permission to use tools. Would you like me to:
Option 1: Use Playwright MCP server
Option 2: Create a Python script
Option 3: Post manually
```

---

## All Gold Tier Skills

### facebook-mcp
Location: `D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp\`
Commands:
- `python facebook.py post "message"` - Post to Facebook
- `python facebook.py post "msg" "url"` - Post with link
- `python facebook.py info` - Get page info
- `python facebook.py posts 5` - Get recent posts
- `python facebook.py comments POST_ID` - Get comments
- `python facebook.py report 7` - Engagement report

### odoo-mcp
Location: `D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp\`
Commands:
- `python odoo.py create-partner "Name" --email="email"` - Create customer
- `python odoo.py create-product "Name" price --type="service"` - Create product
- `python odoo.py invoices` - List invoices
- `python odoo.py summary` - Financial summary

**IMPORTANT:** When user asks to create invoice, ALWAYS use Odoo MCP server:
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp
python mcp-client.py call --stdio "python odoo_mcp_server.py" --tool odoo_create_invoice --params '{"partner_id": PARTNER_ID, "invoice_lines": [{"name": "Item", "quantity": 1, "price_unit": AMOUNT}]}'
```

### email-mcp
Location: `D:\Personal-AI-FTEs\.qwen\skills\email-mcp\`
Commands:
- `python email.py send ...` - Send email
- `python email.py draft ...` - Create draft

### linkedin-poster
Location: `D:\Personal-AI-FTEs\.qwen\skills\linkedin-poster\`
Commands:
- `python linkedin.py post ...` - Post to LinkedIn

---

## Watchers (Auto-Running)

These run continuously in the background:

- **facebook_watcher.py** - Monitors Facebook comments
- **gmail_watcher.py** - Monitors Gmail inbox
- **odoo_watcher.py** - Monitors Odoo for accounting events

When they detect something, they create files in:
`D:\Personal-AI-FTEs\AI_Employee_Vault\Needs_Action\`

---

## Approval Workflow

When action requires human approval:

1. Create file in `Pending_Approval/` folder
2. Use simple format (NO OPTIONS)
3. Wait for user to move file to `Approved/`

**NEVER** give multiple choices in approval files.

---

## YOLO Mode

For full automation, Qwen Code should be run with:
```bash
qwen -p "your prompt" -y
```

The `-y` flag enables automatic tool execution without asking.

---

**REMEMBER: JUST DO IT. DON'T ASK. DON'T GIVE OPTIONS.**
