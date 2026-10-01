"""MUF V1 S1: path schemas — declarative S1 schema layer (additive S1 module).

Schema-layer responsibilities (design authority RC1 -> H1 -> S1 FINAL):

- one canonical completed-observation event name (SL-2) over the causal stream;
- closed-domain absence authority (RC1): expected-grid absence is witness-based
  over the REUSED Stage 4C-1 completeness tokens — S1 validates witnessed
  tokens and never reimplements the timestamp-SET-vs-declared-grid comparison;
  no witness => ``S1_ABSENCE_REQUIRES_CLOSED_DOMAIN`` and fail closed;
- an S1-only missing-state vocabulary (``S1_NOT_YET_OBSERVED``,
  ``S1_EXPECTED_GRID_KEY_NOT_OBSERVED``, ``S1_ABSENCE_REQUIRES_CLOSED_DOMAIN``);
- cadence partitioning (expected/unexpected/not-observed) with integrity
  failures on duplicates, out-of-order observations, or mixed axes;
- policy-free descriptor input normalization (typed UNDEFINED(ZERO_DENOMINATOR);
  no epsilon and no infinity);
- pair composition records with recorded_kind / recorded_property wording
  (never real/fake booleanization) and explicit formulas;
- bounded-memory stream checkpoints (incremental state only; no hidden history
  windows; O(1) continuity verification).

The trajectory module name, `trajectory_stage4c`, remains the sole canonical
completion authority name reused by S1 (RC1 name-law). Episode anchors,
membership, turning points, waves and segments are out of S1 scope entirely:
S1 defines schema foundations only.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, Final, FrozenSet, Mapping, Optional, Tuple, Union

from trading_system.research.information_time import InformationKey
from trading_system.research.trajectory.trajectory_stage4c import (
    COVERAGE_UNAVAILABLE,
    GRID_COMPLETENESS_UNKNOWN,
    GRID_OBSERVATIONS_COMPLETE,
    GRID_OBSERVATIONS_DEFECT_BOTH,
    GRID_OBSERVATIONS_MISSING,
    OFF_GRID_OBSERVATIONS_PRESENT,
)

from trading_system.market_understanding.availability import (
    InformationAxis,
    require_visible_at,
)
from trading_system.market_understanding.contracts import (
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    require_string,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.price_path import (
    ADJACENCY_GRID_CONTIGUOUS,
    ADJACENCY_OBSERVATION_ADJACENT,
    AMBIGUOUS_INTRABAR_CHRONOLOGY,
    BOUNDARY_SINCE_GENESIS,
    BOUNDARY_SINCE_ORIGIN,
    BOUNDARY_CONTRACTS,
    DESCRIPTOR_STAGES,
    DIRECTION_DOWN,
    DIRECTION_FLAT,
    DIRECTION_UP,
    DISCRETE_TV_TRIANGLE_INEQUALITY,
    EXACT,
    METRIC_SEMANTICS,
    NOT_TIME_INDEXED,
    PUBLISHED_OHLC_FACT,
    SAME_BATCH_ORDER_UNPROVEN,
    S1_ABSENCE_REQUIRES_CLOSED_DOMAIN,
    S1_DUPLICATE_OBSERVATION_KEY,
    S1_OUT_OF_ORDER_OBSERVATION,
    S1_GRID_CONTIGUITY_UNPROVEN,
    S1_SCHEMA_VERSION_MISMATCH,
    S1_UNSUPPORTED_DESCRIPTOR_INPUT,
    UNAVAILABLE,
    UNBOUNDED_REFINEMENT,
    ZERO_DENOMINATOR,
    AcceptedBarFacts,
    CausalObservationStream,
    DeclaredGrid,
    DescriptorSpec,
    PublishedOhlcBarFact,
    bar_derivative_metrics,
    intrabar_path_metrics,
    key_axis,
    key_serialization,
    metric_payload,
    pair_adjacency_kind,
    pair_direction,
    exact_metric,
    pair_metrics,
    safe_ratio,
)
from trading_system.market_understanding.records import (
    EventKind,
    EventRecord,
    PublishedRecord,
    freeze_payload,
    payload_canonical_view,
)

# ---------------------------------------------------------------------------
# S1 path-schema identity + reused Stage 4C-1 tokens (one authority name)
# ---------------------------------------------------------------------------

S1_SCHEMA_IDENTITY: Final[SchemaIdentity] = SchemaIdentity("MUF_S1_PATH_SCHEMAS", "V1")

# S1 emits its own record names (official tokens stay at the stage layer).
S1_OBSERVATION_GRID_KEYS: Final[str] = "S1_OBSERVATION_GRID_KEYS"
S1_EXPECTED_GRID_KEY_ABSENCE_RECORD: Final[str] = "S1_EXPECTED_GRID_KEY_ABSENCE"
S1_OBSERVED_ADJACENCY_DESCRIPTOR: Final[str] = "S1_OBSERVED_ADJACENCY_DESCRIPTOR"
S1_GRID_CONTIGUITY_DESCRIPTOR: Final[str] = "S1_GRID_CONTIGUITY_DESCRIPTOR"
S1_PAIR_METRIC_BUNDLE: Final[str] = "S1_PAIR_METRIC_BUNDLE"
S1_PAIR_DISPLACEMENT_WITH_DIRECTION: Final[str] = "S1_PAIR_DISPLACEMENT_WITH_DIRECTION"

# RC1 token names (absence-branch witness pair-tuple reuse).
EXPECTED_GRID_KEY_NOT_OBSERVED: Final[str] = "EXPECTED_GRID_KEY_NOT_OBSERVED"
S1_TYPED_STATE_UNAVAILABLE: Final[TypedState] = TypedState.UNAVAILABLE

# S1-only missing-state vocabulary (RC1 line B).
S1_NOT_YET_OBSERVED: Final[str] = "S1_NOT_YET_OBSERVED"
S1_MISSING_STATES: Final[Tuple[str, ...]] = (
    S1_NOT_YET_OBSERVED,
    EXPECTED_GRID_KEY_NOT_OBSERVED,
    S1_ABSENCE_REQUIRES_CLOSED_DOMAIN,
)

# The single canonical Stage 4C-1 authority module name (name law; no parallel).
STAGE_4C1_AUTHORITY_MODULE: Final[str] = (
    "trading_system.research.trajectory.trajectory_stage4c"
)

_GRID_STATUS_TOKENS: Final[FrozenSet[str]] = frozenset(
    {
        GRID_OBSERVATIONS_COMPLETE,
        GRID_OBSERVATIONS_MISSING,
        OFF_GRID_OBSERVATIONS_PRESENT,
        GRID_OBSERVATIONS_DEFECT_BOTH,
        GRID_COMPLETENESS_UNKNOWN,
    }
)
_COVERAGE_STATUS_TOKENS: Final[FrozenSet[str]] = frozenset({COVERAGE_UNAVAILABLE})

_OHLC_FORMULA: Final[str] = (
    "close_displacement := close_right - close_left; "
    "close_path_step := abs(close_right - close_left); "
    "direction := UP iff close_displacement > 0, DOWN iff close_displacement < 0, "
    "FLAT iff close_displacement == 0 — ONLY where A-before-B chronology is proven; "
    "otherwise typed UNDEFINED(SAME_BATCH_ORDER_UNPROVEN)"
)
_CHRONOLOGY_CAVEAT: Final[str] = (
    "A-before-B chronology unproven where batch relation is not DIFFERENT_BATCH "
    "or causal positions are equal: deterministic_sequence never creates chronology"
)


def require_s1_schema_version(schema_identity: SchemaIdentity) -> None:
    """Fail closed on any S1 schema-version drift (S1_SCHEMA_VERSION_MISMATCH)."""
    if not isinstance(schema_identity, SchemaIdentity):
        raise SchemaViolation("schema_identity must be a SchemaIdentity")
    if schema_identity.as_payload() != S1_SCHEMA_IDENTITY.as_payload():
        raise SchemaViolation(f"{S1_SCHEMA_VERSION_MISMATCH}: {schema_identity!r}")


def bar_provenance(fact: PublishedOhlcBarFact) -> Mapping[str, Any]:
    """Required price-fact provenance (source/dataset identity + published bar ref)."""
    return fact.provenance


def observe_complete_bar_event(
    stream: CausalObservationStream, fact: PublishedOhlcBarFact
) -> AcceptedBarFacts:
    """THE canonical S1 completed-observation event name (append-only)."""
    if not isinstance(stream, CausalObservationStream):
        raise SchemaViolation("observe_complete_bar_event requires a CausalObservationStream")
    return stream.accept(fact)


# ---------------------------------------------------------------------------
# Closed-domain absence authority (RC1: witness over reused stage tokens)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExpectedGridAbsenceWitness:
    """Witnessed Stage 4C-1 completeness authority for expected-grid absence.

    Built from EXPLICITLY witnessed stage tokens (line C2 provenance). S1
    validates the witnessed token fields and their pair-tuple reuse
    (``EXPECTED_GRID_KEY_NOT_OBSERVED`` + availability key + typed
    ``S1_TYPED_STATE_UNAVAILABLE``); it never recomputes the timestamp-SET vs
    declared-grid comparison (no authority reimplementation).
    """

    token_identity: str
    coverage_status: str
    coverage_requires_expectations_met: bool
    origin_module: str
    witnessed_at_key: InformationKey

    def __post_init__(self) -> None:
        require_string(self.token_identity, "token_identity")
        require_string(self.coverage_status, "coverage_status")
        if self.token_identity not in _GRID_STATUS_TOKENS:
            raise SchemaViolation("witness token_identity must be a Stage 4C-1 grid token")
        if self.coverage_status not in _COVERAGE_STATUS_TOKENS:
            raise SchemaViolation("witness coverage_status must be a Stage 4C-1 coverage token")
        if not isinstance(self.coverage_requires_expectations_met, bool):
            raise SchemaViolation("coverage_requires_expectations_met must be a bool")
        if self.origin_module != STAGE_4C1_AUTHORITY_MODULE:
            raise SchemaViolation("absence authority must witness the Stage 4C-1 module")
        if not isinstance(self.witnessed_at_key, InformationKey):
            raise SchemaViolation("witnessed_at_key must be an InformationKey")

    @property
    def proves_complete_coverage(self) -> bool:
        """WITNESSED complete-coverage check (validated, never recomputed).

        Rule (staged completeness contract): GRID_OBSERVATIONS_COMPLETE, or the
        COVERAGE_UNAVAILABLE branch with OFF_GRID_OBSERVATIONS_PRESENT and the
        explicitly asserted expectation claim.
        """
        if self.token_identity == GRID_OBSERVATIONS_COMPLETE:
            return True
        return (
            self.coverage_status == COVERAGE_UNAVAILABLE
            and self.token_identity == OFF_GRID_OBSERVATIONS_PRESENT
            and self.coverage_requires_expectations_met
        )


def absence_pair_tuple(
    availability_key: InformationKey,
) -> Tuple[str, InformationKey, TypedState]:
    """RC1 pair-tuple reuse: (reason, availability key, typed S1 state)."""
    return (EXPECTED_GRID_KEY_NOT_OBSERVED, availability_key, S1_TYPED_STATE_UNAVAILABLE)


@dataclass(frozen=True)
class StreamCheckpoint:
    """Bounded-memory checkpoint over incremental stream state (O(1) verify)."""

    accepted_count: int
    last_accepted_key: Optional[InformationKey]
    observed_close_path_length: float
    grid_contiguous_close_path_length: float
    running_high_so_far: Union[float, TypedState]
    running_low_so_far: Union[float, TypedState]

    def __post_init__(self) -> None:
        if isinstance(self.accepted_count, bool) or not isinstance(self.accepted_count, int):
            raise SchemaViolation("accepted_count must be an int")
        if self.accepted_count < 0:
            raise SchemaViolation("accepted_count must be nonnegative")
        if self.last_accepted_key is not None and not isinstance(
            self.last_accepted_key, InformationKey
        ):
            raise SchemaViolation("last_accepted_key must be an InformationKey or None")
        for name in ("observed_close_path_length", "grid_contiguous_close_path_length"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SchemaViolation(f"{name} must be numeric")


def capture_checkpoint(stream: CausalObservationStream) -> StreamCheckpoint:
    """Snapshot the stream's incremental sufficient state (no history copy)."""
    if not isinstance(stream, CausalObservationStream):
        raise SchemaViolation("capture_checkpoint requires a CausalObservationStream")
    high = stream.running_high_state
    low = stream.running_low_state
    return StreamCheckpoint(
        accepted_count=stream.accepted_count,
        last_accepted_key=stream.last_accepted_key,
        observed_close_path_length=stream.observed_close_path_length,
        grid_contiguous_close_path_length=stream.grid_contiguous_close_path_length,
        running_high_so_far=high.value if high is not None else TypedState.NOT_CONFIGURED,
        running_low_so_far=low.value if low is not None else TypedState.NOT_CONFIGURED,
    )


