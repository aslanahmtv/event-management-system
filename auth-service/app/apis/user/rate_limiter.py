"""Rate limiting implementation"""
import time
from datetime import datetime
from typing import Dict, Tuple

from fastapi import Request, HTTPException, status

from app.apis.config import settings


# Simple in-memory rate limiter
class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}  # client_id -> [timestamps]
        
    def _parse_limit(self, limit: str) -> Tuple[int, int]:
        """Parse a rate limit string like '5/minute' into (5, 60)"""
        count, period = limit.split("/")
        seconds = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
        return int(count), seconds.get(period.lower(), 60)
        
    def is_rate_limited(self, client_id: str, limit: str = settings.LOGIN_RATE_LIMIT) -> bool:
        """Check if a client has exceeded their rate limit"""
        if not settings.RATE_LIMIT_ENABLED:
            return False
            
        count, period_seconds = self._parse_limit(limit)
        now = time.time()
        
        # Initialize client's request history if not present
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Filter out old requests
        self.requests[client_id] = [ts for ts in self.requests[client_id] if now - ts < period_seconds]
        
        # Check if client has exceeded limit
        if len(self.requests[client_id]) >= count:
            return True
            
        # Record this request
        self.requests[client_id].append(now)
        return False


# Create a global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit_login(request: Request):
    """Middleware function to apply rate limiting to login endpoint"""
    client_id = request.client.host
    if rate_limiter.is_rate_limited(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )