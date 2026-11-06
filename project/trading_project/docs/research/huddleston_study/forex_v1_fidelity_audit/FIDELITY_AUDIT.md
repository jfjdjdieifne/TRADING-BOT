# Forex V1 — Fidelity, Constant-Inventory and Lookahead Audit

Audit date: 2026-11-05. Branch: `arena/e6974afe-trading-bot`.
Audited commit: `871041c152f34f6792f39024a62ef1d0fd5dada2`.
Protected file `information_time.py`: SHA-256 `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`, size 12216 — verified unchanged at audit end.
Data: `/tmp/forex-data` @ `56d5f04fd90b29414a70147471309f1db326aa1c`; `2025.csv.gz` SHA-256 `1fa2dca207e3a8a1de37bfcd7653b15ebcffb933c05b4d4e3a4831aaa84d9647` — verified.
No May 2025 data influenced any result. The reported PART 3 and PART 4 runs consumed a pre-filtered copy containing only rows < 2025-03-01 (16 992 rows; max timestamp 2025-02-28 23:55 UTC). Two preliminary runs used the original full-year file via the stock loader (`load_bidask`, runner L90–111), which reads the annual CSV then filters to `[t0, t1)` before any analysis; their case records were verified byte-identical to the filtered runs (439 cases, full equality). No row dated 2025-05-01 or later entered any decision, plan, or outcome.

## Source-document authorship and status

Every document below was committed by the same GitHub account (`jfjdjdieifne`). Git authorship alone cannot distinguish "original material" from "agent summary"; the content must be inspected.

| Document | Git date / message | Status |
|---|---|---|
| `docs/domain_audit/ICT_SOURCE_AUDIT.md` | 2026-10-01 / Initial import | Agent-produced research audit. Not original ICT text. |
| `docs/domain_audit/SOURCES.md` | 2026-10-01 / Initial import | Agent-produced source list. Not original ICT text. |
| `docs/research/huddleston_study/EXTENDED_STUDY_FIVE_VIDEOS.md` | 2026-11-02 / study-links-v1 | Agent-produced study summary. Line 3: "نزّلت المسار الصوتي الأصلي كاملًا لكل فيديو، وحوّلته محليًا إلى نص إنكليزي مؤقّت آليًا ببرنامج faster-whisper tiny.en". Line 60: "تحويلها إلى تمثيل سببي في الكود ENGINEERING_INTERPRETATION". |
| `docs/research/huddleston_study/corpus_full_pass.json` | 2026-11-02 / study-links-v1 | Agent-produced corpus. `timing_note` (L25): "Segment times are approximate ASR alignment, NOT human-verified speech timestamps… Clips and audio remain research-time only in non-persistent cache." The actual transcript text is NOT in this repository. |
| `docs/research/real_chart_study/dataset_v1/source_reliability_hindsight_v1.md` | 2026-11-05 / Unify Forex branch | Agent-produced reliability report. |
| `docs/research/real_chart_study/dataset_v1/ICT_CHART_APPLICATION_LEARNING_DATASET_V1.md` | 2026-11-05 / Unify Forex branch | Agent-produced dataset documentation. |
| `deliverables/89_CONTEXTUAL_MARKET_ANALYSIS_ENGINE_V1_REPORT.md` | (build report) | Agent-produced. L270 references pinned knowledge `jfjdjdieifne/test@6c8bf6fd` — that repo is NOT present in this checkout. |
| `deliverables/92_ICT_GROUNDED_TRADE_PLAN_LAYER_REPORT.md` | (build report) | Agent-produced. L63–65 quote SRC-EX-01/02/03 from the same absent pinned repo. |
| `src/…/contextual_selection/trade_plan.py` SOURCE_EXAMPLES (L147–231) | 2026-11-01 / plan-v1 | Code-embedded quotes attributed to pinned knowledge `jfjdjdieifne/test@6c8bf6fd10e95813` (L145). The pinned repo is NOT in this checkout; the quotes cannot be independently verified here. |

