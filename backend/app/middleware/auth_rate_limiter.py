"""
Rate limiting middleware to prevent brute force attacks and API abuse.
Uses in-memory storage with sliding window algorithm.
"""
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.
    Stores request timestamps in memory (consider Redis for production).
    """

    def __init__(self):
        # Store: {identifier: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = None
        self._cleanup_task = None

    async def _cleanup_old_entries(self):
        """Periodically clean up old entries to prevent memory leaks"""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            async with self.lock:
                current_time = datetime.utcnow()
                for identifier in list(self.requests.keys()):
                    # Remove entries older than 1 hour
                    self.requests[identifier] = [
                        ts for ts in self.requests[identifier]
                        if current_time - ts < timedelta(hours=1)
                    ]
                    # Remove identifier if no entries left
                    if not self.requests[identifier]:
                        del self.requests[identifier]

    async def _ensure_initialized(self):
        """Lazy initialization of async components"""
        if self.lock is None:
            self.lock = asyncio.Lock()
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_entries())

    async def is_rate_limited(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict]:
        """
        Check if identifier has exceeded rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, email)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited: bool, info: dict)
        """
        await self._ensure_initialized()
        async with self.lock:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=window_seconds)

            # Get requests within current window
            if identifier in self.requests:
                # Remove old requests outside window
                self.requests[identifier] = [
                    ts for ts in self.requests[identifier]
                    if ts > window_start
                ]
                request_count = len(self.requests[identifier])
            else:
                request_count = 0

            # Check if rate limited
            is_limited = request_count >= max_requests

            if not is_limited:
                # Add current request
                self.requests[identifier].append(current_time)
                request_count += 1

            # Calculate retry-after time
            retry_after = 0
            if is_limited and self.requests[identifier]:
                oldest_request = self.requests[identifier][0]
                retry_after = int((oldest_request + timedelta(seconds=window_seconds) - current_time).total_seconds())

            return is_limited, {
                "request_count": request_count,
                "limit": max_requests,
                "window_seconds": window_seconds,
                "retry_after": max(0, retry_after),
                "reset_at": (current_time + timedelta(seconds=retry_after)).isoformat() if retry_after > 0 else None
            }

    async def reset_identifier(self, identifier: str):
        """Reset rate limit for an identifier"""
        await self._ensure_initialized()
        async with self.lock:
            if identifier in self.requests:
                del self.requests[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitConfig:
    """Rate limit configurations for different endpoints"""

    # Authentication endpoints (DEVELOPMENT: Relaxed limits for testing)
    # TODO: Tighten these in production
    LOGIN = {"max_requests": 20, "window_seconds": 60}  # 20 attempts per minute
    REGISTER = {"max_requests": 20, "window_seconds": 60}  # 20 attempts per minute
    SEND_OTP = {"max_requests": 20, "window_seconds": 60}  # 20 OTPs per minute
    VERIFY_OTP = {"max_requests": 20, "window_seconds": 60}  # 20 verifications per minute
    PASSWORD_RESET = {"max_requests": 20, "window_seconds": 60}  # 20 resets per minute
    GOOGLE_OAUTH = {"max_requests": 20, "window_seconds": 60}  # 20 OAuth attempts per minute

    # General API endpoints (less restrictive)
    API_GENERAL = {"max_requests": 100, "window_seconds": 60}  # 100 requests per minute
    API_STRICT = {"max_requests": 30, "window_seconds": 60}  # 30 requests per minute


async def check_rate_limit(
    request: Request,
    identifier: str,
    limit_config: Dict[str, int]
):
    """
    Check rate limit and raise HTTPException if exceeded.

    Args:
        request: FastAPI request object
        identifier: Unique identifier (IP, email, user ID)
        limit_config: Dict with 'max_requests' and 'window_seconds'

    Raises:
        HTTPException: If rate limit exceeded
    """
    is_limited, info = await rate_limiter.is_rate_limited(
        identifier,
        limit_config["max_requests"],
        limit_config["window_seconds"]
    )

    # Add rate limit headers to response
    request.state.rate_limit_info = info

    if is_limited:
        logger.warning(
            f"Rate limit exceeded for {identifier}. "
            f"Attempts: {info['request_count']}/{info['limit']}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please try again in {info['retry_after']} seconds.",
                "retry_after": info['retry_after'],
                "reset_at": info['reset_at']
            },
            headers={
                "Retry-After": str(info['retry_after']),
                "X-RateLimit-Limit": str(info['limit']),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": info['reset_at'] or ""
            }
        )


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Handles proxy headers (X-Forwarded-For, X-Real-IP).
    """
    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


async def rate_limit_by_ip(request: Request, limit_config: Dict[str, int]):
    """Rate limit by IP address"""
    ip_address = get_client_ip(request)
    await check_rate_limit(request, f"ip:{ip_address}", limit_config)


async def rate_limit_by_email(request: Request, email: str, limit_config: Dict[str, int]):
    """Rate limit by email address"""
    await check_rate_limit(request, f"email:{email}", limit_config)


async def rate_limit_by_user_id(request: Request, user_id: str, limit_config: Dict[str, int]):
    """Rate limit by user ID"""
    await check_rate_limit(request, f"user:{user_id}", limit_config)
