"""
Gold Trading Agent - Terminal UI
Run: python tui.py [--port 8000]
Connects to the backend API and displays live trading data.
"""

import asyncio
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual.widgets import (
    Header, Footer, Static, Label, DataTable, Log, Rule
)
from textual.timer import Timer
from textual import work


# ─── colour helpers ──────────────────────────────────────────────────────────

def _pct_color(v: Optional[float], neutral: float = 0.0) -> str:
    if v is None:
        return "dim"
    return "green" if v > neutral else "red" if v < neutral else "yellow"


def _signal_color(sig_type: str) -> str:
    t = sig_type.upper()
    if "BUY" in t:
        return "green"
    if "SELL" in t:
        return "red"
    return "yellow"


def _rsi_label(v: Optional[float]) -> str:
    if v is None:
        return "[dim]--[/]"
    color = "red" if v >= 70 else "green" if v <= 30 else "yellow"
    tag = " OB" if v >= 70 else " OS" if v <= 30 else ""
    return f"[{color}]{v:.1f}{tag}[/]"


def _fmt(v: Optional[float], decimals: int = 2, prefix: str = "") -> str:
    if v is None:
        return "[dim]--[/]"
    return f"{prefix}{v:,.{decimals}f}"


# ─── widgets ─────────────────────────────────────────────────────────────────

class PricePanel(Static):
    """Big price display."""

    DEFAULT_CSS = """
    PricePanel {
        border: round $accent;
        padding: 0 1;
        height: 7;
    }
    """

    data: reactive[Optional[Dict]] = reactive(None)

    def render(self) -> str:
        d = self.data
        if d is None:
            return "[dim]Waiting for price data…[/]"
        bid = d.get("bid", 0)
        ask = d.get("ask", 0)
        spread = (ask - bid) * 10  # pips for gold
        sym = d.get("symbol", "XAUUSD")
        ts = d.get("timestamp", "")[:19].replace("T", " ")
        hi = d.get("high", 0)
        lo = d.get("low", 0)
        op = d.get("open", 0)
        chg = bid - op
        chg_color = "green" if chg >= 0 else "red"
        sign = "+" if chg >= 0 else ""
        return (
            f"[bold yellow]{sym}[/]  [dim]{ts}[/]\n\n"
            f"[bold green]BID [white]{bid:,.2f}[/][/]   "
            f"[bold red]ASK [white]{ask:,.2f}[/][/]   "
            f"[dim]Spread {spread:.1f}pts[/]\n\n"
            f"[dim]Open[/] {op:,.2f}   "
            f"[dim]H[/] [green]{hi:,.2f}[/]   "
            f"[dim]L[/] [red]{lo:,.2f}[/]   "
            f"[{chg_color}]{sign}{chg:,.2f}[/]"
        )


class SignalPanel(Static):
    """Latest trading signal."""

    DEFAULT_CSS = """
    SignalPanel {
        border: round $accent;
        padding: 0 1;
        height: 10;
    }
    """

    data: reactive[Optional[Dict]] = reactive(None)

    def render(self) -> str:
        d = self.data
        if d is None:
            return "[dim]No signal yet[/]"
        sig_type = d.get("type", "HOLD")
        color = _signal_color(sig_type)
        conf = d.get("confidence", 0) * 100
        strength = d.get("strength", 0) * 100
        price = d.get("price", 0)
        sl = d.get("suggested_sl")
        tp = d.get("suggested_tp")
        reasons = d.get("reasons", [])
        ts = (d.get("timestamp", "")[:19] or "").replace("T", " ")

        sl_str = f"[red]{sl:,.2f}[/]" if sl else "[dim]--[/]"
        tp_str = f"[green]{tp:,.2f}[/]" if tp else "[dim]--[/]"

        reason_lines = "\n".join(f"  [dim]•[/] {r}" for r in reasons[:4])
        return (
            f"[bold {color}]◉ {sig_type}[/]  [dim]{ts}[/]\n\n"
            f"[dim]Price[/] {price:,.2f}   "
            f"[dim]Conf[/] [yellow]{conf:.0f}%[/]   "
            f"[dim]Strength[/] [cyan]{strength:.0f}%[/]\n\n"
            f"[dim]SL[/] {sl_str}   [dim]TP[/] {tp_str}\n\n"
            f"{reason_lines}"
        )