**Critical finding:** No original ICT/Huddleston transcript text exists in this repository. All "source quotes" available for comparison are (a) agent paraphrases classified as PARAPHRASE or DIRECT_STATEMENT in `corpus_full_pass.json`, (b) quotes embedded in `trade_plan.py` attributed to an external pinned repo not present here, or (c) agent audit summaries. The original YouTube videos are the primary material; they are not in the repo.

---

## PART 1 — Fidelity matrix

Classification key: DERIVED-FROM-SOURCE = code matches an available source statement; PARTIAL = some alignment but operationalization differs or source is paraphrase-only; RESEARCH-CHOICE = declared engineering configuration with no source mandate; ARBITRARY = numeric value with no source or empirical derivation; NOT-IMPLEMENTED = source concept exists but code does not implement it.

| # | Concept | Available source quote (file:line) | Code implementation (file:line) | Class | What differs |
|---|---|---|---|---|---|
| 1 | Context (4 categorical features) | No source found defining these 4 features. | `decision_layer.py` L201–229 `extract_context`: returns `{direction, ref_status, sp05, fc_status}`. | RESEARCH-CHOICE | The 4-feature context key is an engineering design. No source mandates this representation. |
| 2 | Market structure / direction | `ICT_SOURCE_AUDIT.md` L44: "confirmed structural-level close break plus prior sequence state." `corpus_full_pass.json` L79: "Crossing an old low/high is a context for WATCHING a possible shift, not proof of one (DIRECT_STATEMENT/PARAPHRASE)." | `analysis_lifecycle.py` L601–618: direction = last completed F-K leg's direction. No MSS/BOS/CHoCH detector on this path. | PARTIAL | Source describes structural-level close break; code uses F-K leg completion as direction proxy. The audit itself labels this APPROXIMATION (L46). |
| 3 | Swing / leg definition (F-K k-bar pivot) | `deliverables/89…` L270: "F-K knowability… `paraphrase`… verified against the pinned register". Pinned repo absent. `deliverables/89…` L294: "P-ORIGIN-RESEARCH is research configuration (k=5, 4h task scale, role semantics), never an owner-approved analytical policy." | `csm.py` L887–993 `fk_turning_points`: k-bar left/right confirmation, supersession, causal knowable_bar = i+k. `csm.py` L1170–1229 `build_legs`: consecutive alternating confirmed points. | RESEARCH-CHOICE | k=5 is declared research configuration. The F-K algorithm is an engineering operationalization; the pinned source is a paraphrase register, not original ICT text. |
| 4 | FVG (three-candle non-overlap) | `ICT_SOURCE_AUDIT.md` L86–87: "three-candle non-overlap geometry… strict `low[i] > high[i-2]` / inverse geometry, causal creation at bar three." L88: "MATCH on operational geometry". | `connected_readings.py` L413–418: `if b3["low"] > b1["high"]` → upward; `elif b3["high"] < b1["low"]` → downward. Three consecutive completed bars. | DERIVED-FROM-SOURCE | Geometry matches the audit's operational description. The audit notes "intentional departure on 'inefficiency' claims" (L88). |
| 5 | Reference selection (T-S5 role) | `deliverables/89…` L270: "T-S5/SP-04 falsifier semantics… `paraphrase`". `analysis_lifecycle.py` L485–488: "origin-of-last-confirmed-leg (SWS-02; research configuration, never owner-approved)". | `analysis_lifecycle.py` L943–984: reference = `sel.candidate_id` from expert selection, role = origin-of-last-confirmed-leg. `csm.py` L1420–1500 `task_s1_structural_reference`. | PARTIAL | Role semantics are declared research configuration. Source is paraphrase of absent pinned register. |
| 6 | I-primary (continuation) | `corpus_full_pass.json` L79: "Crossing an old low/high is a context for WATCHING a possible shift, not proof of one". `EXTENDED_STUDY…` L60: "تحويلها إلى تمثيل سببي في الكود ENGINEERING_INTERPRETATION". | `analysis_lifecycle.py` L1018–1061: I-primary = "movement-continuation", status active/invalidated based on SP-03 violation of reference. | RESEARCH-CHOICE | Source says "watching, not proof"; code emits a directional continuation interpretation with falsifier. The study doc explicitly labels this ENGINEERING_INTERPRETATION. |
| 7 | I-scenario (unresolved reference) | No source found. | `analysis_lifecycle.py` L1063–1101: I-scenario emitted when reference is unresolved; "alternative-monitoring" status. | RESEARCH-CHOICE | Pure engineering construct for handling unresolved references. |
| 8 | I-alt (reversal) | `corpus_full_pass.json` L280: "If high is taken, he says he is probably wrong and should seek more information / sit on hands (DIRECT_STATEMENT)." L282: "Pause/reassess rather than mechanically reverse when violated (PARAPHRASE)." | `analysis_lifecycle.py` L1104–1130: I-alt = "movement-reversal", alternative-monitoring. `trade_plan.py` L509–513: scenario = reversal when primary_interpretation_id != I-primary. | PARTIAL | Source supports invalidation-on-violation and pause/reassess. Code creates a reversal interpretation and can trade it. Source says "pause/reassess rather than mechanically reverse"; code does mechanically reverse via the plan layer. |
| 9 | Entry rule | `trade_plan.py` L170–172 (SRC-EX-01): "when price trades higher away from the bullish order block and then returns to the bullish order block candle or price bar high". `trade_plan.py` L322–325: "ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable". | `trade_plan.py` L296–345 `build_components`: entry = SP-03 close binding of leg-end (continuation) or falsifier violation (reversal). `definition_origin = declared-research-configuration`. | RESEARCH-CHOICE | The source-stated OB-return entry is explicitly NOT implemented. Code uses a different entry (SP-03 close binding). The code itself declares this. |
| 10 | Invalidation rule | `trade_plan.py` L172–174 (SRC-EX-01): "the low of the bullish order block is the location of a relatively safe stop loss placement". `trade_plan.py` L202–205 (SRC-EX-02): "INVALIDATION: 'Not in primary text read' (P-K)". | `trade_plan.py` L303–305 / L311–315: invalidation = SP-03 close violation of falsifier reference. `csm.py` L1365–1378 `sp03_binding`: close strictly beyond level. | PARTIAL | Stop-at-extreme concept exists in source. Close-based invalidation is engineering/community-influenced, not ICT-primary (code states this at L332–334). |
| 11 | Target / objective rule | `trade_plan.py` L218–221 (SRC-EX-03): "The available information does not select one as 'the' liquidity target without a task and a stated objective". | `trade_plan.py` L335–344: objective = "one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar". `definition_origin = declared-research-configuration`. | RESEARCH-CHOICE | No target definition exists in verified source. Code uses F-K leg completion as objective. Declared research configuration. |
| 12 | SP-03 (close-based binding) | `deliverables/89…` L270: "SP-03 close binding… `paraphrase`… verified against the pinned register". Pinned repo absent. | `csm.py` L1365–1378: `close_price > r.level` (up) or `close_price < r.level` (down); equality is NOT a crossing (TIE-CROSS-EQUAL-UNBOUND-V1). | PARTIAL | Operationalization matches the paraphrase description. Original source text not available for independent verification. |
| 13 | Gate v1 (connected gate) | No source found. Runner L403–405: "V1 connected gate: a strict decision preference AND the connected readings do not contradict (research configuration, declared; no thresholds, no forced trades)." | `run_forex_intraday_v1.py` L402–453 `gate_v1`: blocks if no strict preference; blocks if EVIDENCE_PREFERRED FVG opposes intended direction. | RESEARCH-CHOICE | Entirely engineering. No source mandates this gate logic. |
| 14 | Gate b0 (baseline) | No source found. Runner L456–459: "BASELINE B0 (explicitly defined simple baseline): act on every strict decision preference WITHOUT consulting the connected readings." | `run_forex_intraday_v1.py` L455–464 `gate_b0`: blocks only if no strict preference. | RESEARCH-CHOICE | Comparison baseline. No source. |
| 15 | Timeframe choice (TASK_SCALE=1h, READINGS_SCALE=15m) | No source found mandating 1h task scale for forex. `EXTENDED_STUDY…` L23 mentions 2-minute chart; L43 mentions 5/15-minute. `deliverables/89…` L294: "4h task scale" for BTC. | `run_forex_intraday_v1.py` L81–82: `TASK_SCALE = "1h"`, `READINGS_SCALE = "15m"`. | RESEARCH-CHOICE | The BTC engine used 4h; the forex runner changed to 1h. No source mandates either. |
| 16 | TASK_SCALE value | Same as #15. | `run_forex_intraday_v1.py` L81: `TASK_SCALE = "1h"`. | ARBITRARY | The specific value "1h" has no source or empirical derivation stated. It is a declared research choice. |

