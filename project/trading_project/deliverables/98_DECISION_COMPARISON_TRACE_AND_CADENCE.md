# 98 — Decision Comparison Trace: does the engine actually compare references and FVGs in context?

Status: verified on real BTCUSDT data with a runnable decision trace,
causal stepping with ledger old/new records, and a cadence trace.
A small extension (evidence breakdown + relevance accounting) was added
to the EXISTING engine — no rebuild, no side channel. Protected causal
file unchanged. No trades or recommendations. `selection_quality =
NOT_ESTABLISHED`. Held-out `YT_tpPtItWqmlg` untouched.

Branch tip at start: `97935ae` (wipe #13 hit mid-turn: local git index
reset to `c905f2b`; all six key files on disk sha256-MATCHED
`FETCH_HEAD` → recovered with `git fetch` + `git reset --mixed
FETCH_HEAD`, no `--hard`, no work discarded; venv + BTC mirror rebuilt
pinned, mirror sha exact `15d26d23…cf4`/`e1d5c8f3…979`).

---

## 1. What the existing engine did before this change (honest gap)

The engine DID compare (conclusion categories, discriminating
criteria, alternatives, no input-order tie-break), but its candidate
records only carried criteria booleans — supporting evidence,
counterevidence, unknowns, and the candidate's relation to the HF
context/prior events were not spelled out per candidate, and the
decision trace dumped every candidate/link without relevance
accounting. The smallest useful extension (§4) makes the comparison
itself legible; nothing else changed.

## 2. Window and pause (disclosed)

- window: BTCUSDT 1m mirror, 2025-08-01 → (stepping to 08-07/08-08);
  dataset `BTCUSDT-mirror@27c9be70`.
- pause #1 = **2025-08-07 08:00** (task-scale boundary), BEFORE the
  next event (the 12:00 boundary where a reference interaction is
  observed). Task = `RT-REF-REVIEW` with **3 causally available
  competing reference candidates** (k=5 F-K points, all confirmed and
  knowable before the pause).
- pause #2 = **2025-08-07 12:00**, task = `RT-WATCH-SW-…0001` with
  **208 competing FVG candidates** observable before/at that boundary.
- both pauses and the step counts are demo choices (disclosed in the
  tool output header).

## 3. Decision trace #1 (references) — key output

(`run_artifacts/decision_trace_refs_2025-08.txt`, full text; command
below.) At pause 2025-08-07 08:00:

- **HF context**: trend=down, available/established at **2025-08-06
  12:00** (data time), evidence `SF-DIR-connected-read-v1-32`; labeled
  ENGINEERING-derived from completed structure.
- **declared task** `RT-REF-REVIEW`: "which reference's interaction
  matters for reviewing the current higher-frame reading".
  - evaluation rule (recorded in `task.declared.evaluation_rule`):
    "exactly one candidate with an observed interaction is required for
    a preference; equal or absent evidence stays UNRESOLVED" — class
    `ENGINEERING_INTERPRETATION`, explicitly **"NOT a source
    statement; an evaluation choice of this engine"**.
  - criterion: `interaction_observed` (why: it is the only observable
    discriminator available for this question).
  - conflict handling: "absence of an observed interaction is recorded
    as 'not observed' (an absence, NOT proof that no interaction
    exists); every candidate stays in the record".
