#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v35_bleed_mechanics.py -- STEP 1 of v35: measure the three bleed holes
on the SAVED books of the v34 champion `S1_TEL_3R`, with the 5m candles read
back at every loser's entry bar.

It answers, in numbers only:

  A. STOP-WIDTH ANATOMY   every fill bucketed by stop_dist_pct
                          = (fill_px - stop_px)/fill_px, with n / W-BE-L /
                          WR% / totR / net$ / worst single loss, plus the
                          measured effect of a dollar-risk cap on the wide
                          boxes (RISK_CAP_PCT) and of refusing them outright.
  B. INSTANT-DEATH        the hold <= 0.5h autopsies: how many losers were
                          stopped inside their own fill bar, how many of the
                          44 big winners poked below the seam first, and
                          whether a touch-bar green-box respect gate would
                          have kept the winners.
  C. COLD STREAKS         per-coin streaks and the exact effect of a
                          PER_COIN_COOLDOWN (K consecutive losses -> C days
                          banned, optionally until a fresh 4H BOS up).
  D. THE MARCH 2024 CASE  the month that made +$25.49 on four fills and
                          closed at +$0.53, line by line.

Every counterfactual is FIRST-ORDER on the saved book: it removes or re-prices
the affected fills and keeps every other fill exactly as the engine executed
it (no re-compounding, no re-entry). That is the same discipline the v34
microscope used, and every table says so.

USAGE
    python3 audit_v35_bleed_mechanics.py            # all four sections
    python3 audit_v35_bleed_mechanics.py --only A,B
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DATA = HERE / "data" / "binance_5m"
sys.path.insert(0, str(HERE))

WINNER = "S1_TEL_3R"
WINDOWS = ("W1", "W2")
BIG_R = 3.0
W = 130

GRID = {"XRPUSDT": 4, "ADAUSDT": 4, "SOLUSDT": 2, "BNBUSDT": 2,
        "ETHUSDT": 2, "BTCUSDT": 2, "LINKUSDT": 3, "AVAXUSDT": 2}


def hdr(t):
    print("\n" + "=" * W); print(t); print("=" * W)


def sub(t):
    print("\n" + "-" * W); print(t); print("-" * W)


