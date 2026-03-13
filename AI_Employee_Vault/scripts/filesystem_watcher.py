"""
File System Watcher Module

Monitors a drop folder for new files and creates action files for Claude Code to process.
This is the simplest watcher to set up and test for the Bronze tier.
"""

import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from base_watcher import BaseWatcher


class FileDropItem:
    """Represents a file dropped for processing."""
    
    def __init__(self, source_path: Path, file_hash: str):
        self.source_path = source_path
        self.file_hash = file_hash
        self.name = source_path.name
        self.size = source_path.stat().st_size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_path': str(self.source_path),
            'file_hash': self.file_hash,
            'name': self.name,
            'size': self.size
        }


class FilesystemWatcher(BaseWatcher):
    """
    Watches a drop folder for new files.
    
    When a file is detected, it creates an action file in Needs_Action
    and copies the file to the vault for processing.
    """
    
    def __init__(self, vault_path: str, drop_folder: Optional[str] = None, check_interval: int = 30):
        """
        Initialize the filesystem watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            drop_folder: Path to the folder to watch (default: vault/Inbox)
            check_interval: Seconds between checks (default: 30)
        """
        super().__init__(vault_path, check_interval)
        
        # Set up drop folder
        if drop_folder:
            self.drop_folder = Path(drop_folder)
        else:
            self.drop_folder = self.vault_path / 'Inbox'
        
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        
        # Track processed file hashes to avoid duplicates
        self.processed_hashes: set = set()
        
        self.logger.info(f'Watching folder: {self.drop_folder}')
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file for duplicate detection."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def check_for_updates(self) -> List[FileDropItem]:
        """
        Check the drop folder for new files.
        
        Returns:
            List of new FileDropItem objects
        """
        new_items = []
        
        if not self.drop_folder.exists():
            return new_items
        
        # Get all files in drop folder (not subdirectories)
        for file_path in self.drop_folder.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                file_hash = self._calculate_hash(file_path)
                
                # Skip if already processed
                if file_hash in self.processed_hashes:
                    continue
                
                # Skip .md files (they're already action files)
                if file_path.suffix.lower() == '.md':
                    continue
                
                item = FileDropItem(file_path, file_hash)
                new_items.append(item)
                self.processed_hashes.add(file_hash)
        
        return new_items
    
    def create_action_file(self, item: FileDropItem) -> Optional[Path]:
        """
        Create an action file for a dropped file.
        
        Also copies the file to the vault for safekeeping.
        
        Args:
            item: The FileDropItem to create an action file for
            
        Returns:
            Path to created action file
        """
        try:
            # Copy file to vault
            files_dir = self.vault_path / 'Files'
            files_dir.mkdir(parents=True, exist_ok=True)
            dest_path = files_dir / item.name
            
            # Handle duplicate filenames
            counter = 1
            while dest_path.exists():
                stem = Path(item.name).stem
                suffix = Path(item.name).suffix
                dest_path = files_dir / f'{stem}_{counter}{suffix}'
                counter += 1
            
            shutil.copy2(item.source_path, dest_path)
            
            # Create action file
            frontmatter = self.generate_frontmatter(
                item_type='file_drop',
                original_name=f'"{item.name}"',
                size=item.size,
                file_hash=f'"{item.file_hash}"',
                copied_to=f'"{dest_path.name}"'
            )
            
            content = f'''{frontmatter}
# File Dropped for Processing

**Original File:** `{item.name}`
**Size:** {self._format_size(item.size)}
**Copied To:** `Files/{dest_path.name}`

## Content Summary

*Awaiting AI analysis*

## Suggested Actions

- [ ] Analyze file content
- [ ] Categorize and tag
- [ ] Take appropriate action
- [ ] Move to Done when complete

## Notes

*Add notes here during processing*
'''
            
            # Create action file
            safe_name = self.sanitize_filename(item.name)
            action_file = self.needs_action / f'FILE_{safe_name}.md'
            action_file.write_text(content)
            
            # Remove original from drop folder
            item.source_path.unlink()
            
            self.logger.info(f'Processed file: {item.name} -> {action_file.name}')
            return action_file
            
        except Exception as e:
            self.logger.error(f'Failed to create action file for {item.name}: {e}')
            return None
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'


def main():
    """Main entry point for running the filesystem watcher."""
    import sys
    
    # Get vault path from command line or use default
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    else:
        # Default to AI_Employee_Vault in current directory
        vault_path = str(Path(__file__).parent.parent)
    
    watcher = FilesystemWatcher(vault_path, check_interval=30)
    watcher.run()


if __name__ == '__main__':
    main()
