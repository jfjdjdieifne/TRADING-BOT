# Expert-Grounded Contextual Selection V1 — Build Report

**Task:** CAUSAL TRADING INTELLIGENCE — EXPERT-GROUNDED CONTEXTUAL SELECTION V1
(controlled implementation; no parallel architecture).
**Subject:** one selection task — `STRUCTURAL_REFERENCE_SELECTION` (T-S1).
**Scope:** software mechanism + declared expert-grounded policy. This report
does not assert market correctness, does not issue trading recommendations,
and does not claim any selection quality (which remains NOT_ESTABLISHED).

---

## A. Verified branch and full HEAD SHA

- Branch: `arena/a41fd997-trading-bot` (session branch; unchanged).
- Pre-implementation HEAD, verified against `git ls-remote` before starting:
  **`4fae301eaeabef14d8159d4eecb8cde1982fbb2a`** (equals the task's stated
  reference; remote tip = local).
- Implementation commit: see the completion handoff (this report is written
  before the commit; the exact SHA is in the git log of the same branch).

## B. Exact files changed

| File | Change |
|---|---|
| `project/trading_project/src/trading_system/research/contextual_selection/expert_selection.py` | NEW — the expert judgment layer (knowledge records KP-01..KP-07, evidence model, preference resolution, `ExpertSelection` output) |
| `project/trading_project/src/trading_system/research/contextual_selection/__init__.py` | additive exports only (no existing line changed) |
| `project/trading_project/tests/test_contextual_selection_expert_selection.py` | NEW — 12 required behavioral categories + 2 contract checks |
| `project/trading_project/docs/research/expert_selection_v1/run_expert_selection_market_v1.py` | NEW — chronological market-replay runner |
| `project/trading_project/docs/research/expert_selection_v1/run_artifacts/run_report_v1.json` | NEW — run metrics (deliverable G) |
| `project/trading_project/docs/research/expert_selection_v1/run_artifacts/selection_records_v1.jsonl.gz` | NEW — 114 selection records |
| `project/trading_project/docs/research/expert_selection_v1/run_artifacts/candidate_rows_v1.jsonl.gz` | NEW — 18,615 coverage rows (candidate_record contract) |
| `deliverables/88_EXPERT_GROUNDED_CONTEXTUAL_SELECTION_V1_BUILD_REPORT.md` | NEW — this report |

**Untouched (verified):** `information_time.py`, `information_time_schema.json`,
`INFORMATION_TIME_SPEC.md`, `csm.py`, `artifacts.py`, all manifests
(`MANIFEST.sha256`), `docs/STATUS.md`, all prior `contextual_selection_v1/`
research artifacts, `knowledge_artifacts/`, legacy wave policy values.

## C. Exact existing interfaces consumed (no reimplementation)

- **Candidates & lifecycle:** `PointCandidate`, `LegCandidate`,
  `StatusTransition`/`add_transition`/`status_at()` (append-only history),
  `same_bar_evidence_class`.
- **Eligibility gates:** the kernel's own `task_s1_structural_reference`
  (SP-01 knowability, SP-13 confirmation, SP-14 leg availability, X-SCALE
  view filter, X-SUPER, X-KNOW, same-bar AI surfacing) — the layer calls it
  and never re-derives gate semantics; `sp03_binding` (SP-03 close-crossing)
  for relationship evidence.
- **Information time:** CLOSED 6.2A-0 contract via
  `trading_system.research.information_time` → `SharedInformationAxis`
  (`key_for_time`/`require_key`/`available`), `require_validated_asof`,
  `_validate_time_inputs` fail-closed discipline.
- **Policy provenance:** `PolicyRegistry` (SP-18; versioned snapshots
  `policy_snapshots` on every result; `kind=research_configuration`).
- **Revision & dependency propagation:** `SelectionResult.dependencies /
  dependents / direction`, `UnresolvedState` (schema file 19 §19.1),
  `InterpretationLedger.record(result, payload)` with real recomputation
  payloads (audit D5), `candidate_record` coverage rows.
- **Generators (run only):** `fk_turning_points` (F-K, D2 full-left-context),
  `build_legs` (SP-14, D4 ambiguities), `Representation`.

If any of these had been unavailable the task's stop condition (§12) would
have applied; all were present and consumed as-is.

## D. Source-grounded selection knowledge used

Seven documented records (`EXPERT_KNOWLEDGE_SRS_V1`), each carrying exact
source, task classification (task §4 A–F), context, observable evidence,
exceptions and conflict status:

