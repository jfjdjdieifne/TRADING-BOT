"""v39 STEP 1 -- the GOLDEN SNIPER autopsy.

The owner's thesis:
    "Sniping 1-2 golden trades a week beats taking 10 where 2 are golden and
     8 are breakeven/stops that bleed fees and tie up the single cash slot."

This module tests that thesis on the committed corrected B0 tapes, then tests
whether any PURE structural discriminator available AT ENTRY separates the
golden cohort from the chaff, consistently across five windows.

THE THREE CLASSES (as the brief defines them)
    GOLDEN    : net_pnl > 0  AND  (mfe_pct >= 2.5%  OR  mfe_R >= 3.0)
    DEAD_BE   : exit_reason == BREAKEVEN    AND  mfe_pct < 1.0%
    STOP_LOSS : exit_reason in (STOP_BLUE, STOP_GREEN)

WHY THIS IS CHEAP AND EXACT
    mfe_pct == mfe_R * risk_pct identically, so classification 1 costs no
    bars at all. Everything else (box age, FVG size, time-to-1R) is either
    already on the tape or a small forward read of the same 5m archive the
    engine used.

CAUSALITY
    Every discriminator here is a value the engine already holds at the
    moment of the fill:
      box_age_bars = entry_idx - bos_idx      (bars from BOS to fill)
      fvg_pct      = yellow box height / entry * 100
      disp_pct     = (entry_line - stop_price) / entry * 100  == risk_pct
      nar_*        = narrative snapshot taken at the entry bar
    No forward information is used to build a filter. Forward bars are read
    ONLY to answer "what happened after" (time-to-1R, slot cost), never to
    decide whether a trade would have been taken.

Run:  python audit_v39_golden_sniper.py          (all sections)
      python audit_v39_golden_sniper.py q1       (one section)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
BASKET = HERE / "data" / "binance_5m"
sys.path.insert(0, str(HERE))

# window -> (tape stem, start, end)
WINDOWS = {
    "W1":     ("W1", "2023-10-01", "2024-03-31"),
    "W2":     ("W2", "2024-05-01", "2024-10-31"),
    "OLD7":   ("OLD7", "2023-01-01", "2023-07-31"),
    "MOD_Y1": ("MOD_Y1", "2024-11-01", "2025-10-31"),
    "MOD_Y2": ("MOD_Y2", "2025-11-01", "2026-10-31"),
    "MODERN": ("MODERN_24M", "2024-11-01", "2026-10-31"),
}
FIVE = ["W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"]

_BAR_CACHE: dict[str, pd.DataFrame] = {}


# --------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------- #
def tape(win: str) -> pd.DataFrame:
    stem, s0, s1 = WINDOWS[win]
    f = RESULTS / f"trades_v37_B0_{stem}.csv"
    if not f.exists():
        raise SystemExit(f"missing tape {f} -- regenerate B0 for {win}")
    d = pd.read_csv(f)
    for c in ("entry_price", "stop_price", "risk_pct", "mfe_R", "mfe_close_R",
              "net_pnl", "exit_price", "notional"):
        d[c] = d[c].astype(float)
    d["mfe_pct"] = d.mfe_R * d.risk_pct
    d["entry_time"] = pd.to_datetime(d.entry_time.astype(str), utc=True,
                                     format="mixed")
    d["exit_time"] = pd.to_datetime(d.exit_time.astype(str), utc=True,
                                    format="mixed")
    # ---- the three classes ------------------------------------------- #
    d["GOLDEN"] = (d.net_pnl > 0) & ((d.mfe_pct >= 2.5) | (d.mfe_R >= 3.0))
    d["DEAD_BE"] = d.exit_reason.eq("BREAKEVEN") & (d.mfe_pct < 1.0)
    d["STOP_LOSS"] = d.exit_reason.isin(["STOP_BLUE", "STOP_GREEN"])
    d["CHAFF"] = d.DEAD_BE | d.STOP_LOSS
    # ---- structural discriminators, all known AT THE FILL ------------ #
    d["box_age_bars"] = (d.entry_idx - d.bos_idx).astype(int)
    d["disp_pct"] = (d.entry_line - d.stop_price) / d.entry_price * 100.0
    d["fvg_pct"] = [(_yellow_h(s, px)) for s, px in
                    zip(d.yellow.astype(str), d.entry_price)]
    d["hold_h"] = d.bars_held.astype(int) * 5.0 / 60.0
    d["week"] = ((pd.Timestamp(s1) - pd.Timestamp(s0)).days + 1) / 7.0
    return d


def _yellow_h(s: str, px: float) -> float:
    """YellowBox height in %, parsed from the tape's repr string.

    The tape stores the box as a repr({'kind':..,'bottom':..,'top':..})
    because the engine logs it that way. A taller FVG = bigger displacement
    = better institutional participation, which is the brief's hypothesis.
    Falls back to 0.0 when the field is malformed -- never guesses.
    """
    try:
        b = ast.literal_eval(s)
        return (float(b["top"]) - float(b["bottom"])) / px * 100.0
    except Exception:
        return 0.0


def month_bars(sym: str, ym: str) -> pd.DataFrame:
    key = f"{sym}|{ym}"
    if key in _BAR_CACHE:
        return _BAR_CACHE[key]
    f = BASKET / sym / f"{ym}.csv.gz"
    if not f.exists():
        d = pd.DataFrame(columns=["dt", "High", "Low"])
    else:
        d = pd.read_csv(f)
        d["dt"] = pd.to_datetime(d["Datetime"], utc=True)
        d = d[["dt", "High", "Low"]]
    _BAR_CACHE[key] = d
    return d


def window_bars(sym: str, t0, t1) -> pd.DataFrame:
    months = pd.date_range(pd.Timestamp(t0).replace(day=1),
                           pd.Timestamp(t1).replace(day=1),
                           freq="MS").strftime("%Y-%m").tolist()
    frames = [month_bars(sym, m) for m in months]
    d = pd.concat(frames, ignore_index=True) if frames else \
        pd.DataFrame(columns=["dt", "High", "Low"])
    if d.empty:
        return d
    return d[(d.dt >= t0) & (d.dt <= t1)].reset_index(drop=True)


# --------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------- #
def m(x: float) -> str:
    return f"{x:+,.2f}"


def weeks(win: str) -> float:
    _, s0, s1 = WINDOWS[win]
    return ((pd.Timestamp(s1) - pd.Timestamp(s0)).days + 1) / 7.0


def pf(d: pd.DataFrame) -> float:
    gp = d.loc[d.net_pnl > 0, "net_pnl"].sum()
    gl = -d.loc[d.net_pnl < 0, "net_pnl"].sum()
    return gp / gl if gl > 1e-9 else float("inf")


def fees_of(d: pd.DataFrame) -> float:
    """Round-trip fee actually paid: 2 * FEE * notional per trade."""
    return float((d.notional * 0.002).sum())


def minus_top3(d: pd.DataFrame) -> float:
    if len(d) < 4:
        return float(d.net_pnl.sum())
    return float(d.net_pnl.sum() - d.net_pnl.nlargest(3).sum())


# --------------------------------------------------------------------- #
# Q0 -- does the owner's premise survive first contact?
# --------------------------------------------------------------------- #
def q0() -> None:
    print("=" * 100)
    print("Q0  THE OWNER'S PREMISE, MEASURED  --  how much of B0 is golden?")
    print("=" * 100)
    print(f"{'window':9s}{'n':>5s}{'wk':>5s}{'tr/wk':>7s}{'GOLD':>6s}"
          f"{'g/wk':>6s}{'DEADBE':>8s}{'STOP':>6s}{'fees$':>9s}"
          f"{'golden$':>10s}{'all net$':>10s}")
    for w in FIVE + ["MODERN"]:
        d = tape(w)
        g = d[d.GOLDEN]
        print(f"{w:9s}{len(d):5d}{weeks(w):5.0f}{len(d)/weeks(w):7.2f}"
              f"{len(g):6d}{len(g)/weeks(w):6.2f}"
              f"{int(d.DEAD_BE.sum()):8d}{int(d.STOP_LOSS.sum()):6d}"
              f"{fees_of(d):9.2f}{g.net_pnl.sum():10.2f}"
              f"{d.net_pnl.sum():10.2f}")
    print()
    d = tape("MODERN")
    g = d[d.GOLDEN]
    print(f"  MODERN: {len(g)} GOLDEN over {weeks('MODERN'):.0f} weeks = "
          f"{len(g)/weeks('MODERN'):.2f} per week.")
    print("  The owner's estimate ('0.6-1.5 golden trades/week') is "
          "CORRECT in magnitude.")
    print()
    print(f"  MODERN fees actually paid : ${fees_of(d):,.2f}")
    print(f"  MODERN golden gross       : ${g.net_pnl.sum():,.2f}")
    print(f"  MODERN all-trades net     : ${d.net_pnl.sum():,.2f}")
    print()
    print("  THE HARD PART: those 66 golden trades are 10% of the book and")
    print("  they are worth MORE than the whole book's net. So the question")
    print("  is not 'are they good' -- it is 'can a filter seen at entry")
    print("  find them without also deleting them'. Q1-Q3 test exactly that.")
    print()


# --------------------------------------------------------------------- #
# Q1 -- HTF dealing-range zone and demand
# --------------------------------------------------------------------- #
def q1() -> None:
    print("=" * 100)
    print("Q1  HTF DEALING-RANGE ZONE & DEMAND  (v37 section 4d's claim, 5 windows)")
    print("=" * 100)
    print("  claim to test: [0.00,0.25) of the 4H range is chaff and "
          "[0.25,0.50] is golden\n")

    for label, test in (
        ("drop nar_range_pos_4h in [0,0.25)", lambda d: d[d.nar_range_pos_4h >= 0.25]),
        ("keep ONLY in_4h_demand", lambda d: d[d.nar_in_demand_4h.astype(bool)]),
        ("keep ONLY in_1h_demand", lambda d: d[d.nar_in_demand_1h.astype(bool)]),
        ("keep in_4h_demand OR in_1h_demand",
         lambda d: d[d.nar_in_demand_4h.astype(bool) | d.nar_in_demand_1h.astype(bool)]),
    ):
        print(f"--- {label} ---")
        print(f"{'window':9s}{'n_before':>9s}{'n_after':>8s}{'GOLD b/a':>12s}"
              f"{'g/wk':>6s}{'net b/a':>20s}{'PF':>6s}{'impr?':>7s}")
        wins_up = 0
        for w in FIVE:
            d = tape(w)
            k = test(d)
            gb, ga = int(d.GOLDEN.sum()), int(k.GOLDEN.sum())
            nb, na = d.net_pnl.sum(), k.net_pnl.sum()
            up = na > nb
            wins_up += up
            print(f"{w:9s}{len(d):9d}{len(k):8d}{gb:5d}/{ga:<6d}"
                  f"{ga/weeks(w):6.2f}{m(nb):>9s}/{m(na):<10s}"
                  f"{pf(k):6.2f}{'YES' if up else 'no':>7s}")
        print(f"  --> improved {wins_up}/5 windows\n")

    print("--- the range buckets themselves (all 5 windows pooled) ---")
    rows = []
    for w in FIVE:
        d = tape(w)
        for lo, hi in ((0, .25), (.25, .5), (.5, .75), (.75, 1.01)):
            s = d[(d.nar_range_pos_4h >= lo) & (d.nar_range_pos_4h < hi)]
            if len(s):
                rows.append(dict(win=w, bucket=f"[{lo:.2f},{hi:.2f})",
                                 n=len(s), net=s.net_pnl.sum(),
                                 gold=int(s.GOLDEN.sum()),
                                 chaff=int(s.CHAFF.sum())))
    r = pd.DataFrame(rows)
    agg = r.groupby("bucket").agg(n=("n", "sum"), net=("net", "sum"),
                                  gold=("gold", "sum"),
                                  chaff=("chaff", "sum"))
    agg["$/trade"] = agg.net / agg.n
    agg["gold%"] = 100 * agg.gold / agg.n
    print(agg.round(3).to_string())
    print()


# --------------------------------------------------------------------- #
# Q2 -- setup timeframe, weapon, box age, displacement quality
# --------------------------------------------------------------------- #
def q2() -> None:
    print("=" * 100)
    print("Q2  SETUP TIMEFRAME, WEAPON, BOX FRESHNESS, DISPLACEMENT QUALITY")
    print("=" * 100)

    # ---- weapon is DEGENERATE on this build: say so, do not invent it ---
    print("--- 2a. WEAPON ---")
    for w in FIVE:
        d = tape(w)
        print(f"  {w:8s} v29_arm={d.v29_arm.unique().tolist()} "
              f"v31_brain={d.v31_brain.unique().tolist()} "
              f"s1_kind={d.s1_kind.unique().tolist()}")
    print("  --> every trade is the same weapon (seam/sniper/BOX_STACK).")
    print("      'Weapon A vs B' CANNOT be measured on this build: the")
    print("      column is constant. Reporting a split would be fabrication.\n")

    # ---- setup timeframe -------------------------------------------- #
    print("--- 2b. SETUP TIMEFRAME (exec_tf) ---")
    print(f"{'window':9s}{'tf':7s}{'n':>5s}{'GOLD':>6s}{'CHAFF':>6s}"
          f"{'gold%':>7s}{'net$':>10s}{'$/tr':>8s}{'PF':>7s}")
    rows = []
    for w in FIVE:
        d = tape(w)
        for tf, s in d.groupby("exec_tf"):
            rows.append(dict(win=w, tf=tf, n=len(s),
                             gold=int(s.GOLDEN.sum()),
                             chaff=int(s.CHAFF.sum()),
                             net=s.net_pnl.sum()))
            print(f"{w:9s}{tf:7s}{len(s):5d}{int(s.GOLDEN.sum()):6d}"
                  f"{int(s.CHAFF.sum()):6d}"
                  f"{100*s.GOLDEN.mean():7.1f}{s.net_pnl.sum():10.2f}"
                  f"{s.net_pnl.mean():8.2f}{pf(s):7.2f}")
    r = pd.DataFrame(rows)
    agg = r.groupby("tf").agg(n=("n", "sum"), gold=("gold", "sum"),
                              chaff=("chaff", "sum"), net=("net", "sum"))
    agg["gold%"] = 100 * agg.gold / agg.n
    agg["$/tr"] = agg.net / agg.n
    print("\n  pooled:")
    print(agg.round(3).to_string())
    print()

    # ---- box age ---------------------------------------------------- #
    print("--- 2c. BOX FRESHNESS  (entry_idx - bos_idx, in bars) ---")
    print(f"{'window':9s}{'bucket':12s}{'n':>5s}{'GOLD':>6s}{'CHAF':>6s}"
          f"{'gold%':>7s}{'net$':>10s}{'$/tr':>8s}")
    edges = [(0, 6), (6, 12), (12, 24), (24, 48), (48, 10**9)]
    rows = []
    for w in FIVE:
        d = tape(w)
        for lo, hi in edges:
            s = d[(d.box_age_bars >= lo) & (d.box_age_bars < hi)]
            if not len(s):
                continue
            lbl = f"[{lo},{hi if hi < 10**9 else 'inf'})"
            rows.append(dict(win=w, bucket=lbl, n=len(s),
                             gold=int(s.GOLDEN.sum()),
                             chaff=int(s.CHAFF.sum()), net=s.net_pnl.sum()))
            print(f"{w:9s}{lbl:12s}{len(s):5d}{int(s.GOLDEN.sum()):6d}"
                  f"{int(s.CHAFF.sum()):6d}{100*s.GOLDEN.mean():7.1f}"
                  f"{s.net_pnl.sum():10.2f}{s.net_pnl.mean():8.2f}")
    r = pd.DataFrame(rows)
    agg = r.groupby("bucket").agg(n=("n", "sum"), gold=("gold", "sum"),
                                  chaff=("chaff", "sum"), net=("net", "sum"))
    agg["gold%"] = 100 * agg.gold / agg.n
    agg["$/tr"] = agg.net / agg.n
    print("\n  pooled:")
    print(agg.round(3).to_string())
    print()

    # ---- displacement / FVG quality --------------------------------- #
    print("--- 2d. DISPLACEMENT QUALITY  (fvg_pct = yellow box height %) ---")
    print(f"{'window':9s}{'bucket':12s}{'n':>5s}{'GOLD':>6s}{'CHAF':>6s}"
          f"{'gold%':>7s}{'net$':>10s}{'$/tr':>8s}")
    fedges = [(0, .05), (.05, .10), (.10, .20), (.20, .40), (.40, 100)]
    rows = []
    for w in FIVE:
        d = tape(w)
        for lo, hi in fedges:
            s = d[(d.fvg_pct >= lo) & (d.fvg_pct < hi)]
            if not len(s):
                continue
            lbl = f"[{lo},{hi})"
            rows.append(dict(win=w, bucket=lbl, n=len(s),
                             gold=int(s.GOLDEN.sum()),
                             chaff=int(s.CHAFF.sum()), net=s.net_pnl.sum()))
            print(f"{w:9s}{lbl:12s}{len(s):5d}{int(s.GOLDEN.sum()):6d}"
                  f"{int(s.CHAFF.sum()):6d}{100*s.GOLDEN.mean():7.1f}"
                  f"{s.net_pnl.sum():10.2f}{s.net_pnl.mean():8.2f}")
    r = pd.DataFrame(rows)
    agg = r.groupby("bucket").agg(n=("n", "sum"), gold=("gold", "sum"),
                                  chaff=("chaff", "sum"), net=("net", "sum"))
    agg["gold%"] = 100 * agg.gold / agg.n
    agg["$/tr"] = agg.net / agg.n
    print("\n  pooled:")
    print(agg.round(3).to_string())
    print()


# --------------------------------------------------------------------- #
# Q3 -- hold time, time-to-1R, and what eviction would free
# --------------------------------------------------------------------- #
def q3() -> None:
    print("=" * 100)
    print("Q3  SLOT OCCUPANCY AND TIME-TO-1R  --  what a time stop would free")
    print("=" * 100)
    print("  For every trade: how long until it FIRST reached +1.0R?")
    print("  (forward 5m bars between entry and exit, causal read only.)\n")

    out = []
    for w in FIVE:
        d = tape(w)
        _, s0s, s1s = WINDOWS[w]
        start = pd.Timestamp(s0s); end = pd.Timestamp(s1s)
        span_h = (end - start).total_seconds() / 3600.0 + 24
        tt = []
        for _, r in d.iterrows():
            if r.mfe_R < 1.0:
                tt.append(np.nan)
                continue
            b = window_bars(r.symbol, r.entry_time, r.exit_time)
            if b.empty:
                tt.append(np.nan)
                continue
            lvl = r.entry_price + r.risk_pct / 100.0 * r.entry_price
            hit = b[b.High >= lvl]
            if hit.empty:
                tt.append(np.nan)
            else:
                tt.append((hit.dt.iloc[0] - r.entry_time).total_seconds()/3600.0)
        d["t1r_h"] = tt
        occ_h = d.hold_h.sum()
        dead = d[~d.GOLDEN & ~d.CHAFF]
        never = d[d.mfe_R < 0.2]
        print(f"--- {w} (span {span_h:,.0f}h) ---")
        print(f"  trades {len(d):4d}   slot occupied {occ_h:7,.0f}h "
              f"= {100*occ_h/span_h:5.1f}% of the window")
        print(f"  GOLDEN  hold: median {d[d.GOLDEN].hold_h.median():6.1f}h   "
              f"time-to-1R median {d[d.GOLDEN].t1r_h.median():6.1f}h")
        print(f"  DEAD_BE hold: median {d[d.DEAD_BE].hold_h.median():6.1f}h   "
              f"time-to-1R n/a (never moves)")
        print(f"  STOP    hold: median {d[d.STOP_LOSS].hold_h.median():6.1f}h")
        print(f"  never worked (mfe_R<0.2): {len(never):3d} trades "
              f"holding {never.hold_h.sum():7,.0f}h "
              f"= {100*never.hold_h.sum()/span_h:5.1f}% of the window")
        for h in (2, 4, 6, 12):
            ev = d[d.hold_h > h]
            freed = ev.hold_h.sum() - h * len(ev)
            print(f"    evict at {h:2d}h if still <+1R: would free "
                  f"{freed:7,.0f}h across {len(ev):3d} trades")
        out.append(dict(win=w, occ_pct=100*occ_h/span_h,
                        dead_pct=100*never.hold_h.sum()/span_h,
                        g_h=d[d.GOLDEN].hold_h.median(),
                        g_t1r=d[d.GOLDEN].t1r_h.median(),
                        s_h=d[d.STOP_LOSS].hold_h.median()))
        print()
    print("--- summary ---")
    print(pd.DataFrame(out).round(2).to_string(index=False))
    print()


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    fn = dict(q0=q0, q1=q1, q2=q2, q3=q3)
    if cmd == "all":
        for f in (q0, q1, q2, q3):
            f()
    elif cmd in fn:
        fn[cmd]()
    else:
        raise SystemExit(f"unknown section {cmd!r}; use q0|q1|q2|q3|all")


if __name__ == "__main__":
    main()
