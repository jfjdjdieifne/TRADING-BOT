"""S0 records tests: immutability, append-only events, typed causal references.

Attacks covered: 01, 11, 12, 19. Generic foundations only; no market-specific
S1+ event semantics.
"""
import pandas as pd
import pytest

from trading_system.market_understanding.availability import InformationAxis
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    InformationKeyViolation,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.records import (
    AppendOnlyEventLedger,
    AvailabilityReference,
    CausalRecordReference,
    EventKind,
    EventRecord,
    PublishedRecord,
    validate_reference_at,
    validate_reference_type,
)
from trading_system.research.information_time import (
    INFORMATION_KEY_VERSION,
    InformationKey,
    InformationPhase,
)


def _key(timeline_id="TL", bar_position=0, phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
         sequence=0, event_time_utc=None):
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline_id,
        bar_position=bar_position,
        event_time_utc=event_time_utc,
        information_phase=phase,
        deterministic_sequence=sequence,
    )


_SCHEMA = SchemaIdentity("RECORD_DOMAIN", "RECORD_V1")


def _record(timeline_id="TL", bar_position=0, **overrides):
    fields = dict(
        record_identity="rec-1",
        record_type="GENERIC_FACTUAL_RECORD",
        schema_identity=_SCHEMA,
        timeline_id=timeline_id,
        availability_key=_key(timeline_id=timeline_id, bar_position=bar_position),
        content={"value": "v", "state": TypedState.NOT_CONFIGURED},
    )
    fields.update(overrides)
    return PublishedRecord(**fields)


def _reference(timeline_id="TL", bar_position=0, **overrides):
    fields = dict(
        referenced_record_identity="rec-1",
        referenced_record_type="GENERIC_FACTUAL_RECORD",
        referenced_schema_identity=_SCHEMA,
        timeline_id=timeline_id,
        availability=_key(timeline_id=timeline_id, bar_position=bar_position),
    )
    fields.update(overrides)
    return CausalRecordReference(**fields)


def test_attack01_cross_timeline_causal_reference_rejected():
    reference = _reference(timeline_id="TL_A", bar_position=0)
    at_key = _key(timeline_id="TL_B", bar_position=5)
    with pytest.raises(IllegalCausalReference):
        validate_reference_at(reference=reference, at_key=at_key)
    with pytest.raises(InformationKeyViolation):
        _reference(
            timeline_id="TL_A",
            availability=_key(timeline_id="TL_B"),
        )
    validate_reference_at(
        reference=_reference(timeline_id="TL_A", bar_position=0),
        at_key=_key(timeline_id="TL_A", bar_position=5),
    )


def test_attack11_published_record_mutation_rejected():
    record = _record()
    assert record.content["state"] is TypedState.NOT_CONFIGURED
    with pytest.raises(ImmutabilityViolation):
        record.record_identity = "rec-2"
    with pytest.raises(ImmutabilityViolation):
        record.content = {}
    with pytest.raises(ImmutabilityViolation):
        del record.record_identity
    with pytest.raises(ImmutabilityViolation):
        record.content["value"] = "mutated"


def test_attack12_overwrite_rejected_new_event_required():
    record = _record()
    ledger = AppendOnlyEventLedger()
    replacement = _record(record_identity="rec-2")
    with pytest.raises(ImmutabilityViolation):
        ledger.overwrite("rec-1", replacement)
    supersession = EventRecord(
        event_identity="ev-supersede-1",
        event_kind=EventKind.SUPERSESSION_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=1),
        event_payload={"superseded_by": "rec-2"},
    )
    ledger.append(supersession)
    assert record.record_identity == "rec-1"
    assert record.content["value"] == "v"
    assert ledger.project_supersession("rec-1") == "rec-2"
    with pytest.raises(SchemaViolation):
        ledger.append(supersession)


