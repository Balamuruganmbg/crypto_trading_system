"""
Central configuration for the crypto trading system.
All tunable parameters live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()


BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET: str = os.getenv("BINANCE_SECRET", "")
BINANCE_TESTNET_WS: str = "wss://stream.testnet.binance.vision"
BINANCE_TESTNET_REST: str = "https://testnet.binance.vision"

-
SYMBOLS: list[str] = ["BTCUSDT", "ETHUSDT"]


CANDLE_INTERVAL_SECONDS: int = 60  # 1 minute
MAX_CANDLE_HISTORY: int = 500      # rolling window per symbol


FAST_PERIOD: int = 9
SLOW_PERIOD: int = 21


VARIANT_A_STOP_LOSS: float = 0.15   
VARIANT_B_STOP_LOSS: float = 0.10  
TAKE_PROFIT: float = 0.20           


DEFAULT_ORDER_QTY: dict[str, float] = {
    "BTCUSDT": 0.001,
    "ETHUSDT": 0.01,
}


REST_HOST: str = "127.0.0.1"
REST_PORT: int = 8000
WS_HOST: str = "0.0.0.0"
WS_PORT: int = 8765

TRADE_LOG_FILE: str = "trades.csv"
