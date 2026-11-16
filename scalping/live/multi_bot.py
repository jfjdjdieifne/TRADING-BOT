"""Multi-symbol session scalping bot — "scan every coin, trade only the
golden setups".

Design
------
* A ranked candidate list comes from `scanner.py` (ALL USDT-M futures symbols,
  filtered by 24h quote volume, ranked by volatility x confluence x session).
* One combined Binance websocket carries kline + aggTrade streams for those
  symbols, so every closed 5m bar of every candidate is evaluated in real time.
* Each symbol keeps its own causal history (ATR, swings, order blocks, sweeps,
  session opening ranges, confluence score). Nothing looks into the future.
* ONE position at a time across the whole account (a $100 account must not be
  levered into 8 correlated positions). Hard daily-loss and trades/day brakes.
* The symbol list is re-scanned every `--rescan-min` minutes by reconnecting.
* `paper_only=True` (default) never sends an order.

    python3 -m live.live_bot --mode paper --scan --top 8 --entry-mode momentum --market futures
    python3 -m live.live_bot --mode paper --symbols BTCUSDT,ETHUSDT,SOLUSDT --market futures
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scalping_engine.engine import (  # noqa: E402
    EngineConfig, ScalpingEngine, attach_indicators)
from scalping_engine.sessions import session_name  # noqa: E402
from strategy import (  # noqa: E402
    decide as momentum_decide, momentum_score, rank_symbols)

from .binance import BinanceClient  # noqa: E402

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                   "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]


def synthetic_frames(df: pd.DataFrame, symbols: list[str],
                     max_bars: int = 20000) -> dict[str, pd.DataFrame]:
    """Deterministic stand-in price paths for offline multi-symbol replay.

    Returns of the local BTC series are circularly shifted and re-scaled, so
    each "symbol" has a genuinely different path, volatility and price level,
    while OHLC ordering and session timestamps stay valid. These are NOT real
    coins — this exists only to exercise the multi-symbol loop offline.
    """
    base = df.tail(min(len(df), max_bars)).copy()
    close = base["Close"].to_numpy(float)
    lr = np.diff(np.log(close))
    lr = np.r_[0.0, lr]
    base_mean = float(lr.mean())            # preserve the source regime/drift
    rel_o = (base["Open"] / base["Close"]).to_numpy(float)
    rel_h = (base["High"] / base["Close"]).to_numpy(float)
    rel_l = (base["Low"] / base["Close"]).to_numpy(float)
    vol = base["Volume"].to_numpy(float)
    frames = {}
    for i, sym in enumerate(symbols):
        rr = np.roll(lr, 137 * i)
        rr = (rr - float(rr.mean()) + base_mean) * (0.85 + 0.12 * i)
        log_path = np.cumsum(np.clip(rr, -0.05, 0.05))
        level = 64000.0 / (1.0 + 3.0 * i)
        c = level * np.exp(log_path - log_path[0])
        frames[sym] = pd.DataFrame({
            "Open": c * rel_o, "High": c * rel_h, "Low": c * rel_l,
            "Close": c, "Volume": vol * (0.5 + 0.2 * i),
        }, index=base.index)
    return frames


def pick_symbols(top: int, min_volume_m: float, fallback: list[str]) -> list[str]:
    try:
        from scanner import scan
        rows = scan(top=top, min_volume=min_volume_m * 1e6)
        syms = [r["symbol"] for r in rows[:top]]
        if syms:
            return syms
    except Exception as e:  # noqa: BLE001
        print(f"[scan] market scan unavailable ({e}); using fallback symbols")
    return fallback[:top]


@dataclass
class Position:
    symbol: str
    side: int
    entry: float
    sl: float
    tp: float
    qty: float
    reason: str
    opened_ms: int
    risk: float = 0.0
    bars: int = 0
    be: bool = False


class SymbolState:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.hist = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        self.hist.index.name = "Datetime"
        self.tick_hi = np.nan
        self.tick_lo = np.nan
        self.last_quality = 0.0
        self.daily_close: pd.Series | None = None   # 210 closed daily bars
        self.daily_day = None


class MultiSymbolBot:
    def __init__(self, cfg: EngineConfig, symbols: list[str] | None = None,
                 interval="5m", paper_only=True, testnet=False, window=300,
                 market="futures", top=8, min_volume_m=20.0, rescan_min=30.0):
        self.cfg = cfg
        self.interval = interval
        self.paper_only = paper_only
        self.window = window
        self.top = top
        self.min_volume_m = min_volume_m
        self.rescan_sec = max(60.0, rescan_min * 60.0)
        self.fixed_symbols = symbols
        self.client = BinanceClient(testnet=testnet, paper_only=paper_only,
                                    market=market)
        # Signal generator only: we never call open_position, so engine.pos
        # stays None and positions are managed here (one global position).
        self.engine = ScalpingEngine(cfg)
        self.engine.equity = 100.0
        self.states: dict[str, SymbolState] = {}
        self.pos: Position | None = None
        self.day = None
        self.day_pnl = 0.0
        self.day_trades = 0
        self.paper_trades: list[dict] = []
        self.bars_seen = 0
        self.signals_seen = 0
        self._conf_last = 0.0
        self.symbols: list[str] = []
        self.quiet = False
        self.offline = False
        self.btc_daily: pd.Series | None = None

    # ------------------------------------------------------------------ #
    def _daily_series(self, symbol: str) -> pd.Series | None:
        """210 CLOSED daily bars — the trend/regime layer is a daily signal."""
        kl = self.client.klines(symbol, "1d", limit=210)
        if not kl:
            return None
        d = pd.DataFrame({
            "Datetime": [pd.Timestamp(k[0], unit="ms", tz="UTC") for k in kl],
            "Close": [float(k[4]) for k in kl],
        }).set_index("Datetime")["Close"]
        # last kline is still open -> drop it (no lookahead into today's close)
        return d.iloc[:-1] if len(d) > 2 else d

    def seed_all(self, symbols: list[str]):
        keep = set(symbols)
        for sym in list(self.states):
            if sym not in keep:
                del self.states[sym]
        try:
            self.btc_daily = self._daily_series("BTCUSDT")
        except Exception as e:  # noqa: BLE001
            print(f"[seed] BTC regime unavailable ({e}); gate defaults to risk-on")
        for sym in symbols:
            st = self.states.setdefault(sym, SymbolState(sym))
            if len(st.hist) < 60:
                kl = self.client.klines(sym, self.interval, limit=self.window)
                rows = [{
                    "Datetime": pd.Timestamp(k[0], unit="ms", tz="UTC"),
                    "Open": float(k[1]), "High": float(k[2]), "Low": float(k[3]),
                    "Close": float(k[4]), "Volume": float(k[5]),
                } for k in kl]
                st.hist = pd.DataFrame(rows).set_index("Datetime")
                print(f"[seed] {sym}: {len(st.hist)} {self.interval} bars")
            try:
                st.daily_close = self._daily_series(sym)
            except Exception as e:  # noqa: BLE001
                print(f"[seed] daily trend unavailable for {sym}: {e}")
        self.symbols = symbols

    # ------------------------------------------------------------------ #
    @staticmethod
    def _session_vwap(hist: pd.DataFrame) -> float:
        if hist.empty:
            return np.nan
        day = hist.index[-1].date()
        today = hist[hist.index.date == day]
        typical = (today["High"] + today["Low"] + today["Close"]) / 3.0
        v = today["Volume"]
        if float(v.sum()) > 0:
            return float((typical * v).sum() / v.sum())
        return float(typical.mean()) if len(typical) else np.nan

    def _bar_dict(self, st: SymbolState, bar) -> dict | None:
        hist = st.hist
        if len(hist) < 60:
            return None
        ind = attach_indicators(hist.iloc[-self.window:], self.cfg)
        t = len(hist) - 1
        return {
            "time": bar["time"], "open": bar["open"], "high": bar["high"],
            "low": bar["low"], "close": bar["close"], "volume": bar["volume"],
            "_atr": ind["atr"], "_swing": ind["swing"],
            "_htf_close": ind["htf_close"], "_htf_swing": ind["htf_swing"],
            "_ob": ind["ob"], "_fvg": ind["fvg"],
            "_sweeps": ind["sweeps"], "_candles": ind["candles"],
            "_disp": ind["disp"], "_sessions": ind["sessions"],
            "_confluence": ind["confluence"], "_htf_trend": ind["htf_trend"],
            "_t": t, "_vwap": self._session_vwap(hist.iloc[-self.window:]),
        }

    # ------------------------------------------------------------------ #
    def on_closed_bar(self, symbol: str, bar):
        st = self.states.get(symbol)
        if st is None:
            return
        ts = bar["time"]
        st.hist.loc[ts, ["Open", "High", "Low", "Close", "Volume"]] = [
            bar["open"], bar["high"], bar["low"], bar["close"], bar["volume"]]
        st.hist = st.hist[~st.hist.index.duplicated(keep="last")].sort_index()
        if len(st.hist) > self.window:
            st.hist = st.hist.iloc[-self.window:]
        st.tick_hi, st.tick_lo = np.nan, np.nan
        self.bars_seen += 1

        day = ts.date()
        if self.day != day:
            self.day, self.day_pnl, self.day_trades = day, 0.0, 0

        # manage the ONE open position on its own symbol's bars
        if self.pos is not None:
            if self.pos.symbol == symbol:
                self._manage(bar["high"], bar["low"], bar["close"], ts)
            return
        if self.day_trades >= self.cfg.max_trades_per_day:
            return
        if self.day_pnl <= -abs(self.engine.equity) * self.cfg.daily_loss_pct:
            return

        b = self._bar_dict(st, bar)
        if b is None:
            return
        self._conf_last = float(b["_confluence"][b["_t"]])
        if self.cfg.entry_mode == "momentum":
            sig = self._momentum_signal(symbol, st, b, ts)
        else:
            sig = self.engine.on_bar(b)
        if sig is not None:
            self.signals_seen += 1
            self._enter(sig, symbol, ts)

    # ------------------------------------------------------------------ #
    def _momentum_signal(self, symbol, st, b, ts):
        """MOMENTUM-X: rank ALL scanned coins, enter only the golden setup."""
        from types import SimpleNamespace
        scores = {s: momentum_score(x.hist) for s, x in self.states.items()}
        ranked = rank_symbols(scores)
        rank = ranked.index(symbol) + 1 if symbol in ranked else 10 ** 6
        ind = {"atr": b["_atr"], "htf_trend": b["_htf_trend"],
               "confluence": b["_confluence"], "disp": b["_disp"],
               "session_vwap": b["_vwap"]}
        v = momentum_decide(
            symbol=symbol, ts=ts, hist=st.hist, ind=ind, t=b["_t"],
            daily_close=st.daily_close, btc_daily=self.btc_daily,
            score_rank=rank, universe_size=len(self.states), cfg=self.cfg,
            daily_ok=(self.day_trades < self.cfg.max_trades_per_day
                      and self.day_pnl > -abs(self.engine.equity)
                      * self.cfg.daily_loss_pct))
        if not v.ok:
            return None
        if not self.quiet:
            print(f"[MOMENTUM-X] {symbol} rank={rank}/{len(self.states)} "
                  f"conf={self._conf_last:.2f} 12/12 conditions aligned")
        return SimpleNamespace(side=v.side, trigger=v.trigger, sl=v.sl,
                               reason=v.reason)

    # ------------------------------------------------------------------ #
    def _enter(self, sig, symbol: str, ts):
        side = sig.side
        entry = sig.trigger
        risk = (entry - sig.sl) if side == 1 else (sig.sl - entry)
        if risk <= 0:
            return
        qty = self.engine.equity * self.cfg.risk_pct / risk
        tp = entry + side * self.cfg.rr * risk
        self.pos = Position(symbol, side, entry, sig.sl, tp, qty, sig.reason,
                            int(time.time() * 1000), risk=risk)
        st = self.states.get(symbol)
        if st is not None:
            st.tick_hi, st.tick_lo = np.nan, np.nan   # only post-entry ticks count
        verb = "PAPER" if self.paper_only else "LIVE"
        if not self.quiet:
            print(f"[{verb}] OPEN {('LONG' if side == 1 else 'SHORT')} {symbol} "
                  f"@ {entry:.5f} sl={sig.sl:.5f} tp={tp:.5f} "
                  f"session={session_name(ts)} conf={self._conf_last:.2f} "
                  f"({sig.reason})")
        if not self.paper_only:
            try:
                self.client.place_market_order(symbol, "BUY" if side == 1 else "SELL", qty)
                self.client.place_stop_market(symbol, "SELL" if side == 1 else "BUY", qty, sig.sl)
                self.client.place_take_profit(symbol, "SELL" if side == 1 else "BUY", qty, tp)
            except Exception as e:  # noqa: BLE001
                print(f"[error] order failed: {e}")
                self.pos = None

    def _check_sl_tp(self, high, low, ts) -> bool:
        """Tick-safe: only SL/TP checks, no bar counting."""
        p = self.pos
        if p is None:
            return False
        exit_px, why = None, ""
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
            return False
        self._close_at(exit_px, why, ts)
        return True

    def _manage(self, high, low, close, ts):
        """One closed bar: SL/TP, then breakeven / max-holding-time exit."""
        p = self.pos
        if p is None:
            return
        if self._check_sl_tp(high, low, ts):
            return
        p.bars += 1
        if self.cfg.use_breakeven and not p.be and p.risk > 0:
            r = ((close - p.entry) if p.side == 1 else (p.entry - close)) / p.risk
            if r >= self.cfg.breakeven_at_r:
                p.sl = p.entry
                p.be = True
        if p.bars >= self.cfg.max_holding_bars:
            self._close_at(close, "time", ts)

    def _close_at(self, exit_px, why, ts):
        p = self.pos
        gross = (exit_px - p.entry) * p.qty * p.side
        ef = self.cfg.entry_fee_pct if self.cfg.entry_fee_pct is not None else self.cfg.fee_pct
        xf = self.cfg.exit_fee_pct if self.cfg.exit_fee_pct is not None else self.cfg.fee_pct
        fees = (p.entry * p.qty * ef + exit_px * p.qty * xf
                + (p.entry + exit_px) * p.qty * self.cfg.slippage_pct)
        pnl = gross - fees
        self.engine.equity += pnl
        self.day_pnl += pnl
        self.day_trades += 1
        verb = "PAPER" if self.paper_only else "LIVE"
        if not self.quiet:
            print(f"[{verb}] CLOSE {p.symbol} @ {exit_px:.5f} ({why}) "
                  f"pnl={pnl:+.2f} equity={self.engine.equity:.2f}")
        self.paper_trades.append({"exit": ts, "symbol": p.symbol, "pnl": pnl,
                                  "why": why, "reason": p.reason, "side": p.side,
                                  "entry": p.entry, "exit_px": exit_px})
        self.pos = None

    def on_tick(self, symbol: str, price: float, ts_ms: int):
        """Sub-second tick monitor for the symbol with the open position."""
        st = self.states.get(symbol)
        if st is None:
            return
        st.tick_hi = price if np.isnan(st.tick_hi) else max(st.tick_hi, price)
        st.tick_lo = price if np.isnan(st.tick_lo) else min(st.tick_lo, price)
        if self.pos is not None and self.pos.symbol == symbol:
            self._check_sl_tp(st.tick_hi, st.tick_lo,
                              pd.Timestamp(ts_ms, unit="ms", tz="UTC"))

    # ------------------------------------------------------------------ #
    async def _listen(self, ws):
        async for msg in ws:
            d = json.loads(msg)
            p = d.get("data", d)
            sym = (p.get("s") or d.get("stream", "").split("@")[0]).upper()
            if p.get("e") == "kline":
                k = p["k"]
                if k.get("x"):
                    self.on_closed_bar(sym, {
                        "time": pd.Timestamp(k["t"], unit="ms", tz="UTC"),
                        "open": float(k["o"]), "high": float(k["h"]),
                        "low": float(k["l"]), "close": float(k["c"]),
                        "volume": float(k["v"]),
                    })
            elif p.get("e") == "aggTrade":
                self.on_tick(sym, float(p["p"]), int(p["T"]))

    # ------------------------------------------------------------------ #
    # Offline launch / verification: replay the SAME multi-symbol loop on local
    # data so the whole pipeline can be run without keys or network.
    def replay(self, frames: dict[str, pd.DataFrame], bars: int = 1500,
               verbose: bool = True):
        self.quiet = not verbose
        self.offline = True
        for sym, df in frames.items():
            st = self.states.setdefault(sym, SymbolState(sym))
            st.hist = df.iloc[:-bars].copy()
            st.daily_close = df.iloc[:-bars]["Close"].resample("1D").last().dropna()
        self.btc_daily = self.states[next(iter(frames))].daily_close
        events = []
        for sym, df in frames.items():
            for ts, row in df.tail(bars).iterrows():
                events.append((ts, sym, row))
        events.sort(key=lambda e: (e[0], e[1]))
        for ts, sym, row in events:
            self.on_closed_bar(sym, {
                "time": ts, "open": float(row["Open"]), "high": float(row["High"]),
                "low": float(row["Low"]), "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            })
        self.quiet = False
        return self.summary()

    def summary(self) -> dict:
        t = self.paper_trades
        wins = sum(1 for x in t if x["pnl"] > 0)
        return {"bars": self.bars_seen, "signals": self.signals_seen,
                "trades": len(t), "wins": wins,
                "wr_pct": round(100 * wins / len(t), 1) if t else 0.0,
                "net_usd": round(sum(x["pnl"] for x in t), 2),
                "equity": round(self.engine.equity, 2)}

    async def run(self):
        import websockets
        while True:
            syms = self.fixed_symbols or pick_symbols(self.top, self.min_volume_m,
                                                      DEFAULT_SYMBOLS)
            print(f"[scan] watching {len(syms)} symbols: {', '.join(syms)}")
            try:
                self.seed_all(syms)
            except Exception as e:  # noqa: BLE001
                print(f"[seed] failed: {e}; retrying in 30s")
                await asyncio.sleep(30)
                continue
            streams = []
            for s in syms:
                streams.append(f"{s.lower()}@kline_{self.interval}")
                streams.append(f"{s.lower()}@aggTrade")
            url = f"{self.client.ws_url}/stream?streams={'/'.join(streams)}"
            try:
                async with websockets.connect(url, ping_interval=20,
                                              ping_timeout=20) as ws:
                    await asyncio.wait_for(self._listen(ws), timeout=self.rescan_sec)
                print(f"[scan] re-scanning after {self.rescan_sec/60:.0f} min "
                      f"(bars={self.bars_seen} signals={self.signals_seen})")
            except asyncio.TimeoutError:
                print(f"[scan] re-scanning (bars={self.bars_seen} "
                      f"signals={self.signals_seen})")
            except Exception as e:  # noqa: BLE001
                print(f"[ws] {e}; reconnecting in 10s")
                await asyncio.sleep(10)
