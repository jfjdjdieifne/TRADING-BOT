#!/usr/bin/env python3
"""Stage 6.3-6.7: WIDE feature audit, excursion curves, sweep event study, hour-of-day, hygiene.

All computation here is from saved run outputs plus the verified 5m file; no variant is re-run.
"""

from __future__ import annotations

import json
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "build_v1"))
import v3_core as C                                                   # noqa: E402
from stream_v1 import load_bars                                        # noqa: E402

UTC = timezone.utc
ROOT = Path("/tmp/build_v3")
OUT = HERE / "REPORT_V3"
DATA = Path("/tmp/hud_data/2021.csv.gz")
SEED = 20261109
K_GRID = (0.25, 0.5, 1.0, 2.0, 3.0)
MONTH_END = {"2021-11": "2021-12-01", "2021-10": "2021-11-01",
             "2021-06": "2021-07-01", "2021-07": "2021-08-01", "2021-09": "2021-10-01"}


def load(path: Path) -> list[dict]:
    path = path / "plans_final.jsonl" if path.is_dir() else path
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def excess(plan: dict) -> float | None:
    rr = plan.get("rr_t1")
    if rr is None or rr <= 0:
        return None
    return (1 if plan.get("exit_reason") == "t1_touched" else 0) - 1.0 / (1.0 + rr)


def perm_diff(split: dict[bool, list[float]], keyed: list[tuple[bool, float]], n_perm=10000) -> dict:
    a = split.get(True, [])
    b = split.get(False, [])
    if not a or not b:
        return {"n_yes": len(a), "n_no": len(b), "diff": None, "p": None}
    observed = sum(a) / len(a) - sum(b) / len(b)
    rng = random.Random(SEED)
    values = [v for _, v in keyed]
    idx = list(range(len(values)))
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(idx)
        yes = [values[i] for i in idx[:len(a)]]
        no = [values[i] for i in idx[len(a):len(a) + len(b)]]
        diff = sum(yes) / len(yes) - sum(no) / len(no)
        if observed >= 0 and diff >= observed:
            hits += 1
        elif observed < 0 and diff <= observed:
            hits += 1
    return {"n_yes": len(a), "n_no": len(b), "diff": observed, "p": (hits + 1) / (n_perm + 1)}


def holm(pairs: list[tuple[str, float]]) -> dict:
    ordered = sorted(pairs, key=lambda kv: kv[1])
    m = len(ordered)
    out, running = {}, 0.0
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * p))
        out[name] = running
    return out


def wide_features() -> dict:
    result = {}
    for month in ("2021-11", "2021-10"):
        for frame in ("15m", "1h"):
            plans = [p for p in load(ROOT / f"{month}_WIDE_{frame}") if p.get("state") == "settled"]
            features = {
                "sweep_zone": lambda p: p["zone"]["kind"] == "sweep_level",
                "d_new_yes": lambda p: p["d_new"]["answer"] == "YES",
                "d_old_yes": lambda p: p["d_old"]["answer"] == "YES",
                "fresh_zone": lambda p: bool(p["zone"]["fresh"]),
                "bias_agrees": lambda p: bool(p["zone"]["bias_agrees"]),
                "in_window": lambda p: bool(p["session"]["in_window"]),
                "premium_discount_ok": lambda p: p["gates"]["position"],
                "t1_external": lambda p: (p.get("t1") or {}).get("class") == "EXTERNAL",
                "bullish": lambda p: p["direction"] == "bullish",
                "risk_above_month_median": None,   # filled below
            }
            pips = [p["stop_pips"] for p in plans if p.get("stop_pips")]
            if pips:
                med = statistics.median(pips)
                features["risk_above_month_median"] = (lambda m: (lambda p: p["stop_pips"] > m))(med)
            for name, fn in features.items():
                keyed, split = [], {True: [], False: []}
                for plan in plans:
                    value = excess(plan)
                    if value is None or fn is None:
                        continue
                    flag = bool(fn(plan))
                    keyed.append((flag, value))
                    split[flag].append(value)
                row = perm_diff(split, keyed)
                row["month"], row["frame"], row["feature"] = month, frame, name
                result[f"{month}|{frame}|{name}"] = row
    tests = [(k, v["p"]) for k, v in result.items() if v.get("p") is not None]
    adjusted = holm(tests)
    for key, value in adjusted.items():
        result[key]["p_holm"] = value
    return result


