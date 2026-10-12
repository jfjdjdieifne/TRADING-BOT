# Contextual Selection V1 — Final Targeted Audit Patch (four reproducible defects)

**Project:** trading_project — contextual selection model (CSM V1)
**Mode:** PATCH ONLY + REGRESSION TESTING (no new models, strategies, rules, or
swing policies; no invented scores or confidence values)
**Branch:** `arena/a41fd997-trading-bot`
**Audited baseline (parent of this patch):** `e90a62fda27c3f24f5c2706e611d77a953921cee`
**Certified environment:** Python 3.11, **pandas 2.2.3**, **numpy 2.2.6**
(rebuilt venv; imports and all runs execute from this environment)
**Data (re-downloaded, hashes verified):** `BTCUSDT_1m_2025-08.csv`
(`15d26d23…`), `BTCUSDT_1m_2025-09.csv` (`e1d5c8f3…`), mirror of source commit
`27c9be70`.
**Selection quality: NOT_ESTABLISHED** (unchanged). This patch fixes factual
operations only; no profitability test is required or performed.

This document records deliverables A–H of the final targeted audit patch: the
four reproducible correctness defects identified by the independent re-audit of
`e90a62f`, their repairs, regression evidence, the repaired reproduction run,
and the corrected ambiguity accounting.

---

## A. Inspected HEAD and evidence base

| Item | Value |
|---|---|
| HEAD inspected | `e90a62fda27c3f24f5c2706e611d77a953921cee` (8 files; parent `4e04198`) |
| HEAD source identity at run | `csm_py_sha256=29eca055…`, `experiment_py_sha256=fda039bd…` (record v2 `summary.source_version`) |
| Full suite at baseline | 1,656 passed (pandas 2.2.3 / numpy 2.2.6) |
| Re-audit findings fixed here | (1) F-K tail knowability + T-S2 status; (2) T-S3 cross-timeframe containment; (3) T-S5 origin direction; (4) same-bar ambiguity propagation |

The re-audit's four confirmed defects are treated as the complete scope. Its
independent verifications (record provenance, 36/59 + 59/57 reproduction from
the old implementation, ledger counts, CSV hashes, byte-level gzip caveat) are
accepted and not re-performed.

---

## B. The four repairs

### B1 — F-K tail knowability and T-S2 status gating

**Root cause.** `fk_turning_points` clamped `knowable_time` to
`times[min(i+k, n-1)]`. For a truncated prefix whose confirmation bar lies
beyond the data, the provisional tail candidate therefore *claimed the last
observed timestamp* as its knowable time. `available_at(last_bar)` returned
True on the truncated run and False on the full-history run — and T-S2, which
checks availability but never checked candidate status, bound the provisional
tail candidate.

**Patch (csm.py).**
1. F-K tail: `know_time = times[i+k] if i+k < n else None`. A missing
   `knowable_time` under a time query is now **False** in `available_at`
   (previously: raised). No future-availability claim is ever derived from a
   truncated prefix; the conservative answer is "not available".
2. F-K same-bar pairs record factual OHLC-endpoint order evidence on both
   candidates (see B4).
3. `task_s2_event_binding(..., allow_provisional: bool = False)` now enforces
   the task contract's status gate **before** availability:
   - `superseded` → excluded `X-SUPER` (R:SP-13/SWS-04c);
   - `broken` → excluded `X-STATE` (R:SP-20 — a falsified reference cannot
     bind; the successor is the active reference);
   - `provisional` → excluded `X-STATE` (R:SP-01/SWS-04a) **unless** the
     caller explicitly passes `allow_provisional=True`, in which case
     provisional use is gated on *occurrence visibility*
     (`occurrence_time <= event_time`) — never on the projected confirmation
     time. The experiment declares this contract explicitly
     (`summary.t2_provisional_contract`).

**Equivalence evidence (tests).**
`tests/test_contextual_selection_final_audit_patch.py`:
- `test_tail_knowable_time_never_claims_last_bar` — the auditor's truncated
  k=2 probe: `knowable_time is None` on the truncated prefix, bar-5 timestamp
  on the full history; both runs answer **not available** at bar 4; at every
  query time, truncated-implies-full (no over-claim).
- `test_tail_prefix_full_t2_event_binding_equivalence` — T-S2 binding on the
  truncated candidate equals the full-history candidate at bar 4 (default
  contract: empty, X-STATE exclusion on both; explicit provisional contract:
  identical occurrence-gated binding on both).
