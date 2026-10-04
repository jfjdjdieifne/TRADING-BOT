# MILESTONE MUF V1 S4 CLOSED — Development Policy Calibration Harness

## 1. Closure Decision

`MUF V1 S4 — Development Policy Calibration Harness` is formally **ACCEPTED AND CLOSED** after end-to-end design, build, adversarial testing (`20/20` passed), and independent `/tmp` mutation verification (`8/8` mutants killed).

## 2. Sealed S4 Files & SHA256 Digests

Pinned in `docs/releases/MODULE_MUF_V1_S4_ACCEPTED_SRC_TESTS.sha256`:

- `src/trading_system/market_understanding/policy_calibration.py`
  - SHA256: `0c765a6c261838cb36d4f096b764e9762541ffbb4b2e33ebf994a5fe96b07204`
- `tests/test_muf_s4_policy_calibration.py`
  - SHA256: `1549449b8531230da6afec0953c9fba47b1a17c6a422481c20acf52b34d9b46d`

## 3. Invariants Enforced

1. **Authority Gate `G0` Re-Verification (`S4_MISSING_OR_MISMATCHED_G0_CERTIFICATE`)**:
   - `calibrate_development_policy_artifact` re-runs `evaluate_g0_calibration_gate` on live governance artifacts and verifies exact match with the passed `G0CalibrationGateCertificate`.
2. **Objective Scope Enforcement (`S4_INFORMATION_OBJECTIVE_NOT_VALID_FOR_DETECTOR_FIT`)**:
   - S4 detector policy calibration accepts only `DETECTION_VALIDITY` or `REPRESENTATION_DIAGNOSTIC` objectives and rejects `INFORMATION_OBJECTIVE` before S8 Estimand registration.
3. **`DEVELOPMENT_FIT` Causal Stream & Boundary Firewall (`S4_FIT_STREAM_OUTSIDE_DECLARED_DATASET`)**:
   - `validate_development_fit_bar_stream` enforces `DEVELOPMENT_FIT` role, dataset identity match, source/timeline/axis match, strictly increasing `availability_key`, and causal containment within `[start_key, fit_cutoff_key]`.
4. **Tie Preservation Without Inventing a Winner (`CALIBRATION_OUTCOME_TIE_NO_WINNER`)**:
   - When multiple candidate policies tie under the declared objective, `selected_policy_artifact` remains `TypedState.UNDEFINED` and all tied candidates are preserved in `tied_policy_witness_refs`.
5. **Automatic Exposure & Experiment Lifecycle Logging**:
   - Automatically records `EXPOSED_DEVELOPMENT` on `DatasetRoleArtifact` and transitions the experiment in `ExperimentRegistry` (`PREREGISTERED -> RUNNING -> COMPLETED/FAILED`).
6. **Deterministic Reproduction Verification (`reproduce_and_verify_calibrated_policy`)**:
   - Re-executes the calibration recipe and verifies byte-for-byte identity of `recipe_hash`, `detector_policy_witness_ref`, and `policy_hash`.

## 4. Verification Summary

- `tests/test_muf_s4_policy_calibration.py`: `20 passed`
- `tests/test_muf_s3_policy_governance.py`: `30 passed`
- `tests/test_muf_s2_detector_witness.py`: `30 passed`
- `tests/test_muf_s1_price_path.py` + `tests/test_muf_s1_path_schemas.py`: `89 passed`
- `tests/test_muf_s0_*.py`: `67 passed`
- Full `trading_project` regression suite: `1308 passed`
- S0 AST guards (`scan_private_imports`, `scan_prohibited_implementations`, `scan_market_shape_implementations`): `() / () / ()`
- Independent `/tmp` mutation battery: `8/8 KILLED`
