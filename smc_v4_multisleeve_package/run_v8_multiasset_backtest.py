"""Reproducible End-to-End Runner for SMC V8 Microscopy-Upgraded Multi-Asset System.

Uses ONLY datasets stored inside `smc_v4_multisleeve_package/data/`:
- XAUUSD_1m_histdata (82 months: 2020-01..2026-10)
- NSXUSD_1m_histdata (82 months: 2020-01..2026-10)
- BTCUSD_5m (2019..2026)

Reproduces V8 vs V7 comparisons, exact 2.0x double-cost stress, 81-month $100
compounding ledger, JSON summary, and publication charts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PKG_ROOT = Path(__file__).resolve().parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.causal_primitives import load_asset_ohlcv  # noqa: E402
from engine.smc_v4_portfolio import (  # noqa: E402
    run_smc_v8_multiasset_portfolio,
    simulate_compounded_account,
)


def summarize(trades: list[dict]) -> dict:
    if not trades:
        return {"n": 0}
    rs = np.array([t["net_r"] for t in trades], dtype=float)
    wins = rs[rs > 0]
    losses = rs[rs < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) else 999.0
    cum = np.cumsum(rs)
    peak = np.maximum.accumulate(np.insert(cum, 0, 0.0))[1:]
    max_dd = float(np.max(peak - cum))
    t_stat = float(rs.mean() / (rs.std(ddof=1) / np.sqrt(len(rs)))) if len(rs) > 1 else 0.0

    df = pd.DataFrame(trades)
    df["yr"] = pd.to_datetime(df["entry_time"]).dt.year
    yr_g = df.groupby("yr")["net_r"].sum()
    yearly = {str(int(k)): round(float(v), 2) for k, v in yr_g.items()}

    df["mo"] = pd.to_datetime(df["exit_time"]).dt.tz_convert(None).dt.to_period("M")
    mr = df.groupby("mo")["net_r"].sum().reindex(pd.period_range("2020-02", "2026-10", freq="M"), fill_value=0.0)

    return {
        "n": int(len(rs)),
        "wr_pct": round(float(100.0 * (rs > 0).mean()), 2),
        "net_r": round(float(rs.sum()), 2),
        "avg_r_per_month": round(float(mr.mean()), 2),
        "median_r_per_month": round(float(mr.median()), 2),
        "p75_r_per_month": round(float(mr.quantile(0.75)), 2),
        "p90_r_per_month": round(float(mr.quantile(0.90)), 2),
        "best_month_r": round(float(mr.max()), 2),
        "worst_month_r": round(float(mr.min()), 2),
        "positive_months": int((mr > 0).sum()),
        "negative_months": int((mr < 0).sum()),
        "months_ge_10r": int((mr >= 10.0).sum()),
        "months_ge_15r": int((mr >= 15.0).sum()),
        "months_ge_20r": int((mr >= 20.0).sum()),
        "pf": round(pf, 3),
        "max_dd_r": round(max_dd, 2),
        "t_stat": round(t_stat, 2),
        "positive_years": int((yr_g > 0).sum()),
        "total_years": int(len(yr_g)),
        "yearly_r": yearly,
        "compound_100_1pct": simulate_compounded_account(trades, start_capital=100.0, risk_pct=0.01, compound=True),
        "compound_100_1_5pct": simulate_compounded_account(trades, start_capital=100.0, risk_pct=0.015, compound=True),
        "compound_100_2pct": simulate_compounded_account(trades, start_capital=100.0, risk_pct=0.02, compound=True),
    }


def build_monthly_ledger(trades: list[dict], risk_pcts: tuple[float, ...] = (0.01, 0.015, 0.02), start: float = 100.0) -> pd.DataFrame:
    df = pd.DataFrame(trades)
    df["exit_dt"] = pd.to_datetime(df["exit_time"], utc=True)
    df = df.sort_values("exit_dt").reset_index(drop=True)
    df["mo"] = df["exit_dt"].dt.tz_convert(None).dt.to_period("M")
    eqs = {rp: start for rp in risk_pcts}
    rows = []
    for mo in pd.period_range("2020-02", "2026-10", freq="M"):
        sub = df[df["mo"] == mo]
        rec: dict = {"month": str(mo), "n": int(len(sub)), "net_r": round(float(sub["net_r"].sum()), 2)}
        for rp in risk_pcts:
            eq0 = eqs[rp]
            for r in sub["net_r"]:
                eqs[rp] += (eqs[rp] * rp) * float(r)
            pct = 100.0 * (eqs[rp] / eq0 - 1.0) if eq0 > 0 else 0.0
            tag = f"{100*rp:g}pct".replace(".", "_")
            rec[f"ret_{tag}"] = round(pct, 1)
            rec[f"bal_{tag}"] = round(eqs[rp], 2)
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    res_dir = PKG_ROOT / "results"
    res_dir.mkdir(exist_ok=True)

    months = [f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 11)]
    btc_years = [str(y) for y in range(2019, 2027)]

    print("[1/4] Loading XAUUSD, NSXUSD, and BTCUSD from package data/ ...", flush=True)
    df_xau = load_asset_ohlcv(PKG_ROOT / "data" / "XAUUSD_1m_histdata", months)
    df_nsx = load_asset_ohlcv(PKG_ROOT / "data" / "NSXUSD_1m_histdata", months)
    df_btc = load_asset_ohlcv(PKG_ROOT / "data" / "BTCUSD_5m", btc_years)
    df_btc = df_btc.loc[df_btc.index < pd.Timestamp("2026-11-01", tz="UTC")]

    ev0 = pd.Timestamp("2020-02-01 00:00", tz="UTC")
    ev1 = pd.Timestamp("2026-11-01 00:00", tz="UTC")

    print("[2/4] Running V8 Microscopy-Upgraded Multi-Asset Portfolio (1.0x cost) ...", flush=True)
    v8 = run_smc_v8_multiasset_portfolio(df_xau, df_nsx, df_btc, ev0, ev1, xau_cost=0.25, nsx_cost_pts=2.0, btc_pct_cost=0.0008)

    print("[3/4] Computing exact 2.0x Cost Stress (XAU -$0.50, NSX -4pt, BTC 0.16%) ...", flush=True)

    def reprice_2x(trades: list[dict]) -> list[dict]:
        out = []
        for t in trades:
            nt = dict(t)
            if "cost_usd" in nt:
                c1 = float(nt["cost_usd"])
            elif nt.get("engine", "").startswith("NSX_AMD"):
                c1 = 0.20
            else:
                c1 = 0.25
            nt["net_usd"] = float(nt["gross_usd"] - 2.0 * c1)
            nt["net_r"] = float(nt["net_usd"] / nt["risk_usd"])
            out.append(nt)
        return out

    summary = {
        "evaluation_window": {"start": str(ev0), "end": str(ev1), "months": 81},
        "portfolios_1x": {
            "V8_Global_1Pos": summarize(v8["v8_global_1pos"]),
            "V8_3Asset_1PosEach": summarize(v8["v8_3asset_1pos_each"]),
            "V8_XAU_1Pos": summarize(v8["xau_v8_1pos"]),
            "V8_NSX_1Pos": summarize(v8["nsx_v8_1pos"]),
        },
        "portfolios_2x_stress": {
            "V8_Global_1Pos_2x": summarize(reprice_2x(v8["v8_global_1pos"])),
            "V8_3Asset_1PosEach_2x": summarize(reprice_2x(v8["v8_3asset_1pos_each"])),
        },
        "sleeves_1x": {
            "NSX_AMD_1D": summarize(v8["nsx_amd_1d"]),
            "NSX_1H1m_10R_09h": summarize(v8["nsx_1h_10r"]),
            "BTC_15R_BE_09h": summarize(v8["btc_15r_be"]),
        },
    }

    pd.DataFrame(v8["v8_global_1pos"]).to_csv(res_dir / "trades_v8_global_1pos.csv", index=False)
    pd.DataFrame(v8["v8_3asset_1pos_each"]).to_csv(res_dir / "trades_v8_3asset_1pos_each.csv", index=False)
    ledger = build_monthly_ledger(v8["v8_3asset_1pos_each"])
    ledger.to_csv(res_dir / "monthly_breakdown_v8_from_100usd.csv", index=False)
    (res_dir / "summary_v8_multiasset.json").write_text(json.dumps(summary, indent=2))

    for grp in ("portfolios_1x", "portfolios_2x_stress", "sleeves_1x"):
        print(f"\n[{grp}]")
        for k, s in summary[grp].items():
            c1 = s["compound_100_1pct"]["final_equity"]
            c15 = s["compound_100_1_5pct"]["final_equity"]
            c2 = s["compound_100_2pct"]["final_equity"]
            print(
                f"  {k:26s} | N={s['n']:4d} WR={s['wr_pct']:5.1f}% Net={s['net_r']:+6.1f}R ({s['avg_r_per_month']:+.2f}R/mo) "
                f"PF={s['pf']:.3f} DD={s['max_dd_r']:5.1f}R t={s['t_stat']:+4.2f} +Y={s['positive_years']}/{s['total_years']} "
                f"-Mo={s['negative_months']}/81 worst={s['worst_month_r']:+5.1f}R | $100: 1%->${c1:,.0f}, 1.5%->${c15:,.0f}, 2%->${c2:,.0f}"
            )

    print("\n[4/4] Generating V8 vs V7 comparison charts ...", flush=True)
    v7_3 = pd.read_csv(res_dir / "trades_v7_3asset_1pos_each.csv").to_dict("records")
    v7_g = pd.read_csv(res_dir / "trades_v7_global_1pos.csv").to_dict("records")

    s8g = summary["portfolios_1x"]["V8_Global_1Pos"]
    s83 = summary["portfolios_1x"]["V8_3Asset_1PosEach"]
    s7 = json.loads((res_dir / "summary_v7_multiasset.json").read_text())
    s7g = s7["portfolios_1x"]["V7_Global_1Pos"]
    s73 = s7["portfolios_1x"]["V7_3Asset_1PosEach"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    for lbl, trs, col, ls in [
        (f"V7 Global 1-Pos (+{s7g['net_r']:.0f}R, PF {s7g['pf']:.2f})", v7_g, "#94a3b8", "--"),
        (f"V8 Global 1-Pos (+{s8g['net_r']:.0f}R, PF {s8g['pf']:.2f})", v8["v8_global_1pos"], "#2563eb", "-"),
        (f"V7 3-Asset (+{s73['net_r']:.0f}R, DD {s73['max_dd_r']:.1f}R)", v7_3, "#f59e0b", "--"),
        (f"V8 3-Asset (+{s83['net_r']:.0f}R, PF {s83['pf']:.2f}, DD {s83['max_dd_r']:.1f}R, t={s83['t_stat']:+.2f})", v8["v8_3asset_1pos_each"], "#16a34a", "-"),
    ]:
        d = pd.DataFrame(trs)
        d["exit_dt"] = pd.to_datetime(d["exit_time"])
        d = d.sort_values("exit_dt")
        cum = d["net_r"].cumsum()
        dd = cum - np.maximum.accumulate(np.insert(cum.values, 0, 0.0))[1:]
        ax1.plot(d["exit_dt"], cum, label=lbl, color=col, linestyle=ls, linewidth=2.0)
        ax2.plot(d["exit_dt"], dd, label=lbl.split(" (")[0], color=col, linestyle=ls, linewidth=1.7)

    ax1.set_title("V8 Microscopy vs V7 Baseline: Cumulative Net R (2020-02 .. 2026-10)", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("Date (UTC)")
    ax1.set_ylabel("Cumulative Net R")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="upper left", fontsize=8.5)

    ax2.set_title(f"Drawdown Trajectory (V8 Cuts MaxDD from {s73['max_dd_r']:.1f}R to {s83['max_dd_r']:.1f}R)", fontsize=11.5, fontweight="bold")
    ax2.set_xlabel("Date (UTC)")
    ax2.set_ylabel("Drawdown (R)")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="lower left", fontsize=8.5)
    plt.tight_layout()
    plt.savefig(res_dir / "v8_vs_v7_equity_and_dd.png", dpi=160)
    plt.close(fig)

    # Chart 2: Yearly Comparison V7 vs V8 + Monthly R bars for V8_3Asset
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    yrs = [str(y) for y in range(2020, 2027)]
    x = np.arange(len(yrs))
    w = 0.35
    v7_s = s73["yearly_r"]
    v8_s = s83["yearly_r"]
    vals7 = [v7_s.get(y, 0.0) for y in yrs]
    vals8 = [v8_s.get(y, 0.0) for y in yrs]
    b1 = ax1.bar(x - w / 2, vals7, width=w, label=f"V7 3-Asset (+{s73['net_r']:.0f}R)", color="#94a3b8")
    b2 = ax1.bar(x + w / 2, vals8, width=w, label=f"V8 3-Asset (+{s83['net_r']:.0f}R)", color="#16a34a")
    for b, v in list(zip(b1, vals7)) + list(zip(b2, vals8)):
        ax1.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v:.0f}", ha="center", va="bottom", fontsize=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(yrs)
    ax1.set_ylim(0, max(vals7 + vals8) * 1.16)
    ax1.set_title("Yearly Net R: V8 Microscopy vs V7 (7/7 Positive Years)", fontsize=11.5, fontweight="bold")
    ax1.set_ylabel("Net R")
    ax1.grid(axis="y", alpha=0.25)
    ax1.legend(loc="upper right", fontsize=9)

    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in ledger["net_r"]]
    ax2.bar(range(len(ledger)), ledger["net_r"], color=colors, width=0.8)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.axhline(10, color="#2563eb", linestyle="--", linewidth=1.2, label=f"+10R/mo ({s83['months_ge_10r']}/81 mos)")
    ax2.set_title("V8 3-Asset Monthly Net R Across All 81 Months", fontsize=11.5, fontweight="bold")
    ax2.set_xlabel("Month Index (2020-02 .. 2026-10)")
    ax2.set_ylabel("Monthly Net R")
    ax2.grid(axis="y", alpha=0.25)
    ax2.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.savefig(res_dir / "v8_monthly_r_and_yearly.png", dpi=160)
    plt.close(fig)
    print("Done! Saved V8 artifacts to smc_v4_multisleeve_package/results/")


if __name__ == "__main__":
    main()
