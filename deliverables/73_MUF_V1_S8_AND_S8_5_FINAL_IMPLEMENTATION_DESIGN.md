# Deliverable 73 — MUF V1 S8 & S8.5 Final Implementation Design: Estimand Catalog, FeatureViewSpec, and DevelopmentEvaluationProtocol

## 1. Scope & Governance Authority

- **Sub-Stage**: `MUF V1 S8 & S8.5 — Estimand Catalog, FeatureViewSpec Registration, and DevelopmentEvaluationProtocol Preregistration`
- **Governing Authority**:
  - `deliverables/42_MUF_V1_INDEPENDENT_AUDIT_PATCH_AP1.md` (`§2 State Catalog Must Precede Estimand I-SCAT-1..3`, `§3 Estimand-Specific FeatureViewSpec I-FVIEW-1..5`, `§4 Dependency + Protocol Closure I-SG-1A`)
  - `deliverables/38_MUF_V1_FINAL_DESIGN_PATCH_D1.md` (`D1-17 Estimand Before Information Claim I-EST-1`)
  - `deliverables/39_MUF_V1_FINAL_DESIGN_PATCH_D2.md` (`D2-3`, `D2-4`, `D2-15`, `D2-22`)

---

## 2. Target Files

- **Implementation**: `project/trading_project/src/trading_system/market_understanding/estimand_catalog.py`
- **Test Suite**: `project/trading_project/tests/test_muf_s8_estimand_catalog.py`
- **Sealed S0..S7 non-touch**: All files in `MODULE_MUF_V1_S0..S7_ACCEPTED_SRC_TESTS.sha256` remain byte-for-byte untouched.

---

## 3. Core Contracts & Invariants in `estimand_catalog.py`

### 3.1 `EstimandArtifact` & `EstimandCatalog` (`D1-17`, `AP-1 §2`, `I-EST-1`, `I-SCAT-1..3`, `I-GSG-4`)

- `EstimandArtifact` (`ImmutableRecord`):
  - `estimand_id: str`
  - `state_catalog_hash: str`
  - `population_variable_refs: Tuple[str, ...]`
  - `conditioning_variable_refs: Tuple[str, ...]`
  - `future_observable_kind: str` (`"SUBSEQUENT_WAVE_DISPLACEMENT_RATIO"`, `"SUBSEQUENT_WAVE_EFFICIENCY"`, `"COMPETING_BOUNDARY_FIRST_PASSAGE"`)
  - `boundary_span_contract: str`
  - `censoring_contract: str` (`"EXPLICIT_RIGHT_CENSORED_AT_DATASET_END"`)
  - `missingness_contract: str` (`"EXPLICIT_TYPED_STATE_NO_SILENT_DROP"`)
  - `aggregation_contract: str`
  - `permitted_dataset_roles: Tuple[str, ...]`
  - `preregistration_key: InformationKey`
  - `code_hash: str`
  - `estimand_hash: str`
- **Invariants**:
  - `I-SCAT-1..2`: `EstimandArtifact.create(..., state_catalog=...)` verifies that every variable in `population_variable_refs` and `conditioning_variable_refs` is defined in `state_catalog` (`S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND`).
  - `I-GSG-4`: Creating or registering an `EstimandArtifact` never mutates `StateCatalogArtifact` or `GenericFactualStateGraphSpec`.

### 3.2 `FeatureViewSpec` (`AP-1 §3.1..3.4`, `I-FVIEW-1..5`)

- `FeatureViewSpec` (`ImmutableRecord`):
  - `feature_view_id: str`
  - `state_catalog_hash: str`
  - `selected_state_variable_refs: Tuple[str, ...]`
  - `transformation_refs: Tuple[str, ...]`
  - `missingness_handling_ref: str`
  - `availability_rule_ref: str`
  - `estimand_hash: str`
  - `schema_version: str`
  - `feature_view_hash: str`
- **Invariants (`I-FVIEW-1..5`)**:
  - Every variable in `selected_state_variable_refs` must exist in the bound `StateCatalogArtifact` (`S8_FEATURE_VIEW_UNDECLARED_VARIABLE`).
  - `estimand_hash` must match the bound `EstimandArtifact.estimand_hash`.
  - Modifying `selected_state_variable_refs` or `transformation_refs` changes `feature_view_hash` (`I-FVIEW-2`).

### 3.3 `DevelopmentEvaluationProtocol` (`AP-1 §3.3 & §4.3`, `I-SG-1A`, `I-FVIEW-1`)

- Pins `protocol_id`, `estimand_hash`, `feature_view_hash`, `state_catalog_hash`, `graph_spec_hash`, `dependence_contract_hash`, `objective_hash`, `dataset_id`, `dataset_role`, `experiment_id`, `preregistration_key`, and `protocol_hash`.
- Enforces `I-SG-1A` (`verify_development_protocol_dependency_closure`): verifies all component hashes against the live artifacts and `ExperimentRegistry` before any development estimand realization can be computed.

### 3.4 Causal Competing-Risk & Wave Continuation Realization (`evaluate_development_estimand_realizations`)

- Evaluates a preregistered `EstimandArtifact` + `FeatureViewSpec` under a verified `DevelopmentEvaluationProtocol` on a `DependenceAccountingBundle` (`S7`):
  - Enforces `I-FVIEW-3`: feature values at `decision_key = wave_i.wave_end_confirmed_key` only access state observations visible at `<= decision_key`.
  - Computes subsequent wave outcome (`UNCENSORED` when subsequent wave `i+1` confirms within the dataset; `RIGHT_CENSORED_AT_DATASET_END` with `TypedState.RIGHT_CENSORED` when right-censored at dataset boundary).
