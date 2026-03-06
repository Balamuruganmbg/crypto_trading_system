"""
Module 4 – Trading Strategy

EMA crossover strategy with parameterizable fast/slow periods.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd

from candle_aggregator import Candle
from config import FAST_PERIOD, SLOW_PERIOD


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(slots=True)
class StrategyResult:
    signal: Signal
    fast_ema: float
    slow_ema: float


class StrategyEngine:
    """EMA crossover strategy: fast EMA crosses above slow → BUY, below → SELL."""

    def __init__(
        self,
        fast_period: int = FAST_PERIOD,
        slow_period: int = SLOW_PERIOD,
    ) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def evaluate(self, candles: list[Candle]) -> Optional[StrategyResult]:
        """Evaluate the strategy on a list of completed candles.

        Returns a StrategyResult with the current signal, or None if
        there aren't enough candles to compute both EMAs.
        """
        if len(candles) < self.slow_period + 1:
            return None

        closes = pd.Series([c.close for c in candles])
        fast_ema = closes.ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = closes.ewm(span=self.slow_period, adjust=False).mean()

        prev_fast = fast_ema.iloc[-2]
        prev_slow = slow_ema.iloc[-2]
        curr_fast = fast_ema.iloc[-1]
        curr_slow = slow_ema.iloc[-1]

        # Crossover detection
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            signal = Signal.BUY
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            signal = Signal.SELL
        else:
            signal = Signal.HOLD

        return StrategyResult(
            signal=signal,
            fast_ema=round(curr_fast, 4),
            slow_ema=round(curr_slow, 4),
        )
