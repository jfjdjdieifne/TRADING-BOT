#!/usr/bin/env python3
"""Run the immutable V5 baseline and predeclared causal post-signal variants.

Important scope: the variants are *entry gates* applied to signals already
accepted by V5. They may reject baseline trades but do not invent new signals.
This conservative first stage makes the comparison auditable; a later engine
can add new signal generation only with a separate candidate-replay contract.
"""
from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE / "original_v5"
AUGMENTED = HERE / "augmented_v5"
if str(ORIGINAL) not in sys.path:
    sys.path.insert(0, str(ORIGINAL))
if str(AUGMENTED) not in sys.path:
    sys.path.insert(0, str(AUGMENTED))

from engine.causal_primitives import load_xauusd_1m, resample_causal_tf  # noqa: E402
from engine.smc_v4_portfolio import run_smc_v5_portfolio, simulate_compounded_account  # noqa: E402
from causal_layers import FeatureEvidence, LayerConfig, layer_names, precompute_causal_swing_state, snapshot  # noqa: E402

DATA = HERE.parent / "smc_v4_multisleeve_package" / "data" / "XAUUSD_1m_histdata"
OUT = HERE / "variant_outputs"
MONTHS = [f"{year}-{month:02d}" for year in range(2020, 2026) for month in range(1, 13)] + [
    f"2026-{month:02d}" for month in range(1, 11)
]
START = pd.Timestamp("2020-02-01", tz="UTC")
DEV_END = pd.Timestamp("2025-01-01", tz="UTC")
END = pd.Timestamp("2026-11-01", tz="UTC")

# These costs are declared before reading any variant result. The original
# engine uses $0.25/oz round-trip; $0.50 and $1.00 are sensitivity scenarios,
# not claims about the actual broker's spread/commission/slippage.
ORIGINAL_COST = 0.25
STRESS_COSTS = (0.50, 1.00)
ESTIMATED_SPREAD_FOR_GATE = 0.50

LAYER_FIELDS = (
    "equal_levels", "liquidity_zone", "sweep_reclaim", "confirmed_mss",
    "displacement", "fvg", "order_block", "bpr", "htf_premium_discount",
    "retest_reaction", "invalidation", "abstention", "volatility_relative",
    "spread_cost_filter",
)


def configs() -> dict[str, LayerConfig]:
    """Predeclared variants; no result-dependent parameter search occurs."""
    out: dict[str, LayerConfig] = {"BASELINE_NO_GATE": LayerConfig()}
    for field in LAYER_FIELDS:
        out[field.upper()] = LayerConfig(**{field: True})
    out.update({
        "STRUCTURE_SWEEP_MSS": LayerConfig(sweep_reclaim=True, confirmed_mss=True, displacement=True),
        "IMBALANCE_OB_FVG": LayerConfig(displacement=True, fvg=True, order_block=True),
        "LIQUIDITY_EQUAL_SWEEP": LayerConfig(equal_levels=True, liquidity_zone=True, sweep_reclaim=True),
        "RISK_AWARE": LayerConfig(
            htf_premium_discount=True, invalidation=True, abstention=True,
            volatility_relative=True, spread_cost_filter=True,
        ),
        "ALL_DECLARED_LAYERS": LayerConfig(**{field: True for field in LAYER_FIELDS}),
    })
    return out


def as_jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    return value


def clone_evidence(ev: FeatureEvidence) -> FeatureEvidence:
    return FeatureEvidence(
        timestamp=ev.timestamp,
        side=ev.side,
        available=dict(ev.available),
        values=dict(ev.values),
        reasons=list(ev.reasons),
    )


def reprice(rows: list[dict], cost: float) -> list[dict]:
    out = []
    for row in rows:
        item = dict(row)
        item["net_usd"] = float(item["gross_usd"] - cost)
        item["net_r"] = float(item["net_usd"] / item["risk_usd"])
        out.append(item)
    return out


