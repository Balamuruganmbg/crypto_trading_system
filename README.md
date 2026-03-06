# Crypto Trading System (Binance Testnet)

A real-time crypto trading system that:

* Streams live prices from **Binance Testnet**
* Aggregates ticks into **1-Minute OHLC candles**
* Runs an **EMA trading strategy**
* Executes **sample trades**
* Exposes data through **REST API and WebSocket**

---

# Run the Project

Install dependencies:

pip install -r requirements.txt

Start the system:

python main.py

Server will start at:

REST API
http://localhost:8000

WebSocket
ws://localhost:8765

API Docs
http://localhost:8000/docs

---
## Terminal Dashboard

![Terminal Dashboard](crypto_trading_system/Screenshot%202026-03-06%20102400.png)
# REST API Endpoints

### Latest Tick

http://localhost:8000/ticks/BTCUSDT

http://localhost:8000/ticks/ETHUSDT

Returns the latest price tick.

---

### Candle Data

http://localhost:8000/candles/BTCUSDT

http://localhost:8000/candles/ETHUSDT

Returns 1-Minute OHLC candle history.

Example fields:

* open
* high
* low
* close
* time
* tick_count

---

### Active Positions

http://localhost:8000/positions

Returns current strategy positions.

---

### Trade History

http://localhost:8000/trades

Returns executed trades.

---

# Strategy

EMA Crossover Strategy

Fast EMA = 9
Slow EMA = 21

Rules:

Fast EMA > Slow EMA → BUY
Fast EMA < Slow EMA → SELL
Else → HOLD

---

# Risk Variants

Variant A
Stop Loss: 15%

Variant B
Stop Loss: 10%

Take Profit: 20%

---

# Symbols

BTCUSDT
ETHUSDT

Can be changed in:

config.py

---

# Trade Log

All trades saved to:

trades.csv

---


