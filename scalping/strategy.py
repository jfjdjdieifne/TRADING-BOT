"""MOMENTUM-X v1 — candidate 5m decision rules (one place, exact rules).

This is a pure, causal function set: no I/O, no lookahead, no hidden state. The
live bot (`live/multi_bot.py`) calls `decide()` on every closed 5m bar of the
symbols it is watching. `run_momentum.py` is a SEPARATE daily moving-average
reference test; it does not validate these 12 conditions or the full Binance
USDT-M universe.

The conditions below are deliberately many and strict — the "golden trade".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from scalping_engine.sessions import session_name

TREND_N = 50                      # daily bars, selected walk-forward (never fit on future)
MIN_ATR_PCT = 0.0004             # 0.04% — below this there is no room to pay fees
MAX_ATR_PCT = 0.06               # 6% — above this the stop is a gamble
MIN_RNG_ATR = 0.8                # breakout bar must be a real range bar
SESSIONS_ALLOWED = ("london", "ny", "overlap")


@dataclass
class Verdict:
    ok: bool
    score: float
    reason: str
    side: int = 1
    trigger: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    checks: dict | None = None


def trend_state(daily_close: pd.Series, n: int = TREND_N) -> dict:
    """Causal daily trend of ONE coin. Only the last closed daily bar is used."""
    if daily_close is None or len(daily_close) < n + 1:
        return {"ready": False, "above_ma": True, "roc_pos": True, "n": n}
    c = float(daily_close.iloc[-1])
    ma = float(daily_close.iloc[-(n + 1):-1].rolling(n).mean().iloc[-1]) \
        if len(daily_close) >= n + 1 else float(daily_close.rolling(n).mean().iloc[-1])
    prev = float(daily_close.iloc[-1 - n]) if len(daily_close) > n else c
    return {"ready": True, "above_ma": c > ma, "roc_pos": c > prev,
            "ma": ma, "close": c, "n": n}


def market_regime(btc_daily: pd.Series, n: int = TREND_N) -> bool:
    """Risk-on gate: BTC above its own n-day mean. Flat/cash otherwise."""
    if btc_daily is None or len(btc_daily) < n + 1:
        return True                       # no data -> do not silently block
    ma = float(btc_daily.iloc[-(n + 1):-1].rolling(n).mean().iloc[-1])
    return float(btc_daily.iloc[-1]) > ma


def momentum_score(hist: pd.DataFrame) -> float:
    """24h momentum divided by realised volatility, from closed 5m bars."""
    if len(hist) < 290:
        return 0.0
    c = hist["Close"].to_numpy(float)
    r = np.diff(np.log(c[-289:]))
    mom = float(np.exp(np.nansum(r)) - 1.0)
    vol = float(np.nanstd(r) * np.sqrt(288))
    return mom / vol if vol > 0 else 0.0


def rank_symbols(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda s: scores.get(s, 0.0), reverse=True)


def decide(*, symbol: str, ts, hist: pd.DataFrame, ind: dict, t: int,
           daily_close: pd.Series | None, btc_daily: pd.Series | None,
           score_rank: int, universe_size: int, cfg,
           daily_ok: bool = True) -> Verdict:
    """The GOLDEN TRADE: all 12 conditions must align. Pure function."""
    c = float(hist["Close"].iloc[-1])
    h = float(hist["High"].iloc[-1])
    l = float(hist["Low"].iloc[-1])
    atr = float(ind["atr"][t]) if t < len(ind["atr"]) else np.nan
    vwap = float(ind.get("session_vwap", np.nan)) if isinstance(ind, dict) else np.nan
    if np.isnan(vwap):
        typical = (hist["High"] + hist["Low"] + hist["Close"]) / 3.0
        day = hist.index[-1].date()
        today = typical[hist.index.date == day]
        vwap = float(today.mean()) if len(today) else c
    checks = {}
    checks["01_session_open"] = session_name(ts) in SESSIONS_ALLOWED
    checks["02_btc_regime_up"] = market_regime(btc_daily)
    tr = trend_state(daily_close)
    checks["03_coin_above_50d_ma"] = tr["above_ma"]
    checks["04_coin_50d_momentum_pos"] = tr["roc_pos"]
    checks["05_rank_top_half"] = score_rank <= max(1, int(np.ceil(universe_size / 2)))
    checks["06_tradeable_volatility"] = (not np.isnan(atr) and atr > 0
                                        and MIN_ATR_PCT <= atr / c <= MAX_ATR_PCT)
    checks["07_htf_not_bearish"] = int(ind["htf_trend"][t]) >= 0
    conf = float(ind["confluence"][t])
    checks["08_confluence"] = conf >= cfg.min_confluence
    checks["09_close_above_session_vwap"] = c > vwap
    checks["10_displacement_bar"] = (h - l) >= MIN_RNG_ATR * atr if atr > 0 else False
    checks["11_daily_risk_brakes"] = daily_ok
    # 12: price is near VWAP (a pullback in an uptrend), not extended
    checks["12_pullback_not_extended"] = ((c - vwap) / atr <= 2.5) if atr > 0 else False

    ok = all(checks.values())
    score = sum(checks.values()) / len(checks)
    if not ok:
        return Verdict(False, score, "conditions_not_met", checks=checks)

    risk = max(cfg.sl_atr_mult * atr, cfg.sl_min_atr * atr)
    sl = l - cfg.sl_atr_mult * atr
    sl = min(sl, c - risk)                # never tighter than the risk floor
    tp = c + cfg.rr * (c - sl)
    return Verdict(True, score, "momentum_golden_long", side=1,
                   trigger=c, sl=sl, tp=tp, checks=checks)