def verify_checkpoint_continuity(
    stream: CausalObservationStream, checkpoint: StreamCheckpoint
) -> None:
    """O(1) continuity verification: checkpoint must be an exact stream prefix state."""
    if not isinstance(stream, CausalObservationStream):
        raise SchemaViolation("verify_checkpoint_continuity requires a CausalObservationStream")
    if not isinstance(checkpoint, StreamCheckpoint):
        raise SchemaViolation("verify_checkpoint_continuity requires a StreamCheckpoint")
    current = capture_checkpoint(stream)
    if current.accepted_count < checkpoint.accepted_count:
        raise SchemaViolation("checkpoint ahead of stream state")
    if checkpoint.accepted_count > 0 and checkpoint.last_accepted_key is None:
        raise SchemaViolation("nonempty checkpoint requires a last accepted key")
    if checkpoint.accepted_count > 0:
        keys = stream.accepted_keys
        if keys[checkpoint.accepted_count - 1] != checkpoint.last_accepted_key:
            raise SchemaViolation("checkpoint key mismatch (history reconstruction fault)")


# ---------------------------------------------------------------------------
# Cadence partitioning (expected slots vs accepted observations)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExactSlotCadence:
    """Exact expected-key cadence contract (integrity-checked; no interpolation)."""

    cadence_identity: str
    expected_keys: Tuple[InformationKey, ...]

    def __post_init__(self) -> None:
        require_string(self.cadence_identity, "cadence_identity")
        if not self.expected_keys:
            raise SchemaViolation("cadence requires expected keys")
        seen: Dict[InformationKey, bool] = {}
        previous: Optional[InformationKey] = None
        for key in self.expected_keys:
            if not isinstance(key, InformationKey):
                raise SchemaViolation("expected keys must be InformationKey instances")
            if key in seen:
                raise SchemaViolation(f"{S1_DUPLICATE_OBSERVATION_KEY}: {key!r}")
            if previous is not None and not previous < key:
                raise SchemaViolation("cadence expected keys must be strictly increasing")
            seen[key] = True
            previous = key
        object.__setattr__(self, "_positions", dict(seen))

    def is_expected(self, key: InformationKey) -> bool:
        return key in self._positions


