# 92 — ICT-Grounded Conditional Trade-Plan Layer V1 (BUILD REPORT)

**Task**: extend the engine from market reading to an ICT-grounded
conditional trade plan — one runnable, end-to-end analytical path from
market context to a hypothetical plan, grounded in verifiable published
Michael Huddleston material and the existing project; decide without
fabricating; keep the decision ranking provisional.

---

## 1. Branch / commits / foundation

| item | value |
|---|---|
| branch | `arena/a41fd997-trading-bot` (status: active) |
| start commit (verified) | `6b11544f382cf12a898965aa40606c461d6ea469` = remote |
| **code commit** | **`750d99d00229cc9957c5f3f0828b2fef8d30939c`** — plan layer + tests + runner |
| artifacts commit | this report + `docs/research/plan_v1/run_artifacts/` (see git log) |
| sealed `information_time.py` | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` — untouched (verified before/after) |
| data | dataset commit `27c9be705ac9280248672c895082c057b979ebff`; `BTCUSDT_1m_2025-08.csv` sha256 `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` ✅; `BTCUSDT_1m_2025-09.csv` sha256 `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` ✅ |
| source material | pinned knowledge `jfjdjdieifne/test@6c8bf6fd10e9581322849485d175e825cea5a27f` (the pinned commit — the repo's default branch has moved; only the pinned commit is read) |
| environment | python 3.11.2, numpy 1.26.4, pandas 2.2.3, pytest 8.3.5, tzdata 2026.6 |
| preserved | decision layer, analysis lifecycle, selector, ledger, sealed interfaces, all prior tests and fixes (no regressions; full suite exit 0) |

## 2. The connected lifecycle (implemented and run)

`trade_plan.py` + `run_trade_plan_v1.py` produce, per valid snapshot:

1. **causal market context** across available timeframes (the analysis
   layer's records: 15m/1h/4h availability, movement direction, SP-05
   containment);
2. **structural evidence and its role** (falsifier reference + leg-end
   extreme with levels frozen into the plan);
3. **primary working interpretation** when the evidence supports a
   preference (from the decision layer), with the material alternative
   and counterevidence preserved;
4. **what the scenario waits for** — or the already-observed event,
   marked past (`observed_before_record=True`, never a pre-event claim);
5. **a hypothetical trade-plan candidate ONLY when entry, invalidation
   and objective are each definable** — with each component labeled
   `verifiable-source` or `declared-research-configuration` (see §3);
6. **an observable state** — `MONITORING` / `CONDITION_OBSERVED` /
   `HYPOTHETICAL_ENTRY_MET` / `INVALIDATED` / `MISSED` /
   `NO_JUSTIFIED_PLAN` — every state defined by observable close-based
   bindings and leg completions; no candle counts, percentages, ATR
   multiples, arbitrary horizons or confidence values;
7. **the exact next observation** that would change the scenario/plan;
8. **versioned revisions** — immutable append (`revises` links +
   revision reason) recorded in the **existing InterpretationLedger**
   (`revision_of` payloads; no parallel history).

A plan is an **analytical record, not an order**. No execution
connectivity exists. `position_status` is always `absent` — never
inferred from chart data. Missing entry/invalidation/objective yields
`NO_JUSTIFIED_PLAN` with the **specific missing evidence** — never a
guessed number and never a generic "confirmation".

## 3. Source grounding — what is source-stated vs declared

**SOURCE EXAMPLES** (exact locations, pinned knowledge `6c8bf6fd`):
| id | content | claim class |
|---|---|---|
| `SRC-EX-01-OB-ENTRY-STOP` | ICT Order Blocks lesson (`PIYh0CxoY9c`, Dec-2016 content; P1 partial transcript): OB definition ("the lowest candle or price bar with a down close that has the most range between open to close and is near a support level"); validation ("the high ... is traded through by a later formed candle"); **entry** ("when price trades higher away from the bullish order block and then returns to the bullish order block candle or price bar high"); **stop** ("the low of the bullish order block is the location of a relatively safe stop loss placement") — 05_FVG_ORDER_BLOCKS_ZONES.md §5.4/§5.4a + 08_APPLIED_CHART_CASES.md CASE-02 | directly-stated (P1; no timestamps; auto-caption caveats recorded) |
| `SRC-EX-02-INVALIDATION-GAP` | P-K: ICT-primary invalidation-by-close **NOT in the primary text read**; community close-through = separate S1 rule (05 §5.4a/§5.8) | unsupported-or-unavailable (primary) / paraphrase (community) |
| `SRC-EX-03-NO-TARGET-IN-VERIFIED-TEXT` | no target/objective definition in the verified primary text; "The available information does not select one as 'the' liquidity target without a task and a stated objective" (04_LIQUIDITY.md) | directly-stated (the refusal) |

**Plan components and their origins (identified, per requirement):**

| component | definition | origin |
|---|---|---|
| entry | the scenario's discriminating SP-03 close binding (leg-end extreme for continuation; falsifier violation for reversal) | **declared-research-configuration**. The ICT OB-return entry technique is source-stated (SRC-EX-01) but **NOT implemented**: G-OB-P is recorded NOT RUNNABLE until the owner declares the unset P-N ("near support") and P-W ("the move") slots — no values invented |
| invalidation | SP-03 close violation of the falsifier reference on its falsifying side | **engineering interpretation** of the project's falsifier semantics (pinned paraphrase T-S5/SP-04) with the ICT stop-at-extreme concept recorded (SRC-EX-01); ICT-primary invalidation-by-close = NOT in primary text (P-K) |
| objective | one completed, causally confirmed task-scale F-K leg in the plan direction, knowable after the entry bar | **declared-research-configuration**; no target definition exists in the verified material (SRC-EX-03) |

**source_agreement** (definition-level only, not a performance claim):
entry → *differs* (engine binding vs OB-return technique); invalidation →
*partially aligned* (stop-at-extreme concept; close-based operationalization is engineering); objective → *not stated in verified material*.

**What was explained only after the outcome**: nothing in the verified
examples — the lesson is procedural ("candles, validation, entries,
stops"), not a statistical result (05 §5.7); no outcome-based case is
used as evidence (08 §8.3). Retrospective material teaches methodology
only and never enters a historical decision snapshot.

## 4. Run on real data — the four required examples

Command:
```
cd project/trading_project/docs/research/plan_v1
PYTHONPATH=../../src /home/user/work/venv/bin/python run_trade_plan_v1.py \
  --run --mirror-dir /home/user/work/data/btc/mirror \
  --from 2025-08-01 --to 2025-09-30
