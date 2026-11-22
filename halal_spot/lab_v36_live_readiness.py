#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v36_live_readiness.py -- the field check before any live money.

v36 engine = strategy_v36_ict_champion.py, whose DEFAULTS are now the v35
champion `S1_COIN_GUARD_BOS` (one seat, all cash, K=2 quarantine lifted only
by a fresh causal 4H BOS) plus the 8-dp export fix and EXIT_SLIPPAGE_BPS.

TASKS
  1  the champion is the default, and the PURE stack that v35 never measured:
     `S1_BOS_PLUS_FLASH` = champion + FLASH_SELLER only, WIDE_CAP firmly off.
  2  spot exit-slippage stress: a resting limit entry does not slip, the
     stop-market SELLS do. 0 / 3 / 5 / 8 bps on the exits, and a brutal
     double 5 bps for reference.
  3  blind windows outside v32..v35: the 15 continuous months from $100 with
     no reset (including Aug/Sep 2023 and the April 2024 crash), then the
     modern months.

USAGE
    python3 lab_v36_live_readiness.py arms
    python3 lab_v36_live_readiness.py run ARM [--window W1|W2|FULL15|MODERN|OLD7]
    python3 lab_v36_live_readiness.py statement ARM W1
    python3 lab_v36_live_readiness.py report
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

BASKET = str(HERE / "data" / "binance_5m")          # the validated dev set
BASKET_OOS = str(HERE / "data" / "binance_5m_oos")   # + the fetched months
WINDOWS = {
    "W1": ("2023-10-01", "2024-03-31"),
    "W2": ("2024-05-01", "2024-10-31"),
    # the continuous series: every month on disk, one $100 account
    "FULL15": ("2023-08-01", "2024-10-31"),
    # untouched modern data (2024-11 .. 2026-11 is on disk)
    "MODERN": ("2024-11-01", "2026-10-31"),
    # untouched older data
    "OLD7": ("2023-01-01", "2023-07-31"),
}
SWEEP_CSV = Path(os.environ.get("V36_SWEEP",
                                str(RESULTS / "lab_v36_sweep.csv")))

