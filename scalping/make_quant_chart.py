#!/usr/bin/env python3
"""Generate 2x2 verification chart -> scalping/outputs/quant_hybrid_performance.png."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quant_hybrid import (
    HybridParams,
    combine_hybrid,
    expanding_walk_forward,
    load_resampled_frames,
    run_cont_1h_ema,
    run_discrete_4h_sleeves,
    summarize_daily_returns,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = load_resampled_frames(use_cache=True)

    dr1, tr1 = run_discrete_4h_sleeves(frames, fee=0.0005, slip=0.0002)
    wf1, _, _ = expanding_walk_forward(dr1, tr1)
    ema1, _ = run_cont_1h_ema(frames, cost=0.0007, params=HybridParams(short_floor=0.0))

    dr2, tr2 = run_discrete_4h_sleeves(frames, fee=0.0010, slip=0.0004)
    wf2, _, _ = expanding_walk_forward(dr2, tr2)
    ema2, _ = run_cont_1h_ema(frames, cost=0.0014, params=HybridParams(short_floor=0.0))

    hyb_2 = combine_hybrid(wf1, ema1, 0.020).loc["2021-01-01":]
    hyb_3 = combine_hybrid(wf1, ema1, 0.030).loc["2021-01-01":]
    wf_2 = (wf1 * 0.020).loc["2021-01-01":]
    hyb_s2 = combine_hybrid(wf2, ema2, 0.020).loc["2021-01-01":]

    eq_h2 = 100.0 * (1.0 + hyb_2).cumprod()
    eq_h3 = 100.0 * (1.0 + hyb_3).cumprod()
    eq_wf2 = 100.0 * (1.0 + wf_2).cumprod()
    eq_s2 = 100.0 * (1.0 + hyb_s2).cumprod()

    m_h2 = ((1.0 + hyb_2).resample("ME").prod() - 1.0) * 100.0
    m_h3 = ((1.0 + hyb_3).resample("ME").prod() - 1.0) * 100.0

    y_h2 = ((1.0 + hyb_2).resample("YE").prod() - 1.0) * 100.0
    y_wf2 = ((1.0 + wf_2).resample("YE").prod() - 1.0) * 100.0

    plt.style.use("dark_background")
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), dpi=150)
    fig.patch.set_facecolor("#0d1117")
    for ax in axes.flat:
        ax.set_facecolor("#161b22")
        ax.grid(alpha=0.22, linestyle="--")

    # Panel A: Equity curves (log scale)
    ax = axes[0, 0]
    ax.plot(eq_h3.index, eq_h3.values, color="#3fb950", lw=2.0, label=f"QUANT-HYBRID r=3% (${eq_h3.iloc[-1]:,.0f})")
    ax.plot(eq_h2.index, eq_h2.values, color="#58a6ff", lw=2.0, label=f"QUANT-HYBRID r=2% (${eq_h2.iloc[-1]:,.0f})")
    ax.plot(eq_wf2.index, eq_wf2.values, color="#d2a8ff", lw=1.6, linestyle="--", label=f"WF-4h BreakoutSweep r=2% (${eq_wf2.iloc[-1]:,.0f})")
    ax.plot(eq_s2.index, eq_s2.values, color="#f0883e", lw=1.6, label=f"HYBRID 2x Stress (0.28% RT) (${eq_s2.iloc[-1]:,.0f})")
    ax.axhline(100.0, color="#8b949e", lw=0.9, linestyle=":")
    ax.set_yscale("log")
    ax.set_title("A. Strict OOS Walk-Forward Equity ($100 Start, Log, 2021-2026)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Account Equity (USD)")
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.85)

    # Panel B: Monthly return histogram
    ax = axes[0, 1]
    bins = np.linspace(-35, 45, 25)
    ax.hist(m_h2.values, bins=bins, alpha=0.72, color="#58a6ff", edgecolor="#0d1117", label=f"Hybrid r=2% (med {m_h2.median():+.1f}%, >=10%: {(m_h2>=10).sum()}/71)")
    ax.hist(m_h3.values, bins=bins, alpha=0.45, color="#3fb950", edgecolor="#0d1117", label=f"Hybrid r=3% (med {m_h3.median():+.1f}%, >=10%: {(m_h3>=10).sum()}/71)")
    ax.axvline(10.0, color="#f85149", lw=1.8, linestyle="--", label="+10%/mo target threshold")
    ax.axvline(0.0, color="#c9d1d9", lw=1.0, linestyle=":")
    ax.set_title("B. Monthly Return Distribution (71 OOS Months, 0.14% RT)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Monthly Return (%)")
    ax.set_ylabel("Months Count")
    ax.set_ylim(0, 12.6)
    ax.legend(loc="upper right", fontsize=8.2, framealpha=0.9)

    # Panel C: Annual returns 2021-2026
    ax = axes[1, 0]
    years = [idx.year for idx in y_h2.index]
    x = np.arange(len(years))
    w = 0.36
    b1 = ax.bar(x - w / 2, y_h2.values, width=w, color="#58a6ff", label="QUANT-HYBRID r=2% (6/6 yrs+)")
    b2 = ax.bar(x + w / 2, y_wf2.values, width=w, color="#d2a8ff", label="WF-4h BreakoutSweep r=2% (6/6 yrs+)")
    ax.axhline(0.0, color="#c9d1d9", lw=0.9)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 3.0, f"{h:+.0f}%", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([str(yr) for yr in years])
    ax.set_title("C. Annual OOS Returns by Year (All 6 Years Positive)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Annual Return (%)")
    ax.set_ylim(-10, max(y_h2.max(), y_wf2.max()) * 1.16)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.9)

    # Panel D: Cost Tier & Risk-Level Summary
    ax = axes[1, 1]
    dr0, tr0 = run_discrete_4h_sleeves(frames, fee=0.00035, slip=0.0002)
    wf0, _, _ = expanding_walk_forward(dr0, tr0)
    ema0, _ = run_cont_1h_ema(frames, cost=0.00055, params=HybridParams(short_floor=0.0))

    risks = [0.015, 0.020, 0.025, 0.030]
    labels = ["1.5%", "2.0%", "2.5%", "3.0%"]
    g_maker = [summarize_daily_returns(combine_hybrid(wf0, ema0, r))["geo_month_pct"] for r in risks]
    g_taker = [summarize_daily_returns(combine_hybrid(wf1, ema1, r))["geo_month_pct"] for r in risks]
    g_stress = [summarize_daily_returns(combine_hybrid(wf2, ema2, r))["geo_month_pct"] for r in risks]
    dds = [summarize_daily_returns(combine_hybrid(wf1, ema1, r))["max_dd_pct"] for r in risks]

    xr = np.arange(len(risks))
    ax.plot(xr, g_maker, "o-", color="#3fb950", lw=2.0, label="Maker+Taker (0.11% RT)")
    ax.plot(xr, g_taker, "s-", color="#58a6ff", lw=2.0, label="Taker+Slip (0.14% RT)")
    ax.plot(xr, g_stress, "^-", color="#f0883e", lw=2.0, label="2x Stress (0.28% RT)")
    ax.axhline(10.0, color="#f85149", lw=1.4, linestyle="--", label="10%/mo target ceiling")
    for i, (gm, gt, dd) in enumerate(zip(g_maker, g_taker, dds)):
        ax.annotate(f"{gt:.1f}%/mo\n(DD {dd:.0f}%)", (xr[i], gm), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=7.8, color="#c9d1d9")
    ax.set_xticks(xr)
    ax.set_xticklabels([f"Risk {l}" for l in labels])
    ax.set_xlim(-0.35, 3.35)
    ax.set_ylim(0, 11.4)
    ax.set_ylabel("Geometric Monthly Growth (%/mo)")
    ax.set_title("D. Monthly Compound Growth vs Cost & Drawdown Tradeoff", fontsize=11, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8.2, framealpha=0.85)

    fig.suptitle(
        "QUANT-HYBRID v1 (WF-4h Breakout/Sweep + 1h Multi-Speed EMA)  |  Strict Walk-Forward OOS 2021-2026",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = OUT / "quant_hybrid_performance.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved chart -> {out_path}")


if __name__ == "__main__":
    main()
