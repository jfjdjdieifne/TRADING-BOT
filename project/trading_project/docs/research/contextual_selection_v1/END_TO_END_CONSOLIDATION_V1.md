# CSM V1 — END-TO-END CORRECTNESS CONSOLIDATION

**Task**: audit-verdict remediation (REVISE) on commit `312163a2d17d016067f58141767d3520a92aa93c`.
**Mode**: ROOT-CAUSE PATCH ONLY. No new analytical capabilities, strategies, ICT
definitions, or learning models. No CLOSED-module changes. No trading execution
and no recommendations — causal correctness only.
**Selection quality: NOT_ESTABLISHED** (EP blocker: no acceptable-set
annotations for this instrument/window; unchanged by this work).

---

## A. Exact repository HEAD

- Build base (last audited): `312163a2d17d016067f58141767d3520a92aa93c`
- This deliverable: the consolidation commit on `arena/a41fd997-trading-bot`
  (see `git log -1`). The real-market run (section F) executed on this working
  tree BEFORE the commit; the exact code identities are therefore recorded by
  SHA-256 in the run manifest (`experiment_manifest_v1.json` →
  `source.csm_py_sha256`, `source.experiment_py_sha256`), not by the commit
  hash. Verify any future checkout by hashing the two files and comparing.
- CLOSED `information_time.py` remained BYTE-IDENTICAL throughout
  (sha256 recorded in the manifest; compare with
  `72b03ca614d0f9d763231f9d82799e3ca22b6f7364a7e3051e03af9a37d74ace`).

## B. Root causes (each tied to an audited counterexample)

| # | Audited counterexample | Root cause in code | Fix |
|---|---|---|---|
| 1 | off-grid knowable time bound through raw comparison (T-S2 D1 probe) | `available_at` time path compared raw timestamps; no key validation; task entries accepted time-bearing evidence without an axis | `require_validated_asof` gate on every task entry: time-bearing evidence REQUIRES decision/event boundary + validated `SharedInformationAxis`; `available_at(..., axis=)` validates keys (`axis.available`); off-grid = explicit `X-KNOW` unavailability |
| 2 | late-confirmed T-S5 extreme justified a result | `task_s5` `last-confirmed-extreme` filtered by `knowable_bar <= decision_bar` only (bar-index trap) | time-aware `available_at(..., axis)` governs; late-but-confirmed points get auditable `X-KNOW` exclusions |
| 3 | leg endpoint availability borrowed from one side | `build_legs` `knowable_time=max(known times, default=None)` could claim availability from one endpoint | fail closed: `knowable_time=None` unless BOTH endpoints carry verified times |
| 4 | time-based `status_at` applied a foreign-domain `info_bar` | `status_at` mixed-domain fallback branch matched before the conservative branch (dead code) | time queries NEVER fall back to bars: a transition without `info_time` is unplaceable and is not applied; bar axis only for bar-only queries |
| 5 | cross-view containment returned `contained` on raw bar numbers | `sp05_containment` no-times path had no domain check | cross-view pairs without timestamps are REFUSED; index comparison only inside one declared domain (`view_id`) |
| 6 | B2 regeneration reset recorded lifecycle events | experiment regenerated `pts` per boundary and never re-applied the ledger's transitions | `InterpretationLedger.restore_history(pts)` after every regeneration (and in replay checks); regression asserts the broken reference stays broken |
| 7 | T-S2-only recording never persisted transitions | `_mark_broken`/`restore_history`/`_payload_ids` scanned only `points`/`claims_points` | all three walk `refs_by_view` values too (`_payload_points`); transitions carry `event_ref` |
| 8 | applying an event's own break flipped its binding kind | `propagate` applied the break at the event time before recomputation; replay saw the ref as already broken | `StatusTransition.event_ref` + `status_at(..., excluding_event_ref=)` reconstruct PRE_EVENT_STATE; results carry explicit `event_phase` {PRE_EVENT_STATE, EVENT_BINDING, POST_EVENT_STATE}; `binding_kinds` included in `_diff_results` |
| 9 | `tie_bound=True` contradicted the declared UNBOUND policy | boolean parameter independent of `tie_policy` | behavior derives from the declared policy: `TIE_CROSS_EQUAL_BOUND_V1` added; contradictory combinations raise `ValueError` |
| 10 | registry mutation silently changed historical policy meaning | `PolicyRegistry.register` overwrote entries; `ref()` unversioned | entries versioned (`O:P-x@vN`); results carry `policy_snapshots` (identity/version/value at creation); `_diff_results` reports `policy_refs`/`policy_snapshots` changes |
| 11 | T-S3 justified with `decision_time=None` | `_mk` positional call dropped `decision_time`; no boundary enforcement | `require_validated_asof` rejects time-bearing T-S3 without boundary; every T-S3 result records its `decision_time` |
| 12 | provisional policy did not survive replay | recompute dropped `allow_provisional`/`tie_policy` in an earlier build; now preserved — and `event_ref`/`axis` added to the replay contract | `_recompute` replays the complete declared task contract; regression asserts binding kind and policy snapshot stability |
| 13 | A→B→C probe left B and C at version 1 | `propagate` matched only direct id dependencies, once | transitive waves over registered result-dependency edges (`record` captures uid deps; explicit `depends_on_results`); each result recomputed at most once per call; `dependency-cycle` entries emitted explicitly; unrelated results untouched |
| 14 | 13 terminal provisional F-T ids vanished from the full inventory | F-T `update` branches moved the running extreme WITHOUT retaining the displaced provisional (F-K retains superseded; F-T dropped) | displaced extremes retained as `STATUS_SUPERSEDED` with `superseded_by` (SWS-04c-consistent bookkeeping; excluded from every selection path — X-SUPER — and from legs) |

