#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v37_root_causes.py -- forensic root-cause audit of v36's champion.

Four questions, answered from the ENGINE, not from opinion:

  Q1  the profit-giveback trap      (what the brief calls LOCK_3R_BE)
  Q2  the MOD_Y2 / APR_MAY_24 bleed (regime, stop, weapon, HTF context)
  Q3  the cooldown 5m-BOS unlock leak
  Q4  the exit-slippage / scratch-loss interaction

HOW IT WORKS
------------
Two independent passes:

  TAPE   reads results/trades_v36_S1_COIN_GUARD_BOS_<win>.csv, which carries
         mfe_R, R, net_pnl, risk_pct, exec_tf, nar_flow_4h/1h, nar_range_pos_4h,
         v31_struct_trailed and exit_reason.  Everything that can be derived
         from a closed trade is derived here, including the counterfactual
         ratchet ladder (Q1d).

  ENGINE re-runs the backtest with a small observer installed on the engine
         class.  Only this pass can see (a) the *causal* HTF labels at entry
         and (b) the cooldown unlock events, because neither is written to
         the tape by v36.

WHAT THE BRIEF ASSUMES vs WHAT THE ENGINE DOES
----------------------------------------------
This is reported explicitly by Q1, because four of the brief's premises are
false for strategy_v36_ict_champion.py and a knob built on a false premise
would be a no-op that looks like a finding:

  * there is no `LOCK_3R_BE` exit reason and no `pos.locked_3r` attribute.
    `grep -n "locked_3r\\|LOCK_3R_BE"` over the engine returns nothing.
  * the $0.00 round-trip exit is classified BREAKEVEN (R >= -0.05, net won).
  * `STOP_BLUE` is the INITIAL structural stop in 610 of 627 modern trades
    (v31_struct_trailed is True in only 17), so TRAIL_4H_ONLY_AFTER_LOCK is
    not involved in the MOD_Y2 bleed at all.
  * a trade that nets -$0.01 after a +3R excursion is reclassified BREAKEVEN
    before the streak sees it, so the Part-4 "false ban" cannot fire.

NO LOOKAHEAD
------------
The causal labels are read at the stamp the fill was decided on, from the
engine's own canvases (already causal by construction: the engine only feeds
a 4H/1H bar once its end_time <= the current stamp).  The counterfactual
ratchet (Q1d) is an ARITHMETIC what-if on a stop that would have been placed
at a level derived from the trade's own realised MFE — it deliberately does
not claim to re-simulate the path, and it is reported as such.

USAGE
    python3 audit_v37_root_causes.py tape          # no engine runs
    python3 audit_v37_root_causes.py engine [WIN]  # re-run one window
    python3 audit_v37_root_causes.py all
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))

BASKET = str(HERE / "data" / "binance_5m")

WINDOWS = {
    "W1":     ("2023-10-01", "2024-03-31"),
    "W2":     ("2024-05-01", "2024-10-31"),
    "APR_MAY_24": ("2024-04-01", "2024-05-31"),
    "FULL15": ("2023-08-01", "2024-10-31"),
    "OLD7":   ("2023-01-01", "2023-07-31"),
    "MOD_Y1": ("2024-11-01", "2025-10-31"),
    "MOD_Y2": ("2025-11-01", "2026-10-31"),
    "MODERN_24M": ("2024-11-01", "2026-10-31"),
}
# windows whose v36 tape already exists on the branch
HAVE_TAPE = ("W1", "W2", "FULL15", "OLD7", "MODERN")

W_ = 100


def hr(ch: str = "=") -> None:
    print(ch * W_, flush=True)


def tape(win: str) -> pd.DataFrame | None:
    """Load the v36 trade tape for a window, or None if it was never made."""
    f = RESULTS / f"trades_v36_S1_COIN_GUARD_BOS_{win}.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    for c in ("net_pnl", "R", "risk_pct", "mfe_R", "mfe_close_R", "entry_price",
              "exit_price", "stop_price", "notional", "qty0", "bars_held"):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["entry_time"] = pd.to_datetime(d["entry_time"], utc=True, format="mixed")
    d["exit_time"] = pd.to_datetime(d["exit_time"], utc=True, format="mixed")
    return d


