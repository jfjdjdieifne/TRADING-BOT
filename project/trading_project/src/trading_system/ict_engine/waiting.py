"""Explicit non-implementations; no missing doctrine is silently faked."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WaitingConcept:
    concept: str
    reason: str
    claim_ids: tuple[str, ...] = ()


UNCARDED_CONCEPTS = (
    "relative_equal_highs", "old_high", "old_low", "run_on_stops", "liquidity_pool",
    "short_term_high", "intermediate_term_high", "long_term_high", "swing_high",
    "swing_low", "data_range", "ipda", "breaker", "mitigation_block",
    "rejection_block", "consequent_encroachment", "imbalance", "inefficiency",
    "rebalance", "volume_imbalance", "liquidity_void", "inversion_fair_value_gap",
    "optimal_trade_entry", "2022_model", "premium", "discount", "pd_array",
    "asian_range", "london_session", "new_york_session", "midnight", "opening_price",
    "directional_bias", "higher_time_frame", "lower_time_frame", "seasonal_tendency",
    "mean_threshold", "time_distortion", "non_farm_payroll", "money_management",
    "one_shot_one_kill", "turtle_soup", "silver_bullet", "judas_swing",
    "smt_divergence", "market_maker",
)

WAITING_CONCEPTS = tuple(
    WaitingConcept(concept, "NO_U2_CARD")
    for concept in UNCARDED_CONCEPTS
) + (
    WaitingConcept("swing_hierarchy", "NO_CARD_DEFINITION_FOR_SHORT_INTERMEDIATE_LONG_TERM"),
    WaitingConcept("inversion_fair_value_gap_recognizer", "NAME_ONLY_NO_COMPLETE_CRITERIA", ("U0042",)),
    WaitingConcept("breakaway_gap_recognizer", "RETURN_PERSISTENCE_DURATION_NOT_GIVEN", ("U0043",)),
    WaitingConcept("order_block_full_qualification", "REJECTION_CRITERION_TRUNCATED", ("U0051",)),
    WaitingConcept("market_structure_candidate_tie_break", "SELECTED_BY_DISCRETIONARY_PLAY", ("U0063",)),
    WaitingConcept("carrying_charge_premium", "REQUIRES_NEAR_AND_DEFERRED_CONTRACT_DATA", ("U0088",)),
    WaitingConcept("new_york_wide_window_end", "QUOTE_ENDS_AFTER_WIDE_0830_TO", ("U0095",)),
    WaitingConcept("london_0100_window_end", "START_ONLY_IN_CARD", ("U0089",)),
    WaitingConcept("london_0200_open_window_end", "START_ONLY_IN_CARD", ("U0090", "U0091")),
    WaitingConcept("equal_extreme_cleanliness_cutoff", "ONLY_RELATIVE_RANK_NO_FIXED_TOLERANCE", ("U0022", "U0032")),
    WaitingConcept("displacement_magnitude_cutoff", "ONLY_RELATIVE_ENERGY_NO_FIXED_MULTIPLIER", ("U0055",)),
    WaitingConcept("partial_quantity", "EXPLICITLY_LEFT_TO_TRADER", ("U0119", "U0120")),
    WaitingConcept("no_rush_break_even_trigger", "QUALITATIVE_NO_DETERMINISTIC_TRIGGER", ("U0118",)),
)
