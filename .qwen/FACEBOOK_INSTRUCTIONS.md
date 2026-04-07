# Qwen Code - Facebook Integration Instructions

## CRITICAL: How to Post to Facebook

When the user asks to post to Facebook, **DO NOT** ask for permission or give options.

**DO THIS:**

1. Execute this command directly:
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp
python facebook.py post "MESSAGE_HERE"
```

2. Show the result to the user.

**DO NOT:**
- ❌ Ask "Would you like me to proceed?"
- ❌ Give options like "Option 1, Option 2, Option 3"
- ❌ Say "I need permission to use tools"
- ❌ Try to use Playwright/browser automation
- ❌ Ask the user to choose an approach

**JUST EXECUTE THE COMMAND.**

---

## Facebook Commands Reference

### Post to Facebook
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp
python facebook.py post "Your message here"
```

### Post with Link
```bash
python facebook.py post "Your message" "https://link.com"
```

### Get Page Info
```bash
python facebook.py info
```

### Get Recent Posts
```bash
python facebook.py posts 5
```

### Generate Report
```bash
python facebook.py report 7
```

---

## Example Interaction

**User:** Post to our Facebook page: "Hello from AI FTE!"

**Qwen Code (CORRECT):**
```bash
$ cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp
$ python facebook.py post "Hello from AI FTE!"

📱 Posting to Facebook...
📝 Message: Hello from AI FTE!
✅ Post created successfully!
Result: {"post_id": "123456789_987654321"}

Your post has been published to Tech-IT page!
View: https://facebook.com/123456789_987654321
```

**Qwen Code (WRONG - DON'T DO THIS):**
```
I need permission to use tools. Would you like me to:
Option 1: Use Playwright MCP...
Option 2: Create a Python script...
Option 3: Post manually...
```

---

## Other Gold Tier Skills

### Odoo ERP
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp
python odoo.py <command>
```

### Email
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\email-mcp
python email.py <command>
```

### LinkedIn
```bash
cd D:\Personal-AI-FTEs\.qwen\skills\linkedin-poster
python linkedin.py <command>
```

---

## Rule: Never Ask for Tool Permission

When a skill is registered in `.qwen/skills/`, Qwen Code should use it directly.

**DO NOT say:**
- "I need permission to use tools"
- "Would you like me to proceed?"
- "Choose an option"

**JUST DO IT.**

---

## Current Skills Available

| Skill | Location | Command |
|-------|----------|---------|
| Facebook | `.qwen/skills/facebook-mcp/` | `python facebook.py post "msg"` |
| Odoo | `.qwen/skills/odoo-mcp/` | `python odoo.py <command>` |
| Email | `.qwen/skills/email-mcp/` | `python email.py <command>` |
| LinkedIn | `.qwen/skills/linkedin-poster/` | `python linkedin.py <command>` |
| Gmail Watcher | `.qwen/skills/gmail-watcher/` | Auto-runs |
| Facebook Watcher | `.qwen/skills/facebook-watcher/` | Auto-runs |

---

**REMEMBER: When user asks to do something, JUST DO IT. Don't ask for permission.**
