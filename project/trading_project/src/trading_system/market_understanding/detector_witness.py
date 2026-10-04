"""MUF V1 S2: Detector Witness Adapter over Closed Module 2.1A.

Adapts the public output of ``CausalAdaptiveSwingDetector`` (Closed Module 2.1A
V1.1) into immutable MUF witness records bound to causal availability keys
(``InformationPhase.COMPLETED_ROW_AVAILABLE``).

Certification & authority boundary (D1-4, D1-21, D2-1, D2-22, I-PAUTH-1..4):
- Detector output is recorded strictly as ``WITNESS_ONLY_NOT_MUF_AUTHORITATIVE``.
- ``origin_key`` (when the candidate extreme formed) is strictly separated from
  ``availability_key`` (when the observation or confirmation became causally
  known at bar close). No event witness is ever visible before its
  ``availability_key``.
- At S2, ``PolicyArtifact`` infrastructure is ``TypedState.NOT_CONFIGURED`` (S3/S4).
  Zero ``AuthoritativeTurningPointRecord`` or factual wave identities may be
  promoted or emitted at S2.
"""
from dataclasses import dataclass
import math
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from trading_system.market_understanding.availability import (
    InformationAxis,
    require_visible_at,
)
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    AuthoritativeTurningPointReference,
    canonical_artifact_identity,
)
from trading_system.market_understanding.price_path import (
    EXACT,
    UNAVAILABLE,
    MetricResult,
    PublishedOhlcBarFact,
    exact_metric,
    key_axis,
    key_serialization,
    metric_payload,
    unavailable_metric,
)
from trading_system.market_understanding.records import (
    ImmutableRecord,
    PublishedRecord,
    freeze_payload,
    payload_canonical_view,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationKeyError,
    InformationPhase,
)
from trading_system.structure.swing_detector import (
    CausalAdaptiveSwingDetector,
    EmpiricalConfirmationPolicy,
    SwingConfirmationPolicy,
    SwingDetectorError,
)


S2_SCHEMA_IDENTITY = SchemaIdentity("MUF_S2_DETECTOR_WITNESS", "V1")
S2_ADAPTER_ENGINE_IDENTITY = SchemaIdentity(
    "MODULE_2_1A_CAUSAL_ADAPTIVE_SWING_DETECTOR",
    "V1_1",
)

S2_POLICY_WITNESS_SPEC_RECORD_TYPE = "S2_POLICY_WITNESS_SPEC_RECORD"
S2_CANDIDATE_WITNESS_RECORD_TYPE = "S2_CANDIDATE_WITNESS_RECORD"
S2_SWING_EVENT_WITNESS_RECORD_TYPE = "S2_SWING_EVENT_WITNESS_RECORD"

WITNESS_MODE_EVIDENCE_ONLY = "EVIDENCE_ONLY_NOT_CONFIGURED"
WITNESS_MODE_EXTERNAL_POLICY = "EXTERNAL_POLICY_WITNESS_ONLY"
AUTHORITY_STATUS_WITNESS_ONLY = "WITNESS_ONLY_NOT_MUF_AUTHORITATIVE"

CANDIDATE_SIDE_UNDECIDED = "UNDECIDED"
CANDIDATE_SIDE_HIGH = "HIGH"
CANDIDATE_SIDE_LOW = "LOW"
LEGAL_CANDIDATE_SIDES = frozenset(
    {
        CANDIDATE_SIDE_UNDECIDED,
        CANDIDATE_SIDE_HIGH,
        CANDIDATE_SIDE_LOW,
    }
)
LEGAL_EXTREMA_KINDS = frozenset({CANDIDATE_SIDE_HIGH, CANDIDATE_SIDE_LOW})

# Deterministic S2 failure codes
S2_EMPTY_OBSERVATION_SEQUENCE = "S2_EMPTY_OBSERVATION_SEQUENCE"
S2_INVALID_BAR_FACT = "S2_INVALID_BAR_FACT"
S2_TIMELINE_MISMATCH = "S2_TIMELINE_MISMATCH"
S2_AXIS_MISMATCH = "S2_AXIS_MISMATCH"
S2_SOURCE_MISMATCH = "S2_SOURCE_MISMATCH"
S2_DATASET_MISMATCH = "S2_DATASET_MISMATCH"
S2_DUPLICATE_OBSERVATION_KEY = "S2_DUPLICATE_OBSERVATION_KEY"
S2_OUT_OF_ORDER_OBSERVATION = "S2_OUT_OF_ORDER_OBSERVATION"
S2_DETECTOR_SCHEMA_MISMATCH = "S2_DETECTOR_SCHEMA_MISMATCH"
S2_PASSTHROUGH_TAMPERED = "S2_PASSTHROUGH_TAMPERED"
S2_INVALID_WITNESS_POLICY = "S2_INVALID_WITNESS_POLICY"
S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY = "S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY"
S2_CONTRADICTORY_SWING_CONFIRMATION = "S2_CONTRADICTORY_SWING_CONFIRMATION"
S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS = "S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS"
S2_CONFIRMATION_POSITION_MISMATCH = "S2_CONFIRMATION_POSITION_MISMATCH"
S2_ILLEGAL_SWING_ORIGIN_TIMING = "S2_ILLEGAL_SWING_ORIGIN_TIMING"
S2_INVALID_CANDIDATE_SIDE = "S2_INVALID_CANDIDATE_SIDE"
S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING = "S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING"
S2_INVALID_CANDIDATE_PRICE_STATE = "S2_INVALID_CANDIDATE_PRICE_STATE"
S2_NONFINITE_CONFIRMED_SWING_METRIC = "S2_NONFINITE_CONFIRMED_SWING_METRIC"
S2_AUTHORITY_MISSING_NO_PROMOTION = "S2_AUTHORITY_MISSING_NO_PROMOTION"

# Unavailable-metric reason tokens
REASON_CANDIDATE_UNDECIDED = "S2_CANDIDATE_UNDECIDED"
REASON_CANDIDATE_UNASSESSED = "S2_CANDIDATE_UNASSESSED_ON_EXTENSION_OR_BOOTSTRAP"
REASON_POLICY_GATE_INACTIVE = "S2_POLICY_NOT_CONFIGURED_OR_INSUFFICIENT_HISTORY"
REASON_SIDE_NOT_EVALUATED = "S2_SIDE_REVERSAL_EVIDENCE_NOT_EVALUATED_ON_BAR"
REASON_NO_PRIOR_CONFIRMED_SWINGS = "S2_NO_PRIOR_CONFIRMED_SWINGS_IN_HISTORY"

# Frozen local mirror of Module 2.1A public derived output columns (24 columns).
# Never imported from private _OUTPUT_COLUMNS; verified dynamically at runtime.
S2_FROZEN_2_1A_COLUMNS: Tuple[str, ...] = (
    "candidate_side",
    "candidate_origin_position",
    "candidate_price",
    "candidate_reversal_distance",
    "candidate_reversal_fraction",
    "candidate_reversal_evidence",
    "candidate_continuation_history_count",
    "candidate_confirmed_history_count",
    "candidate_confirmation_threshold",
    "swing_high_reversal_evidence",
    "swing_low_reversal_evidence",
    "swing_high_confirmed",
    "swing_low_confirmed",
    "swing_origin_position",
    "swing_price",
    "swing_confirmation_position",
    "swing_confirmation_price",
    "swing_reversal_distance",
    "swing_reversal_fraction",
    "swing_reversal_evidence",
    "swing_continuation_history_count",
    "swing_confirmed_history_percentile",
    "swing_confirmed_history_count",
    "swing_confirmation_threshold",
)

S2_INPUT_PASSTHROUGH_COLUMNS: Tuple[str, ...] = ("high", "low")
S2_EXPECTED_ANALYZE_COLUMNS: Tuple[str, ...] = (
    S2_INPUT_PASSTHROUGH_COLUMNS + S2_FROZEN_2_1A_COLUMNS
)

POLICY_WITNESS_SPEC_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S2_POLICY_WITNESS_SPEC",
    schema_identity=S2_SCHEMA_IDENTITY,
    identity_defining_fields=("policy_class_name", "policy_parameters", "authority_scope"),
    proof_fields=("caller_note",),
)

CANDIDATE_WITNESS_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S2_CANDIDATE_WITNESS",
    schema_identity=S2_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "availability_key",
        "engine_identity",
        "witness_mode",
        "policy_witness_ref",
    ),
    proof_fields=(
        "dataset_identity",
        "source_identity",
        "bar_record_ref",
    ),
)

SWING_EVENT_WITNESS_IDENTITY_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S2_SWING_EVENT_WITNESS",
    schema_identity=S2_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "origin_key",
        "availability_key",
        "extrema_kind",
        "engine_identity",
        "policy_witness_ref",
    ),
    proof_fields=(
        "dataset_identity",
        "source_identity",
        "origin_bar_record_ref",
        "confirmation_bar_record_ref",
    ),
)


def _is_finite_number(val: Any) -> bool:
    if isinstance(val, bool) or not isinstance(val, (int, float, np.number)):
        return False
    return math.isfinite(float(val))