def test_attack19_future_append_cannot_mutate_record():
    record = _record()
    ledger = AppendOnlyEventLedger()
    ledger.append(
        EventRecord(
            event_identity="ev-1",
            event_kind=EventKind.STATUS_EVENT,
            subject_record_identity="rec-1",
            event_key=_key(bar_position=1),
            event_payload={"status": "ACTIVE"},
        )
    )
    with pytest.raises(ImmutabilityViolation):
        record.__init__(
            record_identity="rec-hijacked",
            record_type="GENERIC_FACTUAL_RECORD",
            schema_identity=_SCHEMA,
            timeline_id="TL",
            availability_key=_key(),
            content={},
        )
    assert record.record_identity == "rec-1"
    events_before = ledger.events()
    ledger.append(
        EventRecord(
            event_identity="ev-2",
            event_kind=EventKind.MEMBERSHIP_EVENT,
            subject_record_identity="rec-1",
            event_key=_key(bar_position=2),
            event_payload={"member_of": "set-1"},
        )
    )
    assert events_before == ledger.events()[:1]
    assert record.record_identity == "rec-1"


def test_ledger_append_only_projection_from_events():
    ledger = AppendOnlyEventLedger()
    assert ledger.project_status("rec-1") is TypedState.UNDEFINED
    assert ledger.project_supersession("rec-1") is TypedState.NOT_APPLICABLE
    ledger.append(
        EventRecord(
            event_identity="ev-a",
            event_kind=EventKind.STATUS_EVENT,
            subject_record_identity="rec-1",
            event_key=_key(bar_position=1),
            event_payload={"status": "ACTIVE"},
        )
    )
    ledger.append(
        EventRecord(
            event_identity="ev-b",
            event_kind=EventKind.STATUS_EVENT,
            subject_record_identity="rec-1",
            event_key=_key(bar_position=2),
            event_payload={"status": "SUPERSEDED_PENDING"},
        )
    )
    assert ledger.project_status("rec-1") == "SUPERSEDED_PENDING"
    assert len(ledger.events()) == 2
    with pytest.raises(SchemaViolation):
        ledger.append("not-an-event")


def test_future_record_cannot_masquerade_as_visible():
    reference = _reference(bar_position=5)
    at_key = _key(bar_position=3)
    with pytest.raises(IllegalCausalReference):
        validate_reference_at(reference=reference, at_key=at_key)
    validate_reference_at(reference=_reference(bar_position=3), at_key=_key(bar_position=5))


def test_reference_type_and_schema_validation():
    reference = _reference()
    validate_reference_type(
        reference=reference,
        expected_record_type="GENERIC_FACTUAL_RECORD",
        expected_schema_identity=_SCHEMA,
    )
    with pytest.raises(IllegalCausalReference):
        validate_reference_type(
            reference=reference,
            expected_record_type="OTHER_RECORD",
            expected_schema_identity=_SCHEMA,
        )
    with pytest.raises(IllegalCausalReference):
        validate_reference_type(
            reference=reference,
            expected_record_type="GENERIC_FACTUAL_RECORD",
            expected_schema_identity=SchemaIdentity("RECORD_DOMAIN", "RECORD_V2"),
        )


def test_unresolved_availability_reference_fails_closed():
    pointer = AvailabilityReference(
        availability_record_identity="avail-1",
        schema_identity=SchemaIdentity("AVAIL_DOMAIN", "AVAIL_V1"),
        timeline_id="TL",
    )
    reference = _reference(availability=pointer)
    with pytest.raises(IllegalCausalReference):
        validate_reference_at(reference=reference, at_key=_key(bar_position=5))
    with pytest.raises(SchemaViolation):
        _reference(timeline_id="TL", availability=42)


# ===========================================================================
# P1 deep-frozen payloads (B1) and O(1) ledger dedup (B2) — tests A..H
# ===========================================================================
import copy as _copy_module  # noqa: E402
import pickle as _pickle_module  # noqa: E402
import sys  # noqa: E402
from collections.abc import Mapping  # noqa: E402
from enum import Enum  # noqa: E402