def s1_scheduled_slot_coverage(
    received_keys: Tuple[InformationKey, ...],
    scheduled_keys: Tuple[InformationKey, ...],
) -> Mapping[InformationKey, Union[str, TypedState]]:
    """S1-only scheduled-slot coverage (pure). Composes with stage tokens externally.

    Present values use ``S1_NOT_YET_OBSERVED`` before observation and
    ``EXPECTED_GRID_KEY_NOT_OBSERVED`` after a witnessed closed domain (composed
    at the schema layer; never computed here).
    """
    received: Dict[InformationKey, bool] = {}
    for key in received_keys:
        if not isinstance(key, InformationKey):
            raise SchemaViolation("received keys must be InformationKey instances")
        if key in received:
            raise SchemaViolation(f"{S1_DUPLICATE_OBSERVATION_KEY}: {key!r}")
        received[key] = True
    result: Dict[InformationKey, Union[str, TypedState]] = {}
    for key in scheduled_keys:
        result[key] = "OBSERVED" if key in received else S1_NOT_YET_OBSERVED
    return result


def cadence_partition(
    received_keys: Tuple[InformationKey, ...],
    cadence: ExactSlotCadence,
) -> Mapping[str, Any]:
    """Partition observations against the cadence contract.

    Returns at_expected_slot / received_at_unexpected_slot / expected_not_observed /
    scheduled_slot_status_map. Fails closed on duplicate keys
    (``S1_DUPLICATE_OBSERVATION_KEY``), out-of-order observations
    (``S1_OUT_OF_ORDER_OBSERVATION``) and mixed axes
    (``S1_GRID_CONTIGUITY_UNPROVEN``).
    """
    if not isinstance(cadence, ExactSlotCadence):
        raise SchemaViolation("cadence_partition requires an ExactSlotCadence")
    previous: Optional[InformationKey] = None
    axis: Optional[InformationAxis] = None
    received: Dict[InformationKey, bool] = {}
    at_expected = []
    unexpected = []
    for key in received_keys:
        if not isinstance(key, InformationKey):
            raise SchemaViolation("received keys must be InformationKey instances")
        if key in received:
            raise SchemaViolation(f"{S1_DUPLICATE_OBSERVATION_KEY}: {key!r}")
        key_axis_value = key_axis(key)
        if axis is None:
            axis = key_axis_value
        elif key_axis_value is not axis:
            raise SchemaViolation(f"{S1_GRID_CONTIGUITY_UNPROVEN}: mixed axes")
        if previous is not None and not key > previous:
            raise SchemaViolation(f"{S1_OUT_OF_ORDER_OBSERVATION}: {key!r}")
        received[key] = True
        if cadence.is_expected(key):
            at_expected.append(key)
        else:
            unexpected.append(key)
        previous = key
    expected_not_observed = tuple(
        key for key in cadence.expected_keys if key not in received
    )
    status_map: Dict[InformationKey, Union[str, TypedState]] = {}
    for key in cadence.expected_keys:
        status_map[key] = "OBSERVED" if key in received else TypedState.UNAVAILABLE
    return {
        "at_expected_slot": tuple(at_expected),
        "received_at_unexpected_slot": tuple(unexpected),
        "expected_not_observed": expected_not_observed,
        "scheduled_slot_status_map": status_map,
    }


# ---------------------------------------------------------------------------
# Policy-free descriptor input normalization (typed UNDEFINED(ZERO_DENOMINATOR))
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DescriptorInputState:
    """Normalized factual descriptor input state (S1: running-only, policy-free)."""

    descriptor_name: str
    descriptor_identity: str
    value: Union[float, int, TypedState]
    semantics: str
    denominator_semantics: Union[str, TypedState]
    missingness: Union[str, TypedState]

    def __post_init__(self) -> None:
        require_string(self.descriptor_name, "descriptor_name")
        require_string(self.descriptor_identity, "descriptor_identity")
        if self.semantics not in METRIC_SEMANTICS:
            raise SchemaViolation(f"unknown metric semantics: {self.semantics!r}")


