---
type: test_guide
created: 2026-03-17
status: ready
---

# Email Reply Test Guide (MCP-Based)

## ✅ Architecture Fixed

**Before:** Standalone `execute_approved_email.py` script
**Now:** MCP Email Server (`mcp/email_server.py`) called by Qwen Code

---

## 🔄 Complete Email Flow

```
1. Email arrives → Gmail Watcher detects
2. Creates file in /Needs_Action/
3. Orchestrator triggers Qwen Code
4. Qwen creates approval request in /Pending_Approval/
5. YOU review and move to /Approved/
6. Orchestrator triggers Qwen Code again
7. Qwen runs: python mcp/email_server.py send --to "..." --subject "..." --body "..."
8. MCP server sends via Gmail API (OAuth2)
9. Email SENT! ✅
10. Qwen updates file status to "executed"
11. Orchestrator moves file to /Done/
```

---

## 🧪 Test Steps

### Step 1: Verify MCP Server Works

```bash
cd "D:\Personal-AI-FTEs\AI_Employee_Vault"
python mcp/email_server.py test
```

**Expected Output:**
```
Testing email connection...
✅ Connected to Gmail: infoinc533@gmail.com
✅ Email adapter connected successfully
```

### Step 2: Prepare an Approval File

Pick one from `/Pending_Approval/`:
- `APPROVAL_Email_Iftar_Invitation_MehwishMeher_2026-03-16.md`
- `APPROVAL_Email_Response_MahaMeherrr_Hello_2026-03-16.md`
- `APPROVAL_Email_Response_MahaMeherrr_JobAssistant_2026-03-16.md`

**Edit the file** and add email details in frontmatter:

```yaml
---
type: approval_request
category: email_response
to: "mehwishmeherr@gmail.com"
subject: "Re: Iftar Invitation"
body: "Walaikum Assalam! Hello sister! InshaAllah this week we'll plan Iftar together."
status: pending
---
```

### Step 3: Move to Approved

Move the file from `Pending_Approval/` to `Approved/`:

```bash
move "D:\Personal-AI-FTEs\AI_Employee_Vault\Pending_Approval\APPROVAL_*.md" "D:\Personal-AI-FTEs\AI_Employee_Vault\Approved\"
```

### Step 4: Run Orchestrator

```bash
cd "D:\Personal-AI-FTEs\AI_Employee_Vault"
python scripts/orchestrator.py
```

**What Happens:**
1. Orchestrator detects file in `/Approved/`
2. Triggers Qwen Code with approved action
3. Qwen runs: `python mcp/email_server.py send --to "..." --subject "..." --body "..."`
4. MCP server sends email via Gmail API
5. Qwen updates file status to `executed`
6. Orchestrator moves file to `/Done/`

### Step 5: Verify Email Sent

**Check these:**
1. **Console output** should show:
   ```
   ✅ Email sent successfully!
      Message ID: 18f1a2b3c4d5e6f7
   ```

2. **Gmail Sent folder** - should show the email

3. **Recipient's inbox** - should receive the email

4. **File moved to Done** - approval file should be in `/Done/`

---

## 🔍 Manual Test (Send Email Directly)

To test MCP server directly without orchestrator:

```bash
cd "D:\Personal-AI-FTEs\AI_Employee_Vault"
python mcp/email_server.py send --to "infoinc533@gmail.com" --subject "Test Email" --body "This is a test email sent via MCP server using Gmail API OAuth2."
```

**Expected Output:**
```
============================================================
MCP Email Server
============================================================
✅ Connected to Gmail: infoinc533@gmail.com
✅ Sending email:
   From: infoinc533@gmail.com
   To: infoinc533@gmail.com
   Subject: Test Email
   Body: This is a test email sent via MCP server using Gmail API OAuth2.
✅ Email SENT successfully!
   Message ID: 18f1a2b3c4d5e6f7
============================================================
```

---

## 📊 Architecture Summary

| Component | Role | Uses OAuth2? |
|-----------|------|--------------|
| `gmail_watcher.py` | Monitors inbox | ✅ Yes |
| `mcp/email_server.py` | Sends emails | ✅ Yes (same token) |
| `orchestrator.py` | Triggers Qwen | N/A |
| Qwen Code | Runs MCP commands | N/A |
| `token.pickle` | OAuth2 credentials | ✅ Shared by all |

**No app password needed!** All components reuse the same `token.pickle` file.

---

## ⚠️ Troubleshooting

### "Token file not found"
```bash
# Verify token exists
dir config\gmail\token.pickle

# If missing, re-run auth
python scripts\gmail_auth.py
```

### "Email not sent - Qwen didn't call MCP"
Check the approval file has proper frontmatter:
```yaml
to: "recipient@email.com"
subject: "Subject Line"
body: "Email body text"
```

### "File stuck in Approved folder"
Check orchestrator logs:
```bash
type Logs\orchestrator_20260317.log
```

---

## ✅ Test Checklist

- [ ] MCP server test passes (`python mcp/email_server.py test`)
- [ ] Approval file has `to:`, `subject:`, `body:` in frontmatter
- [ ] File moved to `/Approved/`
- [ ] Orchestrator runs without errors
- [ ] Email appears in Gmail Sent folder
- [ ] Recipient receives email
- [ ] File moved to `/Done/` after execution

---

*Test Guide v2.0 - MCP-Based Email Architecture*
