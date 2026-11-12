# Causal Multiscale Price-Movement Understanding V1 — Build + Integrated Experiment Report

**Mode:** build + integrated research experiment · **Date:** 2026-10-12 · no recommendations, no execution, no CLOSED-module modifications.
**Final honesty statement (up front):** this build demonstrates that the system can now **place every existing market-element candidate inside factual, causally-evolving movement context at frozen decision boundaries, with zero silent drops and explicit blocked states**. It does **not** demonstrate improved selection accuracy — that claim is explicitly **NOT ESTABLISHED** (blocked prerequisites in K).

---

## A. Exact built commit

| Item | Value |
|---|---|
| Remote HEAD of `arena/01a10a21-trading-bot` (verified `git ls-remote` + `gh api` first) | **`3a33ab48c42ac8c224a693d4b5c656b0f3601ff4`** (2026-10-11T11:16:05Z) — matches last reported HEAD |
| Built against | codeload extraction of this exact SHA (`/home/user/work/target-src`); every imported module is from that tree |
| Local Arena checkout | based on older `c905f2b7`; used only as the docs home for deliverables; no existing file modified |
| Owner run config observed | `field_run_config.json`: `swing_quantile: null`, `swing_prior_*: []`, `sessions: []`, window `BTCUSDT 2026-05` (not used; experiment uses verified public data) |

## B. Files changed

All additions, untracked, under `project/trading_project/docs/research/movement_understanding_v1/` (no existing file touched; no CLOSED module or seal modified):

| File | Role |
|---|---|
| `movement_understanding_integration_v1.py` | the new integration harness (View A/B join, predeclared A/B comparison, 9-test battery, chart) |
| `run_manifest_v1.json` | compact run manifest: hashes, fingerprints, boundary/A-B summary, test results, unanswered questions |
| `MOVEMENT_UNDERSTANDING_V1.md` | this report |

Heavy outputs kept **outside** the repository: `/home/user/work/muf_v1/` (adapter runs `run_nopolicy/`, `run_4h_nopolicy/`, test runs `integration/run_prefix_B1/`, `integration/run_4h_rerun/`, prepared CSVs, `integration/integration_record_v1.json` (1.8 MB), `integration/movement_understanding_chart_v1.png`, `integration/test_log_v1.json`).

## C. Existing components reused (all CLOSED, run through public contracts)

| Component | Role in the build | State in this run |
|---|---|---|
| MUF **S0** `market_understanding/contracts.py` | typed states, schema identity | active |
| MUF **S1** `market_understanding/price_path.py` | factual causal price-path descriptors (`running_high/low_so_far`, `observed_close_path_length`, `sum_close_displacement`, …); `S1_POLICY_DEPENDENCY_FORBIDDEN` | **VIEW B core** — 4,320 facts |
| **S2** `detector_witness.py` | evidence-only witness view (policy gate left inactive) | evidence-only, 0 event witnesses (no policy) |
| **S5** `wave_representation.py` (waves / nested movement) | **blocked**: S5 plans require an authorized `swing_policy_id` (`BLOCKED_MISSING_AUTHORIZED_POLICY` by design) | explicit blocked state, not run |
| Stage4A volatility / order-flow-proxy / absorption-proxy | movement-behavior + response facts | available (proxy semantics preserved) |
| Stage4B2 FVG (= 4.2A semantics) | **VIEW A candidates** | 1,786 (1m) + 75 (4h) entities |
| Stage4B2 liquidity / order-block / dealing-range, Stage4B1 structure | VIEW A families | `UNAVAILABLE_NO_EXPLICIT_SWING_POLICY` |
| Stage4C H1 raw completed buckets | multiscale observations | 72 buckets |
| `research/trajectory/market_movement_representation_research.py` | causal chronological replay, boundary records, entity registry, relationship/coverage machinery, deterministic fingerprint | the experiment engine |
| `zones/fvg.py` CausalFVGEngine | independent recount for completeness test | test-only |

## D. Actual new capability

One research-only integration layer (`movement_understanding_integration_v1.py`) that the repository did not have:

1. **Boundary-anchored View A/View B join**: at each frozen decision boundary, every registered candidate is placed into observed movement context (creation-time S1 descriptor state, containing completed H1 bucket, price/zone relation at the boundary) with an explicit placement state; counts reconcile; nothing is dropped.
2. **Predeclared A/B empirical comparison** on a task-relevant selection question (see F), with hypotheses locked in the harness header before boundary analysis.
3. **A 9-test causal-integrity battery** (leakage, prefix stability, completeness, cross-scale validity, missing-policy behavior, no fabricated labels, no silent filtering, reproducibility, explicit incomplete coverage).
4. **An information-time chart** of observations + candidate availability + domain states at boundaries.

Not created: no detector, no selector, no segmentation algorithm, no importance score, no wave/impulse/correction/reversal/trend labels, no policy values.

## E. Real-market experiment and source

- **Market:** BTCUSDT 1m, **2025-09-24 00:00Z → 2025-09-27 00:00Z** (4,320 bars) — the source-verified SXM decision day plus context; and the same source aggregated to **4h bars 2025-08-01 → 2025-09-26** (342 bars) for the human-referenced scale.
- **Data provenance (same verified source + timestamps for both views):** `parshant231234-eng/BTCUSDT-Historical-Data` @ `27c9be70`; month files sha256 `15d26d23…` (Aug) / `e1d5c8f3…` (Sep) — hash-matched to the prior audit's stored inputs; prepared slices `btcusdt_1m_2025-09-24_26.csv` sha256 `1e6f4819…` and `btcusdt_4h_2025-08_09.csv` sha256 `37bd2ae5…` (lossless re-presentation: `close_time_utc` = bar open + interval; values unchanged). Semantics: `PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED` (as declared by the adapter).
- **Source-verified boundaries (SXM journal, topic 717, exact Discourse metadata):** post 5 `2025-09-25T06:49:22.428Z` (v1, pre-event expectation + "midnight open" reference + "4hr -fvg" reference) → boundary B1 = last completed bar ≤ post time (`2025-09-25T06:49:00Z`, position 1848); post 6 `2025-09-25T19:34:06.983Z` (v3) → B2 (position 2613); B0 = midnight-open bar completion (the named "midnight open" reference's bar).
- Information frozen at each boundary (`COMPLETED_ROW_AVAILABLE` keys); no later movement used for earlier candidate availability (proved in T1/T2).

## F. Movement / candidate comparison outputs

**Movement-evolution observations (factual, no labels):**

| Boundary | Price | S1 `sum_close_displacement` | S1 path length | S1 running low | Last completed H1 (OHLC) |
|---|---|---|---|---|---|
| B0 00:01Z | 113,293.8 | **+1,340.4** | 39,199.6 | 111,042.66 | 23:00–00:00: 113,336/113,429/113,205/113,307 |
| B1 06:49Z | 111,656.6 | **−296.8** | 54,861.2 | 111,042.66 | 05:00–06:00: 111,736/112,040/111,598/111,750 |
| B2 19:34Z | 109,648.5 | **−2,304.9** | 89,001.2 | **108,631.51** | 18:00–19:00: 108,834/109,802/**108,631.51**/109,760 |

The sign change of the running displacement (B0→B1) and its extension (B1→B2), plus the running-low update to the day low, are **prefix facts**, not interpretations — this is the evolving movement context View B adds.

**Predeclared A/B comparison** (Q: does movement context change identifiability of the human-referenced element families at frozen boundaries?):

| Measure | B0 | B1 | B2 | Verdict |
|---|---|---|---|---|
| Q1a candidates A vs B (1m FVG family) | 654 = 654 | 813 = 813 | 1,112 = 1,112 | **H1 ✓** — B never filters |
| Q1b movement-context placement coverage | 654/654 (100%) | 813/813 | 1,112/1,112 | **H2 ✓** — measurable, explicit states |
| Q2 "4hr fvg" reference identifiability | AMBIGUOUS (73 eligible 4h) | AMBIGUOUS (73) | AMBIGUOUS (74) | **H3 ✓** — class **unchanged** by B; no source-stated binding rule; no improvement claimed |
| Q2 "midnight open" reference | UNIQUE (00:00 bar open) | UNIQUE | UNIQUE | unchanged by design |
| Q3 selection-quality improvement | — | — | — | **NOT_ESTABLISHED_BLOCKED** (prerequisites in K) |

**Representation disagreements (preserved, not resolved):**
- Human scale ("4hr fvg") vs run-native 1m entity domain — bridged only by the 4h companion run (73/74 as-of candidates); cross-scale equality validated (T4) but candidate *identity* remains ambiguous.
- Task-relevance of any representation: adapter state `NOT_ASSESSED_MISSING_TASK_AND_OUTCOME_AUTHORITY` (`no_proxy_task_relevance_rule: true`) — kept.
- S4C H1 domain line at a boundary can read `UNAVAILABLE_NO_COMPLETED_BUCKET_ASOF_THIS_KEY` (current bucket incomplete) while the as-of field carries the last completed bucket — both states preserved verbatim.
- The adapter's source contract is **1m-only** (`INTERVAL_UNSUPPORTED` for a "4h" identity label); the 4h run therefore carries the contract's fixed `interval: 1m` label over 4h-barred observations — documented quirk, values unaffected (T4 proves the bars are exact 240×1m aggregates).

## G. Chart inspection artifact

`/home/user/work/muf_v1/integration/movement_understanding_chart_v1.png` (sha256 `37a2e9e9…`, 353 KB) — rendered and inspected. Panels: (1) 1m close + S1 running high/low prefix facts + per-candidate availability marks (green=1m, orange=4h) + the three decision boundaries; (2) monotonic registered-candidate accumulation (no pruning) + spatial relations per boundary (spikes reaching the 128/boundary cap); (3) domain-availability matrix at B0/B1/B2 (green available / red policy-blocked / yellow explicit unavailable). No cosmetic dashboard; no strategy annotation.

## H. Performance and coverage

| Stage | Wall clock | Notes |
|---|---|---|
| Adapter 1m replay (4,320 boundaries) | 87.1 s core + 3.1 s finalize | 1,786 entities, 10,100 producer events, 134,220 relationships (28,584 geometry overlaps; 91,964 price-bar-overlap relations; 3,572 availability/origin/lifecycle refs) |
| Adapter 4h replay (342 boundaries) | 4.8 s | 75 entities, 382 events, 2,170 relationships |
| Integration + tests (incl. prefix re-run + 4h re-run) | 46.6 s | progress lines emitted per stage |
| Peak process RSS | 227.7 MB | process high-water mark, as declared |

**Coverage:** `candidate_universe_complete: true`, `candidate_universe_pruned: false`; relationship coverage = `PARTIAL_QUERY_OR_BOUNDARY_LIMIT` with **26 boundaries** carrying unexamined same-batch pairs/queries (the 128-relations-per-boundary cap) — reported explicitly (T9), not hidden. Domains blocked: structure, liquidity, order-block, dealing-range, dependent-combined, S5 waves, actual executed flow (not supplied), market interpretation (no justified policy).

## I. Tests and failures (exactly which ran)

| Test | Method | Result |
|---|---|---|
| T1_NO_FUTURE_LEAKAGE | replay truncated at B1 vs full-run prefix: OHLC, S1 descriptors, domain states, entity sets | **PASS** (0 mismatches; entity sets equal) |
| T2_PREFIX_ASOF_STABILITY | 1,849 boundary rows semantic-identical truncated vs full | **PASS** |
| T3_CANDIDATE_COMPLETENESS | independent 4.2A recount vs registered entities: 1m 1,786=1,786=1,786; 4h 75=75=75 | **PASS** |
| T4_CROSS_SCALE_VALIDITY | every completed H1 bucket (4,261 checks) and every 4h bucket (342) equals its 1m aggregation | **PASS** (0 mismatches) |
| T5_MISSING_POLICY_BEHAVIOR | swing-dependent domains carry `UNAVAILABLE_NO_EXPLICIT_SWING_POLICY` at all three boundaries | **PASS** |
| T6_NO_FABRICATED_MOVEMENT_LABELS | scan producer outputs for impulse/correction/reversal/trend labels | **PASS** (0 hits) |
| T7_NO_SILENT_CANDIDATE_FILTERING | `candidate_universe_pruned==False` on all 4,662 boundaries; A/B counts equal | **PASS** |
| T8_REPRODUCIBLE_OUTPUTS | 4h in-process re-run: deterministic fingerprint `32281bf6…` == `32281bf6…`; prefix chain equal | **PASS** |
| T9_EXPLICIT_INCOMPLETE_COVERAGE | coverage states surfaced; 26 unexamined boundaries reported | **PASS** |

**Failures: none in the final run.** Build iterations (not test failures): the source contract rejects a "4h" interval identity (fixed by matching the contract's 1m label, documented in F), and offline output dirs must be new/empty (harness now clears test dirs).

## J. What improved, if anything

**Established improvements (measured):**
1. **Contextual placement capability:** every candidate (654/813/1,112) now carries movement-context placement (creation-time S1 state, containing H1 bucket, price relation) at frozen boundaries — 100% coverage, zero drops, previously impossible.
2. **A/B comparison is now executable and measured** on a predeclared selection question — with the honest outcome that B changes **descriptions**, not identifiability (H3 held: no false resolution).
3. **Multiscale validity is machine-checked** (T4): the H1/4h representations used in the join are exact aggregations of the observed 1m facts.
4. The human-referenced scale (4h) is bound into the same causal replay (73/74 as-of candidates at the source boundaries).

**Not improved:** selection identifiability/accuracy — unchanged by movement context without a source-stated binding rule; any claim otherwise would be exactly the "geometric agreement ≠ empirical superiority" error the design forbids.

## K. What remains unproven (explicit)

1. **Selection-quality improvement (Q3)** — blocked on: (a) a ground-truth set of *identifiable* human selections at frozen boundaries (today: 1 unique level reference + 1 ambiguous family); (b) owner swing policy to unblock the structure/liquidity/OB/dealing-range families that dominate the owner's selection problem; (c) task-and-outcome authority (repo state `NOT_ESTABLISHED_MISSING_TASK_AND_OUTCOME_AUTHORITY`).
2. **S5 wave / nested-movement relationships** — not constructed (plans require authorized `swing_policy_id`); no substitute segmentation was invented.
3. **Swing, structural-break, liquidity-cluster, order-block, dealing-range candidate families** — absent by policy gate, so this experiment's View A covers the FVG family only.
4. Generality: one instrument, one 3-day window (+2-month 4h context), one source case family.

## L. Independent audit requirements

1. Verify remote HEAD `3a33ab48…` and that `git status` shows only the three new untracked files (no modified/committed files).
2. Hash-check inputs: mirror months `15d26d23…`/`e1d5c8f3…`; slices `1e6f4819…`/`37bd2ae5…`; chart `37a2e9e9…`; full record `b8914fec…` (paths in `run_manifest_v1.json`).
3. Re-run the two adapter CLIs verbatim (commands in the harness docstring/progress logs) → compare `deterministic_fingerprint_sha256` (1m `38d51936…`, 4h `32281bf6…`) and `prefix_chain_sha256`.
4. Re-run the harness → same 9 PASS results and same boundary/A-B numbers.
5. Inspect `boundary_records.jsonl` / `entities.jsonl` / `relationship_coverage.jsonl` directly for the claimed availability and coverage states; confirm T1–T9 claims against raw outputs.
6. Confirm no CLOSED module diff (target tree vs `3a33ab48` codeload).

## M. Minimal next practical step

**One owner-declared swing-policy file** (the existing `--swing-policy-json` contract: `SwingPolicyConfig` values + `owner_authorization_ref` — a policy decision, not code) and one adapter run with it. That single input unblocks Stage4B1 structure + liquidity/OB/dealing-range candidate families (and authorizes S5 plans for wave nesting), after which the same boundary/A-B harness can answer — for the owner's actual swing/liquidity selection problem — the question this run could only pose: **does factual movement context change candidate identifiability for swing and liquidity references, on a ground-truth set of source-verified identifiable selections?** (The second prerequisite: 3–5 more source examples whose selected element is identifiable at decision time — the 2024-09-16 ICT live case becomes runnable the moment its NQ slice is obtained.)

---

### Practical-output checklist
- One chronological market-analysis record: `integration_record_v1.json` (B0→B1→B2 with full candidate/movement joins) + compacted in `run_manifest_v1.json`.
- Movement-evolution observations: F table (S1 prefix facts + completed H1 buckets).
- Scale-specific representations: 1m bars/entities, H1 raw buckets, 4h entities — all validated (T4).
- Candidate-to-movement relationships: placements per boundary (100% coverage) + adapter relationship types (geometry overlap, price-bar overlap, availability/origin/lifecycle).
- Representation disagreements: F section.
- Coverage & missingness: H section + domain matrix (chart panel 3).
- Chart: G.
---

## N. Preservation & Verification appendix (2026-10-12)

**Purpose:** preserve this completed V1 work and verify that the three preserved files correspond to the reported experiment and that the integration is reproducible from the target repository. Method: fresh `git ls-remote` + `gh api` HEAD re-check; full harness re-run (T1–T9); targeted inspection of the raw adapter outputs in `/home/user/work/muf_v1/`; byte-identity proof of `integration_record_v1.json`; fresh scan for fabricated improvement claims. No CLOSED module was modified; no experimental output was altered except by deterministic re-run.

### N.1 Verification checks (task-specified 1–7)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Correct information-time boundaries | **PASS** | B0 pos 1440 `2025-09-25T00:01:00Z` (midnight-open reference bar); B1 pos 1848 `2025-09-25T06:49:00Z` ≤ post5 created `2025-09-25T06:49:22.428Z` (v1, unedited pre-event); B2 pos 2613 `2025-09-25T19:34:00Z` ≤ post6 created `2025-09-25T19:34:06.983Z` (v3); all keys `COMPLETED_ROW_AVAILABLE`; Discourse metadata embedded in the record's `source_case` |
| 2 | No future leakage | **PASS** | T1 truncated-at-B1 replay == full-run prefix (OHLC, S1, domain states, entity sets) + T2 1,849 prefix rows semantically identical — both reproduced on the fresh re-run; boundary rows carry `coverage_locked_source_bar_count` == position and `closed_global_anchor_asof_boundary = null` |
| 3 | Candidate completeness | **PASS** | T3 independent 4.2A recount 1,786=1,786=1,786 (1m), 75=75=75 (4h); T7 `candidate_universe_pruned==False` on all 4,662 boundaries; A/B counts equal (654/813/1,112) |
| 4 | Cross-scale identity correctness | **PASS with documented limitation** | T4: 4,261 H1 + 342 4h buckets == exact 1m aggregations, 0 mismatches. Limitation adjudicated in N.2 |
| 5 | Deterministic reproduction | **PASS** | Full harness re-run → T1–T9 all PASS, identical boundary/A-B numbers; T8 fingerprints equal (4h `32281bf6…`, 1m `38d51936…`); chart byte-stable (`37a2e9e9…`); `integration_record_v1.json` byte-identical **modulo `timing_seconds_total` only** (46.59 → 44.92): `json.dumps(record with timing=46.59, indent=1)` hashes exactly to the as-reported `b8914fec…` |
| 6 | Explicit incomplete coverage | **PASS** | raw `relationship_coverage.jsonl` states `{COMPLETE: 4238, PARTIAL_QUERY_OR_BOUNDARY_LIMIT: 82}`; summary state `PARTIAL_QUERY_OR_BOUNDARY_LIMIT`; 26 boundaries with unexamined same-batch pairs/queries reported (T9) |
| 7 | No fabricated selection improvement | **PASS** | `improvement_claimed == false` in every A/B block (record + manifest); Q2 classes unchanged; Q3 `NOT_ESTABLISHED_BLOCKED`; section J "Not improved"; the only "superiority" wording is the negated warning in J |

**File↔experiment correspondence:** the three preserved files' claims trace to the raw outputs (`run_nopolicy/`, `run_4h_nopolicy/`, `integration/`), whose input CSV hashes (`1e6f4819…`, `37bd2ae5…`) and adapter fingerprints (`38d51936…`, `32281bf6…`) match section E. Hash reconciliation for the record is recorded in `run_manifest_v1.json → dataset_and_build.full_record` (as-reported `b8914fec…` / current `3034e8b4…` / difference field proof).

### N.2 Adjudication: the `interval: 1m` label on 4h-barred runs (task check 4)

- **Values are safe:** every published OHLCV value on the 4h run is an exact 240×1m aggregate (T4), and no reported conclusion keys on the interval label.
- **Real metadata defect (bounded):** `published_bar_record.source_identity.interval` reads `"1m"` while `ohlcv` is a 4h aggregate. Consequently Stage4C H1 grid fields on that run read `expected_grid_bar_count=60 / missing_grid_observation_count=59` per hour — implying *expected-but-absent* 1m data — where the truthful 4h-aware statement is "no 1m grid was expected in 3 of every 4 hours". Any future consumer keying on these fields would be misled.
- **Self-disclosing in-run:** the same records expose the actual cadence (`H1__observed_source_bar_count=1` per bucket, `H1__coverage_status=GRID_OBSERVATIONS_MISSING`) and the contract state (`source_semantics=CALLER_SUPPLIED_OHLC; SOURCE_ORIGIN_UNVERIFIED`, `tie_order_contract=NOT_PROVEN`).
- **Verdict: DOCUMENTED_LIMITATION_WITH_BOUNDED_METADATA_DEFECT — NOT BLOCKED.** Correctness of every reported conclusion is independently established and none consumes the defective fields. **Hazard note:** future consumers must not treat `source_identity.interval` as content cadence, and must not read `missing_grid_observation_count` as expected-but-absent data for non-1m feeds. Future runs should record a `supplied_bar_cadence` attribute alongside the contract label (documentation-level; CLOSED contracts untouched).

### N.3 Exact reproduction commands

```bash
# 0) target tree: codeload extraction of 3a33ab48c42ac8c224a693d4b5c656b0f3601ff4
#    at /home/user/work/target-src ; python venv at /home/user/work/venv
# 1) input slices (hash-check)
sha256sum /home/user/work/muf_v1/btcusdt_1m_2025-09-24_26.csv   # 1e6f48197eaf13da…
sha256sum /home/user/work/muf_v1/btcusdt_4h_2025-08_09.csv      # 37bd2ae5c63c87e2…
# 2) adapter replay (output dirs must be NEW or empty; run WITHOUT swing policy)
export PYTHONPATH=/home/user/work/target-src/project/trading_project/src
python /home/user/work/target-src/project/trading_project/src/trading_system/research/trajectory/market_movement_representation_research.py \
  --csv /home/user/work/muf_v1/btcusdt_1m_2025-09-24_26.csv --timestamp-column close_time_utc \
  --symbol BTCUSDT --period-start-utc 2025-09-24T00:00:00Z --period-end-utc 2025-09-27T00:00:00Z \
  --output-dir /home/user/work/muf_v1/run_nopolicy_recheck --progress
#   -> movement_representation_report.json: deterministic_fingerprint_sha256 = 38d51936271baef9…
python .../market_movement_representation_research.py \
  --csv /home/user/work/muf_v1/btcusdt_4h_2025-08_09.csv --timestamp-column close_time_utc \
  --symbol BTCUSDT --period-start-utc 2025-08-01T00:00:00Z --period-end-utc 2025-09-27T00:00:00Z \
  --output-dir /home/user/work/muf_v1/run_4h_nopolicy_recheck --progress
#   -> deterministic_fingerprint_sha256 = 32281bf65e6dc404…
# 3) integration battery (harness; clears its own test dirs; re-renders chart)
PYTHONPATH=$PYTHONPATH python \
  /home/user/TRADING-BOT/project/trading_project/docs/research/movement_understanding_v1/movement_understanding_integration_v1.py
#   -> T1..T9 all PASS; record/chart/test_log under /home/user/work/muf_v1/integration/
```

Note: the harness expects the canonical run dirs `/home/user/work/muf_v1/run_nopolicy` and `run_4h_nopolicy` (see its header); the `_recheck` dirs above demonstrate fingerprint-level reproduction without clobbering them. The only expected byte difference on any re-run is `timing_seconds_total` inside `integration_record_v1.json` (N.1 check 5).

### N.4 Next-phase readiness inspection (deliverable E–G of the preservation task)

Inspected at target commit `3a33ab48`: `policy_governance.py` (S3), `policy_calibration.py` (S4), `estimand_catalog.py` (S8/S8.5), `information_selection.py` (S9/Gate G2), `freeze_and_readiness.py` (S10–S12/Gate G3), `final_evaluation_and_reality.py` (S13–S15), `dependence_accounting.py` (S7), `state_graph.py` (S6), `calibration/adaptive_confluence.py` (6.2B), `decision/evidence_vector.py` (6.1A), `research/trajectory/trajectory_relevance_pilot.py`, `movement_context_empirical.py`.

| Next-phase capability | State in target repo |
|---|---|
| Candidate extraction | **Present** — Stage4B2 FVG (4.2A) entity registry at frozen keys; pilot `CandidateContext` registration; V1 placement join (this build) |
| Movement representations | **Present** — S1 descriptors, Stage4C H1/4h buckets, 6.2B confluence features; S5 waves exist but policy-gated |
| Contextual selection | **Partial** — `AssessmentCategory.DECLARED_HUMAN_ASSESSMENT` can register human assessments per candidate at a decision key; the pilot explicitly performs **no** selection evaluation ("SATISFY_CONSTRAINT remains blocked"); zero machine-readable ground-truth selection bindings exist anywhere in the tree |
| Historical learning | **Present as machinery, gated** — S4 G0-gated development calibration (scorecards, receipts, reproduce-and-verify); 6.2B TRAIN-only descriptive confluence; S9/G2 information selection (cluster-weighted scores, censoring) |
| Causal evaluation | **Present** — S8.5 estimand realizations with right-censoring; `DevelopmentEvaluationProtocol` closure pinning; S13 one-shot final evaluation |
| Model persistence | **Present** — `PolicyArtifact` + reproduction verification; `FrozenRepresentationBundle` + protocol-hash pinning |
| Out-of-sample testing | **Present** — `DatasetRoleArtifact` roles (DEVELOPMENT_FIT / DEVELOPMENT_SELECTION / FINAL_EVALUATION_LOCKED), `FoldProtocolArtifact` walk-forward vs final firewall, exposure/ancestry firewalls, S14 `EXPOSED_FINAL` + `EquivalenceClaimArtifact` |

**Hard structural gate:** `build_dependence_accounting_bundle` (S7) requires a real `CandidateWaveRepresentationBundle` (S5) with an authorized `PolicyArtifact` — so the native S6→S7→S8.5→S9 learning/evaluation chain **cannot run at all** without an owner-authorized swing policy, even for an FVG-only task. There is no blocked-state bypass (CLOSED).

**Smallest real missing capability (F):** a **machine-readable, source-verified selection ground-truth binding for ONE task** — record type + loader binding each human-referenced element to a concrete candidate entity id (or an explicit ambiguity set) at a frozen `InformationKey`, with pre-decision knowability state — plus the thin factual comparison accounting (rule-selected candidate == bound candidate, or AMBIGUOUS/UNIDENTIFIABLE; no scores, no probabilities). It is the only gap that is genuinely absent as capability, is required under *any* learning path, and is buildable from already-verified sources without inventing labels. Everything else (features via the placement join, role/fold machinery, registration surface via `DECLARED_HUMAN_ASSESSMENT`, freeze/final-eval governance) already exists.

**Minimal next implementation recommendation (G):** implement exactly that one `selection_ground_truth_v1` artifact + loader + boundary-join validator + factual hit/miss/ambiguous/unidentifiable accounting, seeded with the two existing source-verified SXM-005/006 bindings (1 unique + 1 explicit ambiguity set); in parallel the owner supplies (a) the task/outcome authority artifacts (`ObjectiveArtifact`, `EstimandArtifact` — governance declarations, not code) and (b) if the native S9 path is wanted, one owner-declared swing policy via the existing `--swing-policy-json` contract. No model, no generic framework, no invented labels, no arbitrary swing policy.

### N.5 Preservation record

- Preserved files: `movement_understanding_integration_v1.py` (unmodified; re-executed 2026-10-12 — T1–T9 PASS), `run_manifest_v1.json` (updated 2026-10-12: hash reconciliation + `preservation_verification` block), `MOVEMENT_UNDERSTANDING_V1.md` (this append-only section).
- Commit authorization honored: **only these three files** are committed; `dataset_v1/` and all heavy outputs remain outside the commit scope (dataset work was explicitly not-to-commit).
- Repository safety: `git status` shows no modification to any pre-existing file; no CLOSED module, seal, or test touched.