- **comparison** (counts before/after filtering; nothing removed):
  - candidates before filtering: **3**; by support count: {1: 0, 0: 3};
  - display rule (disclosed, DISPLAY batching only): set ≤ 12 → all 3
    shown in detail;
  - removed from record: **0**; resource limits: "none enforced; every
    confirmed reference is evaluated".
  - each candidate shows: id, level, availability (`knowable_bar`),
    relation to context/prior events, and evidence split:
    supporting = [] (none interacted yet), unknowns = ["no interaction
    … OBSERVED yet … an absence of observation, not proof …"].
- **conclusion**: `UNRESOLVED_NO_EDGE` — "no interaction observed yet
  at any reference; nothing justifies a preference"; explicitly "no
  winner is forced and no permanent abstention is declared: a later
  version may prefer".
- **watch next** (conditional observation, NOT a prediction): the
  recorded interaction observables; the interpretation watch items.

## 4. Decision trace #2 (FVGs, competing gaps) — key output

(`run_artifacts/decision_trace_fvgs_2025-08.txt`.) At pause
2025-08-07 12:00, task `RT-WATCH-SW-connected-read-v1-0001` ("which
FVG region is the displacement/non-overlap evidence for this
shift-watch"):

- criteria (all class `ENGINEERING_INTERPRETATION`, motivated by the
  corpus E03-B sequence reading, NOT quoted as source rules):
  `observable_after_crossing`, `direction_consistent`,
  `interval_contains_crossed_level`.
- **evaluation rule**: "all declared criteria must hold (conjunction)
  for a single-candidate preference" — recorded with
  `source_status: "NOT a source statement; the source material does not
  specify this evaluation, and other evaluation rules remain possible"`.
  This fixed conjunction is an ENGINEERING choice of this engine and is
  NOT presented as Michael's universal method.
- **comparison counts**: 208 candidates before filtering;
  by support count **{0: 90, 1: 116, 2: 2, 3: 0}**; relevance rule
  (display): "at least one declared criterion met OR conflicting
  evidence recorded (categorical — no numerical threshold)";
  removed from record: **0**; resource limits: "none enforced; every
  observable region is evaluated".
- **near-satisfying competitors (2/3 criteria), each with conflicting
  evidence recorded**:
  - `FVG-…-15m-618` (15m, bounds [115566.78, 115839.71], available
    2025-08-07 10:45): supporting = direction_consistent + interval
    contains the crossed level 115720; counterevidence = the gap was
    observable BEFORE the crossing (`fvg_observable_before_crossing`);
    conflict note recorded; kept as alternative.
  - `FVG-…-1h-155` (1h, bounds [115077.37, 116347.23], available
    2025-08-07 12:00): supporting = same two; counterevidence =
    **unorderable_at_boundary** — the crossing bar labels the same
    completion boundary as the gap's observability (ordering
    uncertainty RECORDED, not guessed).
  - plus 6 disclosed examples from the support-1/support-0 groups
    (each with full supporting/counterevidence/unknowns split; one
    example is even "aligned" with the HF context yet fails all three
    criteria — context relation and criteria are separate dimensions),
    and the remaining 200 kept as counts (support distribution).
- **conclusion**: `UNRESOLVED_NO_EDGE` — "no candidate meets the
  declared discriminating criteria; no preference is forced"; 208
  alternatives recorded in the conclusion version; none deleted.

## 5. Causal stepping on the SAME decision (old vs new ledger)

**Trace #1, step 1 (12:00 boundary)**:
- `RT-REF-REVIEW` CHANGED → conclusion v2 (`revision_of` = ledger
  `T-STUDY-READING#3`), recorded_at **2025-08-07 12:00** (data time):
  `EVIDENCE_PREFERRED`, preferred `PSC:F-K(k=5)|high@2025-08-04T20:00`
  — "an interaction is actually observed at this reference and at no
  other". OLD v1 preserved unchanged (`UNRESOLVED_NO_EDGE`).
- ledger records (both kept, revision chain):
  - old `uid=T-STUDY-READING#3`, revision_of=None,
    notes `['status=UNRESOLVED_NO_EDGE', 'preferred=None']`,
    decision_time **2026-11-03 08:55:32Z** (PROCESSING wall clock);
  - new `uid=T-STUDY-READING#84`, revision_of=`T-STUDY-READING#3`,
    notes `['status=EVIDENCE_PREFERRED', 'preferred=PSC:F-K(k=5)|high@2025-08-04T20:00']`,
    decision_time **2026-11-03 08:55:42Z**.
- step 2 (16:00): **no relevant change** — conclusion still v2;
  "nothing was forced" (reported honestly).

**Trace #2, step 1 (16:00 boundary)** — the FVG decision itself:
- `RT-WATCH-SW-…0001` CHANGED → v2 (revision_of `T-STUDY-READING#85`),
  recorded_at 2025-08-07 16:00: `EVIDENCE_PREFERRED`, preferred
  `FVG-connected-read-v1-cr-4h-39` — a NEW 4h gap became observable
  after the crossing and met all three declared criteria; the recorded
  reason includes "the sequence crossing_before_fvg_observable is
  recorded as established; the region is relevant evidence only — NOT
  proof of a shift (E03-A/B) and never a trade signal".
- OLD v1 (UNRESOLVED, with the two near-misses as alternatives)
  preserved unchanged; ledger old `#85` → new `#89` (revision chain).
- conditional watch ≠ prediction: nothing in the trace asserts the
  event will occur; the watch items state observable events and what
  each would change.

## 6. Evaluation cadence — runnable trace (completion vs processing)

(`--cadence` section of `decision_trace_refs_2025-08.txt`; verified in
monitoring.py code: `step_observation` fast path vs `_run_boundary`.)

- 1m observations stream one by one. A 15m/1h bar is PUBLISHED to its
  frame as soon as its last 1m row completes (completion-labelled
  resample) — its **completion time is its label** (e.g.
  2025-08-07 07:45).
- the connected-reading pipeline runs ONLY inside `on_boundary`, i.e.
  when a **task-scale (4h) bar completes**. Between boundaries only
  `on_observation` runs (fine-touch evidence) — it does not scan FVGs
  or change interpretations.
- therefore a 15m bar closing at T is **first consumed** by the
  connected reading at the **next 4h boundary processing**, and a
  recorded interpretation can change only at that processing point.
  Example from the trace: the 16 fifteen-minute bars labelled
  04:15…08:00 were consumed at the boundary as_of 2025-08-07 08:00,
  processed at wall clock 2026-11-03T08:55:42Z.
- three timestamp classes are stored separately and never mixed:
  completion labels (region `observability_time`, facts `at`,
  conclusion `recorded_at`) = DATA times; ledger result
  `decision_time` = PROCESSING wall clock; the stream cursor position
  = consumption count.

## 7. Criteria: conjunction? source or engineering? conflicts?

- yes, a single-candidate preference requires ALL declared criteria
  (conjunction) — recorded verbatim in `task.declared.evaluation_rule`
  with `source_status: "NOT a source statement"`. The corpus does not
  specify this evaluation; the criteria are ENGINEERING choices loosely
  motivated by the E03-B sequence reading (crossing, then displacement
  evidence). No fixed conjunction is presented as Michael's method.
- conflicting evidence is handled by recording it per candidate:
  `supporting_evidence` (met criteria + the observed facts),
  `counterevidence` (unmet criteria + the contradicting observed
  facts), `unknowns` (criteria not evaluable yet — e.g. crossing time
  unknown), and a `conflict_note` for partial support; partial-support
  candidates remain in the candidate list AND in the conclusion's
  alternatives. No numerical score/ranking/confidence is computed.

## 8. The smallest extension (requirement 6) and tests

Files changed (extension only — engine, not rebuild):
- `contextual_selection/connected_readings.py`: per-candidate
  `supporting_evidence`/`counterevidence`/`unknowns`/
  `relation_to_context` (HF trend alignment + prior events)/
  `conflict_note`; `ReadingTask.comparison` (counts before/after
  filtering, relevance rule, removed-from-record=0, resource limits);
  `declared.evaluation_rule` blocks; ref-candidate `level`; `hf_trend`
  parameters. Display batching lives ONLY in the trace tool.
- `contextual_selection/study_links.py`: passes `hf_trend` into the
  two task calls.
- `docs/research/huddleston_study/run_decision_trace_v1.py`: NEW
  trace/step/cadence runner (prints; does not alter engine semantics).
- `tests/test_huddleston_connected_readings.py`: +3 focused tests
  (K: evidence breakdown incl. conflict note and rule labeling;
  L: relevance counts before/after filtering + nothing deleted +
  ref-task unknowns wording; M: breakdown future-invariance +
  save/resume round-trip of comparison state).

Commands and results (exact):

    PYTHONPATH=src python -m pytest tests/test_huddleston_connected_readings.py -q
      → 13 passed (A–J battery + K/L/M).
    PYTHONPATH=src python -m pytest tests/test_huddleston_study_links.py tests/test_contextual_monitoring.py -q
      → 25 passed (no regressions).
    PYTHONPATH=src python -m pytest tests/ -q
      → EXIT=0 (full suite; log /home/user/work/full_suite_2.log).
    python docs/research/huddleston_study/run_decision_trace_v1.py \
        --mirror-dir /home/user/work/data/btc/mirror --months 8 \
        --pause-at 2025-08-07T08:00 --step 2 --cadence \
        --out docs/research/huddleston_study/run_artifacts/decision_trace_2025-08.json
      → EXIT=0 (trace #1; artifact decision_trace_refs_2025-08.txt).
    python docs/research/huddleston_study/run_decision_trace_v1.py \
        --mirror-dir /home/user/work/data/btc/mirror --months 8 \
        --pause-at 2025-08-07T12:00 --step 1 --task RT-WATCH \
        --out docs/research/huddleston_study/run_artifacts/decision_trace_fvgs_2025-08.json
      → EXIT=0 (trace #2; artifact decision_trace_fvgs_2025-08.txt).

## 9. Limitations (honest)

- the two tasks use different evidence kinds (reference interaction vs
  FVG criteria) — a single task that jointly scores references AND
  gaps against one question does not exist yet; the missing connection
  is a shared declared question with mixed candidate kinds. This was
  NOT added because it would require inventing a combined evaluation
  rule with no supportable semantics (recorded as the next capability).
- `direction_consistent` compares region direction to the CROSSING
  direction; `relation_to_context` records HF alignment separately —
  the engine deliberately does not fuse them into one rule.
- display batching (≥2-criteria detail + 3 examples per group) is a
  DISPLAY choice with disclosed counts; the full breakdown for every
  candidate remains in the task record (see the JSON artifacts).
- unorderable chronology (same completion boundary) cannot be resolved
  without finer-than-bar path data; it is recorded as unorderable.
- evaluation cadence is task-scale (4h) by configuration; consuming
  lower-frame evidence between boundaries would require an
  `on_observation` extension of the readings pipeline — disclosed as
  current behavior, not silently claimed.

## 10. Protected file and final state

- `src/trading_system/research/information_time.py` sha256 before =
  after = `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
  (verified after all edits).
- final commit + tree status reported in the closing message.
- source agreement (S), event prediction, and hypothetical trade
  results remain separate; nothing here predicts events; selection
  quality is NOT_ESTABLISHED.