def normalize_descriptor_inputs(
    spec: DescriptorSpec,
    value: Union[float, int, TypedState],
    *,
    denominator: Union[float, int, TypedState, None] = None,
) -> DescriptorInputState:
    """Normalize one factual descriptor input with typed denominator semantics.

    Zero denominators produce typed ``UNDEFINED`` with reason
    ``ZERO_DENOMINATOR``. No epsilon. No infinity. No policy inputs exist.
    """
    if not isinstance(spec, DescriptorSpec):
        raise SchemaViolation("normalize_descriptor_inputs requires a DescriptorSpec")
    if spec.stage not in DESCRIPTOR_STAGES:
        raise SchemaViolation(f"{S1_UNSUPPORTED_DESCRIPTOR_INPUT}: stage {spec.stage!r}")
    if isinstance(value, bool):
        raise SchemaViolation("descriptor value must be numeric or TypedState")
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise SchemaViolation("descriptor values must be finite")
        semantics = EXACT
        typed_value: Union[float, int, TypedState] = value
    elif isinstance(value, TypedState):
        semantics = UNAVAILABLE
        typed_value = value
    else:
        raise SchemaViolation("descriptor value must be numeric or TypedState")
    if denominator is None or isinstance(denominator, TypedState):
        denominator_semantics: Union[str, TypedState] = (
            spec.denominator_semantics
            if denominator is None
            else denominator
        )
    else:
        ratio = safe_ratio(1, denominator)
        denominator_semantics = (
            TypedState.UNDEFINED if isinstance(ratio, TypedState) else EXACT
        )
    return DescriptorInputState(
        descriptor_name=spec.name,
        descriptor_identity=spec.descriptor_identity,
        value=typed_value,
        semantics=semantics,
        denominator_semantics=denominator_semantics,
        missingness=spec.missingness,
    )


# ---------------------------------------------------------------------------
# Pair composition records (recorded_kind / recorded_property wording)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PairSchemaRecords:
    """The four S1 pair-composition records (SL-6)."""

    adjacency_descriptor: PublishedRecord
    grid_contiguity_descriptor: PublishedRecord
    metric_bundle_record: PublishedRecord
    displacement_with_direction_record: PublishedRecord


def _pair_identity(
    artifact_type: str, left: PublishedOhlcBarFact, right: PublishedOhlcBarFact, extra: str
) -> str:
    schema = ArtifactIdentitySchema(
        artifact_type=artifact_type,
        schema_identity=S1_SCHEMA_IDENTITY,
        identity_defining_fields=("origin_key", "adjacent_key", "timeline_id", "recorded_kind"),
    )
    return canonical_artifact_identity(
        schema,
        identity_payload={
            "origin_key": "|".join(key_serialization(left.availability_key)),
            "adjacent_key": "|".join(key_serialization(right.availability_key)),
            "timeline_id": right.availability_key.timeline_id,
            "recorded_kind": extra,
        },
    )


def pair_path_schemas(
    left: PublishedOhlcBarFact,
    right: PublishedOhlcBarFact,
    *,
    source_identity: SchemaIdentity,
    dataset_identity: str,
    declared_grid: Optional[DeclaredGrid] = None,
) -> PairSchemaRecords:
    """Compose the S1 pair records (O(1) per pair; no history access)."""
    if not isinstance(left, PublishedOhlcBarFact) or not isinstance(right, PublishedOhlcBarFact):
        raise SchemaViolation("pair_path_schemas requires PublishedOhlcBarFact operands")
    require_string(dataset_identity, "dataset_identity")
    require_s1_schema_version(S1_SCHEMA_IDENTITY)
    metrics = pair_metrics(left, right)
    direction = pair_direction(left, right)
    adjacency_kind = pair_adjacency_kind(left, right, declared_grid)
    timeline_id = right.availability_key.timeline_id
    key_pair = {
        "origin_key": left.availability_key,
        "adjacent_key": right.availability_key,
        "timeline_id": timeline_id,
        "provenance_refs": (
            left.published_bar_record_ref,
            right.published_bar_record_ref,
        ),
        "dataset_identity": dataset_identity,
    }

    adjacency_descriptor = PublishedRecord(
        record_identity=_pair_identity(
            S1_OBSERVED_ADJACENCY_DESCRIPTOR, left, right, adjacency_kind
        ),
        record_type=S1_OBSERVED_ADJACENCY_DESCRIPTOR,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=timeline_id,
        availability_key=right.availability_key,
        content={
            **key_pair,
            "recorded_kind": adjacency_kind,
            "recorded_property": (
                "STREAM_CAUSAL_ADJACENCY"
                if adjacency_kind == ADJACENCY_OBSERVATION_ADJACENT
                else "PROVEN_GRID_CONTIGUITY_ADJACENCY"
            ),
        },
    )
    grid_proven = adjacency_kind == ADJACENCY_GRID_CONTIGUOUS
    grid_contiguity_descriptor = PublishedRecord(
        record_identity=_pair_identity(
            S1_GRID_CONTIGUITY_DESCRIPTOR,
            left,
            right,
            "GRID_CONTIGUOUS" if grid_proven else "NOT_PROVEN",
        ),
        record_type=S1_GRID_CONTIGUITY_DESCRIPTOR,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=timeline_id,
        availability_key=right.availability_key,
        content={
            **key_pair,
            "recorded_kind": "GRID_CONTIGUOUS" if grid_proven else "NOT_PROVEN",
            "recorded_property": (
                "GRID_CONTIGUITY_PROVEN_BY_DECLARED_CADENCE"
                if grid_proven
                else f"{S1_GRID_CONTIGUITY_UNPROVEN}: no declared contiguity proof"
            ),
        },
    )
    derivatives = dict(bar_derivative_metrics(right))
    bundle_metrics = {
        "close_displacement": metric_payload(metrics["close_displacement"]),
        "close_path_step": metric_payload(metrics["close_path_step"]),
        "bar_range": metric_payload(derivatives["bar_range"]),
        "open_close_displacement": metric_payload(derivatives["open_close_displacement"]),
        "upper_wick": metric_payload(derivatives["upper_wick"]),
        "lower_wick": metric_payload(derivatives["lower_wick"]),
        "bar_count": metric_payload(_exact_pair_count()),
        "bar_count_on_grid": metric_payload(_pair_grid_count(grid_proven)),
    }
    metric_bundle_record = PublishedRecord(
        record_identity=_pair_identity(S1_PAIR_METRIC_BUNDLE, left, right, "PAIR_FACTS"),
        record_type=S1_PAIR_METRIC_BUNDLE,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=timeline_id,
        availability_key=right.availability_key,
        content={**key_pair, "metrics": bundle_metrics},
    )
    displacement_with_direction_record = PublishedRecord(
        record_identity=_pair_identity(
            S1_PAIR_DISPLACEMENT_WITH_DIRECTION, left, right, "SIGNED_FACTS"
        ),
        record_type=S1_PAIR_DISPLACEMENT_WITH_DIRECTION,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=timeline_id,
        availability_key=right.availability_key,
        content={
            **key_pair,
            "formulas": _OHLC_FORMULA,
            "chronology_caveat": _CHRONOLOGY_CAVEAT,
            "close_displacement": metric_payload(metrics["close_displacement"]),
            "direction": direction,
            "intrabar_exact": metric_payload(
                intrabar_path_metrics(right)["intrabar_path_length_exact"]
            ),
            "intrabar_bound_basis": DISCRETE_TV_TRIANGLE_INEQUALITY,
        },
    )
    return PairSchemaRecords(
        adjacency_descriptor=adjacency_descriptor,
        grid_contiguity_descriptor=grid_contiguity_descriptor,
        metric_bundle_record=metric_bundle_record,
        displacement_with_direction_record=displacement_with_direction_record,
    )


