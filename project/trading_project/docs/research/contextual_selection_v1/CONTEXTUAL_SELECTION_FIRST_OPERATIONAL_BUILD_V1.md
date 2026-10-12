# Contextual Selection — First Operational Build (CSM Phase 0)

Status: COMPLETE (research build; no trading recommendations; no live execution)
Date: 2026-10-12
Branch: arena/a41fd997-trading-bot (session branch)
Owner problem (verbatim, file 15): "Given real evolving market movement, multiple
plausible wave representations, and a declared analytical purpose, identify which
movement and structural references are contextually appropriate."

This report separates concept correctness / temporal correctness / contextual
selection quality / consistency / predictive usefulness exactly as required.
Where a dimension is not measurable now, the exact blocker and the shortest
unblocking path are given — NOT_ESTABLISHED is never dressed as success.

---

## A. Repository states and exact commits

| Repo | Branch | Commit | Verified by |
|---|---|---|---|
| jfjdjdieifne/TRADING-BOT | arena/a41fd997-trading-bot | base `c96b9a56b3e966432c30cf058c19abda9c02224b` + this build | `git ls-remote` before work; local == remote |
| jfjdjdieifne/test (knowledge) | arena/5125ef9c-test | `6c8bf6fd10e9581322849485d175e825cea5a27f` | `git ls-remote` first (NOT main `838b9ca6…`) |

Knowledge snapshot used: codeload zip of the above commit (sha-extracted), covering
`knowledge_foundation/00..19`, `architecture/`, `architecture/v2/` and
`claims_index.json`. CLOSED/seals untouched; no canonical push; no PR.

Certified environment (per task): Python venv `venv2`, pandas 2.2.3, numpy 2.2.6.

## B. Capability map (what exists, what is missing)

Existing code (`src/trading_system/market_understanding/…`):

| Knowledge need | Existing code | Status |
|---|---|---|
| Candidate generation (ALPHA..DELTA families, k/τ/O slots) | `wave_representation.py` `WaveRepresentationService` (family kinds `family_kind 5`, S5) | EXISTS — generator-level only |
| Confirmation / provisional states (SP-13, SWS-04a-d) | `detector_witness.py` partial (structure confirmations) | PARTIAL — statuses not generalized to selection |
| Policy registry (SP-18) | `policy_governance.py` (S6 docs) | PARTIAL — docs of policy IDs, not a registry used at selection time |
| Knowability (SP-01) / containment (SP-05) / dominance (SP-06) / consistency (SP-07) | — | **MISSING → built now** |
| Task cards T-S1..T-S6 with H_T/X_T/C_T/Π_T (file 16) | — | **MISSING → built now (T-S1/S2/S3/S5)** |
| Unresolved states MO/MP/AI/IC/EP/OOD + acceptable sets (file 19 §19.1) | — | **MISSING → built now** |
| Revision propagation (SP-20, IC-10/11) | — | **MISSING → built now** |
| Learning: acceptable sets → procedure/classifier (file 18) | `calibration/adaptive_confluence.py` (weights, NOT selection) | **GAP** — no annotation data; do not misuse |

The problem is not raw detection (S5 families already generate k-pivot / τ-reversal
candidates). The gap is *task-conditioned contextual selection with evidence,
temporal discipline, and explicit unresolved states*. That gap is what this build
implements (Phase 0 per `architecture/v2/05`, file 18 §18.9).

## C. Knowledge-to-code gaps closed by this build

New package `src/trading_system/research/contextual_selection/` (2 files):

