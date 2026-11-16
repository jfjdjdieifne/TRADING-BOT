#!/usr/bin/env python3
"""Full-calendar-2021 account replay with one concurrent position maximum.

This is a portfolio/account wrapper around the already-tested causal strategy
engine.  It does not alter the signal definition.  The primary account is:

* starting equity: $100;
* risk: 1% of current equity per taken trade (compounding);
* one position at a time, globally across LONG and SHORT;
* strict S+1 displacement + FVG + P80 range filter;
* gross prices only because the packaged OHLC source has no bid/ask/spread.

The 0.5% and 2% risk curves are reported as fixed sensitivities, never used to
select trades. December 2021 entries may settle in January 2022; January is
loaded as outcome-only and is disclosed separately.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from strategy import (
    Outcome,
    Signal,
    StrategyConfig,
    aggregate_15m,
    detect_signals,
    load_minutes,
    signal_core_signature,
    simulate_with_config,
)

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "smc_v4_multisleeve_package" / "data" / "XAUUSD_1m_histdata"
RESULTS = HERE / "results_2021_account"
CONFIG = StrategyConfig(
    name="STRICT_FVG_P80",
    require_fvg=True,
    large_mode="range_p80",
    large_percentile=80.0,
    min_body_fraction=0.60,
    stop_buffer=0.001,
    horizon_bars=3,
)
RISK_PCTS = (0.005, 0.01, 0.02)
BASE_RISK_PCT = 0.01
PROFILE_NOTE = ""
MAX_ACCEPTABLE_DD_PCT: float | None = None
SIGNAL_FILTER: Callable[[Signal], bool] | None = None
SIGNAL_FILTER_DESCRIPTION = "all eligible signals"


def _risk_label(risk_pct: float) -> str:
    """Stable human label that also works for sub-1% active profiles."""

    return f"{risk_pct * 100:.4f}".rstrip("0").rstrip(".") + "%"


def _curve_name(risk_pct: float) -> str:
    return f"{_risk_label(risk_pct)}_compounded"


def _base_risk_key() -> str:
    return f"{BASE_RISK_PCT:g}"


EVAL_START = datetime(2021, 1, 1, tzinfo=UTC)
EVAL_END = datetime(2022, 1, 1, tzinfo=UTC)
EVAL_MONTHS = [f"2021-{month:02d}" for month in range(1, 13)]
LOAD_MONTHS = ["2020-12", *EVAL_MONTHS, "2022-01"]


def _parse(text: str | None) -> datetime | None:
    return None if text is None else datetime.fromisoformat(text)


def _month(text: str | None) -> str | None:
    return None if text is None else text[:7]


def _week_label(value: datetime | None) -> str | None:
    if value is None:
        return None
    iso_year, iso_week, _ = value.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _week_start(value: datetime) -> datetime:
    return value - timedelta(days=value.weekday())


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


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def _trade_metrics(values: list[float]) -> dict:
    gains = sum(value for value in values if value > 0)
    losses = sum(-value for value in values if value < 0)
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return {
        "win_rate_pct": _round(100.0 * sum(value > 0 for value in values) / len(values), 4) if values else None,
        "profit_factor": _round(gains / losses, 6) if losses else ("inf" if gains else None),
        "max_drawdown_r": _round(max_drawdown, 6),
    }


def _outcome_row(outcome: Outcome) -> dict:
    return asdict(outcome)


def _candidate_row(signal: Signal, outcome: Outcome) -> dict:
    return {
        "config": signal.config,
        "side": signal.side,
        "sweep_index": signal.sweep_index,
        "displacement_index": signal.displacement_index,
        "sweep_time": signal.sweep_time,
        "entry_time": outcome.entry_time,
        "swept_level": signal.swept_level,
        "sweep_extreme": signal.sweep_extreme,
        "target_level": signal.target_level,
        "target_pivot_index": signal.target_pivot_index,
        "fvg": signal.displacement_fvg,
        "post_color": signal.post_candle_color,
        "post_small": signal.post_candle_small,
        "hypothetical_state": outcome.state,
        "hypothetical_r": outcome.r_multiple,
    }


def _risk_curve(taken: list[dict], risk_pct: float, start_equity: float = 100.0) -> dict:
    equity = start_equity
    peak = equity
    max_dd = 0.0
    max_dd_pct = 0.0
    total_r = 0.0
    for row in taken:
        risk_dollars = equity * risk_pct
        pnl = risk_dollars * float(row["r_multiple"])
        equity_before = equity
        equity += pnl
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)
        max_dd_pct = max(max_dd_pct, dd / peak if peak else 0.0)
        total_r += float(row["r_multiple"])
        row.setdefault("risk_dollars_by_rate", {})[f"{risk_pct:g}"] = _round(risk_dollars)
        row.setdefault("pnl_dollars_by_rate", {})[f"{risk_pct:g}"] = _round(pnl)
        row.setdefault("equity_before_by_rate", {})[f"{risk_pct:g}"] = _round(equity_before)
        row.setdefault("equity_after_by_rate", {})[f"{risk_pct:g}"] = _round(equity)
    rs = [float(row["r_multiple"]) for row in taken]
    return {
        "risk_pct": risk_pct,
        "start_equity": start_equity,
        "final_equity_after_all_2021_entries_closed": _round(equity, 4),
        "profit_dollars": _round(equity - start_equity, 4),
        "return_pct": _round((equity / start_equity - 1.0) * 100.0, 4),
        "trades": len(taken),
        "positive_trades": sum(value > 0 for value in rs),
        "negative_trades": sum(value < 0 for value in rs),
        "total_r": _round(total_r, 6),
        "mean_r": _round(statistics.fmean(rs), 6) if rs else None,
        **_trade_metrics(rs),
        "max_drawdown_dollars": _round(max_dd, 4),
        "max_drawdown_pct_of_peak": _round(max_dd_pct * 100.0, 4),
    }


def _summarise_period(
    period_labels: list[str],
    taken: list[dict],
    decisions: list[dict],
    *,
    label_key: str = "period_label",
    risk_key: str | None = None,
) -> list[dict]:
    """Summarise by entry period using the selected profile's base risk."""

    risk_key = _base_risk_key() if risk_key is None else risk_key
    rows: list[dict] = []
    running_equity = 100.0
    for label in period_labels:
        selected_decisions = [row for row in decisions if row[label_key] == label]
        selected = [row for row in taken if row[label_key] == label]
        rs = [float(row["r_multiple"]) for row in selected]
        pnl = [float(row["pnl_dollars_by_rate"][risk_key]) for row in selected]
        equity_before_values = [row["equity_before_by_rate"][risk_key] for row in selected]
        equity_after_values = [row["equity_after_by_rate"][risk_key] for row in selected]
        equity_before = equity_before_values[0] if equity_before_values else running_equity
        equity_after = equity_after_values[-1] if equity_after_values else running_equity
        running_equity = float(equity_after)
        rows.append({
            "period": label,
            "eligible_signals": len(selected_decisions),
            "taken_trades": len(selected),
            "concurrent_blocked": sum(row["decision"] == "CONCURRENT_BLOCKED" for row in selected_decisions),
            "same_time_conflicts": sum(row["decision"] == "SAME_TIME_CONFLICT" for row in selected_decisions),
            "target_hits": sum(row["state"] == "TARGET" for row in selected),
            "stop_hits": sum(row["state"] == "STOP" for row in selected),
            "time_exits": sum(row["state"] == "TIME" for row in selected),
            "positive_trades": sum(value > 0 for value in rs),
            "negative_trades": sum(value < 0 for value in rs),
            **_trade_metrics(rs),
            "sum_r": _round(sum(rs), 6),
            "profit_usd_at_base_risk": _round(sum(pnl), 6),
            "equity_before_period_at_base_risk": _round(equity_before, 6),
            "equity_after_period_at_base_risk": _round(equity_after, 6),
        })
    return rows


