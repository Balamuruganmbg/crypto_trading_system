"""
Module 10 – Main Application

Orchestrates all subsystems: market data ingestion, candle aggregation,
strategy evaluation, risk management, order execution, trade logging,
REST API, and WebSocket broadcasting.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import uvicorn

from binance_stream_client import BinanceStreamClient
from tick_store import TickStore
from candle_aggregator import CandleAggregator, Candle
from strategy_engine import StrategyEngine, Signal
from risk_manager import RiskManager, Variant
from order_manager import OrderManager
from trade_logger import TradeLogger
from websocket_server import WebSocketServer
import api_server
from config import SYMBOLS, DEFAULT_ORDER_QTY, REST_HOST, REST_PORT

import terminal_dashboard
from rich.live import Live

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("system.log")],
)
logger = logging.getLogger("main")

# ── Shared instances ──────────────────────────────────────────────
tick_store = TickStore()
candle_aggregator = CandleAggregator()
strategy_engine = StrategyEngine()
risk_manager = RiskManager()
order_manager = OrderManager()
trade_logger = TradeLogger()
ws_server = WebSocketServer()


# ── Tick handler (called by BinanceStreamClient) ──────────────────
async def on_tick(symbol: str, price: float, timestamp):
    """Process every incoming tick through the pipeline."""
    # 1. Update tick store
    await tick_store.update(symbol, price, timestamp)

    # Dashboard update: Market data
    terminal_dashboard.update_market_data(symbol, price)

    # 2. Feed into candle aggregator
    closed_candle = await candle_aggregator.on_tick(symbol, price, timestamp)

    # 3. If a candle just closed, evaluate strategy & manage risk
    if closed_candle is not None:
        await on_candle_close(symbol, closed_candle)

    # 4. Check stop-loss / take-profit on every tick
    exits = await risk_manager.update_price(symbol, price)
    for pos, reason in exits:
        close_side = "SELL" if pos.side == "BUY" else "BUY"
        logger.info(
            "Risk exit (%s) for %s variant %s @ %.2f",
            reason, symbol, pos.variant.value, price,
        )
        await order_manager.place_market_order(symbol, close_side)
        await risk_manager.close_position(symbol, pos.variant)
        await trade_logger.log_trade(
            symbol=symbol,
            side=close_side,
            size=DEFAULT_ORDER_QTY.get(symbol, 0.001),
            price=price,
            strategy_variant=pos.variant.value,
        )

    # Update dashboard dynamic data
    positions = await risk_manager.get_all_positions()
    terminal_dashboard.update_position(symbol, [p for p in positions if p["symbol"] == symbol])


async def on_candle_close(symbol: str, candle: Candle):
    """Called when a 1-minute candle closes."""
    logger.info(
        "Candle closed: %s O=%.2f H=%.2f L=%.2f C=%.2f",
        symbol, candle.open, candle.high, candle.low, candle.close,
    )

    # Broadcast to WebSocket clients
    await ws_server.broadcast_candle(symbol, candle.to_dict())

    # Update dashboard candle data
    terminal_dashboard.update_candle(symbol, candle)

    # Evaluate strategy
    completed = await candle_aggregator.get_completed_candles(symbol)
    result = strategy_engine.evaluate(completed)
    if result is None:
        return

    logger.info(
        "Strategy %s: fast_ema=%.2f slow_ema=%.2f signal=%s",
        symbol, result.fast_ema, result.slow_ema, result.signal.value,
    )

    terminal_dashboard.update_signal(symbol, result)

    if result.signal == Signal.HOLD:
        return

    # Run both variants
    for variant in (Variant.A, Variant.B):
        side = await risk_manager.should_open(symbol, variant, result.signal)
        if side is None:
            continue
        price = candle.close
        qty = DEFAULT_ORDER_QTY.get(symbol, 0.001)

        logger.info("Opening %s %s variant %s @ %.2f", side, symbol, variant.value, price)
        await order_manager.place_market_order(symbol, side, qty)
        await risk_manager.open_position(symbol, variant, side, price)
        await trade_logger.log_trade(
            symbol=symbol,
            side=side,
            size=qty,
            price=price,
            strategy_variant=variant.value,
        )

    positions = await risk_manager.get_all_positions()
    terminal_dashboard.update_position(symbol, [p for p in positions if p["symbol"] == symbol])


# ── Startup ───────────────────────────────────────────────────────
async def main():
    logger.info("Starting Crypto Trading System…")

    # Wire up REST API with shared state
    api_server.init(tick_store, candle_aggregator, risk_manager, trade_logger)

    # Start order manager (Binance REST client)
    await order_manager.start()

    # Start WebSocket broadcast server
    await ws_server.start()

    # Start Binance stream
    stream_client = BinanceStreamClient(symbols=SYMBOLS, on_tick=on_tick)

    # Start REST API server (non-blocking)
    config = uvicorn.Config(
        api_server.app,
        host=REST_HOST,
        port=REST_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    logger.info("System ready – streaming %s", SYMBOLS)

    terminal_dashboard.show_banner(SYMBOLS, REST_HOST, REST_PORT)
    layout = terminal_dashboard.create_dashboard_layout()

    try:
        with Live(terminal_dashboard.generate_renderable(layout), get_renderable=lambda: terminal_dashboard.generate_renderable(layout), refresh_per_second=4, screen=True):
            await asyncio.gather(
                stream_client.start(),
                server.serve(),
            )
    except KeyboardInterrupt:
        logger.info("Shutting down…")
    finally:
        await stream_client.stop()
        await order_manager.stop()
        await ws_server.stop()


if __name__ == "__main__":
    asyncio.run(main())