def book(win):
    d = pd.read_csv(RESULTS / f"trades_v34_{WINNER}_{win}.csv")
    for c in ("entry_time", "exit_time"):
        d[c] = pd.to_datetime(d[c], utc=True, format="mixed").dt.tz_localize(None)
    for c in ("R", "net_pnl", "entry_price", "exit_price", "stop_price",
              "risk_pct", "notional", "qty0", "bars_held", "mfe_R",
              "mfe_close_R", "v29_seam_px", "purple_mid"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["sym"] = d.symbol.str.split("_").str[0]
    d["cls"] = d["class"].astype(str)
    d["is_win"] = d.cls.isin(["WIN", "SWIN"])
    d["is_loss"] = d.cls.eq("LOSS")
    d["is_be"] = d.cls.isin(["BE", "BREAKEVEN"])
    d["hold_h"] = (d.exit_time - d.entry_time).dt.total_seconds() / 3600.0
    d["stop_dist_pct"] = 100.0 * (d.entry_price - d.stop_price) / d.entry_price
    # the export rounds the LINE columns to 2 dp; compare on the coin's own grid
    d["tick"] = 10.0 ** -d.sym.map(GRID).fillna(2)
    d["seam_gap_ticks"] = (d.entry_price - d.v29_seam_px) / d.tick
    d["pmid_gap_ticks"] = (d.entry_price - d.purple_mid) / d.tick
    return d.sort_values("entry_time").reset_index(drop=True)


def pf(g):
    gp = float(g.loc[g.net_pnl > 0, "net_pnl"].sum())
    gl = float(-g.loc[g.net_pnl < 0, "net_pnl"].sum())
    return (gp / gl) if gl > 1e-9 else float("inf")


def money(x):
    return f"{x:+.2f}"


# --------------------------------------------------------------------- #
# candle access (5m bars at the loser's own entry bar)
# --------------------------------------------------------------------- #
_CACHE: dict = {}


def bars_for(sym):
    """The 5m frame for one coin, from the SAME dataset the engine used."""
    if sym not in _CACHE:
        from engine.causal_primitives import load_asset_ohlcv
        _CACHE[sym] = load_asset_ohlcv(DATA / f"{sym}_5m")
    return _CACHE[sym]


def bar_at(sym, t):
    """The completed 5m bar whose [start, end) contains `t` (the fill bar)."""
    df = bars_for(sym)
    idx = df.index.searchsorted(pd.Timestamp(t).tz_localize("UTC"), side="right") - 1
    if idx < 0 or idx >= len(df):
        return None
    r = df.iloc[idx]
    return dict(open=float(r.Open), high=float(r.High), low=float(r.Low),
                close=float(r.Close), pos=idx)


def patch_through_origin(m):
    """The v29 order price implied by a fill that went THROUGH it: the fill is
    the bar OPEN whenever the bar opened below the resting limit."""
    return bool(m["entry_price"] < m["v29_seam_px"] - 1e-12)


# --------------------------------------------------------------------- #
# A. STOP-WIDTH ANATOMY
# --------------------------------------------------------------------- #
BUCKETS = [(0.0, 0.25, "< 0.25%"), (0.25, 0.50, "0.25-0.50%"),
           (0.50, 0.75, "0.50-0.75%"), (0.75, 1.00, "0.75-1.00%"),
           (1.00, 99.0, "> 1.00%")]


def section_a():
    hdr("A. STOP-WIDTH ANATOMY -- every S1_TEL_3R fill bucketed by stop_dist_pct")
    allrows = []
    for win in WINDOWS:
        d = book(win)
        print(f"\n  {win}: n={len(d)}  net ${d.net_pnl.sum():+.2f}  "
              f"median stop width {d.stop_dist_pct.median():.3f}%")
        print(f"  {'bucket':11s} {'n':>4s} {'W/BE/L':>10s} {'WR%':>6s} "
              f"{'totR':>9s} {'net$':>9s} {'avg$':>7s} {'worst single $':>26s}")
        for lo, hi, lab in BUCKETS:
            g = d[(d.stop_dist_pct >= lo) & (d.stop_dist_pct < hi)]
            if not len(g):
                print(f"  {lab:11s} {0:4d}  {'-':>10s}")
                continue
            w = g.loc[g.net_pnl.idxmin()]
            allrows.append(dict(win=win, lab=lab, n=len(g), net=g.net_pnl.sum()))
            print(f"  {lab:11s} {len(g):4d} "
                  f"{int(g.is_win.sum()):3d}/{int(g.is_be.sum()):2d}/{int(g.is_loss.sum()):2d}"
                  f"  {100*g.is_win.mean():6.1f} {g.R.sum():+9.2f} "
                  f"{g.net_pnl.sum():+9.2f} {g.net_pnl.mean():+7.2f} "
                  f"{w.sym:5s} {str(w.entry_time)[:16]} {w.stop_dist_pct:5.2f}% "
                  f"{w.net_pnl:+7.2f}")
        # the concentration question the brief asks about
        wide = d[d.stop_dist_pct >= 0.60]
        narrow = d[d.stop_dist_pct < 0.60]
        print(f"  wide (>=0.60%): n={len(wide):3d} WR {100*wide.is_win.mean():5.1f}% "
              f"totR {wide.R.sum():+8.2f} net {money(wide.net_pnl.sum())}  |  "
              f"narrow (<0.60%): n={len(narrow):3d} WR {100*narrow.is_win.mean():5.1f}% "
              f"totR {narrow.R.sum():+8.2f} net {money(narrow.net_pnl.sum())}")
        # the tail of the wide boxes
        top = d.nsmallest(5, "net_pnl")
        print("  the five worst single fills of the window:")
        for _, r in top.iterrows():
            print(f"    {r.sym:5s} {str(r.entry_time)[:16]} width {r.stop_dist_pct:5.3f}% "
                  f"{r.exit_reason:15s} {r.R:+7.2f}R {r.net_pnl:+8.2f}$")

    sub("A2. RISK CAP counterfactual -- what if a wide box could only lose "
        "RISK_CAP_PCT of equity?")
    print("  (first-order: the same fills, the same exits, only the cash at risk "
          "is scaled down when the box is wide)")
    print(f"  {'cap rule':44s} {'W1 net$':>9s} {'W1 %':>7s} {'W2 net$':>9s} "
          f"{'W2 %':>7s} {'chained':>9s}")
    base = {w: book(w) for w in WINDOWS}
    rules = [("no cap (the real book)", None, None)]
    for thr in (0.50, 0.60, 0.75):
        for cap in (0.50, 0.60, 0.75):
            if cap < thr:
                continue
            rules.append((f"width>{thr:.2f}%  risk capped at {cap:.2f}% equity",
                          thr, cap))
    rules.append(("REFUSE wide boxes outright (width>0.60%)", 0.60, 0.0))
    for lab, thr, cap in rules:
        ends = {}
        for win in WINDOWS:
            d = base[win].copy()
            if thr is not None:
                wide = d.stop_dist_pct > thr
                if cap is None or cap == 0.0:
                    d = d[~wide] if cap == 0.0 else d
                else:
                    # the engine risks `risk_pct` of the notional; its $-risk is
                    # deliberately > equity*risk_pct because the stop is the
                    # structural box. Cap it.
                    lose = d.R.clip(upper=0).abs() * d.notional * d.risk_pct / 100.0
                    # the $-loss of a -1R stop on a wide box, as % of equity
                    frac = 100.0 * (d.notional * d.risk_pct / 100.0) / 100.0
                    scale = np.where(wide, np.minimum(1.0, cap / frac.clip(lower=1e-9)), 1.0)
                    scale = np.minimum(scale, 1.0)
                    d["net_pnl"] = np.where(d.R < 0, d.net_pnl * scale,
                                            d.net_pnl * np.minimum(scale, 1.0))
                    if cap == 0.0:
                        d = d[~wide]
            ends[win] = 100.0 + float(d.net_pnl.sum())
        ch = ends["W1"] * ends["W2"] / 10000.0 - 1
        print(f"  {lab:44s} {ends['W1']-100:+9.2f} {ends['W1']-100:+7.2f} "
              f"{ends['W2']-100:+9.2f} {ends['W2']-100:+7.2f} {100*ch:+8.2f}%")
    print("\n  NOTE: capping the cash also shrinks the WINNERS that come out of "
          "wide boxes (the engine sizes\n  every fill with all the cash), so a "
          "cap only pays if wide boxes are net-negative -- check A1's")
    print("  wide-vs-narrow line above before believing any cap row.")


# --------------------------------------------------------------------- #
# B. INSTANT DEATH
# --------------------------------------------------------------------- #
def section_b():
    hdr("B. INSTANT DEATH -- the hold <= 0.5h autopsies, bar by bar")
    for win in WINDOWS:
        d = book(win)
        los = d[d.is_loss | d.is_be]
        fast = d[d.hold_h <= 0.5]
        print(f"\n  {win}: n={len(d)}  losers+BE={len(los)}  fills that died "
              f"within 0.5h: {len(fast)}  (their net ${fast.net_pnl.sum():+.2f})")
        # the same-bar stop: the fill bar itself already traded through the stop
        same_bar, poked, ok, missing = [], [], [], 0
        for _, r in los.iterrows():
            b = bar_at(r.sym, r.entry_time)
            if b is None:
                missing += 1
                continue
            if b["low"] <= r.stop_price + 1e-12:
                same_bar.append(r)
            if b["low"] < r.v29_seam_px - 1e-12:
                poked.append(r)
            else:
                ok.append(r)
        print(f"   losers whose OWN fill bar already traded through stop_px : "
              f"{len(same_bar)}/{len(los)}  ({100*len(same_bar)/max(1,len(los)):.1f}%)")
        print(f"   losers whose own fill bar POKED BELOW the seam (mitigation "
              f"intrabar)      : {len(poked)}/{len(los)}")
        print(f"   losers whose own fill bar never broke the seam (clean)        : "
              f"{len(ok)}/{len(los)}")
        if same_bar:
            sb = pd.DataFrame(same_bar)
            print(f"   of those same-bar deaths: net {sb.net_pnl.sum():+.2f}$  "
                  f"R {sb.R.sum():+.2f}  by coin "
                  + " ".join(f"{k}:{v}" for k, v in
                             sb.sym.value_counts().items()))
        # ---- and the same test on the 44 big winners
        big = d[d.R >= BIG_R]
        bw_poked, bw_clean = [], []
        for _, r in big.iterrows():
            b = bar_at(r.sym, r.entry_time)
            if b is None:
                continue
            (bw_poked if b["low"] < r.v29_seam_px - 1e-12 else bw_clean).append(r)
        print(f"   BIG WINNERS (>={BIG_R:.0f}R): {len(bw_poked)}/{len(big)} POKED below "
              f"the seam on their fill bar, {len(bw_clean)} filled clean")
        if bw_poked:
            p = pd.DataFrame(bw_poked)
            print(f"     ...and those poked winners made {p.net_pnl.sum():+.2f}$ of "
                  f"the window's {big.net_pnl.sum():+.2f}$ big-winner money "
                  f"({100*p.net_pnl.sum()/max(1e-9,big.net_pnl.sum()):.1f}%)")

        # ---- the touch-bar gate -------------------------------------
        # HONESTY FIX (v35b): the exported `v29_seam_px` column is rounded to
        # 2 dp, and the seam is min(green.y_top, yellow.y_bottom) -- i.e. the
        # HIGH of the bar that filled. "close < seam" against the rounded
        # column counts a candle closing 4 ticks under an ADA seam, which is
        # NOT the same thing and cannot be the engine's test. The live test
        # v35 uses is fill_px <= the bar's CLOSE (the bar never closed back
        # under the price it filled at = it kept falling). Both readings are
        # printed so the difference is visible, and neither is trusted as a
        # promise: only the engine run in lab_v35 can price it.
        keep_net, drop_net, drop_n = 0.0, 0.0, 0
        keep2, drop2, drop2n = 0.0, 0.0, 0
        for _, r in d.iterrows():
            b = bar_at(r.sym, r.entry_time)
            if b is None:
                keep_net += r.net_pnl; keep2 += r.net_pnl
                continue
            if b["close"] < r.v29_seam_px - 1e-12:
                drop_net += r.net_pnl; drop_n += 1
            else:
                keep_net += r.net_pnl
            if b["close"] < r.entry_price - 1e-12:
                drop2 += r.net_pnl; drop2n += 1
            else:
                keep2 += r.net_pnl
        print(f"   GATE(rounded seam) 'bar closes below seam'      : drops {drop_n} fills "
              f"({drop_net:+.2f}$) -> ${100+keep_net:.2f}")
        print(f"   GATE(honest)       'bar closes below the FILL'  : drops {drop2n} fills "
              f"({drop2:+.2f}$) -> ${100+keep2:.2f}  <-- this is what FLASH_SELLER_VETO does")
        # ---- the stricter gate: the fill bar may not break the GREEN BOX FLOOR
        keep2, drop2, drop2n = 0.0, 0.0, 0
        for _, r in d.iterrows():
            b = bar_at(r.sym, r.entry_time)
            if b is None:
                keep2 += r.net_pnl
                continue
            if b["low"] <= r.stop_price + 1e-12:
                drop2 += r.net_pnl
                drop2n += 1
            else:
                keep2 += r.net_pnl
        print(f"   GATE 'fill bar may not trade through the stop': drops {drop2n} fills "
              f"({drop2:+.2f}$) -> ${100+keep2:.2f} ({100*keep2/100:+.2f}%)")
        print("   (both gates are first-order: the cancelled fill frees the seat "
              "but no substitute trade")
        print("    is invented, so a positive delta here is a LOWER BOUND.)")


# --------------------------------------------------------------------- #
# C. PER-COIN COLD STREAKS
# --------------------------------------------------------------------- #
def _streaks(d, sym):
    """Consecutive-loss streaks of one coin in chronological order."""
    g = d[d.sym == sym].sort_values("entry_time")
    out, cur = [], []
    for _, r in g.iterrows():
        if r.is_win:
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(r)
    if cur:
        out.append(cur)
    return g, out


def _apply_cooldown(d, K, C_days, need_bos=False, bos_map=None):
    """Drop every fill that arrives while its own coin is in quarantine.

    K consecutive non-wins (a BE counts as a non-win, as the brief defines it:
    'L without W') -> the coin is banned for C days, or until a fresh 4H BOS
    up (when need_bos=True and a BOS time is available after the ban starts.
    """
    order = d.sort_values("entry_time")
    state = {}
    drop = pd.Series(False, index=d.index)
    for i, r in order.iterrows():
        st = state.setdefault(r.sym, {"streak": 0, "banned_until": None,
                                      "ban_start": None})
        t = r.entry_time
        if st["banned_until"] is not None:
            active = t < st["banned_until"]
            if need_bos and bos_map is not None:
                nb = bos_map.get((r.sym, st["ban_start"]))
                if nb is not None and t >= nb:
                    active = False
            if active:
                drop[i] = True
                continue
            st["banned_until"] = None
            st["streak"] = 0
        if r.is_win:
            st["streak"] = 0
        else:
            st["streak"] += 1
            if st["streak"] >= K:
                st["banned_until"] = t + pd.Timedelta(days=C_days)
                st["ban_start"] = t
                st["streak"] = 0
    return drop


def _bos_times(win_start):
    """First confirmed 4H BOS-up time AFTER each (coin, ban_start), causal."""
    return None      # computed lazily in section_c when need_bos is used


def section_c():
    hdr("C. PER-COIN COLD STREAKS -- and what a dynamic quarantine would do")
    for win in WINDOWS:
        d = book(win)
        print(f"\n  {win}: the worst streaks per coin (non-win runs, BE included)")
        for sym in sorted(d.sym.unique()):
            g, st = _streaks(d, sym)
            if not st:
                continue
            worst = max(st, key=lambda s: len(s))
            net = sum(r.net_pnl for r in worst)
            print(f"    {sym:5s} fills={len(g):3d}  W{int(g.is_win.sum()):2d} "
                  f"longest non-win run={len(worst):2d}  "
                  f"from {str(worst[0].entry_time)[:16]} -> "
                  f"{str(worst[-1].exit_time)[:16]}  net {net:+.2f}$  "
                  f"(W{sum(1 for r in worst if r.is_win)}/"
                  f"BE{sum(1 for r in worst if r.is_be)}/"
                  f"L{sum(1 for r in worst if r.is_loss)})")
        # the quarantine grid
        print(f"\n  QUARANTINE GRID {win} (first-order: banned fills removed, no "
              f"substitute trade invented)")
        print(f"  {'rule':46s} {'dropped':>8s} {'net$ dropped':>13s} "
              f"{'end$':>9s} {'%':>8s} {'PF':>6s} {'maxDD%':>7s}")
        base_end = 100.0 + float(d.net_pnl.sum())

        def show(lab, keep_mask):
            kept = d[keep_mask]
            end = 100.0 + float(kept.net_pnl.sum())
            e = 100.0 + kept.sort_values("exit_time").net_pnl.cumsum()
            e = pd.concat([pd.Series([100.0]), e], ignore_index=True)
            dd = float(((e / e.cummax()) - 1).min() * 100)
            print(f"  {lab:46s} {int((~keep_mask).sum()):8d} "
                  f"{float(d.loc[~keep_mask, 'net_pnl'].sum()):+13.2f} "
                  f"{end:9.2f} {end-100:+8.2f} {pf(kept):6.2f} {dd:7.2f}")

        show("no quarantine (the real book)", pd.Series(True, index=d.index))
        for K in (2, 3):
            for C in (7, 14, 21):
                drop = _apply_cooldown(d, K, C)
                show(f"K={K} non-wins -> {C}d ban", ~drop)
        print(f"  the real book ends at ${base_end:.2f}")


# --------------------------------------------------------------------- #
# D. THE MARCH 2024 CASE
# --------------------------------------------------------------------- #
def section_d():
    hdr("D. THE CASE THE BRIEF NAMES -- the month that made $25.49 then closed "
        "at +$0.53")
    for win in ("W1", "W2"):
        d = book(win)
        for m in ("2024-03", "2024-07", "2024-08", "2024-09"):
            g = d[d.exit_time.dt.strftime("%Y-%m") == m]
            if not len(g):
                continue
            net = g.net_pnl.sum()
            if net > 10:
                continue
            print(f"\n  {win} {m}: {len(g)} fills, net {net:+.2f}$  "
                  f"W{int(g.is_win.sum())}/BE{int(g.is_be.sum())}/L{int(g.is_loss.sum())}")
            top = g.nlargest(4, "net_pnl")
            print("   the fills that PAID:")
            for _, r in top.iterrows():
                print(f"     {r.sym:5s} {str(r.entry_time)[:16]} "
                      f"{r.exit_reason:15s} {r.R:+7.2f}R {r.net_pnl:+8.2f}$")
            print(f"   everything else ({len(g)-len(top)} fills): "
                  f"{g.drop(top.index).net_pnl.sum():+.2f}$")
            rest = g.drop(top.index)
            if len(rest):
                by = rest.groupby("sym").net_pnl.agg(["size", "sum"])
                by = by.sort_values("sum")
                print("   who ate it: " + "  ".join(
                    f"{k}(n{int(v['size'])}={v['sum']:+.2f})" for k, v in by.head(5).iterrows()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    want = set((a.only or "A,B,C,D").split(","))
    print("V35 BLEED MECHANICS -- measured on the saved S1_TEL_3R books")
    print(f"books: {RESULTS}")
    if "A" in want:
        section_a()
    if "B" in want:
        section_b()
    if "C" in want:
        section_c()
    if "D" in want:
        section_d()
    print("\n" + "=" * W); print("END OF BLEED AUDIT"); print("=" * W)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
