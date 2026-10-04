# Deliverable 65 — MUF V1 S4 Final Implementation Design: Development Policy Calibration Harness

## 1. Scope & Governance Authority

- **Sub-Stage**: `MUF V1 S4 — Development Policy Calibration Harness`
- **Governing Authority**:
  - `deliverables/39_MUF_V1_FINAL_DESIGN_PATCH_D2.md` (`D2-1`, `D2-3`, `D2-4`, `D2-7`, `D2-12`, `D2-22` Annex B: `S4 — Development policy fit where authorized, DEVELOPMENT_FIT only`)
  - `deliverables/38_MUF_V1_FINAL_DESIGN_PATCH_D1.md` (`D1-1`, `D1-2`, `D1-4`, `D1-16`, `D1-21`)
  - `deliverables/63_MUF_V1_S3_FINAL_IMPLEMENTATION_DESIGN.md` & `deliverables/64_MUF_V1_S3_BUILD_AUDIT_AND_CLOSURE_REPORT.md` (`MUF V1 S3 CLOSED`)
- **Strict Non-Invention Discipline**:
  - `S4` invents **zero** numerical quantiles, windows, thresholds, or objectives.
  - `QualificationObjective` remains `TypedState.UNDEFINED` unless an explicit, owner-authorized `ObjectiveArtifact` is passed through Gate `G0`.
  - `S4` cannot execute without a valid `G0CalibrationGateCertificate` produced by `evaluate_g0_calibration_gate`.
  - `S4` operates **exclusively** on `DEVELOPMENT_FIT` datasets (`[start_key, end_key]`) and fails closed if any bar from `DEVELOPMENT_SELECTION` or `FINAL_EVALUATION_LOCKED` (or outside `[start_key, end_key]`) is supplied.

---

## 2. Target Files

- **Implementation**: `project/trading_project/src/trading_system/market_understanding/policy_calibration.py`
- **Test Suite**: `project/trading_project/tests/test_muf_s4_policy_calibration.py`
- **Sealed S0/S1/S2/S3 non-touch**: All files in `MODULE_MUF_V1_S0_ACCEPTED_SRC_TESTS.sha256`, `MODULE_MUF_V1_S1_ACCEPTED_SRC_TESTS.sha256`, `MODULE_MUF_V1_S2_ACCEPTED_SRC_TESTS.sha256`, and `MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256` remain byte-for-byte untouched.

---

## 3. Core Contracts & Invariants in `policy_calibration.py`

### 3.1 `PolicyCandidateScoreCard` (`ImmutableRecord`)

Records the deterministic evaluation of a single candidate `DetectorPolicyWitnessSpec` (and its `SwingConfirmationPolicy`) on a `DEVELOPMENT_FIT` bar stream under an authorized `ObjectiveArtifact`:
- `candidate_policy_witness_ref: str`
- `policy_spec: DetectorPolicyWitnessSpec`
- `confirmed_swing_count: int`
- `candidate_observation_count: int`
- `objective_metric: Union[MetricResult, TypedState]`
- `constraint_satisfied: bool`
- `evaluation_cutoff_key: InformationKey`

### 3.2 `PolicyCalibrationRecipe` (`ImmutableRecord`)

Canonical, domain-separated recipe binding every input to a `DEVELOPMENT_FIT` calibration run:
- `recipe_id: str`
- `g0_certificate: G0CalibrationGateCertificate`
- `objective_artifact_hash: str`
- `fit_dataset_id: str`
- `fit_dataset_identity_hash: str`
- `fit_dataset_role_hash: str`
- `experiment_id: str`
- `scope_timeline_id: str`
- `scope_axis: InformationAxis`
- `scope_representation_id: str`
- `candidate_policy_witness_refs: Tuple[str, ...]`
- `fit_cutoff_key: InformationKey`
- `recipe_hash: str`

### 3.3 `PolicyCalibrationReceipt` (`ImmutableRecord`)