from trading_system.market_understanding.records import (  # noqa: E402
    FrozenPayloadMapping,
    freeze_payload,
    payload_canonical_view,
)
from trading_system.research.hashing import canonical_sha256  # noqa: E402


def _published(content, record_identity="rec-1"):
    return PublishedRecord(
        record_identity=record_identity,
        record_type="GENERIC_FACTUAL_RECORD",
        schema_identity=_SCHEMA,
        timeline_id="TL",
        availability_key=_key(),
        content=content,
    )


def _nested_content():
    """Fresh nested source with deliberately aliased-equal occurrences."""
    return {
        "state": TypedState.NOT_CONFIGURED,
        "features": {
            "window": [1, 2, {"tag": "n1"}],
            "note": "seed",
            "code": TypedState.UNAVAILABLE,
            "phase": InformationPhase.COMPLETED_ROW_AVAILABLE,
            "identity": _SCHEMA,
            "tiny": {"leaf": "v"},
            "first": {"leaf": "v"},
            "second": {"leaf": "v"},
        },
        "pair": ({"x": 1}, {"x": 1}),
        "counts": (1, 2, 3),
    }


def test_p1_a_deep_alias_introspection_and_identity_preservation():
    record = _published(_nested_content())
    payload = record.content
    assert type(payload) is not dict
    assert isinstance(payload, Mapping)  # Mapping semantics (P2 structural storage)
    assert payload["state"] is TypedState.NOT_CONFIGURED
    # equal-valued nested occurrences are separate objects (deep no-alias)
    tiny = payload["features"]["tiny"]
    first = payload["features"]["first"]
    second = payload["features"]["second"]
    assert tiny == first == second == {"leaf": "v"}
    assert tiny is not first and first is not second and tiny is not second
    inner = payload["features"]["window"][2]
    assert inner["tag"] == "n1"
    assert inner is not tiny and inner is not first and inner is not second
    left, right = payload["pair"]
    assert left == right == {"x": 1}
    assert left is not right
    # stored identity objects survive by identity (round-trip contract)
    assert payload["features"]["identity"] is _SCHEMA
    assert payload["features"]["code"] is TypedState.UNAVAILABLE
    assert payload["features"]["phase"] is InformationPhase.COMPLETED_ROW_AVAILABLE
    # nested containers are frozen like the top level
    assert isinstance(payload["features"]["window"], tuple)
    with pytest.raises(ImmutabilityViolation):
        payload["features"]["note"] = "mutated"
    with pytest.raises(ImmutabilityViolation):
        payload["features"].update({"note": "mutated"})
    assert record.content["features"]["note"] == "seed"
    # I-DEEP-5: freeze preserves the approved public canonical hash
    raw = {"a": {"b": [1, 2]}, "c": "x", "d": None, "e": True, "f": (9, 8)}
    frozen = freeze_payload(raw)
    # public canonical_sha256 is the ONLY hash authority; the canonical view
    # maps the immutable structure onto its accepted payload domain (P2)
    assert canonical_sha256(domain="S0-P1-TEST", payload=raw) == canonical_sha256(
        domain="S0-P1-TEST", payload=payload_canonical_view(frozen)
    )


def test_p1_b_direct_nested_mutation_fails_closed():
    record = _published(_nested_content())
    features = record.content["features"]
    attempts = [
        lambda: features.__setitem__("note", "x"),
        lambda: features.__delitem__("note"),
        lambda: features.pop("note"),
        lambda: features.popitem(),
        lambda: features.clear(),
        lambda: features.setdefault("note", "x"),
        lambda: features.update({"note": "x"}),
        lambda: features.__ior__({"note": "x"}),
    ]
    for attempt in attempts:
        with pytest.raises(ImmutabilityViolation):
            attempt()
    with pytest.raises(ImmutabilityViolation):
        record.content["features"]["tiny"]["leaf"] = "mutated"
    assert record.content["features"]["tiny"]["leaf"] == "v"
    # construction-time alias into the caller's source dict is cut
    source = {"a": {"b": 1}}
    rec2 = _published(source, record_identity="rec-2")
    source["a"]["b"] = 999
    assert rec2.content["a"]["b"] == 1


