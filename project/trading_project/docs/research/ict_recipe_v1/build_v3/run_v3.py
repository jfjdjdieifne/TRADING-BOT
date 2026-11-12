#!/usr/bin/env python3
"""V3 runner: one variant, one month, one setup frame.

    python run_v3.py --month 2021-10 --variant V3-0 --frame 15m --out /tmp/build_v3/2021-10_V3-0_15m

The loader is called with an explicit [history_start, month_end) window, so a month that is not part
of the run is never turned into a Bar (see RESERVED_MONTHS in this file).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import v3_core as C

UTC = timezone.utc
DATA = Path("/tmp/hud_data/2021.csv.gz")
DATA_SHA256 = "38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4"
RESERVED_MONTHS = ("2021-08", "2021-12")     # X1, X2 — never loaded in any run of this task


def month_bounds(month: str) -> tuple[datetime, datetime]:
    year, mon = int(month[:4]), int(month[5:7])
    start = datetime(year, mon, 1, tzinfo=UTC)
    end = datetime(year + (mon == 12), (mon % 12) + 1, 1, tzinfo=UTC)
    return start, end


def data_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonl(fh, record: dict) -> None:
    fh.write(json.dumps(record, default=str) + "\n")


def zone_candles(frame: C.FrameV3, formed_index: int) -> list[dict]:
    """The three setup candles of the zone, with open and close times."""

    out = []
    for i in (formed_index - 2, formed_index - 1, formed_index):
        offset = frame.window.t - (frame.index - i)
        if not (0 <= offset < len(frame.window.bars)):
            continue
        bar = frame.window.bars[offset]
        out.append({"index": i, "open_time": bar.start.isoformat(),
                    "close_time": bar.end.isoformat(), "open": bar.bid_open,
                    "high": bar.bid_high, "low": bar.bid_low, "close": bar.bid_close})
    return out


def mean_threshold(zone: dict, candles: list[dict]) -> float | None:
    """S2: the mean threshold of the zone's own candle (order block body) or the zone's equilibrium."""

    if zone["kind"] == "order_block" and candles:
        last = candles[-1]
        return (last["open"] + last["close"]) / 2.0
    return (zone["lower"] + zone["upper"]) / 2.0


def run(*, month: str, variant: str, frame_label: str, out_dir: Path,
        null: bool = False, wide: bool = False, max_bars: int | None = None,
        history_start: str = "2021-01-01") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sha = data_sha256(DATA)
    if sha != DATA_SHA256:
        raise SystemExit(f"data sha256 mismatch: {sha}")

    switches = dict(C.SWITCH_SETS[variant])
    month_start, month_end = month_bounds(month)
    history_start_dt = datetime.fromisoformat(history_start).replace(tzinfo=UTC)
    # the loader never sees a bar at or after month_end, so no later month can enter memory
    from stream_v1 import load_bars, HtfState
    bars = load_bars(DATA, history_start_dt.isoformat(), month_end.isoformat())
    if not bars:
        raise SystemExit("no bars loaded")

    frames = {label: C.FrameV3(label) for label in (frame_label, "15m", "1h")}
    setup = frames[frame_label]
    htf = HtfState()
    ny_htf = C.NyHtfState()

    total_kb = C.memory_total_kb()
    cap_kb = int(total_kb * C.MEMORY_CAP_FRACTION) if total_kb else None

    started = time.time()
    counts = {"bars": 0, "decisions": 0, "plans": 0, "no_plan": 0, "theses": 0}
    reasons: dict[str, int] = {}
    live: list[C.Execution] = []
    finished: list[dict] = []
    consumed: set[str] = set()
    rss_curve: list[dict] = []
    stopped = None

    with open(out_dir / "decisions.jsonl", "w", encoding="utf-8") as fd, \
            open(out_dir / "plans.jsonl", "w", encoding="utf-8") as fp:
        for index, bar in enumerate(bars):
            counts["bars"] += 1
            if max_bars is not None and counts["bars"] > max_bars:
                break
            htf.push(bar)
            if switches["time_ny"]:
                ny_htf.push(bar)
            for label, state in frames.items():
                state.push(bar)

            # ---- settle live plans on every 5m bar
            still: list[C.Execution] = []
            for run_state in live:
                run_state.update(index, bar)
                if run_state.state in ("settled", "cancelled", "expired"):
                    record = run_state.plan
                    record.update(run_state.view())
                    finished.append(record)
                else:
                    still.append(run_state)
            live = still

            if total_kb and index % 60 == 0:
                rss = C.memory_rss_kb()
                if rss is not None:
                    rss_curve.append({"bar": index, "rss_kb": rss})
                    if cap_kb and rss > cap_kb:
                        stopped = {"reason": "memory_cap", "bar": index, "rss_kb": rss, "cap_kb": cap_kb}
                        (out_dir / "partial_status.json").write_text(
                            json.dumps({"stopped": stopped, "decisions": counts["decisions"]}, indent=1),
                            encoding="utf-8")
                        break

            if bar.start < month_start:
                continue
            if setup.last is None:
                continue

            view = setup.last
            session = C.session_now(bar)
            bias_view = ny_htf.view() if switches["time_ny"] else htf.view()
            daily, weekly = bias_view["daily"], bias_view["weekly"]
            bias_daily = daily["bias"] if daily else None
            bias_weekly = weekly["bias"] if weekly else None
            bias = bias_daily or bias_weekly
            bias_conflict = bool(bias_daily and bias_weekly and bias_daily != bias_weekly)
            counts["decisions"] += 1

            decision = {"index": index, "decided_at": bar.start.isoformat(), "variant": variant,
                        "frame": frame_label, "close": bar.bid_close,
                        "bias": {"daily": bias_daily, "weekly": bias_weekly, "resolved": bias,
                                 "conflict": bias_conflict},
                        "session": {"window": session["declared_window"], "in_window": session["in_window"],
                                    "ny_local": session["local_bar_start"]},
                        "range_swing": view["range"]}

            if bias not in ("UP", "DOWN"):
                counts["no_plan"] += 1
                reasons["bias_undefined"] = reasons.get("bias_undefined", 0) + 1
                decision.update({"decision": "NO_PLAN", "reason": "bias_undefined"})
                jsonl(fd, decision)
                continue

            direction = "bullish" if bias == "UP" else "bearish"

            # ---- pools (H3 merge, optional L additions)
            pools = []
            for label in frames:
                pools.extend(frames[label].pool_view())
            if switches["liquidity"]:
                pools.extend(C.htf_pools(bias_view, frame_label))
            pools = C.merge_pools(pools)

            # ---- zones
            candidates = C.rank_zones(
                C.gather_zones(direction=direction, gaps=setup.gaps, blocks=setup.blocks,
                               sweep=(view["sweep_low"] if direction == "bullish" else view["sweep_high"]),
                               close=bar.bid_close),
                bias=("UP" if direction == "bullish" else "DOWN"), close=bar.bid_close,
                range_high=view["range"].get("high", bar.bid_close),
                range_low=view["range"].get("low", bar.bid_close))
            for zone in candidates["ranked"]:
                zone["zone_id"] = f"{frame_label}:{zone['zone_id']}"
                zone["frame"] = frame_label

            ranked = candidates["ranked"]
            decision["zones"] = [{"zone_id": z["zone_id"], "kind": z["kind"], "lower": z["lower"],
                                  "upper": z["upper"], "fresh": z["fresh"],
                                  "bias_agrees": z["bias_agrees"],
                                  "distance_ratio": z["distance_ratio"]} for z in ranked[:6]]
            decision["criteria_conflict"] = candidates["criteria_conflict"]

            if not ranked:
                counts["no_plan"] += 1
                reasons["no_zone"] = reasons.get("no_zone", 0) + 1
                decision.update({"decision": "NO_PLAN", "reason": "no_zone"})
                jsonl(fd, decision)
                continue

            zone = ranked[0]
            entry_edge = zone["upper"] if direction == "bullish" else zone["lower"]

            # ---- R switch: the leg's own dealing range, judged on the zone's entry edge
            if switches["range"] == "leg":
                rg = C.leg_range(setup, zone, direction, view["range"])
            else:
                rg = dict(view["range"])
            position_label, position_ratio = C.range_position(rg, entry_edge)
            decision["range_used"] = {"definition": switches["range"], "low": rg.get("low"),
                                      "high": rg.get("high"), "label_on_entry_edge": position_label,
                                      "ratio": position_ratio}

            # ---- targets
            targets = C.pick_targets(pools, entry=entry_edge, direction=direction, rg=rg,
                                     liquidity=switches["liquidity"])
            decision["targets"] = [{"level": t["level"], "kind": t["kind"], "frames": t.get("frames"),
                                    "class": t.get("class")} for t in targets[:4]]

            # ---- gates (recorded always; applied unless WIDE)
            gate = {}
            gate["session"] = bool(session["in_window"])
            gate["bias_agrees"] = bool(zone["bias_agrees"])
            gate["position"] = position_label in C.GATE_RANGE_POSITION[direction]
            gate["target_exists"] = len(targets) > 0
            gate["zone_in_range"] = position_label in ("premium", "discount", "equilibrium", "INSIDE")
            dnew = C.d_new_features(setup, zone, direction)
            gate["d_new"] = dnew["answer"] == "YES"
            if switches["dgate"]:
                gate["d_new_applied"] = True
            passed = all(gate[k] for k in ("session", "bias_agrees", "position", "target_exists")) \
                and (gate["d_new"] if switches["dgate"] else True)
            decision["gates"] = gate

            if not wide and not passed:
                counts["no_plan"] += 1
                failed = [k for k, v in gate.items() if v is False]
                reason = "gate_" + (failed[0] if failed else "unknown")
                reasons[reason] = reasons.get(reason, 0) + 1
                decision.update({"decision": "NO_PLAN", "reason": reason})
                jsonl(fd, decision)
                continue

            # ---- one thesis = one plan (H9)
            thesis_id = f"{zone['zone_id']}:{direction}"
            if thesis_id in consumed:
                counts["no_plan"] += 1
                reasons["thesis_already_consumed"] = reasons.get("thesis_already_consumed", 0) + 1
                decision.update({"decision": "NO_PLAN", "reason": "thesis_already_consumed"})
                jsonl(fd, decision)
                continue

            # D9 repair: a zone whose record carries no formation index (sweep_level zones) gets the
            # current setup candle as a DECLARED proxy, and the record says so.
            proxy = zone.get("formed_index") is None
            middle = setup.index if proxy else zone["formed_index"]
            zone_local = dict(zone)
            zone_local["formed_index"] = middle
            candles = zone_candles(setup, middle)
            zone_local["mean_threshold"] = mean_threshold(zone_local, candles)
            stop, stop_rule = C.stop_for(switches["stop"], direction=direction, zone=zone_local,
                                         frame=setup, ctx={})
            if stop is None or abs(entry_edge - stop) <= 0:
                counts["no_plan"] += 1
                reasons[stop_rule] = reasons.get(stop_rule, 0) + 1
                decision.update({"decision": "NO_PLAN", "reason": stop_rule})
                jsonl(fd, decision)
                continue

            t1 = targets[0] if targets else None
            t2 = targets[1] if len(targets) > 1 else None
            risk = abs(entry_edge - stop)

            # H4: a target that is not beyond the entry on the trade's side is rejected, with the cause
            if t1 is not None:
                behind = (t1["level"] <= entry_edge) if direction == "bullish" else (t1["level"] >= entry_edge)
                if behind:
                    counts["no_plan"] += 1
                    reasons["TARGET_BEHIND_ENTRY"] = reasons.get("TARGET_BEHIND_ENTRY", 0) + 1
                    decision.update({"decision": "NO_PLAN", "reason": "TARGET_BEHIND_ENTRY",
                                     "detail": {"t1": t1["level"], "entry": entry_edge}})
                    jsonl(fd, decision)
                    continue

            if null:
                # seeded NULL: same entry, same distances, opposite direction
                stop = entry_edge + (entry_edge - stop)
                t1 = None if t1 is None else {**t1, "level": entry_edge - (t1["level"] - entry_edge)}
                t2 = None if t2 is None else {**t2, "level": entry_edge - (t2["level"] - entry_edge)}
                direction_used = "bearish" if direction == "bullish" else "bullish"
            else:
                direction_used = direction

            plan_id = f"plan:{bar.start.isoformat()}:{zone['zone_id']}"
            plan = {
                "plan_id": plan_id, "thesis_id": thesis_id, "variant": variant, "null": null,
                "wide": wide, "setup_frame": frame_label, "direction": direction_used,
                "direction_selected": direction,
                "decision_index": index, "decided_at": bar.start.isoformat(),
                "entry": entry_edge, "entry_edge": entry_edge, "entry_mode": switches["entry"],
                "stop": stop, "stop_rule": stop_rule, "risk_price": risk,
                "stop_pips": risk * C.PIP,
                "t1": None if t1 is None else {"level": t1["level"], "kind": t1["kind"],
                                               "frames": t1.get("frames"), "class": t1.get("class")},
                "t2": None if t2 is None else {"level": t2["level"], "kind": t2["kind"],
                                               "class": t2.get("class")},
                "rr_t1": None if t1 is None else abs(t1["level"] - entry_edge) / risk,
                "zone": {"zone_id": zone["zone_id"], "kind": zone["kind"], "lower": zone["lower"],
                         "upper": zone["upper"], "formed_index": zone["formed_index"],
                         "fresh": zone["fresh"], "bias_agrees": zone["bias_agrees"],
                         "mean_threshold": zone_local["mean_threshold"],
                         "candles": candles,
                         "formation_index_source": "PROXY_CURRENT_CANDLE" if proxy else "RECORDED",
                         "existed_at": candles[-1]["close_time"] if candles else None},
                "swings": setup.swing_log[-6:],
                "range": {"definition": switches["range"], "low": rg.get("low"), "high": rg.get("high"),
                          "equilibrium": rg.get("equilibrium"), "label": position_label,
                          "ratio": position_ratio},
                "zone_vs_range": C.pool_class(entry_edge, "high" if direction == "bullish" else "low", rg),
                "bias": {"daily": bias_daily, "weekly": bias_weekly, "resolved": bias,
                         "conflict": bias_conflict},
                "session": {"window": session["declared_window"], "in_window": session["in_window"]},
                "d_old": {"answer": view["displacement"]["answer"],
                          "ratio": view["displacement"].get("ratio")},
                "d_new": dnew, "rank_expansion": C.rank_expansion(setup, middle),
                "gates": gate, "half_spread_at_decision": bar.spread_open / 2.0,
                "expiry_bars": C.EXPIRY_BARS, "state": "armed",
            }
            ex = C.Execution(plan)
            live.append(ex)
            consumed.add(thesis_id)
            counts["plans"] += 1
            counts["theses"] += 1
            decision.update({"decision": "ARMED" if not wide else "ARMED_WIDE", "plan_id": plan_id})
            jsonl(fp, plan)
            jsonl(fd, decision)

    for run_state in live:                      # still open at the end of the month
        record = run_state.plan
        record.update(run_state.view())
        record["open_at_end"] = True
        finished.append(record)

    settled = [p for p in finished if p.get("state") == "settled"]
    summary = {
        "month": month, "variant": variant, "frame": frame_label, "null": null, "wide": wide,
        "switches": switches, "data_sha256": sha, "bars": counts["bars"],
        "decisions": counts["decisions"], "plans": counts["plans"], "no_plan": counts["no_plan"],
        "no_plan_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "settled": len(settled), "cancelled": sum(1 for p in finished if p.get("state") == "cancelled"),
        "expired": sum(1 for p in finished if p.get("state") == "expired"),
        "open_at_end": sum(1 for p in finished if p.get("open_at_end")),
        "r_values": [p.get("r_measured") for p in settled],
        "elapsed_seconds": round(time.time() - started, 2),
        "memory": {"total_kb": total_kb, "cap_kb": cap_kb, "peak_rss_kb": C.peak_rss_kb(),
                   "rss_curve": rss_curve[:200]},
        "stopped": stopped,
        "reserved_months_loaded": [],
        "loaded_until": month_end.isoformat(),
    }
    (out_dir / "plans_final.jsonl").write_text(
        "".join(json.dumps(p, default=str) + "\n" for p in finished), encoding="utf-8")
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=1, default=str),
                                              encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    ap.add_argument("--variant", required=True, choices=sorted(C.SWITCH_SETS) + ["NULL", "V2-A", "V2-B"])
    ap.add_argument("--frame", required=True, choices=["15m", "1h"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--wide", action="store_true")
    ap.add_argument("--max-bars", type=int, default=None)
    ap.add_argument("--history-start", default="2021-01-01")
    args = ap.parse_args()

    variant = "V3-0" if (args.variant.startswith("V2-") or args.variant == "NULL") else args.variant
    null = args.variant in ("NULL",)
    summary = run(month=args.month, variant=variant, frame_label=args.frame,
                  out_dir=Path(args.out), null=null, wide=args.wide, max_bars=args.max_bars,
                  history_start=args.history_start)
    print(json.dumps({k: summary[k] for k in ("month", "variant", "frame", "plans", "settled",
                                              "cancelled", "expired", "elapsed_seconds")}, indent=1))


if __name__ == "__main__":
    main()