- `csm.py` — CSM kernel: `Representation` (family/view/scale/policy params with
  provenance), `PointCandidate`/`LegCandidate` (occurrence bar, knowable bar,
  status, supersession chain), `Exclusion` (X-KNOW/X-STATE/X-SUPER/X-SCALE/
  X-GEOM/X-DOM/X-POL), `UnresolvedState` (MO/MP/AI/IC/EP/OOD + §19.1 fields),
  `SelectionResult`, `PolicyRegistry` (SP-18), `InterpretationLedger` with
  `record()`/`record_event()`/`propagate()` (SP-20 recomputation chain).
  Generators: `fk_turning_points` (F-K k-pivot with SP-13 causal confirmation:
  provisional at occurrence, confirm at i+k, SWS-04c supersede inside window,
  SWS-04d prefix-replay consistent) and `ft_turning_points` (F-T τ-reversal,
  knowable at the confirming bar). Procedures: `sp01_knowability`,
  `sp03_binding`, `sp05_containment`, `sp06_dominance` (strict-superset rule,
  ties survive as X-DOM-labeled), `sp07_consistency`. Task cards:
  `task_s1_structural_reference` (Π_T roles `origin-of-last-confirmed-leg` /
  `last-confirmed-extreme`), `task_s2_event_binding` (SP-03 close basis, break
  side per reference side, fresh-crossing rule via `prev_close`, unordered
  acceptable set), `task_s3_entry_leg` (W2 pattern; MP preserved on ambiguity),
  `task_s5_falsifier` (interpretations reduced to reference terms or MP).
- `__init__.py` — public API surface.

Deliberately NOT implemented (rejected/deferred with reasons — deliverable E):
FVG / liquidity-sweep / entry-model / trading-rule semantics; LLM selectors;
factor-graph/ranker (v2/00/05 reject these: no defensible supervision signal);
any ownership-authority imitation; S1 causal-segmentation from
`trajectory_relevance_pilot` — DEFERRED as the selection method for this task
(it does not define *contextual* selection criteria and has no measurable
selection capability to compare pre-Phase-0).

## D. Selected method and scope

CSM Phase 0 exactly per file 18 §18.9 and v2/05: bar-replay + declared
generators (F-K k-pivot, F-T τ-reversal) + SP-01..07,13,18,19,20 + task cards
T-S1/T-S2/T-S5 (+T-S3 acceptable-set pattern) + golden-set harness (objective A)
+ declared-rule baselines as witnesses. Scope = movement → swings/waves →
structural references with preservation of unresolved alternatives.

## E. Justification vs alternatives

1. **Chosen: CSM task-card pipeline + deterministic procedures + ledger.**
   Reproducible on real bars; every exclusion carries an X-code; ambiguity is
   first-class (MP/AI/IC); supervision-free (L-class objectives only when
   data exists). This is the only approach that can run honestly TODAY.
2. **Rejected (for now): ranker / factor-graph / learned preference** (v2/00):
   acceptable-set annotations do not exist; file 18 is unambiguous that fitting
   a model without annotation data is not learning evidence.
3. **Rejected: S1 causal segmentation as selector** (relative comparison
   requested by the task): it outputs segmentations, not purpose-conditioned
   reference selection; no annotation harness exists to measure a difference
   ("reject if it has no measurable capability" — capability would be
   unmeasurable now; recorded as DEFER, to revisit when Phase 0 datasets exist).
4. **Rejected: binding everything and filtering later** — that is the failure
   mode the owner's problem describes; contextual selection must be explicit
   and evidence-based.

## F. Files changed

| File | What |
|---|---|
| `src/trading_system/research/contextual_selection/__init__.py` | API exports |
| `src/trading_system/research/contextual_selection/csm.py` | CSM kernel + procedures + task cards + ledger |
| `tests/test_contextual_selection_csm.py` | golden set W1-W5, W8-W10 + generator/procedure tests (12 tests) |
| `docs/research/contextual_selection_v1/experiment_contextual_selection_v1.py` | real-market experiment (reproducible) |
| `docs/research/contextual_selection_v1/experiment_record_v1.json` | experiment output record |
| `docs/research/contextual_selection_v1/CONTEXTUAL_SELECTION_FIRST_OPERATIONAL_BUILD_V1.md` | this report |

No existing file modified. CLOSED/seals untouched.

## G. Real-market experiment (CSM-SEL-EXP-V1)

- Data: BTCUSDT 1m 2025-08-01 → 2025-09-27 (sha256 `15d26d23…` / `e1d5c8f3…`
  verified vs `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70`).
  Published OHLC facts; `SOURCE_ORIGIN_UNVERIFIED`.
