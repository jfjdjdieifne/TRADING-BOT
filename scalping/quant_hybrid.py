"""QUANT-HYBRID v1 & Expanding Walk-Forward 4h Breakout/Sweep Engine.

Discovered after 15 rounds (~700 configs) of strictly causal testing across
local BTCUSD (5m, 2019-2026), XAUUSD (1m, 2020-2026), and NSXUSD (1m, 2020-2026).

Two complementary, strictly non-peeking components:
  1. WF_4h_BreakoutSweep (Discrete 4h):
     - Uniform rules across BTC, XAU, NSX: Keltner(1.5 ATR) + Donchian(30)
       breakouts and SwingState(k=3) structural sweep reclaims, aligned with
       prior closed 1D EMA50/EMA20 regime.
     - Wide risk stops max(2.0 * ATR_14, min_pct * Close) + BE@2R + 3.0 ATR
       Chandelier trailing stop, executed on next bar Open[t+1].
     - Expanding Walk-Forward yearly gate: in year Y (2021..2026), sleeve S
       is active ONLY if strictly prior years (< Y) had >= 8 trades and net_r > 0.
  2. Cont_1h_EMA (Continuous 1h):
     - Multi-speed (5, 10, 20, 40, 80 days) volatility-normalized tanh EMA
       trend signals across BTC, XAU, NSX, scaled by 20-day EWMA inverse vol
       (target_vol=1.0, max_lev=3.5), delayed by 2 bars (shift(2)), with exact
       turnover cost deducted on |delta_pos|.

Note: Strict >= +10% EVERY single month as an unbroken floor is mathematically
incompatible with realistic trading volatility; this engine maximizes risk-
adjusted growth while quantifying exact monthly/drawdown reality honestly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scalping_engine.data import load_btc_5m, load_nsx_1m, load_xau_1m
from scalping_engine.primitives import SwingState

CACHE_DIR = Path("/tmp/scalping_cache")
ASSETS = ("btc", "xau", "nsx")
BPY_1H = {"btc": 24.0 * 365.0, "xau": 24.0 * 260.0, "nsx": 24.0 * 260.0}


def calc_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int = 14) -> np.ndarray:
    tr = np.empty(len(c), dtype=np.float64)
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(
        h[1:] - l[1:],
        np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])),
    )
    return pd.Series(tr).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean().to_numpy()


def calc_ema(c: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(c).ewm(span=n, adjust=False, min_periods=n).mean().to_numpy()


def _resample_ohlcv(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    if df.index.tz is not None:
        df = df.tz_convert("UTC").tz_localize(None)
    return (
        df.resample(tf, label="left", closed="left")
        .agg(
            {
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }
        )
        .dropna(subset=["Open", "High", "Low", "Close"])
    )


def load_resampled_frames(use_cache: bool = True) -> dict[str, dict[str, pd.DataFrame]]:
    """Load 1h, 4h, and 1D OHLCV bars for BTC, XAU, NSX from repo datasets."""
    out: dict[str, dict[str, pd.DataFrame]] = {a: {} for a in ASSETS}
    tfs = ("1h", "4h", "1D")
    if use_cache and all((CACHE_DIR / f"{a}_{tf}.pkl").exists() for a in ASSETS for tf in tfs):
        for a in ASSETS:
            for tf in tfs:
                out[a][tf] = pd.read_pickle(CACHE_DIR / f"{a}_{tf}.pkl")
        return out

    loaders = {"btc": load_btc_5m, "xau": load_xau_1m, "nsx": load_nsx_1m}
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for a, fn in loaders.items():
        raw = fn()
        for tf in tfs:
            res = _resample_ohlcv(raw, tf)
            out[a][tf] = res
            if use_cache:
                res.to_pickle(CACHE_DIR / f"{a}_{tf}.pkl")
    return out


@dataclass
class HybridParams:
    kelt_mult: float = 1.5
    dc_win: int = 30
    sl_mult: float = 2.0
    trail_mult: float = 3.0
    be_trigger_r: float = 2.0
    d1_ema_slow: int = 50
    d1_ema_fast: int = 20
    swing_k: int = 3
    max_hold_4h: int = 180
    wf_min_trades: int = 8
    speeds_days: tuple[int, ...] = (5, 10, 20, 40, 80)
    vol_days: int = 20
    target_vol: float = 1.0
    max_lev: float = 3.5
    short_floor: float = 0.0  # 0.0 = long-only 1h core; -0.5 = asymmetric


def run_discrete_4h_sleeves(
    frames: dict[str, dict[str, pd.DataFrame]],
    fee: float = 0.0005,
    slip: float = 0.0002,
    params: HybridParams = HybridParams(),
    start_date: str = "2020-01-01",
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Simulate all 12 discrete 4h sleeves independently with MTM daily R."""
    sleeve_daily_r: dict[str, pd.Series] = {}
    sleeve_trades: dict[str, pd.DataFrame] = {}

    for asset in ASSETS:
        d1 = frames[asset]["1D"].loc[start_date:]
        d1c = d1["Close"].to_numpy(float)
        d1_up50 = pd.Series(d1c > calc_ema(d1c, params.d1_ema_slow), index=d1.index).shift(1)
        d1_dn50 = pd.Series(d1c < calc_ema(d1c, params.d1_ema_slow), index=d1.index).shift(1)
        d1_up20 = pd.Series(d1c > calc_ema(d1c, params.d1_ema_fast), index=d1.index).shift(1)
        d1_dn20 = pd.Series(d1c < calc_ema(d1c, params.d1_ema_fast), index=d1.index).shift(1)

        h4 = frames[asset]["4h"].loc[start_date:]
        ts = h4.index
        o = h4["Open"].to_numpy(float)
        h = h4["High"].to_numpy(float)
        l = h4["Low"].to_numpy(float)
        c = h4["Close"].to_numpy(float)

        atr = calc_atr(h, l, c, 14)
        ema12 = calc_ema(c, 12)
        ema20 = calc_ema(c, 20)
        ema36 = calc_ema(c, 36)

        days_idx = pd.DatetimeIndex(ts.normalize())
        up50 = d1_up50.reindex(days_idx).fillna(False).to_numpy(bool)
        dn50 = d1_dn50.reindex(days_idx).fillna(False).to_numpy(bool)
        up20 = d1_up20.reindex(days_idx).fillna(False).to_numpy(bool)
        dn20 = d1_dn20.reindex(days_idx).fillna(False).to_numpy(bool)
        up4 = ema12 > ema36
        dn4 = ema12 < ema36

        min_pct = 0.006 if asset == "btc" else 0.003
        sl_arr = np.maximum(params.sl_mult * atr, min_pct * c)

        sw = SwingState.build(h, l, k=params.swing_k)
        ps_hi = np.roll(sw.high, 1)
        ps_hi[0] = np.nan
        ps_lo = np.roll(sw.low, 1)
        ps_lo[0] = np.nan
        pc = np.roll(c, 1)
        pc[0] = c[0]

        khi = ema20 + params.kelt_mult * atr
        klo = ema20 - params.kelt_mult * atr
        pkhi = np.roll(khi, 1)
        pkhi[0] = np.nan
        pklo = np.roll(klo, 1)
        pklo[0] = np.nan
        hi_dc = pd.Series(h).rolling(params.dc_win).max().shift(1).to_numpy()
        lo_dc = pd.Series(l).rolling(params.dc_win).min().shift(1).to_numpy()

        sigs = {
            f"{asset}_bo_L": np.where(
                (up20 & up4 & (c > khi) & (pc <= pkhi)) | (up50 & (c > hi_dc)), 1, 0
            ),
            f"{asset}_bo_S": np.where(
                (dn20 & dn4 & (c < klo) & (pc >= pklo)) | (dn50 & (c < lo_dc)), -1, 0
            ),
            f"{asset}_sw_L": np.where(
                up50 & ~np.isnan(ps_lo) & (l < ps_lo) & (c > ps_lo) & (c > o), 1, 0
            ),
            f"{asset}_sw_S": np.where(
                dn50 & ~np.isnan(ps_hi) & (h > ps_hi) & (c < ps_hi) & (c < o), -1, 0
            ),
        }

        n = len(c)
        for sname, sig in sigs.items():
            mtm = np.zeros(n, dtype=np.float64)
            tr_list: list[tuple[Any, Any, int, float, float, float]] = []
            i = 0
            while i < n - 2:
                side = int(sig[i])
                risk = float(sl_arr[i])
                if side == 0 or np.isnan(risk) or risk <= 0 or np.isnan(atr[i]) or atr[i] <= 0:
                    i += 1
                    continue
                eb = i + 1
                entry = o[eb] * (1.0 + slip * side)
                sl = entry - side * risk
                best = entry
                be = False
                ex_px = None
                ex_bar = eb
                prev_mtm = entry
                for j in range(eb, min(n, eb + params.max_hold_4h)):
                    if side == 1:
                        if l[j] <= sl:
                            ex_px, ex_bar = sl, j
                            break
                        if h[j] > best:
                            best = h[j]
                        if not be and (best - entry) >= params.be_trigger_r * risk:
                            sl = max(sl, entry)
                            be = True
                        if (best - entry) >= params.be_trigger_r * risk and not np.isnan(atr[j]):
                            sl = max(sl, best - params.trail_mult * atr[j])
                    else:
                        if h[j] >= sl:
                            ex_px, ex_bar = sl, j
                            break
                        if l[j] < best:
                            best = l[j]
                        if not be and (entry - best) >= params.be_trigger_r * risk:
                            sl = min(sl, entry)
                            be = True
                        if (entry - best) >= params.be_trigger_r * risk and not np.isnan(atr[j]):
                            sl = min(sl, best + params.trail_mult * atr[j])
                    mtm[j] += ((c[j] - prev_mtm) * side) / risk
                    prev_mtm = c[j]
                if ex_px is None:
                    ex_bar = min(n - 1, eb + params.max_hold_4h - 1)
                    ex_px = c[ex_bar]
                ex_fill = ex_px * (1.0 - slip * side)
                cost_r = (entry + ex_fill) * fee / risk
                mtm[ex_bar] += ((ex_fill - prev_mtm) * side) / risk - cost_r
                net_r = ((ex_fill - entry) * side) / risk - cost_r
                tr_list.append((ts[eb], ts[ex_bar], side, entry, ex_fill, net_r))
                i = ex_bar + 1

            sleeve_daily_r[sname] = pd.Series(mtm, index=ts).resample("1D").sum()
            sleeve_trades[sname] = pd.DataFrame(
                tr_list,
                columns=["entry_t", "exit_t", "side", "entry_px", "exit_px", "net_r"],
            )

    return pd.DataFrame(sleeve_daily_r).fillna(0.0), sleeve_trades


