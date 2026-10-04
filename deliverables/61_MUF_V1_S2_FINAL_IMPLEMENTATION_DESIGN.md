# MUF V1 — S2 FINAL IMPLEMENTATION DESIGN
## DETECTOR WITNESS ADAPTER ONLY — DESIGN ONLY

- Task: DESIGN S2 ONLY (`MUF V1 S2 — Detector Witness Adapter`).
- Official baseline:
  - `MANIFEST.sha256`: `f6d0d00446c70a997d357db66a82db6237a3254fdcea3a8674a7670d5d58e3a6` (`202/202 OK`, `0 stale`, `0 missing`)
  - `MUF V1 S0`: `CLOSED` (`67/67 passed`)
  - `MUF V1 S1`: `CLOSED` (`89/89 passed`)
  - Full `trading_project` suite: `1228/1228 passed`
  - External `field_runner` suite (after Deliverable 60 re-pin): `36/36 passed` (`test_runner_guards.py` = `a89057f6466342c1e8d9b45fcf2a6033ed50219c1c7c57ec1c8cde18b398638e`)
- Status: `DESIGN ONLY — PENDING OWNER AUTHORIZATION FOR S2 BUILD`

---

## 0 — CORE PRINCIPLE & AUTHORITY BOUNDARY (D1-4 / D2-1 / D2-22)

```text
DETECTOR WITNESS  ≠  AUTHORITATIVE TURNING POINT  ≠  FACTUAL WAVE  ≠  MARKET IMPORTANCE
```

Per the governing MUF design chain (`AP-1` ← `Audit 41` ← `Correction-1` ← `D2` ← `D1` ← `37` ← `36`):
1. **S2 is a Detector Witness Adapter ONLY (`D1-4`, `D1-21`, `D2-22`).**
2. Closed Module `2.1A` (`CausalAdaptiveSwingDetector`) is consumed strictly through its **public API** (`analyze(df, high_col=..., low_col=...)`) with a frozen local schema mirror and dynamic output-column verification (zero private `_OUTPUT_COLUMNS` import).
3. **No Authority Laundering (`I-PAUTH-1..4`):**
   - A `DetectorWitnessRecord` proves ONLY: *"Closed engine `MODULE_2_1A_V1_1` produced output $X$ at causal availability key $K_a$ (with origin key $K_o \le K_a$) under witness input/policy identity $Y$."*
   - It does **NOT** grant authority to construct `AuthoritativeTurningPointRecord`, ` AuthoritativeTurningPointReference`, `WaveProcessIdentityBasis`, `WaveIdentityRecord`, or any factual MUF hierarchy.
   - Because `PolicyArtifact` infrastructure belongs to `S3` and `DEVELOPMENT_FIT` calibration belongs to `S4` (behind `G0`), **zero `AuthoritativeTurningPointRecord` instances may be created at S2**. Any attempt to promote a witness record to an authoritative MUF turning point without a valid MUF `PolicyArtifact` authority fails closed with deterministic code `S2_AUTHORITY_MISSING_NO_PROMOTION` (`SchemaViolation`).
4. **Anti-Fragility & Non-Choking Foundation:**
   - Even when `confirmation_policy is None` (`TypedState.NOT_CONFIGURED` / evidence-only mode), `2.1A` produces continuous, causal per-bar candidate reversal evidence (`candidate_side`, `candidate_origin_position`, `candidate_price`, `candidate_reversal_distance`, `candidate_reversal_fraction`, `candidate_reversal_evidence`, `candidate_continuation_history_count`).
   - `S2` preserves this continuous factual witness stream without inventing a threshold or choking the stream when binary confirmation is unconfigured.

---

## 1 — INPUT AUTHORITY & PASSTHROUGH INTEGRITY

### 1.1 Consumed public contracts
- **S0 (`contracts.py`, `identity.py`, `availability.py`, `records.py`):**
  - `SchemaIdentity`, `SchemaViolation`, `IdentityViolation`, `InformationKeyViolation`, `IncomparableInformationKeys`, `PrematureAvailability`, `IllegalCausalReference`, `TypedState`
  - `ArtifactIdentitySchema`, `canonical_artifact_identity`, `verify_canonical_identity`, `AuthoritativeTurningPointReference`
  - `InformationAxis`, `require_visible_at`
  - `PublishedRecord`, `freeze_payload`, `payload_canonical_view`
