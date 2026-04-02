import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.websockets.ws_manager import ws_manager
from app.core.security import decode_access_token
from app.dependencies import get_db
from app.repositories.notifications_repository import NotificationRepository
from app.services.notifications_service import NotificationService

ws_router = APIRouter(tags=["WebSocket"])

# ws://localhost:8000/ws/notifications?token=<access_token>
@ws_router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token:     str          = Query(..., description="JWT access token"),
    db:        AsyncSession = Depends(get_db),
):
    """
    Real-time notification WebSocket.

    Connect with:
    ws://localhost:8000/ws/notifications?token=<access_token>

    Events received:
    {
      "event":           "new_notification",
      "notification_id": 1,
      "user_id":         3,
      "title":           "Leave approved",
      "message":         "Your leave has been approved.",
      "type":            "success",
      "is_read":         false,
      "reference_id":    5,
      "reference_type":  "leave_request",
      "created_at":      "2026-03-22 10:30:00"
    }

    Send ping to keep alive:
    { "type": "ping" }

    Server responds with:
    { "type": "pong" }
    """

    # 1. Verify JWT token
    try:
        payload = decode_access_token(token)
        user_id    = int(payload["sub"])
        company_id = payload["company_id"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid or expired token.")
        return
    # 2. Register connection
    await ws_manager.connect(websocket, user_id)
    # 3. Send unread count on connect
    try:
        repo    = NotificationRepository(db)
        summary = await repo.get_summary(user_id, company_id)
        await websocket.send_text(json.dumps({
            "event":  "connected",
            "user_id": user_id,
            "unread": summary["unread"],
            "total":  summary["total"],
        }))
    except Exception:
        pass

    # 4. Listen for client messages (ping/pong)
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
        ws_manager.disconnect(websocket, user_id)