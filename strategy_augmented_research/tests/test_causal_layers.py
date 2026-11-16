from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "original_v5"))
sys.path.insert(0, str(ROOT / "augmented_v5"))

from causal_layers import LayerConfig, precompute_causal_swing_state, snapshot  # noqa: E402


def make_bars(n: int = 420) -> pd.DataFrame:
    rng = np.random.default_rng(20261116)
    idx = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC")
    close = 1900.0 + np.cumsum(rng.normal(0.0, 0.8, n))
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + rng.uniform(0.05, 0.7, n)
    low = np.minimum(open_, close) - rng.uniform(0.05, 0.7, n)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close}, index=idx)


def assert_values_equal(left: dict, right: dict) -> None:
    assert left.keys() == right.keys()
    for key in left:
        a, b = left[key], right[key]
        if isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b):
            continue
        assert a == b, key


def test_snapshot_is_prefix_invariant_at_completed_bar() -> None:
    bars = make_bars()
    full_state = precompute_causal_swing_state(bars)
    for i in (40, 100, 219, 350):
        prefix = bars.iloc[: i + 1].copy()
        prefix_state = precompute_causal_swing_state(prefix)
        full = snapshot(
            bars, i, "LONG", config=LayerConfig(), as_of=bars.index[i],
            risk_distance=3.0, swing_state=full_state[i],
        )
        cut = snapshot(
            prefix, i, "LONG", config=LayerConfig(), as_of=prefix.index[i],
            risk_distance=3.0, swing_state=prefix_state[-1],
        )
        assert full.available == cut.available
        assert_values_equal(full.values, cut.values)


def test_future_bar_mutation_cannot_change_past_snapshot() -> None:
    bars = make_bars()
    i = 250
    mutated = bars.copy()
    mutated.iloc[i + 1 :, mutated.columns.get_loc("Open")] += 100_000.0
    mutated.iloc[i + 1 :, mutated.columns.get_loc("High")] += 100_000.0
    mutated.iloc[i + 1 :, mutated.columns.get_loc("Low")] += 100_000.0
    mutated.iloc[i + 1 :, mutated.columns.get_loc("Close")] += 100_000.0

    before = snapshot(
        bars, i, "SHORT", config=LayerConfig(), as_of=bars.index[i],
        risk_distance=3.0, swing_state=precompute_causal_swing_state(bars)[i],
    )
    after = snapshot(
        mutated, i, "SHORT", config=LayerConfig(), as_of=mutated.index[i],
        risk_distance=3.0, swing_state=precompute_causal_swing_state(mutated)[i],
    )
    assert before.available == after.available
    assert_values_equal(before.values, after.values)


def test_bar_after_as_of_is_not_available() -> None:
    bars = make_bars()
    state = precompute_causal_swing_state(bars)
    ev = snapshot(
        bars, 80, "LONG", config=LayerConfig(), as_of=bars.index[79],
        risk_distance=3.0, swing_state=state[80],
    )
    assert ev.available == {}
    assert "bar_not_available_as_of" in ev.reasons


def test_htf_premium_discount_excludes_future_htf_bars() -> None:
    source = make_bars()
    htf_idx = pd.date_range("2024-01-01 04:00", periods=100, freq="4h", tz="UTC")
    htf_close = 1900.0 + np.cumsum(np.linspace(-0.3, 0.3, len(htf_idx)))
    htf = pd.DataFrame(
        {
            "Open": htf_close,
            "High": htf_close + 2.0,
            "Low": htf_close - 2.0,
            "Close": htf_close,
        },
        index=htf_idx,
    )
    i = 350
    state = precompute_causal_swing_state(source)
    first = snapshot(
        source, i, "LONG", config=LayerConfig(), as_of=source.index[i],
        risk_distance=3.0, swing_state=state[i], htf_tf=htf,
    )
    changed = htf.copy()
    htf_i = int(htf.index.searchsorted(source.index[i], side="right") - 1)
    changed.iloc[htf_i + 1 :, changed.columns.get_loc("High")] += 100_000.0
    changed.iloc[htf_i + 1 :, changed.columns.get_loc("Low")] += 100_000.0
    second = snapshot(
        source, i, "LONG", config=LayerConfig(), as_of=source.index[i],
        risk_distance=3.0, swing_state=state[i], htf_tf=changed,
    )
    assert_values_equal(first.values, second.values)
    assert first.available == second.available
