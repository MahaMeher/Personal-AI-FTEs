"""
Cleanup Script

Manually clean up stuck files in the AI Employee vault.
Run this once to fix the current state.
"""

import shutil
from pathlib import Path

VAULT_PATH = Path(__file__).parent.parent

def cleanup():
    needs_action = VAULT_PATH / 'Needs_Action'
    approved = VAULT_PATH / 'Approved'
    done = VAULT_PATH / 'Done'
    
    moved_count = 0
    removed_count = 0
    
    # Move stuck completed files from Needs_Action to Done
    for file_path in needs_action.glob('*.md'):
        content = file_path.read_text(encoding='utf-8')
        
        if 'status: completed' in content or 'status: executed' in content:
            dest = done / file_path.name
            if not dest.exists():
                shutil.move(str(file_path), str(dest))
                print(f'Moved {file_path.name} to Done')
                moved_count += 1
            else:
                file_path.unlink()
                print(f'Removed duplicate {file_path.name} (already in Done)')
                removed_count += 1
        elif (done / file_path.name).exists():
            # File already exists in Done (duplicate with different status)
            file_path.unlink()
            print(f'Removed duplicate {file_path.name} (already in Done)')
            removed_count += 1
    
    # Remove duplicates from Approved that are already in Done
    done_files = {f.name for f in done.glob('*.md')}
    
    for approved_file in approved.glob('*.md'):
        if approved_file.name in done_files:
            done_file = done / approved_file.name
            done_content = done_file.read_text(encoding='utf-8')
            if 'status: executed' in done_content or 'status: pending' in done_content:
                approved_file.unlink()
                print(f'Removed duplicate from Approved: {approved_file.name}')
                removed_count += 1
    
    print(f'\nCleanup complete:')
    print(f'  - Moved: {moved_count} files')
    print(f'  - Removed: {removed_count} duplicates')

if __name__ == '__main__':
    cleanup()
