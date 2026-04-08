import json
import asyncio
import redis.asyncio as redis
from fastapi import WebSocket

from app.core.config import settings
from app.websockets.base_handler import BaseWebSocketHandler


class NotificationWebSocketHandler(BaseWebSocketHandler):
    """
    Notification-specific handler.
    member_id  = staff_id
    group_id   = company_id  (or use 0 as a global namespace)
    """

    async def handle_message(
        self,
        websocket: WebSocket,
        group_id: int,
        member_id: int,
        data: dict,
    ) -> None:
        """Notifications are server-push only; clients don't send messages."""
        pass

    async def send_to_staff(self, company_id: int, staff_id: int, data: dict) -> None:
        """Push a notification to one specific staff member."""
        await self.send_to_member(group_id=company_id, member_id=staff_id, data=data)

    async def broadcast_to_company(self, company_id: int, data: dict) -> None:
        """Push a notification to every connected staff in a company."""
        await self.broadcast_to_group(group_id=company_id, data=data)


# ── Redis Pub/Sub ─────────────────────────────────────────────────────────────



async def start_notification_pubsub_listener(handler: NotificationWebSocketHandler) -> None:
    """
    Long-running background task.
    Listens on Redis channel 'notifications' and fans out to local WebSocket connections.
    """
    while True:
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe("notifications")
            print("✅ Notification Pub/Sub listener started")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data       = json.loads(message["data"])
                    company_id = data.get("company_id")
                    staff_id   = data.get("staff_id")   # None = broadcast to whole company

                    if staff_id:
                        await handler.send_to_staff(company_id, staff_id, data)
                    elif company_id:
                        await handler.broadcast_to_company(company_id, data)

                except Exception as e:
                    print(f"❌ Notification pub/sub message error: {e}")

        except Exception as e:
            print(f"❌ Notification pub/sub connection error: {e}. Retrying in 3s...")
            await asyncio.sleep(3)


async def publish_notification(
    redis_client: redis.Redis,
    company_id: int,
    data: dict,
    staff_id: int | None = None,   # None = broadcast to whole company
) -> None:
    """Publish a notification to Redis."""
    payload = {**data, "company_id": company_id, "staff_id": staff_id}
    await redis_client.publish("notifications", json.dumps(payload, default=str))