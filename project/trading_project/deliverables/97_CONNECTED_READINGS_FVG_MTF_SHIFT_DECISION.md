# 97 — Connected Readings: Multi-Timeframe Context, FVGs, References, Shift Watches, and Decision-Making

Status: implemented, tested (focused battery A–J + full suite EXIT=0),
demonstrated on real BTCUSDT data with a pause-and-step example.
`selection_quality = NOT_ESTABLISHED`. Research only; no trades, no
recommendations, no live monitoring claims.

---

## 1. Starting point

- branch `arena/a41fd997-trading-bot`; starting commit `914d520`
  (`study-links-v3: replay artifacts … + report 96`).
- workspace `/home/user/TRADING-BOT` (recovered from wipe #12 by
  `git fetch` + `git reset --mixed FETCH_HEAD` + sha256 verification of
  key files against `FETCH_HEAD`; no `reset --hard`, no untracked work
  discarded).
- data: BTCUSDT 1m mirror in `/home/user/work/data/btc/mirror`
  (`dataset identity BTCUSDT-mirror@27c9be70`), months 2025-08/09.

## 2. Reused components

- `InterpretationLedger` (csm) — extended, never bypassed.
- `AnalysisEngine` + `MonitoringLoop` + `ReplayObservationStream`
  (existing causal monitoring path; the study layer runs inside
  `on_boundary` — no second engine, no side channel).
- `StudyReasoningLayer` (study_links.py): HF context, structural
  references (F-K points), evidence-evaluated roles, E03 shift-watches.
- sealed `research/information_time.py` — untouched (sha in §13).

## 3. Files changed

| file | change |
|---|---|
| `src/.../contextual_selection/connected_readings.py` | NEW module: `FVGRegion`, `FrameLink`, `ReadingTask`, `WorkingInterpretation`, `ConnectedReadingsEngine`, declared geometry/sources/unknowns constants |
| `src/.../contextual_selection/study_links.py` | `StudyReasoningLayer` wiring: readings pipeline in `on_boundary`, state save/resume, `watch_plan` entries, `instrument` parameter |
| `src/.../contextual_selection/csm.py` | `InterpretationLedger.to_state()/load_state()` (full ledger persistence for save/resume; additive only) |
| `src/.../contextual_selection/monitoring.py` | `state_dict`/`load_state` persist and restore `ledger_state` (no parallel history) |
| `tests/test_huddleston_connected_readings.py` | NEW battery A–J (10 tests) |
| `docs/research/huddleston_study/run_connected_reading_v1.py` | NEW pause-and-step runner (real data) |
| `docs/research/huddleston_study/run_artifacts/connected_reading_demo_2025-08.txt` | saved pause-and-step output excerpt |
| `deliverables/97_…` (this file) | report |

## 4. FVG definition and availability

Declared in `connected_readings.FVG_GEOMETRY_DEFINITION` (S/E-labeled):

- three CONSECUTIVE COMPLETED bars (b1, b2, b3) on the declared
  timeframe and bar construction (completion-labelled resample of the
  1m source).
- UPWARD when `b3.low > b1.high` → interval `[b1.high, b3.low]`;
  DOWNWARD when `b3.high < b1.low` → interval `[b3.high, b1.low]`.
