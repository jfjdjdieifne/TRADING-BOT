#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v24_narrative.py — THE FORENSIC NARRATIVE AUDIT (v24 -> v25)
==================================================================
Reads the FULL market story around every one of the 249 v24 trades
(62 WIN / 43 BE / 144 LOSS) directly from the chart, 100% causal:

  PRE-ENTRY  (4H + 1H canvases, rebuilt bar by bar, snapshot exactly at
              the trade's entry time — only bars whose end_time <= t):
    * institutional order-flow direction (last structural break up vs
      last structural break down — no windows, no invented numbers)
    * BSL raid that failed (wick through a red box, close back below)
      happening AFTER the last blue chop  => "the highs were taken out"
    * SSL raid reclaimed AFTER the last red break => bullish fuel
    * distance (in R) to the nearest live bearish wall (sell-side FVG)
    * nearest INVERSION FVG support below (bearish gap closed through)
    * entry inside live HTF demand (bullish FVG / green OB)
    * entry in the HTF discount (<= PurpleBox.mid)
    * ICT UNICORN: a broken red box (breaker) overlapping a live
      bullish FVG / green OB with the entry inside that overlap

  POST-ENTRY (the trade's own exec frame path, bar by bar):
    * first displacement close (+0.5R / +1R / +1.5R)
    * the post-entry higher low that launched the move
    * the bar where a close fell back below that higher low  => the
      moment the bullish story was structurally invalidated
    * bearish CHoCH (that break + a fresh bearish FVG)
    * whether the internal red box above entry was broken
    * MFE on closes, purple-mid cross, actual booked R

  THEN it simulates, on the real data:
    (A) every candidate pre-entry gate: wins kept / losses kept / WR
    (B) the post-displacement structural shield: how many -1R losses
        become scratches, and how many winners it would sacrifice
    (C) the best combination, with per-year trade counts

Outputs: results/audit_v24_features.csv, results/audit_v24_narrative.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import strategy_v24_boxes as v24
from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf

RESULTS = Path(__file__).resolve().parent / "results"
DATA = Path(__file__).resolve().parent / "data" / "BTCUSD_5m"
FEE = v24.FEE
MIN_R = v24.MIN_R
LOOKBACK = 300          # infrastructure: bars of context for fractals/gaps


# ==================================================================== #
# A canvas that also remembers LIQUIDITY RAIDS and INVERSIONS
# ==================================================================== #
class NarrativeCanvas(v24.ChartCanvas):
    def __init__(self, tf):
        super().__init__(tf)
        self.raids_up = []        # (idx, time, box_top) BSL run + fail
        self.raids_dn = []        # (idx, time, box_bot) SSL run + reclaim
        self.last_red_break = None    # (idx, time) body close above a red
        self.last_blue_chop = None    # (idx, time) body close below a blue
        self.ifvgs = []           # bearish gap killed BY CLOSE (inversion)
        self._seen_br = set()
        self._seen_ch = set()
        self._seen_if = set()

    def on_bar(self, o, h, l, c, v, idx, time=None):
        ev = super().on_bar(o, h, l, c, v, idx, time)
        for r in self.reds:
            if r.state == "BROKEN" and id(r) not in self._seen_br:
                self._seen_br.add(id(r))
                self.last_red_break = (idx, time)
        for b in self.blues:
            if b.state == "DEAD" and id(b) not in self._seen_ch:
                self._seen_ch.add(id(b))
                self.last_blue_chop = (idx, time)
        for y in self.yellows_s:
            if y.state == "DEAD" and id(y) not in self._seen_if:
                self._seen_if.add(id(y))
                # killed by a BODY CLOSE above it => inversion (support);
                # killed by a mere touch is not an inversion
                self.ifvgs.append({"idx": idx, "time": time,
                                   "bottom": y.y_bottom, "top": y.y_top,
                                   "by_close": bool(c > y.y_top)})
        # liquidity raids on boxes that SURVIVED the bar (still active)
        for r in self.reds:
            if r.state == "ACTIVE" and h > r.y_top and c < r.y_top:
                self.raids_up.append((idx, time, r.y_top))
        for b in self.blues:
            if b.state == "ACTIVE" and l < b.y_bottom and c > b.y_bottom:
                self.raids_dn.append((idx, time, b.y_bottom))
        return ev

    # ---------------- narrative reads (all causal) ------------------ #
    def flow(self):
        """Direction of the story: whichever structural break printed
        LAST. No lookback windows, no magic numbers."""
        rb, bc = self.last_red_break, self.last_blue_chop
        if rb is None and bc is None:
            return None
        if bc is None:
            return "BULL"
        if rb is None:
            return "BEAR"
        return "BULL" if rb[0] > bc[0] else "BEAR"

    def raid_high_failed(self):
        """BSL run that failed AFTER the last blue chop => the highs
        have already been taken out: buying here is buying the raid."""
        if not self.raids_up:
            return False
        ridx = self.raids_up[-1][0]
        return self.last_blue_chop is None or ridx > self.last_blue_chop[0]

    def raid_low_reclaimed(self):
        """SSL run reclaimed AFTER the last red break => fuel for longs."""
        if not self.raids_dn:
            return False
        didx = self.raids_dn[-1][0]
        return self.last_red_break is None or didx > self.last_red_break[0]

    def wall_r(self, entry, risk):
        w = self.nearest_ceiling(entry)
        return None if w is None else (w.y_bottom - entry) / risk

    def ifvg_support_r(self, entry, risk):
        best = None
        for f in self.ifvgs:
            if f["by_close"] and f["top"] <= entry:
                d = (entry - f["top"]) / risk
                if best is None or d < best:
                    best = d
        return best

    def in_demand(self, entry):
        for b in list(self.greens) + list(self.yellows_b):
            if b.state == "ACTIVE" and b.y_bottom <= entry <= b.y_top:
                return True
        return False

    def discount(self, entry):
        return self.purple is not None and entry <= self.purple.mid

    def unicorn(self, entry):
        """ICT Unicorn: a broken red box (breaker) overlapping a live
        bullish FVG / green OB, with the entry inside the overlap.
        Returns (bool, overlap height in R)."""
        live = [b for b in list(self.greens) + list(self.yellows_b)
                if b.state == "ACTIVE"]
        for r in self.reds:
            if r.state != "BROKEN":
                continue
            for d in live:
                lo = max(r.y_bottom, d.y_bottom)
                hi = min(r.y_top, d.y_top)
                if lo <= entry <= hi:
                    return True, hi - lo
        return False, 0.0


# ==================================================================== #
def build_frames():
    raw = load_asset_ohlcv(DATA, include_stems=[str(y) for y in
                                                range(2020, 2027)])
    frames = {f: resample_causal_tf(raw, f)
              for f in ("5min", "15min", "30min", "1h", "4h")}
    return raw, frames


def pre_entry_context(trades, frames):
    """One causal pass over 1H + 4H; snapshot at every entry time."""
    tf_1h, tf_4h = frames["1h"], frames["4h"]
    H = NarrativeCanvas("1h")
    S = NarrativeCanvas("4h")
    warm = pd.Timestamp("2020-11-01", tz="UTC")
    tf_1h = tf_1h[tf_1h.index >= warm]
    tf_4h = tf_4h[tf_4h.index >= warm]

    by_time = {}
    for i, t in trades.iterrows():
        by_time.setdefault(pd.Timestamp(t["entry_time"]), []).append(i)

    out = {i: {} for i in trades.index}
    p1 = p4 = 0
    # ZERO-LOOKAHEAD: the timeline is the union of HTF bar END times and
    # the trades' own entry times. At a trade time we feed only HTF bars
    # whose end_time <= that instant, so a 5m entry at 12:15 sees the 1H
    # story up to the bar that ended 12:00 — never the one still forming.
    stamps = sorted(set(tf_1h.index) | set(tf_4h.index) | set(by_time))
    for t in stamps:
        while p4 < len(tf_4h) and tf_4h.index[p4] <= t:
            r = tf_4h.iloc[p4]
            S.on_bar(r.Open, r.High, r.Low, r.Close, 0.0,
                     len(S.bars), tf_4h.index[p4])
            p4 += 1
        while p1 < len(tf_1h) and tf_1h.index[p1] <= t:
            r = tf_1h.iloc[p1]
            H.on_bar(r.Open, r.High, r.Low, r.Close, 0.0,
                     len(H.bars), tf_1h.index[p1])
            p1 += 1
        # every trade whose entry bar closed exactly at this stamp
        for ts, rows in list(by_time.items()):
            if ts != t:
                continue
            for i in rows:
                tr = trades.loc[i]
                E = float(tr["entry_price"])
                Rk = E - float(tr["stop_price"])
                SPx = float(tr["stop_price"])
                for tag, cv in (("4h", S), ("1h", H)):
                    uni, depth = cv.unicorn(E)
                    # nesting done right: does the LTF invalidation
                    # (the stop) sit inside live HTF demand, and did the
                    # wave sweep a HTF blue box (SSL raid) to get there?
                    stop_dem = cv.in_demand(SPx)
                    swept_htf = any(b.state == "ACTIVE"
                                    and b.y_bottom <= SPx <= b.y_top
                                    for b in cv.blues)
                    rng = cv.purple
                    pos_in_range = (None if rng is None else
                                    round((E - rng.y_bottom) /
                                          max(rng.height, 1e-9), 3))
                    out[i].update({
                        f"stop_in_demand_{tag}": stop_dem,
                        f"stop_in_htf_blue_{tag}": swept_htf,
                        f"range_pos_{tag}": pos_in_range,
                        f"flow_{tag}": cv.flow(),
                        f"wall_r_{tag}": cv.wall_r(E, Rk),
                        f"ifvg_r_{tag}": cv.ifvg_support_r(E, Rk),
                        f"in_demand_{tag}": cv.in_demand(E),
                        f"discount_{tag}": cv.discount(E),
                        f"raid_high_{tag}": cv.raid_high_failed(),
                        f"raid_low_{tag}": cv.raid_low_reclaimed(),
                        f"unicorn_{tag}": uni,
                        f"unicorn_depth_r_{tag}": round(depth / Rk, 3),
                    })
            del by_time[ts]
        if not by_time:
            break
    return out


def post_entry_story(trades, frames):
    """Bar-by-bar story after the fill, on the trade's own frame."""
    rows = {}
    for i, t in trades.iterrows():
        tf = frames[t["exec_tf"]]
        E = float(t["entry_price"])
        SP = float(t["stop_price"])
        Rk = E - SP
        e_t = pd.Timestamp(t["entry_time"])
        x_t = pd.Timestamp(t["exit_time"])
        seg = tf.loc[e_t:x_t]
        o = seg["Open"].to_numpy(); h = seg["High"].to_numpy()
        l = seg["Low"].to_numpy(); c = seg["Close"].to_numpy()
        n = len(c)
        pmid = float(t["purple_mid"]) if pd.notna(t["purple_mid"]) else None

        def first_close_at(k):
            tgt = E + k * Rk
            for j in range(n):
                if c[j] >= tgt:
                    return j
            return None

        d05, d10, d15 = (first_close_at(0.5), first_close_at(1.0),
                         first_close_at(1.5))
        hl = None            # post-entry higher low that launched it
        shield_bar = None
        shield_r = None
        choch = False
        if d10 is not None:
            hl = float(l[:d10 + 1].min())
            if hl > E:                     # a genuine higher low
                for j in range(d10 + 1, n):
                    if c[j] < hl:
                        shield_bar = j
                        shield_r = round((c[j] - E) / Rk, 3)
                        # bearish CHoCH = that break + a fresh gap down
                        if j >= 2 and h[j] < l[j - 2]:
                            choch = True
                        break
        crossed_mid = None
        if pmid is not None:
            for j in range(n):
                if c[j] > pmid:
                    crossed_mid = j
                    break
        # bearish FVG anywhere after entry (the story turning down)
        bear_fvg = any(j >= 2 and h[j] < l[j - 2] for j in range(n))

        rows[i] = {
            "bars": n,
            "disp_05r_bar": d05, "disp_1r_bar": d10, "disp_15r_bar": d15,
            "post_entry_hl_R": None if hl is None else round((hl - E) / Rk, 3),
            "shield_bar": shield_bar, "shield_R": shield_r,
            "choch_at_shield": choch,
            "crossed_purple_mid": crossed_mid is not None,
            "bear_fvg_after_entry": bear_fvg,
        }
    return rows


def exec_unicorn_from_boxes(trades):
    """The UNICORN on the execution frame itself, straight from the
    boxes the engine recorded at entry (broken red + FVG/OB overlap)."""
    out = {}
    for i, t in trades.iterrows():
        E = float(t["entry_price"])
        Rk = E - float(t["stop_price"])
        br = json.loads(t["broken_red"].replace("'", '"')) \
            if isinstance(t["broken_red"], str) else t["broken_red"]
        uni = False
        depth = 0.0
        if isinstance(br, dict):
            for key in ("yellow", "green"):
                b = json.loads(t[key].replace("'", '"')) \
                    if isinstance(t[key], str) else t[key]
                if not isinstance(b, dict):
                    continue
                lo = max(br["bottom"], b["bottom"])
                hi = min(br["top"], b["top"])
                if lo <= E <= hi:
                    uni = True
                    depth = max(depth, hi - lo)
        # standing ON the breaker: the broken red is now a floor below
        on_breaker = bool(isinstance(br, dict) and br["top"] <= E)
        out[i] = {"unicorn_exec": uni,
                  "unicorn_exec_depth_r": round(depth / Rk, 3),
                  "on_breaker_exec": on_breaker}
    return out


# ==================================================================== #
def main():
    trades = pd.read_csv(RESULTS / "trades_v24.csv")
    trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    trades["exit_time"] = pd.to_datetime(trades["exit_time"])
    trades["yr"] = trades["entry_time"].dt.year.astype(str)
    print(f"[audit] {len(trades)} v24 trades: "
          f"{trades['class'].value_counts().to_dict()}")

    _, frames = build_frames()
    print("[audit] frames rebuilt causally")

    feat = {}
    feat.update(pre_entry_context(trades, frames))
    print("[audit] pre-entry HTF narrative captured")
    post = post_entry_story(trades, frames)
    print("[audit] post-entry story captured")
    exe = exec_unicorn_from_boxes(trades)
    for i in trades.index:
        feat[i].update(post[i]); feat[i].update(exe[i])

    F = pd.DataFrame(feat).T.reindex(trades.index)
    A = pd.concat([trades, F], axis=1)
    A.to_csv(RESULTS / "audit_v24_features.csv", index=False)

    W = A[A["class"] == "WIN"]
    L = A[A["class"] == "LOSS"]
    B = A[A["class"] == "BE"]

    # ---------------- TABLE 1: winners vs losers ------------------- #
    print("\n================ TABLE 1 — WHO WON, WHO LOST ================")
    print(f"WIN n={len(W)}  LOSS n={len(L)}  BE n={len(B)}")
    rows = []
    for col, kind in (("flow_4h", "cat"), ("flow_1h", "cat"),
                      ("raid_high_4h", "bool"), ("raid_high_1h", "bool"),
                      ("raid_low_4h", "bool"), ("raid_low_1h", "bool"),
                      ("in_demand_4h", "bool"), ("in_demand_1h", "bool"),
                      ("discount_4h", "bool"), ("discount_1h", "bool"),
                      ("unicorn_4h", "bool"), ("unicorn_1h", "bool"),
                      ("unicorn_exec", "bool"), ("on_breaker_exec", "bool"),
                      ("stop_in_demand_4h", "bool"),
                      ("stop_in_demand_1h", "bool"),
                      ("stop_in_htf_blue_4h", "bool"),
                      ("stop_in_htf_blue_1h", "bool"),
                      ("crossed_purple_mid", "bool"),
                      ("bear_fvg_after_entry", "bool"),
                      ("choch_at_shield", "bool")):
        if kind == "cat":
            for val in ("BULL", "BEAR", None):
                w = (W[col] == val).mean() * 100 if len(W) else 0
                l = (L[col] == val).mean() * 100 if len(L) else 0
                rows.append([f"{col}={val}", round(w, 1), round(l, 1),
                             round(w - l, 1)])
        else:
            w = W[col].astype(bool).mean() * 100 if len(W) else 0
            l = L[col].astype(bool).mean() * 100 if len(L) else 0
            rows.append([col, round(w, 1), round(l, 1), round(w - l, 1)])
    T1 = pd.DataFrame(rows, columns=["feature", "WIN %", "LOSS %", "gap"])
    print(T1.to_string(index=False))

    print("\n---- numeric context (median) ----")
    for col in ("wall_r_4h", "wall_r_1h", "ifvg_r_4h", "ifvg_r_1h",
                "unicorn_exec_depth_r", "risk_pct", "mfe_close_R"):
        A[col] = pd.to_numeric(A[col], errors="coerce")
        print(f"  {col:22} WIN={W[col].astype(float).median() if len(W) else None}"
              f"  LOSS={L[col].astype(float).median() if len(L) else None}")

    # ---------------- TABLE 2: gate simulations -------------------- #
    print("\n================ TABLE 2 — PRE-ENTRY GATES ================")
    print("(applied to the REAL v24 trade list: what each gate keeps)")

    def sim(mask, label):
        k = A[mask.fillna(False)]
        w = (k["class"] == "WIN").sum(); l = (k["class"] == "LOSS").sum()
        b = (k["class"] == "BE").sum()
        wr = w / max(w + l, 1)
        yrs = k.groupby("yr").size().to_dict()
        ok5 = len(k) >= 150 and all(yrs.get(str(y), 0) >= 12
                                    for y in range(2021, 2026))
        print(f"  {label:46} n={len(k):3} W={w:3} BE={b:3} L={l:3} "
              f"WR={wr:5.1%} a5={'Y' if ok5 else 'n'} yrs={yrs}")
        return {"gate": label, "n": int(len(k)), "W": int(w), "BE": int(b),
                "L": int(l), "WR": round(wr, 4), "assert5_ok": bool(ok5),
                "yearly": {str(k2): int(v) for k2, v in yrs.items()}}

    A["flow_4h"] = A["flow_4h"].where(A["flow_4h"].notna(), None)
    A["flow_1h"] = A["flow_1h"].where(A["flow_1h"].notna(), None)
    gates = []
    gates.append(sim(pd.Series(True, index=A.index), "baseline (no gate)"))
    gates.append(sim(A["flow_4h"] == "BULL", "G1 4H order flow BULLISH"))
    gates.append(sim(A["flow_1h"] == "BULL", "G2 1H order flow BULLISH"))
    gates.append(sim((A["flow_4h"] == "BULL") & (A["flow_1h"] == "BULL"),
                     "G3 4H AND 1H BULLISH"))
    gates.append(sim(~A["raid_high_4h"].astype(bool),
                     "G4 no failed BSL raid on 4H"))
    gates.append(sim(~A["raid_high_1h"].astype(bool),
                     "G5 no failed BSL raid on 1H"))
    gates.append(sim(A["raid_low_1h"].astype(bool),
                     "G6 reclaimed SSL raid on 1H"))
    w1 = A["wall_r_1h"].isna() | (A["wall_r_1h"] >= MIN_R)
    gates.append(sim(w1, "G7 1H wall >= 3R or open sky"))
    gates.append(sim(A["in_demand_1h"].astype(bool),
                     "G8 entry inside 1H demand"))
    gates.append(sim(A["in_demand_4h"].astype(bool),
                     "G9 entry inside 4H demand"))
    gates.append(sim(A["discount_1h"].astype(bool), "G10 1H discount"))
    gates.append(sim(A["unicorn_exec"].astype(bool),
                     "G11 UNICORN on exec frame"))
    gates.append(sim(A["unicorn_1h"].astype(bool), "G12 UNICORN on 1H"))
    gates.append(sim(A["unicorn_4h"].astype(bool), "G13 UNICORN on 4H"))
    i1 = A["ifvg_r_1h"].notna()
    gates.append(sim(i1, "G14 standing on a 1H inversion FVG"))
    i4 = A["ifvg_r_4h"].notna()
    gates.append(sim(i4, "G15 standing on a 4H inversion FVG"))
    gates.append(sim(A["stop_in_demand_4h"].astype(bool),
                     "G16 stop nested in 4H demand"))
    gates.append(sim(A["stop_in_demand_1h"].astype(bool),
                     "G17 stop nested in 1H demand"))
    gates.append(sim(A["stop_in_htf_blue_4h"].astype(bool),
                     "G18 stop inside a live 4H blue (SSL)"))
    rp = pd.to_numeric(A["range_pos_4h"], errors="coerce")
    gates.append(sim(rp <= 0.25, "G19 entry in the 4H bottom quarter"))
    gates.append(sim(rp <= 0.5, "G20 entry in the 4H bottom half"))
    w4 = A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 6)
    gates.append(sim(w4, "G21 4H sky >= 6R (T3 room)"))
    w4b = A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 10)
    gates.append(sim(w4b, "G22 4H sky >= 10R"))
    # combinations
    combo_a = (A["flow_4h"] == "BULL") & w1
    gates.append(sim(combo_a, "C1 G1+G7"))
    combo_b = (A["flow_1h"] == "BULL") & w1
    gates.append(sim(combo_b, "C2 G2+G7"))
    combo_c = (A["flow_4h"] == "BULL") & (A["flow_1h"] == "BULL") & w1
    gates.append(sim(combo_c, "C3 G3+G7"))
    combo_d = (A["flow_1h"] == "BULL") & ~A["raid_high_1h"].astype(bool)
    gates.append(sim(combo_d, "C4 G2+G5"))
    combo_e = ((A["flow_4h"] == "BULL") & ~A["raid_high_1h"].astype(bool)
               & w1)
    gates.append(sim(combo_e, "C5 G1+G5+G7"))
    combo_f = (A["unicorn_exec"].astype(bool) | A["unicorn_1h"].astype(bool)
               | A["unicorn_4h"].astype(bool))
    gates.append(sim(combo_f, "C6 UNICORN on ANY frame"))
    combo_g = combo_f & (A["flow_4h"] == "BULL")
    gates.append(sim(combo_g, "C7 UNICORN any + 4H BULL"))
    combo_h = (i1 | i4)
    gates.append(sim(combo_h, "C8 inversion FVG on 1H or 4H"))
    combo_i = combo_h & (A["flow_4h"] == "BULL")
    gates.append(sim(combo_i, "C9 inversion + 4H BULL"))

    # ---------------- TABLE 3: post-entry shield ------------------- #
    print("\n================ TABLE 3 — POST-DISPLACEMENT SHIELD ==========")
    print("(variants: ARM on a real displacement event, INVALIDATE on a")
    print(" structural break; a scratched trade is neither W nor L)")
    A["_hl"] = pd.to_numeric(A["post_entry_hl_R"], errors="coerce")
    A["_sb"] = pd.to_numeric(A["shield_bar"], errors="coerce")
    variants = {
        "V1 arm +1R close, exit close<post-entry HL":
            A["_sb"].notna() & (A["_hl"] > 0),
        "V2 arm +1R close (any HL)":
            A["disp_1r_bar"].notna() & A["_sb"].notna(),
        "V3 arm +1.5R close":
            A["disp_15r_bar"].notna() & A["_sb"].notna(),
        "V4 arm on 4H purple-mid cross":
            A["crossed_purple_mid"].astype(bool) & A["_sb"].notna(),
        "V5 arm mid-cross AND +1R":
            A["crossed_purple_mid"].astype(bool)
            & A["disp_1r_bar"].notna() & A["_sb"].notna(),
        "V6 arm +1R, invalidate only on bearish CHoCH":
            A["_sb"].notna() & (A["_hl"] > 0)
            & A["choch_at_shield"].astype(bool),
    }
    vrows = []
    for lab, m in variants.items():
        m = m.fillna(False)
        saved = int(((A["class"] == "LOSS") & m).sum())
        sacr = int(((A["class"] == "WIN") & m).sum())
        nw = (A["class"] == "WIN").sum() - sacr
        nl = (A["class"] == "LOSS").sum() - saved
        print(f"  {lab:52} saved={saved:3} sacrificed={sacr:3} "
              f"=> WR {nw/max(nw+nl,1):5.1%} (W={nw} L={nl})")
        vrows.append({"variant": lab, "losses_saved": saved,
                      "winners_sacrificed": sacr,
                      "WR": round(nw / max(nw + nl, 1), 4)})
    print()
    print("(exit at BREAKEVEN when a close falls back below the "
          "post-entry higher low, armed ONLY after a +1R displacement)")
    arm = variants["V1 arm +1R close, exit close<post-entry HL"]
    print(f"  trades where the shield would arm: {int(arm.sum())} / {len(A)}")
    for cls in ("WIN", "LOSS", "BE"):
        sub = A[A["class"] == cls]
        print(f"    {cls:4}: armed {int((sub['shield_bar'].notna()).sum())}"
              f" / {len(sub)}")
    # who is saved, who is sacrificed
    saved = A[(A["class"] == "LOSS") & arm]
    lost = A[(A["class"] == "WIN") & arm]
    print(f"  -1R losses converted to scratch : {len(saved)}")
    print(f"  winners sacrificed to scratch   : {len(lost)} "
          f"(their booked R: "
          f"{sorted(round(x,2) for x in lost['R'].astype(float))[:12]})")
    nw = (A["class"] == "WIN").sum() - len(lost)
    nl = (A["class"] == "LOSS").sum() - len(saved)
    print(f"  => WR after shield alone: {nw}/{nw+nl} = "
          f"{nw/max(nw+nl,1):.1%}  (was 30.1%)")
    print(f"  => trades still >= 180? {len(A)} (unchanged: scratches "
          f"stay in the list)")

    # shield + best gate combos
    print("\n---- shield combined with the gates that kept volume ----")
    for g in gates:
        mask = None
        lab = g["gate"]
        if lab.startswith("G1 "):
            mask = A["flow_4h"] == "BULL"
        elif lab.startswith("G7 "):
            mask = w1
        elif lab.startswith("C5 "):
            mask = combo_e
        elif lab.startswith("C2 "):
            mask = combo_b
        elif lab.startswith("C6 "):
            mask = combo_f
        elif lab.startswith("C8 "):
            mask = combo_h
        elif lab.startswith("G16"):
            mask = A["stop_in_demand_4h"].astype(bool)
        elif lab.startswith("G19"):
            mask = rp <= 0.25
        elif lab.startswith("G21"):
            mask = w4
        elif lab.startswith("G22"):
            mask = w4b
        if mask is None:
            continue
        k = A[mask.fillna(False)]
        a2 = (k["shield_bar"].notna()
              & (pd.to_numeric(k["post_entry_hl_R"], errors="coerce") > 0))
        w2 = (k["class"] == "WIN").sum() - int(((k["class"] == "WIN") & a2).sum())
        l2 = (k["class"] == "LOSS").sum() - int(((k["class"] == "LOSS") & a2).sum())
        yrs = k.groupby("yr").size().to_dict()
        ok5 = len(k) >= 150 and all(yrs.get(str(y), 0) >= 12
                                    for y in range(2021, 2026))
        print(f"  {lab:46} + shield => W={w2:3} L={l2:3} "
              f"WR={w2/max(w2+l2,1):5.1%} n={len(k):3} "
              f"a5={'Y' if ok5 else 'n'} yrs={yrs}")

    with open(RESULTS / "audit_v24_narrative.json", "w") as f:
        json.dump({"table1": T1.to_dict("records"), "gates": gates,
                   "shield_variants": vrows,
                   "shield": {"armed": int(arm.sum()),
                              "losses_saved": int(len(saved)),
                              "winners_sacrificed": int(len(lost)),
                              "wr_after": round(nw / max(nw + nl, 1), 4)}},
                  f, indent=2, default=str)
    print("\n[audit] wrote results/audit_v24_features.csv + "
          "results/audit_v24_narrative.json")


if __name__ == "__main__":
    main()
