"""Prefix-invariance check for the isolated Python V8 reference.

For each cutoff, the V8 reference is run on data truncated strictly before the
cutoff.  Its completed trades are compared with the already saved full-window
V8 artifact, restricted to trades whose exits are also before the cutoff.  An
open/EOD trade at the truncation boundary is intentionally excluded: its exit
cannot be known from a prefix.

This is a causal replay check for the local engine, not proof that QuantConnect
broker fills are identical to the Python reference.
"""

from __future__ import annotations

import hashlib
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

from engine.causal_primitives import load_asset_ohlcv  # noqa: E402
from engine import smc_v4_portfolio as ref_engine  # noqa: E402
from engine.smc_v4_portfolio import lock_single_position, run_smc_v8_multiasset_portfolio  # noqa: E402

EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")
CUTOFFS = (
    pd.Timestamp("2022-01-01 00:00:00", tz="UTC"),
    pd.Timestamp("2023-01-01 00:00:00", tz="UTC"),
    pd.Timestamp("2025-01-01 00:00:00", tz="UTC"),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_boundary_eod_patch() -> None:
    """Patch only the imported reference at runtime, never the package file.

    The reference simulator initialized an EOD result with `exit_idx=entry_idx`.
    On a truncated prefix that made an open position appear to finish at entry,
    allowing later prefix-only trades.  A prefix replay must keep that position
    busy through the last known bar.  This wrapper changes only the boundary
    bookkeeping; it does not alter any signal or fill rule.
    """
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


def load_frames() -> dict[str, pd.DataFrame]:
    months = [f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13)]
    months += [f"2026-{m:02d}" for m in range(1, 11)]
    xau = load_asset_ohlcv(PKG / "data" / "XAUUSD_1m_histdata", months)
    nsx = load_asset_ohlcv(PKG / "data" / "NSXUSD_1m_histdata", months)
    btc = load_asset_ohlcv(PKG / "data" / "BTCUSD_5m", [str(y) for y in range(2019, 2027)])
    return {
        "XAUUSD": xau.loc[xau.index < EV1],
        "NSXUSD": nsx.loc[nsx.index < EV1],
        "BTCUSD": btc.loc[btc.index < EV1],
    }


def current_portfolio(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the same per-asset lock used by the audit harness."""
    buckets: dict[str, list[dict[str, Any]]] = {"XAUUSD": [], "NSXUSD": [], "BTCUSD": []}
    for row in rows:
        buckets[str(row["asset"])].append(dict(row))
    return sorted(
        lock_single_position(buckets["XAUUSD"])
        + lock_single_position(buckets["NSXUSD"])
        + lock_single_position(buckets["BTCUSD"]),
        key=lambda t: pd.Timestamp(t["exit_time"]),
    )


def canonical(rows: list[dict[str, Any]], cutoff: pd.Timestamp) -> list[tuple[Any, ...]]:
    out = []
    for t in rows:
        entry = pd.Timestamp(t["entry_time"])
        exit_time = pd.Timestamp(t["exit_time"])
        # EOD at a prefix boundary is not a completed trade for this test.
        if not (EV0 <= entry < cutoff and exit_time < cutoff and t.get("outcome") != "EOD"):
            continue
        out.append(
            (
                str(t.get("asset", "")),
                str(t.get("engine", "")),
                str(t.get("side", "")),
                str(t["setup_time"]),
                str(t["entry_time"]),
                str(t["exit_time"]),
                str(t.get("outcome", "")),
                round(float(t["entry_price"]), 8),
                round(float(t["sl_price"]), 8),
                round(float(t["exit_price"]), 8),
                round(float(t["net_r"]), 10),
            )
        )
    return sorted(out, key=lambda x: (x[4], x[5], x[0], x[1]))


def main() -> None:
    install_boundary_eod_patch()
    full_path = RES / "trades_V8_current.csv"
    full_df = pd.read_csv(full_path)
    full_rows = full_df.to_dict("records")
    frames = load_frames()
    results: dict[str, Any] = {
        "boundary_patch": "runtime-only: EOD exit index moved to last known prefix bar",
        "source_hashes": {
            "V8_3Asset_1PosEach_QC.py": sha(PKG / "exports" / "quantconnect" / "V8_3Asset_1PosEach_QC.py"),
            "smc_v4_portfolio.py": sha(PKG / "engine" / "smc_v4_portfolio.py"),
            "full_trade_artifact": sha(full_path),
        },
        "cutoffs": {},
    }
    for cutoff in CUTOFFS:
        prefix_frames = {asset: df.loc[df.index < cutoff].copy() for asset, df in frames.items()}
        v8 = run_smc_v8_multiasset_portfolio(
            prefix_frames["XAUUSD"], prefix_frames["NSXUSD"], prefix_frames["BTCUSD"],
            EV0, cutoff, xau_cost=0.25, nsx_cost_pts=2.0, btc_pct_cost=0.0008,
        )
        prefix_rows = current_portfolio(
            [*v8["xau_v8_1pos"], *v8["nsx_v8_1pos"], *v8["btc_15r_be"]]
        )
        expected = canonical(full_rows, cutoff)
        observed = canonical(prefix_rows, cutoff)
        missing = sorted(set(expected) - set(observed))
        unexpected = sorted(set(observed) - set(expected))
        results["cutoffs"][str(cutoff)] = {
            "prefix_source_bars": {asset: int(len(df)) for asset, df in prefix_frames.items()},
            "expected_completed_trades": len(expected),
            "observed_completed_trades": len(observed),
            "exact_match": expected == observed,
            "missing_count": len(missing),
            "unexpected_count": len(unexpected),
            "missing_examples": [list(x) for x in missing[:3]],
            "unexpected_examples": [list(x) for x in unexpected[:3]],
        }
        print(str(cutoff), results["cutoffs"][str(cutoff)], flush=True)
    (RES / "prefix_invariance.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