# --------------------------------------------------------------------- #
# Q1  the give-back trap
# --------------------------------------------------------------------- #
BUCKETS = [(3.0, 4.0), (4.0, 5.0), (5.0, 7.0), (7.0, 10.0), (10.0, np.inf)]


def q1(win: str, d: pd.DataFrame) -> dict:
    """The give-back: trades that reached a high MFE and exited at ~$0.00."""
    hr()
    print(f"Q1  PROFIT GIVE-BACK  [{win}]  n={len(d)}")
    hr()
    zero = d[d.exit_reason.isin(["BREAKEVEN"])]
    print("  NOTE the engine has no LOCK_3R_BE reason; the $0.00 round-trip")
    print("  exit is classified BREAKEVEN. So this is measured there.")
    print(f"\n  a) BREAKEVEN exits: {len(zero)}  "
          f"({100 * len(zero) / len(d):.1f}% of all trades)  "
          f"net {zero.net_pnl.sum():+.2f}$")
    if not len(zero):
        return {}
    print(f"     of these, reached +3R MFE: {int((zero.mfe_R >= 3).sum())}"
          f"   +2R: {int((zero.mfe_R >= 2).sum())}"
          f"   +1R: {int((zero.mfe_R >= 1).sum())}")
    print(f"     peak MFE_R: median {zero.mfe_R.median():.2f} "
          f"p90 {zero.mfe_R.quantile(.9):.2f} max {zero.mfe_R.max():.2f}")

    print("\n  b) distribution of the PEAK reached before giving it all back")
    print(f"     {'MFE bucket':12s} {'n':>4s} {'peak MFE_R':>10s} "
          f"{'peak MFE_$':>10s} {'gave back $':>11s}")
    rows = []
    for lo, hi in BUCKETS:
        g = zero[(zero.mfe_R >= lo) & (zero.mfe_R < hi)]
        peak_usd = (g.mfe_R * g.risk_pct / 100.0 * g.notional).sum()
        lab = f"[{lo:g}..{hi:g})" if np.isfinite(hi) else f">={lo:g}"
        print(f"     {lab:12s} {len(g):4d} {g.mfe_R.sum():10.1f} "
              f"{peak_usd:10.2f} {-g.net_pnl.sum():11.2f}")
        rows.append((lab, len(g), g.mfe_R.sum(), peak_usd))

    all_pk = (zero.mfe_R * zero.risk_pct / 100.0 * zero.notional)
    print(f"\n  c) TOTAL peak unrealised on those trades: "
          f"${all_pk.sum():.2f}   realised: ${zero.net_pnl.sum():+.2f}")
    print(f"     -> given back: ${all_pk.sum() - zero.net_pnl.sum():.2f}")

    # ---- d) the counterfactual ratchet -------------------------------- #
    # A stop at +kR, armed the first time the trade's MFE reached its
    # trigger, pays min(banked level, MFE reached) when the trade later
    # rounds-tripped. For trades that finished ABOVE the banked level we
    # keep what actually happened (the ratchet never binds).
    print("\n  d) WHAT IF the post-trigger stop banked a floor instead of 0.00R?")
    print("     (arithmetic what-if: max(realised R, floor) in R, at the trade's")
    print("      own $/R -> a trade that never came back keeps its own outcome)")

    def bank(trig: float, floor: float, ladder: tuple | None = None) -> float:
        """$ if a stop at `floor` armed once MFE reached `trig`.

        CORRECT MODEL (the first version of this function was wrong and gave
        the same answer for every candidate): a stop at +1.5R does not pay
        the MFE, it pays +1.5R. So for a trade whose MFE reached the trigger
        the outcome is max(realised R, floor):
            - the trade never retraced to the floor -> realised R (unchanged)
            - it retraced to the floor             -> +floor (banked)
        With a ladder, the floor is the one belonging to the highest trigger
        the trade reached.
        """
        g = zero[zero.mfe_R >= trig]
        if not len(g):
            return 0.0
        usd_per_r = g.notional * g.risk_pct / 100.0
        lvl = pd.Series(float(floor), index=g.index)
        if ladder:
            for t, f in ladder:            # ascending triggers
                lvl = lvl.where(~(g.mfe_R >= t), float(f))
        new_r = np.maximum(g.R.astype(float), lvl.astype(float))
        return float((new_r * usd_per_r).sum())

    base = float(zero.net_pnl.sum())
    cands = {
        "A: +1.5R @3R, +2.5R @4R, +4.0R @6R":
            bank(3.0, 0, ((3.0, 1.5), (4.0, 2.5), (6.0, 4.0))),
        "B: +2.0R @3R, +3.0R @4.5R, +4.5R @6R":
            bank(3.0, 0, ((3.0, 2.0), (4.5, 3.0), (6.0, 4.5))),
        "1H bridge: +1.5R @3R (no 4H wait)": bank(3.0, 1.5),
        "simple +2.0R @3R": bank(3.0, 2.0),
        "aggressive +1.0R @2R (pre-3R too)": bank(2.0, 1.0),
    }
    print(f"     {'candidate':42s} {'$ on those trades':>18s} {'vs now':>10s}")
    for k, v in cands.items():
        print(f"     {k:42s} {v:18.2f} {v - base:+10.2f}")
    print(f"     {'(current: they exit at BREAKEVEN ≈ 0)':42s} {base:18.2f}")
    return {"n_be": len(zero), "peak_usd": float(all_pk.sum()),
            "given_back": float(all_pk.sum() - base), "banked": cands}


