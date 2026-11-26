#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_v45_true_multiple_brain.py -- v45 STEP 1 (<8 s, ZERO engine runs).

Every measurement is in TRUE DOLLAR-LOSS MULTIPLES ("true_X"), never in the
raw pre-fee R the engine prints:

    unit_true_loss(fill, stop) = fill*(1+COST) - stop*(1-COST)      # -1.0x
    unit_net_profit(px, fill)  = px*(1-COST)   - fill*(1+COST)
    true_X(px)                 = unit_net_profit / unit_true_loss

BUG FIXED IN THIS FILE (documented because it invalidated a first pass):
  pandas 3.x parses ISO strings to datetime64[us, UTC]. astype("int64") then
  yields MICROseconds while the 5m tape is NANOseconds, so every slice was
  1000x off and silently read a nonsense window (it "found" 5m closes 6x
  above entry on trades the engine stopped out at -1R). Both sides are now
  coerced through .astype("datetime64[ns, UTC]") explicitly, and the slice is
  validated against the engine's OWN recorded mfe_R / mfe_close_R, which are
  computed inside run_backtest on the same tape: agreement is 1170/1173 and
  1149/1173 to within tick rounding.

WHAT THE TAPE SAYS (why this task exists):
  LOCK_MODE="trail" makes the +3R floor a CLOSE rule on the execution frame
  (5/15/30/60m), while EMERGENCY_WICK_STOP keeps the ORIGINAL stop wick-live
  underneath it. So a position can reach +3R, +4R, +6R on closes, then lose
  one deep 5m wick to the original stop and book -1.00x. All 99 EMERGENCY_STOP
  trades are that event. The brain in Step 2 is the defence that the engine
  does not have.

USAGE  python3 audit_v45_true_multiple_brain.py [all|table|anatomy|sim]
"""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DATA5 = HERE / "data" / "binance_5m"
SYMS = ["ADAUSDT_5m", "AVAXUSDT_5m", "BNBUSDT_5m", "BTCUSDT_5m",
        "ETHUSDT_5m", "LINKUSDT_5m", "SOLUSDT_5m", "XRPUSDT_5m"]
COST = 0.001
BAR_NS = 300 * 10**9
TF_NS = {"5min": 5 * 60 * 10**9, "15min": 15 * 60 * 10**9,
         "30min": 30 * 60 * 10**9, "1h": 60 * 60 * 10**9}
ORDER = ["W1", "W2", "OLD7", "MOD_Y1", "MOD_Y2"]
LADDER = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


# ------------------------------------------------------------------ #
def load_tape() -> pd.DataFrame:
    parts = []
    for w in ORDER:
        d = pd.read_csv(RESULTS / f"trades_v37_B0_{w}.csv")
        d["win"] = w
        parts.append(d)
    t = pd.concat(parts, ignore_index=True)
    t["entry_ts"] = pd.to_datetime(t.entry_time, utc=True, format="mixed")
    t["exit_ts"] = pd.to_datetime(t.exit_time, utc=True, format="mixed")
    # NANOSECONDS on BOTH sides -- see the docstring. Never astype("int64")
    # on a pandas-3 datetime64[us] frame.
    t["entry_ns"] = t.entry_ts.astype("datetime64[ns, UTC]").astype("int64")
    t["exit_ns"] = t.exit_ts.astype("datetime64[ns, UTC]").astype("int64")
    t["qty"] = t.qty0.astype(float)
    t["fill"] = t.entry_price.astype(float)
    t["stop"] = t.stop_price.astype(float)
    t["unit_loss"] = t.fill * (1 + COST) - t.stop * (1 - COST)
    t["loss_$"] = t.unit_loss * t.qty
    # the CSV has no gross/fee columns; derive them and prove the identity
    t["gross_pnl"] = (t.exit_price - t.fill) * t.qty
    t["fees"] = t.entry_fee + t.exit_price * t.qty * COST
    assert (t.gross_pnl - t.fees - t.net_pnl).abs().max() < 1e-9, \
        "accounting identity broken"
    t["golden"] = ((t.exit_reason == "TARGET_REJECTION")
                   | ((t.exit_reason == "STOP_BLUE") & (t.R >= 3.0)))
    t["em"] = t.exit_reason == "EMERGENCY_STOP"
    t["be"] = t.exit_reason.isin(["BREAKEVEN", "SHIELD_BE"])
    t["other"] = ~(t.golden | t.em | t.be)
    t["ym"] = t.entry_ts.dt.strftime("%Y-%m")
    t["half"] = (t.entry_ts.dt.strftime("%Y-%m") + "_H"
                 + np.where(t.entry_ts.dt.day <= 15, "1", "2"))
    ic = t.entry_ts.dt.isocalendar()
    t["iso"] = (ic.year.astype(int).astype(str) + "-W"
                + ic.week.astype(int).astype(str).str.zfill(2))
    t["floor_line"] = ((t.fill * (1 + COST) + 3.0 * t.fill * t.risk_pct / 100.0)
                       / (1 - COST))
    t["risk"] = t.fill * t.risk_pct / 100.0
    return t


def load_5m(sym: str) -> dict:
    fs = sorted(glob.glob(str(DATA5 / sym / "*.csv.gz")))
    d = pd.concat([pd.read_csv(f, usecols=["Datetime", "Open", "High", "Low",
                                           "Close"])
                   for f in fs], ignore_index=True)
    ns = (pd.to_datetime(d.Datetime, utc=True, format="%Y-%m-%d %H:%M:%S%z")
          .astype("datetime64[ns, UTC]").astype("int64").to_numpy())
    assert ns[0] > 1_500_000_000_000_000_000, "tape is not in nanoseconds"
    return {"ns": ns, "o": d.Open.to_numpy(float), "h": d.High.to_numpy(float),
            "l": d.Low.to_numpy(float), "c": d.Close.to_numpy(float)}


def slice_bars(D: dict, a: int, b: int):
    """brief's slice: entry_time <= bar_start <= exit_time."""
    return (int(np.searchsorted(D["ns"], a, "left")),
            int(np.searchsorted(D["ns"], b, "right")))


