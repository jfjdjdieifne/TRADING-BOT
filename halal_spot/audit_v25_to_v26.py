#!/usr/bin/env python3
"""
audit_v25_to_v26.py — TARGETED FORENSIC AUDIT FOR THE WR >= 60% QUESTION
=========================================================================
Reads ONLY the artefacts the v25 engine already produced
(results/trades_v25.csv) plus causal re-derivations from fields that were
snapshotted AT ENTRY TIME (therefore zero-lookahead by construction).

It answers the three engineering questions raised for v26:

  Q-A  "Did the +3.00R lock line sit BEYOND the delivery point?"
       Derive, for every trade, the R-distance from the entry to the TOP of
       the 4H dealing range (PurpleBox.y_top) — the ICT draw on liquidity.
       Both inputs (purple_mid and nar_range_pos_4h) were written at entry,
       so the derived quantity is a legitimate PRE-ENTRY gate.

  Q-B  "How many of the 48 scratches / the mid-crossing losers actually
       travelled >= +1.5R .. >= +3.0R before reversing?"
       Uses mfe_close_R (max favourable excursion measured on CLOSES only),
       which is the conservative, non-wick measure.

  Q-C  "Which causal pre-entry filter converts the decided-trade win rate
       WIN/(WIN+LOSS) to >= 60% while keeping total >= 150 and >= 12/year?"
       NOTE the definition, verified in strategy_v25_ict_narrative.py:
           decided  = len(wins) + len(losses)        # BE excluded
           win_rate = len(wins) / decided
           total    = len(wins) + len(losses) + len(be)   # BE included
       So a scratch costs NOTHING in the win-rate denominator but DOES count
       towards the 150-trade floor. That asymmetry is the whole game.

Every filter below is evaluated on REAL v25 outcomes. Filters marked
[PRE-ENTRY] are computable at the entry tick (causal, shippable as-is).
Filters marked [PATH] depend on what happened after entry (they estimate the
effect of an exit-rule change and are therefore UPPER BOUNDS: arming a shield
earlier also destroys some winners, which a CSV replay cannot see).
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

RES = Path(__file__).resolve().parent / "results"
CSV = RES / "trades_v25.csv"
OUT_JSON = RES / "audit_v25_to_v26.json"
OUT_CSV = RES / "audit_v25_to_v26.csv"

YEARS = ("2021", "2022", "2023", "2024", "2025")


# --------------------------------------------------------------------- #
def load() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df["t"] = pd.to_datetime(df["entry_time"], utc=True)
    df["y"] = df["t"].dt.year.astype(str)
    df["risk"] = df["entry_price"] - df["stop_price"]

    # ---- Q-A: derive the 4H dealing-range TOP in R units -------------
    # range_pos = (entry - bottom) / (top - bottom) ; mid = (top+bottom)/2
    #   => H = (entry - mid) / (pos - 0.5) ; top = entry + (1 - pos) * H
    pos = df["nar_range_pos_4h"]
    mid = df["purple_mid"]
    ok = pos.notna() & mid.notna() & ((pos - 0.5).abs() > 1e-6)
    H = (df["entry_price"] - mid) / (pos - 0.5)
    top = df["entry_price"] + (1.0 - pos) * H
    df["purple_top"] = top.where(ok)
    df["sky_r_purple"] = ((top - df["entry_price"]) / df["risk"]).where(ok)
    # same for the range BOTTOM (how far the invalidation really is)
    bot = df["entry_price"] - pos * H
    df["purple_bot"] = bot.where(ok)
    df["floor_r_purple"] = ((df["entry_price"] - bot) / df["risk"]).where(ok)
    return df


def cohort_stats(g: pd.DataFrame) -> dict:
    n = len(g)
    if n == 0:
        return {"n": 0}
    return {
        "n": n,
        "mfe_close_ge_1.0R": int((g["mfe_close_R"] >= 1.0).sum()),
        "mfe_close_ge_1.5R": int((g["mfe_close_R"] >= 1.5).sum()),
        "mfe_close_ge_2.0R": int((g["mfe_close_R"] >= 2.0).sum()),
        "mfe_close_ge_2.9R": int((g["mfe_close_R"] >= 2.9).sum()),
        "mfe_close_ge_3.0R": int((g["mfe_close_R"] >= 3.0).sum()),
        "mfe_wick_ge_3.0R": int((g["mfe_R"] >= 3.0).sum()),
        "mfe_close_median": round(float(g["mfe_close_R"].median()), 3),
        "sky_r_purple_median": round(float(g["sky_r_purple"].median()), 2),
        "sky_r_purple_lt_3": int((g["sky_r_purple"] < 3.0).sum()),
        "disp_mid_true": int(g["disp_mid"].fillna(False).astype(bool).sum()),
        "risk_pct_median": round(float(g["risk_pct"].median()), 4),
    }


def verdict(df: pd.DataFrame, label: str) -> dict:
    """Evaluate the five mandatory asserts on a (possibly filtered) frame."""
    w = df[df["class"] == "WIN"]
    b = df[df["class"] == "BE"]
    l = df[df["class"] == "LOSS"]
    decided = len(w) + len(l)
    wr = len(w) / decided if decided else 0.0
    yearly = df["y"].value_counts().to_dict()
    ge4 = int((w["R"] >= 4.0).sum())
    maxr = float(w["R"].max()) if len(w) else 0.0
    minr = float(w["R"].min()) if len(w) else 0.0
    # loss streak on the kept sequence, chronological (BE resets, as in v25)
    st = worst = 0
    for c in df.sort_values("t")["class"]:
        if c == "LOSS":
            st += 1
            worst = max(worst, st)
        else:
            st = 0
    return {
        "label": label,
        "total": len(df), "W": len(w), "BE": len(b), "L": len(l),
        "WR_decided_pct": round(100 * wr, 2),
        "min_winner_R": round(minr, 2), "runners_ge4R": ge4,
        "max_winner_R": round(maxr, 2), "max_consec_losses": worst,
        "yearly": {y: int(yearly.get(y, 0)) for y in YEARS},
        "A1_WR>=60": bool(wr >= 0.60),
        "A2_minR>=3": bool(minr >= 3.00 - 1e-6),
        "A3_runners": bool(ge4 >= 5 and maxr >= 6.0),
        "A4_streak<=3": bool(worst <= 3),
        "A5_volume": bool(len(df) >= 150 and
                          all(int(yearly.get(y, 0)) >= 12 for y in YEARS)),
        "net_pnl_usd": round(float(df["net_pnl"].sum()), 2),
    }


def main() -> None:
    df = load()
    rep: dict = {"source": str(CSV), "rows": len(df)}

    # ---------------- Q-B: the four cohorts ---------------------------- #
    win = df[df["class"] == "WIN"]
    be = df[df["class"] == "BE"]
    loss = df[df["class"] == "LOSS"]
    loss_mid = loss[loss["disp_mid"].fillna(False).astype(bool)]
    loss_nomid = loss[~loss["disp_mid"].fillna(False).astype(bool)]
    be_mid = be[be["disp_mid"].fillna(False).astype(bool)]

    rep["cohorts"] = {
        "WIN": cohort_stats(win),
        "BE_all": cohort_stats(be),
        "BE_crossed_mid": cohort_stats(be_mid),
        "LOSS_crossed_mid": cohort_stats(loss_mid),
        "LOSS_never_crossed_mid": cohort_stats(loss_nomid),
    }
    print("=" * 78)
    print("Q-B  HOW FAR DID EACH COHORT TRAVEL BEFORE IT DIED?  (mfe on CLOSES)")
    print("=" * 78)
    hdr = f"{'cohort':26s}{'n':>4}{'>=1R':>6}{'>=1.5R':>8}{'>=2R':>6}" \
          f"{'>=2.9R':>8}{'>=3R':>6}{'med':>7}{'skyRtop':>9}{'top<3R':>8}"
    print(hdr)
    for k, v in rep["cohorts"].items():
        if v["n"] == 0:
            print(f"{k:26s}{0:>4}")
            continue
        print(f"{k:26s}{v['n']:>4}{v['mfe_close_ge_1.0R']:>6}"
              f"{v['mfe_close_ge_1.5R']:>8}{v['mfe_close_ge_2.0R']:>6}"
              f"{v['mfe_close_ge_2.9R']:>8}{v['mfe_close_ge_3.0R']:>6}"
              f"{v['mfe_close_median']:>7}{v['sky_r_purple_median']:>9}"
              f"{v['sky_r_purple_lt_3']:>8}")

    # ---------------- Q-A: the dealing-range geometry ------------------ #
    print()
    print("=" * 78)
    print("Q-A  WHERE IS THE TOP OF THE 4H DEALING RANGE, IN R, AT THE ENTRY?")
    print("=" * 78)
    for lo, hi in [(0, 1), (1, 2), (2, 3), (3, 5), (5, 10), (10, 1e9)]:
        g = df[(df["sky_r_purple"] >= lo) & (df["sky_r_purple"] < hi)]
        if not len(g):
            print(f"  top in [{lo},{hi})R : n=0")
            continue
        w = (g["class"] == "WIN").sum(); l = (g["class"] == "LOSS").sum()
        b = (g["class"] == "BE").sum()
        print(f"  top in [{lo:>4},{hi if hi<1e9 else 'inf':>4})R : n={len(g):>3} "
              f"W={w:>3} BE={b:>3} L={l:>3}  WR_decided="
              f"{100*w/(w+l) if (w+l) else 0:>5.1f}%  "
              f"maxR={g.loc[g['class']=='WIN','R'].max() if w else 0:>6.2f}")
    rep["sky_r_purple_nan"] = int(df["sky_r_purple"].isna().sum())

    # ---------------- Q-C: candidate v26 rule sets --------------------- #
    print()
    print("=" * 78)
    print("Q-C  CANDIDATE RULE SETS, SCORED ON REAL v25 OUTCOMES")
    print("     [PRE-ENTRY] = causal gate, shippable as-is")
    print("     [PATH]      = exit-rule change, UPPER BOUND (winner destruction")
    print("                   from an earlier shield is NOT modelled)")
    print("=" * 78)
    rows = [verdict(df, "v25 baseline (as shipped)")]

    # --- PRE-ENTRY geometric gates on the dealing-range top -------------
    for thr in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        rows.append(verdict(df[df["sky_r_purple"] >= thr],
                            f"[PRE-ENTRY] range top >= {thr}R"))
    # --- PRE-ENTRY: the entry must sit in the deep discount of the range
    for thr in (0.25, 0.33, 0.40):
        rows.append(verdict(df[df["nar_range_pos_4h"] <= thr],
                            f"[PRE-ENTRY] range_pos_4h <= {thr}"))
    # --- PATH: arm the BE shield at the mid-cross alone (no BOS wait) ---
    d = df.copy()
    m = (d["class"] == "LOSS") & d["disp_mid"].fillna(False).astype(bool)
    d.loc[m, "class"] = "BE"
    rows.append(verdict(d, "[PATH] BE armed at mid-cross alone"))

    # --- PATH: arm the shield at +1.0R / +1.5R on closes ---------------
    for r in (1.0, 1.5, 2.0):
        d = df.copy()
        m = (d["class"] == "LOSS") & (d["mfe_close_R"] >= r)
        d.loc[m, "class"] = "BE"
        rows.append(verdict(d, f"[PATH] BE armed at +{r}R (closes)"))

    # --- PATH: the lock line moved to the range top when it is < 3R -----
    # i.e. "delivery complete" pays +sky_r_purple instead of nothing
    d = df.copy()
    m = ((d["class"].isin(["BE", "LOSS"])) & (d["mfe_close_R"] >= 2.9)
         & (d["sky_r_purple"] >= 2.9))
    d.loc[m, "class"] = "WIN"
    d.loc[m, "R"] = 3.0
    rows.append(verdict(d, "[PATH] trades that touched +2.9R paid as +3R"))

    # --- combinations ---------------------------------------------------
    for thr in (2.0, 3.0):
        for r in (1.0, 1.5):
            d = df[df["sky_r_purple"] >= thr].copy()
            m = (d["class"] == "LOSS") & (d["mfe_close_R"] >= r)
            d.loc[m, "class"] = "BE"
            rows.append(verdict(d, f"[PRE+PATH] top>={thr}R & BE at +{r}R"))

    rep["variants"] = rows
    hdr = (f"{'variant':48s}{'n':>4}{'W':>4}{'BE':>4}{'L':>4}"
           f"{'WR%':>7}{'>=4R':>5}{'maxR':>7}{'stk':>4}{'ymin':>5}"
           f"{'A1':>3}{'A2':>3}{'A3':>3}{'A4':>3}{'A5':>3}{'pass':>5}")
    print(hdr)
    for v in rows:
        ymin = min(v["yearly"][y] for y in YEARS)
        npass = sum([v["A1_WR>=60"], v["A2_minR>=3"], v["A3_runners"],
                     v["A4_streak<=3"], v["A5_volume"]])
        flag = lambda b: "Y" if b else "."   # noqa: E731
        print(f"{v['label'][:47]:48s}{v['total']:>4}{v['W']:>4}{v['BE']:>4}"
              f"{v['L']:>4}{v['WR_decided_pct']:>7}{v['runners_ge4R']:>5}"
              f"{v['max_winner_R']:>7}{v['max_consec_losses']:>4}{ymin:>5}"
              f"{flag(v['A1_WR>=60']):>3}{flag(v['A2_minR>=3']):>3}"
              f"{flag(v['A3_runners']):>3}{flag(v['A4_streak<=3']):>3}"
              f"{flag(v['A5_volume']):>3}{npass:>4}/5")

    best = max(rows, key=lambda v: (
        sum([v["A1_WR>=60"], v["A2_minR>=3"], v["A3_runners"],
             v["A4_streak<=3"], v["A5_volume"]]), v["WR_decided_pct"]))
    rep["best"] = best
    print()
    print("BEST VARIANT:", json.dumps(best, indent=2))

    # ---------------- what the arithmetic actually requires ------------ #
    print()
    print("=" * 78)
    print("THE CORRECTED ARITHMETIC (v25's report claimed '90 winners needed')")
    print("=" * 78)
    print("  decided = WIN + LOSS        (BE excluded)   <- verified in code")
    print("  total   = WIN + LOSS + BE   (BE included)   <- assert 5 floor 150")
    w, b, l = len(win), len(be), len(loss)
    print(f"  v25 today: {w}W / {b}BE / {l}L  -> WR = {w}/{w+l} = "
          f"{100*w/(w+l):.2f}%   total = {w+b+l}")
    need_l = int(w / 0.60 - w)  # losses allowed at the current win count
    print(f"  keeping all {w} winners, WR>=60% needs losses <= {need_l}"
          f"  (i.e. convert {l-need_l} of {l} losses to BE/WIN)")
    print(f"  ...and total stays >= 150 because the converted trades are")
    print(f"      still counted: {w} + {need_l} + {b + (l-need_l)} = "
          f"{w + need_l + b + (l-need_l)}")
    rep["arithmetic"] = {"wins": w, "be": b, "losses": l,
                         "losses_allowed_at_60pct": need_l,
                         "losses_to_convert": l - need_l}

    OUT_JSON.write_text(json.dumps(rep, indent=2, default=str))
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"\nwritten: {OUT_JSON}\nwritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
