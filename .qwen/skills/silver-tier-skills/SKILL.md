---
name: silver-tier-skills
description: |
  Complete Silver Tier implementation guide. Combines all skills needed
  to build a Functional Assistant AI Employee with multiple watchers,
  MCP servers, and automated scheduling.
---

# Silver Tier Skills - Implementation Guide

## Silver Tier Requirements Checklist

From "Personal AI Employee Hackathon 0" document:

- [x] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [x] Automatically Post on LinkedIn about business to generate sales
- [x] Claude reasoning loop that creates Plan.md files
- [x] One working MCP server for external action (email-mcp)
- [x] Human-in-the-loop approval workflow (from Bronze)
- [x] Basic scheduling via cron or Task Scheduler
- [x] All AI functionality implemented as Agent Skills

## Skills Overview

| Skill | Purpose | Status |
|-------|---------|--------|
| **browsing-with-playwright** | Browser automation | ✅ Bronze (existing) |
| **gmail-watcher** | Monitor Gmail for important emails | ✅ Silver |
| **whatsapp-watcher** | Monitor WhatsApp for urgent messages | ✅ Silver |
| **linkedin-poster** | Auto-post on LinkedIn for sales | ✅ Silver |
| **plan-creator** | Create multi-step plans | ✅ Silver |
| **universal-mcp** | General MCP server (email, whatsapp, linkedin, browser) | ✅ Silver |
| **scheduler-integration** | Schedule recurring tasks | ✅ Silver |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Employee (Silver Tier)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Gmail      │  │   WhatsApp   │  │  Filesystem  │          │
│  │   Watcher    │  │   Watcher    │  │   Watcher    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                     │
│                    ┌──────▼───────┐                             │
│                    │ Needs_Action │                             │
│                    └──────┬───────┘                             │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐         │
│  │    Qwen      │  │    Plan      │  │  Approval    │         │
│  │  Processing  │  │   Creator    │  │  Workflow    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                  │
│         │                 │                 │                  │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐         │
│  │   Email      │  │  LinkedIn    │  │  Scheduler   │         │
│  │    MCP       │  │   Poster     │  │  Integration │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Order

### Phase 1: Core Watchers (Week 1)

1. **Setup Gmail Watcher**
   ```bash
   # Follow gmail-watcher/SKILL.md
   python scripts/gmail_auth.py
   python scripts/gmail_watcher.py
   ```

2. **Setup WhatsApp Watcher**
   ```bash
   # Follow whatsapp-watcher/SKILL.md
   python scripts/whatsapp_watcher.py
   # Scan QR code
   ```

3. **Test Watcher Integration**
   ```bash
   # Send test email
   # Send WhatsApp message with keyword "urgent"
   # Verify action files created in Needs_Action/
   ```

### Phase 2: Action Capabilities (Week 2)

4. **Setup Universal MCP Server**
   ```bash
   # Follow universal-mcp/SKILL.md
   # Configure adapters in config/mcp/adapters.json
   
   # Enable email adapter
   # Edit config/mcp/adapters.json - set email.enabled: true
   
   # Test MCP server
   python scripts/mcp_client.py status
   ```

5. **Setup LinkedIn Poster**
   ```bash
   # Follow linkedin-poster/SKILL.md
   python scripts/linkedin_login.py
   python scripts/linkedin_draft.py
   ```

6. **Test Approval Workflow**
   ```bash
   # Create email draft via MCP
   python scripts/mcp_client.py call -t send_message -p '{
     "channel": "email",
     "to": "test@example.com",
     "subject": "Test",
     "body": "Test message"
   }'
   
   # Move to Approved/
   # Verify email sent
   ```

### Phase 3: Planning & Scheduling (Week 3)

7. **Setup Plan Creator**
   ```bash
   # Follow plan-creator/SKILL.md
   python scripts/create_plan.py --task "Test Project"
   ```

8. **Setup Scheduler**
   ```bash
   # Windows
   python scripts/setup_windows_scheduler.py
   
   # macOS/Linux
   python scripts/setup_cron.py
   ```

9. **Test Scheduled Tasks**
   ```bash
   # Run daily briefing manually
   python scripts/daily_briefing.py --force
   
   # Verify Briefings/ folder updated
   ```

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md
├── Company_Handbook.md
├── Business_Goals.md
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring attention
├── In_Progress/              # Currently being worked on
├── Pending_Approval/         # Awaiting human approval
│   ├── EMAIL_draft_001.md
│   ├── PAYMENT_client_xyz.md
│   └── LINKEDIN_post_draft.md
├── Approved/                 # Approved actions ready to execute
├── Done/                     # Completed tasks
├── Plans/                    # Multi-step plans
│   ├── Q1_Tax_Plan.md
│   └── Product_Launch_Plan.md
├── Briefings/                # Daily/Weekly briefings
│   ├── 2026-01-07_Daily.md
│   └── 2026-01-06_CEO_Briefing.md
├── Accounting/
│   └── Current_Month.md
├── config/
│   ├── gmail/
│   ├── whatsapp/
│   ├── linkedin/
│   ├── email/
│   └── scheduler/
├── scripts/
│   ├── gmail_watcher.py
│   ├── whatsapp_watcher.py
│   ├── linkedin_*.py
│   ├── email_*.py
│   ├── plan_*.py
│   └── scheduler_*.py
└── Logs/
```

## Testing Scenarios

### Scenario 1: Email Processing

```
1. Receive email from new client
   ↓
