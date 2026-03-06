"""
Module 7 – Trade Logger

Appends trade records to a CSV file and keeps an in-memory log.
"""

from __future__ import annotations

import asyncio
import csv
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from config import TRADE_LOG_FILE

FIELDNAMES = ["timestamp", "symbol", "side", "size", "price", "strategy_variant"]


@dataclass(slots=True)
class TradeRecord:
    timestamp: str
    symbol: str
    side: str
    size: float
    price: float
    strategy_variant: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "symbol": self.symbol,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "strategy_variant": self.strategy_variant,
        }


class TradeLogger:
    def __init__(self, file_path: str = TRADE_LOG_FILE) -> None:
        self._file_path = file_path
        self._trades: list[TradeRecord] = []
        self._lock = asyncio.Lock()
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not os.path.exists(self._file_path):
            with open(self._file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writeheader()

    async def log_trade(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float,
        strategy_variant: str,
    ) -> TradeRecord:
        record = TradeRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            strategy_variant=strategy_variant,
        )
        async with self._lock:
            self._trades.append(record)
            with open(self._file_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                writer.writerow(record.to_dict())
        return record

    async def get_trades(self, symbol: Optional[str] = None) -> list[dict]:
        async with self._lock:
            trades = self._trades if symbol is None else [
                t for t in self._trades if t.symbol == symbol
            ]
            return [t.to_dict() for t in trades]
