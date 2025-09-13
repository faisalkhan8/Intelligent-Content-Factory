"""
Rate Limiter Utility - API Request Rate Limiting
===============================================

Implements rate limiting functionality for API endpoints
Prevents abuse and ensures fair resource usage
"""

import time
import logging
from typing import Dict, List
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Token bucket rate limiter for API requests
    
    Implements rate limiting based on client IP addresses
    with configurable request limits and time windows
    """
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_history: Dict[str, deque] = defaultdict(deque)
        
        logger.info(f"Rate limiter initialized: {max_requests} requests per {time_window} seconds")
    
    def allow_request(self, client_id: str) -> bool:
        """
        Check if request should be allowed for the given client
        
        Args:
            client_id: Unique identifier for the client (usually IP address)
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        client_requests = self.request_history[client_id]
        
        # Remove old requests outside the time window
        while client_requests and client_requests[0] <= current_time - self.time_window:
            client_requests.popleft()
        
        # Check if client has exceeded rate limit
        if len(client_requests) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False
        
        # Add current request to history
        client_requests.append(current_time)
        
        logger.debug(f"Request allowed for client {client_id}: {len(client_requests)}/{self.max_requests}")
        return True
    
    def get_client_status(self, client_id: str) -> Dict[str, any]:
        """
        Get rate limiting status for a specific client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with client rate limiting information
        """
        current_time = time.time()
        client_requests = self.request_history[client_id]
        
        # Clean up old requests
        while client_requests and client_requests[0] <= current_time - self.time_window:
            client_requests.popleft()
        
        requests_used = len(client_requests)
        requests_remaining = max(0, self.max_requests - requests_used)
        
        # Calculate reset time (when oldest request will expire)
        reset_time = None
        if client_requests:
            reset_time = client_requests[0] + self.time_window
        
        return {
            "client_id": client_id,
            "requests_used": requests_used,
            "requests_remaining": requests_remaining,
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "reset_time": reset_time,
            "is_limited": requests_used >= self.max_requests
        }
    
    def get_all_clients_status(self) -> List[Dict[str, any]]:
        """
        Get rate limiting status for all clients
        
        Returns:
            List of dictionaries with client information
        """
        return [self.get_client_status(client_id) for client_id in self.request_history.keys()]
    
    def reset_client(self, client_id: str) -> bool:
        """
        Reset rate limit for a specific client (admin function)
        
        Args:
            client_id: Client identifier to reset
            
        Returns:
            True if client was found and reset, False otherwise
        """
        if client_id in self.request_history:
            del self.request_history[client_id]
            logger.info(f"Rate limit reset for client: {client_id}")
            return True
        return False
    
    def cleanup_old_entries(self):
        """
        Clean up old entries from all clients to prevent memory leaks
        Should be called periodically by a background task
        """
        current_time = time.time()
        clients_to_remove = []
        
        for client_id, requests in self.request_history.items():
            # Remove old requests
            while requests and requests[0] <= current_time - self.time_window:
                requests.popleft()
            
            # Mark empty clients for removal
            if not requests:
                clients_to_remove.append(client_id)
        
        # Remove empty clients
        for client_id in clients_to_remove:
            del self.request_history[client_id]
        
        logger.debug(f"Cleaned up {len(clients_to_remove)} inactive clients")
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get overall rate limiter statistics
        
        Returns:
            Dictionary with statistics
        """
        total_clients = len(self.request_history)
        total_requests = sum(len(requests) for requests in self.request_history.values())
        
        # Count active clients (with requests in current window)
        current_time = time.time()
        active_clients = 0
        limited_clients = 0
        
        for requests in self.request_history.values():
            recent_requests = [r for r in requests if r > current_time - self.time_window]
            if recent_requests:
                active_clients += 1
                if len(recent_requests) >= self.max_requests:
                    limited_clients += 1
        
        return {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "limited_clients": limited_clients,
            "total_requests_tracked": total_requests,
            "max_requests_per_window": self.max_requests,
            "time_window_seconds": self.time_window
        }


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple tiers and burst handling
    
    Supports different rate limits for different client types
    and implements burst request handling
    """
    
    def __init__(self):
        self.limiters = {}
        self.client_tiers = {}  # Maps client_id to tier name
        
    def add_tier(self, tier_name: str, max_requests: int, time_window: int):
        """
        Add a rate limiting tier
        
        Args:
            tier_name: Name of the tier (e.g., 'free', 'premium', 'admin')
            max_requests: Maximum requests for this tier
            time_window: Time window in seconds
        """
        self.limiters[tier_name] = RateLimiter(max_requests, time_window)
        logger.info(f"Added rate limiting tier '{tier_name}': {max_requests}/{time_window}s")
    
    def set_client_tier(self, client_id: str, tier_name: str):
        """
        Assign a client to a specific tier
        
        Args:
            client_id: Client identifier
            tier_name: Tier name to assign
        """
        if tier_name not in self.limiters:
            raise ValueError(f"Tier '{tier_name}' not found")
        
        self.client_tiers[client_id] = tier_name
        logger.info(f"Client {client_id} assigned to tier '{tier_name}'")
    
    def allow_request(self, client_id: str) -> bool:
        """
        Check if request should be allowed using tiered rate limiting
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # Default to 'default' tier if not specified
        tier_name = self.client_tiers.get(client_id, 'default')
        
        # Create default tier if it doesn't exist
        if tier_name not in self.limiters:
            self.add_tier('default', 60, 60)  # 60 requests per minute default
        
        return self.limiters[tier_name].allow_request(client_id)
    
    def get_client_status(self, client_id: str) -> Dict[str, any]:
        """Get detailed status for a client including tier information"""
        tier_name = self.client_tiers.get(client_id, 'default')
        
        if tier_name not in self.limiters:
            self.add_tier('default', 60, 60)
        
        status = self.limiters[tier_name].get_client_status(client_id)
        status['tier'] = tier_name
        
        return status