def _activity_metrics(taken: list[dict]) -> dict:
    """Report how often the profile actually trades, not just annual PnL."""

    daily_pnl: dict[str, float] = defaultdict(float)
    daily_counts: dict[str, int] = defaultdict(int)
    base_key = _base_risk_key()
    for row in taken:
        day = str(row["signal_time"])[:10]
        daily_counts[day] += 1
        daily_pnl[day] += float(row["pnl_dollars_by_rate"][base_key])
    calendar_days = (EVAL_END - EVAL_START).days
    total_pnl = sum(daily_pnl.values())
    return {
        "calendar_days": calendar_days,
        "taken_trades": len(taken),
        "trade_days": len(daily_counts),
        "trade_day_coverage_pct": _round(100.0 * len(daily_counts) / calendar_days, 4),
        "avg_trades_per_calendar_day": _round(len(taken) / calendar_days, 6),
        "avg_trades_per_trade_day": _round(len(taken) / len(daily_counts), 6) if daily_counts else None,
        "max_trades_in_one_day": max(daily_counts.values()) if daily_counts else 0,
        "positive_pnl_days": sum(value > 0 for value in daily_pnl.values()),
        "negative_pnl_days": sum(value < 0 for value in daily_pnl.values()),
        "flat_pnl_days": sum(value == 0 for value in daily_pnl.values()),
        "total_pnl_at_base_risk": _round(total_pnl, 6),
        "avg_pnl_per_calendar_day_at_base_risk": _round(total_pnl / calendar_days, 6),
        "avg_pnl_per_trade_day_at_base_risk": _round(total_pnl / len(daily_pnl), 6) if daily_pnl else None,
    }


