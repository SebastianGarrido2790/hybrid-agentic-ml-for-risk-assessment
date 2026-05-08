"""
Security configuration for the FastAPI application.

Provides Global Security Headers and Rate Limiting.
"""

from typing import Awaitable, Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

# Global Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject standard security headers.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
