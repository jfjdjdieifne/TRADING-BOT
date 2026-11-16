#!/usr/bin/env python3
"""Holdout test for the fixed 2021 session hypothesis.

The hypothesis is frozen from the 2021 pattern ledger:
XAUUSD SHORT in UTC London and XAUUSD LONG in UTC New York.  This runner does
not re-select sessions from 2022-2025, so those years are a genuine holdout for
that fixed rule.  It loads the complete pre-holdout history used to initialise
the first-target contract, then reports gross R because the source has no
spread/fee data.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from strategy import StrategyConfig, aggregate_15m, detect_signals, load_ohlc, simulate_with_config

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE.parent / "smc_v4_multisleeve_package" / "data"
RESULTS = HERE / "results_session_oos"
START = datetime(2022, 1, 1, tzinfo=UTC)
END = datetime(2026, 1, 1, tzinfo=UTC)
MONTHS = [
    "2020-12",
    *[f"2021-{month:02d}" for month in range(1, 13)],
    *[f"{year}-{month:02d}" for year in range(2022, 2026) for month in range(1, 13)],
    "2026-01",
]
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
        "files": ["2020.csv.gz", "2021.csv.gz", "2022.csv.gz", "2023.csv.gz", "2024.csv.gz", "2025.csv.gz", "2026.csv.gz"],
        "source_timeframe": "5m",
        "source_interval_minutes": 5,
    },
}
CONFIG = StrategyConfig(
    name="SESSION_HYPOTHESIS_HOLDOUT",
    require_fvg=False,
    large_mode="none",
    min_body_fraction=0.0,
    stop_buffer=0.001,
    horizon_bars=3,
)


def session_filter(signal) -> bool:
    value = datetime.fromisoformat(signal.displacement_time)
    return (
        signal.side == "SHORT" and 7 <= value.hour < 13
    ) or (
        signal.side == "LONG" and 13 <= value.hour < 20
    )


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def risk_curve(rows: list[dict], risk_pct: float) -> dict:
    equity = 100.0
    peak = equity
    max_dd = 0.0
    for row in sorted(rows, key=lambda item: (item["entry_time"], item["signal_time"])):
        equity += equity * risk_pct * float(row["r_multiple"])
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)
    return {
        "risk_pct": risk_pct,
        "final_equity": round(equity, 6),
        "profit_dollars": round(equity - 100.0, 6),
        "max_drawdown_pct_of_peak": round(max_dd * 100.0, 6),
    }


def stats(rows: list[dict]) -> dict:
    ordered = sorted(rows, key=lambda item: (item["entry_time"], item["signal_time"]))
    values = [float(row["r_multiple"]) for row in ordered]
    gains = sum(value for value in values if value > 0)
    losses = sum(-value for value in values if value < 0)
    return {
        "trades": len(values),
        "win_rate_pct": round(100.0 * sum(value > 0 for value in values) / len(values), 6) if values else None,
        "sum_r": round(sum(values), 6),
        "mean_r": round(sum(values) / len(values), 6) if values else None,
        "profit_factor": round(gains / losses, 6) if losses else (None if not gains else "inf"),
        "max_drawdown_r": round(max_drawdown(values), 6),
        "positive": sum(value > 0 for value in values),
        "negative": sum(value < 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "risk_0_15_pct": risk_curve(ordered, 0.0015),
        "risk_0_30_pct": risk_curve(ordered, 0.003),
        "risk_0_50_pct": risk_curve(ordered, 0.005),
    }


def one_position(rows: list[dict]) -> tuple[list[dict], int, int]:
    ordered = sorted(rows, key=lambda row: (row["entry_time"], row["side"], row["signal_time"]))
    by_entry_time: dict[str, list[dict]] = defaultdict(list)
    for row in ordered:
        by_entry_time[row["entry_time"]].append(row)
    portfolio: list[dict] = []
    next_free: datetime | None = None
    blocked = 0
    same_time_conflicts = 0
    for row in ordered:
        if len(by_entry_time[row["entry_time"]]) > 1:
            same_time_conflicts += 1
            continue
        entry = datetime.fromisoformat(row["entry_time"])
        exit_time = datetime.fromisoformat(row["exit_time"])
        if next_free is not None and entry <= next_free:
            blocked += 1
            continue
        portfolio.append(row)
        next_free = exit_time
    return portfolio, blocked, same_time_conflicts


def period_breakdown(asset: str, scope: str, rows: list[dict]) -> list[dict]:
    output: list[dict] = []
    for dimension in ("month", "iso_week", "day"):
        buckets: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            value = datetime.fromisoformat(row["signal_time"])
            if dimension == "month":
                label = value.strftime("%Y-%m")
            elif dimension == "iso_week":
                label = value.strftime("%G-W%V")
            else:
                label = value.strftime("%Y-%m-%d")
            buckets[label].append(row)
        for label, grouped in sorted(buckets.items()):
            metrics = stats(grouped)
            metrics = {key: value for key, value in metrics.items() if not key.startswith("risk_")}
            output.append({"asset": asset, "scope": scope, "dimension": dimension, "period": label, **metrics})
    return output


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


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    asset_summary: dict[str, dict] = {}
    yearly_rows: list[dict] = []
    period_rows: list[dict] = []

    all_outcomes: list[dict] = []
    for asset, asset_config in ASSET_CONFIG.items():
        minutes, asset_hashes = load_ohlc(asset_config["data_dir"], asset_config["files"])
        hashes.update({f"{asset}/{name}": digest for name, digest in asset_hashes.items()})
        bars = aggregate_15m(minutes, asset_config["source_interval_minutes"])
        signals = detect_signals(bars, CONFIG, START, END)
        eligible = [signal for signal in signals if signal.eligible and session_filter(signal)]
        outcomes: list[dict] = []
        for signal in eligible:
            outcome = simulate_with_config(signal, CONFIG, bars, minutes, entry_mode="immediate")
            if outcome.state not in {"TARGET", "STOP", "TIME"} or outcome.entry_time is None:
                continue
            signal_time = datetime.fromisoformat(signal.displacement_time)
            outcomes.append({
                "asset": asset,
                "source_timeframe": asset_config["source_timeframe"],
                "setup_timeframe": "15m",
                "side": signal.side,
                "signal_time": signal.displacement_time,
                "entry_time": outcome.entry_time,
                "exit_time": outcome.exit_time,
                "state": outcome.state,
                "r_multiple": outcome.r_multiple,
                "year": signal_time.year,
            })

        portfolio, blocked, same_time_conflicts = one_position(outcomes)
        period_rows.extend(period_breakdown(asset, "raw_candidates", outcomes))
        period_rows.extend(period_breakdown(asset, "one_position_portfolio", portfolio))

        for year in range(2022, 2026):
            raw = [row for row in outcomes if row["year"] == year]
            taken = [row for row in portfolio if row["year"] == year]
            yearly_rows.append({"asset": asset, "year": year, "scope": "raw_candidates", **stats(raw)})
            yearly_rows.append({"asset": asset, "year": year, "scope": "one_position_portfolio", **stats(taken)})

        all_outcomes.extend(outcomes)
        asset_summary[asset] = {
            "source_timeframe": asset_config["source_timeframe"],
            "setup_timeframe": "15m",
            "minutes_or_source_bars": len(minutes),
            "complete_15m_bars": len(bars),
            "all_signals": len(signals),
            "filtered_eligible": len(eligible),
            "raw_executable": len(outcomes),
            "raw": stats(outcomes),
            "one_position_portfolio": stats(portfolio),
            "concurrent_blocked": blocked,
            "same_time_conflicts": same_time_conflicts,
        }

    combined_portfolio, combined_blocked, combined_same_time = one_position(all_outcomes)
    period_rows.extend(period_breakdown("ALL_ASSETS", "raw_candidates", all_outcomes))
    period_rows.extend(period_breakdown("ALL_ASSETS", "one_position_portfolio", combined_portfolio))
    for year in range(2022, 2026):
        raw = [row for row in all_outcomes if row["year"] == year]
        taken = [row for row in combined_portfolio if row["year"] == year]
        yearly_rows.append({"asset": "ALL_ASSETS", "year": year, "scope": "raw_candidates", **stats(raw)})
        yearly_rows.append({"asset": "ALL_ASSETS", "year": year, "scope": "one_position_portfolio", **stats(taken)})
    asset_summary["ALL_ASSETS"] = {
        "raw": stats(all_outcomes),
        "one_position_portfolio": stats(combined_portfolio),
        "raw_executable": len(all_outcomes),
        "concurrent_blocked": combined_blocked,
        "same_time_conflicts": combined_same_time,
        "contract": "one global position across XAUUSD, NSXUSD, BTCUSD",
    }

    write_csv(RESULTS / "yearly_summary.csv", yearly_rows)
    write_csv(RESULTS / "period_summary.csv", period_rows)
    (RESULTS / "data_hashes.txt").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in sorted(hashes.items())) + "\n",
        encoding="utf-8",
    )
    summary = {
        "evaluation_start_utc": START.isoformat(),
        "evaluation_end_utc_exclusive": END.isoformat(),
        "warmup_periods": {
            "XAUUSD_NSXUSD": ["2020-12", "all 2021 months"],
            "BTCUSD": ["2020.csv.gz", "2021.csv.gz"],
        },
        "outcome_only_months": ["2026-01"],
        "fixed_hypothesis": "side/session rule frozen from 2021: SHORT London UTC 07-12 plus LONG New York UTC 13-19; applied unchanged to each asset",
        "source_contracts": {
            asset: {
                "source_timeframe": config["source_timeframe"],
                "setup_timeframe": "15m",
                "source_interval_minutes": config["source_interval_minutes"],
            }
            for asset, config in ASSET_CONFIG.items()
        },
        "assets": asset_summary,
        "input_sha256": hashes,
        "cost_model": "gross; source has no bid/ask/commission fields",
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    xau = asset_summary["XAUUSD"]
    nsx = asset_summary["NSXUSD"]
    report = [
        "# Holdout test — fixed session hypothesis 2022–2025",
        "",
        "> قاعدة الجلسات لم تُعدّل أثناء فترة الاختبار: SHORT في London UTC وLONG في New York UTC، كما استُخرجت من ledger 2021. طُبقت على XAUUSD وNSXUSD وBTCUSD دون إعادة اختيار. هذه النتيجة holdout وليست ضماناً للمستقبل.",
        "",
        "> BTCUSD مقروء من مصدر 5m الأصلي، وبُنيت منه شموع setup 15m من ثلاث شموع 5m مكتملة؛ XAU/NSX مصدرهما 1m. لا يصح تفسير اختلاف cadence كأفضلية اقتصادية مباشرة.",
        "",
        "- `raw` يعني كل outcome المرشح، وقد تتداخل مراكزُه؛ `taken` يفرض صفقة واحدة عالمياً داخل الأصل، و`ALL_ASSETS` يفرض صفقة واحدة عبر الأصول الثلاثة.",
        "- `DD@0.3%` حساسية compounding فقط. المخاطرة نسبة من equity وليست دولاراً ثابتاً؛ لا توجد مواصفات contract/fees في البيانات.",
        "- `period_summary.csv` يخرج breakdown حسب شهر/ISO week/يوم، مع raw وone-position وwin rate وPF وDD R.",

        "",
        "| الأصل | raw n | raw win% | raw sum R | raw PF | raw DD R | taken n | taken win% | taken sum R | taken PF | taken DD R | DD@0.3% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for asset in ("XAUUSD", "NSXUSD", "BTCUSD", "ALL_ASSETS"):
        value = asset_summary[asset]
        raw = value["raw"]
        taken = value["one_position_portfolio"]
        report.append(
            f"| {asset} | {raw['trades']} | {raw['win_rate_pct']:.2f} | {raw['sum_r']:.4f} | {raw['profit_factor']} | {raw['max_drawdown_r']:.4f} | "
            f"{taken['trades']} | {taken['win_rate_pct']:.2f} | {taken['sum_r']:.4f} | {taken['profit_factor']} | {taken['max_drawdown_r']:.4f} | "
            f"{taken['risk_0_30_pct']['max_drawdown_pct_of_peak']:.4f}% |"
        )
    report += [
        "",
        "## حسب السنة — raw candidates",
        "",
        "| الأصل | السنة | trades | win% | sum R | mean R | PF | DD R |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in yearly_rows:
        if row["scope"] == "raw_candidates":
            report.append(f"| {row['asset']} | {row['year']} | {row['trades']} | {row['win_rate_pct']:.2f} | {row['sum_r']:.4f} | {row['mean_r']:.4f} | {row['profit_factor']} | {row['max_drawdown_r']:.4f} |")
    report += [
        "",
        "## الحكم",
        "",
        "- النمط لم يثبت استمراراً مستقراً: XAUUSD كان سالباً في 2022 و2024 وموجباً في 2023 و2025.",
        "- لذلك لا أستطيع تسمية جلسة London/New York بـ edge خارق أو تحويلها إلى وعد بربح يومي.",
        "- هذه النتيجة تمنع overfitting: لا يجوز أخذ نتيجة 2021 وحدها وتشغيلها بأموال حقيقية قبل إضافة spread/commission واختبار أحدث من 2025.",
        "",
    ]
    (RESULTS / "OOS_REPORT_AR.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
