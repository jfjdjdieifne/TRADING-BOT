"""Performance measurement. Deliberately boring and conventional."""

from __future__ import annotations

import numpy as np
import pandas as pd


def trades_frame(trades) -> pd.DataFrame:
    rows = []
    for t in trades:
        rows.append({
            "t_signal": t.t_signal, "t_entry": t.t_entry, "t_exit": t.t_exit,
            "dir": t.direction, "entry": t.entry, "stop": t.stop0, "t1": t.t1, "t2": t.t2,
            "exit_px": t.exit_px, "R": t.r_mult, "pnl": t.pnl_cash, "prob": t.prob,
            "mfe_R": t.mfe_r, "mae_R": t.mae_r, "bars": t.bars_held,
            "kind": t.exit_kind, "bootstrap": t.bootstrap, "size": t.size,
        })
    return pd.DataFrame(rows)


def equity_stats(equity: np.ndarray, bars_per_year: float) -> dict:
    e = np.asarray(equity, float)
    if len(e) < 10 or e[0] <= 0:
        return {"cagr": np.nan, "sharpe": np.nan, "max_dd": np.nan, "calmar": np.nan}
    r = np.diff(e) / e[:-1]
    r = r[np.isfinite(r)]
    peak = np.maximum.accumulate(e)
    dd = 1.0 - e / np.maximum(peak, 1e-12)
    years = len(e) / bars_per_year
    cagr = (e[-1] / e[0]) ** (1.0 / max(years, 1e-9)) - 1.0
    sd = r.std()
    sharpe = (r.mean() / sd * np.sqrt(bars_per_year)) if sd > 0 else np.nan
    return {"cagr": float(cagr), "sharpe": float(sharpe), "max_dd": float(dd.max()),
            "calmar": float(cagr / dd.max()) if dd.max() > 0 else np.nan}


def summarise(trades, equity=None, bars_per_year: float = 195.0 * 78, label: str = "") -> dict:
    """bars_per_year default: 5-minute bars in a 22.25h session, ~252 sessions."""
    if len(trades) == 0:
        return {"label": label, "n": 0}
    R = np.array([t.r_mult for t in trades], float)
    pnl = np.array([t.pnl_cash for t in trades], float)
    win = R > 0
    gross_win = pnl[win].sum()
    gross_los = -pnl[~win].sum()
    out = {
        "label": label,
        "n": len(trades),
        "win_rate": float(win.mean()),
        "mean_R": float(R.mean()),
        "median_R": float(np.median(R)),
        "std_R": float(R.std()),
        "t_stat_R": float(R.mean() / (R.std() / np.sqrt(len(R)))) if R.std() > 0 else np.nan,
        "expectancy_R": float(R.mean()),
        "profit_factor": float(gross_win / gross_los) if gross_los > 0 else np.inf,
        "best_R": float(R.max()), "worst_R": float(R.min()),
        "mean_win_R": float(R[win].mean()) if win.any() else np.nan,
        "mean_loss_R": float(R[~win].mean()) if (~win).any() else np.nan,
        "avg_bars_held": float(np.mean([t.bars_held for t in trades])),
        "pct_stopped": float(np.mean([t.exit_kind == "stop" for t in trades])),
        "total_pnl": float(pnl.sum()),
    }
    if equity is not None:
        out.update(equity_stats(equity, bars_per_year))
    return out


def yearly(trades, times) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame()
    df = pd.DataFrame({
        "R": [t.r_mult for t in trades],
        "pnl": [t.pnl_cash for t in trades],
        "yr": [times[t.t_signal].year for t in trades],
        "dir": [t.direction for t in trades],
    })
    g = df.groupby("yr").agg(n=("R", "size"), win=("R", lambda x: (x > 0).mean()),
                             mean_R=("R", "mean"), pnl=("pnl", "sum"))
    return g.round(3)


def bootstrap_ci(R: np.ndarray, n_boot: int = 5000, seed: int = 7) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(R), size=(n_boot, len(R)))
    m = R[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
