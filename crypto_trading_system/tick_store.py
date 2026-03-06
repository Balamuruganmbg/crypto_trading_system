"""
Module 2 – Tick Store

Thread-safe in-memory store for the latest tick per symbol.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(slots=True)
class Tick:
    symbol: str
    price: float
    timestamp: datetime


class TickStore:
    """Maintains the most recent tick for every tracked symbol."""

    def __init__(self) -> None:
        self._ticks: dict[str, Tick] = {}
        self._lock = asyncio.Lock()

    async def update(self, symbol: str, price: float, timestamp: datetime) -> Tick:
        tick = Tick(symbol=symbol, price=price, timestamp=timestamp)
        async with self._lock:
            self._ticks[symbol] = tick
        return tick

    async def get(self, symbol: str) -> Optional[Tick]:
        async with self._lock:
            return self._ticks.get(symbol)

    async def get_all(self) -> dict[str, Tick]:
        async with self._lock:
            return dict(self._ticks)

    def get_sync(self, symbol: str) -> Optional[Tick]:
        return self._ticks.get(symbol)

    def to_dict(self, symbol: str) -> Optional[dict]:
        tick = self._ticks.get(symbol)
        if tick is None:
            return None
        return {
            "symbol": tick.symbol,
            "price": tick.price,
            "timestamp": tick.timestamp.isoformat(),
        }
