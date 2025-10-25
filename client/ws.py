import asyncio
import json
from typing import Any, Callable, Dict, Optional

import websockets


class WSClient:
    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self.token: Optional[str] = None
        self._conn: Optional[websockets.WebSocketClientProtocol] = None
        self._recv_task: Optional[asyncio.Task] = None
        self.on_received: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_token(self, token: str) -> None:
        self.token = token

    async def connect(self) -> None:
        self._conn = await websockets.connect(self.ws_url)
        assert self.token
        await self._conn.send(json.dumps({"type": "auth", "token": self.token}))
        if self._recv_task is None:
            self._recv_task = asyncio.create_task(self._recv_loop())

    async def _recv_loop(self) -> None:
        assert self._conn
        try:
            async for message in self._conn:
                data = json.loads(message)
                if self.on_received:
                    self.on_received(data)
        finally:
            self._conn = None

    async def send_message(self, to_user_id: int, body: str) -> None:
        if not self._conn:
            raise RuntimeError("WebSocket not connected")
        await self._conn.send(
            json.dumps({"type": "send", "to_user_id": to_user_id, "body": body})
        )