def _audit_prefixes(
    bars,
    full_signals: list[Signal],
    signal_filter: Callable[[Signal], bool] | None = None,
) -> dict:
    """Compare every calendar-month prefix with the filtered full replay."""

    checks = []
    for month in range(2, 13):
        cutoff = datetime(2021, month, 1, tzinfo=UTC)
        prefix_bars = [bar for bar in bars if bar.end <= cutoff]
        prefix = detect_signals(prefix_bars, CONFIG, EVAL_START, cutoff)
        if signal_filter is not None:
            prefix = [signal for signal in prefix if signal_filter(signal)]
        full_core = [
            (signal.sweep_time, signal_core_signature(signal))
            for signal in full_signals
            if _parse(signal.displacement_time) is not None
            and _parse(signal.displacement_time) < cutoff
        ]
        prefix_core = [(signal.sweep_time, signal_core_signature(signal)) for signal in prefix]
        checks.append({
            "cutoff": cutoff.isoformat(),
            "full_signals_before_cutoff": len(full_core),
            "prefix_signals": len(prefix_core),
            "identical": full_core == prefix_core,
        })
    return {
        "checks": checks,
        "passed": sum(item["identical"] for item in checks),
        "total": len(checks),
        "all_identical": all(item["identical"] for item in checks),
        "outcomes_read_only_after_signal": True,
    }


