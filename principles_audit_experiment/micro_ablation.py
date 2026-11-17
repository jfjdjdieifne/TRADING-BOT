"""Small causal-principle ablations for the isolated matched engine.

This imports the already-separated htf_timeframe_experiment module; it does not
edit package source.  These tests are deliberately labelled as matched-engine
tests, not exact QuantConnect V8 results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from htf_timeframe_experiment import run_experiment as exp  # noqa: E402
from engine.causal_primitives import load_asset_ohlcv  # noqa: E402


KZ_ORIGINAL = exp.in_killzone_utc
ATR_ORIGINAL = exp.causal_atr14


def kz_dst_aware(ts: pd.Timestamp) -> bool:
    """Local-clock proxy: London 08:00-11:00 or New York 08:00-12:00."""
    london = ts.tz_convert(ZoneInfo("Europe/London"))
    new_york = ts.tz_convert(ZoneInfo("America/New_York"))
    return (8 <= london.hour < 11) or (8 <= new_york.hour < 12)


def atr_previous(highs, lows, closes, period=14):
    current = ATR_ORIGINAL(highs, lows, closes, period)
    out = np.full_like(current, np.nan)
    if len(current) > 1:
        out[1:] = current[:-1]
    return out


def run_case(frames, mode: str) -> dict:
    exp.in_killzone_utc = KZ_ORIGINAL
    exp.causal_atr14 = ATR_ORIGINAL
    if mode in {"dst", "dst_previous_atr"}:
        exp.in_killzone_utc = kz_dst_aware
    if mode in {"previous_atr", "dst_previous_atr"}:
        exp.causal_atr14 = atr_previous
    rows = []
    for spec in exp.ASSETS:
        variant = next(v for v in exp.VARIANTS if v.name == "LTF_control")
        tf = exp.CONTROL_SIGNAL_TF[spec.name]
        trades = exp.run_scaled_sniper(
            frames[spec.name], exp.EV0, exp.EV1,
            asset_spec=spec, variant=variant, signal_tf=tf,
        )
        rows.extend(trades)
    rows.sort(key=lambda t: pd.Timestamp(t["exit_time"]))
    def segment(start, end):
        subset = [t for t in rows if start <= pd.Timestamp(t["entry_time"]) < end]
        return exp.summarize(subset)
    return {
        "full": segment(exp.EV0, exp.EV1),
        "train_2020_2022": segment(exp.EV0, pd.Timestamp("2023-01-01", tz="UTC")),
        "holdout_2023_2026": segment(pd.Timestamp("2023-01-01", tz="UTC"), exp.EV1),
        "latest_2025_2026": segment(pd.Timestamp("2025-01-01", tz="UTC"), exp.EV1),
    }


def main() -> None:
    months = [f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 11)]
    frames = {
        "XAUUSD": load_asset_ohlcv(exp.PKG_ROOT / "data" / "XAUUSD_1m_histdata", months),
        "NSXUSD": load_asset_ohlcv(exp.PKG_ROOT / "data" / "NSXUSD_1m_histdata", months),
        "BTCUSD": load_asset_ohlcv(exp.PKG_ROOT / "data" / "BTCUSD_5m", [str(y) for y in range(2019, 2027)]),
    }
    frames["BTCUSD"] = frames["BTCUSD"].loc[frames["BTCUSD"].index < exp.EV1]
    out = {mode: run_case(frames, mode) for mode in ("original", "previous_atr", "dst", "dst_previous_atr")}
    (Path(__file__).resolve().parent / "results" / "micro_ablation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for name, s in out.items():
        print(name, s)


if __name__ == "__main__":
    main()