| ID | Class | Content | Sources |
|---|---|---|---|
| KP-01 | D (task-conditioning) | the declared role determines the reference; "origin of the most recent confirmed leg" is an operational definition, not a market claim | knowledge_foundation/16 SWS-02 + W1; Wyckoff 1931 (five-step); Livermore 1940 (pivotal point) |
| KP-02 | E (conditional preference) | documented-tested reference preferred over prominent-untested one — **tested-vs-untested shape only** (never touch-count ranking) | Grimes 2012 (random-lines falsification); Livermore 1940 (pivotal validation); Osler 2002/2005 (stop clusters; reactions at documented levels) |
| KP-03 | E | REF-OLD-LOW-HTF / REF-OLD-HIGH-RECLAIMED as source-indicated support references | ICT/Huddleston, Month-04 lessons (SRC-ICT-OB/FVG, P1 partial transcripts); knowledge_foundation/05 §5.4a P-R, 08 |
| KP-04 | B (hard constraint) | material same-bar ambiguity never yields a justified result (AI surfaced) | knowledge_foundation/15 §15.7 + audit D4; Lo–Mamaysky–Wang 2000 (look-ahead discipline) |
| KP-05 | F (unresolved hypothesis) | volume-based effort/result; FVG/OB narrative claims about THE reference — documented refusal, **never binding** | Wyckoff 1931; ICT/community marketing forms |
| KP-06 | E | upstream-declared round-number/cluster marker preferred over unmarked | Osler 2002/2005 (dealer-order evidence); instrument transfer marked provisional |
| KP-07 | D | answering scale fixed by the task card first; cross-view mixing excluded | Elder 1993 (tide-first); Wyckoff 1931; T-S6/SP-02/SP-16 |

No numeric weights, no undocumented precedence (task §4/§6). The only
documented precedence used is Π_T-over-preference (file 15 §15.7.3), and any
contradicting preference is preserved as a recorded tension (SP-12 main
alternative), never silently applied.

## E. Actual runnable implementation

- Layer: `contextual_selection/expert_selection.py`
  (`expert_structural_reference_selection(...)` → `ExpertSelection` with
  outcome `SELECTED(candidate_id, evidence)` or
  `UNRESOLVED(reason, surviving_candidate_ids)`).
- Run: `docs/research/expert_selection_v1/run_expert_selection_market_v1.py`
  (chronological information-time replay on real BTCUSDT data).
- Behavior summary: retrieve candidates → existing gates (kernel T-S1) →
  observable evidence (F/S classes) → documented conditional preferences →
  evidence-supported comparisons only → conflicts preserved →
  SELECTED/UNRESOLVED with source provenance → one compatible structural
  interpretation continued when supported → revision dependencies carried by
  `SelectionResult`/ledger payloads. No largest/nearest/newest/prominence
  default exists in the code path.

## F. Behavioral test results

- New suite `tests/test_contextual_selection_expert_selection.py`:
  **14/14 pass** — the 12 required categories (same-scene/different-task;
  multiple eligible; prominent-but-irrelevant; source-grounded preference;
  conflicting preferences preserved; no-applicable-preference → UNRESOLVED;
  temporal unavailability incl. off-grid fail-closed; replay determinism +
  future-event isolation; frozen historical selection; revision after
  changed evidence (W8) with `InterpretationLedger` version retention;
  sealed-foundation hash; runtime bound) + 2 contract checks (F-class never
  binds; preference resolution is pure/replayable).
- Pre-existing suites: `test_contextual_selection_csm.py` (12) +
  `test_contextual_selection_final_audit_patch.py` (14) unchanged and green;
  **full repo suite exit code 0** with the new modules installed.

## G. Chronological market replay results (`run_report_v1.json`)

Real BTCUSDT (mirror `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70`;
82,080 1m rows → 1,368 1h completion-time bars; window 2025-08-01 →
2025-09-27; view C = F-K(k=5); 57 daily boundaries; two modes per boundary):

| Metric | Value |
|---|---|
| Total selection opportunities | **114** (57 × 2 modes) |
| Candidate coverage rows | **18,615** (~327/boundary) |
| Actual selections | M1 role-declared: **56** SELECTED, 1 AI (same-bar ambiguity surfaced); M2 preference-mode: **1** SELECTED, **56** UNRESOLVED (EP) |
| Preference rules activated | KP-02 in 57/57 M2 runs (the only observable-evidence preference in this generator output) |
| Conflicts preserved | 0 on this window (KP-03/KP-06 markers not observable → inactive **by contract**, recorded per run) |
| Source provenance on evidence | F: 9,926 · R: 19,255 · S: 1 (each evidence item class-labeled) |
| Temporal violations | **0** (independent check of every selection: knowable ≤ decision, axis-verified) |
| Revision behavior | **54** reference changes across consecutive boundaries (W8-style, all logged); 37,173 generator status transitions |
| Replay determinism | 3 sampled boundaries recomputed twice → identical records (all true) |