- Views (declared O-policy `P-TF`, sensitivity recorded; owner not consulted):
  C = 1h (1,368 bars), F = 5m (16,416 bars).
- Representations (all kept side by side, never merged — SWS-01):
  C: F-K k∈{5,12}, F-T τ=250; F: F-K k=6, F-T τ=80.
- Frozen decision boundaries (9): 2025-09-20/22/24 daily; B0 `2025-09-25 00:01Z`
  (SXM-005 forward clause); B1 `2025-09-25 06:49Z` (SXM post-5 v1 creation);
  B2 `2025-09-25 19:34Z` (SXM post-6 v3 creation); + 2025-09-25 12:00Z,
  09-26 12:00Z, 09-26 23:00Z. Knowability enforced at bar-close before each.
- Tasks at every boundary: T-S1 (two Π_T roles), T-S5 (falsifiers), T-S2 scan
  between boundaries (fresh crossings, close basis), SP-20 propagation on
  binding of active references, SP-16 representation-dependence report.
- Results (record JSON): **176 selections, ALL justified (justified=176,
  unresolved=0, empty=0) on declared defaults**; **59 fresh binding events**;
  **174 propagation steps** (58 W8-chains × 3); exclusion work-units
  X-SUPER 105,780 / X-POL 145,644 / X-STATE 96 (cumulative across 9 truncated
  reruns — every candidate retained with a code; no pruning).
  **Replay consistency (SWS-04d): 4/4 recomputed-from-truncated == stored.**
  **SP-16: representation disagreement at 9/9 boundaries** (reported per rep;
  never merged). E.g. at B1, C-F-K k=5 and k=12 independently select the same
  reference (1h low 2025-09-24 04:00 ≈ 111,042) while F-T τ=250 selects a
  different one (1h high 2025-09-25 02:00) — the table preserves all three.

## H. Contextual-selection examples (real market)

1. **B1 = 2025-09-25 06:49Z (SXM pre-event decision moment).** T-S1
   `origin-of-last-confirmed-leg` on 1h: F-K k=5 → `low@1300`
   (2025-09-24 04:00Z low ≈ 111,042; last confirmed leg `leg1300-1313`,
   an up-leg). F-K k=12 → the same bar/level (independent agreement).
   F-T τ=250 → `high@1322` (2025-09-25 02:00Z). All three are kept and
   reported; 631/381/… candidates each retained with X-codes
   (X-SUPER supersessions kept in the record, not deleted).
2. **T-S2 bindings 2025-09-25 late morning (fresh crossings, close basis).**
   11:10–11:40Z the fine view breaks `F-F-K low@15960`; at 11:40Z one event
   binds BOTH views simultaneously: `C-F-T low@1327` + `F-F-T low@15976`
   (unordered acceptable set, per-view mapping preserved).
3. **W8-pattern propagation 2025-09-25 ~13:05Z.** The 5m sell-off closes below
   all three coarse origin-lows at the same event bar: each chain records
   `status → broken`, `T-S1 → recomputed at next boundary`, `T-S5 falsifier →
   invalid(contradicted)` — nothing patched in place (SP-20), dependents
   tracked by id.
4. **Golden-set ambiguity (W2)** demonstrates the acceptable-set format
   `{fB, fD}` with explicit `X-POL` fA/fC/fE and `MP` + blocked dependents
   (`zone-boundaries`, `fine-liquidity-below-above`).

## I. Learning evidence (what is achieved, what is not)

- Objective A (replicate declared procedure): **ACHIEVED** — 12/12 exact-match
  tests on the file-19 golden set (W1-W5, W8-W10; W6/W7 out of Phase-0 scope,
  recorded in the test file), run in the certified env.
- Objective B (contextual coherence against expert acceptable sets):
  **NOT_ESTABLISHED.** Blocker: **no acceptable-set annotations exist** for any
  real instrument/window. File 08's cases are SYMBOLIC ("30 40 20 45", not a
  real symbol/timeframe/window) and cannot be annotated as-is. No classifier,
  no preference score, and no "selection quality" number is claimed — per
  file 18, a fitted model without annotation data is not evidence.
