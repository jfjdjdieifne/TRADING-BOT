#!/usr/bin/env python3
"""One month of the scalp study: events, plans, outcomes and the hour-matched control.

    python3 scalp_run.py --month 2021-10 --out /tmp/build_scalp/2021-10

No tuning parameter is read from the results; every switch below is the one declared in
DECLARED_CHOICES_SCALP.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import scalp_core as C
import scalp_data as D

UTC = timezone.utc


def memory_guard() -> None:
    """Self-stop once this process uses over 70% of physical RAM; stdlib /proc only."""
    try:
        status = Path("/proc/self/status").read_text()
        meminfo = Path("/proc/meminfo").read_text()
        rss_kb = int(next(line.split()[1] for line in status.splitlines() if line.startswith("VmRSS:")))
        total_kb = int(next(line.split()[1] for line in meminfo.splitlines() if line.startswith("MemTotal:")))
    except (OSError, StopIteration, ValueError):
        return
    if total_kb and rss_kb / total_kb > 0.70:
        raise MemoryError(f"self-stop: RSS {rss_kb} KiB exceeds 70% of RAM {total_kb} KiB")


CONFIGS = [
    {"id": "PRIMARY", "side": "long", "variant": "1A", "large": "L-RANGE", "window": "3"},
    {"id": "variant_1B", "side": "long", "variant": "1B", "large": "L-RANGE", "window": "3"},
    {"id": "window_2", "side": "long", "variant": "1A", "large": "L-RANGE", "window": "2"},
    {"id": "large_body", "side": "long", "variant": "1A", "large": "L-BODY", "window": "3"},
    {"id": "large_loose", "side": "long", "variant": "1A", "large": "L-LOOSE", "window": "3"},
    {"id": "half_body", "side": "long", "variant": "1A", "large": "L-RANGE", "window": "3", "half_level": "body"},
    {"id": "shorts", "side": "short", "variant": "1A", "large": "L-RANGE", "window": "3"},
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def month_bounds(month: str) -> tuple[str, str]:
    year, mon = int(month[:4]), int(month[5:7])
    start = datetime(year, mon, 1, tzinfo=UTC)
    end = datetime(year + (mon == 12), (mon % 12) + 1, 1, tzinfo=UTC)
    return start.isoformat(), end.isoformat()


def control_draws(candles: list[dict], event: dict, plan: dict, rng: random.Random,
                  m: int = C.M_CONTROL, n_bars: int | None = None) -> list[dict]:
    """M bars from the same month and the same NY hour, outside the declared exclusion zone."""

    event_hour = C.ny_hour(candles[event["h_index"]]["start"])
    s_start = candles[event["s_index"]]["start"]
    pool = [c for c in candles
            if C.ny_hour(c["start"]) == event_hour
            and abs((c["start"] - s_start).total_seconds()) > C.EXCLUSION_HOURS * 3600
            and c["last_bar"] + 1 < (len(candles) if n_bars is None else n_bars)]
    if not pool:
        return []
    picks = rng.sample(pool, min(m, len(pool)))
    out = []
    for candle in picks:
        out.append({"matched_candle": candle, "entry": candle["ask_close"],
                    "hour": event_hour})
    return out


def run(month: str, out_dir: Path) -> dict:
    memory_guard()
    out_dir.mkdir(parents=True, exist_ok=True)
    if month not in D.ALLOWED:
        raise SystemExit(f"month {month} is not in the allowed exploratory pool")
    t0, t1 = month_bounds(month)
    started = time.time()
    bars, meta = D.load_window(t0, t1)
    memory_guard()
    if meta["reserved_months_loaded"]:
        raise SystemExit(f"reserved month loaded: {meta}")
    candles = D.aggregate_15m(bars)
    data_sha = sha256_file(D.DATA)

    rng = random.Random(f"{C.SEED}|{month}")
    plans, controls = [], []
    per_config = {}

    for config in CONFIGS:
        window = C.WINDOW_PRIMARY if config["window"] == "3" else C.WINDOW_SECONDARY
        found = C.events(candles, side=config["side"], variant=config["variant"],
                         large_mode=config["large"], window=window,
                         half_level=config.get("half_level", "range"))
        kept = 0
        for event in found:
            plan = C.build_plan(candles, event, side=config["side"])
            plan["config"] = config["id"]
            plan["month"] = month
            plan["s_start"] = candles[event["s_index"]]["start"].isoformat()
            plan["h_start"] = candles[event["h_index"]]["start"].isoformat()
            plan["ny_hour"] = C.ny_hour(candles[event["h_index"]]["start"])
            if plan.get("excluded"):
                plan["state"] = "excluded"
                plan["sub_pip"] = plan.get("stop_pips", 99) < C.SUB_PIP
                plans.append(plan)
                continue
            outcome = C.simulate(plan, bars)
            plan.update(outcome)
            plan["excess_hit"] = C.excess_hit(plan, outcome)
            plans.append(plan)
            kept += 1
            if config["id"] == "PRIMARY":
                for draw in control_draws(candles, event, plan, rng, n_bars=len(bars)):
                    candle = draw["matched_candle"]
                    control = {
                        "config": "CONTROL", "month": month, "side": "long",
                        "for_h_index": event["h_index"], "for_s_index": event["s_index"],
                        "for_form": event["form"], "entry": draw["entry"], "stop": draw["entry"] - plan["risk"],
                        "target": draw["entry"] + (plan["target"] - plan["entry"]),
                        "risk": plan["risk"], "rr": plan["rr"], "ny_hour": draw["hour"],
                        "entry_index_5m": candle["last_bar"] + 1,
                        "matched_start": candle["start"].isoformat(),
                    }
                    outcome_c = C.simulate(control, bars)
                    control.update(outcome_c)
                    control["excess_hit"] = C.excess_hit(control, outcome_c)
                    controls.append(control)
        per_config[config["id"]] = {"events": len(found), "plans": kept,
                                   "excluded": len(found) - kept}

    with open(out_dir / "plans.jsonl", "w", encoding="utf-8") as fh:
        for plan in plans:
            fh.write(json.dumps(plan, default=str) + "\n")
    with open(out_dir / "controls.jsonl", "w", encoding="utf-8") as fh:
        for control in controls:
            fh.write(json.dumps(control, default=str) + "\n")

    primary = [p for p in plans if p["config"] == "PRIMARY" and p.get("state") == "settled"]
    summary = {
        "month": month, "bars_5m": len(bars), "candles_15m": len(candles),
        "data_sha256": data_sha, **meta,
        "configs": per_config,
        "primary_settled": len(primary),
        "primary_hits": sum(1 for p in primary if p.get("exit_reason") == "target"),
        "primary_mean_r": (sum(p["r"] for p in primary) / len(primary)) if primary else None,
        "controls": len(controls),
        "control_settled": sum(1 for c in controls if c.get("state") == "settled"),
        "seed": C.SEED, "m_control": C.M_CONTROL,
        "window_bars_5m": C.WINDOW_BARS_5M,
        "declared_tests": 20,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summary = run(args.month, Path(args.out))
    print(json.dumps({k: summary[k] for k in ("month", "candles_15m", "configs", "primary_settled",
                                              "primary_hits", "controls", "loaded_until")}, indent=1))


if __name__ == "__main__":
    main()

# What this does NOT establish: it does not establish strategy validity or HYPOTHETICAL_ profitability.
