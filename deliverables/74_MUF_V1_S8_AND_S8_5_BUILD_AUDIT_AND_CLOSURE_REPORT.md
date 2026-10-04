# Deliverable 74: MUF V1 S8 & S8.5 Build, Independent Audit, and Closure Report

## 1. Executive Summary
- **Stage**: `MUF V1 S8 & S8.5 — Estimand Catalog, FeatureViewSpec, and DevelopmentEvaluationProtocol`
- **Status**: **CLOSED**
- **Production Module**: `project/trading_project/src/trading_system/market_understanding/estimand_catalog.py`
  - **SHA256**: `8813ecf9d55da861a650016d8cb2e91a4e792a2f708f8a32d38af79d63a3a967`
- **Test Module**: `project/trading_project/tests/test_muf_s8_estimand_catalog.py`
  - **SHA256**: `5b8eaa3a18c5e75a90e6b7f66884d395b7fb8eab3e06b25ec02a3792531b6b3d`
- **Release Certificate**: `project/trading_project/docs/releases/MODULE_MUF_V1_S8_ACCEPTED_SRC_TESTS.sha256`
- **Milestone Closure**: `project/trading_project/docs/releases/MILESTONE_MUF_V1_S8_CLOSED.md`

---

## 2. Invariant & Audit Verification (`D1-17`, `AP-1 §2, §3, §4`)
1. **Preregistered Estimand Identity & State Variable Closure (`D1-17`, `I-EST-1`, `I-SCAT-1..3`)**:
   - `EstimandArtifact` pins `state_catalog_hash`, `population_variable_refs`, `conditioning_variable_refs`, `future_observable_kind`, `boundary_span_contract`, `censoring_contract`, `missingness_contract`, `aggregation_contract`, `permitted_dataset_roles`, `preregistration_key`, and `code_hash`.
   - Any reference to an undeclared state variable fails closed with `S8_UNDEFINED_STATE_VARIABLE_IN_ESTIMAND`.
2. **FeatureViewSpec Lineage & Immutability (`AP-1 §3.1..3.4`, `I-FVIEW-1..5`, `I-GSG-4`)**:
   - `FeatureViewSpec` binds `state_catalog_hash`, `estimand_hash`, `selected_state_variable_refs`, and `transformation_refs`.
   - Modifying any selected variable or transformation produces a distinct `feature_view_hash` (`I-FVIEW-2`) without mutating `StateCatalogArtifact` or `GenericFactualStateGraphSpec` (`I-GSG-4`).
3. **DevelopmentEvaluationProtocol Dependency Closure (`AP-1 §3.3 & §4.3`, `I-SG-1A`)**:
   - `DevelopmentEvaluationProtocol` and `verify_development_protocol_dependency_closure` enforce complete dependency closure across `estimand_hash`, `feature_view_hash`, `state_catalog_hash`, `graph_spec_hash`, `dependence_contract_hash`, `objective_hash`, and `experiment_id`, and forbid `FINAL_EVALUATION_LOCKED` dataset roles (`I-SEL-3`).
4. **Competing-Risk & Wave-Continuation Realizations with Explicit Right-Censoring**:
   - `evaluate_development_estimand_realizations` evaluates confirmed wave outcomes in single-pass `O(W)` time and explicitly marks terminal unconfirmed subsequent outcomes as `CENSORING_STATUS_RIGHT_CENSORED` with `TypedState.UNAVAILABLE` (never silently dropping right-censored episodes).

---

## 3. Mutation Probe Results (`8/8 KILLED`)
- `M1_disable_estimand_hash_check`: **KILLED**
- `M2_disable_catalog_duplicate_estimand_guard`: **KILLED**
- `M3_disable_feature_view_undeclared_variable_guard`: **KILLED**
- `M4_disable_feature_view_hash_check`: **KILLED**
- `M5_disable_protocol_final_role_block`: **KILLED**
- `M6_disable_protocol_hash_check`: **KILLED**
- `M7_disable_verify_protocol_closure`: **KILLED**
- `M8_wrong_right_censoring_status`: **KILLED**
