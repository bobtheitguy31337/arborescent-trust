"""
Rate limiting middleware using Redis
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import time
from typing import Callable, Optional
from app.config import settings

# Redis client for rate limiting
redis_client: Optional[redis.Redis] = None

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    print(f"Warning: Redis not available for rate limiting: {e}")
    redis_client = None


class RateLimiter:
    """
    Rate limiter using sliding window algorithm
    """
    
    def __init__(self, calls: int, period: int):
        """
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
    
    async def __call__(self, request: Request, call_next: Callable):
        if not redis_client:
            # If Redis is not available, skip rate limiting
            return await call_next(request)
        
        # Get client identifier (IP address or user ID if authenticated)
        client_id = request.client.host if request.client else "unknown"
        
        # Check if user is authenticated and use user ID instead
        if hasattr(request.state, "user") and request.state.user:
            client_id = f"user:{request.state.user.id}"
        
        # Get the request path for different rate limits per endpoint
        path = request.url.path
        
        # Create rate limit key
        key = f"rate_limit:{path}:{client_id}"
        
        current_time = int(time.time())
        window_start = current_time - self.period
        
        try:
            # Remove old entries outside the time window
            redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = redis_client.zcard(key)
            
            if request_count >= self.calls:
                # Rate limit exceeded
                retry_after = self.period
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            
            # Add current request
            redis_client.zadd(key, {str(current_time): current_time})
            
            # Set expiry on key
            redis_client.expire(key, self.period)
            
        except Exception as e:
            # If Redis fails, log but don't block the request
            print(f"Rate limiting error: {e}")
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - request_count - 1))
        response.headers["X-RateLimit-Reset"] = str(current_time + self.period)
        
        return response


def rate_limit(calls: int, period: int):
    """
    Decorator for rate limiting specific endpoints
    
    Usage:
        @app.get("/api/endpoint")
        @rate_limit(calls=10, period=60)  # 10 calls per minute
        async def endpoint():
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This is a placeholder - actual implementation would need
            # to be integrated with FastAPI's dependency injection
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Common rate limit configurations
AUTH_RATE_LIMIT = RateLimiter(calls=5, period=60)  # 5 requests per minute
INVITE_RATE_LIMIT = RateLimiter(calls=10, period=3600)  # 10 requests per hour
ADMIN_RATE_LIMIT = RateLimiter(calls=100, period=3600)  # 100 requests per hour
DEFAULT_RATE_LIMIT = RateLimiter(calls=100, period=60)  # 100 requests per minute