Deliberate reading (task §10): counts do NOT prove selection correctness;
zero temporal violations does NOT prove contextual selection quality. The M2
EP majority is the honest outcome: KP-02 discriminates tested-vs-untested
but when several survivors are tested it orders nothing — no tie-breaker was
invented.

## H. Concrete examples of selected references

1. **M2 preference-resolved (real data), boundary 2025-08-02 00:00 UTC:**
   `SELECTED(C:F-K(k=5)|low@2025-08-01T09:00:00)` — evidence: the candidate
   carried recorded test events (F-class interval/SP-03 facts) while the
   other survivors were observed with none; licensed comparison
   `tested>untested` from KP-02 (source: Grimes 2012 / Livermore 1940 /
   Osler 2002-2005); provenance `R:preference-resolution(KP-02)`.
2. **M1 role-declared (real data), boundary 2025-08-02:** same reference via
   the documented Π_T role semantics (SWS-02), with interpretation
   `{reference: …, direction: "up", state: "reference-active",
   conditional_on: [Π_T precedence doc, …], revision_dependencies: […]}`.
3. **Fixture (tests, file 19 W-world):** role `origin-of-last-confirmed-leg`
   → `L_b` (W1 semantics); role `last-confirmed-extreme` → `H_b` on the same
   scene; no role + no evidence → UNRESOLVED (never the prominent `H_b`).

## I. Concrete examples of unresolved references

1. **Real data, boundary 2025-08-03 (and 55 more):** `UNRESOLVED(EP)` with
   survivors `[low@2025-08-01T09, high@2025-08-01T14, low@2025-08-01T23,
   high@2025-08-02T06, …]` — KP-02 activated but several survivors carry
   test evidence, so documented preferences do not uniquely order them;
   `evidence_needed`: comparative evidence (file 18 objective B) or a
   declared Π_T policy (SP-18). **No tie-breaker applied.**
2. **Real data, 1 boundary in M1:** `UNRESOLVED(AI)` — the role-selected
   reference's intrabar high/low order was materially unresolved (audit D4);
   tick data (MO) or a declared ordering policy needed.
3. **Fixture:** conflicting preferences (KP-02 tested ≻ untested vs KP-06
   cluster ≻ non-cluster on the same pair) → `UNRESOLVED(EP)` with both
   conflicts preserved and zero selection (task §7 honored).

## J. Runtime measurements

| Measurement | Value |
|---|---|
| Market run total (load + 57-boundary replay + checks + artifacts) | **12.7 s** |
| Per boundary (pipeline incl. 2 selections + evidence) | avg **179 ms**, max **498 ms** |
| Test 12 bound (4 selections over ~2×10² candidates, full preference evaluation) | < 5 s asserted; measured ≪ 1 s |
| Full repo test suite | exit 0 (pre-existing runtime envelope unchanged) |

## K. Sealed foundation hash verification

- `src/trading_system/research/information_time.py` sha256 =
  **`72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`** —
  matches the task's stated value exactly (verified before implementation,
  after implementation, in test 11, and recorded in `run_report_v1.json`
  `source_version`).
- `csm.py` and `artifacts.py` unmodified (recorded by their sha256 in the
  run report for provenance). No manifest touched.

## L. Remaining limitations

1. **Selection quality is NOT_ESTABLISHED** — no outcome evaluation was run
   (objective-C quarantine); nothing here is a trading recommendation.
2. `P-ORIGIN-RESEARCH` and every policy entry are
   `kind=research_configuration` — never owner-approved analytical policy
   (audit §8 discipline). Owner policy values remain unset.
3. One coarse view (1h F-K k=5) and one representation family in the market
   run; representation dependence (W9) is covered by the test suite only.
4. KP-03 (ICT REF-OLD-LOW-HTF) and KP-06 (Osler clusters) were inactive in
   the run because their observable markers are upstream declarations not
   produced by this generator — by contract they never default on.
5. Test-history evidence derives from exact interval containment + SP-03
   close crossings; any tolerance-based "touch" definition would require a
   declared policy (not invented here).
6. Preference-conflict statistics on real data are zero because both
   preferences in the KP-02/KP-06 pair shape never co-occurred with
   observable evidence in this window; conflict behavior is proven in tests.
7. Fine view, T-S2/T-S3/T-S5 expert extensions, and the TCS-P1 annotation
   pilot are out of scope for this V1 (single-task constraint).
8. The prior `causal_trading_intelligence/` research package remains lost
   (session-recorded only) and was not recreated, per instruction.
