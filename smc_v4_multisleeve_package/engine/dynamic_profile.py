"""Causal dynamic-profile SMC/ICT research engine (V9 foundation).

This module is deliberately separate from ``V8_3Asset_1PosEach_QC.py``.  V8.4
is the frozen reference implementation; this file is an experimental signal
layer that can be audited before it is connected to an execution adapter.

The implementation turns the supplied ideas into explicit, testable hypotheses:

* volume anomaly is a z-score against the *previous* 100 completed bars;
* adaptive displacement is directional wave distance divided by
  ``bars * prior ATR(14)``;
* an aggressive shallow-FVG entry is allowed only when both anomalies and an
  independently supplied spot executed-flow/CVD gate agree;
* a price/flow divergence never upgrades to aggressive mode;
* CHoCH is a completed-body break of a causally confirmed swing, not a wick;
* an HTF sweep is an explicit input event.  It is not guessed from OHLCV;
* the protected momentum stop is one tick beyond the impulse candle, while
  risk/reward and exchange constraints remain hard gates;
* no order is emitted unless a known opposing zone provides a target at or above
  the configured minimum R multiple.

This is not a claim that FVGs, order blocks, CVD, or the thresholds below prove
institutional activity.  They are operational labels and falsifiable research
features.  The input ``spot_cvd_delta`` must come from a declared spot executed
flow feed; OHLCV close-location is never silently promoted to CVD.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
import math
from typing import Deque, Iterable, Sequence


class StrategyInputError(ValueError):
    """Raised when a bar or configuration violates the causal contract."""


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

    @property
    def sign(self) -> int:
        return 1 if self is Direction.LONG else -1


class Profile(str, Enum):
    WARMUP = "WARMUP"
    DEFENSIVE = "CONSERVATIVE_DEFENSE"
    AGGRESSIVE = "AGGRESSIVE_ATTACK"


class FlowStatus(str, Enum):
    VALID = "VALID_AGGRESSIVE_FLOW"
    DIVERGENT = "NEGATIVE_CVD_DIVERGENCE"
    UNKNOWN = "UNKNOWN_OR_INCOMPLETE"
    NOT_REQUIRED = "NOT_REQUIRED_BY_CONFIG"


class FundingStatus(str, Enum):
    COOL = "COOL"
    HOT = "HOT"
    UNKNOWN = "UNKNOWN_OR_INCOMPLETE"
    NOT_REQUIRED = "NOT_REQUIRED_BY_CONFIG"


@dataclass(frozen=True, slots=True)
class Bar:
    """One completed OHLCV bar plus optional external spot-flow evidence."""

    index: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: object = None
    # This is signed *executed initiated* spot volume, not an inferred pressure
    # or a claim about institutional/whale activity.
    spot_cvd_delta: float | None = None
    funding_rate: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool) or self.index < 0:
            raise StrategyInputError("bar.index must be a non-negative integer")
        values = (self.open, self.high, self.low, self.close, self.volume)
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v)) for v in values):
            raise StrategyInputError("OHLCV values must be finite real numbers")
        if self.high < self.low:
            raise StrategyInputError("bar.high must be >= bar.low")
        if not self.low <= self.open <= self.high:
            raise StrategyInputError("bar.open must lie inside [low, high]")
        if not self.low <= self.close <= self.high:
            raise StrategyInputError("bar.close must lie inside [low, high]")
        if self.volume < 0:
            raise StrategyInputError("bar.volume must be non-negative")
        for name, value in (("spot_cvd_delta", self.spot_cvd_delta), ("funding_rate", self.funding_rate)):
            if value is not None and (
                not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value))
            ):
                raise StrategyInputError(f"bar.{name} must be finite when supplied")


@dataclass(frozen=True, slots=True)
class DynamicProfileConfig:
    """All strategy thresholds are explicit and can be walk-forward calibrated."""

    volume_lookback: int = 100
    minimum_volume_history: int = 100
    atr_period: int = 14
    swing_k: int = 2
    volume_z_threshold: float = 2.5
    adi_threshold: float = 3.0
    cvd_lookback: int = 20
    require_spot_cvd: bool = True
    require_cool_funding: bool = False
    maximum_abs_funding_rate: float = 0.0005
    tick_size: float = 0.01
    minimum_rr: float = 5.0
    pending_expiry_bars: int = 20
    maximum_sweep_age_bars: int = 32
    choch_min_distance_atr: float = 1.0
    choch_min_speed_ratio: float = 2.0
    speed_lookback_bars: int = 12
    deep_ob_retrace_min: float = 0.705
    deep_ob_retrace_max: float = 0.790

    def __post_init__(self) -> None:
        integer_fields = (
            "volume_lookback", "minimum_volume_history", "atr_period", "swing_k",
            "cvd_lookback", "pending_expiry_bars", "maximum_sweep_age_bars",
            "speed_lookback_bars",
        )
        for name in integer_fields:
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise StrategyInputError(f"{name} must be a positive integer")
        if self.minimum_volume_history > self.volume_lookback:
            raise StrategyInputError("minimum_volume_history cannot exceed volume_lookback")
        for name in (
            "volume_z_threshold", "adi_threshold", "maximum_abs_funding_rate",
            "tick_size", "minimum_rr", "choch_min_distance_atr",
            "choch_min_speed_ratio", "deep_ob_retrace_min", "deep_ob_retrace_max",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise StrategyInputError(f"{name} must be finite")
            if value <= 0:
                raise StrategyInputError(f"{name} must be > 0")
        if self.deep_ob_retrace_min >= self.deep_ob_retrace_max or self.deep_ob_retrace_max >= 1.0:
            raise StrategyInputError("deep OB retracement bounds must satisfy 0 < min < max < 1")


@dataclass(frozen=True, slots=True)
class SwingPoint:
    index: int
    price: float
    kind: str  # "HIGH" or "LOW"
    confirmation_index: int
    sequence_class: str  # HH/LH/HL/LL/UNCLASSIFIED


@dataclass(frozen=True, slots=True)
class StructureBreak:
    index: int
    direction: Direction | None
    event: str  # BOS_UP, BOS_DOWN, CHOCH_UP, CHOCH_DOWN, AMBIGUOUS, NONE
    level: float | None
    level_index: int | None
    origin_price: float | None
    origin_index: int | None


@dataclass(frozen=True, slots=True)
class FVGZone:
    zone_id: int
    direction: Direction
    origin_index: int
    creation_index: int
    low: float
    high: float


@dataclass(frozen=True, slots=True)
class OrderBlockZone:
    zone_id: int
    direction: Direction
    source_break: str
    origin_index: int
    creation_index: int
    low: float
    high: float
    body_low: float
    body_high: float


@dataclass(frozen=True, slots=True)
class LiquiditySweep:
    """Explicitly supplied HTF sweep; no sweep is inferred from an LTF wick."""

    index: int
    direction: Direction
    swept_level: float
    extreme: float
    timestamp: object = None

    def __post_init__(self) -> None:
        if self.index < 0:
            raise StrategyInputError("sweep.index must be non-negative")
        if not all(math.isfinite(float(v)) for v in (self.swept_level, self.extreme)):
            raise StrategyInputError("sweep prices must be finite")
        if self.direction is Direction.LONG and self.extreme >= self.swept_level:
            raise StrategyInputError("bullish sweep extreme must be below swept level")
        if self.direction is Direction.SHORT and self.extreme <= self.swept_level:
            raise StrategyInputError("bearish sweep extreme must be above swept level")


@dataclass(frozen=True, slots=True)
class WaveMetrics:
    origin_price: float | None
    termination_price: float | None
    bars: int | None
    atr: float | None
    volume_z: float | None
    adi: float | None


@dataclass(frozen=True, slots=True)
class ProfileDecision:
    profile: Profile
    metrics: WaveMetrics
    flow_status: FlowStatus
    allow_shallow_fvg: bool
    reason: str
    funding_status: FundingStatus = FundingStatus.NOT_REQUIRED


@dataclass(frozen=True, slots=True)
class ChochValidation:
    valid: bool
    direction: Direction | None
    level: float | None
    volume_z: float | None
    speed_ratio: float | None
    distance_atr: float | None
    flow_status: FlowStatus
    reason: str
    funding_status: FundingStatus = FundingStatus.NOT_REQUIRED


@dataclass(frozen=True, slots=True)
class TradePlan:
    plan_id: str
    setup: str
    direction: Direction
    profile: Profile
    entry_price: float
    stop_price: float
    target_price: float
    minimum_target_price: float
    risk: float
    planned_rr: float
    creation_index: int
    expires_index: int
    fvg_id: int | None
    ob_id: int | None
    invalidation_price: float
    reason: str


@dataclass(frozen=True, slots=True)
class BarEvaluation:
    index: int
    volume_z: float | None
    atr: float | None
    structure: StructureBreak
    wave: WaveMetrics
    decision: ProfileDecision
    fvg: FVGZone | None
    order_block: OrderBlockZone | None
    choch: ChochValidation | None
    plan: TradePlan | None


def volume_zscore(current_volume: float, prior_volumes: Sequence[float], *, lookback: int = 100, minimum_history: int = 100) -> float | None:
    """Return a causal z-score; ``prior_volumes`` must exclude the current bar."""

    if lookback < 1 or minimum_history < 1 or minimum_history > lookback:
        raise StrategyInputError("invalid z-score lookback configuration")
    history = list(prior_volumes)[-lookback:]
    if len(history) < minimum_history:
        return None
    if not all(math.isfinite(float(v)) and float(v) >= 0 for v in history):
        raise StrategyInputError("prior volumes must be finite and non-negative")
    mean = sum(float(v) for v in history) / len(history)
    variance = sum((float(v) - mean) ** 2 for v in history) / len(history)
    std = math.sqrt(variance)
    delta = float(current_volume) - mean
    if std == 0.0:
        if delta > 0.0:
            return math.inf
        if delta < 0.0:
            return -math.inf
        return 0.0
    return delta / std


def adaptive_displacement_index(
    origin_price: float,
    termination_price: float,
    bars: int,
    atr: float,
    direction: Direction,
) -> float | None:
    """Compute directional wave displacement over ``bars * ATR``."""

    if bars < 1 or not math.isfinite(float(atr)) or atr <= 0:
        return None
    move = (float(termination_price) - float(origin_price)) * direction.sign
    if move <= 0:
        return 0.0
    return move / (bars * float(atr))


def protected_momentum_stop(direction: Direction, impulse_bar: Bar, tick_size: float) -> float:
    """One-tick invalidation beyond the completed impulse candle."""

    if tick_size <= 0 or not math.isfinite(float(tick_size)):
        raise StrategyInputError("tick_size must be positive and finite")
    return (
        impulse_bar.low - tick_size
        if direction is Direction.LONG
        else impulse_bar.high + tick_size
    )


def tighten_stop(direction: Direction, current_stop: float, candidate_stop: float, market_price: float) -> float:
    """Monotonic trailing-stop update; never loosens risk or crosses the market."""

    if direction is Direction.LONG:
        candidate = min(float(candidate_stop), float(market_price))
        return max(float(current_stop), candidate)
    candidate = max(float(candidate_stop), float(market_price))
    return min(float(current_stop), candidate)


def spot_cvd_delta_from_binance_kline(base_volume: float, taker_buy_base_volume: float) -> float:
    """Derive signed executed-initiated spot delta from Binance kline fields.

    Binance's published kline field ``taker_buy_base_volume`` gives the buy
    initiated base volume.  The remainder is treated as sell initiated volume:
    ``delta = buy - sell = 2 * buy - total``.  This is executed-flow evidence
    for that source, not order-book pressure or proof of institutional trading.
    """

    total = float(base_volume)
    buy = float(taker_buy_base_volume)
    if not all(math.isfinite(v) for v in (total, buy)) or total < 0 or buy < 0 or buy > total:
        raise StrategyInputError("invalid Binance kline volume fields")
    return 2.0 * buy - total


def choose_profile(
    *,
    metrics: WaveMetrics,
    flow_status: FlowStatus,
    config: DynamicProfileConfig,
    exhaustion_divergence: bool = False,
    funding_status: FundingStatus = FundingStatus.NOT_REQUIRED,
) -> ProfileDecision:
    """Apply the hard aggressive gate; all other states remain defensive."""

    if metrics.volume_z is None or metrics.adi is None:
        return ProfileDecision(Profile.WARMUP, metrics, flow_status, False, "INSUFFICIENT_CAUSAL_HISTORY", funding_status)
    if exhaustion_divergence or flow_status is FlowStatus.DIVERGENT:
        return ProfileDecision(Profile.DEFENSIVE, metrics, flow_status, False, "EXHAUSTION_OR_NEGATIVE_CVD_DIVERGENCE", funding_status)
    funding_ok = funding_status is not FundingStatus.HOT and (
        not config.require_cool_funding or funding_status is FundingStatus.COOL
    )
    if not funding_ok:
        return ProfileDecision(Profile.DEFENSIVE, metrics, flow_status, False, "FUNDING_HEAT_GATE_BLOCKED", funding_status)
    if metrics.volume_z > config.volume_z_threshold and metrics.adi > config.adi_threshold:
        if flow_status is FlowStatus.VALID or (not config.require_spot_cvd and flow_status is FlowStatus.NOT_REQUIRED):
            return ProfileDecision(Profile.AGGRESSIVE, metrics, flow_status, True, "VOLUME_AND_VELOCITY_AND_SPOT_FLOW_CONVERGE", funding_status)
        return ProfileDecision(Profile.DEFENSIVE, metrics, flow_status, False, "EXTREME_WAVE_BLOCKED_UNTIL_SPOT_FLOW_CONFIRMS", funding_status)
    return ProfileDecision(Profile.DEFENSIVE, metrics, flow_status, False, "EXTREME_VOLUME_AND_VELOCITY_GATE_NOT_MET", funding_status)


class _RollingStats:
    def __init__(self, maxlen: int) -> None:
        self.values: Deque[float] = deque(maxlen=maxlen)

    def zscore(self, value: float, minimum_history: int) -> float | None:
        return volume_zscore(value, list(self.values), lookback=self.values.maxlen or 1, minimum_history=minimum_history)

    def push(self, value: float) -> None:
        self.values.append(float(value))


class _WilderATR:
    def __init__(self, period: int) -> None:
        self.period = period
        self.prev_close: float | None = None
        self.trs: Deque[float] = deque(maxlen=period)
        self.value: float | None = None

    def _true_range(self, bar: Bar) -> float:
        if self.prev_close is None:
            return bar.high - bar.low
        return max(bar.high - bar.low, abs(bar.high - self.prev_close), abs(bar.low - self.prev_close))

    def peek(self) -> float | None:
        return self.value

    def push(self, bar: Bar) -> None:
        tr = self._true_range(bar)
        self.trs.append(tr)
        if len(self.trs) < self.period:
            self.value = None
        elif len(self.trs) == self.period and self.value is None:
            self.value = sum(self.trs) / self.period
        else:
            assert self.value is not None
            self.value = ((self.value * (self.period - 1)) + tr) / self.period
        self.prev_close = bar.close


class _CausalStructure:
    def __init__(self, k: int) -> None:
        self.k = k
        self.history: list[Bar] = []
        self.latest_high: SwingPoint | None = None
        self.latest_low: SwingPoint | None = None
        self.previous_high: SwingPoint | None = None
        self.previous_low: SwingPoint | None = None
        self.trend = 0
        self._broken_highs: set[int] = set()
        self._broken_lows: set[int] = set()

    @staticmethod
    def _is_pivot_high(window: Sequence[Bar], center: int) -> bool:
        h = window[center].high
        return h > max(b.high for b in window[:center]) and h >= max(b.high for b in window[center + 1 :])

    @staticmethod
    def _is_pivot_low(window: Sequence[Bar], center: int) -> bool:
        l = window[center].low
        return l < min(b.low for b in window[:center]) and l <= min(b.low for b in window[center + 1 :])

    def evaluate(self, bar: Bar) -> StructureBreak:
        if bar.index != len(self.history):
            raise StrategyInputError("bars must arrive in consecutive index order")
        up = self.latest_high is not None and bar.open > self.latest_high.price and bar.close > self.latest_high.price
        down = self.latest_low is not None and bar.open < self.latest_low.price and bar.close < self.latest_low.price
        if up and down:
            return StructureBreak(bar.index, None, "AMBIGUOUS", None, None, None, None)
        if up and self.latest_high is not None and self.latest_high.index not in self._broken_highs:
            event = "CHOCH_UP" if self.trend == -1 else "BOS_UP"
            origin = self.latest_low
            return StructureBreak(bar.index, Direction.LONG, event, self.latest_high.price, self.latest_high.index, origin.price if origin else None, origin.index if origin else None)
        if down and self.latest_low is not None and self.latest_low.index not in self._broken_lows:
            event = "CHOCH_DOWN" if self.trend == 1 else "BOS_DOWN"
            origin = self.latest_high
            return StructureBreak(bar.index, Direction.SHORT, event, self.latest_low.price, self.latest_low.index, origin.price if origin else None, origin.index if origin else None)
        return StructureBreak(bar.index, None, "NONE", None, None, None, None)

    def commit_break(self, event: StructureBreak) -> None:
        if event.direction is None:
            return
        if event.direction is Direction.LONG:
            if event.level_index is not None:
                self._broken_highs.add(event.level_index)
            self.trend = 1
        else:
            if event.level_index is not None:
                self._broken_lows.add(event.level_index)
            self.trend = -1

    def commit_bar(self, bar: Bar) -> SwingPoint | None:
        self.history.append(bar)
        pivot = len(self.history) - 1 - self.k
        if pivot < self.k:
            return None
        window = self.history[pivot - self.k : pivot + self.k + 1]
        point_bar = self.history[pivot]
        if self._is_pivot_high(window, self.k):
            sequence = "UNCLASSIFIED" if self.latest_high is None else ("HH" if point_bar.high > self.latest_high.price else ("LH" if point_bar.high < self.latest_high.price else "EH"))
            point = SwingPoint(pivot, point_bar.high, "HIGH", len(self.history) - 1, sequence)
            self.previous_high, self.latest_high = self.latest_high, point
            return point
        if self._is_pivot_low(window, self.k):
            sequence = "UNCLASSIFIED" if self.latest_low is None else ("HL" if point_bar.low > self.latest_low.price else ("LL" if point_bar.low < self.latest_low.price else "EL"))
            point = SwingPoint(pivot, point_bar.low, "LOW", len(self.history) - 1, sequence)
            self.previous_low, self.latest_low = self.latest_low, point
            return point
        return None


class _FlowTracker:
    def __init__(self, maxlen: int) -> None:
        self.cumulative: float | None = None
        self.values: Deque[float] = deque(maxlen=maxlen)
        self.gap = False

    def status_for(self, delta: float | None, direction: Direction | None, require: bool) -> FlowStatus:
        if delta is None:
            return FlowStatus.UNKNOWN if require else FlowStatus.NOT_REQUIRED
        if self.gap or self.cumulative is None or len(self.values) == 0 or direction is None:
            return FlowStatus.UNKNOWN if require else FlowStatus.NOT_REQUIRED
        candidate = self.cumulative + float(delta)
        if direction is Direction.LONG:
            return FlowStatus.VALID if delta > 0 and candidate > max(self.values) else FlowStatus.DIVERGENT
        return FlowStatus.VALID if delta < 0 and candidate < min(self.values) else FlowStatus.DIVERGENT

    def push(self, delta: float | None) -> None:
        if delta is None:
            self.gap = True
            return
        value = float(delta)
        self.cumulative = value if self.cumulative is None else self.cumulative + value
        self.values.append(self.cumulative)
        self.gap = False


class DynamicProfileEngine:
    """Sequential, zero-lookahead scanner for the V9 hypothesis layer."""

    def __init__(self, config: DynamicProfileConfig | None = None) -> None:
        self.config = config or DynamicProfileConfig()
        self._volume = _RollingStats(self.config.volume_lookback)
        self._atr = _WilderATR(self.config.atr_period)
        self._structure = _CausalStructure(self.config.swing_k)
        self._flow = _FlowTracker(self.config.cvd_lookback)
        self._bars: list[Bar] = []
        self._fvgs: list[FVGZone] = []
        self._obs: list[OrderBlockZone] = []
        self._sweeps: list[LiquiditySweep] = []
        self._next_zone_id = 0

    @property
    def fvg_zones(self) -> tuple[FVGZone, ...]:
        return tuple(self._fvgs)

    @property
    def order_blocks(self) -> tuple[OrderBlockZone, ...]:
        return tuple(self._obs)

    def register_htf_sweep(self, sweep: LiquiditySweep) -> None:
        if self._bars and sweep.index > self._bars[-1].index:
            raise StrategyInputError("an HTF sweep cannot be registered from the future")
        self._sweeps.append(sweep)

    def _new_fvg(self, bar: Bar) -> FVGZone | None:
        if len(self._bars) < 2:
            return None
        first = self._bars[-2]
        if bar.low > first.high:
            zone = FVGZone(self._next_zone_id, Direction.LONG, first.index, bar.index, first.high, bar.low)
        elif bar.high < first.low:
            zone = FVGZone(self._next_zone_id, Direction.SHORT, first.index, bar.index, bar.high, first.low)
        else:
            return None
        self._next_zone_id += 1
        self._fvgs.append(zone)
        return zone

    def _new_order_block(self, event: StructureBreak, bar: Bar) -> OrderBlockZone | None:
        if event.direction is None or event.origin_index is None:
            return None
        candidates = self._bars[event.origin_index :]
        opposite = [
            b for b in candidates
            if (b.close < b.open if event.direction is Direction.LONG else b.close > b.open)
        ]
        if not opposite:
            return None
        source = opposite[-1]
        zone = OrderBlockZone(
            self._next_zone_id,
            event.direction,
            event.event,
            source.index,
            bar.index,
            source.low,
            source.high,
            min(source.open, source.close),
            max(source.open, source.close),
        )
        self._next_zone_id += 1
        self._obs.append(zone)
        return zone

    def _funding_status(self, bar: Bar) -> FundingStatus:
        if bar.funding_rate is None:
            return FundingStatus.UNKNOWN if self.config.require_cool_funding else FundingStatus.NOT_REQUIRED
        return (
            FundingStatus.COOL
            if abs(float(bar.funding_rate)) <= self.config.maximum_abs_funding_rate
            else FundingStatus.HOT
        )

    def _flow_status(self, bar: Bar, direction: Direction | None) -> FlowStatus:
        return self._flow.status_for(bar.spot_cvd_delta, direction, self.config.require_spot_cvd)

    def _wave_metrics(self, event: StructureBreak, bar: Bar, volume_z: float | None, atr: float | None) -> WaveMetrics:
        if event.origin_price is None or event.origin_index is None:
            return WaveMetrics(None, None, None, atr, volume_z, None)
        bars = bar.index - event.origin_index + 1
        adi = adaptive_displacement_index(event.origin_price, bar.close, bars, atr, event.direction) if event.direction and atr is not None else None
        return WaveMetrics(event.origin_price, bar.close, bars, atr, volume_z, adi)

    def _recent_sweep(self, direction: Direction, index: int) -> LiquiditySweep | None:
        candidates = [s for s in self._sweeps if s.direction is direction and 0 <= index - s.index <= self.config.maximum_sweep_age_bars]
        return max(candidates, key=lambda s: s.index) if candidates else None

    def _speed_ratio(self, sweep_index: int, current_index: int, current_bar: Bar) -> float | None:
        # ``current_bar`` is already complete and may be used, but it is not
        # committed to ``self._bars`` until the entire decision is finished.
        up = self._bars[sweep_index + 1 : current_index] + [current_bar]
        prior = self._bars[max(0, sweep_index - self.config.speed_lookback_bars) : sweep_index]
        up_bodies = [b.close - b.open for b in up if b.close > b.open]
        down_bodies = [b.open - b.close for b in prior if b.close < b.open]
        if not up_bodies or not down_bodies:
            return None
        return (sum(up_bodies) / len(up_bodies)) / (sum(down_bodies) / len(down_bodies))

    def _validate_choch(
        self,
        event: StructureBreak,
        bar: Bar,
        volume_z: float | None,
        atr: float | None,
        flow_status: FlowStatus,
        funding_status: FundingStatus,
    ) -> ChochValidation:
        if event.event not in ("CHOCH_UP", "CHOCH_DOWN") or event.direction is None:
            return ChochValidation(False, event.direction, event.level, volume_z, None, None, flow_status, "NOT_A_CHoCH_EVENT", funding_status)
        sweep = self._recent_sweep(event.direction, bar.index)
        if sweep is None:
            return ChochValidation(False, event.direction, event.level, volume_z, None, None, flow_status, "NO_RECENT_MATCHING_HTF_SWEEP", funding_status)
        ratio = self._speed_ratio(sweep.index, bar.index, bar)
        distance = None if atr is None or atr <= 0 or event.level is None else abs(event.level - sweep.extreme) / atr
        volume_ok = volume_z is not None and volume_z > self.config.volume_z_threshold
        distance_ok = distance is not None and distance > self.config.choch_min_distance_atr
        speed_ok = ratio is not None and ratio >= self.config.choch_min_speed_ratio
        flow_ok = flow_status is FlowStatus.VALID or (not self.config.require_spot_cvd and flow_status is FlowStatus.NOT_REQUIRED)
        funding_ok = funding_status is not FundingStatus.HOT and (
            not self.config.require_cool_funding or funding_status is FundingStatus.COOL
        )
        if volume_ok and distance_ok and speed_ok and flow_ok and funding_ok:
            return ChochValidation(True, event.direction, event.level, volume_z, ratio, distance, flow_status, "BODY_CHoCH_PLUS_SPEED_PLUS_DISTANCE_PLUS_FLOW_CONFIRMED", funding_status)
        reasons = []
        if not volume_ok:
            reasons.append("VOLUME_ANOMALY_MISSING")
        if not distance_ok:
            reasons.append("STRUCTURAL_DISTANCE_TOO_SMALL")
        if not speed_ok:
            reasons.append("DISPLACEMENT_SPEED_TOO_SLOW")
        if not flow_ok:
            reasons.append("SPOT_FLOW_NOT_CONFIRMED")
        if not funding_ok:
            reasons.append("FUNDING_HEAT_GATE_BLOCKED")
        return ChochValidation(False, event.direction, event.level, volume_z, ratio, distance, flow_status, "+".join(reasons), funding_status)

    def _zone_is_unmitigated(self, creation_index: int, low: float, high: float) -> bool:
        """Reject a target zone already traded through by a later completed bar."""

        for previous in self._bars:
            if previous.index <= creation_index:
                continue
            if previous.high >= low and previous.low <= high:
                return False
        return True

    def _target_from_zones(
        self,
        direction: Direction,
        entry: float,
        fvgs: Iterable[FVGZone],
        obs: Iterable[OrderBlockZone],
    ) -> tuple[float | None, int | None, int | None]:
        candidates: list[tuple[float, int, int | None, int | None]] = []
        if direction is Direction.LONG:
            for z in fvgs:
                if z.direction is Direction.SHORT and z.high > entry and self._zone_is_unmitigated(z.creation_index, z.low, z.high):
                    candidates.append((z.low if z.low > entry else z.high, z.creation_index, z.zone_id, None))
            for z in obs:
                if z.direction is Direction.SHORT and z.high > entry and self._zone_is_unmitigated(z.creation_index, z.low, z.high):
                    candidates.append((z.low if z.low > entry else z.high, z.creation_index, None, z.zone_id))
        else:
            for z in fvgs:
                if z.direction is Direction.LONG and z.low < entry and self._zone_is_unmitigated(z.creation_index, z.low, z.high):
                    candidates.append((z.high if z.high < entry else z.low, z.creation_index, z.zone_id, None))
            for z in obs:
                if z.direction is Direction.LONG and z.low < entry and self._zone_is_unmitigated(z.creation_index, z.low, z.high):
                    candidates.append((z.high if z.high < entry else z.low, z.creation_index, None, z.zone_id))
        if not candidates:
            return None, None, None
        selected = min(candidates, key=lambda x: (abs(x[0] - entry), x[1]))
        return selected[0], selected[2], selected[3]

    def _plan(self, *, setup: str, direction: Direction, profile: Profile, entry: float, stop: float, target: float | None, index: int, fvg_id: int | None, ob_id: int | None, invalidation: float, reason: str) -> TradePlan | None:
        risk = (entry - stop) if direction is Direction.LONG else (stop - entry)
        if risk <= 0 or target is None:
            return None
        rr = ((target - entry) / risk) if direction is Direction.LONG else ((entry - target) / risk)
        minimum_target = entry + direction.sign * self.config.minimum_rr * risk
        if rr < self.config.minimum_rr:
            return None
        return TradePlan(
            plan_id=f"{setup}:{index}:{fvg_id if fvg_id is not None else ob_id}",
            setup=setup,
            direction=direction,
            profile=profile,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            minimum_target_price=minimum_target,
            risk=risk,
            planned_rr=rr,
            creation_index=index,
            expires_index=index + self.config.pending_expiry_bars,
            fvg_id=fvg_id,
            ob_id=ob_id,
            invalidation_price=invalidation,
            reason=reason,
        )

    def _select_deep_ob(self, direction: Direction, origin: float, termination: float, current_price: float) -> OrderBlockZone | None:
        move = abs(termination - origin)
        if move <= 0:
            return None
        valid: list[OrderBlockZone] = []
        for zone in self._obs:
            if zone.direction is not direction:
                continue
            if direction is Direction.LONG and zone.high >= current_price:
                continue
            if direction is Direction.SHORT and zone.low <= current_price:
                continue
            if direction is Direction.LONG:
                retrace_low = (termination - zone.high) / move
                retrace_high = (termination - zone.low) / move
            else:
                retrace_low = (zone.low - termination) / move
                retrace_high = (zone.high - termination) / move
            if retrace_high >= self.config.deep_ob_retrace_min and retrace_low <= self.config.deep_ob_retrace_max:
                valid.append(zone)
        return max(valid, key=lambda z: z.creation_index) if valid else None

    def update(self, bar: Bar) -> BarEvaluation:
        if bar.index != len(self._bars):
            raise StrategyInputError("bars must be supplied once, in consecutive index order")

        atr = self._atr.peek()
        volume_z = self._volume.zscore(bar.volume, self.config.minimum_volume_history)
        event = self._structure.evaluate(bar)
        flow_status = self._flow_status(bar, event.direction)
        funding_status = self._funding_status(bar)
        wave = self._wave_metrics(event, bar, volume_z, atr)
        decision = choose_profile(
            metrics=wave,
            flow_status=flow_status,
            config=self.config,
            funding_status=funding_status,
        )
        fvg = self._new_fvg(bar)
        ob = self._new_order_block(event, bar)
        choch = (
            self._validate_choch(event, bar, volume_z, atr, flow_status, funding_status)
            if event.event.startswith("CHOCH") else None
        )
        plan: TradePlan | None = None

        if event.direction is not None and event.event in ("BOS_UP", "BOS_DOWN") and event.origin_price is not None:
            if decision.allow_shallow_fvg and fvg is not None and fvg.direction is event.direction:
                # The boundary itself is Low(Candle 3) for a bullish FVG (and
                # High(Candle 3) for a bearish FVG).  The exchange tick-size
                # validator is responsible for rounding; moving one tick
                # inside the zone would collapse the risk against the
                # protected impulse stop when Candle 3 is the impulse bar.
                entry = fvg.high if event.direction is Direction.LONG else fvg.low
                stop = protected_momentum_stop(event.direction, bar, self.config.tick_size)
                target, target_fvg, target_ob = self._target_from_zones(event.direction, entry, self._fvgs[:-1], self._obs)
                plan = self._plan(
                    setup="AGGRESSIVE_SHALLOW_FVG",
                    direction=event.direction,
                    profile=Profile.AGGRESSIVE,
                    entry=entry,
                    stop=stop,
                    target=target,
                    index=bar.index,
                    fvg_id=fvg.zone_id,
                    ob_id=target_ob,
                    invalidation=stop,
                    reason="TOP_OF_SHALLOW_FVG_WITH_PROTECTED_IMPULSE_STOP",
                )
            elif decision.profile is not Profile.WARMUP:
                deep = self._select_deep_ob(event.direction, event.origin_price, bar.close, bar.close)
                if deep is not None:
                    entry = deep.high if event.direction is Direction.LONG else deep.low
                    stop = event.origin_price - self.config.tick_size if event.direction is Direction.LONG else event.origin_price + self.config.tick_size
                    target, _, _ = self._target_from_zones(event.direction, entry, self._fvgs, self._obs)
                    plan = self._plan(
                        setup="DEFENSIVE_DEEP_OB",
                        direction=event.direction,
                        profile=Profile.DEFENSIVE,
                        entry=entry,
                        stop=stop,
                        target=target,
                        index=bar.index,
                        fvg_id=None,
                        ob_id=deep.zone_id,
                        invalidation=stop,
                        reason="SHALLOW_ENTRY_BLOCKED_WAITING_FOR_DEEP_DISCOUNT_OB",
                    )

        if choch is not None and choch.valid and fvg is not None and fvg.direction is choch.direction:
            sweep = self._recent_sweep(choch.direction, bar.index)
            if sweep is not None:
                entry = fvg.high if choch.direction is Direction.LONG else fvg.low
                stop = sweep.extreme - self.config.tick_size if choch.direction is Direction.LONG else sweep.extreme + self.config.tick_size
                target, target_fvg, target_ob = self._target_from_zones(choch.direction, entry, self._fvgs[:-1], self._obs)
                plan = self._plan(
                    setup="COUNTER_TREND_CHOCH_FVG",
                    direction=choch.direction,
                    profile=Profile.DEFENSIVE,
                    entry=entry,
                    stop=stop,
                    target=target,
                    index=bar.index,
                    fvg_id=fvg.zone_id,
                    ob_id=target_ob,
                    invalidation=stop,
                    reason="HTF_SWEEP_PLUS_BODY_CHOCH_PLUS_SPOT_FLOW_GATE",
                )

        # Commit all current-bar facts only after decisions have consumed prior state.
        self._bars.append(bar)
        self._structure.commit_break(event)
        self._structure.commit_bar(bar)
        self._volume.push(bar.volume)
        self._atr.push(bar)
        self._flow.push(bar.spot_cvd_delta)

        return BarEvaluation(bar.index, volume_z, atr, event, wave, decision, fvg, ob, choch, plan)

    def scan(self, bars: Iterable[Bar]) -> tuple[BarEvaluation, ...]:
        return tuple(self.update(bar) for bar in bars)


__all__ = [
    "Bar", "BarEvaluation", "ChochValidation", "Direction", "DynamicProfileConfig",
    "DynamicProfileEngine", "FVGZone", "FlowStatus", "FundingStatus", "LiquiditySweep", "OrderBlockZone",
    "Profile", "ProfileDecision", "StrategyInputError", "StructureBreak", "SwingPoint",
    "TradePlan", "WaveMetrics", "adaptive_displacement_index", "choose_profile",
    "protected_momentum_stop", "spot_cvd_delta_from_binance_kline", "tighten_stop",
    "volume_zscore",
]