- `test_t2_status_gating_provisional_superseded_broken` — provisional →
  `X-STATE`, superseded → `X-SUPER`, broken → `X-STATE`, confirmed → binds;
  `allow_provisional=True` opens the provisional path only.

### B2 — T-S3/SP-05 cross-timeframe containment

**Root cause.** `sp05_containment` and `task_s3_entry_leg` compared raw t0/t1
bar indices. Indices from different timeframe domains are incomparable: an
adversarial fine leg inside the coarse leg's *time* span returned "disjoint"
when its raw indices were larger, and a leg outside the coarse time span
returned "contained" when its indices happened to fall inside. T-S3 also had
no decision-time availability argument.

**Patch (csm.py).**
1. `sp05_containment`: when both legs carry verified `t0_time/t1_time`, time
   containment is evaluated **on timestamps** (sorted endpoint pairs). A mixed
   pair (times on only one leg) raises `ValueError` — raw cross-domain indices
   are never compared. Index comparison remains only inside a single declared
   domain (no times at all).
2. `task_s3_entry_leg(..., decision_time=None)`: availability of **both** the
   coarse leg and every fine leg is evaluated on the shared information axis
   (`available_at(..., as_of_bar=decision_bar, as_of_time=decision_time)`); a
   coarse leg not knowable at the decision time is an early `unresolved`
   (REASON_IC); fine legs not knowable at the decision time are excluded
   `X-KNOW`. SP-06 dominance recomputes `knowable` with the same axis.

**Evidence (tests).** `test_t3_containment_uses_timestamps_not_indices`
(fine-inside with misleading indices → contained; fine-outside → disjoint;
overlapping-not-contained → escaping), `test_t3_decision_time_availability_check`
(late fine leg → `X-KNOW`; coarse not knowable at decision → unresolved),
`test_t3_mixed_time_index_pair_refused` (mixed pair raises).

### B3 — T-S5 origin-of-last-confirmed-leg direction validation

**Root cause.** The T-S5 `origin-of-last-confirmed-leg` branch ignored the
claim's `direction` entirely: with a DOWN last leg, claims `up`, `down`, and
missing all produced the same justified origin.

**Patch (csm.py).** The claim's declared direction (movement representation) is
validated against the supporting leg:
- missing/unsupported → explicit `unresolved` **REASON_IC** (evidence needed:
  supported direction from the interpretation's movement representation);
- opposite to the supporting leg → explicit `unresolved` **REASON_AI**
  (evidence needed: re-read the interpretation; the leg's direction is carried
  on the result);
- match → the previous justified path (unchanged).
The falsified-structure check (broken `L_b`) remains **first**. The
low/high-of-current-leg roles already validated direction (D6) and are
unchanged; `last-confirmed-extreme` keeps its side-based contract.

**Evidence (tests).** `test_s5_origin_direction_validated` (match → justified;
missing → IC; opposite → AI; the two invalid cases never return the justified
result), `test_s5_all_roles_direction_behavior` (low-of-current-leg selects by
direction; invalid/missing → IC; high-of validates; last-confirmed-extreme
unchanged).

### B4 — Same-bar ambiguity propagation

**Root cause.** A selected candidate could carry `same_bar_order="unresolved"`
(intrabar high/low order unknowable from OHLC) while the task result stayed
`justified` — the auditor's M1/D4/D5 pattern (e.g. M1 selects `low@1327` as
the origin of leg 1327–1329 with open/close interior). Dependents received no
notice. Equally, an ambiguity on a *non-selected* candidate must not downgrade
an unrelated choice, and an order *determined by OHLC endpoints* is factual
and must not downgrade anything.

**Patch (csm.py).**
1. `PointCandidate.same_bar_evidence: Optional[str]` — factual endpoint-order
   evidence ("high-first"/"low-first"), computed by `_endpoint_order`
   (CLASS_F endpoint rules: open-at-high ⇒ high-first, open-at-low ⇒
   low-first, close-at-high ⇒ low-first, close-at-low ⇒ high-first; interior
   endpoints ⇒ None). F-K records it on same-bar pairs; F-T records it on the
   ambiguous extreme-vs-reversal state.
2. `material_same_bar_ambiguity(c)` = `same_bar_order == "unresolved"` **and**
   `same_bar_evidence is None`.
3. `task_s1_structural_reference` (both selection branches: origin and
   last-confirmed-extreme) and `task_s5_falsifier` inspect the
   **selected/resolved** candidate(s) only:
   - material ambiguity → task result `unresolved` **REASON_AI**, candidate
     kept as survivor, `dependents_blocked` populated, note
     `"same-bar order unresolved; surfaced (AI)"` (needs tick data (MO) or a
     declared ordering policy);
   - endpoint-determined order → result stays justified, note
     `"same-bar order determined by OHLC endpoints (…); not downgraded"`;
   - ambiguity on non-selected candidates never downgrades.