class IndicatorPanel(Static):
    """Technical indicators."""

    DEFAULT_CSS = """
    IndicatorPanel {
        border: round $accent;
        padding: 0 1;
        height: 10;
    }
    """

    data: reactive[Optional[Dict]] = reactive(None)

    def render(self) -> str:
        d = self.data
        if d is None:
            return "[dim]Waiting for indicators…[/]"

        ema9 = d.get("ema_9")
        ema21 = d.get("ema_21")
        sma50 = d.get("sma_50")
        macd = d.get("macd")
        macd_h = d.get("macd_histogram")
        rsi = d.get("rsi_14")
        bb_upper = d.get("bb_upper")
        bb_lower = d.get("bb_lower")
        bb_pct = d.get("bb_percent")
        atr = d.get("atr_14")
        trend = d.get("trend", "NEUTRAL")
        sig_strength = d.get("signal_strength", 0) * 100

        trend_color = "green" if "UP" in trend.upper() else "red" if "DOWN" in trend.upper() else "yellow"
        macd_color = _pct_color(macd)
        macd_h_color = _pct_color(macd_h)

        ema_cross = ""
        if ema9 and ema21:
            ema_cross = "[green]EMA 9 > 21 ↑[/]" if ema9 > ema21 else "[red]EMA 9 < 21 ↓[/]"

        return (
            f"[bold]Trend[/] [{trend_color}]{trend}[/]   [dim]Sig.[/] [cyan]{sig_strength:.0f}%[/]\n\n"
            f"[dim]EMA[/] 9={_fmt(ema9)}  21={_fmt(ema21)}  50={_fmt(sma50)}   {ema_cross}\n\n"
            f"[dim]MACD[/] [{macd_color}]{_fmt(macd, 4)}[/]  "
            f"[dim]Hist[/] [{macd_h_color}]{_fmt(macd_h, 4)}[/]\n\n"
            f"[dim]RSI(14)[/] {_rsi_label(rsi)}   "
            f"[dim]ATR[/] {_fmt(atr, 2)}\n\n"
            f"[dim]BB[/] [{bb_pct and _pct_color(bb_pct - 0.5) or 'dim'}]"
            f"{_fmt(bb_pct, 2)}[/]  "
            f"[dim]↑[/]{_fmt(bb_upper)}  [dim]↓[/]{_fmt(bb_lower)}"
        )


class AccountPanel(Static):
    """Account summary."""

    DEFAULT_CSS = """
    AccountPanel {
        border: round $accent;
        padding: 0 1;
        height: 7;
    }
    """

    data: reactive[Optional[Dict]] = reactive(None)

    def render(self) -> str:
        d = self.data
        if d is None:
            return "[dim]No account data[/]"
        balance = d.get("balance", 0)
        equity = d.get("equity", 0)
        margin = d.get("margin", 0)
        free_margin = d.get("free_margin", 0)
        profit = d.get("profit", 0)
        p_color = _pct_color(profit)
        p_sign = "+" if profit >= 0 else ""
        currency = d.get("currency", "USD")
        leverage = d.get("leverage", 0)
        return (
            f"[dim]Balance[/]  [bold]{currency} {balance:,.2f}[/]\n\n"
            f"[dim]Equity[/]   {equity:,.2f}   "
            f"[dim]P/L[/] [{p_color}]{p_sign}{profit:,.2f}[/]\n\n"
            f"[dim]Margin[/]   {margin:,.2f}   "
            f"[dim]Free[/] {free_margin:,.2f}   "
            f"[dim]Lev[/] 1:{leverage}"
        )


class StatusBar(Static):
    """Connection + system status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        padding: 0 1;
    }
    """

    status: reactive[str] = reactive("[dim]Connecting…[/]")

    def render(self) -> str:
        return self.status


# ─── main app ────────────────────────────────────────────────────────────────

