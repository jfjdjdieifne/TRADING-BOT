#!/usr/bin/env python3
"""Setup-frame aggregation: build 15m / 1h candles out of the 5m stream, completion-labelled.

A higher-frame candle exists only when its **last** 5m bar has closed.  Until then the partial
high/low is never exposed to any reader, so a 5m bar inside a still-forming 15m candle cannot use
that candle's partial range as structure (DECLARED_CHOICES_V2 row B).

The 5m frame is the identity aggregation: every 5m bar closes as it arrives, which is why V2-0 can
run through the same code path as V2-A and V2-B without behaving differently from v1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from stream_v1 import Bar

UTC = timezone.utc
FRAME_MINUTES = {"5m": 5, "15m": 15, "1h": 60}


def bucket_start(moment: datetime, minutes: int) -> datetime:
    """UTC-aligned bucket start, computed on the epoch so 1h is not a special case."""

    step = minutes * 60
    epoch = int(moment.timestamp())
    return datetime.fromtimestamp((epoch // step) * step, tz=UTC)


class FrameAggregator:
    """Accumulate 5m bars into one higher-frame bar; emit it only at the bucket change."""

    def __init__(self, minutes: int) -> None:
        if minutes < 5 or minutes % 5:
            raise ValueError(f"frame of {minutes} minutes cannot be built from 5m bars")
        self.minutes = minutes
        self.key: datetime | None = None
        self.open_bar: Bar | None = None
        self.high = self.low = self.close = 0.0
        self.ask_high = self.ask_low = self.ask_close = self.ask_open = 0.0
        self.volume = self.ask_volume = 0.0
        self.last: Bar | None = None
        self.count = 0

    def push(self, bar: Bar) -> Bar | None:
        """Feed one 5m bar; return the finished higher-frame bar when its bucket has closed."""

        key = bucket_start(bar.start, self.minutes)
        closed = None
        if self.key is not None and key != self.key:
            closed = self._emit()
        if self.key is None or key != self.key:
            self.key = key
            self.open_bar = bar
            self.high, self.low, self.close = bar.bid_high, bar.bid_low, bar.bid_close
            self.ask_open, self.ask_high = bar.ask_open, bar.ask_high
            self.ask_low, self.ask_close = bar.ask_low, bar.ask_close
            self.volume, self.ask_volume = bar.bid_volume, bar.ask_volume
            self.count = 1
        else:
            self.high = max(self.high, bar.bid_high)
            self.low = min(self.low, bar.bid_low)
            self.close = bar.bid_close
            self.ask_high = max(self.ask_high, bar.ask_high)
            self.ask_low = min(self.ask_low, bar.ask_low)
            self.ask_close = bar.ask_close
            self.volume += bar.bid_volume
            self.ask_volume += bar.ask_volume
            self.count += 1
        self.last = bar
        # a 5m aggregation is complete the moment its own bar closes
        if self.minutes == 5 and closed is None:
            closed = self._emit()
            self.key = None
        return closed

    def flush(self) -> Bar | None:
        """Emit the trailing partial candle at end of stream (labelled as complete by the caller)."""

        return self._emit() if self.key is not None else None

    def _emit(self) -> Bar | None:
        if self.open_bar is None or self.last is None:
            return None
        first, last = self.open_bar, self.last
        bar = Bar(
            start=self.key,
            bid_open=float(first.bid_open), bid_high=float(self.high),
            bid_low=float(self.low), bid_close=float(self.close),
            bid_volume=float(self.volume),
            ask_open=float(first.ask_open), ask_high=float(self.ask_high),
            ask_low=float(self.ask_low), ask_close=float(self.ask_close),
            ask_volume=float(self.ask_volume),
            # the spread fields of a higher-frame candle are the LAST 5m bar's, declared in
            # DECLARED_CHOICES_V2 row B: no aggregation rule for a spread is claimed
            spread_open=float(last.spread_open), spread_open_pips=float(last.spread_open_pips),
            spread_high=float(last.spread_high), spread_high_pips=float(last.spread_high_pips),
            spread_low=float(last.spread_low), spread_low_pips=float(last.spread_low_pips),
            spread_close=float(last.spread_close), spread_close_pips=float(last.spread_close_pips),
        )
        self.open_bar = None
        self.last = None
        return bar


def covered_minutes(minutes: int, bars: int) -> timedelta:
    return timedelta(minutes=minutes * bars)
