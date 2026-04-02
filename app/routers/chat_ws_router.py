import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.websockets.chat_ws_manager import chat_ws_manager
from app.core.security import decode_access_token
from app.dependencies import get_db
from app.repositories.chat_repository import ChatRepository

chat_ws_router = APIRouter(tags=["Chat WebSocket"])


@chat_ws_router.websocket("/ws/chat/{group_id}")
async def chat_websocket(
    websocket: WebSocket,
    group_id:  int,
    token:     str          = Query(..., description="JWT access token"),
    db:        AsyncSession = Depends(get_db),
):
    """
    Real-time chat WebSocket per group.

    Connect with:
    ws://localhost:8000/ws/chat/{group_id}?token=<access_token>

    Events received:
    {
      "event":       "new_message",
      "message_id":  1,
      "group_id":    1,
      "sender_id":   2,
      "sender_name": "John Doe",
      "message_type":"text",
      "content":     "Hello team!",
      "created_at":  "2026-03-22 10:30:00"
    }

    {
      "event":      "message_deleted",
      "message_id": 1,
      "group_id":   1
    }

    {
      "event":    "members_added",
      "group_id": 1,
      "added":    [3, 4]
    }

    {
      "event":    "group_deleted",
      "group_id": 1
    }

    Send ping to keep alive:
    { "type": "ping" }
    Server responds: { "type": "pong" }
    """

    # 1. Verify JWT
    try:
        payload    = decode_access_token(token)
        user_id    = int(payload["sub"])
        company_id = payload["company_id"]
        staff_id   = payload.get("staff_id")

        if not staff_id:
            await websocket.close(code=4003, reason="Only staff can join chat.")
            return

    except Exception:
        await websocket.close(code=4001, reason="Invalid or expired token.")
        return

    # 2. Verify member of group
    try:
        repo   = ChatRepository(db)
        member = await repo.get_member(group_id, staff_id, company_id)
        if not member:
            await websocket.close(code=4003, reason="You are not a member of this group.")
            return
    except Exception:
        await websocket.close(code=4003, reason="Access denied.")
        return

    # 3. Register connection
    await chat_ws_manager.connect(websocket, group_id, staff_id)

    # 4. Notify group — user joined
    try:
        await chat_ws_manager.broadcast_to_group(
            group_id         = group_id,
            data             = {
                "event":    "user_online",
                "group_id": group_id,
                "staff_id": staff_id,
            },
            exclude_staff_id = staff_id,   # don't tell yourself
        )
    except Exception:
        pass

    # 5. Listen for ping/pong
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass

    except WebSocketDisconnect:
        chat_ws_manager.disconnect(websocket, group_id, staff_id)

        # Notify group — user went offline
        try:
            await chat_ws_manager.broadcast_to_group(
                group_id = group_id,
                data     = {
                    "event":    "user_offline",
                    "group_id": group_id,
                    "staff_id": staff_id,
                },
            )
        except Exception:
            pass