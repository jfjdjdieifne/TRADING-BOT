# Deliverable 75: MUF V1 S9 & Gate G2 — Final Implementation Design
## Development Information Evaluation & Gate G2 Selection (`information_selection.py`)

### 1. Scope & Governing Authority
- **Stage**: `MUF V1 S9 + Gate G2` (`D2-3`, `D2-4`, `D2-17`, `D2-22`, `AP-1 §4.1..4.4`)
- **Invariants Enforced**:
  - `I-SEL-1`: Structural qualification (`G1`) does not choose a predictive winner; only `G2` evaluates information objectives on `DEVELOPMENT_SELECTION`.
  - `I-SEL-2`: Information-based selection without a preregistered `EstimandArtifact`, `FeatureViewSpec`, and `DevelopmentEvaluationProtocol` fails closed (`SelectionBlockedError`).
  - `I-SEL-3`: `FINAL_EVALUATION_LOCKED` dataset roles are strictly forbidden in `S9` and `Gate G2`.
  - `I-SEL-4` & `D2-17`: When the `ObjectiveArtifact` is `TypedState.NOT_CONFIGURED` or `TypedState.UNDEFINED`, `Gate G2` returns `GATE_G2_NOT_CONFIGURED` (`TypedState.NOT_CONFIGURED`), preserving the set of structurally `ELIGIBLE` candidates without inventing a winner.
  - `I-SEL-5`: Visual/human subjective preference is forbidden as a tie-breaker; tied candidates under `PRESERVE_TIED_CANDIDATES_NO_WINNER` remain tied with `selected_winner_candidate_id = TypedState.UNDEFINED`.
  - `I-ER-1..5` & `I-FVIEW-2`: Every candidate evaluation is bound to a preregistered experiment in `ExperimentRegistry`; failed/inferior candidates remain permanently recorded in the registry.

### 2. Core Contracts in `src/trading_system/market_understanding/information_selection.py`
1. **`CandidateInformationEvaluationRecord`**:
   - Immutable record capturing a single structurally `ELIGIBLE` candidate's development information evaluation on `DEVELOPMENT_SELECTION` (or authorized development role) under a pinned `DevelopmentEvaluationProtocol`:
     - `evaluation_id`, `candidate_id`, `experiment_id`, `representation_spec_hash`, `policy_hash`, `protocol_hash`, `estimand_hash`, `feature_view_hash`, `state_catalog_hash`, `graph_spec_hash`, `dependence_contract_hash`, `objective_hash`, `dataset_id`, `dataset_role`
     - `structural_eligibility_status` (must be `QUALIFICATION_STATUS_ELIGIBLE`)
     - `uncensored_realization_count`, `right_censored_realization_count`, `non_overlapping_span_cluster_count`
     - `cluster_weighted_information_score` (`MetricResult` or `TypedState`)
     - `evaluation_key`, `evaluation_record_hash`
2. **`GateG2InformationSelectionDecision`**:
   - Immutable record emitted by `run_gate_g2_information_selection(...)`:
     - `decision_id`, `gate_status` (`GATE_G2_SELECTED`, `GATE_G2_TIED_NO_UNIQUE_WINNER`, `GATE_G2_NOT_CONFIGURED`)
     - `objective_hash_or_state` (`str` or `TypedState`)
     - `eligible_candidate_ids`: `Tuple[str, ...]`
     - `candidate_evaluation_hashes`: `Tuple[str, ...]`
     - `selected_winner_candidate_id`: `Union[str, TypedState]`
     - `tied_top_candidate_ids`: `Tuple[str, ...]`
     - `decision_key`: `InformationKey`
     - `research_debt_024_status`: `str` (always `RESEARCH_DEBT_024_OPEN`)
     - `decision_hash`: `str`
3. **`evaluate_candidate_information_on_development(...)` & `run_gate_g2_information_selection(...)`**:
   - Pure, deterministic `O(W)` evaluation using non-overlapping episode span-cluster inverse weighting (`1 / cluster_size` per uncensored realization in cluster) so overlapping episodes do not inflate development information scores.
   - Zero prohibited AST identifiers (`PROHIBITED_IMPLEMENTATION_TERMS`, `PROHIBITED_MARKET_SHAPE_TERMS`), zero private imports, and zero numeric literals outside `{-1, 0, 1}`.