def _exact_pair_count():
    return exact_metric(1)


def _pair_grid_count(grid_proven: bool):
    return exact_metric(1 if grid_proven else 0)


# ---------------------------------------------------------------------------
# Expected-grid absence records + observed grid key set records
# ---------------------------------------------------------------------------


def expected_grid_absence_record(
    *,
    declared_grid: DeclaredGrid,
    availability_key: InformationKey,
    grid_key: InformationKey,
    witness: ExpectedGridAbsenceWitness,
) -> PublishedRecord:
    """RC1 absence record: witness-gated, pair-tuple reuse, typed UNAVAILABLE.

    Without a witnessed complete-coverage token the record cannot exist
    (``S1_ABSENCE_REQUIRES_CLOSED_DOMAIN``). The record never interprets the
    price path and never synthesizes a bar for the missing slot.
    """
    if not isinstance(declared_grid, DeclaredGrid):
        raise SchemaViolation("declared_grid must be a DeclaredGrid")
    if not isinstance(witness, ExpectedGridAbsenceWitness):
        raise SchemaViolation(f"{S1_ABSENCE_REQUIRES_CLOSED_DOMAIN}: witness required")
    if not witness.proves_complete_coverage:
        raise SchemaViolation(f"{S1_ABSENCE_REQUIRES_CLOSED_DOMAIN}: coverage not proven")
    if not isinstance(grid_key, InformationKey):
        raise SchemaViolation("grid_key must be an InformationKey")
    if not isinstance(availability_key, InformationKey):
        raise SchemaViolation("availability_key must be an InformationKey")
    if not declared_grid.is_member(grid_key):
        raise SchemaViolation("grid_key must belong to the declared grid")
    reason, paired_key, typed_state = absence_pair_tuple(availability_key)
    schema = ArtifactIdentitySchema(
        artifact_type="MUF_S1_EXPECTED_GRID_KEY_ABSENCE",
        schema_identity=S1_SCHEMA_IDENTITY,
        identity_defining_fields=("grid_key", "availability_key", "timeline_id", "reason"),
    )
    return PublishedRecord(
        record_identity=canonical_artifact_identity(
            schema,
            identity_payload={
                "grid_key": "|".join(key_serialization(grid_key)),
                "availability_key": "|".join(key_serialization(availability_key)),
                "timeline_id": availability_key.timeline_id,
                "reason": reason,
            },
        ),
        record_type=S1_EXPECTED_GRID_KEY_ABSENCE_RECORD,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=availability_key.timeline_id,
        availability_key=availability_key,
        content={
            "grid_key": grid_key,
            "availability_key": availability_key,
            "absence_pair_tuple": (reason, paired_key, typed_state),
            "missing_observation_reason": reason,
            "typed_state": typed_state,
            "witness_token_identity": witness.token_identity,
            "witness_origin_module": witness.origin_module,
            "provenance": "Stage 4C-1 completeness tokens (reused; witness-based)",
        },
    )


def observed_grid_keys_record(
    *,
    declared_grid: DeclaredGrid,
    availability_key: InformationKey,
    accepted_keys: Tuple[InformationKey, ...],
) -> PublishedRecord:
    """S1_OBSERVATION_GRID_KEYS: observed accepted keys restricted to the grid."""
    if not isinstance(declared_grid, DeclaredGrid):
        raise SchemaViolation("declared_grid must be a DeclaredGrid")
    observed = tuple(key for key in accepted_keys if declared_grid.is_member(key))
    schema = ArtifactIdentitySchema(
        artifact_type="MUF_S1_OBSERVATION_GRID_KEYS",
        schema_identity=S1_SCHEMA_IDENTITY,
        identity_defining_fields=("availability_key", "timeline_id", "cadence_contract_identity"),
    )
    return PublishedRecord(
        record_identity=canonical_artifact_identity(
            schema,
            identity_payload={
                "availability_key": "|".join(key_serialization(availability_key)),
                "timeline_id": availability_key.timeline_id,
                "cadence_contract_identity": declared_grid.cadence_contract_identity,
            },
        ),
        record_type=S1_OBSERVATION_GRID_KEYS,
        schema_identity=S1_SCHEMA_IDENTITY,
        timeline_id=availability_key.timeline_id,
        availability_key=availability_key,
        content={
            "cadence_contract_identity": declared_grid.cadence_contract_identity,
            "observed_grid_keys": observed,
            "observed_count": len(observed),
        },
    )


# ===========================================================================
# S1 schema foundations (PATCH P1) — DEFINE SCHEMAS ONLY; never populated.
#
# Accepted contract: S1 DEFINES these four schema foundations and DOES NOT
# populate market episodes or narratives. Episode anchor identity is structurally
# separate from membership (EpisodeAnchorIdentity != EpisodeMembershipEvent).
# No episode population engine exists. No independence claim exists.
# RESEARCH-DEBT-024 remains OPEN.
# ===========================================================================

CAUSAL_EPISODE_RECORD_TYPE: Final[str] = "S1_CAUSAL_EPISODE_RECORD"
EPISODE_MEMBERSHIP_EVENT_TYPE: Final[str] = "S1_EPISODE_MEMBERSHIP_EVENT"
MARKET_STATE_TRANSITION_RECORD_TYPE: Final[str] = "S1_MARKET_STATE_TRANSITION_RECORD"
EXPLANATION_RECORD_TYPE: Final[str] = "S1_EXPLANATION_RECORD"

# Schema 3 state kinds: literal factual states or descriptor deltas ONLY.
STATE_KIND_LITERAL_FACTUAL: Final[str] = "LITERAL_FACTUAL_STATE"
STATE_KIND_DESCRIPTOR_DELTA: Final[str] = "DESCRIPTOR_DELTA"
TRANSITION_STATE_KINDS: Final[Tuple[str, ...]] = (
    STATE_KIND_LITERAL_FACTUAL,
    STATE_KIND_DESCRIPTOR_DELTA,
)
POLICY_ARTIFACT_NOT_CONFIGURED: Final[TypedState] = TypedState.NOT_CONFIGURED

