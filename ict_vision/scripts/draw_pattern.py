"""Draw the 15m 'hammer after the raid' setup: a labelled schematic plus a real
detected example from the data, so the description can be checked by eye."""

from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ict_vision.data.loader import load_all
from ict_vision.scripts.scalp_15m import build_setups, resolve_all, map_15m_to_1m

UP, DN = "#26a69a", "#ef5350"
ENTRY, STOP, TGT, MID, FVG = "#1565c0", "#c62828", "#2e7d32", "#6a1b9a", "#ffcc80"


def candles(ax, o, h, l, c, w=0.62):
    for i in range(len(o)):
        up = c[i] >= o[i]
        col = UP if up else DN
        ax.plot([i, i], [l[i], h[i]], color=col, lw=1.1, zorder=2)
        ax.add_patch(Rectangle((i - w / 2, min(o[i], c[i])), w,
                               max(abs(c[i] - o[i]), 1e-9),
                               facecolor=col, edgecolor=col, zorder=3))


def hline(ax, y, x0, x1, color, label, ls="--", lw=1.4):
    ax.hlines(y, x0, x1, color=color, ls=ls, lw=lw, zorder=4)
    ax.annotate(label, (x1, y), xytext=(6, 0), textcoords="offset points",
                color=color, fontsize=9, fontweight="bold", va="center", zorder=5)


def schematic(ax):
    """Candles built to embody the setup exactly as described."""
    O = [105.5, 104.9, 102.8, 100.9, 99.4, 96.5, 96.4, 96.6, 101.2, 100.3, 100.6, 101.5, 103.0, 104.5, 106.2]
    H = [106.0, 105.0, 103.2, 101.0, 99.6, 96.8, 96.9, 101.5, 101.6, 100.8, 101.2, 102.6, 103.9, 105.0, 106.4]
    L = [104.8, 102.5, 100.5, 99.0, 96.2, 94.3, 96.2, 96.5, 99.6, 100.0, 100.2, 101.1, 102.8, 104.2, 105.6]
    C = [104.9, 102.8, 100.9, 99.4, 96.5, 96.4, 96.6, 101.2, 100.3, 100.6, 101.0, 102.4, 103.8, 104.9, 106.1]
    O, H, L, C = (np.array(x, float) for x in (O, H, L, C))
    n = len(O)
    candles(ax, O, H, L, C)

    SW_HI, SW_LO, RAID, C1, C2 = 0, 4, 5, 7, 8
    entry, stop = C[C2], L[C2] * (1 - 0.002)
    tgt = H[SW_HI] * (1 - 0.0002)
    mid = 0.5 * (O[C1] + C[C1])

    ax.add_patch(Rectangle((C1 - 0.5, H[C1 - 1]), 2.0, L[C2] - H[C1 - 1],
                           facecolor=FVG, alpha=0.45, zorder=1))
    ax.annotate("FAIR VALUE GAP\n(variant A)", (C1, 0.5 * (H[C1 - 1] + L[C2])),
                ha="center", va="center", fontsize=8.5, fontweight="bold", color="#8d5000", zorder=6)

    hline(ax, H[SW_HI], -0.5, SW_HI + 1, TGT, "target: 1st swing HIGH\n(a hair under its wick)")
    hline(ax, L[SW_LO], -0.5, RAID + 1, "#5d4037", "prior swing LOW\n(liquidity)", ":")
    hline(ax, entry, C2, n - 0.5, ENTRY, "ENTRY = close of C2")
    hline(ax, stop, C2, n - 0.5, STOP, "STOP = 0.2% below C2 low")
    hline(ax, mid, C1 - 0.4, C2 + 0.9, MID, "50% of C1", "-.")

    ax.annotate("RAID\nwick under the low,\nbody CLOSES back above",
                (RAID, L[RAID]), xytext=(0, -46), textcoords="offset points",
                ha="center", fontsize=8.5, color="#5d4037", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#5d4037", lw=1.2))
    ax.annotate("C1\nbig BULLISH\nreversal", (C1, H[C1]), xytext=(0, 30),
                textcoords="offset points", ha="center", fontsize=9,
                fontweight="bold", color="#2e7d32",
                arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.2))
    ax.annotate("C2 BEARISH\nwick must NOT reach 50%", (C2, H[C2]), xytext=(52, 44),
                textcoords="offset points", ha="center", fontsize=9,
                fontweight="bold", color="#c62828",
                arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.2))
    ax.set_title("THE SETUP AS I UNDERSTOOD IT  —  please check this against your chart",
                 fontsize=12, fontweight="bold", pad=30)
    ax.set_xlim(-1.2, n + 1.4)
    ax.set_ylim(L.min() - 1.6, H.max() + 2.6)
    ax.set_xticks(range(n)); ax.set_xticklabels([])
    ax.grid(alpha=0.18, ls=":")


