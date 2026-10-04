# MUF V1 — S3 FINAL IMPLEMENTATION DESIGN
## RESEARCH-GOVERNANCE INFRASTRUCTURE & GATE G0 — DESIGN + BUILD SPECIFICATION

- Task: `MUF V1 S3 — Research-Governance Infrastructure & Gate G0` (`policy_governance.py`).
- Upstream closed baseline:
  - `MUF V1 S0`: `CLOSED` (`67/67 passed`)
  - `MUF V1 S1`: `CLOSED` (`89/89 passed`)
  - `MUF V1 S2`: `CLOSED` (`30/30 passed`, `8/8 mutations killed`)
  - `MANIFEST.sha256`: `4a002858044a5b3877d807f8304deb67930345109882a3a80be4cb35e9f89a13` (`206/206 OK`)

---

## 0 — CORE ARCHITECTURAL ROLE OF S3 & GATE G0 (D1-1..4, D1-16, D2-1..7, D2-18, D2-22)

`MUF V1 S3` builds the **Research-Governance & Anti-Overfitting Infrastructure** that sits between the unpromoted Detector Witness layer (`S2`) and any future development calibration (`S4`):

1. **`ObjectiveArtifact` (`D1-1`, `D2-3`, `I-OA-1..5`):**
   - Formalizes what question is being asked (`DETECTION_VALIDITY`, `REPRESENTATION_DIAGNOSTIC`, `INFORMATION_OBJECTIVE`; `ECONOMIC_OBJECTIVE` is out-of-scope and rejected fail-closed).
   - Enforces `I-OA-1..5` and `D1-17`: `INFORMATION_OBJECTIVE` requires non-empty `estimand_refs`; structural/diagnostic objectives forbid `estimand_refs`.
   - Preserves `QUALIFICATION_OBJECTIVE_DEFAULT = TypedState.UNDEFINED` (`I-OA-5`: no invented objective in S3).

2. **`DatasetIdentityArtifact`, `ExposureAncestry`, and `DatasetRoleArtifact` (`D1-2`, `D2-6`, `D2-7`, `I-DR-1..5`, `I-DATA-1..5`, `I-RES-1..2`):**
   - `DatasetIdentityArtifact` binds `dataset_id` to `content_hash`, `source_identity`, `timeline_id`, `axis`, `start_key`, `end_key`, `transformation_spec_hash`, `parent_dataset_ids`, `creation_code_hash`, and `semantic_schema_hash`.
   - `verify_dataset_independence_and_ancestry` detects:
     - Undeclared shared content hash (`Attack 32`: hiding ancestry of an exposed parent dataset),
     - Transitive exposure inheritance along `parent_dataset_ids` (`Attack 31`: re-hashing/transforming exposed final data and claiming it is fresh),
     - Temporal/source overlap on the same `(source_identity, timeline_id)` (`Attack 33`, `Attack 47`).
   - `DatasetRoleArtifact` enforces:
     - Roles: `DEVELOPMENT_FIT`, `DEVELOPMENT_SELECTION`, `FINAL_EVALUATION_LOCKED`.
     - Reservation vs opening (`D2-6`): `FINAL_EVALUATION_LOCKED` starts at `reservation_status = "FINAL_DATA_RESERVED"` and `exposure_state = "UNEXPOSED"`.
     - Append-only exposure transition (`record_dataset_exposure`): `role_assignment_key <= exposure_key` (`I-DR-1`, `Attack 46`: role cannot be reassigned after exposure).

3. **`FoldProtocolArtifact` & Walk-Forward Firewall (`D1-2`, `D2-18`, `I-WF-1..3`, `Attack 47`):**
   - Represents declared walk-forward folds `(fit_dataset_id, selection_dataset_id)` with causal ordering (`fit_end_key < selection_start_key`), or `TypedState.NOT_CONFIGURED` until numerical fold boundaries are authorized by the Owner.
   - Fails closed (`S3_FINAL_DATA_LEAKED_INTO_WALK_FORWARD`) if any fold references or temporally overlaps a `FINAL_EVALUATION_LOCKED` dataset or any descendant of a final dataset.

