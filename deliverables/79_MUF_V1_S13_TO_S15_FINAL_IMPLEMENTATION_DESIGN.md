# Deliverable 79: MUF V1 S13–S15 — Final Implementation Design
## Final Evaluation Execution, Irreversible Exposure & Lineage Firewall, and Role-Gated Reality / Real-Time Causal Market Understanding Surface (`final_evaluation_and_reality.py`)

### 1. Scope & Governing Authority
- **Stage**: `MUF V1 S13, S14, S15` (`D1-3`, `D1-15`, `D1-20`, `D2-5`, `D2-6`, `D2-10`, `D2-22`, `Correction-1 §3, §4`, `AP-1 §4`)
- **Invariants Enforced**:
  - **S13 (`I-EVAL-1..6`, `I-EVP-1..3`, `I-SG-1B`, `I-SG-2`)**:
    - `open_and_run_final_evaluation_once` requires a valid `GateG3OpenFinalAuthorizationDecision` (`GATE_G3_AUTHORIZED_TO_OPEN`), verifies `I-SG-1B` bundle closure, enforces `allowed_outputs` (`Attack 30`, `Attack 48`), logs non-preregistered post-open output requests as `EXPLORATORY_OUTPUT_REQUESTED` (`I-EVAL-6`), and preserves `protocol.protocol_hash` byte-for-byte (`I-EVP-2`).
  - **S14 (`D1-20`, `I-FE-1..2`, `I-DR-3..4`, `Attacks 22 & 49`)**:
    - `FinalEvaluationOutcomeRecord` and `FinalEvaluationExposureRegistry` permanently record every final evaluation outcome (including negative/unfavorable outcomes, `I-FE-2`) and mark `dataset_ancestry_root` as exposed.
    - Reusing an exposed `dataset_ancestry_root` for a modified lineage fails closed with `EXPOSED_INVALID_FOR_FINAL_SELECTION` (`Attack 22`) unless a certified `EquivalenceClaimArtifact` (`EQUIVALENCE_RESULT_CERTIFIED`) is provided (`D1-20 #5`), and all historical outcomes on that ancestry root remain permanently reported (`Attack 49`).
  - **S15 (`D1-3`, `D1-15`, `Correction-1 §4`, `I-EXPL-1`, `I-HR-1..2`, `I-SG-2`, `Attacks 12 & 24`)**:
    - `ExplanationStateRecord` enforces the descriptive whitelist `{"MONITORING", "PATTERN_REQUIREMENTS_SATISFIED", "CONTRADICTED", "SUPERSEDED"}` and rejects `"PROBABLE"`, `"LIKELY"`, `"SUPPORTED"`, `"WINNING_EXPLANATION"`, and `"FACTUALLY_ESTABLISHED_WHERE_POSSIBLE"` (`Attack 24`).
    - `RealityAuditSurfaceRecord` enforces role-gated reality inspection (`Correction-1 §4`, `I-SG-2`) and triggers `EXPOSED_INVALID_FOR_FINAL_SELECTION` if a final-dataset review requests design changes (`Attack 12`).
    - `analyze_causal_market_state_as_of` delivers a fast, practical, as-of causal market understanding diagnostic report (`CausalMarketUnderstandingDiagnosticReport`) combining live forming wave geometry, confirmed wave state descriptors, episode span-cluster counts, empirical historical continuation distributions (with explicit right-censoring), and descriptive explanation states.