- the 50% midpoint of the interval (external term "Consequent
  Encroachment") is stored as a reference LEVEL only — never a rule.
- **availability**: observable ONLY at bar3's completion label
  (`observability_time`); `FVGRegion.availability(as_of)` returns
  "not_yet_observable …" before that label and "observable since …"
  after; the engine never records a region from fewer than three
  completed bars; bars between completion labels are never treated as
  observable content (an incomplete bar is not presented as a closed
  fact).
- each region record carries: timeframe, instrument (BTCUSDT/TEST),
  timezone, session convention (24h crypto; the US-index first-gap
  session clock does NOT apply), bar convention, source note
  (external secondary references + corpus FVG16-A (S); bounds and
  availability handling (E)), `unknowns`, `hidden_assumptions`, and
  `interpretation_notes` with explicit layers
  (DIRECT_OBSERVATION / DERIVATION / CONTEXTUAL_INTERPRETATION /
  UNKNOWN_UNSUPPORTED).
- revisit status: subsequent completed bars are checked for
  `range_overlaps_interval` / `range_covers_interval` /
  `ce_midpoint_in_range` (observed range relations only — "rebalanced"
  is kept as a coverage relation, never a guarantee), all from data ≤
  as_of.
- what cannot be inferred is enumerated in `FVG_UNKNOWNS` (intrabar
  path, orders/intent, fill inevitability, cross-TF identity, any
  entry/target/reversal signal).

## 5. Multi-timeframe linkage (never interchangeability)

- `link_regions` records `FrameLink`s between observable regions and
  structural references / other-frame regions. Relations:
  `interval_contains_level`, `level_equals_ce_of_interval`,
  `intervals_overlap`; `intervals_disjoint` is a STATED non-relationship
  recorded only for explicitly compared pairs (task candidates) —
  trivial all-pairs disjointness is noise and is not recorded.
- every link note states: "NOT an identity claim: different timeframes
  keep different representations (FVG16-A)". Overlap ≠ same origin,
  significance, or outcome.
- WHY a timeframe matters is recorded where it is used: reading tasks
  declare `frame_scope` and per-candidate `timeframe` + `availability`;
  the HF interpretation records which derived context is used for the
  task and its derivation time.
- reference choice is never automatic (largest/nearest/newest): the
  `RT-REF-REVIEW` task declares its criteria and keeps every candidate
  with an `alternatives_note`.
- real data (window 2025-08-01 → 08-07 + 3 4h steps): 208 regions
  (15m: 171, 1h: 31, 4h: 5, 1D: 1) — the same movement produces
  completely different gap geometry per frame; 648 links (599
  interval-overlap, 49 interval-contains-reference-level).

## 6. Comparison method (selection/decision)

- `ReadingTask`s are declared questions with declared discriminating
  criteria (`class: ENGINEERING_INTERPRETATION`), e.g. for shift-watch
  FVG relevance: `observable_after_crossing` (chronology actually
  established), `direction_consistent`, `interval_contains_crossed_level`.
- conclusions ∈ {`EVIDENCE_PREFERRED`, `PROVISIONAL_WORKING_BASELINE`,
  `UNRESOLVED_NO_EDGE`}; exactly-one-criteria-met → preference with the
  discriminating evidence named; equal evidence → UNRESOLVED with the
  reason "the evidence does not discriminate — no input-order tie-break
  is used"; nothing forced; no numerical ranking or confidence %.
- every conclusion version records: discriminating evidence,
  alternatives (each non-preferred candidate with why-not), watch-next
  items (observable event / would-change / would-weaken / alternative
  remains / cannot establish), and `revision_of` chain.
- chronology per candidate is recorded as established
  (`crossing_before_fvg_observable` / `fvg_observable_before_crossing` /
  `unorderable_at_boundary: the crossing bar labels the same completion
  boundary as the FVG's observability`) — never guessed.

## 7. One preferred case + one unresolved case (real data)

Window 2025-08-01 → 2025-08-07T00:00 pause, then 3 completed 4h steps:

- **preferred**: `RT-REF-REVIEW` v2 at `2025-08-07 12:00` →
  `EVIDENCE_PREFERRED`, preferred
  `PSC:F-K(k=5)|high@2025-08-04T20:00` — reason: "an interaction is
  actually observed at this reference and at no other (for the declared
  review task)". v1 (recorded `2025-08-01 04:00`) was UNRESOLVED and is
  preserved unchanged.
- **unresolved**: `RT-WATCH-SW-connected-read-v1-0001` v1 at
  `2025-08-07 12:00` → `UNRESOLVED_NO_EDGE`, preferred=None —
  reason: "no candidate meets the declared discriminating criteria; no
  preference is forced". All ~40 FVG candidates are retained as
  alternatives with explicit why-not (criteria not all met).
- (also demonstrated in tests C/D/E: same FVG under two HF contexts →
  different relevance with evidence+alternatives; competing references
  → one justified preference + one unresolved, shuffled input order
  gives the same conclusion.)

## 8. Pause-and-step example

Command (`run_connected_reading_v1.py`, real BTCUSDT 1m mirror):

    python docs/research/huddleston_study/run_connected_reading_v1.py \
        --mirror-dir /home/user/work/data/btc/mirror --months 8 \
        --stop-at 2025-08-07T00:00 --state /home/user/work/cr_state.json \
        --step-advance 3 --out-dir docs/research/huddleston_study/run_artifacts

- **initial pause (2025-08-07 00:00)** shows: HF context (trend=down,
  established 2025-08-06 12:00, evidence SF-DIR-connected-read-v1-32),
  structural references (1 task-frame candidate), 185 FVG regions with
  bounds/timeframe/observability/CE midpoint/interactions, 500
  cross-timeframe links (relations only), 0 shift-watches at that time,
  reading task `RT-REF-REVIEW` = UNRESOLVED (no interaction observed
  yet), working interpretation `INT-HF-CONTEXT` v2, watch-next items
  and the unknowns list. Saved excerpt:
  `run_artifacts/connected_reading_demo_2025-08.txt`.
- **stepping** (3 completed 4h bars: 04:00 / 08:00 / 12:00):
  - step 04:00 and 08:00: new observed content only (regions 185→192→199,
    links 500→537→588, facts 224→233→240) — recorded as new
    observations, no conclusion change;
  - step 12:00: regions 199→208, links 588→648; shift-watch `SW-connected-read-v1-0001` opened (WATCHING;
    crossing bar 2025-08-07 12:00) on the recorded reference
    interaction; `RT-REF-REVIEW` RE-VISIONED v1→v2 (UNRESOLVED →
    EVIDENCE_PREFERRED, see §7); `INT-WATCH-…0001` created (both
    "shift occurred" and "no shift is developing" remain listed as
    UNSUPPORTED alternatives); honest no-change was printed for any
    step where nothing changed.
- window selection: pause boundary and the 3 steps were demo-chosen
  (disclosed); nothing about the market is claimed from this choice.

## 9. Old and new interpretation versions (evidence + times)

`INT-HF-CONTEXT` (side by side; old preserved byte-stable):

| v | revision_of | status | statement | reason | evidence | available at |
|---|---|---|---|---|---|---|
| 1 | — | WORKING | "higher-frame context: up …" | initial interpretation at creation | `SF-DIR-connected-read-v1-27` (DERIVATION) | 2025-08-05 16:00 |
| 2 | 1 | REVISED | "higher-frame context: down …" | "higher-frame context changed from up to down on new completed structure" | `trend_change:up->down` (DERIVATION) | 2025-08-06 12:00 |

Also `RT-REF-REVIEW` v1→v2 (§7). Revisions append a new linked version
(`revision_of` chain, in both the task/interpretation records and the
ledger task `T-STUDY-INTERPRETATION`); the old version is never edited;
a weakening hypothesis never flips automatically to its opposite
(`revise()` records status `REVISED`, not an invented reversal).

## 10. Save / resume

- state covers: FVG regions (geometry + interactions + notes),
  cross-timeframe links + seen-keys, reading tasks (candidates +
  conclusion versions + alternatives), working interpretations
  (versions + revisions), sequence facts, frame cursors, ledger uid
  chains; and now the FULL `InterpretationLedger` state
  (`to_state`/`load_state`: results, versions, payloads, events,
  revisions, uid sequence) via `MonitoringLoop.state_dict/load_state`.
- real-data check (`--verify-resume`, T1=2025-08-07T00:00,
  T2=2025-08-09T00:00): study_state (2,629,763 chars) from a NEW
  process resuming the saved state is byte-identical to the continuous
  run → **PASS** (`run_artifacts/verify_result.json`).
- test G (in-process) and test H (engine-level round trip incl. ledger)
  also pass.

## 11. Cadence and resolution limits

- re-evaluation happens at task-scale (4h) bar completion — the study
  layer runs `on_boundary` inside the monitoring loop;
- lower-frame (15m/1h) bars DO update FVG scans, interactions,
  links and shift-watch evidence **as they complete** (their own
  completion labels), because the frames builder publishes completed
  15m/1h bars to the same loop; a lower-frame FVG is still never proof
  of a shift — it is classified (relevant evidence / competing
  reference / to monitor / irrelevant / unresolved) with reasons;
- 1m touch behaviour: this engine does not run at 1m; touches are
  resolved at the finest PUBLISHED frame (15m) as range-containment on
  completed bars — intra-15m ordering is unknown and recorded as such;
- anything finer (tick path inside a bar, intra-bar order of two
  interactions at the same label) needs finer data than the dataset
  provides and is recorded as an unorderable/unknown, never guessed.

## 12. Test commands and results (exact)

    PYTHONPATH=src python -m pytest tests/test_huddleston_connected_readings.py -q
      → 10 passed (battery A–J):
        A FVG observability never before bar3 + bounds; B different
        timeframes never identical representation + link ≠ identity;
        C same FVG two contexts → different classification, evidence +
        alternatives, no direction⇒valid rule; D competing references →
        one justified preference + one unresolved, shuffled input order
        identical, no silent deletion; E shift-watch sequence preserved
        incl. unorderable boundary case, "NOT proof", no shift/trade
        words; F revision appends linked version, old byte-stable, no
        auto-opposite; G no-change observation invents nothing;
        H save/resume preserves FVG/links/alternatives/watch/ledger;
        I future-data invariance (as-of T identical with/without later
        data); J source/engineering/unknowns distinguishable.
    PYTHONPATH=src python -m pytest tests/test_huddleston_study_links.py tests/test_contextual_monitoring.py -q
      → 25 passed (13 study + 12 monitoring, no regressions).
    PYTHONPATH=src python -m pytest tests/ -q
      → EXIT=0 (full suite; log /home/user/work/full_suite.log).
    python docs/research/huddleston_study/run_connected_reading_v1.py … (§8)
      → EXIT=0; --verify-resume → PASS.

Failures encountered during development and fixed (recorded honestly):
link-key collision across save/resume (pipe-join of ids containing
'|'), tz-naive vs tz-aware comparison in the runner, run-scoped region
ids in test-I comparison, initial-version recording for
interpretations, `observable_after_crossing` semantics alignment in
tests. No test was disabled or weakened to pass.

## 13. Protected file hash

- `src/trading_system/research/information_time.py`
  sha256 before = `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
- sha256 after = `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
  (unchanged; verified after all edits)

## 14. Source vs engineering vs unknown

- **(S) source**: three-candle wick non-overlap geometry (external
  secondary references + corpus FVG16-A, which also requires storing
  the gap with its originating timeframe and relating it to previously
  available references without promoting it to inevitable fill); E03
  "crossing = context for watching, not proof"; CE midpoint term
  (external secondary reference) as a level.
- **(E) engineering**: exact interval bounds from published OHLC,
  observability = bar3 completion label, the three discriminating task
  criteria, link-relation vocabulary, conclusion categories, revision
  chaining, ledger integration. All labeled in-code with `(S)`/`(E)` or
  `class:` fields.
- **(unknown/unoperable)**: "price traded to or through" a level needs
  tick/1m path data — implemented as the documented range-containment
  proxy and labeled; intrabar ordering of two same-label interactions
  recorded as unorderable; institutional intent/orders/fill claims are
  out of scope by design. External trade-execution parts of the
  references (entries/stops/targets) were explicitly NOT implemented.

## 15. Final state and next capability

- commits: code + tests (this commit), runner/artifacts + this report
  (second commit) on `arena/a41fd997-trading-bot`, pushed; tree clean
  except the standing keep-outs (`real_chart_study/`,
  `REAL_CHART_ELEMENT_APPLICATION_STUDY_V1.md`, `dataset_v1/`).
- held-out `YT_tpPtItWqmlg` (Ep13) untouched — no held-out result
  exists or is claimed.
- next missing capability: the watch-revisit engine's revisit-event
  precision is limited to completed-bar range relations on the finest
  published frame (15m); true intra-bar sequence ("price traded through
  then recovered") needs 1m-or-finer touch evaluation inside the
  causal boundary — that extension (and only that) is the next step.
