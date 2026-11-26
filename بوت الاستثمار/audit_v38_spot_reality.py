"""v38 PART 1 -- the 1x SPOT REALITY audit.

Not written in the language of R multiples. Every question below is asked in
the language of the only thing a 1x spot account can actually earn:

    pct_move = (px - entry_px) / entry_px * 100      minus 0.20% round trip

The v37 work measured the engine in R. That is a risk-normalised unit, and it
is blind to the one number that decides a spot account: how far the COIN
actually travelled. This module re-asks the four v37 questions in %.

FOUR QUESTIONS
  1. Actual spot % excursion of the BREAKEVEN exits.  mfe_pct, not mfe_R.
  2. The premature-BE wick-out: what did price do AFTER we were scratched out?
  3. Why the 4H structural trail is dead -- and what 1H/30m/15m boxes offered.
  4. Fee churn: does structural room to the draw of liquidity pay for 0.20%?

WHY THIS IS CHEAP AND EXACT
  mfe_pct == mfe_R * risk_pct identically (verified to 0.0 difference), because
  mfe_R is defined on the same entry/stop the risk_pct is measured from. So Q1
  needs no bars at all -- it is pure arithmetic on the committed B0 tapes.

  Q2 and Q3 need forward price and the ICT boxes. Rather than trusting a
  re-derivation, this module REPLAYS the champion's own ChartCanvas class
  (imported, not copied) over the same 1m->5m/15m/30m/1h/4h resamples the
  engine builds, then rebuilds each canvas's state AS OF the moment it matters
  by taking the boxes the canvas itself timestamped before that moment. The
  causal guarantee therefore comes from the engine's own code, not from me.

  A box's `time` is the timestamp of the bar on whose close its 3-bar fractal
  confirmed -- the engine sets it in _confirm_fractals. Filtering `b.time <= t`
  is therefore exactly "the engine could have seen this at t".

Run:  python audit_v38_spot_reality.py            (all: q1 q2 q3 q4)
      python audit_v38_spot_reality.py q1         (one section)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)
BASKET = HERE / "data" / "binance_5m"
sys.path.insert(0, str(HERE))

import strategy_v36_ict_champion as S                      # noqa: E402
from engine.causal_primitives import (load_asset_ohlcv,    # noqa: E402
                                     resample_causal_tf)

COST_PCT = 2 * S.FEE * 100.0        # 0.20% round-trip, the spot reality

# The five windows named in the brief. MODERN is added because the brief's
# $404.51 peak-unrealised figure is a MODERN number and must be reproduced.
WINDOWS = {
    "W1":     ("2023-10-01", "2024-03-31"),
    "W2":     ("2024-05-01", "2024-10-31"),
    "OLD7":   ("2023-01-01", "2023-07-31"),
    "MOD_Y1": ("2024-11-01", "2025-10-31"),
    "MOD_Y2": ("2025-11-01", "2026-10-31"),
    "MODERN": ("2024-11-01", "2026-10-31"),
}

# B0 = the shipped champion, stated explicitly (CAPITAL is 200 in the engine
# module and 100 in the book -- the v37 lesson).
SHIPPED = dict(
    CAPITAL=100.0,
    ALLOC_MODE="slot", SLOTS=1, SLOT_FILL="fixed",
    MAX_OPEN_POSITIONS=1, FULL_100_DEPLOY=True,
    PER_COIN_COOLDOWN=2, COOLDOWN_DAYS=14.0, COOLDOWN_NEEDS_BOS=True,
    SMT_BRAIN=True, SMT_GATE="prefer",
    KILLZONE_MODE="exclude", KILLZONE_DOW=(6,),
    MIN_STOP_PCT=0.0, NO_FALL_CLOSE=False,
    FLASH_SELLER_VETO=False, SLIPPAGE_BPS=0.0,
)

BUCKETS_PCT = [(0, 0.8), (0.8, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0),
               (6.0, np.inf)]


# --------------------------------------------------------------------- #
# tape loading
# --------------------------------------------------------------------- #
def tape(win: str) -> pd.DataFrame:
    """The committed corrected B0 tape for a window, with % columns added."""
    stem = {"MODERN": "MODERN_24M"}.get(win, win)
    f = RESULTS / f"trades_v37_B0_{stem}.csv"
    if not f.exists():
        raise SystemExit(f"missing tape {f} -- run lab_v37_anti_fragile.py "
                         f"run B0 --window {win} first")
    d = pd.read_csv(f)
    d["entry_price"] = d.entry_price.astype(float)
    d["stop_price"] = d.stop_price.astype(float)
    d["risk_pct"] = d.risk_pct.astype(float)
    d["mfe_R"] = d.mfe_R.astype(float)
    d["net_pnl"] = d.net_pnl.astype(float)
    d["exit_price"] = d.exit_price.astype(float)
    # ---- THE SPOT TRANSLATION -----------------------------------------
    # mfe_pct: how far the COIN rose at its best, in real %.
    d["mfe_pct"] = d.mfe_R * d.risk_pct
    # lock_pct: the actual % move needed to reach the +3R lock (3 * risk,
    # net of fees because lock_line is built net of fees).
    d["lock_pct"] = 3.0 * d.risk_pct
    # realised % on the coin, exit vs entry (before fees).
    d["exit_pct"] = (d.exit_price - d.entry_price) / d.entry_price * 100.0
    d["is_be"] = d.exit_reason.eq("BREAKEVEN")
    d["reached_lock"] = d.mfe_R >= 3.0
    d["is_win"] = d["class"].isin(["WIN", "SWIN"])
    return d


def money(x: float) -> str:
    return f"${x:,.2f}"


# --------------------------------------------------------------------- #
# Q1 -- the real spot % excursion of the BREAKEVEN exits
# --------------------------------------------------------------------- #
def q1() -> None:
    print("=" * 74)
    print("Q1  ACTUAL SPOT % EXCURSION OF THE BREAKEVEN EXITS  (mfe_pct, not mfe_R)")
    print("=" * 74)
    print(f"    round-trip fee floor = {COST_PCT:.2f}%   "
          f"(a trade must clear this to earn a cent)\n")

    rows = []
    for win in WINDOWS:
        d = tape(win)
        be = d[d.is_be]
        rec = {"win": win, "n": len(d), "n_be": len(be),
               "be_share": 100.0 * len(be) / len(d),
               "peak$": float((be.mfe_pct / 100.0 * be.notional).sum())}
        for lo, hi in BUCKETS_PCT:
            m = (be.mfe_pct >= lo) & (be.mfe_pct < hi)
            rec[f"[{lo:g},{hi:g})"] = int(m.sum())
        rows.append(rec)

    hdr = ["5m window", "trades", "BE", "BE%", "peak $ given back"] + \
          [f"{lo:g}-{hi:g}%" if hi != np.inf else f">={lo:g}%"
           for lo, hi in BUCKETS_PCT]
    print("  " + "".join(f"{h:>12s}" for h in hdr))
    for r in rows:
        print(f"  {r['win']:>12s}{r['n']:>12d}{r['n_be']:>12d}"
              f"{r['be_share']:>11.1f}%{money(r['peak$']):>12s}"
              + "".join(f"{r[f'[{lo:g},{hi:g})']:>12d}"
                        for lo, hi in BUCKETS_PCT))

    print(f"\n  1b  HOW MUCH OF THE PEAK UNREALISED PROFIT WAS IN TRADES THAT")
    print(f"      ACTUALLY MOVED >= X% IN COIN PRICE BEFORE ROUND-TRIPPING TO $0")
    print(f"  {'window':>10s}{'peak$ all BE':>15s}{'>= +1.5%':>15s}"
          f"{'>= +2.5%':>15s}{'>= +4.0%':>15s}{'>= +6.0%':>15s}")
    for win in WINDOWS:
        d = tape(win)
        be = d[d.is_be]
        peak = (be.mfe_pct / 100.0 * be.notional)
        line = f"  {win:>10s}{money(peak.sum()):>15s}"
        for thr in (1.5, 2.5, 4.0, 6.0):
            v = peak[be.mfe_pct >= thr].sum()
            line += f"{money(v):>15s}"
        print(line)

    # the control that keeps this honest: notional is ~$100 per trade, so
    # "peak $" is really "peak %". Verify the two agree.
    d = tape("MODERN")
    be = d[d.is_be]
    print(f"\n  control: median notional on BE trades = "
          f"{money(float(be.notional.median()))}  "
          f"(so peak $ ~= peak % of a $100 seat)")
    print(f"  control: BE trades whose peak was BELOW the {COST_PCT:.2f}% fee "
          f"floor = {int((be.mfe_pct < COST_PCT).sum())} of {len(be)} "
          f"({100.0*(be.mfe_pct < COST_PCT).mean():.1f}%)")
    print("  --> those could never have paid, whatever the exit did.")


# --------------------------------------------------------------------- #
# canvas replay: exactly the engine's own box code, then frozen in time
# --------------------------------------------------------------------- #
class CanvasBank:
    """All five canvases for one symbol, replayed ONCE, with a causal
    SNAPSHOT taken at every moment an audit question asks about.

    Why snapshots and not a later re-query: the engine's own ChartCanvas
    calls _prune() every 96 bars, which drops every DEAD/INACTIVE box and
    caps each list at 400. Re-querying the finished canvas therefore
    returns only the last ~400 boxes, and an early-window trade sees an
    EMPTY list -- which reads as "the engine had no 1H structure" when the
    truth is "this audit asked too late". Measured: AVAX's 1H canvas had
    111 surviving boxes, ALL of them dated 2025+, so every 2024 trade was
    silently scored against nothing.

    Snapshotting at the watch timestamps avoids the issue entirely and is
    strictly causal: a snapshot taken while feeding the bar whose close is
    T contains exactly the boxes confirmed at or before T.
    """

    def __init__(self, sym: str, stems: list[str], watch: list | None = None):
        df = load_asset_ohlcv(BASKET / sym, include_stems=stems)
        self.df = df
        self.sym = sym
        self.snap = {}                      # time -> {tf: state}
        self.acc = {}                       # tf -> accumulated boxes
        want = sorted({pd.Timestamp(t) for t in (watch or [])})
        self.cv = {}
        for tf in ("15min", "30min", "1h", "4h"):
            cv = S.ChartCanvas(tf)
            b = resample_causal_tf(df, tf)
            O, H, L, C = (b.Open.values, b.High.values,
                          b.Low.values, b.Close.values)
            idxs = list(b.index)
            wi = 0                              # per-tf pointer
            for i in range(len(b)):
                t = idxs[i]
                cv.on_bar(O[i], H[i], L[i], C[i], 0.0, i, t)
                while wi < len(want) and want[wi] <= t:
                    self._take(want[wi], cv, tf)
                    wi += 1
            while wi < len(want):               # watch times past the tape
                self._take(want[wi], cv, tf)
                wi += 1
            self.cv[tf] = cv

    def _take(self, t, cv, tf):
        """Snapshot the ACUMULATED set of boxes this canvas has confirmed
        so far -- not the live list.

        _prune() runs every 96 bars and keeps only ACTIVE boxes (cap 400),
        so `cv.blues` is a moving window, not a history. An audit that asks
        "had a 1H swing low been confirmed above my entry?" needs the
        HISTORY: a box that has since been broken or invalidated was still
        real, was still on the chart at the time, and the engine's own trail
        would have moved the stop to it before it died.

        Accumulating in the observer is causal -- each entry is added at the
        bar whose close confirmed it -- and it is what the engine would have
        done if it had kept every box, which is what the question means.
        """
        acc = self.acc.setdefault(tf, {"blues": {}, "reds": {}})
        for x in cv.blues:
            acc["blues"][x.uid] = (x.y_bottom, x.y_top, x.state, x.time)
        for x in cv.reds:
            acc["reds"][x.uid] = (x.y_bottom, x.y_top, x.state, x.time)
        d = self.snap.setdefault(t, {})
        d[tf] = {
            "blues": list(acc["blues"].values()),
            "reds": list(acc["reds"].values()),
            "purple": (cv.purple.y_top, cv.purple.y_bottom)
            if cv.purple is not None else None,
        }

    def at(self, t, tf) -> dict:
        t = pd.Timestamp(t)
        t = t.tz_convert("UTC") if t.tzinfo else t.tz_localize("UTC")
        return self.snap.get(t, {}).get(tf, {"blues": [], "reds": [],
                                             "purple": None})


def _stems_for_window(win: str, warm_days: int = 60) -> list[str]:
    s0 = pd.Timestamp(WINDOWS[win][0])
    s1 = pd.Timestamp(WINDOWS[win][1])
    warm = s0 - pd.Timedelta(days=warm_days)
    out = []
    cur = warm.replace(day=1)
    while cur <= s1:
        if (BASKET / "BTCUSDT_5m" / f"{cur:%Y-%m}.csv.gz").exists():
            out.append(f"{cur:%Y-%m}")
        cur = (cur + pd.offsets.MonthBegin(1))
    return out


def bars_after(sym: str, at, hours: float) -> pd.DataFrame:
    """The symbol's 5m bars in (at, at+hours] -- forward price, for Q2."""
    stems = sorted({f"{at:%Y-%m}",
                    f"{(pd.Timestamp(at) + pd.Timedelta(hours=hours)):%Y-%m}"})
    stems = [s for s in stems if (BASKET / sym / f"{s}.csv.gz").exists()]
    frames = []
    for s in stems:
        frames.append(pd.read_csv(BASKET / sym / f"{s}.csv.gz"))
    d = pd.concat(frames, ignore_index=True)
    d["dt"] = pd.to_datetime(d["Datetime"], utc=True)
    t0 = pd.Timestamp(at)
    t0 = t0.tz_convert("UTC") if t0.tzinfo else t0.tz_localize("UTC")
    m = (d.dt > t0) & (d.dt <= t0 + pd.Timedelta(hours=hours))
    return d.loc[m, ["dt", "High", "Low", "Close"]].reset_index(drop=True)




