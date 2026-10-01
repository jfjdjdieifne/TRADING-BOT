"""MUF V1 S0: immutable record foundations, append-only events, typed references.

Published records cannot be mutated in place. Lifecycle changes are new
events/records; generic current-state projection derives from events only.
Typed causal references carry record identity, timeline, availability, and
record type/schema identity so later layers can validate visibility,
timeline/phase compatibility, and expected schema/type.

No market-specific S1+ semantics (status/supersession/relation/membership
event kinds are generic foundations only).

DEEP IMMUTABILITY (I-DEEP-1..5, P2 TRUE IMMUTABLE STORAGE): persisted
record/event payloads are recursively canonically frozen at construction
(``freeze_payload``) into ``FrozenPayloadMapping`` — structural immutable
storage: an immutable, key-sorted tuple of ``(str_key, frozen_value)`` pairs.
There is NO dict/list/set backing object in the reachable semantic graph; the
storage container is immutable by type. Caller-owned mutable containers are
never aliased; nested mutation is impossible; freeze is deterministic and
insertion-order independent. Payload content does NOT enter any canonical
identity hash at S0 (identity-defining fields are separate); for
hashing/comparison against the approved public CLOSED hashing, use the
deterministic ``payload_canonical_view`` (records.py) which maps the immutable
structure onto the accepted canonical public payload domain. ``canonical_sha256``
remains the ONLY hash authority (no parallel hashing algorithm); the canonical
hash of the view equals the canonical hash of the equivalent raw structure.

Value-domain contract for frozen payloads (fail closed otherwise):
- str / bool / int / float / None            -> preserved as-is
- Enum members (TypedState, EventKind, ...)  -> preserved as-is
- InformationKey / SchemaIdentity            -> preserved as-is (frozen objects)
- Mapping with str keys                      -> recursively frozen FrozenPayloadMapping
- list / tuple                               -> recursively frozen tuple
- set / frozenset                            -> SchemaViolation (unordered
  collections are not permitted by the S0 semantic contract)
- any other mutable/custom object            -> SchemaViolation (never blindly
  deep-copied; no semantics invented)

copy / deepcopy / pickle of a frozen payload FAIL CLOSED (SchemaViolation): no
operation may return a mutable representation masquerading as the published
immutable contract.

Complexity: record/event construction O(payload_size) (deep freeze, honest —
not O(1)). Frozen payload lookup O(number of keys) over the immutable pairs
(honest; payloads are small semantic structures). Ledger append amortized O(1)
(private identity index; ordered event history remains the projection source);
append is a validate -> duplicate-check -> history -> index transaction with
rollback on stage failure (I-LEDGER-A1..A6). Iteration/projection O(|events|)
when explicitly requested. Reference validation O(1). No market-history access.

SEMANTIC immutability is not a hostile-runtime security boundary: sufficiently
hostile reflection (object.__setattr__, interpreter-level tricks) can reach
private slots; that is explicitly out of contract scope.
"""
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Mapping, Tuple, Union

from trading_system.research.information_time import InformationKey

from trading_system.market_understanding.availability import require_visible_at
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    InformationKeyViolation,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
    require_string,
)

RECORDS_SCHEMA_VERSION: Final[str] = "MUF_S0_RECORDS_V1"


