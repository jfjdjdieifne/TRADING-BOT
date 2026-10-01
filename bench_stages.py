"""Stage-cost benchmark on SYNTHETIC month-scale frames (no owner data)."""
import sys, time
import numpy as np
import pandas as pd

N = int(sys.argv[1]) if len(sys.argv) > 1 else 22320
LABEL = sys.argv[2] if len(sys.argv) > 2 else "half"

log = open(f"/tmp/bench_{LABEL}.log", "w", buffering=1)

def say(msg):
    print(msg, flush=True)
    log.write(msg + "\n")

# synthetic zigzag month (same geometry family as fixture: small legs + crashes)
idx = pd.date_range("2026-05-01", periods=N, freq="min", tz="UTC")
i = np.arange(N)
step = np.where(i % 4 < 3, 0.5, -(2.0 + 0.3 * ((i // 4) % 7)))
close = 100.0 + np.cumsum(step)
open_ = np.concatenate([[100.0], close[:-1]])
high = np.maximum(open_, close) + 0.15
low = np.minimum(open_, close) - 0.15
volume = 1.0 + (i % 7) * 0.03 + (i % 5) * 0.02
buy = 0.5 + (i % 7) * 0.03
sell = 0.4 + (i % 5) * 0.02

mh = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)
actual = pd.DataFrame({"buy_volume": buy, "sell_volume": sell, "volume": volume}, index=idx)

from trading_system.environment.dynamic_volatility import DynamicVolatilityEngine
from trading_system.environment.session_context import CausalSessionContextEngine, SessionDefinition
from trading_system.structure.swing_detector import CausalAdaptiveSwingDetector, EmpiricalConfirmationPolicy
from trading_system.structure.swing_sequence import ConfirmedSwingSequenceEngine
from trading_system.structure.structural_breaks import CausalStructuralBreakEngine
from trading_system.liquidity.liquidity_map import CausalLiquidityMapEngine
from trading_system.orderflow.volume_delta import CausalVolumeDeltaEngine, OrderFlowMode
from trading_system.orderflow.absorption import CausalAbsorptionEvidenceEngine
from trading_system.zones.fvg import CausalFVGEngine
from trading_system.zones.order_blocks import CausalOrderBlockEngine
from trading_system.zones.dealing_range import CausalDealingRangeEngine
from trading_system.multitimeframe.causal_htf import CausalHTFAggregator, TimeAggregationSpec
from datetime import time as dtime

def timed(name, fn):
    t0 = time.time()
    out = fn()
    dt = time.time() - t0
    say(f"STAGE {name}: {dt:.1f}s")
    return out

say(f"== BENCH n={N} label={LABEL} ==")
vol = timed("dynamic_volatility_1_1", lambda: DynamicVolatilityEngine().analyze(mh))
sess = timed("session_context_1_2", lambda: CausalSessionContextEngine(()).analyze(mh))
fvg = timed("fvg_4_2a", lambda: CausalFVGEngine().analyze(mh))
fp = timed("flow_proxy_3_1", lambda: CausalVolumeDeltaEngine(mode=OrderFlowMode.OHLCV_PROXY).analyze(mh))
fa = timed("flow_actual_3_1", lambda: CausalVolumeDeltaEngine(mode=OrderFlowMode.ACTUAL_AGGRESSOR, reconcile_total_volume=True).analyze(actual))
ab_a = timed("absorption_actual_3_2", lambda: CausalAbsorptionEvidenceEngine(mode=OrderFlowMode.ACTUAL_AGGRESSOR).analyze(mh[["close"]].join(fa)))
ab_p = timed("absorption_proxy_3_2", lambda: CausalAbsorptionEvidenceEngine(mode=OrderFlowMode.OHLCV_PROXY).analyze(fp))
htf = timed("htf_5_1_1h", lambda: CausalHTFAggregator(spec=TimeAggregationSpec(duration=pd.Timedelta("1h"))).analyze(mh))

pol = EmpiricalConfirmationPolicy(quantile=0.5, prior_continuation_reversals=(0.005,))
sw = timed("swing_detector_2_1a", lambda: CausalAdaptiveSwingDetector(pol).analyze(mh))
swing_cols = ["swing_high_confirmed", "swing_low_confirmed", "swing_origin_position", "swing_price", "swing_confirmation_position"]
seq = timed("swing_sequence_2_1b", lambda: ConfirmedSwingSequenceEngine().analyze(sw[swing_cols]))
seq_keep = [c for c in ("swing_sequence_class", "structure_event_type", "current_structure_confirmation_position",
                        "current_structure_origin_position", "current_structure_swing_price",
                        "previous_same_type_origin_position", "previous_same_type_price",
                        "same_type_log_price_change", "comparison_available") if c in seq.columns]
st_in = mh[["high", "low", "close"]].join(sw[swing_cols]).join(seq[seq_keep])
stb = timed("structural_breaks_2_1c", lambda: CausalStructuralBreakEngine().analyze(st_in))
liq = timed("liquidity_2_2", lambda: CausalLiquidityMapEngine().analyze(st_in))
ob = timed("order_blocks_4_1", lambda: CausalOrderBlockEngine().analyze(mh[["open","high","low","close"]].join(sw[swing_cols]).join(stb[[c for c in ("structural_break_event","structure_state_before","high_close_breach_event","low_close_breach_event") if c in stb.columns]])))
dr = timed("dealing_range_4_2b", lambda: CausalDealingRangeEngine().analyze(sw[swing_cols].assign(close=mh["close"]).join(seq[seq_keep])))
say("== ENGINES DONE ==")

# timeline seal cost (consumer-side public API)
from trading_system.research.information_time import TimeIndexedTimelineAdapter
from trading_system.research.trajectory.trajectory_contract import MarketObservationTimeline
def _seal():
    ad = TimeIndexedTimelineAdapter(timeline_id="BENCH")
    return MarketObservationTimeline.seal(adapter=ad, market_history=mh)
timeline = timed("timeline_seal", _seal)

from trading_system.decision.evidence_vector import CausalEvidenceVectorEngine, EvidenceVectorConfig, OrderFlowEvidenceMode
from trading_system.decision.narrative import CausalMarketNarrativeEngine

def join_frame(flow_cols, flow_frame):
    frame = mh[["close"]].copy()
    frame = frame.join(vol[[c for c in ("true_range_percentile","true_range_history_count","normalized_tr_change","expansion_percentile","expansion_history_count") if c in vol.columns]])
    frame = frame.join(sess[[c for c in ("hour_utc_sin","hour_utc_cos","weekday_sin","weekday_cos") if c in sess.columns]])
    frame = frame.join(stb[[c for c in ("structure_state_after","structural_break_event") if c in stb.columns]])
    frame = frame.join(liq[0][[c for c in ("high_side_first_wick_only_count","low_side_first_wick_only_count","high_side_first_close_breach_count","low_side_first_close_breach_count","nearest_same_side_distance_fraction","nearest_distance_percentile","nearest_distance_reference_history_count") if c in liq[0].columns]])
    frame = frame.join(ob[[c for c in ("created_ob_displacement_fraction","created_ob_displacement_percentile","created_ob_displacement_history_count","bullish_ob_first_touch_count","bearish_ob_first_touch_count","bullish_ob_first_far_side_wick_breach_count","bearish_ob_first_far_side_wick_breach_count","bullish_ob_first_far_side_close_breach_count","bearish_ob_first_far_side_close_breach_count","bullish_ob_first_reclaim_count","bearish_ob_first_reclaim_count") if c in ob.columns]])
    frame = frame.join(dr[[c for c in ("current_range_position_raw","current_midpoint_displacement","current_discount_depth","current_premium_depth") if c in dr.columns]])
    frame = frame.join(fvg[[c for c in ("created_fvg_gap_width_fraction","created_fvg_gap_width_percentile","created_fvg_gap_width_history_count","bullish_fvg_first_touch_count","bearish_fvg_first_touch_count","bullish_fvg_first_full_range_coverage_count","bearish_fvg_first_full_range_coverage_count","bullish_fvg_first_far_side_wick_breach_count","bearish_fvg_first_far_side_wick_breach_count","bullish_fvg_first_far_side_close_breach_count","bearish_fvg_first_far_side_close_breach_count","bullish_fvg_first_close_reclaim_count","bearish_fvg_first_close_reclaim_count") if c in fvg.columns]])
    frame = frame.join(flow_frame[[c for c in flow_cols if c in flow_frame.columns]])
    return frame

fa_full = mh[["close"]].join(fa).join(ab_a[[c for c in ("actual_absorption_evidence","absorbed_aggression_side","opposed_response_percentile","opposed_response_history_count") if c in ab_a.columns]])
fp_full = fp.join(ab_p[[c for c in ("proxy_absorption_evidence","pressure_side","pressure_opposed_response_percentile","pressure_opposed_response_history_count") if c in ab_p.columns]])
actual_cols = ["delta_ratio","delta_ratio_percentile","delta_ratio_history_count","delta_magnitude_percentile","delta_magnitude_history_count","actual_absorption_evidence","absorbed_aggression_side","opposed_response_percentile","opposed_response_history_count"]
proxy_cols = ["volume_pressure_proxy","pressure_proxy_percentile","pressure_proxy_history_count","pressure_magnitude_percentile","pressure_magnitude_history_count","proxy_absorption_evidence","pressure_side","pressure_opposed_response_percentile","pressure_opposed_response_history_count"]

nar = CausalMarketNarrativeEngine()
for mode_name, fframe, cols, enum in (("actual", fa_full, actual_cols, OrderFlowEvidenceMode.ACTUAL),
                                       ("proxy", fp_full, proxy_cols, OrderFlowEvidenceMode.PROXY)):
    e_in = join_frame(cols, fframe)
    cfg_ev = EvidenceVectorConfig(environment=True, temporal_context=True, structure=True, liquidity=True,
                                  order_blocks=True, fvg=True, dealing_range=True, multiscale=False, order_flow_mode=enum)
    def _ev():
        return CausalEvidenceVectorEngine(config=cfg_ev).analyze(e_in)
    ev_df, mani = timed(f"evidence_6_1a_{mode_name}", _ev)
    timed(f"narrative_6_1b_{mode_name}", lambda: nar.analyze(ev_df, mani))
say("== EVIDENCE+NARRATIVE DONE ==")