# --------------------------------------------------------------------- #
# BASE = the shipped v31 champion C_124 at $100, with every v32 pillar
# switched OFF, so the basket arms are measured as a DELTA against a book
# we already know (v32 with ALLOC_MODE="allcash" must equal v31 exactly).
# --------------------------------------------------------------------- #
BASE = dict(
    # v31 C_124
    ENTRY_ARM="seam", FILL_MODE="blind", MANAGE_5M=False,
    STRUCT_TRAIL=True, STRUCT_TRAIL_MIN_R=1.0, STRUCT_TRAIL_SRC="exec",
    STRUCT_TRAIL_NEEDS_DISP=False, SWIN_MIN_R=0.05, SWIN_CLEARS_VIGIL=False,
    LOCK_ARM_R=3.0, LOCK_MODE="trail", HARVEST_PCT=0.0,
    IMPULSE_PURPLE=False, IMPULSE_MAX_BARS=240, VIGILANCE_SCOPE="none",
    SHIELD_RULE_V30="MID|BOS", ENTRY_BRAIN="sniper", BE_STREAK_MODE="reset",
    RISK_FLOOR_PCT=0.10, RISK_FLOOR_STAGE="both", SIZING="allcash",
    DOLLAR_R_PCT=0.3267, SLIPPAGE_BPS=0.0,
    # v32 basket
    CAPITAL=100.0, V32_DATA_DIR=BASKET, SYMBOL_WHITELIST=None, MAX_COINS=8,
    ALLOC_MODE="allcash", SLOTS=1, SLOT_FILL="fixed", RECYCLE_CASH=True,
    SMT_BRAIN=False, SMT_GATE="off", SMT_MAX_AGE=12,
    REGIME_MODE="A", REGIME_B_NEEDS_HL=True, REGIME_B_NEEDS_BSL=True,
    KILLZONE_MODE="off", KILLZONE_HOURS=(), KILLZONE_DOW=(),
    EMERGENCY_WICK_STOP=True, CLOSE_BASED_SHIELD=False,
    # ---- v33 knobs, EVERY one at its engine default -------------------
    # drive() only setattr()s the keys a combo lists, so any knob missing
    # from BASE keeps whatever the PREVIOUS arm left in the module. That
    # bug was measured, not theorised: the arm printed as LEAD2 also
    # carried TEL's trail lens, and REARM carried both - its counter
    # v33_leader_veto=356 fired although its own config never set
    # V33_ALPHA_LEADER. Those two runs were RELABELLED (TEL_LEAD2 and
    # TEL_LEAD2_REARM), not deleted: the measurements are valid, only the
    # names were wrong. BASE is now complete and guarded below.
    # BASE mirrors the ENGINE defaults (drive() raises if they disagree).
    # v33 ships the telescope, so BASE carries it; V32FULL below switches it
    # back off explicitly to reproduce the v32 book.
    SLOT_DEPLOY_PCT=1.0, TRAIL_LENS_PRE="struct4h", TRAIL_MIN_R_PRE=None,
    TRAIL_4H_ONLY_AFTER_LOCK=True, PURPLE_REARM=False,
    # ---- v34 knobs at their engine defaults (see V34_KNOBS) -----------
    MAX_OPEN_POSITIONS=1, FULL_100_DEPLOY=True, MIN_RRR=3.0, LOCK_R=3.0,
    BRIDGE_1H_PRE_LOCK=False, BRIDGE_ARM_R=1.2, OPPORTUNITY_SWAP=False,
    STALE_HOURS=12.0, STALE_MAX_R=0.8, FAST_HARVEST_2R=False,
    FAST_HARVEST_TRAIL_IF="disp_bos",
    # ---- v35 knobs at their engine defaults -------------------------- #
    MIN_STOP_PCT=0.0, NO_FALL_CLOSE=False, PER_COIN_COOLDOWN=2,
    COOLDOWN_DAYS=14.0, COOLDOWN_NEEDS_BOS=True,
    COOLDOWN_NEEDS_BOS_TIME=False, FLASH_SELLER_VETO=False,
    # ---- v36 SHIPPED defaults: the v35 champion is the engine now ------
    # These are no longer "arm overrides": the engine at import time IS the
    # champion. BASE states them so the guard can prove engine == BASE.
    EXIT_SLIPPAGE_BPS=0.0,
    V33_ALPHA_LEADER=False, LEADER_K=2, LEADER_NEEDS_HTF=False,
    LEADER_MIN_DISP=0.0, LEADER_SMT_REQUIRED=False,
    LEADER_15M_ONLY_TOP1=False, BASKET_REGIME=False, REGIME_EXPAND_MIN=3,
    RANGE_VETO_WEAPON_B=True, RANGE_HARVEST_4H=False,
)

# v34 knobs, every one listed at its engine default (guard in drive()).
V34_KNOBS = ("MAX_OPEN_POSITIONS", "FULL_100_DEPLOY", "MIN_RRR", "LOCK_R",
             "BRIDGE_1H_PRE_LOCK", "BRIDGE_ARM_R", "OPPORTUNITY_SWAP",
             "STALE_HOURS", "STALE_MAX_R", "FAST_HARVEST_2R",
             "FAST_HARVEST_TRAIL_IF")

# Every knob an arm may touch. Used by the anti-leak guard in drive().
V33_KNOBS = ("SLOT_DEPLOY_PCT", "TRAIL_LENS_PRE", "TRAIL_MIN_R_PRE",
             "TRAIL_4H_ONLY_AFTER_LOCK", "PURPLE_REARM", "V33_ALPHA_LEADER",
             "LEADER_K", "LEADER_NEEDS_HTF", "LEADER_MIN_DISP",
             "LEADER_SMT_REQUIRED", "LEADER_15M_ONLY_TOP1", "BASKET_REGIME",
             "REGIME_EXPAND_MIN", "RANGE_VETO_WEAPON_B", "RANGE_HARVEST_4H")
_DEFAULTS_CHECKED = []

