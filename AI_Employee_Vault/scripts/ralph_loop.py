#!/usr/bin/env python3
"""
Ralph Wiggum Loop Orchestrator

Gold Tier Feature: Personal AI FTEs Project

Implements the "Ralph Wiggum" pattern for autonomous multi-step task completion.
This orchestrator keeps Claude Code iterating until tasks are complete.

How it works:
1. Creates state file with task prompt
2. Launches Claude with the prompt
3. Monitors for task completion (file moved to /Done)
4. If not complete and Claude tries to exit, re-inject prompt
5. Repeat until complete or max iterations reached

Reference: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""

import os
import sys
import json
import time
import logging
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ralph_loop.log')
    ]
)
logger = logging.getLogger('ralph-loop')

# Configuration
VAULT_PATH = os.getenv('VAULT_PATH', 'D:/Personal-AI-FTEs/AI_Employee_Vault')
MAX_ITERATIONS = int(os.getenv('MAX_ITERATIONS', '10'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '5'))  # seconds
CLAUDE_TIMEOUT = int(os.getenv('CLAUDE_TIMEOUT', '300'))  # seconds per iteration


class TaskState:
    """Represents the state of a task being processed"""
    
    def __init__(self, task_id: str, prompt: str, status: str = 'pending'):
        self.task_id = task_id
        self.prompt = prompt
        self.status = status  # pending, in_progress, completed, failed
        self.iteration = 0
        self.created = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
        self.claude_output = []
        self.error = None
    
    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'prompt': self.prompt,
            'status': self.status,
            'iteration': self.iteration,
            'created': self.created,
            'last_updated': self.last_updated,
            'claude_output': self.claude_output[-5:],  # Keep last 5 outputs
            'error': self.error
        }
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.now().isoformat()


class RalphLoopOrchestrator:
    """Orchestrates the Ralph Wiggum loop for autonomous task completion"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.state_folder = self.vault_path / '.ralph_state'
        
        # Ensure directories exist
        for folder in [self.in_progress, self.plans, self.state_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.current_task: Optional[TaskState] = None
        self.claude_process: Optional[subprocess.Popen] = None
    
    def create_task(self, prompt: str, task_id: Optional[str] = None) -> TaskState:
        """Create a new task state"""
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = TaskState(task_id, prompt)
        
        # Save state file
        state_file = self.state_folder / f"{task_id}.json"
        state_file.write_text(json.dumps(task.to_dict(), indent=2))
        
        # Create state marker file in In_Progress
        marker_file = self.in_progress / f"RALPH_{task_id}.md"
        marker_file.write_text(f"""---
task_id: {task_id}
created: {task.created}
status: pending
iteration: 0
max_iterations: {MAX_ITERATIONS}
---

# Ralph Wiggum Loop Task

## Prompt
{prompt}

## Status
Task is queued for processing by Claude Code.

## Instructions for Claude
1. Read this task file
2. Execute the prompt
3. Move to /Done when complete
4. Output TASK_COMPLETE when finished

---
*Managed by Ralph Wiggum Loop Orchestrator*
""")
        
        logger.info(f"Created task: {task_id}")
        return task
    
    def check_task_completion(self, task_id: str) -> bool:
        """Check if task has been completed (file moved to Done)"""
        # Check if marker file exists in Done
        marker_in_done = self.done.glob(f"RALPH_{task_id}.md")
        if any(marker_in_done):
            return True
        
        # Check if any file with this task_id exists in Done
        for file in self.done.glob("*.md"):
            try:
                content = file.read_text(encoding='utf-8')
                if task_id in content:
                    return True
            except Exception:
                continue
        
        return False
    
    def launch_claude(self, task: TaskState) -> bool:
        """Launch Claude Code with the task prompt"""
        try:
            # Update task state
            task.update(status='in_progress', iteration=task.iteration + 1)
            self._save_state(task)
            
            # Update marker file
            marker_file = self.in_progress / f"RALPH_{task.task_id}.md"
            if marker_file.exists():
                content = marker_file.read_text(encoding='utf-8')
                content = content.replace('status: pending', 'status: in_progress')
                content = content.replace(f'iteration: {task.iteration - 1}', f'iteration: {task.iteration}')
                marker_file.write_text(content)
            
            # Prepare Claude command
            # The prompt includes instructions to keep iterating
            claude_prompt = f"""{task.prompt}

IMPORTANT INSTRUCTIONS:
1. Work on this task step by step
2. When you complete a step, document it in the task file
3. Continue working until the task is fully complete
4. When COMPLETELY DONE, output: <promise>TASK_COMPLETE</promise>
5. Do not exit until the task is fully complete
6. If you need to make multiple API calls or file operations, do them all before completing

Current iteration: {task.iteration}/{MAX_ITERATIONS}

Begin working on this task now:"""
            
            # Launch Claude Code
            # Note: This assumes claude is in PATH
            cmd = ['claude', '--prompt', claude_prompt]
            
            logger.info(f"Launching Claude (iteration {task.iteration})")
            self.claude_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.vault_path)
            )
            
            # Wait for process with timeout
            try:
                stdout, stderr = self.claude_process.communicate(timeout=CLAUDE_TIMEOUT)
                task.claude_output.append({
                    'iteration': task.iteration,
                    'output': stdout[:5000],  # Keep first 5000 chars
                    'error': stderr[:2000] if stderr else None,
                    'return_code': self.claude_process.returncode
                })
                
                # Check if Claude completed the task
                if '<promise>TASK_COMPLETE</promise>' in stdout:
                    logger.info("Claude signaled task completion")
                    return True
                
                # Check if task file was moved to Done
                if self.check_task_completion(task.task_id):
                    logger.info("Task file moved to Done")
                    return True
                
                return False
                
            except subprocess.TimeoutExpired:
                logger.warning(f"Claude timed out after {CLAUDE_TIMEOUT}s")
                self.claude_process.kill()
                task.claude_output.append({
                    'iteration': task.iteration,
                    'error': f'Timeout after {CLAUDE_TIMEOUT}s'
                })
                return False
            
        except Exception as e:
            logger.error(f"Error launching Claude: {e}")
            task.update(error=str(e))
            return False
    
    def _save_state(self, task: TaskState):
        """Save task state to file"""
        state_file = self.state_folder / f"{task.task_id}.json"
        state_file.write_text(json.dumps(task.to_dict(), indent=2))
    
    def run_task(self, task: TaskState) -> bool:
        """Run the Ralph Wiggum loop for a task"""
        logger.info(f"Starting Ralph Wiggum loop for task: {task.task_id}")
        logger.info(f"Max iterations: {MAX_ITERATIONS}")
        
        while task.iteration < MAX_ITERATIONS:
            # Launch Claude
            completed = self.launch_claude(task)
            
            if completed:
                logger.info(f"Task completed in {task.iteration} iterations")
                task.update(status='completed')
                self._save_state(task)
                
                # Move marker file to Done
                marker_file = self.in_progress / f"RALPH_{task.task_id}.md"
                if marker_file.exists():
                    dest = self.done / f"RALPH_{task.task_id}.md"
                    marker_file.rename(dest)
                
                return True
            
            # Check if we should continue
            if task.iteration >= MAX_ITERATIONS:
                logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached")
                task.update(status='failed', error='Max iterations reached')
                self._save_state(task)
                return False
            
            # Wait before next iteration
            logger.info(f"Waiting {CHECK_INTERVAL}s before next iteration...")
            time.sleep(CHECK_INTERVAL)
        
        return False
    
    def process_needs_action_folder(self) -> int:
        """Process all files in Needs_Action folder using Ralph loop"""
        processed = 0
        
        for file in self.needs_action.glob("*.md"):
            try:
                content = file.read_text(encoding='utf-8')
                
                # Extract task description from file
                # Use the filename and first few lines as the prompt
                lines = content.split('\n')[:10]
                task_description = '\n'.join(lines)
                
                prompt = f"""Process this action file from the Needs_Action folder:

File: {file.name}

Content:
{content}

Instructions:
1. Read and understand the task
2. Execute all required actions
3. Document what you did in the file
4. Move the file to /Done when complete
5. Output <promise>TASK_COMPLETE</promise> when done"""
                
                # Create and run task
                task = self.create_task(prompt, task_id=file.stem)
                success = self.run_task(task)
                
                if success:
                    processed += 1
                    logger.info(f"Successfully processed: {file.name}")
                else:
                    logger.error(f"Failed to process: {file.name}")
                
            except Exception as e:
                logger.error(f"Error processing {file.name}: {e}")
        
        return processed
    
    def get_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task"""
        state_file = self.state_folder / f"{task_id}.json"
        if state_file.exists():
            return json.loads(state_file.read_text())
        return None
    
    def list_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """List all tasks, optionally filtered by status"""
        tasks = []
        for state_file in self.state_folder.glob("*.json"):
            try:
                task_data = json.loads(state_file.read_text())
                if status is None or task_data.get('status') == status:
                    tasks.append(task_data)
            except Exception as e:
                logger.error(f"Error reading {state_file}: {e}")
        return tasks


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop Orchestrator')
    parser.add_argument('prompt', nargs='?', help='Task prompt or description')
    parser.add_argument('--task-id', help='Custom task ID')
    parser.add_argument('--max-iterations', type=int, default=MAX_ITERATIONS,
                       help=f'Maximum iterations (default: {MAX_ITERATIONS})')
    parser.add_argument('--process-needs-action', action='store_true',
                       help='Process all files in Needs_Action folder')
    parser.add_argument('--status', help='Get status of a task by ID')
    parser.add_argument('--list', action='store_true', help='List all tasks')
    
    args = parser.parse_args()
    
    vault_path = VAULT_PATH
    
    # Verify vault exists
    if not Path(vault_path).exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    orchestrator = RalphLoopOrchestrator(vault_path)
    
    try:
        if args.status:
            # Get task status
            status = orchestrator.get_status(args.status)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print(f"Task not found: {args.status}")
                sys.exit(1)
        
        elif args.list:
            # List all tasks
            tasks = orchestrator.list_tasks()
            print(json.dumps(tasks, indent=2))
        
        elif args.process_needs_action:
            # Process Needs_Action folder
            processed = orchestrator.process_needs_action_folder()
            print(f"Processed {processed} tasks from Needs_Action folder")
        
        elif args.prompt:
            # Create and run single task
            task = orchestrator.create_task(args.prompt, args.task_id)
            print(f"Created task: {task.task_id}")
            print(f"Starting Ralph Wiggum loop (max {MAX_ITERATIONS} iterations)...")
            
            success = orchestrator.run_task(task)
            
            if success:
                print(f"✅ Task completed in {task.iteration} iterations")
                sys.exit(0)
            else:
                print(f"❌ Task failed after {task.iteration} iterations")
                if task.error:
                    print(f"Error: {task.error}")
                sys.exit(1)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        if orchestrator.claude_process:
            orchestrator.claude_process.terminate()
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