**Evidence (tests).**
`test_same_bar_ambiguity_surfaces_on_t1_selection` (M1/D4/D5-shaped fixture:
low origin of an up leg with unresolved order → `unresolved` AI, survivors
preserved, T-S5/T-S4 dependents blocked),
`test_same_bar_endpoint_evidence_does_not_downgrade`,
`test_same_bar_ambiguity_on_unselected_candidate_is_unrelated`,
`test_same_bar_ambiguity_surfaces_on_t5_falsifier`,
`test_endpoint_order_evidence_from_generator` (open==high bar → "high-first"
on both same-bar candidates; interior endpoints → None).

On real data the repaired run surfaces exactly the auditor's three boundaries
(M1, D4, D5) as material-ambiguity downgrades — see F.

---

## C. Files changed

| File | Change |
|---|---|
| `src/trading_system/research/contextual_selection/csm.py` | B1–B4: tail knowability, `available_at` missing-time ⇒ False, `_endpoint_order`, `material_same_bar_ambiguity`, `same_bar_evidence` field, `sp05_containment` timestamps + mixed-pair refusal, `task_s3_entry_leg(decision_time=…)`, `task_s2_event_binding(allow_provisional=…)` status gate, T-S5 origin direction validation, ambiguity propagation in T-S1/T-S5, `candidate_record` += `level`, `same_bar_evidence`, leg fields (`leg_direction/leg_depth/leg_t0_time/leg_t1_time`), ambiguity entries carry `rep` + `endpoint_evidence` |
| `src/trading_system/research/contextual_selection/__init__.py` | export `material_same_bar_ambiguity` |
| `tests/test_contextual_selection_final_audit_patch.py` | **new** — 13 regression tests (B1×3, B2×3, B3×2, B4×4, endpoint-order×1) |
| `docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py` | item-5 accounting (`propagation_summary`, `ambiguity_accounting` with recurrence distribution and material-affect scan), `t2_exclusion_histogram`, explicit `allow_provisional=True` contract + `summary.t2_provisional_contract` |
| `docs/research/contextual_selection_v1/experiment_record_v2.json` | repaired rerun record (old record retained as `experiment_record_v1.json`) |
| `docs/research/contextual_selection_v1/candidate_ledger_v1.jsonl.gz` | repaired rerun ledger (9,787 rows; now includes `level` + `same_bar_evidence` + leg fields) |
| `docs/research/contextual_selection_v1/AUDIT_FINAL_PATCH_V1.md` | this report |

---

## D. Regression tests and results

Environment: pandas 2.2.3, numpy 2.2.6, pytest (venv2), CWD
`project/trading_project`, `PYTHONPATH=src`.

| Scope | Result |
|---|---|
| `tests/test_contextual_selection_final_audit_patch.py` (new, per-defect) | **13/13 passed** |
| Focused (golden 12 + audit regressions 14 + final patch 13) | **39/39 passed** |
| Full suite (`tests/`, 84 files) | **1,669 passed** (1,656 baseline + 13 new) |

Per-defect mapping:
- B1: `test_tail_knowable_time_never_claims_last_bar`,
  `test_tail_prefix_full_t2_event_binding_equivalence`,
  `test_t2_status_gating_provisional_superseded_broken`
- B2: `test_t3_containment_uses_timestamps_not_indices`,
  `test_t3_decision_time_availability_check`,
  `test_t3_mixed_time_index_pair_refused`
- B3: `test_s5_origin_direction_validated`,
  `test_s5_all_roles_direction_behavior`
- B4: `test_same_bar_ambiguity_surfaces_on_t1_selection`,
  `test_same_bar_endpoint_evidence_does_not_downgrade`,
  `test_same_bar_ambiguity_on_unselected_candidate_is_unrelated`,
  `test_same_bar_ambiguity_surfaces_on_t5_falsifier`,
  `test_endpoint_order_evidence_from_generator`

---

## E. Reproduction with the repaired code (item 6)

Command (same window/parameters as the audited run; v1 record untouched):

```
PYTHONPATH=project/trading_project/src python \
  docs/research/contextual_selection_v1/experiment_contextual_selection_v2.py \
  --mirror-dir <mirror> --months "2025-08,2025-09" \
  --start "2025-09-20 00:00:00" --end "2025-09-27 00:00:00" \
  --old-record docs/research/contextual_selection_v1/experiment_record_v1.json \
  --out-dir <out>
```

