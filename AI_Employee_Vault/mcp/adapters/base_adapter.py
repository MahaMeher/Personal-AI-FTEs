"""
Base Adapter for MCP Server

All adapters inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAdapter(ABC):
    """Base class for all MCP adapters."""
    
    def __init__(self, config: dict):
        self.config = config
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the service."""
        pass
    
    @abstractmethod
    def send_message(self, **kwargs) -> dict:
        """Send a message."""
        pass
    
    def get_status(self) -> dict:
        """Get connection status."""
        return {'connected': self.connected}
    
    def close(self):
        """Close connection."""
        self.connected = False
