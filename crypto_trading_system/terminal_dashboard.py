"""
Terminal Dashboard using rich.
"""

from typing import Any, Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

console = Console()

# Internal State
market_data: Dict[str, float] = {}
candle_data: Dict[str, Any] = {}
strategy_data: Dict[str, Any] = {}
position_data: Dict[str, List[Any]] = {}

def create_dashboard_layout() -> Layout:
    layout = Layout(name="root")
    layout.split(
        Layout(name="main_split", ratio=1)
    )
    layout["main_split"].split_row(
        Layout(name="left_pane", ratio=1),
        Layout(name="right_pane", ratio=1)
    )
    layout["left_pane"].split_column(
        Layout(name="market_data", ratio=1),
        Layout(name="strategy_status", ratio=1)
    )
    layout["right_pane"].split_column(
        Layout(name="candle_data", ratio=1),
        Layout(name="position_status", ratio=1)
    )
    return layout

def update_market_data(symbol: str, price: float):
    market_data[symbol] = price

def update_candle(symbol: str, candle: Any):
    candle_data[symbol] = candle

def update_signal(symbol: str, signal: Any):
    strategy_data[symbol] = signal

def update_position(symbol: str, position: List[Any]):
    position_data[symbol] = position

def _generate_market_table() -> Table:
    table = Table(expand=True)
    table.add_column("Symbol", style="white")
    table.add_column("Price", justify="right", style="cyan")
    for sym, price in sorted(market_data.items()):
        table.add_row(sym, f"{price:.2f}")
    return table

def _generate_candle_table() -> Table:
    table = Table(expand=True)
    table.add_column("Symbol", style="white")
    table.add_column("Time", style="white")
    table.add_column("Open", style="cyan")
    table.add_column("High", style="cyan")
    table.add_column("Low", style="cyan")
    table.add_column("Close", style="cyan")
    table.add_column("Tick Count", justify="right")
    
    for sym, candle in sorted(candle_data.items()):
        if isinstance(candle, dict):
            time_str = str(candle.get("time", ""))
            open_p, high_p = candle.get("open", 0.0), candle.get("high", 0.0)
            low_p, close_p = candle.get("low", 0.0), candle.get("close", 0.0)
            ticks = candle.get("tick_count", 0)
        else:
            time_str = str(getattr(candle, "time", ""))
            open_p, high_p = getattr(candle, "open", 0.0), getattr(candle, "high", 0.0)
            low_p, close_p = getattr(candle, "low", 0.0), getattr(candle, "close", 0.0)
            ticks = getattr(candle, "tick_count", 0)
            
        if "T" in time_str:
            time_str = time_str.split("T")[-1].split("+")[0][:8]
            
        table.add_row(
            sym, time_str,
            f"{open_p:.2f}",
            f"{high_p:.2f}",
            f"{low_p:.2f}",
            f"{close_p:.2f}",
            str(ticks)
        )
    return table

def _generate_strategy_table() -> Table:
    table = Table(expand=True)
    table.add_column("Symbol", style="white")
    table.add_column("Fast EMA", style="cyan")
    table.add_column("Slow EMA", style="cyan")
    table.add_column("Signal")
    
    for sym, res in sorted(strategy_data.items()):
        if isinstance(res, dict):
            sig = res.get("signal", "HOLD")
            if hasattr(sig, "value"):
                sig = sig.value
        else:
            sig = res.signal.value if hasattr(res, "signal") and hasattr(res.signal, "value") else getattr(res, "signal", "HOLD")
                
        sig_text = Text(str(sig))
        if sig == "BUY":
            sig_text.stylize("bold green")
        elif sig == "SELL":
            sig_text.stylize("bold red")
        elif sig == "HOLD":
            sig_text.stylize("bold yellow")
            
        if isinstance(res, dict):
            fast_ema = res.get("fast_ema", 0.0)
            slow_ema = res.get("slow_ema", 0.0)
        else:
            fast_ema = getattr(res, "fast_ema", 0.0)
            slow_ema = getattr(res, "slow_ema", 0.0)
            
        table.add_row(
            sym, f"{fast_ema:.2f}", f"{slow_ema:.2f}", sig_text
        )
    return table

def _generate_position_table() -> Table:
    table = Table(expand=True)
    table.add_column("Symbol", style="white")
    table.add_column("Variant", style="white")
    table.add_column("Side")
    table.add_column("Entry Price", style="cyan")
    table.add_column("PnL %")
    
    for sym, positions in sorted(position_data.items()):
        for pos in positions:
            if isinstance(pos, dict):
                p_sym = pos.get("symbol", sym)
                variant = pos.get("variant", "")
                side = pos.get("side", "")
                entry = pos.get("entry_price", 0.0)
                pnl = pos.get("pnl_pct", 0.0)
            else:
                p_sym = getattr(pos, "symbol", sym)
                var_obj = getattr(pos, "variant", "")
                variant = var_obj.value if hasattr(var_obj, "value") else str(var_obj)
                side = getattr(pos, "side", "")
                entry = getattr(pos, "entry_price", 0.0)
                pnl = getattr(pos, "pnl_pct", 0.0)
            
            side_text = Text(str(side))
            if side == "BUY":
                side_text.stylize("bold green")
            elif side == "SELL":
                side_text.stylize("bold red")
                
            pnl_text = Text(f"{pnl:.2f}%")
            if pnl > 0:
                pnl_text.stylize("bold green")
            elif pnl < 0:
                pnl_text.stylize("bold red")
                
            table.add_row(p_sym, variant, side_text, f"{entry:.2f}", pnl_text)
            
    return table

def generate_renderable(layout: Layout) -> Layout:
    layout["market_data"].update(Panel(_generate_market_table(), title="MARKET DATA", border_style="bright_blue"))
    layout["strategy_status"].update(Panel(_generate_strategy_table(), title="STRATEGY STATUS", border_style="bright_blue"))
    layout["candle_data"].update(Panel(_generate_candle_table(), title="CANDLE DATA", border_style="bright_blue"))
    layout["position_status"].update(Panel(_generate_position_table(), title="POSITION STATUS", border_style="bright_blue"))
    return layout

def show_banner(symbols: List[str], rest_host: str, rest_port: int, ws_port: int = 8765):
    sym_str = ", ".join(symbols)
    host = "localhost" if rest_host in ("0.0.0.0", "127.0.0.1") else rest_host
    banner = f"Crypto Trading System v1.0\nConnected to Binance Testnet\nStreaming symbols: {sym_str}\nREST API: http://{host}:{rest_port}\nWebSocket: ws://{host}:{ws_port}"
    console.print(Panel(banner, title="Startup", border_style="green", expand=False))
