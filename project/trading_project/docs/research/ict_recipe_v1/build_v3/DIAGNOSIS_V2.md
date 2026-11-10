# DIAGNOSIS V2 — counting only, from saved outputs and the verified 5m file

Source: `plans_final.jsonl` of all 16 saved runs on 2021-06, 2021-07, 2021-09 (every variant), 699
plans in total, and `/tmp/hud_data/2021.csv.gz` sha256
`38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`. No engine run. Numbers in
`DIAGNOSIS_V2.json`, produced by `diagnose_v2.py` in this folder.

**Replay caveat, stated first.** `diagnose_v2.py` has its own `replay()`; it imports no settlement
code. It reproduces the engine's `r_measured` on 175 of 587 settled plans and disagrees on 412
(agreement within 0.05 R). The cause is not isolated here, so the **absolute** R of this replay is not
the engine's R. The 1a comparison is **paired** — the same replay runs twice, once with the v2 side
convention and once side-correct — so the convention's effect is measured with the replay's own bias
held constant. Where the effect lands on a plan with sub-pip risk (288 of 699 plans have risk below
1.0 pip), one plan can move the mean by tens of R, so both the raw and the sub-pip-excluded means are
reported.

## 1a SIDE

| quantity | bullish | bearish | total |
|---|---|---|---|
| plans | 269 | 430 | 699 |
| outcome changes when the side is corrected | 18 | 30 | 48 (6.9 %) |
| mean ΔR, all plans with an R | −0.020 (n=250) | −0.910 (n=308) | — |
| mean ΔR, risk ≥ 1.0 pip | −0.029 (n=171) | −0.175 (n=222) | — |

The v2 convention (`build_v1/wrapper_v1.py` + `build_v1/plan_v1.py:262` `PlanTracker`) reads the bid
for the touch, the stop and the target alike, and charges `half_spread_at_decision + spread/2`
(two halves) as cost. The declared V3 convention: a buy triggers on the **ASK**, a sell on the
**BID**; a buy's stop and target are checked on the **BID**, a sell's on the **ASK**; the spread is
charged **once**, as `spread at the fill bar / 2`, and no other cost term exists.

## 1b STALE — the stop side taken before the fill

**126 of 699 plans (18.0 %)** have a bar, after arming and before any bar trades at the entry level,
on which the stop-side price is already beyond the stop. The engine keeps them armed and fills them
later (dossier P1 of 2021-09 V2-A: bar 53664 trades 1.17350–1.17374 over a 1.17343 entry, and the
fill only comes at 53665). V3 cancels these as `cancelled_invalidated_before_fill` and excludes them
from R.

## 1c ARMED-INSIDE — armed after the entry edge was already crossed

**544 of 699 plans (77.8 %)** are armed on a bar whose close is already past the entry edge, inside
the zone. A limit at that edge then needs price to leave the zone and come back. This is a property
of arming on a 5m close while the entry is a setup-frame edge, not a coding error, but it is the
single largest structural fact in the saved set.

## 1d T2 — the same pool twice

Of 587 plans that have a T2, **21 (3.6 %)** have T2 at exactly the same price as T1 (identity by
exact price equality; no tolerance). 11 of the 21 are in `2021-09_V2-A-OFF`, 8 in `2021-07_V2-A-OFF`.

## 1e GEOMETRY — the two plans whose T1 is behind the entry

Root cause, from the records and the code: `plan_v1.targets_ahead` filters pools for "ahead of the
trade" using `entry = bar.bid_close` (the decision bar's close), while `build_plan` then sets the
plan's entry to the **zone edge**. When the zone edge and the decision close sit on opposite sides of
the nearest pool, the pool passes the filter and lands behind the plan's own entry. The two plans:
`2021-07_V2-A …07-27T06:15…:13986` (T1 1.18023) and `2021-07_V2-A-OFF …07-13T00:15…:13011`
(T1 1.18585). V3 filters against the plan's entry and rejects with `TARGET_BEHIND_ENTRY`.

## 1f RATIO — which price the label is computed from

P1 printed `0.5968`. The entry edge (1.17343) gives 0.742; the **close of the last completed setup
candle** (1.17334) gives 0.5968. So the range label is computed from the setup candle's close, not
from the entry the plan will use. `DealingRangeState.compute` is called with `closed.bid_close`
(`build_v1/stream_v1.py:462-486`, called at `build_v2/wrapper_v2.py:118`).

