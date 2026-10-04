# MILESTONE MUF V1 S3 CLOSED — Research-Governance Infrastructure & Gate G0

## 1. Closure Decision

`MUF V1 S3 — Research-Governance Infrastructure & Gate G0` is formally **ACCEPTED AND CLOSED** after end-to-end design, build, adversarial testing, and independent `/tmp` mutation verification (`8/8` mutants killed).

## 2. Sealed S3 Files & SHA256 Digests

Pinned in `docs/releases/MODULE_MUF_V1_S3_ACCEPTED_SRC_TESTS.sha256`:

- `src/trading_system/market_understanding/policy_governance.py`
  - SHA256: `1564eca58b971ffc5bfa2ae1e1c4ad2944d630d264db9a468f910f608a33fc3b`
- `tests/test_muf_s3_policy_governance.py`
  - SHA256: `fee189f4689010fd1cedca37011729bcb22206c4a13fcef0ac940ca0af1d003f`

## 3. Invariants Enforced

1. **Objective Governance (`D1-1`, `D2-3`, `I-OA-1..5`, Attack 28)**:
   - Standing default `QUALIFICATION_OBJECTIVE_DEFAULT = TypedState.UNDEFINED`.
   - `ECONOMIC_OBJECTIVE` is strictly forbidden in MUF (`S3_ECONOMIC_OBJECTIVE_OUT_OF_SCOPE`).
   - `INFORMATION_OBJECTIVE` requires non-empty `estimand_refs`; non-information objectives forbid `estimand_refs`.
2. **Dataset Identity, Role, Exposure & Ancestry Firewall (`D1-2`, `D2-6`, `D2-7`, `I-DR-1..5`, `I-DATA-1..5`, `I-RES-1..2`, Attacks 30, 31, 32, 33, 46, 49)**:
   - `RESERVE != OPEN`: reserving `FINAL_EVALUATION_LOCKED` keeps `exposure_state = UNEXPOSED` and `reservation_status = FINAL_DATA_RESERVED`.
   - Premature inspection, second open, or design-influencing review transitions `FINAL_EVALUATION_LOCKED` to `EXPOSED_INVALID_FOR_FINAL_SELECTION` (`FINAL_EVALUATION_INVALIDATED`).
   - Role reassignment after any exposure event fails closed (`S3_ROLE_REASSIGNMENT_AFTER_EXPOSURE`).
   - Undeclared shared content hash, temporal overlap on the same source/timeline without parent link, and exposed ancestor chains fail closed.
3. **Walk-Forward vs Final Data Firewall (`D2-18`, `I-WF-1..3`, Attack 47)**:
   - `FoldProtocolArtifact` enforces `DEVELOPMENT_FIT` before `DEVELOPMENT_SELECTION`, monotonic fold progression, and zero reference to or temporal overlap with `FINAL_EVALUATION_LOCKED` datasets.
4. **Human Review Governance & Contamination Tripwire (`D1-3`, `D2-10`, `I-HR-1..2`, Attack 12)**:
   - `HumanReviewRecord.create_and_apply` logs every review causally and automatically invalidates `FINAL_EVALUATION_LOCKED` data if `requested_changes` is non-empty or `change_influence == DESIGN_INFLUENCING`.
5. **Experiment Registry (`D1-16`, `I-ER-1..5`, Attacks 13 & 14)**:
   - Append-only `ExperimentRegistry` forbids deleting or overwriting failed/completed trials (`S3_EXPERIMENT_DELETION_FORBIDDEN`) and rejects `experiment_id` parameter/objective collisions (`S3_EXPERIMENT_IDENTITY_COLLISION`).
6. **PolicyArtifact & Authoritative Turning-Point Promotion (`D1-4`, `D2-1`, `I-PAUTH-1..4`, Attack 25)**:
   - `PolicyArtifact` binds `policy_hash` into `AuthoritativeTurningPointRecord` via `promote_swing_witness_with_policy_artifact`, ensuring distinct turning-point and wave-process identities across distinct policies while preserving `Origin != Availability`.
7. **Authority Gate `G0` (`D1-21`, `D2-22`)**:
   - `evaluate_g0_calibration_gate` fails closed with `SelectionBlockedError` unless all 5 calibration prerequisites are satisfied.

## 4. Verification Summary

- `tests/test_muf_s3_policy_governance.py`: `30 passed`
- `tests/test_muf_s2_detector_witness.py`: `30 passed`
- `tests/test_muf_s1_price_path.py` + `tests/test_muf_s1_path_schemas.py`: `89 passed`
- `tests/test_muf_s0_*.py`: `67 passed`
- Full `trading_project` regression suite: `1288 passed`
- S0 AST guards (`scan_private_imports`, `scan_prohibited_implementations`, `scan_market_shape_implementations`): `() / () / ()`
- Independent `/tmp` mutation battery: `8/8 KILLED`