# The v35 knobs, every one at its engine default (guard in drive()).
V35_KNOBS = ("MIN_STOP_PCT", "NO_FALL_CLOSE", "PER_COIN_COOLDOWN",
             "COOLDOWN_DAYS", "COOLDOWN_NEEDS_BOS", "COOLDOWN_NEEDS_BOS_TIME",
             "FLASH_SELLER_VETO")
# v36 knobs: the shipped champion state + the spot exit slippage.
V36_KNOBS = ("EXIT_SLIPPAGE_BPS", "SLIPPAGE_BPS")

# The champion is now the ENGINE, so an arm only lists what it CHANGES.
# S1 and SMTKZ stay explicit so an arm can still be read as a full statement
# of the shipped strategy (v34's mistake was implying a setting it never set).
S1 = dict(ALLOC_MODE="slot", SLOTS=1, SLOT_FILL="fixed",
          MAX_OPEN_POSITIONS=1, FULL_100_DEPLOY=True,
          PER_COIN_COOLDOWN=2, COOLDOWN_DAYS=14.0, COOLDOWN_NEEDS_BOS=True)
SMTKZ = dict(SMT_BRAIN=True, SMT_GATE="prefer",
             KILLZONE_MODE="exclude", KILLZONE_DOW=(6,))
NO_WIDE_CAP = dict(MIN_STOP_PCT=0.0, NO_FALL_CLOSE=False)   # explicitly OFF

COMBOS = {
    # 1 - THE SHIPPED CHAMPION. Must reproduce v35's S1_COIN_GUARD_BOS
    #     bit for bit (W1 $158.02 / W2 $194.38), which also proves the
    #     8-dp export fix did not touch a single fill.
    "S1_COIN_GUARD_BOS":     dict(**S1, **SMTKZ, **NO_WIDE_CAP),
    # 2 - THE PURE STACK v35 NEVER MEASURED: the champion + FLASH_SELLER,
    #     with WIDE_CAP (which lost money) firmly OFF. v35's
    #     S1_SURGICAL_COMBO mixed in MIN_STOP_PCT=0.25, so its +88% says
    #     nothing about this pair.
    "S1_BOS_PLUS_FLASH":     dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  FLASH_SELLER_VETO=True),
    # 3 - exit-slippage ladder on the shipped champion. A resting spot BUY
    #     LIMIT fills at its own price (0 bps on the entry); the stop-market
    #     SELLS pay 3 / 5 / 8 bps.
    "SLIP_0":                dict(**S1, **SMTKZ, **NO_WIDE_CAP),
    "EXIT_SLIP_1BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  EXIT_SLIPPAGE_BPS=1.0),
    "EXIT_SLIP_2BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  EXIT_SLIPPAGE_BPS=2.0),
    "EXIT_SLIP_3BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  EXIT_SLIPPAGE_BPS=3.0),
    "EXIT_SLIP_5BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  EXIT_SLIPPAGE_BPS=5.0),
    "EXIT_SLIP_8BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  EXIT_SLIPPAGE_BPS=8.0),
    # the brutal reference: 5 bps on BOTH sides through the old COST path
    "BOTH_SLIP_5BPS":        dict(**S1, **SMTKZ, **NO_WIDE_CAP,
                                  SLIPPAGE_BPS=5.0),
}
ORDER = ["S1_COIN_GUARD_BOS", "S1_BOS_PLUS_FLASH", "SLIP_0",
         "EXIT_SLIP_1BPS", "EXIT_SLIP_2BPS", "EXIT_SLIP_3BPS",
         "EXIT_SLIP_5BPS", "EXIT_SLIP_8BPS", "BOTH_SLIP_5BPS"]

WATCH = ("v36_exit_slip_charged",
         "v35_dust_box_veto", "v35_flash_seller_veto", "v35_fall_close_veto",
         "v35_cooldown_armed", "v35_cooldown_skip", "v35_cooldown_expired",
         "v35_cooldown_lifted_by_bos", "slot_full_rejects",
         "portfolio_slots_full", "v31_struct_trail", "trail_4h_structural",
         "fill_below_exchange_min", "v34_deploy_full_ok",
         "v33_stamp_expand", "v33_stamp_range")