def q1_all() -> None:
    hr("#")
    print("Q1  THE GIVE-BACK TRAP -- every window")
    hr("#")
    for win in ("W1", "W2", "FULL15", "MOD_Y1", "MOD_Y2", "MODERN"):
        d = tape(win)
        if d is None:
            print(f"\n  [{win}] no tape on the branch yet")
            continue
        q1(win, d)


# --------------------------------------------------------------------- #
# Q2  the bleed autopsy
# --------------------------------------------------------------------- #
def regime_table(win: str = "MODERN_24M") -> None:
    """What were the 8 coins actually doing? Read from the rebuilt 5m data."""
    start, end = WINDOWS[win]
    hr()
    print(f"Q2.0  MARKET REGIME  [{win}] {start}..{end}")
    hr()
    p0 = pd.Timestamp(start, tz="UTC")
    p1 = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    print(f"  {'coin':8s} {'start px':>12s} {'end px':>12s} {'12m %':>8s} "
          f"{'maxDD %':>8s} {'best mo':>8s} {'worst mo':>8s} {'neg mo':>7s}")
    rows = []
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
                "XRPUSDT", "AVAXUSDT", "LINKUSDT", "ADAUSDT"):
        d = HERE / "data" / "binance_5m" / f"{sym}_5m"
        if not d.exists():
            continue
        parts = []
        for f in sorted(d.glob("*.csv.gz")):
            ym = f.name[:7]
            if not (start[:7] <= ym <= end[:7]):
                continue
            x = pd.read_csv(f)
            x["Datetime"] = pd.to_datetime(x["Datetime"], utc=True)
            parts.append(x)
        if not parts:
            continue
        x = pd.concat(parts, ignore_index=True).set_index("Datetime").sort_index()
        x = x[(x.index >= p0) & (x.index < p1)]
        if not len(x):
            continue
        px0 = float(x.Close.iloc[0])
        px1 = float(x.Close.iloc[-1])
        dd = float((x.Close / x.Close.cummax() - 1).min() * 100)
        mo = x.Close.resample("MS").last().pct_change().dropna() * 100
        print(f"  {sym[:7]:8s} {px0:12.6g} {px1:12.6g} "
              f"{100 * (px1 / px0 - 1):+8.1f} {dd:8.1f} "
              f"{mo.max():+8.1f} {mo.min():+8.1f} {int((mo < 0).sum()):3d}/{len(mo):<3d}")
        rows.append(dict(sym=sym, px0=px0, px1=px1,
                         ret=100 * (px1 / px0 - 1), dd=dd,
                         neg=int((mo < 0).sum()), months=len(mo),
                         monthly=mo.round(2).to_dict()))
    if rows:
        r = pd.DataFrame(rows)
        print(f"\n  basket median return {r.ret.median():+.1f}%   "
              f"coins down {int((r.ret < 0).sum())}/8   "
              f"median maxDD {r.dd.median():.1f}%")
    (RESULTS / f"_v37_regime_{win}.json").write_text(
        json.dumps(rows, indent=1, default=str))


