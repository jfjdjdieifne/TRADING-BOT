# CSM V1 — CLOSED FOUNDATION PRESERVATION AND SAFE INTEGRATION (V1)

**Task mode:** TARGETED REPAIR + INTEGRATION (audit REVISE remediation on
`34a2c7a80b4c159e628b5a224168a109222e72fe`)
**Branch:** `arena/a41fd997-trading-bot` (session branch only; no canonical
branch push, no PR)
**Selection quality:** `NOT_ESTABLISHED` (unchanged; EP blocker — no
acceptable-set annotations for this instrument/window)
**Closure:** NOT DECLARED. This report is evidence for an independent audit.

---

## A. Exact inspected HEAD

| item | value |
|---|---|
| target branch | `arena/a41fd997-trading-bot` |
| last audited HEAD (task input, verified) | `34a2c7a80b4c159e628b5a224168a109222e72fe` |
| parent (previous audited) | `312163a2d17d016067f58141767d3520a92aa93c` |
| knowledge pin | `jfjdjdieifne/test @ 6c8bf6fd10e9581322849485d175e825cea5a27f` |
| data pin | `parshant231234-eng/BTCUSDT-Historical-Data @ 27c9be705ac9280248672c895082c057b979ebff` |
| environment | Python 3.11, `pandas==2.2.3`, `numpy==2.2.6` (venv2) |

Workspace note: the shared checkout had been rewound by a sandbox reset to
the pre-session base `c905f2b7`; recovery was performed by `git fetch` +
per-file `git hash-object` verification (9/9 work files matched the remote
blobs) + `git reset --hard FETCH_HEAD` before any new work. This
recovery procedure and its verification are the same as in the previous
task's appendix; no other-session leftovers were committed.

## B. Foundation authority map

For each failing CSM responsibility of audit §F, the classification
(EXISTING_AUTHORITY / MISSING_INTERFACE / CSM_LOCAL_RESPONSIBILITY /
CONTRACT_GAP) and the integration decision:

| failing responsibility | classification | authority / decision |
|---|---|---|
| information-key validity, cross-timeline comparability, as-of visibility | **EXISTING_AUTHORITY** | CLOSED `research/information_time.py` (`InformationKey`, `TimeIndexedTimelineAdapter`, `InformationKeyError`) + CLOSED `market_understanding/availability.py` (`require_visible_at` fail-closed semantics). CSM consumes them ONLY through its minimal adapter `SharedInformationAxis` (`key_for_time` builds CLOSED keys; comparisons are CLOSED `InformationKey` comparisons). No redefinition. |
| shared-axis membership of time-bearing fields (F1) | **EXISTING_AUTHORITY** (key construction) + **CSM_LOCAL_RESPONSIBILITY** (use-site gates) | Key construction is CLOSED. WHERE an unverifiable time may/may not be used is CSM task semantics: eligibility gates fail closed (explicit unavailability/exclusion), structural applications (`add_transition`) reject loudly. |
| same-time event ordering policy (F2) | **CONTRACT_GAP → CSM_LOCAL** | The CLOSED key carries a `deterministic_sequence` slot but defines no event-ordering policy. `EVENT_ORDER_V1` (order by event identity `event_ref`) is the CSM-local filling of that slot — documented, enforced by `status_at` and the application/recording paths. No CLOSED semantics changed. |
| chronological transition handling; replay identity; lifecycle state (F2) | **CSM_LOCAL_RESPONSIBILITY** | Candidate lifecycle is CSM's own state (no CLOSED lifecycle layer exists). |
| effective policy snapshots and versions (F3) | **CSM_LOCAL_RESPONSIBILITY** | No CLOSED policy layer exists; `PolicyRegistry` is CSM-local. |
| dependency recomputation / stale marking (F4) | **CSM_LOCAL_RESPONSIBILITY** | No CLOSED dependency layer exists; `InterpretationLedger.propagate` is CSM-local. |
| candidate/leg/task coverage accounting (F5) | **CSM_LOCAL_RESPONSIBILITY** | `candidate_record` serialization is CSM-local. |
| atomic artifact writing (F6) | **CSM_LOCAL_RESPONSIBILITY** | Smallest necessary OPEN local mechanism: new `contextual_selection/artifacts.py` (temp+fsync+replace, clean-dir refusal). No framework, no CLOSED contact. |
| market-data identity of the inputs | **EXISTING_AUTHORITY** (statement, not verification) | Inputs are labeled `PUBLISHED_OHLC_FACT; SOURCE_ORIGIN_UNVERIFIED` per the source-adapter milestone's identity vocabulary; hashes identify bytes only (see I). |