def drive(combo: str, win: str, save: bool = True):
    import strategy_v36_ict_champion as S
    if combo not in COMBOS:
        raise SystemExit(f"unknown combo {combo!r} (would silently run BASE)")
    cfg = dict(BASE)
    cfg.update(COMBOS[combo])
    # ---- ANTI-LEAK GUARD (added after the mislabelled LEAD2/REARM runs) --
    missing = [k for k in V33_KNOBS + V34_KNOBS + V35_KNOBS + V36_KNOBS if k not in cfg]
    if missing:
        raise SystemExit(f"combo {combo}: BASE lacks v33 knobs {missing}; "
                         "they would inherit the previous arm's values")
    if not _DEFAULTS_CHECKED:
        # first run in this process: BASE must equal the engine's shipped
        # defaults, or a typo in BASE silently redefines every arm
        bad = {k: (BASE[k], getattr(S, k)) for k in V33_KNOBS + V34_KNOBS + V35_KNOBS + V36_KNOBS
               if BASE[k] != getattr(S, k)}
        if bad:
            raise SystemExit(f"BASE disagrees with the engine defaults: {bad}")
        _DEFAULTS_CHECKED.append(True)
        print("    [guard] BASE == engine defaults for all "
              f"{len(V33_KNOBS) + len(V34_KNOBS)} v33+v34 knobs",
              flush=True)
    # the OOS windows need the enlarged basket; W1/W2 must keep the exact
    # dev set so the identity check stays bit-for-bit
    cfg = dict(cfg)
    cfg["V32_DATA_DIR"] = (BASKET_OOS if win in ("FULL15", "MODERN", "OLD7")
                           else BASKET)
    for k, v in cfg.items():
        if not hasattr(S, k):        # an undefined knob is a SILENT no-op
            raise SystemExit(f"combo {combo}: engine has no knob {k!r}")
        setattr(S, k, v)
    start, end = WINDOWS[win]
    print(f"\n##### LIVE ENGINE combo={combo} {win} {start}..{end} #####",
          flush=True)
    print("    cfg: " + "  ".join(f"{k}={v}" for k, v in cfg.items()
                                 if v != BASE.get(k)) or "    cfg: = BASE",
          flush=True)
    t0 = time.time()
    run = S.run_backtest(S.v34_data_dir(), start, end, tag=f"v34{combo}{win}")
    secs = time.time() - t0
    tr = pd.DataFrame(run["trades"])
    eq = run["equity"]
    res = {"combo": combo, "window": win, "start": start, "end": end,
           "seconds": round(secs, 1), "symbols": run["symbols"],
           "capital": float(S.CAPITAL), "n": int(len(tr))}
    cash_end = float(run["pool_cash_end"])
    if len(tr):
        for c in ("R", "net_pnl", "entry_time", "exit_time", "symbol",
                  "exit_reason"):
            if c not in tr.columns:
                tr[c] = np.nan if c in ("R", "net_pnl") else ""
        tr["R"] = tr["R"].astype(float)
        tr["net_pnl"] = tr["net_pnl"].astype(float)
        cls = tr["class"].astype(str)
        res.update(
            totR=round(float(tr.R.sum()), 4),
            wins=int(cls.isin(["WIN", "SWIN"]).sum()),
            swin=int(cls.eq("SWIN").sum()),
            be=int(cls.isin(["BE", "BREAKEVEN"]).sum()),
            losses=int(cls.eq("LOSS").sum()),
            wr=round(100.0 * cls.isin(["WIN", "SWIN"]).sum() / len(tr), 2),
            wr_strict=round(100.0 * cls.eq("WIN").sum() / len(tr), 2),
            net=round(float(tr.net_pnl.sum()), 4),
            end_equity=round(100.0 + float(tr.net_pnl.sum()), 4)
            if abs(S.CAPITAL - 100.0) < 1e-9
            else round(float(S.CAPITAL) + float(tr.net_pnl.sum()), 4),
            pool_cash_end=round(cash_end, 4),
            maxR=round(float(tr.R.max()), 3),
            fees=round(float(run["fees"]), 4),
            by_coin={k: [int(v), round(float(g.R.sum()), 3),
                         round(float(g.net_pnl.sum()), 3)]
                     for k, (v, g) in
                     ((k, (len(g), g)) for k, g in tr.groupby("symbol"))},
            exits=tr.exit_reason.value_counts().to_dict(),
        )
        gp = float(tr.loc[tr.net_pnl > 0, "net_pnl"].sum())
        gl = float(-tr.loc[tr.net_pnl < 0, "net_pnl"].sum())
        res["pf"] = round(gp / gl, 3) if gl > 1e-9 else float("inf")
    if len(eq):
        e = eq["equity"].astype(float)
        peak = e.cummax()
        res["maxDD_pct"] = round(float(((e / peak) - 1.0).min() * 100.0), 3)
        res["eq_end"] = round(float(e.iloc[-1]), 4)
        res["eq_min"] = round(float(e.min()), 4)
    res["counters"] = {k: int(run["count"].get(k, 0)) for k in WATCH}
    res["v33_stamps_expand"] = int(run.get("v33_stamps_expand", 0))
    res["v33_stamps_range"] = int(run.get("v33_stamps_range", 0))
    res["v33_leader_stamps"] = run.get("v33_leader_stamps", {})
    if len(tr):
        # How big were the winners IN PRICE, not in R? R hides the choke
        # because the median stop is only 0.41% wide.
        pr = ((tr.exit_price.astype(float) / tr.entry_price.astype(float)
               - 1.0) * 100.0)
        res["price_move_pct"] = {
            "median_all": round(float(pr.median()), 3),
            "median_winners": round(float(pr[tr.net_pnl > 0].median()), 3)
            if bool((tr.net_pnl > 0).any()) else None,
            "max": round(float(pr.max()), 3),
            "wins_over_5pct": int((pr > 5).sum()),
            "wins_over_15pct": int((pr > 15).sum())}
        rw = tr.risk_pct.astype(float)
        res["stop_width_pct"] = {"median": round(float(rw.median()), 4),
                                 "min": round(float(rw.min()), 4),
                                 "max": round(float(rw.max()), 4)}
        res["bars_held_median"] = float(tr.bars_held.median())
        gp = float(tr.loc[tr.net_pnl > 0, "net_pnl"].sum())
        res["fee_share_of_gross_wins_pct"] = (
            round(100.0 * float(run["fees"]) / gp, 2) if gp > 1e-9 else None)
    res["smt_bull_stamps"] = int(run.get("smt_bull_stamps", 0))
    res["smt_stamps"] = int(run.get("smt_stamps", 0))
    print(f"    n={res['n']} totR={res.get('totR')} "
          f"end=${res.get('end_equity')} DD={res.get('maxDD_pct')}% "
          f"({secs:.0f}s)", flush=True)
    print("    coins: " + json.dumps(res.get("by_coin", {})), flush=True)
    print("    counters: " + json.dumps(
        {k: v for k, v in res["counters"].items() if v}), flush=True)
    if save:
        if len(tr):
            tr.to_csv(RESULTS / f"trades_v36_{combo}_{win}.csv", index=False)
        (RESULTS / f"lab_v36_{combo}_{win}.json").write_text(
            json.dumps(res, indent=1, default=str))
        row = {k: res.get(k) for k in
               ("combo", "window", "n", "totR", "net", "end_equity",
                "maxDD_pct", "wr", "wr_strict", "pf", "maxR", "fees",
                "seconds")}
        row["by_coin_R"] = json.dumps(
            {k: v[1] for k, v in res.get("by_coin", {}).items()})
        row["counters"] = json.dumps(
            {k: v for k, v in res["counters"].items() if v})
        df = pd.DataFrame([row])
        header = not SWEEP_CSV.exists()
        df.to_csv(SWEEP_CSV, mode="a", index=False, header=header)
    return res