def test_p1_c_nested_list_and_sequence_freezing():
    record = _published(_nested_content())
    window = record.content["features"]["window"]
    assert isinstance(window, tuple)
    assert isinstance(window[2], Mapping)
    with pytest.raises(ImmutabilityViolation):
        window[2]["tag"] = "mutated"
    assert record.content["features"]["window"][2]["tag"] == "n1"
    # list at top level becomes an immutable tuple with nested mapping frozen
    rec2 = _published({"rows": [{"k": 1}, [2, 3]]}, record_identity="rec-2")
    rows = rec2.content["rows"]
    assert isinstance(rows, tuple)
    assert isinstance(rows[0], Mapping)
    assert isinstance(rows[1], tuple)
    assert rows == ({"k": 1}, (2, 3))


def test_p1_d_event_payload_deep_frozen():
    ledger = AppendOnlyEventLedger()
    event = EventRecord(
        event_identity="ev-1",
        event_kind=EventKind.STATUS_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=1),
        event_payload={"status": "ACTIVE", "meta": {"src": "x", "list": [1, 2]}},
    )
    ledger.append(event)
    payload = event.event_payload
    assert type(payload) is not dict
    with pytest.raises(ImmutabilityViolation):
        payload["status"] = "MUTATED"
    with pytest.raises(ImmutabilityViolation):
        payload["meta"]["src"] = "MUTATED"
    assert event.event_payload["meta"]["src"] == "x"
    assert isinstance(event.event_payload["meta"]["list"], tuple)
    assert ledger.events()[0].event_payload["status"] == "ACTIVE"


class _HasState:
    def __init__(self):
        self.state = "open"


_EQ_CALLS = []


class _InstrumentedStr(str):
    """String subclass probe: freeze must preserve it as-is (no re-encoding)."""

    __hash__ = str.__hash__

    def __eq__(self, other):
        _EQ_CALLS.append("eq")
        return str.__eq__(self, other)

    def __hash__(self):
        _EQ_CALLS.append("hash")
        return str.__hash__(self)


def test_p1_e_unsupported_objects_fail_closed_str_subclass_preserved():
    with pytest.raises(SchemaViolation):
        _published({"bad": {"a", "b"}})  # set
    with pytest.raises(SchemaViolation):
        _published({"bad": {"deep": frozenset({"a"})}})  # frozenset nested
    with pytest.raises(SchemaViolation):
        _published({"bad": [1, {2, 3}]})  # set inside list
    with pytest.raises(SchemaViolation):
        _published({"bad": (object(),)})  # unsupported object in tuple
    with pytest.raises(SchemaViolation):
        _published({"bad": object()})  # unsupported object
    with pytest.raises(SchemaViolation):
        _published({"bad": _HasState()})  # custom object never deep-copied
    with pytest.raises(SchemaViolation):
        _published({"bad": {"deep": [object()]}})  # unsupported nested
    with pytest.raises(SchemaViolation):
        _published({1: "int key"})  # non-str mapping key
    # str subclass is preserved as-is: same object, no eq/hash re-encoding
    _EQ_CALLS.clear()
    instrumented = _InstrumentedStr("value-x")
    record = _published({"s": instrumented})
    assert record.content["s"] is instrumented
    assert _EQ_CALLS == []
    assert record.content["s"] == "value-x"


def test_p1_f_ledger_projection_unchanged_by_duplicate_rejection():
    ledger = AppendOnlyEventLedger()
    e1 = EventRecord(
        event_identity="ev-1",
        event_kind=EventKind.STATUS_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=1),
        event_payload={"status": "ACTIVE"},
    )
    e2 = EventRecord(
        event_identity="ev-2",
        event_kind=EventKind.STATUS_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=2),
        event_payload={"status": "STALE"},
    )
    ledger.append(e1)
    before = ledger.events()
    assert ledger.project_status("rec-1") == "ACTIVE"
    with pytest.raises(SchemaViolation):
        ledger.append(e1)  # duplicate rejected
    after = ledger.events()
    assert before == after == (e1,)
    assert ledger.project_status("rec-1") == "ACTIVE"  # projection preserved
    ledger.append(e2)
    assert [ev.event_identity for ev in ledger.events()] == ["ev-1", "ev-2"]
    assert ledger.project_status("rec-1") == "STALE"  # forward semantics unchanged


