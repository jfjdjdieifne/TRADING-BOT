"""Honest performance metrics. No smoothing, no cherry-picking."""

from __future__ import annotations

import numpy as np


def compute_metrics(trades, equity_curve=None, initial_equity: float = 100.0) -> dict:
    import pandas as pd
    if not trades:
        return {"n": 0, "wr_pct": 0.0, "pf": 0.0, "net_r": 0.0, "gross_r": 0.0,
                "avg_cost_r": 0.0, "total_cost_r": 0.0, "net_pct": 0.0,
                "expectancy_r": 0.0, "max_dd_pct": 0.0, "t_stat": 0.0,
                "avg_win_r": 0.0, "avg_loss_r": 0.0, "avg_bars": 0.0,
                "final_equity": initial_equity, "reasons": {}, "exits": {}}
    r = np.array([t.pnl_r for t in trades], dtype=float)
    pnl = np.array([t.pnl for t in trades], dtype=float)
    wins = r[r > 0]
    losses = r[r <= 0]
    gross_w = wins.sum()
    gross_l = -losses.sum()
    pf = (gross_w / gross_l) if gross_l > 0 else float("inf") if gross_w > 0 else 0.0
    n = len(r)
    mean_r = r.mean()
    sd_r = r.std(ddof=1) if n > 1 else 0.0
    t_stat = (mean_r / (sd_r / np.sqrt(n))) if sd_r > 0 else 0.0

    if equity_curve is not None:
        eq = np.asarray(equity_curve, dtype=float)
        eq = eq[~np.isnan(eq)]
        hwm = np.maximum.accumulate(eq)
        dd = (hwm - eq) / hwm
        max_dd = float(dd.max()) if len(dd) else 0.0
        final = float(eq[-1]) if len(eq) else initial_equity
    else:
        eq = initial_equity + np.cumsum(pnl)
        hwm = np.maximum.accumulate(eq)
        dd = (hwm - eq) / hwm
        max_dd = float(dd.max()) if len(dd) else 0.0
        final = float(eq[-1])

    gross_r = float(sum(t.pnl_r + t.fees / t.risk_usd for t in trades)) if trades else 0.0
    avg_cost_r = float(np.mean([t.fees / t.risk_usd for t in trades])) if trades else 0.0
    total_cost_r = float(sum(t.fees / t.risk_usd for t in trades)) if trades else 0.0
    reasons, exits = {}, {}
    for tr in trades:
        reasons[tr.reason] = reasons.get(tr.reason, 0) + 1
        exits[tr.exit_reason] = exits.get(tr.exit_reason, 0) + 1

    return {
        "n": n,
        "wr_pct": float(len(wins) / n * 100.0),
        "pf": float(pf),
        "net_r": float(r.sum()),
        "gross_r": gross_r,
        "avg_cost_r": avg_cost_r,
        "total_cost_r": total_cost_r,
        "net_pct": float((final - initial_equity) / initial_equity * 100.0),
        "expectancy_r": float(mean_r),
        "max_dd_pct": float(max_dd * 100.0),
        "t_stat": float(t_stat),
        "avg_win_r": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses.mean()) if len(losses) else 0.0,
        "avg_bars": float(np.mean([t.bars_held for t in trades])),
        "final_equity": float(final),
        "reasons": reasons,
        "exits": exits,
    }


def fmt(m: dict) -> str:
    return (
        f"N={m['n']}  WR={m['wr_pct']:.1f}%  PF={m['pf']:.3f}  "
        f"net={m['net_r']:.2f}R ({m['net_pct']:+.1f}%)  "
        f"gross={m.get('gross_r', 0.0):.2f}R  cost={m.get('avg_cost_r', 0.0):.2f}R/tr  "
        f"exp={m['expectancy_r']:.3f}R  maxDD={m['max_dd_pct']:.1f}%  "
        f"t={m['t_stat']:.2f}  final=${m['final_equity']:.2f}"
    )
