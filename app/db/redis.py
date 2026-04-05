import redis.asyncio as redis

from app.core.config import settings

redis_client: redis.Redis | None = None

async def connect_redis() -> None:
    global redis_client
    redis_url = settings.REDIS_URL  
    redis_client = redis.from_url(
        redis_url,
        decode_responses=True,
        max_connections=20
    )
    await redis_client.ping()
    print("✅ Redis connected")



async def disconnect_redis() -> None:
    global redis_client
    if redis_client:
        await redis_client.aclose()
        print("✅ Redis disconnected")

async def get_redis() -> redis.Redis:
    """Original dependency — keep for existing routers."""
    if redis_client is None:
        raise RuntimeError("Redis is not connected")
    return redis_client

async def check_redis():
    """Health check — call on startup"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        return False


# ✅ alias — used by notification_service and ws_manager
def get_redis_client() -> redis.Redis:
    """Sync dependency — used by FastAPI Depends() in notification service."""
    if redis_client is None:
        raise RuntimeError("Redis is not connected")
    return redis_client