"""Causal 1m/5m scalping engine.

The engine is a bar-level state machine. It emits *signals* on a closed bar and
leaves execution (intrabar SL/TP, costs, sizing) to the simulator / live bot so
the same signal logic is tested and traded.

Signal stack (all causal, see primitives.py):
  * HTF bias from a higher-timeframe causal swing break.
  * Liquidity sweep (takeout of a confirmed swing + rejection close).
  * Order-block / FVG confluence at the sweep level.
  * Candlestick confirmation (engulfing / pin bar).
  * VWAP mean-reversion pullback (optional).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class EngineConfig:
    # structure
    k_swing: int = 2
    atr_len: int = 14
    htf_rule: str = "1h"          # bias timeframe (for a 5m LTF)
    # entries
    entry_mode: str = "combo"     # sweep | ob | vwap | bos | reclaim | combo
    rr: float = 1.5
    sl_atr_mult: float = 0.5      # buffer beyond sweep extreme / OB edge
    sl_min_atr: float = 0.5       # never tighter than this (ATR units)
    require_candle_confirm: bool = True
    require_htf_align: bool = True
    killzone: tuple = (7, 16)     # UTC hours inclusive
    # trade management
    max_holding_bars: int = 12
    use_breakeven: bool = True
    breakeven_at_r: float = 1.0
    # risk / costs
    risk_pct: float = 0.01
    fee_pct: float = 0.00075      # per side default (Binance taker w/ BNB)
    entry_fee_pct: float | None = None   # None -> fee_pct; use 0.0002 for maker limit entries
    exit_fee_pct: float | None = None
    slippage_pct: float = 0.0002
    max_trades_per_day: int = 6
    daily_loss_pct: float = 0.03
    # vwap / mean-reversion mode
    vwap_z_max: float = 2.0
    vwap_pullback_r: float = 0.5
    mr_z: float = 2.0                # ATR deviation from session mean for mr mode


@dataclass
class Signal:
    bar_idx: int
    time: pd.Timestamp
    side: int
    reason: str
    trigger: float
    sl: float
    atr: float
    htf_trend: int


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: int
    entry_price: float
    exit_price: float
    sl: float
    tp: float
    qty: float
    risk_usd: float
    pnl: float
    pnl_r: float
    fees: float
    reason: str
    exit_reason: str
    bars_held: int


class ScalpingEngine:
    """Bar-level causal signal generator + position manager."""

    def __init__(self, config: EngineConfig | None = None):
        self.cfg = config or EngineConfig()
        self.reset()

    def reset(self):
        c = self.cfg
        self.n = 0
        self.atr = None
        self.swing = None
        self.htf_close = None
        self.htf_swing = None
        self.ob_list: list = []
        self.fvg_list: list = []
        self.cum_pv = 0.0
        self.cum_v = 0.0
        self.cum_tp = 0.0
        self.cum_n = 0
        self.vwap = np.nan
        self.last_day = None
        self.equity = 0.0
        self.hwm = 0.0
        self.day = None
        self.day_pnl = 0.0
        self.day_trades = 0
        self.pos: Optional[dict] = None
        self.trades: list[Trade] = []

    # ------------------------------------------------------------------ #
    def _htf_bias(self, t: int) -> int:
        """+1/-1/0 from the higher-timeframe causal swing break at bar t."""
        if self.htf_swing is None or t >= len(self.htf_close):
            return 0
        sh = self.htf_swing.high[t]
        sl = self.htf_swing.low[t]
        c = self.htf_close[t]
        if np.isnan(sh) or np.isnan(sl):
            return 0
        if c > sh:
            return 1
        if c < sl:
            return -1
        return 0

    def _in_killzone(self, ts: pd.Timestamp) -> bool:
        lo, hi = self.cfg.killzone
        return lo <= ts.hour <= hi

    # ------------------------------------------------------------------ #
    def on_bar(self, bar: dict) -> Optional[Signal]:
        """Consume one *closed* bar. Returns a Signal or None.

        bar keys: time, open, high, low, close, volume (and optional htf arrays
        attached by the simulator).
        """
        c = self.cfg
        t = self.n
        self.n += 1
        ts = bar["time"]
        o, h, l, cl, v = (float(bar["open"]), float(bar["high"]),
                          float(bar["low"]), float(bar["close"]), float(bar["volume"]))

        # session VWAP
        day = ts.date() if hasattr(ts, "date") else None
        typical = (h + l + cl) / 3.0
        if day != self.last_day:
            self.cum_pv, self.cum_v = typical * v, v
            self.cum_tp, self.cum_n = typical, 1
            self.last_day = day
        else:
            self.cum_pv += typical * v
            self.cum_v += v
            self.cum_tp += typical
            self.cum_n += 1
        # volume-weighted when volume exists, else equal-weighted typical mean
        self.vwap = (self.cum_pv / self.cum_v) if self.cum_v > 0 else (self.cum_tp / self.cum_n)

        # attach precomputed arrays
        self.atr = bar["_atr"]
        self.swing = bar["_swing"]
        self.htf_close = bar["_htf_close"]
        self.htf_swing = bar["_htf_swing"]
        self.ob_list = bar["_ob"]
        self.fvg_list = bar["_fvg"]
        self._disp = bar["_disp"]
        self._bar_idx = t

        # ---------------- position management (on this closed bar) ------- #
        if self.pos is not None:
            self._manage_position(bar)

        # ---------------- new signal ------------------------------------- #
        if self.pos is not None:
            return None
        if not self._in_killzone(ts):
            return None
        if self.day != day:
            self.day, self.day_pnl, self.day_trades = day, 0.0, 0
        if self.day_trades >= c.max_trades_per_day:
            return None
        if self.day_pnl <= -abs(self.equity) * c.daily_loss_pct:
            return None

        htf = self._htf_bias(t)
        if c.require_htf_align and htf == 0:
            return None

        bull_sweep, bear_sweep = bar["_sweeps"]
        bull_c, bear_c = bar["_candles"]
        atr_now = self.atr[t] if t < len(self.atr) and not np.isnan(self.atr[t]) else np.nan
        if np.isnan(atr_now) or atr_now <= 0:
            return None

        side = 0
        reason = ""
        trigger = cl
        sl = np.nan

        # 1) liquidity sweep reversal
        if c.entry_mode in ("sweep", "combo"):
            if bull_sweep[t] and (htf == 1 or not c.require_htf_align):
                if (not c.require_candle_confirm) or bull_c[t]:
                    side, reason = 1, "sweep_bull"
                    sl = min(l, self.swing.low[t]) - c.sl_atr_mult * atr_now
                    trigger = cl
            elif bear_sweep[t] and (htf == -1 or not c.require_htf_align):
                if (not c.require_candle_confirm) or bear_c[t]:
                    side, reason = -1, "sweep_bear"
                    sl = max(h, self.swing.high[t]) + c.sl_atr_mult * atr_now
                    trigger = cl

        # 1b) break-of-structure continuation (displacement through a level)
        if side == 0 and c.entry_mode in ("bos", "combo"):
            sh = self.swing.high[t]
            slo = self.swing.low[t]
            disp = bool(self._disp[t]) if t < len(self._disp) else False
            if disp and not np.isnan(sh) and cl > sh and (htf == 1 or not c.require_htf_align):
                side, reason = 1, "bos_bull"
                sl = min(l, slo) - c.sl_atr_mult * atr_now if not np.isnan(slo) else l - c.sl_atr_mult * atr_now
                trigger = cl
            elif disp and not np.isnan(slo) and cl < slo and (htf == -1 or not c.require_htf_align):
                side, reason = -1, "bos_bear"
                sl = max(h, sh) + c.sl_atr_mult * atr_now if not np.isnan(sh) else h + c.sl_atr_mult * atr_now
                trigger = cl

        # 1c) sweep-and-reclaim continuation (hunt then close back beyond level)
        if side == 0 and c.entry_mode in ("reclaim", "combo") and t >= 1:
            prev = t - 1
            bull_prev, bear_prev = bar["_sweeps"][0][prev], bar["_sweeps"][1][prev]
            lvl_hi = self.swing.high[prev]
            lvl_lo = self.swing.low[prev]
            if bull_prev and not np.isnan(lvl_hi) and cl > lvl_hi and (htf == 1 or not c.require_htf_align):
                side, reason = 1, "reclaim_bull"
                sl = min(l, self.swing.low[prev]) - c.sl_atr_mult * atr_now
                trigger = cl
            elif bear_prev and not np.isnan(lvl_lo) and cl < lvl_lo and (htf == -1 or not c.require_htf_align):
                side, reason = -1, "reclaim_bear"
                sl = max(h, self.swing.high[prev]) + c.sl_atr_mult * atr_now
                trigger = cl

        # 2) order-block mitigation
        if side == 0 and c.entry_mode in ("ob", "combo"):
            for ob in self.ob_list:
                if ob.mitigated or ob.impulse_idx >= t:
                    continue
                if t - ob.impulse_idx > 24:
                    continue
                if ob.side == 1 and htf in (0, 1):
                    if l <= ob.top and cl > ob.bottom and (not c.require_candle_confirm or bull_c[t]):
                        side, reason = 1, "ob_bull"
                        sl = ob.bottom - c.sl_atr_mult * atr_now
                        trigger = cl
                        break
                if ob.side == -1 and htf in (0, -1):
                    if h >= ob.bottom and cl < ob.top and (not c.require_candle_confirm or bear_c[t]):
                        side, reason = -1, "ob_bear"
                        sl = ob.top + c.sl_atr_mult * atr_now
                        trigger = cl
                        break

        # 3) VWAP / session-mean pullback with reversal confirmation
        if side == 0 and c.entry_mode in ("vwap", "combo") and not np.isnan(self.vwap):
            if (cl > self.vwap and htf in (0, 1) and l <= self.vwap
                    and (not c.require_candle_confirm or bull_c[t])):
                side, reason = 1, "vwap_pullback_bull"
                sl = l - c.sl_atr_mult * atr_now
                trigger = cl
            elif (cl < self.vwap and htf in (0, -1) and h >= self.vwap
                  and (not c.require_candle_confirm or bear_c[t])):
                side, reason = -1, "vwap_pullback_bear"
                sl = h + c.sl_atr_mult * atr_now
                trigger = cl

        # 4) extreme deviation mean-reversion (counter-trend, session mean)
        if side == 0 and c.entry_mode in ("mr", "combo") and not np.isnan(self.vwap):
            dev = (cl - self.vwap) / atr_now
            if dev >= c.mr_z and bear_c[t]:
                side, reason = -1, "mr_bear"
                sl = h + c.sl_atr_mult * atr_now
                trigger = cl
            elif dev <= -c.mr_z and bull_c[t]:
                side, reason = 1, "mr_bull"
                sl = l - c.sl_atr_mult * atr_now
                trigger = cl

        if side == 0 or np.isnan(sl):
            return None
        risk = (trigger - sl) if side == 1 else (sl - trigger)
        floor = max(c.sl_min_atr * atr_now, 1e-9)
        if risk < floor:
            sl = (trigger - floor) if side == 1 else (trigger + floor)
            risk = floor
        tp = trigger + side * c.rr * risk
        return Signal(t, ts, side, reason, trigger, sl, atr_now, htf)

    # ------------------------------------------------------------------ #
    def _manage_position(self, bar: dict):
        p = self.pos
        h, l, cl = float(bar["high"]), float(bar["low"]), float(bar["close"])
        ts = bar["time"]
        # intrabar SL then TP (conservative: SL first)
        if p["side"] == 1:
            if l <= p["sl"]:
                self._close(p, p["sl"], ts, "sl")
                return
            if h >= p["tp"]:
                self._close(p, p["tp"], ts, "tp")
                return
        else:
            if h >= p["sl"]:
                self._close(p, p["sl"], ts, "sl")
                return
            if l <= p["tp"]:
                self._close(p, p["tp"], ts, "tp")
                return
        p["bars"] += 1
        if self.cfg.use_breakeven and not p.get("be", False):
            r = (cl - p["entry"]) / p["risk"] if p["side"] == 1 else (p["entry"] - cl) / p["risk"]
            if r >= self.cfg.breakeven_at_r:
                p["sl"] = p["entry"]
                p["be"] = True
        if p["bars"] >= self.cfg.max_holding_bars:
            self._close(p, cl, ts, "time")

    def open_position(self, side, entry, sl, tp, qty, risk_usd, reason, ts):
        self.pos = {
            "side": side, "entry": entry, "sl": sl, "tp": tp,
            "qty": qty, "risk_usd": risk_usd, "risk": abs(entry - sl),
            "reason": reason, "entry_time": ts, "bars": 0, "be": False,
        }

    def _close(self, p, px, ts, why):
        gross = (px - p["entry"]) * p["qty"] * p["side"]
        # costs: fee on entry+exit notional, slippage already applied at entry
        notional = p["entry"] * p["qty"]
        exit_notional = px * p["qty"]
        ef = self.cfg.entry_fee_pct if self.cfg.entry_fee_pct is not None else self.cfg.fee_pct
        xf = self.cfg.exit_fee_pct if self.cfg.exit_fee_pct is not None else self.cfg.fee_pct
        fees = notional * ef + exit_notional * xf
        pnl = gross - fees
        pnl_r = pnl / p["risk_usd"] if p["risk_usd"] > 0 else 0.0
        self.equity += pnl
        self.day_pnl += pnl
        self.day_trades += 1
        self.trades.append(Trade(
            entry_time=p["entry_time"], exit_time=ts, side=p["side"],
            entry_price=p["entry"], exit_price=px, sl=p["sl"], tp=p["tp"],
            qty=p["qty"], risk_usd=p["risk_usd"], pnl=pnl, pnl_r=pnl_r,
            fees=fees, reason=p["reason"], exit_reason=why, bars_held=p["bars"],
        ))
        self.pos = None


# --------------------------------------------------------------------------- #
# Indicator bundle (shared by backtest and live)
# --------------------------------------------------------------------------- #
def attach_indicators(df: pd.DataFrame, cfg: EngineConfig) -> dict:
    """Compute every causal array the engine needs from a closed-bar dataframe."""
    from .primitives import (wilder_atr, SwingState, order_blocks,
                             fair_value_gaps, sweep_events, candle_patterns,
                             displacement)
    o = df["Open"].to_numpy(float)
    h = df["High"].to_numpy(float)
    l = df["Low"].to_numpy(float)
    c = df["Close"].to_numpy(float)
    atr = wilder_atr(h, l, c, cfg.atr_len)
    swing = SwingState.build(h, l, cfg.k_swing)
    bull_sweep, bear_sweep = sweep_events(h, l, c, swing)
    bull_c, bear_c = candle_patterns(o, h, l, c)
    htf_close, htf_swing = _htf_bias_series(df, cfg.htf_rule, cfg.k_swing)
    return {
        "atr": atr,
        "swing": swing,
        "ob": order_blocks(o, h, l, c, atr),
        "fvg": fair_value_gaps(h, l),
        "sweeps": (bull_sweep, bear_sweep),
        "candles": (bull_c, bear_c),
        "disp": displacement(c, o, atr, 1.0),
        "htf_close": htf_close,
        "htf_swing": htf_swing,
    }


# --------------------------------------------------------------------------- #
# Backtest simulator (causal, intrabar SL/TP, costs)
# --------------------------------------------------------------------------- #
def simulate(df: pd.DataFrame, config: EngineConfig | None = None,
             initial_equity: float = 100.0, risk_pct: float | None = None):
    """Run the engine over a closed-bar OHLCV dataframe.

    Signal on bar ``t`` (closed) is executed at the *open* of bar ``t+1`` with
    slippage; SL/TP are then checked intrabar on subsequent bars.
    """
    cfg = config or EngineConfig()
    if risk_pct is not None:
        cfg.risk_pct = risk_pct
    eng = ScalpingEngine(cfg)
    eng.equity = initial_equity
    eng.hwm = initial_equity

    o = df["Open"].to_numpy(float)
    h = df["High"].to_numpy(float)
    l = df["Low"].to_numpy(float)
    c = df["Close"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.zeros(len(df))
    times = df.index

    ind = attach_indicators(df, cfg)
    atr = ind["atr"]
    swing = ind["swing"]
    obs = ind["ob"]
    fv = ind["fvg"]
    bull_sweep, bear_sweep = ind["sweeps"]
    bull_c, bear_c = ind["candles"]
    disp = ind["disp"]
    htf_close, htf_swing = ind["htf_close"], ind["htf_swing"]

    pending: Optional[Signal] = None
    equity_curve = np.full(len(df), np.nan)
    pending_entry_bar = None

    for t in range(len(df)):
        bar = {
            "time": times[t], "open": o[t], "high": h[t], "low": l[t],
            "close": c[t], "volume": v[t],
            "_atr": atr, "_swing": swing, "_htf_close": htf_close,
            "_htf_swing": htf_swing, "_ob": obs, "_fvg": fv,
            "_sweeps": (bull_sweep, bear_sweep), "_candles": (bull_c, bear_c),
            "_disp": disp,
        }
        eng.equity = eng.equity  # keep
        # execute pending signal at this bar's open
        if pending is not None and pending_entry_bar == t:
            side = pending.side
            entry = o[t] * (1 + cfg.slippage_pct * side)
            sl = pending.sl
            risk = (entry - sl) if side == 1 else (sl - entry)
            if risk > 0:
                risk_usd = max(0.0, eng.equity) * cfg.risk_pct
                qty = risk_usd / risk
                tp = entry + side * cfg.rr * risk
                eng.open_position(side, entry, sl, tp, qty, risk_usd,
                                  pending.reason, times[t])
            pending = None

        # engine consumes the bar (manages position / emits signal)
        sig = eng.on_bar(bar)
        if sig is not None and eng.pos is None:
            pending = sig
            pending_entry_bar = t + 1
        elif eng.pos is not None:
            pending = None

        eng.hwm = max(eng.hwm, eng.equity)
        equity_curve[t] = eng.equity

    # close any open position at the last close
    if eng.pos is not None:
        eng._close(eng.pos, c[-1], times[-1], "eod")

    return eng, equity_curve


def _htf_bias_series(df: pd.DataFrame, rule: str, k: int):
    """Causally resample to ``rule`` and build an HTF SwingState.

    Returns (htf_close_aligned_to_ltf, htf_swing_aligned_to_ltf) where the
    value at LTF bar ``t`` reflects the last *completed* HTF bar at or before
    the LTF bar's end time (no future HTF information).
    """
    from .primitives import SwingState
    if rule in ("", "none", None):
        return df["Close"].to_numpy(float), SwingState.build(
            df["High"].to_numpy(float), df["Low"].to_numpy(float), k)
    norm = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}
    r = norm.get(rule, rule)
    g = df.resample(r, label="left", closed="left").agg(
        Open=("Open", "first"), High=("High", "max"),
        Low=("Low", "min"), Close=("Close", "last"), Volume=("Volume", "sum"))
    # HTF bar starting at S covers [S, S+r); it is complete at S+r.
    # Align to LTF by end time: index = start + r.
    g.index = g.index + pd.Timedelta(r)
    htf_close = g["Close"].reindex(df.index, method="ffill").to_numpy(float)
    hs = SwingState.build(g["High"].to_numpy(float), g["Low"].to_numpy(float), k)
    # align swing arrays to LTF by end time
    hi = pd.Series(hs.high, index=g.index).reindex(df.index, method="ffill").to_numpy(float)
    li = pd.Series(hs.low, index=g.index).reindex(df.index, method="ffill").to_numpy(float)
    htf_swing = SwingState(hi, li, np.full(len(df), -1), np.full(len(df), -1))
    return htf_close, htf_swing