Record/ledger written to `docs/research/contextual_selection_v1/
{experiment_record_v2.json, candidate_ledger_v1.jsonl.gz}`.
`summary.source_version`: `git_head_at_run=e90a62fda27c…` (parent of this
patch), `csm_py_sha256=9a808487bc19…` (repaired csm).

**Self-check:** `comparison_v1_vs_v2.new_run_future_reference_violations =
0` — no event in the repaired run binds a reference whose knowable time is
after the event. Old-implementation reproduction (from the v1 record):
`unavailable_at_event_time_bindings = 36`,
`later_boundary_selection_retroactive_bindings = 59` across `57` events —
matching the audit report (36 of 59). Replay recomputation checks: all equal.

**Event count change (documented contract consequence).** The audited run
recorded 74 binding events / 106 bound refs; the repaired run records **14
events**. Cause, measured by `summary.t2_exclusion_histogram`: **2,832
exclusions of `X-STATE | broken reference not bindable`**. The old T-S2 bound
references that had already been falsified (broken) at the event time — i.e.
repeat crossings of a violated level counted as "the event binds the
reference". Under the declared contract (SP-20/D5: a broken reference cannot
serve; its successor is the active reference) those rows no longer bind; the
broken state remains recorded as an append-only change fact and still drives
propagation. Provisional references remain bindable under the explicit
occurrence-visible contract (`allow_provisional=True`, documented in
`summary.t2_provisional_contract`). This is a semantics change of the event
record, not a data change; old rows are preserved in
`experiment_record_v1.json` and are never used as corrected evidence.

**Selection stability.** T-S1 origin/extreme selections across the nine
boundaries are identical to the audited run except the three
ambiguity-downgraded cases in F (which now surface `unresolved` AI instead of
`justified`). SP-16: 1 agree / 8 disagree (unchanged; a declared limitation).

---

## F. Corrected ambiguity accounting and propagation language (item 5)

Computed by the repaired experiment (`record.ambiguity_accounting`,
`record.propagation_summary`). Semantics note (standing): rows are **cumulative
per-boundary records of one replay stream** — repeated observations of the
same bar event recur across boundary runs and are **never** described as
independent market events.

**Propagation (1 run, boundary-record scale).**

| Measure | Count |
|---|---|
| total rows | 267 |
| change-facts (append-only state changes) | **16** |
| recomputations | **251** (124 with computed diffs, 127 no-ops) |

(At the audited run these were 1,659 = 106 change-facts + 1,553
recomputations = 250 with computed diffs + 1,303 no-ops. The change of scale
follows the event-record semantics change of E.)

**Same-bar ambiguity (cumulative records vs distinct events).**

| Measure | Count |
|---|---|
| total cumulative records | **1,480** (F-T 1,472; F-K 8) |
| distinct rep-bar events | **304** |
| recurrence distribution (records per event) | 1×33, 2×44, 3×28, 4×12, 5×23, 6×43, 7×114, 8×7 (max 8) |
| records resolved by OHLC endpoints | **183** (high-first 89, low-first 94) |
| genuinely unresolved records | **1,297** |
| genuinely unresolved distinct events | **268** |
| material ambiguities affecting actual selections | **3** (below) |

**Material effect on actual selections** (`ambiguity_accounting.affecting_actual_selections`,
`material: true`):

| Boundary | Rep | Task | Candidate | Task result |
|---|---|---|---|---|
| M1_2025-09-25_noon | C_FT250 | T-S1_origin | `C:F-T(tau=250)\|low@127` | `unresolved` (AI) |
| D4_2025-09-26 | C_FT250 | T-S1_origin | `C:F-T(tau=250)\|low@151` | `unresolved` (AI) |
| D5_2025-09-26_end | C_FT250 | T-S1_origin | `C:F-T(tau=250)\|high@162` | `unresolved` (AI) |

These are exactly the auditor's M1/D4/D5 pattern (e.g. M1: a same-bar
low-origin of a 2-bar up leg with open/close interior): previously `justified`
with `same_bar_order="unresolved"`; now surfaced (REASON_AI, survivors kept,
T-S5/T-S4 dependents blocked). Endpoint-resolved selections (evidence present)
stay justified and are annotated; non-selected ambiguity never downgrades
any task. Unresolved-code histogram of the run: `IC 55, MP 7, AI 16` (the 16
AI = 3 T-S1 origin + 13 T-S5/other recomputed dependents carrying the
surfaced state through W8-style recomputation).