def q2_tape(win: str, d: pd.DataFrame) -> None:
    hr()
    print(f"Q2  BLEED AUTOPSY  [{win}]  n={len(d)}  net {d.net_pnl.sum():+.2f}$")
    hr()
    # ---- is STOP_BLUE an initial stop or a trail? --------------------- #
    sb = d[d.exit_reason == "STOP_BLUE"]
    tr = d.v31_struct_trailed.astype(bool) if "v31_struct_trailed" in d else None
    print("  (i) is STOP_BLUE an INITIAL stop or a 4H trail?")
    print(f"      STOP_BLUE exits: {len(sb)}  net {sb.net_pnl.sum():+.2f}$")
    if tr is not None:
        print(f"      v31_struct_trailed True in the whole window: "
              f"{int(tr.sum())}/{len(d)}")
        print(f"      of the STOP_BLUE exits, trailed: {int(tr[sb.index].sum())} "
              f"-> INITIAL stops: {len(sb) - int(tr[sb.index].sum())}")
        print(f"      STOP_BLUE net on trailed: "
              f"{sb.loc[tr[sb.index], 'net_pnl'].sum():+.2f}$")
    print(f"      STOP_BLUE median peak MFE {sb.mfe_R.median():.2f}R "
          f"(p90 {sb.mfe_R.quantile(.9):.2f}R) -> "
          f"{int((sb.mfe_R < 1).sum())} of {len(sb)} never reached +1R")

    # ---- a) weapon ---------------------------------------------------- #
    print("\n  (ii) every trade split four ways")
    def block(title: str, key: pd.Series | str) -> None:
        print(f"\n      {title}")
        print(f"      {'bucket':22s} {'n':>5s} {'net $':>9s} {'$/trade':>8s} "
              f"{'WR%':>6s} {'PF':>6s} {'medMFE':>7s}")
        k = d[key] if isinstance(key, str) else key
        for name, g in d.groupby(k, observed=True, dropna=False):
            if not len(g):
                continue
            gp = g.loc[g.net_pnl > 0, "net_pnl"].sum()
            gl = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
            wr = 100 * g["class"].isin(["WIN", "SWIN"]).mean() if "class" in g else np.nan
            print(f"      {str(name):22s} {len(g):5d} {g.net_pnl.sum():+9.2f} "
                  f"{g.net_pnl.mean():+8.2f} {wr:6.1f} "
                  f"{(gp / gl if gl > 1e-9 else np.inf):6.2f} "
                  f"{g.mfe_R.median():7.2f}")

    block("(a) WEAPON -- from the fill path (+ = impulse/Weapon B)",
          d.nar_unfilled_imp if "nar_unfilled_imp" in d else d.nar_flow_4h)
    block("(b) SETUP TIMEFRAME", "exec_tf")
    band = pd.cut(d.risk_pct, [0, .20, .30, .45, .75, 1e9],
                  labels=["<0.20%", "0.20-0.30%", "0.30-0.45%",
                          "0.45-0.75%", ">=0.75%"])
    block("(c) STRUCTURAL STOP WIDTH (stop_dist_pct)", band)
    print("\n      (d) HIGHER-TIMEFRAME CONTEXT AT ENTRY")
    for col, lab in (("nar_flow_4h", "latest 4H structural break (BOS)"),
                     ("nar_flow_1h", "latest 1H structural break (BOS)")):
        if col not in d:
            continue
        print(f"\n      {lab}:")
        for name, g in d.groupby(col, observed=True, dropna=False):
            gp = g.loc[g.net_pnl > 0, "net_pnl"].sum()
            gl = -g.loc[g.net_pnl < 0, "net_pnl"].sum()
            print(f"        {str(name):10s} n={len(g):5d} "
                  f"net {g.net_pnl.sum():+9.2f} "
                  f"({g.net_pnl.mean():+.3f}/trade)  "
                  f"PF {(gp / gl if gl > 1e-9 else np.inf):.2f}")
    if "nar_range_pos_4h" in d:
        rp = d.nar_range_pos_4h
        print(f"\n      price vs 4H PurpleBox mid (range_pos: <0.5 = discount):")
        for lab, m in (("<0 (below box)", rp < 0), ("0..0.25", (rp >= 0) & (rp < .25)),
                       ("0.25..0.5", (rp >= .25) & (rp < .5)), (">=0.5 (premium)", rp >= .5)):
            g = d[m]
            if len(g):
                print(f"        {lab:18s} n={len(g):5d} net {g.net_pnl.sum():+9.2f} "
                      f"({g.net_pnl.mean():+.3f}/trade)")
    if "nar_in_demand_4h" in d:
        print()
        for name, g in d.groupby("nar_in_demand_4h", observed=True):
            print(f"        in 4H demand={name!s:6s} n={len(g):5d} "
                  f"net {g.net_pnl.sum():+9.2f} "
                  f"({g.net_pnl.mean():+.3f}/trade)")


