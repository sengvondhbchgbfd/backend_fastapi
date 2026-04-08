import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import redis.asyncio as redis
from app.core.config import settings



class WebSocketManager:
    """
    Manages active WebSocket connections per user.
    One user can have multiple connections (phone + browser).
    """
    def __init__(self):
        # { user_id: set of WebSocket connections }
        self.connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:

        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        if user_id in self.connections:
            self.connections[user_id].discard(websocket)
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Push notification to all connections of a user."""
        if user_id not in self.connections:
            return
        dead = set()
        for ws in self.connections[user_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.add(ws)
        # cleanup dead connections
        for ws in dead:
            self.connections[user_id].discard(ws)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections and bool(self.connections[user_id])

    def online_users(self) -> list[int]:
        return list(self.connections.keys())
# Global instance — shared across all requests
ws_manager = WebSocketManager()
# ===========================================================================
# Redis Pub/Sub listener
# Runs in background — listens for published notifications
# and pushes to connected WebSocket clients
# ===========================================================================

async def start_redis_pubsub_listener() -> None:
    """
    Background task started on app startup.
    Subscribes to Redis channel 'notifications'
    Pushes to WebSocket when message received.
    """
    while True:
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                encoding        = "utf-8",
                decode_responses = True,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe("notifications")

            print("✅ Redis Pub/Sub listener started")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data    = json.loads(message["data"])
                    user_id = data.get("user_id")

                    if user_id and ws_manager.is_online(user_id):
                        await ws_manager.send_to_user(user_id, data)

                except Exception as e:
                    print(f"❌ Pub/Sub message error: {e}")

        except Exception as e:
            print(f"❌ Redis Pub/Sub connection error: {e}. Retrying in 3s...")
            await asyncio.sleep(3)   # retry on disconnect

# ===========================================================================
# Publish helper — called from notification_service.send()
# ===========================================================================

async def publish_notification(
    redis_client: redis.Redis,
    user_id:      int,
    data:         dict,
) -> None:
    """
    Publish notification to Redis channel.
    Redis Pub/Sub listener picks it up and pushes to WebSocket.
    """
    payload = {**data, "user_id": user_id}
    await redis_client.publish("notifications", json.dumps(payload, default=str))