---
name: linkedin-poster
description: |
  Automatically post on LinkedIn to generate sales and business leads.
  Uses Playwright browser automation to create posts, engage with content,
  and track engagement metrics. Requires human approval before posting.
---

# LinkedIn Poster Skill

Automate LinkedIn posting for business development and lead generation.

## Architecture

Uses Playwright browser automation to:
1. Log into LinkedIn (persistent session)
2. Draft posts based on business goals
3. Submit for human approval
4. Post approved content
5. Track engagement metrics

## Setup

### 1. Install Dependencies

```bash
cd AI_Employee_Vault
uv add playwright
playwright install chromium
```

### 2. Create Session Directory

```bash
mkdir -p config/linkedin/session
```

### 3. First-Time Login

```bash
# Start LinkedIn session (will pause for login)
python scripts/linkedin_login.py

# Login with credentials
# Session saved to config/linkedin/session/
```

## Usage

### Create Post Draft

```bash
# AI creates draft based on Business_Goals.md
python scripts/linkedin_draft.py

# Or specify topic
python scripts/linkedin_draft.py --topic "product launch"
```

### Review Drafts

Drafts are created in `Pending_Approval/`:

```markdown
---
type: linkedin_post
topic: business update
created: 2026-01-07T10:30:00Z
status: pending_approval
---

# LinkedIn Post Draft

**Topic:** Business Update  
**Estimated Reach:** 500-1000 impressions

## Post Content

🚀 Excited to announce our new AI Employee system!

Key features:
✅ Autonomous task management
✅ 24/7 monitoring
✅ Human-in-the-loop approval

#AI #Automation #Productivity

## Posting Details

- **Best time to post:** Tuesday 10 AM
- **Target audience:** Business owners, managers
- **Expected engagement:** 20-50 likes, 5-10 comments

---
*To approve: Move this file to /Approved/*
```

### Post Approved Content

```bash
# Orchestrator triggers this when file moved to Approved/
python scripts/linkedin_post.py --file Approved/LINKEDIN_post_draft.md
```

## Content Strategy

### Post Types

1. **Business Updates** - Company news, milestones
2. **Thought Leadership** - Industry insights, trends
3. **Product Announcements** - New features, launches
4. **Client Success** - Testimonials, case studies
5. **Educational** - Tips, how-tos, best practices

### Posting Schedule

| Day | Best Time | Content Type |
|-----|-----------|--------------|
| Tuesday | 10 AM | Business update |
| Wednesday | 2 PM | Thought leadership |
| Thursday | 11 AM | Product news |
| Friday | 9 AM | Educational content |

### AI Content Generation

AI creates posts based on:
- `Business_Goals.md` - Current objectives
- `Done/` folder - Recent accomplishments
- Industry trends (via web search)

## Approval Workflow

```
1. AI drafts post based on business goals
   ↓
2. Creates file in Pending_Approval/
   ↓
3. Human reviews content
   ↓
4. Move to Approved/ to publish
   ↓
5. AI posts to LinkedIn
   ↓
6. Logs result in Dashboard.md
```

## Action File Format

```markdown
---
type: linkedin_post
topic: client success story
created: 2026-01-07T10:30:00Z
scheduled: 2026-01-08T10:00:00Z
status: posted
engagement:
  likes: 45
  comments: 12
  shares: 8
---

# LinkedIn Post - EXECUTED

**Posted:** 2026-01-08 10:00 AM  
**Post URL:** https://linkedin.com/posts/xyz123

## Content

[Post content here]

## Engagement (as of 2026-01-08 5 PM)

- Likes: 45
- Comments: 12
- Shares: 8
- Impressions: 1,234

## Notes

Strong engagement on client success stories. Consider more case study posts.
```

## Scripts

### `linkedin_login.py`

One-time login and session management.

### `linkedin_draft.py`

Create post drafts based on business goals.

### `linkedin_post.py`

Execute posting approved content.

### `linkedin_engagement.py`

Track post performance and engagement.

## Configuration

Edit `config/linkedin/settings.json`:

```json
{
  "session_path": "config/linkedin/session",
  "headless": true,
  "post_schedule": {
    "tuesday": "10:00",
    "wednesday": "14:00",
    "thursday": "11:00",
    "friday": "09:00"
  },
  "hashtags": ["#AI", "#Automation", "#Productivity"],
  "max_posts_per_day": 2
}
```

## Integration with AI Employee

### Weekly Content Planning

```
1. AI reads Business_Goals.md every Monday
   ↓
2. Creates weekly content plan in Plans/LinkedIn_Week_01.md
   ↓
3. Generates drafts for each day
   ↓
4. Human reviews and approves
   ↓
5. AI posts on schedule
   ↓
6. Reports engagement in weekly briefing
```

### CEO Briefing Integration

AI includes LinkedIn metrics in weekly reports:
- Total posts this week
- Engagement summary
- Top performing content
- Recommendations

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login fails | Clear session and re-login |
| Post doesn't publish | Check if file moved to Approved/ |
| Wrong formatting | LinkedIn strips some Markdown - use plain text |
| Rate limited | Wait 24 hours before next post |

## Security

- **Never commit** session files to git
- Add to `.gitignore`:
  ```
  config/linkedin/session/
  ```
- LinkedIn may flag automation - use sparingly
- Always disclose AI-generated content if required

## Best Practices

1. **Human Review** - Always approve before posting
2. **Authentic Voice** - Match your personal brand
3. **Engagement** - Respond to comments within 24 hours
4. **Variety** - Mix content types
5. **Analytics** - Review performance weekly

## Testing

```bash
# Create a draft post
python scripts/linkedin_draft.py --topic "test"

# Review draft in Pending_Approval/

# Move to Approved/ to publish

# Check Logs/linkedin_*.log for results
```