def _normalize_optional_metric(val: Any, unavailable_reason: str) -> MetricResult:
    if isinstance(val, (int, float, np.number)) and not isinstance(val, bool):
        as_float = float(val)
        if math.isfinite(as_float):
            if as_float == 0.0:
                as_float = 0.0
            return exact_metric(as_float)
        if math.isnan(as_float):
            return unavailable_metric(unavailable_reason, TypedState.UNDEFINED)
    raise SchemaViolation(
        f"{S2_NONFINITE_CONFIRMED_SWING_METRIC}: unexpected metric value {val!r}"
    )


def _require_finite_metric(val: Any, field_name: str) -> MetricResult:
    if isinstance(val, (int, float, np.number)) and not isinstance(val, bool):
        as_float = float(val)
        if math.isfinite(as_float):
            if as_float == 0.0:
                as_float = 0.0
            return exact_metric(as_float)
    raise SchemaViolation(
        f"{S2_NONFINITE_CONFIRMED_SWING_METRIC}: field {field_name!r} must be finite, got {val!r}"
    )


def _canonicalize_policy_param_value(val: Any) -> Any:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (float, np.floating)):
        as_float = float(val)
        if not math.isfinite(as_float):
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: non-finite float in policy parameters: {val!r}"
            )
        return 0.0 if as_float == 0.0 else as_float
    if isinstance(val, str):
        return val
    if isinstance(val, TypedState):
        return val
    if isinstance(val, (SchemaIdentity, InformationKey)):
        return val
    if isinstance(val, (list, tuple)):
        return tuple(_canonicalize_policy_param_value(item) for item in val)
    if isinstance(val, Mapping):
        if len(val) == 0:
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: policy parameter mapping cannot be empty"
            )
        out: dict[str, Any] = {}
        for k, v in val.items():
            if not isinstance(k, str) or not k.strip():
                raise SchemaViolation(
                    f"{S2_INVALID_WITNESS_POLICY}: policy parameter key must be a non-empty string"
                )
            out[k] = _canonicalize_policy_param_value(v)
        return out
    raise SchemaViolation(
        f"{S2_INVALID_WITNESS_POLICY}: unsupported policy parameter value {val!r}"
    )


def _policy_param_identity_tree(val: Any) -> Any:
    if isinstance(val, TypedState):
        return val
    if isinstance(val, (SchemaIdentity, InformationKey)):
        return val
    if isinstance(val, bool):
        return f"bool:{val}"
    if isinstance(val, int):
        return f"int:{val}"
    if isinstance(val, float):
        norm = 0.0 if val == 0.0 else val
        return f"float:{norm!r}"
    if isinstance(val, str):
        return f"str:{val}"
    if isinstance(val, tuple):
        return {
            f"seq_{idx}": _policy_param_identity_tree(item)
            for idx, item in enumerate(val)
        }
    if isinstance(val, Mapping):
        return {str(k): _policy_param_identity_tree(val[k]) for k in val}
    raise SchemaViolation(
        f"{S2_INVALID_WITNESS_POLICY}: unsupported canonical identity value {val!r}"
    )


def _require_non_negative_int(val: Any, field_name: str) -> int:
    if isinstance(val, bool) or not isinstance(val, (int, np.integer)):
        raise SchemaViolation(f"field {field_name!r} must be an integer, got {val!r}")
    as_int = int(val)
    if as_int < 0:
        raise SchemaViolation(f"field {field_name!r} must be >= 0, got {as_int}")
    return as_int


@dataclass(frozen=True)
class DetectorPolicyWitnessSpec(ImmutableRecord):
    """Canonical witness-only specification of an external 2.1A confirmation policy.

    A ``DetectorPolicyWitnessSpec`` is NEVER a MUF ``PolicyArtifact`` (S3/S4).
    It records the exact parameter fingerprint of a ``SwingConfirmationPolicy``
    supplied to Module 2.1A so that witness records have deterministic,
    collision-free identity without authority laundering (I-PAUTH-1..4).
    """

    policy_class_name: str
    policy_parameters: Any
    authority_scope: str
    muf_policy_artifact_ref: TypedState
    caller_note: str
    spec_identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.policy_class_name, str) or not self.policy_class_name.strip():
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: policy_class_name must be a non-empty string"
            )
        if self.authority_scope != AUTHORITY_STATUS_WITNESS_ONLY:
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: authority_scope must be {AUTHORITY_STATUS_WITNESS_ONLY!r}"
            )
        if self.muf_policy_artifact_ref is not TypedState.NOT_CONFIGURED:
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: muf_policy_artifact_ref must be TypedState.NOT_CONFIGURED at S2"
            )
        if not isinstance(self.caller_note, str):
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: caller_note must be a string"
            )
        canonical_params = _canonicalize_policy_param_value(self.policy_parameters)
        if not isinstance(canonical_params, Mapping):
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: policy_parameters must be a non-empty mapping"
            )
        frozen_params = freeze_payload(canonical_params)
        object.__setattr__(self, "policy_parameters", frozen_params)
        param_identity_map = _policy_param_identity_tree(canonical_params)
        expected_id = canonical_artifact_identity(
            POLICY_WITNESS_SPEC_IDENTITY_SCHEMA,
            identity_payload={
                "policy_class_name": self.policy_class_name,
                "policy_parameters": param_identity_map,
                "authority_scope": self.authority_scope,
            },
            proof_payload={"caller_note": self.caller_note},
        )
        if self.spec_identity != expected_id:
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: spec_identity mismatch "
                f"({self.spec_identity!r} != {expected_id!r})"
            )

    @classmethod
    def from_policy(
        cls,
        policy: SwingConfirmationPolicy,
        *,
        custom_parameters: Optional[Mapping[str, Any]] = None,
        caller_note: str = "",
    ) -> "DetectorPolicyWitnessSpec":
        if not isinstance(policy, SwingConfirmationPolicy):
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: policy must be a SwingConfirmationPolicy instance, "
                f"got {type(policy).__name__}"
            )
        if isinstance(policy, EmpiricalConfirmationPolicy):
            if custom_parameters is not None:
                raise SchemaViolation(
                    f"{S2_INVALID_WITNESS_POLICY}: EmpiricalConfirmationPolicy parameters are "
                    "extracted canonically; custom_parameters must be None"
                )
            raw_params: Mapping[str, Any] = {
                "prior_confirmed_reversals": tuple(
                    float(x) for x in policy.prior_confirmed_reversals
                ),
                "prior_continuation_reversals": tuple(
                    float(x) for x in policy.prior_continuation_reversals
                ),
                "quantile": float(policy.quantile),
            }
        else:
            if not isinstance(custom_parameters, Mapping) or len(custom_parameters) == 0:
                raise SchemaViolation(
                    f"{S2_INVALID_WITNESS_POLICY}: custom SwingConfirmationPolicy subclass "
                    f"{type(policy).__name__!r} requires a non-empty custom_parameters mapping"
                )
            raw_params = dict(custom_parameters)

        canonical_params = _canonicalize_policy_param_value(raw_params)
        frozen_params = freeze_payload(canonical_params)
        param_identity_map = _policy_param_identity_tree(canonical_params)
        class_name = f"{type(policy).__module__}.{type(policy).__qualname__}"
        spec_id = canonical_artifact_identity(
            POLICY_WITNESS_SPEC_IDENTITY_SCHEMA,
            identity_payload={
                "policy_class_name": class_name,
                "policy_parameters": param_identity_map,
                "authority_scope": AUTHORITY_STATUS_WITNESS_ONLY,
            },
            proof_payload={"caller_note": caller_note},
        )
        return cls(
            policy_class_name=class_name,
            policy_parameters=frozen_params,
            authority_scope=AUTHORITY_STATUS_WITNESS_ONLY,
            muf_policy_artifact_ref=TypedState.NOT_CONFIGURED,
            caller_note=caller_note,
            spec_identity=spec_id,
        )


