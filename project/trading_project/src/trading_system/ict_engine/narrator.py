"""Causal Arabic chart narration and prefix-only M2 decision predictions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .data import Candle
from .displacement import displacement_trace
from .gaps import GapEventKind, fvg_trace
from .htf import (
    CalendarAnchor,
    HigherTimeframe,
    htf_extreme_pools,
    htf_trace,
)
from .liquidity import (
    LiquidityPool,
    PoolEventKind,
    PoolKind,
    RankedDraw,
    liquidity_trace,
    pool_draw,
    rank_draws,
)
from .management import BreakEvenContext, BreakEvenState, break_even_states
from .market_status import MarketStatus, market_status
from .order_blocks import (
    OrderBlockDirection,
    OrderBlockEventKind,
    OrderBlockZone,
    order_block_trace,
)
from .predictions import Prediction, PredictionType
from .price import PriceBasis, ohlc
from .ranges import (
    RANGE_CLAIM_IDS,
    RangeObservation,
    RangePosition,
    dealing_range_trace,
)
from .sessions import CLOCK_VARIANTS, ClockDefinition, observe_session
from .swings import SwingSide, swing_trace
from .variants import EngineVariant, TargetRanking


class DecisionType(str, Enum):
    TARGET_CHOICE = "target_choice"
    ENTRY_CHOICE = "entry_choice"
    STOP_CHOICE = "stop_choice"
    STAND_ASIDE = "stand_aside"
    MANAGEMENT = "management"


@dataclass(frozen=True, slots=True)
class NarrationEvent:
    event_id: str
    available_at: datetime
    concept: str
    claim_ids: tuple[str, ...]
    text: str


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    available_at: datetime
    decision_type: DecisionType
    concept: str
    claim_ids: tuple[str, ...]
    reason: str
    prediction_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChartReading:
    available_at: datetime
    narration: tuple[NarrationEvent, ...]
    predictions: tuple[Prediction, ...]
    decisions: tuple[DecisionRecord, ...]
    management: tuple[BreakEvenState, ...]


@dataclass(slots=True)
class _ActiveOrderBlock:
    zone: OrderBlockZone
    touched: bool = False


def _claims(*groups: str | tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for group in groups:
        values = (group,) if isinstance(group, str) else group
        for value in values:
            if value not in result:
                result.append(value)
    return tuple(result)


def _price(value: float) -> str:
    return format(value, ".12g")


def _narration(
    variant: EngineVariant,
    available_at: datetime,
    source_id: str,
    concept: str,
    claim_ids: tuple[str, ...],
    text: str,
) -> NarrationEvent:
    return NarrationEvent(
        event_id=f"n:{variant.variant_id}:{source_id}",
        available_at=available_at,
        concept=concept,
        claim_ids=claim_ids,
        text=text,
    )


def _decision(
    variant: EngineVariant,
    available_at: datetime,
    source_id: str,
    decision_type: DecisionType,
    concept: str,
    claim_ids: tuple[str, ...],
    reason: str,
    prediction_id: str | None = None,
) -> DecisionRecord:
    return DecisionRecord(
        decision_id=f"d:{variant.variant_id}:{decision_type.value}:{source_id}",
        available_at=available_at,
        decision_type=decision_type,
        concept=concept,
        claim_ids=claim_ids,
        reason=reason,
        prediction_id=prediction_id,
    )


def _direction(side: SwingSide) -> OrderBlockDirection:
    return (
        OrderBlockDirection.BULLISH
        if side is SwingSide.HIGH
        else OrderBlockDirection.BEARISH
    )


def _pool_is_ahead(pool: LiquidityPool, close: float) -> bool:
    return (pool.side is SwingSide.HIGH and close < pool.level) or (
        pool.side is SwingSide.LOW and close > pool.level
    )


def _target_choice_claims(pool: LiquidityPool) -> tuple[str, ...]:
    if pool.side is SwingSide.LOW:
        return ("K2C-013", "U0167")
    if pool.kind is PoolKind.RELATIVE_EQUAL_PAIR:
        return ("U0205", "U0206")
    return ("K2C-040", "U0189")


def _draw_prediction(
    variant: EngineVariant, pool: LiquidityPool, candle: Candle
) -> Prediction | None:
    if market_status(candle) is not MarketStatus.MARKET:
        return None
    close = ohlc(candle, variant.basis)[3]
    if not _pool_is_ahead(pool, close):
        return None
    direction = _direction(pool.side)
    claims = _claims(pool.claim_ids, _target_choice_claims(pool), "U0020")
    if pool.side is SwingSide.HIGH:
        expectation = f"تجاوز صارم فوق مستوى السيولة المرشح {_price(pool.level)}."
        invalidation = "اكتمال 288 شمعة سوق لاحقة من دون تجاوز المستوى."
    else:
        expectation = f"اختراق صارم دون مستوى السيولة المرشح {_price(pool.level)}."
        invalidation = "اكتمال 288 شمعة سوق لاحقة من دون اختراق المستوى."
    return Prediction(
        prediction_id=f"p:{variant.variant_id}:draw:{pool.pool_id}",
        available_at=candle.end,
        variant_id=variant.variant_id,
        concept="liquidity_pool_candidate",
        prediction_type=PredictionType.DRAW_TOUCH,
        direction=direction,
        basis=variant.basis,
        claim_ids=claims,
        expectation=expectation,
        invalidation=invalidation,
        source_event_id=f"{pool.pool_id}:formed:{candle.end.isoformat()}",
        target_id=pool.pool_id,
        target_price=pool.level,
    )


def _ob_prediction(
    variant: EngineVariant, zone: OrderBlockZone, candle: Candle
) -> Prediction:
    return Prediction(
        prediction_id=f"p:{variant.variant_id}:ob:{zone.zone_id}",
        available_at=candle.end,
        variant_id=variant.variant_id,
        concept="order_block_candidate",
        prediction_type=PredictionType.OB_FIRST_RETRACEMENT,
        direction=zone.direction,
        basis=variant.basis,
        claim_ids=_claims(zone.claim_ids, "K2C-004"),
        expectation="أول عودة إلى منطقة الكتلة المرشحة قبل انتهاك جانبها البعيد.",
        invalidation=(
            f"انتهاك الجانب البعيد {_price(zone.far_side)} قبل أول لمس، "
            "أو اكتمال 288 شمعة سوق بلا لمس؛ واجتماع اللمس والانتهاك غير محسوم."
        ),
        source_event_id=f"{zone.zone_id}:created:{candle.end.isoformat()}",
        stop_price=zone.far_side,
        zone_lower=min(zone.opening, zone.far_side),
        zone_upper=max(zone.opening, zone.far_side),
    )


def select_target(
    pools: Sequence[LiquidityPool],
    *,
    direction: OrderBlockDirection,
    entry: float,
    range_observation: RangeObservation,
    ranking: TargetRanking,
) -> tuple[LiquidityPool, RankedDraw] | None:
    """Select an active ahead pool using only the pre-registered ranking."""

    dealing_range = range_observation.dealing_range
    if dealing_range is None or dealing_range.high <= dealing_range.low:
        return None
    wanted_side = (
        SwingSide.HIGH
        if direction is OrderBlockDirection.BULLISH
        else SwingSide.LOW
    )
    candidates = tuple(
        pool
        for pool in pools
        if pool.side is wanted_side and _pool_is_ahead(pool, entry)
    )
    if not candidates:
        return None
    ranked = rank_draws(
        tuple(pool_draw(pool) for pool in candidates),
        current_price=entry,
        recent_range=dealing_range.high - dealing_range.low,
    )
    by_id = {pool.pool_id: pool for pool in candidates}
    if ranking is TargetRanking.DAILY_THEN_DISTANCE:
        chosen = min(
            ranked,
            key=lambda item: (
                item.timeframe_significance_rank
                if item.timeframe_significance_rank is not None
                else 10**9,
                item.distance_rank,
                item.draw.candidate_id,
            ),
        )
    else:
        chosen = min(
            ranked,
            key=lambda item: (item.distance_rank, item.draw.candidate_id),
        )
    return by_id[chosen.draw.candidate_id], chosen


def _stand_aside(
    variant: EngineVariant,
    candle: Candle,
    zone: OrderBlockZone,
    reason_code: str,
    reason: str,
    claim_ids: tuple[str, ...],
) -> DecisionRecord:
    return _decision(
        variant,
        candle.end,
        f"{zone.zone_id}:{reason_code}",
        DecisionType.STAND_ASIDE,
        "stand_aside",
        _claims(
            claim_ids,
            "K2C-019",
            "K2C-020",
            "K2C-021",
            "K2C-022",
            "K2C-023",
            "K2C-024",
            "K2C-026",
        ),
        reason,
    )


def _setup_at_first_touch(
    variant: EngineVariant,
    candle: Candle,
    zone: OrderBlockZone,
    range_observation: RangeObservation,
    active_pools: Sequence[LiquidityPool],
) -> tuple[
    Prediction | None,
    tuple[DecisionRecord, ...],
    tuple[BreakEvenState, ...],
    tuple[NarrationEvent, ...],
]:
    """Apply all gates at the first-touch close; never inspect a later bar."""

    _, _, _, entry = ohlc(candle, variant.basis)
    if zone.direction is OrderBlockDirection.BULLISH:
        position_ok = range_observation.position in {
            RangePosition.DISCOUNT,
            RangePosition.EQUILIBRIUM,
        }
        position_claims = ("K2C-002", "K2C-003", "K2C-016", "K2C-037")
    else:
        position_ok = range_observation.position is RangePosition.PREMIUM
        position_claims = ("K2C-038",)
    range_claims = (
        _claims(
            range_observation.dealing_range.claim_ids,
            "U0149",
            "U0150",
            "U0151",
            "U0152",
        )
        if range_observation.dealing_range is not None
        else RANGE_CLAIM_IDS
    )
    if not position_ok:
        aside = _stand_aside(
            variant,
            candle,
            zone,
            "range_position",
            "الامتناع: موضع النطاق غير مناسب أو غير محدد، ولا يكفي وحده للدخول.",
            _claims(range_claims, position_claims),
        )
        return None, (aside,), (), ()

    clock = next(item for item in CLOCK_VARIANTS if item.definition_id is variant.clock)
    session = observe_session(candle, clock)
    if session.in_window is not True:
        aside = _stand_aside(
            variant,
            candle,
            zone,
            "outside_window",
            "الامتناع: أول عودة وقعت خارج نافذة الوقت المثبتة.",
            _claims(clock.claim_ids, "K2C-028"),
        )
        return None, (aside,), (), ()

    dealing_range = range_observation.dealing_range
    selected = select_target(
        active_pools,
        direction=zone.direction,
        entry=entry,
        range_observation=range_observation,
        ranking=variant.target_ranking,
    )
    if selected is None or dealing_range is None:
        aside = _stand_aside(
            variant,
            candle,
            zone,
            "no_target",
            "الامتناع: لا يوجد مستوى سيولة نشط في الاتجاه وخلف الدخول.",
            ("K2C-013", "K2C-040", "K2C-025"),
        )
        return None, (aside,), (), ()
    target, ranked_target = selected

    entry_decimal = Decimal(str(entry))
    stop_decimal = Decimal(str(zone.far_side))
    target_decimal = Decimal(str(target.level))
    if zone.direction is OrderBlockDirection.BULLISH:
        reward = target_decimal - entry_decimal
        risk = entry_decimal - stop_decimal
    else:
        reward = entry_decimal - target_decimal
        risk = stop_decimal - entry_decimal
    if reward <= 0 or risk <= 0:
        aside = _stand_aside(
            variant,
            candle,
            zone,
            "invalid_geometry",
            "الامتناع: هندسة الدخول والهدف والوقف لا تعطي مسافتين موجبتين.",
            ("U0048",),
        )
        return None, (aside,), (), ()

    reward_risk = reward / risk
    if reward_risk < Decimal("3"):
        aside = _stand_aside(
            variant,
            candle,
            zone,
            "below_three",
            "الامتناع: مسافة الهدف أقل من ثلاثة أمثال مسافة الوقف.",
            ("K2C-042",),
        )
        return None, (aside,), (), ()

    source_id = f"{zone.zone_id}:first_touch:{candle.end.isoformat()}"
    prediction_id = f"p:{variant.variant_id}:setup:{zone.zone_id}"
    target_choice_claims = _target_choice_claims(target)
    ranking_claims = (
        ("U0024", "U0025", "U0020", "K2C-009")
        if variant.target_ranking is TargetRanking.DAILY_THEN_DISTANCE
        else ("U0020",)
    )
    claims = _claims(
        zone.claim_ids,
        target.claim_ids,
        range_claims,
        position_claims,
        clock.claim_ids,
        ranking_claims,
        "K2C-004",
        "K2C-028",
        "K2C-042",
        target_choice_claims,
    )
    prediction = Prediction(
        prediction_id=prediction_id,
        available_at=candle.end,
        variant_id=variant.variant_id,
        concept="candidate_first_retracement_continuation",
        prediction_type=PredictionType.SETUP_TARGET_BEFORE_STOP,
        direction=zone.direction,
        basis=variant.basis,
        claim_ids=claims,
        expectation=(
            f"بلوغ الهدف {_price(target.level)} قبل الوقف "
            f"{_price(zone.far_side)}، بدءاً من الشمعة التالية للدخول الرصدي."
        ),
        invalidation=(
            "انتهاك الوقف أولاً أو اكتمال 288 شمعة سوق بلا حسم؛ "
            "واجتماع الهدف والوقف في شمعة واحدة غير محسوم."
        ),
        source_event_id=source_id,
        entry_price=entry,
        target_id=target.pool_id,
        target_price=target.level,
        stop_price=zone.far_side,
        reward_risk=str(reward_risk),
    )
    decisions = (
        _decision(
            variant,
            candle.end,
            source_id + ":target",
            DecisionType.TARGET_CHOICE,
            "target_choice",
            _claims(target.claim_ids, ranking_claims, target_choice_claims),
            (
                f"اختير {target.pool_id} بترتيب {ranked_target.distance_rank} للمسافة "
                f"وترتيب الإطار {ranked_target.timeframe_significance_rank}."
            ),
            prediction_id,
        ),
        _decision(
            variant,
            candle.end,
            source_id + ":entry",
            DecisionType.ENTRY_CHOICE,
            "entry_choice",
            _claims(zone.claim_ids, range_claims, position_claims, clock.claim_ids, "K2C-004", "K2C-028"),
            f"الدخول الرصدي عند إغلاق أول عودة: {_price(entry)}.",
            prediction_id,
        ),
        _decision(
            variant,
            candle.end,
            source_id + ":stop",
            DecisionType.STOP_CHOICE,
            "stop_choice",
            ("U0048", "K2C-042"),
            (
                f"الوقف عند الجانب البعيد {_price(zone.far_side)}؛ "
                f"نسبة المسافتين {reward_risk}."
            ),
            prediction_id,
        ),
    )
    management = break_even_states(
        BreakEvenContext(
            first_profit_taken=False,
            objective_progress=Decimal("0"),
            london_active=True,
            long_term=False,
        )
    )
    management_narration = tuple(
        _narration(
            variant,
            candle.end,
            source_id + f":management:{state.variant.value}",
            "break_even_management",
            state.claim_ids,
            f"حالة إدارة التعادل {state.variant.value}: {state.action.value}.",
        )
        for state in management
    )
    return prediction, decisions, management, management_narration


def _daily_pools_for_basis(
    completed,
    *,
    available_at: datetime,
    basis: PriceBasis,
) -> tuple[LiquidityPool, LiquidityPool]:
    pools = htf_extreme_pools(completed, available_at=available_at)
    if basis is PriceBasis.BID:
        return pools
    return (
        replace(
            pools[0],
            level=completed.ask_high,
            member_levels=(completed.ask_high,),
        ),
        replace(
            pools[1],
            level=completed.ask_low,
            member_levels=(completed.ask_low,),
        ),
    )


def reading_trace(
    candles: Sequence[Candle], variant: EngineVariant
) -> tuple[ChartReading, ...]:
    """Narrate every M1 event and emit predictions from each closed prefix."""

    basis = variant.basis
    swings = swing_trace(candles, basis)
    ranges = dealing_range_trace(candles, basis)
    displacements = displacement_trace(candles, basis)
    gaps = fvg_trace(candles, basis)
    pools = liquidity_trace(candles, basis)
    order_blocks = order_block_trace(candles, variant.order_block, basis)
    htf = {
        (timeframe, anchor): htf_trace(candles, timeframe, anchor)
        for timeframe in HigherTimeframe
        for anchor in CalendarAnchor
    }

    active_pools: dict[str, LiquidityPool] = {}
    daily_pool_ids: set[str] = set()
    daily_awaiting_return: dict[str, LiquidityPool] = {}
    active_order_blocks: dict[str, _ActiveOrderBlock] = {}
    trace: list[ChartReading] = []

    for index, candle in enumerate(candles):
        narration: list[NarrationEvent] = []
        predictions: list[Prediction] = []
        decisions: list[DecisionRecord] = []
        management: tuple[BreakEvenState, ...] = ()
        status = market_status(candle)
        _, high, low, close = ohlc(candle, basis)

        if status is MarketStatus.UNRESOLVED_ZERO_VOLUME:
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"market:{candle.start.isoformat()}:unresolved",
                    "market_status",
                    (),
                    "حجم الصفر غير مسطح؛ الحالة غير محسومة ولا تولد إشارة سوق.",
                )
            )

        for swing in swings[index]:
            side_text = "قمة" if swing.side is SwingSide.HIGH else "قاع"
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"swing:{basis.value}:{swing.side.value}:{swing.source_time.isoformat()}",
                    "swing_candidate",
                    _claims(swing.claim_ids, "U0217", "U0218")
                    if swing.side is SwingSide.HIGH
                    else swing.claim_ids,
                    f"تأكد {side_text} مرشحاً عند {_price(swing.price)}؛ الهرمية ما زالت في الانتظار.",
                )
            )

        range_observation = ranges[index]
        dealing_range = range_observation.dealing_range
        if dealing_range is not None and dealing_range.selected_at == candle.end:
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"range:{basis.value}:{candle.end.isoformat()}",
                    "dealing_range",
                    dealing_range.claim_ids,
                    (
                        f"تحدث نطاق التعامل: {_price(dealing_range.low)} إلى "
                        f"{_price(dealing_range.high)}، والتعادل {_price(dealing_range.equilibrium)}."
                    ),
                )
            )

        displacement = displacements[index]
        if displacement.is_displacement and displacement.broken_swing is not None:
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"displacement:{basis.value}:{candle.end.isoformat()}",
                    "displacement",
                    displacement.claim_ids,
                    (
                        f"إزاحة برتبة مدى {displacement.range_rank} وإغلاق خلف "
                        f"{displacement.broken_swing.side.value} عند {_price(displacement.broken_swing.price)}."
                    ),
                )
            )

        for event in gaps[index]:
            gap = event.gap
            text = {
                GapEventKind.CREATED: "تكونت فجوة قيمة عادلة",
                GapEventKind.FIRST_TOUCH: "حدث أول لمس لفجوة القيمة العادلة",
                GapEventKind.FULLY_CLOSED: "أغلقت فجوة القيمة العادلة كاملة؛ هذا رصد لا حكم فشل",
            }[event.kind]
            additional_claims = {
                GapEventKind.CREATED: ("U0153", "U0155"),
                GapEventKind.FIRST_TOUCH: ("U0201", "U0203", "U0204"),
                GapEventKind.FULLY_CLOSED: ("U0201",),
            }[event.kind]
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"{gap.gap_id}:{event.kind.value}:{candle.end.isoformat()}",
                    "fair_value_gap",
                    _claims(event.claim_ids, additional_claims),
                    f"{text} بين {_price(gap.lower)} و{_price(gap.upper)}.",
                )
            )

        # Existing daily pools are updated before newly knowable pools are added.
        for pool_id in tuple(sorted(daily_awaiting_return)):
            pool = daily_awaiting_return[pool_id]
            returned = (pool.side is SwingSide.HIGH and close < pool.level) or (
                pool.side is SwingSide.LOW and close > pool.level
            )
            if status is MarketStatus.MARKET and returned:
                narration.append(
                    _narration(
                        variant,
                        candle.end,
                        f"{pool_id}:returned:{candle.end.isoformat()}",
                        "liquidity_pool",
                        pool.claim_ids,
                        f"عاد الإغلاق داخل المستوى اليومي {_price(pool.level)}.",
                    )
                )
                del daily_awaiting_return[pool_id]

        for pool_id in tuple(sorted(daily_pool_ids)):
            pool = active_pools.get(pool_id)
            if pool is None or status is not MarketStatus.MARKET:
                continue
            taken = (pool.side is SwingSide.HIGH and high > pool.level) or (
                pool.side is SwingSide.LOW and low < pool.level
            )
            if not taken:
                continue
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"{pool_id}:taken:{candle.end.isoformat()}",
                    "liquidity_pool",
                    pool.claim_ids,
                    f"أخذ مستوى السيولة اليومية {_price(pool.level)}.",
                )
            )
            del active_pools[pool_id]
            daily_pool_ids.remove(pool_id)
            returned = (pool.side is SwingSide.HIGH and close < pool.level) or (
                pool.side is SwingSide.LOW and close > pool.level
            )
            if returned:
                narration.append(
                    _narration(
                        variant,
                        candle.end,
                        f"{pool_id}:returned:{candle.end.isoformat()}",
                        "liquidity_pool",
                        pool.claim_ids,
                        f"عاد الإغلاق داخل المستوى اليومي {_price(pool.level)} في شمعة الأخذ.",
                    )
                )
            else:
                daily_awaiting_return[pool_id] = pool

        for event in pools[index]:
            pool = event.pool
            if event.kind is PoolEventKind.FORMED:
                active_pools[pool.pool_id] = pool
            elif event.kind is PoolEventKind.TAKEN:
                active_pools.pop(pool.pool_id, None)
            text = {
                PoolEventKind.FORMED: "تكون مستوى سيولة مرشح",
                PoolEventKind.TAKEN: "أخذ مستوى السيولة المرشح",
                PoolEventKind.RETURNED_INSIDE: "عاد الإغلاق داخل مستوى السيولة",
            }[event.kind]
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"{pool.pool_id}:{event.kind.value}:{candle.end.isoformat()}",
                    "liquidity_pool",
                    event.claim_ids,
                    f"{text} عند {_price(pool.level)}.",
                )
            )
            if event.kind is PoolEventKind.FORMED:
                prediction = _draw_prediction(variant, pool, candle)
                if prediction is not None:
                    predictions.append(prediction)
                    decisions.append(
                        _decision(
                            variant,
                            candle.end,
                            prediction.prediction_id,
                            DecisionType.TARGET_CHOICE,
                            "target_choice",
                            prediction.claim_ids,
                            f"الهدف المرشح هو المستوى غير المأخوذ {_price(pool.level)}.",
                            prediction.prediction_id,
                        )
                    )

        selected_daily = htf[(HigherTimeframe.DAILY, variant.daily_anchor)][index]
        for completed in selected_daily.newly_completed:
            for pool in _daily_pools_for_basis(
                completed, available_at=candle.end, basis=basis
            ):
                active_pools[pool.pool_id] = pool
                daily_pool_ids.add(pool.pool_id)
                narration.append(
                    _narration(
                        variant,
                        candle.end,
                        f"{pool.pool_id}:formed:{candle.end.isoformat()}",
                        "higher_timeframe_liquidity",
                        pool.claim_ids,
                        f"أضيف طرف يومي مكتمل كمستوى سيولة عند {_price(pool.level)}.",
                    )
                )
                prediction = _draw_prediction(variant, pool, candle)
                if prediction is not None:
                    predictions.append(prediction)
                    decisions.append(
                        _decision(
                            variant,
                            candle.end,
                            prediction.prediction_id,
                            DecisionType.TARGET_CHOICE,
                            "target_choice",
                            prediction.claim_ids,
                            f"الهدف اليومي المكتمل المرشح عند {_price(pool.level)}.",
                            prediction.prediction_id,
                        )
                    )

        violated_ids = {
            event.zone.zone_id
            for event in order_blocks[index]
            if event.kind is OrderBlockEventKind.VIOLATED
        }
        for zone_id in tuple(sorted(active_order_blocks)):
            state = active_order_blocks[zone_id]
            zone = state.zone
            if status is MarketStatus.MARKET and not state.touched:
                lower = min(zone.opening, zone.far_side)
                upper = max(zone.opening, zone.far_side)
                touches = high > lower and low < upper
                if touches:
                    state.touched = True
                    narration.append(
                        _narration(
                            variant,
                            candle.end,
                            f"{zone_id}:first_touch:{candle.end.isoformat()}",
                            "order_block_first_retracement",
                            _claims(zone.claim_ids, "K2C-004"),
                            "حدثت أول عودة إلى الكتلة المرشحة؛ تقييم الدخول عند هذا الإغلاق فقط.",
                        )
                    )
                    if zone_id in violated_ids:
                        decisions.append(
                            _stand_aside(
                                variant,
                                candle,
                                zone,
                                "touch_violation_collision",
                                "الامتناع: اجتمع أول لمس والانتهاك في شمعة واحدة فلا يعرف ترتيبهما.",
                                ("U0048",),
                            )
                        )
                    else:
                        prediction, new_decisions, new_management, management_narration = _setup_at_first_touch(
                            variant,
                            candle,
                            zone,
                            range_observation,
                            tuple(active_pools[key] for key in sorted(active_pools)),
                        )
                        if prediction is not None:
                            predictions.append(prediction)
                        decisions.extend(new_decisions)
                        management += new_management
                        narration.extend(management_narration)
            if zone_id in violated_ids:
                del active_order_blocks[zone_id]

        for event in order_blocks[index]:
            zone = event.zone
            text = (
                "تكونت كتلة أوامر مرشحة؛ الاعتماد الكامل في الانتظار"
                if event.kind is OrderBlockEventKind.CANDIDATE_CREATED
                else "انتهكت الكتلة المرشحة عند جانبها البعيد"
            )
            narration.append(
                _narration(
                    variant,
                    candle.end,
                    f"{zone.zone_id}:{event.kind.value}:{candle.end.isoformat()}",
                    "order_block_candidate",
                    event.claim_ids,
                    f"{text}؛ الافتتاح {_price(zone.opening)} والجانب البعيد {_price(zone.far_side)}.",
                )
            )
            if event.kind is OrderBlockEventKind.CANDIDATE_CREATED:
                active_order_blocks[zone.zone_id] = _ActiveOrderBlock(zone)
                prediction = _ob_prediction(variant, zone, candle)
                predictions.append(prediction)
                decisions.extend(
                    (
                        _decision(
                            variant,
                            candle.end,
                            prediction.prediction_id + ":entry",
                            DecisionType.ENTRY_CHOICE,
                            "entry_choice",
                            _claims(zone.claim_ids, "K2C-004"),
                            "الدخول المشروط ينتظر أول عودة، لا عودة لاحقة ولا مطاردة الإزاحة.",
                            prediction.prediction_id,
                        ),
                        _decision(
                            variant,
                            candle.end,
                            prediction.prediction_id + ":stop",
                            DecisionType.STOP_CHOICE,
                            "stop_choice",
                            ("U0048",),
                            f"الإبطال الرصدي هو الجانب البعيد {_price(zone.far_side)}.",
                            prediction.prediction_id,
                        ),
                    )
                )

        for (timeframe, anchor), states in htf.items():
            for completed in states[index].newly_completed:
                narration.append(
                    _narration(
                        variant,
                        candle.end,
                        f"htf:{anchor.value}:{timeframe.value}:{completed.bucket_start.isoformat()}",
                        "higher_timeframe_close",
                        ("U0012", "U0024", "U0025", "U0052", "U0053"),
                        (
                            f"اكتملت شمعة {timeframe.value} بمرساة {anchor.value}: "
                            f"{_price(completed.bid_low)} إلى {_price(completed.bid_high)} على العرض."
                        ),
                    )
                )

        if status is MarketStatus.MARKET:
            for clock in CLOCK_VARIANTS:
                session = observe_session(candle, clock)
                if session.starts_here:
                    if clock.definition_id in {
                        ClockDefinition.LONDON_START_0100_OPEN_END,
                        ClockDefinition.LONDON_START_0200_OPEN_END,
                        ClockDefinition.EURO_0200_0500,
                    }:
                        session_claims = _claims(clock.claim_ids, "U0169", "U0170")
                    elif clock.definition_id in {
                        ClockDefinition.NEW_YORK_SESSION_NOT_KILLZONE,
                        ClockDefinition.WIDE_0830_NOT_NY_KILLZONE_OPEN_END,
                    }:
                        session_claims = _claims(clock.claim_ids, "U0185", "U0186")
                    else:
                        session_claims = clock.claim_ids
                    narration.append(
                        _narration(
                            variant,
                            candle.end,
                            f"session:{clock.definition_id.value}:{candle.start.isoformat()}",
                            "session_clock",
                            session_claims,
                            (
                                f"بدأت نافذة {clock.definition_id.value} بنيويورك؛ "
                                f"سماح تسميتها منطقة قتل: {clock.killzone_label_allowed}."
                            ),
                        )
                    )

        trace.append(
            ChartReading(
                available_at=candle.end,
                narration=tuple(narration),
                predictions=tuple(predictions),
                decisions=tuple(decisions),
                management=management,
            )
        )
    return tuple(trace)
