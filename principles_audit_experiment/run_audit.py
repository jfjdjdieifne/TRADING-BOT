"""Read-only audit and isolated ablation tests for the frozen V8 strategy.

The target QC file and the package engine are never edited here.  This script
runs the existing local Python reference plus isolated variants to answer three
questions:

1. Which V8 filters survive a later-period holdout?
2. Which apparent improvements are full-sample selection effects?
3. Which implementation principles need a candidate patch before live use?

The variants are deliberately kept outside the production source tree.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "smc_v4_multisleeve_package"
OUT = Path(__file__).resolve().parent
RES = OUT / "results"
RES.mkdir(parents=True, exist_ok=True)
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine.causal_primitives import build_causal_htf_structure, load_asset_ohlcv, resample_causal_tf  # noqa: E402
from engine.smc_v4_portfolio import (  # noqa: E402
    lock_single_position,
    run_engine_amd_pro,
    run_engine_sniper_htf,
    run_smc_v6_xau_portfolio,
    run_smc_v8_multiasset_portfolio,
)

EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")
TRAIN_END = pd.Timestamp("2023-01-01 00:00:00", tz="UTC")
TEST_END = EV1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frames() -> dict[str, pd.DataFrame]:
    months = [f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 11)]
    btc_years = [str(y) for y in range(2019, 2027)]
    xau = load_asset_ohlcv(PKG / "data" / "XAUUSD_1m_histdata", months)
    nsx = load_asset_ohlcv(PKG / "data" / "NSXUSD_1m_histdata", months)
    btc = load_asset_ohlcv(PKG / "data" / "BTCUSD_5m", btc_years)
    btc = btc.loc[btc.index < EV1]
    return {"XAUUSD": xau, "NSXUSD": nsx, "BTCUSD": btc}


def copy_trades(rows: list[dict[str, Any]], asset: str | None = None, engine: str | None = None) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        t = dict(row)
        if asset is not None:
            t["asset"] = asset
        if engine is not None:
            t["engine"] = engine
        out.append(t)
    return out


def portfolio(xau: list[dict[str, Any]], nsx: list[dict[str, Any]], btc: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        lock_single_position(xau) + lock_single_position(nsx) + lock_single_position(btc),
        key=lambda t: pd.Timestamp(t["exit_time"]),
    )


def summarize(rows: list[dict[str, Any]], start: pd.Timestamp = EV0, end: pd.Timestamp = EV1) -> dict[str, Any]:
    chosen = [
        t for t in rows
        if start <= pd.Timestamp(t["entry_time"]) < end
    ]
    if not chosen:
        return {"n": 0, "wr_pct": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "t_stat": 0.0, "positive_years": 0, "total_years": 0}
    chosen = sorted(chosen, key=lambda t: pd.Timestamp(t["exit_time"]))
    rs = np.asarray([float(t["net_r"]) for t in chosen], dtype=float)
    wins, losses = rs[rs > 0], rs[rs < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) else 999.0
    cum = np.cumsum(rs)
    peak = np.maximum.accumulate(np.insert(cum, 0, 0.0))[1:]
    max_dd = float(np.max(peak - cum))
    std = float(rs.std(ddof=1)) if len(rs) > 1 else 0.0
    t_stat = float(rs.mean() / (std / np.sqrt(len(rs)))) if std > 1e-12 else 0.0
    by_year = pd.DataFrame({"entry": pd.to_datetime([t["entry_time"]], utc=True) for t in []})
    years: dict[str, float] = {}
    for t, r in zip(chosen, rs):
        y = str(pd.Timestamp(t["entry_time"]).year)
        years[y] = years.get(y, 0.0) + float(r)
    return {
        "n": int(len(rs)),
        "wr_pct": round(float(100.0 * np.mean(rs > 0)), 2),
        "net_r": round(float(rs.sum()), 2),
        "pf": round(pf, 3),
        "max_dd_r": round(max_dd, 2),
        "t_stat": round(t_stat, 2),
        "positive_years": int(sum(v > 0 for v in years.values())),
        "total_years": int(len(years)),
        "yearly_r": {k: round(v, 2) for k, v in sorted(years.items())},
    }


def periods(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "full": summarize(rows, EV0, EV1),
        "train_2020_2022": summarize(rows, EV0, TRAIN_END),
        "holdout_2023_2026": summarize(rows, TRAIN_END, TEST_END),
        "latest_2025_2026": summarize(rows, pd.Timestamp("2025-01-01", tz="UTC"), EV1),
    }


def overlap_days(df: pd.DataFrame) -> dict[str, Any]:
    """Count daily ER14 values in the QC's overlapping .20-.25 regime band."""
    d = resample_causal_tf(df, "1d")
    c = d["Close"].to_numpy(dtype=float)
    er = np.full(len(c), np.nan)
    for i in range(14, len(c)):
        den = np.abs(np.diff(c[i - 14 : i + 1])).sum()
        er[i] = abs(c[i] - c[i - 14]) / den if den > 0 else 0.0
    mask = (er >= 0.20) & (er < 0.25)
    valid = np.isfinite(er)
    return {
        "daily_bars": int(valid.sum()),
        "overlap_days": int(mask.sum()),
        "overlap_pct_of_valid_days": round(float(100.0 * mask.sum() / valid.sum()), 2) if valid.sum() else 0.0,
        "er_ge_025_days": int(((er >= 0.25) & valid).sum()),
        "er_lt_020_days": int(((er < 0.20) & valid).sum()),
    }


