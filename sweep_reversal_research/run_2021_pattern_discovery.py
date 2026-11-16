#!/usr/bin/env python3
"""Descriptive, causal pattern ledger for the 2021 instruments.

This script does not tune a live rule from future outcomes. It records every
eligible active-profile outcome for XAUUSD, NSXUSD, and BTCUSD, then groups the
already closed outcomes by month, ISO week, day, weekday, UTC session, hour,
and side. XAU/NSX use native 1-minute observations; BTC uses native 5-minute
observations assembled into exact three-source-bar 15-minute setup bars. The
resulting session profile is a research hypothesis and must still be tested on
an unseen period before live use.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from strategy import (
    StrategyConfig,
    aggregate_15m,
    detect_signals,
    load_ohlc,
    signal_core_signature,
    simulate_with_config,
)

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE.parent / "smc_v4_multisleeve_package" / "data"
RESULTS = HERE / "results_2021_pattern_discovery"
START = datetime(2021, 1, 1, tzinfo=UTC)
END = datetime(2022, 1, 1, tzinfo=UTC)
MONTHS = ["2020-12", *[f"2021-{month:02d}" for month in range(1, 13)], "2022-01"]
ASSET_CONFIG = {
    "XAUUSD": {
        "data_dir": DATA_ROOT / "XAUUSD_1m_histdata",
        "files": [f"{month}.csv.gz" for month in MONTHS],
        "source_timeframe": "1m",
        "source_interval_minutes": 1,
    },
    "NSXUSD": {
        "data_dir": DATA_ROOT / "NSXUSD_1m_histdata",
        "files": [f"{month}.csv.gz" for month in MONTHS],
        "source_timeframe": "1m",
        "source_interval_minutes": 1,
    },
    "BTCUSD": {
        "data_dir": DATA_ROOT / "BTCUSD_5m",
        "files": ["2020.csv.gz", "2021.csv.gz", "2022.csv.gz"],
        "source_timeframe": "5m",
        "source_interval_minutes": 5,
    },
}
CONFIG = StrategyConfig(
    name="PATTERN_DIRECTION_NO_SIZE_NO_FVG",
    require_fvg=False,
    large_mode="none",
    min_body_fraction=0.0,
    stop_buffer=0.001,
    horizon_bars=3,
)


def utc_session(hour: int) -> str:
    if 0 <= hour < 7:
        return "ASIA_00_07"
    if 7 <= hour < 13:
        return "LONDON_07_13"
    if 13 <= hour < 20:
        return "NY_13_20"
    return "LATE_20_24"


def half(month: str) -> str:
    return "H1_JAN_JUN" if month <= "2021-06" else "H2_JUL_DEC"


def write_csv(path: Path, rows: list[dict]) -> None:
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


def _max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return max_drawdown


def stats(rows: list[dict]) -> dict:
    ordered = sorted(rows, key=lambda row: (row["signal_time"], row["side"], row["sweep_index"]))
    values = [float(row["r_multiple"]) for row in ordered]
    gains = sum(value for value in values if value > 0)
    losses = sum(-value for value in values if value < 0)
    return {
        "n": len(values),
        "win_rate_pct": round(100.0 * sum(value > 0 for value in values) / len(values), 4) if values else None,
        "sum_r": round(sum(values), 6),
        "mean_r": round(sum(values) / len(values), 6) if values else None,
        "profit_factor": round(gains / losses, 6) if losses else (None if not gains else "inf"),
        "max_drawdown_r": round(_max_drawdown(values), 6),
        "positive": sum(value > 0 for value in values),
        "negative": sum(value < 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "target": sum(row["state"] == "TARGET" for row in ordered),
        "stop": sum(row["state"] == "STOP" for row in ordered),
        "time": sum(row["state"] == "TIME" for row in ordered),
    }


def prefix_audit(bars, full_signals: list) -> dict:
    checks = []
    for month in range(2, 13):
        cutoff = datetime(2021, month, 1, tzinfo=UTC)
        prefix_bars = [bar for bar in bars if bar.end <= cutoff]
        prefix_signals = detect_signals(prefix_bars, CONFIG, START, cutoff)
        full_core = [
            (signal.sweep_time, signal_core_signature(signal))
            for signal in full_signals
            if datetime.fromisoformat(signal.displacement_time) < cutoff
        ]
        prefix_core = [(signal.sweep_time, signal_core_signature(signal)) for signal in prefix_signals]
        checks.append({"cutoff": cutoff.isoformat(), "identical": full_core == prefix_core})
    return {
        "passed": sum(item["identical"] for item in checks),
        "total": len(checks),
        "all_identical": all(item["identical"] for item in checks),
        "checks": checks,
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    hashes: dict[str, str] = {}
    asset_counts: dict[str, dict] = {}

    for asset, asset_config in ASSET_CONFIG.items():
        minutes, asset_hashes = load_ohlc(asset_config["data_dir"], asset_config["files"])
        hashes.update({f"{asset}/{name}": digest for name, digest in asset_hashes.items()})
        bars = aggregate_15m(minutes, asset_config["source_interval_minutes"])
        signals = detect_signals(bars, CONFIG, START, END)
        eligible = [signal for signal in signals if signal.eligible]
        executable = 0
        for signal in eligible:
            outcome = simulate_with_config(signal, CONFIG, bars, minutes, entry_mode="immediate")
            if outcome.state not in {"TARGET", "STOP", "TIME"} or outcome.entry_time is None:
                continue
            executable += 1
            signal_time = datetime.fromisoformat(signal.displacement_time)
            month = signal_time.strftime("%Y-%m")
            all_rows.append({
                "asset": asset,
                "side": signal.side,
                "signal_time": signal.displacement_time,
                "entry_time": outcome.entry_time,
                "exit_time": outcome.exit_time,
                "state": outcome.state,
                "r_multiple": outcome.r_multiple,
                "source_timeframe": asset_config["source_timeframe"],
                "setup_timeframe": "15m",
                "session": utc_session(signal_time.hour),
                "weekday": signal_time.strftime("%a"),
                "hour_utc": signal_time.hour,
                "month": month,
                "iso_week": signal_time.strftime("%G-W%V"),
                "day": signal_time.strftime("%Y-%m-%d"),
                "half": half(month),
                "sweep_index": signal.sweep_index,
                "target_level": signal.target_level,
            })
        asset_counts[asset] = {
            "source_timeframe": asset_config["source_timeframe"],
            "setup_timeframe": "15m",
            "minutes_or_source_bars": len(minutes),
            "complete_15m_bars": len(bars),
            "all_signals": len(signals),
            "eligible_signals": len(eligible),
            "executable_outcomes": executable,
            "zero_lookahead": prefix_audit(bars, signals),
        }

    group_rows: list[dict] = []

    def add_group(group_type: str, key_names: tuple[str, ...], period: str, rows: list[dict]) -> None:
        if not rows:
            return
        values = {name: rows[0][name] for name in key_names}
        group_rows.append({"group_type": group_type, **values, "period": period, **stats(rows)})

    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in all_rows:
        groups[(row["asset"], row["side"], row["session"])].append(row)
    for key, rows in sorted(groups.items()):
        add_group("asset_side_session", ("asset", "side", "session"), "FULL_2021", rows)
        for period in ("H1_JAN_JUN", "H2_JUL_DEC"):
            add_group("asset_side_session", ("asset", "side", "session"), period, [row for row in rows if row["half"] == period])

    weekday_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in all_rows:
        weekday_groups[(row["asset"], row["side"], row["session"], row["weekday"])].append(row)
    for key, rows in sorted(weekday_groups.items()):
        add_group("asset_side_session_weekday", ("asset", "side", "session", "weekday"), "FULL_2021", rows)
        for period in ("H1_JAN_JUN", "H2_JUL_DEC"):
            add_group("asset_side_session_weekday", ("asset", "side", "session", "weekday"), period, [row for row in rows if row["half"] == period])

    # Explicit breakdowns requested by the research contract. These are raw
    # candidate outcomes (not an account portfolio); the one-position account
    # effect is tested separately by the holdout runner.
    breakdown_rows: list[dict] = []
    dimensions = ("month", "iso_week", "day", "weekday", "session", "hour_utc", "side")
    for asset in sorted(ASSET_CONFIG):
        asset_rows = [row for row in all_rows if row["asset"] == asset]
        breakdown_rows.append({"asset": asset, "dimension": "asset_total", "bucket": "ALL", **stats(asset_rows)})
        for dimension in dimensions:
            buckets: dict[str, list[dict]] = defaultdict(list)
            for row in asset_rows:
                buckets[str(row[dimension])].append(row)
            for bucket, rows in sorted(buckets.items()):
                breakdown_rows.append({"asset": asset, "dimension": dimension, "bucket": bucket, **stats(rows)})

    write_csv(RESULTS / "candidate_outcomes.csv", all_rows)
    write_csv(RESULTS / "pattern_summary.csv", group_rows)
    write_csv(RESULTS / "breakdown_summary.csv", breakdown_rows)
    (RESULTS / "data_hashes.txt").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in sorted(hashes.items())) + "\n",
        encoding="utf-8",
    )

    def find(asset: str, side: str, session: str, period: str) -> dict:
        for row in group_rows:
            if (
                row["group_type"] == "asset_side_session"
                and row["asset"] == asset
                and row["side"] == side
                and row["session"] == session
                and row["period"] == period
            ):
                return row
        return stats([])

    report_lines = [
        "# Pattern discovery — XAUUSD وNSXUSD وBTCUSD — 2021",
        "",
        "> هذا تحليل وصفي على outcomes أُغلقت بعد الإشارة. لا يستخدم نتيجة مستقبلية لصناعة signal، لكنه لا يحوّل اختيار pattern من نفس السنة إلى إثبات out-of-sample.",
        "",
        "## العقد",
        "",
        "- active causal profile: sweep + displacement `S+1` الصحيح + أول target سابق؛ FVG وP80 غير مطلوبين لزيادة العينة.",
        "- الجلسات كلها UTC: Asia `00-07`، London `07-13`، New York `13-20`، Late `20-24`.",
        "- XAUUSD وNSXUSD يستخدمان مصدر 1m؛ BTCUSD يستخدم مصدره الأصلي 5m، وتُبنى منه شمعة setup 15m من ثلاث شموع 5m مكتملة. لذلك BTC ليس مقارنة tick-for-tick مع 1m.",
        "- كل صف في `candidate_outcomes.csv` هو outcome مستقل مرشح؛ أرقام الحساب ذي الصفقة الواحدة موجودة في تقرير holdout.",
        "- `breakdown_summary.csv` يخرج n وwin rate وtotal/mean R وprofit factor وmax drawdown R حسب الشهر والأسبوع واليوم واليوم الأسبوعي والجلسة والساعة والاتجاه.",
        "- لكل أصل يوجد prefix audit في `summary.json`؛ لا يكفي أن يكون الحساب causal على XAU فقط.",

        "",
        "## الأنماط ذات الاستقرار النسبي بين نصفي السنة",
        "",
        "| الأصل | الاتجاه | الجلسة | H1 n | H1 sum R | H1 PF | H1 DD R | H2 n | H2 sum R | H2 PF | H2 DD R | FULL n | FULL sum R | FULL PF | FULL DD R |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    selected = [
        ("XAUUSD", "SHORT", "LONDON_07_13"),
        ("XAUUSD", "LONG", "NY_13_20"),
        ("NSXUSD", "SHORT", "LONDON_07_13"),
        ("BTCUSD", "SHORT", "LONDON_07_13"),
        ("BTCUSD", "LONG", "NY_13_20"),
        ("XAUUSD", "LONG", "LATE_20_24"),
    ]
    for asset, side, session in selected:
        h1 = find(asset, side, session, "H1_JAN_JUN")
        h2 = find(asset, side, session, "H2_JUL_DEC")
        full = find(asset, side, session, "FULL_2021")
        report_lines.append(
            f"| {asset} | {side} | {session} | {h1['n']} | {h1['sum_r']:.4f} | {h1['profit_factor']} | {h1['max_drawdown_r']:.4f} | "
            f"{h2['n']} | {h2['sum_r']:.4f} | {h2['profit_factor']} | {h2['max_drawdown_r']:.4f} | "
            f"{full['n']} | {full['sum_r']:.4f} | {full['profit_factor']} | {full['max_drawdown_r']:.4f} |"
        )
    report_lines += [
        "",
        "## القراءة",
        "",
        "- XAUUSD SHORT في London وLONG في New York كانا موجبين في H1 وH2 داخل هذه العينة، ولذلك استُخدما كفرضية `run_2021_session_profile.py` لا كـ edge مثبت.",
        "- الجدول يقارن BTCUSD أيضاً، لكن اختلاف المصدر 5m مقابل 1m يفرض قراءة BTC كاختبار cadence مستقل، لا كترتيب مباشر بين الأصول.",
        "- NSXUSD London وXAUUSD LONG في Late ظهرا سالبين في النصفين؛ لم أضفهما إلى profile الرابح.",
        "- هذه ليست ضماناً أن السوق يكرر النمط مستقبلاً؛ تقرير `results_session_oos/` يختبر الفرضية المجمدة على 2022-2025.",
        "- prefix audits لكل الأصول الثلاثة يجب أن تكون 11/11؛ هذا يثبت replay السببي، لا يثبت pattern edge.",
        "",
        "## الملفات",
        "",
        "- `candidate_outcomes.csv`: كل outcome مؤهل مع الأصل والاتجاه والجلسة والساعة واليوم.",
        "- `pattern_summary.csv`: تجميع FULL/H1/H2 والجلسة واليوم للأصل والاتجاه.",
        "- `breakdown_summary.csv`: جداول الشهر/الأسبوع/اليوم/weekday/session/hour/side مع PF وDD.",
        "- `data_hashes.txt`: بصمات ملفات XAU وNSX وBTC المقروءة.",
        "",
    ]
    (RESULTS / "PATTERN_REPORT_AR.md").write_text("\n".join(report_lines), encoding="utf-8")
    summary = {
        "dataset": {
            "evaluation_start_utc": START.isoformat(),
            "evaluation_end_utc_exclusive": END.isoformat(),
            "warmup_months": ["2020-12"],
            "outcome_only_months": ["2022-01"],
            "sessions_utc": {
                "ASIA_00_07": "00:00-06:59",
                "LONDON_07_13": "07:00-12:59",
                "NY_13_20": "13:00-19:59",
                "LATE_20_24": "20:00-23:59",
            },
            "source_contracts": {
                asset: {
                    "source_timeframe": config["source_timeframe"],
                    "setup_timeframe": "15m",
                    "source_interval_minutes": config["source_interval_minutes"],
                }
                for asset, config in ASSET_CONFIG.items()
            },
            "input_sha256": hashes,
        },
        "config": {"name": CONFIG.name, "require_fvg": CONFIG.require_fvg, "large_mode": CONFIG.large_mode, "min_body_fraction": CONFIG.min_body_fraction},
        "asset_counts": asset_counts,
        "candidate_outcomes": len(all_rows),
        "selected_hypothesis": [
            "XAUUSD SHORT LONDON_07_13",
            "XAUUSD LONG NY_13_20",
        ],
        "zero_lookahead_scope": "signal decisions and outcome timestamps are causal; pattern selection remains a research hypothesis requiring holdout validation",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