# Schema 4: allowed explanation states (closed set; exactly these four).
EXPLANATION_STATE_MONITORING: Final[str] = "MONITORING"
EXPLANATION_STATE_PATTERN_REQUIREMENTS_SATISFIED: Final[str] = "PATTERN_REQUIREMENTS_SATISFIED"
EXPLANATION_STATE_CONTRADICTED: Final[str] = "CONTRADICTED"
EXPLANATION_STATE_SUPERSEDED: Final[str] = "SUPERSEDED"
EXPLANATION_STATES: Final[Tuple[str, ...]] = (
    EXPLANATION_STATE_MONITORING,
    EXPLANATION_STATE_PATTERN_REQUIREMENTS_SATISFIED,
    EXPLANATION_STATE_CONTRADICTED,
    EXPLANATION_STATE_SUPERSEDED,
)
S1_REJECTED_EXPLANATION_STATES: Final[Tuple[str, ...]] = (
    "PROBABLE",
    "LIKELY",
    "SUPPORTED",
    "WINNING_EXPLANATION",
)

# Forbidden schema fields across all four foundations (fail closed).
FORBIDDEN_SCHEMA_FIELDS: Final[FrozenSet[str]] = frozenset(
    {
        "membership_refs",
        "probability",
        "weight",
        "score",
        "likelihood",
        "predictive_support",
        "winner",
        "threshold",
        "regime",
        "policy_inference",
    }
)

# Market-interpretation / threshold-regime tokens: forbidden in schema-3 states.
_STATE_TOKEN_BANNED: Final[FrozenSet[str]] = frozenset(
    {
        "REGIME",
        "THRESHOLD",
        "POLICY",
        "PROB",
        "LIKELI",
        "SCORE",
        "WEIGHT",
        "PREDICT",
        "WINNER",
        "BULL",
        "BEAR",
        "TREND",
        "SIGNAL",
    }
)

_EPISODE_ALLOWED_FIELDS: Final[FrozenSet[str]] = frozenset(
    {
        "schema_identity",
        "timeline_id",
        "axis",
        "anchor_information_key",
        "anchor_rule_version",
        "anchor_fact_ref",
        "provenance",
        "availability_information_key",
    }
)
_MEMBERSHIP_ALLOWED_FIELDS: Final[FrozenSet[str]] = frozenset(
    {
        "schema_identity",
        "episode_id",
        "member_fact_ref",
        "member_fact_availability_key",
        "membership_information_key",
        "provenance",
    }
)
_TRANSITION_ALLOWED_FIELDS: Final[FrozenSet[str]] = frozenset(
    {
        "schema_identity",
        "timeline_id",
        "from_state",
        "to_state",
        "state_kind",
        "descriptor_deltas",
        "policy_artifact_ref",
        "availability_information_key",
        "provenance",
    }
)
_EXPLANATION_ALLOWED_FIELDS: Final[FrozenSet[str]] = frozenset(
    {
        "schema_identity",
        "timeline_id",
        "state",
        "fact_refs",
        "availability_information_key",
        "provenance",
    }
)

_EPISODE_IDENTITY_SCHEMA: Final[ArtifactIdentitySchema] = ArtifactIdentitySchema(
    artifact_type="MUF_S1_CAUSAL_EPISODE",
    schema_identity=S1_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "anchor_fact_ref",
        "anchor_rule_version",
        "anchor_information_key",
    ),
)
_MEMBERSHIP_IDENTITY_SCHEMA: Final[ArtifactIdentitySchema] = ArtifactIdentitySchema(
    artifact_type="MUF_S1_EPISODE_MEMBERSHIP_EVENT",
    schema_identity=S1_SCHEMA_IDENTITY,
    identity_defining_fields=("episode_id", "member_fact_ref", "membership_information_key"),
)
_TRANSITION_IDENTITY_SCHEMA: Final[ArtifactIdentitySchema] = ArtifactIdentitySchema(
    artifact_type="MUF_S1_MARKET_STATE_TRANSITION",
    schema_identity=S1_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "from_state",
        "to_state",
        "state_kind",
        "availability_information_key",
    ),
)
_EXPLANATION_IDENTITY_SCHEMA: Final[ArtifactIdentitySchema] = ArtifactIdentitySchema(
    artifact_type="MUF_S1_EXPLANATION",
    schema_identity=S1_SCHEMA_IDENTITY,
    identity_defining_fields=("timeline_id", "state", "fact_refs", "availability_information_key"),
)


def _strict_fields(
    schema_name: str, allowed: FrozenSet[str], provided: Mapping[str, Any]
) -> Dict[str, Any]:
    """Fail closed on any unknown or forbidden schema field."""
    data = dict(provided)
    for name in data:
        if name == "membership_refs":
            raise SchemaViolation(
                f"{schema_name}: membership_refs is structurally forbidden "
                "(episode anchor facts never carry membership)"
            )
        if name not in allowed or name in FORBIDDEN_SCHEMA_FIELDS:
            raise SchemaViolation(f"{schema_name}: unknown/forbidden field {name!r}")
    return data


def _require_literal_state_token(value: str, field_name: str) -> None:
    """Schema-3 states must be literal factual tokens; no threshold/regime language."""
    require_string(value, field_name)
    upper = value.upper()
    for token in _STATE_TOKEN_BANNED:
        if token in upper:
            raise SchemaViolation(
                f"{field_name} {value!r}: threshold/regime/policy/interpretation tokens "
                "require a PolicyArtifact and remain NOT_CONFIGURED at S1"
            )


