#!/usr/bin/env python3
"""Full reproducible Walk-Forward verification for QUANT-HYBRID v1 & WF_4h_BreakoutSweep.

Usage:
    python3 run_quant_hybrid.py                # full audit (3 cost tiers + sensitivity + outputs)
    python3 run_quant_hybrid.py --quick        # skip +-20% parameter plateau sweep
    python3 run_quant_hybrid.py --live-signals # print latest causal signal weights
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from quant_hybrid import (
    HybridParams,
    combine_hybrid,
    current_signals,
    expanding_walk_forward,
    load_resampled_frames,
    run_cont_1h_ema,
    run_discrete_4h_sleeves,
    summarize_daily_returns,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"

COST_TIERS = (
    ("maker_taker_0.11pct", "Binance Futures Maker+Taker (0.11% RT)", 0.00035, 0.0002, 0.00055),
    ("taker_slip_0.14pct", "Futures Taker+Slip (0.14% RT)", 0.00050, 0.0002, 0.00070),
    ("stress_2x_0.28pct", "Stress 2x Cost (0.28% RT)", 0.00100, 0.0004, 0.00140),
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="Skip +-20% sensitivity sweep")
    ap.add_argument("--live-signals", action="store_true", help="Show latest causal weights")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    frames = load_resampled_frames(use_cache=True)

    if args.live_signals:
        print(json.dumps(current_signals(frames), indent=2))
        return

    summary: dict[str, dict] = {"cost_tiers": {}, "active_sleeves_by_year": {}}
    monthly_export: dict[str, pd.Series] = {}

    for key, label, fee, slip, c_cost in COST_TIERS:
        print(f"\n=== {label} ===")
        dr_df, tr_map = run_discrete_4h_sleeves(frames, fee=fee, slip=slip)
        wf_r, active_yr, oos_trades = expanding_walk_forward(dr_df, tr_map)
        ema_l, _ = run_cont_1h_ema(frames, cost=c_cost, params=HybridParams(short_floor=0.0))

        if key == "taker_slip_0.14pct":
            summary["active_sleeves_by_year"] = {str(y): cols for y, cols in active_yr.items()}
            summary["wf_4h_oos_trades"] = {
                "count": int(len(oos_trades)),
                "net_r": round(float(oos_trades["net_r"].sum()), 2),
                "win_rate_pct": round(100.0 * float((oos_trades["net_r"] > 0).mean()), 2),
                "profit_factor": round(
                    float(
                        oos_trades.loc[oos_trades["net_r"] > 0, "net_r"].sum()
                        / abs(oos_trades.loc[oos_trades["net_r"] < 0, "net_r"].sum())
                    ),
                    3,
                ),
            }

        tier_results: dict[str, dict] = {}
        for r_pct in (0.015, 0.020, 0.025, 0.030):
            wf_series = wf_r * r_pct
            hyb_series = combine_hybrid(wf_r, ema_l, risk_pct=r_pct)
            run_boot = r_pct == 0.020

            wf_name = f"WF_4h_r{r_pct*100:.1f}pct"
            hyb_name = f"Hybrid_r{r_pct*100:.1f}pct"
            tier_results[wf_name] = summarize_daily_returns(wf_series, run_bootstrap=run_boot)
            tier_results[hyb_name] = summarize_daily_returns(hyb_series, run_bootstrap=run_boot)

            for nm, st in ((wf_name, tier_results[wf_name]), (hyb_name, tier_results[hyb_name])):
                print(
                    f"  {nm:18s}: $100->${st['final_100usd']:>9,.2f}  Sh={st['sharpe']:4.2f}  "
                    f"DD={st['max_dd_pct']:4.1f}%  gmo={st['geo_month_pct']:5.2f}%  "
                    f"med={st['median_month_pct']:5.2f}%  m>0={st['positive_months']}/{st['months']}  "
                    f"m>=10%={st['months_ge_10pct']}/{st['months']}  worst={st['worst_month_pct']:5.1f}%"
                    + (f"  p={st['p_bootstrap']:.4f} DSR={st['deflated_sharpe_700']:.3f}" if run_boot else "")
                )

            if key == "taker_slip_0.14pct" and r_pct in (0.020, 0.030):
                tag = f"{int(r_pct*100)}pct"
                monthly_export[f"wf4h_{tag}"] = ((1.0 + wf_series.loc["2021-01-01":]).resample("ME").prod() - 1.0) * 100.0
                monthly_export[f"hybrid_{tag}"] = ((1.0 + hyb_series.loc["2021-01-01":]).resample("ME").prod() - 1.0) * 100.0
            if key == "stress_2x_0.28pct" and r_pct == 0.020:
                monthly_export["hybrid_stress2x_2pct"] = ((1.0 + hyb_series.loc["2021-01-01":]).resample("ME").prod() - 1.0) * 100.0

        summary["cost_tiers"][key] = tier_results

    if monthly_export:
        mdf = pd.DataFrame(monthly_export).round(2)
        mdf.index = mdf.index.strftime("%Y-%m")
        mdf.index.name = "month"
        mdf.to_csv(OUT / "quant_hybrid_monthly.csv")
        print(f"\nSaved monthly table -> {OUT / 'quant_hybrid_monthly.csv'} ({len(mdf)} months)")

    if not args.quick:
        print("\n=== +-20% Parameter Plateau Sensitivity (0.14% RT, Hybrid r=2.0%) ===")
        base_ema = run_cont_1h_ema(frames, cost=0.0007, params=HybridParams(short_floor=0.0))[0]
        variants = [
            ("BASE (k1.5, dc30, sl2, tr3, d50)", HybridParams(short_floor=0.0), False),
            ("4h kelt=1.2 (-20%)", HybridParams(kelt_mult=1.2, short_floor=0.0), False),
            ("4h kelt=1.8 (+20%)", HybridParams(kelt_mult=1.8, short_floor=0.0), False),
            ("4h dc=24 (-20%)", HybridParams(dc_win=24, short_floor=0.0), False),
            ("4h dc=36 (+20%)", HybridParams(dc_win=36, short_floor=0.0), False),
            ("4h sl=1.6 tr=2.4 (-20%)", HybridParams(sl_mult=1.6, trail_mult=2.4, short_floor=0.0), False),
            ("4h sl=2.4 tr=3.6 (+20%)", HybridParams(sl_mult=2.4, trail_mult=3.6, short_floor=0.0), False),
            ("4h d1_ema=40 (-20%)", HybridParams(d1_ema_slow=40, short_floor=0.0), False),
            ("4h d1_ema=60 (+20%)", HybridParams(d1_ema_slow=60, short_floor=0.0), False),
            ("1h speeds (4,8,16,32,64)", HybridParams(speeds_days=(4, 8, 16, 32, 64), short_floor=0.0), True),
            ("1h speeds (6,12,24,48,96)", HybridParams(speeds_days=(6, 12, 24, 48, 96), short_floor=0.0), True),
            ("1h vol_days=15 (-25%)", HybridParams(vol_days=15, short_floor=0.0), True),
            ("1h vol_days=25 (+25%)", HybridParams(vol_days=25, short_floor=0.0), True),
        ]
        sens_rows = []
        for label, p, recalc_ema in variants:
            dr_v, tr_v = run_discrete_4h_sleeves(frames, fee=0.0005, slip=0.0002, params=p)
            wf_v, _, _ = expanding_walk_forward(dr_v, tr_v, params=p)
            ema_v = run_cont_1h_ema(frames, cost=0.0007, params=p)[0] if recalc_ema else base_ema
            st = summarize_daily_returns(combine_hybrid(wf_v, ema_v, risk_pct=0.020))
            st["variant"] = label
            sens_rows.append(st)
            print(f"  {label:34s}: $100->${st['final_100usd']:>8,.2f}  Sh={st['sharpe']:4.2f}  DD={st['max_dd_pct']:4.1f}%  gmo={st['geo_month_pct']:5.2f}%")
        pd.DataFrame(sens_rows).to_csv(OUT / "quant_hybrid_sensitivity.csv", index=False)
        summary["sensitivity_count"] = len(sens_rows)

    (OUT / "quant_hybrid_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Saved summary JSON -> {OUT / 'quant_hybrid_summary.json'}")


if __name__ == "__main__":
    main()