@dataclass(frozen=True)
class CandidateWitnessRecord(ImmutableRecord):
    """Per-bar causal witness of Module 2.1A candidate state at bar close."""

    timeline_id: str
    availability_key: InformationKey
    bar_position_in_stream: int
    candidate_side: str
    candidate_origin_position: Union[int, TypedState]
    candidate_origin_key: Union[InformationKey, TypedState]
    candidate_price: MetricResult
    candidate_reversal_distance: MetricResult
    candidate_reversal_fraction: MetricResult
    candidate_reversal_evidence: MetricResult
    candidate_continuation_history_count: int
    candidate_confirmed_history_count: int
    candidate_policy_gate_value: MetricResult
    swing_high_reversal_evidence: MetricResult
    swing_low_reversal_evidence: MetricResult
    confirmed_event_on_bar: bool
    witness_mode: str
    policy_witness_ref: Union[str, TypedState]
    authority_status: str
    muf_authority_policy_ref: TypedState
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        if self.candidate_side not in LEGAL_CANDIDATE_SIDES:
            raise SchemaViolation(
                f"{S2_INVALID_CANDIDATE_SIDE}: {self.candidate_side!r}"
            )
        if self.bar_position_in_stream < 0:
            raise SchemaViolation("bar_position_in_stream must be >= 0")
        if self.candidate_side == CANDIDATE_SIDE_UNDECIDED:
            if self.candidate_origin_position is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_SIDE}: UNDECIDED candidate must have "
                    "candidate_origin_position = TypedState.NOT_APPLICABLE"
                )
            if self.candidate_origin_key is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_SIDE}: UNDECIDED candidate must have "
                    "candidate_origin_key = TypedState.NOT_APPLICABLE"
                )
            if self.candidate_price.semantics != UNAVAILABLE:
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_PRICE_STATE}: UNDECIDED candidate_price must be UNAVAILABLE"
                )
        else:
            if isinstance(self.candidate_origin_position, bool) or not isinstance(
                self.candidate_origin_position, int
            ):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: active candidate must have integer origin_position"
                )
            if (
                self.candidate_origin_position < 0
                or self.candidate_origin_position > self.bar_position_in_stream
            ):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: origin_position "
                    f"{self.candidate_origin_position} outside [0, {self.bar_position_in_stream}]"
                )
            if not isinstance(self.candidate_origin_key, InformationKey):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: active candidate must bind an InformationKey"
                )
            require_visible_at(
                fact_key=self.candidate_origin_key,
                at_key=self.availability_key,
            )
            if self.candidate_price.semantics != EXACT:
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_PRICE_STATE}: active candidate_price must be EXACT"
                )
        if self.authority_status != AUTHORITY_STATUS_WITNESS_ONLY:
            raise SchemaViolation(
                f"authority_status must be {AUTHORITY_STATUS_WITNESS_ONLY!r}"
            )
        if self.muf_authority_policy_ref is not TypedState.NOT_CONFIGURED:
            raise SchemaViolation(
                "muf_authority_policy_ref must be TypedState.NOT_CONFIGURED at S2"
            )
        if self.witness_mode == WITNESS_MODE_EVIDENCE_ONLY:
            if self.policy_witness_ref is not TypedState.NOT_CONFIGURED:
                raise SchemaViolation(
                    "EVIDENCE_ONLY candidate witness requires policy_witness_ref = TypedState.NOT_CONFIGURED"
                )
            if self.confirmed_event_on_bar:
                raise SchemaViolation(
                    f"{S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY}: EVIDENCE_ONLY candidate "
                    "witness cannot have confirmed_event_on_bar=True"
                )
            expected_policy_ser = TypedState.NOT_CONFIGURED.value
        elif self.witness_mode == WITNESS_MODE_EXTERNAL_POLICY:
            if not isinstance(self.policy_witness_ref, str) or not self.policy_witness_ref.strip():
                raise SchemaViolation(
                    f"{S2_INVALID_WITNESS_POLICY}: EXTERNAL_POLICY candidate witness requires "
                    "non-empty string policy_witness_ref"
                )
            expected_policy_ser = self.policy_witness_ref
        else:
            raise SchemaViolation(f"unknown witness_mode: {self.witness_mode!r}")

        if not isinstance(self.published_record, PublishedRecord):
            raise SchemaViolation("published_record must be a PublishedRecord")
        if self.published_record.schema_identity != S2_SCHEMA_IDENTITY:
            raise SchemaViolation("published_record.schema_identity mismatch")
        if self.published_record.record_type != S2_CANDIDATE_WITNESS_RECORD_TYPE:
            raise SchemaViolation(
                f"published_record.record_type must be {S2_CANDIDATE_WITNESS_RECORD_TYPE!r}"
            )
        if self.published_record.timeline_id != self.timeline_id:
            raise SchemaViolation("published_record.timeline_id mismatch")
        if self.published_record.availability_key != self.availability_key:
            raise SchemaViolation("published_record.availability_key mismatch")

        engine_id_str = (
            f"{S2_ADAPTER_ENGINE_IDENTITY.schema_domain}:"
            f"{S2_ADAPTER_ENGINE_IDENTITY.schema_version}"
        )
        expected_id = canonical_artifact_identity(
            CANDIDATE_WITNESS_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "availability_key": "|".join(key_serialization(self.availability_key)),
                "engine_identity": engine_id_str,
                "witness_mode": self.witness_mode,
                "policy_witness_ref": expected_policy_ser,
            },
        )
        if self.published_record.record_identity != expected_id:
            raise SchemaViolation(
                "published_record.record_identity does not match canonical S2 candidate witness identity"
            )
        rec_content = self.published_record.content
        _require_non_negative_int(
            self.candidate_continuation_history_count,
            "candidate_continuation_history_count",
        )
        _require_non_negative_int(
            self.candidate_confirmed_history_count,
            "candidate_confirmed_history_count",
        )
        for metric_name, metric_obj in (
            ("candidate_price", self.candidate_price),
            ("candidate_reversal_distance", self.candidate_reversal_distance),
            ("candidate_reversal_fraction", self.candidate_reversal_fraction),
            ("candidate_reversal_evidence", self.candidate_reversal_evidence),
            ("candidate_policy_gate_value", self.candidate_policy_gate_value),
            ("swing_high_reversal_evidence", self.swing_high_reversal_evidence),
            ("swing_low_reversal_evidence", self.swing_low_reversal_evidence),
        ):
            if not isinstance(metric_obj, MetricResult):
                raise SchemaViolation(f"{metric_name} must be a MetricResult")
        if (
            rec_content["bar_position_in_stream"] != self.bar_position_in_stream
            or rec_content["candidate_side"] != self.candidate_side
            or rec_content["candidate_origin_position"] != self.candidate_origin_position
            or rec_content["candidate_origin_key"] != self.candidate_origin_key
            or rec_content["candidate_price"] != freeze_payload(metric_payload(self.candidate_price))
            or rec_content["candidate_reversal_distance"]
            != freeze_payload(metric_payload(self.candidate_reversal_distance))
            or rec_content["candidate_reversal_fraction"]
            != freeze_payload(metric_payload(self.candidate_reversal_fraction))
            or rec_content["candidate_reversal_evidence"]
            != freeze_payload(metric_payload(self.candidate_reversal_evidence))
            or rec_content["candidate_continuation_history_count"]
            != self.candidate_continuation_history_count
            or rec_content["candidate_confirmed_history_count"]
            != self.candidate_confirmed_history_count
            or rec_content["candidate_confirmation_threshold"]
            != freeze_payload(metric_payload(self.candidate_policy_gate_value))
            or rec_content["swing_high_reversal_evidence"]
            != freeze_payload(metric_payload(self.swing_high_reversal_evidence))
            or rec_content["swing_low_reversal_evidence"]
            != freeze_payload(metric_payload(self.swing_low_reversal_evidence))
            or rec_content["confirmed_event_on_bar"] != self.confirmed_event_on_bar
            or rec_content["witness_mode"] != self.witness_mode
            or rec_content["policy_witness_ref"] != self.policy_witness_ref
            or rec_content["authority_status"] != self.authority_status
            or rec_content["muf_authority_policy_ref"] is not TypedState.NOT_CONFIGURED
        ):
            raise SchemaViolation(
                "published_record.content does not match CandidateWitnessRecord attributes"
            )

    @property
    def record_identity(self) -> str:
        return self.published_record.record_identity

    def as_record(self) -> PublishedRecord:
        return self.published_record


