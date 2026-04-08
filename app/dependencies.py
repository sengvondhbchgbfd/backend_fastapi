from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from typing import AsyncGenerator
import redis.asyncio as redis
from app.db.redis import get_redis
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
       
async def get_redis_client() -> redis.Redis:
    return await get_redis()