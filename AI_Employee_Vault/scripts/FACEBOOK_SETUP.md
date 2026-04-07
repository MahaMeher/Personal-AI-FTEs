# Facebook API Configuration Guide
## Gold Tier - Personal AI FTEs Project

This guide walks you through obtaining Facebook API credentials for the Facebook MCP Server.

---

## Step 1: Create Meta Developer Account

1. Go to https://developers.facebook.com/
2. Click **"Get Started"** or **"Log In"**
3. Complete the developer verification process
4. Accept Meta Platform Terms of Service

---

## Step 2: Create a Facebook App

1. Go to https://developers.facebook.com/apps/
2. Click **"Create App"**
3. Select use case: **Business** (recommended) or **Other**
4. Click **"Next"**

5. Fill in app details:
   ```
   App Name: Personal AI FTE - Social Media Automation
   App Contact Email: your-email@example.com
   ```

6. Click **"Create App"**
7. Complete security verification (CAPTCHA)

---

## Step 3: Add Facebook Login Product

1. In your app dashboard, scroll to **"Add Products to Your App"**
2. Find **"Facebook Login"** and click **"Set Up"**
3. Configure settings:
   - **Valid OAuth Redirect URIs:** `https://localhost`
   - **Web OAuth Login:** Enabled
   - **Embedded Browser OAuth:** Enabled
4. Click **"Save Changes"**

---

## Step 4: Get App ID and App Secret

1. Go to **Settings → Basic** in your app dashboard
2. Copy these values:
   ```
   App ID: 123456789012345  ← Copy this
   App Secret: abc123def456...  ← Click "Show" then copy
   ```

3. Update your `.env` file:
   ```bash
   FACEBOOK_APP_ID=123456789012345
   FACEBOOK_APP_SECRET=abc123def456...
   ```

---

## Step 5: Generate Access Token with Permissions

### Option A: Using Graph API Explorer (Recommended for Testing)

1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app from the dropdown
3. Click **"Generate Access Token"**

4. Grant these permissions:
   - ✅ `pages_manage_posts` - Create and schedule posts
   - ✅ `pages_read_engagement` - Read comments and reactions
   - ✅ `pages_read_user_content` - Read page content
   - ✅ `instagram_basic` - Basic Instagram info
   - ✅ `instagram_content_publish` - Publish to Instagram
   - ✅ `instagram_manage_insights` - Instagram analytics
   - ✅ `pages_manage_metadata` - Manage page settings

5. Click **"Generate Token"** and complete authorization

6. Copy the **Access Token** from the field

### Option B: Get Long-Lived Token (Recommended for Production)

1. After generating token in Graph API Explorer:
2. Click on the token info icon (ℹ️)
3. Click **"Continue to Access Token Tool"**
4. Click **"Extend Access Token"**
5. Copy the new long-lived token (valid for 60 days)

---

## Step 6: Get Facebook Page ID

1. Go to https://developers.facebook.com/tools/explorer/
2. With your access token selected, make this request:
   ```
   GET /me/accounts
   ```
3. Click **"Submit"**

4. You'll see a response like:
   ```json
   {
     "data": [
       {
         "name": "Your Page Name",
         "id": "987654321098765",
         "access_token": "page_access_token_here"
       }
     ]
   }
   ```

5. Copy the **Page ID**:
   ```bash
   FACEBOOK_PAGE_ID=987654321098765
   ```

6. Also copy the **Page Access Token** (this is different from user token):
   ```bash
   FACEBOOK_ACCESS_TOKEN=page_access_token_here
   ```

---

## Step 7: Get Instagram Business Account ID

### Prerequisites
- Instagram account must be **Business** or **Creator** (not Personal)
- Instagram account must be connected to your Facebook Page

### Convert to Business Account (if needed)
1. Open Instagram app
2. Go to Settings → Account
3. Tap **"Switch to Professional Account"**
4. Select **"Business"**

