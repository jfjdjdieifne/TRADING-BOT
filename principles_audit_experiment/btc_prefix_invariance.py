"""Causal prefix check for the one-change BTC no-BE candidate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "smc_v4_multisleeve_package"
HERE = Path(__file__).resolve().parent
RES = HERE / "results"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine import smc_v4_portfolio as ref_engine  # noqa: E402
from engine.causal_primitives import load_asset_ohlcv  # noqa: E402
from engine.smc_v4_portfolio import lock_single_position, run_engine_sniper_htf  # noqa: E402

EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")
CUTOFFS = (
    pd.Timestamp("2022-01-01 00:00:00", tz="UTC"),
    pd.Timestamp("2023-01-01 00:00:00", tz="UTC"),
    pd.Timestamp("2025-01-01 00:00:00", tz="UTC"),
)


def install_boundary_eod_patch() -> None:
    for name in ("_sim_1m_path", "_sim_1m_trail_1h"):
        original = getattr(ref_engine, name)
        if getattr(original, "_prefix_boundary_patch", False):
            continue

        def wrapped(*args, _original=original, **kwargs):
            result = _original(*args, **kwargs)
            if result is not None and result.get("outcome") == "EOD":
                times = kwargs.get("t1")
                if times is not None and len(times):
                    result["exit_idx"] = len(times) - 1
                    result["exit_time"] = str(times[-1])
            return result

        wrapped._prefix_boundary_patch = True  # type: ignore[attr-defined]
        setattr(ref_engine, name, wrapped)


def canonical(rows: list[dict[str, Any]], cutoff: pd.Timestamp) -> list[tuple[Any, ...]]:
    out = []
    for t in rows:
        entry = pd.Timestamp(t["entry_time"])
        exit_time = pd.Timestamp(t["exit_time"])
        if not (EV0 <= entry < cutoff and exit_time < cutoff and t.get("outcome") != "EOD"):
            continue
        out.append((
            str(t.get("engine", "")), str(t.get("side", "")), str(t["setup_time"]),
            str(t["entry_time"]), str(t["exit_time"]), str(t.get("outcome", "")),
            round(float(t["entry_price"]), 8), round(float(t["sl_price"]), 8),
            round(float(t["exit_price"]), 8), round(float(t["net_r"]), 10),
        ))
    return sorted(out, key=lambda x: (x[3], x[4], x[0]))


def run(df: pd.DataFrame, end: pd.Timestamp) -> list[dict[str, Any]]:
    rows = run_engine_sniper_htf(
        df, EV0, end,
        asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=None, be_lock_r=1.0,
        use_killzone=False, min_hour_utc=9, cost=0.0, pct_cost=0.0008,
        engine_label="BTC_15R_no_BE",
    )
    return lock_single_position(rows)


def main() -> None:
    install_boundary_eod_patch()
    full_df = pd.read_csv(RES / "trades_V8_no_BTC_BE_only.csv")
    full_rows = [r for r in full_df.to_dict("records") if r["asset"] == "BTCUSD"]
    data = load_asset_ohlcv(PKG / "data" / "BTCUSD_5m", [str(y) for y in range(2019, 2027)])
    results: dict[str, Any] = {"boundary_patch": "runtime-only", "cutoffs": {}}
    for cutoff in CUTOFFS:
        observed = run(data.loc[data.index < cutoff], cutoff)
        expected = canonical(full_rows, cutoff)
        got = canonical(observed, cutoff)
        results["cutoffs"][str(cutoff)] = {
            "expected_completed_trades": len(expected),
            "observed_completed_trades": len(got),
            "exact_match": expected == got,
            "missing_count": len(set(expected) - set(got)),
            "unexpected_count": len(set(got) - set(expected)),
        }
        print(str(cutoff), results["cutoffs"][str(cutoff)], flush=True)
    (RES / "btc_no_be_prefix_invariance.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