def statement(combo: str, win: str):
    """Table 2: the monthly (1..6) and weekly (1..26) statement of the book.

    Ending balance is taken from the engine's own per-stamp equity marks
    (cash + open positions at market), so an open runner counts; per-coin
    contribution, WR%, totR, PF and maxDD% are computed on the trades that
    CLOSED inside the bucket.
    """
    f = RESULTS / f"trades_v36_{combo}_{win}.csv"
    j = RESULTS / f"lab_v36_{combo}_{win}.json"
    if not f.exists():
        raise SystemExit(f"run it first: python3 {Path(__file__).name} run "
                         f"{combo} --window {win}")
    tr = pd.read_csv(f, parse_dates=["entry_time", "exit_time"])
    meta = json.loads(j.read_text())
    cap = float(meta.get("capital", 100.0))
    tr["net_pnl"] = tr["net_pnl"].astype(float)
    tr["R"] = tr["R"].astype(float)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True,
                                     format="mixed").dt.tz_localize(None)
    tr["cls"] = tr["class"].astype(str)

    def bucket(g, label):
        win_mask = g["cls"].isin(["WIN", "SWIN"])
        gp = float(g.loc[g.net_pnl > 0, "net_pnl"].sum())
        gl = float(-g.loc[g.net_pnl < 0, "net_pnl"].sum())
        coins = {k: round(float(v), 2)
                 for k, v in g.groupby("symbol").net_pnl.sum().items()
                 if abs(v) > 1e-9}
        return {"bucket": label, "n": int(len(g)),
                "W": int(win_mask.sum()),
                "L": int((g["cls"] == "LOSS").sum()),
                "BE": int(g["cls"].isin(["BE", "BREAKEVEN"]).sum()),
                "WR%": round(100.0 * win_mask.sum() / len(g), 1) if len(g)
                else None,
                "totR": round(float(g.R.sum()), 2),
                "net$": round(float(g.net_pnl.sum()), 2),
                "PF": round(gp / gl, 2) if gl > 1e-9 else None,
                "by_coin$": coins}

    out = {"combo": combo, "window": win, "capital": cap,
           "final_equity": meta.get("end_equity"),
           "maxDD_pct": meta.get("maxDD_pct")}
    # ---- monthly: ending balance walks the closed-trade cash ladder ------
    rows, bal = [], cap
    months = sorted({t.strftime("%Y-%m") for t in tr.exit_time})
    for m in months:
        g = tr[tr.exit_time.dt.strftime("%Y-%m") == m]
        bal += float(g.net_pnl.sum())
        r = bucket(g, m)
        r["end_balance$"] = round(bal, 2)
        sub = tr[tr.exit_time <= pd.Timestamp(m + "-01") + pd.offsets.MonthEnd(0)]
        e = cap + float(sub.net_pnl.sum())
        pk = cap
        for v in sub.net_pnl.cumsum():
            pk = max(pk, cap + v)
        r["maxDD%_cum"] = round(100.0 * (e / pk - 1.0), 2) if pk else None
        rows.append(r)
    out["monthly"] = rows
    # ---- weekly: ISO weeks of the window ---------------------------------
    rows, bal = [], cap
    s0, s1 = pd.Timestamp(meta["start"]), pd.Timestamp(meta["end"])
    weeks = pd.date_range(s0, s1, freq="7D")
    for i, w0 in enumerate(weeks, start=1):
        w1 = min(w0 + pd.Timedelta(days=7), s1 + pd.Timedelta(days=1))
        g = tr[(tr.exit_time >= w0) & (tr.exit_time < w1)]
        bal += float(g.net_pnl.sum())
        r = bucket(g, f"W{i:02d} {w0.date()}")
        r["end_balance$"] = round(bal, 2)
        rows.append(r)
    out["weekly"] = rows
    dest = RESULTS / f"statement_v36_{combo}_{win}.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["monthly"], indent=1, default=str))
    print(f"\n{len(out['weekly'])} weekly buckets -> {dest.name}")
    print("weekly end balances: " + " ".join(
        f"{r['end_balance$']:.2f}" for r in out["weekly"]))
    return out