def test_p1_g_duplicate_identity_rejected_via_unique_index():
    ledger = AppendOnlyEventLedger()
    e1 = EventRecord(
        event_identity="ev-dup",
        event_kind=EventKind.STATUS_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=1),
        event_payload={"a": 1},
    )
    e2 = EventRecord(
        event_identity="ev-dup",
        event_kind=EventKind.STATUS_EVENT,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=2),
        event_payload={"a": 2},
    )
    ledger.append(e1)
    with pytest.raises(SchemaViolation):
        ledger.append(e2)  # same identity, different payload: still rejected
    assert [ev.event_identity for ev in ledger.events()] == ["ev-dup"]
    assert ledger.events()[0] is e1  # original projection source kept


def _count_append_line_events(n: int) -> int:
    """Deterministic executed-line count over the whole ledger append path.

    Counts every executed line of records.py during the traced append loop
    (append + all internal transaction stages), so a restored linear duplicate
    scan anywhere in the ledger path shows up as quadratic growth.
    """
    ledger = AppendOnlyEventLedger()
    events = [
        EventRecord(
            event_identity=f"ev-{i}",
            event_kind=EventKind.STATUS_EVENT,
            subject_record_identity="rec-1",
            event_key=_key(bar_position=i),
            event_payload={"status": "ACTIVE"},
        )
        for i in range(n)
    ]
    import trading_system.market_understanding.records as _records_module

    code_file = _records_module.__file__
    counter = {"n": 0}

    def tracer(frame, event, arg):
        if event == "line" and frame.f_code.co_filename == code_file:
            counter["n"] += 1
        return tracer

    sys.settrace(tracer)
    try:
        for event in events:
            ledger.append(event)
    finally:
        sys.settrace(None)
    return counter["n"]


def test_p1_h_ledger_append_operation_count_scales_linearly():
    counts = [_count_append_line_events(n) for n in (500, 1000, 2000)]
    ratio_2x = counts[1] / counts[0]
    ratio_4x = counts[2] / counts[0]
    # linear model: N -> 2N doubles work; a linear scan would quadruple it
    assert 1.6 <= ratio_2x <= 2.6, counts
    assert 3.2 <= ratio_4x <= 5.2, counts


# ===========================================================================
# P2 TRUE IMMUTABLE PAYLOAD STORAGE + LEDGER CONSISTENCY — tests P2-01..P2-18
# ===========================================================================


def _event(identity, bar=1, event_kind=EventKind.STATUS_EVENT, **payload):
    return EventRecord(
        event_identity=identity,
        event_kind=event_kind,
        subject_record_identity="rec-1",
        event_key=_key(bar_position=bar),
        event_payload={"status": "ACTIVE", **payload},
    )


def _ledger_internals(ledger):
    """Hostile-read probe for invariant VERIFICATION only (documented boundary).

    Semantic immutability contract != hostile-runtime security boundary: this
    helper deliberately uses reflection to OBSERVE internals for the
    I-LEDGER-A3/A4 invariant checks. Nothing in the supported public API
    exposes these containers; hostile reflection is out of contract scope.
    """
    history = object.__getattribute__(ledger, "_AppendOnlyEventLedger__history")
    index = object.__getattribute__(ledger, "_AppendOnlyEventLedger__identity_index")
    return history, index


class _HistoryAppendFailsLedger(AppendOnlyEventLedger):
    def _history_append(self, event):
        raise RuntimeError("injected history-append failure")


