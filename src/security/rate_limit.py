"""
Rate Limiting Configuration
Protects API from abuse and DoS attacks
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Callable
import structlog

logger = structlog.get_logger(__name__)


def get_api_key_identifier(request: Request) -> str:
    """
    Get rate limit identifier (API key or IP).
    
    Priority:
    1. API key (if authenticated)
    2. User ID (if available)
    3. IP address (fallback)
    """
    # Try to get API key from request state (set by auth middleware)
    if hasattr(request.state, 'api_key') and request.state.api_key:
        return f"key:{request.state.api_key.id}"
    
    # Try to get user ID
    if hasattr(request.state, 'user_id') and request.state.user_id:
        return f"user:{request.state.user_id}"
    
    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=["100/minute", "1000/hour", "10000/day"],
    storage_uri="memory://",  # Use in-memory storage (can use Redis later)
    strategy="fixed-window",
    headers_enabled=True  # Add rate limit headers to responses
)


def configure_rate_limiting(app):
    """
    Configure rate limiting for FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        app = FastAPI()
        configure_rate_limiting(app)
    """
    # Add limiter to app state
    app.state.limiter = limiter
    
    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info("rate_limiting_configured",
               default_limits=limiter._default_limits,
               strategy=limiter._strategy)


# Rate limit decorators for common use cases

def rate_limit_strict(limit: str = "30/minute"):
    """
    Strict rate limit (for expensive operations).
    
    Usage:
        @app.post("/expensive")
        @limiter.limit(rate_limit_strict())
        async def expensive_operation():
            ...
    """
    return limit


def rate_limit_normal(limit: str = "60/minute"):
    """
    Normal rate limit (for standard API calls).
    
    Usage:
        @app.post("/api/conversation")
        @limiter.limit(rate_limit_normal())
        async def conversation():
            ...
    """
    return limit


def rate_limit_lenient(limit: str = "120/minute"):
    """
    Lenient rate limit (for lightweight operations).
    
    Usage:
        @app.get("/health")
        @limiter.limit(rate_limit_lenient())
        async def health():
            ...
    """
    return limit


def get_rate_limit_for_key(api_key) -> str:
    """
    Get custom rate limit for specific API key.
    
    Args:
        api_key: APIKey object from database
    
    Returns:
        Rate limit string (e.g., "100/minute")
    """
    if not api_key:
        return rate_limit_normal()
    
    # Use key's configured limit
    return f"{api_key.rate_limit_per_minute}/minute"


# Logging middleware for rate limit events
async def log_rate_limit_event(request: Request, exc: RateLimitExceeded):
    """Log rate limit violations"""
    identifier = get_api_key_identifier(request)
    
    logger.warning("rate_limit_exceeded",
                  identifier=identifier,
                  path=request.url.path,
                  method=request.method,
                  limit=str(exc))
    
    # Could also:
    # - Send alert to admin
    # - Block IP after N violations
    # - Update abuse score in database
