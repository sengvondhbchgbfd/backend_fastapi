import json
import asyncio
import redis.asyncio as redis
from fastapi import WebSocket

from app.core.config import settings
from app.websockets.base_handler import BaseWebSocketHandler


class ChatWebSocketHandler(BaseWebSocketHandler):
    """
    Chat-specific handler.
    Inherits full connection pool + broadcast logic from BaseWebSocketHandler.
    Adds Redis Pub/Sub so messages fan out across multiple server instances.
    """

    async def handle_message(
        self,
        websocket: WebSocket,
        group_id: int,
        member_id: int,
        data: dict,
    ) -> None:
        """
        Called by the router when a staff member sends a message.
        Override here to add typing indicators, read receipts, etc.
        """
        await self.broadcast_to_group(
            group_id=group_id,
            data=data,
            exclude_member_id=None,  # include sender — Redis echo handles dedup if needed
        )


# ── Redis Pub/Sub ─────────────────────────────────────────────────────────────

async def start_chat_pubsub_listener(handler: ChatWebSocketHandler) -> None:
    """
    Long-running background task.
    Listens on Redis channel 'chat' and fans out to local WebSocket connections.
    Auto-reconnects on failure.
    """
    while True:
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe("chat")
            print("✅ Chat Pub/Sub listener started")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    group_id = data.get("group_id")
                    if group_id:
                        await handler.broadcast_to_group(
                            group_id=group_id,
                            data=data,
                            exclude_member_id=None,
                        )
                except Exception as e:
                    print(f"❌ Chat pub/sub message error: {e}")

        except Exception as e:
            print(f"❌ Chat pub/sub connection error: {e}. Retrying in 3s...")
            await asyncio.sleep(3)


async def publish_chat_message(
    redis_client: redis.Redis,
    group_id: int,
    data: dict,
) -> None:
    """Publish a chat message to Redis so all server instances broadcast it."""
    payload = {**data, "group_id": group_id}
    await redis_client.publish("chat", json.dumps(payload, default=str))