class _IndexAddFailsLedger(AppendOnlyEventLedger):
    def _index_add(self, identity):
        raise RuntimeError("injected index-add failure")


class _RollbackFailsLedger(AppendOnlyEventLedger):
    def _index_add(self, identity):
        raise RuntimeError("injected index-add failure")

    def _append_rollback(self, event, identity, depth):
        raise RuntimeError("injected rollback failure")


class _FailOnceHistoryLedger(AppendOnlyEventLedger):
    calls = 0

    def _history_append(self, event):
        cls = type(self)
        cls.calls += 1
        if cls.calls == 1:
            raise RuntimeError("injected history-append failure (once)")
        super()._history_append(event)


class _FailOnceIndexLedger(AppendOnlyEventLedger):
    calls = 0

    def _index_add(self, identity):
        cls = type(self)
        cls.calls += 1
        if cls.calls == 1:
            raise RuntimeError("injected index-add failure (once)")
        super()._index_add(identity)


def test_p2_01_dict_base_class_bypass_impossible():
    record = _published({"a": {"b": 1}, "c": "x"})
    frozen = record.content
    assert not isinstance(frozen, dict)  # not a dict: no dict base-class surface
    baseline = repr(frozen)
    bypasses = [
        lambda: dict.__setitem__(frozen, "a", 999),
        lambda: dict.__delitem__(frozen, "a"),
        lambda: dict.update(frozen, {"a": 999}),
        lambda: dict.pop(frozen, "a"),
        lambda: dict.popitem(frozen),
        lambda: dict.clear(frozen),
        lambda: dict.setdefault(frozen, "z", 1),
    ]
    for attempt in bypasses:
        with pytest.raises(TypeError):
            attempt()  # impossible by type
    assert record.content["a"]["b"] == 1
    assert record.content["c"] == "x"
    assert repr(record.content) == baseline


def test_p2_02_no_reachable_mutable_backing_store():
    def walk(value, seen):
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, FrozenPayloadMapping):
            assert getattr(value, "__dict__", None) is None
            for name in type(value).__slots__:
                storage = getattr(value, name)
                assert isinstance(storage, tuple), (name, type(storage))
                for pair in storage:
                    assert isinstance(pair, tuple) and len(pair) == 2
                    assert isinstance(pair[0], str)
                    walk(pair[1], seen)
        elif isinstance(value, tuple):
            for item in value:
                walk(item, seen)
        else:
            assert value is None or isinstance(
                value, (str, bool, int, float, Enum, InformationKey, SchemaIdentity)
            ), type(value)

    record = _published(_nested_content())
    walk(record.content, set())
    frozen = record.content
    with pytest.raises(ImmutabilityViolation):
        frozen._pairs = ()
    with pytest.raises(ImmutabilityViolation):
        del frozen._pairs


def test_p2_03_nested_source_aliases_cut():
    source = {
        "level1": {"level2": {"level3": [1, 2, {"leaf": "v"}]}},
        "pair": ({"x": 1},),
    }
    rec = _published(source, record_identity="rec-src")
    source["level1"]["level2"]["level3"][2]["leaf"] = "MUTATED"
    source["level1"]["level2"]["new"] = "MUTATED"
    source["pair"][0]["x"] = 999
    assert rec.content["level1"]["level2"]["level3"][2]["leaf"] == "v"
    assert "new" not in rec.content["level1"]["level2"]
    assert rec.content["pair"][0]["x"] == 1


def test_p2_04_nested_published_graph_immutable():
    record = _published(_nested_content())
    graph_mappings = [
        record.content,
        record.content["features"],
        record.content["features"]["tiny"],
    ]
    for mapping in graph_mappings:
        with pytest.raises(ImmutabilityViolation):
            mapping.__setitem__("k", "v")
        with pytest.raises(ImmutabilityViolation):
            mapping.update({"k": "v"})
    sequences = [
        record.content["features"]["window"],
        record.content["counts"],
        record.content["pair"],
    ]
    for seq in sequences:
        assert isinstance(seq, tuple)
        with pytest.raises(TypeError):
            seq[0] = "MUTATED"
        with pytest.raises(AttributeError):
            seq.append("MUTATED")