### Connect Instagram to Facebook Page
1. Open Instagram app
2. Go to Settings → Account → Linked Accounts
3. Select Facebook and connect to your Page

### Get Instagram Business Account ID
1. Go to Graph API Explorer
2. Make this request:
   ```
   GET /{your-facebook-page-id}?fields=instagram_business_account
   ```
3. Click **"Submit"**

4. Response:
   ```json
   {
     "instagram_business_account": {
       "id": "17841400123456789"
     }
   }
   ```

5. Copy the Instagram Business Account ID:
   ```bash
   INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400123456789
   ```

---

## Step 8: Update Your .env File

Navigate to `D:\Personal-AI-FTEs\AI_Employee_Vault\scripts\` and create `.env`:

```bash
# Copy from .env.example
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

Update these values:

```bash
# Facebook API Configuration
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abc123def456ghi789jkl012mno345pqr
FACEBOOK_ACCESS_TOKEN=EAABwzLixnjYBO7ZCxvZBqWERTYUIOPASDFGHJKLZXCVBNM1234567890
FACEBOOK_PAGE_ID=987654321098765
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400123456789
```

---

## Step 9: Verify Configuration

Test your Facebook connection:

```bash
cd D:\Personal-AI-FTEs\AI_Employee_Vault\scripts

# Test Facebook MCP server
python facebook_mcp_server.py
```

Expected output:
```
INFO:facebook-mcp:Starting Facebook/Instagram MCP Server...
INFO:facebook-mcp:Connected to Facebook Page: Your Page Name
```

---

## Step 10: Test in Claude Code

```bash
# Get page info
@facebook facebook_get_page_info

# Create a test post
@facebook facebook_create_post message="Test post from AI FTE Gold Tier"

# Get posts
@facebook facebook_get_posts limit=5
```

---

## Troubleshooting

### Error: "Invalid Access Token"
- Token may have expired - generate a new one
- Token may not have required permissions
- Use the Page Access Token, not User Access Token

### Error: "Missing Permissions"
- Go to App Dashboard → App Review
- Submit for advanced access if needed
- For testing, you can use the app in Development mode

### Error: "Page Not Found"
- Verify you're admin of the Facebook Page
- Check Page ID is correct (should be numeric)
- Ensure access token has `pages_manage_posts` permission

### Error: "Instagram Account Not Connected"
- Convert Instagram to Business account
- Link Instagram to Facebook Page in Instagram settings
- Wait 5-10 minutes for connection to propagate

---

## Token Expiration

| Token Type | Validity | How to Extend |
|------------|----------|---------------|
| Short-lived User Token | 1-2 hours | Use "Extend" in Access Token Tool |
| Long-lived User Token | 60 days | Refresh before expiry |
| Page Access Token | Never expires* | Generated from long-lived user token |

*Page tokens from long-lived user tokens don't expire

---

## Security Best Practices

1. **Never commit `.env` to Git** - Already in `.gitignore`
2. **Use long-lived tokens** for production
3. **Rotate credentials** every 60-90 days
4. **Use separate app** for development vs production
5. **Limit permissions** to only what's needed
6. **Monitor app usage** in Meta Developer Dashboard

---

## Quick Reference

### Where to Get Credentials

| Credential | Where to Find |
|------------|---------------|
| `FACEBOOK_APP_ID` | App Dashboard → Settings → Basic |
| `FACEBOOK_APP_SECRET` | App Dashboard → Settings → Basic (click Show) |
| `FACEBOOK_ACCESS_TOKEN` | Graph API Explorer → Generate Token |
| `FACEBOOK_PAGE_ID` | Graph API Explorer → GET /me/accounts |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Graph API Explorer → GET /{page-id}?fields=instagram_business_account |

### Required Permissions

- `pages_manage_posts`
- `pages_read_engagement`
- `pages_read_user_content`
- `instagram_basic`
- `instagram_content_publish`
- `instagram_manage_insights`

---

**Date:** 2026-03-25  
**Version:** 1.0  
**Status:** Ready for Configuration