def report() -> int:
    """The full result table + the two ledgers, from the saved artefacts."""
    import json as _j
    W_ = 132
    print("\n" + "=" * W_)
    print("LAB v35 -- THE SURGICAL SHIELD : every arm, both windows, chained")
    print("=" * W_)
    print(f"{'arm':24s} {'W1 n':>5s} {'W1 R':>9s} {'W1 end$':>9s} {'W1 DD%':>7s} "
          f"{'W2 n':>5s} {'W2 R':>9s} {'W2 end$':>9s} {'W2 DD%':>7s} "
          f"{'chained':>9s} {'net$/DD':>8s}")
    rows = []
    for combo in ORDER:
        try:
            j1 = _j.loads((RESULTS / f"lab_v36_{combo}_W1.json").read_text())
            j2 = _j.loads((RESULTS / f"lab_v36_{combo}_W2.json").read_text())
        except FileNotFoundError:
            print(f"{combo:24s}  (not run yet)")
            continue
        ch = (float(j1["end_equity"]) / 100.0) * (float(j2["end_equity"]) / 100.0) - 1
        dd = max(abs(float(j1["maxDD_pct"])), abs(float(j2["maxDD_pct"])))
        net = float(j1["net"]) + float(j2["net"])
        rows.append(dict(combo=combo, ch=ch, r=net / dd if dd else 0,
                         j1=j1, j2=j2))
        print(f"{combo:24s} {int(j1['n']):5d} {float(j1['totR']):+9.2f} "
              f"{float(j1['end_equity']):9.2f} {float(j1['maxDD_pct']):7.2f} "
              f"{int(j2['n']):5d} {float(j2['totR']):+9.2f} "
              f"{float(j2['end_equity']):9.2f} {float(j2['maxDD_pct']):7.2f} "
              f"{100*ch:+8.2f}% {net/dd if dd else 0:8.2f}")
    if rows:
        best = max(rows, key=lambda r: r["ch"])
        print(f"\n  BEST CHAINED: {best['combo']}  {100*best['ch']:+.2f}%  "
              f"(net$/maxDD {best['r']:.2f})")
        best_r = max(rows, key=lambda r: r["r"])
        print(f"  BEST RISK-ADJUSTED (net$/maxDD): {best_r['combo']}  "
              f"{best_r['r']:.2f}")
        # counters that prove the shields fired
        print("\n  counters (W1 / W2):")
        keys = sorted({k for r in rows for k in
                       (list(r['j1'].get('counters', {})) )})
        for k in keys:
            a = int(rows[0]['j1'].get('counters', {}).get(k, 0))
            b = int(rows[0]['j2'].get('counters', {}).get(k, 0))
            if not (a or b):
                continue
            print(f"    {k:32s} " + "  ".join(
                f"{r['combo'][:14]}={int(r['j1'].get('counters',{}).get(k,0))}/"
                f"{int(r['j2'].get('counters',{}).get(k,0))}" for r in rows))
        # the monthly + weekly ledgers of the best arm
        for combo in ("BASE_S1_TEL_3R", "S1_COIN_GUARD_BOS",
                      "S1_FLASH_SELLER", "S1_WIDE_CAP"):
            if not (RESULTS / f"statement_v36_{combo}_W1.json").exists():
                continue
            sub_ledger(combo, "W1"); sub_ledger(combo, "W2")
    return 0