- **S1 (`price_path.py`):**
  - `PublishedOhlcBarFact`, `key_axis`, `key_serialization`, `EXACT`, `UNAVAILABLE`, `MetricResult`, `exact_metric`, `unavailable_metric`, `metric_payload`
- **Closed Module `2.1A` (`trading_system.structure.swing_detector`):**
  - Public symbols only: `CausalAdaptiveSwingDetector`, `SwingConfirmationPolicy`, `EmpiricalConfirmationPolicy`, `SwingDetectorError`, `SwingConfigError`, `SwingDataError`

### 1.2 Sealed OHLC sequence & passthrough verification
- Input to `S2` is a non-empty causal tuple of `PublishedOhlcBarFact` items `(B_0, B_1, ..., B_{n-1})` sharing one `timeline_id`, one `InformationAxis`, one `source_identity`, and one `dataset_identity`, with strictly increasing `availability_key` (`B_0.availability_key < B_1.availability_key < ... < B_{n-1}.availability_key`), all at `InformationPhase.COMPLETED_ROW_AVAILABLE`.
- Duplicate or out-of-order observation keys fail closed (`S2_DUPLICATE_OBSERVATION_KEY`, `S2_OUT_OF_ORDER_OBSERVATION`) without silent sorting.
- Before calling `detector.analyze(df)`, `S2` constructs an isolated two-column `DataFrame({"high": ..., "low": ...})` with `RangeIndex(0, n)`.
- After `detector.analyze(df)` returns `out`:
  1. **Dynamic Schema Mirror Gate (`S2_DETECTOR_SCHEMA_MISMATCH`):** `tuple(out.columns)` must equal `("high", "low") + S2_FROZEN_2_1A_COLUMNS` exactly (order, names, count). Any added, removed, or reordered column fails closed.
  2. **Passthrough Integrity Gate (`S2_PASSTHROUGH_TAMPERED`):** `out["high"]` and `out["low"]` must be bitwise-identical (`uint64` view) to the sealed input `high_price` and `low_price` arrays from `PublishedOhlcBarFact`.

---

## 2 — WITNESS POLICY MODES (NO MUF AUTHORITY AT S2)

`S2` classifies the detector's policy configuration into one of two witness-only modes:
1. `WITNESS_MODE_EVIDENCE_ONLY = "EVIDENCE_ONLY_NOT_CONFIGURED"`
   - When `confirmation_policy is None`.
   - `policy_witness_ref = TypedState.NOT_CONFIGURED`.
   - Binary confirmation columns (`swing_high_confirmed`, `swing_low_confirmed`) must be `False` on every row (if a rogue detector ever emits `True` in evidence-only mode, `S2` fails closed with `S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY`).
2. `WITNESS_MODE_EXTERNAL_POLICY = "EXTERNAL_POLICY_WITNESS_ONLY"`
   - When an explicit `SwingConfirmationPolicy` instance is supplied together with a caller-declared `external_policy_witness_id: str`.
   - Crucially (`D1-4` Case B): this is an **external/legacy witness only**, NOT a `MUF_POLICY_ARTIFACT`.
   - Every emitted record carries `muf_authority_policy_hash = TypedState.NOT_CONFIGURED` and `authority_status = "WITNESS_ONLY_NOT_MUF_AUTHORITATIVE"`.

---

## 3 — S2 IMMUTABLE RECORD SCHEMAS

All S2 records are emitted as immutable S0 `PublishedRecord` objects under `S2_SCHEMA_IDENTITY = SchemaIdentity("MUF_S2_DETECTOR_WITNESS", "V1")`.

### 3.1 `S2_CANDIDATE_WITNESS_RECORD` (emitted per accepted bar `i`)
- **Identity schema (`MUF_S2_CANDIDATE_WITNESS`):**
  - Identity-defining fields: `("timeline_id", "availability_key", "engine_version", "witness_mode", "policy_witness_ref")`
  - Proof/non-identity fields: `("dataset_identity", "bar_record_ref")`
- **Causal timing (`Origin ≠ Availability`):**
  - `availability_key = B_i.availability_key` (`COMPLETED_ROW_AVAILABLE` at bar `i`).
  - When `candidate_side in ("HIGH", "LOW")`, `candidate_origin_position = int(row["candidate_origin_position"])` must satisfy `0 <= candidate_origin_position <= i`, and `candidate_origin_key = B_{candidate_origin_position}.availability_key`. `require_visible_at(fact_key=candidate_origin_key, at_key=availability_key)` is enforced.
  - When `candidate_side == "UNDECIDED"`, `candidate_origin_key = TypedState.NOT_APPLICABLE` and `candidate_price = TypedState.UNDEFINED`.