@dataclass(frozen=True)
class SwingEventWitnessRecord(ImmutableRecord):
    """Causal witness of a Module 2.1A confirmed swing event at confirmation bar close.

    Strictly separates ``origin_key`` (bar where the extreme was reached) from
    ``availability_key`` (bar where confirmation occurred). Never visible prior
    to ``availability_key`` and never authoritative without an S3/S4 MUF
    ``PolicyArtifact`` (I-PAUTH-1..4).
    """

    timeline_id: str
    extrema_kind: str
    origin_position: int
    confirmation_position: int
    origin_key: InformationKey
    availability_key: InformationKey
    swing_price: MetricResult
    swing_confirmation_price: MetricResult
    swing_reversal_distance: MetricResult
    swing_reversal_fraction: MetricResult
    swing_reversal_evidence: MetricResult
    swing_continuation_history_count: int
    swing_confirmed_history_percentile: MetricResult
    swing_confirmed_history_count: int
    swing_policy_gate_value: MetricResult
    witness_mode: str
    policy_witness_ref: str
    authority_status: str
    muf_authority_policy_ref: TypedState
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        if self.extrema_kind not in LEGAL_EXTREMA_KINDS:
            raise SchemaViolation(
                f"extrema_kind must be HIGH or LOW, got {self.extrema_kind!r}"
            )
        if self.origin_position < 0 or self.origin_position >= self.confirmation_position:
            raise SchemaViolation(
                f"{S2_ILLEGAL_SWING_ORIGIN_TIMING}: require 0 <= origin_position "
                f"({self.origin_position}) < confirmation_position ({self.confirmation_position})"
            )
        require_visible_at(fact_key=self.origin_key, at_key=self.availability_key)
        if not (self.origin_key < self.availability_key):
            raise SchemaViolation(
                f"{S2_ILLEGAL_SWING_ORIGIN_TIMING}: origin_key must be strictly earlier "
                "than availability_key"
            )
        if self.witness_mode != WITNESS_MODE_EXTERNAL_POLICY:
            raise SchemaViolation(
                f"{S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY}: swing event witness "
                f"requires {WITNESS_MODE_EXTERNAL_POLICY!r}"
            )
        if not isinstance(self.policy_witness_ref, str) or not self.policy_witness_ref.strip():
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: swing event witness requires non-empty policy_witness_ref"
            )
        if self.authority_status != AUTHORITY_STATUS_WITNESS_ONLY:
            raise SchemaViolation(
                f"authority_status must be {AUTHORITY_STATUS_WITNESS_ONLY!r}"
            )
        if self.muf_authority_policy_ref is not TypedState.NOT_CONFIGURED:
            raise SchemaViolation(
                "muf_authority_policy_ref must be TypedState.NOT_CONFIGURED at S2"
            )
        if not isinstance(self.published_record, PublishedRecord):
            raise SchemaViolation("published_record must be a PublishedRecord")
        if self.published_record.schema_identity != S2_SCHEMA_IDENTITY:
            raise SchemaViolation("published_record.schema_identity mismatch")
        if self.published_record.record_type != S2_SWING_EVENT_WITNESS_RECORD_TYPE:
            raise SchemaViolation(
                f"published_record.record_type must be {S2_SWING_EVENT_WITNESS_RECORD_TYPE!r}"
            )
        if self.published_record.timeline_id != self.timeline_id:
            raise SchemaViolation("published_record.timeline_id mismatch")
        if self.published_record.availability_key != self.availability_key:
            raise SchemaViolation(
                "published_record.availability_key must equal availability_key"
            )
        for metric_field_name, metric_val in (
            ("swing_price", self.swing_price),
            ("swing_confirmation_price", self.swing_confirmation_price),
            ("swing_reversal_distance", self.swing_reversal_distance),
            ("swing_reversal_fraction", self.swing_reversal_fraction),
            ("swing_reversal_evidence", self.swing_reversal_evidence),
        ):
            if not isinstance(metric_val, MetricResult) or metric_val.semantics != EXACT:
                raise SchemaViolation(
                    f"{S2_NONFINITE_CONFIRMED_SWING_METRIC}: {metric_field_name} must be EXACT MetricResult"
                )
        engine_id_str = (
            f"{S2_ADAPTER_ENGINE_IDENTITY.schema_domain}:"
            f"{S2_ADAPTER_ENGINE_IDENTITY.schema_version}"
        )
        expected_id = canonical_artifact_identity(
            SWING_EVENT_WITNESS_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "origin_key": "|".join(key_serialization(self.origin_key)),
                "availability_key": "|".join(key_serialization(self.availability_key)),
                "extrema_kind": self.extrema_kind,
                "engine_identity": engine_id_str,
                "policy_witness_ref": self.policy_witness_ref,
            },
        )
        if self.published_record.record_identity != expected_id:
            raise SchemaViolation(
                "published_record.record_identity does not match canonical S2 swing event witness identity"
            )
        rec_content = self.published_record.content
        _require_non_negative_int(
            self.swing_continuation_history_count,
            "swing_continuation_history_count",
        )
        _require_non_negative_int(
            self.swing_confirmed_history_count,
            "swing_confirmed_history_count",
        )
        for opt_metric_name, opt_metric_val in (
            ("swing_confirmed_history_percentile", self.swing_confirmed_history_percentile),
            ("swing_policy_gate_value", self.swing_policy_gate_value),
        ):
            if not isinstance(opt_metric_val, MetricResult):
                raise SchemaViolation(f"{opt_metric_name} must be a MetricResult")
        if (
            rec_content["extrema_kind"] != self.extrema_kind
            or rec_content["origin_position"] != self.origin_position
            or rec_content["confirmation_position"] != self.confirmation_position
            or rec_content["origin_key"] != self.origin_key
            or rec_content["availability_key"] != self.availability_key
            or rec_content["swing_price"] != freeze_payload(metric_payload(self.swing_price))
            or rec_content["swing_confirmation_price"]
            != freeze_payload(metric_payload(self.swing_confirmation_price))
            or rec_content["swing_reversal_distance"]
            != freeze_payload(metric_payload(self.swing_reversal_distance))
            or rec_content["swing_reversal_fraction"]
            != freeze_payload(metric_payload(self.swing_reversal_fraction))
            or rec_content["swing_reversal_evidence"]
            != freeze_payload(metric_payload(self.swing_reversal_evidence))
            or rec_content["swing_continuation_history_count"]
            != self.swing_continuation_history_count
            or rec_content["swing_confirmed_history_percentile"]
            != freeze_payload(metric_payload(self.swing_confirmed_history_percentile))
            or rec_content["swing_confirmed_history_count"]
            != self.swing_confirmed_history_count
            or rec_content["swing_confirmation_threshold"]
            != freeze_payload(metric_payload(self.swing_policy_gate_value))
            or rec_content["witness_mode"] != self.witness_mode
            or rec_content["policy_witness_ref"] != self.policy_witness_ref
            or rec_content["authority_status"] != self.authority_status
            or rec_content["muf_authority_policy_ref"] is not TypedState.NOT_CONFIGURED
        ):
            raise SchemaViolation(
                "published_record.content does not match SwingEventWitnessRecord attributes"
            )

    @property
    def record_identity(self) -> str:
        return self.published_record.record_identity

    def as_record(self) -> PublishedRecord:
        return self.published_record


@dataclass(frozen=True)
class DetectorWitnessAsOfView(ImmutableRecord):
    """Causal as-of projection of a ``DetectorWitnessBundle`` at ``query_key``."""

    timeline_id: str
    query_key: InformationKey
    witness_mode: str
    policy_witness_ref: Union[str, TypedState]
    candidate_witnesses: Tuple[CandidateWitnessRecord, ...]
    swing_event_witnesses: Tuple[SwingEventWitnessRecord, ...]
    authoritative_turning_points: Tuple[AuthoritativeTurningPointReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query_key, InformationKey):
            raise InformationKeyViolation("query_key must be an InformationKey")
        if self.query_key.timeline_id != self.timeline_id:
            raise InformationKeyViolation(
                f"{S2_TIMELINE_MISMATCH}: query_key timeline mismatch"
            )
        if self.query_key.information_phase == InformationPhase.BAR_PRE_CLOSE:
            raise IllegalCausalReference(
                "BAR_PRE_CLOSE query cannot access completed-row S2 witness surface"
            )
        if len(self.authoritative_turning_points) != 0:
            raise SchemaViolation(
                f"{S2_AUTHORITY_MISSING_NO_PROMOTION}: S2 witness view cannot contain "
                "authoritative turning points"
            )
        for cand in self.candidate_witnesses:
            if not isinstance(cand, CandidateWitnessRecord):
                raise SchemaViolation("candidate_witnesses must contain CandidateWitnessRecord")
            require_visible_at(fact_key=cand.availability_key, at_key=self.query_key)
        for ev in self.swing_event_witnesses:
            if not isinstance(ev, SwingEventWitnessRecord):
                raise SchemaViolation("swing_event_witnesses must contain SwingEventWitnessRecord")
            require_visible_at(fact_key=ev.availability_key, at_key=self.query_key)


@dataclass(frozen=True)
class DetectorWitnessBundle(ImmutableRecord):
    """Immutable bundle of all S2 witness records emitted over a sealed bar sequence."""

    timeline_id: str
    axis: InformationAxis
    source_identity: SchemaIdentity
    dataset_identity: str
    engine_identity: SchemaIdentity
    witness_mode: str
    policy_witness_spec: Union[DetectorPolicyWitnessSpec, TypedState]
    policy_witness_ref: Union[str, TypedState]
    observation_keys: Tuple[InformationKey, ...]
    candidate_witnesses: Tuple[CandidateWitnessRecord, ...]
    swing_event_witnesses: Tuple[SwingEventWitnessRecord, ...]

    def __post_init__(self) -> None:
        if len(self.observation_keys) == 0:
            raise SchemaViolation(f"{S2_EMPTY_OBSERVATION_SEQUENCE}: empty observation_keys")
        if len(self.candidate_witnesses) != len(self.observation_keys):
            raise SchemaViolation(
                "candidate_witnesses length must equal observation_keys length"
            )
        if self.witness_mode == WITNESS_MODE_EVIDENCE_ONLY:
            if self.policy_witness_spec is not TypedState.NOT_CONFIGURED:
                raise SchemaViolation(
                    "EVIDENCE_ONLY mode requires policy_witness_spec = TypedState.NOT_CONFIGURED"
                )
            if self.policy_witness_ref is not TypedState.NOT_CONFIGURED:
                raise SchemaViolation(
                    "EVIDENCE_ONLY mode requires policy_witness_ref = TypedState.NOT_CONFIGURED"
                )
            if len(self.swing_event_witnesses) != 0:
                raise SchemaViolation(
                    f"{S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY}: EVIDENCE_ONLY mode "
                    "cannot contain swing_event_witnesses"
                )
        elif self.witness_mode == WITNESS_MODE_EXTERNAL_POLICY:
            if not isinstance(self.policy_witness_spec, DetectorPolicyWitnessSpec):
                raise SchemaViolation(
                    "EXTERNAL_POLICY mode requires a DetectorPolicyWitnessSpec"
                )
            if self.policy_witness_ref != self.policy_witness_spec.spec_identity:
                raise SchemaViolation(
                    "policy_witness_ref must match policy_witness_spec.spec_identity"
                )
        else:
            raise SchemaViolation(f"unknown witness_mode: {self.witness_mode!r}")

        prev_obs_key: Optional[InformationKey] = None
        for idx, obs_key in enumerate(self.observation_keys):
            if not isinstance(obs_key, InformationKey):
                raise InformationKeyViolation("observation_keys must contain InformationKey")
            if obs_key.timeline_id != self.timeline_id:
                raise InformationKeyViolation(f"{S2_TIMELINE_MISMATCH}: observation_key timeline mismatch")
            if key_axis(obs_key) is not self.axis:
                raise IncomparableInformationKeys(f"{S2_AXIS_MISMATCH}: observation_key axis mismatch")
            if obs_key.information_phase != InformationPhase.COMPLETED_ROW_AVAILABLE:
                raise IllegalCausalReference("observation_keys must be COMPLETED_ROW_AVAILABLE")
            if prev_obs_key is not None:
                if prev_obs_key == obs_key:
                    raise InformationKeyViolation(f"{S2_DUPLICATE_OBSERVATION_KEY}: duplicate observation_key")
                if not (prev_obs_key < obs_key):
                    raise PrematureAvailability(f"{S2_OUT_OF_ORDER_OBSERVATION}: out-of-order observation_key")
            prev_obs_key = obs_key

            cand = self.candidate_witnesses[idx]
            if not isinstance(cand, CandidateWitnessRecord):
                raise SchemaViolation("candidate_witnesses must contain CandidateWitnessRecord")
            if (
                cand.timeline_id != self.timeline_id
                or cand.availability_key != obs_key
                or cand.bar_position_in_stream != idx
                or cand.witness_mode != self.witness_mode
                or cand.policy_witness_ref != self.policy_witness_ref
            ):
                raise SchemaViolation(f"candidate_witnesses[{idx}] inconsistent with bundle header")

        confirmed_positions: set[int] = set()
        prev_conf_pos = -1
        for ev in self.swing_event_witnesses:
            if not isinstance(ev, SwingEventWitnessRecord):
                raise SchemaViolation("swing_event_witnesses must contain SwingEventWitnessRecord")
            if (
                ev.timeline_id != self.timeline_id
                or ev.witness_mode != self.witness_mode
                or ev.policy_witness_ref != self.policy_witness_ref
            ):
                raise SchemaViolation("swing_event_witness inconsistent with bundle header")
            if ev.confirmation_position <= prev_conf_pos or ev.confirmation_position >= len(self.observation_keys):
                raise SchemaViolation("swing_event_witness confirmation_position out of order or bounds")
            if ev.origin_key != self.observation_keys[ev.origin_position]:
                raise SchemaViolation("swing_event_witness origin_key does not match observation_keys[origin_position]")
            if ev.availability_key != self.observation_keys[ev.confirmation_position]:
                raise SchemaViolation("swing_event_witness availability_key does not match observation_keys[confirmation_position]")
            prev_conf_pos = ev.confirmation_position
            confirmed_positions.add(ev.confirmation_position)

        for idx, cand in enumerate(self.candidate_witnesses):
            if cand.confirmed_event_on_bar != (idx in confirmed_positions):
                raise SchemaViolation(
                    f"candidate_witnesses[{idx}].confirmed_event_on_bar mismatch with swing_event_witnesses"
                )


