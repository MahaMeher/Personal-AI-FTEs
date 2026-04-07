---
created: 2026-03-13
version: 0.2
status: complete
---

# Silver Tier Setup Guide

## Overview

Silver Tier builds on Bronze Tier with:
- ✅ Gmail Watcher - Monitor Gmail for important emails
- ✅ LinkedIn Watcher - Monitor LinkedIn for messages and notifications
- ✅ Plan Creator - Create multi-step plans
- ✅ Scheduler Integration - Windows Task Scheduler
- ✅ Daily/CEO Briefings - Automated reporting

## Quick Start

### Step 1: Install Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Setup Gmail (Required)

```bash
# Authenticate Gmail
python scripts/gmail_auth.py

# Test Gmail Watcher
python scripts/gmail_watcher.py --interval 60
```

**Credentials:** Already configured from `credentails.json` in project root.

### Step 3: Setup LinkedIn (Optional)

```bash
# Run LinkedIn Watcher (first time requires manual login)
python scripts/linkedin_watcher.py --interval 300
```

### Step 4: Setup Scheduler

```bash
# Create Windows Task Scheduler tasks
python scripts/setup_scheduler.py

# View created tasks
python scripts/setup_scheduler.py --list
```

### Step 5: Test Briefings

```bash
# Run daily briefing
python scripts/daily_briefing.py

# Run CEO briefing
python scripts/ceo_briefing.py
```

## Folder Structure

```
AI_Employee_Vault/
├── scripts/
│   ├── gmail_auth.py          ← Gmail authentication
│   ├── gmail_watcher.py       ← Gmail monitoring
│   ├── linkedin_watcher.py    ← LinkedIn monitoring
│   ├── plan_creator.py        ← Plan creation
│   ├── daily_briefing.py      ← Daily summary
│   ├── ceo_briefing.py        ← Weekly CEO briefing
│   └── setup_scheduler.py     ← Task Scheduler setup
├── config/
│   ├── gmail/
│   │   ├── credentials.json   ← Gmail OAuth credentials
│   │   └── token.pickle       ← Gmail auth token (generated)
│   └── linkedin/
│       └── session/           ← LinkedIn browser session
├── Briefings/
│   ├── YYYY-MM-DD_Daily.md    ← Daily briefings
│   └── YYYY-MM-DD_CEO_Briefing.md ← Weekly briefings
└── Plans/
    └── PLAN_*.md              ← Multi-step plans
```

## Watcher Comparison

| Watcher | Interval | Purpose | Approval Required |
|---------|----------|---------|-------------------|
| **Filesystem** | 30s | Local file drops | Per Company Handbook |
| **Gmail** | 2min | Email monitoring | New contacts, payments |
| **LinkedIn** | 5min | Messages, notifications | All responses/posts |

## Gmail Watcher

### What It Does

- Monitors Gmail for **unread emails**
- Creates action files in `Needs_Action/`
- Flags urgent keywords: `urgent`, `asap`, `invoice`, `payment`
- Determines if approval needed

### Action File Format

```markdown
---
type: email
from: "client@example.com"
subject: "Invoice #1234"
priority: high
status: pending
requires_approval: true
---

# Email Received

**From:** client@example.com  
**Subject:** Invoice #1234  
**Priority:** HIGH

## Preview

Payment request for services...

## Actions Required

- [ ] **URGENT**: Respond within 2 hours
- [ ] Process payment request
- [ ] Get human approval before responding
```

### Commands

```bash
# Run once
python scripts/gmail_watcher.py --interval 60

# Run with custom vault path
python scripts/gmail_watcher.py --vault "D:\MyVault"
```

## LinkedIn Watcher

### What It Does

- Monitors LinkedIn for **messages** and **notifications**
- Uses Playwright browser automation
- Creates action files for important items
- Requires first-time manual login

### First-Time Setup

1. Run: `python scripts/linkedin_watcher.py`
2. Browser opens to LinkedIn login
3. Login manually with your credentials
4. Session saved for future runs

### Commands

```bash
# Run LinkedIn watcher
python scripts/linkedin_watcher.py --interval 300
```

## Plan Creator

### What It Does

- Creates structured `Plan.md` files for complex tasks
- Breaks tasks into phases with checkboxes
- Tracks progress percentage

### Usage

```bash
# Create plan manually
python scripts/plan_creator.py --task "Q1 Tax Preparation" --deadline "2026-01-31" --priority high

# View active plans
python scripts/plan_creator.py
```

### Plan Format