- **Non-finite float normalization (S0 frozen-payload domain compliance):**
  - In `2.1A`, unassessed or bootstrap fields (`candidate_reversal_distance`, `candidate_reversal_fraction`, `candidate_reversal_evidence`, `candidate_confirmation_threshold`, `swing_high_reversal_evidence`, `swing_low_reversal_evidence`) are `NaN`.
  - In `S2`, every floating-point witness value is normalized into a typed S1 `MetricResult` payload: finite float → `exact_metric(val)`, `NaN` → `unavailable_metric(reason, TypedState.UNDEFINED)` (e.g., `S2_CANDIDATE_UNASSESSED_ON_EXTENSION_OR_BOOTSTRAP`, `S2_POLICY_NOT_CONFIGURED_OR_EMPTY_HISTORY`). No raw `NaN` or `inf` enters semantic metric payloads.

### 3.2 `S2_SWING_EVENT_WITNESS_RECORD` (emitted ONLY on confirmation bar `i` when confirmed under `EXTERNAL_POLICY_WITNESS_ONLY`)
- **Identity schema (`MUF_S2_SWING_EVENT_WITNESS`):**
  - Identity-defining fields: `("timeline_id", "origin_key", "availability_key", "extrema_kind", "engine_version", "policy_witness_ref")`
- **Strict Origin vs Availability invariants (`I-T3-1`, `D1-4`):**
  - `origin_position = int(row["swing_origin_position"])`
  - `confirmation_position = int(row["swing_confirmation_position"])`
  - Must satisfy `confirmation_position == i` and `0 <= origin_position < confirmation_position` (in `2.1A`, an extension bar cannot confirm its own reversal; therefore `origin_position < i` strictly). If `origin_position >= i`, fail closed (`S2_ILLEGAL_SWING_ORIGIN_TIMING`).
  - `origin_key = B_{origin_position}.availability_key`
  - `availability_key = B_i.availability_key`
  - **Never visible before `availability_key`**: at any query key $K < B_i.\text{availability\_key}$, this event witness is invisible (`require_visible_at`).
  - **Explicit non-authority stamp:**
    - `authority_status = "WITNESS_ONLY_NOT_MUF_AUTHORITATIVE"`
    - `muf_authority_policy_hash = TypedState.NOT_CONFIGURED`

### 3.3 Promotion Gate & Factual Query Firewall (`I-PAUTH-1..4`)
- `promote_witness_to_authoritative_turning_point(witness_record, *, muf_policy_artifact=TypedState.NOT_CONFIGURED)`:
  - At `S2`, `PolicyArtifact` infrastructure does not exist yet (`S3`).
  - Any call with `TypedState.NOT_CONFIGURED`, `None`, or any object raises `SchemaViolation("S2_AUTHORITY_MISSING_NO_PROMOTION: PolicyArtifact infrastructure is not configured at S2; witness cannot be promoted to AuthoritativeTurningPointRecord")`.
- `query_witness_surface_as_of(bundle, at_key)` vs `query_authoritative_turning_points_as_of(bundle, at_key)`:
  - `query_witness_surface_as_of(bundle, at_key)` returns only `DetectorWitnessRecord` items whose `availability_key <= at_key` (enforced via `require_visible_at`), preserving byte-identical prefix invariance under future bar appends.
  - `query_authoritative_turning_points_as_of(bundle, at_key)` always returns an empty tuple `()` when only witness records exist (`I-PAUTH-1`: factual queries exclude witness records).

---

## 4 — AST GUARD & COMPLEXITY COMPLIANCE

1. **S0 AST Guard Compliance (`scan_private_imports`, `scan_prohibited_implementations`, `scan_market_shape_implementations`):**
   - Zero private imports (`_OUTPUT_COLUMNS` is mirrored locally as `S2_FROZEN_2_1A_COLUMNS`, never imported).
   - Zero prohibited implementation terms (`model`, `strategy`, `pnl`, `signal`, `trade`, `execute`) in any class/function/variable name.
   - Zero prohibited market-shape terms (`threshold`, `window`, `horizon`, `quantile`, `lookback`, `period`, `interval`) in any class/function/variable name.
   - Only `0` and `1` appear as numeric literals in production code.