@dataclass(frozen=True)
class CausalEpisodeRecord:
    """Schema foundation 1: episode ANCHOR/creation facts only.

    Contains anchor/creation facts only. NEVER contains membership_refs.
    ``episode_identity`` is derived from anchor facts alone and structurally
    cannot depend on future membership. Schema definition only: no episode
    population engine, no independence claim (RESEARCH-DEBT-024 OPEN).
    """

    schema_identity: SchemaIdentity
    timeline_id: str
    axis: InformationAxis
    anchor_information_key: InformationKey
    anchor_rule_version: str
    anchor_fact_ref: str
    provenance: Mapping[str, Any]
    availability_information_key: InformationKey
    episode_identity: str

    def __post_init__(self) -> None:
        require_s1_schema_version(self.schema_identity)
        require_string(self.timeline_id, "timeline_id")
        if not isinstance(self.axis, InformationAxis):
            raise SchemaViolation("axis must be an InformationAxis")
        if not isinstance(self.anchor_information_key, InformationKey):
            raise SchemaViolation("anchor_information_key must be an InformationKey")
        if not isinstance(self.availability_information_key, InformationKey):
            raise SchemaViolation("availability_information_key must be an InformationKey")
        if self.anchor_information_key.timeline_id != self.timeline_id:
            raise SchemaViolation("anchor key timeline must match timeline_id")
        if self.availability_information_key.timeline_id != self.timeline_id:
            raise SchemaViolation("availability key timeline must match timeline_id")
        if key_axis(self.anchor_information_key) is not self.axis:
            raise SchemaViolation("axis binding must match the anchor key axis")
        require_string(self.anchor_rule_version, "anchor_rule_version")
        require_string(self.anchor_fact_ref, "anchor_fact_ref")
        object.__setattr__(self, "provenance", freeze_payload(dict(self.provenance), field_name="provenance"))
        require_visible_at(
            fact_key=self.anchor_information_key,
            at_key=self.availability_information_key,
        )
        expected = canonical_artifact_identity(
            _EPISODE_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "anchor_fact_ref": self.anchor_fact_ref,
                "anchor_rule_version": self.anchor_rule_version,
                "anchor_information_key": "|".join(key_serialization(self.anchor_information_key)),
            },
        )
        if self.episode_identity != expected:
            raise SchemaViolation(
                "episode_identity must be the anchor-derived canonical identity "
                "(membership can never change it)"
            )

    @classmethod
    def create(cls, **fields: Any) -> "CausalEpisodeRecord":
        """Strict factory: unknown fields fail closed; identity derives from anchor."""
        data = _strict_fields("CausalEpisodeRecord", _EPISODE_ALLOWED_FIELDS, fields)
        episode_identity = canonical_artifact_identity(
            _EPISODE_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": data["timeline_id"],
                "anchor_fact_ref": data["anchor_fact_ref"],
                "anchor_rule_version": data["anchor_rule_version"],
                "anchor_information_key": "|".join(
                    key_serialization(data["anchor_information_key"])
                ),
            },
        )
        return cls(episode_identity=episode_identity, **data)

    def as_record(self) -> PublishedRecord:
        """Immutable S0 published record (anchor facts only; no membership key exists)."""
        return PublishedRecord(
            record_identity=self.episode_identity,
            record_type=CAUSAL_EPISODE_RECORD_TYPE,
            schema_identity=S1_SCHEMA_IDENTITY,
            timeline_id=self.timeline_id,
            availability_key=self.availability_information_key,
            content={
                "episode_identity": self.episode_identity,
                "schema_identity": self.schema_identity.as_payload(),
                "timeline_id": self.timeline_id,
                "axis": self.axis,
                "anchor_information_key": self.anchor_information_key,
                "anchor_rule_version": self.anchor_rule_version,
                "anchor_fact_ref": self.anchor_fact_ref,
                "provenance": self.provenance,
                "availability_information_key": self.availability_information_key,
            },
        )


@dataclass(frozen=True)
class EpisodeMembershipEvent:
    """Schema foundation 2: separate append-only membership event.

    Adding membership NEVER changes ``episode_id``. Membership availability uses
    earliest-lawful InformationKey semantics (the membership key may never
    precede the member fact's availability). Historical membership events are
    immutable: lifecycle change == new event. No automatic market episode
    creation exists here.
    """

    schema_identity: SchemaIdentity
    episode_id: str
    member_fact_ref: str
    member_fact_availability_key: InformationKey
    membership_information_key: InformationKey
    provenance: Mapping[str, Any]
    event_identity: str

    def __post_init__(self) -> None:
        require_s1_schema_version(self.schema_identity)
        require_string(self.episode_id, "episode_id")
        require_string(self.member_fact_ref, "member_fact_ref")
        if not isinstance(self.member_fact_availability_key, InformationKey):
            raise SchemaViolation("member_fact_availability_key must be an InformationKey")
        if not isinstance(self.membership_information_key, InformationKey):
            raise SchemaViolation("membership_information_key must be an InformationKey")
        object.__setattr__(self, "provenance", freeze_payload(dict(self.provenance), field_name="provenance"))
        require_visible_at(
            fact_key=self.member_fact_availability_key,
            at_key=self.membership_information_key,
        )
        expected = canonical_artifact_identity(
            _MEMBERSHIP_IDENTITY_SCHEMA,
            identity_payload={
                "episode_id": self.episode_id,
                "member_fact_ref": self.member_fact_ref,
                "membership_information_key": "|".join(
                    key_serialization(self.membership_information_key)
                ),
            },
        )
        if self.event_identity != expected:
            raise SchemaViolation("event_identity must be the canonical membership-event identity")

    @classmethod
    def create(cls, **fields: Any) -> "EpisodeMembershipEvent":
        """Strict factory for one append-only membership event."""
        data = _strict_fields("EpisodeMembershipEvent", _MEMBERSHIP_ALLOWED_FIELDS, fields)
        event_identity = canonical_artifact_identity(
            _MEMBERSHIP_IDENTITY_SCHEMA,
            identity_payload={
                "episode_id": data["episode_id"],
                "member_fact_ref": data["member_fact_ref"],
                "membership_information_key": "|".join(
                    key_serialization(data["membership_information_key"])
                ),
            },
        )
        return cls(event_identity=event_identity, **data)

    def as_event_record(self) -> EventRecord:
        """Immutable S0 event record (EventKind.MEMBERSHIP_EVENT; append-only)."""
        return EventRecord(
            event_identity=self.event_identity,
            event_kind=EventKind.MEMBERSHIP_EVENT,
            subject_record_identity=self.episode_id,
            event_key=self.membership_information_key,
            event_payload={
                "schema_identity": self.schema_identity.as_payload(),
                "episode_id": self.episode_id,
                "member_fact_ref": self.member_fact_ref,
                "member_fact_availability_key": self.member_fact_availability_key,
                "membership_information_key": self.membership_information_key,
                "provenance": self.provenance,
                "event_identity": self.event_identity,
            },
        )


