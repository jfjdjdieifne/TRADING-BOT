# Deliverable 69 — MUF V1 S6 Final Implementation Design: Descriptor Registry, StateCatalogArtifact, and GenericFactualStateGraphSpec

## 1. Scope & Governance Authority

- **Sub-Stage**: `MUF V1 S6 — Descriptor Registry, StateCatalogArtifact, and GenericFactualStateGraphSpec`
- **Governing Authority**:
  - `deliverables/42_MUF_V1_INDEPENDENT_AUDIT_PATCH_AP1.md` (`§1 GenericFactualStateGraphSpec I-GSG-1..4`, `§2 StateCatalogArtifact I-SCAT-1..3`, `§4 Dependency & Protocol Closure`)
  - `deliverables/39_MUF_V1_FINAL_DESIGN_PATCH_D2.md` (`D2-8 Cycle-Safe Snapshot Closure I-CLOS-1..3`, `D2-9 Adjacency != Alternatives I-DELTA-1..4`, `D2-10 InformationKey Everywhere I-IKA-1`, `D2-16 Running Descriptor Causality Contract I-DESC-1..2`, `D2-22 Annex B`)
  - `deliverables/40_MUF_V1_D2_CORRECTION_1.md` (`§4 State Graph Computation != Human Reality Surface I-SG-1..2`)
  - `deliverables/38_MUF_V1_FINAL_DESIGN_PATCH_D1.md` (`D1-6..13`, `I-SD-1..4`, `I-DE-1`, `I-DESC-1..3`)

---

## 2. Target Files

- **Implementation**: `project/trading_project/src/trading_system/market_understanding/state_graph.py`
- **Test Suite**: `project/trading_project/tests/test_muf_s6_state_graph.py`
- **Sealed S0..S5 non-touch**: All files in `MODULE_MUF_V1_S0..S5_ACCEPTED_SRC_TESTS.sha256` remain byte-for-byte untouched.

---

## 3. Core Contracts & Invariants in `state_graph.py`

### 3.1 `DescriptorSpec` & `DescriptorRegistry` (`D2-16`, `I-DESC-1..3`, `I-DE-1`)

- `DescriptorSpec` (`ImmutableRecord`):
  - `descriptor_id: str`
  - `semantic_definition: str`
  - `stage: str` (`"RUNNING_ONLY"`, `"FINAL_ONLY"`, `"BOTH_SEPARATE_FORMULAE"`)
  - `required_input_refs: Tuple[str, ...]`
  - `availability_rule_ref: str`
  - `denominator_contract: str`
  - `boundary_contract: str`
  - `policy_dependencies: Tuple[str, ...]`
  - `missingness_contract: str`
  - `running_formula_hash: Union[str, TypedState]`
  - `final_formula_hash: Union[str, TypedState]`
  - `descriptor_hash: str`
- **Invariants**:
  - `I-DESC-1 / I-DESC-2`: `RUNNING_ONLY` and the running side of `BOTH_SEPARATE_FORMULAE` reject any `required_input_refs` referencing end/final/future wave facts (`S6_FUTURE_FACT_IN_RUNNING_DESCRIPTOR`).
  - `BOTH_SEPARATE_FORMULAE` requires two distinct, non-empty formula hashes (`running_formula_hash != final_formula_hash`).
  - `I-DESC-3 / I-GSG-2`: Rejects any reference to `estimand`, `information_objective`, `horizon`, or `evaluation_result`.

### 3.2 `StateVariableSpec` & `StateCatalogArtifact` (`AP-1 §2`, `I-SCAT-1..3`)

- `StateVariableSpec` (`ImmutableRecord`):
  - `variable_id: str`, `semantic_definition: str`, `value_domain_kind: str`
  - `source_descriptor_refs: Tuple[str, ...]`, `source_relation_refs: Tuple[str, ...]`
  - `availability_rule_ref: str`, `missingness_semantics_ref: str`, `variable_hash: str`
- `StateCatalogArtifact` (`ImmutableRecord`):
  - `state_catalog_id: str`
  - `variable_specs: Tuple[StateVariableSpec, ...]`
  - `descriptor_refs: Tuple[str, ...]`
  - `relation_refs: Tuple[str, ...]`
  - `availability_missingness_semantics: str`
  - `schema_version: str`
  - `state_catalog_hash: str`
- Enforces that every descriptor/relation referenced by a `StateVariableSpec` is declared in `descriptor_refs` / `relation_refs` (`I-SCAT-1..2`), and changing any variable spec changes `state_catalog_hash` (`I-SCAT-3`).

### 3.3 `GenericFactualStateGraphSpec` (`AP-1 §1`, `I-GSG-1..4`)

- Binds `graph_spec_id`, `graph_spec_hash`, `state_catalog_hash`, `source_contract_hashes`, `representation_contract_hashes`, `descriptor_contract_hashes`, `relation_contract_hashes`, `missingness_contract_hash`, `information_key_contract_hash`, and `schema_version`.
- Strictly Estimand-free and Objective-free (`I-GSG-2`).

### 3.4 Relation Semantics (`D2-9`, `I-DELTA-1..4`) & Cycle-Safe Closure (`D2-8`, `I-CLOS-1..3`)

- Relation types: `ADJACENT_TO`, `ALTERNATES_WITH`, `CONTAINS`, `GEOMETRICALLY_COINCIDENT`, `PARTIAL_OVERLAP`, `GENERAL_REFERENCE`.
- `I-DELTA-1`: `ALTERNATES_WITH` is never accepted as `ADJACENT_TO` or parent containment (`S6_ALTERNATES_WITH_NOT_ADJACENCY`).
- `I-DELTA-2`: Unproven same-batch chronology (`KNOWN_SAME_BATCH` / `UNKNOWN_IF_SAME_BATCH`) cannot create a directed `ADJACENT_TO` relation (`S6_UNPROVEN_CHRONOLOGY_FOR_ADJACENT_TO`).
- `I-DELTA-3 / I-DELTA-4`: Same-direction merge rule defaults to `TypedState.NOT_CONFIGURED`, and Delta populated containment hierarchy without configured merge/adjacency authority is contract-only (`EVENT_ANCHORED_CONTAINMENT_HIERARCHY_CONTRACT_ONLY_NOT_CONFIGURED`).
- `compute_cycle_safe_graph_closure`:
  - Rejects `CONTAINS` cycles with `S6_ILLEGAL_WAVE_CONTAINMENT_CYCLE` (`D2-8`).
  - Traverses `GENERAL_REFERENCE` cycles deterministically once per node via visited set without infinite recursion (`I-CLOS-1`).
  - Validates `availability_key <= at_key` on every reachable node and relation (`I-CLOS-2`).
  - Produces an insertion-order-independent canonical `closure_hash` (`I-CLOS-3`).

### 3.5 Causal Scale-Invariant Wave Descriptor & State Graph Engine (`build_generic_factual_state_graph`)

- Computes in `O(N)` time over a `CandidateWaveRepresentationBundle` (`S5`):
  - Running wave descriptors (`running_displacement`, `running_path_length`, `running_efficiency_ratio`, `running_amplitude_vs_prior_wave`, `running_pace_vs_prior_wave`)
  - Finalized wave descriptors (`final_displacement`, `final_path_length`, `final_efficiency_ratio`, `final_retracement_or_extension_ratio`, `final_causal_efficiency_rank`)
  - Causal `ADJACENT_TO` wave transition relations (`relation_information_key = max(source_key, target_key)`, `D2-10`, `I-IKA-1`)
  - Causal state-variable observations bound to `StateCatalogArtifact` and `GenericFactualStateGraphSpec`.