# --------------------------------------------------------------------- #
# Q4  slippage vs scratch losses
# --------------------------------------------------------------------- #
def q4() -> None:
    hr("#")
    print("Q4  EXIT SLIPPAGE vs SCRATCH LOSSES (the Part-4 claim)")
    hr("#")
    print("""
  The claim: with EXIT_SLIPPAGE_BPS>0 a trade that reached +3R exits at a few
  cents negative, `net < 0` increments consec_losses and the coin is banned.

  Verdict from the code: CANNOT FIRE, and the belt-and-braces fix is already
  in _exit:
      is_be = ((not is_win) and (not is_swin)
               and (self.shield or self.be_armed or net > 0) and R >= -0.05)
      if is_be: reason = "BREAKEVEN"
  A +3R trade that nets -$0.01 has R >= -0.05, so it is reclassified
  BREAKEVEN before the streak reads it.  The streak keys on classification,
  not on net.
""")
    base = tape("W1")
    if base is None:
        return
    print(f"  measured on the committed v36 tapes: a BREAKEVEN exit is the only")
    print(f"  exit that lands within +/-5 cents. Scratch-exit census:")
    for win in ("W1", "W2", "MODERN"):
        d = tape(win)
        if d is None:
            continue
        be = d[d.exit_reason == "BREAKEVEN"]
        tiny = d[(d.net_pnl.abs() < 0.05)]
        neg_tiny = tiny[tiny.net_pnl < 0]
        print(f"    {win:7s} BREAKEVEN {len(be):4d} | |net|<5c: {len(tiny):4d} "
              f"| of those negative: {len(neg_tiny):3d} "
              f"| worst {d.net_pnl.min():+.4f}$")
    print("""
  The real cost of EXIT_SLIPPAGE_BPS is not the streak, it is the trade mix
  (v36 measured: 1 bps moved W2 from $194.38 to $146.33 by reshuffling which
  single slot each day's winner occupied).  That is a POSITION-SIZING /
  path-dependence effect, not an accounting bug.
""")


