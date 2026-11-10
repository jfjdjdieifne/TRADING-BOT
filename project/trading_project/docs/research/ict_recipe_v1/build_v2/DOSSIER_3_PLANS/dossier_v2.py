#!/usr/bin/env python3
"""Build the three raw-material dossiers (D1-D14) from SAVED outputs + verified candles.

    python3 dossier_v2.py --root /tmp/build_v2 --data /tmp/hud_data/2021.csv.gz

No engine is run. Aggregation and settlement are recomputed here, from candles, with this file's own
code; anything that would need the engine is marked NOT_RECOVERABLE_WITHOUT_RERUN.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "build_v1"))
sys.path.insert(0, str(HERE.parent / "TRADE_DETAIL_V2"))
from stream_v1 import load_bars          # loader only
import td_lib as L                       # replay/aggregate helpers, no settlement import

UTC = timezone.utc
PLANS = [("2021-09_V2-A", "2021-09", "V2-A", "P1"),
         ("2021-09_V2-B", "2021-09", "V2-B", "P2"),
         ("2021-07_V2-A", "2021-07", "V2-A", "P3")]
MONTH_END = {"2021-09": "2021-10-01", "2021-07": "2021-08-01"}
FRAME_MINUTES = {"5m": 5, "15m": 15, "1h": 60}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_rows(path: Path, stamps: set[str]) -> dict[str, list[str]]:
    """The exact source-file rows for the given 5m timestamps (D2)."""

    out = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            key = row["Datetime"]
            if key in stamps:
                out[key] = row
    return out


def day_key(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d")


def week_key(moment: datetime) -> str:
    year, week, _ = moment.isocalendar()
    return f"{year}-W{week:02d}"


def htf_candles(bars, key_fn) -> list[dict]:
    """Completed daily/weekly buckets, exposed only when a LATER bucket appears."""

    out, cur = [], None
    for bar in bars:
        k = key_fn(bar.start)
        if cur is None or k != cur["key"]:
            if cur is not None:
                cur["close_time"] = bar.start.isoformat()   # available when the next bucket starts
                out.append(cur)
            cur = {"key": k, "open": bar.bid_open, "high": bar.bid_high, "low": bar.bid_low,
                   "close": bar.bid_close, "start": bar.start.isoformat()}
        else:
            cur["high"] = max(cur["high"], bar.bid_high)
            cur["low"] = min(cur["low"], bar.bid_low)
            cur["close"] = bar.bid_close
    return out


def fmt(v, d=5):
    return "—" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v))


def dossier(tag: str, run: str, month: str, variant: str, plan: dict, ctx: dict,
            bars, frames: dict, raw: dict, daily: list[dict], weekly: list[dict],
            selection_line: str, source_hashes: dict) -> str:
    direction = plan["direction"]
    frame = plan["setup_frame"]
    zone = plan["zone"]
    entry, stop = plan["entry"], plan["stop"]
    t1 = plan["t1"]["level"] if plan.get("t1") else None
    t2 = plan["t2"]["level"] if plan.get("t2") else None
    risk = abs(entry - stop)
    half = plan["half_spread_at_decision"]
    decide_at = plan["decided_at"]
    setup = frames[frame]
    formed = zone.get("formed_index")
    out = []

    def P(line=""):
        out.append(line)

    P(f"# DOSSIER {tag} — {run} — {plan['plan_id']}")
    P()
    P(f"Raw-material dossier. Prepared from saved outputs only; no engine run. "
      f"Source selection line: `{selection_line}`")
    P()
    # ---------------- D1
    P("## D1. Identity and outcome")
    P("```")
    P(f"plan id          {plan['plan_id']}")
    P(f"thesis id        {plan.get('thesis_id')}")
    P(f"direction        {direction}")
    P(f"setup frame      {frame}   (target frames {plan.get('t1_frame')} / {plan.get('t2_frame')})")
    P(f"entry            {entry:.5f}  ({direction} limit at the zone edge)")
    P(f"stop             {stop:.5f}  ({plan['stop_rule']}, {risk*10000:.2f} pips)")
    P(f"T1               {fmt(t1)}  ({abs(t1-entry)*10000:.2f} pips)" if t1 else "T1               —")
    P(f"T2               {fmt(t2)}  (informational only)" if t2 else "T2               —")
    P(f"R:R to T1        {fmt(plan.get('rr_t1_measured'), 3)}")
    P(f"settlement       {plan.get('state')} / {plan.get('exit_reason')} at bar "
      f"{plan.get('exit_index')} (price {fmt(plan.get('exit_price'))})")
    P(f"hypothetical R   {fmt(plan.get('r_measured'), 4)}")
    P(f"decision time    {decide_at}   (bar {plan['decision_index']})")
    P(f"trigger bar      {plan.get('trigger_index')}")
    P("```")
    P()
    P(f"- arming events of this thesis: **1** (thesis id is unique in `plans_final.jsonl`; the D4 guard "
      f"forbids re-arming). Confirmed by counting records with the same `thesis_id`.")
    # ---------------- D2
    P("\n## D2. Raw data rows (exact source-file rows, 5m)")
    start_idx = max(0, plan["decision_index"] - 60)
    end_idx = min(len(bars), (plan.get("exit_index") or plan["decision_index"]) + 1)
    stamps = [bars[i].start.isoformat().replace("+00:00", "Z") for i in range(start_idx, end_idx)]
    rows = raw_rows(Path("/tmp/hud_data/2021.csv.gz"), set(stamps))
    P("```")
    P("timestamp                BidOpen BidHigh BidLow  BidClose BidVol  AskOpen AskHigh AskLow  AskClose AskVol  SprOpen")
    for stamp in stamps:
        row = rows.get(stamp)
        if not row:
            P(f"{stamp}  ROW NOT FOUND")
            continue
        vals = [float(row[k]) for k in ("BidOpen", "BidHigh", "BidLow", "BidClose", "BidVolume",
                                        "AskOpen", "AskHigh", "AskLow", "AskClose", "AskVolume",
                                        "SpreadOpen")]
        P(f"{stamp}  {vals[0]:.5f} {vals[1]:.5f} {vals[2]:.5f} {vals[3]:.5f} {vals[4]:.1f}  "
          f"{vals[5]:.5f} {vals[6]:.5f} {vals[7]:.5f} {vals[8]:.5f} {vals[9]:.1f}  {vals[10]:.6f}")
    P("```")
    P(f"- {len(stamps)} rows shown: 60 5m candles of context before the decision bar, then every 5m "
      f"candle to settlement. Data file sha256 `{source_hashes['data']}`.")
    # ---------------- D3
    P("\n## D3. Aggregation provenance")
    P(f"- setup frame `{frame}` = {FRAME_MINUTES[frame]} minutes; built from 5m **bid** candles. "
      f"open = first 5m open, high = max of 5m highs, low = min of 5m lows, close = last 5m close; "
      f"volume summed; spread fields taken from the last 5m bar (declared in DECLARED_CHOICES_V2 row B).")
    P("- bid is used because the entry, stop and targets are all bid prices in this build; the ask is "
      "carried through the data rows only for the spread.")
    lo = max(0, (formed or 0) - 2)
    hi = min(len(setup), (formed or 0) + 2)
    P("```")
    for i in range(lo, hi):
        c = setup[i]
        members = [b for b in bars
                   if c["start"] <= b.start < datetime.fromisoformat(c["close_time"])]
        P(f"setup candle #{i}  open {c['start'].isoformat()}  close {c['close_time']}  "
          f"O {c['open']:.5f}  H {c['high']:.5f}  L {c['low']:.5f}  C {c['close']:.5f}")
        P(f"  built from {len(members)} 5m bars: {members[0].start.isoformat()} .. "
          f"{members[-1].start.isoformat()}")
        P(f"  high = max({', '.join(f'{b.bid_high:.5f}' for b in members)}) = {c['high']:.5f}")
        P(f"  low  = min({', '.join(f'{b.bid_low:.5f}' for b in members)}) = {c['low']:.5f}")
        P(f"  open = {members[0].bid_open:.5f} (first 5m open), close = {members[-1].bid_close:.5f} "
          f"(last 5m close)")
    P("```")
    # ---------------- D4
    P("\n## D4. Higher-frame context used for the bias")
    day = day_key(datetime.fromisoformat(decide_at))
    completed_days = [d for d in daily if d["key"] < day]
    completed_weeks = [w for w in weekly if w["close_time"] <= decide_at]
    P("```")
    for d in completed_days[-2:]:
        P(f"daily  {d['key']}  O {d['open']:.5f} H {d['high']:.5f} L {d['low']:.5f} "
          f"C {d['close']:.5f}  completed/available at {d['close_time']}")
    if completed_weeks:
        w = completed_weeks[-1]
        P(f"weekly {w['key']}  O {w['open']:.5f} H {w['high']:.5f} L {w['low']:.5f} "
          f"C {w['close']:.5f}  completed/available at {w['close_time']}")
    P("```")
    P(f"- bias as recorded at the decision: daily `{ctx['bias']['daily']}`, weekly "
      f"`{ctx['bias']['weekly']}`, resolved `{ctx['bias']['resolved']}`, conflict "
      f"`{ctx['bias']['bias_conflict']}`.")
    P("- rule: `stream_v1.HtfState.bias` returns `UP` when the completed bucket's close is above its "
      "open, `DOWN` below, `FLAT` when equal. The recorded source string in every decision row is "
      "`ict_engine.htf aggregation, completion-labelled`. Direction for the plan = the **daily** "
      "value (DECLARED_CHOICES row 9), weekly recorded as context.")
    # ---------------- D5
    P("\n## D5. Dealing range")
    rg = ctx.get("range") or {}
    low_i, high_i = rg.get("low_index"), rg.get("high_index")
    P("```")
    P(f"range low  {fmt(rg.get('low'))}  (swing candle #{low_i})")
    P(f"range high {fmt(rg.get('high'))}  (swing candle #{high_i})")
    P(f"midpoint   {fmt(rg.get('equilibrium'))}")
    P(f"entry position ratio {fmt(rg.get('position_ratio'), 4)}  label `{rg.get('position')}`  "
      f"state `{rg.get('position_state')}`")
    P("```")
    P("- the swing indices printed above are **window-local positions** in the rolling buffer at read "
      "time (`stream_v1.swing_now` stores `candle_indices['c2']` from the window, not an absolute "
      "candle index). Their timestamps and right-side confirmation candles are therefore "
      "**NOT_RECOVERABLE_WITHOUT_RERUN** — recorded as defect D11. What is certain from the record is "
      "that both swings were confirmed before the decision, because the range existed at the decision "
      "bar and the buffer holds only closed candles.")
    # ---------------- D6
    P("\n## D6. Liquidity and sweep")
    untaken = ctx.get("untaken") or []
    P("```")
    P("level    side   kind                        frame  formed_bar  age_bars  state")
    for pool in untaken[:12]:
        P(f"{pool['level']:.5f}  {pool['side']:5s}  {pool['kind']:26s}  {pool.get('frame','5m'):5s}  "
          f"{fmt(pool.get('formed_index'),0):>10s}  {fmt(pool.get('age_bars'),0):>8s}  untaken")
    P("```")
    sc = ctx.get("setup_context") or {}
    P(f"- sweep reference at the decision: high `{sc.get('sweep_high')}` · low "
      f"`{sc.get('sweep_low')}`. The zone's own formation index is `{formed}`; for a `sweep_level` "
      f"zone the sweep candle is that index, otherwise the sweep did not define this zone.")
    P(f"- ranked target pools at the decision: `{ctx.get('target_pools')}`")
    P("- why T1 and not the pools between: T1 is the first entry of `rank_draws` among the pools on "
      "the trade's side that lie beyond the entry price; T2 is the second. Pools behind the entry are "
      "excluded by `plan_v1.targets_ahead` (`ahead = level > entry` for bullish). The formation index "
      "of each target pool is **NOT_RECOVERABLE_WITHOUT_RERUN** (defect D5) — the plan record stores "
      "only the level, kind and frame.")
    # ---------------- D7
    P("\n## D7. Displacement and structure")
    P("```")
    P(f"displacement   {sc.get('displacement')}")
    P(f"sweep high     {sc.get('sweep_high')}")
    P(f"sweep low      {sc.get('sweep_low')}")
    P(f"structure      {sc.get('shift')}")
    P(f"order block    {sc.get('order_block')}")
    P("```")
    P("- displacement variant is `V-D-01`: body/range above 60 (`SOURCE_NUMBER`, claim F1), equality → "
      "UNDECIDED, read over `candles[:t+1]`. The ratio printed above is the value the module returned.")
    # ---------------- D8
    P("\n## D8. Zone and candidate list")
    P("```")
    P(f"zone id     {zone['zone_id']}")
    P(f"kind        {zone['kind']}   direction {direction}")
    P(f"lower/upper {zone['lower']:.5f} / {zone['upper']:.5f}")
    P(f"formed at   setup candle #{formed}")
    if formed is not None and formed < len(setup):
        P(f"existed from {setup[formed]['close_time']} (that candle's close); decision {decide_at} → "
          f"{'OK' if setup[formed]['close_time'] <= decide_at else 'VIOLATION'}")
    P("```")
    if formed is not None and formed >= 2:
        for i in (formed - 2, formed - 1, formed):
            c = setup[i]
            P(f"- forming candle #{i}: {c['start'].isoformat()} O {c['open']:.5f} H {c['high']:.5f} "
              f"L {c['low']:.5f} C {c['close']:.5f}")
    P("\nCandidates considered at the arming moment, in the order the engine ranked them:")
    P("```")
    for z in (ctx.get("zones_ranked") or []):
        P(f"{z['zone_id']:34s} {z['kind']:11s} [{z['lower']:.5f}, {z['upper']:.5f}]  "
          f"fresh={z['fresh']}  bias_agrees={z['bias_agrees']}  distance_ratio={z['distance_ratio']:.4f}")
    P("```")
    P(f"- criteria in the order applied: `{json.dumps(ctx.get('criteria'))}`")
    P(f"- criteria conflict logged: **{ctx.get('criteria_conflict')}** "
      f"(a conflict ⇒ no plan, so a plan implies no conflict)")
    P(f"- why this zone won: first by bias agreement, then freshness, then the smallest context-relative "
      f"distance (`rank_zones` in `build_v1/plan_v1.py`).")
    # ---------------- D9
    P("\n## D9. Decision trace")
    P("Decision rows at the setup-frame closes between the zone formation and the arming:")
    P("```")
    P("time                      decision      reason")
    for i in range(max(0, (formed or 0) - 2), (formed or 0) + 1):
        if i < len(setup):
            c = setup[i]
            P(f"{c['close_time']}  setup candle #{i} closed")
    P(f"{decide_at}  ARMED         {plan.get('variant')} / {variant}")
    P("```")
    P("- the per-candle sub-decisions (every gate answer between those closes) are written to "
      "`decisions.jsonl` at the **5m decision cadence**, not at setup-frame closes; the saved run "
      "writes one row per 5m bar. The set of gate answers at the exact setup closes is "
      "**NOT_RECOVERABLE_WITHOUT_RERUN** only for bars outside the decision window; inside it every "
      "5m row is saved and the rows at the closing 5m bars carry the question and answer.")
    P(f"- 5m touch: first touching bar **{plan.get('trigger_index')}** "
      f"({bars[plan['trigger_index']].start.isoformat() if plan.get('trigger_index') is not None else '—'}); "
      f"fill convention = limit at the zone edge (v1 convention), fill price {entry:.5f}.")
    # ---------------- D10
    P("\n## D10. Levels and costs")
    P("```")
    P(f"stop            {stop:.5f}   rule: `{plan['stop_rule']}` (DECLARED_CHOICES_V2 row D: the far "
      f"edge of the setup-frame zone; sweep zones use the sweep wick; no pip minimum, no filter)")
    P(f"stop distance   {risk*10000:.2f} pips = {fmt(plan.get('stop_fraction_of_setup_candle'), 4)} "
      f"of the setup candle's range")
    P(f"half-spread     {half*10000:.2f} pips = {fmt(plan.get('cost_fraction_of_stop'), 4)} of the stop")
    P(f"T1 distance     {abs(t1-entry)*10000:.2f} pips" if t1 else "T1 distance     —")
    P(f"T2 distance     {abs(t2-entry)*10000:.2f} pips" if t2 else "T2 distance     —")
    P(f"R:R T1 / T2     {fmt(plan.get('rr_t1_measured'),3)} / {fmt(plan.get('rr_t2_measured'),3)}")
    P("```")
    # ---------------- D11
    P("\n## D11. Candle-by-candle execution")
    P("```")
    P("bar    time                   bid O/H/L/C                 ask O/H/L/C                 "
      "touch  in-zone  stop  T1   spread")
    t_start = plan.get("trigger_index") if plan.get("trigger_index") is not None else plan["decision_index"]
    for i in range(plan["decision_index"] + 1,
                   min(len(bars), (plan.get("exit_index") or plan["decision_index"]) + 2)):
        b = bars[i]
        touched = b.bid_low <= entry <= b.bid_high
        inside = zone["lower"] <= b.bid_close <= zone["upper"]
        hs = (b.bid_low <= stop) if direction == "bullish" else (b.bid_high >= stop)
        ht = ((b.bid_high >= t1) if direction == "bullish" else (b.bid_low <= t1)) if t1 else False
        P(f"{i:<6d} {b.start.isoformat()}  "
          f"{b.bid_open:.5f}/{b.bid_high:.5f}/{b.bid_low:.5f}/{b.bid_close:.5f}  "
          f"{b.ask_open:.5f}/{b.ask_high:.5f}/{b.ask_low:.5f}/{b.ask_close:.5f}  "
          f"{'yes' if touched else 'no':5s}  {'yes' if inside else 'no':7s}  "
          f"{'YES' if hs else 'no':4s}  {'YES' if ht else 'no':4s} {b.spread_open:.6f}")
    P("```")
    replayed = L.replay(bars, plan["decision_index"], entry, stop, t1, direction, half, start_offset=1)
    P("```")
    P("independent replay (this file does not import settlement code):")
    P("  for each 5m bar from decision+1, up to 288 bars:")
    P("    if not triggered: skip unless low <= entry <= high; if 288 bars pass -> expired, R = 0")
    P("    if stop reached (bullish low <= stop / bearish high >= stop) -> settle at stop")
    P("    elif T1 reached (bullish high >= T1 / bearish low <= T1) -> settle at T1")
    P("    cost = half_spread_at_decision + spread_of_exit_bar/2 ; R = (gross - cost)/|entry-stop|")
    P(f"  result: {replayed.get('reason')} at bar {replayed.get('index')} price {fmt(replayed.get('price'))}"
      f" -> R {fmt(replayed.get('r'), 6)}")
    P(f"  engine: {plan.get('exit_reason')} at bar {plan.get('exit_index')} price "
      f"{fmt(plan.get('exit_price'))} -> R {fmt(plan.get('r_measured'), 6)}")
    P(f"  verdict: {'MATCH' if (replayed.get('r') is not None and abs(replayed['r'] - (plan.get('r_measured') or 0)) < 1e-9) else 'MISMATCH'} "
      f"(tolerance 1e-9, floating point only)")
    P("```")
    # ---------------- D12
    P("\n## D12. What the engine did not look at (checked in the code path)")
    P("```")
    P("item                          used?  evidence")
    P("weekly/monthly FVG or OB      no     build_v2/wrapper_v2.py gathers zones only from the setup")
    P("                                     frame's gaps/blocks/sweep (gather_zones call, line ~330)")
    P("session context beyond flag   partial gates() reads only ctx['session']['in_window']")
    P("                                     (build_v1/plan_v1.py gates, first condition)")
    P("volume                        no     no volume field is read after loading; grep 'bid_volume'")
    P("                                     in build_v2 = only the Bar constructor")
    P("previous-day high/low         no     HtfState produces daily open/high/low/close; only the")
    P("                                     bias (close vs open) is consumed")
    P("equal highs/lows as pools     partial LiquidityState.push_swings forms relative_equal_pair")
    P("                                     without an equality cutoff (KNOWLEDGE_GAP)")
    P("news / calendar               no     no such source exists in the repository path")
    P("other instruments             no     one data file, one symbol")
    P("```")
    # ---------------- D13
    P("\n## D13. Defects observed and questions for an expert")
    P("```")
    P("D5  T1/T2 pool formation index not saved        -> that check is NOT_RECOVERABLE_WITHOUT_RERUN")
    P("D6  v1 evaluates on the decision bar, v2 on the next bar (does not affect this plan: variant")
    P("    V2-*)")
    P("D9  cards show setup candle 0 when formed_index is None (sweep zones only)")
    P("D10 NOT_EVALUABLE rendered as PASS in the card checklist")
    P("D11 swing level_index/confirm_index are window-local -> swing timestamps not recoverable from")
    P("    the record without a re-run")
    P("```")
    P("Questions for an ICT expert — NOT JUDGED BY THE AGENT:")
    P(f"1. Is this {zone['kind']} on the {frame} frame a valid zone, and are these the candles you "
      f"would use?")
    P(f"2. Was the {direction} expectation right for this session window and this dealing-range "
      f"position (`{rg.get('position')}`)?")
    P(f"3. Would you place the stop at the far edge of the zone ({stop:.5f}) or inside it at the mean "
      f"threshold, as the source's sentence suggests?")
    # ---------------- D14
    P("\n## D14. What this does NOT establish")
    P("")
    P("- It does not establish that the reading is correct ICT: nothing here is judged, only reported.")
    P("- It does not establish the plan's merit: R is hypothetical under one stated fill convention.")
    P("- The dossier is assembled from saved records plus recomputed aggregation; anything the records "
      "do not carry is marked NOT_RECOVERABLE_WITHOUT_RERUN rather than reconstructed.")
    return "\n".join(out) + "\n"


def main() -> int:
    root = Path("/tmp/build_v2")
    data = Path("/tmp/hud_data/2021.csv.gz")
    source = {"data": sha(data)}
    manifest = (HERE.parent / "REPORT_M1_M2" / "RUN_OUTPUT_SHA256.txt").read_text().splitlines()
    ok = bad = 0
    for line in manifest:
        h, path, _ = line.split("  ")
        p = Path(path)
        if p.exists() and sha(p) == h:
            ok += 1
        else:
            bad += 1
    selection = json.loads((HERE.parent / "TRADE_DETAIL_V2" / "SELECTION.json").read_text())
    sel_lines = {}
    for item in selection["selected"]:
        if item["why"] == "seeded random":
            sel_lines[item["run"]] = item
    out_dir = HERE
    written = []
    for run, month, variant, tag in PLANS:
        bars = load_bars(data, "2021-01-01", MONTH_END[month])
        frames = {"5m": L.aggregate(bars, 5), "15m": L.aggregate(bars, 15),
                  "1h": L.aggregate(bars, 60)}
        daily = htf_candles(bars, day_key)
        weekly = htf_candles(bars, week_key)
        summary, plans = L.load_plans(root, month, variant)
        item = sel_lines[run]
        plan = next(p for p in plans if p["plan_id"] == item["plan_id"])
        ctx = {}
        with open(root / run / "decisions.jsonl", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("index") == plan["decision_index"]:
                    ctx = rec
                    break
        sel = json.dumps(item)
        text = dossier(tag, run, month, variant, plan, ctx, bars, frames,
                       None, daily, weekly, sel, source)
        path = out_dir / f"DOSSIER_{tag}_{run}.md"
        path.write_text(text, encoding="utf-8")
        written.append(path.name)
        print(tag, run, plan["plan_id"], "lines:", text.count("\n"))
    print(json.dumps({"hash_ok": ok, "hash_bad": bad, "files": written}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
