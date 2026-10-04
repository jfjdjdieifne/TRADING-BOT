"""Module 7.0 — Causal Multi-Timeframe ICT Confluence, Multi-Tier Liquidity Target Ladder & Dynamic Trade Lifecycle Engine.

Built strictly on top of CLOSED MUF V1 S0–S15 (`CausalMarketUnderstandingDiagnosticReport`)
and CLOSED Layers 0–6 contracts:
- Zero Lookahead (`Origin != Availability`): every structural swing, break, zone, and
  liquidity target pool is verified via `require_visible_at(fact_key=..., at_key=at_key)`.
- Zero Magic Numbers: all risk/qualification hurdles and empirical rank boundaries are
  explicit contract inputs (`TradeRiskAndQualificationContract`) or derived directly
  from causal historical distributions.
- PROXY and ACTUAL flow regimes are kept strictly separate and never merged into one number.
- Solves the "Pending Order Closed at 3R During a 10R+ Explosion" operational problem via:
  1. Multi-Tier Structural Liquidity Target Ladder (`T1` qualification hurdle, `T2` intermediate HTF, `T3+` major HTF runner);
  2. Live Dynamic Target Unlocking (`ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP`) when price reaches `T1` with strong impulse geometry;
  3. Pending-Order Multi-Leg Split Blueprint (`DynamicTargetExecutionBlueprint`) when trading via resting exchange limit orders;
  4. Post-Target Continuation Pullback Re-Entry (`ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS`) if an external limit order already closed 100% at `T1` and price broke through `T1` toward `T2`/`T3` (`10R+`).
"""

from dataclasses import dataclass
import math
from typing import Optional, Tuple

from trading_system.market_understanding.availability import (
    InformationKey,
    require_visible_at,
)
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.final_evaluation_and_reality import (
    CausalMarketUnderstandingDiagnosticReport,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)

MODULE_CAUSAL_ICT_LIFECYCLE_VERSION = "CAUSAL_ICT_LIFECYCLE_V1"

DIRECTION_LONG = "LONG"
DIRECTION_SHORT = "SHORT"
VALID_DIRECTIONS = (DIRECTION_LONG, DIRECTION_SHORT)

RANGE_ZONE_DISCOUNT = "DISCOUNT"
RANGE_ZONE_PREMIUM = "PREMIUM"
RANGE_ZONE_EQUILIBRIUM = "EQUILIBRIUM"
VALID_RANGE_ZONES = (RANGE_ZONE_DISCOUNT, RANGE_ZONE_PREMIUM, RANGE_ZONE_EQUILIBRIUM)

FLOW_REGIME_SUPPORTIVE_DISPLACEMENT = "SUPPORTIVE_DISPLACEMENT"
FLOW_REGIME_NEUTRAL = "NEUTRAL"
FLOW_REGIME_ABSORPTION_AGAINST = "ABSORPTION_AGAINST"
VALID_FLOW_REGIMES = (
    FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
    FLOW_REGIME_NEUTRAL,
    FLOW_REGIME_ABSORPTION_AGAINST,
)

EXECUTION_MODE_DYNAMIC_TARGET_UNLOCK = "DYNAMIC_TARGET_UNLOCK_MODE"
EXECUTION_MODE_PENDING_SPLIT_LADDER = "PENDING_ORDER_SPLIT_LADDER_MODE"

DECISION_ENTER_LONG = "ENTER_LONG"
DECISION_ENTER_SHORT = "ENTER_SHORT"
DECISION_CONTINUATION_REENTRY_LONG = "CONTINUATION_REENTRY_LONG"
DECISION_CONTINUATION_REENTRY_SHORT = "DECISION_CONTINUATION_REENTRY_SHORT"
DECISION_WAIT_NO_QUALIFYING_SETUP = "WAIT_NO_QUALIFYING_SETUP"

ACTION_HOLD_INITIAL_STRUCTURAL_STOP = "HOLD_INITIAL_STRUCTURAL_STOP"
ACTION_RATCHET_STOP_TO_CONFIRMED_SWING = "RATCHET_STOP_TO_CONFIRMED_SWING"
ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP = "UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP"
ACTION_TAKE_PARTIAL_AND_TRAIL_RUNNER = "TAKE_PARTIAL_AND_TRAIL_RUNNER"
ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL = "EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL"
ACTION_EXIT_FULL_AT_FINAL_TARGET = "EXIT_FULL_AT_FINAL_TARGET"
ACTION_EXIT_STOP_LOSS_HIT = "EXIT_STOP_LOSS_HIT"
ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS = (
    "EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS"
)

TRADE_RECOMMENDATION_SCHEMA = SchemaIdentity(
    "CAUSAL_ICT_TRADE_RECOMMENDATION",
    "V1",
)
TRADE_RECOMMENDATION_ARTIFACT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="CAUSAL_ICT_TRADE_RECOMMENDATION_RECORD",
    schema_identity=TRADE_RECOMMENDATION_SCHEMA,
    identity_defining_fields=(
        "at_key",
        "decision",
        "direction",
        "entry_price",
        "structural_stop_price",
        "qualifying_target_price",
        "runner_target_price",
        "expected_value_in_r",
    ),
)

TRADE_LIFECYCLE_ACTION_SCHEMA = SchemaIdentity(
    "CAUSAL_ICT_TRADE_LIFECYCLE_ACTION",
    "V1",
)
TRADE_LIFECYCLE_ACTION_ARTIFACT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="CAUSAL_ICT_TRADE_LIFECYCLE_ACTION_RECORD",
    schema_identity=TRADE_LIFECYCLE_ACTION_SCHEMA,
    identity_defining_fields=(
        "trade_id",
        "at_key",
        "action",
        "updated_stop_price",
        "active_target_price",
        "remaining_position_fraction",
    ),
)