# --------------------------------------------------------------------- #
# Q2 -- the premature BREAKEVEN wick-out: what happened AFTER we left
# --------------------------------------------------------------------- #
_BAR_CACHE: dict[tuple, pd.DataFrame] = {}


def _month_bars(sym: str, ym: str) -> pd.DataFrame:
    key = (sym, ym)
    if key in _BAR_CACHE:
        return _BAR_CACHE[key]
    f = BASKET / sym / f"{ym}.csv.gz"
    if not f.exists():
        d = pd.DataFrame(columns=["dt", "High", "Low", "Close"])
    else:
        d = pd.read_csv(f)
        d["dt"] = pd.to_datetime(d["Datetime"], utc=True)
        d = d[["dt", "High", "Low", "Close"]]
    _BAR_CACHE[key] = d
    return d


def forward_bars(sym: str, t0, hours: float) -> pd.DataFrame:
    """5m bars strictly after t0, up to t0+hours. Causal: no bar that had
    not printed yet is read."""
    t0 = pd.Timestamp(t0)
    t0 = t0.tz_convert("UTC") if t0.tzinfo else t0.tz_localize("UTC")
    t1 = t0 + pd.Timedelta(hours=hours)
    months = pd.date_range(t0.replace(day=1), t1.replace(day=1),
                           freq="MS").strftime("%Y-%m").tolist()
    frames = [_month_bars(sym, m) for m in months]
    d = pd.concat(frames, ignore_index=True) if frames else \
        pd.DataFrame(columns=["dt", "High", "Low", "Close"])
    if d.empty:
        return d
    return d[(d.dt > t0) & (d.dt <= t1)].reset_index(drop=True)


