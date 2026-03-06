"""
Module 5 – Risk Management

Two strategy variants with different stop-loss thresholds.
Tracks positions and enforces stop-loss / take-profit rules.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from config import (
    VARIANT_A_STOP_LOSS,
    VARIANT_B_STOP_LOSS,
    TAKE_PROFIT,
)
from strategy_engine import Signal


class Variant(str, Enum):
    A = "A"
    B = "B"


VARIANT_PARAMS: dict[Variant, dict] = {
    Variant.A: {"stop_loss": VARIANT_A_STOP_LOSS, "take_profit": TAKE_PROFIT},
    Variant.B: {"stop_loss": VARIANT_B_STOP_LOSS, "take_profit": TAKE_PROFIT},
}


@dataclass
class Position:
    symbol: str
    variant: Variant
    side: str            # "BUY" or "SELL"
    entry_price: float
    stop_loss: float     # absolute price level
    take_profit: float   # absolute price level
    current_price: float = 0.0

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        if self.side == "BUY":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        return (self.entry_price - self.current_price) / self.entry_price * 100

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "variant": self.variant.value,
            "side": self.side,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "pnl_pct": round(self.pnl_pct, 4),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }


class RiskManager:
    """Manages positions for both strategy variants."""

    def __init__(self) -> None:
        # key = (symbol, variant)
        self._positions: dict[tuple[str, Variant], Position] = {}
        self._lock = asyncio.Lock()

    async def open_position(
        self, symbol: str, variant: Variant, side: str, price: float
    ) -> Position:
        params = VARIANT_PARAMS[variant]
        sl_pct = params["stop_loss"]
        tp_pct = params["take_profit"]

        if side == "BUY":
            stop_loss = round(price * (1 - sl_pct), 2)
            take_profit = round(price * (1 + tp_pct), 2)
        else:
            stop_loss = round(price * (1 + sl_pct), 2)
            take_profit = round(price * (1 - tp_pct), 2)

        pos = Position(
            symbol=symbol,
            variant=variant,
            side=side,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            current_price=price,
        )
        async with self._lock:
            self._positions[(symbol, variant)] = pos
        return pos

    async def close_position(self, symbol: str, variant: Variant) -> Optional[Position]:
        async with self._lock:
            return self._positions.pop((symbol, variant), None)

    async def update_price(self, symbol: str, price: float) -> list[tuple[Position, str]]:
        """Update current price for all positions on this symbol.

        Returns list of (position, reason) for positions that should be closed.
        """
        to_close: list[tuple[Position, str]] = []
        async with self._lock:
            for key, pos in list(self._positions.items()):
                if pos.symbol != symbol:
                    continue
                pos.current_price = price

                if pos.side == "BUY":
                    if price <= pos.stop_loss:
                        to_close.append((pos, "stop_loss"))
                    elif price >= pos.take_profit:
                        to_close.append((pos, "take_profit"))
                else:
                    if price >= pos.stop_loss:
                        to_close.append((pos, "stop_loss"))
                    elif price <= pos.take_profit:
                        to_close.append((pos, "take_profit"))
        return to_close

    async def has_position(self, symbol: str, variant: Variant) -> bool:
        async with self._lock:
            return (symbol, variant) in self._positions

    async def get_all_positions(self) -> list[dict]:
        async with self._lock:
            return [p.to_dict() for p in self._positions.values()]

    async def should_open(
        self, symbol: str, variant: Variant, signal: Signal
    ) -> Optional[str]:
        """Returns the side ('BUY'/'SELL') if we should open, else None."""
        if signal == Signal.HOLD:
            return None
        if await self.has_position(symbol, variant):
            return None
        return signal.value