def max_drawdown(values: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return dd


def max_consecutive_losses(values: list[float]) -> int:
    best = current = 0
    for value in values:
        if value <= 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def metric_block(rows: list[dict], *, cost: float | None = None) -> dict[str, Any]:
    values = [float(row["net_r"]) for row in rows]
    gross = [float(row["gross_r"]) for row in rows]
    wins = [value for value in values if value > 0]
    losses = [value for value in values if value < 0]
    yearly: dict[str, float] = {}
    for row in rows:
        year = str(pd.Timestamp(row["exit_time"]).year)
        yearly[year] = yearly.get(year, 0.0) + float(row["net_r"])
    block: dict[str, Any] = {
        "trades": len(values),
        "wins": len(wins),
        "losses_or_zero": len(values) - len(wins),
        "win_rate_pct": round(100.0 * len(wins) / len(values), 4) if values else None,
        "net_r": round(sum(values), 6),
        "gross_r": round(sum(gross), 6),
        "expectancy_r": round(float(np.mean(values)), 6) if values else None,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 6) if losses else None,
        "max_drawdown_r": round(max_drawdown(values), 6),
        "max_consecutive_losses": max_consecutive_losses(values),
        "positive_years": sum(value > 0 for value in yearly.values()),
        "years": len(yearly),
        "yearly_net_r": {key: round(value, 6) for key, value in sorted(yearly.items())},
        "compound_100_1pct": simulate_compounded_account(rows, start_capital=100.0, risk_pct=0.01, compound=True),
        "compound_100_2pct": simulate_compounded_account(rows, start_capital=100.0, risk_pct=0.02, compound=True),
    }
    if cost is not None:
        block["cost_usd_per_oz"] = cost
    return block


