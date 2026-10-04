# Deliverable 67 — MUF V1 S5 & Gate G1 Final Implementation Design: Candidate Wave Representation Construction & Structural Qualification

## 1. Scope & Governance Authority

- **Sub-Stage**: `MUF V1 S5 — Candidate Wave Representation Construction & Structural Qualification Gate G1`
- **Governing Authority**:
  - `deliverables/39_MUF_V1_FINAL_DESIGN_PATCH_D2.md` (`D2-1`, `D2-2`, `D2-3`, `D2-17`, `D2-22` Annex B: `S5 — Candidate representation construction on DEVELOPMENT only`, `G1 — Structural Qualification: ELIGIBLE / INELIGIBLE — no predictive winner`)
  - `deliverables/40_MUF_V1_D2_CORRECTION_1.md` (`§1 Earliest Lawful Availability I-EARLY-1..3`, `§2 Identity-Defining Basis != Proof/Witness Refs I-IDB-1..3`)
  - `deliverables/38_MUF_V1_FINAL_DESIGN_PATCH_D1.md` (`D1-4`, `D1-5`, `D1-6`, `D1-8`, `I-WID-1..3`, `I-SD-1..4`, `I-DE-1`)
- **Real-Time & Streaming Performance Architecture**:
  - Single-pass `O(N)` construction (`O(1)` amortized per bar) using prefix-sum path-length accumulators (`prefix_path_len`) so finalized wave geometry between any `start_origin` and `end_origin` is computed in **`O(1)` time** without re-scanning intermediate bars.
  - `IncrementalWaveRepresentationEngine` supports live bar-by-bar streaming updates in **`O(1)` time per bar**.
  - `query_wave_representation_as_of` guarantees byte-identical prefix invariance (`I-IMM-3`).

---

## 2. Target Files

- **Implementation**: `project/trading_project/src/trading_system/market_understanding/wave_representation.py`
- **Test Suite**: `project/trading_project/tests/test_muf_s5_wave_representation.py`
- **Sealed S0/S1/S2/S3/S4 non-touch**: All files in `MODULE_MUF_V1_S0..S4_ACCEPTED_SRC_TESTS.sha256` remain byte-for-byte untouched.

---

## 3. Core Contracts & Invariants in `wave_representation.py`

### 3.1 `CandidateWaveRepresentationSpec` (`ImmutableRecord`)

Defines a candidate wave representation specification:
- `representation_id: str`
- `family_kind: str` (`"ALPHA_POLICY_SCALE"`, `"BETA_PARAMETER_FREE"`, `"GAMMA_RESIDUAL"`, `"DELTA_EVENT_CONTAINMENT"`)
- `scope_timeline_id: str`
- `scope_axis: InformationAxis`
- `intrinsic_scale_key: Union[str, TypedState]` (`I-SD-4`: must be `TypedState.NOT_APPLICABLE` for `BETA_PARAMETER_FREE` and `DELTA_EVENT_CONTAINMENT`; must be non-empty `str` for `ALPHA_POLICY_SCALE`)
- `identity_rule_ref: Union[str, TypedState]` (`I-WIB-2`: if `TypedState.NOT_CONFIGURED`, wave construction fails closed with `S5_IDENTITY_RULE_NOT_CONFIGURED`)
- `representation_spec_hash: str`

### 3.2 Append-Only Wave Process Tables (`D1-5`, `D2-1`, `D2-2`, `Correction-1 §1 & §2`)

1. **`WaveIdentityRecord`** (`ImmutableRecord`):
   - `wave_process_id: str` (computed strictly via S0 `wave_process_identity(identity_basis)` — zero end facts, zero proof noise, `I-WPI-1..5`, `I-IDB-1..3`)
   - `identity_basis: WaveProcessIdentityBasis`
   - `identity_proof: WaveIdentityProof`
   - `start_turning_point_id: str`
   - `origin_position: int`
   - `origin_key: InformationKey`
   - `wave_identity_information_key: InformationKey` (`I-EARLY-1..3`: must equal the earliest lawful `InformationKey` where all required basis inputs are visible; earlier raises `PrematureAvailability`, later without a new required basis input raises `NonEarliestAvailability`)
   - `wave_direction: str` (`DIRECTION_UP` when `start_turning_point.extrema_kind == "LOW"`, `DIRECTION_DOWN` when `"HIGH"`)
   - `published_record: PublishedRecord`
