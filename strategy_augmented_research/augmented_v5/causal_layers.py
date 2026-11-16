"""Causal, auditable ICT/SMC-style feature layers for the V5 clone.

The original strategy does not define all of these terms as a formal contract.
This module therefore records explicit operational definitions for research; it
does not claim to reproduce an unspecified chart author's private definitions.
Every feature is computed from completed bars no later than ``as_of``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from engine.causal_primitives import causal_atr14, detect_swings_causal


@dataclass(frozen=True)
class LayerConfig:
    """Predeclared additive layer switches and fixed research parameters."""

    equal_levels: bool = False
    liquidity_zone: bool = False
    sweep_reclaim: bool = False
    confirmed_mss: bool = False
    displacement: bool = False
    fvg: bool = False
    order_block: bool = False
    bpr: bool = False
    htf_premium_discount: bool = False
    retest_reaction: bool = False
    invalidation: bool = False
    abstention: bool = False
    volatility_relative: bool = False
    spread_cost_filter: bool = False
    equal_tolerance_atr: float = 0.10
    zone_lookback: int = 32
    min_displacement_atr: float = 1.0
    min_fvg_atr: float = 0.20
    max_entry_spread_risk_fraction: float = 0.20
    min_risk_atr: float = 0.25
    max_risk_atr: float = 5.0
    reaction_body_fraction: float = 0.50


@dataclass
class FeatureEvidence:
    """One completed-bar feature snapshot and its audit explanation."""

    timestamp: pd.Timestamp
    side: str
    available: dict[str, bool] = field(default_factory=dict)
    values: dict[str, float | int | str | None] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    def enabled_pass(self, config: LayerConfig) -> bool:
        """Pass only if every enabled layer is true; record every failure."""
        switches = {
            "equal_levels": config.equal_levels,
            "liquidity_zone": config.liquidity_zone,
            "sweep_reclaim": config.sweep_reclaim,
            "confirmed_mss": config.confirmed_mss,
            "displacement": config.displacement,
            "fvg": config.fvg,
            "order_block": config.order_block,
            "bpr": config.bpr,
            "htf_premium_discount": config.htf_premium_discount,
            "retest_reaction": config.retest_reaction,
            "invalidation": config.invalidation,
            "abstention": config.abstention,
            "volatility_relative": config.volatility_relative,
            "spread_cost_filter": config.spread_cost_filter,
        }
        failures = [name for name, enabled in switches.items() if enabled and not self.available.get(name, False)]
        for name in failures:
            reason = f"layer_failed:{name}"
            if reason not in self.reasons:
                self.reasons.append(reason)
        return not failures


def _confirmed_swings(high: np.ndarray, low: np.ndarray, ends: pd.DatetimeIndex, k: int, i: int) -> list[Any]:
    """Return swing points whose confirmation index is no later than ``i``."""
    events = detect_swings_causal(high, low, ends, k)
    out: list[Any] = []
    for confirmed in range(max(0, i + 1)):
        out.extend(events.get(confirmed, []))
    return out


def _same_level(a: float | None, b: float | None, atr: float, tolerance_atr: float) -> bool:
    return bool(a is not None and b is not None and np.isfinite(atr) and abs(a - b) <= tolerance_atr * atr)


def _directional_displacement(o: np.ndarray, c: np.ndarray, i: int, side: str, atr: float, threshold: float) -> bool:
    if i < 0 or not np.isfinite(atr) or atr <= 0:
        return False
    body = abs(float(c[i] - o[i]))
    return bool(body >= threshold * atr and ((c[i] > o[i]) if side == "LONG" else (c[i] < o[i])))


def _directional_fvg(h: np.ndarray, l: np.ndarray, i: int, side: str, atr: float, min_gap_atr: float) -> bool:
    """Three-bar imbalance using only the current and two earlier completed bars."""
    if i < 2 or not np.isfinite(atr) or atr <= 0:
        return False
    if side == "LONG":
        return bool(float(l[i] - h[i - 2]) >= min_gap_atr * atr)
    return bool(float(l[i - 2] - h[i]) >= min_gap_atr * atr)


def _bpr(h: np.ndarray, l: np.ndarray, i: int, side: str, atr: float, min_gap_atr: float) -> bool:
    """Operational BPR: an older opposite imbalance overlaps a current one."""
    if i < 3 or not np.isfinite(atr) or atr <= 0:
        return False
    older_bull = float(l[i - 1] - h[i - 3]) >= min_gap_atr * atr
    older_bear = float(l[i - 3] - h[i - 1]) >= min_gap_atr * atr
    current_bull = float(l[i] - h[i - 2]) >= min_gap_atr * atr
    current_bear = float(l[i - 2] - h[i]) >= min_gap_atr * atr
    # The direction requested must have a current imbalance and an older
    # opposite imbalance; overlap is conservatively approximated by their
    # price intervals intersecting.
    if side == "LONG" and current_bull and older_bear:
        return bool(max(float(h[i - 2]), float(h[i - 3])) <= min(float(l[i]), float(l[i - 1])))
    if side == "SHORT" and current_bear and older_bull:
        return bool(max(float(h[i - 1]), float(h[i - 2])) <= min(float(l[i - 3]), float(l[i])))
    return False


def _order_block(o: np.ndarray, c: np.ndarray, i: int, side: str) -> bool:
    """Operational OB: prior completed candle is opposite to current displacement."""
    if i < 1:
        return False
    if side == "LONG":
        return bool(c[i - 1] < o[i - 1] and c[i] > o[i])
    return bool(c[i - 1] > o[i - 1] and c[i] < o[i])


def _retest_reaction(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, i: int, side: str, atr: float, body_fraction: float) -> bool:
    """Operational retest/reaction: current bar revisits prior candle body and rejects."""
    if i < 2 or not np.isfinite(atr) or atr <= 0:
        return False
    prev_body_low = min(float(o[i - 1]), float(c[i - 1]))
    prev_body_high = max(float(o[i - 1]), float(c[i - 1]))
    body = abs(float(c[i] - o[i]))
    if side == "LONG":
        return bool(l[i] <= prev_body_high and c[i] > prev_body_high and body >= body_fraction * atr)
    return bool(h[i] >= prev_body_low and c[i] < prev_body_low and body >= body_fraction * atr)


def precompute_causal_swing_state(tf: pd.DataFrame, k: int = 2) -> list[dict[str, float | bool | None]]:
    """Build confirmed swing state once, without looking beyond each index.

    This is both an efficiency helper for large replays and a convenient place
    to audit the confirmation boundary used by every snapshot.
    """
    ends = pd.DatetimeIndex(tf.index)
    high = tf["High"].to_numpy(dtype=float)
    low = tf["Low"].to_numpy(dtype=float)
    events = detect_swings_causal(high, low, ends, k)
    latest_high: float | None = None
    latest_low: float | None = None
    highs: list[float] = []
    lows: list[float] = []
    out: list[dict[str, float | bool | None]] = []
    for i in range(len(tf)):
        for point in events.get(i, []):
            if point.kind == "high":
                latest_high = float(point.price)
                highs.append(latest_high)
            else:
                latest_low = float(point.price)
                lows.append(latest_low)
        out.append({
            "latest_high": latest_high,
            "latest_low": latest_low,
            "equal_high": bool(len(highs) >= 2 and np.isfinite(highs[-1]) and np.isfinite(highs[-2])),
            "equal_low": bool(len(lows) >= 2 and np.isfinite(lows[-1]) and np.isfinite(lows[-2])),
            "equal_high_distance": abs(highs[-1] - highs[-2]) if len(highs) >= 2 else None,
            "equal_low_distance": abs(lows[-1] - lows[-2]) if len(lows) >= 2 else None,
        })
    return out


def snapshot(
    tf: pd.DataFrame,
    i: int,
    side: str,
    *,
    config: LayerConfig,
    as_of: pd.Timestamp | None = None,
    estimated_spread: float = 0.0,
    risk_distance: float | None = None,
    swing_state: dict[str, float | bool | None] | None = None,
    htf_tf: pd.DataFrame | None = None,
) -> FeatureEvidence:
    """Compute a feature snapshot from bars ``0..i`` only.

    ``risk_distance`` must be a value known at setup time (the runner uses the
    setup close to the already-defined stop), never the future fill price.
    """
    ends = pd.DatetimeIndex(tf.index)
    if i < 0 or i >= len(tf):
        raise IndexError(i)
    ts = ends[i]
    ev = FeatureEvidence(timestamp=ts, side=side)
    if as_of is not None and ts > as_of:
        ev.reasons.append("bar_not_available_as_of")
        return ev

    o = tf["Open"].to_numpy(dtype=float)
    h = tf["High"].to_numpy(dtype=float)
    l = tf["Low"].to_numpy(dtype=float)
    c = tf["Close"].to_numpy(dtype=float)
    atrs = causal_atr14(h, l, c)
    atr = float(atrs[i]) if np.isfinite(atrs[i]) else float("nan")
    if swing_state is None:
        confirmed = _confirmed_swings(h, l, ends, 2, i)
        highs = [float(point.price) for point in confirmed if point.kind == "high"]
        lows = [float(point.price) for point in confirmed if point.kind == "low"]
        latest_high = highs[-1] if highs else None
        latest_low = lows[-1] if lows else None
        equal_high_distance = abs(highs[-1] - highs[-2]) if len(highs) >= 2 else None
        equal_low_distance = abs(lows[-1] - lows[-2]) if len(lows) >= 2 else None
    else:
        latest_high = swing_state.get("latest_high")
        latest_low = swing_state.get("latest_low")
        equal_high_distance = swing_state.get("equal_high_distance")
        equal_low_distance = swing_state.get("equal_low_distance")
    equal_high = bool(
        equal_high_distance is not None and np.isfinite(atr) and float(equal_high_distance) <= config.equal_tolerance_atr * atr
    )
    equal_low = bool(
        equal_low_distance is not None and np.isfinite(atr) and float(equal_low_distance) <= config.equal_tolerance_atr * atr
    )

    prior_start = max(0, i - config.zone_lookback)
    prior_high = float(np.max(h[prior_start:i])) if i > prior_start else float("nan")
    prior_low = float(np.min(l[prior_start:i])) if i > prior_start else float("nan")
    zone = bool(
        np.isfinite(atr) and
        ((side == "LONG" and np.isfinite(prior_low) and l[i] <= prior_low + 0.25 * atr) or
         (side == "SHORT" and np.isfinite(prior_high) and h[i] >= prior_high - 0.25 * atr))
    )

    sweep_reclaim = bool(
        np.isfinite(atr) and
        ((side == "LONG" and latest_low is not None and l[i] < latest_low and c[i] > latest_low) or
         (side == "SHORT" and latest_high is not None and h[i] > latest_high and c[i] < latest_high))
    )
    mss = bool(
        (side == "LONG" and latest_high is not None and c[i] > latest_high) or
        (side == "SHORT" and latest_low is not None and c[i] < latest_low)
    )
    displacement = _directional_displacement(o, c, i, side, atr, config.min_displacement_atr)
    fvg = _directional_fvg(h, l, i, side, atr, config.min_fvg_atr)
    ob = _order_block(o, c, i, side) and displacement
    bpr = _bpr(h, l, i, side, atr, config.min_fvg_atr)

    # Premium/discount uses a real completed 4H context supplied by the
    # runner. The current 4H bar is excluded from the dealing range, so the
    # midpoint was already knowable at setup time.
    htf_bar_end: pd.Timestamp | None = None
    htf_prior_high = float("nan")
    htf_prior_low = float("nan")
    if htf_tf is not None:
        htf_idx = pd.DatetimeIndex(htf_tf.index)
        htf_i = int(htf_idx.searchsorted(ts, side="right") - 1)
        if htf_i >= 1:
            htf_h = htf_tf["High"].to_numpy(dtype=float)
            htf_l = htf_tf["Low"].to_numpy(dtype=float)
            htf_start = max(0, htf_i - config.zone_lookback)
            htf_prior_high = float(np.max(htf_h[htf_start:htf_i]))
            htf_prior_low = float(np.min(htf_l[htf_start:htf_i]))
            htf_bar_end = htf_idx[htf_i]
    if np.isfinite(htf_prior_high) and np.isfinite(htf_prior_low):
        midpoint = (htf_prior_high + htf_prior_low) / 2.0
        pd_ok = bool(c[i] <= midpoint if side == "LONG" else c[i] >= midpoint)
    else:
        midpoint = float("nan")
        pd_ok = False
    reaction = _retest_reaction(o, h, l, c, i, side, atr, config.reaction_body_fraction)
    invalidation = bool(
        (side == "LONG" and latest_low is not None and c[i] >= latest_low) or
        (side == "SHORT" and latest_high is not None and c[i] <= latest_high)
    )
    abstention = bool(np.isfinite(atr) and atr > 0 and (risk_distance is None or risk_distance > 0))
    vol_relative = bool(
        abstention and risk_distance is not None and
        config.min_risk_atr * atr <= risk_distance <= config.max_risk_atr * atr
    )
    cost_ok = bool(
        risk_distance is not None and risk_distance > 0 and
        estimated_spread <= config.max_entry_spread_risk_fraction * risk_distance
    )

    ev.values.update({
        "atr": atr,
        "latest_confirmed_swing_high": latest_high,
        "latest_confirmed_swing_low": latest_low,
        "equal_high": int(equal_high),
        "equal_low": int(equal_low),
        "prior_liquidity_high": prior_high,
        "prior_liquidity_low": prior_low,
        "prior_dealing_midpoint_4h": midpoint,
        "prior_4h_high": htf_prior_high,
        "prior_4h_low": htf_prior_low,
        "htf_bar_end": htf_bar_end,
        "estimated_spread": estimated_spread,
        "risk_distance_at_setup_close": risk_distance,
    })
    ev.available.update({
        "equal_levels": equal_low if side == "LONG" else equal_high,
        "liquidity_zone": zone,
        "sweep_reclaim": sweep_reclaim,
        "confirmed_mss": mss,
        "displacement": displacement,
        "fvg": fvg,
        "order_block": ob,
        "bpr": bpr,
        "htf_premium_discount": pd_ok,
        "retest_reaction": reaction,
        "invalidation": invalidation,
        "abstention": abstention,
        "volatility_relative": vol_relative,
        "spread_cost_filter": cost_ok,
    })
    if not invalidation:
        ev.reasons.append("invalidation_level_broken_or_unavailable")
    if not abstention:
        ev.reasons.append("abstention_bad_volatility_or_risk")
    if not cost_ok:
        ev.reasons.append("spread_cost_too_large_for_setup_risk")
    return ev


def layer_names(config: LayerConfig) -> list[str]:
    """Return enabled layer names in stable report order."""
    return [
        name for name in (
            "equal_levels", "liquidity_zone", "sweep_reclaim", "confirmed_mss",
            "displacement", "fvg", "order_block", "bpr", "htf_premium_discount",
            "retest_reaction", "invalidation", "abstention", "volatility_relative",
            "spread_cost_filter",
        ) if getattr(config, name)
    ]