Explicitly **not** built: no parallel causal-timing implementation, no
second availability engine, no generic causal-state framework, no new
learning model, no new strategy. `available_at` remains the single CSM
availability entry and every key it uses is a CLOSED `InformationKey`.

## C. Confirmed root causes (audit §F, reproduced probes)

| # | audit probe (reproduced) | root cause in `csm.py` / experiment |
|---|---|---|
| F1a | direct T-S2 call **accepted** an off-grid provisional occurrence time | the provisional occurrence gate compared the raw `occurrence_time` (`occ_t <= event_time`) with no key validation |
| F1b | direct T-S3 call **used** off-grid leg endpoints | `sp05_containment` geometry ran on raw endpoint timestamps with no key validation |
| F1c | an off-grid status-transition time was **applied** | `add_transition` accepted any `info_time`; nothing validated it against the shared axis |
| F2a | same-time events A/B reverse first-break vs later-interaction labels with processing order | pre-event state used insertion-ordered `applicable[-1]`; no same-time total order existed |
| F2b | out-of-order transitions made `status_at(35)` return `superseded` despite the chronologically later transition being `broken` | `status_at` took the last transition in **insertion order**, not chronological order |
| F2c | replay without `event_ref` silently relabeled the same event; "the API accepts replay without that identity" | `event_ref` was optional on the time path; identity-less queries were indistinguishable from replays |
| F2d | event-phase-only change yielded empty `computed_changes` | `_diff_results` compared status/selected/survivors/exclusions/binding_kinds/policy — not `event_phase` |
| F3a | mutating a nested value changed an already-recorded policy snapshot without a version change | `PolicyRegistry.register/get/snapshot_of` shared live nested objects (shallow copies) |
| F3b | a T-S3 direction condition disagreed with its stored policy snapshot | the snapshot stored the **registry** value while behavior used the **call** parameter; no agreement check; effective value never recorded |
| F4 | A→B→C with B non-recomputable left B and C at v1; only B identified | `propagate` stopped at the non-recomputable node (`continue`) and never marked downstream dependents |
| F5a | every T-S5 leg row `eligible=false, selected=false`, no exclusion reason | serializer compared **leg ids** with T-S5 survivor ids, which are **point ids** |
| F5b | T-S1 extreme and T-S2 candidates had no ledger rows | coverage rows were emitted only for T-S1-origin points and T-S5 legs |
| F5c | rows lacked the transition sequence / explicit `superseded_by` | `candidate_record` serialized only `status_at_decision`/`status_final` |
| F6a | 4 KiB RLIMIT probe left a truncated gzip beside seeded stale files | direct `gzip.open`/`write_text` writes; no atomicity; no clean-dir refusal |
| F6b | manifest listed `propagation_log_v1.jsonl` but it was never emitted | the file was listed but never written (revisions lived only in the JSON record) |
| F6c | `REPRODUCE.md` command pointed `--old-record` at the output record itself | the reproduction command embedded `out_path` |
| B (report) | report stated a wrong `information_time.py` sha256 (`72b03ca614d0…`) and claimed the 1,365 recomputations "have computed diffs" | report transcription errors (the manifest already held the correct digest; the run's 1,365 diffs are all **empty**) — corrected in section F/G below |

## D. Minimal implemented fixes (OPEN layer only)

Changed files (8 modified + 2 new; ZERO CLOSED-module changes):

1. `src/trading_system/research/contextual_selection/csm.py`
   - **F1**: `SharedInformationAxis.require_key`/`is_on_grid` (CLOSED-key
     construction); T-S2 provisional gate never compares an unverifiable
     occurrence time (X-KNOW exclusion, detail names the axis failure);
     T-S3 `_leg_endpoints_verified` gate (fine → X-GEOM, coarse →
     unresolved IC — containment never computed from unverifiable
     geometry); `add_transition` REQUIRES the validated axis for any
     time-bearing `info_time` and rejects off-grid times (fail closed —
     "never applied"); task gates validate every stored transition time.
   - **F2**: `EVENT_ORDER_V1` module contract (same-time events ordered by
     `event_ref`); `status_at` chronological + EVENT_ORDER_V1 ordering
     (never insertion order) and same-time-later-event exclusion at an
     event's causal coordinate; `task_s2` REQUIRES `event_ref` on the
     time path and rejects out-of-order same-time application;
     `InterpretationLedger.record_event` enforces the same-time recording
     order (optional `event_ref` parameter added); `_diff_results` records
     `event_phase` moves.
   - **F3**: `PolicyRegistry` deep-copies values at `register`, `get`,
     `snapshot_of`, `items`; T-S3 records the EFFECTIVE
     `continuation_condition` in the snapshot (`value`) together with the
     registered form (`registered_value`) and rejects a structured
     registry/call contradiction (same doctrine as the existing T-S2
     tie-policy contradiction).
   - **F4**: `propagate` marks a non-recomputable/failed node `stale`
     (with `stale_reason`) and cascades `stale-descendant` entries to every
     transitive dependent (blocked against a stale upstream); `snapshot()`
     reports `stale_results`/`n_stale_results`.
   - **F5**: `candidate_record` adds `initial_status`, `superseded_by`,
     `status_transitions[]` (info_bar/status/info_time/by/note/event_ref)
     and `task_detail`.
   - generators `fk_turning_points`/`ft_turning_points`, `restore_history`,
     `_mark_broken`, `propagate` accept/forward `axis` so every
     time-bearing transition is validated at application.
2. `src/trading_system/research/contextual_selection/artifacts.py` (NEW,
   smallest OPEN local mechanism): `require_clean_out_dir`,
   `atomic_write_text/json/jsonl/jsonl_gzip`, `write_run_artifacts`
   (stage-all-then-commit, residue cleanup on failure, per-artifact sha256).
3. `docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py`
   - **F5**: per-task rows — `T-S1_origin` and `T-S1_extreme` for every
     point, `T-S2` rows per event-ref (with `binding_kind`), and
     `T-S5_support` leg rows with LEG-level classification
     (`evaluated_support` + `support_of_falsifier` in `task_detail`);
     leg ids are never compared against point survivor ids.
   - **F6**: refuses a non-clean output directory; writes all five
     artifacts via `write_run_artifacts` (atomic); EMITS
     `propagation_log_v1.jsonl` (the ledger's change-fact /
     recomputation / stale rows — the manifest list is now truthful);
     `REPRODUCE.md`'s `--old-record` names the DISTINCT tracked historical
     record (a comparison input), never the output.
4. Tests: 5 existing CSM test files updated to the repaired contract
   (axis/event_ref on time-bearing calls; the test-8 diff scenario rebuilt
   as a GENUINE world change); NEW
   `tests/test_contextual_selection_integration_repairs.py` — 14 behavioral
   regressions (section E).

No release seal, no historical record (`experiment_record_v1/v2.json`
tracked copies untouched), no CLOSED module, and no canonical branch was
modified.

## E. Regression tests (behavioral, one per reproduced probe)

`tests/test_contextual_selection_integration_repairs.py` (14 tests — each
asserts actual behavior, never a returned status name alone):

| test | probe covered | asserts |
|---|---|---|
| `test_f1_t2_off_grid_provisional_occurrence_never_eligible` | F1a | provisional excluded X-KNOW, never eligible; on-grid control eligible |
| `test_f1_t3_off_grid_leg_endpoints_never_used_for_geometry` | F1b | fine → X-GEOM (containment never computed); coarse → unresolved |
| `test_f1_off_grid_status_transition_time_never_applied` | F1c | rejected with and without axis; `status_transitions` stays empty |
| `test_f2_same_time_event_labels_are_order_independent` | F2a | canonical labels (first-break / later-interaction); reversed application raises `EVENT_ORDER_V1`; reconstruction canonical both ways |
| `test_f2_status_at_chronological_not_insertion_order` | F2b | out-of-order insertion reproduces the audit's `status_at(35)` case; chronological result wins at every boundary |
| `test_f2_replay_identity_is_mandatory_and_stable` | F2c | identity-less time-path call raises; identity-bearing replay stable (`first-break`) |
| `test_f2_event_phase_only_change_is_a_computed_change` | F2d | phase-only move appears in `computed_changes` with `n_changed ≥ 1` |
| `test_f3_policy_snapshots_immutable_to_nested_mutation` | F3a | nested mutation of returned registry/snapshot objects changes nothing |
| `test_f3_t3_effective_policy_contradiction_and_snapshot` | F3b | structured contradiction raises; snapshot carries effective + registered forms |
| `test_f4_unrecomputable_intermediate_marks_descendants_stale` | F4 | B stale + C `stale-descendant` naming B; `n_stale_results == 2` |
| `test_f5_candidate_record_lifecycle_and_supersession` | F5c | transition sequence + `superseded_by` + `task_detail` per row |
| `test_f6_atomic_write_failure_leaves_no_artifacts` | F6a | injected failure leaves no target and no temp residue |
| `test_f6_refuses_stale_output_dir_and_commits_cleanly` | F6a | stale-dir refusal (seeded file untouched); clean commit; gzip complete |
| `test_complete_path_future_data_invariance` | mission | observations→candidates→history→selection→binding→dependency→persisted rows; FUTURE bars do not change earlier outputs |

Updated-in-contract legacy expectations (same files as before; semantics
preserved except where the audit named the old behavior as the defect):
time-bearing `add_transition` now requires the axis; time-path `task_s2`
requires `event_ref`; the former identity-less "later-state view" is now
expressed by a distinct identity (`event_ref="E21"`), and the
identity-less call is rejected (audit F2c — the API must not accept a
replay without identity).

**Suites** (pandas 2.2.3 / numpy 2.2.6, CWD `project/trading_project`):

| suite | count | result |
|---|---|---|
| focused CSM set (5 legacy files) | 69 | ALL PASS |
| new integration regressions | 14 | ALL PASS |
| **full suite** | **1,713 collected (1,699 prior + 14 new)** | **PYTEST_EXIT=0 — ALL PASS** (warnings only) |

Exact commands in section I.

## F. Real-market reproduction — see G for the fresh-run numbers

Pinned inputs (identical bytes to the audit's run):

| file | sha256 | rows |
|---|---|---|
| BTCUSDT_1m_2025-08.csv | `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` | 44,640 (+header) |
| BTCUSDT_1m_2025-09.csv | `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` | 43,200 (+header) |

Input identity statement (unchanged): `PUBLISHED_OHLC_FACT;
SOURCE_ORIGIN_UNVERIFIED` — hashes identify the CSV bytes used; they do
NOT establish exchange authenticity or market truth.

Window (unchanged): context 2025-08-01 .. 2025-09-20 UTC; evaluation/event
window 2025-09-20 .. 2025-09-27 UTC. Bar completions 1m=83,520 /
5m=16,704 / 1h=1,392; 9 decision boundaries (D1, D2, D3, B0, B1, M1, B2,
D4, D5).

Source identities at run (`experiment_manifest_v1.json`):

| source | sha256 |
|---|---|
| `information_time.py` (CLOSED, byte-identical to 34a2c7a) | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` |
| `csm.py` | `6db88bca1f82eafde5d8f4ff8529815895f3c2a79e1fc609706841d19fda05be` |
| `experiment_contextual_selection_v2.py` | `869872fb417d69d2726e0ab390d4e752dcae3d185e381a89548d5d3842c4e3b7` |
| `artifacts.py` (new) | `ce088aaeb06d8444a431a7ae2bfa15f3864aac51e320b5b24f892c617a82e239` |

> **Report-checksum correction (audit §B):** the previous consolidation
> report transcribed the `information_time.py` digest as
> `72b03ca614d0f9d763231f9d82799e3ca22b6f7364a7e3051e03af9a37d74ace`.
> That was a report typo only. The correct digest (manifest, this report,
> and `sha256sum`) is
> `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`.
> The module itself is byte-identical between `312163a` and `34a2c7a`
> and unchanged by this build (see E: zero CLOSED diff).

## G. Fresh-run results (authoritative artifacts — filled from the run)

_Artifacts (outside Git): `/home/user/work/csm_run_v2/` —
`experiment_record_v2.json`, `candidate_ledger_v1.jsonl.gz`,
`propagation_log_v1.jsonl`, `experiment_manifest_v1.json`, `REPRODUCE.md`;
live log `/home/user/work/logs/csm_full_run_v2.log`. Written atomically
into a clean directory (`EXPERIMENT_EXIT=0`); per-artifact sha256 below._

| metric | value |
|---|---|
| self-check: axis-verified bindings / future-reference violations | **96 / 96** and **0** (zero tolerated) |
| boundaries / event records / bindings | 9 / 70 / 96 = **19 first-break + 77 later-interaction** (audit-matching) |
| candidate ledger rows — total | **480,241** |
| — composition | `T-S1_origin` 205,101 + `T-S1_extreme` 205,101 + `T-S5_support` 69,720 + `T-S2` 319 (with `binding_kind` + `event_ref` per row) |
| — rows carrying transition-sequence evidence | **410,521** (85%) |
| — rows carrying explicit `superseded_by` | **264,854** |
| ledger results | 1,570 = 1,520 justified / 45 unresolved (AI 40, IC 10) / 5 falsified / **0 stale** |
| revisions | 1,461 = 96 change-facts + 1,365 recomputations — **all 1,365 computed diffs EMPTY** (honest zero; the previous report's "have computed diffs" claim was wrong) + 0 stale-descendant rows (nothing unrecomputable occurred) |
| incomplete dependency coverage / cycles | **0 / 0** |
| historical transitions re-applied (cumulative) | **536** (B2 restore included; replay B2_post6 C_FK5 stored==recomputed==None) |
| identity recognition (eval-window → full context) | **653 / 653** |
| replay checks | **4 / 4 equal** (B1 C_FK5, B1 F_FK6, B2 C_FK5, B2 F_FK6) |
| retention | prefix-only ids **0 × 5 reps**; superseded retained 481 / 307 / 732 / 5,594 / 8,462 |
| ambiguity accounting | 25,087 records / 2,927 distinct rep-bar events / 20,989 genuinely unresolved records / 2,456 unresolved events / 1,227 endpoint-resolved (audit-matching) |
| SP-16 representation dependence | disagree × 9 (reported, never merged) |
| exclusion histogram | X-SUPER 1,561,572 / X-POL 852,392 / X-STATE 1,188 |

Artifact sha256 (from the run's atomic commit):

| artifact | sha256 |
|---|---|
| `experiment_record_v2.json` | `217db2a8b1ff35c403c05fc5031b77942505e602c9cf5aff4503eaf9c4d0004b` |
| `candidate_ledger_v1.jsonl.gz` | `184d3d88c03ca6e9ac75ab645028ee0b8b7e09df040d6332d34237af0d18fec2` |
| `propagation_log_v1.jsonl` (now emitted) | `dbf772c536152172bd82c5b76df072c5f8fd6c8af56e77ff4dad35038b2af01b` |
| `experiment_manifest_v1.json` | `cd77e3a63a360c779e58f73e0d6493553460ddecf95d7dbb40f80a505eb8e831` |
| `REPRODUCE.md` | `e168fef2dbd16264511f6c4f6b85f5f5d8cfb53543974d6351b16469286bf001` |

## H. Candidate / dependency coverage

- **Per-task rows exist for every task variant the experiment runs**
  (audit F5b closed): the two T-S1 variants double the previous point
  coverage (205,101 each); the 319 T-S2 rows cover every candidate
  evaluated at every recorded event (70 events × its reference set) with
  its pre-event `binding_kind`; the 69,720 leg rows are classified at the
  LEG level (`evaluated_support` + `support_of_falsifier` in
  `task_detail`) — a leg id is never compared against T-S5 point survivor
  ids (audit F5a closed).
- **Lifecycle evidence is per-row, not aggregate**: 410,521 rows carry
  their full status-transition sequence (times + authorizing `event_ref`
  where applicable), and 264,854 rows carry the explicit `superseded_by`
  relation. The aggregate `historical_transitions_reapplied = 536` is the
  cumulative re-application count across regenerations (not distinct
  transitions — audit §D note preserved).
- **Dependency updates**: 96 change-facts (event-authorized, with
  `event_ref`) drive 1,365 recomputations; every recomputation's computed
  diff is EMPTY (no result materially changed in this run — reported
  honestly, never inflated). The run registers **zero result-dependency
  edges** (task inputs here are candidate ids, not result uids) — so
  transitive recomputation and stale-descendant marking are demonstrated
  by the behavioral tests (`test_f4_unrecomputable_intermediate_marks_descendants_stale`
  exercises A→B→C with a non-recomputable intermediate → C marked
  `stale-descendant`), NOT claimed as run evidence (limitation J.5).
- `incomplete_dependency_coverage: []`, `n_stale_results: 0`,
  `dependency_cycles_detected: 0` — in this run every registered result
  was recomputable and nothing went stale; the accounting paths themselves
  are regression-tested.

## I. Exact commands

```bash
# environment (pinned)
python3 -m venv /home/user/work/venv2
/home/user/work/venv2/bin/pip install pandas==2.2.3 numpy==2.2.6 pytest

# suites (CWD = project/trading_project)
PYTHONPATH=src /home/user/work/venv2/bin/python -m pytest \
  tests/test_contextual_selection_csm.py \
  tests/test_contextual_selection_audit_regressions.py \
  tests/test_contextual_selection_final_audit_patch.py \
  tests/test_contextual_selection_causal_integration.py \
  tests/test_contextual_selection_end_to_end.py \
  tests/test_contextual_selection_integration_repairs.py -q
PYTHONPATH=src /home/user/work/venv2/bin/python -m pytest tests/ -q   # full

# real-market reproduction (clean output directory; atomic artifacts)
PYTHONPATH=src /home/user/work/venv2/bin/python \
  docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --out-dir /home/user/work/csm_run_v2 \
  --months 2025-08,2025-09 --start 2025-08-01 --end 2025-09-28 \
  --old-record docs/research/contextual_selection_v1/experiment_record_v2.json \
  --src src
```

## J. Remaining limitations (and audit requirements for the next review)

1. Selection quality remains `NOT_ESTABLISHED` (EP). Nothing in this build
   measures selection quality; no acceptable-set annotations exist for this
   instrument/window. No trading recommendation or strategy conclusion
   follows from any result here.
2. The 16 old bound candidate ids (pre-stable-id scheme) remain
   **unverifiable, not cleared** (audit §H preserved).
3. `EVENT_ORDER_V1` is a CSM-local policy filling the CLOSED
   `deterministic_sequence` slot. If the owner defines an authoritative
   event-ordering policy in the CLOSED layer, CSM must adopt it verbatim
   (CONTRACT_GAP acknowledged; not invented as authority here).
4. Stale-marking (F4) blocks descendants against a stale upstream; it does
   not magically make an unrecomputable intermediate computable. Coverage
   `incomplete_dependency_coverage` still counts such nodes (honest).
5. The market run registers zero result-dependency edges (task results in
   this experiment consume candidate ids, not other results' uids) —
   transitive recomputation is demonstrated by the behavioral tests
   (A→B→C both fully-recomputable and stale-cascade cases), not by this
   run. Reported as such; not claimed as run evidence.
6. Full-experiment wall-clock performance is not claimed (audit §G
   precedent). The parent-vs-target microbenchmarks of the audit are noted
   as narrow synthetic timings only.
7. Time-bearing API inputs now REJECT unverifiable application (transition
   times) and fail closed on unverifiable eligibility (occurrence/endpoint
   times → exclusion). This is a contract change on the OPEN research API;
   the 14 audit-confirmed behaviors whose surfaces touched these paths were
   updated to supply the required axis/identity — their assertions were
   preserved except where the audit named the old behavior as the defect
   (identity-less replay). This is called out for the auditor's attention.

### Requirements for the next independent audit

1. Verify zero CLOSED-module / seal / historical-record changes
   (`git diff 34a2c7a -- src/trading_system/research/information_time.py
   src/trading_system/market_understanding docs/releases MANIFEST.sha256`
   is empty).
2. Replay every §F probe as a public-path call and confirm the §E
   behaviors (not just the test names).
3. Re-run both suites (expected 1,713 / exit 0) and the reproduction
   command into a clean directory; compare artifact sha256 values with §G.
4. Inspect the candidate ledger composition (task_id distribution, leg
   eligibility reasons, transition sequences) against §H.
5. Attempt the 4 KiB RLIMIT / kill-mid-write probes again: expect no
   truncated artifact and no stale mixture.
6. Probe same-time events and out-of-order transitions afresh (EVENT_ORDER_V1).
7. Confirm `--old-record` in `REPRODUCE.md` names a distinct input file.

---

_Not closed. Evidence only. Selection quality NOT_ESTABLISHED. No
recommendations, no execution, no learning model, no new strategy._
