#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lab_v32_superbrain_6m.py — the live laboratory for the v32 MULTI-COIN ICT
SUPER-BRAIN. Same discipline as lab_v31_compounding_brain.py: every arm is
measured by running the REAL engine (`strategy_v32_ict_superbrain
.run_backtest`) on the real Binance SPOT basket, never by filtering a book
after the fact (a vetoed fill changes the streak/vigilance state machine, so
post-hoc filtering is not the same strategy).

DATA (see build_5m_from_1m.py for the full provenance + bit-exactness proof)
    data/binance_5m/<SYM>_5m/<YYYY-MM>.csv.gz, 8 coins, 2023-08..2024-10.
    BTCUSDT/ETHUSDT come from the official Binance monthly 5m ZIPs; the six
    altcoins are resampled from the official Binance spot 1m monthly archives
    and the resampler was PROVEN bit-exact against those ZIPs on 263,808
    bars (Open/High/Low/Close/Volume, 30 coin-months, 0 mismatches).

WINDOWS (the brief's two 6-month dev windows; 5.8 years stays forbidden)
    W1 = 2023-10-01 .. 2024-03-31      W2 = 2024-05-01 .. 2024-10-31
    warmup 60 days (measured: 30 silently changes the book — W2 n=51 -> 50)

FIDELITY (the owner's explicit choice over speed)
    all four EXEC_FRAMES, warmup 60 days, ~6 min per window for 8 coins on
    this 2-CPU sandbox. Do NOT "optimise" by dropping frames: measured,
    ("5min",) alone turns W1 +3.43R into -6.70R.

USAGE
    python3 lab_v32_superbrain_6m.py arms                  # list combos
    python3 lab_v32_superbrain_6m.py run COMBO [COMBO ...] # both windows
    python3 lab_v32_superbrain_6m.py run COMBO --window W1
    python3 lab_v32_superbrain_6m.py statement COMBO [W1]  # month/week book

Every run writes results/trades_v32_<combo>_<win>.csv,
results/lab_v32_<combo>_<win>.json and appends a row to the sweep CSV
(V32_SWEEP env var keeps parallel batches in separate files).
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

BASKET = str(HERE / "data" / "binance_5m")
WINDOWS = {"W1": ("2023-10-01", "2024-03-31"),
           "W2": ("2024-05-01", "2024-10-31")}
SWEEP_CSV = Path(os.environ.get("V32_SWEEP",
                                str(RESULTS / "lab_v32_sweep.csv")))

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
)

# 3 slots is the working basket default for the pillar arms: measured on the
# 2-coin probe, slotting halves maxDD but scales the return down with it, so
# each pillar is judged against the SAME slot law, not against all-in sizing.
S3 = dict(ALLOC_MODE="slot", SLOTS=3, SLOT_FILL="fixed")

COMBOS = {
    # ---- table 1 row 1: the v31 champion alone, same data, same windows --
    "BTC_C124":   dict(SYMBOL_WHITELIST=("BTCUSDT",)),
    # ---- PILLAR 1: rotation + slot law ----------------------------------
    "P1_all8":    dict(),                                   # v31 law, 8 coins
    "P1_slot1":   dict(ALLOC_MODE="slot", SLOTS=1),         # full-slot compound
    "P1_slot2":   dict(ALLOC_MODE="slot", SLOTS=2),
    "P1_slot3":   dict(S3),
    "P1_slot3d":  dict(S3, SLOT_FILL="dynamic"),
    "P1_slot4":   dict(ALLOC_MODE="slot", SLOTS=4),
    "P1_harvest": dict(S3, HARVEST_PCT=0.5),   # split-harvest cash recycling
    # ---- PILLAR 2: SMT divergence ---------------------------------------
    "P2_prefer":  dict(S3, SMT_BRAIN=True, SMT_GATE="prefer"),
    "P2_require": dict(S3, SMT_BRAIN=True, SMT_GATE="require"),
    "P2_gate1":   dict(ALLOC_MODE="slot", SLOTS=1, SMT_BRAIN=True,
                       SMT_GATE="require"),
    # ---- PILLAR 3: regime weapons ---------------------------------------
    "P3_B":       dict(S3, REGIME_MODE="B"),
    "P3_AB":      dict(S3, REGIME_MODE="AB"),
    "P3_B_hl":    dict(S3, REGIME_MODE="B", REGIME_B_NEEDS_BSL=False),
    # ---- PILLAR 4: time + protection ------------------------------------
    "P4_kz":      dict(S3, KILLZONE_MODE="exclude", KILLZONE_DOW=(6,)),
    "P4_cbs":     dict(S3, CLOSE_BASED_SHIELD=True),
    "P4_kz_cbs":  dict(S3, KILLZONE_MODE="exclude", KILLZONE_DOW=(6,),
                       CLOSE_BASED_SHIELD=True),
    # ---- combined candidates --------------------------------------------
    "FULL_3s":    dict(S3, SMT_BRAIN=True, SMT_GATE="prefer",
                       KILLZONE_MODE="exclude", KILLZONE_DOW=(6,)),
    "FULL_3s_B":  dict(S3, SMT_BRAIN=True, SMT_GATE="prefer",
                       KILLZONE_MODE="exclude", KILLZONE_DOW=(6,),
                       REGIME_MODE="B"),
    "FULL_1s":    dict(ALLOC_MODE="slot", SLOTS=1, SMT_BRAIN=True,
                       SMT_GATE="require", KILLZONE_MODE="exclude",
                       KILLZONE_DOW=(6,)),
}

WATCH = ("v32_smt_veto", "v32_regime_b_veto", "v32_regime_b_no_anchor",
         "v32_killzone_skip", "v32_emergency_stop", "v31_impulse_anchored",
         "fill_below_exchange_min", "shield_armed_disp")


def drive(combo: str, win: str, save: bool = True):
    import strategy_v32_ict_superbrain as S
    if combo not in COMBOS:
        raise SystemExit(f"unknown combo {combo!r} (would silently run BASE)")
    cfg = dict(BASE)
    cfg.update(COMBOS[combo])
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
    run = S.run_backtest(S.v32_data_dir(), start, end, tag=f"v32{combo}{win}")
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
    print(f"    n={res['n']} totR={res.get('totR')} "
          f"end=${res.get('end_equity')} DD={res.get('maxDD_pct')}% "
          f"({secs:.0f}s)", flush=True)
    print("    coins: " + json.dumps(res.get("by_coin", {})), flush=True)
    print("    counters: " + json.dumps(
        {k: v for k, v in res["counters"].items() if v}), flush=True)
    if save:
        if len(tr):
            tr.to_csv(RESULTS / f"trades_v32_{combo}_{win}.csv", index=False)
        (RESULTS / f"lab_v32_{combo}_{win}.json").write_text(
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
    f = RESULTS / f"trades_v32_{combo}_{win}.csv"
    j = RESULTS / f"lab_v32_{combo}_{win}.json"
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
    dest = RESULTS / f"statement_v32_{combo}_{win}.json"
    dest.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["monthly"], indent=1, default=str))
    print(f"\n{len(out['weekly'])} weekly buckets -> {dest.name}")
    print("weekly end balances: " + " ".join(
        f"{r['end_balance$']:.2f}" for r in out["weekly"]))
    return out


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
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        wins = ["W1", "W2"]
        if "--window" in sys.argv:
            wins = [sys.argv[sys.argv.index("--window") + 1]]
        for combo in args or list(COMBOS):
            for w in wins:
                drive(combo, w)
        return 0
    if cmd == "statement":
        combo = sys.argv[2]
        win = sys.argv[3] if len(sys.argv) > 3 else "W1"
        statement(combo, win)
        return 0
    raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    sys.exit(main())