Determination for counterexample 14 (task §6): **representation lifecycle
issue AND a genuine retention defect** — the provisional-vs-final difference is
expected at the semantic level (a displaced extreme is not a turning point),
but silently dropping the candidate broke inventory completeness. Retention is
now lifecycle bookkeeping; selection outcomes are unchanged (regression).

## C. Reused CLOSED infrastructure (read-only)

- `trading_system.research.information_time` (CLOSED 6.2A-0):
  `InformationKey`, `InformationKeyError`, `InformationPhase`,
  `TimeIndexedTimelineAdapter`, `SharedInformationAxis` (constructed in the
  experiment/ledger layer; the module itself is untouched — byte-identical).
- Prior OPEN build blocks kept and extended in place: `StatusTransition` /
  `status_at`, `stable_point_id`/`stable_leg_id`, `reference_state_at`,
  `InterpretationLedger` (change-facts vs computed diffs), `PolicyRegistry`,
  `Exclusion`/`UnresolvedState` records. No duplicate machinery was added.

## D. Minimal code changes

Files touched (5, plus tests):
1. `src/trading_system/research/contextual_selection/csm.py` — kernel fixes
   (sections B1–B5, B7–B14): `TIE_CROSS_EQUAL_BOUND_V1`, event-phase
   constants, `StatusTransition.event_ref`, `status_at` restructure,
   `available_at(axis=)`, `_time_bearing`/`require_validated_asof`, `build_legs`
   fail-closed, `sp05_containment` domain check, task entries S1/S2/S3/S5,
   `PolicyRegistry` versioning, `SelectionResult.event_phase`/`policy_snapshots`,
   `InterpretationLedger` (`_payload_points`, `_mark_broken(event_ref=)`,
   `restore_history`, `_result_deps`, transitive `propagate`,
   `_find_dependency_cycle`, `_diff_results`, `snapshot`),
   `ft_turning_points` `_retire`, `candidate_record` start/end ids.
