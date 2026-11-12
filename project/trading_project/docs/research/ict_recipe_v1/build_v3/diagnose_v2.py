#!/usr/bin/env python3
"""Stage 1 diagnosis: counting only, from the SAVED v2 outputs and the verified 5m file.

No engine is imported for settlement: `replay()` below is written here, from candles, for both the
v2 convention (every level on the bid) and the side-correct convention (buy at ask, sell at bid).
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "build_v1"))
from stream_v1 import load_bars                                        # noqa: E402

UTC = timezone.utc
DATA = Path("/tmp/hud_data/2021.csv.gz")
DATA_SHA256 = "38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4"
RUNS = ["2021-06_v1", "2021-06_V2-0", "2021-06_V2-A", "2021-06_V2-B",
        "2021-07_v1", "2021-07_V2-0", "2021-07_V2-A", "2021-07_V2-B",
        "2021-07_V2-A-OFF", "2021-07_V2-B-OFF",
        "2021-09_v1", "2021-09_V2-0", "2021-09_V2-A", "2021-09_V2-B",
        "2021-09_V2-A-OFF", "2021-09_V2-B-OFF"]
MONTH_END = {"2021-06": "2021-07-01", "2021-07": "2021-08-01", "2021-09": "2021-10-01",
             "2021-10": "2021-11-01"}
EXPIRY = 288


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def replay(plan: dict, bars: list, side_correct: bool) -> dict:
    """Independent replay.  Returns fill/exit facts for one convention."""

    direction = plan["direction"]
    entry, stop = plan["entry"], plan["stop"]
    t1 = (plan.get("t1") or {}).get("level")
    start = datetime.fromisoformat(plan["decided_at"])
    idx = next((i for i, b in enumerate(bars) if b.start == start), None)
    if idx is None:
        return {"state": "no_bars", "changed": False}
    filled = fill_i = None
    stop_i = t1_i = None
    for j in range(idx + 1, min(idx + 1 + EXPIRY, len(bars))):
        b = bars[j]
        if filled is None:
            hit_entry = (b.bid_low <= entry <= b.bid_high) if direction == "bearish" else (
                (b.ask_low <= entry <= b.ask_high) if side_correct else (b.bid_low <= entry <= b.bid_high))
            stop_first = (b.ask_high >= stop) if (side_correct and direction == "bearish") else (
                b.bid_low <= stop if (side_correct and direction == "bullish") else
                (b.bid_high >= stop if direction == "bearish" else b.bid_low <= stop))
            if hit_entry:
                filled, fill_i = entry, j
            elif stop_first:
                return {"state": "cancelled", "changed": False, "fill_index": None}
            else:
                continue
        b = bars[j]
        stop_hit = (b.ask_high >= stop) if (side_correct and direction == "bearish") else (
            b.bid_low <= stop if (side_correct and direction == "bullish") else
            (b.bid_high >= stop if direction == "bearish" else b.bid_low <= stop))
        if stop_hit:
            stop_i = j
            break
        if t1 is not None:
            t1_hit = (b.ask_low <= t1) if (side_correct and direction == "bearish") else (
                b.bid_high >= t1 if (side_correct and direction == "bullish") else
                (b.bid_low <= t1 if direction == "bearish" else b.bid_high >= t1))
            if t1_hit:
                t1_i = j
                break
    risk = abs(entry - stop)
    if filled is None:
        return {"state": "expired", "changed": False, "fill_index": None}
    if stop_i is not None:
        gross = (entry - stop) if direction == "bearish" else (stop - entry)
        return {"state": "stop", "r": (gross - 0.00001) / risk, "fill_index": fill_i, "changed": False}
    if t1_i is not None:
        gross = (entry - t1) if direction == "bearish" else (t1 - entry)
        return {"state": "t1", "r": (gross - 0.00001) / risk, "fill_index": fill_i, "changed": False}
    return {"state": "open", "r": 0.0, "fill_index": fill_i, "changed": False}


def main() -> None:
    if sha(DATA) != DATA_SHA256:
        raise SystemExit("data hash mismatch")
    out = {"data_sha256": DATA_SHA256, "runs": {}, "totals": {}}
    bars_by_month = {}
    for month in ("2021-06", "2021-07", "2021-09"):
        bars_by_month[month] = load_bars(DATA, f"{month}-01T00:00:00+00:00",
                                         datetime.fromisoformat(MONTH_END[month]).isoformat() + "+00:00")

    agg = {"plans": 0, "side_changed": 0, "stale": 0, "armed_inside": 0, "t2_same": 0,
           "t2_present": 0, "geom_behind": 0, "zone_outside_range": 0, "range_after_zone": "NOT_RECOVERABLE",
           "delta_r_sum": {"bullish": 0.0, "bearish": 0.0},
           "delta_r_n": {"bullish": 0, "bearish": 0}, "side_changed_dir": {"bullish": 0, "bearish": 0},
           "clean_sum": {}, "clean_n": {}}

    for run in RUNS:
        path = Path("/tmp/build_v2") / run / "plans_final.jsonl"
        if not path.exists():
            continue
        month = run[:7]
        bars = bars_by_month[month]
        plans = [json.loads(x) for x in path.read_text().splitlines()]
        stat = {"plans": len(plans), "side_changed": 0, "stale": 0, "armed_inside": 0,
                "t2_same": 0, "t2_present": 0, "geom_behind": 0, "zone_outside_range": 0,
                "delta_r": {"bullish": [], "bearish": []}}
        stat["validation_match"] = 0
        stat["validation_mismatch"] = 0
        stat["sub_pip_risk"] = 0
        stat["delta_r_clean"] = {"bullish": [], "bearish": []}
        for plan in plans:
            agg["plans"] += 1
            a = replay(plan, bars, side_correct=False)
            b = replay(plan, bars, side_correct=True)
            risk_pips = abs(plan["entry"] - plan["stop"]) * 10000.0
            if risk_pips < 1.0:
                stat["sub_pip_risk"] += 1
                agg["sub_pip_risk"] = agg.get("sub_pip_risk", 0) + 1
            if plan.get("state", "").startswith("settled") and plan.get("r_measured") is not None \
                    and a.get("r") is not None:
                if abs(a["r"] - plan["r_measured"]) < 0.05:
                    stat["validation_match"] += 1
                else:
                    stat["validation_mismatch"] += 1
                    agg["validation_mismatch"] = agg.get("validation_mismatch", 0) + 1
            if a["state"] != b["state"]:
                stat["side_changed"] += 1
                agg["side_changed"] += 1
                agg["side_changed_dir"][plan["direction"]] += 1
            if a.get("r") is not None and b.get("r") is not None:
                if risk_pips >= 1.0:
                    stat["delta_r_clean"][plan["direction"]].append(b["r"] - a["r"])
                    agg["clean_sum"][plan["direction"]] = agg["clean_sum"].get(plan["direction"], 0.0) + (b["r"] - a["r"])
                    agg["clean_n"][plan["direction"]] = agg["clean_n"].get(plan["direction"], 0) + 1
                stat["delta_r"][plan["direction"]].append(b["r"] - a["r"])
                agg["delta_r_sum"][plan["direction"]] += b["r"] - a["r"]
                agg["delta_r_n"][plan["direction"]] += 1

            # 1b stale: the stop side was taken before the first bar that traded at the entry
            start = datetime.fromisoformat(plan["decided_at"])
            idx = next((i for i, x in enumerate(bars) if x.start == start), None)
            if idx is not None:
                direction, entry, stop = plan["direction"], plan["entry"], plan["stop"]
                for j in range(idx + 1, min(idx + 1 + EXPIRY, len(bars))):
                    bar = bars[j]
                    touched = bar.bid_low <= entry <= bar.bid_high if direction == "bearish" else \
                        bar.ask_low <= entry <= bar.ask_high
                    stop_hit = bar.ask_high >= stop if direction == "bearish" else bar.bid_low <= stop
                    if touched:
                        break
                    if stop_hit:
                        stat["stale"] += 1
                        agg["stale"] += 1
                        break

            # 1c armed inside: the arming bar already closed past the entry edge into the zone
            if idx is not None:
                bar = bars[idx]
                zone = plan.get("zone") or {}
                edge = zone.get("upper") if plan["direction"] == "bullish" else zone.get("lower")
                if edge is not None:
                    inside = bar.bid_close > edge if plan["direction"] == "bearish" else bar.bid_close < edge
                    if inside:
                        stat["armed_inside"] += 1
                        agg["armed_inside"] += 1

            # 1d T2 identity
            t2 = plan.get("t2")
            if t2:
                stat["t2_present"] += 1
                agg["t2_present"] += 1
                if plan.get("t1") and abs(t2["level"] - plan["t1"]["level"]) < 1e-12:
                    stat["t2_same"] += 1
                    agg["t2_same"] += 1

            # 1e T1 behind the entry
            t1 = (plan.get("t1") or {}).get("level")
            if t1 is not None:
                behind = t1 <= plan["entry"] if plan["direction"] == "bullish" else t1 >= plan["entry"]
                if behind:
                    stat["geom_behind"] += 1
                    agg["geom_behind"] += 1

            # 1f zone outside its dealing range
            rg = plan.get("range") or {}
            zone = plan.get("zone") or {}
            if rg.get("low") is not None and rg.get("high") is not None and zone:
                if zone["lower"] < rg["low"] or zone["upper"] > rg["high"]:
                    stat["zone_outside_range"] += 1
                    agg["zone_outside_range"] += 1
        stat["delta_r_mean"] = {k: (sum(v) / len(v) if v else None) for k, v in stat["delta_r"].items()}
        stat["delta_r_mean_clean"] = {k: (sum(v) / len(v) if v else None)
                                      for k, v in stat["delta_r_clean"].items()}
        del stat["delta_r"], stat["delta_r_clean"]
        out["runs"][run] = stat

    out["totals"]["delta_r_mean"] = {k: (agg["delta_r_sum"][k] / agg["delta_r_n"][k]
                                         if agg["delta_r_n"][k] else None)
                                     for k in ("bullish", "bearish")}
    out["totals"]["delta_r_n"] = agg["delta_r_n"]
    for key in ("plans", "side_changed", "stale", "armed_inside", "t2_same", "t2_present",
                "geom_behind", "zone_outside_range"):
        out["totals"][key] = agg[key]
    out["totals"]["side_changed_dir"] = agg["side_changed_dir"]
    out["totals"]["delta_r_mean_clean"] = {k: (agg["clean_sum"][k] / agg["clean_n"][k]
                                               if agg["clean_n"].get(k) else None)
                                           for k in ("bullish", "bearish")}
    out["totals"]["delta_r_n_clean"] = agg["clean_n"]
    (HERE / "DIAGNOSIS_V2.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["totals"], indent=1))


if __name__ == "__main__":
    main()
