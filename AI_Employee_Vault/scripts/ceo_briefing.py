"""
CEO Briefing for AI Employee

Generates weekly business summary every Monday:
- Revenue summary
- Completed tasks
- Bottlenecks identified
- Proactive suggestions

Silver Tier Implementation

Usage:
    python scripts/ceo_briefing.py
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta


def _generate_executive_summary(tasks_completed: int, active_plans: int, revenue: str) -> str:
    """Generate executive summary based on metrics."""
    if tasks_completed > 10:
        summary = "Strong week with high productivity. "
    elif tasks_completed > 5:
        summary = "Moderate activity this week. "
    else:
        summary = "Light week. Consider reviewing priorities. "

    if active_plans > 3:
        summary += f"Multiple active plans ({active_plans}) require attention."

    return summary


def _identify_bottlenecks(active_plans: list) -> str:
    """Identify potential bottlenecks."""
    bottlenecks = []

    for plan in active_plans:
        if plan['progress'] < 20:
            bottlenecks.append(f"- **{plan['title']}**: Low progress ({plan['progress']}%)")

    if bottlenecks:
        return "\n".join(bottlenecks)
    else:
        return "*No significant bottlenecks identified*"


def _generate_suggestions(completed: list, active_plans: list) -> str:
    """Generate proactive suggestions."""
    suggestions = []

    # Suggest reviewing low-progress plans
    for plan in active_plans:
        if plan['progress'] < 30:
            suggestions.append(f"- Review **{plan['title']}** - consider reallocating resources")

    # Suggest celebrating wins
    if len(completed) > 10:
        suggestions.append("- Great productivity! Consider documenting successful processes")

    if suggestions:
        return "\n".join(suggestions)
    else:
        return "*No specific suggestions this week*"


def _get_upcoming_deadlines(plans_dir: Path) -> str:
    """Get upcoming deadlines from plans."""
    deadlines = []

    if not plans_dir.exists():
        return "*No upcoming deadlines*"

    today = datetime.now()

    for plan in plans_dir.glob('PLAN_*.md'):
        content = plan.read_text(encoding='utf-8')

        # Extract deadline
        deadline_match = re.search(r'deadline:\s*(\d{4}-\d{2}-\d{2})', content)
        if deadline_match:
            deadline_str = deadline_match.group(1)
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')

            # Extract title
            title_match = re.search(r'title:\s*(.+)', content)
            title = title_match.group(1).strip() if title_match else plan.name

            # Check if due within 2 weeks
            days_until = (deadline - today).days
            if 0 <= days_until <= 14:
                status = "OVERDUE" if days_until < 0 else f"{days_until} days"
                deadlines.append(f"- **{title}**: {status} ({deadline_str})")

    if deadlines:
        return "\n".join(deadlines)
    else:
        return "*No upcoming deadlines in next 2 weeks*"


def generate_ceo_briefing(vault_path: Path) -> str:
    """Generate CEO briefing content."""

    done_dir = vault_path / 'Done'
    plans_dir = vault_path / 'Plans'
    accounting_dir = vault_path / 'Accounting'
    business_goals = vault_path / 'Business_Goals.md'

    # Get last week's date range
    today = datetime.now()
    last_week_start = today - timedelta(days=today.weekday() + 7)
    last_week_end = last_week_start + timedelta(days=6)

    # Count completed tasks this week
    completed_this_week = []
    if done_dir.exists():
        for file in done_dir.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if last_week_start.date() <= mtime.date() <= last_week_end.date():
                    completed_this_week.append(file.name)
            except Exception:
                continue

    # Get accounting summary
    revenue_summary = ""
    transactions_count = 0
    if accounting_dir.exists():
        for file in accounting_dir.glob('*.md'):
            content = file.read_text(encoding='utf-8')
            transactions_count += content.count('amount:')
            # Look for total
            for line in content.split('\n'):
                if 'Total:' in line:
                    revenue_summary = line.strip()

    # Get active plans status
    active_plans = []
    if plans_dir.exists():
        for plan in plans_dir.glob('PLAN_*.md'):
            content = plan.read_text(encoding='utf-8')
            if 'status: in_progress' in content or 'status: pending' in content:
                # Extract title
                title_match = re.search(r'title:\s*(.+)', content)
                title = title_match.group(1).strip() if title_match else plan.name

                # Calculate progress
                completed = content.count('- [x]')
                total = content.count('- [x]') + content.count('- [ ]')
                percent = int((completed / total) * 100) if total > 0 else 0

                active_plans.append({
                    'title': title,
                    'progress': percent,
                    'file': plan.name
                })

    # Load business goals if available
    goals_summary = ""
    if business_goals.exists():
        content = business_goals.read_text(encoding='utf-8')
        # Extract revenue goal if present
        goal_match = re.search(r'Monthly goal:?\s*\$?(\d+)', content)
        if goal_match:
            goals_summary = f"Monthly Revenue Goal: ${goal_match.group(1)}"

    # Generate briefing
    week_start_str = last_week_start.strftime('%Y-%m-%d')
    week_end_str = last_week_end.strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    briefing = f'''# CEO Briefing - Week of {week_start_str}

## Executive Summary

{_generate_executive_summary(len(completed_this_week), len(active_plans), revenue_summary)}

## Revenue

'''

    if revenue_summary:
        briefing += f"- **{revenue_summary}**\n"
    else:
        briefing += "- *No revenue tracked this week*\n"

    if goals_summary:
        briefing += f"- {goals_summary}\n"

    briefing += f'''
## Completed Tasks (Week of {week_start_str} - {week_end_str})

'''

    if completed_this_week:
        for task in completed_this_week[:15]:  # Limit to 15
            briefing += f"- [x] {task}\n"
    else:
        briefing += "*No tasks completed this week*\n"

    briefing += f'''
## Active Plans Status

'''

    if active_plans:
        briefing += "| Plan | Progress | Status |\n"
        briefing += "|------|----------|--------|\n"
        for plan in active_plans:
            status = "On Track" if plan['progress'] > 50 else "In Progress"
            briefing += f"| {plan['title']} | {plan['progress']}% | {status} |\n"
    else:
        briefing += "*No active plans*\n"

    briefing += f'''
## Bottlenecks

{_identify_bottlenecks(active_plans)}

## Proactive Suggestions

{_generate_suggestions(completed_this_week, active_plans)}

## Upcoming Deadlines

{_get_upcoming_deadlines(plans_dir)}

---
*Generated by AI Employee CEO Briefing - {today_str}*
'''

    return briefing


def main():
    """Main entry point."""
    # Get vault path
    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])
    else:
        vault_path = Path(__file__).parent.parent

    print("=" * 60)
    print("AI Employee - CEO Briefing")
    print("=" * 60)

    # Generate briefing
    briefing = generate_ceo_briefing(vault_path)

    # Save to Briefings folder
    briefings_dir = vault_path / 'Briefings'
    briefings_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    briefing_file = briefings_dir / f'{today}_CEO_Briefing.md'

    briefing_file.write_text(briefing, encoding='utf-8')

    print(f"\n✓ CEO Briefing created: {briefing_file}")
    print(f"\nSaved to: Briefings/{briefing_file.name}")

    # Update Dashboard
    dashboard_path = vault_path / 'Dashboard.md'
    if dashboard_path.exists():
        content = dashboard_path.read_text(encoding='utf-8')
        if '| Last CEO Briefing |' in content:
            content = re.sub(
                r'\| Last CEO Briefing \|.*\|',
                f'| Last CEO Briefing | {today} |',
                content
            )
            dashboard_path.write_text(content, encoding='utf-8')
            print(f"  - Dashboard updated")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