2. `src/trading_system/research/contextual_selection/__init__.py` — exports.
3. `docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py`
   — validated axis on every task entry, `restore_history` after regeneration
   (B2 fix), `event_ref`/`event_phase`, full task-variant serialization
   (survivors+reasons for T-S1_extreme/T-S5), leg coverage rows, prefix-vs-full
   retention probe, always-on self-check, manifest + REPRODUCE.md.
4. `tests/test_contextual_selection_end_to_end.py` — NEW adversarial gate (14).
5. Existing four test files — fixture migration to the validated as-of
   contract (axis + decision boundaries on every time-bearing call; legs carry
   verified times; two expectations updated to the repaired contract:
   cross-view-no-times now refused (was "contained"); F-T tie test now asserts
   retention of the displaced extreme).

No CLOSED module modified (diff check: `git diff 312163a..HEAD --stat` shows
no `information_time.py`/release-seal paths). No new policies: the only new
policy constant is `TIE_CROSS_EQUAL_BOUND_V1`, the declared counterpart of the
already-existing equality-crossing BEHAVIOR (task §4 requires the declared
policy and the behavior to agree).

## E. Finding-by-finding regression evidence

`tests/test_contextual_selection_end_to_end.py` — one behavioral test per
audited counterexample (asserting states, bound sets, transition histories,
computed version chains — not status names):

| Test | Counterexample reproduced | Behavioral assertion |
|---|---|---|
| `test_off_grid_knowable_time_is_not_a_verified_claim` | 1 | off-grid ref never binds (X-KNOW); axis-less time-bearing call raises |
| `test_late_confirmed_extreme_never_justifies_at_decision_time` | 2 | bar-trap point excluded X-KNOW at t; selected at t' > knowable |
| `test_missing_endpoint_time_makes_leg_availability_fail_closed` | 3 | leg with one missing endpoint time: `knowable_time is None`, unavailable |
| `test_time_query_never_borrows_a_foreign_domain_bar_index` | 4 | unplaceable transition not applied by time query; placeable one applies |
| `test_cross_view_containment_without_times_is_refused` | 5 | ValueError across views; same-domain indices still work |
| `test_lifecycle_reset_at_b2_is_prevented_by_restore_history` | 6 | regenerated world without restore = fresh confirmed (the defect); with restore = broken, and T-S1 cannot re-select it |
| `test_t2_only_recording_persists_broken_transition` | 7 | refs_by_view-only payload: break persists on the point; replay kind stable |
| `test_pre_event_binding_survives_the_events_own_transition` | 8 | first-break stays first-break with `excluding_event_ref`; phases recorded; `binding_kinds` lands in computed diffs when it changes |
| `test_tie_policy_and_tie_behavior_cannot_contradict` | 9 | contradiction raises; UNBOUND = no equality bind; BOUND = bind; snapshot names the policy |
| `test_policy_mutation_after_result_creation_is_never_silent` | 10 | v1 snapshot preserved; `ref()` versions differ; recompute diff names the policy fields |
| `test_t3_requires_decision_boundary_for_time_bearing_legs` | 11 | missing boundary raises; result records its decision_time |
| `test_provisional_policy_survives_replay_with_exact_declared_values` | 12 | `allow_provisional=True` replay reproduces `provisional:first-break`; default excludes |
| `test_transitive_dependency_recomputation_a_b_c` | 13 | A→B→C all leave version 1 in one propagate; unrelated D untouched; cycle reported |
| `test_terminal_provisional_candidates_retained_across_prefixes` | 14 | prefix ids ⊆ full-history inventory; retired rows carry `superseded_by`; superseded never selected |

Certified suite (pandas==2.2.3, numpy==2.2.6): focused
`tests/test_contextual_selection_*.py` = 69/69; FULL suite `tests/` = 1,699
collected, pytest exit 0 (see `full_suite_v2.log`).

## F. Real-market run reproduction