---

## PART 2 — Constant inventory

Every hard-coded numeric threshold, window, count, weight, or tolerance in the five audited files. Structural indices (0, 1 for slicing/versioning) are omitted; only values that control behavior are listed.

### run_forex_intraday_v1.py

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 83 | `K = 5` | F-K confirmation window (bars) | `deliverables/89…` L294: "k=5… research configuration". No empirical derivation. |
| 85 | `HORIZON_BARS = 12` | Episode label horizon (task-scale bars = 12h) | No source found. `decision_layer.py` L182: "EPISODE_HORIZON_BARS = 24 is NOT source-grounded". Runner overrides to 12. No derivation stated for 12. |
| 115 | `1440` | 1D frame width (minutes) | Unit conversion. Not a research parameter. |
| 115 | `240` | 4h frame width (minutes) | Unit conversion. |
| 116 | `60` | 1h frame width (minutes) | Unit conversion. |
| 116 | `15` | 15m frame width (minutes) | Unit conversion. |
| 182–186 | `2.0` | Mid-price = (bid+ask)/2 | Arithmetic definition of mid. Not a research parameter. |
| 318 | `1e4` | Pips conversion (EURUSD pip = 0.0001) | Market convention for EURUSD. Not a research parameter. |
| 323 | `2` | `round(pips, 2)` — display precision | Arbitrary display choice. |
| 473 | `500` | Progress print interval (decisions) | Arbitrary UI choice. |
| 737 | `3` | `--step` default (pause-and-step) | Arbitrary demo choice. |

