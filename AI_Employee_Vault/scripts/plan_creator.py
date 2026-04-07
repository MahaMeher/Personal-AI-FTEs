"""
Plan Creator for AI Employee

Creates structured Plan.md files for multi-step tasks.
Breaks down complex objectives into actionable checkboxes with progress tracking.

Silver Tier Implementation

Usage:
    python scripts/plan_creator.py --task "Task Name" --deadline "2026-01-31"
    python scripts/plan_creator.py --auto  # Process tasks in Needs_Action
"""

import sys
import re
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))


class PlanCreator:
    """
    Plan Creator - Creates and manages multi-step plans.
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize Plan Creator.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.plans_dir = self.vault_path / 'Plans'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging."""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f'plan_creator_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('PlanCreator')
    
    def create_plan(self, title: str, deadline: str = None, 
                    tasks: List[str] = None, priority: str = 'normal') -> Optional[Path]:
        """
        Create a new plan.
        
        Args:
            title: Plan title
            deadline: Deadline date (YYYY-MM-DD)
            tasks: List of tasks
            priority: Plan priority (low, normal, high)
            
        Returns:
            Path to created plan file
        """
        if not deadline:
            # Default: 2 weeks from now
            deadline = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        if not tasks:
            tasks = self._generate_default_tasks(title)
        
        # Create plan filename
        safe_title = self._sanitize_filename(title)
        plan_file = self.plans_dir / f'PLAN_{safe_title}_{datetime.now().strftime("%Y%m%d")}.md'
        
        # Generate plan content
        content = self._generate_plan_content(title, deadline, tasks, priority)
        
        plan_file.write_text(content, encoding='utf-8')
        self.logger.info(f"Created plan: {plan_file.name}")
        
        # Update dashboard
        self._update_dashboard()
        
        return plan_file
    
    def _generate_plan_content(self, title: str, deadline: str, 
                               tasks: List[str], priority: str) -> str:
        """Generate plan Markdown content."""
        
        # Calculate phases
        phases = self._organize_into_phases(tasks)
        
        content = f'''---
type: plan
title: {title}
created: {datetime.now().isoformat()}
deadline: {deadline}
priority: {priority}
status: in_progress
owner: AI Employee
---

# Plan: {title}

## Objective

{self._generate_objective(title)}

## Success Criteria

'''
        # Add success criteria checkboxes
        for i, task in enumerate(tasks[:5], 1):
            content += f"- [ ] {task}\n"
        
        content += "\n## Tasks\n\n"
        
        # Add phases
        for phase_name, phase_tasks in phases.items():
            content += f"### {phase_name}\n\n"
            for task in phase_tasks:
                content += f"- [ ] {task}\n"
            content += "\n"
        
        # Add progress table
        content += f'''## Progress

| Phase | Status | Completion |
|-------|--------|------------|
'''
        for phase_name in phases.keys():
            content += f"| {phase_name} | Pending | 0% |\n"
        
        # Add blockers and notes
        content += f'''
## Blockers

*None yet*

## Notes

*Add notes during execution*

---
*Created by Plan Creator - {datetime.now().strftime('%Y-%m-%d %H:%M')}*
'''
        
        return content
    
    def _generate_default_tasks(self, title: str) -> List[str]:
        """Generate default tasks based on title keywords."""
        title_lower = title.lower()
        
        if 'email' in title_lower or 'response' in title_lower:
            return [
                'Review email content',
                'Draft response',
                'Get approval if needed',
                'Send response',
                'Archive email'
            ]
        elif 'payment' in title_lower or 'invoice' in title_lower:
            return [
                'Verify payment details',
                'Check approval requirements',
                'Create approval request',
                'Process payment after approval',
                'Update accounting records',
                'Archive documentation'
            ]
        elif 'post' in title_lower or 'linkedin' in title_lower:
            return [
                'Draft post content',
                'Review against company guidelines',
                'Get human approval',
                'Schedule or publish post',
                'Monitor engagement'
            ]
        elif 'meeting' in title_lower or 'call' in title_lower:
            return [
                'Check calendar availability',
                'Propose meeting times',
                'Send calendar invite',
                'Prepare agenda',
                'Follow up after meeting'
            ]
        else:
            return [
                'Analyze task requirements',
                'Break down into subtasks',
                'Execute phase 1',
                'Execute phase 2',
                'Review and complete'
            ]
    
    def _organize_into_phases(self, tasks: List[str]) -> Dict[str, List[str]]:
        """Organize tasks into phases."""
        if len(tasks) <= 3:
            return {'Phase 1': tasks}
        
        # Split into 3 phases
        third = len(tasks) // 3
        return {
            'Phase 1: Preparation': tasks[:third],
            'Phase 2: Execution': tasks[third:2*third],
            'Phase 3: Completion': tasks[2*third:]
        }
    
    def _generate_objective(self, title: str) -> str:
        """Generate objective statement from title."""
        return f"Complete: {title}. This plan breaks down the task into manageable steps with clear success criteria and progress tracking."
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:50]
    
    def _update_dashboard(self):
        """Update Dashboard.md with active plans count."""
        if not self.dashboard.exists():
            return
        
        try:
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Count active plans
            active_plans = len(list(self.plans_dir.glob('PLAN_*.md')))
            
            # Update plans count if exists
            if '| Active Plans |' in content:
                content = re.sub(
                    r'\| Active Plans \|.*\|',
                    f'| Active Plans | {active_plans} |',
                    content
                )
            
            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.debug("Dashboard updated")
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
    
    def update_plan_progress(self, plan_path: Path, completed_tasks: List[str]) -> bool:
        """
        Update plan progress.
        
        Args:
            plan_path: Path to plan file
            completed_tasks: List of completed task names
            
        Returns:
            True if updated successfully
        """
        if not plan_path.exists():
            return False
        
        try:
            content = plan_path.read_text(encoding='utf-8')
            
            # Mark tasks as completed
            for task in completed_tasks:
                # Find and check off task
                pattern = rf'- \[ \] {re.escape(task)}'
                replacement = f'- [x] {task}'
                content = re.sub(pattern, replacement, content)
            
            # Update progress table (simplified)
            completed = content.count('- [x]')
            total = content.count('- [x]') + content.count('- [ ]')
            percent = int((completed / total) * 100) if total > 0 else 0
            
            if percent == 100:
                # Update status to completed
                content = re.sub(r'status:\s*\w+', 'status: completed', content)
                content += f"\n\n## Completed\n\n*Plan completed on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
            
            plan_path.write_text(content, encoding='utf-8')
            self.logger.info(f"Updated progress for {plan_path.name}: {percent}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating plan: {e}")
            return False
    
    def get_active_plans(self) -> List[Path]:
        """Get list of active (in-progress) plans."""
        plans = []
        for plan_file in self.plans_dir.glob('PLAN_*.md'):
            content = plan_file.read_text(encoding='utf-8')
            if 'status: in_progress' in content or 'status: pending' in content:
                plans.append(plan_file)
        return plans
    
    def get_plan_summary(self) -> str:
        """Get summary of all active plans."""
        active = self.get_active_plans()
        
        if not active:
            return "No active plans"
        
        summary = "## Active Plans\n\n"
        for plan in active:
            content = plan.read_text(encoding='utf-8')
            
            # Extract title
            title_match = re.search(r'title:\s*(.+)', content)
            title = title_match.group(1).strip() if title_match else plan.name
            
            # Extract deadline
            deadline_match = re.search(r'deadline:\s*(\S+)', content)
            deadline = deadline_match.group(1) if deadline_match else 'N/A'
            
            # Calculate progress
            completed = content.count('- [x]')
            total = content.count('- [x]') + content.count('- [ ]')
            percent = int((completed / total) * 100) if total > 0 else 0
            
            summary += f"- **{title}**: {percent}% complete (Due: {deadline})\n"
        
        return summary


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Plan Creator for AI Employee')
    parser.add_argument('--task', type=str, help='Task name for new plan')
    parser.add_argument('--deadline', type=str, help='Deadline (YYYY-MM-DD)')
    parser.add_argument('--priority', type=str, default='normal',
                       choices=['low', 'normal', 'high'],
                       help='Plan priority')
    parser.add_argument('--vault', type=str, default=None,
                       help='Path to vault')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-create plans from Needs_Action items')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault:
        vault_path = args.vault
    else:
        vault_path = str(Path(__file__).parent.parent)
    
    creator = PlanCreator(vault_path)
    
    if args.auto:
        # Auto-create plans from complex tasks
        print("Checking for tasks that need plans...")
        # This would integrate with Needs_Action processing
        print("Auto-plan creation not yet implemented")
        
    elif args.task:
        # Create new plan
        plan_path = creator.create_plan(
            title=args.task,
            deadline=args.deadline,
            priority=args.priority
        )
        print(f"\n✓ Plan created: {plan_path}")
        
    else:
        # Show active plans
        print("\nActive Plans:")
        print(creator.get_plan_summary())


if __name__ == '__main__':
    main()