- Objective C (predictive usefulness): **NOT_ESTABLISHED / not evaluated in the
  selection step** by design (separate measurement; the kernel must not sneak
  event labels in).
- Objective D (out-of-sample): **NOT_ESTABLISHED** (no training to generalize).

## J. Independent evaluation — what to evaluate and how

An independent reviewer can reproduce and check, without trusting this report:

1. `pytest tests/test_contextual_selection_csm.py` in the certified env → 12/12.
2. `python docs/research/contextual_selection_v1/experiment_contextual_selection_v1.py`
   → identical selections; replay checks `equal=True`; the committed
   `experiment_record_v1.json` matches a fresh run (record is deterministic).
3. CSM-vs-source alignment: the 1h reference selected at B1 (≈111,042, pre-event)
   and the ~13:05Z break/propagation of 2025-09-25 are consistent in DIRECTION
   with SXM post-5's pre-event downside plan (entry 116,632, stops 117,313,
   SXM post-6 "stopped") — stated as a consistency observation only; the SXM
   journal is peer content, not ownership authority, and no source verified
   whether SXM used these exact points.
4. Audit exclusion completeness: every non-selected candidate in the record
   carries an X-code; no deletion.

## K. Causal integrity tests

- Time cutoffs: every task receives only bars with close-time ≤ decision time
  (bar-replay truncation; knowable-bar discipline from SP-01/SP-13).
- Replay consistency (SWS-04d): recomputation from truncated inputs equals
  stored outputs — 4/4 checks on real data (B1/B2 × C-FK5/F-FK6) + the golden
  tests include a W4 replay assertion.
- Supersession (SWS-04c): provisional → superseded inside the confirmation
  window keeps the chain (`superseded_by`), verified on synthetic + real runs
  (X-SUPER counts).
- Event freshness: binding fires on crossings (prev-close not beyond), not on
  every bar beyond the level — fixed during the build after the first real run
  exposed the semantics bug (288 repeated "events" collapsed to true crossings).

## L. Blocked capabilities and their dependencies

| Capability | Blocked by |
|---|---|
| Selection-quality improvement over baselines (owner's core metric) | Acceptable-set annotations (EP) |
| Objective B / supervised selection learning (file 18 objectives) | Annotation protocol + ≥2 annotators + owner acceptance threshold |
| S5 native (wave_bundle + authorized PolicyArtifact) | Owner's authoritative swing-selection values (S2) |
| S7 → S9 native | S5 + owner policy |
| Selection ground-truth binding format (`selection_ground_truth_v1`) | Should be replaced by the §19.1 acceptable-set schema here |
| ICT semantic classes (FVG/liquidity/entry) | Task explicitly excludes for this build |

## M. Minimal next step

1. Adopt file 03 §2 annotation protocol + file 19 §19.1 schema; import the
   existing source-verified cases as the first bindings (SXM-005 = 1 unique
   selection, SXM-006 = 1 AMBIGUOUS outside clean setups, GU-2026-04-17,
   ICT-2024-09-16) using their exact times/windows/annotation status.
2. Owner decision needed (recorded as such — not invented here): the
   **authoritative swing-selection values** (S2, "the most significant missing
   knowledge item") and the objective-B acceptance threshold.
3. Only after (1)-(2): run objective A/B harness on the annotated set and
   measure selection improvement vs the declared-rule baselines (SP-12/SP-16
   grids already in place).

## N. Independent audit requirements

1. Verify remote HEADs were checked before work (`git ls-remote`, both repos)
   and that this build is on `arena/a41fd997-trading-bot` only (no canonical
   push, no PR, no CLOSED changes).
2. Verify certified env used (pandas 2.2.3 / numpy 2.2.6) for all runs.
3. Re-run J1-J2 and confirm determinism; inspect that no candidate is dropped
   silently and that ambiguous/representational conflicts stay visible (SP-16
   `disagree` cells are load-bearing).
4. Verify claims boundary: no trading recommendation, no execution, no
   ownership-authority imitation, no fabricated annotations, no learning claim
   beyond objective A.
