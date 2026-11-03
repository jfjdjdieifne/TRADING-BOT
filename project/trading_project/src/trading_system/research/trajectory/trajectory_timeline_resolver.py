"""Protocol boundary for future durable timeline retrieval.

The repository currently has loaders for caller-selected paths, but no resolver
that can recover exact market rows from a durable timeline/artifact identity.
This module deliberately defines only the adapter contract. It contains no
filesystem scan, hash-index lookup, loader wrapper, or in-memory-frame fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, runtime_checkable

import pandas as pd

from trading_system.research.information_time import (
    PositionalTimelineAdapter,
    TimeIndexedTimelineAdapter,
)
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TimelineAdapter = PositionalTimelineAdapter | TimeIndexedTimelineAdapter
DURABLE_RETRIEVAL_BLOCKER = "BLOCKED — DURABLE TIMELINE RETRIEVAL NOT AVAILABLE"


class DurableTimelineRetrievalUnavailable(RuntimeError):
    """No concrete durable resolver is available in this repository."""

    def __init__(self) -> None:
        super().__init__(DURABLE_RETRIEVAL_BLOCKER)


class TimelineArtifactReferenceError(ValueError):
    """Malformed or incomplete durable-artifact reference."""


@dataclass(frozen=True)
class TimelineArtifactReference:
    """A locator plus independent content/timeline identities.

    A SHA-256 alone is not a locator and does not imply that rows can be
    recovered. A concrete resolver must open ``uri``, verify the bytes against
    ``artifact_sha256``, parse them under the declared format, then verify the
    resulting rows against ``timeline_id`` and ``timeline_hash``.
    """

    reference_id: str
    uri: str
    artifact_format: str
    artifact_sha256: str
    timeline_id: str
    timeline_hash: str

    def __post_init__(self) -> None:
        for name in ("reference_id", "uri", "artifact_format", "timeline_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise TimelineArtifactReferenceError(f"{name} must be a nonempty string")
        for name in ("artifact_sha256", "timeline_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
                raise TimelineArtifactReferenceError(f"{name} must be lowercase SHA-256 hex")


@runtime_checkable
class ResolvedTimelineArtifact(Protocol):
    """Result contract for a *real* resolver implementation.

    Implementations must bind ``market_history`` to the exact referenced bytes,
    verify the byte digest, and return a timeline whose public ``verify`` method
    succeeds on those rows. Merely wrapping a caller-provided DataFrame does not
    satisfy this contract.
    """

    reference: TimelineArtifactReference
    timeline: MarketObservationTimeline
    adapter: TimelineAdapter
    market_history: pd.DataFrame
    verified_artifact_sha256: str


@runtime_checkable
class DurableTimelineResolver(Protocol):
    """Adapter shape only; there is intentionally no concrete implementation."""

    def resolve(self, reference: TimelineArtifactReference) -> ResolvedTimelineArtifact:
        """Return the exact referenced artifact and its verified market rows."""
        ...


def require_durable_resolver(resolver: object | None) -> DurableTimelineResolver:
    """Reject missing/non-resolver inputs without substituting caller data."""

    if resolver is None:
        raise DurableTimelineRetrievalUnavailable()
    method = getattr(resolver, "resolve", None)
    if not callable(method):
        raise TypeError("a concrete DurableTimelineResolver implementation is required")
    return resolver  # type: ignore[return-value]
