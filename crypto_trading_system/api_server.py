"""
Module 8 – REST API

FastAPI application exposing candles, ticks, positions, and trade history.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

# These will be injected at startup by main.py
app = FastAPI(title="Crypto Trading System", version="1.0.0")

# Module references – set by main.py before the server starts
_tick_store = None
_candle_aggregator = None
_risk_manager = None
_trade_logger = None


def init(tick_store, candle_aggregator, risk_manager, trade_logger) -> None:
    global _tick_store, _candle_aggregator, _risk_manager, _trade_logger
    _tick_store = tick_store
    _candle_aggregator = candle_aggregator
    _risk_manager = risk_manager
    _trade_logger = trade_logger


@app.get("/candles/{symbol}")
async def get_candles(symbol: str):
    symbol = symbol.upper()
    candles = await _candle_aggregator.get_candles(symbol)
    return {"symbol": symbol, "count": len(candles), "candles": candles}


@app.get("/ticks/{symbol}")
async def get_ticks(symbol: str):
    symbol = symbol.upper()
    tick = _tick_store.to_dict(symbol)
    if tick is None:
        raise HTTPException(status_code=404, detail=f"No tick data for {symbol}")
    return tick


@app.get("/positions")
async def get_positions():
    positions = await _risk_manager.get_all_positions()
    return {"count": len(positions), "positions": positions}


@app.get("/trades")
async def get_trades():
    trades = await _trade_logger.get_trades()
    return {"count": len(trades), "trades": trades}
