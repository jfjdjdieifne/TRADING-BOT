#!/usr/bin/env python3
"""6.8: two raw-material dossiers in the D1-D11 format, for the seeded-random plan of
V3-FULL/15m and V3-S1/15m on N1 (2021-11).  Saved outputs + verified candles only; the replay at the
bottom is written here and imports no settlement code.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "build_v1"))
from stream_v1 import load_bars                                        # noqa: E402

UTC = timezone.utc
ROOT = Path("/tmp/build_v3")
OUT = HERE / "REPORT_V3"
DATA = Path("/tmp/hud_data/2021.csv.gz")
SEED = "20261109"
PIP = 10000.0


def pick(run_id: str, plans: list[dict]) -> dict:
    rng = random.Random(f"{SEED}|{run_id}")
    return plans[rng.randrange(len(plans))]


def replay(plan: dict, bars: list, offset: int) -> dict:
    """Side-correct replay written here: buy on ask, sell on bid, spread charged once."""

    direction, entry, stop = plan["direction"], plan["entry"], plan["stop"]
    t1 = (plan["t1"] or {}).get("level")
    start = plan["fill_index"] - offset if plan.get("fill_index") is not None else None
    if start is None:
        return {"verdict": "NO_FILL", "state": plan.get("state")}
    risk = abs(entry - stop)
    for j in range(start + 1, min(start + 289, len(bars))):
        bar = bars[j]
        if direction == "bearish":
            stop_hit = bar.ask_high >= stop
            t1_hit = t1 is not None and bar.ask_low <= t1
        else:
            stop_hit = bar.bid_low <= stop
            t1_hit = t1 is not None and bar.bid_high >= t1
        if stop_hit:
            gross = (entry - stop) if direction == "bearish" else (stop - entry)
            return {"state": "settled", "reason": "stop", "index": start + (j - start),
                    "price": stop, "r": (gross - bar.spread_open / 2.0) / risk}
        if t1_hit:
            gross = (entry - t1) if direction == "bearish" else (t1 - entry)
            return {"state": "settled", "reason": "t1_touched", "index": start + (j - start),
                    "price": t1, "r": (gross - bar.spread_open / 2.0) / risk}
    return {"state": "open"}


def row(bar) -> str:
    return (f"{bar.start.strftime('%Y-%m-%dT%H:%M:%SZ')}  {bar.bid_open:.5f} {bar.bid_high:.5f} "
            f"{bar.bid_low:.5f} {bar.bid_close:.5f} {bar.bid_volume:7.1f}  {bar.ask_open:.5f} "
            f"{bar.ask_high:.5f} {bar.ask_low:.5f} {bar.ask_close:.5f} {bar.ask_volume:7.1f}  "
            f"{bar.spread_open:.6f}")


def dossier(kind: str, month: str, frame: str, run_id: str) -> Path:
    plans = [json.loads(x) for x in (ROOT / f"{month}_{kind}_{frame}" / "plans_final.jsonl").read_text().splitlines()]
    plan = pick(run_id, plans)
    end = datetime.fromisoformat("2021-12-01T00:00:00+00:00")
    bars_full = load_bars(DATA, "2021-01-01T00:00:00+00:00", end.isoformat())
    month_bars = load_bars(DATA, f"{month}-01T00:00:00+00:00", end.isoformat())
    offset = len(bars_full) - len(month_bars)

    decision_index = plan["decision_index"]
    first = max(0, decision_index - offset - 60)
    last = min(len(month_bars), (plan.get("exit_index") or decision_index - offset) + 2)
    rp = replay(plan, month_bars, offset)
    engine_r = plan.get("r_measured")
    if plan.get("fill_index") is None:
        match = rp.get("verdict") == "NO_FILL" and plan.get("state") in ("cancelled", "expired")
    else:
        match = (rp.get("state") == "settled" and plan.get("state") == "settled"
                 and rp.get("reason") == plan.get("exit_reason")
                 and engine_r is not None and abs(rp["r"] - engine_r) < 1e-9)

    lines = [f"# DOSSIER {kind} {frame} {month} — {plan['plan_id']}", "",
             "Raw-material dossier, built from the saved run output and the verified 5m file. "
             "No engine run; the replay below imports no settlement code.", "",
             "## D1. Identity and outcome", "```",
             f"plan id          {plan['plan_id']}",
             f"thesis id        {plan['thesis_id']}",
             f"variant          {plan['variant']}",
             f"direction        {plan['direction']}",
             f"setup frame      {plan['setup_frame']}   execution frame 5m",
             f"entry            {plan['entry']:.5f}  mode {plan['entry_mode']}",
             f"stop             {plan['stop']:.5f}  rule {plan['stop_rule']}",
             f"T1               {0 if not plan.get('t1') else plan['t1']['level']:.5f}",
             f"T2               {0 if not plan.get('t2') else plan['t2']['level']:.5f}",
             f"R:R to T1        {0 if plan.get('rr_t1') is None else plan['rr_t1']:.3f}",
             f"decision time    {plan['decided_at']}  (5m bar index {plan['decision_index']})",
             f"fill / exit      {plan.get('fill_index')} / {plan.get('exit_index')}  {plan.get('exit_reason')}",
             f"state            {plan.get('state')}   hypothetical R {engine_r}",
             "```", "",
             "## D2. Raw 5m rows (exact source-file rows) from 60 candles of context to settlement", "```",
             "timestamp                BidOpen BidHigh BidLow  BidClose BidVol  AskOpen AskHigh AskLow  "
             "AskClose AskVol  SprOpen"]
    for bar in month_bars[first:last]:
        lines.append(row(bar))
    lines += ["```",
              f"- rows shown: {last - first}; file sha256 38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4",
              "", "## D3. Aggregation provenance", "```"]
    for candle in plan["zone"]["candles"]:
        lines.append(f"setup candle #{candle['index']}  open {candle['open_time']}  close {candle['close_time']}  "
                     f"O {candle['open']:.5f} H {candle['high']:.5f} L {candle['low']:.5f} C {candle['close']:.5f}")
    lines += ["```",
              f"- setup frame {frame} is built from 5m bid candles: open = first 5m open, high = max, "
              "low = min, close = last 5m close (DECLARED_CHOICES_V3 A).",
              f"- formation index source: {plan['zone'].get('formation_index_source')}",
              "", "## D4. Bias context", "```",
              json.dumps(plan["bias"], indent=1), "```", "",
              "## D5. Dealing range used", "```",
              json.dumps({k: v for k, v in plan["range"].items()}, indent=1), "```",
              f"- zone against its own range: {plan['zone_vs_range']}", "",
              "## D6. Pools and targets", "```",
              "T1: " + json.dumps(plan.get("t1")),
              "T2: " + json.dumps(plan.get("t2")), "```", "",
              "## D7. Displacement", "```",
              "D-old: " + json.dumps(plan["d_old"]),
              "D-new: " + json.dumps(plan["d_new"]),
              f"rank expansion of the formation candle: {plan.get('rank_expansion')}", "```", "",
              "## D8. Zone", "```",
              json.dumps({k: v for k, v in plan["zone"].items() if k != "candles"}, indent=1), "```", "",
              "## D9. Gates (recorded; applied unless the run was WIDE)", "```",
              json.dumps(plan["gates"], indent=1), "```", "",
              "## D10. Levels and costs", "```",
              f"stop distance {plan['stop_pips']:.2f} pips",
              f"half spread at the decision {plan['half_spread_at_decision']:.6f}",
              f"expiry {plan['expiry_bars']} bars", "```", "",
              "## D11. Candle-by-candle execution and independent replay", "```"]
    start = plan.get("fill_index")
    if start is not None:
        for j in range(start - offset, min(start - offset + 12, len(month_bars))):
            bar = month_bars[j]
            lines.append(f"{plan['fill_index'] + (j - (start - offset)):6d}  {bar.start.strftime('%Y-%m-%dT%H:%M:%SZ')}  "
                         f"{bar.bid_open:.5f}/{bar.bid_high:.5f}/{bar.bid_low:.5f}/{bar.bid_close:.5f}  "
                         f"{bar.ask_open:.5f}/{bar.ask_high:.5f}/{bar.ask_low:.5f}/{bar.ask_close:.5f}  "
                         f"{bar.spread_open:.6f}")
    lines += ["```", "```",
              "independent replay: side-correct, spread charged once at the exit bar / 2",
              f"  result: {rp}",
              f"  engine: state={plan.get('state')} exit={plan.get('exit_reason')} r={engine_r}",
              f"  verdict: {'MATCH' if match else 'MISMATCH'}",
              "```", "", "## What this does NOT establish", "",
              "- It does not establish that this plan's reading is correct ICT; nothing is judged here.",
              "- It does not establish that the gates or the switch improve anything: one plan is one plan.",
              "- Fields the record does not carry are absent, not reconstructed.", ""]
    path = OUT / f"DOSSIER_{kind}_{frame}_{month}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, match, plan["plan_id"]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    info = []
    for kind in ("V3-FULL", "V3-S1"):
        path, match, plan_id = dossier(kind, "2021-11", "15m", f"{kind}|15m|2021-11|{SEED}")
        info.append({"kind": kind, "path": str(path.name), "plan_id": plan_id, "replay_match": match})
    (OUT / "DOSSIERS_6_8.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
