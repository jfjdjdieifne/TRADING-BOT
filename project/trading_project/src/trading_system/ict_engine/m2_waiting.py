"""M2 explicit non-implementations, including every thin K2 concept card."""

from __future__ import annotations

from .waiting import WAITING_CONCEPTS, WaitingConcept

K2_THIN_CONCEPTS = (
    "asian_range",
    "consequent_encroachment",
    "directional_bias",
    "higher_time_frame",
    "inefficiency",
    "inversion_fair_value_gap",
    "judas_swing",
    "liquidity_void",
    "long_term_high",
    "market_maker",
    "midnight",
    "money_management",
    "non_farm_payroll",
    "old_low",
    "opening_price",
    "pd_array",
    "rebalance",
    "relative_equal_highs",
    "seasonal_tendency",
    "silver_bullet",
    "swing_high",
    "time_distortion",
    "volume_imbalance",
)

M2_WAITING_CONCEPTS = WAITING_CONCEPTS + tuple(
    WaitingConcept(
        f"k2_thin:{concept}",
        "THIN_CARD_ONE_TO_THREE_PROBE_WINDOWS_NO_NEW_RECOGNIZER",
    )
    for concept in K2_THIN_CONCEPTS
) + (
    WaitingConcept(
        "breaker_swing_point_entry",
        "COMPARISON_DOES_NOT_SUPPLY_COMPLETE_BREAKER_RECOGNIZER",
        ("K2C-001", "U0141", "U0142"),
    ),
    WaitingConcept(
        "mean_threshold_stop_boundary",
        "BODY_OR_WICK_AND_MULTI_CANDLE_SELECTION_UNRESOLVED",
        ("K2C-032", "U0177", "U0180"),
    ),
    WaitingConcept(
        "fixed_pip_stop_transfer",
        "CONTEXT_SPECIFIC_EXAMPLES_NOT_EURUSD_RULES",
        ("K2C-011", "K2C-033", "K2C-034"),
    ),
    WaitingConcept(
        "account_risk_percent",
        "NO_ACCOUNT_OR_POSITION_SIZE_DATA",
        ("K2C-012",),
    ),
    WaitingConcept(
        "stronger_move_higher_threshold",
        "COMPARISON_HAS_NO_DETERMINISTIC_MAGNITUDE",
        ("K2C-017",),
    ),
    WaitingConcept(
        "three_month_inactivity_filter",
        "LITTLE_TO_NO_MOVEMENT_HAS_NO_THRESHOLD",
        ("K2C-027",),
    ),
    WaitingConcept(
        "daily_high_low_selection",
        "PRIORITY_STATEMENT_IS_NOT_A_COMPLETE_PREDICTOR",
        ("K2C-029",),
    ),
    WaitingConcept(
        "eight_item_process",
        "COMPLETE_ORDERED_EIGHT_ITEM_DEFINITION_NOT_IN_COMPARISON",
        ("K2C-030",),
    ),
    WaitingConcept(
        "personal_money_watch",
        "NOT_A_CHART_OBSERVABLE",
        ("K2C-031",),
    ),
    WaitingConcept(
        "post_stop_thesis_management",
        "NO_DETERMINISTIC_REENTRY_RULE",
        ("K2C-035", "K2C-036"),
    ),
    WaitingConcept(
        "liquidity_run_10_20_pips",
        "NO_CROSS_INSTRUMENT_EURUSD_TRANSFER_RULE",
        ("K2C-041",),
    ),
    WaitingConcept(
        "hourly_four_hour_execution_frames",
        "NO_H1_H4_RECOGNIZER_AND_OBVIOUS_HTF_TREND_IS_THIN",
        ("K2C-005", "K2C-006", "K2C-007", "K2C-010"),
    ),
    WaitingConcept(
        "first_profit_partial_quantity",
        "PREMIUM_EXIT_COMPARISON_DOES_NOT_FIX_PARTIAL_QUANTITY",
        ("K2C-014", "K2C-015", "U0119", "U0120"),
    ),
    WaitingConcept(
        "ambiguous_no_trade_conditions",
        "REFERENT_OF_THESE_CONDITIONS_NOT_SUPPLIED",
        ("K2C-018",),
    ),
    WaitingConcept(
        "exit_before_price_leg",
        "ACTUAL_PRICE_LEG_NOT_RESOLVED_TO_A_CAUSAL_LEVEL",
        ("K2C-039",),
    ),
)