def expanding_walk_forward(
    dr_df: pd.DataFrame,
    tr_map: dict[str, pd.DataFrame],
    params: HybridParams = HybridParams(),
    start_year: int = 2021,
    end_year: int = 2026,
) -> tuple[pd.Series, dict[int, list[str]], pd.DataFrame]:
    """Select active sleeves for year Y strictly from trades exited in < Y."""
    wf_r = pd.Series(0.0, index=dr_df.index)
    active_by_year: dict[int, list[str]] = {}
    oos_trades = []
    for yr in range(start_year, end_year + 1):
        cols = []
        for col, tdf in tr_map.items():
            prior = tdf[tdf["exit_t"].dt.year < yr]
            if len(prior) >= params.wf_min_trades and float(prior["net_r"].sum()) > 0.0:
                cols.append(col)
        active_by_year[yr] = cols
        if cols:
            mask = dr_df.index.year == yr
            wf_r.loc[mask] = dr_df.loc[mask, cols].sum(axis=1)
            for col in cols:
                tdf = tr_map[col]
                sub = tdf[tdf["exit_t"].dt.year == yr].copy()
                if len(sub):
                    sub["sleeve"] = col
                    oos_trades.append(sub)
    trades_df = pd.concat(oos_trades, ignore_index=True) if oos_trades else pd.DataFrame()
    return wf_r, active_by_year, trades_df