2. **Complexity (`I-P-1`):**
   - `2.1A` execution + single-pass witness materialization: $O(n)$ in number of bars (with $O(\log n)$ per episode push inside `CausalPercentileTracker` when an external policy is active, and $O(1)$ per bar in evidence-only mode).
   - As-of prefix query: $O(n)$ scan with `require_visible_at` and byte-identical prefix hash before/after future append.

---

## 5 — PLANNED FILES & ADVERSARIAL TEST BATTERY (FOR S2 BUILD)

- Production file (1):
  - `src/trading_system/market_understanding/detector_witness.py`
- Test file (1):
  - `tests/test_muf_s2_detector_witness.py`
- Mandatory adversarial tests (minimum 25 tests + mutation proofs):
  1. Evidence-only mode (`policy=None`) emits per-bar candidate witnesses with `TypedState.NOT_CONFIGURED` policy ref and zero swing event witnesses.
  2. External witness policy mode emits both candidate witnesses and confirmed swing event witnesses stamped `WITNESS_ONLY_NOT_MUF_AUTHORITATIVE`.
  3. Attack 1 (`D1 Annex D #1`): witness record never appears in `query_authoritative_turning_points_as_of` and cannot construct `AuthoritativeTurningPointReference` or `WaveProcessIdentityBasis`.
  4. Attack 2 (`D1 Annex D #2`): `promote_witness_to_authoritative_turning_point` fails closed with `S2_AUTHORITY_MISSING_NO_PROMOTION` for `NOT_CONFIGURED`, `None`, or forged policy objects.
  5. Origin $\ne$ Availability: swing event witness with `origin_position = 1` and `confirmation_position = 2` has `origin_key = key(1)` and `availability_key = key(2)`, is invisible at `at_key = key(1)`, and visible at `at_key = key(2)`.
  6. Prefix truncation / future append invariance (`I-IMM-3`): `query_witness_surface_as_of(T)` on a 10-bar stream vs a 20-bar extended stream produces byte-identical records and identical canonical hashes at every $T \le 10$.
  7. Duplicate observation key rejected (`S2_DUPLICATE_OBSERVATION_KEY`).
  8. Out-of-order observation key rejected (`S2_OUT_OF_ORDER_OBSERVATION`) — no silent sorting.
  9. Cross-timeline / cross-axis / cross-dataset / cross-source observation rejected fail-closed.
  10. `BAR_PRE_CLOSE` query at bar $T$ rejected (`IllegalCausalReference`) for completed-bar witness at bar $T$.
  11. Dynamic schema mirror gate: rogue detector adding/removing/renaming a column fails closed (`S2_DETECTOR_SCHEMA_MISMATCH`).
  12. Passthrough integrity gate: rogue detector mutating `high` or `low` fails closed (`S2_PASSTHROUGH_TAMPERED`).
  13. Rogue detector claiming confirmation in evidence-only mode fails closed (`S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY`).
  14. Rogue detector claiming `swing_origin_position >= swing_confirmation_position` fails closed (`S2_ILLEGAL_SWING_ORIGIN_TIMING`).
  15. Equal highs / equal lows retain earlier origin in `2.1A` candidate witness without epsilon.
  16. Outside bar (`extends_high` and `extends_low` from undecided) remains `UNDECIDED` and confirms nothing (intrabar ambiguity respected).
  17. Proof-noise independence: changing `dataset_identity` or `bar_record_ref` does not change `record_identity` of candidate or event witness records (`I-IDB-1/2`).
  18. Deep immutability: attempting to mutate any published witness record or its nested `content` raises `ImmutabilityViolation`.
  19. S0 AST guards (`scan_private_imports`, `scan_prohibited_implementations`, `scan_market_shape_implementations`) all return `()` on `detector_witness.py`.
  20. Mutation proofs: disabling schema check, passthrough check, promotion gate, or visibility check causes the corresponding adversarial test to fail.

---

## 6 — CERTIFICATION BOUNDARY

`MUF V1 S2` certifies **ONLY** the causal Detector Witness Adapter over Closed Module `2.1A`, preserving `Origin ≠ Availability`, `WITNESS_ONLY_NOT_MUF_AUTHORITATIVE` separation, fail-closed promotion blocking (`I-PAUTH-1..4`), and byte-identical past under future append.
It does **NOT** certify: authoritative turning points, `PolicyArtifact` calibration, wave identity, wave hierarchy, $\alpha/\beta/\gamma/\delta$ representations, predictive support, statistical independence (`RESEARCH-DEBT-024` remains OPEN), edge, profitability, Model, Strategy, Signal, or PnL.