4. **`HumanReviewRecord` & Review Firewall (`D1-3`, `D2-10`, `I-HR-1..2`, `Attack 12`):**
   - Records every human/chart/reality review with `review_information_key` (`InformationKey`), `dataset_id`, `dataset_role`, `review_kind`, `artifacts_viewed`, `charts_viewed`, `observations`, `requested_changes`, and `change_influence`.
   - Contradiction check: non-empty `requested_changes` with `change_influence != "DESIGN_INFLUENCING"` fails closed (`S3_CONTRADICTORY_REVIEW_INFLUENCE`).
   - Automatic contamination tripwire (`I-HR-2`, `Attack 12`): applying a `HumanReviewRecord` with `requested_changes` or `DESIGN_INFLUENCING` to a `FINAL_EVALUATION_LOCKED` dataset transitions its `DatasetRoleArtifact` to `EXPOSED_INVALID_FOR_FINAL_SELECTION`, permanently blocking it from certifying that artifact lineage.

5. **`RepresentationExperimentRecord` & Append-Only `ExperimentRegistry` (`D1-16`, `I-ER-1..5`, `Attacks 13 & 14`):**
   - Enforces preregistration before execution/completion/failure (`preregistration_key <= event_key`).
   - Append-only: failed trials (`FAILED`) and superseded trials (`SUPERSEDED`) are permanently retained and cannot be deleted (`Attack 13`).
   - Semantic immutability per `experiment_id`: attempting to re-register an existing `experiment_id` with a different `objective_artifact_hash`, `representation_spec_hash`, `policy_artifact_hashes`, or `dataset_identities_by_role` fails closed (`S3_EXPERIMENT_IDENTITY_COLLISION`, `Attack 14`).

6. **`PolicyArtifact` Infrastructure & `AuthoritativeTurningPointRecord` Promotion (`D1-4`, `D2-1`, `I-PAUTH-1..4`, `Attack 25`):**
   - `PolicyArtifact` binds `authority_kind`, `target_engine_identity`, `detector_policy_witness_ref` (`DetectorPolicyWitnessSpec.spec_identity`), `scope_timeline_id`, `scope_axis`, `scope_representation_id`, `calibration_provenance_kind`, `objective_artifact_hash`, `fit_dataset_role_hash`, `reproduction_recipe_hash`, `effective_from_key`, and `owner_authorization_ref`.
   - `promote_swing_witness_with_policy_artifact` promotes an S2 `SwingEventWitnessRecord` into a new immutable `AuthoritativeTurningPointRecord` (`record_type = TURNING_POINT_RECORD_TYPE`) ONLY when:
     - `policy_artifact` is a valid `PolicyArtifact`,
     - timeline, axis, and `detector_policy_witness_ref` match (`PolicyScopeMismatch` / `S3_POLICY_SCOPE_MISMATCH` otherwise),
     - `policy_artifact.effective_from_key <= witness.availability_key` (`PrematureAvailability` otherwise),
     - preserving `origin_key < availability_key` without mutating the S2 witness record.
   - Two `PolicyArtifact` instances with different `policy_hash` values promoting the same underlying price origin produce distinct `AuthoritativeTurningPointRecord` identities and distinct `WaveProcessIdentityBasis` hashes (`I-WPI-1/4`, `Attack 25`).

7. **Authority Gate `G0` (`evaluate_g0_calibration_gate` — `D1-21`, `D2-22`):**
   - Blocks any `S4` calibration (`SelectionBlockedError`) unless a valid `ObjectiveArtifact`, an uncontaminated `DEVELOPMENT_FIT` `DatasetRoleArtifact`, a verified `DatasetIdentityArtifact` with zero final-data ancestry/overlap, a preregistered `RepresentationExperimentRecord`, and an explicit `owner_fit_authorization_ref` are all present and coherent.

---

## 1 — PLANNED FILES

- Production file (1):
  - `src/trading_system/market_understanding/policy_governance.py`
- Test file (1):
  - `tests/test_muf_s3_policy_governance.py`
