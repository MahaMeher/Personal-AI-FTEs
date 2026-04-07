---
name: scheduler-integration
description: |
  Schedule recurring AI Employee tasks using cron (Linux/Mac) or Task
  Scheduler (Windows). Automate daily briefings, weekly audits, and
  periodic watcher checks.
---

# Scheduler Integration Skill

Schedule recurring tasks for the AI Employee system.

## Supported Schedulers

| Platform | Scheduler | Setup Time |
|----------|-----------|------------|
| Windows | Task Scheduler | 5 minutes |
| macOS | cron / launchd | 5 minutes |
| Linux | cron / systemd | 5 minutes |

## Quick Start

### Windows (Task Scheduler)

```powershell
# Run this PowerShell script to create scheduled tasks
python scripts/setup_windows_scheduler.py
```

### macOS/Linux (cron)

```bash
# Add cron jobs
python scripts/setup_cron.py

# Or manually edit crontab
crontab -e
```

## Scheduled Tasks

### Daily Tasks

| Task | Time | Description |
|------|------|-------------|
| Morning Briefing | 8:00 AM | Generate daily summary |
| Inbox Processing | Every 30 min | Check for new items |
| Evening Audit | 6:00 PM | Review completed tasks |

### Weekly Tasks

| Task | Day/Time | Description |
|------|----------|-------------|
| CEO Briefing | Monday 7:00 AM | Weekly business summary |
| Subscription Audit | Friday 3:00 PM | Review recurring charges |
| Plan Review | Sunday 5:00 PM | Check active plans progress |

### Monthly Tasks

| Task | Day/Time | Description |
|------|----------|-------------|
| Accounting Close | 1st, 9:00 AM | Monthly accounting summary |
| Goal Review | 1st, 10:00 AM | Review monthly goals |
| Backup | 15th, 2:00 AM | Full vault backup |

## Setup Scripts

### Windows: `setup_windows_scheduler.py`

Creates these scheduled tasks:

```xml
<!-- AI Employee - Daily Briefing -->
<Task>
  <Trigger>
    <CalendarTrigger>
      <StartBoundary>2026-01-07T08:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Trigger>
  <Action>
    <Exec>
      <Command>python</Command>
      <Arguments>scripts/daily_briefing.py</Arguments>
      <WorkingDirectory>D:\Personal-AI-FTEs\AI_Employee_Vault</WorkingDirectory>
    </Exec>
  </Action>
</Task>
```

### macOS/Linux: `setup_cron.py`

Adds these cron entries:

```cron
# AI Employee - Daily Briefing (8 AM)
0 8 * * * cd /path/to/AI_Employee_Vault && python scripts/daily_briefing.py

# AI Employee - CEO Briefing (Monday 7 AM)
0 7 * * 1 cd /path/to/AI_Employee_Vault && python scripts/ceo_briefing.py

# AI Employee - Subscription Audit (Friday 3 PM)
0 15 * * 5 cd /path/to/AI_Employee_Vault && python scripts/subscription_audit.py

# AI Employee - Backup (15th of month, 2 AM)
0 2 15 * * cd /path/to/AI_Employee_Vault && python scripts/backup_vault.py
```

## Task Scripts

### `daily_briefing.py`

Generates daily summary:

```markdown
# Daily Briefing - 2026-01-07

## Yesterday's Accomplishments

- [x] Processed 5 payment requests
- [x] Responded to 12 emails
- [x] Created 3 LinkedIn posts

## Today's Priorities

1. Follow up on pending approvals
2. Process monthly accounting
3. Review active plans

## Pending Items

| Item | Type | Priority |
|------|------|----------|
| Payment approval - Client A | Payment | High |
| Email draft - Vendor B | Email | Medium |
```

### `ceo_briefing.py`

Generates weekly CEO briefing:

