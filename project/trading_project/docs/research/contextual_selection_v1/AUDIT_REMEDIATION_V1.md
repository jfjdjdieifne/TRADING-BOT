# Contextual Selection V1 — Audit Findings Remediation

Status: COMPLETE (targeted patch + causal reproduction; no redesign)
Date: 2026-10-12
Branch: arena/a41fd997-trading-bot (session branch; no PR; no canonical push)
Audited commit: `4e041980f17a34e84553af22320fe9cc9e95b5eb`
Environment: certified venv — pandas 2.2.3 / numpy 2.2.6

Scope discipline: PATCH OF CONFIRMED DEFECTS ONLY. No new market model, swing
family, learning algorithm, or strategy. No trading recommendations. No live
execution. No CLOSED-module modifications. Selection quality remains
**NOT_ESTABLISHED** (unchanged). No learned intelligence is claimed.

---

## A. Repository state / exact HEADs

| Item | Value | Verification |
|---|---|---|
| Remote HEAD before work | `4e041980f17a34e84553af22320fe9cc9e95b5eb` | `git ls-remote origin arena/a41fd997-trading-bot` (matches audited commit) |
| Local working tree | reset to `4e041980…` exactly | `git log`; clean tree except keep-list untracked files |
| CLOSED modules / seals / MANIFEST | untouched | no writes outside the files listed in D |
| Canonical branches | untouched | no fetch/push to canonical; no PR |
| Data inputs | `BTCUSDT_1m_2025-08.csv` sha `15d26d23…`, `2025-09` sha `e1d5c8f3…` @ `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70` | sha256 re-verified before the rerun |
| Run provenance (record) | `git_head_at_run=4e041980…`, `csm_py_sha256=29eca055…`, `experiment_py_sha256=fda039bd…` | recorded inside `experiment_record_v2.json → summary.source_version` |

## B. Finding-by-finding remediation

