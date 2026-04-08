import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import redis.asyncio as redis
from app.core.config import settings


class ChatWebSocketManager:
    """
    Manages WebSocket connections per group.
    Multiple staff can be connected to the same group simultaneously.
    """

    def __init__(self):
        # { group_id: { staff_id: set of WebSocket connections } }
        self.connections: Dict[int, Dict[int, Set[WebSocket]]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        group_id:  int,
        staff_id:  int,
    ) -> None:
        await websocket.accept()
        if group_id not in self.connections:
            self.connections[group_id] = {}
        if staff_id not in self.connections[group_id]:
            self.connections[group_id][staff_id] = set()
        self.connections[group_id][staff_id].add(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        group_id:  int,
        staff_id:  int,
    ) -> None:
        if group_id in self.connections:
            if staff_id in self.connections[group_id]:
                self.connections[group_id][staff_id].discard(websocket)
                if not self.connections[group_id][staff_id]:
                    del self.connections[group_id][staff_id]
            if not self.connections[group_id]:
                del self.connections[group_id]

    async def broadcast_to_group(
        self,
        group_id: int,
        data:     dict,
        exclude_staff_id: int | None = None,
    ) -> None:
        """Send message to all members connected to this group."""
        if group_id not in self.connections:
            return

        dead = []
        for staff_id, sockets in self.connections[group_id].items():
            if exclude_staff_id and staff_id == exclude_staff_id:
                continue
            for ws in sockets:
                try:
                    await ws.send_text(json.dumps(data, default=str))
                except Exception:
                    dead.append((staff_id, ws))

        for staff_id, ws in dead:
            if group_id in self.connections:
                self.connections[group_id].get(staff_id, set()).discard(ws)






    def get_online_members(self, group_id: int) -> list[int]:
        """Return list of staff_ids currently connected to this group."""
        if group_id not in self.connections:
            return []
        return list(self.connections[group_id].keys())
    

# Global instance
chat_ws_manager = ChatWebSocketManager()


# ===========================================================================
# Redis Pub/Sub listener for chat
# ===========================================================================

async def start_chat_pubsub_listener() -> None:
    """
    Background task — listens to Redis channel 'chat'
    and broadcasts messages to connected WebSocket clients.
    """
    while True:
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                encoding         = "utf-8",
                decode_responses = True,
            )
            pubsub = client.pubsub()
            await pubsub.subscribe("chat")

            print("✅ Chat Pub/Sub listener started")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data     = json.loads(message["data"])
                    group_id = data.get("group_id")
                    if group_id:
                        await chat_ws_manager.broadcast_to_group(
                            group_id         = group_id,
                            data             = data,
                            exclude_staff_id = None,  # send to everyone including sender
                        )
                except Exception as e:
                    print(f"❌ Chat pub/sub error: {e}")

        except Exception as e:
            print(f"❌ Chat pub/sub connection error: {e}. Retrying in 3s...")
            await asyncio.sleep(3)


async def publish_chat_message(
    redis_client: redis.Redis,
    group_id:     int,
    data:         dict,
) -> None:
    """Publish chat message to Redis → all group members receive via WebSocket."""
    payload = {**data, "group_id": group_id}
    await redis_client.publish("chat", json.dumps(payload, default=str))