def _validate_sealed_bar_sequence(
    bars: Sequence[PublishedOhlcBarFact],
) -> Tuple[Tuple[PublishedOhlcBarFact, ...], str, InformationAxis, SchemaIdentity, str]:
    if not isinstance(bars, Sequence) or isinstance(bars, (str, bytes)):
        raise SchemaViolation(
            f"{S2_INVALID_BAR_FACT}: bars must be a sequence of PublishedOhlcBarFact"
        )
    bar_tuple = tuple(bars)
    if len(bar_tuple) == 0:
        raise SchemaViolation(
            f"{S2_EMPTY_OBSERVATION_SEQUENCE}: bars must be non-empty"
        )
    first = bar_tuple[0]
    if not isinstance(first, PublishedOhlcBarFact):
        raise SchemaViolation(
            f"{S2_INVALID_BAR_FACT}: expected PublishedOhlcBarFact, got {type(first).__name__}"
        )
    timeline_id = first.availability_key.timeline_id
    axis = key_axis(first.availability_key)
    source_id = first.source_identity
    dataset_id = first.dataset_identity

    prev_key: Optional[InformationKey] = None
    for idx, item in enumerate(bar_tuple):
        if not isinstance(item, PublishedOhlcBarFact):
            raise SchemaViolation(
                f"{S2_INVALID_BAR_FACT}: element {idx} is {type(item).__name__}, "
                "expected PublishedOhlcBarFact"
            )
        key = item.availability_key
        if key.information_phase != InformationPhase.COMPLETED_ROW_AVAILABLE:
            raise IllegalCausalReference(
                f"bar {idx} availability_key must be COMPLETED_ROW_AVAILABLE"
            )
        if key.timeline_id != timeline_id:
            raise InformationKeyViolation(
                f"{S2_TIMELINE_MISMATCH}: bar {idx} timeline {key.timeline_id!r} != {timeline_id!r}"
            )
        item_axis = key_axis(key)
        if item_axis is not axis:
            raise IncomparableInformationKeys(
                f"{S2_AXIS_MISMATCH}: bar {idx} axis {item_axis!r} != {axis!r}"
            )
        if item.source_identity != source_id:
            raise SchemaViolation(
                f"{S2_SOURCE_MISMATCH}: bar {idx} source_identity mismatch"
            )
        if item.dataset_identity != dataset_id:
            raise SchemaViolation(
                f"{S2_DATASET_MISMATCH}: bar {idx} dataset_identity mismatch"
            )
        if prev_key is not None:
            if prev_key == key:
                raise InformationKeyViolation(
                    f"{S2_DUPLICATE_OBSERVATION_KEY}: duplicate key at index {idx}"
                )
            if not (prev_key < key):
                raise PrematureAvailability(
                    f"{S2_OUT_OF_ORDER_OBSERVATION}: bar {idx} key precedes prior key"
                )
        prev_key = key

    return bar_tuple, timeline_id, axis, source_id, dataset_id


def _verify_detector_output_frame(
    out: Any,
    *,
    expected_high: np.ndarray,
    expected_low: np.ndarray,
) -> pd.DataFrame:
    if not isinstance(out, pd.DataFrame):
        raise SchemaViolation(
            f"{S2_DETECTOR_SCHEMA_MISMATCH}: detector output must be a DataFrame"
        )
    actual_cols = tuple(out.columns)
    if actual_cols != S2_EXPECTED_ANALYZE_COLUMNS:
        raise SchemaViolation(
            f"{S2_DETECTOR_SCHEMA_MISMATCH}: detector columns {actual_cols!r} "
            f"!= expected {S2_EXPECTED_ANALYZE_COLUMNS!r}"
        )
    if len(out) != len(expected_high):
        raise SchemaViolation(
            f"{S2_DETECTOR_SCHEMA_MISMATCH}: detector row count {len(out)} "
            f"!= input row count {len(expected_high)}"
        )
    actual_high = np.asarray(out["high"].to_numpy(copy=False), dtype=np.float64)
    actual_low = np.asarray(out["low"].to_numpy(copy=False), dtype=np.float64)
    if not np.array_equal(actual_high.view(np.uint64), expected_high.view(np.uint64)):
        raise SchemaViolation(
            f"{S2_PASSTHROUGH_TAMPERED}: detector altered passthrough 'high' column"
        )
    if not np.array_equal(actual_low.view(np.uint64), expected_low.view(np.uint64)):
        raise SchemaViolation(
            f"{S2_PASSTHROUGH_TAMPERED}: detector altered passthrough 'low' column"
        )
    return out