def sub_ledger(combo, win):
    import json as _j
    f = RESULTS / f"statement_v36_{combo}_{win}.json"
    if not f.exists():
        return
    st = _j.loads(f.read_text())
    print(f"\n  --- LEDGER {combo} {win} : months ---")
    print(f"  {'month':8s} {'start$':>8s} {'end$':>8s} {'$':>8s} {'%':>7s} "
          f"{'n':>4s} {'W/BE/L':>10s} {'PF':>6s}")
    for m in st["monthly"]:
        prev = float(m["end_balance$"]) - float(m["net$"])
        print(f"  {m['bucket']:8s} {prev:8.2f} {float(m['end_balance$']):8.2f} "
              f"{float(m['net$']):+8.2f} {100*float(m['net$'])/prev:+7.2f} "
              f"{int(m['n']):4d} {int(m['W']):3d}/{int(m['BE']):2d}/{int(m['L']):2d} "
              f"{(m.get('PF') or 0):6.2f}")
    wk = sorted(st["weekly"], key=lambda r: -float(r["net$"]))[:10]
    print(f"  best 10 weeks:")
    for r in wk:
        print(f"    {r['bucket']:12s} {float(r['net$']):+8.2f}$ "
              f"{int(r['n']):3d} fills W{int(r['W'])}/BE{int(r['BE'])}/L{int(r['L'])}  "
              + " ".join(f"{k[:-3]}{v:+.2f}" for k, v in
                         sorted((r.get('by_coin$') or {}).items(),
                                key=lambda kv: -kv[1])[:3]))


