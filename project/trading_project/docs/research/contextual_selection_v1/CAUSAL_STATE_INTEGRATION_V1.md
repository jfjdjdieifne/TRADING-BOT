# Causal-State Integration & Root-Cause Remediation V1

- **Task:** CONTEXTUAL SELECTION — CAUSAL STATE INTEGRATION AND ROOT-CAUSE REMEDIATION V1
- **Mode:** targeted architectural repair + real-market reproduction (no new strategy, no live execution)
- **Branch:** `arena/a41fd997-trading-bot` (from audited `fd7e27ee4230538132f4dceadaa4ab024d65032c`)
- **Knowledge base:** `test@6c8bf6fd` (`knowledge_foundation/16_SWING_WAVE_SELECTION.md` §16.3)
- **Data:** `BTCUSDT_1m_2025-08/09` from `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70`
  (sha256 `15d26d23…0a0cf4` / `e1d5c8f3…48979` — hash-verified identical to the audited inputs)
- **Environment:** Python 3.11 + pandas 2.2.3 / numpy 2.2.6 (venv2)
- **Selection quality:** **NOT_ESTABLISHED** (unchanged — this task is a correctness repair)

---

## A. Root-cause report (shared causes of the recurring defects)

The observation class was: *the same state/information-time defect kept recurring under
different masks — unbound status transitions, same-bar claims of opposite polarity,
breaks that could not bind, later crossings treated as noise, window-dependent
selections.* Each was patched in isolation before and each returned. The shared causes:

| ID | Root cause | Evidence in the audited run (`fd7e27e`) |
|----|-----------|------------------------------------------|
| RC-1 | **Mixed time axes inside one task:** lifecycle (2.1/2.2) used occurrence time (`time`/`t1_time`), eligibility (2.4/2.5/2.6) used event time (`knowable_time`), T-S2 used decision time. No single time axis per task. | Invert 2.1/2.2 labels in the left-context window flip T-S1 origin; eligibility never changes → T-S1 outcome flips silently |
| RC-2 | **Lifecycle/eligibility entanglement in T-S2's broken gate:** the gate required `status=="confirmed"` at **decision time**, silently dropping factual close crossings of already-broken levels and inventing a first-break-only binding policy. | **43 later close crossings of broken refs / 37 timestamps** — the auditor found them raw and found the gate had no foundation in knowledge base `16` (which defines broken references as binding *defeaters* at state-change time, never first-break-only) |
| RC-3 | **Pre/post-event conflation:** selections and bindings were computed/verified against post-event states, so state-change times were effectively ignored and future information could leak into event-bound results. | 36 of 59 old records bound references unavailable at event time; 59/57 retroactive bindings; old break states (`broken`, `brk_time=t1`) recorded current status without the event's pre/post phase → `status_at` mislabeled transitions |
| RC-4 | **Window-relative identity:** candidate ids embedded local bar indices, so the same source candidate got different ids in different replay windows and identity checks compared bar numbers across timeframes. | Replay on overlapping windows produced divergent selections; T-S1 windows compared raw `origin_bar` bars across 5m/15m/1h domains |
| RC-5 | **Endpoint-order overclaim:** `endpoint_order_at` extended "high-first/low-first proven" to bars whose close==extreme, and every `close-at-…` slip/failed high/failed low was coded "low-first/high-first proven". | Record classes `proven:high-first:close-at-low` (a **constrained** case) and `proven:low-first:close-at-high` (slips) |
| RC-6 | **Dependency semantics:** genuine dependency recomputations and caller-driven change facts shared one stream, and (earlier) missing task parameters caused divergent recomputations. | Replay payloads must reproduce every declared task parameter (`allow_provisional`, `tie_policy`) or recomputation ≠ original result |

## B. Causal-state integration plan (implemented)

**Real kernel contracts (all in the OPEN kernel `csm.py`, engine-independent):**

1. **Single time axis per task (RC-1):** availability = `available_at(as_of, query_kind)`;
   every task interface carries `decision_time` and the binding interface carries
   `event_time`. T-S1 uses event-time eligibility; T-S2 uses event-time binding with
   decision-time gating (TIE_CROSS_NOT_INITIALIZED); T-S3 entry uses decision-time
   eligibility. One axis is exposed per task; no mixed query in one decision.
