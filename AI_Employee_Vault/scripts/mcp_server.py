"""
Universal MCP Server

Main MCP server implementation supporting multiple adapters:
- Email (Gmail, Outlook, SMTP)
- WhatsApp
- LinkedIn
- Browser (Playwright)
- Slack (coming soon)
- Twitter (coming soon)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import sys

# Setup paths for adapter imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
sys.path.insert(0, str(script_dir / 'mcp_server'))

# Import adapters
from adapters.base_adapter import BaseAdapter


class UniversalMCPServer:
    """
    Universal MCP Server with multiple adapter support.
    """
    
    def __init__(self, config_path: str = "config/mcp/adapters.json"):
        """
        Initialize MCP server with adapter configuration.
        
        Args:
            config_path: Path to adapter configuration file
        """
        self.config_path = Path(config_path)
        self.adapters: Dict[str, BaseAdapter] = {}
        self.vault_path = Path(__file__).parent.parent
        self.logs_dir = self.vault_path / "Logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        self._load_adapters()
        
    def _setup_logging(self):
        """Setup logging to file."""
        log_file = self.logs_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('UniversalMCPServer')
        
    def _load_adapters(self):
        """Load and initialize adapters from config."""
        if not self.config_path.exists():
            self.logger.warning(f"Config not found: {self.config_path}")
            self.logger.info("Creating default config...")
            self._create_default_config()
            return
            
        try:
            config = json.loads(self.config_path.read_text())
            
            for adapter_name, adapter_config in config.get('adapters', {}).items():
                if not adapter_config.get('enabled', False):
                    self.logger.info(f"Adapter {adapter_name} is disabled")
                    continue
                    
                try:
                    adapter = self._create_adapter(adapter_name, adapter_config)
                    if adapter and adapter.connect():
                        self.adapters[adapter_name] = adapter
                        self.logger.info(f"Adapter {adapter_name} connected successfully")
                    else:
                        self.logger.warning(f"Failed to connect adapter {adapter_name}")
                except Exception as e:
                    self.logger.error(f"Error loading adapter {adapter_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            
    def _create_adapter(self, name: str, config: dict) -> Optional[BaseAdapter]:
        """
        Create adapter instance by name.
        
        Args:
            name: Adapter name (email, whatsapp, linkedin, browser)
            config: Adapter configuration
            
        Returns:
            Adapter instance or None
        """
        try:
            if name == 'email':
                from mcp_server.adapters.email_adapter import EmailAdapter
                return EmailAdapter(config)
            elif name == 'whatsapp':
                from mcp_server.adapters.whatsapp_adapter import WhatsAppAdapter
                return WhatsAppAdapter(config)
            elif name == 'linkedin':
                from mcp_server.adapters.linkedin_adapter import LinkedInAdapter
                return LinkedInAdapter(config)
            elif name == 'browser':
                from mcp_server.adapters.browser_adapter import BrowserAdapter
                return BrowserAdapter(config)
            else:
                self.logger.warning(f"Unknown adapter: {name}")
                return None
        except ImportError as e:
            self.logger.error(f"Failed to import adapter {name}: {e}")
            return None
            
    def _create_default_config(self):
        """Create default adapter configuration."""
        default_config = {
            "adapters": {
                "email": {
                    "enabled": False,
                    "provider": "gmail",
                    "credentials": "config/email/credentials.json"
                },
                "whatsapp": {
                    "enabled": False,
                    "session_path": "config/whatsapp/session"
                },
                "linkedin": {
                    "enabled": False,
                    "session_path": "config/linkedin/session"
                },
                "browser": {
                    "enabled": True,
                    "headless": True
                }
            }
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(default_config, indent=2))
        self.logger.info(f"Default config created: {self.config_path}")
        
    def send_message(self, channel: str, **kwargs) -> dict:
        """
        Send message via specified channel.
        
        Args:
            channel: Channel name (email, whatsapp, linkedin, etc.)
            **kwargs: Channel-specific parameters
            
        Returns:
            Result dict with success status and message_id
        """
        if channel not in self.adapters:
            return {
                'success': False,
                'error': f'Channel {channel} not available'
            }
            
        adapter = self.adapters[channel]
        
        try:
            result = adapter.send_message(**kwargs)
            self._log_action('send_message', channel, kwargs, result)
            return result
        except Exception as e:
            self.logger.error(f"Error sending message via {channel}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def browser_action(self, action: str, **kwargs) -> dict:
        """
        Perform browser automation action.
        
        Args:
            action: Action type (navigate, click, type, screenshot, evaluate)
            **kwargs: Action-specific parameters
            
        Returns:
            Result dict with action result
        """
        if 'browser' not in self.adapters:
            return {
                'success': False,
                'error': 'Browser adapter not available'
            }
            
        adapter = self.adapters['browser']
        
        try:
            if action == 'navigate':
                result = adapter.navigate(kwargs.get('url'))
            elif action == 'click':
                result = adapter.click(kwargs.get('selector'))
            elif action == 'type':
                result = adapter.type_text(
                    kwargs.get('selector'),
                    kwargs.get('text')
                )
            elif action == 'screenshot':
                result = adapter.screenshot()
            elif action == 'evaluate':
                result = adapter.evaluate(kwargs.get('script'))
            else:
                result = {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
            self._log_action('browser_action', action, kwargs, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in browser action {action}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_status(self) -> dict:
        """
        Get status of all adapters.
        
        Returns:
            Dict with adapter statuses
        """
        status = {}
        for name, adapter in self.adapters.items():
            status[name] = adapter.get_status()
        return status
        
    def list_contacts(self, channel: str, limit: int = 50) -> dict:
        """
        List contacts from specified channel.
        
        Args:
            channel: Channel name
            limit: Maximum contacts to return
            
        Returns:
            Dict with contact list
        """
        if channel not in self.adapters:
            return {
                'success': False,
                'error': f'Channel {channel} not available'
            }
            
        adapter = self.adapters[channel]
        
        try:
            contacts = adapter.list_contacts(limit=limit)
            return {
                'success': True,
                'contacts': contacts
            }
        except Exception as e:
            self.logger.error(f"Error listing contacts for {channel}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def _log_action(self, action_type: str, channel: str, params: dict, result: dict):
        """Log action to JSONL file."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'channel': channel,
            'params': params,
            'result': result
        }
        
        log_file = self.logs_dir / f"mcp_actions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    def close(self):
        """Close all adapters."""
        for name, adapter in self.adapters.items():
            try:
                adapter.close()
                self.logger.info(f"Adapter {name} closed")
            except Exception as e:
                self.logger.error(f"Error closing adapter {name}: {e}")