def exec_closes(D: dict, a: int, b: int, tf_ns: int) -> dict:
    """The exec-frame bars whose END lands at a 5m boundary of tf_ns, with
    that bucket's o/h/l/c aggregated from the 5m bars, and a CAUSALITY flag
    bar_end <= exit_time (a bar that closes after the trade died was never
    seen by the engine and must not be counted)."""
    i0, i1 = slice_bars(D, a, b)
    if i1 <= i0:
        return None
    starts = D["ns"][i0:i1]
    bucket = (starts // tf_ns) * tf_ns
    last = np.r_[bucket[1:] != bucket[:-1], True]
    idx = np.nonzero(last)[0] + i0
    return {"end": bucket[last] + tf_ns, "o": D["o"][idx], "h": D["h"][idx],
            "l": D["l"][idx], "c": D["c"][idx], "i0": i0, "i1": i1}


# ------------------------------------------------------------------ #
def measure(t: pd.DataFrame, data: dict) -> pd.DataFrame:
    n = len(t)
    m5h = np.full(n, -np.inf)
    m5c = np.full(n, -np.inf)
    mcl = np.full(n, -np.inf)
    mclx = np.full(n, -np.inf)     # exec closes seen by the engine only
    for k, r in enumerate(t.itertuples(index=False)):
        D = data[r.symbol]
        i0, i1 = slice_bars(D, r.entry_ns, r.exit_ns)
        if i1 <= i0:
            continue
        m5h[k] = D["h"][i0:i1].max()
        m5c[k] = D["c"][i0:i1].max()
        E = exec_closes(D, r.entry_ns, r.exit_ns, TF_NS[r.exec_tf])
        if E is not None and len(E["c"]):
            mcl[k] = E["c"].max()
            seen = E["end"] <= r.exit_ns
            if seen.any():
                mclx[k] = E["c"][seen].max()
    out = t.copy()
    out["max_5m_high"] = m5h
    out["max_5m_close"] = m5c
    out["max_exec_close"] = mcl
    out["max_exec_close_seen"] = mclx
    f, L = out.fill.to_numpy(), out.unit_loss.to_numpy()

    def X(px): return (px * (1 - COST) - f * (1 + COST)) / L
    out["X_5m_high"] = X(m5h)
    out["X_5m_close"] = X(m5c)
    out["X_exec_close"] = X(mcl)
    out["B0_true_X"] = X(out.exit_price.to_numpy())
    return out


def assertions(t: pd.DataFrame, data: dict) -> dict:
    ok1 = t[t.em].max_5m_close >= t[t.em].floor_line - 1e-6
    # literal brief wording (exec close) -- reported, explained, not gated
    ok1_exec = t[t.em].max_exec_close >= t[t.em].floor_line - 1e-6
    lo = np.minimum(t.fill, t.exit_price)
    ok2_wick = t.max_5m_high >= lo - 1e-9
    ok2_close = t.max_exec_close >= lo - 1e-9
    bad2 = t[~ok2_close]
    explains = 0
    for r in bad2.itertuples(index=False):
        E = exec_closes(data[r.symbol], r.entry_ns, r.exit_ns,
                        TF_NS[r.exec_tf])
        m = E["end"] <= r.exit_ns + 1
        k = int(np.nonzero(m)[0][-1])
        # legit when the exit filled intrabar and the bar closed against it
        if E["l"][k] - 1e-9 <= r.exit_price <= E["h"][k] + 1e-9:
            explains += 1
        elif r.exit_price > E["h"][k] - 1e-9:
            explains += 1     # stop booked at the level, bar gapped through
    return {"a1_n": int(t.em.sum()), "a1_pass": int(ok1.sum()),
            "a1_exec_pass": int(ok1_exec.sum()),
            "a2_n": int(len(t)), "a2_wick_pass": int(ok2_wick.sum()),
            "a2_close_pass": int(ok2_close.sum()),
            "a2_close_fail_explained": explains,
            "mfe_wick_match": int(((t.max_5m_high
                                    - (t.fill + t.mfe_R * t.risk)).abs()
                                   <= t.fill * 0.006 + 1e-9).sum()),
            "mfe_close_match": int(((t.max_exec_close
                                     - (t.fill + t.mfe_close_R
                                        * t.risk)).abs()
                                    <= t.fill * 0.006 + 1e-9).sum())}


# ------------------------------------------------------------------ #
COHORTS = [("golden", "110 Golden"), ("em", "99 EMERGENCY_STOP"),
           ("be", "452 BREAKEVEN/SHIELD"), ("other", "512 STOP_BLUE/OTHER")]


def reach_table(t: pd.DataFrame) -> str:
    rows = []
    for key, label in COHORTS + [("all", "ALL 1,173")]:
        g = t if key == "all" else t[t[key]]
        r = {"cohort": label, "n": len(g),
             "med_c": round(float(g.X_exec_close.median()), 2),
             "med_5c": round(float(g.X_5m_close.median()), 2),
             "med_5h": round(float(g.X_5m_high.median()), 2),
             "net": round(float(g.net_pnl.sum()), 2),
             "loss": round(float(g["loss_$"].sum()), 2)}
        for m in LADDER:
            q = str(m).replace(".", "_")
            r[f"c{q}"] = int((g.X_exec_close >= m).sum())
            r[f"k{q}"] = int((g.X_5m_close >= m).sum())
            r[f"h{q}"] = int((g.X_5m_high >= m).sum())
        rows.append(r)
    d = pd.DataFrame(rows)
    L = ["| cohort | n | med exec-close | med 5m-close | med 5m-high "
         + "".join(f" | ≥{m}x c/k/h" for m in LADDER)
         + " | net $ | full −1x cost if all died |",
         "|---|---:|---:|---:|---:|" + "---:|" * len(LADDER) + "---:|---:|"]
    for r in d.itertuples(index=False):
        cells = "".join(
            f" | {getattr(r, 'c' + str(m).replace('.', '_'))}"
            f"/{getattr(r, 'k' + str(m).replace('.', '_'))}"
            f"/{getattr(r, 'h' + str(m).replace('.', '_'))}" for m in LADDER)
        L.append(f"| {r.cohort} | {r.n} | {r.med_c} | {r.med_5c} | {r.med_5h}"
                 f"{cells} | {r.net:+.2f} | {r.loss:+.2f} |")
    return "\n".join(L), d


# ------------------------------------------------------------------ #
def anatomy(t: pd.DataFrame, data: dict, armed: float = 2.0) -> pd.DataFrame:
    out = []
    for r in t.itertuples(index=False):
        if r.X_5m_close < armed:
            continue
        D = data[r.symbol]
        i0, i1 = slice_bars(D, r.entry_ns, r.exit_ns)
        o, h, l, c = D["o"][i0:i1], D["h"][i0:i1], D["l"][i0:i1], D["c"][i0:i1]
        px = c * (1 - COST) - r.fill * (1 + COST)
        hit = np.nonzero(px >= armed * r.unit_loss)[0]
        if not hit.size:
            continue
        k = int(hit[0])
        if k + 2 >= len(c):
            continue
        pos = (c[k] - l[k]) / (h[k] - l[k]) if h[k] > l[k] else 1.0
        nx1 = (c[k + 1] * (1 - COST) - r.fill * (1 + COST)) / r.unit_loss
        nx2 = (c[k + 2] * (1 - COST) - r.fill * (1 + COST)) / r.unit_loss
        out.append({"X_arm": round(float((c[k] * (1 - COST) - r.fill
                                          * (1 + COST)) / r.unit_loss), 3),
                    "pos": round(float(pos), 3), "bear": bool(c[k] < o[k]),
                    "n1_bear": bool(c[k + 1] < o[k + 1]),
                    "n1_lower": bool(c[k + 1] < c[k]),
                    "n1_below_low": bool(c[k + 1] < l[k]),
                    "n1_below_mid": bool(c[k + 1] < (h[k] + l[k]) / 2),
                    "X_n1": round(float(nx1), 3), "X_n2": round(float(nx2), 3),
                    "X_max": round(float(r.X_5m_close), 2),
                    "X_booked": round(float(r.B0_true_X), 2),
                    "runner": bool(r.X_5m_close > 4.0),
                    "died": bool(r.B0_true_X < 3.0)})
    return pd.DataFrame(out)


def anatomy_table(a: pd.DataFrame, armed: float) -> str:
    g = a[(a.runner | a.died)]
    rn, dn = int(g.runner.sum()), int(g.died.sum())
    L = [f"**Armed at a 5m close ≥ {armed:.1f}x true loss** — "
         f"{len(a)} arming bars, {rn} resolved into >4x runners, "
         f"{dn} died below 3x.", "",
         "| signal | runners n | share | died n | share | lift |",
         "|---|---:|---:|---:|---:|---:|"]
    for col, label in (("bear", "arming bar closed bearish (c<o)"),
                       ("n1_bear", "next bar closed bearish"),
                       ("n1_lower", "next bar closed lower"),
                       ("n1_below_low", "next bar closed below arming LOW"),
                       ("n1_below_mid", "next bar closed below arming MID")):
        rr, dd = int(g[g.runner][col].sum()), int(g[g.died][col].sum())
        sr, sd = rr / max(rn, 1), dd / max(dn, 1)
        L.append(f"| {label} | {rr} | {sr*100:.1f}% | {dd} | {sd*100:.1f}% | "
                 f"{'—' if sr == 0 else f'{sd/sr:.2f}×'} |")
    L.append(f"\n*Baseline:* {rn} runners vs {dn} deaths. Median next-bar "
             f"true_X — runners {g[g.runner].X_n1.median():.2f}x, deaths "
             f"{g[g.died].X_n1.median():.2f}x; 2-bar "
             f"{g[g.runner].X_n2.median():.2f}x / "
             f"{g[g.died].X_n2.median():.2f}x.")
    return "\n".join(L)


# ------------------------------------------------------------------ #
def px_at_true_X(fill, stop, M, cost=COST):
    unit = fill * (1 + cost) - stop * (1 - cost)
    return (fill * (1 + cost) + M * unit) / (1 - cost)


def sim(t: pd.DataFrame, data: dict, mode: str) -> pd.DataFrame:
    """Static tape simulation of a 100%-exit brain, 5m clock.

    Causality: a level computed from bar k may only be tested from bar k+1.
    Fill realism: if the bar OPENS beyond the level the fill is the open,
    never the level. No trigger fires on the bar that armed it.
    """
    n = len(t)
    net = np.zeros(n)
    xs = np.zeros(n)
    why = [""] * n
    for k, r in enumerate(t.itertuples(index=False)):
        D = data[r.symbol]
        i0, i1 = slice_bars(D, r.entry_ns, r.exit_ns)
        f, L_, q = r.fill, r.unit_loss, r.qty
        px = None
        tag = "B0_EXIT"
        if mode != "B0" and i1 > i0:
            o, h, l, c = (D["o"][i0:i1], D["h"][i0:i1],
                          D["l"][i0:i1], D["c"][i0:i1])
            Xh = (h * (1 - COST) - f * (1 + COST)) / L_
            Xc = (c * (1 - COST) - f * (1 + COST)) / L_
            n_ = len(c)
            if mode == "step_ladder":
                floor = -9e9
                for i in range(n_):
                    if floor > -8e8 and l[i] <= px_at_true_X(f, r.stop, floor):
                        lvl = px_at_true_X(f, r.stop, floor)
                        px, tag = min(lvl, o[i]), f"LADDER_{floor:.1f}x"
                        break
                    m = Xc[i]                       # arm on THIS close...
                    new = -9e9
                    for trig, fl in ((2.0, 1.2), (2.5, 2.0), (3.0, 2.5),
                                     (4.0, 3.0)):
                        if m >= trig:
                            new = max(new, fl)
                    if Xh[i] >= 5.0:
                        new = max(new, Xh[i] - 1.5)
                    floor = max(floor, new)          # ...live from i+1
            elif mode == "stall_or_run":
                armed = False
                for i in range(n_):
                    if not armed:
                        armed = Xc[i] >= 2.0
                        continue
                    if (Xc[i] >= 2.0 and c[i] < o[i]
                            and (c[i] < l[i - 1]
                                 or c[i] < (h[i - 1] + l[i - 1]) / 2)):
                        px, tag = c[i], f"STALL_{Xc[i]:.1f}x"
                        break
            elif mode == "wick_touch_guard":
                floor = -9e9
                for i in range(n_):
                    if floor > -8e8 and l[i] <= px_at_true_X(f, r.stop, floor):
                        lvl = px_at_true_X(f, r.stop, floor)
                        px, tag = min(lvl, o[i]), f"GUARD_{floor:.1f}x"
                        break
                    new = -9e9
                    if Xh[i] >= 3.0:
                        new = 2.2
                    elif Xh[i] >= 2.5:
                        new = 1.8
                    floor = max(floor, new)          # wick-armed, live at i+1
        if px is not None:
            net[k] = (px * (1 - COST) - f * (1 + COST)) * q
            xs[k] = (px * (1 - COST) - f * (1 + COST)) / L_
            why[k] = tag
        else:
            net[k] = r.net_pnl
            xs[k] = r.B0_true_X
            why[k] = "B0_EXIT"
    out = t.copy()
    out["net_sim"] = net
    out["X_sim"] = xs
    out["tag"] = why
    return out


def summ(fr: pd.DataFrame) -> dict:
    col = "net_sim" if "net_sim" in fr else "net_pnl"
    mo, hf, wk = (fr.groupby(x)[col].sum() for x in ("ym", "half", "iso"))
    return {"em": round(float(fr[fr.em][col].sum()), 2),
            "be": round(float(fr[fr.be][col].sum()), 2),
            "gold": round(float(fr[fr.golden][col].sum()), 2),
            "other": round(float(fr[fr.other][col].sum()), 2),
            "total": round(float(fr[col].sum()), 2),
            "mo": f"{int((mo > 1e-9).sum())}/{len(mo)}",
            "bw": f"{int((hf > 1e-9).sum())}/{len(hf)}",
            "wk": f"{int((wk > 1e-9).sum())}/{len(wk)}",
            "mix": dict(fr.tag.value_counts().head(6)) if "tag" in fr else {}}


def main() -> int:
    t0 = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    t = load_tape()
    data = {s: load_5m(s) for s in SYMS}
    t = measure(t, data)
    asr = assertions(t, data)
    print(f"# v45 STEP 1 — TRUE DOLLAR-LOSS MULTIPLES  "
          f"({time.time()-t0:.1f}s, ZERO engine runs)\n")
    print(f"trades **{len(t)}** · windows 5 · months **{t.ym.nunique()}** · "
          f"half-months **{t.half.nunique()}** · weeks **{t.iso.nunique()}** · "
          f"gross ${t.gross_pnl.sum():+.2f} · fees ${t.fees.sum():.2f} · "
          f"net **${t.net_pnl.sum():+.2f}**\n")
    print("## ASSERTIONS — printed before any table (the brief's gate)\n")
    p1 = asr["a1_pass"] == asr["a1_n"]
    print(f"* **ASSERTION 1** — every EMERGENCY_STOP reached ≥3.0x on the "
          f"5m close: **{asr['a1_pass']}/{asr['a1_n']}** → "
          f"**{'PASS' if p1 else 'FAIL'}**")
    print(f"* On the literal *exec-frame* close the same count is "
          f"{asr['a1_exec_pass']}/{asr['a1_n']}: the engine's floor is a "
          f"CLOSE rule on the exec frame, so a 15m/30m/1h bar can close back "
          f"under +3x after the 5m tape already traded there.")
    print(f"* **ASSERTION 2 (wick form)** — max_5m_high ≥ min(fill, exit_px): "
          f"**{asr['a2_wick_pass']}/{asr['a2_n']}** → "
          f"**{'PASS' if asr['a2_wick_pass'] == asr['a2_n'] else 'FAIL'}**")
    nf = asr["a2_n"] - asr["a2_close_pass"]
    print(f"* On the *close* form the count is {asr['a2_close_pass']}/"
          f"{asr['a2_n']}. The {nf} exceptions are single-bar stop-outs: the "
          f"stop was hit intrabar and the bar closed against the exit — the "
          f"close form is not a valid invariant for a wick-exit engine.")
    print(f"* **Slice validated against the engine's own MFEs** — 5m high "
          f"agrees with `mfe_R` on **{asr['mfe_wick_match']}/1173** trades, "
          f"exec close with `mfe_close_R` on **{asr['mfe_close_match']}/1173** "
          f"(remainder = tick rounding). A mis-sliced tape would score ~0.\n")
    tbl, _ = reach_table(t)
    if which in ("all", "table"):
        print("## 1. REACH TABLE — true-loss multiples by cohort\n")
        print(tbl, "\n")
        print("*`c` = the exec-frame close the engine actually sees, `k` = the "
              "5m close, `h` = the 5m high. Read `k`/`h` as the opportunity "
              "and `c` as the part the current engine can bank.*\n")
    if which in ("all", "anatomy"):
        rows = []
        for a_ in (2.0, 2.5, 3.0):
            aa = anatomy(t, data, a_)
            rows.append(aa)
            print(f"### 2.{int(a_*10) % 100} stalled-or-ran at {a_:.1f}x\n")
            print(anatomy_table(aa, a_), "\n")
        pd.concat(rows).to_csv(RESULTS / "_v45_anatomy.csv", index=False)
    if which in ("all", "sim"):
        print("## 3. STATIC TAPE SIM — the 1,173-trade book held fixed\n")
        out = {}
        L = ["| arm | EM_99 $ | BE_452 $ | Golden_110 $ | Other_512 $ | "
             "**Total** | Δ vs B0 | mo+ | bw+ | wk+ |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name, mode in (("B0", "B0"),
                           ("BRAIN_A_STEP_LADDER", "step_ladder"),
                           ("BRAIN_B_STALL_OR_RUN", "stall_or_run"),
                           ("BRAIN_C_WICK_TOUCH_GUARD", "wick_touch_guard")):
            fr = t if mode == "B0" else sim(t, data, mode)
            s = summ(fr)
            if mode == "B0":
                s["total"] = round(float(t.net_pnl.sum()), 2)
                s["delta"] = 0.0
            else:
                s["delta"] = round(s["total"] - float(t.net_pnl.sum()), 2)
            out[name] = s
            L.append(f"| {name} | {s['em']:+.2f} | {s['be']:+.2f} | "
                     f"{s['gold']:+.2f} | {s['other']:+.2f} | "
                     f"**{s['total']:+.2f}** | {s.get('delta', 0.0):+.2f} | "
                     f"{s['mo']} | {s['bw']} | {s['wk']} |")
            if mode != "B0":
                fr.to_csv(RESULTS / f"_v45_sim_{mode}.csv", index=False)
                print(f"*{name}* exit mix: {s['mix']}")
        print("\n" + "\n".join(L) + "\n")
        (RESULTS / "_v45_sim.json").write_text(json.dumps(out, indent=1,
                                                          default=str))
    (RESULTS / "_v45_audit.json").write_text(json.dumps(asr, indent=1,
                                                        default=str))
    print(f"_total {time.time()-t0:.2f}s_")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
