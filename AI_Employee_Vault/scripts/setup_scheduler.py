"""
Windows Task Scheduler Setup for AI Employee

Creates scheduled tasks for:
- Daily Briefing (8:00 AM)
- CEO Briefing (Monday 7:00 AM)
- Gmail Watcher (every 30 minutes)
- LinkedIn Watcher (every hour)

Silver Tier Implementation

Usage:
    python scripts/setup_scheduler.py
    python scripts/setup_scheduler.py --remove  # Remove all tasks
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class SchedulerSetup:
    """Setup Windows Task Scheduler for AI Employee."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.scripts_dir = self.vault_path / 'scripts'
        self.python_exe = sys.executable
        
        # Task names
        self.tasks = {
            'daily_briefing': 'AI Employee - Daily Briefing',
            'ceo_briefing': 'AI Employee - CEO Briefing',
            'gmail_watcher': 'AI Employee - Gmail Watcher',
            'linkedin_watcher': 'AI Employee - LinkedIn Watcher',
            'linkedin_draft': 'AI Employee - LinkedIn Draft Creator'
        }
        
    def _run_command(self, command: str) -> bool:
        """Run schtasks command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                # Don't treat "task already exists" as error
                if 'ERROR: The system cannot find the file specified' in result.stderr:
                    return False
                if 'The task XML contains an unexpected node' in result.stderr:
                    return False
                print(f"Error: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"Exception: {e}")
            return False
    
    def create_daily_briefing_task(self) -> bool:
        """Create daily briefing task (8:00 AM daily)."""
        script = self.scripts_dir / 'daily_briefing.py'
        
        # Use simpler command format
        cmd = f'schtasks /Create /TN "{self.tasks["daily_briefing"]}" /TR "{self.python_exe} {script}" /SC DAILY /ST 08:00 /RL HIGHEST /F'
        
        return self._run_command(cmd)
    
    def create_ceo_briefing_task(self) -> bool:
        """Create CEO briefing task (Monday 7:00 AM)."""
        script = self.scripts_dir / 'ceo_briefing.py'
        
        cmd = f'schtasks /Create /TN "{self.tasks["ceo_briefing"]}" /TR "{self.python_exe} {script}" /SC WEEKLY /D MON /ST 07:00 /RL HIGHEST /F'
        
        return self._run_command(cmd)
    
    def create_gmail_watcher_task(self) -> bool:
        """Create Gmail watcher task (every 30 minutes)."""
        script = self.scripts_dir / 'gmail_watcher.py'
        
        cmd = f'schtasks /Create /TN "{self.tasks["gmail_watcher"]}" /TR "{self.python_exe} {script} --interval 1800" /SC MINUTE /MO 30 /RL HIGHEST /F'
        
        return self._run_command(cmd)
    
    def create_linkedin_watcher_task(self) -> bool:
        """Create LinkedIn watcher task (every hour)."""
        script = self.scripts_dir / 'linkedin_watcher.py'
        
        cmd = f'schtasks /Create /TN "{self.tasks["linkedin_watcher"]}" /TR "{self.python_exe} {script} --interval 3600" /SC MINUTE /MO 60 /RL HIGHEST /F'
        
        return self._run_command(cmd)
    
    def create_linkedin_draft_task(self) -> bool:
        """Create LinkedIn draft creation task (Monday, Wednesday, Friday 9 AM)."""
        script = self.scripts_dir / 'linkedin_draft.py'
        
        cmd = f'schtasks /Create /TN "{self.tasks["linkedin_draft"]}" /TR "{self.python_exe} {script} --auto" /SC WEEKLY /D MON,WED,FRI /ST 09:00 /RL HIGHEST /F'
        
        return self._run_command(cmd)
    
    def _register_task(self, task_name: str, xml: str) -> bool:
        """Register task with Windows Task Scheduler."""
        # Save XML to temp file
        temp_xml = self.vault_path / f'temp_{task_name.replace(" ", "_")}.xml'
        temp_xml.write_text(xml, encoding='utf-8')
        
        # Delete existing task if exists
        self._run_command(f'schtasks /Delete /TN "{task_name}" /F')
        
        # Register new task
        cmd = f'schtasks /Create /TN "{task_name}" /XML "{temp_xml}" /F'
        success = self._run_command(cmd)
        
        # Clean up temp file
        temp_xml.unlink()
        
        return success
    
    def setup_all_tasks(self) -> bool:
        """Create all scheduled tasks using simple command format."""
        print("\n" + "=" * 60)
        print("Setting up AI Employee Scheduled Tasks")
        print("=" * 60)
        
        tasks = [
            ('Daily Briefing (8 AM daily)', self.create_daily_briefing_task),
            ('CEO Briefing (Monday 7 AM)', self.create_ceo_briefing_task),
            ('Gmail Watcher (every 30 min)', self.create_gmail_watcher_task),
            ('LinkedIn Watcher (every hour)', self.create_linkedin_watcher_task),
            ('LinkedIn Draft Creator (Mon/Wed/Fri 9 AM)', self.create_linkedin_draft_task)
        ]
        
        success_count = 0
        for name, func in tasks:
            print(f"\nCreating: {name}...")
            if func():
                print(f"  ✓ Created: {name}")
                success_count += 1
            else:
                print(f"  ✗ Failed: {name}")
        
        print("\n" + "=" * 60)
        print(f"Setup Complete: {success_count}/{len(tasks)} tasks created")
        print("=" * 60)
        
        # List tasks
        print("\nTo view tasks:")
        print("  Open Task Scheduler → Task Scheduler Library")
        print("  Look for tasks starting with 'AI Employee'")
        print("\nTo run a task manually:")
        print(f'  schtasks /Run /TN "{self.tasks["daily_briefing"]}"')
        
        return success_count == len(tasks)
    
    def remove_all_tasks(self):
        """Remove all AI Employee tasks."""
        print("\nRemoving AI Employee scheduled tasks...")
        
        for task_name in self.tasks.values():
            print(f"  Removing: {task_name}...")
            self._run_command(f'schtasks /Delete /TN "{task_name}" /F')
        
        print("Done!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup AI Employee Scheduler')
    parser.add_argument('--vault', type=str, default=None,
                       help='Path to vault')
    parser.add_argument('--remove', action='store_true',
                       help='Remove all tasks')
    parser.add_argument('--list', action='store_true',
                       help='List existing tasks')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault:
        vault_path = args.vault
    else:
        vault_path = str(Path(__file__).parent.parent)
    
    setup = SchedulerSetup(vault_path)
    
    if args.remove:
        setup.remove_all_tasks()
    elif args.list:
        # List existing tasks
        subprocess.run('schtasks /Query /TN "AI Employee"', shell=True)
    else:
        setup.setup_all_tasks()


if __name__ == '__main__':
    main()
