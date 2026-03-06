"""
Module 3 – 1-Minute Candle Aggregation

Aggregates incoming ticks into OHLC candles aligned to minute boundaries.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from config import CANDLE_INTERVAL_SECONDS, MAX_CANDLE_HISTORY


@dataclass(slots=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    time: str            # ISO-8601 UTC string for the candle open time
    tick_count: int = 0

    def to_dict(self) -> dict:
        return {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "time": self.time,
            "tick_count": self.tick_count,
        }


class CandleAggregator:
    """Builds 1-minute OHLC candles from raw ticks."""

    def __init__(self, max_history: int = MAX_CANDLE_HISTORY) -> None:
        # symbol -> deque of completed candles
        self._candles: dict[str, deque[Candle]] = {}
        # symbol -> in-progress candle
        self._current: dict[str, Candle] = {}
        # symbol -> minute bucket (floored timestamp)
        self._current_minute: dict[str, datetime] = {}
        self._max_history = max_history
        self._lock = asyncio.Lock()
        # callback fired when a candle closes
        self._on_candle_close: Optional[callable] = None

    def set_on_candle_close(self, callback: callable) -> None:
        self._on_candle_close = callback

    @staticmethod
    def _floor_minute(dt: datetime) -> datetime:
        return dt.replace(second=0, microsecond=0)

    async def on_tick(self, symbol: str, price: float, timestamp: datetime) -> Optional[Candle]:
        """Process a new tick. Returns a completed candle if one just closed."""
        minute = self._floor_minute(timestamp)
        closed_candle: Optional[Candle] = None

        async with self._lock:
            if symbol not in self._candles:
                self._candles[symbol] = deque(maxlen=self._max_history)

            current_minute = self._current_minute.get(symbol)

            # New minute bucket → close previous candle, start fresh
            if current_minute is not None and minute > current_minute:
                closed_candle = self._current.pop(symbol, None)
                if closed_candle is not None:
                    self._candles[symbol].append(closed_candle)

            if symbol not in self._current:
                # Start a new candle
                self._current[symbol] = Candle(
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    time=minute.isoformat(),
                    tick_count=1,
                )
                self._current_minute[symbol] = minute
            else:
                c = self._current[symbol]
                c.high = max(c.high, price)
                c.low = min(c.low, price)
                c.close = price
                c.tick_count += 1

        if closed_candle is not None and self._on_candle_close:
            await self._on_candle_close(symbol, closed_candle)

        return closed_candle

    async def get_candles(self, symbol: str) -> list[dict]:
        async with self._lock:
            result = [c.to_dict() for c in self._candles.get(symbol, [])]
            current = self._current.get(symbol)
            if current:
                result.append(current.to_dict())
            return result

    async def get_completed_candles(self, symbol: str) -> list[Candle]:
        async with self._lock:
            return list(self._candles.get(symbol, []))
