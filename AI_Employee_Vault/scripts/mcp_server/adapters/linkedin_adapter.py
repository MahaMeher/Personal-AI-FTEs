"""
LinkedIn Adapter for MCP Server

Uses Playwright browser automation to post on LinkedIn.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base_adapter import BaseAdapter


class LinkedInAdapter(BaseAdapter):
    """
    LinkedIn adapter using Playwright for LinkedIn automation.
    """
    
    def __init__(self, config: dict):
        """
        Initialize LinkedIn adapter.
        
        Args:
            config: LinkedIn configuration
                - session_path: Path to store browser session
                - headless: Run browser in headless mode
        """
        super().__init__(config)
        self.session_path = config.get('session_path', 'config/linkedin/session')
        self.headless = config.get('headless', True)
        self.page = None
        self.browser = None
        
    def connect(self) -> bool:
        """
        Connect to LinkedIn.
        
        Returns:
            True if connected successfully
        """
        try:
            from playwright.sync_api import sync_playwright
            
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=self.headless
            )
            
            if not self.browser.pages:
                self.page = self.browser.new_page()
            else:
                self.page = self.browser.pages[0]
                
            self.page.goto('https://www.linkedin.com/feed/')
            
            # Wait for LinkedIn to load (check for feed)
            try:
                self.page.wait_for_selector('[class*="share-box"]', timeout=30000)
                self.connected = True
                return True
            except Exception:
                print("LinkedIn login required. Please login manually.")
                # Wait for user to login
                try:
                    self.page.wait_for_selector('[class*="share-box"]', timeout=120000)
                    self.connected = True
                    return True
                except Exception as e:
                    print(f"Connection timeout: {e}")
                    self.close()
                    return False
                    
        except Exception as e:
            print(f"LinkedIn connection failed: {e}")
            self.connected = False
            return False
            
    def send_message(self, content: str, hashtags: Optional[List[str]] = None) -> dict:
        """
        Post on LinkedIn.
        
        Args:
            content: Post content
            hashtags: List of hashtags
            
        Returns:
            Result dict with success status
        """
        if not self.connected:
            if not self.connect():
                return {'success': False, 'error': 'Not connected'}
                
        try:
            # Click on "Start a post"
            start_post = self.page.query_selector('[class*="share-box"] [role="button"]')
            if start_post:
                start_post.click()
                self.page.wait_for_timeout(2000)
            else:
                return {'success': False, 'error': 'Could not find post button'}
                
            # Find text input and type content
            text_input = self.page.query_selector('[role="textbox"][contenteditable="true"]')
            if text_input:
                # Add hashtags to content
                full_content = content
                if hashtags:
                    full_content += '\n\n' + ' '.join(hashtags)
                    
                text_input.fill(full_content)
                self.page.wait_for_timeout(1000)
                
                # Click Post button
                post_button = self.page.query_selector('[class*="share-box"] button[type="submit"]')
                if post_button:
                    post_button.click()
                    self.page.wait_for_timeout(2000)
                    
                    return {
                        'success': True,
                        'message_id': f'linkedin_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    }
                else:
                    return {'success': False, 'error': 'Post button not found'}
            else:
                return {'success': False, 'error': 'Text input not found'}
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_status(self) -> dict:
        """Get LinkedIn adapter status."""
        if not self.page:
            return {'status': 'disconnected'}
            
        try:
            # Check if still logged in
            self.page.title()
            return {
                'status': 'connected' if self.connected else 'disconnected',
                'session_path': self.session_path
            }
        except Exception:
            self.connected = False
            return {'status': 'disconnected'}
            
    def close(self):
        """Close LinkedIn connection."""
        if self.browser:
            self.browser.close()
            self.browser = None
        self.page = None
        self.connected = False
        
    def requires_approval(self, **kwargs) -> bool:
        """
        Check if LinkedIn post requires approval.
        
        All posts require approval by default.
        """
        return True  # Always require approval for posts
