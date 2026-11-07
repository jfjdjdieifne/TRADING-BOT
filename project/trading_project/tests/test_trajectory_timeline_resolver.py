from __future__ import annotations

import pytest

from trading_system.research.trajectory.trajectory_timeline_resolver import (
    DURABLE_RETRIEVAL_BLOCKER,
    DurableTimelineRetrievalUnavailable,
    TimelineArtifactReference,
    TimelineArtifactReferenceError,
    require_durable_resolver,
)


def test_hash_without_locator_is_not_a_durable_artifact_reference():
    with pytest.raises(TimelineArtifactReferenceError, match="uri"):
        TimelineArtifactReference(
            reference_id="ref-1",
            uri="",
            artifact_format="csv",
            artifact_sha256="a" * 64,
            timeline_id="timeline-1",
            timeline_hash="b" * 64,
        )


def test_artifact_reference_keeps_locator_artifact_hash_and_timeline_hash_separate():
    reference = TimelineArtifactReference(
        reference_id="ref-1",
        uri="file:///artifacts/market.csv",
        artifact_format="csv",
        artifact_sha256="a" * 64,
        timeline_id="timeline-1",
        timeline_hash="b" * 64,
    )
    assert reference.uri != reference.artifact_sha256
    assert reference.artifact_sha256 != reference.timeline_hash


def test_missing_concrete_resolver_fails_with_required_blocker():
    with pytest.raises(DurableTimelineRetrievalUnavailable) as exc:
        require_durable_resolver(None)
    assert str(exc.value) == DURABLE_RETRIEVAL_BLOCKER
    assert str(exc.value) == "BLOCKED — DURABLE TIMELINE RETRIEVAL NOT AVAILABLE"


def test_dataframe_cannot_be_mistaken_for_resolver():
    with pytest.raises(TypeError, match="concrete DurableTimelineResolver"):
        require_durable_resolver(object())
