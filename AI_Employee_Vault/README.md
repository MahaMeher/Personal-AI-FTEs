# AI Employee Vault

## Quick Start

### 1. Install Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
```

### 2. Start the Filesystem Watcher (Bronze Tier)

```bash
# Option A: Run in foreground
python scripts/filesystem_watcher.py

# Option B: Run in background (Windows)
start /B python scripts/filesystem_watcher.py

# Option C: Run in background (Linux/Mac)
nohup python scripts/filesystem_watcher.py &
```

### 3. Start the Orchestrator

```bash
# In a new terminal
python scripts/orchestrator.py
```

### 4. Test the System

1. Drop a file into the `Inbox` folder
2. Watcher will create an action file in `Needs_Action`
3. Orchestrator will automatically trigger Qwen Code to process it
4. Check `Done/` folder for completed tasks

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md          # Real-time status dashboard
├── Company_Handbook.md   # Rules of engagement
├── Business_Goals.md     # Objectives and targets
├── Inbox/                # Drop files here for processing
├── Needs_Action/         # Action files created by watchers
├── Done/                 # Completed tasks
├── Plans/                # Multi-step plans
├── Pending_Approval/     # Awaiting human approval
├── Approved/             # Approved actions ready to execute
├── Rejected/             # Rejected actions
├── Briefings/            # CEO briefings and reports
├── Accounting/           # Financial records
├── Logs/                 # System logs
├── Files/                # Processed files
└── scripts/
    ├── base_watcher.py       # Base watcher class
    ├── filesystem_watcher.py # File drop watcher
    └── orchestrator.py       # Main coordinator
```

## Usage Examples

### Drop a File for Processing

```bash
# Copy any file to the Inbox folder
cp document.pdf AI_Employee_Vault/Inbox/

# The watcher will automatically:
# 1. Detect the new file
# 2. Create an action file in Needs_Action
# 3. Move the file to Files/ folder
# 4. Orchestrator triggers Qwen to process it
```

### Approval Workflow (Human-in-the-Loop)

For actions requiring approval (payments >$50, sensitive actions):

```bash
# 1. Qwen creates approval file in Pending_Approval/
# 2. YOU review the file
# 3. Move to Approved/ to execute:
mv Pending_Approval/payment_request.md Approved/

# 4. Orchestrator automatically detects and executes
# 5. File moves to Done/ after execution

# Or move to Rejected/ to cancel:
mv Pending_Approval/payment_request.md Rejected/
```

### Manual Qwen Processing

If you want to process pending items manually:

```bash
cd AI_Employee_Vault
qwen "Process all pending items in Needs_Action folder. Follow Company_Handbook rules."
```

### Check Logs

```bash
# View today's watcher logs
cat Logs/watcher_*.log

# View orchestrator logs
cat Logs/orchestrator_*.log

# View action logs
cat Logs/actions_*.jsonl
```

## Configuration

### Environment Variables

Create a `.env` file (optional):

```bash
# .env
VAULT_PATH=/path/to/AI_Employee_Vault
DRY_RUN=false
LOG_LEVEL=INFO
```

### Watcher Intervals

- Filesystem Watcher: 30 seconds (default)
- Orchestrator: 60 seconds (default)

Modify in script constructors if needed.

## Troubleshooting

### Watcher Not Detecting Files

1. Check the Inbox folder path
2. Verify file permissions
3. Check Logs/watcher_*.log for errors

### Qwen Code Not Available

The system creates a `PROCESS_ME.md` file with instructions when Qwen Code CLI is not installed.

### Qwen Processing Timeout

If processing takes more than 10 minutes, the orchestrator will log a timeout message. You can continue manually:

```bash
cd AI_Employee_Vault
qwen "Continue processing pending items"
```

### Files Not Being Processed

1. Ensure watcher is running
2. Check that files are not .md format (those are treated as action files)
3. Verify the file hash hasn't been processed before

## Next Steps (Silver Tier)

- Add Gmail watcher
- Add WhatsApp watcher  
- Set up MCP servers for external actions
- Configure scheduled tasks

---
*AI Employee v0.1 - Bronze Tier*
