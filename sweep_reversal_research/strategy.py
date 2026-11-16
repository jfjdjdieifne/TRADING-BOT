"""Causal sweep -> one-bar displacement research engine.

This module is deliberately independent from the frozen engines elsewhere in the
repository.  It implements the clarified owner hypothesis in a small, auditable
form:

* a liquidity level is a previously confirmed one-bar-each-side swing;
* a long sweep runs below a confirmed swing low and closes back above it;
* a short sweep runs above a confirmed swing high and closes back below it;
* displacement is the *next* completed candle only (S + 1), never S + 2/S + 3;
* the displacement must point in the same direction as the trade and may create
  the three-candle wick-to-wick FVG;
* the target is the first prior confirmed opposite swing before the swept
  swing (long: first swing high before the swept low; short: first swing low
  before the swept high);
* outcomes are measured on the following three completed setup candles using
  the underlying one-minute OHLC bars.

The code never uses a candle after the displacement to decide whether the
signal exists.  Optional post-displacement observations (small candle/hammer
labels) are descriptive fields only.  They are not filters in the primary run.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

UTC = timezone.utc
FIFTEEN_MINUTES = timedelta(minutes=15)
ONE_MINUTE = timedelta(minutes=1)


@dataclass(frozen=True)
class MinuteBar:
    index: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Bar15:
    index: int
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    first_minute: int
    last_minute: int
    minute_count: int
    complete: bool

    @property
    def price_range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def body_fraction(self) -> float:
        return self.body / self.price_range if self.price_range > 0 else 0.0

    @property
    def color(self) -> str:
        if self.close > self.open:
            return "GREEN"
        if self.close < self.open:
            return "RED"
        return "DOJI"


@dataclass(frozen=True)
class SwingPoint:
    pivot_index: int
    confirmation_index: int
    kind: str  # HIGH or LOW
    price: float


@dataclass(frozen=True)
class StrategyConfig:
    name: str
    require_fvg: bool = True
    large_mode: str = "range_p80"  # range_p80, body_p80, none
    large_percentile: float = 80.0
    min_body_fraction: float = 0.60
    stop_buffer: float = 0.001
    horizon_bars: int = 3


@dataclass(frozen=True)
class Signal:
    config: str
    side: str  # LONG or SHORT
    sweep_index: int
    displacement_index: int
    sweep_time: str
    displacement_time: str
    swept_pivot_index: int
    swept_level: float
    sweep_extreme: float
    target_pivot_index: int | None
    target_confirmation_index: int | None
    target_level: float | None
    displacement_fvg: bool
    displacement_range: float
    displacement_body: float
    displacement_body_fraction: float
    displacement_color: str
    target_rr_at_close: float | None
    eligible: bool
    exclusion: str | None
    post_candle_color: str | None
    post_candle_range: float | None
    post_candle_body_fraction: float | None
    post_candle_small: bool | None
    post_candle_hammer_like: bool | None


@dataclass(frozen=True)
class Outcome:
    config: str
    side: str
    sweep_index: int
    displacement_index: int
    entry_mode: str
    state: str  # TARGET, STOP, TIME, NOT_ELIGIBLE, DATA_GAP, PRE_ENTRY_BARRIER
    entry_time: str | None
    exit_time: str | None
    entry_price: float | None
    exit_price: float | None
    stop_price: float | None
    target_price: float | None
    risk: float | None
    r_multiple: float | None
    bars_held: int | None
    target_hit: bool
    stop_hit: bool
    hit_both_same_minute: bool
    mfe_r: float | None
    mae_r: float | None
    positive_at_horizon: bool | None


def _parse_timestamp(text: str) -> datetime:
    # The packaged historical files use a naive UTC timestamp.
    if text.endswith("Z"):
        text = text[:-1]
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_minutes(data_dir: Path, months: Sequence[str]) -> tuple[list[MinuteBar], dict[str, str]]:
    """Load exactly the requested monthly files in UTC chronological order.

    No data is silently downloaded, filled, interpolated, or forward-filled.
    The returned hash map binds the replay to the bytes actually read.
    """

    requested = sorted(set(months))
    rows: list[MinuteBar] = []
    hashes: dict[str, str] = {}
    for month in requested:
        path = data_dir / f"{month}.csv.gz"
        if not path.exists():
            raise FileNotFoundError(path)
        hashes[path.name] = sha256_file(path)
        with gzip.open(path, "rt", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"Datetime", "Open", "High", "Low", "Close"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"{path}: missing OHLC columns")
            for raw in reader:
                timestamp = _parse_timestamp(raw["Datetime"])
                values = tuple(float(raw[name]) for name in ("Open", "High", "Low", "Close"))
                op, hi, lo, close = values
                if not (lo <= op <= hi and lo <= close <= hi and hi >= lo):
                    raise ValueError(f"{path}: invalid OHLC at {timestamp}")
                rows.append(MinuteBar(len(rows), timestamp, op, hi, lo, close))
    rows.sort(key=lambda row: row.timestamp)
    # Re-index after sorting, and reject duplicate timestamps rather than
    # allowing file order to decide which future fact wins.
    seen: set[datetime] = set()
    normalised: list[MinuteBar] = []
    for row in rows:
        if row.timestamp in seen:
            raise ValueError(f"duplicate minute timestamp: {row.timestamp.isoformat()}")
        seen.add(row.timestamp)
        normalised.append(MinuteBar(len(normalised), row.timestamp, row.open, row.high, row.low, row.close))
    return normalised, hashes


def _flush_bucket(bucket: list[MinuteBar], out: list[Bar15]) -> None:
    if not bucket:
        return
    start = bucket[0].timestamp.replace(
        minute=(bucket[0].timestamp.minute // 15) * 15,
        second=0,
        microsecond=0,
    )
    expected = [start + ONE_MINUTE * offset for offset in range(15)]
    actual = [row.timestamp for row in bucket]
    complete = len(bucket) == 15 and actual == expected
    out.append(
        Bar15(
            index=len(out),
            start=start,
            end=start + FIFTEEN_MINUTES,
            open=bucket[0].open,
            high=max(row.high for row in bucket),
            low=min(row.low for row in bucket),
            close=bucket[-1].close,
            first_minute=bucket[0].index,
            last_minute=bucket[-1].index,
            minute_count=len(bucket),
            complete=complete,
        )
    )


def aggregate_15m(minutes: Sequence[MinuteBar]) -> list[Bar15]:
    """Build left-closed 15-minute bars without filling market-data gaps."""

    result: list[Bar15] = []
    bucket: list[MinuteBar] = []
    bucket_key: datetime | None = None
    for row in minutes:
        key = row.timestamp.replace(minute=(row.timestamp.minute // 15) * 15, second=0, microsecond=0)
        if bucket_key is None or key == bucket_key:
            bucket.append(row)
            bucket_key = key
        else:
            _flush_bucket(bucket, result)
            bucket = [row]
            bucket_key = key
    _flush_bucket(bucket, result)
    complete = [bar for bar in result if bar.complete]
    # Internal indices are positions in this returned sequence, not positions
    # in the unfiltered bucket stream.
    return [
        Bar15(
            index=index,
            start=bar.start,
            end=bar.end,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            first_minute=bar.first_minute,
            last_minute=bar.last_minute,
            minute_count=bar.minute_count,
            complete=True,
        )
        for index, bar in enumerate(complete)
    ]


def _contiguous(bars: Sequence[Bar15], start: int, end: int) -> bool:
    """True if every 15m boundary in [start, end] is present."""

    if start < 0 or end >= len(bars) or start > end:
        return False
    return all(bars[i].start - bars[i - 1].start == FIFTEEN_MINUTES for i in range(start + 1, end + 1))


def percentile(values: Sequence[float], percent: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(float(value) for value in values)
    rank = max(1, math.ceil((percent / 100.0) * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def detect_swings(bars: Sequence[Bar15]) -> list[SwingPoint]:
    """Detect strict three-candle swings; a pivot is visible one bar later."""

    swings: list[SwingPoint] = []
    for pivot in range(1, len(bars) - 1):
        if not _contiguous(bars, pivot - 1, pivot + 1):
            continue
        left, middle, right = bars[pivot - 1], bars[pivot], bars[pivot + 1]
        if middle.high > left.high and middle.high > right.high:
            swings.append(SwingPoint(pivot, pivot + 1, "HIGH", middle.high))
        if middle.low < left.low and middle.low < right.low:
            swings.append(SwingPoint(pivot, pivot + 1, "LOW", middle.low))
    return swings


def _latest_confirmed(swings: Sequence[SwingPoint], kind: str, before_index: int) -> SwingPoint | None:
    eligible = [point for point in swings if point.kind == kind and point.confirmation_index < before_index]
    return max(eligible, key=lambda point: point.pivot_index) if eligible else None


def _target_before_swept_swing(
    swings: Sequence[SwingPoint],
    side: str,
    swept_pivot_index: int,
    sweep_index: int,
) -> SwingPoint | None:
    wanted = "HIGH" if side == "LONG" else "LOW"
    eligible = [
        point
        for point in swings
        if point.kind == wanted
        and point.pivot_index < swept_pivot_index
        and point.confirmation_index < sweep_index
    ]
    # The contract calls for the first opposite swing before the swept swing,
    # not the latest/nearest one selected with max().  The pivot index is the
    # causal chronological order of the confirmed swings.
    return min(eligible, key=lambda point: point.pivot_index) if eligible else None


def _is_large(displacement: Bar15, prior: Sequence[Bar15], config: StrategyConfig) -> bool:
    if config.large_mode == "none":
        return True
    if not prior:
        return False
    if config.large_mode == "range_p80":
        reference = [bar.price_range for bar in prior]
        return displacement.price_range >= percentile(reference, config.large_percentile)
    if config.large_mode == "body_p80":
        reference = [bar.body for bar in prior]
        return displacement.body >= percentile(reference, config.large_percentile)
    raise ValueError(f"unknown large_mode: {config.large_mode}")


def _has_fvg(bars: Sequence[Bar15], sweep_index: int, displacement_index: int, side: str) -> bool:
    # Three candles are [pre-sweep, sweep, displacement].  This is known only
    # when displacement_index closes, and uses wicks exactly.
    if sweep_index < 1 or displacement_index != sweep_index + 1:
        return False
    first = bars[sweep_index - 1]
    third = bars[displacement_index]
    if side == "LONG":
        return third.low > first.high
    return third.high < first.low


def _post_candle_features(
    bars: Sequence[Bar15], displacement_index: int, side: str, lookback: int = 20
) -> tuple[str | None, float | None, float | None, bool | None, bool | None]:
    """Descriptive small/hammer labels, intentionally after the signal."""

    index = displacement_index + 1
    if index >= len(bars) or not _contiguous(bars, displacement_index, index):
        return None, None, None, None, None
    post = bars[index]
    prior = bars[max(0, index - lookback) : index]
    if len(prior) < lookback:
        return post.color, post.price_range, post.body_fraction, None, None
    small = post.price_range <= percentile([bar.price_range for bar in prior], 50.0)
    body = post.body_fraction
    if side == "LONG":
        wick = min(post.open, post.close) - post.low
        opposite_wick = post.high - max(post.open, post.close)
    else:
        wick = post.high - max(post.open, post.close)
        opposite_wick = min(post.open, post.close) - post.low
    hammer = body > 0 and wick >= 1.5 * post.body and opposite_wick <= post.body
    return post.color, post.price_range, body, small, hammer


def _safe_rr(side: str, entry: float, stop: float, target: float) -> float | None:
    risk = entry - stop if side == "LONG" else stop - entry
    reward = target - entry if side == "LONG" else entry - target
    return reward / risk if risk > 0 and reward > 0 else None


def detect_signals(
    bars: Sequence[Bar15],
    config: StrategyConfig,
    eval_start: datetime | None = None,
    eval_end: datetime | None = None,
) -> list[Signal]:
    """Scan sequentially; all decision fields stop at S+1.

    The `post_candle_*` fields are explicitly descriptive and do not affect
    `eligible`, so a prefix replay can be audited independently of them.
    """

    swings = detect_swings(bars)
    signals: list[Signal] = []
    lookback = 20
    first_signal_index = max(lookback + 1, 3)
    for sweep_index in range(first_signal_index, len(bars) - 1):
        sweep = bars[sweep_index]
        displacement_index = sweep_index + 1
        displacement = bars[displacement_index]
        if not _contiguous(bars, sweep_index - 1, displacement_index):
            continue
        if eval_start is not None and displacement.end <= eval_start:
            continue
        if eval_end is not None and displacement.end > eval_end:
            continue

        for side, swept_kind in (("LONG", "LOW"), ("SHORT", "HIGH")):
            swept = _latest_confirmed(swings, swept_kind, sweep_index)
            if swept is None:
                continue
            if side == "LONG":
                is_sweep = sweep.low < swept.price and sweep.close > swept.price
                direction_ok = displacement.close > displacement.open
            else:
                is_sweep = sweep.high > swept.price and sweep.close < swept.price
                direction_ok = displacement.close < displacement.open
            if not is_sweep:
                continue

            prior = bars[max(0, displacement_index - lookback) : displacement_index]
            large_ok = _is_large(displacement, prior, config)
            body_ok = displacement.body_fraction >= config.min_body_fraction
            fvg = _has_fvg(bars, sweep_index, displacement_index, side)
            target = _target_before_swept_swing(swings, side, swept.pivot_index, sweep_index)
            target_level = target.price if target is not None else None
            entry = displacement.close
            stop = sweep.low - config.stop_buffer if side == "LONG" else sweep.high + config.stop_buffer
            target_rr = _safe_rr(side, entry, stop, target_level) if target_level is not None else None
            exclusion: str | None = None
            if not direction_ok:
                exclusion = "DISPLACEMENT_WRONG_COLOR"
            elif not large_ok:
                exclusion = "DISPLACEMENT_NOT_LARGE_P80"
            elif not body_ok:
                exclusion = "DISPLACEMENT_BODY_TOO_SMALL"
            elif config.require_fvg and not fvg:
                exclusion = "NO_THREE_CANDLE_FVG"
            elif target is None:
                exclusion = "NO_PRIOR_OPPOSITE_SWING_TARGET"
            elif target_rr is None:
                exclusion = "TARGET_BEHIND_OR_AT_ENTRY"
            post = _post_candle_features(bars, displacement_index, side)
            signals.append(
                Signal(
                    config=config.name,
                    side=side,
                    sweep_index=sweep_index,
                    displacement_index=displacement_index,
                    sweep_time=sweep.start.isoformat(),
                    displacement_time=displacement.start.isoformat(),
                    swept_pivot_index=swept.pivot_index,
                    swept_level=swept.price,
                    sweep_extreme=sweep.low if side == "LONG" else sweep.high,
                    target_pivot_index=target.pivot_index if target else None,
                    target_confirmation_index=target.confirmation_index if target else None,
                    target_level=target_level,
                    displacement_fvg=fvg,
                    displacement_range=displacement.price_range,
                    displacement_body=displacement.body,
                    displacement_body_fraction=displacement.body_fraction,
                    displacement_color=displacement.color,
                    target_rr_at_close=target_rr,
                    eligible=exclusion is None,
                    exclusion=exclusion,
                    post_candle_color=post[0],
                    post_candle_range=post[1],
                    post_candle_body_fraction=post[2],
                    post_candle_small=post[3],
                    post_candle_hammer_like=post[4],
                )
            )
    return signals


def signal_core_signature(signal: Signal) -> tuple:
    """Fields that must be invariant when future bars are appended."""

    return (
        signal.config,
        signal.side,
        signal.sweep_index,
        signal.displacement_index,
        signal.swept_pivot_index,
        signal.swept_level,
        signal.target_pivot_index,
        signal.target_confirmation_index,
        signal.target_level,
        signal.displacement_fvg,
        signal.eligible,
        signal.exclusion,
    )


def _minute_path(
    minutes: Sequence[MinuteBar], bars: Sequence[Bar15], start_bar: int, end_bar: int
) -> Iterable[MinuteBar]:
    if start_bar < 0 or end_bar >= len(bars):
        return []
    start = bars[start_bar].first_minute
    end = bars[end_bar].last_minute
    return minutes[start : end + 1]


def _path_has_barrier(
    minutes: Sequence[MinuteBar], bars: Sequence[Bar15], start_bar: int, end_bar: int, side: str, stop: float, target: float
) -> tuple[bool, bool]:
    hit_stop = False
    hit_target = False
    for minute in _minute_path(minutes, bars, start_bar, end_bar):
        if side == "LONG":
            hit_stop = hit_stop or minute.low <= stop
            hit_target = hit_target or minute.high >= target
        else:
            hit_stop = hit_stop or minute.high >= stop
            hit_target = hit_target or minute.low <= target
    return hit_stop, hit_target


def _make_outcome(**kwargs: object) -> Outcome:
    """Construct outcomes by field name so a positional-field shift cannot hide a bug."""

    return Outcome(**kwargs)  # type: ignore[arg-type]


def simulate(
    signal: Signal,
    bars: Sequence[Bar15],
    minutes: Sequence[MinuteBar],
    *,
    entry_mode: str = "immediate",
) -> Outcome:
    """Convenience wrapper using the default one-tick stop buffer."""

    return simulate_with_config(signal, StrategyConfig(name=signal.config), bars, minutes, entry_mode=entry_mode)


def simulate_with_config(
    signal: Signal,
    config: StrategyConfig,
    bars: Sequence[Bar15],
    minutes: Sequence[MinuteBar],
    *,
    entry_mode: str = "immediate",
) -> Outcome:
    """Simulate a three-15m-bar trade with conservative stop-first ties.

    `immediate`: enter at the displacement close, then observe D+1..D+3.
    `after_three`: wait for the close of D+3.  If stop/target was already
    reached before that close, no trade is entered; otherwise observe D+4..D+6.
    This avoids hindsight fills while still measuring the delayed-entry idea.
    """

    common = {
        "config": signal.config,
        "side": signal.side,
        "sweep_index": signal.sweep_index,
        "displacement_index": signal.displacement_index,
        "entry_mode": entry_mode,
    }
    if not signal.eligible or signal.target_level is None:
        return _make_outcome(**common, state="NOT_ELIGIBLE", entry_time=None, exit_time=None,
                             entry_price=None, exit_price=None, stop_price=None, target_price=None,
                             risk=None, r_multiple=None, bars_held=None, target_hit=False,
                             stop_hit=False, hit_both_same_minute=False, mfe_r=None, mae_r=None,
                             positive_at_horizon=None)

    d = signal.displacement_index
    pre_entry_end = d + config.horizon_bars
    final_end = pre_entry_end if entry_mode == "immediate" else pre_entry_end + config.horizon_bars
    if final_end >= len(bars) or not _contiguous(bars, d, final_end):
        return _make_outcome(**common, state="DATA_GAP", entry_time=None, exit_time=None,
                             entry_price=None, exit_price=None, stop_price=None,
                             target_price=signal.target_level, risk=None, r_multiple=None,
                             bars_held=None, target_hit=False, stop_hit=False,
                             hit_both_same_minute=False, mfe_r=None, mae_r=None,
                             positive_at_horizon=None)

    if entry_mode == "immediate":
        entry_bar = d
        path_start = d + 1
        path_end = pre_entry_end
    elif entry_mode == "after_three":
        entry_bar = pre_entry_end
        path_start = entry_bar + 1
        path_end = final_end
        provisional_stop = (
            signal.sweep_extreme - config.stop_buffer
            if signal.side == "LONG"
            else signal.sweep_extreme + config.stop_buffer
        )
        stop_pre, target_pre = _path_has_barrier(
            minutes, bars, d + 1, entry_bar, signal.side, provisional_stop, signal.target_level
        )
        if stop_pre or target_pre:
            return _make_outcome(
                **common, state="PRE_ENTRY_BARRIER", entry_time=None, exit_time=None,
                entry_price=None, exit_price=None, stop_price=provisional_stop,
                target_price=signal.target_level, risk=None, r_multiple=None, bars_held=None,
                target_hit=target_pre, stop_hit=stop_pre, hit_both_same_minute=False,
                mfe_r=None, mae_r=None, positive_at_horizon=None,
            )
        path_start = entry_bar + 1
    else:
        raise ValueError(f"unknown entry_mode: {entry_mode}")

    entry_price = bars[entry_bar].close
    stop = (
        signal.sweep_extreme - config.stop_buffer
        if signal.side == "LONG"
        else signal.sweep_extreme + config.stop_buffer
    )
    target = signal.target_level
    risk = entry_price - stop if signal.side == "LONG" else stop - entry_price
    reward = target - entry_price if signal.side == "LONG" else entry_price - target
    if risk <= 0 or reward <= 0:
        return _make_outcome(
            **common, state="NOT_ELIGIBLE", entry_time=None, exit_time=None,
            entry_price=entry_price, exit_price=None, stop_price=stop, target_price=target,
            risk=risk, r_multiple=None, bars_held=None, target_hit=False, stop_hit=False,
            hit_both_same_minute=False, mfe_r=None, mae_r=None, positive_at_horizon=None,
        )

    path = list(_minute_path(minutes, bars, path_start, path_end))
    if not path:
        return _make_outcome(
            **common, state="DATA_GAP", entry_time=bars[entry_bar].end.isoformat(),
            exit_time=None, entry_price=entry_price, exit_price=None, stop_price=stop,
            target_price=target, risk=risk, r_multiple=None, bars_held=None, target_hit=False,
            stop_hit=False, hit_both_same_minute=False, mfe_r=None, mae_r=None,
            positive_at_horizon=None,
        )

    max_favourable = 0.0
    max_adverse = 0.0
    for minute in path:
        if signal.side == "LONG":
            max_favourable = max(max_favourable, minute.high - entry_price)
            max_adverse = max(max_adverse, entry_price - minute.low)
            hit_stop = minute.low <= stop
            hit_target = minute.high >= target
        else:
            max_favourable = max(max_favourable, entry_price - minute.low)
            max_adverse = max(max_adverse, minute.high - entry_price)
            hit_stop = minute.high >= stop
            hit_target = minute.low <= target
        if hit_stop:
            # OHLC does not reveal order inside one minute.  Stop-first is the
            # conservative, reproducible convention when both are touched.
            return _make_outcome(
                **common, state="STOP", entry_time=bars[entry_bar].end.isoformat(),
                exit_time=minute.timestamp.isoformat(), entry_price=entry_price,
                exit_price=stop, stop_price=stop, target_price=target, risk=risk,
                r_multiple=-1.0, bars_held=max(1, minute.index - bars[entry_bar].last_minute),
                target_hit=False, stop_hit=True, hit_both_same_minute=hit_target,
                mfe_r=max_favourable / risk, mae_r=max_adverse / risk,
                positive_at_horizon=False,
            )
        if hit_target:
            return _make_outcome(
                **common, state="TARGET", entry_time=bars[entry_bar].end.isoformat(),
                exit_time=minute.timestamp.isoformat(), entry_price=entry_price,
                exit_price=target, stop_price=stop, target_price=target, risk=risk,
                r_multiple=reward / risk, bars_held=max(1, minute.index - bars[entry_bar].last_minute),
                target_hit=True, stop_hit=False, hit_both_same_minute=False,
                mfe_r=max_favourable / risk, mae_r=max_adverse / risk,
                positive_at_horizon=True,
            )

    exit_bar = bars[path_end]
    exit_price = exit_bar.close
    r = (exit_price - entry_price) / risk if signal.side == "LONG" else (entry_price - exit_price) / risk
    return _make_outcome(
        **common, state="TIME", entry_time=bars[entry_bar].end.isoformat(),
        exit_time=exit_bar.end.isoformat(), entry_price=entry_price, exit_price=exit_price,
        stop_price=stop, target_price=target, risk=risk, r_multiple=r,
        bars_held=config.horizon_bars, target_hit=False, stop_hit=False,
        hit_both_same_minute=False, mfe_r=max_favourable / risk, mae_r=max_adverse / risk,
        positive_at_horizon=r > 0,
    )


def as_jsonable(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {key: as_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    return value


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(as_jsonable(value), indent=2, sort_keys=True), encoding="utf-8")