class GoldTradingTUI(App):
    """Gold Trading Agent — Terminal UI"""

    TITLE = "Gold Trading Agent"
    SUB_TITLE = "XAUUSD Live Dashboard"

    CSS = """
    Screen {
        layout: vertical;
    }
    #top-row {
        layout: horizontal;
        height: auto;
    }
    #mid-row {
        layout: horizontal;
        height: auto;
    }
    PricePanel { width: 2fr; }
    SignalPanel { width: 1fr; }
    IndicatorPanel { width: 1fr; }
    AccountPanel { width: 1fr; }
    #positions-panel {
        border: round $accent;
        height: auto;
        min-height: 6;
        max-height: 14;
        padding: 0 1;
    }
    #positions-label {
        color: $text-muted;
    }
    #log-panel {
        border: round $accent;
        height: 8;
        padding: 0 1;
    }
    DataTable {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh now"),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self._refresh_timer: Optional[Timer] = None
        self._client: Optional[httpx.AsyncClient] = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="top-row"):
                yield PricePanel(id="price")
                yield AccountPanel(id="account")
            with Horizontal(id="mid-row"):
                yield SignalPanel(id="signal")
                yield IndicatorPanel(id="indicators")
            with Container(id="positions-panel"):
                yield Label("Open Positions", id="positions-label")
                yield DataTable(id="positions-table", show_cursor=False)
            with Container(id="log-panel"):
                yield Log(id="event-log", max_lines=100)
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        # Configure positions table
        table = self.query_one("#positions-table", DataTable)
        table.add_columns("Ticket", "Symbol", "Type", "Lots", "Open", "Current", "SL", "TP", "P/L")

        self._client = httpx.AsyncClient(timeout=5.0)
        self._log("TUI started — connecting to backend…")
        self._refresh_timer = self.set_interval(3, self._do_refresh)
        self._do_refresh()

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.aclose()

    def _log(self, msg: str) -> None:
        log = self.query_one("#event-log", Log)
        ts = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{ts}] {msg}")

    async def _fetch(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            r = await self._client.get(f"{self.base_url}/api{path}")
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    @work(exclusive=True)
    async def _do_refresh(self) -> None:
        status_bar = self.query_one("#status-bar", StatusBar)

        # Fetch all endpoints in parallel
        price, indicators, signal, account, positions, dash = await asyncio.gather(
            self._fetch("/price"),
            self._fetch("/indicators"),
            self._fetch("/signal"),
            self._fetch("/account"),
            self._fetch("/positions"),
            self._fetch("/status"),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        price      = price      if isinstance(price, dict)      else None
        indicators = indicators if isinstance(indicators, dict) else None
        signal     = signal     if isinstance(signal, dict)     else None
        account    = account    if isinstance(account, dict)    else None
        positions  = positions  if isinstance(positions, list)  else []
        dash       = dash       if isinstance(dash, dict)       else None

        # Update panels
        self.query_one("#price", PricePanel).data = price
        self.query_one("#signal", SignalPanel).data = signal
        self.query_one("#indicators", IndicatorPanel).data = indicators
        self.query_one("#account", AccountPanel).data = account

        # Update positions table
        table = self.query_one("#positions-table", DataTable)
        table.clear()
        if positions:
            for p in positions:
                profit = p.get("profit", 0)
                p_str = f"+{profit:.2f}" if profit >= 0 else f"{profit:.2f}"
                table.add_row(
                    str(p.get("ticket", "")),
                    p.get("symbol", ""),
                    p.get("type", ""),
                    str(p.get("volume", "")),
                    f"{p.get('open_price', 0):,.2f}",
                    f"{p.get('current_price', 0):,.2f}",
                    f"{p.get('sl', 0):,.2f}" if p.get("sl") else "--",
                    f"{p.get('tp', 0):,.2f}" if p.get("tp") else "--",
                    p_str,
                )

        # Status bar
        ts = datetime.now().strftime("%H:%M:%S")
        if dash:
            provider = dash.get("data_provider", "?")
            trading = "ON" if dash.get("trading_enabled") else "OFF"
            conn = "✓ Connected" if dash.get("is_connected") else "✗ Disconnected"
            status_bar.status = (
                f"[green]{conn}[/]  [dim]|[/]  Provider: [cyan]{provider}[/]  "
                f"[dim]|[/]  Trading: [yellow]{trading}[/]  "
                f"[dim]|[/]  Updated: {ts}  [dim]|[/]  [dim]R=refresh  Q=quit[/]"
            )
            self._log(f"Refreshed — price={price and price.get('bid', '?')}  signal={signal and signal.get('type', '?')}")
        else:
            status_bar.status = (
                f"[red]✗ Backend unreachable[/]  [dim]{self.base_url}[/]  {ts}"
            )
            self._log("Backend unreachable — is the server running?")

    def action_refresh(self) -> None:
        self._log("Manual refresh…")
        self._do_refresh()


# ─── entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gold Trading Agent TUI")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--host", default="localhost", help="Backend host (default: localhost)")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    GoldTradingTUI(base_url=url).run()


if __name__ == "__main__":
    main()