def adapt_detector_witness_stream(
    bars: Sequence[PublishedOhlcBarFact],
    *,
    confirmation_policy: Optional[SwingConfirmationPolicy] = None,
    custom_policy_parameters: Optional[Mapping[str, Any]] = None,
    policy_caller_note: str = "",
    detector_instance: Optional[CausalAdaptiveSwingDetector] = None,
) -> DetectorWitnessBundle:
    """Run Closed Module 2.1A over sealed ``PublishedOhlcBarFact`` bars and emit S2 witnesses.

    Parameters
    ----------
    bars:
        Strictly increasing sequence of ``PublishedOhlcBarFact`` sharing a single
        timeline, information axis, source identity, and dataset identity.
    confirmation_policy:
        Optional ``SwingConfirmationPolicy`` passed to Module 2.1A. When ``None``,
        runs in ``WITNESS_MODE_EVIDENCE_ONLY`` (no binary swing confirmations).
        When provided, runs in ``WITNESS_MODE_EXTERNAL_POLICY`` and stamps all
        outputs as ``WITNESS_ONLY_NOT_MUF_AUTHORITATIVE``.
    custom_policy_parameters:
        Required only when ``confirmation_policy`` is a non-standard subclass of
        ``SwingConfirmationPolicy`` other than ``EmpiricalConfirmationPolicy``.
    policy_caller_note:
        Optional non-identity provenance note attached to ``DetectorPolicyWitnessSpec``.
    detector_instance:
        Optional pre-constructed ``CausalAdaptiveSwingDetector`` (must match
        ``confirmation_policy``). When ``None``, a fresh ``CausalAdaptiveSwingDetector``
        is instantiated.
    """
    bar_tuple, timeline_id, axis, source_id, dataset_id = _validate_sealed_bar_sequence(bars)

    if confirmation_policy is None:
        if custom_policy_parameters is not None:
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: custom_policy_parameters must be None "
                "when confirmation_policy is None"
            )
        witness_mode = WITNESS_MODE_EVIDENCE_ONLY
        policy_spec: Union[DetectorPolicyWitnessSpec, TypedState] = TypedState.NOT_CONFIGURED
        policy_ref: Union[str, TypedState] = TypedState.NOT_CONFIGURED
        policy_ref_serialized: str = TypedState.NOT_CONFIGURED.value
    else:
        witness_mode = WITNESS_MODE_EXTERNAL_POLICY
        policy_spec = DetectorPolicyWitnessSpec.from_policy(
            confirmation_policy,
            custom_parameters=custom_policy_parameters,
            caller_note=policy_caller_note,
        )
        policy_ref = policy_spec.spec_identity
        policy_ref_serialized = policy_spec.spec_identity

    ref_detector = CausalAdaptiveSwingDetector(confirmation_policy=confirmation_policy)
    if detector_instance is None:
        detector = ref_detector
    else:
        if not isinstance(detector_instance, CausalAdaptiveSwingDetector):
            raise SchemaViolation(
                f"{S2_DETECTOR_SCHEMA_MISMATCH}: detector_instance must be a "
                "CausalAdaptiveSwingDetector"
            )
        if vars(detector_instance) != vars(ref_detector):
            raise SchemaViolation(
                f"{S2_INVALID_WITNESS_POLICY}: detector_instance policy state "
                "does not match confirmation_policy argument"
            )
        detector = detector_instance

    high_arr = np.asarray([b.high_price for b in bar_tuple], dtype=np.float64)
    low_arr = np.asarray([b.low_price for b in bar_tuple], dtype=np.float64)
    input_df = pd.DataFrame({"high": high_arr.copy(), "low": low_arr.copy()})

    try:
        raw_out = detector.analyze(input_df, high_col="high", low_col="low")
    except SwingDetectorError as exc:
        raise SchemaViolation(f"Module 2.1A execution error: {exc}") from exc

    out = _verify_detector_output_frame(
        raw_out,
        expected_high=high_arr,
        expected_low=low_arr,
    )

    n_bars = len(bar_tuple)
    candidate_records: list[CandidateWitnessRecord] = []
    swing_event_records: list[SwingEventWitnessRecord] = []
    engine_id_str = (
        f"{S2_ADAPTER_ENGINE_IDENTITY.schema_domain}:"
        f"{S2_ADAPTER_ENGINE_IDENTITY.schema_version}"
    )
    source_id_str = f"{source_id.schema_domain}:{source_id.schema_version}"

    col_cand_side = out["candidate_side"].tolist()
    col_cand_origin_pos = out["candidate_origin_position"].tolist()
    col_cand_price = out["candidate_price"].to_numpy(copy=False)
    col_cand_rev_dist = out["candidate_reversal_distance"].to_numpy(copy=False)
    col_cand_rev_frac = out["candidate_reversal_fraction"].to_numpy(copy=False)
    col_cand_rev_ev = out["candidate_reversal_evidence"].to_numpy(copy=False)
    col_cand_cont_cnt = out["candidate_continuation_history_count"].to_numpy(copy=False)
    col_cand_conf_cnt = out["candidate_confirmed_history_count"].to_numpy(copy=False)
    col_cand_gate = out["candidate_confirmation_threshold"].to_numpy(copy=False)
    col_high_rev_ev = out["swing_high_reversal_evidence"].to_numpy(copy=False)
    col_low_rev_ev = out["swing_low_reversal_evidence"].to_numpy(copy=False)

    col_high_conf = out["swing_high_confirmed"].to_numpy(copy=False)
    col_low_conf = out["swing_low_confirmed"].to_numpy(copy=False)
    col_sw_origin_pos = out["swing_origin_position"].tolist()
    col_sw_price = out["swing_price"].to_numpy(copy=False)
    col_sw_conf_pos = out["swing_confirmation_position"].tolist()
    col_sw_conf_price = out["swing_confirmation_price"].to_numpy(copy=False)
    col_sw_rev_dist = out["swing_reversal_distance"].to_numpy(copy=False)
    col_sw_rev_frac = out["swing_reversal_fraction"].to_numpy(copy=False)
    col_sw_rev_ev = out["swing_reversal_evidence"].to_numpy(copy=False)
    col_sw_cont_cnt = out["swing_continuation_history_count"].to_numpy(copy=False)
    col_sw_conf_pct = out["swing_confirmed_history_percentile"].to_numpy(copy=False)
    col_sw_conf_cnt = out["swing_confirmed_history_count"].to_numpy(copy=False)
    col_sw_gate = out["swing_confirmation_threshold"].to_numpy(copy=False)

    for idx in range(n_bars):
        bar_fact = bar_tuple[idx]
        avail_key = bar_fact.availability_key
        avail_key_ser = "|".join(key_serialization(avail_key))

        high_conf = bool(col_high_conf[idx])
        low_conf = bool(col_low_conf[idx])
        if high_conf and low_conf:
            raise SchemaViolation(
                f"{S2_CONTRADICTORY_SWING_CONFIRMATION}: both swing_high_confirmed "
                f"and swing_low_confirmed are True at row {idx}"
            )
        confirmed_on_bar = high_conf or low_conf

        raw_sw_origin_pos = col_sw_origin_pos[idx]
        raw_sw_conf_pos = col_sw_conf_pos[idx]

        if not confirmed_on_bar:
            if not pd.isna(raw_sw_origin_pos) or not pd.isna(raw_sw_conf_pos):
                raise SchemaViolation(
                    f"{S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS}: unconfirmed row {idx} "
                    f"has swing positions ({raw_sw_origin_pos!r}, {raw_sw_conf_pos!r})"
                )
        else:
            if witness_mode == WITNESS_MODE_EVIDENCE_ONLY:
                raise SchemaViolation(
                    f"{S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY}: row {idx} confirmed "
                    "a swing while confirmation_policy is None"
                )
            if pd.isna(raw_sw_origin_pos) or pd.isna(raw_sw_conf_pos):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_SWING_ORIGIN_TIMING}: confirmed row {idx} has missing "
                    f"swing positions ({raw_sw_origin_pos!r}, {raw_sw_conf_pos!r})"
                )
            sw_origin_pos = _require_non_negative_int(
                raw_sw_origin_pos, "swing_origin_position"
            )
            sw_conf_pos = _require_non_negative_int(
                raw_sw_conf_pos, "swing_confirmation_position"
            )
            if sw_conf_pos != idx:
                raise SchemaViolation(
                    f"{S2_CONFIRMATION_POSITION_MISMATCH}: row {idx} has "
                    f"swing_confirmation_position={sw_conf_pos}"
                )
            if sw_origin_pos < 0 or sw_origin_pos >= idx:
                raise SchemaViolation(
                    f"{S2_ILLEGAL_SWING_ORIGIN_TIMING}: row {idx} has illegal "
                    f"swing_origin_position={sw_origin_pos}"
                )
            extrema_kind = CANDIDATE_SIDE_HIGH if high_conf else CANDIDATE_SIDE_LOW
            origin_bar_fact = bar_tuple[sw_origin_pos]
            origin_key = origin_bar_fact.availability_key
            origin_key_ser = "|".join(key_serialization(origin_key))

            sw_price_m = _require_finite_metric(col_sw_price[idx], "swing_price")
            sw_conf_price_m = _require_finite_metric(
                col_sw_conf_price[idx], "swing_confirmation_price"
            )
            sw_rev_dist_m = _require_finite_metric(
                col_sw_rev_dist[idx], "swing_reversal_distance"
            )
            sw_rev_frac_m = _require_finite_metric(
                col_sw_rev_frac[idx], "swing_reversal_fraction"
            )
            sw_rev_ev_m = _require_finite_metric(
                col_sw_rev_ev[idx], "swing_reversal_evidence"
            )
            sw_cont_cnt = _require_non_negative_int(
                col_sw_cont_cnt[idx], "swing_continuation_history_count"
            )
            sw_conf_cnt = _require_non_negative_int(
                col_sw_conf_cnt[idx], "swing_confirmed_history_count"
            )
            sw_conf_pct_m = _normalize_optional_metric(
                col_sw_conf_pct[idx], REASON_NO_PRIOR_CONFIRMED_SWINGS
            )
            sw_gate_m = _normalize_optional_metric(
                col_sw_gate[idx], REASON_POLICY_GATE_INACTIVE
            )

            event_id = canonical_artifact_identity(
                SWING_EVENT_WITNESS_IDENTITY_SCHEMA,
                identity_payload={
                    "timeline_id": timeline_id,
                    "origin_key": origin_key_ser,
                    "availability_key": avail_key_ser,
                    "extrema_kind": extrema_kind,
                    "engine_identity": engine_id_str,
                    "policy_witness_ref": policy_ref_serialized,
                },
                proof_payload={
                    "dataset_identity": dataset_id,
                    "source_identity": source_id_str,
                    "origin_bar_record_ref": origin_bar_fact.published_bar_record_ref,
                    "confirmation_bar_record_ref": bar_fact.published_bar_record_ref,
                },
            )
            event_content = {
                "timeline_id": timeline_id,
                "extrema_kind": extrema_kind,
                "origin_position": sw_origin_pos,
                "confirmation_position": sw_conf_pos,
                "origin_key": origin_key,
                "availability_key": avail_key,
                "swing_price": metric_payload(sw_price_m),
                "swing_confirmation_price": metric_payload(sw_conf_price_m),
                "swing_reversal_distance": metric_payload(sw_rev_dist_m),
                "swing_reversal_fraction": metric_payload(sw_rev_frac_m),
                "swing_reversal_evidence": metric_payload(sw_rev_ev_m),
                "swing_continuation_history_count": sw_cont_cnt,
                "swing_confirmed_history_percentile": metric_payload(sw_conf_pct_m),
                "swing_confirmed_history_count": sw_conf_cnt,
                "swing_confirmation_threshold": metric_payload(sw_gate_m),
                "engine_identity": engine_id_str,
                "witness_mode": witness_mode,
                "policy_witness_ref": policy_ref,
                "authority_status": AUTHORITY_STATUS_WITNESS_ONLY,
                "muf_authority_policy_ref": TypedState.NOT_CONFIGURED,
                "dataset_identity": dataset_id,
                "source_identity": source_id_str,
                "origin_bar_record_ref": origin_bar_fact.published_bar_record_ref,
                "confirmation_bar_record_ref": bar_fact.published_bar_record_ref,
            }
            event_pub = PublishedRecord(
                record_identity=event_id,
                record_type=S2_SWING_EVENT_WITNESS_RECORD_TYPE,
                schema_identity=S2_SCHEMA_IDENTITY,
                timeline_id=timeline_id,
                availability_key=avail_key,
                content=event_content,
            )
            swing_event_records.append(
                SwingEventWitnessRecord(
                    timeline_id=timeline_id,
                    extrema_kind=extrema_kind,
                    origin_position=sw_origin_pos,
                    confirmation_position=sw_conf_pos,
                    origin_key=origin_key,
                    availability_key=avail_key,
                    swing_price=sw_price_m,
                    swing_confirmation_price=sw_conf_price_m,
                    swing_reversal_distance=sw_rev_dist_m,
                    swing_reversal_fraction=sw_rev_frac_m,
                    swing_reversal_evidence=sw_rev_ev_m,
                    swing_continuation_history_count=sw_cont_cnt,
                    swing_confirmed_history_percentile=sw_conf_pct_m,
                    swing_confirmed_history_count=sw_conf_cnt,
                    swing_policy_gate_value=sw_gate_m,
                    witness_mode=witness_mode,
                    policy_witness_ref=str(policy_ref),
                    authority_status=AUTHORITY_STATUS_WITNESS_ONLY,
                    muf_authority_policy_ref=TypedState.NOT_CONFIGURED,
                    published_record=event_pub,
                )
            )

        cand_side = col_cand_side[idx]
        if cand_side not in LEGAL_CANDIDATE_SIDES:
            raise SchemaViolation(
                f"{S2_INVALID_CANDIDATE_SIDE}: row {idx} candidate_side={cand_side!r}"
            )
        raw_cand_origin_pos = col_cand_origin_pos[idx]
        raw_cand_price = col_cand_price[idx]
        if cand_side == CANDIDATE_SIDE_UNDECIDED:
            if not pd.isna(raw_cand_origin_pos):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: row {idx} is UNDECIDED "
                    f"but candidate_origin_position={raw_cand_origin_pos!r}"
                )
            if _is_finite_number(raw_cand_price):
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_PRICE_STATE}: row {idx} is UNDECIDED "
                    f"but candidate_price is finite ({raw_cand_price!r})"
                )
            cand_origin_pos: Union[int, TypedState] = TypedState.NOT_APPLICABLE
            cand_origin_key: Union[InformationKey, TypedState] = TypedState.NOT_APPLICABLE
            cand_price_m = unavailable_metric(
                REASON_CANDIDATE_UNDECIDED, TypedState.UNDEFINED
            )
        else:
            if pd.isna(raw_cand_origin_pos):
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: row {idx} is {cand_side} "
                    "but candidate_origin_position is missing"
                )
            cand_origin_pos_int = _require_non_negative_int(
                raw_cand_origin_pos, "candidate_origin_position"
            )
            if cand_origin_pos_int > idx:
                raise SchemaViolation(
                    f"{S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING}: row {idx} has "
                    f"candidate_origin_position={cand_origin_pos_int} > {idx}"
                )
            if not _is_finite_number(raw_cand_price):
                raise SchemaViolation(
                    f"{S2_INVALID_CANDIDATE_PRICE_STATE}: row {idx} is {cand_side} "
                    f"but candidate_price is non-finite ({raw_cand_price!r})"
                )
            cand_origin_pos = cand_origin_pos_int
            cand_origin_key = bar_tuple[cand_origin_pos_int].availability_key
            cand_price_m = exact_metric(float(raw_cand_price))

        cand_rev_dist_m = _normalize_optional_metric(
            col_cand_rev_dist[idx], REASON_CANDIDATE_UNASSESSED
        )
        cand_rev_frac_m = _normalize_optional_metric(
            col_cand_rev_frac[idx], REASON_CANDIDATE_UNASSESSED
        )
        cand_rev_ev_m = _normalize_optional_metric(
            col_cand_rev_ev[idx], REASON_CANDIDATE_UNASSESSED
        )
        cand_cont_cnt = _require_non_negative_int(
            col_cand_cont_cnt[idx], "candidate_continuation_history_count"
        )
        cand_conf_cnt = _require_non_negative_int(
            col_cand_conf_cnt[idx], "candidate_confirmed_history_count"
        )
        cand_gate_m = _normalize_optional_metric(
            col_cand_gate[idx], REASON_POLICY_GATE_INACTIVE
        )
        high_rev_ev_m = _normalize_optional_metric(
            col_high_rev_ev[idx], REASON_SIDE_NOT_EVALUATED
        )
        low_rev_ev_m = _normalize_optional_metric(
            col_low_rev_ev[idx], REASON_SIDE_NOT_EVALUATED
        )

        cand_id = canonical_artifact_identity(
            CANDIDATE_WITNESS_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": timeline_id,
                "availability_key": avail_key_ser,
                "engine_identity": engine_id_str,
                "witness_mode": witness_mode,
                "policy_witness_ref": policy_ref_serialized,
            },
            proof_payload={
                "dataset_identity": dataset_id,
                "source_identity": source_id_str,
                "bar_record_ref": bar_fact.published_bar_record_ref,
            },
        )
        cand_content = {
            "timeline_id": timeline_id,
            "bar_position_in_stream": idx,
            "availability_key": avail_key,
            "candidate_side": cand_side,
            "candidate_origin_position": cand_origin_pos,
            "candidate_origin_key": cand_origin_key,
            "candidate_price": metric_payload(cand_price_m),
            "candidate_reversal_distance": metric_payload(cand_rev_dist_m),
            "candidate_reversal_fraction": metric_payload(cand_rev_frac_m),
            "candidate_reversal_evidence": metric_payload(cand_rev_ev_m),
            "candidate_continuation_history_count": cand_cont_cnt,
            "candidate_confirmed_history_count": cand_conf_cnt,
            "candidate_confirmation_threshold": metric_payload(cand_gate_m),
            "swing_high_reversal_evidence": metric_payload(high_rev_ev_m),
            "swing_low_reversal_evidence": metric_payload(low_rev_ev_m),
            "confirmed_event_on_bar": confirmed_on_bar,
            "engine_identity": engine_id_str,
            "witness_mode": witness_mode,
            "policy_witness_ref": policy_ref,
            "authority_status": AUTHORITY_STATUS_WITNESS_ONLY,
            "muf_authority_policy_ref": TypedState.NOT_CONFIGURED,
            "dataset_identity": dataset_id,
            "source_identity": source_id_str,
            "bar_record_ref": bar_fact.published_bar_record_ref,
        }
        cand_pub = PublishedRecord(
            record_identity=cand_id,
            record_type=S2_CANDIDATE_WITNESS_RECORD_TYPE,
            schema_identity=S2_SCHEMA_IDENTITY,
            timeline_id=timeline_id,
            availability_key=avail_key,
            content=cand_content,
        )
        candidate_records.append(
            CandidateWitnessRecord(
                timeline_id=timeline_id,
                availability_key=avail_key,
                bar_position_in_stream=idx,
                candidate_side=cand_side,
                candidate_origin_position=cand_origin_pos,
                candidate_origin_key=cand_origin_key,
                candidate_price=cand_price_m,
                candidate_reversal_distance=cand_rev_dist_m,
                candidate_reversal_fraction=cand_rev_frac_m,
                candidate_reversal_evidence=cand_rev_ev_m,
                candidate_continuation_history_count=cand_cont_cnt,
                candidate_confirmed_history_count=cand_conf_cnt,
                candidate_policy_gate_value=cand_gate_m,
                swing_high_reversal_evidence=high_rev_ev_m,
                swing_low_reversal_evidence=low_rev_ev_m,
                confirmed_event_on_bar=confirmed_on_bar,
                witness_mode=witness_mode,
                policy_witness_ref=policy_ref,
                authority_status=AUTHORITY_STATUS_WITNESS_ONLY,
                muf_authority_policy_ref=TypedState.NOT_CONFIGURED,
                published_record=cand_pub,
            )
        )

    return DetectorWitnessBundle(
        timeline_id=timeline_id,
        axis=axis,
        source_identity=source_id,
        dataset_identity=dataset_id,
        engine_identity=S2_ADAPTER_ENGINE_IDENTITY,
        witness_mode=witness_mode,
        policy_witness_spec=policy_spec,
        policy_witness_ref=policy_ref,
        observation_keys=tuple(b.availability_key for b in bar_tuple),
        candidate_witnesses=tuple(candidate_records),
        swing_event_witnesses=tuple(swing_event_records),
    )