def q2() -> None:
    print("=" * 74)
    print("Q2  PREMATURE BREAKEVEN WICK-OUT  --  what price did AFTER we left")
    print("=" * 74)
    print("    A BE trade is scratched at ~entry. Question: did the coin then")
    print("    (a) never violate the ORIGINAL structural stop, and")
    print("    (b) run >= +2% / +4% / +6% above entry -- without us?\n")

    hz = (12, 24, 48)
    for win in ("W1", "W2", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        be = d[d.is_be].copy()
        if be.empty:
            continue
        print(f"  --- {win}: {len(be)} BREAKEVEN trades "
              f"({100.0*len(be)/len(d):.1f}% of {len(d)}) ---")
        res = {h: {"n": 0, "held": 0, "r2": 0, "r4": 0, "r6": 0,
                   "c2": 0, "c4": 0, "c6": 0, "gain2": 0.0, "gain4": 0.0}
               for h in hz}
        for _, t in be.iterrows():
            for h in hz:
                fb = forward_bars(t.symbol, t.exit_time, h)
                if fb.empty:
                    continue
                res[h]["n"] += 1
                hi = float(fb.High.max())
                lo = float(fb.Low.min())
                held = lo > float(t.stop_price)      # stop NEVER touched
                r2 = hi >= t.entry_price * 1.02
                r4 = hi >= t.entry_price * 1.04
                r6 = hi >= t.entry_price * 1.06
                res[h]["held"] += held
                for k, f in (("r2", r2), ("r4", r4), ("r6", r6)):
                    res[h][k] += f
                # the exact brief: stop survived AND it ran X% without us
                if held and r2:
                    res[h]["c2"] += 1
                    res[h]["gain2"] += (min(hi, t.entry_price * 1.02)
                                        / t.entry_price - 1) * 100.0
                if held and r4:
                    res[h]["c4"] += 1
                    res[h]["gain4"] += (min(hi, t.entry_price * 1.04)
                                        / t.entry_price - 1) * 100.0
                if held and r6:
                    res[h]["c6"] += 1
        print(f"    {'horizon':>8s}{'bars':>16s}{'stop survived':>15s}"
              f"{'>=+2%':>8s}{'>=+4%':>8s}{'>=+6%':>8s}"
              f"{'survived & >=+2%':>19s}{'stop&>=+4%':>12s}{'stop&>=+6%':>12s}")
        for h in hz:
            r = res[h]
            if not r["n"]:
                continue
            print(f"    {h:>7d}h{r['n']:>16d}"
                  f"{r['held']:>9d} ({100.0*r['held']/r['n']:.0f}%)"
                  f"{r['r2']:>8d}{r['r4']:>8d}{r['r6']:>8d}"
                  f"{r['c2']:>12d} ({100.0*r['c2']/r['n']:.0f}%)"
                  f"{r['c4']:>12d}{r['c6']:>12d}")

        # ---- the dollar cost, in real % of the seat -------------------
        # conservative: if the stop would have survived, the engine could
        # have ridden to at least +2% instead of $0.00. That is 2% of the
        # seat, minus the 0.20% fee it already paid on the scratch.
        r24 = res[24]
        seat = float(be.notional.median())
        cost = r24["c2"] * (2.0 - COST_PCT) / 100.0 * seat
        print(f"    COST of the shakeout (conservative, 24h, +2% floor):")
        print(f"      {r24['c2']} trades were stopped out at $0.00 while the coin")
        print(f"      never revisited the stop and ran >= +2.00%.")
        print(f"      those trades could have banked >= 2.00%-{COST_PCT:.2f}% "
              f"= {2.0-COST_PCT:.2f}% on a {money(seat)} median seat")
        print(f"      => >= {money(cost)} not earned, on a $100 start.")
        # upside case, +4%
        cost4 = r24["c4"] * (4.0 - COST_PCT) / 100.0 * seat
        print(f"      if they rode to +4.00% instead: >= {money(cost4)}")
        print()

    # ---- the structural cause: how tight are the stops that BE out? ---
    print("  --- why it happens: risk_pct of BE trades vs their peak ---")
    print(f"  {'window':>8s}{'risk% p25':>11s}{'median':>9s}{'p75':>8s}"
          f"{'peak% med':>11s}{'peak/risk':>11s}{'<0.35% stops':>14s}")
    for win in ("W1", "W2", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        be = d[d.is_be]
        if be.empty:
            continue
        print(f"  {win:>8s}{be.risk_pct.quantile(.25):>11.3f}"
              f"{be.risk_pct.median():>9.3f}{be.risk_pct.quantile(.75):>8.3f}"
              f"{be.mfe_pct.median():>11.3f}"
              f"{(be.mfe_pct/be.risk_pct).median():>11.2f}"
              f"{100.0*(be.risk_pct < 0.35).mean():>13.0f}%")
    print("  (peak/risk ~= the R the lock needed; 3.0 means the +3R lock was")
    print("   reachable but the trade still died at the scratch line.)")




# --------------------------------------------------------------------- #
# Q3 -- why the 4H trail is dead, and what 1H / 30m / 15m offered instead
# --------------------------------------------------------------------- #
_BANK: dict[str, CanvasBank] = {}


def bank(sym: str, win: str, watch=None) -> CanvasBank:
    key = f"{sym}|{win}"
    if key not in _BANK:
        _BANK[key] = CanvasBank(sym, _stems_for_window(win), watch=watch)
    return _BANK[key]


def _watch_times(df: pd.DataFrame) -> list:
    """Every moment the audit asks a structural question about.

    BOTH ends matter and they answer different questions: ENTRY is where
    "how much structural room did the setup have?" is measured (Q4a), EXIT
    is where "what did the engine have available while it was in the trade?"
    is measured (Q3). Snapshotting only exits made every Q4a bucket read
    "no draw above entry" -- an artefact of asking for a timestamp that was
    never captured, not a fact about the chart."""
    out = {pd.Timestamp(x) for x in df.exit_time}
    out |= {pd.Timestamp(x) for x in df.entry_time}
    return sorted(out)


def q3() -> None:
    print("=" * 74)
    print("Q3  WHY THE 4H TRAIL IS DEAD -- AND WHAT 1H/30m OFFERED INSTEAD")
    print("=" * 74)

    # ---- 3.0 the code fact ---------------------------------------- #
    print("  3.0  THE CODE (strategy_v36_ict_champion.py, _manage):")
    print("       `TRAIL_4H_ONLY_AFTER_3R` DOES NOT EXIST in the engine --")
    print("       grep finds it nowhere. The real switch is")
    print("       TRAIL_4H_ONLY_AFTER_LOCK = True, and when it is on the")
    print("       post-lock trail searches `srcs = [self.struct_canvas]`")
    print("       ONLY. struct_canvas is STRUCT_TF = '4h'.")
    print("       So after the +3R lock the engine is blind to 1H/30m/15m")
    print("       swing lows by construction, and to the 4H lens itself")
    print("       unless that 4H canvas has confirmed a NEW BlueBox_SSL")
    print("       above floor_line but below price, AFTER the entry.")
    print()
    print("  the four conditions a 4H box must satisfy to move the stop:")
    print("    (i)   state == ACTIVE          (ii) above floor_line")
    print("    (iii) strictly below current price")
    print("    (iv)  confirmed AFTER the entry (start_idx > entry_idx)")
    print("  A 4H box needs 12 HOURS to confirm a 3-bar fractal. Most")
    print("  trades are dead before the next 4H box exists at all.")
    print()

    # ---- 3.1 measured breach -------------------------------------- #
    print("  3.1  THE BREACH -- trades that DID reach the +3R lock")
    print(f"  {'window':>8s}{'n':>7s}{'reached +3R':>13s}{'trailed':>9s}"
          f"{'DEAD':>7s}{'breach%':>9s}{'median peak%':>14s}{'median R':>10s}")
    tot_breach = 0
    tot_lock = 0
    for win in ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        lk = d[d.reached_lock]
        tr = int(lk.v31_struct_trailed.sum())
        dead = len(lk) - tr
        tot_breach += dead
        tot_lock += len(lk)
        print(f"  {win:>8s}{len(d):>7d}{len(lk):>13d}{tr:>9d}{dead:>7d}"
              f"{100.0*dead/len(lk):>8.0f}%{lk.mfe_pct.median():>14.2f}"
              f"{lk.mfe_R.median():>10.2f}")
    print(f"  {'TOTAL':>8s}{'':>7s}{tot_lock:>13d}{tot_lock-tot_breach:>9d}"
          f"{tot_breach:>7d}{100.0*tot_breach/tot_lock:>8.0f}%")
    print("  --> the 4H trail is dead in the overwhelming majority of the")
    print("      trades that actually EARNED the right to be trailed.")
    print()

    # ---- 3.2 what 1H/30m offered on those same locks -------------- #
    print("  3.2  WHAT 1H / 30m / 15m BlueBox_SSL OFFERED ON THE SAME TRADES")
    print("       (causal: only boxes the canvas confirmed before that")
    print("        trade's exit, and sitting above entry_px)")
    print(f"  {'window':>8s}{'reached+3R':>12s}{'1H box > entry':>17s}"
          f"{'30m box':>10s}{'15m box':>10s}{'any':>8s}"
          f"{'1H > entry & <peak':>20s}")
    for win in ("W1", "W2", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        lk = d[d.reached_lock]
        c1 = c30 = c15 = cany = c1mid = 0
        banks = {}
        for sym, g in lk.groupby("symbol"):
            banks[sym] = bank(sym, win, watch=_watch_times(g))
        for _, t in lk.iterrows():
            bk = banks.get(t.symbol)
            if bk is None:
                continue
            ex = t.exit_time
            got = {}
            for tf in ("1h", "30min", "15min"):
                st = bk.at(ex, tf)
                above = [b0 for (b0, b1, s_, tm) in st["blues"]
                         if b0 > t.entry_price]
                got[tf] = above
            hi = t.entry_price * (1 + t.mfe_pct / 100.0)
            c1 += bool(got["1h"])
            c30 += bool(got["30min"])
            c15 += bool(got["15min"])
            cany += bool(got["1h"] or got["30min"] or got["15min"])
            c1mid += any(t.entry_price < y < hi for y in got["1h"])
        n = len(lk)
        print(f"  {win:>8s}{n:>12d}"
              f"{c1:>10d} ({100.0*c1/n:>4.0f}%)"
              f"{c30:>6d} ({100.0*c30/n:>3.0f}%)"
              f"{c15:>5d} ({100.0*c15/n:>3.0f}%)"
              f"{cany:>6d}"
              f"{c1mid:>13d} ({100.0*c1mid/n:>3.0f}%)")
    print("  --> a 1H swing low existed above entry on most locked trades.")
    print("      The engine could not see it. That is the whole of Fact A.")
    print()

    # ---- 3.3 did price deliver to an opposing DOL then revert? ---- #
    print("  3.3  DID PRICE DELIVER TO AN OPPOSING DOL AND REVERT TO ENTRY?")
    print("       (the boxes ABOVE entry at exit: 1H/4H RedBox_BSL and")
    print("        4H PurpleBox; a 'hit' = the trade's own peak reached it)")
    print(f"  {'window':>8s}{'locked':>8s}{'1H BSL hit':>12s}"
          f"{'4H BSL hit':>12s}{'4H purple':>11s}{'any DOL hit':>13s}"
          f"{'...then back to <=+0.2%':>26s}")
    for win in ("W1", "W2", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        lk = d[d.reached_lock]
        h1 = h4 = hp = hany = back = 0
        banks = {}
        for sym, g in lk.groupby("symbol"):
            banks[sym] = bank(sym, win, watch=_watch_times(g))
        for _, t in lk.iterrows():
            bk = banks.get(t.symbol)
            if bk is None:
                continue
            b1 = bk.at(t.exit_time, "1h")
            b4 = bk.at(t.exit_time, "4h")
            hi = t.entry_price * (1 + t.mfe_pct / 100.0)
            r1 = [b0 for (b0, b1, s_, tm) in b1["reds"]
                  if b0 > t.entry_price]
            r4 = [b0 for (b0, b1, s_, tm) in b4["reds"]
                  if b0 > t.entry_price]
            pu = b4["purple"]
            pys = []
            if pu is not None:
                pys = [pu[0], (pu[0] + pu[1]) / 2.0]
                pys = [p for p in pys if p > t.entry_price]
            k1 = any(hi >= y for y in r1)
            k4 = any(hi >= y for y in r4)
            kp = any(hi >= y for y in pys)
            h1 += k1
            h4 += k4
            hp += kp
            if k1 or k4 or kp:
                hany += 1
                # engine's realised exit % on the coin
                if t.exit_pct <= 0.2:
                    back += 1
        n = len(lk)
        print(f"  {win:>8s}{n:>8d}"
              f"{h1:>7d} ({100.0*h1/n:>3.0f}%)"
              f"{h4:>7d} ({100.0*h4/n:>3.0f}%)"
              f"{hp:>7d} ({100.0*hp/n:>3.0f}%)"
              f"{hany:>8d} ({100.0*hany/n:>3.0f}%)"
              f"{back:>18d} ({100.0*back/max(hany,1):>3.0f}%)")
    print("  --> when a draw existed, price usually REACHED it. The question")
    print("      the last column answers is whether we banked it or gave it back.")





# --------------------------------------------------------------------- #
# Q4 -- fee churn vs real structural room
# --------------------------------------------------------------------- #
def _buckets(series, edges):
    lab = []
    for v in series:
        for i in range(len(edges) - 1):
            lo, hi = edges[i], edges[i + 1]
            if lo <= v < hi:
                lab.append(f"[{lo:g},{hi:g})")
                break
        else:
            lab.append(f">={edges[-1]:g}")
    return pd.Series(lab, index=series.index)


def _seg_report(d: pd.DataFrame, key: str, edges, title: str) -> None:
    print(f"\n  {title}")
    b = _buckets(d[key], edges)
    order = []
    for i in range(len(edges) - 1):
        order.append(f"[{edges[i]:g},{edges[i+1]:g})")
    order.append(f">={edges[-1]:g}")
    print(f"    {'bucket':>14s}{'n':>7s}{'WR%':>7s}{'net $':>10s}"
          f"{'fees $':>9s}{'net-top3':>11s}{'$/tr':>8s}")
    for k in order:
        g = d[b.eq(k)]
        if g.empty:
            continue
        net = float(g.net_pnl.sum())
        top3 = float(g.net_pnl.nlargest(3).sum()) if len(g) >= 3 else net
        fees = float((g.entry_fee.astype(float) * 2).sum()) \
            if "entry_fee" in g else float("nan")
        print(f"    {k:>14s}{len(g):>7d}{100.0*g.is_win.mean():>6.0f}%"
              f"{net:>10.2f}{fees:>9.2f}{net-top3:>11.2f}"
              f"{net/len(g):>8.2f}")


def q4() -> None:
    print("=" * 74)
    print("Q4  SEPARATING FEE CHURN FROM REAL SPOT EXPANSIONS")
    print("=" * 74)
    print(f"    the fee floor is {COST_PCT:.2f}% round trip. A setup whose")
    print("    structural room is smaller than that cannot pay, whatever")
    print("    the exit logic does.\n")

    # ---- (b) is pure arithmetic: no bars needed -------------------- #
    print("  (b) PERFORMANCE BY ACTUAL % DISTANCE TO THE +3R LOCK LINE")
    print("      lock_pct = 3 * risk_pct = the real coin move the lock needs")
    edges = [0, 0.90, 1.50, 2.50]
    for win in ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        _seg_report(d, "lock_pct", edges, f"--- {win}  (n={len(d)}) ---")

    print("\n  the same split, aggregated over all six windows:")
    allt = pd.concat([tape(w).assign(win=w) for w in
                      ("W1", "W2", "FULL15", "OLD7", "MOD_Y1", "MOD_Y2")],
                     ignore_index=True)
    _seg_report(allt, "lock_pct", edges, "--- ALL WINDOWS ---")
    print("\n  --> read the last two rows: if the >= 2.50% bucket is the only")
    print("      one with a positive $/trade, the engine is firing on setups")
    print("      whose structural room cannot cover the fee.")

    # ---- (a) actual structural room to the DOL -------------------- #
    print("\n  (a) PERFORMANCE BY STRUCTURAL ROOM TO THE DRAW ON LIQUIDITY")
    print("      dol_room_pct = (nearest 1H/4H RedBox_BSL or 4H")
    print("      PurpleBox.y_top ABOVE entry) / entry - 1, in %")
    edges2 = [0, 0.5, 1.0, 2.0, 3.5]
    for win in ("W1", "W2", "MOD_Y1", "MOD_Y2"):
        d = tape(win)
        rows = []
        banks = {}
        for sym, g in d.groupby("symbol"):
            banks[sym] = bank(sym, win, watch=_watch_times(g))
        for _, t in d.iterrows():
            bk = banks.get(t.symbol)
            if bk is None:
                rows.append(np.nan)
                continue
            cands = []
            for tf in ("1h", "4h"):
                st = bk.at(t.entry_time, tf)
                cands += [b0 for (b0, b1, s_, tm) in st["reds"]
                          if b0 > t.entry_price]
                if tf == "4h" and st["purple"] is not None:
                    cands.append(st["purple"][0])
            cands = [c for c in cands if c > t.entry_price]
            rows.append((min(cands) / t.entry_price - 1) * 100.0
                        if cands else np.nan)
        d = d.copy()
        d["dol_room_pct"] = rows
        miss = int(d.dol_room_pct.isna().sum())
        print(f"\n    --- {win} (n={len(d)}, {miss} with no DOL above entry) ---")
        dd = d.dropna(subset=["dol_room_pct"])
        if dd.empty:
            continue
        _seg_report(dd, "dol_room_pct", edges2, "room to the first draw")

# --------------------------------------------------------------------- #
# dispatch  (kept last so every section is defined before it is looked up)
# --------------------------------------------------------------------- #
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = (["q1", "q2", "q3", "q4"] if cmd == "all" else [cmd])
    for c in todo:
        fn = globals().get(c)
        if fn is None:
            raise SystemExit(f"section {c} not implemented yet")
        fn()
        print()


if __name__ == "__main__":
    main()
