"""Split the combined BTC time/BE ablation into one change at a time.

The XAU and NSX rows are taken from the saved V8 reference artifact.  Only the
BTC engine is rerun, so the two candidate files differ from V8 in exactly one
BTC policy at a time:
  * remove only the 09:00 UTC gate, retain BE@3R(+1R);
  * retain the 09:00 UTC gate, remove BE@3R.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "smc_v4_multisleeve_package"
HERE = Path(__file__).resolve().parent
RES = HERE / "results"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from engine.causal_primitives import load_asset_ohlcv  # noqa: E402
from engine.smc_v4_portfolio import lock_single_position, run_engine_sniper_htf  # noqa: E402

EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")


def run_btc(df: pd.DataFrame, *, min_hour_utc: int | None, be_act_r: float | None, label: str) -> list[dict]:
    return run_engine_sniper_htf(
        df, EV0, EV1,
        asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=be_act_r, be_lock_r=1.0,
        use_killzone=False, min_hour_utc=min_hour_utc, cost=0.0, pct_cost=0.0008,
        engine_label=label,
    )


def main() -> None:
    current_path = RES / "trades_V8_current.csv"
    current = pd.read_csv(current_path)
    non_btc = current.loc[current["asset"] != "BTCUSD"].to_dict("records")
    months = [str(y) for y in range(2019, 2027)]
    btc = load_asset_ohlcv(PKG / "data" / "BTCUSD_5m", months)
    btc = btc.loc[btc.index < EV1]
    variants = {
        "V8_no_BTC_09h_only": run_btc(btc, min_hour_utc=None, be_act_r=3.0, label="BTC_15R_BE_no_09h"),
        "V8_no_BTC_BE_only": run_btc(btc, min_hour_utc=9, be_act_r=None, label="BTC_15R_no_BE"),
    }
    for name, btc_rows in variants.items():
        rows = non_btc + lock_single_position(btc_rows)
        rows.sort(key=lambda row: pd.Timestamp(row["exit_time"]))
        pd.DataFrame(rows).to_csv(RES / f"trades_{name}.csv", index=False)
        print(name, "BTC raw", len(btc_rows), "portfolio", len(rows), flush=True)


if __name__ == "__main__":
    main()