---

## G. Remaining limitations

1. **OHLC ordering is fundamentally underdetermined.** 268 distinct bar events
   remain genuinely unresolved (1,297 cumulative records); resolving them
   needs tick data (MO) or a declared ordering policy. Endpoint rules resolve
   only 183 records; no policy is invented here (SWS-05 open).
2. **Selection quality: NOT_ESTABLISHED.** Blocked on EP acceptable-set
   annotations; nothing in this patch measures or claims selection quality.
3. **SP-16 cross-timeframe agreement remains 1 agree / 8 disagree** —
   representation sensitivity is a declared limitation, unchanged.
4. **Byte-level gzip reproducibility of the ledger is NOT established**
   (JSON content reproducible; gzip bytes differ across runs).
5. **Event-record semantics changed** (E): 74 → 14 events under the
   broken-reference gate. If the owner's contract intends that falsified
   levels may re-bind on later crossings, the gate is the single switch
   (`task_s2_event_binding` status gate); both behaviors are one parameter
   apart, and the old record is preserved for comparison.
6. **Tie policies remain experiment facts** (TIE-FT-EQ-FIRST-V1,
   TIE-CROSS-EQUAL-UNBOUND-V1); F-T FIRST-vs-LAST sensitivity is policy
   sensitivity, not evidence of quality (unchanged: fine 5,903 vs 5,763 with
   5,402 shared; D4 flips under the policy).
7. **Ledger coverage improved but not complete:** rows now carry `level`,
   `same_bar_evidence`, and leg fields (`leg_direction/leg_depth/
   leg_t0_time/leg_t1_time`), fixing the flagged omissions; full per-boundary
   excluded-expansion remains capped in the record diffs (first 20) as a size
   measure.

## H. Independent re-audit instructions

1. **Environment:** Python 3.11, `pandas==2.2.3`, `numpy==2.2.6`, pytest;
   CWD `project/trading_project`; `PYTHONPATH=src`.
2. **Identity:** `git rev-parse HEAD` on `arena/a41fd997-trading-bot`; the
   patch's parent must be `e90a62fda27c3f24f5c2706e611d77a953921cee`.
   `summary.source_version` of `experiment_record_v2.json` must show
   `git_head_at_run=e90a62fda27c…` and `csm_py_sha256=9a808487bc19…`
   (repaired csm; re-hash `csm.py` to verify).
3. **Full suite:** `pytest tests/ -q` → expect **1,669 passed**.
   Focused: `pytest tests/test_contextual_selection_csm.py
   tests/test_contextual_selection_audit_regressions.py
   tests/test_contextual_selection_final_audit_patch.py -q` → **39 passed**.
4. **Prefix/full equivalence (B1):** run the two tail tests; then independently
   rebuild a k=2 F-K fixture, truncate before the confirmation bar, and
   compare `available_at` and `task_s2_event_binding` outputs between
   truncated and full candidates at every query time (truncated must never be
   more permissive; `knowable_time is None` on the truncated tail).
5. **Containment (B2):** build two legs with times on one and indices only on
   the other → `sp05_containment` must raise; both-with-times → timestamp
   comparison (test the misleading-index case).
6. **Direction (B3):** T-S5 origin claims with direction missing/opposite/
   matching a DOWN leg → expect IC / AI / justified(B) respectively.
7. **Ambiguity (B4):** the M1-shaped fixture test must return `unresolved`
   AI with survivors and blocked dependents; the endpoint-evidence fixture
   must stay justified with the endpoint note; the unselected-ambiguity
   fixture must stay justified.
8. **Reproduction (E):** re-run the command in E with the same mirror CSVs
   (hashes `15d26d23…`, `e1d5c8f3…`). Expect `new_run_future_reference_violations=0`;
   `t2_exclusion_histogram = {"X-STATE|broken reference not bindabl…": 2832}`;
   14 events; T-S1 selections as in E/F; `ambiguity_accounting` exactly as in
   F (1,480/304/183/1,297/268; M1/D4/D5 material). JSON content must match
   modulo machine paths; gzip bytes are not expected to match byte-for-byte
   (limitation 4).
9. **Accounting language check (F):** confirm the record/report never counts
   cumulative per-boundary records as independent market events.
10. **Prohibited-dealings check:** no trading recommendations, no execution,
    no deterministic fallback into unusable evidence, no canonical-branch
    activity; selection quality remains `NOT_ESTABLISHED`.
