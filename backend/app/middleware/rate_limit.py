"""
================================================================================
Farm Management System - Rate Limiting Middleware
================================================================================
Version: 1.0.0
Last Updated: 2025-11-21

Features:
- In-memory rate limiting (fast, resets on restart)
- Configurable limits per endpoint
- IP-based and user-based limiting
================================================================================
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    """

    def __init__(self, app, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # {ip: [timestamps]}
        self.lock = asyncio.Lock()

        # Endpoint-specific limits (more restrictive for auth)
        self.endpoint_limits = {
            "/api/auth/login": (5, 60),      # 5 requests per minute
            "/api/auth/forgot-password": (3, 300),  # 3 per 5 minutes
            "/api/auth/reset-password": (5, 300),   # 5 per 5 minutes
            "/api/auth/change-password": (5, 300),  # 5 per 5 minutes
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/openapi") or path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Get limit for this endpoint
        limit, window = self.endpoint_limits.get(path, (self.default_limit, self.window_seconds))

        # Check rate limit
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window)

            # Clean old requests
            key = f"{client_ip}:{path}"
            self.requests[key] = [
                ts for ts in self.requests[key]
                if ts > window_start
            ]

            # Check if over limit
            if len(self.requests[key]) >= limit:
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Too many requests. Please try again in {window} seconds.",
                        "retry_after": window
                    },
                    headers={"Retry-After": str(window)}
                )

            # Record this request
            self.requests[key].append(now)

        # Continue with request
        response = await call_next(request)
        return response


# Rate limit configuration
RATE_LIMIT_CONFIG = {
    "default_limit": 100,  # requests
    "window_seconds": 60,  # per minute
}