def main():
    """Main entry point for MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal MCP Server')
    parser.add_argument('--config', default='config/mcp/adapters.json',
                       help='Path to adapter config')
    parser.add_argument('--adapters', default=None,
                       help='Comma-separated list of adapters to enable')
    
    args = parser.parse_args()
    
    server = UniversalMCPServer(config_path=args.config)
    
    print("Universal MCP Server started")
    print(f"Available adapters: {list(server.adapters.keys())}")
    print("\nCommands:")
    print("  status - Get adapter status")
    print("  send <channel> <to> <message> - Send message")
    print("  browser <action> [params] - Browser action")
    print("  quit - Exit server")
    
    try:
        while True:
            cmd = input("\nmcp> ").strip()
            
            if cmd.lower() == 'quit':
                break
            elif cmd.lower() == 'status':
                status = server.get_status()
                print(json.dumps(status, indent=2))
            elif cmd.lower().startswith('send '):
                parts = cmd.split(' ', 3)
                if len(parts) >= 4:
                    channel = parts[1]
                    to = parts[2]
                    message = parts[3]
                    result = server.send_message(
                        channel=channel,
                        to=to,
                        message=message
                    )
                    print(json.dumps(result, indent=2))
                else:
                    print("Usage: send <channel> <to> <message>")
            elif cmd.lower().startswith('browser '):
                parts = cmd.split(' ', 2)
                if len(parts) >= 2:
                    action = parts[1]
                    params = json.loads(parts[2]) if len(parts) > 2 else {}
                    result = server.browser_action(action, **params)
                    print(json.dumps(result, indent=2))
                else:
                    print("Usage: browser <action> [params]")
            else:
                print("Unknown command")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()


if __name__ == '__main__':
    main()
