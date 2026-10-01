"""MUF V1 S1: factual price-path primitives (additive S1 module).

Governing design authority (RC1 -> H1 -> S1 FINAL IMPLEMENTATION DESIGN).
This module implements ONLY factual, causal price-path representation:

    PRICE PATH FACT != TURNING POINT != WAVE != MARKET IMPORTANCE

Price semantics: ``PUBLISHED_OHLC_FACT`` — a published OHLC bar fact delivered
by an integrated source under its published source contract. Price fields NEVER
use flow-style ACTUAL/PROXY semantics; those labels are reserved for flow
contexts. The integrated source (currently Binance Spot kline) is the source of
supply, NOT the ontology: the price-path contract is source-general. Published
OHLC does NOT reconstruct the tick-by-tick market path; no claim is made that
any intermediate price was traded.

Observed intrabar chronology is UNPROVEN from OHLC alone: exact intrabar path
length is UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY); the retained lower bound
is a BOUND proved over discrete observed-price sequences by the triangle
inequality plus required extrema visitation (``DISCRETE_TV_TRIANGLE_INEQUALITY``);
the upper bound is UNAVAILABLE.

The accepted observation stream is strictly causal under public CLOSED
InformationKey semantics: a new key must be lawfully strictly greater than the
previous accepted key; duplicates and out-of-order keys are REJECTED and input
is never silently sorted. OBSERVATION_ADJACENT means consecutive accepted
observations only; GRID_CONTIGUOUS is a separate property proven through a
declared grid contract. Mechanical processing order is never market chronology;
within an unproven same-batch causal coordinate the signed displacement is
UNDEFINED(SAME_BATCH_ORDER_UNPROVEN).

Running extremes are RUNNING_EXTREME prefix facts (never turning points). Tie
origins form an UNORDERED SEMANTIC SET: any canonical storage ordering is
serialization-only and explicitly non-semantic; no winner/first origin exists;
deterministic_sequence never establishes a semantic winner.

Complexity: O(1) amortized fact computation per accepted observation, O(n)
total, with incremental sufficient state; running-extreme tie sets are O(k)
memory with NO arbitrary truncation. Published S1 records are immutable S0
records over frozen payloads; evolution is a new record/event only.

S1 defines schema foundations only; it does NOT populate market episodes or
narratives. RESEARCH-DEBT-024 remains OPEN: no statistical independence claim
exists anywhere in S1.
"""
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, Final, FrozenSet, Mapping, Optional, Tuple, Union

from trading_system.research.information_time import InformationKey, InformationPhase