def real_example(ax, b15, b5, m15_a, m15_b):
    S = build_setups(b15)
    R = resolve_all(S, b5, m15_a, m15_b, stop_pct=0.010)
    good = R[(R.res == "target") & R.fvg].sort_values("bars")
    pick = int(good.iloc[len(good) // 2]["t_c2"])
    j = pick
    a, b = max(0, j - 9), min(b15.n, j + 22)
    o, h, l, c = b15.o[a:b], b15.h[a:b], b15.l[a:b], b15.c[a:b]
    candles(ax, o, h, l, c)
    k = j - a
    entry, stop, tgt = c[k], l[k] * (1 - 0.002), float(R[R.t_c2 == j].iloc[0]["tgt_hi"]) if False else None
    row = S[S.t_c2 == j].iloc[0]
    tgt = float(row["tgt_hi"]) * (1 - 0.0002)
    hline(ax, entry, k, len(o) - 0.5, ENTRY, "entry")
    hline(ax, stop, k, len(o) - 0.5, STOP, "stop")
    hline(ax, tgt, k, len(o) - 0.5, TGT, "target")
    ax.annotate("C1", (k - 1, h[k - 1]), xytext=(0, 18), textcoords="offset points",
                ha="center", fontsize=9, fontweight="bold", color="#2e7d32",
                arrowprops=dict(arrowstyle="->", color="#2e7d32"))
    ax.annotate("C2", (k, h[k]), xytext=(34, 26), textcoords="offset points",
                ha="center", fontsize=9, fontweight="bold", color="#c62828",
                arrowprops=dict(arrowstyle="->", color="#c62828"))
    ax.set_title(f"REAL BTCUSD 15m example  —  {b15.idx[j]:%Y-%m-%d %H:%M}  (a winner, variant A)",
                 fontsize=11, fontweight="bold", pad=16)
    ax.set_xlim(-1, len(o) + 0.5)
    ax.set_xticks(range(0, len(o), 4))
    ax.set_xticklabels([f"{b15.idx[a+i]:%H:%M}" for i in range(0, len(o), 4)], fontsize=8)
    ax.grid(alpha=0.18, ls=":")


def main() -> int:
    out = "ict_vision/docs"
    os.makedirs(out, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(15, 12), gridspec_kw={"hspace": 0.34})
    schematic(axes[0])
    b5 = load_all("smc_v4_multisleeve_package/data/BTCUSD_5m", minutes=5, cache="/tmp/btc.pkl")
    b15 = load_all("smc_v4_multisleeve_package/data/BTCUSD_5m", minutes=15, cache="/tmp/btc.pkl")
    real_example(axes[1], b15, b5, *map_15m_to_1m(b15, b5))
    for ax in axes:
        ax.set_ylabel("price", fontsize=9)
        ax.tick_params(labelsize=8)
    fig.suptitle("15m scalper: liquidity raid -> big bullish C1 -> shallow bearish C2 -> entry on C2 close",
                 fontsize=13, fontweight="bold", y=0.965)
    path = os.path.join(out, "scalp_15m_pattern.png")
    fig.savefig(path, dpi=115, bbox_inches="tight", facecolor="white")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