@dataclass(frozen=True)
class MarketStateTransitionRecord:
    """Schema foundation 3: literal factual states or descriptor deltas ONLY.

    No regime threshold. No policy inference. No probability. No market
    interpretation. Any threshold-derived regime requires a PolicyArtifact and
    remains ``NOT_CONFIGURED`` at S1.
    """

    schema_identity: SchemaIdentity
    timeline_id: str
    from_state: str
    to_state: str
    state_kind: str
    policy_artifact_ref: Union[str, TypedState]
    availability_information_key: InformationKey
    provenance: Mapping[str, Any]
    descriptor_deltas: Mapping[str, Any] = field(default_factory=dict)
    transition_identity: str = ""

    def __post_init__(self) -> None:
        require_s1_schema_version(self.schema_identity)
        require_string(self.timeline_id, "timeline_id")
        _require_literal_state_token(self.from_state, "from_state")
        _require_literal_state_token(self.to_state, "to_state")
        if self.state_kind not in TRANSITION_STATE_KINDS:
            raise SchemaViolation(
                f"state_kind {self.state_kind!r}: threshold-derived regimes require a "
                "PolicyArtifact and remain NOT_CONFIGURED at S1"
            )
        if not isinstance(self.availability_information_key, InformationKey):
            raise SchemaViolation("availability_information_key must be an InformationKey")
        if self.availability_information_key.timeline_id != self.timeline_id:
            raise SchemaViolation("availability key timeline must match timeline_id")
        if not isinstance(self.policy_artifact_ref, (str, TypedState)):
            raise SchemaViolation("policy_artifact_ref must be a string or TypedState")
        if self.policy_artifact_ref is not TypedState.NOT_CONFIGURED:
            raise SchemaViolation(
                "policy binding requires a PolicyArtifact and remains NOT_CONFIGURED at S1"
            )
        deltas = dict(self.descriptor_deltas)
        if self.state_kind == STATE_KIND_LITERAL_FACTUAL and deltas:
            raise SchemaViolation("literal factual transitions carry no descriptor deltas")
        for name in deltas:
            require_string(name, "descriptor delta name")
            value = deltas[name]
            if isinstance(value, bool) or not isinstance(value, (int, float, str, TypedState)):
                raise SchemaViolation("descriptor deltas must be numeric, textual or TypedState")
            if isinstance(value, float) and not math.isfinite(value):
                raise SchemaViolation("descriptor deltas must be finite")
        object.__setattr__(self, "descriptor_deltas", freeze_payload(deltas, field_name="descriptor_deltas"))
        object.__setattr__(self, "provenance", freeze_payload(dict(self.provenance), field_name="provenance"))
        expected = canonical_artifact_identity(
            _TRANSITION_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "from_state": self.from_state,
                "to_state": self.to_state,
                "state_kind": self.state_kind,
                "availability_information_key": "|".join(
                    key_serialization(self.availability_information_key)
                ),
            },
        )
        if not self.transition_identity:
            object.__setattr__(self, "transition_identity", expected)
        elif self.transition_identity != expected:
            raise SchemaViolation("transition_identity must be the canonical transition identity")

    @classmethod
    def create(cls, **fields: Any) -> "MarketStateTransitionRecord":
        """Strict factory: unknown fields fail closed; no policy inputs exist."""
        data = _strict_fields("MarketStateTransitionRecord", _TRANSITION_ALLOWED_FIELDS, fields)
        return cls(**data)

    def as_record(self) -> PublishedRecord:
        """Immutable S0 published record for the transition foundation."""
        return PublishedRecord(
            record_identity=self.transition_identity,
            record_type=MARKET_STATE_TRANSITION_RECORD_TYPE,
            schema_identity=S1_SCHEMA_IDENTITY,
            timeline_id=self.timeline_id,
            availability_key=self.availability_information_key,
            content={
                "transition_identity": self.transition_identity,
                "schema_identity": self.schema_identity.as_payload(),
                "timeline_id": self.timeline_id,
                "from_state": self.from_state,
                "to_state": self.to_state,
                "state_kind": self.state_kind,
                "descriptor_deltas": self.descriptor_deltas,
                "policy_artifact_ref": self.policy_artifact_ref,
                "availability_information_key": self.availability_information_key,
                "provenance": self.provenance,
            },
        )


@dataclass(frozen=True)
class ExplanationRecord:
    """Schema foundation 4: explanation states referencing FACTS ONLY.

    Allowed states exactly: MONITORING / PATTERN_REQUIREMENTS_SATISFIED /
    CONTRADICTED / SUPERSEDED. No probability, weight, score, predictive
    support, winner or likelihood. Schema definition only: no narrative
    population engine exists.
    """

    schema_identity: SchemaIdentity
    timeline_id: str
    state: str
    fact_refs: Tuple[str, ...]
    availability_information_key: InformationKey
    provenance: Mapping[str, Any]
    explanation_identity: str = ""

    def __post_init__(self) -> None:
        require_s1_schema_version(self.schema_identity)
        require_string(self.timeline_id, "timeline_id")
        if self.state not in EXPLANATION_STATES:
            raise SchemaViolation(
                f"explanation state {self.state!r} forbidden: allowed states are exactly "
                "MONITORING / PATTERN_REQUIREMENTS_SATISFIED / CONTRADICTED / SUPERSEDED "
                "(no probability, weight, score, predictive support, winner or likelihood)"
            )
        if not self.fact_refs or not isinstance(self.fact_refs, tuple):
            raise SchemaViolation("fact_refs must be a nonempty tuple of fact references")
        for ref in self.fact_refs:
            require_string(ref, "fact ref")
        if not isinstance(self.availability_information_key, InformationKey):
            raise SchemaViolation("availability_information_key must be an InformationKey")
        if self.availability_information_key.timeline_id != self.timeline_id:
            raise SchemaViolation("availability key timeline must match timeline_id")
        object.__setattr__(self, "provenance", freeze_payload(dict(self.provenance), field_name="provenance"))
        expected = canonical_artifact_identity(
            _EXPLANATION_IDENTITY_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "state": self.state,
                "fact_refs": "|".join(self.fact_refs),
                "availability_information_key": "|".join(
                    key_serialization(self.availability_information_key)
                ),
            },
        )
        if not self.explanation_identity:
            object.__setattr__(self, "explanation_identity", expected)
        elif self.explanation_identity != expected:
            raise SchemaViolation("explanation_identity must be the canonical explanation identity")

    @classmethod
    def create(cls, **fields: Any) -> "ExplanationRecord":
        """Strict factory: probability/weight/score/... fields fail closed."""
        data = _strict_fields("ExplanationRecord", _EXPLANATION_ALLOWED_FIELDS, fields)
        return cls(**data)

    def as_record(self) -> PublishedRecord:
        """Immutable S0 published record referencing facts only."""
        return PublishedRecord(
            record_identity=self.explanation_identity,
            record_type=EXPLANATION_RECORD_TYPE,
            schema_identity=S1_SCHEMA_IDENTITY,
            timeline_id=self.timeline_id,
            availability_key=self.availability_information_key,
            content={
                "explanation_identity": self.explanation_identity,
                "schema_identity": self.schema_identity.as_payload(),
                "timeline_id": self.timeline_id,
                "state": self.state,
                "fact_refs": self.fact_refs,
                "availability_information_key": self.availability_information_key,
                "provenance": self.provenance,
            },
        )