def _make_report(summary: dict, path: Path) -> None:
    base = summary["account_curves"][_curve_name(BASE_RISK_PCT)]
    base_key = _base_risk_key()
    base_label = _risk_label(BASE_RISK_PCT)
    monthly = summary["monthly_entry_ledger"]
    weekly = summary["weekly_entry_ledger"]
    daily = summary["daily_entry_ledger"]
    trade_rows = summary["taken_trades"]
    lines = [
        "# حساب 100$ — replay كامل لسنة 2021",
        "",
        f"> هذا تقرير machine replay على XAUUSD الحقيقي الموجود في المستودع. النسخة الأساسية هي `{CONFIG.name}`، مع منع صفقتين مفتوحتين في الوقت نفسه.",
        "",
        "## عقد الحساب",
        "",
        "- الرصيد الابتدائي: **$100**.",
        f"- الحساب الأساسي: مخاطرة **{base_label} من الرصيد الحالي لكل صفقة مأخوذة**، مع compounding. المنحنيات الأخرى حساسية فقط.",
        f"- نتيجة الحساب الأساسية في هذا التقرير هي منحنى `{base_label}`؛ لا تُقرأ أرقام الدولار من دون هذا الافتراض.",
        "- الحد الأقصى: **صفقة واحدة عالمياً** بين LONG وSHORT. الإشارة التي تظهر أثناء صفقة مفتوحة تسجل `CONCURRENT_BLOCKED` ولا تدخل.",
        "- signal لا يظهر إلا بعد إغلاق displacement في `S+1`؛ لا يتم استعمال أي شمعة لاحقة لصناعة الإشارة.",
        "- target: أول swing معاكس مؤكد قبل الـ swept swing؛ HIGH سابق للـ swept LOW في LONG، وLOW سابق للـ swept HIGH في SHORT.",
        f"- فلتر النمط/الجلسة: `{SIGNAL_FILTER_DESCRIPTION}`.",
        "- لا bid/ask/spread في ملفات XAU المعبأة؛ لذلك النتائج gross ولا توجد رسوم مختلقة.",
        "- صفقات إشارتها في ديسمبر 2021 قد تغلق في يناير 2022؛ يناير محمّل outcome-only ومذكور صراحة.",
        "",
        "## النتيجة النهائية",
        "",
        "| curve | trades | win% | PF | positive | negative | total R | profit | final equity | return | max DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, curve in summary["account_curves"].items():
        dd = (
            "—"
            if curve["max_drawdown_dollars"] is None
            else f"${curve['max_drawdown_dollars']:.4f} ({curve['max_drawdown_pct_of_peak']:.2f}%)"
        )
        lines.append(
            f"| {name} | {curve['trades']} | {curve['win_rate_pct']} | {curve['profit_factor']} | {curve['positive_trades']} | {curve['negative_trades']} | "
            f"{curve['total_r']:.4f} | ${curve['profit_dollars']:.4f} | ${curve['final_equity_after_all_2021_entries_closed']:.4f} | "
            f"{curve['return_pct']:.2f}% | {dd} |"
        )
    activity = summary["activity_metrics"]
    lines += [
        "",
        "## النشاط اليومي",
        "",
        f"- أيام التداول التي ظهر فيها دخول مأخوذ: **{activity['trade_days']} من {activity['calendar_days']}** ({activity['trade_day_coverage_pct']:.2f}%).",
        f"- متوسط الصفقات المأخوذة: **{activity['avg_trades_per_calendar_day']:.3f} صفقة/يوم تقويمي**، و**{activity['avg_trades_per_trade_day']:.2f}** في يوم التداول النشط.",
        f"- أيام PnL الموجب/السالب: **{activity['positive_pnl_days']} / {activity['negative_pnl_days']}**. متوسط PnL اليومي عند {base_label}: **${activity['avg_pnl_per_calendar_day_at_base_risk']:.6f}**.",
        "- تكرار الدخول لا يعني ربحاً يومياً؛ التقرير يعرض الأيام السالبة أيضاً ولا يخفيها.",
        "",
        "## كل شهر — حسب شهر ظهور الإشارة",
        "",
        f"`profit_usd_at_base_risk` هو الربح المنسوب لشهر دخول الإشارة عند مخاطرة {base_label}. صفقة يمكن أن تغلق في الشهر التالي، وتفصيلها الكامل موجود في جدول الصفقات.",
        "",
        f"| الشهر | eligible | taken | blocked | targets | stops | time | win% | PF | DD R | sum R | profit $ at {base_label} | equity start | equity end |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in monthly:
        lines.append(
            f"| {row['period']} | {row['eligible_signals']} | {row['taken_trades']} | {row['concurrent_blocked']} | "
            f"{row['target_hits']} | {row['stop_hits']} | {row['time_exits']} | {row['win_rate_pct']} | {row['profit_factor']} | {row['max_drawdown_r']:.4f} | "
            f"{row['sum_r']:.4f} | ${row['profit_usd_at_base_risk']:.4f} | ${row['equity_before_period_at_base_risk']:.6f} | ${row['equity_after_period_at_base_risk']:.6f} |"
        )
    lines += [
        "",
        "## كل أسبوع بالتفصيل",
        "",
        f"| الأسبوع | eligible | taken | blocked | targets | stops | time | win% | PF | DD R | sum R | profit $ at {base_label} | equity start | equity end |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in weekly:
        lines.append(
            f"| {row['period']} | {row['eligible_signals']} | {row['taken_trades']} | {row['concurrent_blocked']} | "
            f"{row['target_hits']} | {row['stop_hits']} | {row['time_exits']} | {row['win_rate_pct']} | {row['profit_factor']} | {row['max_drawdown_r']:.4f} | {row['sum_r']:.4f} | "
            f"${row['profit_usd_at_base_risk']:.4f} | ${row['equity_before_period_at_base_risk']:.6f} | ${row['equity_after_period_at_base_risk']:.6f} |"
        )
    lines += [
        "",
        "## كل يوم فيه إشارة مأخوذة",
        "",
        f"`daily_summary.csv` يحتوي أيضاً الأيام الصفرية؛ الجدول التالي يعرض الأيام التي فيها صفقة واحدة على الأقل، عند مخاطرة {base_label}.",
        "",
        "| اليوم | eligible | taken | blocked | targets | stops | time | win% | PF | DD R | sum R | PnL $ | equity start | equity end |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in daily:
        if not row["taken_trades"]:
            continue
        lines.append(
            f"| {row['period']} | {row['eligible_signals']} | {row['taken_trades']} | {row['concurrent_blocked']} | "
            f"{row['target_hits']} | {row['stop_hits']} | {row['time_exits']} | {row['win_rate_pct']} | {row['profit_factor']} | {row['max_drawdown_r']:.4f} | {row['sum_r']:.4f} | "
            f"${row['profit_usd_at_base_risk']:.4f} | ${row['equity_before_period_at_base_risk']:.6f} | ${row['equity_after_period_at_base_risk']:.6f} |"
        )
    lines += [
        "",
        "## كل الصفقات المأخوذة",
        "",
        "| # | signal time | side | entry | exit | state | entry px | target | stop | R | risk $ | PnL $ | equity after |",
        "|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(trade_rows, 1):
        lines.append(
            f"| {index} | {row['signal_time']} | {row['side']} | {row['entry_time']} | {row['exit_time']} | {row['state']} | "
            f"{row['entry_price']:.3f} | {row['target_price']:.3f} | {row['stop_price']:.3f} | {row['r_multiple']:.4f} | "
            f"${row['risk_dollars_by_rate'][base_key]:.4f} | ${row['pnl_dollars_by_rate'][base_key]:.4f} | ${row['equity_after_by_rate'][base_key]:.4f} |"
        )
    lines += [
        "",
        "## فحص zero look-ahead",
        "",
        f"- prefix audits: **{summary['zero_lookahead']['passed']}/{summary['zero_lookahead']['total']}** identical.",
        "- كل prefix قورن مع full replay على قرار signal قبل cutoff، وليس على outcome المستقبلي.",
        "- `outcomes_read_only_after_signal = True`.",
        "",
        "## تنبيه",
        "",
        "- هذه سنة واحدة وبيانات أصل واحد؛ هذا ليس إثبات edge أو ضماناً لربح يومي.",
        f"- الحساب {base_label} هو افتراض معلن؛ لا يجوز قراءة رقم $100 من دون هذا الافتراض.",
        *([f"- {PROFILE_NOTE}"] if PROFILE_NOTE else []),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    minutes, hashes = load_minutes(DATA_DIR, LOAD_MONTHS)
    bars = aggregate_15m(minutes)
    detected_signals = detect_signals(bars, CONFIG, EVAL_START, EVAL_END)
    full_signals = [
        signal
        for signal in detected_signals
        if SIGNAL_FILTER is None or SIGNAL_FILTER(signal)
    ]
    eligible = [signal for signal in full_signals if signal.eligible]
    hypothetical: dict[tuple[str, str, int], Outcome] = {}
    for signal in eligible:
        hypothetical[(signal.side, signal.sweep_time, signal.sweep_index)] = simulate_with_config(
            signal, CONFIG, bars, minutes, entry_mode="immediate"
        )

    # First pass: mark all eligible signals chronologically.  Signals sharing a
    # timestamp are discarded as a group rather than resolving an opposite-side
    # tie by looking at the future or by tuning a side preference.
    ordered = sorted(eligible, key=lambda item: (item.displacement_time, item.side, item.sweep_index))
    by_entry_time: dict[str, list[Signal]] = defaultdict(list)
    for signal in ordered:
        outcome = hypothetical[(signal.side, signal.sweep_time, signal.sweep_index)]
        if outcome.entry_time is not None:
            by_entry_time[outcome.entry_time].append(signal)

    decisions: list[dict] = []
    taken: list[dict] = []
    next_free: datetime | None = None
    for signal in ordered:
        outcome = hypothetical[(signal.side, signal.sweep_time, signal.sweep_index)]
        entry_time = _parse(outcome.entry_time)
        period_label = _month(signal.sweep_time)
        week_label = _week_label(_parse(signal.sweep_time))
        decision = {
            "side": signal.side,
            "sweep_index": signal.sweep_index,
            "signal_time": signal.displacement_time,
            "entry_time": outcome.entry_time,
            "exit_time": outcome.exit_time,
            "period_label": period_label,
            "week_label": week_label,
            "day_label": signal.displacement_time[:10],
            "hypothetical_state": outcome.state,
            "decision": None,
        }
        if outcome.state not in {"TARGET", "STOP", "TIME"} or entry_time is None:
            decision["decision"] = "NO_EXECUTABLE_OUTCOME"
            decisions.append(decision)
            continue
        same_time = by_entry_time.get(outcome.entry_time or "", [])
        if len(same_time) > 1:
            decision["decision"] = "SAME_TIME_CONFLICT"
            decisions.append(decision)
            continue
        if next_free is not None and entry_time <= next_free:
            decision["decision"] = "CONCURRENT_BLOCKED"
            decisions.append(decision)
            continue
        decision["decision"] = "TAKEN"
        decisions.append(decision)
        taken.append({
            "signal_time": signal.displacement_time,
            "entry_time": outcome.entry_time,
            "exit_time": outcome.exit_time,
            "side": signal.side,
            "sweep_index": signal.sweep_index,
            "displacement_index": signal.displacement_index,
            "swept_level": signal.swept_level,
            "sweep_extreme": signal.sweep_extreme,
            "target_price": outcome.target_price,
            "stop_price": outcome.stop_price,
            "entry_price": outcome.entry_price,
            "exit_price": outcome.exit_price,
            "state": outcome.state,
            "r_multiple": float(outcome.r_multiple),
            "mfe_r": outcome.mfe_r,
            "mae_r": outcome.mae_r,
            "period_label": period_label,
            "week_label": week_label,
            "day_label": signal.displacement_time[:10],
            "exit_month": _month(outcome.exit_time),
        })
        next_free = _parse(outcome.exit_time)

    # Apply all risk curves to the same predeclared taken-trade sequence.
    account_curves: dict[str, dict] = {}
    for risk_pct in RISK_PCTS:
        account_curves[_curve_name(risk_pct)] = _risk_curve(taken, risk_pct)
    # Fixed $1 is included because it is the simplest non-compounding $100
    # interpretation and provides an audit-friendly dollar cross-check.
    fixed_profit = sum(float(row["r_multiple"]) for row in taken)
    account_curves["fixed_$1_per_trade"] = {
        "risk_pct": None,
        "start_equity": 100.0,
        "final_equity_after_all_2021_entries_closed": _round(100.0 + fixed_profit, 4),
        "profit_dollars": _round(fixed_profit, 4),
        "return_pct": _round(fixed_profit, 4),
        "trades": len(taken),
        "positive_trades": sum(float(row["r_multiple"]) > 0 for row in taken),
        "negative_trades": sum(float(row["r_multiple"]) < 0 for row in taken),
        "total_r": _round(fixed_profit, 6),
        "mean_r": _round(statistics.fmean([float(row["r_multiple"]) for row in taken]), 6) if taken else None,
        **_trade_metrics([float(row["r_multiple"]) for row in taken]),
        "max_drawdown_dollars": None,
        "max_drawdown_pct_of_peak": None,
    }

    monthly = _summarise_period(EVAL_MONTHS, taken, decisions)
    week_starts = []
    cursor = _week_start(EVAL_START)
    while cursor < EVAL_END:
        week_starts.append(cursor.strftime("%G-W%V"))
        cursor += timedelta(days=7)
    weekly = _summarise_period(week_starts, taken, decisions, label_key="week_label")
    day_labels = []
    cursor = EVAL_START
    while cursor < EVAL_END:
        day_labels.append(cursor.strftime("%Y-%m-%d"))
        cursor += timedelta(days=1)
    daily = _summarise_period(day_labels, taken, decisions, label_key="day_label")

    decisions_rows = []
    for row in decisions:
        decision_row = dict(row)
        decision_row["period_label"] = row["period_label"]
        decisions_rows.append(decision_row)
    candidate_rows = []
    for signal in full_signals:
        if signal.eligible:
            outcome = hypothetical[(signal.side, signal.sweep_time, signal.sweep_index)]
            candidate_rows.append(_candidate_row(signal, outcome))

    zero_lookahead = _audit_prefixes(bars, full_signals, SIGNAL_FILTER)
    taken_count = len(taken)
    account_summary = {
        "dataset": {
            "symbol": "XAUUSD",
            "setup_timeframe": "15m",
            "path_timeframe": "1m",
            "evaluation_start_utc": EVAL_START.isoformat(),
            "evaluation_end_utc_exclusive": EVAL_END.isoformat(),
            "evaluation_months": EVAL_MONTHS,
            "warmup_months": ["2020-12"],
            "outcome_only_months": ["2022-01"],
            "minutes_loaded": len(minutes),
            "complete_15m_bars": len(bars),
            "input_sha256": hashes,
        },
        "account_contract": {
            "starting_equity": 100.0,
            "base_risk_pct": BASE_RISK_PCT,
            "risk_curves": RISK_PCTS,
            "max_acceptable_drawdown_pct": MAX_ACCEPTABLE_DD_PCT,
            "profile_note": PROFILE_NOTE,
            "signal_filter": SIGNAL_FILTER_DESCRIPTION,
            "max_concurrent_positions": 1,
            "same_timestamp_policy": "discard all candidates sharing an entry timestamp",
            "target_definition": "first prior confirmed opposite swing before the swept swing: HIGH before swept LOW for long, LOW before swept HIGH for short",
            "signal_contract": asdict(CONFIG),
            "no_fees": True,
            "no_lookahead": True,
        },
        "candidate_counts": {
            "all_signals_before_profile_filter": len(detected_signals),
            "all_signals": len(full_signals),
            "eligible_signals": len(eligible),
            "taken": taken_count,
            "concurrent_blocked": sum(row["decision"] == "CONCURRENT_BLOCKED" for row in decisions),
            "same_time_conflicts": sum(row["decision"] == "SAME_TIME_CONFLICT" for row in decisions),
            "no_executable_outcome": sum(row["decision"] == "NO_EXECUTABLE_OUTCOME" for row in decisions),
        },
        "account_curves": account_curves,
        "activity_metrics": _activity_metrics(taken),
        "monthly_entry_ledger": monthly,
        "weekly_entry_ledger": weekly,
        "daily_entry_ledger": daily,
        "taken_trades": taken,
        "zero_lookahead": zero_lookahead,
    }

    _write_csv(RESULTS / "eligible_candidates.csv", candidate_rows)
    _write_csv(RESULTS / "portfolio_decisions.csv", decisions_rows)
    _write_csv(RESULTS / "taken_trades.csv", taken)
    _write_csv(RESULTS / "monthly_summary.csv", monthly)
    _write_csv(RESULTS / "weekly_summary.csv", weekly)
    _write_csv(RESULTS / "daily_summary.csv", daily)
    (RESULTS / "data_hashes.txt").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in sorted(hashes.items())) + "\n",
        encoding="utf-8",
    )
    (RESULTS / "summary.json").write_text(json.dumps(account_summary, indent=2, sort_keys=True), encoding="utf-8")
    _make_report(account_summary, RESULTS / "ACCOUNT_REPORT_AR.md")
    print(json.dumps({
        "candidate_counts": account_summary["candidate_counts"],
        "account_curves": account_curves,
        "zero_lookahead": zero_lookahead,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
