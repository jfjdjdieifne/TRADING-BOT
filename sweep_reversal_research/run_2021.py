#!/usr/bin/env python3
"""Run the corrected one-bar displacement replay on packaged XAUUSD data.

The default run is intentionally fixed before reading the results:
2021-06 through 2021-11 are the six evaluation months. 2021-05 is warm-up;
2021-12 is outcome-only context for signals near the end of November. No
parameter is selected from the generated results.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from strategy import (
    Bar15,
    MinuteBar,
    Outcome,
    Signal,
    StrategyConfig,
    aggregate_15m,
    as_jsonable,
    detect_signals,
    load_minutes,
    signal_core_signature,
    simulate_with_config,
    write_json,
)
from report import write_report

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "smc_v4_multisleeve_package" / "data" / "XAUUSD_1m_histdata"
RESULTS = HERE / "results_2021_six_months"
EVAL_MONTHS = [f"2021-{month:02d}" for month in range(6, 12)]
LOAD_MONTHS = ["2021-05", *EVAL_MONTHS, "2021-12"]
EVAL_START = datetime(2021, 6, 1, tzinfo=UTC)
EVAL_END = datetime(2021, 12, 1, tzinfo=UTC)

CONFIGS = (
    StrategyConfig(
        name="STRICT_FVG_P80",
        require_fvg=True,
        large_mode="range_p80",
        large_percentile=80.0,
        min_body_fraction=0.60,
        stop_buffer=0.001,
        horizon_bars=3,
    ),
    StrategyConfig(
        name="DIRECTION_P80_NO_FVG",
        require_fvg=False,
        large_mode="range_p80",
        large_percentile=80.0,
        min_body_fraction=0.60,
        stop_buffer=0.001,
        horizon_bars=3,
    ),
    StrategyConfig(
        name="FVG_NO_SIZE_FILTER",
        require_fvg=True,
        large_mode="none",
        large_percentile=80.0,
        min_body_fraction=0.0,
        stop_buffer=0.001,
        horizon_bars=3,
    ),
)
PRIMARY = CONFIGS[0].name


def _parse(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text)


def _month(text: str) -> str:
    return text[:7]


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _signal_row(signal: Signal, config: StrategyConfig) -> dict:
    row = asdict(signal)
    row["stop_price"] = (
        signal.sweep_extreme - config.stop_buffer
        if signal.side == "LONG"
        else signal.sweep_extreme + config.stop_buffer
    )
    row["target_definition"] = (
        "nearest confirmed swing high before swept low"
        if signal.side == "LONG"
        else "nearest confirmed swing low before swept high"
    )
    row["eval_month"] = _month(signal.sweep_time)
    return row


def _outcome_row(outcome: Outcome) -> dict:
    row = asdict(outcome)
    row["eval_month"] = _month(outcome.entry_time) if outcome.entry_time else None
    return row


def _stats(outcomes: list[Outcome]) -> dict:
    entered = [item for item in outcomes if item.state in {"TARGET", "STOP", "TIME"}]
    settled_barrier = [item for item in entered if item.state in {"TARGET", "STOP"}]
    rs = [float(item.r_multiple) for item in entered if item.r_multiple is not None]
    mfe = [float(item.mfe_r) for item in entered if item.mfe_r is not None]
    mae = [float(item.mae_r) for item in entered if item.mae_r is not None]
    target_count = sum(item.state == "TARGET" for item in entered)
    stop_count = sum(item.state == "STOP" for item in entered)
    return {
        "signals_in_group": len(outcomes),
        "entered": len(entered),
        "target_hits": target_count,
        "stop_hits": stop_count,
        "time_exits": sum(item.state == "TIME" for item in entered),
        "pre_entry_barrier": sum(item.state == "PRE_ENTRY_BARRIER" for item in outcomes),
        "not_eligible": sum(item.state == "NOT_ELIGIBLE" for item in outcomes),
        "data_gap": sum(item.state == "DATA_GAP" for item in outcomes),
        "target_hit_rate_of_barrier_exits": (
            target_count / len(settled_barrier) if settled_barrier else None
        ),
        "positive_at_three_bar_horizon": sum(
            bool(item.positive_at_horizon) for item in entered if item.positive_at_horizon is not None
        ),
        "positive_at_three_bar_horizon_rate": (
            sum(bool(item.positive_at_horizon) for item in entered if item.positive_at_horizon is not None)
            / len([item for item in entered if item.positive_at_horizon is not None])
            if any(item.positive_at_horizon is not None for item in entered)
            else None
        ),
        "sum_r": sum(rs) if rs else 0.0,
        "mean_r": statistics.fmean(rs) if rs else None,
        "median_r": statistics.median(rs) if rs else None,
        "mean_mfe_r": statistics.fmean(mfe) if mfe else None,
        "mean_mae_r": statistics.fmean(mae) if mae else None,
        "max_r": max(rs) if rs else None,
        "min_r": min(rs) if rs else None,
    }


def _group_summary(signals: list[Signal], outcome_map: dict[tuple, Outcome], entry_mode: str) -> dict:
    groups: dict[tuple[str, str], list[Outcome]] = defaultdict(list)
    for signal in signals:
        key = (signal.config, signal.side, signal.sweep_index, entry_mode)
        if key in outcome_map:
            groups[(signal.config, signal.side)].append(outcome_map[key])
    result: dict[str, dict] = {}
    for (config, side), outcomes in sorted(groups.items()):
        result[f"{config}|{side}|{entry_mode}"] = _stats(outcomes)
    return result


def _monthly_summary(signals: list[Signal], outcomes: list[Outcome], entry_mode: str) -> dict:
    by_signal: dict[tuple, Signal] = {
        (signal.config, signal.side, signal.sweep_index): signal for signal in signals
    }
    grouped: dict[tuple[str, str, str], list[Outcome]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.entry_mode != entry_mode:
            continue
        signal = by_signal.get((outcome.config, outcome.side, outcome.sweep_index))
        if signal is not None:
            grouped[(_month(signal.sweep_time), outcome.config, outcome.side)].append(outcome)
    result: dict[str, dict] = {}
    for (month, config, side), group in sorted(grouped.items()):
        result[f"{month}|{config}|{side}|{entry_mode}"] = _stats(group)
    return result


def _svg_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_example(path: Path, signal: Signal, bars: list[Bar15], config: StrategyConfig) -> None:
    """Write a dependency-free SVG candlestick card for a real replay signal."""

    lo = max(0, signal.sweep_index - 6)
    hi = min(len(bars), signal.displacement_index + 5)
    window = bars[lo:hi]
    stop = signal.sweep_extreme - config.stop_buffer if signal.side == "LONG" else signal.sweep_extreme + config.stop_buffer
    prices = [value for bar in window for value in (bar.high, bar.low)]
    prices += [signal.swept_level, signal.target_level or signal.swept_level, stop]
    pmin, pmax = min(prices), max(prices)
    pad = max((pmax - pmin) * 0.12, 0.01)
    pmin -= pad
    pmax += pad
    width, height = 1180, 680
    left, right, top, bottom = 70, 30, 80, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    step = plot_w / max(1, len(window))
    body_w = min(34.0, step * 0.58)

    def y(price: float) -> float:
        return top + (pmax - price) / (pmax - pmin) * plot_h

    def x(index: int) -> float:
        return left + (index - lo + 0.5) * step

    def text(xp: float, yp: float, content: str, size: int = 15, color: str = "#dbeafe", anchor: str = "start") -> str:
        return f'<text x="{xp:.1f}" y="{yp:.1f}" fill="{color}" font-size="{size}px" text-anchor="{anchor}" font-family="Arial, sans-serif">{_svg_escape(content)}</text>'

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0b1220"/>',
        text(left, 32, f"{signal.side}: sweep -> next-candle displacement -> prior swing target", 21, "#f8fafc"),
        text(left, 56, f"Real XAUUSD 15m | S {signal.sweep_time} | D {signal.displacement_time} | FVG={signal.displacement_fvg}", 13, "#94a3b8"),
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#111827" stroke="#334155"/>',
    ]
    for tick in range(5):
        price = pmin + (pmax - pmin) * tick / 4
        yp = y(price)
        lines.append(f'<line x1="{left}" y1="{yp:.1f}" x2="{left + plot_w}" y2="{yp:.1f}" stroke="#1f2937"/>')
        lines.append(text(left - 8, yp + 5, f"{price:.3f}", 12, "#64748b", "end"))

    for bar in window:
        cx = x(bar.index)
        color = "#22c55e" if bar.close >= bar.open else "#ef4444"
        lines.append(f'<line x1="{cx:.1f}" y1="{y(bar.high):.1f}" x2="{cx:.1f}" y2="{y(bar.low):.1f}" stroke="{color}" stroke-width="2"/>')
        by = min(y(bar.open), y(bar.close))
        bh = max(2.0, abs(y(bar.open) - y(bar.close)))
        lines.append(f'<rect x="{cx - body_w / 2:.1f}" y="{by:.1f}" width="{body_w:.1f}" height="{bh:.1f}" fill="{color}" opacity="0.92"/>')
        if bar.index in (signal.sweep_index, signal.displacement_index):
            label = "S SWEEP" if bar.index == signal.sweep_index else "D C1"
            lines.append(text(cx, y(bar.high) - 12, label, 13, "#f8fafc", "middle"))

    target_color = "#f59e0b"
    sweep_color = "#a78bfa"
    stop_color = "#fb7185"
    if signal.target_level is not None:
        yt = y(signal.target_level)
        lines.append(f'<line x1="{left}" y1="{yt:.1f}" x2="{left + plot_w}" y2="{yt:.1f}" stroke="{target_color}" stroke-width="2" stroke-dasharray="8 5"/>')
        lines.append(text(left + plot_w - 4, yt - 7, f"TARGET prior {'HIGH' if signal.side == 'LONG' else 'LOW'} {signal.target_level:.3f}", 13, target_color, "end"))
    ys = y(signal.swept_level)
    lines.append(f'<line x1="{left}" y1="{ys:.1f}" x2="{left + plot_w}" y2="{ys:.1f}" stroke="{sweep_color}" stroke-width="1.5" stroke-dasharray="4 5"/>')
    lines.append(text(left + 5, ys - 7, f"swept {'LOW' if signal.side == 'LONG' else 'HIGH'} {signal.swept_level:.3f}", 13, sweep_color))
    ystop = y(stop)
    lines.append(f'<line x1="{left}" y1="{ystop:.1f}" x2="{left + plot_w}" y2="{ystop:.1f}" stroke="{stop_color}" stroke-width="1.5" stroke-dasharray="3 5"/>')
    lines.append(text(left + 5, ystop + 18, f"STOP beyond sweep {stop:.3f}", 13, stop_color))

    legend_y = height - 48
    lines += [
        text(left, legend_y, "Green = bullish candle", 13, "#22c55e"),
        text(left + 185, legend_y, "Red = bearish candle", 13, "#ef4444"),
        text(left + 370, legend_y, "Amber = target", 13, target_color),
        text(left + 530, legend_y, "Purple = swept liquidity", 13, sweep_color),
        '</svg>',
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    charts = RESULTS / "charts"
    charts.mkdir(exist_ok=True)
    minutes, hashes = load_minutes(DATA_DIR, LOAD_MONTHS)
    bars = aggregate_15m(minutes)
    all_signals: list[Signal] = []
    all_outcomes: list[Outcome] = []
    config_by_name = {config.name: config for config in CONFIGS}

    for config in CONFIGS:
        signals = detect_signals(bars, config, EVAL_START, EVAL_END)
        all_signals.extend(signals)
        for signal in signals:
            all_outcomes.append(simulate_with_config(signal, config, bars, minutes, entry_mode="immediate"))
            all_outcomes.append(simulate_with_config(signal, config, bars, minutes, entry_mode="after_three"))

    signal_rows = [_signal_row(signal, config_by_name[signal.config]) for signal in all_signals]
    outcome_rows = [_outcome_row(outcome) for outcome in all_outcomes]
    _write_csv(RESULTS / "signals.csv", signal_rows)
    _write_csv(RESULTS / "outcomes.csv", outcome_rows)

    immediate = {(outcome.config, outcome.side, outcome.sweep_index, "immediate"): outcome for outcome in all_outcomes if outcome.entry_mode == "immediate"}
    summary = {
        "dataset": {
            "symbol": "XAUUSD",
            "setup_timeframe": "15m",
            "path_timeframe": "1m",
            "evaluation_start_utc": EVAL_START.isoformat(),
            "evaluation_end_utc_exclusive": EVAL_END.isoformat(),
            "evaluation_months": EVAL_MONTHS,
            "warmup_months": ["2021-05"],
            "outcome_only_months": ["2021-12"],
            "minute_rows_loaded": len(minutes),
            "complete_15m_bars": len(bars),
            "input_sha256": hashes,
        },
        "contract": {
            "sweep": "LONG: low < prior confirmed swing low and close > it; SHORT: high > prior confirmed swing high and close < it",
            "swing_confirmation": "strict three-candle swing; pivot becomes available on the next completed candle",
            "displacement_timing": "exactly S+1; S+2 and S+3 are rejected, not silently accepted",
            "fvg": "wick-to-wick low(D) > high(S-1) for long / high(D) < low(S-1) for short",
            "target": "nearest prior confirmed opposite swing before the swept swing: HIGH before swept LOW for long, LOW before swept HIGH for short",
            "stop": "one source tick (0.001 XAU price unit) beyond sweep extreme",
            "entry": "close of the completed displacement candle",
            "horizon": "three following completed 15m bars; 1m OHLC orders exits, stop-first on same-minute ambiguity",
            "cost": "0: packaged XAU bars have no bid/ask/spread fields; no fee is invented",
            "post_candle": "small/hammer labels are descriptive only and cannot make a signal eligible",
        },
        "configs": {},
        "primary_monthly_immediate": _monthly_summary(all_signals, all_outcomes, "immediate"),
        "primary_after_three_entry": _monthly_summary(all_signals, all_outcomes, "after_three"),
        "zero_lookahead": {},
    }
    for config in CONFIGS:
        config_signals = [signal for signal in all_signals if signal.config == config.name]
        summary["configs"][config.name] = {
            "config": asdict(config),
            "signals_by_side": {
                side: sum(signal.side == side for signal in config_signals)
                for side in ("LONG", "SHORT")
            },
            "eligible_by_side": {
                side: sum(signal.side == side and signal.eligible for signal in config_signals)
                for side in ("LONG", "SHORT")
            },
            "immediate": _group_summary(config_signals, immediate, "immediate"),
            "after_three": _group_summary(
                config_signals,
                {(outcome.config, outcome.side, outcome.sweep_index, "after_three"): outcome for outcome in all_outcomes if outcome.entry_mode == "after_three"},
                "after_three",
            ),
        }

    # Keep a small exact ledger for the primary eligible rows so the Arabic
    # report can show real timestamps/prices without loading the multi-megabyte
    # CSV by hand.
    strict = CONFIGS[0]
    strict_full = detect_signals(bars, strict, EVAL_START, EVAL_END)
    summary["primary_eligible_examples"] = []
    for signal in strict_full:
        if not signal.eligible:
            continue
        outcome = immediate[(signal.config, signal.side, signal.sweep_index, "immediate")]
        summary["primary_eligible_examples"].append({
            "side": signal.side,
            "sweep_time": signal.sweep_time,
            "displacement_time": signal.displacement_time,
            "swept_level": signal.swept_level,
            "sweep_extreme": signal.sweep_extreme,
            "target_level": signal.target_level,
            "target_pivot_index": signal.target_pivot_index,
            "fvg": signal.displacement_fvg,
            "post_color": signal.post_candle_color,
            "post_small": signal.post_candle_small,
            "outcome": outcome.state,
            "entry_price": outcome.entry_price,
            "exit_price": outcome.exit_price,
            "r_multiple": outcome.r_multiple,
        })

    # Immutable causal replay check: the full run and a prefix must agree on
    # all signal decisions whose displacement has already closed.
    cut_time = datetime(2021, 10, 1, tzinfo=UTC)
    prefix_bars = [bar for bar in bars if bar.end <= cut_time]
    strict_prefix = detect_signals(prefix_bars, strict, EVAL_START, cut_time)
    full_prefix_core = [
        (item.sweep_time, signal_core_signature(item))
        for item in strict_full
        if _parse(item.displacement_time) is not None and _parse(item.displacement_time) < cut_time
    ]
    prefix_core = [
        (item.sweep_time, signal_core_signature(item))
        for item in strict_prefix
    ]
    summary["zero_lookahead"] = {
        "prefix_cutoff_utc": cut_time.isoformat(),
        "full_core_signals_before_cut": len(full_prefix_core),
        "prefix_core_signals": len(prefix_core),
        "prefix_core_identical": full_prefix_core == prefix_core,
        "future_outcome_data_is_not_used_for_signal_eligibility": True,
    }

    write_json(RESULTS / "summary.json", summary)
    write_report(summary, RESULTS / "REPORT_AR.md")
    (RESULTS / "data_hashes.txt").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in sorted(hashes.items())) + "\n",
        encoding="utf-8",
    )

    # Prefer real eligible strict examples; fall back only for the visual card,
    # never for the reported primary totals.
    strict_signals = [signal for signal in strict_full if signal.config == PRIMARY and signal.eligible]
    long_example = next((signal for signal in strict_signals if signal.side == "LONG"), None)
    short_example = next((signal for signal in strict_signals if signal.side == "SHORT"), None)
    fallback = [signal for signal in strict_full if signal.config == PRIMARY]
    if long_example is None:
        long_example = next((signal for signal in fallback if signal.side == "LONG"), None)
    if short_example is None:
        short_example = next((signal for signal in fallback if signal.side == "SHORT"), None)
    if long_example:
        render_example(charts / "long_example.svg", long_example, bars, strict)
    if short_example:
        render_example(charts / "short_example_2021.svg", short_example, bars, strict)

    # Compact console result for the coding-agent run log.
    print(json.dumps({
        "bars": len(bars),
        "minutes": len(minutes),
        "primary": summary["configs"][PRIMARY],
        "zero_lookahead": summary["zero_lookahead"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