def excursion() -> dict:
    """6.4: share of filled WIDE plans that reach k*r before the stop (r = the plan's own risk)."""

    out = {}
    for month in ("2021-11", "2021-10"):
        # fill_index counts 5m bars from the run's history start (2021-01-01), so the same array is used
        end = datetime.fromisoformat(MONTH_END[month]).replace(tzinfo=UTC)
        bars = load_bars(DATA, "2021-01-01T00:00:00+00:00", end.isoformat())
        month_bars = load_bars(DATA, f"{month}-01T00:00:00+00:00", end.isoformat())
        offset = len(bars) - len(month_bars)
        for frame in ("15m", "1h"):
            plans = [p for p in load(ROOT / f"{month}_WIDE_{frame}") if p.get("fill_index") is not None]
            reaches = {k: 0 for k in K_GRID}
            n = 0
            for plan in plans:
                idx = plan["fill_index"] - offset
                risk = abs(plan["entry"] - plan["stop"])
                if risk <= 0:
                    continue
                n += 1
                best = 0.0
                for j in range(idx + 1, min(idx + 289, len(month_bars))):
                    bar = month_bars[j]
                    if plan["direction"] == "bearish":
                        best = max(best, plan["entry"] - bar.bid_low)
                        stop = bar.ask_high >= plan["stop"]
                    else:
                        best = max(best, bar.bid_high - plan["entry"])
                        stop = bar.bid_low <= plan["stop"]
                    if stop:
                        break
                for k in K_GRID:
                    if best >= k * risk:
                        reaches[k] += 1
            out[f"{month}|{frame}"] = {"n": n,
                                       "share": {str(k): (reaches[k] / n if n else None) for k in K_GRID},
                                       "random_walk": {str(k): 1.0 / (1.0 + k) for k in K_GRID}}
    return out


def sweep_study() -> dict:
    """6.5: setup-frame sweep events over the whole month stream.  Mid prices, spread ignored."""

    out = {}
    for month in ("2021-11", "2021-10"):
        start = datetime.fromisoformat(f"{month}-01T00:00:00+00:00")
        end = datetime.fromisoformat(MONTH_END[month]).replace(tzinfo=UTC)
        bars = load_bars(DATA, start.isoformat(), end.isoformat())
        for frame_label in ("15m", "1h"):
            state = C.FrameV3(frame_label)
            candles, events = [], []
            for bar in bars:
                closed = state.push(bar)
                if closed is None:
                    continue
                candles.append({"open": closed.bid_open, "high": closed.bid_high,
                                "low": closed.bid_low, "close": closed.bid_close,
                                "mid_high": (closed.bid_high + closed.ask_high) / 2.0,
                                "mid_low": (closed.bid_low + closed.ask_low) / 2.0,
                                "mid_close": (closed.bid_close + closed.ask_close) / 2.0})
                if state.last:
                    for side, key in (("high", "sweep_high"), ("low", "sweep_low")):
                        if state.last[key].get("answer") == "YES":
                            events.append({"index": len(candles) - 1, "side": side})
            reaches = {k: 0 for k in K_GRID}
            for event in events:
                i, side = event["index"], event["side"]
                candle = candles[i]
                extreme = candle["mid_high"] if side == "high" else candle["mid_low"]
                close = candle["mid_close"]
                u = abs(extreme - close)
                if u <= 0:
                    continue
                best = 0.0
                for j in range(i + 1, min(i + 289, len(candles))):
                    nxt = candles[j]
                    if side == "high":
                        best = max(best, close - nxt["mid_low"])
                        if nxt["mid_high"] > extreme:
                            break
                    else:
                        best = max(best, nxt["mid_high"] - close)
                        if nxt["mid_low"] < extreme:
                            break
                for k in K_GRID:
                    if best >= k * u:
                        reaches[k] += 1
            n = len(events)
            out[f"{month}|{frame_label}"] = {
                "events": n,
                "share": {str(k): (reaches[k] / n if n else None) for k in K_GRID},
                "random_walk": {str(k): 1.0 / (1.0 + k) for k in K_GRID}}
    return out


