---
name: plan-creator
description: |
  Create structured Plan.md files for multi-step tasks. Breaks down complex
  objectives into actionable checkboxes with progress tracking. Integrates
  with AI Employee reasoning loop for autonomous task completion.
---

# Plan Creator Skill

Create and manage multi-step plans for complex tasks.

## When to Use

Create a Plan.md when:
- Task requires 3+ steps
- Task spans multiple days
- Task requires coordination between different actions
- Task needs progress tracking
- Task involves approval workflows

## Plan File Format

```markdown
---
type: plan
title: Q1 Tax Preparation
created: 2026-01-07T10:30:00Z
deadline: 2026-01-31
priority: high
status: in_progress
owner: AI Employee
---

# Plan: Q1 Tax Preparation

## Objective

Prepare and file Q1 2026 business taxes accurately and on time.

## Success Criteria

- [ ] All income categorized
- [ ] All expenses documented
- [ ] Receipts organized
- [ ] Tax forms completed
- [ ] Filed before deadline

## Tasks

### Phase 1: Data Collection (Week 1)

- [ ] Gather all bank statements
- [ ] Collect receipts from Accounting/ folder
- [ ] Export payment processor reports
- [ ] List all business expenses

### Phase 2: Categorization (Week 2)

- [ ] Categorize income by source
- [ ] Categorize expenses by type
- [ ] Identify tax-deductible expenses
- [ ] Calculate total deductible amount

### Phase 3: Documentation (Week 3)

- [ ] Organize receipts by category
- [ ] Scan missing receipts
- [ ] Create expense summary spreadsheet
- [ ] Reconcile with bank statements

### Phase 4: Filing (Week 4)

- [ ] Complete tax forms
- [ ] Review calculations
- [ ] Create approval request for filing
- [ ] File taxes (after approval)

## Progress

| Phase | Status | Completion |
|-------|--------|------------|
| Data Collection | Done | 100% |
| Categorization | In Progress | 60% |
| Documentation | Pending | 0% |
| Filing | Pending | 0% |

## Blockers

- Waiting for December bank statement

## Notes

- Accountant review scheduled for Jan 25
- Extension deadline: April 15 if needed

---
*Last updated: 2026-01-15 3:00 PM*
```

## Usage

### Create Plan from Task

```bash
# AI automatically creates plan for complex tasks
qwen -y "Create a plan for [task description]"

# Or manually trigger
python scripts/create_plan.py --task "Q1 Tax Preparation" --deadline "2026-01-31"
```

### Update Plan Progress

```bash
# Update plan with completed tasks
python scripts/update_plan.py --plan Plans/Q1_Tax_Plan.md --complete "Gather all bank statements"
```

### Generate Plan Summary

```bash
# Get progress report
python scripts/plan_summary.py --plan Plans/Q1_Tax_Plan.md
```

## AI Integration

### Reasoning Loop

```
1. AI receives complex task in Needs_Action/
   ↓
2. AI determines task requires multiple steps
   ↓
3. AI creates Plan.md in Plans/ folder
   ↓
4. AI works through tasks sequentially
   ↓
5. AI updates plan progress after each step
   ↓
6. AI moves plan to Done/ when complete
```

### Plan Creation Trigger

AI creates plan when task has:
- More than 3 required actions
- Dependencies between steps
- External deadlines
- Approval requirements

## Plan Templates

### Event Planning Template

```markdown
---
type: plan
title: [Event Name]
deadline: [Date]
---

# Plan: [Event Name]

## Pre-Event

- [ ] Book venue
- [ ] Send invitations
- [ ] Arrange catering
- [ ] Prepare materials

## During Event

- [ ] Registration
- [ ] Presentations
- [ ] Q&A session

## Post-Event

- [ ] Send thank you emails
- [ ] Collect feedback
- [ ] Process recordings
- [ ] Follow up with leads
```

### Project Template

```markdown
---
type: plan
title: [Project Name]
deadline: [Date]
budget: $[Amount]
---

# Plan: [Project Name]

## Requirements

- [ ] Gather requirements
- [ ] Define scope
- [ ] Get approval

## Execution

- [ ] Phase 1
- [ ] Phase 2
- [ ] Phase 3

## Delivery

- [ ] Testing
- [ ] Documentation
- [ ] Handoff
- [ ] Training
```

## Progress Tracking

### Status Values

- `pending` - Not started
- `in_progress` - Currently working
- `blocked` - Waiting on external factor
- `completed` - All tasks done
- `cancelled` - Plan abandoned

### Dashboard Integration

Plans update Dashboard.md:

```markdown
## Active Plans

| Plan | Progress | Deadline | Status |
|------|----------|----------|--------|
| Q1 Tax Prep | 60% | Jan 31 | On Track |
| Product Launch | 30% | Feb 15 | At Risk |
```

## Scripts

### `create_plan.py`

Generate new plan from task description.

### `update_plan.py`

Mark tasks complete and update progress.

### `plan_summary.py`

Generate progress report for CEO briefing.

### `plan_archive.py`

Move completed plans to Done/ with summary.

## Weekly Review

AI reviews all active plans weekly:

```
1. Check each plan's deadline
   ↓
2. Calculate progress percentage
   ↓
3. Flag at-risk plans (behind schedule)
   ↓
4. Update Dashboard.md
   ↓
5. Include in CEO Briefing
```

## CEO Briefing Integration

Weekly briefing includes:

```markdown
## Plan Status Summary

### Completed This Week
- Website Redesign Plan ✅

### In Progress
- Q1 Tax Prep: 60% complete (On Track)
- Product Launch: 30% complete (At Risk - waiting on design)

### Overdue
- None 🎉

### Recommended Actions
- Product Launch needs design approval - flag for review
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plan too vague | Break into smaller sub-tasks |
| Progress not updating | Ensure AI updates after each action |
| Plans never complete | Set realistic deadlines |
| Too many active plans | Prioritize and defer non-critical |

## Best Practices

1. **Clear Objectives** - Define success criteria upfront
2. **Measurable Tasks** - Each task should be verifiable
3. **Realistic Deadlines** - Account for approval delays
4. **Regular Updates** - Update progress after each action
5. **Blocker Tracking** - Document what's preventing progress
