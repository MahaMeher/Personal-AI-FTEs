"""
Browser Adapter for MCP Server

Uses Playwright for general web automation (navigate, click, type, screenshot, evaluate).
"""

from typing import Optional, Any
from datetime import datetime

from .base_adapter import BaseAdapter


class BrowserAdapter(BaseAdapter):
    """
    Browser adapter using Playwright for web automation.
    """
    
    def __init__(self, config: dict):
        """
        Initialize browser adapter.
        
        Args:
            config: Browser configuration
                - headless: Run browser in headless mode
                - user_agent: Custom user agent
                - timeout: Default timeout in ms
        """
        super().__init__(config)
        self.headless = config.get('headless', True)
        self.user_agent = config.get('user_agent')
        self.timeout = config.get('timeout', 30000)
        self.page = None
        self.browser = None
        self.playwright = None
        
    def connect(self) -> bool:
        """
        Launch browser.
        
        Returns:
            True if connected successfully
        """
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            
            if self.user_agent:
                self.page.set_extra_http_headers({'User-Agent': self.user_agent})
            
            self.page.set_default_timeout(self.timeout)
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Browser connection failed: {e}")
            self.connected = False
            return False
            
    def navigate(self, url: str) -> dict:
        """
        Navigate to URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Result dict with success status and page title
        """
        if not self.connected:
            if not self.connect():
                return {'success': False, 'error': 'Not connected'}
                
        try:
            response = self.page.goto(url)
            self.page.wait_for_load_state('networkidle')
            
            return {
                'success': True,
                'title': self.page.title(),
                'url': url,
                'status': response.status if response else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def click(self, selector: str) -> dict:
        """
        Click element matching selector.
        
        Args:
            selector: CSS selector for element
            
        Returns:
            Result dict with success status
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            self.page.click(selector)
            return {
                'success': True,
                'message': f'Clicked: {selector}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def type_text(self, selector: str, text: str) -> dict:
        """
        Type text into element.
        
        Args:
            selector: CSS selector for input element
            text: Text to type
            
        Returns:
            Result dict with success status
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            self.page.fill(selector, text)
            return {
                'success': True,
                'message': f'Typed into: {selector}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def screenshot(self, full_page: bool = True) -> dict:
        """
        Take screenshot of current page.
        
        Args:
            full_page: Capture full page or viewport only
            
        Returns:
            Result dict with screenshot path
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'Logs/screenshot_{timestamp}.png'
            
            self.page.screenshot(
                path=screenshot_path,
                full_page=full_page
            )
            
            return {
                'success': True,
                'path': screenshot_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def evaluate(self, script: str) -> dict:
        """
        Execute JavaScript on page.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Result dict with script result
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            result = self.page.evaluate(script)
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def snapshot(self) -> dict:
        """
        Get accessibility snapshot of current page (for finding element refs).
        
        Returns:
            Result dict with page snapshot
        """
        if not self.connected:
            return {'success': False, 'error': 'Not connected'}
            
        try:
            snapshot = self.page.accessibility.snapshot()
            return {
                'success': True,
                'snapshot': snapshot,
                'url': self.page.url,
                'title': self.page.title()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def send_message(self, **kwargs) -> dict:
        """
        Send message via browser (alias for browser actions).
        
        This is a wrapper for compatibility with the MCP interface.
        """
        action = kwargs.get('action', 'navigate')
        
        if action == 'navigate':
            return self.navigate(kwargs.get('url'))
        elif action == 'click':
            return self.click(kwargs.get('selector'))
        elif action == 'type':
            return self.type_text(kwargs.get('selector'), kwargs.get('text'))
        elif action == 'screenshot':
            return self.screenshot()
        elif action == 'evaluate':
            return self.evaluate(kwargs.get('script'))
        elif action == 'snapshot':
            return self.snapshot()
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}'
            }
            
    def get_status(self) -> dict:
        """Get browser adapter status."""
        if not self.page:
            return {'status': 'disconnected'}
            
        try:
            return {
                'status': 'connected' if self.connected else 'disconnected',
                'url': self.page.url,
                'title': self.page.title()
            }
        except Exception:
            self.connected = False
            return {'status': 'disconnected'}
            
    def close(self):
        """Close browser."""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        self.page = None
        self.connected = False
        
    def requires_approval(self, **kwargs) -> bool:
        """
        Check if browser action requires approval.
        
        Approval required for:
        - Payment portals
        - Banking sites
        - Sensitive operations
        """
        url = kwargs.get('url', '')
        action = kwargs.get('action', '')
        
        # Sensitive sites
        sensitive_keywords = ['payment', 'bank', 'checkout', 'invoice', 'transfer']
        if any(keyword in url.lower() for keyword in sensitive_keywords):
            return True
            
        # Sensitive actions
        if action in ['evaluate', 'type']:
            return True
            
        return False