2. **One information-time identity per market event (RC-1/RC-3):**
   `InformationKey(key_time, axis, open_at, close_at, source_domain, evidence_class)` —
   reused from **CLOSED 6.2A-0 `information_time.py`** (not duplicated). Same-bar
   class is the kernel's `same_bar_evidence_class()` (open = first trade only,
   close = last touch only) mapped onto the SAME InformationKey semantics:
   `proven:{high-first|low-first}:open-at-…` | `constrained:close-at-…` | `unavailable`.
   The real-run side uses `SharedInformationAxis` (one `BTCUSDT_1m_utc_completion`
   master timeline) which **verifies** every binding's claim with the CLOSED
   `InformationKey` machinery (`axis.available(knowable, event)`).
3. **Reconstructible historical candidate state (RC-3/RC-4):**
   `CandidateLedger` now supports `record_change(..., event_ref=)` (change-fact rows
   with `from_status`, `to_status`, `ref_time`, `time_column`, `event_ref`) and
   `restore_history()` (replays transitions over regenerated versions with new ids
   but preserved `source_fingerprint`). Stable identity = `stable_point_id` /
   `stable_leg_id` (source + source-time based — timeline-independent).
   `reference_state_at(history, event_time)` = the **historical API** for pre-event
   state (per knowledge rule: record the historical break state, not the current
   lifecycle at selection time).
4. **Tasks consume only decision-boundary-available state (RC-3):** T-S2 keys on
   `reference_state_at(..., event_time=decision_time)` with explicit
   `t2_attribution(..., decision_time)`; bindings carry `event_time`; provisional
   bindings state their policy (`provisional:suppress-on-contrast` /
   `provisional:admit-downturn`); breaks record facts at their real times.
5. **Pre/post-event protocol (task order item 5), kernel-native:**
   (a) restore/reconstruct the pre-event state (`restore_history` +
   `reference_state_at`) → (b) evaluate crossings against **pre-event** refs →
   (c) record the binding tagged `first-break` | `later-interaction` →
   (d) apply transitions as change-facts with `event_ref` (no first-break-only
   policy — later factual interactions are preserved) → (e) recompute dependents
   through the existing `propagate()` (typed `"kind": "recomputation"` with
   `source_id`/`policy_version`/`recompute_boundary`/`input_versions`/`result_version`
   /`prev_result_version`/`computed_diffs`, never conflated with `"kind": "change-fact"`)
   → (f) append versions (`n_result_versions`, `record_change`).
   **The original pre-event binding survives later breaks:** binding_kinds are
   derived from pre-event state and are immutable thereafter.
6. **Stable historical facts (RC-3):** `is_future_reference` remains as an audit
   guard; the real run reports `future_reference_violations` verified on the shared
   axis; `snapshot()` reports `n_dependents_without_payload` /
   `incomplete_dependency_coverage` so completeness is a *reported fact*.

## C. Remediating patch summary

| File (path relative to `project/trading_project/`) | Change |
|---|---|
| `src/trading_system/research/contextual_selection/csm.py` | kernel v1: `_endpoint_order` 3-class; `same_bar_evidence_class`; `available_at`; `SharedInformationAxis`; `InformationKey` wiring (`endpoint_order_ref`, `key_time_ref`); `stable_point_id`/`stable_leg_id`; T-S1/T-S2/T-S3 `decision_time` params; `t2_attribution(decision_time)`; `reference_state_at` + `t2_attribution_from_history` + `binding_from_history_event` (new `binding_kinds` field); `record_change(event_ref=)`; `restore_history`; `_recompute` preserves all declared task params (`allow_provisional`, `tie_policy`, `decision_time`); `propagate(..., event_ref=)`; typed revision `kinds`; `snapshot()` coverage fields; `restore_bar_indices` for window replay |
| `src/trading_system/research/contextual_selection/__init__.py` | exports `SharedInformationAxis`, `same_bar_evidence_class`, `stable_point_id`, `stable_leg_id` |
| `docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py` | pre/post-event pipeline (break facts → bindings → recomputations); `binding_kind_counts`; shared-axis self-check; `left_context`/`evaluation_event_window` fields; 3-class ambiguity accounting; `binding_accounting` + `identity_recognition`; replay preserves `allow_provisional`/`tie_policy` |
| `tests/test_contextual_selection_causal_integration.py` | **NEW** adversarial regressions (15) |
| `tests/test_contextual_selection_csm.py` | `_fill_leg_times` strict-fixture helper |
| `tests/test_contextual_selection_final_audit_patch.py` | 4 rewritten semantics + new constrained-evidence test |

**Closed-module compliance:** the six CLOSED modules were **not modified**.
`information_time.py` (CLOSED 6.2A-0) is consumed as-is (import only). No
release-seal modifications; no canonical-branch push; no PR.

## D. Defect-triggering traces (before)