def test_p2_05_raw_frozen_canonical_hash_compatibility():
    raw = {"z": 1, "a": {"b": [1, 2, [3]], "c": "x"}, "d": None, "e": True,
           "f": (9, 8), "g": []}
    frozen = freeze_payload(raw)
    assert canonical_sha256(domain="S0-P2-TEST", payload=raw) == canonical_sha256(
        domain="S0-P2-TEST", payload=payload_canonical_view(frozen)
    )
    # P1 claim preserved exactly: list<->tuple canonical equivalence
    alt = {"z": 1, "a": {"b": (1, 2, (3,)), "c": "x"}, "d": None, "e": True,
           "f": [9, 8], "g": ()}
    assert canonical_sha256(domain="S0-P2-TEST", payload=alt) == canonical_sha256(
        domain="S0-P2-TEST", payload=payload_canonical_view(freeze_payload(alt))
    )
    assert canonical_sha256(domain="S0-P2-TEST", payload=raw) == canonical_sha256(
        domain="S0-P2-TEST", payload=alt
    )


def test_p2_06_mapping_insertion_order_identity_invariance():
    a = freeze_payload({"a": 1, "b": {"x": 1, "y": 2}, "c": "z"})
    b = freeze_payload({"c": "z", "b": {"y": 2, "x": 1}, "a": 1})
    assert a == b
    assert payload_canonical_view(a) == payload_canonical_view(b)
    assert canonical_sha256(
        domain="S0-P2-TEST", payload=payload_canonical_view(a)
    ) == canonical_sha256(domain="S0-P2-TEST", payload=payload_canonical_view(b))
    assert a._pairs == b._pairs  # structural storage itself is order-independent
    assert dict(a) == dict(b) == {"a": 1, "b": {"x": 1, "y": 2}, "c": "z"}


def test_p2_07_list_tuple_canonical_semantics_preserved():
    frozen = freeze_payload({"rows": [{"k": 1}, [2, 3]]})
    rows = frozen["rows"]
    assert isinstance(rows, tuple)
    assert rows == ({"k": 1}, (2, 3))
    assert freeze_payload([1, 2]) == freeze_payload((1, 2)) == (1, 2)


def test_p2_08_unsupported_objects_fail_closed():
    for bad in (
        {"s": {"a", "b"}},
        {"s": frozenset({"a"})},
        {"s": object()},
        {1: "x"},
        {"s": [object()]},
    ):
        with pytest.raises(SchemaViolation):
            freeze_payload(bad)
    with pytest.raises(SchemaViolation):
        _published({"bad": _HasState()})


def test_p2_09_history_append_failure_leaves_ledger_unchanged():
    ledger = _HistoryAppendFailsLedger()
    with pytest.raises(RuntimeError):
        ledger.append(_event("ev-1"))
    history, index = _ledger_internals(ledger)
    assert list(history) == [] and set(index) == set()
    assert ledger.events() == ()
    assert ledger.project_status("rec-1") == TypedState.UNDEFINED


def test_p2_10_index_add_failure_rolls_back_history():
    ledger = _IndexAddFailsLedger()
    with pytest.raises(RuntimeError):
        ledger.append(_event("ev-1"))
    history, index = _ledger_internals(ledger)
    assert len(history) == 0 and "ev-1" not in index  # rollback restored invariant
    assert ledger.events() == ()


def test_p2_11_retry_after_injected_failure_succeeds_exactly_once():
    for cls in (_FailOnceHistoryLedger, _FailOnceIndexLedger):
        cls.calls = 0
        ledger = cls()
        event = _event("ev-retry")
        with pytest.raises(RuntimeError):
            ledger.append(event)  # injected failure at the stage
        ledger.append(event)  # retry succeeds (I-LEDGER-A5: no poisoned index)
        history, index = _ledger_internals(ledger)
        assert [e.event_identity for e in history] == ["ev-retry"]
        assert set(index) == {"ev-retry"}
        with pytest.raises(SchemaViolation):
            ledger.append(event)  # third attempt is a genuine duplicate
        assert ledger.events() == (event,)


