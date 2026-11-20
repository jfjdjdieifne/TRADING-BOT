#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v24_search.py — exhaustive, honest search over the counterfactual
classes produced by audit_v24_shield.py.

For every (pre-entry gate x shield arm rule) pair it evaluates ALL FIVE
mandatory asserts on the v24 trade population, in entry-time order
(so the consecutive-loss streak is real, not approximate):

  1 WR = WIN/(WIN+LOSS) >= 0.60
  2 min winner >= +3.00R net
  3 runners >= 4R  >= 5  AND  max winner >= 6.0R
  4 max consecutive losses <= 3
  5 total >= 150 AND every year 2021..2025 >= 12

Only sanctioned constants are used to build the gates: 3R/6R/10R (the
user's own target ladder), 25% (bottom quarter), 50% (mid), plus purely
structural booleans (demand membership, liquidity raids, unicorn
overlap, inversion FVG, order-flow direction).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parent / "results"
RULES = ["NONE", "A0.25", "A0.5", "A0.75", "A1", "A1.5", "A2",
         "MID", "BOS", "MID+BOS", "MID+A1", "BOS+A1"]


def streak_of(cls, be_resets=True):
    """Consecutive TRUE losses. A scratch is not a loss; with
    BE_RELEASES_STREAK (v24's measured fix, kept in v25) it also resets
    the count. The conservative variant (be_resets=False) is reported
    too, so the assert is checked under BOTH readings."""
    best = cur = 0
    for c in cls:
        if c == "LOSS":
            cur += 1
            best = max(best, cur)
        elif c == "WIN" or (be_resets and c == "BE"):
            cur = 0
    return best


def main():
    A = pd.read_csv(RESULTS / "audit_v24_shield.csv")
    A["entry_time"] = pd.to_datetime(A["entry_time"])
    A["yr"] = A["entry_time"].dt.year.astype(str)
    A = A.sort_values("entry_time").reset_index(drop=True)
    for c in ("wall_r_4h", "wall_r_1h", "range_pos_4h", "range_pos_1h",
              "ifvg_r_4h", "unicorn_exec_depth_r"):
        A[c] = pd.to_numeric(A[c], errors="coerce")

    T = pd.Series(True, index=A.index)
    atoms = {
        "q4": A["range_pos_4h"] <= 0.25,            # 4H bottom quarter
        "h4": A["range_pos_4h"] <= 0.50,            # 4H bottom half
        "sky3": A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 3),
        "sky6": A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 6),
        "sky10": A["wall_r_4h"].isna() | (A["wall_r_4h"] >= 10),
        "dem4": A["in_demand_4h"].astype(bool),
        "dem1": A["in_demand_1h"].astype(bool),
        "noraid4": ~A["raid_high_4h"].astype(bool),
        "noraid1": ~A["raid_high_1h"].astype(bool),
        "raidlow1": A["raid_low_1h"].astype(bool),
        "flow4b": A["flow_4h"] == "BULL",
        "flow4r": A["flow_4h"] == "BEAR",
        "uni_any": (A["unicorn_4h"].astype(bool)
                    | A["unicorn_1h"].astype(bool)
                    | A["unicorn_exec"].astype(bool)),
        "stopdem4": A["stop_in_demand_4h"].astype(bool),
        "stopblue4": A["stop_in_htf_blue_4h"].astype(bool),
        "ifvg4": A["ifvg_r_4h"].notna(),
    }
    # candidate gate sets: singles, pairs and a few triples
    gates = {"ALL": T}
    for k, v in atoms.items():
        gates[k] = v.fillna(False)
    for (k1, v1), (k2, v2) in itertools.combinations(atoms.items(), 2):
        gates[f"{k1}&{k2}"] = (v1.fillna(False) & v2.fillna(False))
    for trip in (("q4", "sky6", "dem4"), ("q4", "sky10", "dem4"),
                 ("q4", "sky6", "noraid4"), ("q4", "sky10", "noraid4"),
                 ("h4", "sky6", "dem4"), ("q4", "sky6", "stopdem4"),
                 ("q4", "sky10", "dem4"), ("q4", "sky6", "uni_any"),
                 ("q4", "sky10", "flow4r"), ("q4", "sky6", "flow4r")):
        m = T.copy()
        for name in trip:
            m = m & atoms[name].fillna(False)
        gates["&".join(trip)] = m

    rows = []
    for gname, gm in gates.items():
        k = A[gm]
        if len(k) < 40:
            continue
        for rule in RULES:
            cls = k[f"cls_{rule}"].tolist()
            R = k[f"R_{rule}"].astype(float)
            w = cls.count("WIN"); l = cls.count("LOSS")
            wr = w / max(w + l, 1)
            winR = R[[c == "WIN" for c in cls]]
            minw = float(winR.min()) if len(winR) else 0.0
            maxw = float(winR.max()) if len(winR) else 0.0
            run4 = int((winR >= 4 - 1e-9).sum())
            st = streak_of(cls, True)
            st_c = streak_of(cls, False)
            yrs = k.groupby("yr").size().to_dict()
            a = {
                1: wr >= 0.60,
                2: minw >= 3.00 - 1e-6,
                3: run4 >= 5 and maxw >= 6.0,
                4: st <= 3 and st_c <= 3,
                5: len(k) >= 150 and all(yrs.get(str(y), 0) >= 12
                                         for y in range(2021, 2026)),
            }
            rows.append({"gate": gname, "rule": rule, "n": len(k),
                         "W": w, "L": l, "BE": cls.count("BE"),
                         "WR": round(wr, 4), "minW": round(minw, 2),
                         "maxW": round(maxw, 2), "run4": run4,
                         "streak": st, "streak_conservative": st_c,
                         "passed": sum(a.values()),
                         "a1": a[1], "a5": a[5],
                         "yearly": {str(x): int(y) for x, y in yrs.items()}})

    R = pd.DataFrame(rows)
    R.to_csv(RESULTS / "audit_v24_search.csv", index=False)
    print(f"[search] {len(R)} (gate x rule) combinations evaluated")

    print("\n===== TOP 20 BY NUMBER OF ASSERTS PASSED, THEN WR =====")
    top = R.sort_values(["passed", "WR", "n"],
                        ascending=[False, False, False]).head(20)
    for _, r in top.iterrows():
        print(f"  pass={r['passed']}/5 a1={str(r['a1'])[0]} a5={str(r['a5'])[0]} "
              f"gate={r['gate']:22} rule={r['rule']:8} n={r['n']:3} "
              f"W={r['W']:3} L={r['L']:3} BE={r['BE']:3} WR={r['WR']:6.1%} "
              f"minW={r['minW']:5.2f} maxW={r['maxW']:6.2f} run4={r['run4']:2} "
              f"streak={r['streak']}")

    print("\n===== HIGHEST WR AMONG COMBOS THAT PASS ASSERT 5 =====")
    a5 = R[R["a5"]].sort_values("WR", ascending=False).head(12)
    for _, r in a5.iterrows():
        print(f"  gate={r['gate']:22} rule={r['rule']:8} n={r['n']:3} "
              f"WR={r['WR']:6.1%} W={r['W']:3} L={r['L']:3} BE={r['BE']:3} "
              f"run4={r['run4']:2} maxW={r['maxW']:6.2f} streak={r['streak']} "
              f"yearly={r['yearly']}")

    print("\n===== HIGHEST WR OVERALL (assert 5 ignored) =====")
    for _, r in R.sort_values("WR", ascending=False).head(12).iterrows():
        print(f"  gate={r['gate']:22} rule={r['rule']:8} n={r['n']:3} "
              f"WR={r['WR']:6.1%} run4={r['run4']:2} a5={str(r['a5'])[0]} "
              f"yearly={r['yearly']}")

    print("\n===== ANY COMBO PASSING ALL FIVE? =====")
    full = R[R["passed"] == 5]
    print(f"  {len(full)} combinations pass 5/5")
    if len(full):
        print(full.to_string(index=False))
    with open(RESULTS / "audit_v24_search.json", "w") as f:
        json.dump({"n_combos": len(R),
                   "best_by_passes": top.to_dict("records"),
                   "best_assert5": a5.to_dict("records"),
                   "all_five": full.to_dict("records")},
                  f, indent=2, default=str)


if __name__ == "__main__":
    main()