1. **43 later crossings / 37 timestamps (RC-2):** T-S2's broken gate
   (`status == CONFIRMED`) silently excluded every close crossing of an already-broken
   ref. The auditor scanned raw crossings: **43 event-level crossings at 37 timestamps**
   (e.g. `2025-09-24 00:40` re-closing the broken `F:F-K(k=6)|high@2025-09-23T23:10`).
2. **Unbound transition (RC-3):** old break rows `{"status": "broken", "brk_time": t1}`
   carry no event time; `status_at` mislabeled the pre/post-event state.
3. **Same-bar overclaim (RC-5):** `M1 C:F-T(tau=250)|low@127` recorded
   `same_bar_order = "proven:low-first:close-at-high"` — a slip, i.e. close-at-high
   (constrained), never proven-by-open.
4. **Mixed axes (RC-1):** T-S1 compared raw `origin_bar` across 5m/15m/1h frames
   (`raw-order-[5m:227,15m:132,1h:31]` in the record).
5. **Window-relative identity (RC-4):** ids embed local bar indices → replay on a
   shifted window produced different ids for the same source candidate.
6. **Missing replay parameters (RC-6):** a recorded task payload omitting
   `allow_provisional`/`tie_policy`/`decision_time` makes recomputation diverge
   from the original result.

## E. Repaired traces (after) — real Sep-20..27 run

1. **43 later crossings PRESERVED:** `binding_accounting =
   {first-break: 16, later-interaction: 43}` — **43 later-interaction rows at exactly
   37 distinct timestamps** (the auditor's numbers reproduced as factual events,
   not dropped, not first-break-eligible). New-run `t2_exclusions: {}` (no gate
   swallowing).
2. **Every binding state-attributable:** each event row carries `pre_event`,
   `post_event`, `bound`, `breaks`, `binding_kinds`, `discarded_post_event_bindings`
   (empty in this run); all bindings computed on pre-event state.
3. **Same-bar evidence:** 3-class accounting —
   `evidence_class_counts = {unavailable: 1297, constrained: 99, proven: 84}`;
   proven only as `proven:{high-first|low-first}:open-at-…` (84), constrained
   `constrained:close-at-…` (99). The M1/D4/D5 material ambiguity now carries
   time-based identities (`C:F-T(tau=250)|low@2025-09-25T08:00:00` etc.).
4. **Single axis:** `shared axis: BTCUSDT_1m_utc_completion rows=10080`;
   `new_run_future_reference_violations = 0`, `new_run_information_key_axis_verified_bindings = 59`
   (every binding verified by the CLOSED InformationKey availability rule).
5. **Stable identity:** `identity_recognition` (C_FK5, evaluation-window vs
   full-context replay): **78/78 candidates recognized** by `stable_point_id`;
   replay determinism `replay: True` (4/4 selections equal).
6. **Propagation semantics:** `995` revision rows = **59 change-facts** +
   **936 recomputations** (149 with `computed_diffs`, 787 no-op) — streams typed
   and never conflated; every row carries `source_id`, `policy_version`,
   `recompute_boundary`, `input_versions`, `result_version`, `prev_result_version`;
   `n_dependents_without_payload: 0`, `incomplete_dependency_coverage: []`.
7. **Replay preserves declared params:** stored T-S2 payloads now carry
   `allow_provisional` and `tie_policy`; recomputation reproduces the stored
   selection exactly.

## F. Adversarial regression tests (11 failure classes → 16 new tests)

`tests/test_contextual_selection_causal_integration.py` (15) + 1 in
`test_contextual_selection_final_audit_patch.py`:

1. mixed time axes → `test_t1_uses_event_time_for_leg_availability`;
2. unbound transitions → `test_status_at_time_axis_over_domain_bar` /
   `test_restore_history_preserves_pre_event_binding` + history attribution tests;
3. same-bar overclaim → `test_endpoint_order_close_at_is_never_proven` +
   `test_same_bar_close_equals_extreme_is_constrained_not_proven` + 3-class test;
4. broken refs not bindable → `test_t2_binding_stability_under_later_break` +
   later-interaction preservation tests;
5. first-break-only swallowing → `test_later_interactions_preserved_as_factual_events`;
6. window-relative identity → `test_stable_point_id_recognition_across_replay_windows` +
   stable id tests;
7. cross-timeframe bar comparison → `test_t1_uses_event_time…` (time-based windows)
   + `test_shared_axis_refuses_cross_timeline_bar_compare`;
8. pre/post-event conflation → `test_break_fact_is_pre_event_labeled`-class tests
   + `test_discarded_post_event_bindings…`;
