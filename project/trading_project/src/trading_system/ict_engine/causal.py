"""Executable prefix-invariance contract for every later engine function."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from .data import Candle

Output = TypeVar("Output")


class PrefixInvarianceError(AssertionError):
    """A trace changed retrospectively when future candles were removed."""


def assert_prefix_invariance(
    function: Callable[[Sequence[Candle]], Sequence[Output]],
    candles: Sequence[Candle],
    *,
    lengths: Iterable[int] | None = None,
) -> None:
    """Check that a per-bar causal trace is unchanged by future truncation.

    ``function`` must be pure and return exactly one output per input candle.
    Output ``i`` is the state at ``candles[i].end`` and may depend only on
    ``candles[:i + 1]``.  With no ``lengths``, every prefix (including empty)
    is checked.  Long real-data smoke tests should pass explicit lengths to
    avoid a quadratic number of rows processed.

    Exact equality is intentional: later deterministic states and events are
    value objects, so approximate comparison could hide ordering instability.
    """

    full_trace = tuple(function(candles))
    if len(full_trace) != len(candles):
        raise PrefixInvarianceError(
            "Causal function must return one output per input candle; "
            f"got {len(full_trace)} outputs for {len(candles)} candles"
        )

    checked_lengths = range(len(candles) + 1) if lengths is None else lengths
    for length in sorted(set(checked_lengths)):
        if not 0 <= length <= len(candles):
            raise ValueError(
                f"Prefix length {length} is outside [0, {len(candles)}]"
            )
        truncated_trace = tuple(function(candles[:length]))
        expected = full_trace[:length]
        if truncated_trace != expected:
            divergence = next(
                (
                    index
                    for index, (left, right) in enumerate(
                        zip(truncated_trace, expected, strict=False)
                    )
                    if left != right
                ),
                min(len(truncated_trace), len(expected)),
            )
            raise PrefixInvarianceError(
                f"Future truncation changed the trace at prefix {length}, "
                f"first divergence at output {divergence}"
            )