2. **`RunningWaveObservationRecord`** (`ImmutableRecord`):
   - Append-only running descriptor observation at bar `observation_key >= wave_identity_information_key` while the wave process is active:
   - `observation_id: str`, `wave_process_id: str`, `timeline_id: str`, `observation_position: int`, `observation_key: InformationKey`
   - `running_bar_count: int`
   - `running_displacement: MetricResult` (`EXACT`)
   - `running_path_length: MetricResult` (`EXACT`)
   - `running_efficiency_ratio: Union[MetricResult, TypedState]` (`EXACT` when `running_path_length > 0`, else `TypedState.UNDEFINED` per `I-DE-1`)
   - `running_extreme_price: MetricResult` (`EXACT`)
   - `published_record: PublishedRecord`
3. **`FinalizedWaveGeometryRecord`** (`ImmutableRecord`):
   - Separate append-only record emitted only when an alternating opposite `AuthoritativeTurningPointRecord` (`origin_position > start.origin_position`) is confirmed at `end_turning_point.availability_key`:
   - `geometry_record_id: str`, `wave_process_id: str`, `timeline_id: str`
   - `start_turning_point_id: str`, `end_turning_point_id: str`
   - `start_origin_position: int`, `end_origin_position: int`
   - `start_origin_key: InformationKey`, `end_origin_key: InformationKey`
   - `wave_end_confirmed_key: InformationKey` (`max(wave_identity_information_key, end_turning_point.availability_key)`)
   - `final_bar_count: int`
   - `final_displacement: MetricResult` (`EXACT`)
   - `final_path_length: MetricResult` (`EXACT`, computed in `O(1)` via prefix sums)
   - `final_efficiency_ratio: Union[MetricResult, TypedState]` (`EXACT` or `TypedState.UNDEFINED` on zero denominator per `I-DE-1`)
   - `published_record: PublishedRecord`
4. **`WaveStatusEventRecord`** (`ImmutableRecord`):
   - Append-only lifecycle transitions (`"FORMING"`, `"CONFIRMED"`, `"SUPERSEDED"`) keyed by `status_event_key: InformationKey`.

### 3.3 `CandidateWaveRepresentationBundle` & `As-Of` Projection

- `construct_candidate_wave_representation(...) -> CandidateWaveRepresentationBundle`:
  - Enforces development-only dataset role (`DEVELOPMENT_FIT` or `DEVELOPMENT_SELECTION`; rejects `FINAL_EVALUATION_LOCKED` with `SelectionBlockedError`).
  - Promotes S2 `SwingEventWitnessRecord` items using the authorized `PolicyArtifact` and constructs the 4 append-only wave tables in a single `O(N)` pass.
- `query_wave_representation_as_of(bundle, *, at_key) -> WaveRepresentationAsOfView`:
  - Filters all 4 tables causally by `availability_key <= at_key` (`require_visible_at`), derives active vs confirmed status at `at_key` from visible `WaveStatusEventRecord` rows without mutating any record, and guarantees byte-identical prefix invariance (`verify_wave_prefix_invariance`).

### 3.4 Gate `G1` — Structural Qualification (`evaluate_g1_structural_qualification`)

- Evaluates a `CandidateWaveRepresentationBundle` against explicit `StructuralQualificationCriteria` (`min_confirmed_waves`, `min_wave_identities`, `require_causal_prefix_invariance`).
- Rejects `FINAL_EVALUATION_LOCKED` datasets (`G1_BLOCKED_FINAL_DATASET_FORBIDDEN`) and rejects any attempt to claim a predictive winner (`claim_predictive_winner=True` -> `G1_WINNER_CLAIM_FORBIDDEN`, `I-SEL-1`).
- Emits `StructuralQualificationRecord` with `qualification_status ∈ {"ELIGIBLE", "INELIGIBLE"}` and `claim_boundary = "STRUCTURAL_ELIGIBILITY_ONLY_NOT_PREDICTIVE_WINNER"`.