### trade_plan.py

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 599–600 | `+ 1` | Scan starts at reference/leg-end occurrence bar + 1 | Causality: a binding is meaningful only AFTER the point exists. Engineering rule. |
| 603 | `0`, `1` | Range bounds for scan | Structural. |

No numeric thresholds, weights, or tolerances exist in `trade_plan.py`. All entry/invalidation/objective logic is categorical (SP-03 close binding, F-K leg completion). The file explicitly states (L467–468): "no probabilities, no candle counts, no percentages, no ATR multiples and no confidence values are used or implied".

### analysis_lifecycle.py (analysis engine)

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 500 | `k: int = 5` | Default F-K confirmation window | Same as runner K=5. Research configuration. |
| 507 | `1` | `if k < 1: raise` — minimum k | Logical minimum. |
| 438 | `3` | `supporting_evidence[:3]` — display truncation | Arbitrary display limit. |
| 440 | `3` | `opposed_evidence[:3]` — display truncation | Arbitrary display limit. |
| 442 | `2` | `alternative_explanations[:2]` — display truncation | Arbitrary display limit. |
| 566 | `12` | SHA-256 hex digest truncation for IDs | Arbitrary ID length. |
| 767 | `5` | `post[:5]` — violation evidence truncation | Arbitrary display limit. |
| 815 | `5` | `before[:5]` — violation evidence truncation | Arbitrary display limit. |
| 890 | `5` | `post[:5]` — violation evidence truncation | Arbitrary display limit. |
| 962 | `5` | `viol[:5]` — invalidating observations truncation | Arbitrary display limit. |
| 972 | `6` | `sel.evidence[:6]` — selection evidence truncation | Arbitrary display limit. |
| 995 | `3` | `survivors[:3]` — per-survivor readings limit | Arbitrary display limit. |
| 1014 | `2` | `derived-frame-availability[:2]` — support truncation | Arbitrary display limit. |
| 1147 | `3` | `survivors[:3]` — readings limit | Arbitrary display limit. |
| 1231 | `3` | `incomplete.index[-3:]` — incomplete leg display | Arbitrary display limit. |
| 1264 | `8` | `active_fvs[:8]` — forecast version limit | Arbitrary display limit. |
| 1378 | `8` | `sel.evidence[:8]` — selection evidence truncation | Arbitrary display limit. |
| 1379 | `8` | `sel.conflicts[:8]` — conflict truncation | Arbitrary display limit. |
| 1413 | `8` | `sel.evidence[:8]` — evidence truncation | Arbitrary display limit. |