### D1 — Cross-timeframe future leakage (36 of 59 event records)
**Reproduced exactly** on the old record with the repaired availability axis:
`unavailable_at_event_time = 36 bindings in 36 distinct events of 59` (audit
counter reproduced verbatim), and root cause #2 quantified: `59 retroactive
bindings in 57 events` (old events were scanned with the selection computed at
the LATER boundary). Examples with event time vs. knowable time are in
`experiment_record_v2.json → comparison_v1_vs_v2`.
**Root causes:** (1) `task_s2` compared `knowable_bar <= event_bar` across
view domains (1h indices vs 5m indices); (2) the experiment loop applied each
boundary's fresh T-S1 selection to events of the PREVIOUS interval.
**Fix:** shared information-time axis — `PointCandidate/LegCandidate` carry
`occurrence_time`/`knowable_time`; `available_at()` compares timestamps
whenever both sides have them and REFUSES bar fallback when a time query has a
timeless candidate (fail-loud, never silent cross-domain compare);
`task_s2` requires `event_time` for multi-view queries (ValueError otherwise);
`reference_state_at()` serves chronological event replay — events in
(b_{i-1}, b_i] use only the state selected at b_{i-1}, each reference filtered
by its own availability time. The regenerated run has
**0 future-reference violations over 74 events** (recorded in the comparison).
**Tests:** `test_D1_cross_timeframe_unavailable_reference_cannot_bind`,
`test_D1_cross_view_requires_time_axis`,
`test_D1_chronological_event_replay_uses_prior_state_only`.

### D2 — F-K premature confirmation
**Root causes:** confirmation flush ran BEFORE the bar's supersession pass and
the supersession window used a strict upper bound (`i < knowable`), so a more
extreme point AT the confirmation bar could not supersede (auditor's k=2
fixture: High 10 @2 confirmed at 4 despite High 11 @4); shortened left-edge
windows (`max(0, i-k)` for `i < k`) emitted candidates without full left
context.
**Fix:** registration requires full left context (`i >= k`) unless the
explicitly different policy slot `allow_short_left=True` is declared; SWS-04c
supersession is endpoint-inclusive (`occurrence < j <= knowable`); at each bar
the order is (1) register (2) supersede (3) confirm-flush. Occurrence and
confirmation/availability times remain separate fields.
**Tests:** `test_D2_fk_confirmation_endpoint_inclusive_supersession` (the k=2
fixture verbatim), `test_D2_fk_full_left_context_required`.

### D3 — Mutable final status contaminates history
**Root cause:** single mutable `status` mutated by later supersession; as-of
queries saw the future state.
**Fix:** `StatusTransition` (append-only, with information time) +
`PointCandidate.status_at(bar, time)` reconstructs the status knowable at the
queried boundary; a query before the first transition returns the constructed
`initial_status`; later supersession never rewrites the earlier provisional
state. `sp01_knowability` evaluates `status_at()` and handles
`broken` (X-STATE). `allow_provisional` is explicit task-level policy:
without it provisional references get the explicit X-STATE exclusion — never
silently confirmed (W4 semantics preserved; tests added).
**Tests:** `test_D3_later_supersession_does_not_rewrite_earlier_state`,
`test_D3_provisional_state_explicit_exclusion`, plus W4/W8 golden paths.

### D4 — Same-bar ambiguity and equal-extreme ties
**Root causes:** `build_legs` synthesized intrabar order from generator list
ordering (zero-duration directional legs between same-bar high/low points;
equal-level pairs silently "down"); F-T used `>=`/`<=` and silently preferred
the LATEST equal extreme; F-T update-vs-reversal on one bar silently picked
one branch order.
**Fix:** no zero-duration or zero-amplitude directional legs — same-bar pairs
and equal-level pairs are skipped and recorded as explicit
`same-bar-order-unresolved` / `zero-amplitude-leg` ambiguity records; F-T
equal-extreme ties follow the versioned policy `TIE-FT-EQ-FIRST-V1` (default,
keeps first) or the explicitly declared `TIE-FT-EQ-LAST-V1` — never implicit;
a bar that both extends the extreme and completes the reversal records a
`same-bar-extreme-vs-reversal` ambiguity (tagged `same_bar_order="unresolved"`)
and no sequence is synthesized. Regenerated run: **25,087 ambiguity records**
(counted, first 200 serialized in the record).
**Tests:** `test_D4_no_zero_duration_legs_from_same_bar_order`,
`test_D4_ft_equal_extreme_tie_policy_explicit`,
`test_D4_ft_same_bar_extreme_and_reversal_unresolved`.

### D5 — Fake dependency propagation
**Root cause:** `InterpretationLedger.propagate()` appended caller-supplied
before/after strings and called it propagation (the old W8 test asserted exactly
that).
**Fix:** `record(result, payload=…)` stores the task kind + inputs; every
result carries explicit `dependencies`; `propagate(update_bar, changed_ids,
changed_states=…)` (a) records upstream FACTS via `record_change` (append-only)
and (b) RECOMPUTES every dependent from its stored payload as of the update
boundary via an internal dispatcher (`_recompute`), then appends a new result
version whose `computed_changes` are the ACTUAL diffs (`_diff_results`).
Prior versions are preserved. A dependent without a payload is marked
"not recomputable" and NO propagation is claimed for it. Caller strings are no
longer accepted anywhere.
**W8 counterexample (auditor's bar-53/bar-56):** now reproduced with the
correct semantics — at bar 53 the break of L_b recomputes T-S1 to
`unresolved(IC)` (computed) and T-S5 to `falsified` (computed); **H_b does NOT
appear at 53** (successor leg knowable only at 56); at bar 56 the recomputation
moves T-S1 to H_b with a computed `selected_id: None → H_b` diff.
**Tests:** rewritten `test_W8_role_change_and_propagation`,
`test_D5_propagate_never_accepts_caller_before_after_strings`.

### D6 — Direction / T-S3 depth / candidate ledger
**Root causes:** the experiment derived T-S5 direction from note strings;
`task_s5` accepted any/missing direction silently; T-S3 depth printed
`min(|Δp|, 0)` (= 0 always); coverage claims rested on aggregate counts.
**Fix:** `SelectionResult.direction` is derived from the supporting leg data
(T-S1/T-S5 never read note strings); directional T-S5 roles require a
supported direction and return explicit `IC` unresolved when it is missing or
invalid; changing direction changes the resolved reference (tested);
T-S3 depth = `LegCandidate.depth` = `|p_start − p_end|` with numeric tests
(depth=10 / depth=20 asserted); `candidate_record()` serializes the full
coverage contract per candidate (identity, rep identity, occurrence/knowable
times, status_at_decision, eligibility, exclusion code+detail, selected flag,
unresolved reason) — the regenerated run wrote **126,900 candidate rows**
(`candidate_ledger_v1.jsonl.gz`) from which every coverage statement is
verifiable.
**Tests:** `test_D6_direction_sensitive_falsifier_effect`,
`test_D6_candidate_ledger_covers_every_candidate`, W2/W3 golden extensions.

### D7 — Policy and provenance
**Fix:** `PolicyRegistry.register(…, kind=…)` distinguishes
`research_configuration` / `authorized_analytical_policy` /
`factual_calculation` / `ict_source_interpretation` /
`source_declared_procedure`; every experiment policy is classified in the
record (`summary.policy_classification`) — builder research values
(P-TF, F-K/F-T grids, tie default) are marked `research_configuration` and
NEVER owner-approved; the SXM boundary times are `ict_source_interpretation`;
SP-03/SP-18 rules are `source_declared_procedure`. Sensitivity requirements
are preserved on the entries. The record's `source_version` now identifies the
ACTUAL source used for the run (git head at run + sha256 of `csm.py` and the
experiment script) instead of the wrong `target_commit`. Input/output paths
are argparse-configurable (`--mirror-dir`, `--out-dir`, `--months`, `--start`,
`--end`, `--old-record`, `--src`). No CLOSED contract touched.

## C. Root causes and minimal fixes (summary)

| # | Root cause | Minimal fix |
|---|---|---|
| D1a | cross-domain index comparison in availability | timestamp axis + fail-loud `available_at` + `event_time` required cross-view |
| D1b | later-boundary selection applied retroactively | chronological replay via `reference_state_at` (previous-state-only) |
| D2a | confirm-flush before endpoint supersession | supersede-inclusive window, register→supersede→confirm order |
| D2b | short left-edge windows | full left context required (`allow_short_left` explicit policy) |
| D3 | mutable status | append-only `StatusTransition` + `status_at()` |
| D4a | invented intrabar order | same-bar/zero-amplitude ambiguities; no zero-duration legs |
| D4b | silent equal-extreme preference | versioned tie policies, first-by-default |
| D5 | string-append "propagation" | payload-stored recomputation + computed diffs + versions |
| D6a | direction from notes | structural `direction` + explicit IC on missing/inconsistent |
| D6b | depth = min(x, 0) | `abs(Δp)` + value tests |
| D6c | aggregate-only coverage | `candidate_record` serialized candidate ledger |
| D7 | promoted research config / wrong commit / fixed paths | policy `kind` field; run source hashes; argparse paths |

## D. Files changed

| File | Change |
|---|---|
| `src/trading_system/research/contextual_selection/csm.py` | D1–D7 kernel fixes (timestamps, F-K/F-T semantics, status history, real propagation ledger, direction/depth, candidate_record, policy kinds) |
| `src/trading_system/research/contextual_selection/__init__.py` | exports for the new API surface |
| `tests/test_contextual_selection_csm.py` | W5/W10 time-axis calls; W8 rewritten to real-propagation counterexample; W2/W3 value & direction asserts |
| `tests/test_contextual_selection_audit_regressions.py` | **NEW** — 14 focused regression tests (one block per defect) |
| `docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py` | **NEW** — repaired rerun (chronological replay, provenance, configurable paths, candidate ledger, old-vs-new comparison) |
| `docs/research/contextual_selection_v1/experiment_record_v2.json` | **NEW** — regenerated run record (with embedded comparison) |
| `docs/research/contextual_selection_v1/candidate_ledger_v1.jsonl.gz` | **NEW** — 126,900 serialized candidate rows (coverage evidence) |
| `docs/research/contextual_selection_v1/AUDIT_REMEDIATION_V1.md` | this report |

Preserved unchanged: the audited artifacts `experiment_contextual_selection_v1.py`
and `experiment_record_v1.json` (history/comparison only — never evidence of
corrected behavior), all golden fixtures and their expectations (except W8,
whose old assertions encoded the D5 defect).

## E. New regression tests

`tests/test_contextual_selection_audit_regressions.py` (14 tests):
cross-timeframe availability (×2), chronological event replay, confirmation
endpoint (auditor's k=2 fixture), full left-context, historical supersession
stability, provisional-state policy, same-bar order, equal-extreme ties,
same-bar extreme-vs-reversal, real recomputation (no caller strings),
direction-sensitive falsifiers, candidate-level completeness, prefix-replay
determinism. Plus the strengthened golden file (W8 counterexample, W2 depth
values, W3 direction effect + missing-direction IC).

## F. Real-market rerun (CSM-SEL-EXP-V2)

Command (paths configurable):
`python experiment_contextual_selection_v2.py --mirror-dir … --out-dir … --old-record …/experiment_record_v1.json`

Regenerated from the repaired implementation on the same verified inputs
(1h + 5m views; 5 representations; 9 frozen boundaries incl. SXM B0/B1/B2):

| Quantity | Value |
|---|---|
| Binding events (fresh crossings, chronological replay) | **74** |
| Candidate rows (serialized coverage) | **126,900** |
| Same-bar/tie ambiguity records | **25,087** (first 200 serialized) |
| Task results | 1,717 (1,451 justified / 133 unresolved-IC / 133 falsified) |
| Exclusion work-units (cumulative, all retained with codes) | X-SUPER 520,071 / X-POL 410,842 / X-KNOW **5,349** / X-STATE 601 |
| Dependency recomputation entries | 1,659 (change-facts + recomputed versions with COMPUTED diffs) |
| SP-16 representation disagreement | 9/9 boundaries (reported, never merged) |
| Replay consistency (truncated rerun == stored) | 4/4 equal |
| Future-reference violations in the new events | **0 / 74** |

Note on the falsified/unresolved counts: they are the computed W8-pattern
effects (a break of the active reference falsifies its T-S5 claim and blocks
T-S1 until the successor leg is knowable) — they are integrity outputs, not
trading judgments.

## G. Old-vs-new comparison (old numbers are NOT targets)

| Check | Old (4e04198) | Repaired |
|---|---|---|
| events with references unavailable at event time | **36 of 59** (audit counter reproduced exactly) | **0 of 74** |
| retroactive later-boundary bindings | 59 bindings / 57 events | 0 (chronological replay only) |
| propagation entries | 174 caller-supplied strings (NOT causal evidence) | 1,659 entries: change-facts + recomputed versions with computed diffs |
| candidate coverage | aggregate counts only | 126,900 serialized rows |
| tie/same-bar handling | silent latest-equal + invented order | explicit policies + 25,087 recorded ambiguities |
| target provenance | `target_commit=c96b9a56…` (wrong for the run) | git head at run + sha256 of the exact code files |

Selections also shifted where the repaired semantics require (e.g. F-T fine
view one bar at B2/D4 via `TIE-FT-EQ-FIRST-V1`; F-F-K fine view at B2/D5 via
same-bar exclusion) — such differences are expected outputs of the fix, not
regressions; SP-16 disagreement remains reported at every boundary.

## H. Candidate-coverage evidence

`candidate_ledger_v1.jsonl.gz` — one JSON row per candidate per boundary run
(126,900 rows): candidate id, representation id, side, occurrence/knowable
bars AND times, `status_at_decision`, final status, `same_bar_order`,
eligibility flag, exclusion code + detail, selected flag, unresolved reason.
Any coverage statement in this report can be verified by filtering these rows;
aggregate histograms in the record are derivable from them.

## I. Dependency-recomputation evidence

`experiment_record_v2.json → propagation_revisions`: every entry names the
dependent uid/subject, the version number, and `computed_changes` produced by
re-running the stored task payload as of the update boundary (see the sample
where T-S1 `status: justified→unresolved` and `selected_id: …→None` are
computed diffs, and T-S5 `→falsified` is computed). Golden W8 asserts the
bar-53/56 knowability gate explicitly. Non-recomputable registrations are
marked as such and never claimed as propagation.

## J. Remaining limitations

1. Selection quality: **NOT_ESTABLISHED** — unchanged; no acceptable-set
   annotations exist (EP); nothing in this remediation evaluates quality.
2. F-T trailing extremes have `knowable_time=None` (availability unknowable
   until a reversal); time-axis queries fail loud on them rather than guessing
   (conservative; may exclude legitimate end-of-window references).
3. The F-K/F-T grids, tie defaults, and 1h/5m timeframes remain builder
   research configuration (SP-12 sensitivity must still be run before any
   preference claim).
4. Boundary-time propagation recomputes dependents whose inputs include the
   changed id; a full transitive dependency graph across task families is not
   built (SP-20 covers registered dependents only).
5. Same-bar ambiguity is recorded but not resolved — resolution would need
   tick/intrabar data (MO) or a declared policy; it is correctly unresolved.
6. The record keeps bounded samples of large exclusion diffs (exact counts
   preserved); full detail lives in the candidate ledger.

## K. Independent re-audit instructions

1. Verify remote HEAD = this remediation commit on `arena/a41fd997-trading-bot`
   and that the audited commit `4e041980…` is its parent context (history
   preserved: `experiment_record_v1.json` untouched).
2. `pytest tests/test_contextual_selection_csm.py tests/test_contextual_selection_audit_regressions.py`
   in pandas 2.2.3 / numpy 2.2.6 → 26/26 (includes the auditor's k=2 fixture
   and the W8 bar-53/56 counterexample verbatim).
3. Re-run `experiment_contextual_selection_v2.py` (§F command) → identical
   selections (record `replay_checks` all equal; record hashes match:
   `csm_py_sha256`, `experiment_py_sha256` in `summary.source_version`).
4. Re-derive the 36/59 counterexample from `experiment_record_v1.json` +
   `candidate_ledger_v1.jsonl.gz` (compare each old event's bound ids against
   their knowable times) — expect 36; re-run the new events — expect 0.
5. Verify propagation claims: every `computed_changes` entry must be
   recomputable from the stored payload; no entry may carry caller strings.
6. Verify no CLOSED files changed: `git diff 4e041980… --stat` lists only §D.
7. Confirm the report claims nothing about selection quality or learned
   intelligence.

## L. Exact next step toward genuine contextual learning

The remediation removes the causal-integrity blockers; the learning blockers
are unchanged and precise:

1. **Owner decision (recorded, not invented):** authoritative swing-selection
   values (S2) and the objective-B acceptance threshold.
2. **Annotation protocol (file 03 §2) + file 19 §19.1 acceptable-set schema**
   applied to source-verified cases (SXM-005 unique / SXM-006 ambiguous,
   GU-2026-04-17, ICT-2024-09-16) — the candidate ledger now provides the
   exact eligibility/exclusion base the annotators must judge.
3. Only then: objective A/B harness on the annotated set and a measured
   selection-quality comparison vs the declared-rule baselines (SP-12/SP-16
   sensitivity grids). Until step 2 exists, no preference learning is honest.