class FrozenPayloadMapping(MappingABC):
    """TRUE immutable payload mapping: structural immutable storage (P2).

    The semantic storage is an immutable tuple of ``(str_key, frozen_value)``
    pairs, key-sorted (deterministic canonical structure). No dict/list/set
    backing object exists anywhere in the reachable semantic graph — the
    storage container itself is immutable by type. Read access implements
    ``collections.abc.Mapping``.

    Explicit mutator methods raise ImmutabilityViolation for clear failure
    semantics, but the immutability guarantee does NOT rely on blocking them:
    even ``dict.__setitem__(frozen, ...)`` and friends are impossible by type
    (this is not a dict), and the tuple storage cannot be mutated by any
    ordinary or base-class operation. Attribute rebinding is refused.

    This is a SEMANTIC immutability contract, not a hostile-runtime security
    boundary (see module docstring).
    """

    __slots__ = ("_pairs",)

    def __new__(cls, pairs):
        self = super().__new__(cls)
        object.__setattr__(self, "_pairs", tuple(pairs))
        return self

    def __init__(self, pairs=()) -> None:
        # Storage is sealed structurally in __new__ (immutable tuple).
        pass

    # ---- read access (Mapping semantics; keys are key-sorted) ----
    def __getitem__(self, key: str) -> Any:
        for item_key, item_value in self._pairs:
            if item_key == key:
                return item_value
        raise KeyError(key)

    def __iter__(self):
        return (item_key for item_key, _ in self._pairs)

    def __len__(self) -> int:
        return len(self._pairs)

    # ---- structural equality (mapping semantics; order-independent) ----
    def __eq__(self, other: object) -> bool:
        if isinstance(other, FrozenPayloadMapping):
            return self._pairs == other._pairs
        if isinstance(other, MappingABC):
            if len(self) != len(other):
                return False
            try:
                return all(other[key] == value for key, value in self._pairs)
            except KeyError:
                return False
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    __hash__ = None  # mapping equality: deliberately unhashable (P1 parity)

    # ---- explicit mutators: fail loudly (immutability does not rely on them) ----
    def _deny(self, *args, **kwargs):
        raise ImmutabilityViolation(
            "frozen payload mapping is immutable; lifecycle change requires a new record/event"
        )

    __setitem__ = _deny
    __delitem__ = _deny
    clear = _deny
    pop = _deny
    popitem = _deny
    setdefault = _deny
    update = _deny
    __ior__ = _deny

    def __setattr__(self, name, value):
        raise ImmutabilityViolation("frozen payload storage cannot be rebound")

    def __delattr__(self, name):
        raise ImmutabilityViolation("frozen payload storage cannot be rebound")

    # ---- copy/deepcopy/pickle fail closed ----
    def __copy__(self):
        raise SchemaViolation("frozen payload copy is unsupported: fail closed")

    def __deepcopy__(self, memo):
        raise SchemaViolation("frozen payload deepcopy is unsupported: fail closed")

    def __reduce__(self):
        raise SchemaViolation("frozen payload pickling is unsupported: fail closed")

    def __repr__(self) -> str:
        return f"FrozenPayloadMapping({dict(self._pairs)!r})"


