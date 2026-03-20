"""
Security middleware for production deployment.
Add security headers and rate limiting.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.

    For production, use Redis-backed rate limiting with libraries like:
    - slowapi
    - fastapi-limiter
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for X-Forwarded-For header (from reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client.host
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if client has exceeded rate limit.

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        now = time.time()
        minute_ago = now - 60

        # Clean up old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] if req_time > minute_ago
        ]

        # Check rate limit
        request_count = len(self.requests[client_ip])
        if request_count >= self.requests_per_minute:
            # Calculate retry-after (time until oldest request expires)
            oldest_request = min(self.requests[client_ip])
            retry_after = int(60 - (now - oldest_request))
            return True, retry_after

        # Add current request
        self.requests[client_ip].append(now)
        return False, 0

    async def dispatch(self, request: Request, call_next):
        # Exclude health check endpoints from rate limiting
        if request.url.path in ["/api/health", "/health", "/"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        is_limited, retry_after = self._is_rate_limited(client_ip)

        if is_limited:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        # Add rate limit headers to successful responses
        response = await call_next(request)
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response


# Usage in main.py:
# from middleware.security import SecurityHeadersMiddleware, RateLimitMiddleware
#
# app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
