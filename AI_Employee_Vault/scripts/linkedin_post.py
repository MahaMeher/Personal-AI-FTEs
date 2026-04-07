"""
LinkedIn Post Executor

Posts approved LinkedIn content to LinkedIn.
Uses Playwright browser automation to publish posts.

Silver Tier Requirement: "Automatically Post on LinkedIn about business to generate sales"

Usage:
    python scripts/linkedin_post.py --file Approved/LINKEDIN_POST_*.md
    python scripts/linkedin_post.py --auto  # Process all approved posts
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class LinkedInPostExecutor:
    """Execute approved LinkedIn posts."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / 'Approved'
        self.done_dir = self.vault_path / 'Done'
        self.config_dir = self.vault_path / 'config' / 'linkedin'
        self.logs_dir = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        for d in [self.config_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.session_path = self.config_dir / 'session'
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Setup logging
        import logging
        self.logger = logging.getLogger('LinkedInPostExecutor')
    
    def _init_browser(self) -> bool:
        """Initialize Playwright browser with saved session."""
        try:
            from playwright.sync_api import sync_playwright
            
            # Ensure session directory exists
            self.session_path.mkdir(parents=True, exist_ok=True)
            
            self.playwright = sync_playwright().start()
            
            # Use same settings as linkedin_watcher.py for consistency
            self.browser = self.playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=False,  # Use visible browser for reliability
                timeout=60000
            )
            
            if not self.browser.pages:
                self.page = self.browser.new_page()
            else:
                self.page = self.browser.pages[0]
            
            self.logger.info("Browser initialized with session")
            return True
            
        except Exception as e:
            print(f"Browser initialization failed: {e}")
            return False
    
    def _login_linkedin(self) -> bool:
        """Check if logged in to LinkedIn."""
        try:
            print("  Checking LinkedIn login status...")
            self.page.goto('https://www.linkedin.com/feed/')
            self.page.wait_for_timeout(8000)  # Wait longer for session to load
            
            # Check if logged in with multiple selectors
            logged_in_selectors = [
                '[class*="share-box"]',  # Post creation box
                '[class*="feed"]',  # Feed container
                'nav[role="navigation"]',  # Navigation bar
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = self.page.query_selector(selector)
                    if element:
                        print("  ✓ Logged in to LinkedIn")
                        return True
                except Exception:
                    continue
            
            # Check URL - if not on login page, probably logged in
            current_url = self.page.url
            if 'login' not in current_url and 'checkpoint' not in current_url:
                print("  ✓ Logged in (URL check)")
                return True
            
            print("  ❌ Not logged in - session may have expired")
            print("  Solution: Run 'python scripts/linkedin_watcher.py' to re-login")
            return False
                
        except Exception as e:
            print(f"  Login check failed: {e}")
            return False
    
    def _post_to_linkedin(self, content: str) -> bool:
        """
        Post content to LinkedIn.
        """
        try:
            # Navigate to LinkedIn feed
            print("  Navigating to LinkedIn feed...")
            self.page.goto('https://www.linkedin.com/feed/')
            self.page.wait_for_timeout(5000)
            
            # Debug: Show page title and URL
            page_title = self.page.title()
            page_url = self.page.url
            print(f"  Page: {page_title}")
            print(f"  URL: {page_url}")
            
            # Click "Start a post" button - try many selectors
            print("  Looking for 'Start a post' button...")
            
            start_post_selectors = [
                '[class*="share-box"] [role="button"]',
                '[class*="share-box"] button',
                'button:has-text("Start a post")',
                'div[role="button"]:has-text("Start")',
                '.share-box button',
                '[aria-label*="post"]',
            ]
            
            start_post_btn = None
            for selector in start_post_selectors:
                try:
                    start_post_btn = self.page.query_selector(selector)
                    if start_post_btn:
                        print(f"  ✓ Found with: {selector}")
                        break
                except Exception:
                    continue
            
            # If still not found, list what we did find
            if not start_post_btn:
                print("  ❌ Could not find 'Start a post' button")
                print("  Looking for any buttons on page...")
                
                all_buttons = self.page.query_selector_all('button, div[role="button"]')
                print(f"  Found {len(all_buttons)} clickable elements")
                
                for i, btn in enumerate(all_buttons[:10]):  # Show first 10
                    try:
                        btn_text = btn.inner_text().strip()[:50]
                        print(f"    [{i}] '{btn_text}'")
                    except Exception:
                        pass
                
                return False
            
            # Click the button
            print("  Clicking 'Start a post'...")
            start_post_btn.click()
            print("  ✓ Clicked 'Start a post'")
            
            # Wait for modal to open
            print("  Waiting for modal to open...")
            self.page.wait_for_timeout(4000)
            
            # Find text input and type
            print("  Finding text input...")
            text_input = self.page.query_selector('[role="textbox"][contenteditable="true"]')
            
            if not text_input:
                print("  ❌ Could not find text input")
                return False
            
            print(f"  Typing content ({len(content)} chars)...")
            text_input.fill(content)
            self.page.wait_for_timeout(2000)
            print("  ✓ Content typed")
            
            # Find and click Post button
            print("  Finding Post button...")
            
            # Wait a bit for Post button to become enabled
            self.page.wait_for_timeout(2000)
            
            # Find all buttons and look for "Post"
            all_buttons = self.page.query_selector_all('button')
            post_btn = None
            
            for btn in all_buttons:
                try:
                    btn_text = btn.inner_text().strip().lower()
                    is_disabled = btn.get_attribute('disabled')
                    
                    if btn_text == 'post' and not is_disabled:
                        post_btn = btn
                        print(f"  ✓ Found Post button")
                        break
                except Exception:
                    continue
            
            if not post_btn:
                print("  ❌ Could not find enabled Post button")
                return False
            
            print("  Clicking Post button...")
            post_btn.scroll_into_view_if_needed()
            self.page.wait_for_timeout(1000)
            post_btn.click()
            
            # Wait for post to publish
            print("  Waiting for post to publish...")
            self.page.wait_for_timeout(5000)
            
            print("  ✓ Post completed!")
            return True
                
        except Exception as e:
            print(f"  Posting failed: {e}")
            return False
    
    def _extract_post_content(self, file_path: Path) -> Optional[str]:
        """Extract post content from approved file."""
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract content between ``` markers
            code_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            
            # Fallback: look for "## Post Content" section
            section_match = re.search(r'## Post Content\s*\n\n(.*?)(?:\n##|$)', content, re.DOTALL)
            if section_match:
                return section_match.group(1).strip()
            
            return None
            
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def _update_dashboard(self, success: bool, post_file: str):
        """Update dashboard with posting result."""
        if not self.dashboard.exists():
            return
        
        try:
            content = self.dashboard.read_text(encoding='utf-8')
            
            # Add to recent activity
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            status = "✅" if success else "❌"
            action = "posted" if success else "failed"
            
            activity_line = f"- **{timestamp}** - {status} LinkedIn post {action}: {post_file}\n"
            
            # Insert after "## Recent Activity"
            if '## Recent Activity' in content:
                content = content.replace(
                    '## Recent Activity\n',
                    f'## Recent Activity\n{activity_line}'
                )
            
            self.dashboard.write_text(content, encoding='utf-8')
            
        except Exception as e:
            print(f"Error updating dashboard: {e}")
    
    def _log_post(self, file_path: Path, success: bool, error: str = None):
        """Log post result."""
        log_file = self.logs_dir / 'linkedin_posts.jsonl'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': file_path.name,
            'success': success,
            'error': error
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
    
    def post_file(self, file_path: Path) -> bool:
        """
        Post a single approved file to LinkedIn.
        
        Args:
            file_path: Path to approved post file
            
        Returns:
            True if posted successfully
        """
        print(f"\nPosting: {file_path.name}")
        
        # Extract content
        content = self._extract_post_content(file_path)
        if not content:
            print("  ❌ Could not extract post content")
            return False
        
        print(f"  Content length: {len(content)} characters")
        
        # Initialize browser if needed
        if not self.page:
            print("  Initializing browser...")
            if not self._init_browser():
                return False
        
        # Check login
        if not self._login_linkedin():
            print("  ❌ Not logged in to LinkedIn")
            return False
        
        # Post to LinkedIn
        print("  Posting to LinkedIn...")
        success = self._post_to_linkedin(content)
        
        if success:
            print(f"  ✅ Posted successfully!")
            
            # Update file status
            try:
                file_content = file_path.read_text(encoding='utf-8')
                file_content = file_content.replace(
                    'status: pending_approval',
                    'status: posted'
                )
                file_content += f'\n\n## Posted\n\n*Posted on {datetime.now().strftime("%Y-%m-%d %H:%M")}*\n'
                file_path.write_text(file_content, encoding='utf-8')
            except Exception as e:
                print(f"  Warning: Could not update file status: {e}")
            
            self._log_post(file_path, True)
            self._update_dashboard(True, file_path.name)
        else:
            print(f"  ❌ Posting failed")
            self._log_post(file_path, False, "Posting failed")
            self._update_dashboard(False, file_path.name)
        
        return success
    
    def process_approved_posts(self) -> List[Path]:
        """Process all approved LinkedIn posts."""
        if not self.approved_dir.exists():
            return []
        
        posted = []
        
        for file in self.approved_dir.glob('LINKEDIN_POST_*.md'):
            if self.post_file(file):
                # Move to Done
                done_path = self.done_dir / file.name
                try:
                    file.rename(done_path)
                    posted.append(done_path)
                    print(f"  Moved to Done/")
                except Exception as e:
                    print(f"  Warning: Could not move to Done: {e}")
        
        return posted
    
    def close(self):
        """Close browser."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Executor')
    parser.add_argument('--file', type=str, help='Specific post file to post')
    parser.add_argument('--auto', action='store_true', help='Process all approved posts')
    parser.add_argument('--vault', type=str, help='Path to vault')
    
    args = parser.parse_args()
    
    # Get vault path
    vault_path = args.vault if args.vault else str(Path(__file__).parent.parent)
    
    executor = LinkedInPostExecutor(vault_path)
    
    print("=" * 60)
    print("AI Employee - LinkedIn Post Executor")
    print("=" * 60)
    
    try:
        if args.file:
            # Post specific file
            file_path = Path(args.file)
            if not file_path.exists():
                # Try in Approved folder
                file_path = Path(vault_path) / 'Approved' / args.file
            
            if file_path.exists():
                executor.post_file(file_path)
            else:
                print(f"File not found: {args.file}")
        
        elif args.auto:
            # Process all approved posts
            print("\nProcessing approved LinkedIn posts...")
            posted = executor.process_approved_posts()
            print(f"\n✓ Posted {len(posted)} post(s) to LinkedIn")
        
        else:
            print("\nUsage:")
            print("  python scripts/linkedin_post.py --file Approved/LINKEDIN_POST_*.md")
            print("  python scripts/linkedin_post.py --auto")
    
    finally:
        executor.close()
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