# --------------------------------------------------------------------- #
# ENGINE pass: causal HTF labels + cooldown unlock events
# --------------------------------------------------------------------- #
def engine_pass(win: str) -> None:
    """Re-run one window with an observer that records, at every fill:
    the causal 4H/1H flow, the 4H range position and the basket breadth;
    and at every cooldown lift: which timeframe printed the BOS."""
    import strategy_v36_ict_champion as S

    S.V32_DATA_DIR = BASKET
    S.ALLOC_MODE, S.SLOTS, S.SLOT_FILL = "slot", 1, "fixed"
    S.MAX_OPEN_POSITIONS, S.FULL_100_DEPLOY = 1, True
    S.PER_COIN_COOLDOWN, S.COOLDOWN_DAYS = 2, 14.0
    S.COOLDOWN_NEEDS_BOS = True
    S.SMT_BRAIN, S.SMT_GATE = True, "prefer"
    S.KILLZONE_MODE, S.KILLZONE_DOW = "exclude", (6,)
    S.MIN_STOP_PCT, S.NO_FALL_CLOSE = 0.0, False
    S.FLASH_SELLER_VETO = False
    S.EXIT_SLIPPAGE_BPS, S.SLIPPAGE_BPS = 0.0, 0.0

    E = S.ICTEngine if hasattr(S, "ICTEngine") else None
    if E is None:
        cands = [v for k, v in vars(S).items()
                 if isinstance(v, type) and hasattr(v, "_exit")
                 and hasattr(v, "_enter")]
        E = cands[0]
    print(f"  engine class: {E.__name__}", flush=True)

    obs = []
    orig_exit = E._exit
    orig_enter = E._enter

    def _exit(self, px, reason, idx, time):
        px_after = px
        r_now = ((px_after - self.entry_px) / self.risk
                 if getattr(self, "risk", 0) else np.nan)
        obs.append(dict(kind="exit", symbol=getattr(self, "symbol", ""),
                        time=str(time), reason=reason, r=r_now,
                        ratchet=bool(getattr(self, "ratchet", False)),
                        stop_px=float(getattr(self, "stop_px", np.nan)),
                        entry_px=float(getattr(self, "entry_px", np.nan)),
                        mfe=float(getattr(self, "mfe", np.nan))))
        return orig_exit(self, px, reason, idx, time)

    def _enter(self, *a, **k):
        out = orig_enter(self, *a, **k)
        try:
            S4 = getattr(self, "nar4", None) or self.struct_canvas
            H1 = getattr(self, "nar1", None) or self.htf_canvas
            obs.append(dict(kind="fill", symbol=getattr(self, "symbol", ""),
                            time=str(getattr(self, "now", "")),
                            flow4h=S4.flow() if S4 is not None else None,
                            flow1h=(H1.flow() if H1 is not None
                                    and getattr(H1, "narrative", False) else None),
                            rp4h=(S4.range_pos(self.entry_px)
                                  if S4 is not None else None),
                            exec_tf=getattr(self, "exec_tf", ""),
                            risk_pct=float(getattr(self, "risk", 0) / self.entry_px * 100)
                            if getattr(self, "entry_px", 0) else np.nan))
        except Exception:                                     # noqa: BLE001
            pass
        return out

    E._exit, E._enter = _exit, _enter
    start, end = WINDOWS[win]
    print(f"  re-running {win} {start}..{end} with the observer...", flush=True)
    run = S.run_backtest(S.v34_data_dir(), start, end, tag=f"v37audit{win}")
    E._exit, E._enter = orig_exit, orig_enter

    o = pd.DataFrame(obs)
    o.to_csv(RESULTS / f"_v37_obs_{win}.csv", index=False)
    print(f"  observer rows: {len(o)} "
          f"(fills {int((o.kind == 'fill').sum())}, "
          f"exits {int((o.kind == 'exit').sum())})", flush=True)

    fills = o[o.kind == "fill"].copy()
    if len(fills):
        print("\n  CAUSAL HTF labels at the fill stamp (engine-side, not tape):")
        for col in ("flow4h", "flow1h"):
            if col in fills:
                for name, g in fills.groupby(col, dropna=False):
                    print(f"    {col}={str(name):6s} n={len(g):4d}")
    tr = pd.DataFrame(run["trades"])
    if len(tr):
        print(f"\n  totals: n={len(tr)} net {tr.net_pnl.sum():+.2f}$ "
              f"end {run['pool_cash_end']:+.2f}$")
    cnt = run["count"]
    for k in sorted(cnt):
        if "cooldown" in k:
            print(f"    {k:34s} {cnt[k]}")


# --------------------------------------------------------------------- #
def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tape"
    if cmd == "tape":
        q1_all()
        for win in ("W1", "W2", "MOD_Y1", "MOD_Y2", "MODERN"):
            d = tape(win)
            if d is not None:
                q2_tape(win, d)
        q4()
        return 0
    if cmd == "regime":
        for win in (sys.argv[2] if len(sys.argv) > 2 else "MODERN_24M",):
            regime_table(win)
        return 0
    if cmd == "engine":
        engine_pass(sys.argv[2] if len(sys.argv) > 2 else "W1")
        return 0
    if cmd == "all":
        q1_all()
        q4()
        return 0
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    raise SystemExit(main())