def hour_table() -> dict:
    out = {}
    for month in ("2021-11", "2021-10"):
        for frame in ("15m", "1h"):
            for variant in ("V3-0", "WIDE"):
                plans = load(ROOT / f"{month}_{variant}_{frame}")
                buckets: dict[int, list[float]] = {}
                for plan in plans:
                    if plan.get("state") != "settled":
                        continue
                    hour = int(plan["decided_at"][11:13])
                    buckets.setdefault(hour, []).append(plan["r_measured"])
                out[f"{month}|{frame}|{variant}"] = {
                    str(h): {"n": len(v), "mean_r": sum(v) / len(v)} for h, v in sorted(buckets.items())}
    return out


def hygiene_effect() -> dict:
    """6.7: V2 saved results versus V3-0 on 2021-06/07/09, paired by thesis id.  IN_SAMPLE."""

    out = {}
    for month in ("2021-06", "2021-07", "2021-09"):
        for frame, v2runs in (("15m", ("V2-A", "V2-0")), ("1h", ("V2-B", "V2-0"))):
            v3 = {p["thesis_id"]: p for p in load(ROOT / f"{month}_V3-0_{frame}")}
            for v2name in v2runs:
                v2 = {p["thesis_id"]: p for p in load(Path("/tmp/build_v2") / f"{month}_{v2name}")}
                common = sorted(set(v2) & set(v3))
                if not common:
                    continue
                deltas = []
                for key in common:
                    a, b = v2[key], v3[key]
                    if a.get("state", "").startswith("settled") and b.get("state") == "settled":
                        deltas.append(b["r_measured"] - a["r_measured"])
                out[f"{month}|{frame}|V2 {v2name} vs V3-0"] = {
                    "v2_plans": len(v2), "v3_plans": len(v3), "common": len(common),
                    "n_pairs": len(deltas),
                    "delta_r_mean": (sum(deltas) / len(deltas)) if deltas else None}
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    payload = {"features": wide_features(), "excursion": excursion(), "sweep": sweep_study(),
               "hours": hour_table(), "hygiene": hygiene_effect()}
    (OUT / "ANALYSIS_6_3_6_7.json").write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")

    lines = ["# 6.3 / 6.4 / 6.5 / 6.6 / 6.7 (generated)", "",
             "6.3 WIDE feature audit — exploratory, none of it is a claim", "```",
             f"{'feature':34s} {'n_yes':>5s} {'n_no':>5s} {'diff':>8s} {'p':>7s} {'p_holm':>7s}"]
    for key, row in payload["features"].items():
        lines.append(f"{key:34s} {row['n_yes']:5d} {row['n_no']:5d} "
                     f"{0 if row['diff'] is None else row['diff']:8.4f} "
                     f"{0 if row['p'] is None else row['p']:7.4f} "
                     f"{row.get('p_holm', 1):7.4f}")
    lines += ["```", "", "6.4 excursion curve (share reaching k*r before the stop; random walk 1/(1+k))", "```"]
    for key, row in payload["excursion"].items():
        lines.append(f"{key:14s} n={row['n']:3d}  " + "  ".join(
            f"k={k}: {row['share'][str(k)]:.3f} (rw {1/(1+k):.3f})" for k in K_GRID))
    lines += ["```", "", "6.5 sweep event study (mid prices, spread ignored)", "```"]
    for key, row in payload["sweep"].items():
        lines.append(f"{key:14s} events={row['events']:4d}  " + "  ".join(
            f"k={k}: {row['share'][str(k)]:.3f} (rw {1/(1+k):.3f})" for k in K_GRID))
    lines += ["```", "", "6.6 hour-of-day (mean R, settled plans)", "```"]
    for key, row in payload["hours"].items():
        cells = " ".join(f"{int(h):02d}h:{v['n']}/{v['mean_r']:.2f}" for h, v in row.items())
        lines.append(f"{key:26s} {cells}")
    lines += ["```", "", "6.7 hygiene effect (IN_SAMPLE, paired by thesis id)", "```"]
    for key, row in payload["hygiene"].items():
        lines.append(f"{key:40s} v2={row['v2_plans']:3d} v3={row['v3_plans']:3d} "
                     f"common={row['common']:3d} pairs={row['n_pairs']:3d} "
                     f"deltaR={0 if row['delta_r_mean'] is None else row['delta_r_mean']:.3f}")
    lines.append("```")
    (OUT / "TABLES_6_3_6_7.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"features": len(payload["features"]), "excursion": len(payload["excursion"]),
                      "sweep": len(payload["sweep"]), "hygiene": len(payload["hygiene"])}, indent=1))


if __name__ == "__main__":
    main()
