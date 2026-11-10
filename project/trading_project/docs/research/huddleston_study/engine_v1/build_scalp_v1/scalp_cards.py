#!/usr/bin/env python3
"""Twelve seeded case cards for the owner.  Two modes, in this order:

    python3 scalp_cards.py --key     -> REPORT_SCALP/ANSWER_KEY.json   (committed first)
    python3 scalp_cards.py --cards   -> REPORT_SCALP/CARDS/*.md        (committed after)

A card shows candles up to and including the entry candle only.  The outcome lives in the answer key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import scalp_core as C
import scalp_data as D

ROOT = Path("/tmp/build_scalp")
OUT = Path(__file__).resolve().parent / "REPORT_SCALP"
MONTHS = ("2021-06", "2021-07", "2021-09", "2021-10", "2021-11")
SEED = 20261109
N_PER_FORM = 6


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def pick() -> list[dict]:
    pool = []
    for month in MONTHS:
        for plan in load(ROOT / month / "plans.jsonl"):
            if plan["config"] == "PRIMARY" and plan.get("state") == "settled":
                pool.append({**plan, "month": month})
    rng = random.Random(f"{SEED}|cards")
    chosen = []
    for form in (1, 2):
        items = sorted([p for p in pool if p["form"] == form],
                       key=lambda p: (p["month"], p["s_start"]))
        if len(items) < N_PER_FORM:
            raise SystemExit(f"only {len(items)} settled form-{form} plans; cannot draw {N_PER_FORM}")
        chosen.extend(rng.sample(items, N_PER_FORM))
    chosen.sort(key=lambda p: (p["month"], p["s_start"]))
    return chosen


def key() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, plan in enumerate(pick(), start=1):
        entries.append({"card": f"CARD_{i:02d}", "month": plan["month"], "form": plan["form"],
                        "s_start": plan["s_start"], "h_start": plan["h_start"],
                        "entry": plan["entry"], "stop": plan["stop"], "target": plan["target"],
                        "exit_reason": plan["exit_reason"], "r": plan["r"],
                        "ambiguous_bars": plan.get("ambiguous_bars", 0)})
    payload = {"seed": SEED, "cards": entries,
               "note": "outcomes only; the cards themselves never show them"}
    path = OUT / "ANSWER_KEY.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / "ANSWER_KEY.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    print(json.dumps({"cards": len(entries), "sha256": digest}, indent=1))


def cards() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    card_dir = OUT / "CARDS"
    card_dir.mkdir(exist_ok=True)
    chosen = pick()
    cache = {}
    events_by_month = {}
    for month in MONTHS:
        y, m = int(month[:4]), int(month[5:7])
        lo = f"{month}-01T00:00:00+00:00"
        hi = datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=timezone.utc).isoformat()
        bars, _ = D.load_window(lo, hi)
        candles = D.aggregate_15m(bars)
        cache[month] = (bars, candles)
        events_by_month[month] = C.events(candles, side="long", variant="1A")
    for i, plan in enumerate(chosen, start=1):
        month = plan["month"]
        t0 = f"{month}-01T00:00:00+00:00"
        year, mon = int(month[:4]), int(month[5:7])
        t1 = datetime(year + (mon == 12), (mon % 12) + 1, 1, tzinfo=timezone.utc).isoformat()
        bars, candles = cache[month]
        s_index = plan["s_index"]
        event = next(e for e in events_by_month[month]
                     if e["s_index"] == plan["s_index"] and e["r_index"] == plan["r_index"]
                     and e["h_index"] == plan["h_index"])
        swept_low, r_half = event["swept_low"], event["r_half"]
        first = max(0, s_index - 3)
        last = plan["h_index"]          # nothing after the entry candle is shown
        lines = [f"# CARD_{i:02d} — {month} — 15m", "",
                 "Candles up to and including the entry candle only. No outcome on this card.", "",
                 "```",
                 f"{'idx':>4s} {'time (UTC)':22s} {'open':>8s} {'high':>8s} {'low':>8s} {'close':>8s}  marks"]
        for idx in range(first, last + 1):
            candle = candles[idx]
            marks = []
            if idx == plan["s_index"]:
                marks.append("S (sweep)")
            if idx == plan["r_index"]:
                marks.append("R (rebound; FVG middle)")
            if idx == plan["r_index"] + 1 and plan["fvg"]:
                marks.append("FVG confirmed at this close")
            if idx == plan["h_index"]:
                marks.append("H (entry candle)")
            lines.append(f"{idx:>4d} {candle['start'].strftime('%Y-%m-%dT%H:%M'):22s} "
                         f"{candle['open']:.5f} {candle['high']:.5f} {candle['low']:.5f} "
                         f"{candle['close']:.5f}  {' '.join(marks)}")
        lines += ["```", "",
                  f"- swept low (previous confirmed swing low): {swept_low:.5f}",
                  f"- R range: {candles[plan['r_index']]['low']:.5f} .. {candles[plan['r_index']]['high']:.5f}"
                  f"; 50% level {r_half:.5f}",
                  f"- FVG on R: {'YES' if plan['fvg'] else 'NO'}  → Form {plan['form']}",
                  f"- entry (ask close of H): {plan['entry']:.5f}",
                  f"- stop: {plan['stop']:.5f}  ({plan['stop_pips']:.2f} pips)",
                  f"- target: {plan['target']:.5f}  (swing high before the swept low, minus buffer)",
                  "",
                  "Is this the pattern as the owner described?",
                  "",
                  "## What this does NOT establish", "",
                  "- It does not establish that the pattern works; the card checks the reading only.",
                  "- It does not show the outcome; that is in ANSWER_KEY.json, hashed before this card.",
                  "- It does not establish a working strategy or profitability.",
                  ""]
        (card_dir / f"CARD_{i:02d}_{month}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"cards_written": len(chosen), "dir": str(card_dir.name)}, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args()
    if args.key:
        key()
    if args.cards:
        cards()


if __name__ == "__main__":
    main()

# What this does NOT establish: it does not establish strategy validity or profitability.
