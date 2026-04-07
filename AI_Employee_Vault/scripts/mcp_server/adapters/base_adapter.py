"""
Base Adapter for MCP Server

Abstract base class for all communication channel adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAdapter(ABC):
    """
    Abstract base class for MCP server adapters.
    
    All adapters must implement:
    - connect(): Establish connection
    - send_message(): Send message via channel
    - get_status(): Get connection status
    - close(): Close connection
    """
    
    def __init__(self, config: dict):
        """
        Initialize adapter with configuration.
        
        Args:
            config: Adapter-specific configuration
        """
        self.config = config
        self.connected = False
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the service.
        
        Returns:
            True if connected successfully
        """
        pass
        
    @abstractmethod
    def send_message(self, **kwargs) -> dict:
        """
        Send message via this channel.
        
        Args:
            **kwargs: Channel-specific parameters
            
        Returns:
            Result dict with success status and message_id
        """
        pass
        
    @abstractmethod
    def get_status(self) -> dict:
        """
        Get current connection status.
        
        Returns:
            Dict with status information
        """
        pass
        
    @abstractmethod
    def close(self):
        """
        Close connection and cleanup resources.
        """
        pass
        
    def list_contacts(self, limit: int = 50) -> List[dict]:
        """
        List contacts from this channel.
        
        Args:
            limit: Maximum contacts to return
            
        Returns:
            List of contact dicts
        """
        return []
        
    def requires_approval(self, **kwargs) -> bool:
        """
        Check if action requires human approval.
        
        Args:
            **kwargs: Action parameters
            
        Returns:
            True if approval required
        """
        return True  # Default: always require approval
