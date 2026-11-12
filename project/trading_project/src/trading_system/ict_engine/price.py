"""Explicit BID/ASK observables; no silently selected midpoint."""

from __future__ import annotations

from enum import Enum

from .data import Candle


class PriceBasis(str, Enum):
    BID = "bid"
    ASK = "ask"


def ohlc(candle: Candle, basis: PriceBasis) -> tuple[float, float, float, float]:
    if basis is PriceBasis.BID:
        return candle.bid_open, candle.bid_high, candle.bid_low, candle.bid_close
    if basis is PriceBasis.ASK:
        return candle.ask_open, candle.ask_high, candle.ask_low, candle.ask_close
    raise ValueError(f"Unsupported price basis: {basis!r}")


def spread_at_open(candle: Candle) -> float:
    return candle.ask_open - candle.bid_open
