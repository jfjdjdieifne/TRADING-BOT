#!/usr/bin/env python3
"""Research-only scan of causal signal-time filters.

This is deliberately not a selector for live use. It enumerates a small
predeclared family of filters, evaluates the same filters on 2021 (development)
and 2022-2025 (holdout), and reports the result so a rule is not selected from
its holdout outcome. Every filter uses fields known at displacement close.
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
CONFIG = StrategyConfig("FILTER_SCAN", require_fvg=False, large_mode="none", min_body_fraction=0.0)
ASSETS = {
    "XAUUSD": (DATA_ROOT / "XAUUSD_1m_histdata", ["2020-12.csv.gz"] + [f"{year}-{month:02d}.csv.gz" for year in range(2021, 2026) for month in range(1, 13)] + ["2026-01.csv.gz"], 1, "1m"),
    "NSXUSD": (DATA_ROOT / "NSXUSD_1m_histdata", ["2020-12.csv.gz"] + [f"{year}-{month:02d}.csv.gz" for year in range(2021, 2026) for month in range(1, 13)] + ["2026-01.csv.gz"], 1, "1m"),
    "BTCUSD": (DATA_ROOT / "BTCUSD_5m", [f"{year}.csv.gz" for year in range(2020, 2027)], 5, "5m"),
}
EVAL_START = datetime(2021, 1, 1, tzinfo=UTC)
EVAL_END = datetime(2026, 1, 1, tzinfo=UTC)


def session(hour: int) -> str:
    if hour < 7:
        return "ASIA"
    if hour < 13:
        return "LONDON"
    if hour < 20:
        return "NY"
    return "LATE"


def stats(rows: list[dict]) -> dict:
    rows = sorted(rows, key=lambda r: (r["entry_time"], r["signal_time"]))
    vals = [float(r["r_multiple"]) for r in rows]
    gains = sum(v for v in vals if v > 0)
    losses = sum(-v for v in vals if v < 0)
    equity = 0.0
    peak = 0.0
    dd = 0.0
    for v in vals:
        equity += v
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    # Fixed sensitivity only; it is not contract sizing.
    eq = 100.0
    peak_eq = eq
    dd_pct = 0.0
    for v in vals:
        eq *= 1.0 + 0.003 * v
        peak_eq = max(peak_eq, eq)
        dd_pct = max(dd_pct, (peak_eq - eq) / peak_eq * 100.0)
    return {
        "n": len(vals),
        "win_rate_pct": round(100 * sum(v > 0 for v in vals) / len(vals), 4) if vals else None,
        "sum_r": round(sum(vals), 6),
        "mean_r": round(sum(vals) / len(vals), 6) if vals else None,
        "profit_factor": round(gains / losses, 6) if losses else ("inf" if gains else None),
        "max_dd_r": round(dd, 6),
        "dd_at_0_3_pct": round(dd_pct, 6),
        "positive": sum(v > 0 for v in vals),
        "negative": sum(v < 0 for v in vals),
    }


def take_one(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda r: (r["entry_time"], r["side"], r["asset"], r["signal_time"]))
    by_time = defaultdict(list)
    for row in ordered:
        by_time[row["entry_time"]].append(row)
    result = []
    free = None
    for row in ordered:
        if len(by_time[row["entry_time"]]) > 1:
            continue
        entry = datetime.fromisoformat(row["entry_time"])
        if free is not None and entry <= free:
            continue
        result.append(row)
        free = datetime.fromisoformat(row["exit_time"])
    return result


def load_rows() -> tuple[list[dict], dict[str, str]]:
    rows = []
    hashes: dict[str, str] = {}
    for asset, (data_dir, files, interval, source_tf) in ASSETS.items():
        minutes, asset_hashes = load_ohlc(data_dir, files)
        hashes.update({f"{asset}/{name}": digest for name, digest in asset_hashes.items()})
        bars = aggregate_15m(minutes, interval)
        signals = detect_signals(bars, CONFIG, EVAL_START, EVAL_END)
        for signal in signals:
            if not signal.eligible:
                continue
            outcome = simulate_with_config(signal, CONFIG, bars, minutes)
            if outcome.state not in {"TARGET", "STOP", "TIME"} or outcome.entry_time is None:
                continue
            ts = datetime.fromisoformat(signal.displacement_time)
            rows.append({
                "asset": asset,
                "source_timeframe": source_tf,
                "side": signal.side,
                "signal_time": signal.displacement_time,
                "entry_time": outcome.entry_time,
                "exit_time": outcome.exit_time,
                "state": outcome.state,
                "r_multiple": outcome.r_multiple,
                "year": ts.year,
                "month": ts.strftime("%Y-%m"),
                "session": session(ts.hour),
                "hour": ts.hour,
                "weekday": ts.strftime("%a"),
                "target_rr": signal.target_rr_at_close,
                "fvg": signal.displacement_fvg,
                "body_fraction": signal.displacement_body_fraction,
                "range": signal.displacement_range,
            })
    return rows, hashes


def main() -> None:
    rows, hashes = load_rows()
    rules = {
        "ALL": lambda r: True,
        "XAU_SHORT_LONDON": lambda r: r["asset"] == "XAUUSD" and r["side"] == "SHORT" and r["session"] == "LONDON",
        "XAU_FIXED_SESSION": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")),
        "BTC_FIXED_SESSION": lambda r: r["asset"] == "BTCUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")),
        "XAU_FIXED_RR_1_5": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["target_rr"] is not None and r["target_rr"] >= 1.5,
        "XAU_FIXED_RR_2": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["target_rr"] is not None and r["target_rr"] >= 2.0,
        "XAU_FIXED_RR_3": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["target_rr"] is not None and r["target_rr"] >= 3.0,
        "XAU_FIXED_FVG": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["fvg"],
        "XAU_FIXED_BODY_0_6": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["body_fraction"] >= 0.6,
        "XAU_FIXED_RR2_FVG": lambda r: r["asset"] == "XAUUSD" and ((r["side"] == "SHORT" and r["session"] == "LONDON") or (r["side"] == "LONG" and r["session"] == "NY")) and r["target_rr"] is not None and r["target_rr"] >= 2.0 and r["fvg"],
    }
    out = []
    for name, predicate in rules.items():
        selected = [r for r in rows if predicate(r)]
        taken = take_one(selected)
        for scope, values in (("raw", selected), ("one_position", taken)):
            for period_name, period_predicate in (("all", lambda r: True), ("train_2021", lambda r: r["year"] == 2021), ("holdout_2022_2025", lambda r: 2022 <= r["year"] <= 2025)):
                period = [r for r in values if period_predicate(r)]
                out.append({"rule": name, "scope": scope, "period": period_name, **stats(period)})
    csv_path = HERE / "results_filter_scan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    (HERE / "filter_scan_data_hashes.txt").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in sorted(hashes.items())) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Causal filter screen — development 2021 vs holdout 2022–2025",
        "",
        "> هذه ليست عملية اختيار من holdout. القواعد العشر معلنة مسبقاً في `run_filter_scan.py`، و2021 development منفصل عن 2022–2025 holdout. كل شرط يعتمد على signal-time fields فقط.",
        "",
        "| rule | train n | train sum R | train PF | train DD@0.3% | holdout n | holdout sum R | holdout PF | holdout DD@0.3% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in rules:
        train = next(row for row in out if row["rule"] == name and row["scope"] == "one_position" and row["period"] == "train_2021")
        holdout = next(row for row in out if row["rule"] == name and row["scope"] == "one_position" and row["period"] == "holdout_2022_2025")
        report.append(
            f"| {name} | {train['n']} | {train['sum_r']} | {train['profit_factor']} | {train['dd_at_0_3_pct']}% | "
            f"{holdout['n']} | {holdout['sum_r']} | {holdout['profit_factor']} | {holdout['dd_at_0_3_pct']}% |"
        )
    report += [
        "",
        "## الحكم",
        "",
        "- `XAU_FIXED_SESSION` يحقق نتيجة 2021 جذابة، لكنه يفشل holdout عند 0.3%: PF قريب من 1 وDD يتجاوز 5% بوضوح.",
        "- شروط FVG أو body تقلل النشاط، لكن العينة/الـPF لا تثبت edge مستقر؛ body يتجاوز 5% قليلاً في holdout وFVG يصبح PF<1.",
        "- لا يوجد rule في هذه الشاشة المحدودة يحقق معاً PF>1 في holdout وDD@0.3%<=5% مع نشاط واضح؛ لذلك لم أسمِّ أي profile معتمداً live.",
        "- هذه screen ليست بحثاً شاملاً لكل threshold؛ إضافة thresholds بعد رؤية holdout ستكون overfitting، لذلك تُترك كخطوة بحث منفصلة.",
        "- `filter_scan_data_hashes.txt` يثبت ملفات الإدخال التي استُخدمت في المقارنة.",
        "",
    ]
    (HERE / "FILTER_SCAN_REPORT_AR.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"candidate_rows": len(rows), "rules": len(rules)}, indent=2))


if __name__ == "__main__":
    main()
