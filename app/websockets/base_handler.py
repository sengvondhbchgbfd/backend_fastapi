import json
from abc import ABC, abstractmethod
from typing import Dict, Set
from fastapi import WebSocket


class BaseWebSocketHandler(ABC):
    """
    Generic WebSocket connection pool.
     Keyed by group_id → member_id → set of WebSocket connections
    (one member can open multiple tabs/devices).
    Subclass this and implement handle_message().
    """

    def __init__(self):
        # { group_id: { member_id: {WebSocket, ...} } }
        self.connections: Dict[int, Dict[int, Set[WebSocket]]] = {}
    # ── Lifecycle ─────────────────────────────────────────

    async def connect(self, websocket: WebSocket, group_id: int, member_id: int) -> None:
        await websocket.accept()
        self.connections.setdefault(group_id, {}).setdefault(member_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, group_id: int, member_id: int) -> None:
        group = self.connections.get(group_id, {})
        sockets = group.get(member_id, set())
        sockets.discard(websocket)
        if not sockets:
            group.pop(member_id, None)
        if not group:
            self.connections.pop(group_id, None)

    # ── Send helpers ──────────────────────────────────────

    async def send_to_member(self, group_id: int, member_id: int, data: dict) -> None:
        """Send to all sockets of one specific member in a group."""
        sockets = self.connections.get(group_id, {}).get(member_id, set())
        await self._send_to_sockets(sockets, data)

    async def broadcast_to_group(
        self,
        group_id: int,
        data: dict,
        exclude_member_id: int | None = None,
    ) -> None:
        """Broadcast to every member in a group, optionally skipping one."""
        dead: list[tuple[int, WebSocket]] = []

        for member_id, sockets in self.connections.get(group_id, {}).items():
            if exclude_member_id and member_id == exclude_member_id:
                continue
            for ws in sockets:
                try:
                    await ws.send_text(json.dumps(data, default=str))
                except Exception:
                    dead.append((member_id, ws))

        self._cleanup_dead(group_id, dead)

    async def broadcast_all(self, data: dict) -> None:
        """Broadcast to every connection across all groups."""
        for group_id in list(self.connections):
            await self.broadcast_to_group(group_id, data)

    # ── Presence ──────────────────────────────────────────

    def get_online_members(self, group_id: int) -> list[int]:
        return list(self.connections.get(group_id, {}).keys())

    def is_online(self, group_id: int, member_id: int) -> bool:
        return bool(self.connections.get(group_id, {}).get(member_id))

    # ── Abstract ──────────────────────────────────────────

    @abstractmethod
    async def handle_message(self, websocket: WebSocket, group_id: int, member_id: int, data: dict) -> None:
        """Called by the router for every inbound message from a client."""
        ...

    # ── Internal ──────────────────────────────────────────

    async def _send_to_sockets(self, sockets: Set[WebSocket], data: dict) -> None:
        dead = []
        for ws in sockets:
            try:
                await ws.send_text(json.dumps(data, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            sockets.discard(ws)

    def _cleanup_dead(self, group_id: int, dead: list[tuple[int, WebSocket]]) -> None:
        for member_id, ws in dead:
            self.connections.get(group_id, {}).get(member_id, set()).discard(ws)