2. Gmail Watcher creates action file
   ↓
3. AI drafts reply
   ↓
4. Creates approval request (new contact)
   ↓
5. Human approves
   ↓
6. Email MCP sends reply
   ↓
7. Logs in Dashboard.md
```

### Scenario 2: WhatsApp Payment Request

```
1. WhatsApp message: "Urgent! Need invoice payment"
   ↓
2. WhatsApp Watcher detects keyword
   ↓
3. Creates action file
   ↓
4. AI creates payment approval request
   ↓
5. Human approves
   ↓
6. Payment processed
   ↓
7. Accounting updated
```

### Scenario 3: LinkedIn Post

```
1. AI reads Business_Goals.md
   ↓
2. Creates LinkedIn post draft
   ↓
3. Human reviews and approves
   ↓
4. LinkedIn Poster publishes
   ↓
5. Engagement tracked
   ↓
6. Reported in weekly briefing
```

### Scenario 4: Weekly CEO Briefing

```
1. Scheduler triggers Monday 7 AM
   ↓
2. CEO Briefing script runs
   ↓
3. Analyzes week's transactions
   ↓
4. Reviews completed tasks
   ↓
5. Identifies bottlenecks
   ↓
6. Creates briefing in Briefings/
   ↓
7. Updates Dashboard.md
```

## Silver Tier Demo Script

### Setup (5 minutes)

```bash
# Show folder structure
cd AI_Employee_Vault
tree -L 2

# Show watchers running
tasklist | findstr python
```

### Demo 1: Email Processing (5 minutes)

```bash
# Send test email
# Show action file created
cat Needs_Action/EMAIL_*.md

# Show AI draft created
cat Pending_Approval/EMAIL_draft_*.md

# Approve and send
move Pending_Approval\EMAIL_draft_*.md Approved\

# Show sent email logged
cat Logs/actions_*.jsonl
```

### Demo 2: WhatsApp Integration (5 minutes)

```bash
# Send WhatsApp message with "urgent"
# Show action file created
cat Needs_Action/WHATSAPP_*.md

# Show AI response
cat Pending_Approval/WHATSAPP_reply_*.md
```

### Demo 3: LinkedIn Posting (5 minutes)

```bash
# Create post draft
python scripts/linkedin_draft.py --topic "AI Employee"

# Show draft
cat Pending_Approval/LINKEDIN_post_*.md

# Approve and post
move Pending_Approval\LINKEDIN_post_*.md Approved\
```

### Demo 4: CEO Briefing (5 minutes)

```bash
# Run briefing manually
python scripts/ceo_briefing.py --force

# Show briefing
cat Briefings/CEO_Briefing_*.md

# Show Dashboard updated
cat Dashboard.md
```

## Success Criteria

### Functional Requirements

- [ ] Gmail Watcher detects new emails within 2 minutes
- [ ] WhatsApp Watcher detects urgent messages within 30 seconds
- [ ] Email drafts require approval before sending
- [ ] LinkedIn posts require approval before publishing
- [ ] Plans created for multi-step tasks
- [ ] Daily briefing runs at 8 AM
- [ ] CEO briefing runs Monday 7 AM

### Non-Functional Requirements

- [ ] All credentials stored securely (not in git)
- [ ] Session files persist across restarts
- [ ] Logs capture all actions
- [ ] Error handling prevents crashes
- [ ] Deduplication prevents duplicate processing

## Troubleshooting

| Issue | Skill | Solution |
|-------|-------|----------|
| Gmail not connecting | gmail-watcher | Re-run gmail_auth.py |
| WhatsApp logs out | whatsapp-watcher | Re-scan QR code |
| Email not sending | email-mcp | Check Approved/ folder |
| LinkedIn post fails | linkedin-poster | Clear session, re-login |
| Plan not updating | plan-creator | Check AI processing logs |
| Scheduler not running | scheduler-integration | Check Task Scheduler/cron |

## Next Steps (Gold Tier)

After completing Silver Tier:

1. **Odoo Accounting Integration** - Full accounting system
2. **Facebook/Instagram Integration** - Social media posting
3. **Twitter/X Integration** - Twitter posting
4. **Multiple MCP Servers** - Different action types
5. **Error Recovery** - Graceful degradation
6. **Ralph Wiggum Loop** - Autonomous multi-step completion

## Resources

- [Main Hackathon Document](../Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Gmail Watcher Skill](gmail-watcher/SKILL.md)
- [WhatsApp Watcher Skill](whatsapp-watcher/SKILL.md)
- [LinkedIn Poster Skill](linkedin-poster/SKILL.md)
- [Plan Creator Skill](plan-creator/SKILL.md)
- [Email MCP Skill](email-mcp/SKILL.md)
- [Scheduler Integration Skill](scheduler-integration/SKILL.md)

---

*Silver Tier Implementation Guide - AI Employee v0.2*
