"""
Module 6 – Order Manager

Places sample MARKET orders on Binance Testnet via REST API.
Credentials are loaded from environment variables.
"""

from __future__ import annotations

import logging
from typing import Optional

from binance import AsyncClient, BinanceAPIException

from config import BINANCE_API_KEY, BINANCE_SECRET, BINANCE_TESTNET_REST, DEFAULT_ORDER_QTY

logger = logging.getLogger(__name__)


class OrderManager:
    """Thin wrapper around the Binance Testnet order API."""

    def __init__(self) -> None:
        self._client: Optional[AsyncClient] = None

    async def start(self) -> None:
        self._client = await AsyncClient.create(
            api_key=BINANCE_API_KEY,
            api_secret=BINANCE_SECRET,
            testnet=True,
        )
        logger.info("OrderManager connected to Binance Testnet")

    async def stop(self) -> None:
        if self._client:
            await self._client.close_connection()
            self._client = None

    async def place_market_order(
        self, symbol: str, side: str, quantity: Optional[float] = None
    ) -> dict:
        """Place a MARKET order on Binance Testnet.

        Args:
            symbol: e.g. 'BTCUSDT'
            side: 'BUY' or 'SELL'
            quantity: order size; defaults to DEFAULT_ORDER_QTY for the symbol
        """
        if self._client is None:
            raise RuntimeError("OrderManager not started – call start() first")

        qty = quantity or DEFAULT_ORDER_QTY.get(symbol, 0.001)

        try:
            order = await self._client.create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=qty,
            )
            logger.info("Order placed: %s %s %s qty=%s → %s", side, symbol, "MARKET", qty, order.get("orderId"))
            return order
        except BinanceAPIException as exc:
            logger.error("Order failed: %s", exc)
            return {"error": str(exc), "symbol": symbol, "side": side}