def run_cont_1h_ema(
    frames: dict[str, dict[str, pd.DataFrame]],
    cost: float = 0.0007,
    params: HybridParams = HybridParams(),
    start_date: str = "2020-01-01",
) -> tuple[pd.Series, pd.DataFrame]:
    """Multi-speed 1h vol-targeted EMA portfolio with 2-bar signal/execution lag."""
    daily_rets: dict[str, pd.Series] = {}
    latest_pos: dict[str, pd.Series] = {}
    for a in ASSETS:
        df = frames[a]["1h"].loc[start_date:]
        c = df["Close"]
        bpy = BPY_1H[a]
        r = c.pct_change().fillna(0.0)
        span_v = int(max(10, round(bpy * (params.vol_days / 365.0))))
        vol = (r.ewm(span=span_v, min_periods=span_v).std() * np.sqrt(bpy)).clip(lower=0.04)
        sigs = []
        for d in params.speeds_days:
            lb = max(3, int(round(d * bpy / 365.0)))
            ef = c.ewm(span=max(2, lb // 2), min_periods=max(2, lb // 2)).mean()
            es = c.ewm(span=lb * 2, min_periods=lb * 2).mean()
            diff = (ef - es) / (c * (vol / np.sqrt(bpy)) * np.sqrt(lb))
            sigs.append(np.tanh(diff * 1.5).clip(lower=params.short_floor))
        sig = pd.concat(sigs, axis=1).mean(axis=1)
        pos = (sig * (params.target_vol / vol)).clip(-params.max_lev, params.max_lev).fillna(0.0)
        pos_held = pos.shift(2).fillna(0.0)
        net_r = pos_held * r - cost * pos_held.diff().abs().fillna(0.0)
        daily_rets[a] = (1.0 + net_r).resample("1D").prod() - 1.0
        latest_pos[a] = pos
    daily_df = pd.DataFrame(daily_rets).fillna(0.0)
    return daily_df.mean(axis=1), pd.DataFrame(latest_pos)


def combine_hybrid(wf_daily_r: pd.Series, ema_daily: pd.Series, risk_pct: float = 0.02) -> pd.Series:
    """Risk-balanced 50/50 blend between WF_4h_BreakoutSweep and Cont_1h_EMA."""
    return (
        wf_daily_r * risk_pct * 0.70 + ema_daily * (risk_pct / 0.02) * 0.70
    ).reindex(wf_daily_r.index).fillna(0.0)


def block_bootstrap_p(
    daily_rets: np.ndarray, n_boot: int = 2000, block_len: int = 14, seed: int = 42
) -> float:
    """Centered circular block bootstrap p-value testing H0: mean daily return <= 0."""
    rng = np.random.default_rng(seed)
    sd_obs = daily_rets.std(ddof=1)
    if sd_obs <= 0:
        return 1.0
    obs_t = daily_rets.mean() / (sd_obs / np.sqrt(len(daily_rets)))
    centered = daily_rets - daily_rets.mean()
    m = len(centered)
    n_blocks = int(math.ceil(m / block_len))
    ge = 0
    for _ in range(n_boot):
        starts = rng.integers(0, m, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block_len) % m for s in starts])[:m]
        sample = centered[idx]
        sd = sample.std(ddof=1)
        t_b = sample.mean() / (sd / np.sqrt(m)) if sd > 0 else 0.0
        if t_b >= obs_t:
            ge += 1
    return (ge + 1.0) / (n_boot + 1.0)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _inv_norm(p: float) -> float:
    t = math.sqrt(-2.0 * math.log(1.0 - p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)


def deflated_sharpe(daily_rets: np.ndarray, n_trials: int = 700) -> float:
    """Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio probability."""
    sd = daily_rets.std(ddof=1)
    if sd <= 0 or len(daily_rets) < 30:
        return 0.0
    sr = daily_rets.mean() / sd
    t_len = len(daily_rets)
    skew = float(pd.Series(daily_rets).skew())
    kurt = float(pd.Series(daily_rets).kurt() + 3.0)
    gamma = 0.5772156649
    z1 = _inv_norm(1.0 - 1.0 / max(2, n_trials))
    z2 = _inv_norm(1.0 - 1.0 / (max(2, n_trials) * math.e))
    sr_star = ((1.0 - gamma) * z1 + gamma * z2) * math.sqrt(1.0 / t_len)
    var_sr = max(1e-12, (1.0 - skew * sr + ((kurt - 1.0) / 4.0) * (sr ** 2)) / (t_len - 1.0))
    return _norm_cdf((sr - sr_star) / math.sqrt(var_sr))


def summarize_daily_returns(
    daily_rets: pd.Series,
    oos_start: str = "2021-01-01",
    run_bootstrap: bool = False,
    n_trials: int = 700,
) -> dict[str, Any]:
    sub = daily_rets.loc[oos_start:].dropna()
    eq = 100.0 * (1.0 + sub).cumprod()
    dd = float(((eq.cummax() - eq) / eq.cummax()).max())
    m = (1.0 + sub).resample("ME").prod() - 1.0
    y = (1.0 + sub).resample("YE").prod() - 1.0
    sd = float(sub.std(ddof=1))
    sh = float((sub.mean() / sd) * np.sqrt(365.0)) if sd > 0 else 0.0
    t_stat = float(sub.mean() / (sd / np.sqrt(len(sub)))) if sd > 0 else 0.0
    gmo = float((eq.iloc[-1] / 100.0) ** (1.0 / len(m)) - 1.0)
    out: dict[str, Any] = {
        "months": int(len(m)),
        "final_100usd": round(float(eq.iloc[-1]), 2),
        "total_return_pct": round(float(eq.iloc[-1] - 100.0), 1),
        "sharpe": round(sh, 2),
        "t_stat": round(t_stat, 2),
        "max_dd_pct": round(100.0 * dd, 1),
        "geo_month_pct": round(100.0 * gmo, 2),
        "mean_month_pct": round(float(100.0 * m.mean()), 2),
        "median_month_pct": round(float(100.0 * m.median()), 2),
        "positive_months": int((m > 0).sum()),
        "months_ge_10pct": int((m >= 0.10).sum()),
        "best_month_pct": round(float(100.0 * m.max()), 1),
        "worst_month_pct": round(float(100.0 * m.min()), 1),
        "positive_years": int((y > 0).sum()),
        "total_years": int(len(y)),
        "yearly_pct": {str(i.year): round(100.0 * float(v), 1) for i, v in y.items()},
    }
    if run_bootstrap:
        arr = sub.to_numpy(dtype=np.float64)
        out["p_bootstrap"] = round(block_bootstrap_p(arr), 4)
        out["deflated_sharpe_700"] = round(deflated_sharpe(arr, n_trials=n_trials), 3)
    return out


def current_signals(frames: dict[str, dict[str, pd.DataFrame]], params: HybridParams = HybridParams()) -> dict[str, Any]:
    """Inspect latest strictly causal signals across BTC, XAU, NSX."""
    dr_df, tr_map = run_discrete_4h_sleeves(frames, params=params)
    _, active_yr, _ = expanding_walk_forward(dr_df, tr_map, params=params)
    active_2026 = active_yr.get(2026, [])
    _, ema_pos = run_cont_1h_ema(frames, params=params)
    latest_1h = {}
    for a in ASSETS:
        s = ema_pos[a].dropna()
        latest_1h[a] = {
            "timestamp": str(s.index[-1]),
            "target_leverage_weight": round(float(s.iloc[-1]), 3),
        }
    return {
        "active_wf_sleeves_2026": active_2026,
        "cont_1h_ema_latest": latest_1h,
    }
