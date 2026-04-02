import redis.asyncio as redis

from app.core.config import settings

redis_client: redis.Redis | None = None


# # Single shared Redis connection pool  aiofiles
# redis_client = aioredis.from_url(
#     settings.REDIS_URL,
#     encoding="utf-8",
#     decode_responses=True,
#     max_connections=20,      # pool size
#     socket_timeout=5,        # fail fast if Redis is down
#     socket_connect_timeout=5,
# )


async def connect_redis() -> None:
    global redis_client
    redis_client = redis.Redis(
        host             = settings.REDIS_HOST,
        port             = settings.REDIS_PORT,
        password         = settings.REDIS_PASSWORD or None,
        db               = settings.REDIS_DB,
        decode_responses = True,
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