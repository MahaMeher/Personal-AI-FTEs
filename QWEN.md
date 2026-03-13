# Personal AI FTEs Project

## Project Overview

This project implements a **Digital FTE (Full-Time Equivalent)** — an autonomous AI employee that manages personal and business affairs 24/7. The system uses **Claude Code** as the reasoning engine and **Obsidian** (local Markdown) as the dashboard/memory, with lightweight Python "Watcher" scripts for monitoring and **MCP (Model Context Protocol)** servers for external actions.

**Tagline:** *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

### Core Architecture

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine, task planning, decision-making |
| **Memory/GUI** | Obsidian Vault | Dashboard, long-term memory, human-readable state |
| **Senses** | Python Watchers | Monitor Gmail, WhatsApp, filesystems, bank transactions |
| **Hands** | MCP Servers | External actions (email, browser automation, payments) |

### Key Design Patterns

1. **Watcher Pattern**: Lightweight Python scripts run continuously, detecting changes and creating `.md` files in `/Needs_Action` folder
2. **Ralph Wiggum Loop**: A Stop hook that keeps Claude iterating until multi-step tasks are complete
3. **Human-in-the-Loop (HITL)**: Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
4. **Claim-by-Move**: Agents claim tasks by moving files to `/In_Progress/<agent>/`

## Directory Structure

```
D:\Personal-AI-FTEs\
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md  # Main documentation
├── skills-lock.json          # Qwen skill dependencies
├── .qwen/
│   └── skills/
│       └── browsing-with-playwright/  # Browser automation skill
│           ├── SKILL.md              # Playwright MCP usage guide
│           ├── scripts/
│           │   ├── mcp-client.py     # MCP client for tool calls
│           │   ├── start-server.sh   # Start Playwright MCP server
│           │   ├── stop-server.sh    # Stop Playwright MCP server
│           │   └── verify.py         # Server health check
│           └── references/
│               └── playwright-tools.md
└── .git/
```

### Expected Obsidian Vault Structure (to be created)

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time summary
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring attention
├── In_Progress/              # Currently being worked on
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved actions ready to execute
├── Done/                     # Completed tasks
├── Plans/                    # Multi-step plans (Plan.md)
├── Briefings/                # CEO briefings, weekly audits
└── Accounting/
    └── Current_Month.md      # Transaction logs
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Latest | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts & orchestration |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers & automation |
| [GitHub Desktop](https://desktop.github.com/download/) | Latest | Version control |

### Hardware Requirements

- **Minimum**: 8GB RAM, 4-core CPU, 20GB free disk space
- **Recommended**: 16GB RAM, 8-core CPU, SSD storage
- **For always-on**: Dedicated mini-PC or cloud VM (Oracle Cloud Free Tier)

### Setup Checklist

```bash
# 1. Verify Claude Code
claude --version

# 2. Create Obsidian vault
mkdir AI_Employee_Vault
cd AI_Employee_Vault
# Initialize folder structure
mkdir -p Inbox Needs_Action In_Progress Pending_Approval Approved Done Plans Briefings Accounting

# 3. Set up Python environment (UV recommended)
uv init
uv add watchdog google-api-python-client playwright

# 4. Install Playwright browsers
playwright install

# 5. Verify Playwright MCP server
bash .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Starting the Playwright MCP Server

```bash
# Start server (shared browser context for stateful sessions)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Or manually:
npx @playwright/mcp@latest --port 8808 --shared-browser-context &

# Verify it's running
python .qwen/skills/browsing-with-playwright/scripts/verify.py
```

### Stopping the Playwright MCP Server

```bash
# Graceful shutdown (closes browser first)
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh
```

### Running a Ralph Wiggum Loop

```bash
# Start autonomous task processing
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

## Development Conventions

### Coding Style

- **Python**: Follow PEP 8, use type hints for watcher scripts
- **Markdown**: Use YAML frontmatter for metadata in all `.md` files
- **Naming**: `snake_case` for files/functions, `PascalCase` for classes

### Watcher Script Pattern

All watchers inherit from `BaseWatcher`:

```python
from base_watcher import BaseWatcher

class GmailWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        """Return list of new items to process"""
        pass

    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder"""
        pass
```

### Markdown File Schema

All action files use YAML frontmatter:

```yaml
---
type: email
from: sender@example.com
subject: Urgent: Invoice Required
received: 2026-01-07T10:30:00Z
priority: high
status: pending
---
```

### Human-in-the-Loop Pattern

For sensitive actions, Claude creates an approval request:

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
created: 2026-01-07T10:30:00Z
expires: 2026-01-08T10:30:00Z
status: pending
---
```

User moves file from `/Pending_Approval` → `/Approved` to execute.

## Testing Practices

1. **Unit Tests**: Test watcher logic with mock data
2. **Integration Tests**: Verify end-to-end flow (Watcher → Claude → MCP → Action)
3. **Manual Verification**: Use `verify.py` scripts before production runs

## Achievement Tiers

| Tier | Description | Estimated Time |
|------|-------------|----------------|
| **Bronze** | Foundation: One watcher + Claude + Obsidian | 8-12 hours |
| **Silver** | Functional: Multiple watchers + MCP + HITL | 20-30 hours |
| **Gold** | Autonomous: Full integration + Ralph Wiggum + Briefings | 40+ hours |
| **Platinum** | Production: Cloud deployment + specialization | 60+ hours |

## Key Resources

- **Main Documentation**: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **Playwright Tools Reference**: `.qwen/skills/browsing-with-playwright/references/playwright-tools.md`
- **Ralph Wiggum Pattern**: [GitHub Reference](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- **MCP Servers**: [Model Context Protocol](https://github.com/modelcontextprotocol)
- **Community**: Wednesday Research Meetings (Zoom: 871 8870 7642, Passcode: 744832)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright MCP not responding | Run `bash scripts/stop-server.sh && bash scripts/start-server.sh` |
| Element not found in browser | Run `browser_snapshot` first to get current refs |
| Claude exits prematurely | Use Ralph Wiggum loop to keep task running |
| Watcher not detecting changes | Check file permissions and folder paths |
| Approval workflow stuck | Verify file movement triggers orchestrator |
