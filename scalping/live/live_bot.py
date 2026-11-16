"""Live / paper / replay scalping bot.

Modes
-----
  replay : read local closed bars and run the exact live loop offline (no net).
  paper  : real Binance websocket market data, simulated orders (default).
  live   : real Binance websocket data + real signed orders (needs API keys and
           an explicit --live flag; testnet recommended first).

The bot is deliberately conservative: one position at a time, hard daily-loss
and trades-per-day circuit breakers, and it never sends an order unless
paper_only is false AND --live was passed.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scalping_engine.engine import (  # noqa: E402
    EngineConfig, ScalpingEngine, attach_indicators, simulate)
from scalping_engine.metrics import compute_metrics  # noqa: E402

from .binance import BinanceClient, stream_klines  # noqa: E402


# --------------------------------------------------------------------------- #
# Replay: validate the live loop on historical bars
# --------------------------------------------------------------------------- #
def replay(df: pd.DataFrame, cfg: EngineConfig, risk_pct: float = 0.01,
          verbose: bool = True):
    eng = ScalpingEngine(cfg)
    eng.equity = 100.0
    eng.hwm = 100.0
    o = df["Open"].to_numpy(float)
    h = df["High"].to_numpy(float)
    l = df["Low"].to_numpy(float)
    c = df["Close"].to_numpy(float)
    v = df["Volume"].to_numpy(float)
    times = df.index
    ind = attach_indicators(df, cfg)
    pending = None
    pending_bar = None
    for t in range(len(df)):
        bar = {
            "time": times[t], "open": o[t], "high": h[t], "low": l[t],
            "close": c[t], "volume": v[t],
            "_atr": ind["atr"], "_swing": ind["swing"],
            "_htf_close": ind["htf_close"], "_htf_swing": ind["htf_swing"],
            "_ob": ind["ob"], "_fvg": ind["fvg"],
            "_sweeps": ind["sweeps"], "_candles": ind["candles"],
            "_disp": ind["disp"],
        }
        if pending is not None and pending_bar == t:
            side = pending.side
            entry = o[t] * (1 + cfg.slippage_pct * side)
            risk = (entry - pending.sl) if side == 1 else (pending.sl - entry)
            if risk > 0:
                qty = eng.equity * cfg.risk_pct / risk
                eng.open_position(side, entry, pending.sl,
                                  entry + side * cfg.rr * risk, qty,
                                  eng.equity * cfg.risk_pct, pending.reason, times[t])
                if verbose:
                    print(f"  [{times[t]}] OPEN {('LONG' if side==1 else 'SHORT')} "
                          f"@ {entry:.2f}  sl={pending.sl:.2f}  ({pending.reason})")
            pending = None
        sig = eng.on_bar(bar)
        if sig is not None and eng.pos is None:
            pending, pending_bar = sig, t + 1
        elif eng.pos is not None:
            pending = None
        if verbose and eng.trades and len(eng.trades) % 25 == 0 and t % 200 == 0:
            pass
    if eng.pos is not None:
        eng._close(eng.pos, c[-1], times[-1], "eod")
    return eng


# --------------------------------------------------------------------------- #
# Live bot
# --------------------------------------------------------------------------- #
@dataclass
class Position:
    side: int
    entry: float
    sl: float
    tp: float
    qty: float
    reason: str
    opened_ms: int


class LiveBot:
    def __init__(self, cfg: EngineConfig, symbol="BTCUSDT", interval="5m",
                 paper_only=True, testnet=False, window=600):
        self.cfg = cfg
        self.symbol = symbol
        self.interval = interval
        self.paper_only = paper_only
        self.client = BinanceClient(testnet=testnet, paper_only=paper_only)
        self.window = window
        self.engine = ScalpingEngine(cfg)
        self.engine.equity = 100.0
        self.hist = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        self.hist.index.name = "Datetime"
        self.pos: Position | None = None
        self.day_pnl = 0.0
        self.day_trades = 0
        self.day = None
        self.last_bar_time = None
        self.tick_hi = np.nan
        self.tick_lo = np.nan
        self.paper_trades = []

    # ------------------------------------------------------------------ #
    def seed_history(self):
        kl = self.client.klines(self.symbol, self.interval, limit=self.window)
        rows = []
        for k in kl:
            rows.append({
                "Datetime": pd.Timestamp(k[0], unit="ms", tz="UTC"),
                "Open": float(k[1]), "High": float(k[2]),
                "Low": float(k[3]), "Close": float(k[4]), "Volume": float(k[5]),
            })
        self.hist = pd.DataFrame(rows).set_index("Datetime")
        print(f"[seed] {len(self.hist)} {self.interval} bars "
              f"{self.hist.index[0]} .. {self.hist.index[-1]}")

    def _indicators(self):
        if len(self.hist) < 30:
            return None
        return attach_indicators(self.hist.iloc[-self.window:], self.cfg)

    # ------------------------------------------------------------------ #
    def on_closed_bar(self, bar):
        ts = bar["time"]
        self.hist.loc[ts, ["Open", "High", "Low", "Close", "Volume"]] = [
            bar["open"], bar["high"], bar["low"], bar["close"], bar["volume"]]
        self.hist = self.hist[~self.hist.index.duplicated(keep="last")].sort_index()
        if len(self.hist) > self.window:
            self.hist = self.hist.iloc[-self.window:]

        ind = self._indicators()
        if ind is None:
            return
        t = len(self.hist) - 1
        day = ts.date()
        if self.day != day:
            self.day, self.day_pnl, self.day_trades = day, 0.0, 0
        b = {
            "time": ts, "open": bar["open"], "high": bar["high"],
            "low": bar["low"], "close": bar["close"], "volume": bar["volume"],
            "_atr": ind["atr"], "_swing": ind["swing"],
            "_htf_close": ind["htf_close"], "_htf_swing": ind["htf_swing"],
            "_ob": ind["ob"], "_fvg": ind["fvg"],
            "_sweeps": ind["sweeps"], "_candles": ind["candles"],
            "_disp": ind["disp"],
        }
        # manage open position on this closed bar
        if self.pos is not None:
            self._manage(bar["high"], bar["low"], bar["close"], ts)
        if self.pos is not None:
            return
        if self.day_trades >= self.cfg.max_trades_per_day:
            return
        if self.day_pnl <= -abs(self.engine.equity) * self.cfg.daily_loss_pct:
            print(f"[risk] daily loss brake hit ({self.day_pnl:.2f}); no new trades today")
            return
        sig = self.engine.on_bar(b)
        if sig is not None:
            self._enter(sig, ts)

    # ------------------------------------------------------------------ #
    def _enter(self, sig, ts):
        side = sig.side
        # paper fills at the signal close; live fills at market with slippage
        entry = sig.trigger
        risk = (entry - sig.sl) if side == 1 else (sig.sl - entry)
        if risk <= 0:
            return
        qty = self.engine.equity * self.cfg.risk_pct / risk
        tp = entry + side * self.cfg.rr * risk
        self.pos = Position(side, entry, sig.sl, tp, qty, sig.reason, int(time.time() * 1000))
        verb = "PAPER" if self.paper_only else "LIVE"
        print(f"[{verb}] OPEN {('LONG' if side==1 else 'SHORT')} {self.symbol} "
              f"{qty:.6f} @ {entry:.2f}  sl={sig.sl:.2f} tp={tp:.2f}  ({sig.reason})")
        if not self.paper_only:
            try:
                self.client.place_market_order(self.symbol,
                                               "BUY" if side == 1 else "SELL", qty)
                self.client.place_stop_market(self.symbol,
                                              "SELL" if side == 1 else "BUY", qty, sig.sl)
                self.client.place_take_profit(self.symbol,
                                              "SELL" if side == 1 else "BUY", qty, tp)
            except Exception as e:  # noqa: BLE001
                print(f"[error] order failed: {e}")
                self.pos = None

    def _manage(self, high, low, close, ts):
        p = self.pos
        exit_px = None
        why = ""
        if p.side == 1:
            if low <= p.sl:
                exit_px, why = p.sl, "sl"
            elif high >= p.tp:
                exit_px, why = p.tp, "tp"
        else:
            if high >= p.sl:
                exit_px, why = p.sl, "sl"
            elif low <= p.tp:
                exit_px, why = p.tp, "tp"
        if exit_px is None:
            return
        gross = (exit_px - p.entry) * p.qty * p.side
        fees = (p.entry * p.qty + exit_px * p.qty) * self.cfg.fee_pct
        pnl = gross - fees
        self.engine.equity += pnl
        self.day_pnl += pnl
        self.day_trades += 1
        verb = "PAPER" if self.paper_only else "LIVE"
        print(f"[{verb}] CLOSE {('LONG' if p.side==1 else 'SHORT')} @ {exit_px:.2f} "
              f"({why})  pnl={pnl:+.2f}  equity={self.engine.equity:.2f}")
        self.paper_trades.append({"exit": ts, "pnl": pnl, "why": why,
                                  "reason": p.reason, "side": p.side,
                                  "entry": p.entry, "exit_px": exit_px})
        self.pos = None

    # ------------------------------------------------------------------ #
    def on_tick(self, price, ts_ms):
        """Sub-second tick monitor: fast sweep/reclaim trigger + position check."""
        self.tick_hi = price if np.isnan(self.tick_hi) else max(self.tick_hi, price)
        self.tick_lo = price if np.isnan(self.tick_lo) else min(self.tick_lo, price)
        if self.pos is not None:
            self._manage(self.tick_hi, self.tick_lo, price,
                         pd.Timestamp(ts_ms, unit="ms", tz="UTC"))
            return
        # real-time sweep detection against the last closed bar's swing level
        if len(self.hist) < 30:
            return
        ind = self._indicators()
        if ind is None:
            return
        t = len(self.hist) - 1
        sh = ind["swing"].high[t]
        sl = ind["swing"].low[t]
        atr = ind["atr"][t]
        if np.isnan(atr) or atr <= 0:
            return
        # price took out the swing high and is now back below it -> bull sweep
        if (not np.isnan(sh) and self.tick_hi > sh and price < sh
                and self.engine.pos is None and self.day_trades < self.cfg.max_trades_per_day):
            print(f"[tick] bull sweep @ {price:.2f} (level {sh:.2f})")
        if (not np.isnan(sl) and self.tick_lo < sl and price > sl
                and self.engine.pos is None and self.day_trades < self.cfg.max_trades_per_day):
            print(f"[tick] bear sweep @ {price:.2f} (level {sl:.2f})")

    # ------------------------------------------------------------------ #
    async def run(self):
        self.seed_history()
        loop = asyncio.get_event_loop()
        state = {"kline": None}

        def on_kline(bar):
            state["kline"] = bar

        def on_aggtrade(price, ts):
            self.on_tick(price, ts)

        # run the stream; on each closed kline bar, run the bar logic
        import websockets
        base = self.client.ws_url
        streams = f"{self.symbol.lower()}@kline_{self.interval}/{self.symbol.lower()}@aggTrade"
        url = f"{base}/stream?streams={streams}"
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
            async for msg in ws:
                data = json.loads(msg)
                p = data.get("data", data)
                if p.get("e") == "kline" and p["k"].get("x"):
                    self.on_closed_bar({
                        "time": pd.Timestamp(p["k"]["t"], unit="ms", tz="UTC"),
                        "open": float(p["k"]["o"]), "high": float(p["k"]["h"]),
                        "low": float(p["k"]["l"]), "close": float(p["k"]["c"]),
                        "volume": float(p["k"]["v"]),
                    })
                elif p.get("e") == "aggTrade":
                    self.on_tick(float(p["p"]), int(p["T"]))


import json  # noqa: E402


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["replay", "paper", "live"], default="replay")
    ap.add_argument("--asset", choices=["btc5m", "xau1m", "nsx1m"], default="btc5m")
    ap.add_argument("--years", type=int, nargs="*", default=[2026])
    ap.add_argument("--months", nargs="*", default=None)
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="5m")
    ap.add_argument("--entry-mode", default="combo")
    ap.add_argument("--rr", type=float, default=1.5)
    ap.add_argument("--sl-atr", type=float, default=0.5)
    ap.add_argument("--max-bars", type=int, default=12)
    ap.add_argument("--risk", type=float, default=0.01)
    ap.add_argument("--testnet", action="store_true")
    ap.add_argument("--window", type=int, default=600)
    a = ap.parse_args()

    cfg = EngineConfig(entry_mode=a.entry_mode, rr=a.rr, risk_pct=a.risk,
                       sl_atr_mult=a.sl_atr, max_holding_bars=a.max_bars)

    if a.mode == "replay":
        from scalping_engine import data
        if a.asset == "btc5m":
            df = data.load_btc_5m(a.years)
        elif a.asset == "xau1m":
            df = data.load_xau_1m(a.months)
        else:
            df = data.load_nsx_1m(a.months)
        eng = replay(df, cfg, a.risk)
        m = compute_metrics(eng.trades, initial_equity=100.0)
        print("=" * 70)
        print(f"REPLAY {a.asset}  N={m['n']}  WR={m['wr_pct']:.1f}%  "
              f"PF={m['pf']:.3f}  net={m['net_r']:.2f}R  DD={m['max_dd_pct']:.1f}%")
        print("reasons:", m["reasons"], "exits:", m["exits"])
        return

    if not a.testnet and not os.environ.get("BINANCE_API_KEY"):
        print("Refusing to connect without BINANCE_API_KEY (use --testnet or set keys).")
        return
    bot = LiveBot(cfg, symbol=a.symbol, interval=a.interval,
                  paper_only=(a.mode != "live"), testnet=a.testnet, window=a.window)
    print(f"[bot] mode={a.mode} symbol={a.symbol} interval={a.interval} "
          f"paper_only={bot.paper_only} entry_mode={a.entry_mode}")
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
