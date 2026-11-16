#!/usr/bin/env python3
"""Re-run the byte-preserved original V5 engine without touching its source/results.

This is the immutable baseline requested by the owner. The copied engine lives
under ``original_v5/``; all outputs are written under this new research folder.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "original_v5"
if str(ORIGINAL) not in sys.path:
    sys.path.insert(0, str(ORIGINAL))

from engine.causal_primitives import load_xauusd_1m  # noqa: E402
from engine.smc_v4_portfolio import run_smc_v5_portfolio, simulate_compounded_account  # noqa: E402

DATA = HERE.parent / "smc_v4_multisleeve_package" / "data" / "XAUUSD_1m_histdata"
RESULTS = HERE / "baseline_outputs"
MONTHS = [f"{year}-{month:02d}" for year in range(2020, 2026) for month in range(1, 13)] + [
    f"2026-{month:02d}" for month in range(1, 11)
]
START = pd.Timestamp("2020-02-01", tz="UTC")
END = pd.Timestamp("2026-11-01", tz="UTC")


def summarize(rows: list[dict]) -> dict:
    values = [float(row["net_r"]) for row in rows]
    gains = sum(value for value in values if value > 0)
    losses = sum(-value for value in values if value < 0)
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    years: dict[str, float] = {}
    for row in rows:
        year = str(pd.Timestamp(row["entry_time"]).year)
        years[year] = years.get(year, 0.0) + float(row["net_r"])
    return {
        "trades": len(values),
        "wins": sum(value > 0 for value in values),
        "win_rate_pct": round(100.0 * sum(value > 0 for value in values) / len(values), 4) if values else None,
        "total_r": round(sum(values), 6),
        "expectancy_r": round(sum(values) / len(values), 6) if values else None,
        "profit_factor": round(gains / losses, 6) if losses else None,
        "max_dd_r": round(max_dd, 6),
        "yearly_net_r": {year: round(value, 6) for year, value in sorted(years.items())},
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    data = load_xauusd_1m(DATA, MONTHS)
    result = run_smc_v5_portfolio(data, START, END, cost=0.25, single_position_lock=True)
    baseline = result["v5_1pos_lock"]
    summary = {
        "source": "strategy_augmented_research/original_v5 (byte-preserved copy)",
        "original_source_sha256": {
            "engine/__init__.py": "b497d9c50e361a5f34c8df9cd55176330dd4eac856e365f37f0bcde24d081340",
            "engine/causal_primitives.py": "83f1c3a954c01d23f0b5527456453e1051c4666a661e1021ec0152d3a67d98a7",
            "engine/dynamic_profile.py": "b80a74a67b72dd666e2710723f87a346f1d7a7eb1aadab4ffb62034588c03d2f",
            "engine/smc_v3_trend_engine.py": "23ee3034d9867f6adf4b1f02fe227dffa530b825fda216c3df1471608ac84306",
            "engine/smc_v4_portfolio.py": "bec70ed41027dfcc29e8766d2645d4ef734b998dd7347533e314a5eb658517f0",
            "run_v4_multisleeve_backtest.py": "edb88bf866d276af70e9b2569cc9aaf2cb4a3f177a4573736aad972efd562ef0",
        },
        "evaluation": {"start_utc": START.isoformat(), "end_utc_exclusive": END.isoformat(), "cost_usd_per_oz": 0.25},
        "baseline": summarize(baseline),
        "compound_100": {
            "risk_1pct": simulate_compounded_account(baseline, start_capital=100.0, risk_pct=0.01, compound=True),
            "risk_2pct": simulate_compounded_account(baseline, start_capital=100.0, risk_pct=0.02, compound=True),
        },
        "contract": {
            "engine": "V5: V3_Pro + VisB_Pro + VisA + AMD_Pro",
            "entry_source": "causal HTF structure and lower-timeframe triggers",
            "portfolio": "one open position globally across V5 sleeves",
            "cost_model": "gross OHLC plus fixed $0.25/oz round-trip cost in original engine",
        },
    }
    (RESULTS / "summary_v5_clone.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame(baseline).to_csv(RESULTS / "taken_trades_v5_clone.csv", index=False)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