from trading_system.market_understanding.availability import (
    BatchRelation,
    InformationAxis,
    InformationBatchKey,
    information_batch_relation,
)
from trading_system.market_understanding.contracts import (
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    require_string,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.records import PublishedRecord

# ---------------------------------------------------------------------------
# S1 metric semantics vocabulary (design: every metric declares its semantics)
# ---------------------------------------------------------------------------

EXACT: Final[str] = "EXACT"
BOUND: Final[str] = "BOUND"
PROXY: Final[str] = "PROXY"
UNAVAILABLE: Final[str] = "UNAVAILABLE"

METRIC_SEMANTICS: Final[Tuple[str, ...]] = (EXACT, BOUND, PROXY, UNAVAILABLE)

# Typed reasons (closed vocabulary; fail-closed on anything else)
AMBIGUOUS_INTRABAR_CHRONOLOGY: Final[str] = "AMBIGUOUS_INTRABAR_CHRONOLOGY"
UNBOUNDED_REFINEMENT: Final[str] = "UNBOUNDED_REFINEMENT"
NOT_TIME_INDEXED: Final[str] = "NOT_TIME_INDEXED"
ZERO_DENOMINATOR: Final[str] = "ZERO_DENOMINATOR"
SAME_BATCH_ORDER_UNPROVEN: Final[str] = "SAME_BATCH_ORDER_UNPROVEN"
GRID_OBSERVATION_NOT_PROVEN_CONTIGUOUS: Final[str] = "GRID_OBSERVATION_NOT_PROVEN_CONTIGUOUS"

DISCRETE_TV_TRIANGLE_INEQUALITY: Final[str] = "DISCRETE_TV_TRIANGLE_INEQUALITY"

# Direction vocabulary (observed close displacement only — never market language)
DIRECTION_UP: Final[str] = "UP"
DIRECTION_DOWN: Final[str] = "DOWN"
DIRECTION_FLAT: Final[str] = "FLAT"

# Adjacency kinds (H1-2): stream-causal adjacency vs proven grid contiguity
ADJACENCY_OBSERVATION_ADJACENT: Final[str] = "OBSERVATION_ADJACENT"
ADJACENCY_GRID_CONTIGUOUS: Final[str] = "GRID_CONTIGUOUS"

# Deterministic S1 rejection codes (fail-closed; no silent repair)
S1_INVALID_OHLC: Final[str] = "S1_INVALID_OHLC"
S1_DUPLICATE_OBSERVATION_KEY: Final[str] = "S1_DUPLICATE_OBSERVATION_KEY"
S1_OUT_OF_ORDER_OBSERVATION: Final[str] = "S1_OUT_OF_ORDER_OBSERVATION"
S1_ABSENCE_REQUIRES_CLOSED_DOMAIN: Final[str] = "S1_ABSENCE_REQUIRES_CLOSED_DOMAIN"
S1_GRID_CONTIGUITY_UNPROVEN: Final[str] = "S1_GRID_CONTIGUITY_UNPROVEN"
S1_UNSUPPORTED_SOURCE_SEMANTICS: Final[str] = "S1_UNSUPPORTED_SOURCE_SEMANTICS"
S1_SCHEMA_VERSION_MISMATCH: Final[str] = "S1_SCHEMA_VERSION_MISMATCH"
S1_POLICY_DEPENDENCY_FORBIDDEN: Final[str] = "S1_POLICY_DEPENDENCY_FORBIDDEN"
S1_UNSUPPORTED_DESCRIPTOR_INPUT: Final[str] = "S1_UNSUPPORTED_DESCRIPTOR_INPUT"

# Price input typing: published OHLC fact (NOT flow semantics)
PUBLISHED_OHLC_FACT: Final[str] = "PUBLISHED_OHLC_FACT"

# S1 schema identities (S0 hashing; no parallel identity scheme)
PRICE_PATH_SCHEMA: Final[SchemaIdentity] = SchemaIdentity("MUF_S1_PRICE_PATH", "V1")

# Allowed descriptor stages / boundary contracts (closed literals)
STAGE_RUNNING_ONLY: Final[str] = "RUNNING_ONLY"
STAGE_FINAL_ONLY: Final[str] = "FINAL_ONLY"
STAGE_BOTH_SEPARATE_FORMULAE: Final[str] = "BOTH_SEPARATE_FORMULAE"
DESCRIPTOR_STAGES: Final[Tuple[str, ...]] = (
    STAGE_RUNNING_ONLY,
    STAGE_FINAL_ONLY,
    STAGE_BOTH_SEPARATE_FORMULAE,
)
BOUNDARY_SINCE_GENESIS: Final[str] = "SINCE_GENESIS"
BOUNDARY_SINCE_ORIGIN: Final[str] = "SINCE_ORIGIN"
BOUNDARY_CONTRACTS: Final[Tuple[str, ...]] = (BOUNDARY_SINCE_GENESIS, BOUNDARY_SINCE_ORIGIN)
AVAILABILITY_AT_ACCEPTED_KEY: Final[str] = "AT_ACCEPTED_OBSERVATION_KEY"

# Input kinds a factual S1 descriptor may declare (final-scope inputs rejected)
S1_DESCRIPTOR_INPUT_KINDS: Final[FrozenSet[str]] = frozenset(
    {
        "OHLC_BAR_FACT",
        "CLOSE_DISPLACEMENT",
        "CLOSE_PATH_STEP",
        "BAR_RANGE",
        "OPEN_CLOSE_DISPLACEMENT",
        "UPPER_WICK",
        "LOWER_WICK",
        "RUNNING_HIGH_SO_FAR",
        "RUNNING_LOW_SO_FAR",
        "DECLARED_GRID_KEYS",
    }
)


# ---------------------------------------------------------------------------
# Metric results (typed; every metric declares EXACT / BOUND / PROXY / UNAVAILABLE)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricResult:
    """One metric outcome with explicit semantics; never ambiguous."""

    semantics: str
    value: Union[float, int, TypedState]
    reason: Union[str, TypedState] = TypedState.NOT_APPLICABLE
    bound_basis: Union[str, TypedState] = TypedState.NOT_APPLICABLE

    def __post_init__(self) -> None:
        if self.semantics not in METRIC_SEMANTICS:
            raise SchemaViolation(f"unknown metric semantics: {self.semantics!r}")
        if self.semantics in (EXACT, BOUND):
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise SchemaViolation("EXACT/BOUND metrics require a numeric value")
            if not math.isfinite(self.value):
                raise SchemaViolation("metric values must be finite")
            if self.semantics == BOUND and not isinstance(self.bound_basis, str):
                raise SchemaViolation("BOUND metrics require a bound_basis string")
            if self.semantics == EXACT and self.bound_basis is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation("EXACT metrics carry no bound_basis")
        if self.semantics == UNAVAILABLE:
            if not isinstance(self.value, TypedState):
                raise SchemaViolation("UNAVAILABLE metrics carry a TypedState value")
            if not isinstance(self.reason, str):
                raise SchemaViolation("UNAVAILABLE metrics require a typed reason string")


def metric_payload(result: MetricResult) -> Mapping[str, Any]:
    """Frozen-payload-domain view of a MetricResult (plain values only)."""
    if not isinstance(result, MetricResult):
        raise SchemaViolation("metric_payload requires a MetricResult")
    return {
        "semantics": result.semantics,
        "value": result.value,
        "reason": result.reason,
        "bound_basis": result.bound_basis,
    }


def exact_metric(value: Union[float, int]) -> MetricResult:
    """EXACT metric factory (finite numeric value)."""
    return MetricResult(EXACT, value)


def bound_metric(value: Union[float, int], bound_basis: str) -> MetricResult:
    """BOUND metric factory (lower/upper bound with declared basis)."""
    return MetricResult(BOUND, value, bound_basis=bound_basis)


def unavailable_metric(reason: str, typed: TypedState = TypedState.UNAVAILABLE) -> MetricResult:
    """UNAVAILABLE metric factory (typed state + reason; fail-closed)."""
    return MetricResult(UNAVAILABLE, typed, reason=reason)


def safe_ratio(numerator: Union[float, int], denominator: Union[float, int]) -> Union[float, TypedState]:
    """Ratio with typed zero-denominator semantics: UNDEFINED(ZERO_DENOMINATOR).

    No epsilon. No infinity. No coercion. Denominator zero returns the typed
    state ``TypedState.UNDEFINED``; the reason token is ``ZERO_DENOMINATOR``.
    """
    if isinstance(denominator, bool) or not isinstance(denominator, (int, float)):
        raise SchemaViolation("denominator must be numeric")
    if isinstance(numerator, bool) or not isinstance(numerator, (int, float)):
        raise SchemaViolation("numerator must be numeric")
    if not math.isfinite(numerator) or not math.isfinite(denominator):
        raise SchemaViolation("ratio operands must be finite")
    if denominator == 0:
        return TypedState.UNDEFINED
    return numerator / denominator


# ---------------------------------------------------------------------------
# Key serialization (canonical, non-semantic) and axis semantics
# ---------------------------------------------------------------------------


def key_serialization(key: InformationKey) -> Tuple[str, ...]:
    """Canonical serialization of a key's PUBLIC fields.

    Used ONLY as deterministic byte-canonical ordering for unordered semantic
    sets (tie origins). This serialization order is explicitly NON-SEMANTIC:
    it is never market chronology and never selects a winner.
    """
    if not isinstance(key, InformationKey):
        raise SchemaViolation("key_serialization requires an InformationKey")
    event_time = "" if key.event_time_utc is None else key.event_time_utc.isoformat()
    phase = key.information_phase
    phase_text = phase.value if isinstance(phase, Enum) else str(phase)
    return (
        str(key.information_key_version),
        str(key.timeline_id),
        str(key.bar_position),
        event_time,
        str(phase_text),
        str(key.deterministic_sequence),
    )


def key_axis(key: InformationKey) -> InformationAxis:
    """Axis binding of a key: TIME_INDEXED iff a lawful timestamp is present.

    No invented timestamps: POSITIONAL keys carry ``event_time_utc is None``.
    """
    if not isinstance(key, InformationKey):
        raise SchemaViolation("key_axis requires an InformationKey")
    return InformationAxis.TIME_INDEXED if key.event_time_utc is not None else InformationAxis.POSITIONAL


def pair_bar_count_duration(left: InformationKey, right: InformationKey) -> MetricResult:
    """Bar-count duration between keys (EXACT in key space; separate from time)."""
    _require_pair_comparable(left, right)
    return exact_metric(right.bar_position - left.bar_position)


def pair_wall_clock_duration(left: InformationKey, right: InformationKey) -> MetricResult:
    """Wall-clock duration: EXACT only under lawful TIME_INDEXED timestamps.

    POSITIONAL paths carry no timestamps: the wall-clock duration is
    UNAVAILABLE(NOT_TIME_INDEXED). No silent axis conversion exists.
    """
    _require_pair_comparable(left, right)
    if key_axis(left) is InformationAxis.POSITIONAL or key_axis(right) is InformationAxis.POSITIONAL:
        return unavailable_metric(NOT_TIME_INDEXED)
    delta = right.event_time_utc - left.event_time_utc
    return exact_metric(delta.total_seconds())


def _require_pair_comparable(left: InformationKey, right: InformationKey) -> None:
    if not isinstance(left, InformationKey) or not isinstance(right, InformationKey):
        raise SchemaViolation("duration operands must be InformationKey instances")
    if key_axis(left) is not key_axis(right):
        raise IncomparableInformationKeys("cross-axis comparison forbidden (no silent conversion)")
    if left.timeline_id != right.timeline_id:
        raise IncomparableInformationKeys("cross-timeline comparison forbidden")


# ---------------------------------------------------------------------------
# Published OHLC bar fact (PUBLISHED_OHLC_FACT input contract)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublishedOhlcBarFact:
    """A published OHLC bar fact with source provenance (price = PUBLISHED_OHLC_FACT).

    Price fields carry NO flow-style ACTUAL/PROXY semantics. Validated strictly:
    finite positive prices, ``high >= max(open, close)``, ``low <= min(open,
    close)``, ``high >= low``. No clipping, no repair, no coercion. The class
    exposes no tick-path reconstruction.
    """

    open_price: float
    high_price: float
    low_price: float
    close_price: float
    availability_key: InformationKey
    source_identity: SchemaIdentity
    dataset_identity: str
    published_bar_record_ref: str
    information_batch: Optional[InformationBatchKey] = None

    def __post_init__(self) -> None:
        for name in ("open_price", "high_price", "low_price", "close_price"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SchemaViolation(f"{name} must be numeric")
            if not math.isfinite(value):
                raise SchemaViolation(f"{name} must be finite")
            if value <= 0:
                raise SchemaViolation(f"{name} must be in the positive price domain")
        if self.high_price < max(self.open_price, self.close_price):
            raise SchemaViolation(f"{S1_INVALID_OHLC}: high below open/close")
        if self.low_price > min(self.open_price, self.close_price):
            raise SchemaViolation(f"{S1_INVALID_OHLC}: low above open/close")
        if self.high_price < self.low_price:
            raise SchemaViolation(f"{S1_INVALID_OHLC}: high below low")
        if not isinstance(self.availability_key, InformationKey):
            raise SchemaViolation("availability_key must be an InformationKey")
        if self.availability_key.information_phase is not InformationPhase.COMPLETED_ROW_AVAILABLE:
            raise PrematureAvailability(
                "completed bar facts are available only at COMPLETED_ROW_AVAILABLE keys"
            )
        if not isinstance(self.source_identity, SchemaIdentity):
            raise SchemaViolation("source_identity must be a SchemaIdentity")
        require_string(self.dataset_identity, "dataset_identity")
        require_string(self.published_bar_record_ref, "published_bar_record_ref")
        if self.information_batch is not None and not isinstance(
            self.information_batch, InformationBatchKey
        ):
            raise SchemaViolation("information_batch must be an InformationBatchKey or None")

    @property
    def provenance(self) -> Mapping[str, Any]:
        """Required provenance: source/dataset identity + published bar reference."""
        return {
            "price_semantics": PUBLISHED_OHLC_FACT,
            "source_identity": self.source_identity.as_payload(),
            "dataset_identity": self.dataset_identity,
            "published_bar_record_ref": self.published_bar_record_ref,
        }


# ---------------------------------------------------------------------------
# Running extremes (RUNNING_EXTREME; unordered semantic tie-set)
# ---------------------------------------------------------------------------


def canonical_origin_order(origins: Tuple[InformationKey, ...]) -> Tuple[InformationKey, ...]:
    """Canonical serialization order over tie origins — NON-SEMANTIC only.

    The resulting tuple is a deterministic byte form of an UNORDERED SEMANTIC
    SET. Sorting is by canonical public-field serialization; it encodes NO
    market chronology and selects NO winner.
    """
    return tuple(sorted(origins, key=key_serialization))


@dataclass(frozen=True)
class RunningExtremeState:
    """RUNNING_EXTREME prefix fact with its unordered semantic origin set.

    Ties retain ALL origins. No winner, no first origin, no tie-break exists.
    """

    value: float
    origins: Tuple[InformationKey, ...]
    is_high: bool

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise SchemaViolation("running extreme value must be numeric")
        if not math.isfinite(self.value):
            raise SchemaViolation("running extreme value must be finite")
        if not self.origins:
            raise SchemaViolation("running extreme requires at least one origin")
        if tuple(self.origins) != canonical_origin_order(tuple(self.origins)):
            raise SchemaViolation("origins must be stored in canonical serialization order")
        if not isinstance(self.is_high, bool):
            raise SchemaViolation("is_high must be a bool")

    @property
    def origins_unordered(self) -> FrozenSet[InformationKey]:
        """The tie origins as the semantic object: an unordered set."""
        return frozenset(self.origins)

    @classmethod
    def seed(cls, key: InformationKey, value: float, is_high: bool) -> "RunningExtremeState":
        return cls(value, canonical_origin_order((key,)), is_high)

    def observe(self, key: InformationKey, value: float) -> "RunningExtremeState":
        """O(1) amortized update; ties join the unordered set (no winner)."""
        if not isinstance(key, InformationKey):
            raise SchemaViolation("observe requires an InformationKey")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise SchemaViolation("observe value must be finite numeric")
        if self.is_high:
            better = value > self.value
            worse = value < self.value
        else:
            better = value < self.value
            worse = value > self.value
        if better:
            return RunningExtremeState.seed(key, value, self.is_high)
        if worse:
            return self
        return RunningExtremeState(
            self.value, canonical_origin_order(self.origins + (key,)), self.is_high
        )


# ---------------------------------------------------------------------------
# Intrabar ambiguity (no H-before-L inference ever)
# ---------------------------------------------------------------------------


def intrabar_path_metrics(fact: PublishedOhlcBarFact) -> Mapping[str, MetricResult]:
    """Intrabar path metrics over published OHLC facts (discrete proof).

    EXACT:    UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY) — OHLC never reveals
              whether high preceded low; no traversal is ever assumed.
    BOUND:    (high - low) + min(|open-high| + |low-close|, |open-low| + |high-close|)
              = lower bound on total variation over ANY finite ordered
              observed/executed price sequence consistent with the published
              facts (starts at open, ends at close, attains high and low).
              Proof basis: triangle inequality + required extrema visitation.
              No continuity is assumed; no intermediate price is claimed traded.
    UPPER:    UNAVAILABLE(UNBOUNDED_REFINEMENT).
    """
    if not isinstance(fact, PublishedOhlcBarFact):
        raise SchemaViolation("intrabar_path_metrics requires a PublishedOhlcBarFact")
    o, h, low, c = fact.open_price, fact.high_price, fact.low_price, fact.close_price
    lower_bound = (h - low) + min(
        abs(o - h) + abs(low - c),
        abs(o - low) + abs(h - c),
    )
    return {
        "intrabar_path_length_exact": unavailable_metric(AMBIGUOUS_INTRABAR_CHRONOLOGY),
        "intrabar_path_length_lower_bound": bound_metric(
            lower_bound, DISCRETE_TV_TRIANGLE_INEQUALITY
        ),
        "intrabar_path_length_upper_bound": unavailable_metric(UNBOUNDED_REFINEMENT),
    }


def bar_derivative_metrics(fact: PublishedOhlcBarFact) -> Mapping[str, MetricResult]:
    """Per-completed-bar factual derivatives (P3-P5): EXACT span/body/wick facts."""
    o, h, low, c = fact.open_price, fact.high_price, fact.low_price, fact.close_price
    return {
        "bar_range": exact_metric(h - low),
        "open_close_displacement": exact_metric(c - o),
        "upper_wick": exact_metric(h - max(o, c)),
        "lower_wick": exact_metric(min(o, c) - low),
    }


# ---------------------------------------------------------------------------
# Pair facts (adjacent accepted observations)
# ---------------------------------------------------------------------------


def same_batch_chronology_unproven(
    left: PublishedOhlcBarFact, right: PublishedOhlcBarFact
) -> bool:
    """True iff A-before-B chronology is UNPROVEN between two facts.

    S0 rules: batch relations ``KNOWN_SAME_BATCH``/``UNKNOWN_IF_SAME_BATCH``
    never prove order (UNKNOWN is never promoted); equal causal positions are
    ordered by deterministic_sequence only, which never creates chronology.
    """
    if right.availability_key.bar_position <= left.availability_key.bar_position:
        return True
    left_batch, right_batch = left.information_batch, right.information_batch
    if left_batch is not None and right_batch is not None:
        relation = information_batch_relation(left_batch, right_batch)
        if relation is not BatchRelation.DIFFERENT_BATCH:
            return True
    return False


def pair_metrics(
    left: PublishedOhlcBarFact, right: PublishedOhlcBarFact
) -> Mapping[str, MetricResult]:
    """Close-space pair primitives P1/P2 between adjacent accepted observations.

    Magnitudes are order-free EXACT facts. Signed displacement and direction
    require proven chronology; where chronology is unproven they are typed
    UNDEFINED(SAME_BATCH_ORDER_UNPROVEN) and are never inferred from
    deterministic_sequence.
    """
    if not isinstance(left, PublishedOhlcBarFact) or not isinstance(right, PublishedOhlcBarFact):
        raise SchemaViolation("pair_metrics requires PublishedOhlcBarFact operands")
    delta = right.close_price - left.close_price
    step = abs(delta)
    chronology_unproven = same_batch_chronology_unproven(left, right)
    if chronology_unproven:
        displacement = unavailable_metric(SAME_BATCH_ORDER_UNPROVEN, TypedState.UNDEFINED)
    else:
        displacement = exact_metric(delta)
    return {
        "close_displacement": displacement,
        "close_path_step": exact_metric(step),
    }


def pair_direction(
    left: PublishedOhlcBarFact, right: PublishedOhlcBarFact
) -> Union[str, TypedState]:
    """Observed close displacement direction: UP/DOWN/FLAT — or typed UNDEFINED.

    Describes observed displacement only. Never trend/structure language.
    """
    if same_batch_chronology_unproven(left, right):
        return TypedState.UNDEFINED
    delta = right.close_price - left.close_price
    if delta > 0:
        return DIRECTION_UP
    if delta < 0:
        return DIRECTION_DOWN
    return DIRECTION_FLAT


def pair_adjacency_kind(
    left: PublishedOhlcBarFact, right: PublishedOhlcBarFact, declared_grid: Optional["DeclaredGrid"]
) -> str:
    """Adjacency kind: GRID_CONTIGUOUS only when proven by the declared grid.

    OBSERVATION_ADJACENT = consecutive accepted observations (stream-causal).
    GRID_CONTIGUOUS is a separate property; a pair crossing a not-observed
    expected grid key is never GRID_CONTIGUOUS (no synthetic bars, no fill).
    """
    if declared_grid is None:
        return ADJACENCY_OBSERVATION_ADJACENT
    return (
        ADJACENCY_GRID_CONTIGUOUS
        if declared_grid.are_consecutive(left.availability_key, right.availability_key)
        else ADJACENCY_OBSERVATION_ADJACENT
    )


# ---------------------------------------------------------------------------
# Declared grid (cadence contract over expected keys; separate from adjacency)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeclaredGrid:
    """Declared expected-key grid (cadence contract identity).

    Grid membership proves GRID_CONTIGUOUS adjacency only. It proves NO
    absence: missing-observation determination requires a closed observation
    domain (see path_schemas). Never market/feed completeness.
    """

    cadence_contract_identity: str
    expected_keys: Tuple[InformationKey, ...]

    def __post_init__(self) -> None:
        require_string(self.cadence_contract_identity, "cadence_contract_identity")
        if not self.expected_keys:
            raise SchemaViolation("declared grid requires expected keys")
        if tuple(self.expected_keys) != canonical_origin_order(tuple(self.expected_keys)):
            raise SchemaViolation("expected keys must be stored in canonical serialization order")
        positions: Dict[InformationKey, int] = {}
        previous: Optional[InformationKey] = None
        for key in self.expected_keys:
            if not isinstance(key, InformationKey):
                raise SchemaViolation("expected keys must be InformationKey instances")
            if key in positions:
                raise SchemaViolation("declared grid keys must be unique")
            if previous is not None and not previous < key:
                raise SchemaViolation("declared grid keys must be strictly increasing")
            positions[key] = len(positions)
            previous = key
        object.__setattr__(self, "_positions", positions)

    def is_member(self, key: InformationKey) -> bool:
        return key in self._positions

    def are_consecutive(self, left: InformationKey, right: InformationKey) -> bool:
        left_position = self._positions.get(left)
        right_position = self._positions.get(right)
        return (
            left_position is not None
            and right_position is not None
            and right_position == left_position + 1
        )


# ---------------------------------------------------------------------------
# DescriptorSpec registry (factual running descriptors; no policies at S1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DescriptorSpec:
    """Immutable descriptor declaration (design section: running descriptors)."""

    name: str
    version: str
    descriptor_identity: str
    stage: str
    required_inputs: Tuple[str, ...]
    availability_rule: str
    boundary_contract: str
    missingness: str
    denominator_semantics: Union[str, TypedState]
    incremental_state: str
    policy_dependencies: Tuple[str, ...]

    def __post_init__(self) -> None:
        require_string(self.name, "name")
        require_string(self.version, "version")
        require_string(self.descriptor_identity, "descriptor_identity")
        if self.stage not in DESCRIPTOR_STAGES:
            raise SchemaViolation(f"unsupported descriptor stage: {self.stage!r}")
        if not self.required_inputs:
            raise SchemaViolation("required_inputs must be nonempty")
        for item in self.required_inputs:
            if item not in S1_DESCRIPTOR_INPUT_KINDS:
                raise SchemaViolation(f"{S1_UNSUPPORTED_DESCRIPTOR_INPUT}: {item!r}")
        require_string(self.availability_rule, "availability_rule")
        if self.boundary_contract not in BOUNDARY_CONTRACTS:
            raise SchemaViolation(f"undeclared boundary contract: {self.boundary_contract!r}")
        require_string(self.missingness, "missingness")
        if not isinstance(self.denominator_semantics, (str, TypedState)):
            raise SchemaViolation("denominator_semantics must be typed")
        require_string(self.incremental_state, "incremental_state")
        if self.policy_dependencies != ():
            raise SchemaViolation(S1_POLICY_DEPENDENCY_FORBIDDEN)


def _descriptor_identity(spec_name: str, version: str, stage: str, inputs: Tuple[str, ...]) -> str:
    schema = ArtifactIdentitySchema(
        artifact_type="MUF_S1_DESCRIPTOR",
        schema_identity=PRICE_PATH_SCHEMA,
        identity_defining_fields=("name", "version", "stage", "required_inputs"),
    )
    return canonical_artifact_identity(
        schema,
        identity_payload={
            "name": spec_name,
            "version": version,
            "stage": stage,
            "required_inputs": ",".join(sorted(inputs)),
        },
    )


def _make_spec(name: str, inputs: Tuple[str, ...], incremental_state: str, missingness: str) -> DescriptorSpec:
    return DescriptorSpec(
        name=name,
        version="V1",
        descriptor_identity=_descriptor_identity(name, "V1", STAGE_RUNNING_ONLY, inputs),
        stage=STAGE_RUNNING_ONLY,
        required_inputs=inputs,
        availability_rule=AVAILABILITY_AT_ACCEPTED_KEY,
        boundary_contract=BOUNDARY_SINCE_GENESIS,
        missingness=missingness,
        denominator_semantics=TypedState.NOT_APPLICABLE,
        incremental_state=incremental_state,
        policy_dependencies=(),
    )


S1_DESCRIPTOR_SPECS: Final[Tuple[DescriptorSpec, ...]] = (
    _make_spec(
        "observed_close_path_length",
        ("CLOSE_PATH_STEP",),
        "last_close_plus_accumulator",
        "NOT_APPLICABLE",
    ),
    _make_spec(
        "grid_contiguous_close_path_length",
        ("CLOSE_PATH_STEP", "DECLARED_GRID_KEYS"),
        "accumulator_over_proven_grid_contiguous_steps",
        "NOT_CONFIGURED_WITHOUT_DECLARED_GRID",
    ),
    _make_spec(
        "running_high_so_far",
        ("RUNNING_HIGH_SO_FAR",),
        "running_extreme_state",
        "NOT_APPLICABLE",
    ),
    _make_spec(
        "running_low_so_far",
        ("RUNNING_LOW_SO_FAR",),
        "running_extreme_state",
        "NOT_APPLICABLE",
    ),
    _make_spec(
        "bar_count_observed",
        ("OHLC_BAR_FACT",),
        "accepted_observation_count",
        "NOT_APPLICABLE",
    ),
    _make_spec(
        "bar_count_grid",
        ("OHLC_BAR_FACT", "DECLARED_GRID_KEYS"),
        "accepted_grid_member_count",
        "NOT_CONFIGURED_WITHOUT_DECLARED_GRID",
    ),
    _make_spec(
        "sum_close_displacement",
        ("CLOSE_DISPLACEMENT",),
        "first_close_plus_last_close",
        "UNPROVEN_ORDER_PARTS_EXCLUDED",
    ),
)

DESCRIPTOR_SPECS_BY_NAME: Final[Mapping[str, DescriptorSpec]] = {
    spec.name: spec for spec in S1_DESCRIPTOR_SPECS
}


# ---------------------------------------------------------------------------
# Accepted observation stream (strict causal ingestion; never silently sorted)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AcceptedBarFacts:
    """Immutable bundle of S1 facts emitted for one accepted observation."""

    derivatives_record: PublishedRecord
    running_snapshot_record: PublishedRecord
    descriptor_records: Tuple[PublishedRecord, ...]
    displacement_record: Optional[PublishedRecord]

    def __post_init__(self) -> None:
        if not isinstance(self.derivatives_record, PublishedRecord):
            raise SchemaViolation("derivatives_record must be a PublishedRecord")
        if not isinstance(self.running_snapshot_record, PublishedRecord):
            raise SchemaViolation("running_snapshot_record must be a PublishedRecord")
        if not isinstance(self.descriptor_records, tuple):
            raise SchemaViolation("descriptor_records must be a tuple")
        if self.displacement_record is not None and not isinstance(
            self.displacement_record, PublishedRecord
        ):
            raise SchemaViolation("displacement_record must be a PublishedRecord or None")


class CausalObservationStream:
    """Strict causal accepted-observation stream emitting S1 price-path facts.

    Contract (H1-2): each accepted key must be lawfully strictly greater than
    the previous accepted key under public CLOSED InformationKey semantics.
    Duplicate keys raise ``S1_DUPLICATE_OBSERVATION_KEY``; out-of-order
    comparable keys raise ``S1_OUT_OF_ORDER_OBSERVATION``; input is NEVER
    silently sorted. Cross-timeline/axis observations are rejected. Incomparable
    keys fail closed under the S0 error contract.

    OBSERVATION_ADJACENT = consecutive accepted observations (stream-causal
    only). GRID_CONTIGUOUS is proven only through the declared grid. Same-batch
    chronology stays unproven where S0 says so (signed facts typed
    UNDEFINED(SAME_BATCH_ORDER_UNPROVEN); deterministic_sequence never creates
    chronology).

    Per accepted observation the work is O(1) amortized fact computation plus
    output-proportional record materialization; no history rescan ever occurs.
    """

    def __init__(
        self,
        *,
        source_identity: SchemaIdentity,
        dataset_identity: str,
        declared_grid: Optional[DeclaredGrid] = None,
    ) -> None:
        if not isinstance(source_identity, SchemaIdentity):
            raise SchemaViolation("source_identity must be a SchemaIdentity")
        require_string(dataset_identity, "dataset_identity")
        if declared_grid is not None and not isinstance(declared_grid, DeclaredGrid):
            raise SchemaViolation("declared_grid must be a DeclaredGrid or None")
        self._source_identity = source_identity
        self._dataset_identity = dataset_identity
        self._declared_grid = declared_grid
        self._seen_keys: set = set()
        self._accepted: list = []
        self._high_state: Optional[RunningExtremeState] = None
        self._low_state: Optional[RunningExtremeState] = None
        self._observed_path_length: float = 0.0
        self._grid_path_length: float = 0.0
        self._first_close: Optional[float] = None
        self._grid_member_count: int = 0

    # -- internal helpers (private by convention; not a supported public API) --

    def _check_new_key(self, key: InformationKey) -> None:
        if key in self._seen_keys:
            raise SchemaViolation(f"{S1_DUPLICATE_OBSERVATION_KEY}: {key!r}")
        if self._accepted:
            previous_key = self._accepted[-1].availability_key
            if not key > previous_key:
                raise SchemaViolation(f"{S1_OUT_OF_ORDER_OBSERVATION}: {key!r}")

    def _emit_displacement_record(
        self,
        left: PublishedOhlcBarFact,
        right: PublishedOhlcBarFact,
        adjacency_kind: str,
        metrics: Mapping[str, MetricResult],
    ) -> PublishedRecord:
        direction = pair_direction(left, right)
        schema = ArtifactIdentitySchema(
            artifact_type="MUF_S1_OBSERVED_DISPLACEMENT",
            schema_identity=PRICE_PATH_SCHEMA,
            identity_defining_fields=(
                "origin_key",
                "adjacent_key",
                "adjacency_kind",
                "timeline_id",
            ),
        )
        identity_payload = {
            "origin_key": "|".join(key_serialization(left.availability_key)),
            "adjacent_key": "|".join(key_serialization(right.availability_key)),
            "adjacency_kind": adjacency_kind,
            "timeline_id": right.availability_key.timeline_id,
        }
        content = {
            "origin_key": left.availability_key,
            "adjacent_key": right.availability_key,
            "adjacency_kind": adjacency_kind,
            "close_displacement": metric_payload(metrics["close_displacement"]),
            "close_path_step": metric_payload(metrics["close_path_step"]),
            "direction": direction,
            "provenance_refs": (
                left.published_bar_record_ref,
                right.published_bar_record_ref,
            ),
            "dataset_identity": self._dataset_identity,
        }
        return PublishedRecord(
            record_identity=canonical_artifact_identity(
                schema, identity_payload=identity_payload
            ),
            record_type="S1_OBSERVED_DISPLACEMENT",
            schema_identity=PRICE_PATH_SCHEMA,
            timeline_id=right.availability_key.timeline_id,
            availability_key=right.availability_key,
            content=content,
        )

    def _emit_derivatives_record(self, fact: PublishedOhlcBarFact) -> PublishedRecord:
        metrics = dict(bar_derivative_metrics(fact))
        metrics.update(intrabar_path_metrics(fact))
        metrics_view = {name: metric_payload(result) for name, result in metrics.items()}
        schema = ArtifactIdentitySchema(
            artifact_type="MUF_S1_BAR_FACT_DERIVATIVES",
            schema_identity=PRICE_PATH_SCHEMA,
            identity_defining_fields=("bar_key", "timeline_id"),
        )
        content = {
            "bar_key": fact.availability_key,
            "metrics": metrics_view,
            "metric_semantics": {
                name: result.semantics for name, result in metrics.items()
            },
            "bound_basis": {
                "intrabar_path_length_lower_bound": DISCRETE_TV_TRIANGLE_INEQUALITY
            },
            "provenance_ref": fact.published_bar_record_ref,
            "dataset_identity": self._dataset_identity,
        }
        return PublishedRecord(
            record_identity=canonical_artifact_identity(
                schema,
                identity_payload={
                    "bar_key": "|".join(key_serialization(fact.availability_key)),
                    "timeline_id": fact.availability_key.timeline_id,
                },
            ),
            record_type="S1_BAR_FACT_DERIVATIVES",
            schema_identity=PRICE_PATH_SCHEMA,
            timeline_id=fact.availability_key.timeline_id,
            availability_key=fact.availability_key,
            content=content,
        )

    def _emit_running_snapshot(self, fact: PublishedOhlcBarFact) -> PublishedRecord:
        schema = ArtifactIdentitySchema(
            artifact_type="MUF_S1_RUNNING_EXTREME_SNAPSHOT",
            schema_identity=PRICE_PATH_SCHEMA,
            identity_defining_fields=("snapshot_key", "timeline_id", "scope"),
        )
        content = {
            "snapshot_key": fact.availability_key,
            "scope": "COMPLETED_BARS_ONLY",
            "running_high_so_far": self._high_state.value,
            "running_high_origins": self._high_state.origins,
            "running_low_so_far": self._low_state.value,
            "running_low_origins": self._low_state.origins,
            "origins_semantics": "UNORDERED_SEMANTIC_SET_CANONICAL_SERIALIZATION_ORDER_ONLY",
        }
        return PublishedRecord(
            record_identity=canonical_artifact_identity(
                schema,
                identity_payload={
                    "snapshot_key": "|".join(key_serialization(fact.availability_key)),
                    "timeline_id": fact.availability_key.timeline_id,
                    "scope": "COMPLETED_BARS_ONLY",
                },
            ),
            record_type="S1_RUNNING_EXTREME_SNAPSHOT",
            schema_identity=PRICE_PATH_SCHEMA,
            timeline_id=fact.availability_key.timeline_id,
            availability_key=fact.availability_key,
            content=content,
        )

    def _descriptor_values(self, fact: PublishedOhlcBarFact) -> Mapping[str, Any]:
        grid_ready = self._declared_grid is not None
        return {
            "observed_close_path_length": self._observed_path_length,
            "grid_contiguous_close_path_length": (
                self._grid_path_length if grid_ready else TypedState.NOT_CONFIGURED
            ),
            "running_high_so_far": self._high_state.value,
            "running_low_so_far": self._low_state.value,
            "bar_count_observed": len(self._accepted),
            "bar_count_grid": self._grid_member_count if grid_ready else TypedState.NOT_CONFIGURED,
            "sum_close_displacement": (
                fact.close_price - self._first_close
                if self._first_close is not None
                else 0
            ),
        }

    def _emit_descriptor_records(self, fact: PublishedOhlcBarFact) -> Tuple[PublishedRecord, ...]:
        values = self._descriptor_values(fact)
        records = []
        for spec in S1_DESCRIPTOR_SPECS:
            schema = ArtifactIdentitySchema(
                artifact_type="MUF_S1_DESCRIPTOR_VALUE",
                schema_identity=PRICE_PATH_SCHEMA,
                identity_defining_fields=("descriptor_identity", "at_key", "timeline_id"),
            )
            records.append(
                PublishedRecord(
                    record_identity=canonical_artifact_identity(
                        schema,
                        identity_payload={
                            "descriptor_identity": spec.descriptor_identity,
                            "at_key": "|".join(key_serialization(fact.availability_key)),
                            "timeline_id": fact.availability_key.timeline_id,
                        },
                    ),
                    record_type="S1_DESCRIPTOR_VALUE",
                    schema_identity=PRICE_PATH_SCHEMA,
                    timeline_id=fact.availability_key.timeline_id,
                    availability_key=fact.availability_key,
                    content={
                        "descriptor_name": spec.name,
                        "descriptor_version": spec.version,
                        "boundary_contract": spec.boundary_contract,
                        "availability_rule": spec.availability_rule,
                        "value": values[spec.name],
                    },
                )
            )
        return tuple(records)

    # -- public API --

    @property
    def accepted_count(self) -> int:
        return len(self._accepted)

    @property
    def dataset_identity(self) -> str:
        return self._dataset_identity

    @property
    def accepted_keys(self) -> Tuple[InformationKey, ...]:
        """Accepted observation keys in accepted (causal) order."""
        return tuple(fact.availability_key for fact in self._accepted)

    @property
    def last_accepted_key(self) -> Optional[InformationKey]:
        return self._accepted[-1].availability_key if self._accepted else None

    @property
    def observed_close_path_length(self) -> float:
        return self._observed_path_length

    @property
    def grid_contiguous_close_path_length(self) -> float:
        return self._grid_path_length

    @property
    def running_high_state(self) -> Optional[RunningExtremeState]:
        return self._high_state

    @property
    def running_low_state(self) -> Optional[RunningExtremeState]:
        return self._low_state

    def accept(self, fact: PublishedOhlcBarFact) -> AcceptedBarFacts:
        """Accept one published observation under the strict causal contract."""
        if not isinstance(fact, PublishedOhlcBarFact):
            raise SchemaViolation("accept requires a PublishedOhlcBarFact")
        key = fact.availability_key
        if self._accepted:
            previous_key = self._accepted[-1].availability_key
            if previous_key.timeline_id != key.timeline_id:
                raise InformationKeyViolation("cross-timeline observation stream forbidden")
            if key_axis(previous_key) is not key_axis(key):
                raise InformationKeyViolation("cross-axis observation stream forbidden")
        if fact.source_identity != self._source_identity:
            raise SchemaViolation(
                f"{S1_UNSUPPORTED_SOURCE_SEMANTICS}: source_identity mismatch"
            )
        if fact.dataset_identity != self._dataset_identity:
            raise SchemaViolation(
                f"{S1_UNSUPPORTED_SOURCE_SEMANTICS}: dataset_identity mismatch"
            )
        self._check_new_key(key)

        displacement_record = None
        previous_fact = self._accepted[-1] if self._accepted else None
        if previous_fact is not None:
            adjacency_kind = pair_adjacency_kind(previous_fact, fact, self._declared_grid)
            metrics = pair_metrics(previous_fact, fact)
            displacement_record = self._emit_displacement_record(
                previous_fact, fact, adjacency_kind, metrics
            )
            self._observed_path_length += metrics["close_path_step"].value
            if adjacency_kind == ADJACENCY_GRID_CONTIGUOUS:
                self._grid_path_length += metrics["close_path_step"].value

        self._seen_keys.add(key)
        self._accepted.append(fact)
        if self._first_close is None:
            self._first_close = fact.close_price
        if self._high_state is None:
            self._high_state = RunningExtremeState.seed(key, fact.high_price, True)
            self._low_state = RunningExtremeState.seed(key, fact.low_price, False)
        else:
            self._high_state = self._high_state.observe(key, fact.high_price)
            self._low_state = self._low_state.observe(key, fact.low_price)
        if self._declared_grid is not None and self._declared_grid.is_member(key):
            self._grid_member_count += 1

        derivatives_record = self._emit_derivatives_record(fact)
        running_snapshot_record = self._emit_running_snapshot(fact)
        descriptor_records = self._emit_descriptor_records(fact)
        return AcceptedBarFacts(
            derivatives_record=derivatives_record,
            running_snapshot_record=running_snapshot_record,
            descriptor_records=descriptor_records,
            displacement_record=displacement_record,
        )