Full regeneration (no outdated records reused) with context 2025-08-01 onward
and evaluation window 2025-09-20..27 UTC. Authoritative outputs (outside Git,
regenerable):
- `/home/user/work/csm_run/experiment_record_v2.json`
- `/home/user/work/csm_run/candidate_ledger_v1.jsonl.gz`
- `/home/user/work/csm_run/propagation_log_v1.jsonl`
- `/home/user/work/csm_run/experiment_manifest_v1.json` — source commit,
  code hashes, input CSV identities, policy registry with versions, window,
  coverage counts, event bindings, transitions, dependency updates, ambiguity
  accounting, incomplete-coverage report, retention probe, self-check
- `/home/user/work/csm_run/REPRODUCE.md` — exact command + identities

Run numbers and self-check (from `experiment_manifest_v1.json` and the run
record; the run executed on this working tree — code identities by SHA-256):

| Item | Value |
|---|---|
| context / evaluation | 2025-08-01 → 2025-09-28 UTC (eval window 09-20..27) |
| bars | 1m=83,520 · 5m=16,704 · 1h=1,392 (shared axis: true completion times) |
| boundaries | 9 (D1, D2, D3, B0, B1, M1, B2, D4, D5 — B0/B1/M1/B2 = the audited B-pattern) |
| event bindings | 70 rows / 96 bindings = **19 first-break + 77 later-interaction** |
| self-check | **axis_verified_bindings = 96/96; future_reference_violations = 0** |
| candidate rows | 274,821 (points AND legs, start/end ids, per task variant) |
| ledger | 1,570 results (1,520 justified / 45 unresolved / 5 falsified); 1,461 revisions = 96 change-facts + 1,365 computed recomputations |
| historical transitions re-applied after regeneration | 536 |
| incomplete dependency coverage | [] (0 dependents without payload) |
| identity recognition | 653/653 eval-window candidates recognized in full context |
| replay consistency (SWS-04d) | **4/4 equal** (incl. B2_post6: recomputed == stored == None after in-interval breaks) |
| ambiguity | 25,087 records / 2,927 distinct events (1,227 proven / 2,871 constrained / 20,989 unavailable) |
| retention probe | prefix-only ids **0/0/0/0/0** (all 5 reps); superseded retained 481/307/732/5,594/8,462 |
| SP-16 | disagreement reported at all 9 boundaries (never merged) |
| selection quality | NOT_ESTABLISHED (unchanged) |

OLD-vs-NEW comparison (recorded in the run): the old record's bound ids use
the pre-consolidation bar-index scheme — 16 old bound ids are **unverifiable
under the stable scheme, explicitly not cleared**; 0 confirmed
future-reference uses among resolvable rows (previously the audit measured
36/59 contaminated event rows).

The stale tracked artifacts (`experiment_record_v2.json` @ e90a62f short
window, `candidate_ledger_v1.jsonl.gz`) are retained for historical comparison
ONLY; the manifest and this report identify the authoritative output.

## G. Historical state and dependency evidence