def longrun(combo: str) -> int:
    """The 15 continuous months, month by month, from ONE $100 account."""
    import json as _j
    W_ = 120
    for win in ("FULL15", "MODERN", "OLD7"):
        f = RESULTS / f"statement_v36_{combo}_{win}.json"
        if not f.exists():
            print(f"\n  {win}: not run yet ({f.name})")
            continue
        st = _j.loads(f.read_text())
        print("\n" + "=" * W_)
        print(f"{win}  {st.get('capital')} -> {st.get('final_equity')}   "
              f"maxDD {st.get('maxDD_pct')}%   arm {combo}")
        print("=" * W_)
        print(f"{'month':8s} {'start$':>9s} {'end$':>9s} {'$':>9s} {'%':>8s} "
              f"{'n':>4s} {'W/BE/L':>11s} {'PF':>6s}  best coin")
        for m in st["monthly"]:
            prev = float(m["end_balance$"]) - float(m["net$"])
            coins = m.get("by_coin$") or {}
            top = (max(coins.items(), key=lambda kv: kv[1]) if coins else ("-", 0))
            print(f"{m['bucket']:8s} {prev:9.2f} {float(m['end_balance$']):9.2f} "
                  f"{float(m['net$']):+9.2f} {100*float(m['net$'])/prev:+8.2f} "
                  f"{int(m['n']):4d} {int(m['W']):3d}/{int(m['BE']):2d}/{int(m['L']):2d} "
                  f"  {(m.get('PF') or 0):6.2f}  {top[0][:6]} {top[1]:+.2f}")
        tot = sum(float(m["net$"]) for m in st["monthly"])
        pos = sum(1 for m in st["monthly"] if float(m["net$"]) > 0)
        print(f"{'TOTAL':8s} {float(st['capital']):9.2f} "
              f"{float(st['final_equity']):9.2f} {tot:+9.2f} "
              f"{100*tot/float(st['capital']):+8.2f} "* 1)
        print(f"  months positive: {pos}/{len(st['monthly'])}")
        wk = sorted(st["weekly"], key=lambda r: -float(r["net$"]))[:10]
        print("  best 10 weeks:")
        for r in wk:
            print(f"    {r['bucket']:14s} {float(r['net$']):+9.2f}$  "
                  f"{int(r['n']):3d} fills W{int(r['W'])}/BE{int(r['BE'])}/L{int(r['L'])}  "
                  + " ".join(f"{k[:-3]}{v:+.2f}" for k, v in
                             sorted((r.get('by_coin$') or {}).items(),
                                    key=lambda kv: -kv[1])[:3]))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "arms":
        for k, v in COMBOS.items():
            print(f"{k:12s} " + "  ".join(f"{a}={b}" for a, b in v.items()))
        return 0
    if cmd == "run":
        wins = ["W1", "W2"]
        if "--window" in sys.argv:
            wins = [sys.argv[sys.argv.index("--window") + 1]]
        elif "--all-windows" in sys.argv:
            wins = list(WINDOWS)
        args = [a for a in sys.argv[2:]
                if not a.startswith("--") and a not in wins]
        for combo in args or list(COMBOS):
            for w in wins:
                drive(combo, w)
        return 0
    if cmd == "report":
        return report()
    if cmd == "longrun":
        return longrun(sys.argv[2] if len(sys.argv) > 2
                       else "S1_COIN_GUARD_BOS")
    if cmd == "statement":
        combo = sys.argv[2]
        win = sys.argv[3] if len(sys.argv) > 3 else "W1"
        statement(combo, win)
        return 0
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
