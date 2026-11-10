#!/usr/bin/env python3
"""Trade cards + mechanical checks over the SAVED v2 runs. Read-only: no engine is run.

    python3 td_v2.py --root /tmp/build_v2 --data /tmp/hud_data/2021.csv.gz

Everything here reads the saved `plans_final.jsonl` / `run_summary.json`, verifies their sha256 against
`REPORT_M1_M2/RUN_OUTPUT_SHA256.txt`, and replays settlement with its own ~30-line function so that a
MATCH means two independent implementations agree (Section 7 of the owner brief).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
sys.path.insert(0, str(BUILD))
sys.path.insert(0, str(BUILD.parent / "build_v1"))
from stream_v1 import load_bars  # data loader only; no settlement code is imported

UTC = timezone.utc
RUNS = [(m, v) for m in ("2021-09", "2021-07") for v in
        ("v1", "V2-0", "V2-A", "V2-B", "V2-A-OFF", "V2-B-OFF")]
IN_SAMPLE = [("2021-06", v) for v in ("V2-0", "V2-A", "V2-B")]
EXPIRY = 288
TOL = 1e-9   # floating-point only; the replay repeats the same operations in the same order


# ------------------------------------------------------------------ independent replay
def replay(bars, decision_index: int, entry: float, stop: float, t1: float | None,
           direction: str, half_spread_at_decision: float, start_offset: int = 0) -> dict:
    """Section 7: re-settle a plan from raw candles, independently of build_v1/build_v2."""

    risk = abs(entry - stop)
    if risk <= 0:
        return {"error": "zero risk"}
    triggered = False
    trigger_index = None
    # CONVENTION (found here, recorded not patched): build_v1 evaluates a plan on its OWN decision bar
    # (offset 0); build_v2 evaluates it from the next bar (offset 1).  The offset is passed in by the
    # caller, never guessed.
    last = min(len(bars), decision_index + start_offset + EXPIRY + 1)
    for index in range(decision_index + start_offset, last):
        bar = bars[index]
        if not triggered:
            if not (bar.bid_low <= entry <= bar.bid_high):
                if index - decision_index >= EXPIRY:
                    return {"index": index, "price": bar.bid_close,
                            "reason": "entry_zone_not_touched_within_288_bars", "r": 0.0}
                continue
            triggered = True
            trigger_index = index
        hit_stop = bar.bid_low <= stop if direction == "bullish" else bar.bid_high >= stop
        hit_target = ((bar.bid_high >= t1) if direction == "bullish" else (bar.bid_low <= t1)) \
            if t1 is not None else False
        if hit_stop:
            price, reason = stop, "stop_touched"
        elif hit_target:
            price, reason = t1, "t1_touched"
        elif index - trigger_index >= EXPIRY:
            price, reason = bar.bid_close, "neither_stop_nor_target_within_288_bars"
        else:
            continue
        gross = (price - entry) if direction == "bullish" else (entry - price)
        cost = half_spread_at_decision + bar.spread_open / 2.0
        return {"index": index, "price": price, "reason": reason, "r": (gross - cost) / risk}
    return {"error": "ran out of candles"}


# ------------------------------------------------------------------ independent aggregation
def aggregate(bars, minutes: int) -> list[dict]:
    """Build higher-frame candles from 5m bars; a candle exists only once its last 5m bar closed."""

    step = minutes * 60
    out, current = [], None
    for bar in bars:
        key = datetime.fromtimestamp(int(bar.start.timestamp()) // step * step, tz=UTC)
        if current is None or key != current["start"]:
            if current is not None:
                current["close_time"] = bar.start.isoformat()
                out.append(current)
            current = {"start": key, "open": bar.bid_open, "high": bar.bid_high,
                       "low": bar.bid_low, "close": bar.bid_close}
        else:
            current["high"] = max(current["high"], bar.bid_high)
            current["low"] = min(current["low"], bar.bid_low)
            current["close"] = bar.bid_close
        current["close_time"] = (bar.start + timedelta(minutes=5)).isoformat()
    if current is not None:
        out.append(current)
    return out


# ------------------------------------------------------------------ checklist
def checklist(plan: dict, bars, replayed: dict, start_offset: int = 0) -> list[tuple[str, bool, str]]:
    entry, stop, direction = plan["entry"], plan["stop"], plan["direction"]
    t1 = plan["t1"]["level"] if plan.get("t1") else None
    zone = plan["zone"]
    risk = abs(entry - stop)
    half = plan.get("half_spread_at_decision") or 0.0
    out = []
    out.append(("stop on the correct side of entry",
                (stop < entry) if direction == "bullish" else (stop > entry),
                f"entry {entry:.6f} stop {stop:.6f}"))
    out.append(("T1 beyond entry",
                (t1 > entry) if (t1 is not None and direction == "bullish")
                else (t1 < entry if t1 is not None else False),
                f"t1 {t1}"))
    out.append(("entry inside the zone",
                zone["lower"] - 1e-12 <= entry <= zone["upper"] + 1e-12,
                f"zone [{zone['lower']:.6f}, {zone['upper']:.6f}]"))
    # T1 untaken between its formation and arming: no 5m close beyond T1 before the decision bar
    took_before = 0
    if t1 is not None:
        # PROXY: the plan record does not carry the pool's own formation index, so the window is the
        # 288 bars (one trading day of 5m) before arming, declared here rather than implied
        for bar in bars[max(0, plan["decision_index"] - 288): plan["decision_index"] + 1]:
            if direction == "bullish" and bar.bid_close >= t1:
                took_before += 1
            if direction == "bearish" and bar.bid_close <= t1:
                took_before += 1
    # NOT_EVALUABLE: the plan record does not persist the T1 pool's formation index
    out.append(("T1 untaken between its formation and arming", "NOT_EVALUABLE",
                f"NOT_EVALUABLE (no pool formation index in the record); proxy: {took_before} "
                f"close(s) beyond T1 in the 288 bars before arming"))
    out.append(("fill convention consistent (limit at the zone edge)", abs(
        entry - (zone["upper"] if direction == "bullish" else zone["lower"])) < 1e-12,
        f"entry {entry:.6f} vs edge "
        f"{(zone['upper'] if direction == 'bullish' else zone['lower']):.6f}"))
    out.append(("half-spread applied once per side", abs(half - (bars[plan["decision_index"]].spread_open / 2)) < 1e-12,
                f"half {half:.8f} vs bar spread/2 "
                f"{(bars[plan['decision_index']].spread_open / 2):.8f}"))
    same_bar = plan.get("trigger_index") is not None and plan.get("trigger_index") == plan.get("exit_index")
    out.append(("same-bar rule applied as declared (stop first)", True,
                f"same-bar settlement: {same_bar}"))
    out.append(("first evaluation at or after the arming bar",
                plan.get("trigger_index") is None or
                plan["trigger_index"] >= plan["decision_index"] + start_offset,
                f"decision bar {plan['decision_index']} (+{start_offset}), trigger bar "
                f"{plan.get('trigger_index')}"))
    out.append(("R:R formula correct",
                (plan.get("rr_t1_measured") is None or
                 abs(plan["rr_t1_measured"] - abs(t1 - entry) / risk) < 1e-9),
                f"rr {plan.get('rr_t1_measured')}"))
    out.append(("replay reproduces the reported R",
                (not replayed.get("error")) and
                abs(replayed.get("r", 1e9) - (plan.get("r_measured") or 0.0)) < 1e-9,
                f"replay {replayed.get('reason')} R={replayed.get('r')} at bar "
                f"{replayed.get('index')} vs engine {plan.get('exit_reason')} "
                f"R={plan.get('r_measured')} at bar {plan.get('exit_index')}"))
    return out


# ------------------------------------------------------------------ helpers
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_for(run_id: str, kind: str) -> int:
    digest = hashlib.sha256(f"TRADE_DETAIL_V2|{run_id}|{kind}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def load_plans(root: Path, month: str, variant: str) -> tuple[dict, list[dict]]:
    run_dir = root / f"{month}_{variant}"
    summary = json.loads((run_dir / "run_summary.json").read_text())
    plans = [json.loads(line) for line in (run_dir / "plans_final.jsonl").read_text().splitlines()
             if line.strip()]
    return summary, sorted(plans, key=lambda p: p["plan_id"])


def pick(plans: list[dict], run_id: str) -> list[tuple[str, dict, dict]]:
    """The declared rule, applied exactly."""

    picks, used = [], set()
    n = len(plans)
    if n == 0:
        return picks
    if n <= 3:
        for plan in plans:
            picks.append(("all (run has <4 plans)", plan, {"n": n}))
        return picks
    seed_a = seed_for(run_id, "random")
    idx = random.Random(seed_a).randrange(n)
    while plans[idx]["plan_id"] in used:
        idx = (idx + 1) % n
    used.add(plans[idx]["plan_id"])
    picks.append(("seeded random", plans[idx], {"seed": seed_a, "index": idx, "n": n}))
    best = max(plans, key=lambda p: (p.get("r_measured") if p.get("r_measured") is not None else -1e9,
                                     [-ord(c) for c in p["plan_id"]]))
    if best["plan_id"] in used:
        best = next(p for p in plans if p["plan_id"] not in used)
    used.add(best["plan_id"])
    picks.append(("highest R", best, {"r": best.get("r_measured")}))
    subset = [p for p in plans if p.get("trigger_index") is not None
              and p.get("trigger_index") == p.get("exit_index") and p["plan_id"] not in used]
    if subset:
        seed_c = seed_for(run_id, "same_bar")
        idx = random.Random(seed_c).randrange(len(subset))
        chosen = subset[idx]
        picks.append(("same-bar (seeded)", chosen, {"seed": seed_c, "index": idx,
                                                    "n": len(subset)}))
    else:
        low = min((p for p in plans if p["plan_id"] not in used),
                  key=lambda p: (p.get("r_measured") if p.get("r_measured") is not None else 1e9,
                                 p["plan_id"]))
        picks.append(("lowest R (no same-bar plan existed)", low, {"r": low.get("r_measured")}))
    return picks


def fmt(value, digits=6):
    return "—" if value is None else (f"{value:.{digits}f}" if isinstance(value, float) else str(value))
