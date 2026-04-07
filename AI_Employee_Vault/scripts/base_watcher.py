"""
Base Watcher Module

Abstract base class for all watcher scripts in the AI Employee system.
Watchers monitor external sources and create actionable .md files in the Needs_Action folder.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all AI Employee watchers.
    
    Watchers run continuously, monitoring various inputs and creating
    actionable files for Claude Code to process.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root directory
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        self.logger.info(f'Initialized {self.__class__.__name__}')
    
    def _setup_logging(self) -> None:
        """Setup logging to file and console."""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f'watcher_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new items to process.
        
        Returns:
            List of new items that need action
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create a .md action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to created file, or None if failed
        """
        pass
    
    def run(self) -> None:
        """
        Main run loop. Continuously checks for updates and creates action files.

        This method runs indefinitely until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__} (interval: {self.check_interval}s)')

        try:
            while True:
                try:
                    self.logger.info(f"--- Check cycle at {datetime.now().strftime('%H:%M:%S')} ---")
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f'Found {len(items)} new item(s) to process')

                        for item in items:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f'✓ Created: {filepath.name}')
                    else:
                        self.logger.info(f"No new items. Next check in {self.check_interval}s...")

                except Exception as e:
                    self.logger.error(f'Error in cycle: {e}', exc_info=True)

                self.logger.info(f"--- Cycle complete. Sleeping {self.check_interval}s ---\n")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            raise
    
    def generate_frontmatter(self, item_type: str, **kwargs) -> str:
        """
        Generate YAML frontmatter for action files.
        
        Args:
            item_type: Type of item (email, file_drop, whatsapp, etc.)
            **kwargs: Additional metadata fields
            
        Returns:
            Formatted YAML frontmatter string
        """
        kwargs['type'] = item_type
        kwargs['received'] = datetime.now().isoformat()
        kwargs['status'] = 'pending'
        
        frontmatter = '---\n'
        for key, value in kwargs.items():
            frontmatter += f'{key}: {value}\n'
        frontmatter += '---\n\n'
        
        return frontmatter
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit length
        return name[:100] if len(name) > 100 else name