### decision_layer.py (context extraction + decision)

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 179 | `EPISODE_HORIZON_BARS = 24` | Default episode label horizon | L182–192: "NOT source-grounded, NOT owner-approved, and NOT a market rule: it is a declared engineering parameter". Runner overrides to 12. |
| 802 | `2/3` | `train_fraction` default for chronological split | No source found. Arbitrary split ratio. |
| 866 | `4` | `round(…, 4)` — coverage precision | Arbitrary display precision. |
| 868 | `4` | `round(…, 4)` — hit rate precision | Arbitrary display precision. |
| 870 | `4` | `round(…, 4)` — hit rate precision | Arbitrary display precision. |
| 929 | `4` | `round(…, 4)` — baseline hit rate precision | Arbitrary display precision. |
| 952 | `4` | `round(…, 4)` — no-edge frequency precision | Arbitrary display precision. |

### csm.py (referenced by runner; core geometry)

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 910–911 | `k < 1` | Minimum k validation | Logical minimum. |
| 1294 | `tie_inclusive: bool = True` | SP-05 containment boundary tie rule | L1295–1296: "declared policy (SWS-06; TIE-BOUNDARIES-INCLUSIVE-V1 default)". Research configuration. |
| 1366 | `tie_bound: bool = False` | SP-03 equality-is-not-crossing rule | L1368–1369: "TIE-CROSS-EQUAL-UNBOUND-V1 default: equality is not a crossing". Research configuration. |
| 1014 | `tau <= 0` | F-T threshold minimum validation | Logical minimum. F-T not used on the forex path (F-K only). |

### connected_readings.py (FVG detection)

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 200 | `2.0` | CE midpoint = (lower+upper)/2 | Arithmetic midpoint. `ICT_SOURCE_AUDIT.md` L97: "commonly used for midpoint/50% of an imbalance". |
| 405 | `n - 2` | Three-bar window (j, j+1, j+2) | Three-candle FVG geometry. Source: `ICT_SOURCE_AUDIT.md` L86. |

### study_links.py

| Line | Value | Controls | Source / derivation |
|---|---|---|---|
| 721 | `k: int = 2` | Default k for StudyReasoningLayer | Overridden by runner K=5. No source for default 2. |
| 722 | `task_scale: str = "4h"` | Default task scale | Overridden by runner TASK_SCALE="1h". No source for default. |

---

## PART 3 — Learning check

### What the dev model stores

`run_forex_intraday_v1.py` L648–654 `model_state`: serializes `{"kind": "context-event-model-v1", "counts": [[context_key, {event: count}]], "n_episodes": int, "trained_through": timestamp}`.

`decision_layer.py` L412–432 `ContextEventModel.fit`: accumulates per-context event counts from chronological training episodes. The context key is `(direction, ref_status, sp05, fc_status)` (L232–234). Events are E-CONTINUATION, E-VIOLATION, E-NONE-IN-HORIZON, E-AMBIGUOUS-SAME-BAR (L101–105).

The January-trained model (`/tmp/rerun_out/dev/dev_model.json`) contains 468 fitted episodes, `trained_through = 2025-01-31 10:00:00+00:00`.

### Experiment

