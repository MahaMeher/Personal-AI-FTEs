"""
LinkedIn Watcher for AI Employee

Monitors LinkedIn for notifications, messages, and engagement.
Creates action files in Needs_Action folder for important items.

Silver Tier Implementation

Usage:
    python scripts/linkedin_watcher.py [--interval 300]
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """
    LinkedIn Watcher - Monitors LinkedIn for important notifications and messages.
    
    Uses Playwright browser automation to check LinkedIn.
    Creates action files in Needs_Action folder for AI processing.
    """
    
    def __init__(self, vault_path: str, check_interval: int = 300):
        """
        Initialize LinkedIn Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            check_interval: Seconds between checks (default: 300 = 5 min)
        """
        super().__init__(vault_path, check_interval)
        
        # LinkedIn configuration
        self.config_dir = self.vault_path / 'config' / 'linkedin'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = self.config_dir / 'session'
        
        # Keywords that indicate important LinkedIn activity
        self.urgent_keywords = ['message', 'connection request', 'job opportunity', 'urgent', 'hiring']

        # Track processed notifications - LOAD FROM FILE
        self.processed_ids_file = self.config_dir / 'processed_ids.json'
        self.processed_ids = self._load_processed_ids()

        # Playwright browser
        self.browser = None
        self.page = None
        self.playwright = None

    def _load_processed_ids(self) -> set:
        """Load processed IDs from file."""
        try:
            import json
            if self.processed_ids_file.exists():
                data = json.loads(self.processed_ids_file.read_text())
                processed = set(data.get('linkedin', []))
                self.logger.info(f"Loaded {len(processed)} processed IDs")
                return processed
        except Exception as e:
            self.logger.debug(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed IDs to file."""
        try:
            import json
            data = {'linkedin': list(self.processed_ids)}
            self.processed_ids_file.write_text(json.dumps(data))
            self.logger.debug(f"Saved {len(self.processed_ids)} processed IDs")
        except Exception as e:
            self.logger.debug(f"Could not save processed IDs: {e}")
        
    def _init_browser(self):
        """Initialize Playwright browser for LinkedIn."""
        try:
            from playwright.sync_api import sync_playwright
            
            # Clean up any existing browser processes first
            if self.browser:
                try:
                    self.browser.close()
                except Exception:
                    pass
            if self.playwright:
                try:
                    self.playwright.stop()
                except Exception:
                    pass
            
            self.playwright = sync_playwright().start()
            
            # Clear session if corrupted
            if not self.session_path.exists():
                self.session_path.mkdir(parents=True, exist_ok=True)
            
            self.browser = self.playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=False  # Visible browser
            )
            
            if not self.browser.pages:
                self.page = self.browser.new_page()
            else:
                self.page = self.browser.pages[0]
            
            self.logger.info("Browser initialized for LinkedIn")
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            # If session is corrupted, clear it
            if 'has been closed' in error_msg or 'Target page' in error_msg:
                self.logger.warning("Browser session corrupted, clearing session...")
                try:
                    # Close any existing browser
                    if self.browser:
                        self.browser.close()
                    if self.playwright:
                        self.playwright.stop()
                    
                    # Clear session directory
                    import shutil
                    if self.session_path.exists():
                        shutil.rmtree(self.session_path)
                    self.session_path.mkdir(parents=True, exist_ok=True)
                    
                    # Try again with fresh session
                    self.logger.info("Retrying with fresh session...")
                    return self._init_browser()
                    
                except Exception as retry_error:
                    self.logger.error(f"Retry failed: {retry_error}")
                    return False
            
            self.logger.error(f"Browser initialization failed: {e}")
            return False
    
    def _login_linkedin(self) -> bool:
        """
        Login to LinkedIn if not already logged in.

        Returns:
            True if logged in successfully
        """
        try:
            self.page.goto('https://www.linkedin.com/feed/')
            self.page.wait_for_timeout(5000)

            # Check if already logged in using multiple possible selectors
            if self._is_logged_in():
                self.logger.info("Already logged in to LinkedIn")
                return True

            # Need to login
            self.logger.info("Login required. Please login manually in the browser.")
            self.logger.info("After login, the watcher will automatically continue...")

            # Wait for user to login (max 5 minutes)
            self.logger.info("Waiting for login... (up to 5 minutes)")
            
            for attempt in range(30):  # Check every 10 seconds for 5 minutes
                self.page.wait_for_timeout(10000)
                if self._is_logged_in():
                    self.logger.info("✓ Login detected! Starting monitoring...")
                    return True

            self.logger.error("Login timeout after 5 minutes")
            return False

        except Exception as e:
            self.logger.error(f"LinkedIn login failed: {e}")
            return False

    def _is_logged_in(self) -> bool:
        """
        Check if user is logged in to LinkedIn.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Try multiple selectors that indicate logged-in state
            logged_in_selectors = [
                '[class*="share-box"]',  # Post creation box
                '[class*="feed"]',  # Feed container
                '[data-control-name="topbar"]',  # Top navigation
                'nav[role="navigation"]',  # Navigation bar
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        return True
                except Exception:
                    continue
            
            # Also check URL - if we're not on login page, we're probably logged in
            current_url = self.page.url
            if 'login' not in current_url and 'checkpoint' not in current_url:
                return True
                
            return False
            
        except Exception:
            return False
    
    def _check_notifications(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn notifications.
        """
        notifications = []

        try:
            self.logger.info("Navigating to notifications page...")
            self.page.goto('https://www.linkedin.com/notifications/')
            self.page.wait_for_timeout(8000)

            # Find notification elements (we know there are 6 from debug)
            notification_elements = self.page.query_selector_all('[class*="notification"]')
            
            self.logger.info(f"Found {len(notification_elements)} notification elements")

            # Process each notification element
            for elem in notification_elements[:20]:
                try:
                    # Get all text from this element
                    text = elem.inner_text().strip()
                    
                    if not text or len(text) < 5:
                        continue
                    
                    self.logger.info(f"Notification: {text[:100]}...")
                    
                    # Check if message-related
                    if 'message' in text.lower():
                        notif_id = hash(text) % 1000000
                        if notif_id not in self.processed_ids:
                            notifications.append({
                                'id': str(notif_id),
                                'text': text[:200],
                                'urgent': True,
                                'type': 'notification'  # Fixed: was 'new_message_notification'
                            })
                            self.processed_ids.add(notif_id)
                            self.logger.info(f"✓ NEW MESSAGE: {text[:80]}...")
                    
                except Exception as e:
                    self.logger.debug(f"Error reading notification: {e}")
                    continue

            self.logger.info(f"Total notifications captured: {len(notifications)}")

        except Exception as e:
            self.logger.error(f"Error checking notifications: {e}")

        return notifications
    
    def _check_messages(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn messages.
        ONLY checks UNREAD messages (bold names, unread indicators).
        """
        messages = []

        try:
            self.logger.info("Navigating to messaging page...")
            self.page.goto('https://www.linkedin.com/messaging/')
            self.page.wait_for_timeout(8000)

            # Find message elements
            message_elems = self.page.query_selector_all('[class*="message"]')
            
            self.logger.info(f"Found {len(message_elems)} message elements")
            
            # Process each message element - ONLY UNREAD
            for msg_elem in message_elems[:10]:
                try:
                    # Check if this conversation is UNREAD
                    # LinkedIn shows unread as: bold text, blue dot, or "new" class
                    is_unread = False
                    
                    # Check for bold name (unread indicator)
                    try:
                        strong_elem = msg_elem.query_selector('strong')
                        if strong_elem:
                            is_unread = True
                            self.logger.debug("Found bold text (unread)")
                    except Exception:
                        pass
                    
                    # Check for unread/new class
                    if not is_unread:
                        try:
                            elem_class = msg_elem.get_attribute('class')
                            if elem_class and ('unread' in elem_class.lower() or 'new' in elem_class.lower()):
                                is_unread = True
                                self.logger.debug("Found unread/new class")
                        except Exception:
                            pass
                    
                    # Check for unread dot/indicator
                    if not is_unread:
                        try:
                            dot = msg_elem.query_selector('[class*="dot"], [class*="unread-indicator"]')
                            if dot:
                                is_unread = True
                                self.logger.debug("Found unread dot")
                        except Exception:
                            pass
                    
                    # ONLY process if UNREAD
                    if is_unread:
                        # Get text content
                        text = msg_elem.inner_text().strip()
                        
                        # Skip empty or system messages
                        if not text or len(text) < 5:
                            continue
                        
                        # Skip LinkedIn system messages
                        if 'LinkedIn' in text or 'Jobs' in text or 'Connections' in text:
                            continue
                        
                        # Extract name and preview
                        lines = text.split('\n')
                        name = lines[0].strip()[:100] if lines else "Unknown"
                        preview = ' '.join(lines[1:]).strip()[:200] if len(lines) > 1 else text[:200]
                        
                        # Skip if name is too short
                        if len(name) < 2:
                            continue
                        
                        msg_id = hash(name + preview) % 1000000
                        
                        if msg_id not in self.processed_ids:
                            messages.append({
                                'id': str(msg_id),
                                'from': name,
                                'preview': preview,
                                'type': 'unread_message',  # Mark as unread
                                'urgent': True
                            })
                            self.processed_ids.add(msg_id)
                            self.logger.info(f"✓ UNREAD message from {name}: {preview[:50]}...")
                        else:
                            self.logger.debug(f"Already processed: {name}")
                    else:
                        self.logger.debug(f"Skipping read message")
                        
                except Exception as e:
                    self.logger.debug(f"Error: {e}")
                    continue

            self.logger.info(f"Total UNREAD messages: {len(messages)}")

        except Exception as e:
            self.logger.error(f"Error: {e}")

        return messages
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn for new message notifications.
        Simple approach: Check notifications page for "new message" alerts.
        """
        # Initialize browser
        self.logger.info("Initializing browser...")
        
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
        
        if not self._init_browser():
            self.logger.error("Failed to initialize browser")
            return []
        
        if not self._login_linkedin():
            self.logger.error("Failed to login")
            return []

        self.logger.info("Checking for new message notifications...")
        all_items = []

        # Go to notifications page
        self.logger.info("Navigating to notifications page...")
        self.page.goto('https://www.linkedin.com/notifications/')
        self.page.wait_for_timeout(8000)

        # Find notification elements
        notification_elements = self.page.query_selector_all('[class*="notification"]')
        self.logger.info(f"Found {len(notification_elements)} notification elements")

        # Process each notification
        for elem in notification_elements[:20]:
            try:
                text = elem.inner_text().strip()
                
                if not text or len(text) < 10:
                    continue
                
                # Check if it's a MESSAGE notification
                if 'message' in text.lower():
                    notif_id = hash(text) % 1000000
                    
                    if notif_id not in self.processed_ids:
                        all_items.append({
                            'id': str(notif_id),
                            'text': text[:200],
                            'type': 'message_notification',
                            'urgent': True
                        })
                        self.processed_ids.add(notif_id)
                        self.logger.info(f"✓ NEW MESSAGE notification: {text[:80]}...")
                        
            except Exception as e:
                self.logger.debug(f"Error: {e}")
                continue

        self.logger.info(f"Total new message notifications: {len(all_items)}")

        # Close browser
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass

        # Save processed IDs
        self._save_processed_ids()

        return all_items
    
    def _check_messages(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn messages - grabs FIRST conversation (newest message).
        """
        messages = []

        try:
            self.logger.info("Navigating to messaging page to grab new message...")
            self.page.goto('https://www.linkedin.com/messaging/')
            self.page.wait_for_timeout(5000)

            # IMMEDIATELY grab the first conversation (newest message)
            conversations = self.page.query_selector_all('[role="listitem"]')
            
            self.logger.info(f"Found {len(conversations)} conversations")
            
            if conversations:
                # Get the FIRST conversation (most recent)
                first_conv = conversations[0]
                text = first_conv.inner_text()
                lines = text.split('\n')
                
                if len(lines) >= 2:
                    name = lines[0].strip()[:100]
                    preview = ' '.join(lines[1:]).strip()[:200]
                    
                    if name and len(name) > 2:
                        msg_id = hash(name + preview) % 1000000
                        messages.append({
                            'id': str(msg_id),
                            'from': name,
                            'preview': preview,
                            'type': 'message',
                            'urgent': True
                        })
                        self.logger.info(f"✓ Grabbed message from {name}: {preview[:50]}...")
            
            self.logger.info(f"Total messages grabbed: {len(messages)}")

        except Exception as e:
            self.logger.error(f"Error grabbing messages: {e}")

        return messages
    
    def create_action_file(self, item: Dict) -> Optional[Path]:
        """
        Create action file for LinkedIn item.
        
        Args:
            item: LinkedIn notification or message dict
            
        Returns:
            Path to created action file
        """
        try:
            item_type = item.get('type', 'unknown')
            priority = 'high' if item.get('urgent', False) else 'normal'
            
            if item_type == 'message' or item_type == 'message_notification':
                content = f'''---
type: linkedin_message_notification
text: "{item.get('text', '')}"
received: {datetime.now().isoformat()}
priority: high
status: pending
linkedin_id: {item.get('id', '')}
---

# LinkedIn New Message Notification

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Priority:** HIGH

## Notification

{item.get('text', 'You have a new message')}

## Action Required

**You have a new LinkedIn message!**

- [ ] Open LinkedIn to read the message
- [ ] Reply to the sender
- [ ] Mark as processed

## Notes

Open LinkedIn messaging to see who sent the message and reply.

---
*Auto-generated by LinkedIn Watcher*
'''
                filename = f'LINKEDIN_NEW_MESSAGE_{item.get("id", "unknown")}.md'
                
            elif item_type == 'notification':
                content = f'''---
type: linkedin_notification
text: "{item.get('text', '')}"
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
linkedin_id: {item.get('id', '')}
---

# LinkedIn Notification

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Priority:** {priority.upper()}

## Notification

{item.get('text', 'No details available')}

## Actions Required

- [ ] Review notification
- [ ] Take appropriate action
- [ ] Mark as processed

## Notes

*Add notes during processing*

---
*Auto-generated by LinkedIn Watcher*
'''
                filename = f'LINKEDIN_NOTIF_{item.get("id", "unknown")}.md'
            else:
                self.logger.error(f"Unknown item type: {item_type}")
                return None

            # Create action file
            try:
                action_file = self.needs_action / filename
                self.logger.info(f"Writing file: {filename}")
                action_file.write_text(content, encoding='utf-8')
                self.logger.info(f"✓ Successfully created: {filename}")
                return action_file
            except Exception as e:
                self.logger.error(f"FAILED to write file {filename}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return None

        except Exception as e:
            self.logger.error(f"Failed to create action file: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:50]
    
    def close(self):
        """Close browser safely."""
        try:
            if self.page:
                self.page.close()
                self.page = None
        except Exception as e:
            self.logger.debug(f"Error closing page: {e}")
        
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            self.logger.debug(f"Error closing browser: {e}")
        
        try:
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            self.logger.debug(f"Error stopping playwright: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Watcher for AI Employee')
    parser.add_argument('--interval', type=int, default=300,
                       help='Check interval in seconds (default: 300)')
    parser.add_argument('--vault', type=str, default=None,
                       help='Path to vault (default: parent directory)')
    
    args = parser.parse_args()
    
    # Get vault path
    if args.vault:
        vault_path = args.vault
    else:
        vault_path = str(Path(__file__).parent.parent)
    
    print("=" * 60)
    print("LinkedIn Watcher - AI Employee (Silver Tier)")
    print("=" * 60)
    print(f"Vault: {vault_path}")
    print(f"Check Interval: {args.interval}s")
    print("=" * 60)
    print("\nMonitoring LinkedIn for notifications and messages...")
    print("First run will require manual login")
    print("Press Ctrl+C to stop\n")
    
    watcher = LinkedInWatcher(vault_path, check_interval=args.interval)
    
    try:
        watcher.run()
    finally:
        watcher.close()


if __name__ == '__main__':
    main()