def _validate_query_key_against_bundle(
    bundle: DetectorWitnessBundle,
    at_key: InformationKey,
) -> None:
    if not isinstance(bundle, DetectorWitnessBundle):
        raise SchemaViolation("bundle must be a DetectorWitnessBundle")
    if not isinstance(at_key, InformationKey):
        raise InformationKeyViolation("at_key must be an InformationKey")
    if at_key.timeline_id != bundle.timeline_id:
        raise InformationKeyViolation(
            f"{S2_TIMELINE_MISMATCH}: query key timeline {at_key.timeline_id!r} "
            f"!= bundle timeline {bundle.timeline_id!r}"
        )
    if at_key.information_phase == InformationPhase.BAR_PRE_CLOSE:
        raise IllegalCausalReference(
            "BAR_PRE_CLOSE query cannot access completed-row S2 witness surface"
        )
    if key_axis(at_key) is not bundle.axis:
        raise IncomparableInformationKeys(
            f"{S2_AXIS_MISMATCH}: query key axis {key_axis(at_key)!r} != bundle axis {bundle.axis!r}"
        )


def query_witness_surface_as_of(
    bundle: DetectorWitnessBundle,
    *,
    at_key: InformationKey,
) -> DetectorWitnessAsOfView:
    """Return the causal witness surface visible at ``at_key`` (``availability_key <= at_key``).

    Enforces S0 ``require_visible_at`` on every witness record. Swing event
    witnesses whose ``origin_key <= at_key < availability_key`` are strictly
    excluded (Origin != Availability; zero retrospective backfill).
    """
    _validate_query_key_against_bundle(bundle, at_key)

    visible_candidates: list[CandidateWitnessRecord] = []
    for cand in bundle.candidate_witnesses:
        try:
            is_visible = cand.availability_key <= at_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if is_visible:
            require_visible_at(fact_key=cand.availability_key, at_key=at_key)
            visible_candidates.append(cand)

    visible_events: list[SwingEventWitnessRecord] = []
    for ev in bundle.swing_event_witnesses:
        try:
            is_visible = ev.availability_key <= at_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
        if is_visible:
            require_visible_at(fact_key=ev.availability_key, at_key=at_key)
            visible_events.append(ev)

    return DetectorWitnessAsOfView(
        timeline_id=bundle.timeline_id,
        query_key=at_key,
        witness_mode=bundle.witness_mode,
        policy_witness_ref=bundle.policy_witness_ref,
        candidate_witnesses=tuple(visible_candidates),
        swing_event_witnesses=tuple(visible_events),
        authoritative_turning_points=(),
    )