Two eval runs on identical filtered data (2025-02-01 → 2025-03-01, gate v1, fill-mode next_open):
- (a) January-trained model: `/tmp/rerun_out/dev/dev_model.json`
- (b) Empty model: `{"kind": "context-event-model-v1", "counts": [], "n_episodes": 0, "trained_through": null}`

No source edits were needed; the eval path loads the model from `--model` (runner L379–389).

### Results

| Metric | Jan-trained | Empty |
|---|---|---|
| Cases total | 439 | 480 |
| Decisions | 480 | 480 |
| Strict preference | 384 | 0 |
| Gate pass | 43 | 0 |
| Plans created | 3 | 0 |
| No-plan | 433 | 480 |
| Outcomes | win: 2, no-entry: 1 | (none) |

Field-by-field comparison of the 433 common no-plan boundaries: **337 differ** in `decision_state` and/or `gate_reason`; 96 are identical.

The trained model produces strict preferences (384/480 decisions) because its per-context counts distinguish continuation from violation. The empty model has no counts, so `model.rank()` returns "unsupported-context" for every context (L465–468), `chosen = None`, `primary_is_baseline = True`, and the gate blocks every attempt.

Example difference (2025-02-06 10:00 UTC):
- Trained: `gate_reason = "connected readings hold EVIDENCE_PREFERRED FVG FVG-fx-intraday-v1-cr-1h-83 (downward) opposing the intended direction (up from pid=I-primary ctx=up)…"`
- Empty: `gate_reason = "decision has no strict evidence-supported preference: EVENT_OCCURRED"`

**Conclusion:** The stored counters materially change decisions. Without them, no plan is ever created.

---

## PART 4 — Empirical lookahead test

### Method

Three eval runs on identical filtered data, gate v1, fill-mode next_open, January-trained model:
- Full: 2025-02-01 → 2025-03-01 (439 cases)
- Cut A: 2025-02-01 → 2025-02-10 (81 cases)
- Cut B: 2025-02-01 → 2025-02-17 (201 cases)

Comparison: all records with timestamp strictly before the cut date are extracted from both the full run and the cut run, indexed by `(timestamp, kind, plan_id)`, and compared field-by-field (full JSON equality).

### Results

| Cut | Records before cut (full) | Records before cut (cut run) | Common keys | Differing records | Only in full | Only in cut |
|---|---|---|---|---|---|---|
| 2025-02-10 | 80 | 80 | 80 | **0** | 0 | 0 |
| 2025-02-17 | 200 | 200 | 200 | **0** | 0 | 0 |

**No lookahead detected.** Truncating future data does not change any decision or plan record dated before the truncation point. All three plans opened and resolved on Feb 4–6 (before the Feb 10 cut), so the cut runs contain the same plans with identical fields.

### What was NOT tested

- No test with data truncated mid-plan (all plans resolved before Feb 10).
- No test of the `bar_close` fill mode (non-causal by design).
- No test of the dev training path's lookahead (the dev path uses `window_end_time <= dev_end` filtering, runner L586–589, but this was not empirically tested with truncated data in this audit).
- No test of the `pause` phase.

---

## PART 5 — Verdict

### Source-traceable (definition-level alignment with an available source statement)

1. **FVG three-candle non-overlap geometry** — code matches `ICT_SOURCE_AUDIT.md` L86–87 operational description. (Note: the audit is agent-produced; original ICT text not in repo.)
2. **Stop-at-structural-extreme concept** — source-stated in SRC-EX-01 (`trade_plan.py` L172–174). Code's invalidation uses the falsifier reference extreme, though the close-based operationalization is engineering.
3. **Invalidation-on-violation / pause** — `corpus_full_pass.json` L280: "If high is taken, he says he is probably wrong". Code's I-alt and invalidation logic align at the concept level.

### Research-choice or arbitrary (no source mandate; declared engineering configuration)