def freeze_payload(value: Any, *, field_name: str = "payload") -> Any:
    """Recursively canonical-freeze an S0 payload structure (I-DEEP-1..5, P2).

    Deterministic and insertion-order independent (mapping pairs are stored
    key-sorted). Caller-owned containers are copied structurally; nested
    mutable structures cannot permit post-construction mutation. Unsupported
    objects fail closed with SchemaViolation (no invented semantics).
    """
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Enum):
        return value
    if isinstance(value, (InformationKey, SchemaIdentity)):
        return value
    if isinstance(value, Mapping):
        pairs = []
        for key in value:
            if not isinstance(key, str):
                raise SchemaViolation(
                    f"{field_name} mapping keys must be strings; got {type(key)!r}"
                )
            pairs.append(
                (key, freeze_payload(value[key], field_name=f"{field_name}[{key!r}]"))
            )
        pairs.sort(key=lambda pair: pair[0])
        return FrozenPayloadMapping(pairs)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_payload(item, field_name=field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        raise SchemaViolation(
            f"{field_name} does not permit unordered collections (set/frozenset)"
        )
    raise SchemaViolation(
        f"{field_name} contains an unsupported value of type {type(value)!r}; "
        "fail closed (no semantics invented for unsupported objects)"
    )


def payload_canonical_view(value: Any) -> Any:
    """Deterministic canonical view of a frozen payload for HASHING/COMPARISON.

    The approved public ``canonical_sha256`` accepts only its own canonical
    payload domain (dict / sequence / scalars). This view maps the immutable
    structural storage onto that accepted domain; the published record itself
    stays immutable and ``canonical_sha256`` remains the ONLY hash authority
    (no parallel hashing algorithm). Deterministic: frozen storage is
    key-sorted and the public canonical hash sorts mapping keys, so mapping
    insertion order never alters identity. Sequences map to sequences — the
    public canonical hashing already treats list/tuple identically, so the P1
    list->tuple semantic equivalence is preserved exactly.
    """
    if isinstance(value, FrozenPayloadMapping):
        return {key: payload_canonical_view(item) for key, item in value._pairs}
    if isinstance(value, tuple):
        return [payload_canonical_view(item) for item in value]
    return value


class ImmutableRecord:
    """Published record: constructed once, sealed, never mutated in place."""

    def __init__(self, **fields: Any) -> None:
        if getattr(self, "_sealed", False):
            raise ImmutabilityViolation(
                "an already-sealed record cannot be re-initialized"
            )
        object.__setattr__(self, "_sealed", False)
        for name, value in fields.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        raise ImmutabilityViolation(
            f"published record is immutable: in-place mutation forbidden ({name})"
        )

    def __delattr__(self, name: str) -> None:
        raise ImmutabilityViolation(
            f"published record is immutable: deletion forbidden ({name})"
        )


class PublishedRecord(ImmutableRecord):
    """Generic published factual record with typed availability."""

    def __init__(
        self,
        *,
        record_identity: str,
        record_type: str,
        schema_identity: SchemaIdentity,
        timeline_id: str,
        availability_key: InformationKey,
        content: Mapping[str, Any],
    ) -> None:
        require_string(record_identity, "record_identity")
        require_string(record_type, "record_type")
        if not isinstance(schema_identity, SchemaIdentity):
            raise SchemaViolation("schema_identity must be a SchemaIdentity")
        require_string(timeline_id, "timeline_id")
        if not isinstance(availability_key, InformationKey):
            raise SchemaViolation("availability_key must be an InformationKey")
        if availability_key.timeline_id != timeline_id:
            raise InformationKeyViolation(
                "record timeline must match its availability key timeline"
            )
        if not isinstance(content, Mapping):
            raise SchemaViolation("content must be a mapping")
        super().__init__(
            record_identity=record_identity,
            record_type=record_type,
            schema_identity=schema_identity,
            timeline_id=timeline_id,
            availability_key=availability_key,
            content=freeze_payload(content, field_name="content"),
        )


class EventKind(Enum):
    """Generic event-kind foundations (market semantics belong to later S1+)."""

    STATUS_EVENT = "STATUS_EVENT"
    SUPERSESSION_EVENT = "SUPERSESSION_EVENT"
    RELATION_EVENT = "RELATION_EVENT"
    MEMBERSHIP_EVENT = "MEMBERSHIP_EVENT"


class EventRecord(ImmutableRecord):
    """Immutable lifecycle event; lifecycle change == new event, never rewrite."""

    def __init__(
        self,
        *,
        event_identity: str,
        event_kind: EventKind,
        subject_record_identity: str,
        event_key: InformationKey,
        event_payload: Mapping[str, Any],
    ) -> None:
        require_string(event_identity, "event_identity")
        if not isinstance(event_kind, EventKind):
            raise SchemaViolation("event_kind must be an EventKind")
        require_string(subject_record_identity, "subject_record_identity")
        if not isinstance(event_key, InformationKey):
            raise SchemaViolation("event_key must be an InformationKey")
        if not isinstance(event_payload, Mapping):
            raise SchemaViolation("event_payload must be a mapping")
        super().__init__(
            event_identity=event_identity,
            event_kind=event_kind,
            subject_record_identity=subject_record_identity,
            event_key=event_key,
            event_payload=freeze_payload(event_payload, field_name="event_payload"),
        )


class AppendOnlyEventLedger:
    """Append-only event ledger; current state derives from events only.

    Duplicate detection uses an identity index (internal bookkeeping only):
    amortized O(1) per append, O(n) cumulative for n unique events. The ordered
    event history remains the sole source of projection semantics.

    Append is a two-stage transaction with documented mutation order
    (I-LEDGER-A1..A6):

    1. validate (invalid event rejected before any mutation);
    2. duplicate check (duplicate rejected before any mutation);
    3. stage 1: append event to history;
    4. stage 2: add identity to index;
    5. on stage-2 failure: roll stage 1 back (remove the staged event,
       restore index consistency), verify the invariant, then re-raise the
       original error.

    Stage-1 failure leaves state unchanged (list append is atomic). A rollback
    that cannot restore the invariant raises ImmutabilityViolation loudly —
    the ledger never continues silently with corrupted state. A retry of an
    event whose prior append failed is never falsely rejected (no poisoned
    index).

    Storage exposure: history and identity index live in name-mangled slots
    (no ``__dict__``); ordinary rebinding (``ledger._events = ...``) is
    impossible/refused and ``events()`` returns an immutable snapshot tuple.
    This is a SEMANTIC immutability/consistency contract, NOT a hostile-runtime
    security boundary: sufficiently hostile reflection can still reach slots.
    """

    __slots__ = ("__history", "__identity_index")

    def __init__(self) -> None:
        object.__setattr__(self, "_AppendOnlyEventLedger__history", [])
        object.__setattr__(self, "_AppendOnlyEventLedger__identity_index", set())

    def __setattr__(self, name: str, value: Any) -> None:
        raise ImmutabilityViolation(
            "ledger internals cannot be rebound (semantic contract, not a sandbox)"
        )

    def __delattr__(self, name: str) -> None:
        raise ImmutabilityViolation("ledger internals cannot be rebound")

    # ---- append-transaction stages (internal failure-injection seams) ----
    def _history_append(self, event: "EventRecord") -> None:
        """Stage 1 of the append transaction (failure-injection seam)."""
        self.__history.append(event)

    def _index_add(self, identity: str) -> None:
        """Stage 2 of the append transaction (failure-injection seam)."""
        self.__identity_index.add(identity)

    def _index_contains(self, identity: str) -> bool:
        return identity in self.__identity_index

    def _append_rollback(self, event, identity: str, depth: int) -> None:
        """Roll stage 1 back after a failed stage 2 (I-LEDGER-A4/A5)."""
        if len(self.__history) != depth + 1 or self.__history[-1] is not event:
            raise ImmutabilityViolation(
                "append rollback cannot locate the staged event: fail loudly"
            )
        self.__history.pop()
        self.__identity_index.discard(identity)
        if len(self.__history) != depth or identity in self.__identity_index:
            raise ImmutabilityViolation(
                "append rollback left inconsistent ledger state: fail loudly"
            )

    def append(self, event: EventRecord) -> None:
        """Append transaction: validate -> duplicate check -> history -> index."""
        if not isinstance(event, EventRecord):
            raise SchemaViolation("only EventRecord instances can be appended")
        identity = event.event_identity
        if self._index_contains(identity):
            raise SchemaViolation(
                "duplicate event_identity: events are append-only and unique"
            )
        depth = len(self.__history)
        self._history_append(event)
        try:
            self._index_add(identity)
        except BaseException:
            try:
                self._append_rollback(event, identity, depth)
            except BaseException as rollback_error:
                raise ImmutabilityViolation(
                    "append rollback failed: ledger state may be inconsistent; "
                    "fail loudly"
                ) from rollback_error
            raise

    def overwrite(self, record_identity: str, replacement: PublishedRecord) -> None:
        """Overwrite is forbidden: lifecycle change requires a new event."""
        raise ImmutabilityViolation(
            "published records cannot be overwritten; append a new event"
        )

    def events(self) -> Tuple[EventRecord, ...]:
        return tuple(self.__history)

    def project_status(self, record_identity: str) -> Union[str, TypedState]:
        """Derive current status from events only; UNDEFINED when no event."""
        require_string(record_identity, "record_identity")
        status = TypedState.UNDEFINED
        for event in self.__history:
            if (
                event.subject_record_identity == record_identity
                and event.event_kind is EventKind.STATUS_EVENT
            ):
                value = event.event_payload.get("status", TypedState.UNDEFINED)
                status = value
        return status

    def project_supersession(self, record_identity: str) -> Union[str, TypedState]:
        """Derive supersession from events only; NOT_APPLICABLE when none."""
        require_string(record_identity, "record_identity")
        superseded_by = TypedState.NOT_APPLICABLE
        for event in self.__history:
            if (
                event.subject_record_identity == record_identity
                and event.event_kind is EventKind.SUPERSESSION_EVENT
            ):
                value = event.event_payload.get(
                    "superseded_by", TypedState.UNDEFINED
                )
                superseded_by = value
        return superseded_by


# ---------------------------------------------------------------------------
# Typed causal references (foundation for later closure validation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AvailabilityReference:
    """Resolvable availability pointer (resolution belongs to later layers)."""

    availability_record_identity: str
    schema_identity: SchemaIdentity
    timeline_id: str

    def __post_init__(self) -> None:
        require_string(self.availability_record_identity, "availability_record_identity")
        if not isinstance(self.schema_identity, SchemaIdentity):
            raise SchemaViolation("schema_identity must be a SchemaIdentity")
        require_string(self.timeline_id, "timeline_id")


@dataclass(frozen=True)
class CausalRecordReference:
    """Typed causal reference: identity + timeline + availability + type/schema."""

    referenced_record_identity: str
    referenced_record_type: str
    referenced_schema_identity: SchemaIdentity
    timeline_id: str
    availability: Union[InformationKey, AvailabilityReference]

    def __post_init__(self) -> None:
        require_string(self.referenced_record_identity, "referenced_record_identity")
        require_string(self.referenced_record_type, "referenced_record_type")
        if not isinstance(self.referenced_schema_identity, SchemaIdentity):
            raise SchemaViolation("referenced_schema_identity must be a SchemaIdentity")
        require_string(self.timeline_id, "timeline_id")
        if isinstance(self.availability, InformationKey):
            if self.availability.timeline_id != self.timeline_id:
                raise InformationKeyViolation(
                    "reference availability key must share the reference timeline"
                )
        elif isinstance(self.availability, AvailabilityReference):
            if self.availability.timeline_id != self.timeline_id:
                raise InformationKeyViolation(
                    "reference availability pointer must share the reference timeline"
                )
        else:
            raise SchemaViolation(
                "availability must be an InformationKey or an AvailabilityReference"
            )


def validate_reference_at(
    *, reference: CausalRecordReference, at_key: InformationKey
) -> None:
    """Validate that a causal reference is legitimately visible at ``at_key``.

    Prevents an arbitrary future record reference from masquerading as a
    currently visible one. Unresolvable availability pointers fail closed.
    """
    if not isinstance(reference, CausalRecordReference):
        raise SchemaViolation("reference must be a CausalRecordReference")
    if not isinstance(at_key, InformationKey):
        raise SchemaViolation("at_key must be an InformationKey")
    if reference.timeline_id != at_key.timeline_id:
        raise IllegalCausalReference("cross-timeline causal reference forbidden")
    if isinstance(reference.availability, InformationKey):
        require_visible_at(fact_key=reference.availability, at_key=at_key)
        return
    raise IllegalCausalReference(
        "availability is an unresolved AvailabilityReference: visibility cannot "
        "be established at S0, fail closed"
    )


def validate_reference_type(
    *,
    reference: CausalRecordReference,
    expected_record_type: str,
    expected_schema_identity: SchemaIdentity,
) -> None:
    """Validate the referenced record type and schema identity are as expected."""
    if not isinstance(reference, CausalRecordReference):
        raise SchemaViolation("reference must be a CausalRecordReference")
    require_string(expected_record_type, "expected_record_type")
    if not isinstance(expected_schema_identity, SchemaIdentity):
        raise SchemaViolation("expected_schema_identity must be a SchemaIdentity")
    if reference.referenced_record_type != expected_record_type:
        raise IllegalCausalReference("referenced record type is not the expected type")
    if reference.referenced_schema_identity != expected_schema_identity:
        raise IllegalCausalReference(
            "referenced schema identity is not the expected schema identity"
        )