def prepare_variants(frames: dict[str, pd.DataFrame]) -> dict[str, list[dict[str, Any]]]:
    print("Running V8 reference components ...", flush=True)
    v8 = run_smc_v8_multiasset_portfolio(
        frames["XAUUSD"], frames["NSXUSD"], frames["BTCUSD"], EV0, EV1,
        xau_cost=0.25, nsx_cost_pts=2.0, btc_pct_cost=0.0008,
    )
    print("Running unfiltered XAU V6 component for the XAU time-filter ablation ...", flush=True)
    v6 = run_smc_v6_xau_portfolio(frames["XAUUSD"], EV0, EV1, cost=0.25, single_position_lock=False)

    xau_current = copy_trades(v8["xau_v8_1pos"], "XAUUSD")
    nsx_current = copy_trades(v8["nsx_v8_1pos"], "NSXUSD")
    btc_current = copy_trades(v8["btc_15r_be"], "BTCUSD")

    xau_no_cash_skip = copy_trades(v6["v6_1pos_lock"], "XAUUSD", "XAU_no_cash_open_filter")

    print("Running NSX no-09:00 UTC ablation ...", flush=True)
    nsx_all_hours = run_engine_sniper_htf(
        frames["NSXUSD"], EV0, EV1,
        asset="NSXUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="4h",
        min_risk_abs=10.0, min_risk_pct=0.0010, fixed_rr=10.0, trail_1h_after_r=None,
        use_killzone=True, min_hour_utc=None, cost=2.0, engine_label="NSX_1H1m_10R_all_hours",
    )
    nsx_no_hour = lock_single_position(copy_trades(v8["nsx_amd_1d"], "NSXUSD") + nsx_all_hours)

    print("Running NSX no-1D-regime-gate ablation ...", flush=True)
    nsx_scaled = frames["NSXUSD"].copy()
    for col in ("Open", "High", "Low", "Close"):
        nsx_scaled[col] = nsx_scaled[col] / 10.0
    amd_raw_scaled = run_engine_amd_pro(nsx_scaled, EV0, EV1, cost=0.20)
    amd_raw = []
    for t in amd_raw_scaled:
        nt = dict(t)
        nt["engine"] = "NSX_AMD_no_1D_gate"
        nt["asset"] = "NSXUSD"
        nt["cost_usd"] = 2.0
        nt["gross_usd"] = float(nt["gross_usd"] * 10.0)
        nt["net_usd"] = float(nt["net_usd"] * 10.0)
        nt["risk_usd"] = float(nt["risk_usd"] * 10.0)
        nt["net_r"] = float(nt["net_usd"] / nt["risk_usd"])
        nt["gross_r"] = float(nt["gross_usd"] / nt["risk_usd"])
        for key in ("entry_price", "sl_price", "tp_price", "exit_price"):
            nt[key] = float(nt[key] * 10.0)
        amd_raw.append(nt)
    nsx_no_1d = lock_single_position(amd_raw + copy_trades(v8["nsx_1h_10r"], "NSXUSD"))

    print("Running BTC no-09:00 and no-BE ablation ...", flush=True)
    btc_no_gates = run_engine_sniper_htf(
        frames["BTCUSD"], EV0, EV1,
        asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=None, be_lock_r=1.5,
        use_killzone=False, min_hour_utc=None, cost=0.0, pct_cost=0.0008,
        engine_label="BTC_15R_no_BE_no_09h",
    )

    variants = {
        "V8_current": portfolio(xau_current, nsx_current, btc_current),
        "V8_no_XAU_13_14_filter": portfolio(xau_no_cash_skip, nsx_current, btc_current),
        "V8_no_NSX_09h_filter": portfolio(xau_current, nsx_no_hour, btc_current),
        "V8_no_NSX_1D_gate": portfolio(xau_current, nsx_no_1d, btc_current),
        "V8_no_BTC_09h_BE": portfolio(xau_current, nsx_current, btc_no_gates),
        "V8_all_selected_time_regime_filters_removed": portfolio(xau_no_cash_skip, nsx_no_hour, btc_no_gates),
    }
    for name, rows in variants.items():
        pd.DataFrame(rows).to_csv(RES / f"trades_{name}.csv", index=False)
    return variants


def main() -> None:
    frames = load_frames()
    print({k: len(v) for k, v in frames.items()}, flush=True)
    variants = prepare_variants(frames)
    v7_path = PKG / "results" / "trades_v7_3asset_1pos_each.csv"
    v7 = pd.read_csv(v7_path).to_dict("records")
    for t in v7:
        t["asset"] = t.get("asset", "unknown")
    variants["V7_reference_from_artifact"] = v7

    out: dict[str, Any] = {
        "evaluation_window": {"start": str(EV0), "end": str(EV1), "holdout_start": str(TRAIN_END)},
        "variants": {name: periods(rows) for name, rows in variants.items()},
        "nsx_er_regime_overlap": {
            "XAUUSD": overlap_days(frames["XAUUSD"]),
            "NSXUSD": overlap_days(frames["NSXUSD"]),
            "BTCUSD": overlap_days(frames["BTCUSD"]),
        },
        "source_hashes": {
            "V8_3Asset_1PosEach_QC.py": sha(PKG / "exports" / "quantconnect" / "V8_3Asset_1PosEach_QC.py"),
            "smc_v4_portfolio.py": sha(PKG / "engine" / "smc_v4_portfolio.py"),
            "smc_core.py": sha(PKG / "exports" / "quantconnect" / "smc_core.py"),
        },
    }
    (RES / "summary_principles_audit.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Saved", RES / "summary_principles_audit.json", flush=True)


if __name__ == "__main__":
    main()