```markdown
---
type: plan
title: Q1 Tax Preparation
deadline: 2026-01-31
priority: high
status: in_progress
---

# Plan: Q1 Tax Preparation

## Success Criteria

- [ ] All income categorized
- [ ] All expenses documented

## Tasks

### Phase 1: Preparation
- [ ] Gather bank statements
- [ ] Collect receipts

### Phase 2: Execution
- [ ] Categorize transactions

## Progress

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 1 | Done | 100% |
| Phase 2 | In Progress | 50% |
```

## Scheduler Integration

### Scheduled Tasks (Windows)

| Task | Schedule | Script |
|------|----------|--------|
| Daily Briefing | 8:00 AM daily | `daily_briefing.py` |
| CEO Briefing | Monday 7:00 AM | `ceo_briefing.py` |
| Gmail Watcher | Every 30 min | `gmail_watcher.py` |
| LinkedIn Watcher | Every hour | `linkedin_watcher.py` |

### Commands

```bash
# Setup all tasks
python scripts/setup_scheduler.py

# Remove all tasks
python scripts/setup_scheduler.py --remove

# List existing tasks
python scripts/setup_scheduler.py --list

# Run task manually
schtasks /Run /TN "AI Employee - Daily Briefing"
```

## Daily Briefing

### What It Includes

- Yesterday's accomplishments
- Today's priorities
- Pending items count
- Accounting summary

### Output

Saved to: `Briefings/YYYY-MM-DD_Daily.md`

## CEO Briefing

### What It Includes

- Executive summary
- Revenue summary
- Completed tasks (weekly)
- Active plans status
- Bottlenecks identified
- Proactive suggestions
- Upcoming deadlines

### Output

Saved to: `Briefings/YYYY-MM-DD_CEO_Briefing.md`

## Testing

### Test Gmail Integration

```bash
# 1. Authenticate
python scripts/gmail_auth.py

# Expected: "Authentication successful!"

# 2. Send yourself a test email
# Subject: "Test Email"
# Body: "Testing Gmail watcher"

# 3. Run watcher
python scripts/gmail_watcher.py --interval 30

# 4. Check Needs_Action folder
# Should see: EMAIL_*_Test_Email.md
```

### Test LinkedIn Integration

```bash
# 1. Run watcher (login when browser opens)
python scripts/linkedin_watcher.py --interval 60

# 2. Send yourself a LinkedIn message from another account

# 3. Check Needs_Action folder
# Should see: LINKEDIN_MSG_*.md
```

### Test Plan Creator

```bash
# Create test plan
python scripts/plan_creator.py --task "Test Project" --deadline "2026-12-31"

# Check Plans folder
# Should see: PLAN_Test_Project_*.md
```

### Test Briefings

```bash
# Run daily briefing
python scripts/daily_briefing.py

# Check Briefings folder
# Should see: YYYY-MM-DD_Daily.md

# Run CEO briefing
python scripts/ceo_briefing.py

# Check Briefings folder
# Should see: YYYY-MM-DD_CEO_Briefing.md
```

## Troubleshooting

### Gmail Authentication Fails

```
Error: Token file not found
```

**Solution:** Run `python scripts/gmail_auth.py` to authenticate.

### Gmail Watcher Returns No Emails

```
Found 0 new email(s)
```

**Solution:** 
- Check if emails are marked as unread
- Verify token.pickle exists in `config/gmail/`
- Check Gmail API quota

### LinkedIn Login Required Every Time

```
Login required. Please login manually.
```

**Solution:**
- Ensure session folder exists: `config/linkedin/session/`
- Don't close browser during first login
- Wait for LinkedIn feed to load before closing

### Scheduler Tasks Don't Run

```
Task failed to start
```

**Solution:**
- Open Task Scheduler → Find "AI Employee" tasks
- Check "Run whether user is logged on or not"
- Verify Python path in task properties

## Silver Tier Checklist

- [ ] Gmail credentials configured
- [ ] Gmail authentication completed
- [ ] Gmail watcher tested
- [ ] LinkedIn watcher tested (optional)
- [ ] Plan creator tested
- [ ] Scheduler tasks created
- [ ] Daily briefing runs successfully
- [ ] CEO briefing runs successfully

## Next Steps (Gold Tier)

After completing Silver Tier:
1. WhatsApp Watcher integration
2. MCP server for sending emails
3. Odoo accounting integration
4. Facebook/Instagram integration
5. Twitter/X integration
6. Ralph Wiggum loop for autonomous completion

---

*Silver Tier Setup Guide - AI Employee v0.2*