Immutable output receipt of `calibrate_development_policy_artifact`:
- `receipt_id: str`
- `recipe: PolicyCalibrationRecipe`
- `scorecards: Tuple[PolicyCandidateScoreCard, ...]`
- `outcome_status: str` (`"CALIBRATED_UNIQUE"`, `"TIE_PRESERVED_NO_WINNER"`, `"NO_CANDIDATE_SATISFIED_OBJECTIVE"`)
- `selected_policy_artifact: Union[PolicyArtifact, TypedState]`
- `tied_policy_witness_refs: Tuple[str, ...]`
- `updated_fit_dataset_role: DatasetRoleArtifact`
- `updated_experiment_record: RepresentationExperimentRecord`
- `receipt_hash: str`

### 3.4 Calibration & Reproduction Functions

1. `validate_development_fit_bar_stream(bars, *, fit_dataset_identity, fit_dataset_role, fit_cutoff_key=None)`:
   - Verifies `fit_dataset_role.role == DATASET_ROLE_DEVELOPMENT_FIT` and `exposure_state in (UNEXPOSED, EXPOSED_DEVELOPMENT)`.
   - Verifies non-empty `bars` of `PublishedOhlcBarFact`, all with `dataset_identity == fit_dataset_identity.dataset_id`, `source_identity == fit_dataset_identity.source_identity`, `availability_key.timeline_id == fit_dataset_identity.timeline_id`, strictly increasing `availability_key`, and every `bar.availability_key` inside `[fit_dataset_identity.start_key, effective_cutoff_key]` where `effective_cutoff_key <= fit_dataset_identity.end_key`.
   - Any bar after `effective_cutoff_key` or outside `[start_key, end_key]` raises `PrematureAvailability`.
2. `calibrate_development_policy_artifact(...) -> PolicyCalibrationReceipt`:
   - Re-verifies ` evaluate_g0_calibration_gate(...)` and cross-checks that the passed `g0_certificate` matches the live `ObjectiveArtifact`, `DatasetIdentityArtifact`, `DatasetRoleArtifact`, `ExperimentRegistry`, `experiment_id`, and `owner_fit_authorization_ref`.
   - Rejects `OBJECTIVE_KIND_INFORMATION` in S4 detector policy calibration (`S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT`) because detector policy calibration in S4 is governed by `DETECTION_VALIDITY` or `REPRESENTATION_DIAGNOSTIC` objectives before S8 Estimand registration.
   - Evaluates each candidate `(SwingConfirmationPolicy, DetectorPolicyWitnessSpec)` causally on the validated `DEVELOPMENT_FIT` bar stream via `adapt_detector_witness_stream`.
   - Transitions the experiment in `ExperimentRegistry` (`PREREGISTERED -> RUNNING -> COMPLETED` or `FAILED`) and appends a `DEVELOPMENT_FIT` exposure event to `fit_dataset_role`.
   - Enforces tie discipline: if the top-ranked candidates tie (or if `comparison_direction is TypedState.NOT_APPLICABLE` / `SATISFY_CONSTRAINT` with multiple satisfying candidates), preserves all tied candidates (`outcome_status = "TIE_PRESERVED_NO_WINNER"`, `selected_policy_artifact = TypedState.UNDEFINED`) instead of inventing a tie-breaker!
   - When a unique valid candidate is selected, constructs and returns an immutable `PolicyArtifact` with `calibration_provenance_kind = PROVENANCE_DEVELOPMENT_FIT` and `reproduction_recipe_hash = recipe.recipe_hash`.
3. `reproduce_and_verify_calibrated_policy(...) -> bool`:
   - Re-runs the calibration evaluation on the `DEVELOPMENT_FIT` bar stream and verifies that the resulting `recipe_hash`, `detector_policy_witness_ref`, and `policy_hash` match the target `PolicyArtifact` byte-for-byte (`S3_POLICY_REPRODUCTION_MISMATCH` on any discrepancy).
