# Expert-Grounded Contextual Selection V1 — Build Report

**Task:** CAUSAL TRADING INTELLIGENCE — EXPERT-GROUNDED CONTEXTUAL SELECTION V1
(controlled implementation; no parallel architecture).
**Subject:** one selection task — `STRUCTURAL_REFERENCE_SELECTION` (T-S1).
**Scope:** software mechanism + declared expert-grounded policy. This report
does not assert market correctness, does not issue trading recommendations,
and does not claim any selection quality (which remains NOT_ESTABLISHED).

---

> **V1.1 AUDIT REMEDIATION ADDENDUM** (base `f040ffd` → remediation
> `9bca73b2cf0033a2a39e48d56b351e55b8d47bec`).  All six audit findings are
> fixed; see the addendum at the end of this report for the per-finding
> mapping, adversarial-test results and the post-remediation replay
> manifest.  Sections A-L below describe the V1 build; where V1.1 changes
> behavior the addendum states the change explicitly.

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

---

# V1.1 Audit Remediation Addendum

Base: `f040ffd2ee61b5f9bdaf20fb855a8bcb30e9e854` ·
Remediation commit: **`9bca73b2cf0033a2a39e48d56b351e55b8d47bec`** ·
Scope: minimal — audit findings only.

## Finding-by-finding mapping

**F1 — relationship-evidence validation.** New `ContextualRelationships.
validated(decision_bar, decision_time, axis)` validates EVERY fact — test
events (`test_history`), `ref_kind` and `round_cluster` declarations —
against the decision boundary through the approved interfaces over the
sealed 6.2A-0 contract (`SharedInformationAxis.is_on_grid`/`available`).
Every fact must carry a knowability stamp (`bar`/`time`, or
`known_bar`/`known_time`). Missing stamp = unmappable; off-grid time; future
stamp; time-bearing fact without axis/boundary — all **unavailable**, dropped
AND logged (`ExpertSelection.dropped_evidence` + provenance count). The
sealed `information_time.py` was neither modified nor duplicated.

**F2 — task/role requirement, eligibility, explicit unresolved, no silent
omission.** `VALID_ROLES` is enforced: a missing/unknown role yields
UNRESOLVED (MP) with an explicit "no valid declared role" reason and NEVER
falls through to preference selection. A missing policy (kernel MP state)
does not bypass task/role eligibility: comparisons run only over
gate-eligible candidates (kernel survivors + X-POL role-removed — X-POL is
the Pi_T decision, not an eligibility gate). Missing evidence or incomplete
comparisons return UNRESOLVED with explicit reasons/evidence_needed.
`_account_all_candidates` surfaces every input candidate the kernel filters
silently (X-STATE for broken/provisional, X-SUPER for superseded).

**F3 — KP-02/KP-06 nonbinding; event types distinct.** `test_history`
nonempty is removed as binding evidence. Events are kept as two DISTINCT
state-only observations (`wick-range-touch` vs `close-through`; unknown
kinds unmappable), and no evidence text infers rejection, validation or
successful reaction (file 15 §15.4: taken status "establishes state, not
cause"; touch count cannot establish relevance alone). "tested > untested"
and "cluster > non-cluster" are reclassified **F — nonbinding research
hypotheses** (F-class records can never license a comparison; enforced in
`ExpertPreference.__post_init__`). The only source-substantiated conditional
comparison is **KP-03** (REF-OLD-LOW-HTF / REF-OLD-HIGH-RECLAIMED;
knowledge_foundation/05 §5.4a P-R + 15 §15.3 H).

**F4 — equal-knowable-time ties unresolved.** Both kernel T-S1 branches are
tie-aware (`last-confirmed-extreme`: identical knowable stamps;
`origin-of-last-confirmed-leg`: identical leg-recency keys with distinct
origins) and return UNRESOLVED (MP, "declare a tie policy (SP-18)"), never
an order-picked winner. The expert selector carries an independent tie
guard (defense in depth). Input-permutation tests prove order invariance.

**F5 — real ledger recomputation.** `InterpretationLedger` gained an
extensible `register_recompute_handler(kind, fn)` (built-ins unchanged);
`expert_structural_reference_selection` registers a real handler that
recomputes from the payload's COMPLETE inputs (live objects + serialized
`input_records`) as of the update boundary. `ExpertSelection.final_result`
(mirroring the expert outcome) is the registered SelectionResult. Empty or
incomplete payloads raise and are marked **stale — never success**. Tested
through an actual dependent conclusion (T-S5 falsifier of interpretation
I1): both results get NEW versions with ACTUAL computed changes and updated
dependencies after a recorded break fact (SP-20 transitive).

**F6 — replay manifest.** `run_artifacts/replay_manifest_v1.json` records:
dataset commit `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70`; both
input-file SHA-256 values (`BTCUSDT_1m_2025-08.csv` =
`15d26d23…1c90a0cf4`, `BTCUSDT_1m_2025-09.csv` = `e1d5c8f3…0d7a48979`);
final source commit `9bca73b2cf0033a2a39e48d56b351e55b8d47bec`; dependency
versions python 3.11.2 / **numpy 1.26.4 / pandas 2.2.3 / pytest 8.3.5** (the
pinned set, installed and used for every run).