def test_p2_12_duplicate_rejection_unchanged():
    ledger = AppendOnlyEventLedger()
    e1, e2 = _event("ev-dup"), _event("ev-dup", bar=2)
    ledger.append(e1)
    with pytest.raises(SchemaViolation):
        ledger.append(e2)
    history, index = _ledger_internals(ledger)
    assert [e.event_identity for e in history] == ["ev-dup"]
    assert set(index) == {"ev-dup"}
    assert ledger.events() == (e1,)


def test_p2_13_projection_order_unchanged():
    ledger = AppendOnlyEventLedger()
    e1 = _event("ev-1", bar=1, status="ACTIVE")
    e2 = _event("ev-2", bar=2, status="STALE")
    sup = _event("ev-3", bar=3, event_kind=EventKind.SUPERSESSION_EVENT,
                 superseded_by="rec-2")
    ledger.append(e1)
    ledger.append(e2)
    ledger.append(sup)
    assert [ev.event_identity for ev in ledger.events()] == ["ev-1", "ev-2", "ev-3"]
    assert ledger.project_status("rec-1") == "STALE"
    assert ledger.project_supersession("rec-1") == "rec-2"
    history, index = _ledger_internals(ledger)
    assert {e.event_identity for e in history} == set(index)  # I-LEDGER-A3


def test_p2_14_ledger_complexity_remains_linear_cumulative():
    counts = [_count_append_line_events(n) for n in (400, 800, 1600)]
    ratio_2x = counts[1] / counts[0]
    ratio_4x = counts[2] / counts[0]
    assert 1.6 <= ratio_2x <= 2.6, counts
    assert 3.2 <= ratio_4x <= 5.2, counts


def test_p2_15_two_ledgers_share_no_state():
    ledger_a, ledger_b = AppendOnlyEventLedger(), AppendOnlyEventLedger()
    ledger_a.append(_event("ev-1"))
    assert ledger_b.events() == ()
    ledger_b.append(_event("ev-2"))
    assert [ev.event_identity for ev in ledger_a.events()] == ["ev-1"]
    assert [ev.event_identity for ev in ledger_b.events()] == ["ev-2"]
    hist_a, idx_a = _ledger_internals(ledger_a)
    hist_b, idx_b = _ledger_internals(ledger_b)
    assert hist_a is not hist_b and idx_a is not idx_b


def test_p2_16_copy_deepcopy_pickle_fail_closed():
    frozen = freeze_payload({"a": {"b": [1, 2]}})
    for attempt in (
        lambda: _copy_module.copy(frozen),
        lambda: _copy_module.deepcopy(frozen),
        lambda: _pickle_module.dumps(frozen),
    ):
        with pytest.raises(SchemaViolation):
            attempt()  # fail closed: no mutable/masquerading representation


def test_p2_17_rollback_failure_loud_no_public_mutation_path():
    ledger = _RollbackFailsLedger()
    with pytest.raises(ImmutabilityViolation):  # loud invariant error, not silent
        ledger.append(_event("ev-1"))
    # section 6: ordinary attributes are NOT a supported public API
    for name in ("_events", "identity_index", "history", "index"):
        assert getattr(ledger, name, None) is None
        with pytest.raises((ImmutabilityViolation, AttributeError)):
            setattr(ledger, name, [])
    assert isinstance(ledger.events(), tuple)


def test_p2_18_history_index_invariant_after_success():
    ledger = AppendOnlyEventLedger()
    for i in range(5):
        ledger.append(_event(f"ev-{i}"))
    history, index = _ledger_internals(ledger)
    assert len(history) == 5
    assert {e.event_identity for e in history} == set(index) == {
        f"ev-{i}" for i in range(5)
    }
