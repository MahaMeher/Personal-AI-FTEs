---
name: facebook-mcp
description: |
  Facebook and Instagram integration via Meta Graph API.
  Post to Facebook Pages, read comments, get insights, and manage Instagram Business accounts.
  Use for social media automation, engagement monitoring, and analytics.
---

# Facebook/Instagram MCP Integration

Automate Facebook and Instagram via MCP server.

## Quick Start (Recommended)

Use the helper script for simple commands:

```bash
# Navigate to skill folder
cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp

# Post to Facebook
python facebook.py post "Hello from AI FTE! Gold Tier is complete! 🚀"

# Post with link
python facebook.py post "Check this out!" "https://example.com"

# Get page info
python facebook.py info

# Get recent posts
python facebook.py posts 5

# Generate engagement report
python facebook.py report 7
```

## Server Lifecycle

### Start Facebook MCP Server

```bash
# Navigate to skill folder
cd D:\Personal-AI-FTEs\.qwen\skills\facebook-mcp

# Start Facebook MCP server (stdio transport)
python facebook_mcp_server.py
```

**Note:** The server runs in the background. Qwen Code will start it automatically when needed.

### Stop Server

```bash
# Kill the Python process
taskkill /F /IM python.exe /FI "WINDOWTITLE eq facebook_mcp_server*"
```

## Quick Reference

### Page Management

```bash
# Get page info
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_page_info --params '{}'
```

### Posting

```bash
# Create a post
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_create_post \
  --params '{"message": "Hello from AI FTE!", "published": true}'

# Create post with link
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_create_post \
  --params '{"message": "Check this out!", "link": "https://example.com"}'

# Schedule a post
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_schedule_post \
  --params '{"message": "Scheduled post", "scheduled_time": "2026-03-29 09:00:00"}'
```

### Reading Content

```bash
# Get recent posts
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_posts \
  --params '{"limit": 10}'

# Get comments on a post
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_post_comments \
  --params '{"post_id": "123456789", "limit": 50}'

# Get conversations (messages)
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_conversations \
  --params '{"limit": 25}'
```

## Engagement

### Reply to Comment
```bash
# Get comment ID first
python facebook.py comments POST_ID

# Then reply using the comment ID
python reply_to_comment.py COMMENT_ID "Your reply message"
```

### Like a Post or Comment
```bash
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_like_object \
  --params '{"object_id": "post_123"}'
```

### Analytics

```bash
# Get page insights
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_page_insights \
  --params '{"metrics": ["page_impressions_unique", "page_engagements"]}'

# Generate engagement report
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_generate_engagement_report \
  --params '{"days": 7}'
```

### Instagram

```bash
# Get Instagram account info
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool instagram_get_account_info \
  --params '{}'

# Get Instagram media
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool instagram_get_media \
  --params '{"limit": 25}'

# Get Instagram insights
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool instagram_get_insights \
  --params '{"period": "week"}'
```

## Configuration

Ensure `.env` file exists in `D:\Personal-AI-FTEs\AI_Employee_Vault\scripts\`:

```bash
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_PAGE_ID=your_page_id
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id
```

## Usage Examples

### Example 1: Post to Facebook

```bash
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_create_post \
  --params '{"message": "Exciting news! Our AI FTE Gold Tier is complete! 🚀 #Automation"}'
```

### Example 2: Check for New Comments

```bash
# Get recent posts first
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_posts \
  --params '{"limit": 5}'

# Then get comments on the most recent post
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_get_post_comments \
  --params '{"post_id": "POST_ID_HERE", "limit": 50}'
```

### Example 3: Generate Weekly Report

```bash
python mcp-client.py call --stdio "python facebook_mcp_server.py" --tool facebook_generate_engagement_report \
  --params '{"days": 7}'
```

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| `Invalid access token` | Regenerate token in Graph API Explorer |
| `Missing permissions` | Check app has required permissions |
| `Page not found` | Verify PAGE_ID is correct |
| `Token expired` | Use long-lived token (60 days) |

## Required Facebook Permissions

- `pages_manage_posts` - Create and schedule posts
- `pages_read_engagement` - Read comments and reactions
- `pages_read_user_content` - Read page content
- `instagram_basic` - Basic Instagram info
- `instagram_content_publish` - Publish to Instagram
- `instagram_manage_insights` - Instagram analytics
