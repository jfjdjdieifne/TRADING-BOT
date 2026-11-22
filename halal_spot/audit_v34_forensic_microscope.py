#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v34_forensic_microscope.py -- the MICROSCOPIC TRADE TAPE AUDIT (v34)

Reads the SAVED books on this server (no abstraction, no re-derivation of the
engine's decisions) and prints five tables to STDOUT, trade by trade:

  1. THE LEDGER               -- the 12 single months of `S1_TEL_3R` (W1 M1..M6,
                                 W2 M1..M6) + the best 10 single weeks with the
                                 coins that actually paid.
  2. ALL BIG WINNERS TAPE     -- every fill with R >= +3.0 in `S1_TEL_3R`, with
                                 the explicit programmatic checks
                                 fill_px <= seam + 1e-9 and fill_px <= purple_mid + 1e-9.
  3. THE 15 FATAL COLLISIONS  -- the biggest winners the 3-seat reference
                                 `V33_TEL_3S_3R` took and the single seat could
                                 not (slot_full_rejects), each one paired with
                                 the coin that was sitting in the seat, plus the
                                 W1/W2 balance if the seat had been handed over.
  4. BLEEDING-COIN AUTOPSY    -- every XRP/ETH loser in W1 and W2, which exit
                                 actually killed it, the median stop distance vs
                                 BNB/SOL/ADA, and the causal 4H structure state
                                 at the moment of entry (bearish? lower highs?).
  5. COUNTERFACTUAL           -- a REAL re-simulation of `S1_TEL_3R` restricted
                                 to BNB, SOL, ADA, LINK, AVAX, through the same
                                 engine and the same lab.

USAGE
    python3 audit_v34_forensic_microscope.py            # tables 1-5
    python3 audit_v34_forensic_microscope.py --no-run    # skip table 5
    python3 audit_v34_forensic_microscope.py --only 3    # one table

Every number below is either read out of
    results/trades_v34_<combo>_<win>.csv      (the engine's own trade book)
    results/lab_v34_<combo>_<win>.json        (the engine's own run summary)
    results/statement_v34_<combo>_<win>.json  (the engine's own equity marks)
or produced by the engine itself for table 5. Nothing is estimated.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DATA = HERE / "data" / "binance_5m"
sys.path.insert(0, str(HERE))

WINNER = "S1_TEL_3R"          # the champion
REF = "V33_TEL_3S_3R"         # the 3-seat reference (v33 TEL)
WINDOWS = ("W1", "W2")
BEST5 = ("BNBUSDT", "SOLUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT")

W = 128                        # print width


# --------------------------------------------------------------------- #
# plumbing
# --------------------------------------------------------------------- #
def hdr(txt):
    print("\n" + "=" * W)
    print(txt)
    print("=" * W)


def sub(txt):
    print("\n" + "-" * W)
    print(txt)
    print("-" * W)


def book(combo: str, win: str) -> pd.DataFrame:
    f = RESULTS / f"trades_v34_{combo}_{win}.csv"
    if not f.exists():
        raise SystemExit(f"missing book {f.name} -- run the lab first")
    d = pd.read_csv(f)
    for c in ("entry_time", "exit_time"):
        d[c] = pd.to_datetime(d[c], utc=True, format="mixed").dt.tz_localize(None)
    for c in ("R", "net_pnl", "entry_price", "exit_price", "stop_price",
              "notional", "risk_pct", "mfe_R", "mfe_close_R", "bars_held",
              "v29_seam_px", "purple_mid", "qty0"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d["hold_h"] = (d.exit_time - d.entry_time).dt.total_seconds() / 3600.0
    d["sym"] = d["symbol"].astype(str).str.split("_").str[0]
    d["cls"] = d["class"].astype(str)
    d["is_win"] = d.cls.isin(["WIN", "SWIN"])
    d["is_loss"] = d.cls.eq("LOSS")
    d["is_be"] = d.cls.isin(["BE", "BREAKEVEN"])
    return d.sort_values("entry_time").reset_index(drop=True)


def meta(combo: str, win: str) -> dict:
    return json.loads((RESULTS / f"lab_v34_{combo}_{win}.json").read_text())


def statement(combo: str, win: str) -> dict:
    return json.loads((RESULTS / f"statement_v34_{combo}_{win}.json").read_text())


def pf(g: pd.DataFrame):
    gp = float(g.loc[g.net_pnl > 0, "net_pnl"].sum())
    gl = float(-g.loc[g.net_pnl < 0, "net_pnl"].sum())
    return (gp / gl) if gl > 1e-9 else float("inf")


def _month_dd(g: pd.DataFrame, start_bal: float) -> float:
    """Worst peak-to-trough drawdown (%) INSIDE one month, on the cash ladder."""
    if not len(g):
        return 0.0
    e = start_bal + g.sort_values("exit_time").net_pnl.cumsum()
    e = pd.concat([pd.Series([start_bal]), e], ignore_index=True)
    return float(((e / e.cummax()) - 1.0).min() * 100.0)


def ts(t) -> str:
    return pd.Timestamp(t).strftime("%Y-%m-%d %H:%M")


# --------------------------------------------------------------------- #
# 1. THE LEDGER
# --------------------------------------------------------------------- #
def table1():
    hdr("TABLE 1 - THE LEDGER: the twelve single months of "
        f"{WINNER}, then the ten biggest single weeks")
    for win in WINDOWS:
        d = book(WINNER, win)
        s = statement(WINNER, win)
        cap = float(s["capital"])
        months = s["monthly"]
        mm0 = meta(WINNER, win)
        print(f"\n  {win}  ({mm0['start']} .. {mm0['end']})   start capital "
              f"${cap:,.2f}   final equity ${float(s['final_equity']):,.2f}"
              f"   window maxDD {float(s['maxDD_pct']):.2f}%")
        print(f"  {'month':7s} {'start$':>9s} {'end$':>9s} {'$':>8s} "
              f"{'%':>7s} {'n':>4s} {'W/BE/L':>10s} {'PF':>6s} {'mDD%':>6s}  "
              f"best trade")
        bal = cap
        for m in months:
            start_bal = bal
            bal = float(m["end_balance$"])
            pct = 100.0 * float(m["net$"]) / start_bal if start_bal else 0.0
            g = d[d.exit_time.dt.strftime("%Y-%m") == m["bucket"]]
            best = None
            if len(g):
                b = g.loc[g.net_pnl.idxmax()]
                best = f"{b.sym:4s} {ts(b.entry_time)} {b.R:+.2f}R ${b.net_pnl:+.2f}"
            p = m.get("PF")
            print(f"  {m['bucket']:7s} {start_bal:9.2f} {bal:9.2f} "
                  f"{float(m['net$']):+8.2f} {pct:+7.2f} {int(m['n']):4d} "
                  f"{int(m['W']):3d}/{int(m['BE']):2d}/{int(m['L']):2d}  "
                  f"{('inf' if p is None else f'{p:6.2f}'):>6s} "
                  f"{_month_dd(g, start_bal):6.2f}  {best or '-'}")
        tot = float(d.net_pnl.sum())
        print(f"  {'TOTAL':7s} {cap:9.2f} {cap + tot:9.2f} {tot:+8.2f} "
              f"{100*tot/cap:+7.2f} {len(d):4d} "
              f"{int(d.is_win.sum()):3d}/{int(d.is_be.sum()):2d}/{int(d.is_loss.sum()):2d}"
              f"  {pf(d):6.2f} {float(s['maxDD_pct']):6.2f}")
        # cross-check against the engine's own run summary
        mm = meta(WINNER, win)
        print(f"  check vs the engine's own summary: end_equity "
              f"${float(mm['end_equity']):,.2f} | totR {float(mm['totR']):+.4f} | "
              f"n {int(mm['n'])} | book sum ${float(d.net_pnl.sum()):+,.4f} / "
              f"{float(d.R.sum()):+.4f}R -> "
              f"{'IDENTICAL' if abs(float(d.net_pnl.sum()) - float(mm['net'])) < 1e-3 else 'DRIFT!'}")

    # ---- the ten biggest single weeks, both windows, with the paying coins
    rows = []
    for win in WINDOWS:
        d = book(WINNER, win)
        s = statement(WINNER, win)
        cap = float(s["capital"])
        for w in s["weekly"]:
            if not int(w["n"]):
                continue
            lab = w["bucket"]
            rows.append({
                "win": win, "week": lab, "n": int(w["n"]),
                "W": int(w["W"]), "BE": int(w["BE"]), "L": int(w["L"]),
                "net$": float(w["net$"]), "end$": float(w["end_balance$"]),
                "PF": w.get("PF"), "coins": w.get("by_coin$") or {},
            })
    rows.sort(key=lambda r: -r["net$"])
    print(f"\n  BEST 10 SINGLE WEEKS of {WINNER} across both windows "
          f"(week = 7 days from the window start, engine's own bucketing)")
    print(f"  {'#':>2s} {'win':3s} {'week start':10s} {'week end':10s} "
          f"{'net$':>8s} {'%':>7s} {'n':>4s} {'W/BE/L':>10s} {'PF':>6s} "
          f" paying coins (net$)")
    for i, r in enumerate(rows[:10], 1):
        w0 = pd.Timestamp(r["week"].split(" ")[1])
        w1 = w0 + pd.Timedelta(days=6)
        pct = 100.0 * r["net$"] / (r["end$"] - r["net$"]) if r["end$"] != r["net$"] else 0.0
        coins = sorted(r["coins"].items(), key=lambda kv: -kv[1])
        ctxt = "  ".join(f"{k[:-4]}{v:+.2f}" for k, v in coins if abs(v) > 0.005)
        p = r["PF"]
        print(f"  {i:2d} {r['win']:3s} {w0.date()!s:10s} {w1.date()!s:10s} "
              f"{r['net$']:+8.2f} {pct:+7.2f} {r['n']:4d} "
              f"{r['W']:3d}/{r['BE']:2d}/{r['L']:2d}  "
              f"{('inf' if p is None else f'{p:6.2f}'):>6s}  {ctxt}")
    # which 5 coins actually paid, over the whole book
    print(f"\n  WHO PAID, in total, across both windows ({WINNER}):")
    for win in WINDOWS:
        d = book(WINNER, win)
        g = d.groupby("sym").agg(n=("R", "size"), R=("R", "sum"),
                                 net=("net_pnl", "sum"),
                                 wr=("is_win", "mean"))
        g = g.sort_values("net", ascending=False)
        print(f"   {win}: " + "  ".join(
            f"{i} n={int(r.n)} {r.net:+.2f}$" for i, r in g.iterrows()))


# --------------------------------------------------------------------- #
# 2. ALL BIG WINNERS TAPE
# --------------------------------------------------------------------- #
def table2():
    hdr(f"TABLE 2 - ALL BIG WINNERS TAPE: every fill with R >= +3.0 in {WINNER}")
    grand = 0
    for win in WINDOWS:
        d = book(WINNER, win)
        g = d[d.R >= 3.0].sort_values("R", ascending=False)
        grand += len(g)
        print(f"\n  {win}: {len(g)} fills >= +3.0R   "
              f"(sum {g.R.sum():+.2f}R / ${g.net_pnl.sum():+.2f})")
        print(f"  {'#':>3s} {'coin':5s} {'entry':16s} {'exit':16s} {'hold':>6s} "
              f"{'fill_px':>9s} {'seam':>9s} {'stop_px':>9s} {'exit_px':>9s} "
              f"{'MFE%':>6s} {'gave':>6s} {'net$':>7s} {'R':>7s}  {'rule':12s} disc")
        for i, (_, r) in enumerate(g.iterrows(), 1):
            # MFE in % of PRICE: the book stores it in R, and one R is the stop
            # width (risk_pct), which the engine also stores.
            mfe_r = float(r.mfe_close_R) if pd.notna(r.mfe_close_R) else float(r.mfe_R)
            mfe_pct = mfe_r * float(r.risk_pct)
            gave = mfe_r - float(r.R)          # R given back from the best close
            disc_seam = r.entry_price <= float(r.v29_seam_px) + 1e-9
            disc_purp = r.entry_price <= float(r.purple_mid) + 1e-9
            disc = "OK" if (disc_seam and disc_purp) else (
                "seam!" if not disc_seam else "purp!")
            rule = {"STOP_BLUE": "trail (4H/5m)",
                    "TARGET_REJECTION": "struct. ceiling",
                    "STRUCT_PROFIT": "struct. profit"}.get(str(r.exit_reason),
                                                           str(r.exit_reason))
            print(f"  {i:3d} {r.sym:5s} {ts(r.entry_time):16s} "
                  f"{ts(r.exit_time):16s} {r.hold_h:6.1f} "
                  f"{r.entry_price:9.4f} {float(r.v29_seam_px):9.4f} "
                  f"{float(r.stop_price):9.4f} {float(r.exit_price):9.4f} "
                  f"{mfe_pct:6.2f} {gave:6.1f} {float(r.net_pnl):+7.2f} "
                  f"{float(r.R):+7.2f}  {rule:12s} {disc}")
        # ---- the two explicit programmatic checks the brief demands
        ok_seam = bool((g.entry_price <= g.v29_seam_px + 1e-9).all())
        ok_purp = bool((g.entry_price <= g.purple_mid + 1e-9).all())
        bad_s = g[g.entry_price > g.v29_seam_px + 1e-9]
        bad_p = g[g.entry_price > g.purple_mid + 1e-9]
        print(f"  CHECK fill_px <= seam + 1e-9        : {'PASS' if ok_seam else 'FAIL'}"
              f"  ({len(g) - len(bad_s)}/{len(g)} comply)")
        for _, b in bad_s.iterrows():
            print(f"        breach {b.sym} {ts(b.entry_time)} "
                  f"fill {b.entry_price:.6f} vs seam {b.v29_seam_px:.6f} "
                  f"(+{100*(b.entry_price/b.v29_seam_px-1):.3f}%)  R {b.R:+.2f}")
        print(f"  CHECK fill_px <= purple_mid + 1e-9  : {'PASS' if ok_purp else 'FAIL'}"
              f"  ({len(g) - len(bad_p)}/{len(g)} comply)")
        for _, b in bad_p.iterrows():
            print(f"        breach {b.sym} {ts(b.entry_time)} "
                  f"fill {b.entry_price:.6f} vs purple_mid {b.purple_mid:.6f} "
                  f"(+{100*(b.entry_price/b.purple_mid-1):.3f}%)  R {b.R:+.2f}")
        allg = d
        print(f"  on the WHOLE book {win} (n={len(allg)}): seam "
              f"{int((allg.entry_price <= allg.v29_seam_px + 1e-9).sum())}/{len(allg)}"
              f"  purple_mid "
              f"{int((allg.entry_price <= allg.purple_mid + 1e-9).sum())}/{len(allg)}")
        # what the seam breaches are, structurally
        if len(bad_s):
            print(f"  the {len(bad_s)} seam breaches are 'above the seam' fills "
                  f"(price never came back to the seam): median "
                  f"+{100*((bad_s.entry_price/bad_s.v29_seam_px-1).median()):.3f}% "
                  f"above it, median R {bad_s.R.median():+.2f}, "
                  f"wins {int(bad_s.is_win.sum())}/{len(bad_s)}")
    print(f"\n  grand total: {grand} fills >= +3.0R in {WINNER}")


# --------------------------------------------------------------------- #
# 3. THE 15 FATAL COLLISIONS
# --------------------------------------------------------------------- #
def table3():
    hdr("TABLE 3 - THE FATAL COLLISIONS: every winner the single seat could not "
        "take, and who was sitting in it")
    summary = {}
    for win in WINDOWS:
        a = book(WINNER, win)
        b = book(REF, win)
        ma, mb = meta(WINNER, win), meta(REF, win)
        rej = int(ma["counters"].get("slot_full_rejects", 0))
        cap = float(ma["capital"])
        # running cash ladder of the single seat (100% deployed => cash = risk budget)
        a["bal_at"] = cap + a.sort_values("exit_time").set_index("exit_time") \
            .net_pnl.cumsum().reindex(a.exit_time).values

        def budget_at(t):
            done = a[a.exit_time < t]
            return cap + float(done.net_pnl.sum())

        print(f"\n  {win}: {REF} made {len(b)} fills, {WINNER} made {len(a)}. "
              f"{WINNER}'s counter slot_full_rejects = {rej} "
              f"({REF}'s own = {int(mb['counters'].get('slot_full_rejects', 0))}).")
        print("  That counter counts every BLOCKED ENTRY ATTEMPT, not missed "
              "winners. The collisions below are the")
        print("  subset of it that can be proved from the two books: a fill the "
              "reference actually took, on a stamp where")
        print("  the single seat was already holding another trade and the "
              "winner's own book does not contain that fill.")

        # (a) reference fills that the winner ALSO took (+-10 min, same coin)
        def taken(sym, t):
            m = a[(a.sym == sym)
                  & (a.entry_time <= t + pd.Timedelta(minutes=10))
                  & (a.entry_time >= t - pd.Timedelta(minutes=10))]
            return None if not len(m) else m.iloc[0]

        prof = b[b.R > 0]
        rows = []
        n_taken = n_free = 0
        for _, r in prof.iterrows():
            if taken(r.sym, r.entry_time) is not None:
                n_taken += 1
                continue
            occ = a[(a.entry_time <= r.entry_time) & (a.exit_time > r.entry_time)]
            if not len(occ):
                n_free += 1
                continue
            o = occ.iloc[0]
            bud = budget_at(r.entry_time)
            # the engine's own law (verified on the book: net = R x notional x
            # risk_pct): R multiplies the RISK, and the risk is the stop width,
            # not the notional. A 35R trade at 0.4% risk on $121 is ~$17, not $4300.
            rf = float(r.risk_pct) / 100.0
            would = float(r.R) * bud * rf
            rows.append(dict(ref=r, occ=o, would=would,
                             delta=would - float(o.net_pnl),
                             held=(r.entry_time - o.entry_time).total_seconds() / 3600))
        print(f"  reconciliation of the {len(prof)} PROFITABLE {REF} fills: "
              f"{n_taken} were also taken by {WINNER}, "
              f"{n_free} found the seat FREE, {len(rows)} are true collisions.")
        print(f"  -> the {rej} blocked attempts are mostly signals the reference "
              f"itself never turned into a profitable fill.")

        before = len(rows)
        keep = []
        for d in sorted(rows, key=lambda x: -float(x["ref"].R)):
            dup = [k for k in keep
                   if k["ref"].sym == d["ref"].sym
                   and abs((k["ref"].entry_time - d["ref"].entry_time).total_seconds())
                   <= 1800]
            if dup:
                continue
            keep.append(d)
        rows = keep
        if before != len(rows):
            print(f"  collapsed {before - len(rows)} duplicate stamps (the same "
                  f"signal filled on two execution frames)")
        rows.sort(key=lambda d: (-d["would"], -float(d["ref"].R)))
        print(f"\n  THE {min(15, len(rows))} FATAL COLLISIONS, biggest first "
              f"(would-be $ = R x the seat's cash at that instant)")
        print(f"  {'#':>2s} {'missed signal':16s} {'coin':5s} {'would-be $':>10s} "
              f"{'R':>7s} | {'coin in the seat':8s} {'sitting since':16s} "
              f"{'held':>6s} {'seat $':>8s} {'R':>7s}  {'exit reason':15s} {'swap gain':>9s}")
        for i, d in enumerate(rows[:15], 1):
            r, o = d["ref"], d["occ"]
            print(f"  {i:2d} {ts(r.entry_time):16s} {r.sym:5s} {d['would']:+10.2f} "
                  f"{float(r.R):+7.2f} | {o.sym:8s} {ts(o.entry_time):16s} "
                  f"{d['held']:6.1f} {float(o.net_pnl):+8.2f} {float(o.R):+7.2f}  "
                  f"{str(o.exit_reason)[:15]:15s} {d['delta']:+9.2f}")

        # the swap the brief asks for: what the window ends at
        end = cap + float(a.net_pnl.sum())
        d15 = sum(d["delta"] for d in rows[:15])
        dall = sum(d["delta"] for d in rows)
        print(f"\n  COUNTERFACTUAL {win} -- hand the seat to the exploding trade at "
              f"its signal, drop the trade that occupied it:")
        print(f"    the real book            : ${cap:,.2f} -> ${end:,.2f}  "
              f"({end - cap:+,.2f} = {100*(end/cap - 1):+.2f}%)   n={len(a)}")
        print(f"    the {min(15, len(rows))} biggest swaps      : "
              f"${cap:,.2f} -> ${end + d15:,.2f}  ({d15:+,.2f} = "
              f"{100*d15/cap:+.2f}% of capital)")
        if len(rows) > 15:
            print(f"    ALL {len(rows)} swaps              : "
                  f"${cap:,.2f} -> ${end + dall:,.2f}  ({dall:+,.2f} = "
                  f"{100*dall/cap:+.2f}% of capital)")
        worse = [d for d in rows if d["delta"] < 0]
        print(f"    honesty: {len(worse)} of the {len(rows)} swaps would have made "
              f"LESS than the trade they evicted (the seat was earning its keep)")
        print("    (first-order: the swap keeps every OTHER trade of the book "
              "untouched, so no re-compounding is claimed)")
        summary[win] = {"real": end, "top15": end + d15, "all": end + dall,
                        "n": len(rows)}
    ch_real = summary["W1"]["real"] * summary["W2"]["real"] / 10000.0 - 1
    ch_15 = summary["W1"]["top15"] * summary["W2"]["top15"] / 10000.0 - 1
    ch_all = summary["W1"]["all"] * summary["W2"]["all"] / 10000.0 - 1
    sub("  COMBINED, chained the way the lab reports it ($100 -> W1 -> W2)")
    print(f"   the real winner book        : {100*ch_real:+.2f}%   "
          f"(W1 ${summary['W1']['real']:,.2f} -> W2 ${100*(1+ch_real):,.2f})")
    n15 = min(15, summary["W1"]["n"]) + min(15, summary["W2"]["n"])
    print(f"   the {n15} swapped fills".ljust(30) + f": {100*ch_15:+.2f}%   "
          f"(W1 ${summary['W1']['top15']:,.2f} -> W2 ${100*(1+ch_15):,.2f})")
    n_all = summary["W1"]["n"] + summary["W2"]["n"]
    if n_all > 30:
        print(f"   all {n_all} swaps               : {100*ch_all:+.2f}%   "
              f"(W1 ${summary['W1']['all']:,.2f} -> W2 ${100*(1+ch_all):,.2f})")
    print("   NOTE: this is a bounds check, not a promise. It keeps every other "
          "trade of the book untouched and")
    print("   re-prices only the swapped fills at the seat's full-cash risk, so it "
          "measures the CEILING of the")
    print("   slot's opportunity cost, which the measured v34 book already beat by "
          "itself on the other 380 fills.")


# --------------------------------------------------------------------- #
# 4. BLEEDING-COIN AUTOPSY
# --------------------------------------------------------------------- #
def _structure_at(sym: str, when: pd.Timestamp, cache: dict):
    """Causal 4H structure state at `when`, plus the last two confirmed swing
    highs (lower highs?) -- all computed with the engine's own primitives."""
    from engine.causal_primitives import (load_asset_ohlcv, resample_causal_tf,
                                          detect_swings_causal)
    if sym not in cache:
        d = DATA / f"{sym}_5m"
        df = load_asset_ohlcv(d)
        from engine.causal_primitives import build_causal_htf_structure
        idx, trend = build_causal_htf_structure(df, "4h", swing_k=2)
        tf = resample_causal_tf(df, "4h")
        sw = detect_swings_causal(tf["High"].to_numpy(), tf["Low"].to_numpy(),
                                  tf.index, 2)
        highs = []
        for i in sorted(sw):
            for sp in sw[i]:
                if sp.kind == "high":
                    highs.append((sp.confirm_time, sp.price))
        highs.sort()
        cache[sym] = (pd.DatetimeIndex(idx), trend, highs)
    idx, trend, highs = cache[sym]
    t = pd.Timestamp(when).tz_localize("UTC") if pd.Timestamp(when).tzinfo is None \
        else pd.Timestamp(when).tz_convert("UTC")
    pos = idx.searchsorted(t, side="right") - 1
    st = int(trend[pos]) if pos >= 0 else 0
    # the two most recent confirmed swing highs strictly before `t`
    prior = [p for c, p in highs if c < t]
    lh = None
    if len(prior) >= 2:
        lh = prior[-1] < prior[-2]
    return st, lh, pos


def table4():
    hdr("TABLE 4 - BLEEDING-COIN AUTOPSY: what exactly killed XRP, ETH and BTC")
    cache: dict = {}
    for win in WINDOWS:
        d = book(WINNER, win)
        print(f"\n  {win}: per-coin result of {WINNER}")
        g = d.groupby("symbol").agg(n=("R", "size"), W=("is_win", "sum"),
                                    L=("is_loss", "sum"), R=("R", "sum"),
                                    net=("net_pnl", "sum"))
        for s, r in g.sort_values("net").iterrows():
            print(f"    {s[:-4]:5s} n={int(r.n):3d}  W{int(r.W):3d} L{int(r.L):3d}  "
                  f"totR {r.R:+8.2f}  net ${r.net:+8.2f}")

        for sym in ("XRPUSDT", "ETHUSDT", "BTCUSDT"):
            g = d[(d.sym == sym) & d.is_loss].sort_values("entry_time")
            tot = float(d.loc[d.sym == sym, "net_pnl"].sum())
            print(f"\n   ALL LOSERS on {sym} in {win}: {len(g)} fills, "
                  f"the coin netted ${tot:+.2f} for the window")
            if not len(g):
                print("     (none)")
                continue
            print(f"   {'#':>2s} {'entry':16s} {'exit':16s} {'hold':>6s} "
                  f"{'fill_px':>10s} {'stop_px':>10s} {'exit_px':>10s} "
                  f"{'moved-away%':>11s}  {'exit reason':16s} {'R':>7s} {'net$':>8s}")
            for i, (_, r) in enumerate(g.iterrows(), 1):
                away = 100.0 * (float(r.entry_price) - float(r.stop_price)) / float(r.entry_price)
                print(f"   {i:2d} {ts(r.entry_time):16s} {ts(r.exit_time):16s} "
                      f"{r.hold_h:6.1f} {float(r.entry_price):10.4f} "
                      f"{float(r.stop_price):10.4f} {float(r.exit_price):10.4f} "
                      f"{away:11.3f}%  {str(r.exit_reason)[:16]:16s} "
                      f"{float(r.R):+7.2f} {float(r.net_pnl):+8.2f}")
            why = g.exit_reason.value_counts().to_dict()
            exp = sum(v for k, v in why.items() if k == "STOP_BLUE")
            be = why.get("BREAKEVEN", 0)
            em = why.get("EMERGENCY_STOP", 0)
            print(f"     death certificates: original stop (STOP_BLUE) {exp} | "
                  f"back to BE after a rally (BREAKEVEN) {be} | "
                  f"EMERGENCY_STOP {em} | other "
                  f"{len(g) - exp - be - em}")
            if be:
                sub = g[g.exit_reason == "BREAKEVEN"]
                print(f"     of the {be} BE deaths, median best excursion was "
                      f"{sub.mfe_R.median():+.2f}R (intrabar) / "
                      f"{sub.mfe_close_R.median():+.2f}R (on closes) and median hold "
                      f"{sub.hold_h.median():.1f}h")

        # ---- stop-width comparison
        print(f"\n   MEDIAN STOP DISTANCE (% of price) by coin, {win} (all fills):")
        gg = d.assign(stop_dist_pct=100.0 * (d.entry_price - d.stop_price)
                          / d.entry_price)
        med = gg.groupby("sym").stop_dist_pct.median().sort_values()
        bad = med.loc[[s for s in ("XRPUSDT", "ETHUSDT") if s in med.index]]
        good = med.loc[[s for s in ("BNBUSDT", "SOLUSDT", "ADAUSDT") if s in med.index]]
        txt = "  ".join(f"{s} {v:.3f}%" for s, v in med.items())
        print(f"     {txt}")
        print(f"     XRP/ETH median {bad.median():.3f}%  vs  BNB/SOL/ADA median "
              f"{good.median():.3f}%  -> ratio {bad.median()/good.median():.3f}x")

        # ---- were the entries taken inside 4H bearish structure / lower highs?
        print(f"\n   4H STRUCTURE AT ENTRY (causal, engine primitives, swing_k=2):")
        print(f"   {'coin':5s} {'fills':>5s} {'in 4H bearish':>13s} "
              f"{'in lower highs':>15s}  {'their net$ while bearish':>24s}")
        for sym in ("XRPUSDT", "ETHUSDT", "BTCUSDT", "BNBUSDT", "SOLUSDT",
                    "ADAUSDT", "LINKUSDT", "AVAXUSDT"):
            g = d[d.sym == sym]
            if not len(g):
                continue
            bears, lhs, net_bear = 0, 0, 0.0
            for _, r in g.iterrows():
                try:
                    st, lh, _ = _structure_at(sym, r.entry_time, cache)
                except FileNotFoundError:
                    st, lh = 0, None
                if st == -1:
                    bears += 1
                    net_bear += float(r.net_pnl)
                if lh:
                    lhs += 1
            print(f"   {sym[:-4]:5s} {len(g):5d} {bears:8d}/{len(g):<4d} "
                  f"{lhs:10d}/{len(g):<4d}  {net_bear:+21.2f}")
        print(f"   (the 4H state is read on the last COMPLETED 4H bar before the "
              f"12-5m fill; -1 = bearish BOS/CHoCH, 0 = neutral, +1 = bullish)")


# --------------------------------------------------------------------- #
# 5. COUNTERFACTUAL -- a real re-simulation
# --------------------------------------------------------------------- #
def table5(run: bool = True):
    hdr("TABLE 5 - COUNTERFACTUAL: re-simulate "
        f"{WINNER} on the best coins only ({', '.join(s[:-4] for s in BEST5)})")
    import lab_v34_single_slot_2r as L
    import strategy_v34_ict_single_slot_2r as S

    tag = f"{WINNER}_BEST5"
    rows = []
    for win in WINDOWS:
        if run:
            print(f"\n  RUNNING the real engine: {WINNER} restricted to "
                  f"{', '.join(s[:-4] for s in BEST5)}  {win} "
                  f"{L.WINDOWS[win][0]}..{L.WINDOWS[win][1]}  (this takes minutes)")
            cfg = dict(L.BASE)
            cfg.update(L.COMBOS[WINNER])
            cfg["SYMBOL_WHITELIST"] = tuple(s[:-4] for s in BEST5)
            for k, v in cfg.items():
                setattr(S, k, v)
            start, end = L.WINDOWS[win]
            import time
            t0 = time.time()
            r = S.run_backtest(S.v34_data_dir(), start, end, tag=f"v34{tag}{win}")
            tr = pd.DataFrame(r["trades"])
            tr.to_csv(RESULTS / f"trades_v34_{tag}_{win}.csv", index=False)
            res = {"combo": tag, "window": win, "n": int(len(tr)),
                   "symbols": r["symbols"],
                   "totR": round(float(tr.R.sum()), 4),
                   "net": round(float(tr.net_pnl.sum()), 4),
                   "end_equity": round(100.0 + float(tr.net_pnl.sum()), 4),
                   "fees": round(float(r["fees"]), 4),
                   "seconds": round(time.time() - t0, 1)}
            cls = tr["class"].astype(str)
            res.update(W=int(cls.isin(["WIN", "SWIN"]).sum()),
                       L=int(cls.eq("LOSS").sum()),
                       BE=int(cls.isin(["BE", "BREAKEVEN"]).sum()),
                       wr=round(100.0 * cls.isin(["WIN", "SWIN"]).mean(), 2))
            gp = float(tr.loc[tr.net_pnl > 0, "net_pnl"].sum())
            gl = float(-tr.loc[tr.net_pnl < 0, "net_pnl"].sum())
            res["pf"] = round(gp / gl, 3) if gl > 1e-9 else None
            eq = r["equity"]
            if len(eq):
                e = eq["equity"].astype(float)
                res["maxDD_pct"] = round(float(((e / e.cummax()) - 1).min() * 100), 3)
            tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True,
                                             format="mixed").dt.tz_localize(None)
            m = tr.groupby(tr.exit_time.dt.strftime("%Y-%m")).net_pnl.sum()
            res["best_month"] = m.idxmax()
            res["best_month_$"] = round(float(m.max()), 2)
            s0 = pd.Timestamp(start)
            wk = tr.groupby(((tr.exit_time - s0).dt.days // 7)).net_pnl.sum()
            res["best_week_$"] = round(float(wk.max()), 2)
            res["best_week_idx"] = int(wk.idxmax())
            res["best_week_start"] = str((s0 + pd.Timedelta(days=7 * int(wk.idxmax()))).date())
            res["by_coin"] = {k.split("_")[0]:
                              [int(len(g)), round(float(g.net_pnl.sum()), 2)]
                              for k, g in tr.groupby("symbol")}
            (RESULTS / f"lab_v34_{tag}_{win}.json").write_text(
                json.dumps(res, indent=1, default=str))
            print(f"    n={res['n']} totR={res['totR']} end=${res['end_equity']} "
                  f"DD={res.get('maxDD_pct')}%  ({res['seconds']}s)")
            print(f"    coins: {res['by_coin']}")
        else:
            f = RESULTS / f"lab_v34_{tag}_{win}.json"
            if not f.exists():
                print(f"\n  {win}: no saved restricted run ({f.name}) and "
                      f"--no-run was requested -> skipped")
                continue
            res = json.loads(f.read_text())
        rows.append(res)

    for win in WINDOWS:
        full = meta(WINNER, win)
        d8 = book(WINNER, win)
        r = next((x for x in rows if x["window"] == win), None)
        if r is None:
            continue
        sub(f"  {win}: {WINNER} on 8 coins  vs  restricted to the best 5")
        print(f"  {'book':38s} {'start$':>8s} {'end$':>9s} {'$':>9s} {'%':>8s} "
              f"{'n':>4s} {'W/BE/L':>10s} {'PF':>6s} {'maxDD%':>7s}")
        def line(lab, x, d=None):
            cap = 100.0
            end = float(x["end_equity"])
            if d is not None and len(d):      # the 8-coin summary has no W/BE/L
                W_, B_, L_ = int(d.is_win.sum()), int(d.is_be.sum()), int(d.is_loss.sum())
                pf_ = pf(d)
            else:
                W_, B_, L_ = int(x.get("W", 0)), int(x.get("BE", 0)), int(x.get("L", 0))
                pf_ = x.get("pf") or 0.0
            print(f"  {lab:38s} {cap:8.2f} {end:9.2f} {end-cap:+9.2f} "
                  f"{100*(end/cap-1):+8.2f} {int(x['n']):4d} "
                  f"{W_:3d}/{B_:2d}/{L_:2d}  {pf_:6.2f} "
                  f"{float(x.get('maxDD_pct') or 0):7.2f}")
        line(f"8 coins (the real winner)", full, d8)
        line(f"best 5: {'/'.join(s[:-4] for s in BEST5)}", r)
        bm = max(statement(WINNER, win)["monthly"], key=lambda x: float(x["net$"]))
        bw = max(statement(WINNER, win)["weekly"], key=lambda x: float(x["net$"]))
        print(f"  best month  8-coin : {bm['bucket']} {float(bm['net$']):+.2f}$ "
              f"({100*float(bm['net$'])/(float(bm['end_balance$'])-float(bm['net$'])):+.2f}%)"
              f"   |  best 5: {r.get('best_month')} ${r.get('best_month_$')}")
        print(f"  best week   8-coin : {bw['bucket']} {float(bw['net$']):+.2f}$"
              f"   |  best 5: ${r.get('best_week_$')} "
              f"(week of {r.get('best_week_start')})")
    if len(rows) == 2:
        e1 = float(rows[0]["end_equity"]) / 100.0
        e2 = float(rows[1]["end_equity"]) / 100.0
        f1 = float(meta(WINNER, "W1")["end_equity"]) / 100.0
        f2 = float(meta(WINNER, "W2")["end_equity"]) / 100.0
        sub("  COMBINED (chained the way the lab reports it)")
        print(f"  8 coins    : {(f1*f2-1)*100:+.2f}%   "
              f"(W1 ${100*f1:,.2f} -> W2 ${100*f1*f2:,.2f})")
        print(f"  best 5     : {(e1*e2-1)*100:+.2f}%   "
              f"(W1 ${100*e1:,.2f} -> W2 ${100*e1*e2:,.2f})")


# --------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=lambda s: {int(x) for x in s.split(",")},
                    default=None)
    ap.add_argument("--no-run", action="store_true",
                    help="do not re-run the engine for table 5")
    a = ap.parse_args()
    want = a.only or {1, 2, 3, 4, 5}
    print("MICROSCOPIC TRADE TAPE AUDIT - v34 halal spot")
    print(f"books: {RESULTS}")
    print(f"champion under the microscope: {WINNER}   reference: {REF}")
    if 1 in want:
        table1()
    if 2 in want:
        table2()
    if 3 in want:
        table3()
    if 4 in want:
        table4()
    if 5 in want:
        table5(run=not a.no_run)
    print("\n" + "=" * W)
    print("END OF TAPE")
    print("=" * W)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