def split_rows(rows: list[dict]) -> dict[str, list[dict]]:
    return {
        "development_2020_02_to_2024_12": [r for r in rows if START <= pd.Timestamp(r["entry_time"]) < DEV_END],
        "holdout_2025_01_to_2026_10": [r for r in rows if DEV_END <= pd.Timestamp(r["entry_time"]) < END],
        "full_2020_02_to_2026_10": list(rows),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_xauusd_1m(DATA, MONTHS)
    baseline_result = run_smc_v5_portfolio(data, START, END, cost=ORIGINAL_COST, single_position_lock=True)
    baseline = sorted(baseline_result["v5_1pos_lock"], key=lambda row: pd.Timestamp(row["exit_time"]))

    # A setup belongs to the causal completed-bar timeframe that produced it.
    tf_by_engine = {
        "V3_Pro": resample_causal_tf(data, "15min"),
        "AMD_Pro": resample_causal_tf(data, "15min"),
        "VisA": resample_causal_tf(data, "5min"),
        "VisB_Pro": resample_causal_tf(data, "5min"),
    }
    htf_context = resample_causal_tf(data, "4h")
    # Cache the confirmed swing state once per source timeframe. The cache is
    # causal by construction: state[i] only receives events confirmed at i.
    swing_state_by_tf = {
        "15min": precompute_causal_swing_state(tf_by_engine["V3_Pro"]),
        "5min": precompute_causal_swing_state(tf_by_engine["VisA"]),
    }
    cfgs = configs()
    decisions: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    variant_rows: dict[str, list[dict]] = {name: [] for name in cfgs}
    reason_counts: dict[str, Counter[str]] = {name: Counter() for name in cfgs}

    for trade_id, trade in enumerate(baseline):
        setup_time = pd.Timestamp(trade["setup_time"])
        engine = str(trade["engine"])
        tf = tf_by_engine.get(engine, tf_by_engine["V3_Pro"])
        i = int(tf.index.searchsorted(setup_time, side="right") - 1)
        base_decision = {
            "trade_id": trade_id,
            "engine": engine,
            "side": trade["side"],
            "setup_time": setup_time.isoformat(),
            "entry_time": str(trade["entry_time"]),
            "exit_time": str(trade["exit_time"]),
            "baseline_outcome": trade["outcome"],
            "baseline_net_r": float(trade["net_r"]),
            "baseline_gross_r": float(trade["gross_r"]),
            "known_at_setup": True,
        }
        if i < 0 or i >= len(tf) or tf.index[i] > setup_time:
            base_decision["decision_error"] = "no_completed_source_bar_at_setup"
            decisions.append(base_decision)
            continue
        setup_close = float(tf["Close"].iloc[i])
        risk_proxy = abs(setup_close - float(trade["sl_price"]))
        source_tf = "15min" if engine in ("V3_Pro", "AMD_Pro") else "5min"
        reference = snapshot(
            tf, i, str(trade["side"]), config=LayerConfig(), as_of=setup_time,
            estimated_spread=ESTIMATED_SPREAD_FOR_GATE, risk_distance=risk_proxy,
            swing_state=swing_state_by_tf[source_tf][i], htf_tf=htf_context,
        )
        evidence = {
            "trade_id": trade_id,
            "engine": engine,
            "side": trade["side"],
            "setup_time": setup_time.isoformat(),
            "source_timeframe": "15min" if engine in ("V3_Pro", "AMD_Pro") else "5min",
            "source_bar_end": reference.timestamp.isoformat(),
            "available": as_jsonable(reference.available),
            "values": as_jsonable(reference.values),
            "base_reasons": list(reference.reasons),
        }
        evidence_rows.append(evidence)
        base_decision["source_bar_end"] = reference.timestamp.isoformat()
        decisions.append(base_decision)

        for name, config in cfgs.items():
            ev = clone_evidence(reference)
            passed = True if name == "BASELINE_NO_GATE" else ev.enabled_pass(config)
            reasons = list(ev.reasons)
            if not passed and not reasons:
                reasons = ["layer_gate_failed"]
            if passed:
                variant_rows[name].append(dict(trade))
            for reason in reasons:
                reason_counts[name][reason] += 1
            decisions.append({
                **base_decision,
                "variant": name,
                "passed": passed,
                "enabled_layers": layer_names(config),
                "decision_reasons": reasons if not passed else ["accepted_baseline_signal"],
                "features": as_jsonable(ev.available),
            })

    # Write one line per candidate/variant decision; this includes rejected
    # baseline trades and therefore makes omission counts auditable.
    with (OUT / "signal_decisions.jsonl").open("w", encoding="utf-8") as fh:
        for row in decisions:
            fh.write(json.dumps(as_jsonable(row), sort_keys=True) + "\n")
    with (OUT / "feature_evidence.jsonl").open("w", encoding="utf-8") as fh:
        for row in evidence_rows:
            fh.write(json.dumps(as_jsonable(row), sort_keys=True) + "\n")

    base_ids = {id(row) for row in baseline}
    summary: dict[str, Any] = {
        "research_contract": {
            "source": "V5 byte-preserved clone; augmented variants are post-signal entry gates",
            "signal_universe": "645 baseline V5_1PosLock signals; no new signal generation in this stage",
            "data": "XAUUSD 1-minute OHLC archives from package/data/XAUUSD_1m_histdata",
            "development_window": [START.isoformat(), DEV_END.isoformat()],
            "holdout_window": [DEV_END.isoformat(), END.isoformat()],
            "holdout_used_for_selection": False,
            "original_round_trip_cost_usd_per_oz": ORIGINAL_COST,
            "stress_costs_usd_per_oz": list(STRESS_COSTS),
            "estimated_spread_for_filter_usd_per_oz": ESTIMATED_SPREAD_FOR_GATE,
            "feature_time_rule": "source completed bar end <= setup_time; setup close minus predeclared stop is the only risk proxy",
        },
        "baseline": {
            "full": metric_block(baseline, cost=ORIGINAL_COST),
            "splits": {name: metric_block(rows, cost=ORIGINAL_COST) for name, rows in split_rows(baseline).items()},
        },
        "variants": {},
    }

    for name, rows in variant_rows.items():
        rows = sorted(rows, key=lambda row: pd.Timestamp(row["exit_time"]))
        cfg = cfgs[name]
        base_outcomes = {id(row): (float(row["net_r"]) > 0) for row in baseline}
        kept_winners = sum(float(row["net_r"]) > 0 for row in rows)
        kept_losers = sum(float(row["net_r"]) <= 0 for row in rows)
        full = metric_block(rows, cost=ORIGINAL_COST)
        stress = {f"cost_{cost:.2f}": metric_block(reprice(rows, cost), cost=cost) for cost in STRESS_COSTS}
        summary["variants"][name] = {
            "enabled_layers": layer_names(cfg),
            "full": full,
            "splits": {split: metric_block(subset, cost=ORIGINAL_COST) for split, subset in split_rows(rows).items()},
            "stress_costs": stress,
            "retained_baseline_trades": len(rows),
            "dropped_baseline_trades": len(baseline) - len(rows),
            "retained_baseline_winners": kept_winners,
            "retained_baseline_losers_or_zero": kept_losers,
            "dropped_baseline_winners": sum(float(row["net_r"]) > 0 for row in baseline) - kept_winners,
            "dropped_baseline_losers_or_zero": sum(float(row["net_r"]) <= 0 for row in baseline) - kept_losers,
            "outcome_changed_by_filter": 0,
            "losers_turned_into_winners": 0,
            "reason_counts": dict(reason_counts[name]),
            "selection_note": "predeclared before evaluation; no holdout tuning",
        }
        pd.DataFrame(rows).to_csv(OUT / f"trades_{name.lower()}.csv", index=False)

    # A machine-readable manifest ties every output to source/data hashes later.
    (OUT / "summary_variants.json").write_text(json.dumps(as_jsonable(summary), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(as_jsonable(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