## Adversarial tests (25 expert tests total, all green)

future relationship evidence unavailable · off-grid event time unavailable ·
unmappable event/declaration unavailable · future declaration unavailable ·
missing/mismatched roles explicit-unresolved (5 shapes) · incomplete
comparisons (both-sided and one-sided) unresolved with no omission ·
KP-02 event types distinct + nonbinding proof (identical output across
test_history variations; no inference words) · equal-knowable tie
unresolved in kernel AND layer (both orders) · equal leg-recency tie
unresolved + permutation invariant · input-permutation invariance
(outcome/selected/survivor-set/exclusion-map) · real ledger propagation
(expert + T-S5 dependent: version 2, computed_changes, updated deps) ·
stale/empty recompute rejected as success (no version bump, snapshot counts
stale) · F-class records can never bind or license.

Focused suites in the pinned environment: **25/25** expert + **26/26**
kernel/audit = 51 green; **full repo suite exit 0**.

## Post-remediation historical replay (V1.1)

Same real window (2025-08-01 → 2025-09-27, 57 boundaries, 114 opportunities,
18,615 coverage rows).  M1 role-declared: 56 SELECTED + 1 AI (same-bar
ambiguity surfaced).  **M2 preference mode: 0 selections, 57 explicit
UNRESOLVED (MP)** — with KP-02/KP-06 nonbinding and no observable
ref_kind/cluster declarations in this generator output, nothing can
legitimately resolve and nothing is forced (V1's single KP-02 selection is
correctly gone).  Temporal violations 0; 54 reference revisions; replay
determinism identical ×3; runtime 12.7 s total (173 ms/boundary avg).

## Verification