def query_authoritative_turning_points_as_of(
    bundle: DetectorWitnessBundle,
    *,
    at_key: InformationKey,
) -> Tuple[AuthoritativeTurningPointReference, ...]:
    """Query authoritative MUF turning points at ``at_key``.

    Per ``I-PAUTH-1`` and ``D1-4``, witness records are excluded from factual
    queries and never constitute authoritative turning points at S2. Always
    returns an empty tuple after validating ``at_key``.
    """
    _validate_query_key_against_bundle(bundle, at_key)
    for obs_key in bundle.observation_keys:
        try:
            _ = obs_key <= at_key
        except InformationKeyError as exc:
            raise IncomparableInformationKeys(str(exc)) from exc
    return ()


def promote_witness_to_authoritative_turning_point(
    witness_record: Union[CandidateWitnessRecord, SwingEventWitnessRecord, PublishedRecord],
    *,
    muf_policy_artifact: Any = TypedState.NOT_CONFIGURED,
) -> AuthoritativeTurningPointReference:
    """Attempt to promote an S2 witness record to an ``AuthoritativeTurningPointReference``.

    At S2, MUF ``PolicyArtifact`` authority infrastructure does not exist yet
    (scheduled for S3/S4). Any promotion attempt — whether with
    ``TypedState.NOT_CONFIGURED``, ``None``, a ``DetectorPolicyWitnessSpec``, or
    a forged object — fails closed with ``S2_AUTHORITY_MISSING_NO_PROMOTION``
    (I-PAUTH-1..4; D1 Annex D Attacks 1 & 2).
    """
    raise SchemaViolation(
        f"{S2_AUTHORITY_MISSING_NO_PROMOTION}: S2 emits detector witness records "
        f"({AUTHORITY_STATUS_WITNESS_ONLY}) only; MUF PolicyArtifact authority is "
        f"not configured at S2 (received witness={type(witness_record).__name__}, "
        f"muf_policy_artifact={muf_policy_artifact!r})"
    )


def verify_prefix_witness_invariance(
    prefix_bundle: DetectorWitnessBundle,
    full_bundle: DetectorWitnessBundle,
    *,
    at_key: InformationKey,
) -> bool:
    """Verify byte-identical prefix invariance between a truncated run and a full run at ``at_key``."""
    prefix_view = query_witness_surface_as_of(prefix_bundle, at_key=at_key)
    full_view = query_witness_surface_as_of(full_bundle, at_key=at_key)

    if len(prefix_view.candidate_witnesses) != len(full_view.candidate_witnesses):
        raise SchemaViolation(
            "prefix candidate witness count differs from full bundle as-of projection"
        )
    for left_c, right_c in zip(
        prefix_view.candidate_witnesses, full_view.candidate_witnesses
    ):
        if left_c.record_identity != right_c.record_identity:
            raise SchemaViolation(
                "candidate witness record_identity mutated under future bar append"
            )
        if left_c.published_record.content != right_c.published_record.content:
            raise SchemaViolation(
                "candidate witness content mutated under future bar append"
            )

    if len(prefix_view.swing_event_witnesses) != len(full_view.swing_event_witnesses):
        raise SchemaViolation(
            "prefix swing event witness count differs from full bundle as-of projection"
        )
    for left_e, right_e in zip(
        prefix_view.swing_event_witnesses, full_view.swing_event_witnesses
    ):
        if left_e.record_identity != right_e.record_identity:
            raise SchemaViolation(
                "swing event witness record_identity mutated under future bar append"
            )
        if left_e.published_record.content != right_e.published_record.content:
            raise SchemaViolation(
                "swing event witness content mutated under future bar append"
            )

    return True


__all__ = [
    "AUTHORITY_STATUS_WITNESS_ONLY",
    "CANDIDATE_SIDE_HIGH",
    "CANDIDATE_SIDE_LOW",
    "CANDIDATE_SIDE_UNDECIDED",
    "CANDIDATE_WITNESS_IDENTITY_SCHEMA",
    "CandidateWitnessRecord",
    "DetectorPolicyWitnessSpec",
    "DetectorWitnessAsOfView",
    "DetectorWitnessBundle",
    "LEGAL_CANDIDATE_SIDES",
    "LEGAL_EXTREMA_KINDS",
    "POLICY_WITNESS_SPEC_IDENTITY_SCHEMA",
    "REASON_CANDIDATE_UNASSESSED",
    "REASON_CANDIDATE_UNDECIDED",
    "REASON_NO_PRIOR_CONFIRMED_SWINGS",
    "REASON_POLICY_GATE_INACTIVE",
    "REASON_SIDE_NOT_EVALUATED",
    "S2_ADAPTER_ENGINE_IDENTITY",
    "S2_AUTHORITY_MISSING_NO_PROMOTION",
    "S2_AXIS_MISMATCH",
    "S2_CANDIDATE_WITNESS_RECORD_TYPE",
    "S2_CONFIRMATION_POSITION_MISMATCH",
    "S2_CONTRADICTORY_SWING_CONFIRMATION",
    "S2_DATASET_MISMATCH",
    "S2_DETECTOR_SCHEMA_MISMATCH",
    "S2_DUPLICATE_OBSERVATION_KEY",
    "S2_EMPTY_OBSERVATION_SEQUENCE",
    "S2_EXPECTED_ANALYZE_COLUMNS",
    "S2_FROZEN_2_1A_COLUMNS",
    "S2_ILLEGAL_CANDIDATE_ORIGIN_TIMING",
    "S2_ILLEGAL_SWING_ORIGIN_TIMING",
    "S2_INPUT_PASSTHROUGH_COLUMNS",
    "S2_INVALID_BAR_FACT",
    "S2_INVALID_CANDIDATE_PRICE_STATE",
    "S2_INVALID_CANDIDATE_SIDE",
    "S2_INVALID_WITNESS_POLICY",
    "S2_NONFINITE_CONFIRMED_SWING_METRIC",
    "S2_OUT_OF_ORDER_OBSERVATION",
    "S2_PASSTHROUGH_TAMPERED",
    "S2_POLICY_WITNESS_SPEC_RECORD_TYPE",
    "S2_SCHEMA_IDENTITY",
    "S2_SOURCE_MISMATCH",
    "S2_SWING_EVENT_WITNESS_RECORD_TYPE",
    "S2_TIMELINE_MISMATCH",
    "S2_UNCONFIRMED_ROW_CARRIES_SWING_POSITIONS",
    "S2_UNEXPECTED_CONFIRMATION_WITHOUT_POLICY",
    "SWING_EVENT_WITNESS_IDENTITY_SCHEMA",
    "SwingEventWitnessRecord",
    "WITNESS_MODE_EVIDENCE_ONLY",
    "WITNESS_MODE_EXTERNAL_POLICY",
    "adapt_detector_witness_stream",
    "promote_witness_to_authoritative_turning_point",
    "query_authoritative_turning_points_as_of",
    "query_witness_surface_as_of",
    "verify_prefix_witness_invariance",
]