- B2 pattern: at boundary B2_post6 the event-ordering is now historically
  consistent (events of (B1, B2] processed BEFORE B2's tasks): the Sep-24
  reference broken during the interval is NOT re-selected at B2
  (`stored == recomputed == None`), and `restored_transitions` totals 536
  across the 9 boundaries prove regeneration never resets lifecycle state.
  Regression test 6 encodes the exact audited reset-and-restore behavior.
- Transitive propagation: 1,461 computed revision rows (96 change-facts +
  1,365 recomputations, each with computed diffs — 0 caller-supplied strings);
  0 incomplete dependency coverage. Result-uid transitive edges (A→B→C) and
  explicit `dependency-cycle` detection are exercised by regression test 13.
- T-S2-only persistence and pre/post-event stability: regression tests 7–8;
  the run's `binding_events[*].event_phase` rows preserve PRE_EVENT_STATE /
  EVENT_BINDING / POST_EVENT_STATE for every binding.

## H. Candidate and ambiguity coverage

- `candidate_ledger_v1.jsonl.gz` covers points AND legs (start/end ids) for
  every boundary/rep/task; rows carry status-at-decision, eligibility,
  exclusion code, selected flag, unresolved reason.
- Every task variant serializes survivors + reasons (T-S1_origin,
  T-S1_extreme, T-S5, T-S2 binding rows).
- Retention probe (prefix-vs-full): `n_prefix_only_ids = 0` for C_FK5,
  C_FK12, C_FT250, F_FK6, F_FT80 (the 13 audited terminal-provisional ids are
  retained — superseded-but-present with `superseded_by`); regression test 14.
- Ambiguity accounting (all-task `affecting` scan): 25,087 records / 2,927
  events; 15 material affecting-actual-selection rows listed in the record
  (all with `task_status=unresolved` — ambiguity never silently decides);
  every task output carries survivors + reasons.

## I. Exact tests and commands

```bash
# environment (pinned)
python -m venv ~/work/venv2 && ~/work/venv2/bin/pip install pandas==2.2.3 numpy==2.2.6 pytest
# focused adversarial + consolidation gate
cd project/trading_project && PYTHONPATH=src ~/work/venv2/bin/python -m pytest \
  tests/test_contextual_selection_csm.py tests/test_contextual_selection_audit_regressions.py \
  tests/test_contextual_selection_final_audit_patch.py tests/test_contextual_selection_causal_integration.py \
  tests/test_contextual_selection_end_to_end.py -q
# certified full suite
PYTHONPATH=src ~/work/venv2/bin/python -m pytest tests/ -q
# real-market run (identities in the manifest)
PYTHONPATH=src ~/work/venv2/bin/python \
  docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py \
  --mirror-dir <btc-usdt-1m-mirror> --out-dir <out> \
  --months 2025-08,2025-09 --start 2025-08-01 --end 2025-09-28 \
  --old-record docs/research/contextual_selection_v1/experiment_record_v2.json --src src
```

## J. Remaining limitations (deliberate scope boundaries)

- Selection quality remains NOT_ESTABLISHED (EP); nothing here evaluates
  selection usefulness.
- `allow_provisional=True` at event replay remains an explicit policy choice
  of the experiment (occurrence-visible contract), not a market policy.
- Same-bar OHLC ambiguity remains intrinsically unresolvable without endpoints;
  the pipeline records it (proven/constrained/unavailable) and never invents
  ordering.
- The manifest's `git_head_at_run` identifies the base commit; the working
  tree code is identified by SHA-256 (see A).
- First-break vs later-interaction classification is a policy choice of the
  knowledge contract (file 16), preserved — not redefined.
- Trailing provisional endpoints (F-T terminal provisional at the data edge)
  remain provisional by construction; they are now RETAINED in the inventory.

## K. Independent audit instructions

1. `git log -1` on `arena/a41fd997-trading-bot`; verify `information_time.py`
   hash equals the manifest value.
2. Run section I commands in order (venv, focused 69, full 1,699).
3. Re-run the 14 probes from the audit against the APIs — each must now fail
   closed / raise / exclude as asserted in section E (the test file names the
   exact behavioral expectation).
4. Re-run the experiment command; compare `experiment_manifest_v1.json`
   (source hashes, counts, self-check `future_reference_violations == 0`,
   retention `n_prefix_only_ids == 0` for every rep).
5. Confirm no file under CLOSED paths differs from `312163a`.

## L. Readiness for contextual-learning development

With the causal-state contracts enforced end-to-end (validated as-of,
append-only lifecycle, explicit event phases, versioned policies, transitive
recomputation, complete inventories), the recorded histories are now safe
inputs for a future contextual-learning phase. This task did NOT implement,
prototype, or authorize any learning model (LRN-01..06 remain in force);
selection quality stays NOT_ESTABLISHED and the learned-preference interface
(L-class) remains unimplemented.
