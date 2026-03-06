"""
Module 1 – Market Data Ingestion

Connects to the Binance Testnet WebSocket, subscribes to trade streams
for configured symbols, and forwards normalised ticks to the TickStore
and CandleAggregator.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from config import BINANCE_TESTNET_WS, SYMBOLS

logger = logging.getLogger(__name__)


class BinanceStreamClient:
    """Streams real-time trade data from Binance Testnet WebSocket."""

    def __init__(
        self,
        symbols: list[str] | None = None,
        on_tick: Optional[Callable] = None,
    ) -> None:
        self._symbols = [s.lower() for s in (symbols or SYMBOLS)]
        self._on_tick = on_tick
        self._running = False
        self._ws = None

    def _build_url(self) -> str:
        streams = "/".join(f"{s}@trade" for s in self._symbols)
        return f"{BINANCE_TESTNET_WS}/stream?streams={streams}"

    async def start(self) -> None:
        self._running = True
        url = self._build_url()
        logger.info("Connecting to %s", url)

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    self._ws = ws
                    logger.info("WebSocket connected")
                    await self._read_loop(ws)
            except ConnectionClosed as exc:
                logger.warning("WebSocket closed (%s), reconnecting in 3s…", exc)
            except Exception as exc:
                logger.error("WebSocket error: %s, reconnecting in 3s…", exc)
            if self._running:
                await asyncio.sleep(3)

    async def _read_loop(self, ws) -> None:
        async for raw in ws:
            try:
                msg = json.loads(raw)
                data = msg.get("data", msg)
                symbol = data.get("s", "").upper()
                price = float(data["p"])
                ts_ms = data["T"]  # trade time in epoch ms
                timestamp = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

                if self._on_tick:
                    await self._on_tick(symbol, price, timestamp)
            except (KeyError, ValueError, TypeError) as exc:
                logger.debug("Skipping malformed message: %s", exc)

    async def stop(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()