def _require_finite_positive(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaViolation(f"{field_name} must be numeric")
    fval = float(value)
    if not math.isfinite(fval) or fval <= 0.0:
        raise SchemaViolation(f"{field_name} must be finite and > 0")
    return fval


def _require_unit_interval(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaViolation(f"{field_name} must be numeric")
    fval = float(value)
    if not math.isfinite(fval) or fval < 0.0 or fval > 1.0:
        raise SchemaViolation(f"{field_name} must be in [0.0, 1.0]")
    return fval


def require_earliest_lawful_availability(
    *,
    origin_key: InformationKey,
    available_key: InformationKey,
) -> None:
    if not isinstance(origin_key, InformationKey) or not isinstance(available_key, InformationKey):
        raise SchemaViolation("origin_key and available_key must be InformationKey instances")
    if origin_key.timeline_id != available_key.timeline_id:
        raise IllegalCausalReference("cross-timeline origin/availability reference forbidden")
    if available_key < origin_key:
        raise PrematureAvailability("available_key cannot precede origin_key")


@dataclass(frozen=True)
class TradeRiskAndQualificationContract:
    """Explicit owner-supplied risk and qualification contract (zero magic numbers)."""

    account_equity: float
    capital_risk_fraction: float
    min_qualification_rr: float
    transaction_cost_in_r: float
    impulse_expansion_min_causal_rank: float
    exhaustion_max_causal_rank: float

    def __post_init__(self) -> None:
        _require_finite_positive(self.account_equity, "account_equity")
        risk_frac = _require_unit_interval(self.capital_risk_fraction, "capital_risk_fraction")
        if risk_frac == 0.0:
            raise SchemaViolation("capital_risk_fraction must be > 0.0")
        min_rr = _require_finite_positive(self.min_qualification_rr, "min_qualification_rr")
        if min_rr < 1.0:
            raise SchemaViolation("min_qualification_rr must be >= 1.0")
        if isinstance(self.transaction_cost_in_r, bool) or not isinstance(
            self.transaction_cost_in_r, (int, float)
        ):
            raise SchemaViolation("transaction_cost_in_r must be numeric")
        if not math.isfinite(float(self.transaction_cost_in_r)) or float(self.transaction_cost_in_r) < 0.0:
            raise SchemaViolation("transaction_cost_in_r must be finite and >= 0.0")
        imp_rank = _require_unit_interval(
            self.impulse_expansion_min_causal_rank,
            "impulse_expansion_min_causal_rank",
        )
        exh_rank = _require_unit_interval(
            self.exhaustion_max_causal_rank,
            "exhaustion_max_causal_rank",
        )
        if exh_rank >= imp_rank:
            raise SchemaViolation(
                "exhaustion_max_causal_rank must be strictly less than impulse_expansion_min_causal_rank"
            )


@dataclass(frozen=True)
class StructuralLiquidityTargetPool:
    """Causal draw-on-liquidity target pool (HTF swing extreme, un-swept liquidity pool, or HTF FVG)."""

    pool_id: str
    pool_kind: str
    scale_label: str
    target_price: float
    origin_key: InformationKey
    available_key: InformationKey

    def __post_init__(self) -> None:
        if not isinstance(self.pool_id, str) or not self.pool_id.strip():
            raise SchemaViolation("pool_id must be a non-empty string")
        if not isinstance(self.pool_kind, str) or not self.pool_kind.strip():
            raise SchemaViolation("pool_kind must be a non-empty string")
        if not isinstance(self.scale_label, str) or not self.scale_label.strip():
            raise SchemaViolation("scale_label must be a non-empty string")
        _require_finite_positive(self.target_price, "target_price")
        require_earliest_lawful_availability(
            origin_key=self.origin_key,
            available_key=self.available_key,
        )


@dataclass(frozen=True)
class StructuralTargetLadder:
    """Ordered ladder of causal liquidity targets from nearest qualifying T1 (`>= min_rr`) to HTF Runner (`10R+`)."""

    direction: str
    entry_price: float
    structural_stop_price: float
    stop_distance: float
    targets_with_rr: Tuple[Tuple[StructuralLiquidityTargetPool, float], ...]

    @classmethod
    def build_causal_ladder(
        cls,
        *,
        direction: str,
        entry_price: float,
        structural_stop_price: float,
        candidate_pools: Tuple[StructuralLiquidityTargetPool, ...],
        at_key: InformationKey,
    ) -> "StructuralTargetLadder":
        if direction not in VALID_DIRECTIONS:
            raise SchemaViolation(f"direction must be one of {VALID_DIRECTIONS}")
        _require_finite_positive(entry_price, "entry_price")
        _require_finite_positive(structural_stop_price, "structural_stop_price")

        if direction == DIRECTION_LONG:
            if structural_stop_price >= entry_price:
                raise SchemaViolation("LONG structural_stop_price must be strictly below entry_price")
            stop_distance = entry_price - structural_stop_price
        else:
            if structural_stop_price <= entry_price:
                raise SchemaViolation("SHORT structural_stop_price must be strictly above entry_price")
            stop_distance = structural_stop_price - entry_price

        valid_pairs = []
        for pool in candidate_pools:
            require_visible_at(fact_key=pool.available_key, at_key=at_key)
            if direction == DIRECTION_LONG and pool.target_price > entry_price:
                rr = (pool.target_price - entry_price) / stop_distance
                valid_pairs.append((pool, rr))
            elif direction == DIRECTION_SHORT and pool.target_price < entry_price:
                rr = (entry_price - pool.target_price) / stop_distance
                valid_pairs.append((pool, rr))

        valid_pairs.sort(key=lambda item: (item[1], item[0].pool_id))
        return cls(
            direction=direction,
            entry_price=entry_price,
            structural_stop_price=structural_stop_price,
            stop_distance=stop_distance,
            targets_with_rr=tuple(valid_pairs),
        )


@dataclass(frozen=True)
class CausalICTConfluenceObservation:
    """Multi-timeframe causal ICT state observation at `at_key`."""

    at_key: InformationKey
    htf_parent_direction: str
    htf_dealing_range_zone: str
    htf_poi_mitigated: bool
    htf_poi_kind: str
    htf_poi_origin_key: InformationKey
    htf_poi_available_key: InformationKey
    ltf_break_confirmed: bool
    ltf_break_kind: str
    ltf_break_direction: str
    ltf_break_origin_key: InformationKey
    ltf_break_available_key: InformationKey
    ltf_invalidation_swing_price: float
    ltf_invalidation_origin_key: InformationKey
    ltf_invalidation_available_key: InformationKey
    child_wave_efficiency_rank: float
    child_wave_velocity_rank: float
    proxy_flow_regime: str
    actual_flow_regime: str | TypedState

    def __post_init__(self) -> None:
        if self.htf_parent_direction not in VALID_DIRECTIONS:
            raise SchemaViolation("Invalid htf_parent_direction")
        if self.htf_dealing_range_zone not in VALID_RANGE_ZONES:
            raise SchemaViolation("Invalid htf_dealing_range_zone")
        if self.ltf_break_direction not in VALID_DIRECTIONS:
            raise SchemaViolation("Invalid ltf_break_direction")
        if self.proxy_flow_regime not in VALID_FLOW_REGIMES:
            raise SchemaViolation("Invalid proxy_flow_regime")
        if not isinstance(self.actual_flow_regime, TypedState):
            if self.actual_flow_regime not in VALID_FLOW_REGIMES:
                raise SchemaViolation("actual_flow_regime must be a valid flow regime or TypedState")

        _require_finite_positive(self.ltf_invalidation_swing_price, "ltf_invalidation_swing_price")
        _require_unit_interval(self.child_wave_efficiency_rank, "child_wave_efficiency_rank")
        _require_unit_interval(self.child_wave_velocity_rank, "child_wave_velocity_rank")

        require_earliest_lawful_availability(
            origin_key=self.htf_poi_origin_key,
            available_key=self.htf_poi_available_key,
        )
        require_earliest_lawful_availability(
            origin_key=self.ltf_break_origin_key,
            available_key=self.ltf_break_available_key,
        )
        require_earliest_lawful_availability(
            origin_key=self.ltf_invalidation_origin_key,
            available_key=self.ltf_invalidation_available_key,
        )
        require_visible_at(fact_key=self.htf_poi_available_key, at_key=self.at_key)
        require_visible_at(fact_key=self.ltf_break_available_key, at_key=self.at_key)
        require_visible_at(fact_key=self.ltf_invalidation_available_key, at_key=self.at_key)


@dataclass(frozen=True)
class PendingOrderSplitLeg:
    """Single leg of a multi-tier pending order blueprint for traders using resting limit orders."""

    leg_index: int
    pool_id: str
    target_price: float
    rr_multiple: float
    position_fraction: float
    position_units: float
    role_description: str


@dataclass(frozen=True)
class DynamicTargetExecutionBlueprint:
    """Dual-mode execution plan preventing premature 100% exit at T1 (3R) during 10R+ impulse waves."""

    qualifying_target_pool: StructuralLiquidityTargetPool
    qualifying_rr_multiple: float
    runner_target_pool: StructuralLiquidityTargetPool
    runner_rr_multiple: float
    live_resting_exchange_tp_price: float
    live_t1_checkpoint_price: float
    pending_order_split_legs: Tuple[PendingOrderSplitLeg, ...]


@dataclass(frozen=True)
class CausalTradeRecommendationRecord:
    """Complete, auditable trade recommendation output with structural stop, 1% sizing, and 3R->10R+ blueprint."""

    recommendation_id: str
    at_key: InformationKey
    decision: str
    direction: str | TypedState
    entry_price: float
    structural_stop_price: float | TypedState
    stop_distance: float | TypedState
    risk_capital_amount: float
    position_units: float
    qualifying_target_price: float | TypedState
    qualifying_rr_multiple: float | TypedState
    runner_target_price: float | TypedState
    runner_rr_multiple: float | TypedState
    shrunk_continuation_probability: float
    shrunk_reversal_probability: float
    right_censored_fraction: float
    effective_sample_mass: float
    expected_value_in_r: float
    execution_blueprint: Optional[DynamicTargetExecutionBlueprint]
    proxy_flow_regime: str
    actual_flow_regime: str | TypedState
    reason_codes: Tuple[str, ...]
    provenance_muf_report_id: str


def _compute_shrunk_competing_risk_probabilities(
    muf_report: CausalMarketUnderstandingDiagnosticReport,
) -> Tuple[float, float, float, float]:
    """Derive dependency-weighted continuation and reversal probabilities with Laplace shrinkage."""
    eff_mass = float(muf_report.non_overlapping_span_cluster_count)
    total_vis = float(muf_report.visible_episode_count)
    right_cens = float(muf_report.historical_right_censored_count)
    cens_frac = (right_cens / total_vis) if total_vis > 0.0 else 0.0

    emp_rate = muf_report.empirical_continuation_rate
    if isinstance(emp_rate, TypedState) or eff_mass <= 0.0:
        return (0.5, 0.5, cens_frac, eff_mass)

    raw_cont_rate = float(emp_rate.value)
    eff_cont = eff_mass * raw_cont_rate
    eff_rev = eff_mass * (1.0 - raw_cont_rate)
    p_cont_shrunk = (eff_cont + 1.0) / (eff_cont + eff_rev + 2.0)
    p_rev_shrunk = 1.0 - p_cont_shrunk
    return (p_cont_shrunk, p_rev_shrunk, cens_frac, eff_mass)


def _build_execution_blueprint(
    *,
    qualifying_targets: Tuple[Tuple[StructuralLiquidityTargetPool, float], ...],
    total_position_units: float,
) -> DynamicTargetExecutionBlueprint:
    t1_pool, t1_rr = qualifying_targets[0]
    runner_pool, runner_rr = qualifying_targets[-1]

    if len(qualifying_targets) == 1:
        legs = (
            PendingOrderSplitLeg(
                leg_index=1,
                pool_id=t1_pool.pool_id,
                target_price=t1_pool.target_price,
                rr_multiple=t1_rr,
                position_fraction=1.0,
                position_units=total_position_units,
                role_description="SINGLE_QUALIFYING_STRUCTURAL_TARGET",
            ),
        )
    elif len(qualifying_targets) == 2:
        f1 = 1.0 / (1.0 + t1_rr)
        f2 = 1.0 - f1
        legs = (
            PendingOrderSplitLeg(
                leg_index=1,
                pool_id=t1_pool.pool_id,
                target_price=t1_pool.target_price,
                rr_multiple=t1_rr,
                position_fraction=f1,
                position_units=total_position_units * f1,
                role_description="T1_DERISK_LOCK_1R_SLICE",
            ),
            PendingOrderSplitLeg(
                leg_index=2,
                pool_id=runner_pool.pool_id,
                target_price=runner_pool.target_price,
                rr_multiple=runner_rr,
                position_fraction=f2,
                position_units=total_position_units * f2,
                role_description="T2_HTF_RUNNER_CORE_SLICE",
            ),
        )
    else:
        t2_pool, t2_rr = qualifying_targets[1]
        f1 = 1.0 / (1.0 + t1_rr)
        remaining = 1.0 - f1
        f2 = remaining * (t2_rr / (t2_rr + runner_rr))
        f3 = 1.0 - f1 - f2
        legs = (
            PendingOrderSplitLeg(
                leg_index=1,
                pool_id=t1_pool.pool_id,
                target_price=t1_pool.target_price,
                rr_multiple=t1_rr,
                position_fraction=f1,
                position_units=total_position_units * f1,
                role_description="T1_DERISK_LOCK_1R_SLICE",
            ),
            PendingOrderSplitLeg(
                leg_index=2,
                pool_id=t2_pool.pool_id,
                target_price=t2_pool.target_price,
                rr_multiple=t2_rr,
                position_fraction=f2,
                position_units=total_position_units * f2,
                role_description="T2_INTERMEDIATE_HTF_STRUCTURE_SLICE",
            ),
            PendingOrderSplitLeg(
                leg_index=3,
                pool_id=runner_pool.pool_id,
                target_price=runner_pool.target_price,
                rr_multiple=runner_rr,
                position_fraction=f3,
                position_units=total_position_units * f3,
                role_description="T3_MAJOR_HTF_UNCAPPED_RUNNER_SLICE",
            ),
        )

    return DynamicTargetExecutionBlueprint(
        qualifying_target_pool=t1_pool,
        qualifying_rr_multiple=t1_rr,
        runner_target_pool=runner_pool,
        runner_rr_multiple=runner_rr,
        live_resting_exchange_tp_price=runner_pool.target_price,
        live_t1_checkpoint_price=t1_pool.target_price,
        pending_order_split_legs=legs,
    )


def evaluate_causal_ict_recommendation_as_of(
    *,
    muf_report: CausalMarketUnderstandingDiagnosticReport,
    confluence: CausalICTConfluenceObservation,
    candidate_liquidity_pools: Tuple[StructuralLiquidityTargetPool, ...],
    entry_price: float,
    risk_contract: TradeRiskAndQualificationContract,
    is_post_t1_continuation_reentry: bool = False,
) -> CausalTradeRecommendationRecord:
    """Evaluate multi-timeframe ICT confluence, structural stop, 1% sizing, and 3R->10R+ target ladder as of `at_key`."""
    if muf_report.query_key != confluence.at_key:
        raise IllegalCausalReference(
            "muf_report.query_key and confluence.at_key must match exactly"
        )
    at_key = muf_report.query_key
    muf_report_id = muf_report.explanation_record.explanation_hash
    _require_finite_positive(entry_price, "entry_price")

    p_cont, p_rev, cens_frac, eff_mass = _compute_shrunk_competing_risk_probabilities(
        muf_report
    )
    risk_capital = risk_contract.account_equity * risk_contract.capital_risk_fraction

    reasons = []
    direction = confluence.htf_parent_direction

    if direction == DIRECTION_LONG and confluence.htf_dealing_range_zone != RANGE_ZONE_DISCOUNT:
        reasons.append("HTF_ZONE_NOT_DISCOUNT_FOR_LONG")
    if direction == DIRECTION_SHORT and confluence.htf_dealing_range_zone != RANGE_ZONE_PREMIUM:
        reasons.append("HTF_ZONE_NOT_PREMIUM_FOR_SHORT")
    if not confluence.htf_poi_mitigated:
        reasons.append("HTF_POI_NOT_MITIGATED")
    if not confluence.ltf_break_confirmed:
        reasons.append("LTF_STRUCTURAL_BREAK_NOT_CONFIRMED")
    if confluence.ltf_break_direction != direction:
        reasons.append("LTF_BREAK_DIRECTION_MISMATCHES_HTF_PARENT")

    if confluence.proxy_flow_regime == FLOW_REGIME_ABSORPTION_AGAINST:
        reasons.append("PROXY_FLOW_ABSORPTION_AGAINST_DIRECTION")
    if confluence.actual_flow_regime == FLOW_REGIME_ABSORPTION_AGAINST:
        reasons.append("ACTUAL_FLOW_ABSORPTION_AGAINST_DIRECTION")

    if confluence.child_wave_efficiency_rank <= risk_contract.exhaustion_max_causal_rank:
        reasons.append("CHILD_WAVE_EFFICIENCY_EXHAUSTED")

    stop_price = confluence.ltf_invalidation_swing_price
    if (direction == DIRECTION_LONG and stop_price >= entry_price) or (
        direction == DIRECTION_SHORT and stop_price <= entry_price
    ):
        reasons.append("INVALID_STRUCTURAL_STOP_GEOMETRY")
        return _build_wait_record(
            at_key=at_key,
            entry_price=entry_price,
            risk_capital=risk_capital,
            p_cont=p_cont,
            p_rev=p_rev,
            cens_frac=cens_frac,
            eff_mass=eff_mass,
            confluence=confluence,
            muf_report_id=muf_report_id,
            reasons=tuple(reasons),
        )

    ladder = StructuralTargetLadder.build_causal_ladder(
        direction=direction,
        entry_price=entry_price,
        structural_stop_price=stop_price,
        candidate_pools=candidate_liquidity_pools,
        at_key=at_key,
    )
    qualifying_targets = tuple(
        (pool, rr)
        for pool, rr in ladder.targets_with_rr
        if rr >= risk_contract.min_qualification_rr
    )
    if not qualifying_targets:
        reasons.append("NO_STRUCTURAL_LIQUIDITY_TARGET_MEETS_MIN_RR")
        return _build_wait_record(
            at_key=at_key,
            entry_price=entry_price,
            risk_capital=risk_capital,
            p_cont=p_cont,
            p_rev=p_rev,
            cens_frac=cens_frac,
            eff_mass=eff_mass,
            confluence=confluence,
            muf_report_id=muf_report_id,
            reasons=tuple(reasons),
        )

    t1_pool, t1_rr = qualifying_targets[0]
    runner_pool, runner_rr = qualifying_targets[-1]

    ev_in_r = (p_cont * t1_rr) - (p_rev * 1.0) - risk_contract.transaction_cost_in_r
    if ev_in_r <= 0.0:
        reasons.append("NON_POSITIVE_COMPETING_RISK_EXPECTED_VALUE")

    if reasons:
        return _build_wait_record(
            at_key=at_key,
            entry_price=entry_price,
            risk_capital=risk_capital,
            p_cont=p_cont,
            p_rev=p_rev,
            cens_frac=cens_frac,
            eff_mass=eff_mass,
            confluence=confluence,
            muf_report_id=muf_report_id,
            reasons=tuple(reasons),
        )

    position_units = risk_capital / ladder.stop_distance
    blueprint = _build_execution_blueprint(
        qualifying_targets=qualifying_targets,
        total_position_units=position_units,
    )

    if is_post_t1_continuation_reentry:
        decision = (
            DECISION_CONTINUATION_REENTRY_LONG
            if direction == DIRECTION_LONG
            else DECISION_CONTINUATION_REENTRY_SHORT
        )
        ok_reasons = (
            "HTF_LTF_CONFLUENCE_CONFIRMED",
            "POST_T1_CONTINUATION_PULLBACK_QUALIFIED",
            "DYNAMIC_RUNNER_LADDER_UNLOCKED",
        )
    else:
        decision = DECISION_ENTER_LONG if direction == DIRECTION_LONG else DECISION_ENTER_SHORT
        ok_reasons = (
            "HTF_LTF_CONFLUENCE_CONFIRMED",
            "STRUCTURAL_STOP_AND_MIN_RR_QUALIFIED",
            "POSITIVE_COMPETING_RISK_EV_CONFIRMED",
        )

    rec_id = canonical_artifact_identity(
        TRADE_RECOMMENDATION_ARTIFACT_SCHEMA,
        identity_payload={
            "at_key": at_key,
            "decision": decision,
            "direction": direction,
            "entry_price": f"{entry_price:.8f}",
            "structural_stop_price": f"{stop_price:.8f}",
            "qualifying_target_price": f"{t1_pool.target_price:.8f}",
            "runner_target_price": f"{runner_pool.target_price:.8f}",
            "expected_value_in_r": f"{ev_in_r:.8f}",
        },
    )

    return CausalTradeRecommendationRecord(
        recommendation_id=rec_id,
        at_key=at_key,
        decision=decision,
        direction=direction,
        entry_price=entry_price,
        structural_stop_price=stop_price,
        stop_distance=ladder.stop_distance,
        risk_capital_amount=risk_capital,
        position_units=position_units,
        qualifying_target_price=t1_pool.target_price,
        qualifying_rr_multiple=t1_rr,
        runner_target_price=runner_pool.target_price,
        runner_rr_multiple=runner_rr,
        shrunk_continuation_probability=p_cont,
        shrunk_reversal_probability=p_rev,
        right_censored_fraction=cens_frac,
        effective_sample_mass=eff_mass,
        expected_value_in_r=ev_in_r,
        execution_blueprint=blueprint,
        proxy_flow_regime=confluence.proxy_flow_regime,
        actual_flow_regime=confluence.actual_flow_regime,
        reason_codes=ok_reasons,
        provenance_muf_report_id=muf_report_id,
    )


def _build_wait_record(
    *,
    at_key: InformationKey,
    entry_price: float,
    risk_capital: float,
    p_cont: float,
    p_rev: float,
    cens_frac: float,
    eff_mass: float,
    confluence: CausalICTConfluenceObservation,
    muf_report_id: str,
    reasons: Tuple[str, ...],
) -> CausalTradeRecommendationRecord:
    rec_id = canonical_artifact_identity(
        TRADE_RECOMMENDATION_ARTIFACT_SCHEMA,
        identity_payload={
            "at_key": at_key,
            "decision": DECISION_WAIT_NO_QUALIFYING_SETUP,
            "direction": TypedState.NOT_APPLICABLE,
            "entry_price": f"{entry_price:.8f}",
            "structural_stop_price": TypedState.NOT_APPLICABLE,
            "qualifying_target_price": TypedState.NOT_APPLICABLE,
            "runner_target_price": TypedState.NOT_APPLICABLE,
            "expected_value_in_r": "0.00000000",
        },
    )
    return CausalTradeRecommendationRecord(
        recommendation_id=rec_id,
        at_key=at_key,
        decision=DECISION_WAIT_NO_QUALIFYING_SETUP,
        direction=TypedState.NOT_APPLICABLE,
        entry_price=entry_price,
        structural_stop_price=TypedState.NOT_APPLICABLE,
        stop_distance=TypedState.NOT_APPLICABLE,
        risk_capital_amount=risk_capital,
        position_units=0.0,
        qualifying_target_price=TypedState.NOT_APPLICABLE,
        qualifying_rr_multiple=TypedState.NOT_APPLICABLE,
        runner_target_price=TypedState.NOT_APPLICABLE,
        runner_rr_multiple=TypedState.NOT_APPLICABLE,
        shrunk_continuation_probability=p_cont,
        shrunk_reversal_probability=p_rev,
        right_censored_fraction=cens_frac,
        effective_sample_mass=eff_mass,
        expected_value_in_r=0.0,
        execution_blueprint=None,
        proxy_flow_regime=confluence.proxy_flow_regime,
        actual_flow_regime=confluence.actual_flow_regime,
        reason_codes=reasons,
        provenance_muf_report_id=muf_report_id,
    )


@dataclass(frozen=True)
class ConfirmedStructuralTrailSwing:
    """Causally confirmed sub-wave swing floor (for LONG) or ceiling (for SHORT) eligible for stop ratcheting."""

    swing_id: str
    swing_price: float
    origin_key: InformationKey
    available_key: InformationKey
    followed_by_bos_in_direction: bool

    def __post_init__(self) -> None:
        if not isinstance(self.swing_id, str) or not self.swing_id.strip():
            raise SchemaViolation("swing_id must be a non-empty string")
        _require_finite_positive(self.swing_price, "swing_price")
        require_earliest_lawful_availability(
            origin_key=self.origin_key,
            available_key=self.available_key,
        )


@dataclass(frozen=True)
class ContinuationPullbackSetup:
    """Causal continuation pullback above T1 (for LONG) or below T1 (for SHORT) when external limit order closed at T1."""

    pullback_poi_kind: str
    pullback_entry_price: float
    pullback_invalidation_stop_price: float
    origin_key: InformationKey
    available_key: InformationKey
    ltf_continuation_break_confirmed: bool

    def __post_init__(self) -> None:
        _require_finite_positive(self.pullback_entry_price, "pullback_entry_price")
        _require_finite_positive(
            self.pullback_invalidation_stop_price,
            "pullback_invalidation_stop_price",
        )
        require_earliest_lawful_availability(
            origin_key=self.origin_key,
            available_key=self.available_key,
        )


@dataclass(frozen=True)
class OpenTradeLifecycleState:
    """Immutable state of an active or T1-externally-closed trade across bars."""

    trade_id: str
    direction: str
    entry_price: float
    initial_stop_price: float
    current_stop_price: float
    stop_distance: float
    remaining_position_fraction: float
    realized_r_banked: float
    active_target_index: int
    target_ladder: Tuple[Tuple[StructuralLiquidityTargetPool, float], ...]
    external_limit_closed_at_t1: bool = False

    def __post_init__(self) -> None:
        if self.direction not in VALID_DIRECTIONS:
            raise SchemaViolation("Invalid trade direction")
        _require_finite_positive(self.entry_price, "entry_price")
        _require_finite_positive(self.initial_stop_price, "initial_stop_price")
        _require_finite_positive(self.current_stop_price, "current_stop_price")
        _require_finite_positive(self.stop_distance, "stop_distance")
        _require_unit_interval(self.remaining_position_fraction, "remaining_position_fraction")
        if not self.target_ladder:
            raise SchemaViolation("target_ladder must be non-empty")
        if self.active_target_index < 0 or self.active_target_index >= len(self.target_ladder):
            raise SchemaViolation("active_target_index out of bounds")


@dataclass(frozen=True)
class TradeLifecycleActionRecord:
    """Bar-by-bar lifecycle decision and updated trade state produced in O(1) time."""

    action_id: str
    trade_id: str
    at_key: InformationKey
    action: str
    updated_state: OpenTradeLifecycleState
    updated_stop_price: float
    active_target_price: float
    active_target_rr: float
    remaining_position_fraction: float
    realized_r_increment: float
    cumulative_locked_r: float
    continuation_reentry_recommendation: Optional[CausalTradeRecommendationRecord]
    reason_code: str


def _compute_locked_r(
    direction: str,
    entry_price: float,
    stop_price: float,
    stop_distance: float,
    remaining_fraction: float,
    realized_r_banked: float,
) -> float:
    if direction == DIRECTION_LONG:
        open_locked_r = ((stop_price - entry_price) / stop_distance) * remaining_fraction
    else:
        open_locked_r = ((entry_price - stop_price) / stop_distance) * remaining_fraction
    return realized_r_banked + open_locked_r


def evaluate_open_trade_lifecycle_as_of(
    *,
    state: OpenTradeLifecycleState,
    at_key: InformationKey,
    bar_low: float,
    bar_high: float,
    bar_close: float,
    current_wave_efficiency_rank: float,
    current_wave_velocity_rank: float,
    opposing_ltf_choch_confirmed: bool,
    proxy_flow_regime: str,
    actual_flow_regime: str | TypedState,
    confirmed_trail_swings: Tuple[ConfirmedStructuralTrailSwing, ...],
    risk_contract: TradeRiskAndQualificationContract,
    muf_report: Optional[CausalMarketUnderstandingDiagnosticReport] = None,
    continuation_pullback: Optional[ContinuationPullbackSetup] = None,
) -> TradeLifecycleActionRecord:
    """Evaluate open trade lifecycle at `at_key` in O(1) per bar."""
    _require_finite_positive(bar_low, "bar_low")
    _require_finite_positive(bar_high, "bar_high")
    _require_finite_positive(bar_close, "bar_close")
    if bar_low > bar_high:
        raise SchemaViolation("bar_low cannot exceed bar_high")
    _require_unit_interval(current_wave_efficiency_rank, "current_wave_efficiency_rank")
    _require_unit_interval(current_wave_velocity_rank, "current_wave_velocity_rank")

    for swing in confirmed_trail_swings:
        require_visible_at(fact_key=swing.available_key, at_key=at_key)

    direction = state.direction
    active_pool, active_rr = state.target_ladder[state.active_target_index]

    if state.external_limit_closed_at_t1 and state.remaining_position_fraction == 0.0:
        if (
            continuation_pullback is not None
            and continuation_pullback.ltf_continuation_break_confirmed
            and muf_report is not None
        ):
            require_visible_at(
                fact_key=continuation_pullback.available_key,
                at_key=at_key,
            )
            higher_pools = tuple(
                pool
                for pool, _ in state.target_ladder[state.active_target_index :]
            )
            synth_confluence = CausalICTConfluenceObservation(
                at_key=at_key,
                htf_parent_direction=direction,
                htf_dealing_range_zone=(
                    RANGE_ZONE_DISCOUNT if direction == DIRECTION_LONG else RANGE_ZONE_PREMIUM
                ),
                htf_poi_mitigated=True,
                htf_poi_kind=continuation_pullback.pullback_poi_kind,
                htf_poi_origin_key=continuation_pullback.origin_key,
                htf_poi_available_key=continuation_pullback.available_key,
                ltf_break_confirmed=True,
                ltf_break_kind="CONTINUATION_BOS",
                ltf_break_direction=direction,
                ltf_break_origin_key=continuation_pullback.origin_key,
                ltf_break_available_key=continuation_pullback.available_key,
                ltf_invalidation_swing_price=continuation_pullback.pullback_invalidation_stop_price,
                ltf_invalidation_origin_key=continuation_pullback.origin_key,
                ltf_invalidation_available_key=continuation_pullback.available_key,
                child_wave_efficiency_rank=current_wave_efficiency_rank,
                child_wave_velocity_rank=current_wave_velocity_rank,
                proxy_flow_regime=proxy_flow_regime,
                actual_flow_regime=actual_flow_regime,
            )
            reentry_rec = evaluate_causal_ict_recommendation_as_of(
                muf_report=muf_report,
                confluence=synth_confluence,
                candidate_liquidity_pools=higher_pools,
                entry_price=continuation_pullback.pullback_entry_price,
                risk_contract=risk_contract,
                is_post_t1_continuation_reentry=True,
            )
            if reentry_rec.decision in (
                DECISION_CONTINUATION_REENTRY_LONG,
                DECISION_CONTINUATION_REENTRY_SHORT,
            ):
                return _finalize_lifecycle_action(
                    state=state,
                    at_key=at_key,
                    action=ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS,
                    updated_state=state,
                    realized_r_increment=0.0,
                    reentry_rec=reentry_rec,
                    reason_code="EXTERNAL_T1_CLOSED_CONTINUATION_PULLBACK_REENTRY_ISSUED",
                )

    stop_hit = (
        bar_low <= state.current_stop_price
        if direction == DIRECTION_LONG
        else bar_high >= state.current_stop_price
    )
    if stop_hit and state.remaining_position_fraction > 0.0:
        if direction == DIRECTION_LONG:
            stop_r = (state.current_stop_price - state.entry_price) / state.stop_distance
        else:
            stop_r = (state.entry_price - state.current_stop_price) / state.stop_distance
        r_increment = stop_r * state.remaining_position_fraction
        closed_state = OpenTradeLifecycleState(
            trade_id=state.trade_id,
            direction=direction,
            entry_price=state.entry_price,
            initial_stop_price=state.initial_stop_price,
            current_stop_price=state.current_stop_price,
            stop_distance=state.stop_distance,
            remaining_position_fraction=0.0,
            realized_r_banked=state.realized_r_banked + r_increment,
            active_target_index=state.active_target_index,
            target_ladder=state.target_ladder,
            external_limit_closed_at_t1=state.external_limit_closed_at_t1,
        )
        return _finalize_lifecycle_action(
            state=state,
            at_key=at_key,
            action=ACTION_EXIT_STOP_LOSS_HIT,
            updated_state=closed_state,
            realized_r_increment=r_increment,
            reentry_rec=None,
            reason_code="STRUCTURAL_STOP_LOSS_TRIGGERED",
        )

    best_stop = state.current_stop_price
    for swing in confirmed_trail_swings:
        if not swing.followed_by_bos_in_direction:
            continue
        if direction == DIRECTION_LONG and swing.swing_price > best_stop and swing.swing_price < bar_low:
            best_stop = swing.swing_price
        elif direction == DIRECTION_SHORT and swing.swing_price < best_stop and swing.swing_price > bar_high:
            best_stop = swing.swing_price

    target_reached = (
        bar_high >= active_pool.target_price
        if direction == DIRECTION_LONG
        else bar_low <= active_pool.target_price
    )
    has_higher_target = state.active_target_index + 1 < len(state.target_ladder)
    flow_against = (
        proxy_flow_regime == FLOW_REGIME_ABSORPTION_AGAINST
        or actual_flow_regime == FLOW_REGIME_ABSORPTION_AGAINST
    )
    is_impulse_expansion = (
        current_wave_efficiency_rank >= risk_contract.impulse_expansion_min_causal_rank
        and current_wave_velocity_rank >= risk_contract.impulse_expansion_min_causal_rank
        and not opposing_ltf_choch_confirmed
        and not flow_against
    )
    is_exhausted = (
        opposing_ltf_choch_confirmed
        or flow_against
        or current_wave_efficiency_rank <= risk_contract.exhaustion_max_causal_rank
    )

    if target_reached and state.remaining_position_fraction > 0.0:
        if not has_higher_target:
            r_increment = active_rr * state.remaining_position_fraction
            final_state = OpenTradeLifecycleState(
                trade_id=state.trade_id,
                direction=direction,
                entry_price=state.entry_price,
                initial_stop_price=state.initial_stop_price,
                current_stop_price=best_stop,
                stop_distance=state.stop_distance,
                remaining_position_fraction=0.0,
                realized_r_banked=state.realized_r_banked + r_increment,
                active_target_index=state.active_target_index,
                target_ladder=state.target_ladder,
                external_limit_closed_at_t1=state.external_limit_closed_at_t1,
            )
            return _finalize_lifecycle_action(
                state=state,
                at_key=at_key,
                action=ACTION_EXIT_FULL_AT_FINAL_TARGET,
                updated_state=final_state,
                realized_r_increment=r_increment,
                reentry_rec=None,
                reason_code="FINAL_HTF_RUNNER_TARGET_REACHED",
            )

        if is_exhausted:
            r_increment = active_rr * state.remaining_position_fraction
            exited_state = OpenTradeLifecycleState(
                trade_id=state.trade_id,
                direction=direction,
                entry_price=state.entry_price,
                initial_stop_price=state.initial_stop_price,
                current_stop_price=best_stop,
                stop_distance=state.stop_distance,
                remaining_position_fraction=0.0,
                realized_r_banked=state.realized_r_banked + r_increment,
                active_target_index=state.active_target_index,
                target_ladder=state.target_ladder,
                external_limit_closed_at_t1=state.external_limit_closed_at_t1,
            )
            return _finalize_lifecycle_action(
                state=state,
                at_key=at_key,
                action=ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL,
                updated_state=exited_state,
                realized_r_increment=r_increment,
                reentry_rec=None,
                reason_code="TARGET_REACHED_WITH_WAVE_EXHAUSTION_OR_REVERSAL",
            )

        if is_impulse_expansion:
            ratcheted_stop = best_stop
            if direction == DIRECTION_LONG and ratcheted_stop < state.entry_price:
                ratcheted_stop = state.entry_price
            elif direction == DIRECTION_SHORT and ratcheted_stop > state.entry_price:
                ratcheted_stop = state.entry_price

            unlocked_state = OpenTradeLifecycleState(
                trade_id=state.trade_id,
                direction=direction,
                entry_price=state.entry_price,
                initial_stop_price=state.initial_stop_price,
                current_stop_price=ratcheted_stop,
                stop_distance=state.stop_distance,
                remaining_position_fraction=state.remaining_position_fraction,
                realized_r_banked=state.realized_r_banked,
                active_target_index=state.active_target_index + 1,
                target_ladder=state.target_ladder,
                external_limit_closed_at_t1=state.external_limit_closed_at_t1,
            )
            return _finalize_lifecycle_action(
                state=state,
                at_key=at_key,
                action=ACTION_UNLOCK_HIGHER_TARGET_AND_RATCHET_STOP,
                updated_state=unlocked_state,
                realized_r_increment=0.0,
                reentry_rec=None,
                reason_code="IMPULSE_EXPANSION_UNLOCKED_NEXT_HTF_LIQUIDITY_TARGET",
            )

        derisk_slice = state.remaining_position_fraction * (1.0 / (1.0 + active_rr))
        new_remaining = state.remaining_position_fraction - derisk_slice
        r_increment = active_rr * derisk_slice
        ratcheted_stop = best_stop
        if direction == DIRECTION_LONG and ratcheted_stop < state.entry_price:
            ratcheted_stop = state.entry_price
        elif direction == DIRECTION_SHORT and ratcheted_stop > state.entry_price:
            ratcheted_stop = state.entry_price

        partial_state = OpenTradeLifecycleState(
            trade_id=state.trade_id,
            direction=direction,
            entry_price=state.entry_price,
            initial_stop_price=state.initial_stop_price,
            current_stop_price=ratcheted_stop,
            stop_distance=state.stop_distance,
            remaining_position_fraction=new_remaining,
            realized_r_banked=state.realized_r_banked + r_increment,
            active_target_index=state.active_target_index + 1,
            target_ladder=state.target_ladder,
            external_limit_closed_at_t1=state.external_limit_closed_at_t1,
        )
        return _finalize_lifecycle_action(
            state=state,
            at_key=at_key,
            action=ACTION_TAKE_PARTIAL_AND_TRAIL_RUNNER,
            updated_state=partial_state,
            realized_r_increment=r_increment,
            reentry_rec=None,
            reason_code="MODERATE_WAVE_PARTIAL_DERISK_AND_HTF_RUNNER_TRAIL",
        )

    if opposing_ltf_choch_confirmed and state.remaining_position_fraction > 0.0:
        if direction == DIRECTION_LONG:
            close_r = (bar_close - state.entry_price) / state.stop_distance
        else:
            close_r = (state.entry_price - bar_close) / state.stop_distance
        r_increment = close_r * state.remaining_position_fraction
        rev_state = OpenTradeLifecycleState(
            trade_id=state.trade_id,
            direction=direction,
            entry_price=state.entry_price,
            initial_stop_price=state.initial_stop_price,
            current_stop_price=best_stop,
            stop_distance=state.stop_distance,
            remaining_position_fraction=0.0,
            realized_r_banked=state.realized_r_banked + r_increment,
            active_target_index=state.active_target_index,
            target_ladder=state.target_ladder,
            external_limit_closed_at_t1=state.external_limit_closed_at_t1,
        )
        return _finalize_lifecycle_action(
            state=state,
            at_key=at_key,
            action=ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL,
            updated_state=rev_state,
            realized_r_increment=r_increment,
            reentry_rec=None,
            reason_code="OPPOSING_LTF_CHOCH_CONFIRMED_MID_FLIGHT",
        )

    if best_stop != state.current_stop_price:
        ratcheted_state = OpenTradeLifecycleState(
            trade_id=state.trade_id,
            direction=direction,
            entry_price=state.entry_price,
            initial_stop_price=state.initial_stop_price,
            current_stop_price=best_stop,
            stop_distance=state.stop_distance,
            remaining_position_fraction=state.remaining_position_fraction,
            realized_r_banked=state.realized_r_banked,
            active_target_index=state.active_target_index,
            target_ladder=state.target_ladder,
            external_limit_closed_at_t1=state.external_limit_closed_at_t1,
        )
        return _finalize_lifecycle_action(
            state=state,
            at_key=at_key,
            action=ACTION_RATCHET_STOP_TO_CONFIRMED_SWING,
            updated_state=ratcheted_state,
            realized_r_increment=0.0,
            reentry_rec=None,
            reason_code="CONFIRMED_SUBWAVE_SWING_BOS_RATCHETED_STOP",
        )

    return _finalize_lifecycle_action(
        state=state,
        at_key=at_key,
        action=ACTION_HOLD_INITIAL_STRUCTURAL_STOP,
        updated_state=state,
        realized_r_increment=0.0,
        reentry_rec=None,
        reason_code="WAVE_FORMING_HOLD_STRUCTURAL_STOP_WITHOUT_PREMATURE_MOVE",
    )


def _finalize_lifecycle_action(
    *,
    state: OpenTradeLifecycleState,
    at_key: InformationKey,
    action: str,
    updated_state: OpenTradeLifecycleState,
    realized_r_increment: float,
    reentry_rec: Optional[CausalTradeRecommendationRecord],
    reason_code: str,
) -> TradeLifecycleActionRecord:
    active_pool, active_rr = updated_state.target_ladder[updated_state.active_target_index]
    locked_r = _compute_locked_r(
        direction=updated_state.direction,
        entry_price=updated_state.entry_price,
        stop_price=updated_state.current_stop_price,
        stop_distance=updated_state.stop_distance,
        remaining_fraction=updated_state.remaining_position_fraction,
        realized_r_banked=updated_state.realized_r_banked,
    )
    action_id = canonical_artifact_identity(
        TRADE_LIFECYCLE_ACTION_ARTIFACT_SCHEMA,
        identity_payload={
            "trade_id": state.trade_id,
            "at_key": at_key,
            "action": action,
            "updated_stop_price": f"{updated_state.current_stop_price:.8f}",
            "active_target_price": f"{active_pool.target_price:.8f}",
            "remaining_position_fraction": f"{updated_state.remaining_position_fraction:.8f}",
        },
    )
    return TradeLifecycleActionRecord(
        action_id=action_id,
        trade_id=state.trade_id,
        at_key=at_key,
        action=action,
        updated_state=updated_state,
        updated_stop_price=updated_state.current_stop_price,
        active_target_price=active_pool.target_price,
        active_target_rr=active_rr,
        remaining_position_fraction=updated_state.remaining_position_fraction,
        realized_r_increment=realized_r_increment,
        cumulative_locked_r=locked_r,
        continuation_reentry_recommendation=reentry_rec,
        reason_code=reason_code,
    )
