"""Reprice saved audit trades at 1x/2x/3x reference round-trip costs.

This is a cost-only sensitivity analysis: fills, signal times and exits are
held fixed.  The 3x row is an explicit upper stress relative to the local
reference costs, not a claim about a broker's actual spread/slippage model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")
TRAIN_END = pd.Timestamp("2023-01-01 00:00:00", tz="UTC")


def summary(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, multiplier: float) -> dict[str, Any]:
    if df.empty:
        return {"n": 0, "wr_pct": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "t_stat": 0.0}
    d = df.copy()
    d["entry_dt"] = pd.to_datetime(d["entry_time"], utc=True)
    d["exit_dt"] = pd.to_datetime(d["exit_time"], utc=True)
    # A few legacy V6 XAU rows predate the explicit cost_usd column.
    inferred_cost = d["asset"].map({"XAUUSD": 0.25, "NSXUSD": 2.0})
    inferred_cost = inferred_cost.where(d["asset"] != "BTCUSD", 0.0008 * d["entry_price"].astype(float))
    d["cost_usd"] = d["cost_usd"].fillna(inferred_cost)
    if d["cost_usd"].isna().any():
        raise ValueError("unpriced rows remain; audit artifact needs an explicit asset/cost")
    d = d.loc[(d.entry_dt >= start) & (d.entry_dt < end)].sort_values("exit_dt")
    if d.empty:
        return {"n": 0, "wr_pct": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "t_stat": 0.0}
    rs = (d["gross_usd"].astype(float) - multiplier * d["cost_usd"].astype(float)) / d["risk_usd"].astype(float)
    rs = rs.to_numpy(dtype=float)
    wins, losses = rs[rs > 0], rs[rs < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) else 999.0
    cumulative = np.cumsum(rs)
    peak = np.maximum.accumulate(np.insert(cumulative, 0, 0.0))[1:]
    std = float(rs.std(ddof=1)) if len(rs) > 1 else 0.0
    t_stat = float(rs.mean() / (std / np.sqrt(len(rs)))) if std > 1e-12 else 0.0
    years: dict[str, float] = {}
    for year, value in zip(d["entry_dt"].dt.year.astype(str), rs):
        years[year] = years.get(year, 0.0) + float(value)
    return {
        "n": int(len(rs)),
        "wr_pct": round(float(100 * np.mean(rs > 0)), 2),
        "net_r": round(float(rs.sum()), 2),
        "pf": round(pf, 3),
        "max_dd_r": round(float(np.max(peak - cumulative)), 2),
        "t_stat": round(t_stat, 2),
        "positive_years": int(sum(v > 0 for v in years.values())),
        "total_years": int(len(years)),
        "yearly_r": {k: round(v, 2) for k, v in sorted(years.items())},
    }


def main() -> None:
    files = sorted(RES.glob("trades_*.csv"))
    output: dict[str, Any] = {
        "cost_definition": {
            "1x": "cost_usd embedded in each saved reference trade",
            "2x": "2 * embedded round-trip cost",
            "3x_stress": "3 * embedded round-trip cost; fills unchanged",
        },
        "variants": {},
    }
    periods = {
        "full": (EV0, EV1),
        "train_2020_2022": (EV0, TRAIN_END),
        "holdout_2023_2026": (TRAIN_END, EV1),
        "latest_2025_2026": (pd.Timestamp("2025-01-01", tz="UTC"), EV1),
    }
    for path in files:
        name = path.stem.removeprefix("trades_")
        df = pd.read_csv(path)
        output["variants"][name] = {
            period: {f"{int(multiplier)}x": summary(df, start, end, multiplier) for multiplier in (1, 2, 3)}
            for period, (start, end) in periods.items()
        }
    (RES / "cost_stress.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    for name, periods_out in output["variants"].items():
        x = periods_out["holdout_2023_2026"]
        print(name, "holdout", {m: {k: x[m][k] for k in ("net_r", "pf", "max_dd_r", "t_stat")} for m in ("1x", "2x", "3x")})


if __name__ == "__main__":
    main()
