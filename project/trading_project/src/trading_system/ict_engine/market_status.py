"""Causal market/filler status derived from each bar's own recorded structure."""

from __future__ import annotations

from enum import Enum

from .data import Candle


class MarketStatus(str, Enum):
    MARKET = "market"
    NO_MARKET_WEEKEND_FILLER = "no_market_weekend_filler"
    NO_MARKET_INTRAWEEK_FLAT = "no_market_intraweek_flat"
    UNRESOLVED_ZERO_VOLUME = "unresolved_zero_volume"


def is_exactly_flat(candle: Candle) -> bool:
    """Exact BID and ASK range equality; no epsilon or price threshold."""

    return candle.bid_high == candle.bid_low and candle.ask_high == candle.ask_low


def has_zero_bid_and_ask_volume(candle: Candle) -> bool:
    return candle.bid_volume == 0 and candle.ask_volume == 0


def market_status(candle: Candle) -> MarketStatus:
    """Classify using only this candle, never neighbours or future information.

    Every zero-volume Friday bar in the pinned data is exact flat closure filler.
    Thus Friday/Saturday/Sunday + exact flat + zero BID/ASK volume is the causal
    weekend class; Monday-Thursday with the same structure is intra-week flat.
    Positive-volume flat bars remain market bars. Non-flat zero-volume bars are
    unresolved and must not be silently discarded.
    """

    if not has_zero_bid_and_ask_volume(candle):
        return MarketStatus.MARKET
    if not is_exactly_flat(candle):
        return MarketStatus.UNRESOLVED_ZERO_VOLUME
    if candle.start.weekday() >= 4:
        return MarketStatus.NO_MARKET_WEEKEND_FILLER
    return MarketStatus.NO_MARKET_INTRAWEEK_FLAT


def is_no_market(candle: Candle) -> bool:
    """The only statuses primitives may exclude as structurally absent market."""

    return market_status(candle) in {
        MarketStatus.NO_MARKET_WEEKEND_FILLER,
        MarketStatus.NO_MARKET_INTRAWEEK_FLAT,
    }