Zones lying at least partly outside their own dealing range at arming: **0 of 699** (all zone bodies
sat inside). Whether a range was *formed after* the zone's last candle cannot be counted from the
saved records: the range carries `low_index`/`high_index` in window-local units while the zone
carries an absolute frame index, and no swing timestamps are saved — **NOT_RECOVERABLE_WITHOUT_RERUN**.

## 1g DISPLACEMENT USE — record-only?

It is not record-only, but it is not a gate either. Every use, by file and line:

- `build_v1/wrapper_v1.py:129` and `:151` — `if displacement.get("answer") == "YES"` → order-block
  creation and a concept counter.
- `build_v1/wrapper_v1.py:126` → `structure_shift(bar, swings, displacement)`; the shift flag is
  recorded in the decision, and in v1 it also gates `maybe_create`'s `structure_break` argument.
- `build_v2/wrapper_v2.py:96` → same, per frame; `:287` → recorded in the decision row.
- `build_v1/plan_v1.py` (gates, `rank_zones`, `targets_ahead`, `build_plan`): **no reference to
  displacement at all**. So the displacement answer never reaches a gate, the zone ranking, the stop or
  the targets. Its only route into a plan is through the creation of an `order_block` zone.

## 1h TIME

- The session window `EURO_0200_0500` is defined in **America/New_York** local clock:
  `src/trading_system/ict_engine/sessions.py:38` (`ClockVariant(..., time(2), time(5), ...)`) and
  `observe_session` converts with `candle.start.astimezone(NEW_YORK)` (`sessions.py:55`), where
  `NEW_YORK = ZoneInfo("America/New_York")` (`sessions.py:14`). DST is therefore handled.
- Data timestamps are **UTC** (`stream_v1.Bar.start`, parsed from the `Datetime` column with `Z`).
- Daily and weekly buckets used for the bias are **UTC calendar day and ISO week**:
  `build_v1/stream_v1.py:361-372` (`_keys` uses `(year, month, day)` and `bar.start.isocalendar()` at
  the bar start). Consequences: the New-York 17:00 roll is not honoured, and a Sunday-evening session
  is split across the ISO week boundary — the Sunday bars start a new ISO week at Monday 00:00 UTC,
  so Sunday 22:00 UTC bars belong to the week that is still open, and the weekly bucket rolls at
  Monday 00:00 UTC instead of Sunday 17:00 NY.
- An NY-anchored calendar exists in the engine (`ict_engine/htf.py:26-29` `CalendarAnchor.NEW_YORK`,
  used at `:61`), but the v1/v2 bias state does not use it.
- Source search for New-York anchoring of day/week/session in the repository's own material: the only
  hits in `docs/research/` are unrelated timestamp analyses (`analysis_v1/…/analysis_explanation_v1.md`,
  window `SF-SP05-*`); no card states a 17:00-NY day roll or a Sunday-17:00 week open. **KNOWLEDGE_GAP:
  NY_ANCHOR_SOURCE**.

## 1i FIELDS — what the plan record saves, and what it does not

Saved: direction, decision index and time, entry, stop, `stop_rule`, T1/T2 with kind and distance
metrics, risk, R, zone id/kind/lower/upper/`formed_index`, bias, range (with `low_index`/`high_index`
in window-local units), session, criteria and conflict flag, `half_spread_at_decision`,
`stop_fraction_of_setup_candle`, displacement answer and ratio, exit index/reason/price.

Missing: absolute swing indices and their timestamps; the confirmation candle of each swing; pool
formation indices and timestamps (v2 pools carry `formed_index` but the target pools' formation index
is not copied into the plan); per-pool class (internal/external); the position of the zone against its
range computed from the entry edge; any timestamp for the dealing range's swings. These are the
fields V3 hygiene item H5 adds.

## What this does NOT establish

- It does not establish that any of these counts is a defect in the ICT reading; they are counts of
  what the saved records contain.
- The replay caveat above means the R deltas are indicative of direction, not engine-exact.
- Stale, armed-inside and T2-same are properties of the recorded plans; how often they would recur on
  another month is not known from these three months.
