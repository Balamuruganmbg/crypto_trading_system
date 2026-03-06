"""
Module 9 – WebSocket Server

Broadcasts candle updates to connected clients in real time.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from config import WS_HOST, WS_PORT

logger = logging.getLogger(__name__)


class WebSocketServer:
    """Simple pub-sub WebSocket server for candle updates."""

    def __init__(self, host: str = WS_HOST, port: int = WS_PORT) -> None:
        self._host = host
        self._port = port
        self._clients: Set[WebSocketServerProtocol] = set()
        self._server = None

    async def start(self) -> None:
        self._server = await websockets.serve(
            self._handler, self._host, self._port
        )
        logger.info("WebSocket server listening on ws://%s:%s", self._host, self._port)

    async def _handler(self, ws: WebSocketServerProtocol, path: str = "/") -> None:
        self._clients.add(ws)
        logger.info("Client connected (%d total)", len(self._clients))
        try:
            async for _ in ws:
                pass  # we only broadcast, ignore incoming
        finally:
            self._clients.discard(ws)
            logger.info("Client disconnected (%d total)", len(self._clients))

    async def broadcast_candle(self, symbol: str, candle_dict: dict) -> None:
        if not self._clients:
            return
        payload = json.dumps({"symbol": symbol, **candle_dict})
        dead: list[WebSocketServerProtocol] = []
        for client in self._clients:
            try:
                await client.send(payload)
            except Exception:
                dead.append(client)
        for c in dead:
            self._clients.discard(c)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