```markdown
# CEO Briefing - Week of 2026-01-06

## Executive Summary

Strong week with revenue ahead of target. One bottleneck identified.

## Revenue

- **This Week:** $2,450
- **MTD:** $4,500 (45% of $10,000 target)
- **Trend:** On track

## Completed Tasks

- [x] Client A invoice sent and paid
- [x] Project Alpha milestone 2 delivered

## Bottlenecks

| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Client B proposal | 2 days | 5 days | +3 days |

## Proactive Suggestions

### Cost Optimization
- **Notion:** No team activity in 45 days. Cost: $15/month.
  - [ACTION] Cancel subscription? Move to /Pending_Approval
```

### `subscription_audit.py`

Reviews recurring charges:

```python
# Analyze transactions for subscriptions
SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'spotify.com': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
}

# Flag unused subscriptions
for subscription in detected_subscriptions:
    if subscription.last_used > 30 days:
        create_approval_request(f"Cancel {subscription.name}?")
```

### `backup_vault.py`

Creates vault backup:

```python
# Create timestamped backup
backup_name = f"vault_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copytree(vault_path, f"backups/{backup_name}")

# Compress backup
shutil.make_archive(f"backups/{backup_name}", 'zip', vault_path)

# Log backup
log_backup_created(backup_name)
```

## Configuration

Edit `config/scheduler/settings.json`:

```json
{
  "daily_briefing": {
    "enabled": true,
    "time": "08:00",
    "timezone": "UTC"
  },
  "ceo_briefing": {
    "enabled": true,
    "day": "monday",
    "time": "07:00"
  },
  "subscription_audit": {
    "enabled": true,
    "day": "friday",
    "time": "15:00"
  },
  "backup": {
    "enabled": true,
    "day_of_month": 15,
    "time": "02:00",
    "retention_days": 90
  }
}
```

## Management Commands

### View Scheduled Tasks

```bash
# Windows
schtasks /Query /TN "AI Employee*"

# macOS/Linux
crontab -l
```

### Enable/Disable Tasks

```bash
# Disable daily briefing
python scripts/scheduler_control.py --disable daily_briefing

# Enable all tasks
python scripts/scheduler_control.py --enable all
```

### Run Task Manually

```bash
# Run daily briefing now
python scripts/daily_briefing.py --force

# Run CEO briefing now
python scripts/ceo_briefing.py --force
```

## Troubleshooting

### Windows Task Scheduler

| Issue | Solution |
|-------|----------|
| Task doesn't run | Check "Run whether user is logged on or not" |
| Python not found | Use full path: `C:\Python313\python.exe` |
| Working directory wrong | Set in Action properties |

### cron

| Issue | Solution |
|-------|----------|
| Task doesn't run | Check cron logs: `grep CRON /var/log/syslog` |
| Python not found | Use full path: `/usr/bin/python3` |
| Environment missing | Add PATH to crontab |

### General

| Issue | Solution |
|-------|----------|
| Task runs but errors | Check Logs/ folder for script output |
| Duplicate runs | Ensure previous instance completed |
| Timezone wrong | Update settings.json timezone |

## Best Practices

1. **Log Everything** - All scheduled tasks should log to Logs/ folder
2. **Error Handling** - Scripts should handle failures gracefully
3. **Idempotent** - Safe to run multiple times
4. **Notifications** - Alert on critical failures
5. **Documentation** - Document what each task does

## Integration with AI Employee

### Workflow

```
1. Scheduler triggers task at scheduled time
   ↓
2. Task script runs (e.g., daily_briefing.py)
   ↓
3. Creates briefing file in Briefings/ folder
   ↓
4. Updates Dashboard.md with summary
   ↓
5. If action items found → creates in Needs_Action/
   ↓
6. AI processes action items normally
```

### Dashboard Integration

Scheduled tasks update Dashboard.md:

```markdown
## Scheduled Tasks Status

| Task | Last Run | Next Run | Status |
|------|----------|----------|--------|
| Daily Briefing | 2026-01-07 8:00 AM | 2026-01-08 8:00 AM | ✅ OK |
| CEO Briefing | 2026-01-06 7:00 AM | 2026-01-13 7:00 AM | ✅ OK |
| Subscription Audit | 2026-01-03 3:00 PM | 2026-01-10 3:00 PM | ✅ OK |
```
