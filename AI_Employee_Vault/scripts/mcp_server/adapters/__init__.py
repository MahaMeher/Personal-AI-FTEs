"""
MCP Server Adapters Package

Contains adapters for different communication channels:
- Email (Gmail, Outlook, SMTP)
- WhatsApp
- LinkedIn
- Browser (Playwright)
"""

from .base_adapter import BaseAdapter

__all__ = ['BaseAdapter']
