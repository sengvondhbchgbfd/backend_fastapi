from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.core.config import settings

def get_user_or_ip(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


# IP-based → for auth endpoints (login, refresh, logout)

ip_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,    # ← Redis
    default_limits=["5/minute"],  # only 5 login attempts per minute per IP
)


user_limiter = Limiter(
    key_func=get_user_or_ip,
    storage_uri=settings.REDIS_URL,
    default_limits=["1000/minute"],
)