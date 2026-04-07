"""
Orchestrator Module

Main coordination script for the AI Employee system.
Monitors the Needs_Action folder and triggers Qwen Code to process pending items.
Handles cleanup, deduplication, and proper file flow management.
"""

import subprocess
import sys
import logging
import platform
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Set, Dict
import time


class Orchestrator:
    """
    Orchestrates the AI Employee workflow.

    Monitors folders, triggers Qwen Code processing, and updates the Dashboard.
    Handles cleanup, deduplication, and proper file lifecycle management.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root directory
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.pending_approval = self.vault_path / 'Pending_Approval'

        # Ensure directories exist
        for folder in [self.needs_action, self.done, self.logs, self.approved, self.rejected, self.pending_approval]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Track processed files (by hash) to avoid duplicates
        self.processed_files: Set[str] = set()

        self.logger.info(f'Orchestrator initialized for vault: {self.vault_path}')

    def _setup_logging(self) -> None:
        """Setup logging to file and console."""
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate a simple hash for file deduplication."""
        try:
            content = file_path.read_text(encoding='utf-8')
            return f"{file_path.name}:{len(content)}:{hash(content) % 1000000}"
        except Exception:
            return str(file_path)

    def get_pending_files(self) -> List[Path]:
        """
        Get list of pending action files.

        Returns:
            List of Path objects for .md files in Needs_Action
        """
        if not self.needs_action.exists():
            return []

        pending = []
        for file_path in self.needs_action.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.md':
                file_hash = self._calculate_file_hash(file_path)
                if file_hash not in self.processed_files:
                    pending.append(file_path)

        return sorted(pending, key=lambda x: x.stat().st_mtime)

    def trigger_qwen_processing(self) -> bool:
        """
        Trigger Qwen Code to process pending items in batches of 5.
        
        Returns:
            True if processing was triggered, False if no pending items
        """
        pending_files = self.get_pending_files()

        if not pending_files:
            self.logger.debug('No pending items to process')
            return False

        # Process in batches of 2 to avoid Windows command line length limits
        batch_size = 2
        batch_files = pending_files[:batch_size]
        
        self.logger.info(f'Found {len(pending_files)} pending item(s), processing batch of {len(batch_files)}')

        # Build the prompt for Qwen
        prompt = self._build_qwen_prompt(batch_files)

        # Log the action
        self._log_action('trigger_qwen', {
            'pending_files': [f.name for f in pending_files],
            'prompt_length': len(prompt)
        })

        try:
            use_shell = platform.system() == 'Windows'

            result = subprocess.run(
                ['qwen', '--version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=use_shell
            )

            if result.returncode == 0:
                self.logger.info(f'Qwen Code found (version: {result.stdout.strip()}), triggering processing...')
                success = self._run_qwen_interactive(prompt)
                if success:
                    # Mark files as processed after Qwen runs
                    for f in pending_files:
                        self.processed_files.add(self._calculate_file_hash(f))
                return success
            else:
                self.logger.warning(f'Qwen Code returned error: {result.stderr}')
                return self._create_processing_instructions(pending_files)

        except FileNotFoundError:
            self.logger.warning('Qwen Code not installed, creating processing instructions')
            return self._create_processing_instructions(pending_files)
        except subprocess.TimeoutExpired:
            self.logger.error('Timeout checking Qwen Code version')
            return False
        except Exception as e:
            self.logger.error(f'Error triggering Qwen: {e}')
            return False

    def _build_qwen_prompt(self, pending_files: List[Path]) -> str:
        """Build a prompt for Qwen Code based on pending files."""

        files_info = []
        for file_path in pending_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                files_info.append(f"## File: {file_path.name}\n\n{content}\n")
            except Exception as e:
                files_info.append(f"## File: {file_path.name}\n\n[Error reading file: {e}]\n")

        prompt = f"""You are the AI Employee assistant. Process the following pending action files from the Obsidian vault.

## Context
- Vault: {self.vault_path}
- Current time: {datetime.now().isoformat()}
- Pending files: {len(pending_files)}

## Instructions - OUTPUT JSON ONLY

You MUST output ONLY valid JSON, no explanations, no options.

### For Each Email, Output This JSON Format:

```json
{
  "action": "create_approval",
  "source_file": "EMAIL_*.md",
  "to": "sender@email.com",
  "subject": "Re: Original Subject",
  "body": "A complete friendly reply - write the FULL response text here",
  "approval_file": "APPROVAL_Email_Name_YYYY-MM-DD.md"
}
```

### Rules for body field:
- Write a COMPLETE friendly reply (2-4 sentences)
- Include greeting, acknowledgment, and sign-off
- NO options (A/B/C)
- NO "Option A:", "Option B:", etc.
- Just ONE complete reply text

### Example Output:

```json
{
  "action": "create_approval",
  "source_file": "EMAIL_abc123.md",
  "to": "john@example.com",
  "subject": "Re: Meeting",
  "body": "Hi John,\n\nThank you for your email. I received your message about the meeting.\n\nBest regards,\nAI Employee"
}
```

## Pending Files

{''.join(files_info)}

## Output Format

**OUTPUT ONLY JSON - nothing else. NO explanations, NO options.**
"""

        return prompt

    def _run_qwen_interactive(self, prompt: str) -> bool:
        """
        Run Qwen Code automatically to process pending items.
        Reads prompt from file to avoid command line length limits.
        """
        try:
            prompt_file = self.vault_path / '.qwen_prompt.txt'
            prompt_file.write_text(prompt, encoding='utf-8')

            self.logger.info(f'Prompt written to: {prompt_file}')
            self.logger.info('Starting Qwen Code to process pending items...')
            self.logger.info('Note: Running with -y flag, reading from .qwen_prompt.txt')

            use_shell = platform.system() == 'Windows'

            # Use UTF-8 encoding to handle special characters (emoji, etc.)
            # On Windows, set PYTHONIOENCODING to utf-8
            env = None
            if use_shell:
                import os
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

            # Read prompt from file using type command and pipe to qwen
            result = subprocess.run(
                f'type ".qwen_prompt.txt" | qwen -y',
                cwd=str(self.vault_path),
                timeout=600,
                shell=use_shell,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            if result.returncode == 0:
                self.logger.info('Qwen Code processing completed successfully')
                return True
            else:
                self.logger.warning(f'Qwen Code exited with code: {result.returncode}')
                if result.stderr:
                    self.logger.error(f'Qwen error output: {result.stderr[:500]}')
                return True

        except subprocess.TimeoutExpired:
            self.logger.error('Qwen Code processing timed out (10 minutes)')
            self.logger.info('Items are still being processed')
            return True
        except Exception as e:
            self.logger.error(f'Error running Qwen: {e}')
            return False

    def _create_processing_instructions(self, pending_files: List[Path]) -> bool:
        """
        Create instructions file for manual Qwen processing.

        This is a fallback when Qwen Code CLI is not available.
        """
        try:
            instructions_file = self.vault_path / 'PROCESS_ME.md'

            content = f"""---
created: {datetime.now().isoformat()}
type: processing_request
status: pending
files_count: {len(pending_files)}
---

# AI Employee Processing Request

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Pending Files:** {len(pending_files)}

## Instructions

1. Open Qwen Code in this vault directory
2. Run: `qwen "Process the pending items in /Needs_Action folder"`
3. Follow the Company Handbook rules
4. Update this file when complete

## Pending Files

"""

            for file_path in pending_files:
                content += f"- `{file_path.name}`\n"

            content += f"""
## Processing Log

*Awaiting processing...*

---
*This file was auto-generated by orchestrator.py*
"""

            instructions_file.write_text(content, encoding='utf-8')

            self.logger.info(f'Created processing instructions: {instructions_file}')
            return True

        except Exception as e:
            self.logger.error(f'Error creating instructions: {e}')
            return False

    def update_dashboard(self) -> None:
        """Update the Dashboard.md with current status."""
        try:
            pending_count = len(self.get_pending_files())
            done_count = len(list(self.done.glob('*.md'))) if self.done.exists() else 0
            approved_count = len(list(self.approved.glob('*.md'))) if self.approved.exists() else 0

            if self.dashboard.exists():
                content = self.dashboard.read_text(encoding='utf-8')

                content = re.sub(
                    r'\| Pending Tasks \|.*\|',
                    f'| Pending Tasks | {pending_count} |',
                    content
                )
                content = re.sub(
                    r'\| Completed Today \|.*\|',
                    f'| Completed Today | {done_count} |',
                    content
                )
                content = re.sub(
                    r'\| Last Activity \|.*\|',
                    f'| Last Activity | {datetime.now().strftime("%Y-%m-%d %H:%M")} |',
                    content
                )

                self.dashboard.write_text(content, encoding='utf-8')
                self.logger.debug('Dashboard updated')

        except Exception as e:
            self.logger.error(f'Error updating dashboard: {e}')

    def get_approved_actions(self) -> List[Path]:
        """
        Get list of approved action files ready for execution.

        Returns:
            List of Path objects for .md files in Approved/
        """
        if not self.approved.exists():
            return []

        approved = []
        for file_path in self.approved.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.md':
                file_hash = self._calculate_file_hash(file_path)
                if file_hash not in self.processed_files:
                    approved.append(file_path)

        return sorted(approved, key=lambda x: x.stat().st_mtime)

    def process_approved_actions(self) -> bool:
        """
        Process approved actions - send emails directly (no Qwen needed).
        """
        approved_files = self.get_approved_actions()

        if not approved_files:
            self.logger.debug('No approved actions to execute')
            return False

        self.logger.info(f'Found {len(approved_files)} approved action(s) to execute')

        # Execute each approved file directly
        for approved_file in approved_files:
            self._execute_approval_file(approved_file)
        
        return True

    def _parse_and_create_approvals(self, qwen_output: str):
        """Parse Qwen's JSON output and create approval files."""
        import json
        
        # Find all JSON blocks in output
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, qwen_output, re.DOTALL)
        
        approvals_created = 0
        for match in matches:
            try:
                data = json.loads(match.strip())
                
                if data.get('action') != 'create_approval':
                    continue
                
                # Extract fields
                source_file = data.get('source_file', '')
                to_email = data.get('to', '')
                subject = data.get('subject', '')
                body = data.get('body', '')
                approval_filename = data.get('approval_file', f'APPROVAL_Email_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
                
                if not all([source_file, to_email, subject, body]):
                    self.logger.warning(f'Missing fields in JSON: {data}')
                    continue
                
                # Create approval file content
                approval_content = f'''---
type: approval_request
action: email_response
to: "{to_email}"
subject: "{subject}"
body: "{body}"
status: pending
source_file: {source_file}
created: {datetime.now().isoformat()}
---

# Email Reply Approval

**From:** {to_email}
**Subject:** {subject}

## Draft Reply

{body}

---
**Move to /Approved/ to send this email.**
'''
                
                # Save approval file
                approval_file = self.pending_approval / approval_filename
                approval_file.write_text(approval_content, encoding='utf-8')
                
                # Update source file
                source_path = self.needs_action / source_file
                if source_path.exists():
                    source_content = source_path.read_text(encoding='utf-8')
                    if 'status: pending' in source_content or 'status: awaiting_approval' in source_content:
                        source_content = re.sub(
                            r'status:\s*(pending|awaiting_approval)',
                            'status: awaiting_approval',
                            source_content
                        )
                        source_content += f'\n\n## Approval\nAwaiting approval - see {approval_filename}\n'
                        source_path.write_text(source_content, encoding='utf-8')
                
                self.logger.info(f'Created approval: {approval_filename}')
                self.logger.info(f'To: {to_email}, Subject: {subject}')
                approvals_created += 1
                
            except json.JSONDecodeError as e:
                self.logger.debug(f'Could not parse JSON: {e}')
            except Exception as e:
                self.logger.error(f'Error processing approval: {e}')
        
        self.logger.info(f'Created {approvals_created} approval file(s)')

    def _execute_approval_file(self, approved_file: Path):
        """Execute an approved action file - send email if it's an email approval."""
        try:
            content = approved_file.read_text(encoding='utf-8')
            
            # Check if this is an email approval
            if 'action: email_response' not in content:
                self.logger.debug(f'Not an email approval: {approved_file.name}')
                return
            
            # Extract email details from frontmatter
            import re
            
            to_match = re.search(r'to:\s*["\']?([^"\'\n]+)["\']?', content)
            subject_match = re.search(r'subject:\s*["\']?([^"\'\n]+)["\']?', content)
            body_match = re.search(r'body:\s*["\']?([^"\'\n]+)["\']?', content)
            source_match = re.search(r'source_file:\s*(\S+)', content)
            
            if not all([to_match, subject_match, body_match]):
                self.logger.warning(f'Missing email fields in {approved_file.name}')
                return
            
            to_email = to_match.group(1).strip()
            subject = subject_match.group(1).strip()
            body = body_match.group(1).strip()
            source_file = source_match.group(1) if source_match else None
            
            self.logger.info(f'Sending email to {to_email}: {subject}')

            # Fix: Convert literal \n strings to actual newlines
            # YAML stores newlines as literal \n, need to decode them
            import codecs
            body_decoded = codecs.decode(body, 'unicode_escape')
            
            # Send via MCP server - use temp file to avoid shell escaping issues
            import tempfile
            import os
            
            # Write body to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                f.write(body_decoded)
                body_file = f.name
            
            subject_escaped = subject.replace('"', '\\"')

            cmd = (
                f'python "mcp/email_server.py" send '
                f'--to "{to_email}" '
                f'--subject "{subject_escaped}" '
                f'--body-file "{body_file}"'
            )

            use_shell = platform.system() == 'Windows'
            result = subprocess.run(
                cmd,
                cwd=str(self.vault_path),
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Clean up temp file
            try:
                os.unlink(body_file)
            except:
                pass

            output = result.stdout + result.stderr
            
            # Check if email was sent successfully
            if '[OK] Email SENT successfully' in output or 'Message ID:' in output:
                self.logger.info(f'Email sent successfully to {to_email}')
                
                # Extract message ID
                msg_id_match = re.search(r'Message ID:\s*(\S+)', output)
                message_id = msg_id_match.group(1) if msg_id_match else 'unknown'
                
                # Update approval file with executed status
                new_content = re.sub(
                    r'status:\s*pending',
                    f'status: executed\nexecuted: {datetime.now().isoformat()}\nmessage_id: {message_id}',
                    content
                )
                approved_file.write_text(new_content, encoding='utf-8')
                
                # Update source file if it exists
                if source_file:
                    source_path = self.needs_action / source_file
                    if source_path.exists():
                        source_content = source_path.read_text(encoding='utf-8')
                        if 'status: awaiting_approval' in source_content:
                            source_content = re.sub(
                                r'status:\s*awaiting_approval',
                                'status: completed',
                                source_content
                            )
                            source_content += f'\n\n## Executed\nEmail sent via approval: {approved_file.name}\nMessage ID: {message_id}\n'
                            source_path.write_text(source_content, encoding='utf-8')
                            self.logger.info(f'Updated source file: {source_file}')
                
                self.logger.info(f'Approval file updated: {approved_file.name}')
                
            else:
                self.logger.warning(f'Email send may have failed: {output[:200]}')
                # Update with failed status
                new_content = re.sub(
                    r'status:\s*pending',
                    f'status: failed\nfailed: {datetime.now().isoformat()}\nerror: {output[:200]}',
                    content
                )
                approved_file.write_text(new_content, encoding='utf-8')
                
        except Exception as e:
            self.logger.error(f'Error executing approval file {approved_file.name}: {e}')

    def cleanup_completed_files(self) -> int:
        """
        Move completed files from Needs_Action to Done.

        Files are considered completed if:
        - status: completed in frontmatter (simple action done)
        - status: executed in frontmatter (approval executed)
        - status: rejected in frontmatter (human rejected)

        Files that should STAY in Needs_Action:
        - status: awaiting_approval (approval created, waiting for human)
        - status: awaiting_human_input (clarification needed, waiting for human)
        - status: processed (generic - need to check context)

        Returns:
            Number of files moved
        """
        moved_count = 0

        if not self.needs_action.exists():
            return 0

        for file_path in self.needs_action.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() != '.md':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # Files that should STAY in Needs_Action
                if 'status: awaiting_approval' in content:
                    self.logger.debug(f'Keeping {file_path.name} in Needs_Action (awaiting approval)')
                    continue
                elif 'status: awaiting_human_input' in content:
                    self.logger.debug(f'Keeping {file_path.name} in Needs_Action (awaiting human input)')
                    continue

                # Files ready to move to Done
                if 'status: completed' in content or 'status: executed' in content:
                    self._move_to_done(file_path, 'completed')
                    moved_count += 1
                elif 'status: rejected' in content:
                    self._move_to_done(file_path, 'rejected')
                    moved_count += 1
                elif 'status: processed' in content:
                    # Check if this is a clarification scenario (should stay)
                    if 'awaiting_approval' in content or 'awaiting_human_input' in content:
                        self.logger.debug(f'Keeping {file_path.name} in Needs_Action (processed but awaiting response)')
                        continue
                    else:
                        # Generic processed, safe to move
                        self._move_to_done(file_path, 'processed')
                        moved_count += 1

            except Exception as e:
                self.logger.error(f'Error checking file {file_path.name}: {e}')

        return moved_count

    def cleanup_executed_approvals(self) -> int:
        """
        Move executed approval files from Approved folder to Done.

        Files in Approved folder should be moved to Done after execution.
        This is separate from cleanup_completed_files which handles Needs_Action.

        Returns:
            Number of files moved
        """
        moved_count = 0

        if not self.approved.exists():
            return 0

        for file_path in self.approved.iterdir():
            if not file_path.is_file() or file_path.suffix.lower() != '.md':
                continue

            try:
                content = file_path.read_text(encoding='utf-8')

                # Check if file was executed (status: executed)
                if 'status: executed' in content:
                    self._move_to_done(file_path, 'executed')
                    moved_count += 1
                    self.logger.info(f'Moved executed approval {file_path.name} to Done')

            except Exception as e:
                self.logger.error(f'Error checking approved file {file_path.name}: {e}')

        return moved_count

    def cleanup_rejected_files(self) -> int:
        """
        Handle rejected approvals by updating source files and moving to Done.
        
        Returns:
            Number of files processed
        """
        processed_count = 0
        
        if not self.rejected.exists():
            return 0
        
        for rejected_file in self.rejected.iterdir():
            if not rejected_file.is_file() or rejected_file.suffix.lower() != '.md':
                continue
            
            try:
                content = rejected_file.read_text(encoding='utf-8')
                
                # Extract source file info from frontmatter
                source_match = re.search(r'source_file:\s*(\S+)', content)
                if source_match:
                    source_filename = source_match.group(1).replace('Files/', '')
                    source_action_file = self.needs_action / f'FILE_{source_filename}.md'
                    
                    # Update source file if it exists
                    if source_action_file.exists():
                        self._mark_as_rejected(source_action_file, rejected_file.name)
                        processed_count += 1
                        self.logger.info(f'Marked source file as rejected: {source_action_file.name}')
                
            except Exception as e:
                self.logger.error(f'Error processing rejected file {rejected_file.name}: {e}')
        
        return processed_count

    def _mark_as_rejected(self, file_path: Path, rejection_file: str) -> None:
        """Mark a file as rejected and move to Done."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Update status
            content = re.sub(
                r'status:\s*\w+',
                'status: rejected',
                content
            )
            
            # Add rejection note if not present
            if '## Rejection' not in content:
                content += f'\n\n## Rejection\n\nThis approval was REJECTED. See: {rejection_file}\n'
            
            file_path.write_text(content, encoding='utf-8')
            self._move_to_done(file_path, 'rejected')
            
        except Exception as e:
            self.logger.error(f'Error marking file as rejected: {e}')

    def _move_to_done(self, file_path: Path, status: str) -> None:
        """
        Move a file to the Done folder.
        
        Checks for duplicates before moving to prevent same file being added twice.
        """
        try:
            # Check if file already exists in Done (by name)
            existing_in_done = self.done / file_path.name
            
            if existing_in_done.exists():
                # Check if existing file already has the same status
                existing_content = existing_in_done.read_text(encoding='utf-8')
                if f'status: {status}' in existing_content:
                    # File already exists with same status - skip to prevent duplicate
                    self.logger.info(f'Skipping {file_path.name} - already in Done with status: {status}')
                    return
                else:
                    # File exists but different status - update existing file
                    self.logger.info(f'Updating existing {file_path.name} in Done with status: {status}')
                    # Update status in existing file
                    import re
                    updated_content = re.sub(r'status:\s*\w+', f'status: {status}', existing_content)
                    existing_in_done.write_text(updated_content, encoding='utf-8')
                    # Delete the source file (it's already in Done)
                    if file_path.exists():
                        file_path.unlink()
                    return
            
            # File doesn't exist in Done - proceed with move
            dest_path = self.done / file_path.name

            # Handle duplicate filenames with counter
            counter = 1
            while dest_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                dest_path = self.done / f'{stem}_{counter}{suffix}'
                counter += 1

            shutil.move(str(file_path), str(dest_path))
            self.processed_files.add(self._calculate_file_hash(dest_path))
            self.logger.info(f'Moved {file_path.name} to Done (status: {status})')

        except Exception as e:
            self.logger.error(f'Error moving {file_path.name} to Done: {e}')

    def cleanup_approved_folder(self) -> int:
        """
        Clean up Approved folder by removing duplicates already in Done.

        Returns:
            Number of files removed
        """
        removed_count = 0

        if not self.approved.exists() or not self.done.exists():
            return 0

        done_files = {f.name for f in self.done.glob('*.md')}

        for approved_file in self.approved.iterdir():
            if approved_file.is_file() and approved_file.suffix.lower() == '.md':
                # Check if a similar file exists in Done
                if approved_file.name in done_files:
                    # Check if the Done version has executed status
                    done_file = self.done / approved_file.name
                    done_content = done_file.read_text(encoding='utf-8')
                    if 'status: executed' in done_content or 'status: pending' in done_content:
                        # Remove duplicate from Approved
                        approved_file.unlink()
                        self.processed_files.add(self._calculate_file_hash(approved_file))
                        removed_count += 1
                        self.logger.info(f'Removed duplicate from Approved: {approved_file.name}')
        
        return removed_count

    def cleanup_pending_approval_folder(self) -> int:
        """
        Clean up Pending_Approval folder by removing files where:
        - Source file already moved to Done (clarification/approval resolved)
        - Duplicate exists in Done folder
        
        Returns:
            Number of files removed
        """
        removed_count = 0
        
        if not self.pending_approval.exists() or not self.done.exists():
            return 0
        
        done_files = {f.name for f in self.done.glob('*.md')}
        
        for pending_file in self.pending_approval.iterdir():
            if not pending_file.is_file() or pending_file.suffix.lower() != '.md':
                continue
            
            try:
                content = pending_file.read_text(encoding='utf-8')
                
                # Check if this file already exists in Done (executed)
                if pending_file.name in done_files:
                    pending_file.unlink()
                    self.processed_files.add(self._calculate_file_hash(pending_file))
                    removed_count += 1
                    self.logger.info(f'Removed from Pending_Approval (already in Done): {pending_file.name}')
                    continue
                
                # Check if source file is already in Done (resolved without this approval)
                source_match = re.search(r'source_file:\s*(\S+)', content)
                if source_match:
                    source_filename = source_match.group(1).replace('Files/', '')
                    expected_source = f'FILE_{source_filename}.md'
                    
                    # If source is in Done but this approval isn't, cleanup
                    if expected_source in done_files and pending_file.name not in done_files:
                        # Check if this is a clarification that was resolved differently
                        source_file = self.done / expected_source
                        source_content = source_file.read_text(encoding='utf-8')
                        if 'status: completed' in source_content or 'status: executed' in source_content:
                            # Source completed without this approval, remove pending
                            pending_file.unlink()
                            removed_count += 1
                            self.logger.info(f'Removed from Pending_Approval (source resolved): {pending_file.name}')
                
            except Exception as e:
                self.logger.error(f'Error checking pending file {pending_file.name}: {e}')
        
        return removed_count

    def _log_action(self, action_type: str, details: dict) -> None:
        """Log an action to the logs folder."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'actor': 'orchestrator',
                'details': details
            }

            log_file = self.logs / f'actions_{datetime.now().strftime("%Y%m%d")}.jsonl'

            with open(log_file, 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            self.logger.error(f'Error logging action: {e}')

    def run(self) -> None:
        """
        Main run loop. Continuously monitors and processes pending items.

        Cycle:
        1. Execute approved actions (Qwen updates status, doesn't move files)
        2. Cleanup completed files from Needs_Action → move to Done
        3. Cleanup executed approvals from Approved → move to Done
        4. Handle rejected files → update and move to Done
        5. Clean up duplicates in Approved folder
        6. Clean up Pending_Approval folder (resolved items)
        7. Trigger Qwen processing for pending items
        8. Update dashboard
        """
        self.logger.info(f'Starting Orchestrator (interval: {self.check_interval}s)')

        try:
            while True:
                try:
                    # Step 1: Execute approved actions (Qwen updates status only)
                    if self.process_approved_actions():
                        self.logger.info('Approved actions executed (files updated, not moved)')

                    # Step 2: Cleanup completed files from Needs_Action
                    completed = self.cleanup_completed_files()
                    if completed > 0:
                        self.logger.info(f'Moved {completed} completed file(s) to Done')

                    # Step 3: Cleanup executed approvals from Approved folder
                    executed = self.cleanup_executed_approvals()
                    if executed > 0:
                        self.logger.info(f'Moved {executed} executed approval(s) to Done')

                    # Step 4: Handle rejected files
                    rejected = self.cleanup_rejected_files()
                    if rejected > 0:
                        self.logger.info(f'Processed {rejected} rejected file(s)')

                    # Step 5: Clean up duplicates in Approved folder
                    duplicates = self.cleanup_approved_folder()
                    if duplicates > 0:
                        self.logger.info(f'Removed {duplicates} duplicate(s) from Approved')

                    # Step 6: Clean up Pending_Approval folder (resolved/cancelled items)
                    pending_cleaned = self.cleanup_pending_approval_folder()
                    if pending_cleaned > 0:
                        self.logger.info(f'Removed {pending_cleaned} resolved item(s) from Pending_Approval')

                    # Step 6: Trigger Qwen processing for pending items
                    if self.trigger_qwen_processing():
                        self.logger.info('Processing triggered')

                    # Step 7: Update dashboard
                    self.update_dashboard()

                except Exception as e:
                    self.logger.error(f'Error in orchestration cycle: {e}', exc_info=True)

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise


def main():
    """Main entry point for running the orchestrator."""
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        vault_path = str(Path(__file__).parent.parent)

    interval = 60
    if len(sys.argv) > 2:
        try:
            interval = int(sys.argv[2])
        except ValueError:
            pass

    orchestrator = Orchestrator(vault_path, check_interval=interval)
    orchestrator.run()


if __name__ == '__main__':
    main()