1. Context 4-feature representation (`decision_layer.py` L201–229).
2. F-K k=5 confirmation window (runner L83; `deliverables/89…` L294 declares it research configuration).
3. HORIZON_BARS = 12 (runner L85; no derivation stated).
4. EPISODE_HORIZON_BARS = 24 default (`decision_layer.py` L179; L182 explicitly states "NOT source-grounded").
5. TASK_SCALE = "1h" (runner L81; no source mandates this for forex).
6. READINGS_SCALE = "15m" (runner L82).
7. I-primary continuation interpretation (`analysis_lifecycle.py` L1018–1061; study doc L60 labels ENGINEERING_INTERPRETATION).
8. I-scenario unresolved-reference construct (`analysis_lifecycle.py` L1063–1101).
9. Entry rule = SP-03 close binding (`trade_plan.py` L296–345; explicitly NOT the source-stated OB-return entry).
10. Target rule = F-K leg completion (`trade_plan.py` L335–344; no target in verified source).
11. Gate v1 connected-contradiction logic (runner L402–453).
12. Gate b0 baseline (runner L455–464).
13. SP-03 tie rule: equality is not a crossing (`csm.py` L1366–1369).
14. SP-05 tie rule: inclusive boundaries (`csm.py` L1294–1296).
15. train_fraction = 2/3 (`decision_layer.py` L802).
16. All display truncation limits (3, 5, 6, 8 in `analysis_lifecycle.py`; 4 in `decision_layer.py`).
17. Reference role "origin-of-last-confirmed-leg" (`analysis_lifecycle.py` L485–488; declared research configuration).

### Not implemented or unknown

1. **OB-return entry technique** (SRC-EX-01) — explicitly NOT implemented. `trade_plan.py` L322–325: "G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)".
2. **ICT-primary invalidation-by-close** — SRC-EX-02 (`trade_plan.py` L202–205): "Not in primary text read (P-K)". The close-based rule is engineering/community-influenced.
3. **Liquidity target selection** — SRC-EX-03 (`trade_plan.py` L218–221): source explicitly refuses to select a target. Code's F-K leg objective is a research substitute.
4. **MSS/BOS/CHoCH detectors** — not on the forex V1 path. Direction is derived from F-K leg completion only.
5. **Order Block / Mitigation Block / Breaker Block / Inverse FVG** — `ICT_SOURCE_AUDIT.md` L74, L79, L93: NOT_IMPLEMENTED.
6. **Original ICT transcript verification** — the pinned knowledge repo (`jfjdjdieifne/test@6c8bf6fd`) is absent from this checkout. All source quotes are agent paraphrases or code-embedded attributions that cannot be independently verified here.
7. **Empirical derivation of any numeric constant** — no constant in the audited files has a stated empirical derivation (e.g., optimization, cross-validation, statistical test). All are declared research choices or arbitrary display limits.

---

## Execution log

| Run | Window | Model | Gate | Fill | Exit | Duration | Cases |
|---|---|---|---|---|---|---|---|
| eval_full_filtered | Feb 1 → Mar 1 | Jan-trained | v1 | next_open | 0 | 308.2s | 439 |
| eval_empty_filtered | Feb 1 → Mar 1 | empty | v1 | next_open | 0 | 308.8s | 480 |
| eval_cut_feb10 | Feb 1 → Feb 10 | Jan-trained | v1 | next_open | 0 | 10.0s | 81 |
| eval_cut_feb17 | Feb 1 → Feb 17 | Jan-trained | v1 | next_open | 0 | 42.3s | 201 |

All runs used `/tmp/fidelity_audit/data_le_feb/2025.csv.gz` (16 992 rows, max 2025-02-28 23:55 UTC). No May 2025 row was present.

Commands (template):
```
/home/user/.venv/bin/python project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py \
  --bidask-dir /tmp/fidelity_audit/data_le_feb \
  --phase eval --from 2025-02-01 --to <END> \
  --gate v1 --fill-mode next_open \
  --model <MODEL_PATH> --out-dir <OUT>
```

Protected file verified at audit end:
```
SHA-256: 72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace
Size: 12216 bytes
```

No existing tracked file was modified. No source code was patched. No parameter was tuned.
