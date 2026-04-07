"""
WhatsApp Adapter for MCP Server

Uses Playwright browser automation to send WhatsApp messages via WhatsApp Web.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .base_adapter import BaseAdapter


class WhatsAppAdapter(BaseAdapter):
    """
    WhatsApp adapter using Playwright for WhatsApp Web automation.
    """
    
    def __init__(self, config: dict):
        """
        Initialize WhatsApp adapter.
        
        Args:
            config: WhatsApp configuration
                - session_path: Path to store browser session
                - headless: Run browser in headless mode
        """
        super().__init__(config)
        self.session_path = config.get('session_path', 'config/whatsapp/session')
        self.headless = config.get('headless', True)
        self.page = None
        self.browser = None
        
    def connect(self) -> bool:
        """
        Connect to WhatsApp Web.
        
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
                
            self.page.goto('https://web.whatsapp.com')
            
            # Wait for WhatsApp to load (check for chat list)
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                self.connected = True
                return True
            except Exception:
                print("QR code scan required. Please scan with WhatsApp mobile app.")
                # Wait for user to scan QR
                try:
                    self.page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                    self.connected = True
                    return True
                except Exception as e:
                    print(f"Connection timeout: {e}")
                    self.close()
                    return False
                    
        except Exception as e:
            print(f"WhatsApp connection failed: {e}")
            self.connected = False
            return False
            
    def send_message(self, to: str, message: str) -> dict:
        """
        Send WhatsApp message.
        
        Args:
            to: Phone number or contact name
            message: Message text
            
        Returns:
            Result dict with success status
        """
        if not self.connected:
            if not self.connect():
                return {'success': False, 'error': 'Not connected'}
                
        try:
            # Search for contact/number
            search_box = self.page.query_selector('[role="textbox"][title="Search or start new chat"]')
            if search_box:
                search_box.fill(to)
                self.page.wait_for_timeout(2000)
                
                # Click on first result
                first_result = self.page.query_selector('[role="listitem"]')
                if first_result:
                    first_result.click()
                    self.page.wait_for_timeout(1000)
                else:
                    return {'success': False, 'error': f'Contact not found: {to}'}
                    
            # Type message
            message_box = self.page.query_selector('[role="textbox"][data-tab="10"]')
            if message_box:
                message_box.fill(message)
                self.page.wait_for_timeout(500)
                
                # Send message
                send_button = self.page.query_selector('[data-testid="compose-btn-send"]')
                if send_button:
                    send_button.click()
                    self.page.wait_for_timeout(1000)
                    
                    return {
                        'success': True,
                        'message_id': f'whatsapp_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    }
                else:
                    # Try Enter key to send
                    self.page.keyboard.press('Enter')
                    return {
                        'success': True,
                        'message_id': f'whatsapp_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    }
            else:
                return {'success': False, 'error': 'Message box not found'}
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_status(self) -> dict:
        """Get WhatsApp adapter status."""
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
        """Close WhatsApp connection."""
        if self.browser:
            self.browser.close()
            self.browser = None
        self.page = None
        self.connected = False
        
    def list_contacts(self, limit: int = 50) -> List[dict]:
        """
        List recent WhatsApp contacts.
        
        Args:
            limit: Maximum contacts to return
            
        Returns:
            List of contact dicts
        """
        if not self.connected:
            return []
            
        try:
            contacts = []
            contact_elements = self.page.query_selector_all('[role="listitem"]')
            
            for elem in contact_elements[:limit]:
                try:
                    name_elem = elem.query_selector('[role="link"] span[title]')
                    if name_elem:
                        contacts.append({
                            'name': name_elem.get_attribute('title'),
                            'type': 'contact'
                        })
                except Exception:
                    continue
                    
            return contacts
            
        except Exception:
            return []
            
    def requires_approval(self, **kwargs) -> bool:
        """
        Check if WhatsApp message requires approval.
        
        Approval required when:
        - New contact (first time messaging)
        - Contains payment keywords
        """
        to = kwargs.get('to', '')
        message = kwargs.get('message', '')
        
        # Check for payment keywords
        payment_keywords = ['invoice', 'payment', 'pay', 'money', 'urgent', 'asap']
        if any(keyword in message.lower() for keyword in payment_keywords):
            return True
            
        # Require approval for all messages by default
        return True
