import json
from typing import Any
from fastapi import Depends
import redis.asyncio as redis
from fastapi.encoders import jsonable_encoder
from app.db.redis import get_redis_client

class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Any | None:
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        json_value = json.dumps(jsonable_encoder(value))
        await self.redis.set(key, json_value, ex=ttl)



    async def delete(self, key: str) -> None:
        await self.redis.delete(key)



    async def exists(self, key: str) -> bool:
        return bool(await self.redis.exists(key))
    



    async def delete_pattern(self, pattern: str) -> None:
        """
        Delete all keys matching the given pattern.
        Uses SCAN to avoid blocking Redis.
        """
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

def get_cache_service(
        redis_client: redis.Redis =  Depends(get_redis_client)
) -> CacheService:
    return CacheService(redis_client)