- `git diff --check`: clean.
- `information_time.py` sha256 =
  `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
  (unchanged; asserted by test 11 and recorded in the run report).
- No trading, performance or selection-quality claims are made; selection
  quality remains NOT_ESTABLISHED.  No live trades executed.

---

# V1.2 Audit Remediation Addendum — Five Remaining Findings Closed

Base: `856c2c369b36c6fae4e469e24259bbc1aa667de6` ·
Code commit (recorded in the replay manifest):
**`33df36b190fdeb70b1a882e10a84c1bbd099d0f5`** · Scope: minimal, test-backed.

## 1 — Relationship stamp integrity

`validate_relationship_stamp` (public selection API) now rejects and RECORDS
each of: **negative** `known_bar`; **out-of-axis** `known_bar` (no such axis
coordinate: `known_bar >= axis.n_rows` under the codebase's shared-axis
convention that the scene's bar domain is the axis's coordinate domain);
future stamps; off-grid times; missing/unmappable stamps; and **inconsistent
`known_bar`/`known_time` pairs** — the pair must identify the SAME axis
coordinate: `key_for_time(known_time).bar_position == known_bar` (approved
sealed-interface usage; `InformationKey` compares by `bar_position`, the
key type declares `eq=False`).  Every rejection lands in
`dropped_evidence` with its reason and never influences selection.
New adversarial tests: negative bars (declarations and events), out-of-axis
bars, inconsistent bar/time pairs (+ a consistent-pair control), beside the
existing future/off-grid/unmappable tests.

## 2 — Task, role, and comparison completeness

* every preference record's `task_id` must equal the active task — a
  foreign record is inactive with an explicit "task mismatch" cause and
  never influences selection (control test proves the same record applies
  when its task matches);
* registered policy semantics must match the declared role:
  `policy.snapshot_of(policy_id)["value"] == role`, else UNRESOLVED with
  "policy-role mismatch" (both mismatch directions tested; matching control
  passes);
* an unknown `ref_kind` is **incomparable**, never an ordinary "other":
  the declared vocabulary `KNOWN_REF_KINDS = (old-low-htf,
  old-high-reclaimed, local)` is enforced via the rule's `domain`;
* comparisons require **complete comparable evidence across the eligible
  set**: evidence missing for any eligible candidate (or a value outside
  the documented domain) licenses NO comparison and yields UNRESOLVED with
  explicit per-candidate reasons (IC for missing, EP for unknown values) —
  never a subset comparison, never a silent omission.  Tests: partial
  evidence (3 of 4 eligible; the subset would have "won") → UNRESOLVED
  naming the gap; unknown `ref_kind` → UNRESOLVED naming candidate + value.

## 3 — Binding source support (KP-03 disposition)

Determination from the pinned source (`jfjdjdieifne/test @ 6c8bf6fd`):
* `knowledge_foundation/05 §5.4a` P-R — "Support reference | **Partly
  stated** | REF-OLD-LOW-HTF (old low on higher timeframe); REF-OLD-HIGH-
  RECLAIMED ... Both verbal (P1)" — inside the **G-OB-P order-block
  parameter register**;
* `knowledge_foundation/15 §15.2` H — "higher-timeframe preference for
  support references" listed among ICT-source-supported distinctions
  ("only those marked S in §15.3");
* `knowledge_foundation/15 §15.3` S — "'old low on a higher timeframe' as
  a support reference (P1) | **Only as the source's stated condition, not
  as an observed fact**";
* `knowledge_foundation/16 §16.3` — T-S1's Π_T "is an operational
  definition, not a market claim (SWS-02)" and "**is not an ICT-source
  claim**".

The exact comparison+context (old-low-htf beats locally drawn candidates
WHEN SELECTING T-S1's origin/extreme reference) **cannot be established**
by the pinned source — the support-reference statement lives in the
order-block construction context and is expressly a stated condition only.
Per the finding, **KP-03 is now nonbinding research-only (F-class,
licenses="none")**; no replacement rule or citation was invented.  Tests
show unsupported contexts cannot produce a selection through this
preference alone: with the BEST declaration evidence, the origin role
(no policy) stays UNRESOLVED and the extreme role resolves only through
its operational role definition (no `preference:` evidence item, KP-03
inactive) — both roles, KP-03 never active.

## 4 — Tie guard

When the delegated kernel reports (or the independent detector confirms) an
equal-knowable-time tie — top knowable-stamp tie for
`last-confirmed-extreme`, top leg-recency tie with distinct origins for
`origin-of-last-confirmed-leg` — the expert layer returns UNRESOLVED(MP,
"declare a tie policy (SP-18)") **before applying preferences**.  A
preference never overrides a tie.  Tests: valid preference evidence on BOTH
tied candidates (the preference would pick one) for BOTH roles, repeated
with reversed candidate order — outcome UNRESOLVED, survivors = the tied
set, `activated_preferences` empty.

## 5 — Real downstream dependency update

`task_s5_falsifier`'s early-UNRESOLVED exits (missing direction → IC;
direction contradiction → AI) now preserve the dependencies ACTUALLY
evaluated — the supporting leg consumed by `max(vlegs, key=leg_recency_key)`
contributes `start_id` + `leg_id` even though the computation exits
unresolved (result may remain unresolved; no conclusion is forced).
`_diff_results` reports dependency updates as computed changes.  The
changed-evidence test asserts the downstream T-S5 version 2 carries
**H_b and Leg4** in `dependencies` (with a `dependencies` computed-change
entry) while honestly remaining unresolved.

## 6 — Reproducibility and acceptance

`replay_manifest_v1.json` records the **actual timezone-data package
version** (tzdata **2026.6**, via `importlib.metadata` — with documented
module/system fallbacks, never a guess).  The reported **54** is now
labelled `n_asymmetric_adjacent_selection_id_changes_M1` with a
`count_semantics` string: an asymmetric adjacent-selection-ID change count
(consecutive M1 boundaries with different selected IDs), **not ledger
propagation** (no propagation is run or counted in this replay).

## Verification and results

* Focused suites (pinned env): **35/35** expert +
  **26/26** kernel/audit = 61 green; **full suite exit 0**.
  Test commands:
  `PYTHONPATH=src python -m pytest tests/test_contextual_selection_expert_selection.py -q`
  `PYTHONPATH=src python -m pytest tests/test_contextual_selection_csm.py tests/test_contextual_selection_final_audit_patch.py -q`
  `PYTHONPATH=src python -m pytest tests/ -q`
* Historical replay re-run after the code changes; manifest
  `final_source_commit` = **`33df36b190fdeb70b1a882e10a84c1bbd099d0f5`**
  (exact code commit executed).  57 boundaries × 2 modes, 18,615 coverage
  rows; M1 56 SELECTED + 1 AI; M2 0 selections / 57 explicit UNRESOLVED
  (MP); 0 temporal violations; replay determinism identical ×3; 13.9 s.
* `git diff --check`: clean.  `information_time.py` sha256 =
  `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
  (untouched).
* No trading, performance or selection-quality claims; selection quality
  remains NOT_ESTABLISHED.  No live trades executed.

## Remaining limitations (explicit)

* Out-of-axis `known_bar` detection requires the axis (`axis.n_rows` under
  the shared-axis bar-domain convention); with no axis supplied, only the
  negative/future checks apply.
* The bar/time same-coordinate check encodes the codebase's convention
  (scene bar domain == axis coordinate domain); a scene whose bars are NOT
  axis coordinates would need an explicit mapping interface (not invented
  here).
* The comparison mechanism (license rules, domains, completeness) is
  exercised through explicitly injected knowledge records; the DEFAULT
  knowledge set contains no binding comparison (KP-02/03/06 all F-class by
  the two audit rounds), so default-KB selections are never
  preference-produced.
* Policy-role match requires the registered policy `value` to name the role
  string exactly (the registry's documented usage in this codebase).