9. changed vs recomputed conflation → `test_propagate_separates_change_facts_from_recomputations`;
10. incomplete dependency reconstruction → `test_propagate_reports_incomplete_dependency_coverage`;
11. missing replay parameters → `test_recompute_preserves_declared_task_params` +
    `test_replay_retains_provisional_policy_payload`.

Suite totals: **focused 55/55** (15+12+14+14); **full 1,685/1,685** on
pandas 2.2.3 / numpy 2.2.6.

## G. Old-vs-new comparison (historical — not evidence)

| Metric | Old record (V1, `experiment_record_v1.json`) | New run (V2, `experiment_record_v2.json`) |
|---|---|---|
| Events | 59 | 51 rows / **59 bindings** (16 first-break + 43 later-interaction) |
| Bindings unavailable at event time (reproduced from old payloads) | **36 of 59** | **0** (59/59 axis-verified) |
| Later-boundary-selection retroactive bindings (reproduced) | 59 / 57 events | 0 (binding_kinds from pre-event state) |
| Future-reference violations | ≥36 (audit) | **0** |
| Later close crossings of broken refs | swallowed by the gate (**43 / 37 timestamps** hidden) | **43 / 37 timestamps preserved** as `later-interaction` |
| Same-bar evidence classes | conflated (`close-at-…` marked proven) | 3-class: proven 84 / constrained 99 / unavailable 1,297 |
| T-S2 gate exclusions | 2,832 `X-STATE broken reference not bindable` | 0 |
| Candidate identity across windows | window-relative | **78/78 recognized** (stable ids) |
| Replay determinism | — | True (4/4) |
| Propagation | untyped merge | 59 change-facts + 936 recomputations (typed, versioned) |
| Material ambiguity | 3 events (M1/D4/D5) | same 3 events, now with time-based identities |

The old numbers are preserved in `experiment_record_v1.json` for historical
comparison only (deliverable H's basis), never reused as repaired evidence.

## H. Reproducibility

- `experiment_record_v2.json` + `candidate_ledger_v1.jsonl.gz` under `/home/user/work/csm_run/`
  (regenerable from `experiment_contextual_selection_v2.py`; run under
  `/home/user/work/` to keep the repo clean).
- Inputs pinned by sha256 (recorded in `summary.inputs.files`): `15d26d23…0a0cf4` (Aug),
  `e1d5c8f3…48979` (Sep) at `parshant231234-eng/BTCUSDT-Historical-Data@27c9be70`.
- Semantic rule reused verbatim from closed `information_time.py`:
  `PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED`.
- Left context: 2025-08-01 → (context only). Evaluation event window:
  2025-09-20 00:00 → 2025-09-27 00:00 UTC.

## I. Coverage / missingness

`incomplete_dependency_coverage: []`; `n_dependents_without_payload: 0`;
`snapshot()` exposes both fields. Ambiguity bookkeeping (cumulative-record caveat
included in the record itself): 1,480 records over 304 distinct rep-bar events;
evidence classes recorded per record; 268 genuinely unresolved events.

## J. Acceptance criteria status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | zero future-reference use | PASS (`violations: 0`, 59/59 axis-verified) |
| 2 | zero silent state transitions | PASS (change-facts with `event_ref`, pre/post fields on every event) |
| 3 | zero raw cross-timeframe bar comparison | PASS (time-based windows; SharedInformationAxis refuses cross-timeline bar compare — tested) |
| 4 | stable IDs across replay windows | PASS (78/78 recognized) |
| 5 | broken-reference semantics preserve later factual interactions | PASS (43/37 preserved, first-break-only rejected — tested) |
| 6 | pre/post-event protocol with stable historical facts | PASS (E.2, `reference_state_at`, `restore_history`) |
| 7 | T-S1/T-S2/T-S3/T-S5 time/state integration | PASS (single axis per task, `decision_time` everywhere) |
| 8 | same-bar evidence 3-class + material propagation | PASS (84/99/1,297; M1/D4/D5 material, `unresolved`) |
| 9 | dependency diffs with input IDs / policy / boundary / versions | PASS (E.6) |
| 10 | CLOSED modules untouched | PASS (import-only consumption) |

## K. Selection-quality verdict

**NOT_ESTABLISHED — unchanged.** The same selection question, the same task set,
the same evidence boundary as before. This task repaired causal-state correctness
only. All factual state is now boundary-honest, but that changes what the pipeline
is *allowed* to claim — not whether the selection works. No performance claim is
made from these runs.