```

60 boundaries → **32 plans + 18 no-justified-plan records** (~21 s).
Final plan states: 20 INVALIDATED · 6 CONDITION_OBSERVED ·
6 HYPOTHETICAL_ENTRY_MET. **All four required examples come from the
real data:**

**(a)+(b)+(c) `PLAN-plan-v1-0002`** covers monitored-before-condition →
entry-met → invalidated in one real sequence:
```
v1 [2025-08-13] MONITORING: awaiting the entry condition
     (the first completed task-scale bar whose CLOSE is strictly beyond
      the last leg's END extreme in the leg direction)
v2 [2025-08-14] HYPOTHETICAL_ENTRY_MET: the entry condition was observed
     at bar 76 after the plan record (observed_before_record=False)
     — a HYPOTHETICAL entry, not an order
v3 [2025-08-15] INVALIDATED: the invalidation condition was observed at
     bar 82 after the hypothetical entry (bar 76) and before the
     objective
```
**(d) no-plan with specific missing evidence** (2025-08-02):
`missing = ["evidence-supported directional preference (decision
UNRESOLVED…)", "precise falsifier reference (reference_status=
unresolved…)", "completed task-scale leg with a resolved end extreme"]`,
next discriminator: "the first completed task-scale leg's existence and
direction".

**Hypothetical plan outcomes** (mechanics only — NOT profits):
objective-before-invalidation **5** · invalidated-before-entry **19** ·
invalidated-after-entry **1** · missed **0** · open at run end **7**.
Losses/invalidations/open cases are all reported; nothing is trained on
wins. (`MISSED` — entry+objective first visible at one boundary — did
not occur in this run; its absence is reported, not filled.)

## 5. Evaluation (four separate axes, `plan_eval_v1.json`)

1. **Reproducibility & causal integrity**: append-after-T invariance and
   immutable-revision tests pass (`tests/test_contextual_trade_plan.py`);
   bindings only after the referenced point exists; post-record events
   only drive revisions; full suite exit 0.
2. **Agreement with explicit source examples**: §3 matrix (differs /
   partially aligned / not stated) — definition-level, never a
   performance claim.
3. **Observable event forecasts on later data**: carried forward from
   the fixed evaluation (train ≤ 09-06 < eval ≥ 09-11, 4 purged):
   model 10/17 (0.5882) vs ex-ante baseline `E-CONTINUATION` 6/17
   (0.3529) — **small, correlated sample; the ranking stays PROVISIONAL
   and UNVALIDATED**; 10/17 vs 6/17 establishes nothing about market
   understanding or trading readiness.
4. **Hypothetical plan outcomes**: §4 counts.

## 6. Tests

```
PYTHONPATH=src python -m pytest tests/test_contextual_trade_plan.py -q   → 10 passed
PYTHONPATH=src python -m pytest tests/ -q                                → exit 0
focused combined (decision+lifecycle+plan+selection)                     → 94 passed
```
Coverage: components labeled + no invented numbers; NO_JUSTIFIED_PLAN
with specific missing evidence; monitored-before-condition → entry met
post-record; pre-entry invalidation; MISSED definition;
CONDITION_OBSERVED at startup never a pre-event claim; append-after-T
invariance; plan-is-not-an-order; ledger revision linkage; source
register honesty.

## 7. Provenance (`plan_manifest_v1.json`)

final source commit `750d99d00229cc9957c5f3f0828b2fef8d30939c`; input
hashes ✅ both; sealed hash ✅; dependency versions as §1; run context
`historical-replay` (a replay is never an actual live observation);
`selection_quality = NOT_ESTABLISHED` throughout.

## 8. Limitations

1. Entry/objective are **declared research configurations**, not
   ICT-published rules (the source-stated OB entry technique is not
   implementable without owner-declared P-N/P-W slots — none invented).
2. No target/objective definition exists in the verified primary text;
   the leg-completion objective is an engineering choice, identified as
   such.
3. The OB/FVG zone machinery (G-OB-P/G-FVG) is not run at all (the
   foundation records it NOT RUNNABLE); zone context appears in the
   source register only.
4. 32 plans/60 boundaries on one instrument (BTCUSDT) and one task
   scale (4h, k=5 research configuration); no sensitivity analysis.
5. MISSED occurred 0 times in this run; entry-met plans are 6 (5
   objective-before-invalidation + 1 invalidated-after-entry) — thin.
6. The decision ranking remains provisional/unvalidated (axis 3); the
   hypothetical outcomes are plan MECHANICS, not profits or accuracy.

**No trades executed. No live order execution exists. No automatic PR.
No exact replication of Michael Huddleston, no proven accuracy, no
profitability is claimed.  selection_quality = NOT_ESTABLISHED.**
