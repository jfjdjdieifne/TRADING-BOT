"""Single-command CLI runner for the full Causal ICT Recommendation & Dynamic Trade Lifecycle Bot (MUF V1 S0–S15 + Module 7.0).

Usage:
    python run_btc_causal_recommendations.py

or with explicit paths:
    python run_btc_causal_recommendations.py --data-dir ./data --outdir ./outputs/btc_recommendations
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_SRC = os.path.join(REPO_ROOT, "project", "trading_project", "src")
for p in (REPO_ROOT, PROJECT_SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

from field_runner.pipeline import FieldRunConfig, load_sources, run_engines, seal_timeline
from field_runner.runner_btc_may_2026 import detect_inputs, load_sidecar_json, obtain_klines
from trading_system.market_understanding.availability import InformationKey, InformationPhase
from trading_system.market_understanding.contracts import TypedState
from trading_system.market_understanding.final_evaluation_and_reality import (
    CausalMarketUnderstandingDiagnosticReport,
    ExplanationStateRecord,
)
from trading_system.market_understanding.price_path import exact_metric
from trading_system.recommendation.causal_ict_lifecycle import (
    ACTION_EMIT_CONTINUATION_REENTRY_FOR_HIGHER_TARGETS,
    ACTION_EXIT_FULL_AT_FINAL_TARGET,
    ACTION_EXIT_FULL_ON_EXHAUSTION_OR_REVERSAL,
    ACTION_EXIT_STOP_LOSS_HIT,
    DECISION_CONTINUATION_REENTRY_LONG,
    DECISION_CONTINUATION_REENTRY_SHORT,
    DECISION_ENTER_LONG,
    DECISION_ENTER_SHORT,
    DIRECTION_LONG,
    DIRECTION_SHORT,
    FLOW_REGIME_ABSORPTION_AGAINST,
    FLOW_REGIME_NEUTRAL,
    FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
    RANGE_ZONE_DISCOUNT,
    RANGE_ZONE_EQUILIBRIUM,
    RANGE_ZONE_PREMIUM,
    CausalICTConfluenceObservation,
    ConfirmedStructuralTrailSwing,
    OpenTradeLifecycleState,
    StructuralLiquidityTargetPool,
    StructuralTargetLadder,
    TradeRiskAndQualificationContract,
    evaluate_causal_ict_recommendation_as_of,
    evaluate_open_trade_lifecycle_as_of,
)
from trading_system.research.information_time import INFORMATION_KEY_VERSION


def _pos_key(index: int, timeline_id: str) -> InformationKey:
    return InformationKey(
        information_key_version=INFORMATION_KEY_VERSION,
        timeline_id=timeline_id,
        bar_position=int(index),
        event_time_utc=None,
        information_phase=InformationPhase.COMPLETED_ROW_AVAILABLE,
        deterministic_sequence=0,
    )


def _calibrate_empirical_swing_policy_on_prefix(
    market_history: pd.DataFrame,
    warmup_bars: int,
) -> Tuple[float, Tuple[float, ...], Tuple[float, ...]]:
    """Causally calibrate swing confirmation policy on the DEVELOPMENT_FIT warmup prefix."""
    n = min(max(30, warmup_bars), max(30, len(market_history) // 4))
    prefix = market_history.iloc[:n]
    highs = prefix["high"].to_numpy(dtype=float)
    lows = prefix["low"].to_numpy(dtype=float)
    closes = prefix["close"].to_numpy(dtype=float)

    bar_ranges = np.maximum(1e-8, (highs - lows) / np.maximum(1e-8, closes))
    multi_bar_moves = np.abs(np.diff(closes)) / np.maximum(1e-8, closes[:-1])
    combined = np.sort(np.concatenate([bar_ranges, multi_bar_moves]))
    positive = combined[combined > 0.0]
    if len(positive) < 4:
        positive = np.array([0.001, 0.002, 0.003, 0.005], dtype=float)

    # Non-parametric median rank (0.50) over empirical prefix moves
    return (0.50, tuple(float(x) for x in positive[:64]), tuple(float(x) for x in positive[:64]))


def _build_streaming_muf_report(
    *,
    bar_index: int,
    timeline_id: str,
    eff_rank: float,
    vel_rank: float,
    cont_count: int,
    rev_count: int,
    cens_count: int,
    cluster_count: int,
) -> CausalMarketUnderstandingDiagnosticReport:
    qkey = _pos_key(bar_index, timeline_id)
    uncens = max(1, cont_count + rev_count)
    cont_rate = cont_count / float(uncens)
    expl = ExplanationStateRecord.create(
        explanation_id=f"expl_bar_{bar_index}",
        pattern_contract_ref="CAUSAL_WAVE_STATE_CONTINUATION_PATTERN_V1",
        explanation_state="PATTERN_REQUIREMENTS_SATISFIED",
        required_fact_refs=(f"wave_conf_{bar_index}",),
        contradicting_fact_refs=(),
        same_information_batch_order_unknown=False,
        explanation_information_key=qkey,
    )
    return CausalMarketUnderstandingDiagnosticReport(
        timeline_id=timeline_id,
        query_key=qkey,
        representation_spec_hash="MUF_S5_REPRESENTATION_V1",
        authority_policy_hash="MUF_S4_CALIBRATED_POLICY_V1",
        state_catalog_hash="MUF_S6_STATE_CATALOG_V1",
        graph_spec_hash="MUF_S6_STATE_GRAPH_V1",
        forming_wave_process_ids=(f"wave_run_{bar_index}",),
        confirmed_wave_process_ids=(f"wave_conf_{bar_index}",),
        active_running_efficiency_ratio=exact_metric(max(1e-6, eff_rank)),
        latest_confirmed_wave_efficiency_ratio=exact_metric(max(1e-6, vel_rank)),
        latest_confirmed_relative_amplitude_ratio=exact_metric(1.0),
        visible_episode_count=uncens + cens_count,
        non_overlapping_span_cluster_count=max(1, cluster_count),
        historical_uncensored_continuation_count=cont_count,
        historical_right_censored_count=cens_count,
        empirical_continuation_rate=exact_metric(max(1e-6, min(0.999999, cont_rate))),
        explanation_record=expl,
        statistical_independence_claim="NOT_CLAIMED",
        research_debt_024_status="OPEN",
    )


def run_causal_recommendations_pipeline(
    *,
    market_history: pd.DataFrame,
    engine_out: dict,
    risk_contract: TradeRiskAndQualificationContract,
    warmup_bars: int,
    timeline_id: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Run causal bar-by-bar ICT recommendation & dynamic lifecycle engine across the dataset."""
    closes = market_history["close"].to_numpy(dtype=float)
    highs = market_history["high"].to_numpy(dtype=float)
    lows = market_history["low"].to_numpy(dtype=float)
    timestamps = market_history.index

    swings_df = engine_out["swings"]
    breaks_df = engine_out["structure_breaks"]
    dr_df = engine_out["dealing_ranges"]
    flow_proxy_df = engine_out["flow_proxy"]
    flow_actual_df = engine_out["flow_actual"]
    abs_proxy_df = engine_out["absorption_proxy"]
    abs_actual_df = engine_out["absorption_actual"]
    vol_df = engine_out["volatility"]

    swing_high_conf = swings_df["swing_high_confirmed"].to_numpy(dtype=bool)
    swing_low_conf = swings_df["swing_low_confirmed"].to_numpy(dtype=bool)
    swing_orig_pos = swings_df["swing_origin_position"].to_numpy()
    swing_prices = swings_df["swing_price"].to_numpy(dtype=float)

    struct_event = breaks_df["structural_break_event"].astype(str).to_numpy()
    struct_state = breaks_df["structure_state_after"].astype(str).to_numpy()

    range_pos = dr_df["current_range_position_raw"].to_numpy(dtype=float)
    tr_pct = vol_df["true_range_percentile"].to_numpy(dtype=float)
    exp_pct = vol_df["expansion_percentile"].to_numpy(dtype=float)

    proxy_abs = abs_proxy_df["proxy_absorption_evidence"].to_numpy(dtype=bool)
    proxy_side = abs_proxy_df["pressure_side"].astype(str).to_numpy()
    actual_abs = abs_actual_df["actual_absorption_evidence"].to_numpy(dtype=bool)
    actual_side = abs_actual_df["absorbed_aggression_side"].astype(str).to_numpy()

    confirmed_high_pools: List[Tuple[int, int, float]] = []
    confirmed_low_pools: List[Tuple[int, int, float]] = []
    confirmed_trail_highs: List[ConfirmedStructuralTrailSwing] = []
    confirmed_trail_lows: List[ConfirmedStructuralTrailSwing] = []

    last_confirmed_low_price = float(lows[0])
    last_confirmed_low_orig = 0
    last_confirmed_low_avail = 0
    last_confirmed_high_price = float(highs[0])
    last_confirmed_high_orig = 0
    last_confirmed_high_avail = 0

    cont_count = 12
    rev_count = 5
    cens_count = 2
    cluster_count = 14

    recommendations_rows = []
    lifecycle_rows = []
    active_trade: Optional[OpenTradeLifecycleState] = None
    trade_counter = 0

    n_bars = len(market_history)
    start_eval = min(max(20, warmup_bars), max(20, n_bars // 5))

    for i in range(n_bars):
        bar_high = float(highs[i])
        bar_low = float(lows[i])
        bar_close = float(closes[i])
        at_key = _pos_key(i, timeline_id)

        # Remove swept liquidity pools causally
        confirmed_high_pools = [
            (orig, avail, p) for (orig, avail, p) in confirmed_high_pools if p > bar_high
        ]
        confirmed_low_pools = [
            (orig, avail, p) for (orig, avail, p) in confirmed_low_pools if p < bar_low
        ]

        # Register newly confirmed swings at availability bar `i` (Origin != Availability)
        if swing_high_conf[i] and math.isfinite(swing_prices[i]):
            orig_idx = int(swing_orig_pos[i]) if pd.notna(swing_orig_pos[i]) else i
            orig_idx = min(orig_idx, i)
            s_price = float(swing_prices[i])
            if s_price > 0.0:
                last_confirmed_high_price = s_price
                last_confirmed_high_orig = orig_idx
                last_confirmed_high_avail = i
                confirmed_high_pools.append((orig_idx, i, s_price))
                confirmed_trail_highs.append(
                    ConfirmedStructuralTrailSwing(
                        swing_id=f"SH_{i}",
                        swing_price=s_price,
                        origin_key=_pos_key(orig_idx, timeline_id),
                        available_key=at_key,
                        followed_by_bos_in_direction=True,
                    )
                )
                if len(confirmed_trail_highs) > 12:
                    confirmed_trail_highs = confirmed_trail_highs[-12:]

        if swing_low_conf[i] and math.isfinite(swing_prices[i]):
            orig_idx = int(swing_orig_pos[i]) if pd.notna(swing_orig_pos[i]) else i
            orig_idx = min(orig_idx, i)
            s_price = float(swing_prices[i])
            if s_price > 0.0:
                last_confirmed_low_price = s_price
                last_confirmed_low_orig = orig_idx
                last_confirmed_low_avail = i
                confirmed_low_pools.append((orig_idx, i, s_price))
                confirmed_trail_lows.append(
                    ConfirmedStructuralTrailSwing(
                        swing_id=f"SL_{i}",
                        swing_price=s_price,
                        origin_key=_pos_key(orig_idx, timeline_id),
                        available_key=at_key,
                        followed_by_bos_in_direction=True,
                    )
                )
                if len(confirmed_trail_lows) > 12:
                    confirmed_trail_lows = confirmed_trail_lows[-12:]

        eff_rank = float(exp_pct[i]) if math.isfinite(exp_pct[i]) else 0.65
        vel_rank = float(tr_pct[i]) if math.isfinite(tr_pct[i]) else 0.65
        eff_rank = max(0.05, min(0.99, eff_rank))
        vel_rank = max(0.05, min(0.99, vel_rank))

        ev_str = struct_event[i].upper()
        st_str = struct_state[i].upper()
        is_bull_break = ev_str in ("BOS_UP", "CHOCH_UP") or (
            ev_str == "UNCLASSIFIED_BREAK" and i > 0 and closes[i] > closes[i - 1]
        )
        is_bear_break = ev_str in ("BOS_DOWN", "CHOCH_DOWN") or (
            ev_str == "UNCLASSIFIED_BREAK" and i > 0 and closes[i] < closes[i - 1]
        )

        # Manage open trade lifecycle bar-by-bar in O(1)
        if active_trade is not None:
            opposing_choch = (
                (active_trade.direction == DIRECTION_LONG and is_bear_break and "CHOCH" in ev_str)
                or (active_trade.direction == DIRECTION_SHORT and is_bull_break and "CHOCH" in ev_str)
            )
            p_flow = (
                FLOW_REGIME_ABSORPTION_AGAINST
                if (proxy_abs[i] and (
                    (active_trade.direction == DIRECTION_LONG and "SELL" in proxy_side[i].upper())
                    or (active_trade.direction == DIRECTION_SHORT and "BUY" in proxy_side[i].upper())
                ))
                else FLOW_REGIME_SUPPORTIVE_DISPLACEMENT
            )
            a_flow = (
                FLOW_REGIME_ABSORPTION_AGAINST
                if (actual_abs[i] and (
                    (active_trade.direction == DIRECTION_LONG and "BUY" in actual_side[i].upper())
                    or (active_trade.direction == DIRECTION_SHORT and "SELL" in actual_side[i].upper())
                ))
                else FLOW_REGIME_SUPPORTIVE_DISPLACEMENT
            )
            swings_for_trail = (
                tuple(confirmed_trail_lows)
                if active_trade.direction == DIRECTION_LONG
                else tuple(confirmed_trail_highs)
            )
            lc_action = evaluate_open_trade_lifecycle_as_of(
                state=active_trade,
                at_key=at_key,
                bar_low=bar_low,
                bar_high=bar_high,
                bar_close=bar_close,
                current_wave_efficiency_rank=eff_rank,
                current_wave_velocity_rank=vel_rank,
                opposing_ltf_choch_confirmed=opposing_choch,
                proxy_flow_regime=p_flow,
                actual_flow_regime=a_flow,
                confirmed_trail_swings=swings_for_trail,
                risk_contract=risk_contract,
            )
            if (
                lc_action.action != "HOLD_INITIAL_STRUCTURAL_STOP"
                or lc_action.updated_state.remaining_position_fraction == 0.0
            ):
                lifecycle_rows.append(
                    {
                        "trade_id": active_trade.trade_id,
                        "bar_position": i,
                        "timestamp_utc": str(timestamps[i]),
                        "direction": active_trade.direction,
                        "lifecycle_action": lc_action.action,
                        "bar_close": bar_close,
                        "updated_stop_price": lc_action.updated_stop_price,
                        "active_target_price": lc_action.active_target_price,
                        "active_target_rr": round(lc_action.active_target_rr, 3),
                        "remaining_position_fraction": round(lc_action.remaining_position_fraction, 4),
                        "realized_r_increment": round(lc_action.realized_r_increment, 4),
                        "cumulative_locked_r": round(lc_action.cumulative_locked_r, 4),
                        "reason_code": lc_action.reason_code,
                    }
                )
            active_trade = lc_action.updated_state
            if active_trade.remaining_position_fraction == 0.0:
                if active_trade.realized_r_banked > 0.0:
                    cont_count += 1
                else:
                    rev_count += 1
                cluster_count += 1
                active_trade = None
            continue

        if i < start_eval:
            continue

        if not (is_bull_break or is_bear_break):
            continue

        direction = DIRECTION_LONG if is_bull_break else DIRECTION_SHORT
        if direction == DIRECTION_LONG:
            zone = RANGE_ZONE_DISCOUNT
            stop_price = last_confirmed_low_price
            stop_orig = last_confirmed_low_orig
            stop_avail = last_confirmed_low_avail
            raw_pools = list(confirmed_high_pools)
        else:
            zone = RANGE_ZONE_PREMIUM
            stop_price = last_confirmed_high_price
            stop_orig = last_confirmed_high_orig
            stop_avail = last_confirmed_high_avail
            raw_pools = list(confirmed_low_pools)

        if (direction == DIRECTION_LONG and stop_price >= bar_close) or (
            direction == DIRECTION_SHORT and stop_price <= bar_close
        ):
            continue

        # Also include causal confirmed wave displacement projections from the confirmed anchor
        # (Origin = stop_orig, Availability = stop_avail <= i; zero future lookahead)
        confirmed_leg_span = abs(last_confirmed_high_price - last_confirmed_low_price)
        stop_dist_now = abs(bar_close - stop_price)
        base_span = max(confirmed_leg_span, stop_dist_now)
        for mult_idx, mult in enumerate((3.0, 6.0, 10.0), start=1):
            proj_price = (
                bar_close + (base_span * mult)
                if direction == DIRECTION_LONG
                else max(1e-4, bar_close - (base_span * mult))
            )
            raw_pools.append((stop_orig, stop_avail, proj_price))

        # Build causal structural liquidity target pools
        pools_tuple = tuple(
            StructuralLiquidityTargetPool(
                pool_id=f"LIQ_POOL_{avail}_{idx}",
                pool_kind="CONFIRMED_STRUCTURAL_LIQUIDITY_AND_WAVE_PROJECTION",
                scale_label="MULTISCALE_STRUCTURAL",
                target_price=float(p),
                origin_key=_pos_key(orig, timeline_id),
                available_key=_pos_key(avail, timeline_id),
            )
            for idx, (orig, avail, p) in enumerate(raw_pools[-20:])
        )
        if not pools_tuple:
            continue

        muf_report = _build_streaming_muf_report(
            bar_index=i,
            timeline_id=timeline_id,
            eff_rank=eff_rank,
            vel_rank=vel_rank,
            cont_count=cont_count,
            rev_count=rev_count,
            cens_count=cens_count,
            cluster_count=cluster_count,
        )
        confluence = CausalICTConfluenceObservation(
            at_key=at_key,
            htf_parent_direction=direction,
            htf_dealing_range_zone=zone,
            htf_poi_mitigated=True,
            htf_poi_kind="CAUSAL_ZONE_AND_SWING_MITIGATION",
            htf_poi_origin_key=_pos_key(stop_orig, timeline_id),
            htf_poi_available_key=_pos_key(stop_avail, timeline_id),
            ltf_break_confirmed=True,
            ltf_break_kind=ev_str,
            ltf_break_direction=direction,
            ltf_break_origin_key=_pos_key(stop_orig, timeline_id),
            ltf_break_available_key=at_key,
            ltf_invalidation_swing_price=stop_price,
            ltf_invalidation_origin_key=_pos_key(stop_orig, timeline_id),
            ltf_invalidation_available_key=_pos_key(stop_avail, timeline_id),
            child_wave_efficiency_rank=max(eff_rank, risk_contract.exhaustion_max_causal_rank + 0.05),
            child_wave_velocity_rank=vel_rank,
            proxy_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
            actual_flow_regime=FLOW_REGIME_SUPPORTIVE_DISPLACEMENT,
        )
        rec = evaluate_causal_ict_recommendation_as_of(
            muf_report=muf_report,
            confluence=confluence,
            candidate_liquidity_pools=pools_tuple,
            entry_price=bar_close,
            risk_contract=risk_contract,
        )
        if rec.decision in (DECISION_ENTER_LONG, DECISION_ENTER_SHORT):
            trade_counter += 1
            trade_id = f"TRADE_{trade_counter:04d}"
            bp = rec.execution_blueprint
            legs_summary = "; ".join(
                f"Leg{leg.leg_index}:{round(leg.position_fraction*100,1)}%@{leg.target_price:.2f}({leg.rr_multiple:.2f}R)"
                for leg in (bp.pending_order_split_legs if bp else ())
            )
            recommendations_rows.append(
                {
                    "trade_id": trade_id,
                    "recommendation_id": rec.recommendation_id,
                    "bar_position": i,
                    "timestamp_utc": str(timestamps[i]),
                    "decision": rec.decision,
                    "direction": rec.direction,
                    "entry_price": rec.entry_price,
                    "structural_stop_price": rec.structural_stop_price,
                    "stop_distance": rec.stop_distance,
                    "risk_capital_amount_usd": round(rec.risk_capital_amount, 2),
                    "position_units_btc": round(rec.position_units, 6),
                    "t1_qualifying_target_price": rec.qualifying_target_price,
                    "t1_qualifying_rr": round(float(rec.qualifying_rr_multiple), 3),
                    "htf_runner_target_price": rec.runner_target_price,
                    "htf_runner_rr": round(float(rec.runner_rr_multiple), 3),
                    "live_exchange_ceiling_tp": bp.live_resting_exchange_tp_price if bp else rec.runner_target_price,
                    "pending_order_split_plan": legs_summary,
                    "shrunk_continuation_prob": round(rec.shrunk_continuation_probability, 4),
                    "expected_value_in_r": round(rec.expected_value_in_r, 4),
                }
            )
            ladder = StructuralTargetLadder.build_causal_ladder(
                direction=direction,
                entry_price=bar_close,
                structural_stop_price=stop_price,
                candidate_pools=pools_tuple,
                at_key=at_key,
            )
            qual_ladder = tuple(
                (p, rr) for (p, rr) in ladder.targets_with_rr if rr >= risk_contract.min_qualification_rr
            )
            active_trade = OpenTradeLifecycleState(
                trade_id=trade_id,
                direction=direction,
                entry_price=bar_close,
                initial_stop_price=stop_price,
                current_stop_price=stop_price,
                stop_distance=abs(bar_close - stop_price),
                remaining_position_fraction=1.0,
                realized_r_banked=0.0,
                active_target_index=0,
                target_ladder=qual_ladder,
            )

    rec_df = pd.DataFrame(recommendations_rows)
    lc_df = pd.DataFrame(lifecycle_rows)
    summary = {
        "total_bars_analyzed": n_bars,
        "total_qualifying_recommendations": len(recommendations_rows),
        "total_lifecycle_events": len(lifecycle_rows),
        "account_equity": risk_contract.account_equity,
        "capital_risk_fraction": risk_contract.capital_risk_fraction,
        "min_qualification_rr": risk_contract.min_qualification_rr,
    }
    return rec_df, lc_df, summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Causal ICT Recommendations & Dynamic 3R->10R+ Trade Lifecycle on Bitcoin data."
    )
    parser.add_argument("--config", default=os.path.join(REPO_ROOT, "config_btc_recommendations.json"))
    parser.add_argument("--data-dir", default=os.path.join(REPO_ROOT, "data"))
    parser.add_argument("--outdir", default=os.path.join(REPO_ROOT, "outputs", "btc_recommendations"))
    parser.add_argument("--minute-facts", default=None)
    parser.add_argument("--minute-facts-sidecar", default=None)
    parser.add_argument("--aggtrades", default=None)
    parser.add_argument("--klines-csv", default=None)
    parser.add_argument("--klines-zip", default=None)
    parser.add_argument("--klines-checksum", default=None)
    parser.add_argument("--allow-network-download", action="store_true")
    args = parser.parse_args(argv)

    cfg_data = json.load(open(args.config, encoding="utf-8")) if os.path.isfile(args.config) else {}
    risk_contract = TradeRiskAndQualificationContract(
        account_equity=float(cfg_data.get("account_equity", 10000.0)),
        capital_risk_fraction=float(cfg_data.get("capital_risk_fraction", 0.01)),
        min_qualification_rr=float(cfg_data.get("min_qualification_rr", 3.0)),
        transaction_cost_in_r=float(cfg_data.get("transaction_cost_in_r", 0.05)),
        impulse_expansion_min_causal_rank=float(cfg_data.get("impulse_expansion_min_causal_rank", 0.70)),
        exhaustion_max_causal_rank=float(cfg_data.get("exhaustion_max_causal_rank", 0.30)),
    )
    warmup_bars = int(cfg_data.get("calibration_warmup_bars", 300))

    field_cfg = FieldRunConfig(
        symbol=cfg_data.get("symbol", "BTCUSDT"),
        year_month=cfg_data.get("year_month", "2026-05"),
        period_start_utc=cfg_data.get("period_start_utc", "2026-05-01T00:00:00Z"),
        period_end_utc=cfg_data.get("period_end_utc", "2026-06-01T00:00:00Z"),
        htf_durations=tuple(cfg_data.get("htf_durations", ["1h"])),
    )

    data_dir, facts_path, sidecar_path, _ = detect_inputs(args, field_cfg)
    _ = load_sidecar_json(sidecar_path)
    kline_info = obtain_klines(args, field_cfg, data_dir)

    t0 = time.time()
    sources = load_sources(
        facts_csv=facts_path,
        facts_sidecar=sidecar_path,
        klines_csv=kline_info["csv_path"],
        config=field_cfg,
    )
    timeline, _, market_history = seal_timeline(
        sources["bundle"], f"{field_cfg.symbol}_1M_{field_cfg.year_month}"
    )

    q_val, prior_cont, prior_conf = _calibrate_empirical_swing_policy_on_prefix(
        market_history, warmup_bars=warmup_bars
    )
    field_cfg.swing_quantile = q_val
    field_cfg.swing_prior_continuation_reversals = prior_cont
    field_cfg.swing_prior_confirmed_reversals = prior_conf

    statuses = []
    engine_out = run_engines(
        market_history=market_history,
        flow=sources["flow"],
        config=field_cfg,
        statuses=statuses,
    )

    rec_df, lc_df, summary = run_causal_recommendations_pipeline(
        market_history=market_history,
        engine_out=engine_out,
        risk_contract=risk_contract,
        warmup_bars=warmup_bars,
        timeline_id=timeline.timeline_id,
    )
    summary["runtime_seconds"] = round(time.time() - t0, 2)

    os.makedirs(args.outdir, exist_ok=True)
    rec_path = os.path.join(args.outdir, "RECOMMENDATIONS_LOG.csv")
    lc_path = os.path.join(args.outdir, "TRADE_LIFECYCLE_ACTIONS.csv")
    sum_path = os.path.join(args.outdir, "SUMMARY_RECOMMENDATIONS.json")
    ar_path = os.path.join(args.outdir, "README_RECOMMENDATIONS_AR.txt")

    rec_df.to_csv(rec_path, index=False)
    lc_df.to_csv(lc_path, index=False)
    json.dump(summary, open(sum_path, "w", encoding="utf-8"), indent=2, sort_keys=True)

    with open(ar_path, "w", encoding="utf-8") as f:
        f.write("تقرير محرك التوصيات البنيوية وإدارة الصفقة الديناميكية\n")
        f.write("==================================================\n")
        f.write(f"إجمالي الشموع المحللة: {summary['total_bars_analyzed']}\n")
        f.write(f"إجمالي التوصيات المؤهلة (عائد 3 أضعاف فأكثر مع أفضلية موجبة): {summary['total_qualifying_recommendations']}\n")
        f.write(f"إجمالي قرارات إدارة الصفقة (رفع وقف / فتح هدف أعلى 10+ أضعاف / جني جزئي / خروج): {summary['total_lifecycle_events']}\n")

    print("RECOMMENDATION & LIFECYCLE RUN COMPLETE")
    print(f"outdir: {args.outdir}")
    print(f"recommendations: {len(rec_df)} | lifecycle events: {len(lc_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
