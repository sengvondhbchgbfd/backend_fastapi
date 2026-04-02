from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings


def get_user_or_ip(request: Request) -> str:
    """
    Rate limit key:
    - logged in user  → user:42
    - not logged in   → ip:192.168.1.1
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# IP-based → for auth endpoints (login, refresh, logout)


ip_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,    # ← Redis
    default_limits=["200/minute"],     # global fallback
)

# User-based → for protected API endpoints
user_limiter = Limiter(
    key_func=get_user_or_ip,
    storage_uri=settings.REDIS_URL,    # ← Redis
    default_limits=["1000/minute"],    # global fallback
)