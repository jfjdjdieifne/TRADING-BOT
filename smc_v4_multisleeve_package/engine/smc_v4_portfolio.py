"""SMC V4 & V5 Multi-Sleeve Portfolio Engine (Zero-Lookahead).

V4 Legacy Sleeves:
1. `V3_NY`: Dual 4H+1H BOS Alignment -> 15m BOS Displacement FVG in NY Killzone (12-17 UTC), 2.5R TP.
2. `VisB`: 4H BOS Bias -> 1H Major Swing (k=3, >=4h age) Real Sweep -> 5m CHoCH + FVG, 2.5R TP.
3. `VisA`: 15m Major Swing (k=3) Zone + 5m Trendline (>=3 pivots) -> Tap -> CHoCH -> Target Origin.

V5 Upgraded Sleeves (Causal 1H Trailing & AMD/PO3 Expansion):
1. `V3_Pro`: `V3_NY` with `0.75 ATR` SL buffer + 1H (k=2) swing trail at +2.5R (+1.0R SL lock).
2. `VisB_Pro`: `VisB` with 1H (k=2) swing trail at +1.5R (+1.0R SL lock).
3. `VisA`: Kept at structural Origin TP (mean-reverting range exhaustion).
4. `AMD_Pro`: 15m Accumulation Range (8 bars <= 2.5 ATR) -> Fake Sweep Manipulation ->
   1H BOS Aligned Distribution (BOS + FVG) -> 1H (k=2) swing trail at +2.0R (+1.0R SL lock).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .causal_primitives import (
    build_causal_htf_structure,
    build_causal_swing_events,
    causal_atr14,
    detect_swings_causal,
    in_killzone_utc,
    resample_causal_tf,
)
from .smc_v3_trend_engine import SMCV3Config, run_smc_v3_backtest


def _sim_1m_path(
    *,
    engine: str,
    side: str,
    entry_idx: int,
    fill: float,
    sl: float,
    tp: float,
    h1: np.ndarray,
    l1: np.ndarray,
    t1: pd.DatetimeIndex,
    cost: float,
    setup_time: pd.Timestamp | None = None,
    be_act_r: float | None = None,
    be_lock_r: float = 1.0,
) -> dict[str, Any] | None:
    risk = (fill - sl) if side == "LONG" else (sl - fill)
    if risk <= 0:
        return None
    cur_sl = float(sl)
    be_px = (fill + float(be_act_r) * risk if side == "LONG" else fill - float(be_act_r) * risk) if be_act_r is not None else None
    be_on = False
    out_idx, out_px, out_lbl = entry_idx, fill, "EOD"
    if (side == "LONG" and l1[entry_idx] <= cur_sl) or (side == "SHORT" and h1[entry_idx] >= cur_sl):
        out_idx, out_px, out_lbl = entry_idx, cur_sl, "SL"
    else:
        for j in range(entry_idx + 1, len(t1)):
            if side == "LONG":
                if l1[j] <= cur_sl:
                    out_idx, out_px, out_lbl = j, cur_sl, ("BE" if be_on else "SL")
                    break
                if h1[j] >= tp:
                    out_idx, out_px, out_lbl = j, tp, "TP"
                    break
                if be_px is not None and not be_on and h1[j] >= be_px:
                    be_on = True
                    cur_sl = max(cur_sl, fill + float(be_lock_r) * risk)
            else:
                if h1[j] >= cur_sl:
                    out_idx, out_px, out_lbl = j, cur_sl, ("BE" if be_on else "SL")
                    break
                if l1[j] <= tp:
                    out_idx, out_px, out_lbl = j, tp, "TP"
                    break
                if be_px is not None and not be_on and l1[j] <= be_px:
                    be_on = True
                    cur_sl = min(cur_sl, fill - float(be_lock_r) * risk)
    gross_usd = (out_px - fill) if side == "LONG" else (fill - out_px)
    net_usd = gross_usd - cost
    return {
        "engine": engine,
        "side": side,
        "setup_time": str(setup_time) if setup_time is not None else str(t1[entry_idx]),
        "entry_time": str(t1[entry_idx]),
        "exit_time": str(t1[out_idx]),
        "entry_idx": entry_idx,
        "exit_idx": out_idx,
        "entry_price": float(fill),
        "sl_price": float(sl),
        "tp_price": float(tp),
        "exit_price": float(out_px),
        "outcome": out_lbl,
        "gross_usd": float(gross_usd),
        "net_usd": float(net_usd),
        "gross_r": float(gross_usd / risk),
        "net_r": float(net_usd / risk),
        "risk_usd": float(risk),
        "planned_rr": float(abs(tp - fill) / risk),
    }


def _sim_1m_trail_1h(
    *,
    engine: str,
    side: str,
    entry_idx: int,
    fill: float,
    sl: float,
    act_r: float,
    be_lock_r: float,
    h1: np.ndarray,
    l1: np.ndarray,
    t1: pd.DatetimeIndex,
    s1h_t: pd.DatetimeIndex,
    s1h_k: list[str],
    s1h_p: np.ndarray,
    cost: float,
    setup_time: pd.Timestamp | None = None,
) -> dict[str, Any] | None:
    risk = (fill - sl) if side == "LONG" else (sl - fill)
    if risk <= 0:
        return None
    act_px = fill + act_r * risk if side == "LONG" else fill - act_r * risk
    cur_sl = float(sl)
    trail_active = False
    out_idx, out_px, out_lbl = entry_idx, fill, "EOD"
    ptr = int(s1h_t.searchsorted(t1[entry_idx], side="right"))

    if (side == "LONG" and l1[entry_idx] <= cur_sl) or (side == "SHORT" and h1[entry_idx] >= cur_sl):
        out_idx, out_px, out_lbl = entry_idx, cur_sl, "SL"
    else:
        for j in range(entry_idx + 1, len(t1)):
            tj = t1[j]
            while ptr < len(s1h_t) and s1h_t[ptr] <= tj:
                if trail_active:
                    if side == "LONG" and s1h_k[ptr] == "low" and s1h_p[ptr] > cur_sl and s1h_p[ptr] < l1[j]:
                        cur_sl = float(s1h_p[ptr])
                    elif side == "SHORT" and s1h_k[ptr] == "high" and s1h_p[ptr] < cur_sl and s1h_p[ptr] > h1[j]:
                        cur_sl = float(s1h_p[ptr])
                ptr += 1

            if side == "LONG":
                if l1[j] <= cur_sl:
                    out_idx, out_px = j, cur_sl
                    out_lbl = "TRAIL" if trail_active else "SL"
                    break
                if not trail_active and h1[j] >= act_px:
                    trail_active = True
                    cur_sl = max(cur_sl, fill + be_lock_r * risk)
            else:
                if h1[j] >= cur_sl:
                    out_idx, out_px = j, cur_sl
                    out_lbl = "TRAIL" if trail_active else "SL"
                    break
                if not trail_active and l1[j] <= act_px:
                    trail_active = True
                    cur_sl = min(cur_sl, fill - be_lock_r * risk)

    gross_usd = (out_px - fill) if side == "LONG" else (fill - out_px)
    net_usd = gross_usd - cost
    return {
        "engine": engine,
        "side": side,
        "setup_time": str(setup_time) if setup_time is not None else str(t1[entry_idx]),
        "entry_time": str(t1[entry_idx]),
        "exit_time": str(t1[out_idx]),
        "entry_idx": entry_idx,
        "exit_idx": out_idx,
        "entry_price": float(fill),
        "sl_price": float(sl),
        "tp_price": float(act_px),
        "exit_price": float(out_px),
        "outcome": out_lbl,
        "gross_usd": float(gross_usd),
        "net_usd": float(net_usd),
        "gross_r": float(gross_usd / risk),
        "net_r": float(net_usd / risk),
        "risk_usd": float(risk),
        "planned_rr": float(act_r),
    }


def run_engine_vis_a(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    htf_freq: str = "15min",
    htf_k: int = 3,
    ltf_k: int = 2,
    entry_mode: str = "break_close",
    max_rr: float = 6.0,
    cost: float = 0.25,
) -> list[dict[str, Any]]:
    """Sleeve 3 (VisA): Trendline Liquidity Compression into HTF Zone + Sweep + Break to Origin."""
    tf5 = resample_causal_tf(df_1m, "5min")
    tfh = resample_causal_tf(df_1m, htf_freq)

    o5, h5, l5, c5 = tf5["Open"].to_numpy(), tf5["High"].to_numpy(), tf5["Low"].to_numpy(), tf5["Close"].to_numpy()
    end5, st5 = tf5.index, tf5["start_time"]
    f1m, l1m = tf5["first_1m_pos"].to_numpy(), tf5["last_1m_pos"].to_numpy()
    atr5 = causal_atr14(h5, l5, c5)
    sw5 = detect_swings_causal(h5, l5, end5, ltf_k)

    hh, lh = tfh["High"].to_numpy(), tfh["Low"].to_numpy()
    endh = tfh.index
    swh = detect_swings_causal(hh, lh, endh, htf_k)

    o1, h1, l1, t1 = df_1m["Open"].to_numpy(), df_1m["High"].to_numpy(), df_1m["Low"].to_numpy(), df_1m.index

    active_htf_highs, active_htf_lows = [], []
    recent_5m_lows, recent_5m_highs = [], []
    ph = 0
    pending, trades = [], []
    busy_until = -1
    last_zone_tap_short, last_zone_tap_long = -999, -999
    tap_high_px, tap_low_px = 0.0, 1e9
    warmup_start = eval_start - pd.Timedelta(hours=12)

    for i in range(len(tf5)):
        te, ts = end5[i], st5.iloc[i]
        while ph < len(endh) and endh[ph] <= te:
            active_htf_highs = [sp for sp in active_htf_highs if hh[ph] <= sp.price * 1.003 and (ph - sp.candle_idx) <= 120]
            active_htf_lows = [sp for sp in active_htf_lows if lh[ph] >= sp.price * 0.997 and (ph - sp.candle_idx) <= 120]
            for sp in swh.get(ph, []):
                if sp.kind == "high" and hh[sp.candle_idx + 1 : ph + 1].max() <= sp.price:
                    active_htf_highs.append(sp)
                elif sp.kind == "low" and lh[sp.candle_idx + 1 : ph + 1].min() >= sp.price:
                    active_htf_lows.append(sp)
            ph += 1

        new_p = []
        for st in pending:
            if i > st["expire"]:
                continue
            ps, pe = int(f1m[i]), int(l1m[i])
            if st["type"] == "next_open":
                m = ps
                tm = t1[m]
                if m > busy_until and eval_start <= tm < eval_end and in_killzone_utc(tm):
                    fill = float(o1[m])
                    risk = (fill - st["sl"]) if st["side"] == "LONG" else (st["sl"] - fill)
                    if risk > 0:
                        rr = abs(st["tp"] - fill) / risk
                        if 2.0 <= rr <= max_rr:
                            res = _sim_1m_path(
                                engine="VisA", side=st["side"], entry_idx=m, fill=fill,
                                sl=st["sl"], tp=st["tp"], h1=h1, l1=l1, t1=t1, cost=cost,
                                setup_time=st["setup_time"],
                            )
                            if res:
                                busy_until = res["exit_idx"]
                                trades.append(res)
                continue

            dead = False
            for m in range(ps, pe + 1):
                tm = t1[m]
                if st["side"] == "SHORT":
                    if o1[m] >= st["sl"] or o1[m] <= st["tp"]:
                        dead = True
                        break
                    if h1[m] >= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm):
                            if h1[m] >= st["sl"] or l1[m] <= st["tp"] or m <= busy_until:
                                dead = True
                                break
                            continue
                        if not (eval_start <= tm < eval_end):
                            continue
                        fill = max(float(o1[m]), st["trig"])
                        risk = st["sl"] - fill
                        if risk > 0 and 2.0 <= (fill - st["tp"]) / risk <= max_rr:
                            res = _sim_1m_path(
                                engine="VisA", side="SHORT", entry_idx=m, fill=fill,
                                sl=st["sl"], tp=st["tp"], h1=h1, l1=l1, t1=t1, cost=cost,
                                setup_time=st["setup_time"],
                            )
                            if res:
                                busy_until = res["exit_idx"]
                                trades.append(res)
                        dead = True
                        break
                else:
                    if o1[m] <= st["sl"] or o1[m] >= st["tp"]:
                        dead = True
                        break
                    if l1[m] <= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm):
                            if l1[m] <= st["sl"] or h1[m] >= st["tp"] or m <= busy_until:
                                dead = True
                                break
                            continue
                        if not (eval_start <= tm < eval_end):
                            continue
                        fill = min(float(o1[m]), st["trig"])
                        risk = fill - st["sl"]
                        if risk > 0 and 2.0 <= (st["tp"] - fill) / risk <= max_rr:
                            res = _sim_1m_path(
                                engine="VisA", side="LONG", entry_idx=m, fill=fill,
                                sl=st["sl"], tp=st["tp"], h1=h1, l1=l1, t1=t1, cost=cost,
                                setup_time=st["setup_time"],
                            )
                            if res:
                                busy_until = res["exit_idx"]
                                trades.append(res)
                        dead = True
                        break
            if not dead:
                new_p.append(st)
        pending = new_p

        a5 = float(atr5[i]) if np.isfinite(atr5[i]) else 1.5
        buf = max(1.00, 0.5 * a5)

        for sp in active_htf_highs:
            if h5[i] >= sp.price - 0.5 * a5:
                tap_high_px = float(h5[i]) if (i - last_zone_tap_short > 18) else max(tap_high_px, float(h5[i]))
                last_zone_tap_short = i
        for sp in active_htf_lows:
            if l5[i] <= sp.price + 0.5 * a5:
                tap_low_px = float(l5[i]) if (i - last_zone_tap_long > 18) else min(tap_low_px, float(l5[i]))
                last_zone_tap_long = i

        if in_killzone_utc(ts) and warmup_start <= te < eval_end and i >= 1:
            if (i - last_zone_tap_short) <= 12 and len(recent_5m_lows) >= 3:
                la, lb, lc = recent_5m_lows[-3], recent_5m_lows[-2], recent_5m_lows[-1]
                if la.price < lb.price < lc.price and (i - la.candle_idx) <= 72 and lc.candle_idx < i:
                    if c5[i - 1] >= lc.price and c5[i] < lc.price:
                        sl = max(tap_high_px, float(h5[max(0, i - 6) : i + 1].max())) + buf
                        tp = float(la.price)
                        if entry_mode == "break_close":
                            pending.append({"type": "next_open", "side": "SHORT", "sl": sl, "tp": tp, "expire": i + 1, "setup_time": te})
                        else:
                            pending.append({"type": "limit", "side": "SHORT", "trig": float(lc.price), "sl": sl, "tp": tp, "expire": i + 12, "setup_time": te})
                        last_zone_tap_short = -999

            if (i - last_zone_tap_long) <= 12 and len(recent_5m_highs) >= 3:
                ha, hb, hc = recent_5m_highs[-3], recent_5m_highs[-2], recent_5m_highs[-1]
                if ha.price > hb.price > hc.price and (i - ha.candle_idx) <= 72 and hc.candle_idx < i:
                    if c5[i - 1] <= hc.price and c5[i] > hc.price:
                        sl = min(tap_low_px, float(l5[max(0, i - 6) : i + 1].min())) - buf
                        tp = float(ha.price)
                        if entry_mode == "break_close":
                            pending.append({"type": "next_open", "side": "LONG", "sl": sl, "tp": tp, "expire": i + 1, "setup_time": te})
                        else:
                            pending.append({"type": "limit", "side": "LONG", "trig": float(hc.price), "sl": sl, "tp": tp, "expire": i + 12, "setup_time": te})
                        last_zone_tap_long = -999

        for sp in sw5.get(i, []):
            if sp.kind == "low":
                recent_5m_lows.append(sp)
                if len(recent_5m_lows) > 20:
                    recent_5m_lows = recent_5m_lows[-15:]
            else:
                recent_5m_highs.append(sp)
                if len(recent_5m_highs) > 20:
                    recent_5m_highs = recent_5m_highs[-15:]

    return trades


def run_engine_vis_b(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    htf_freq: str = "1h",
    htf_k: int = 3,
    min_htf_age: int = 4,
    disp_atr: float = 0.8,
    fvg_atr: float = 0.20,
    rr: float = 2.5,
    htf_align: bool = True,
    cost: float = 0.25,
    trail_1h_after_r: float | None = None,
    be_lock_r: float = 1.0,
    engine_label: str = "VisB",
) -> list[dict[str, Any]]:
    """Sleeve 2 (VisB / VisB_Pro): 4H BOS Bias -> 1H Major Swing Sweep -> 5m CHoCH + FVG."""
    tf5 = resample_causal_tf(df_1m, "5min")
    tfh = resample_causal_tf(df_1m, htf_freq)

    o5, h5, l5, c5 = tf5["Open"].to_numpy(), tf5["High"].to_numpy(), tf5["Low"].to_numpy(), tf5["Close"].to_numpy()
    end5, st5 = tf5.index, tf5["start_time"]
    f1m, l1m = tf5["first_1m_pos"].to_numpy(), tf5["last_1m_pos"].to_numpy()
    atr5 = causal_atr14(h5, l5, c5)
    sw5 = detect_swings_causal(h5, l5, end5, 2)

    hh, lh, ch = tfh["High"].to_numpy(), tfh["Low"].to_numpy(), tfh["Close"].to_numpy()
    endh = tfh.index
    swh = detect_swings_causal(hh, lh, endh, htf_k)
    e4, t4 = build_causal_htf_structure(df_1m, "4h", 2)

    use_1h_trail = trail_1h_after_r is not None
    if use_1h_trail:
        s1h_t, s1h_k, s1h_p = build_causal_swing_events(df_1m, "1h", 2)
    else:
        s1h_t, s1h_k, s1h_p = pd.DatetimeIndex([]), [], np.array([], dtype=np.float64)

    o1, h1, l1, t1 = df_1m["Open"].to_numpy(), df_1m["High"].to_numpy(), df_1m["Low"].to_numpy(), df_1m.index

    active_h, active_l = [], []
    last5_sh, last5_sl = None, None
    ph, p4, cur_4h = 0, 0, 0
    sweep_cands, pending, trades = [], [], []
    busy_until = -1
    warmup_start = eval_start - pd.Timedelta(hours=12)

    for i in range(len(tf5)):
        te, ts = end5[i], st5.iloc[i]
        while p4 < len(e4) and e4[p4] <= te:
            cur_4h = int(t4[p4])
            p4 += 1

        while ph < len(endh) and endh[ph] <= te:
            for sp in active_l:
                if (ph - sp.candle_idx) >= min_htf_age and lh[ph] < sp.price and ch[ph] > sp.price:
                    sweep_cands.append({"side": "LONG", "start_i": i, "sl_base": float(lh[ph]), "choch_lvl": last5_sh})
            for sp in active_h:
                if (ph - sp.candle_idx) >= min_htf_age and hh[ph] > sp.price and ch[ph] < sp.price:
                    sweep_cands.append({"side": "SHORT", "start_i": i, "sl_base": float(hh[ph]), "choch_lvl": last5_sl})

            active_h = [sp for sp in active_h if hh[ph] <= sp.price and (ph - sp.candle_idx) <= 120]
            active_l = [sp for sp in active_l if lh[ph] >= sp.price and (ph - sp.candle_idx) <= 120]
            for sp in swh.get(ph, []):
                if sp.kind == "high" and hh[sp.candle_idx + 1 : ph + 1].max() <= sp.price:
                    active_h.append(sp)
                elif sp.kind == "low" and lh[sp.candle_idx + 1 : ph + 1].min() >= sp.price:
                    active_l.append(sp)
            ph += 1

        new_p = []
        for st in pending:
            if i > st["expire"]:
                continue
            ps, pe = int(f1m[i]), int(l1m[i])
            dead = False
            for m in range(ps, pe + 1):
                tm = t1[m]
                if st["side"] == "LONG":
                    if o1[m] <= st["sl"] or o1[m] >= st["tp"]:
                        dead = True
                        break
                    if l1[m] <= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm):
                            if l1[m] <= st["sl"] or h1[m] >= st["tp"] or m <= busy_until:
                                dead = True
                                break
                            continue
                        if not (eval_start <= tm < eval_end):
                            continue
                        fill = min(float(o1[m]), st["trig"])
                        if use_1h_trail:
                            res = _sim_1m_trail_1h(
                                engine=engine_label, side="LONG", entry_idx=m, fill=fill,
                                sl=st["sl"], act_r=float(trail_1h_after_r), be_lock_r=be_lock_r,
                                h1=h1, l1=l1, t1=t1, s1h_t=s1h_t, s1h_k=s1h_k, s1h_p=s1h_p,
                                cost=cost, setup_time=st["setup_time"],
                            )
                        else:
                            res = _sim_1m_path(
                                engine=engine_label, side="LONG", entry_idx=m, fill=fill,
                                sl=st["sl"], tp=st["tp"], h1=h1, l1=l1, t1=t1, cost=cost,
                                setup_time=st["setup_time"],
                            )
                        if res:
                            busy_until = res["exit_idx"]
                            trades.append(res)
                        dead = True
                        break
                else:
                    if o1[m] >= st["sl"] or o1[m] <= st["tp"]:
                        dead = True
                        break
                    if h1[m] >= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm):
                            if h1[m] >= st["sl"] or l1[m] <= st["tp"] or m <= busy_until:
                                dead = True
                                break
                            continue
                        if not (eval_start <= tm < eval_end):
                            continue
                        fill = max(float(o1[m]), st["trig"])
                        if use_1h_trail:
                            res = _sim_1m_trail_1h(
                                engine=engine_label, side="SHORT", entry_idx=m, fill=fill,
                                sl=st["sl"], act_r=float(trail_1h_after_r), be_lock_r=be_lock_r,
                                h1=h1, l1=l1, t1=t1, s1h_t=s1h_t, s1h_k=s1h_k, s1h_p=s1h_p,
                                cost=cost, setup_time=st["setup_time"],
                            )
                        else:
                            res = _sim_1m_path(
                                engine=engine_label, side="SHORT", entry_idx=m, fill=fill,
                                sl=st["sl"], tp=st["tp"], h1=h1, l1=l1, t1=t1, cost=cost,
                                setup_time=st["setup_time"],
                            )
                        if res:
                            busy_until = res["exit_idx"]
                            trades.append(res)
                        dead = True
                        break
            if not dead:
                new_p.append(st)
        pending = new_p

        if i >= 2 and in_killzone_utc(ts) and warmup_start <= te < eval_end:
            a5 = float(atr5[i]) if np.isfinite(atr5[i]) else 1.5
            buf = max(1.00, 0.5 * a5)
            c1i, c2i, c3i = i - 2, i - 1, i
            c2b = abs(float(c5[c2i] - o5[c2i]))
            still = []
            for sc in sweep_cands:
                if i - sc["start_i"] > 12:
                    continue
                if sc["side"] == "LONG":
                    if l5[i] < sc["sl_base"]:
                        continue
                    gap = float(l5[c3i] - h5[c1i])
                    choch_ok = sc["choch_lvl"] is not None and c5[c3i] > sc["choch_lvl"]
                    if gap >= 0.20 and c5[c2i] > o5[c2i] and c2b >= disp_atr * a5 and gap >= fvg_atr * a5 and choch_ok:
                        if not htf_align or cur_4h == 1:
                            trig = float(l5[c3i])
                            sl = sc["sl_base"] - buf
                            risk = trig - sl
                            if risk > 0:
                                pending.append({"side": "LONG", "trig": trig, "sl": sl, "tp": trig + rr * risk, "expire": i + 18, "setup_time": te})
                                continue
                else:
                    if h5[i] > sc["sl_base"]:
                        continue
                    gap = float(l5[c1i] - h5[c3i])
                    choch_ok = sc["choch_lvl"] is not None and c5[c3i] < sc["choch_lvl"]
                    if gap >= 0.20 and c5[c2i] < o5[c2i] and c2b >= disp_atr * a5 and gap >= fvg_atr * a5 and choch_ok:
                        if not htf_align or cur_4h == -1:
                            trig = float(h5[c3i])
                            sl = sc["sl_base"] + buf
                            risk = sl - trig
                            if risk > 0:
                                pending.append({"side": "SHORT", "trig": trig, "sl": sl, "tp": trig - rr * risk, "expire": i + 18, "setup_time": te})
                                continue
                still.append(sc)
            sweep_cands = still

        for sp in sw5.get(i, []):
            if sp.kind == "high":
                last5_sh = sp.price
            else:
                last5_sl = sp.price

    return trades


def run_engine_vis_b_pro(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    cost: float = 0.25,
) -> list[dict[str, Any]]:
    """Upgraded Sleeve 2 (`VisB_Pro`): 1H (k=2) swing trail at +1.5R with +1.0R SL lock."""
    return run_engine_vis_b(
        df_1m,
        eval_start,
        eval_end,
        htf_freq="1h",
        htf_k=3,
        htf_align=True,
        cost=cost,
        trail_1h_after_r=1.5,
        be_lock_r=1.0,
        engine_label="VisB_Pro",
    )


def run_engine_amd_pro(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    range_bars: int = 8,
    max_box_atr: float = 2.5,
    disp_atr: float = 0.8,
    fvg_atr: float = 0.25,
    trail_1h_after_r: float = 2.0,
    be_lock_r: float = 1.0,
    cost: float = 0.25,
) -> list[dict[str, Any]]:
    """Sleeve 4 (`AMD_Pro`): 15m Accumulation Range -> Manipulation Fake Sweep -> 1H-Aligned BOS + FVG -> 1H Trail."""
    tf15 = resample_causal_tf(df_1m, "15min")
    o15, h15, l15, c15 = tf15["Open"].to_numpy(), tf15["High"].to_numpy(), tf15["Low"].to_numpy(), tf15["Close"].to_numpy()
    end15, st15 = tf15.index, tf15["start_time"]
    f1m15, l1m15 = tf15["first_1m_pos"].to_numpy(), tf15["last_1m_pos"].to_numpy()
    atr15 = causal_atr14(h15, l15, c15)

    e1, t1h = build_causal_htf_structure(df_1m, "1h", 2)
    s1h_t, s1h_k, s1h_p = build_causal_swing_events(df_1m, "1h", 2)
    o1, h1, l1, t1 = df_1m["Open"].to_numpy(), df_1m["High"].to_numpy(), df_1m["Low"].to_numpy(), df_1m.index

    p1, cur1 = 0, 0
    manips: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    busy_until = -1
    warmup_start = eval_start - pd.Timedelta(hours=12)

    for i in range(max(12, range_bars + 2), len(tf15)):
        te, ts = end15[i], st15.iloc[i]
        while p1 < len(e1) and e1[p1] <= te:
            cur1 = int(t1h[p1])
            p1 += 1

        npend = []
        for st in pending:
            if i > st["expire"]:
                continue
            ps, pe = int(f1m15[i]), int(l1m15[i])
            dead = False
            for m in range(ps, pe + 1):
                tm = t1[m]
                if st["side"] == "LONG":
                    if o1[m] <= st["sl"]:
                        dead = True
                        break
                    if l1[m] <= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm) or not (eval_start <= tm < eval_end):
                            if m <= busy_until or l1[m] <= st["sl"]:
                                dead = True
                                break
                            continue
                        res = _sim_1m_trail_1h(
                            engine="AMD_Pro", side="LONG", entry_idx=m,
                            fill=min(float(o1[m]), st["trig"]), sl=st["sl"],
                            act_r=trail_1h_after_r, be_lock_r=be_lock_r,
                            h1=h1, l1=l1, t1=t1, s1h_t=s1h_t, s1h_k=s1h_k, s1h_p=s1h_p,
                            cost=cost, setup_time=st["setup_time"],
                        )
                        if res:
                            busy_until = res["exit_idx"]
                            trades.append(res)
                        dead = True
                        break
                else:
                    if o1[m] >= st["sl"]:
                        dead = True
                        break
                    if h1[m] >= st["trig"]:
                        if m <= busy_until or not in_killzone_utc(tm) or not (eval_start <= tm < eval_end):
                            if m <= busy_until or h1[m] >= st["sl"]:
                                dead = True
                                break
                            continue
                        res = _sim_1m_trail_1h(
                            engine="AMD_Pro", side="SHORT", entry_idx=m,
                            fill=max(float(o1[m]), st["trig"]), sl=st["sl"],
                            act_r=trail_1h_after_r, be_lock_r=be_lock_r,
                            h1=h1, l1=l1, t1=t1, s1h_t=s1h_t, s1h_k=s1h_k, s1h_p=s1h_p,
                            cost=cost, setup_time=st["setup_time"],
                        )
                        if res:
                            busy_until = res["exit_idx"]
                            trades.append(res)
                        dead = True
                        break
            if not dead:
                npend.append(st)
        pending = npend

        a = float(atr15[i])
        if not np.isfinite(a) or a <= 0 or te < warmup_start or te >= eval_end:
            continue

        box_hi = float(h15[i - range_bars : i].max())
        box_lo = float(l15[i - range_bars : i].min())
        if (box_hi - box_lo) <= max_box_atr * a:
            if l15[i] < box_lo and c15[i] >= box_lo - 0.8 * a:
                manips.append({"side": "LONG", "r_hi": box_hi, "r_lo": box_lo, "ext": float(l15[i]), "si": i})
            if h15[i] > box_hi and c15[i] <= box_hi + 0.8 * a:
                manips.append({"side": "SHORT", "r_hi": box_hi, "r_lo": box_lo, "ext": float(h15[i]), "si": i})

        new_m = []
        c1i, c2i, c3i = i - 2, i - 1, i
        c2b = abs(float(c15[c2i] - o15[c2i]))
        for mp in manips:
            if i - mp["si"] > 8:
                continue
            if mp["side"] == "LONG":
                mp["ext"] = min(mp["ext"], float(l15[i]))
                gap = float(l15[c3i] - h15[c1i])
                if c15[i] > mp["r_hi"] and gap >= fvg_atr * a and c15[c2i] > o15[c2i] and c2b >= disp_atr * a and cur1 == 1 and in_killzone_utc(ts):
                    trig = float(l15[c3i])
                    sl = mp["ext"] - 0.5 * a
                    if trig - sl > 0:
                        pending.append({"side": "LONG", "trig": trig, "sl": sl, "expire": i + 20, "setup_time": te})
                        continue
            else:
                mp["ext"] = max(mp["ext"], float(h15[i]))
                gap = float(l15[c1i] - h15[c3i])
                if c15[i] < mp["r_lo"] and gap >= fvg_atr * a and c15[c2i] < o15[c2i] and c2b >= disp_atr * a and cur1 == -1 and in_killzone_utc(ts):
                    trig = float(h15[c3i])
                    sl = mp["ext"] + 0.5 * a
                    if sl - trig > 0:
                        pending.append({"side": "SHORT", "trig": trig, "sl": sl, "expire": i + 20, "setup_time": te})
                        continue
            new_m.append(mp)
        manips = new_m

    return trades


def apply_cost_reprice(trades: list[dict[str, Any]], cost: float) -> list[dict[str, Any]]:
    """Recompute net USD & net R for an alternative round-trip cost without altering fills."""
    out = []
    for t in trades:
        nt = dict(t)
        nt["net_usd"] = float(nt["gross_usd"] - cost)
        nt["net_r"] = float(nt["net_usd"] / nt["risk_usd"])
        out.append(nt)
    return out


def lock_single_position(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chronological filter allowing at most 1 open position across all sleeves."""
    ordered = sorted(trades, key=lambda x: (pd.Timestamp(x["entry_time"]), pd.Timestamp(x["exit_time"])))
    kept: list[dict[str, Any]] = []
    busy_until = pd.Timestamp.min.tz_localize("UTC")
    for tr in ordered:
        et = pd.Timestamp(tr["entry_time"])
        if et > busy_until:
            kept.append(tr)
            busy_until = pd.Timestamp(tr["exit_time"])
    kept.sort(key=lambda x: pd.Timestamp(x["exit_time"]))
    return kept


def simulate_compounded_account(
    trades: list[dict[str, Any]],
    *,
    start_capital: float = 100.0,
    risk_pct: float = 0.02,
    compound: bool = True,
) -> dict[str, Any]:
    """Simulate real-world equity compounding sequentially by trade exit_time."""
    ordered = sorted(trades, key=lambda x: pd.Timestamp(x["exit_time"]))
    eq = float(start_capital)
    peak = eq
    max_dd_pct = 0.0
    yearly_equity: dict[str, float] = {}
    for tr in ordered:
        risk_usd = (eq * risk_pct) if compound else (start_capital * risk_pct)
        eq += risk_usd * float(tr["net_r"])
        if eq <= 0:
            eq = 0.0
            break
        peak = max(peak, eq)
        max_dd_pct = max(max_dd_pct, 100.0 * (peak - eq) / peak)
        yearly_equity[str(pd.Timestamp(tr["exit_time"]).year)] = round(eq, 2)
    return {
        "start_capital": round(start_capital, 2),
        "risk_pct": round(100.0 * risk_pct, 2),
        "compound": compound,
        "final_equity": round(eq, 2),
        "total_return_pct": round(100.0 * (eq / start_capital - 1.0), 1),
        "max_dd_pct": round(max_dd_pct, 2),
        "yearly_equity": yearly_equity,
    }


def run_smc_v4_portfolio(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    cost: float = 0.25,
    single_position_lock: bool = False,
) -> dict[str, Any]:
    """Run all 3 causal V4 sleeves and combine into V4_MultiSleeve."""
    t_v3 = run_smc_v3_backtest(
        df_1m,
        SMCV3Config(killzone_mode="ny", rr_target=2.5, round_trip_cost_usd=cost),
        eval_start,
        eval_end,
    )["trades"]
    t_vb = run_engine_vis_b(df_1m, eval_start, eval_end, htf_freq="1h", htf_k=3, htf_align=True, cost=cost)
    t_va = run_engine_vis_a(df_1m, eval_start, eval_end, htf_freq="15min", htf_k=3, entry_mode="break_close", cost=cost)

    combined = sorted(t_v3 + t_vb + t_va, key=lambda x: (pd.Timestamp(x["entry_time"]), pd.Timestamp(x["exit_time"])))
    if single_position_lock:
        combined = lock_single_position(combined)
    else:
        combined.sort(key=lambda x: pd.Timestamp(x["exit_time"]))

    return {
        "combined": combined,
        "v3_ny": t_v3,
        "vis_b": t_vb,
        "vis_a": t_va,
    }


def run_smc_v5_portfolio(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    cost: float = 0.25,
    single_position_lock: bool = True,
) -> dict[str, Any]:
    """Run all 4 upgraded causal V5 sleeves (V3_Pro + VisB_Pro + VisA + AMD_Pro)."""
    t_v3p = run_smc_v3_backtest(
        df_1m,
        SMCV3Config(
            killzone_mode="ny",
            sl_buffer_atr_mult=0.75,
            rr_target=2.5,
            round_trip_cost_usd=cost,
            trail_1h_after_r=2.5,
            be_lock_r=1.0,
            engine_label="V3_Pro",
        ),
        eval_start,
        eval_end,
    )["trades"]
    t_vbp = run_engine_vis_b_pro(df_1m, eval_start, eval_end, cost=cost)
    t_va = run_engine_vis_a(df_1m, eval_start, eval_end, htf_freq="15min", htf_k=3, entry_mode="break_close", cost=cost)
    t_amd = run_engine_amd_pro(df_1m, eval_start, eval_end, cost=cost)

    unlocked = sorted(t_v3p + t_vbp + t_va + t_amd, key=lambda x: pd.Timestamp(x["exit_time"]))
    locked = lock_single_position(unlocked)

    return {
        "combined": locked if single_position_lock else unlocked,
        "v5_1pos_lock": locked,
        "v5_unlocked": unlocked,
        "v3_pro": t_v3p,
        "vis_b_pro": t_vbp,
        "vis_a": t_va,
        "amd_pro": t_amd,
    }


def run_engine_ltf_1m(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    min_risk_abs: float = 2.00,
    min_risk_pct: float = 0.0010,
    rr: float = 3.0,
    cost: float = 0.25,
    engine_label: str = "XAU_LTF1M",
) -> list[dict[str, Any]]:
    """Sleeve 5 (`XAU_LTF1M`): Dual 4H+1H BOS Bias -> 15m (k=2) Sweep -> 1m CHoCH + 1m FVG (3.0R TP)."""
    tf15 = resample_causal_tf(df_1m, "15min")
    h15, l15, c15 = tf15["High"].to_numpy(), tf15["Low"].to_numpy(), tf15["Close"].to_numpy()
    end15 = tf15.index
    sw15 = detect_swings_causal(h15, l15, end15, 2)

    e4, t4 = build_causal_htf_structure(df_1m, "4h", 2)
    e1, t1h = build_causal_htf_structure(df_1m, "1h", 2)

    o1 = df_1m["Open"].to_numpy()
    h1 = df_1m["High"].to_numpy()
    l1 = df_1m["Low"].to_numpy()
    c1 = df_1m["Close"].to_numpy()
    t1_idx = df_1m.index
    atr1 = causal_atr14(h1, l1, c1)
    sw1 = detect_swings_causal(h1, l1, t1_idx, 2)

    p15, p4, p1 = 0, 0, 0
    cur_4h, cur_1h = 0, 0
    act_h15: list[Any] = []
    act_l15: list[Any] = []
    last1_sh: float | None = None
    last1_sl: float | None = None
    cands: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    busy_until = -1
    warmup = eval_start - pd.Timedelta(hours=12)

    for m in range(len(t1_idx)):
        tm = t1_idx[m]
        while p4 < len(e4) and e4[p4] <= tm:
            cur_4h = int(t4[p4])
            p4 += 1
        while p1 < len(e1) and e1[p1] <= tm:
            cur_1h = int(t1h[p1])
            p1 += 1
        while p15 < len(end15) and end15[p15] <= tm:
            for sp in act_l15:
                if (p15 - sp.candle_idx) >= 2 and l15[p15] < sp.price and c15[p15] > sp.price:
                    cands.append({"side": "LONG", "start_m": m, "sl_base": float(l15[p15]), "choch": last1_sh})
            for sp in act_h15:
                if (p15 - sp.candle_idx) >= 2 and h15[p15] > sp.price and c15[p15] < sp.price:
                    cands.append({"side": "SHORT", "start_m": m, "sl_base": float(h15[p15]), "choch": last1_sl})
            act_h15 = [sp for sp in act_h15 if h15[p15] <= sp.price and (p15 - sp.candle_idx) <= 48]
            act_l15 = [sp for sp in act_l15 if l15[p15] >= sp.price and (p15 - sp.candle_idx) <= 48]
            for sp in sw15.get(p15, []):
                if sp.kind == "high" and h15[sp.candle_idx + 1 : p15 + 1].max() <= sp.price:
                    act_h15.append(sp)
                elif sp.kind == "low" and l15[sp.candle_idx + 1 : p15 + 1].min() >= sp.price:
                    act_l15.append(sp)
            p15 += 1

        new_p = []
        for st in pending:
            if m > st["expire"]:
                continue
            if st["side"] == "LONG":
                if o1[m] <= st["sl"] or o1[m] >= st["tp"]:
                    continue
                if l1[m] <= st["trig"]:
                    if m <= busy_until or not in_killzone_utc(tm):
                        if l1[m] <= st["sl"] or h1[m] >= st["tp"] or m <= busy_until:
                            continue
                        new_p.append(st)
                        continue
                    if not (eval_start <= tm < eval_end):
                        continue
                    fill = min(float(o1[m]), st["trig"])
                    res = _sim_1m_path(
                        engine=engine_label,
                        side="LONG",
                        entry_idx=m,
                        fill=fill,
                        sl=st["sl"],
                        tp=st["tp"],
                        h1=h1,
                        l1=l1,
                        t1=t1_idx,
                        cost=cost,
                        setup_time=st["setup_time"],
                    )
                    if res:
                        busy_until = res["exit_idx"]
                        trades.append(res)
                    continue
            else:
                if o1[m] >= st["sl"] or o1[m] <= st["tp"]:
                    continue
                if h1[m] >= st["trig"]:
                    if m <= busy_until or not in_killzone_utc(tm):
                        if h1[m] >= st["sl"] or l1[m] <= st["tp"] or m <= busy_until:
                            continue
                        new_p.append(st)
                        continue
                    if not (eval_start <= tm < eval_end):
                        continue
                    fill = max(float(o1[m]), st["trig"])
                    res = _sim_1m_path(
                        engine=engine_label,
                        side="SHORT",
                        entry_idx=m,
                        fill=fill,
                        sl=st["sl"],
                        tp=st["tp"],
                        h1=h1,
                        l1=l1,
                        t1=t1_idx,
                        cost=cost,
                        setup_time=st["setup_time"],
                    )
                    if res:
                        busy_until = res["exit_idx"]
                        trades.append(res)
                    continue
            new_p.append(st)
        pending = new_p

        if m >= 2 and in_killzone_utc(tm) and warmup <= tm < eval_end:
            a1 = float(atr1[m]) if np.isfinite(atr1[m]) else 0.5
            buf = max(0.50, 1.0 * a1)
            min_r = max(min_risk_abs, float(c1[m]) * min_risk_pct)
            c1i, c2i, c3i = m - 2, m - 1, m
            c2b = abs(float(c1[c2i] - o1[c2i]))
            still = []
            for sc in cands:
                if m - sc["start_m"] > 20:
                    continue
                if sc["side"] == "LONG":
                    if l1[m] < sc["sl_base"]:
                        continue
                    gap = float(l1[c3i] - h1[c1i])
                    if (
                        cur_1h == 1
                        and cur_4h == 1
                        and sc["choch"] is not None
                        and c1[c3i] > sc["choch"]
                        and gap >= max(0.15, 0.25 * a1)
                        and c1[c2i] > o1[c2i]
                        and c2b >= 1.0 * a1
                    ):
                        trig = float(l1[c3i])
                        sl = sc["sl_base"] - buf
                        risk = trig - sl
                        if risk >= min_r:
                            pending.append(
                                {"side": "LONG", "trig": trig, "sl": sl, "tp": trig + rr * risk, "expire": m + 20, "setup_time": tm}
                            )
                            continue
                else:
                    if h1[m] > sc["sl_base"]:
                        continue
                    gap = float(l1[c1i] - h1[c3i])
                    if (
                        cur_1h == -1
                        and cur_4h == -1
                        and sc["choch"] is not None
                        and c1[c3i] < sc["choch"]
                        and gap >= max(0.15, 0.25 * a1)
                        and c1[c2i] < o1[c2i]
                        and c2b >= 1.0 * a1
                    ):
                        trig = float(h1[c3i])
                        sl = sc["sl_base"] + buf
                        risk = sl - trig
                        if risk >= min_r:
                            pending.append(
                                {"side": "SHORT", "trig": trig, "sl": sl, "tp": trig - rr * risk, "expire": m + 20, "setup_time": tm}
                            )
                            continue
                still.append(sc)
            cands = still

        for sp in sw1.get(m, []):
            if sp.kind == "high":
                last1_sh = sp.price
            else:
                last1_sl = sp.price

    return trades


def run_smc_v6_xau_portfolio(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    cost: float = 0.25,
    single_position_lock: bool = True,
) -> dict[str, Any]:
    """Run 5-sleeve causal XAUUSD V6 portfolio (V5 + fast XAU_LTF1M 15m-sweep->1m sleeve)."""
    v5 = run_smc_v5_portfolio(df_1m, eval_start, eval_end, cost=cost, single_position_lock=False)
    t_ltf = run_engine_ltf_1m(df_1m, eval_start, eval_end, cost=cost)

    unlocked = sorted(v5["v5_unlocked"] + t_ltf, key=lambda x: pd.Timestamp(x["exit_time"]))
    locked = lock_single_position(unlocked)

    return {
        "combined": locked if single_position_lock else unlocked,
        "v6_1pos_lock": locked,
        "v6_unlocked": unlocked,
        "v5_1pos_lock": v5["v5_1pos_lock"],
        "v5_unlocked": v5["v5_unlocked"],
        "v3_pro": v5["v3_pro"],
        "vis_b_pro": v5["vis_b_pro"],
        "vis_a": v5["vis_a"],
        "amd_pro": v5["amd_pro"],
        "ltf_1m": t_ltf,
    }


def run_engine_sniper_htf(
    df_ltf: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "XAUUSD",
    sweep_tf: str = "1h",
    sweep_k: int = 3,
    min_age: int = 4,
    htf_mode: str = "dual",
    min_risk_abs: float = 0.0,
    min_risk_pct: float = 0.0010,
    fixed_rr: float | None = 15.0,
    trail_1h_after_r: float | None = None,
    be_act_r: float | None = None,
    be_lock_r: float = 1.5,
    entry_mode: str = "fvg_edge",
    require_cisd: bool = False,
    use_killzone: bool = True,
    min_hour_utc: int | None = None,
    cost: float = 0.25,
    pct_cost: float = 0.0,
    engine_label: str = "Sniper_HTF",
) -> list[dict[str, Any]]:
    """Causal HTF-Sweep -> LTF (1m/5m) CHoCH+FVG (or ICT OB/BISI+CISD) Sniper Engine."""
    tf_sw = resample_causal_tf(df_ltf, sweep_tf)
    hs, ls, cs = tf_sw["High"].to_numpy(), tf_sw["Low"].to_numpy(), tf_sw["Close"].to_numpy()
    ends = tf_sw.index
    sw_htf = detect_swings_causal(hs, ls, ends, sweep_k)

    e4, t4 = build_causal_htf_structure(df_ltf, "4h", 2)
    e1, t1h = build_causal_htf_structure(df_ltf, "1h", 2)
    s1h_t, s1h_k, s1h_p = build_causal_swing_events(df_ltf, "1h", 2)

    o1 = df_ltf["Open"].to_numpy()
    h1 = df_ltf["High"].to_numpy()
    l1 = df_ltf["Low"].to_numpy()
    c1 = df_ltf["Close"].to_numpy()
    t1_idx = df_ltf.index
    atr1 = causal_atr14(h1, l1, c1)
    sw1 = detect_swings_causal(h1, l1, t1_idx, 2)

    ps, p4, p1 = 0, 0, 0
    cur_4h, cur_1h = 0, 0
    act_h: list[Any] = []
    act_l: list[Any] = []
    last1_sh: float | None = None
    last1_sl: float | None = None
    cands: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    busy_until = -1
    warmup = eval_start - pd.Timedelta(hours=12)
    max_age = 120 if sweep_tf == "1h" else 48
    max_wait = 60 if sweep_tf == "1h" else 20
    use_trail = trail_1h_after_r is not None

    for m in range(len(t1_idx)):
        tm = t1_idx[m]
        while p4 < len(e4) and e4[p4] <= tm:
            cur_4h = int(t4[p4])
            p4 += 1
        while p1 < len(e1) and e1[p1] <= tm:
            cur_1h = int(t1h[p1])
            p1 += 1
        while ps < len(ends) and ends[ps] <= tm:
            for sp in act_l:
                if (ps - sp.candle_idx) >= min_age and ls[ps] < sp.price and cs[ps] > sp.price:
                    cands.append({"side": "LONG", "start_m": m, "sl_base": float(ls[ps]), "choch": last1_sh})
            for sp in act_h:
                if (ps - sp.candle_idx) >= min_age and hs[ps] > sp.price and cs[ps] < sp.price:
                    cands.append({"side": "SHORT", "start_m": m, "sl_base": float(hs[ps]), "choch": last1_sl})
            act_h = [sp for sp in act_h if hs[ps] <= sp.price and (ps - sp.candle_idx) <= max_age]
            act_l = [sp for sp in act_l if ls[ps] >= sp.price and (ps - sp.candle_idx) <= max_age]
            for sp in sw_htf.get(ps, []):
                if sp.kind == "high" and hs[sp.candle_idx + 1 : ps + 1].max() <= sp.price:
                    act_h.append(sp)
                elif sp.kind == "low" and ls[sp.candle_idx + 1 : ps + 1].min() >= sp.price:
                    act_l.append(sp)
            ps += 1

        kz_ok = ((not use_killzone) or in_killzone_utc(tm)) and (min_hour_utc is None or tm.hour >= min_hour_utc)
        new_p = []
        for st in pending:
            if m > st["expire"]:
                continue
            if st["side"] == "LONG":
                if o1[m] <= st["sl"]:
                    continue
                if l1[m] <= st["trig"]:
                    if m <= busy_until or not kz_ok:
                        if l1[m] <= st["sl"] or m <= busy_until:
                            continue
                        new_p.append(st)
                        continue
                    if not (eval_start <= tm < eval_end):
                        continue
                    fill = min(float(o1[m]), st["trig"])
                    c_eff = float(cost + pct_cost * fill)
                    if use_trail:
                        res = _sim_1m_trail_1h(
                            engine=engine_label,
                            side="LONG",
                            entry_idx=m,
                            fill=fill,
                            sl=st["sl"],
                            act_r=float(trail_1h_after_r),
                            be_lock_r=be_lock_r,
                            h1=h1,
                            l1=l1,
                            t1=t1_idx,
                            s1h_t=s1h_t,
                            s1h_k=s1h_k,
                            s1h_p=s1h_p,
                            cost=c_eff,
                            setup_time=st["setup_time"],
                        )
                    else:
                        tp = fill + float(fixed_rr) * (fill - st["sl"])
                        res = _sim_1m_path(
                            engine=engine_label,
                            side="LONG",
                            entry_idx=m,
                            fill=fill,
                            sl=st["sl"],
                            tp=tp,
                            h1=h1,
                            l1=l1,
                            t1=t1_idx,
                            cost=c_eff,
                            setup_time=st["setup_time"],
                            be_act_r=be_act_r,
                            be_lock_r=be_lock_r,
                        )
                    if res:
                        res["asset"] = asset
                        res["cost_usd"] = c_eff
                        busy_until = res["exit_idx"]
                        trades.append(res)
                    continue
            else:
                if o1[m] >= st["sl"]:
                    continue
                if h1[m] >= st["trig"]:
                    if m <= busy_until or not kz_ok:
                        if h1[m] >= st["sl"] or m <= busy_until:
                            continue
                        new_p.append(st)
                        continue
                    if not (eval_start <= tm < eval_end):
                        continue
                    fill = max(float(o1[m]), st["trig"])
                    c_eff = float(cost + pct_cost * fill)
                    if use_trail:
                        res = _sim_1m_trail_1h(
                            engine=engine_label,
                            side="SHORT",
                            entry_idx=m,
                            fill=fill,
                            sl=st["sl"],
                            act_r=float(trail_1h_after_r),
                            be_lock_r=be_lock_r,
                            h1=h1,
                            l1=l1,
                            t1=t1_idx,
                            s1h_t=s1h_t,
                            s1h_k=s1h_k,
                            s1h_p=s1h_p,
                            cost=c_eff,
                            setup_time=st["setup_time"],
                        )
                    else:
                        tp = fill - float(fixed_rr) * (st["sl"] - fill)
                        res = _sim_1m_path(
                            engine=engine_label,
                            side="SHORT",
                            entry_idx=m,
                            fill=fill,
                            sl=st["sl"],
                            tp=tp,
                            h1=h1,
                            l1=l1,
                            t1=t1_idx,
                            cost=c_eff,
                            setup_time=st["setup_time"],
                            be_act_r=be_act_r,
                            be_lock_r=be_lock_r,
                        )
                    if res:
                        res["asset"] = asset
                        res["cost_usd"] = c_eff
                        busy_until = res["exit_idx"]
                        trades.append(res)
                    continue
            new_p.append(st)
        pending = new_p

        if m >= 6 and kz_ok and warmup <= tm < eval_end:
            a1 = float(atr1[m]) if np.isfinite(atr1[m]) else float(c1[m]) * 0.0005
            buf = 1.0 * a1
            min_r = max(min_risk_abs, float(c1[m]) * min_risk_pct)
            c1i, c2i, c3i = m - 2, m - 1, m
            c2b = abs(float(c1[c2i] - o1[c2i]))
            still = []
            for sc in cands:
                if m - sc["start_m"] > max_wait:
                    continue
                if sc["side"] == "LONG":
                    if l1[m] < sc["sl_base"]:
                        continue
                    gap = float(l1[c3i] - h1[c1i])
                    ok_htf = (
                        (htf_mode == "none")
                        or (htf_mode == "4h" and cur_4h == 1)
                        or (htf_mode == "1h" and cur_1h == 1)
                        or (htf_mode == "dual" and cur_4h == 1 and cur_1h == 1)
                    )
                    if (
                        ok_htf
                        and sc["choch"] is not None
                        and c1[c3i] > sc["choch"]
                        and gap >= 0.25 * a1
                        and c1[c2i] > o1[c2i]
                        and c2b >= 1.0 * a1
                    ):
                        k_end = c1i
                        while k_end >= 1 and c1[k_end] >= o1[k_end] and (c1i - k_end) <= 2:
                            k_end -= 1
                        k_start = k_end
                        while k_start >= 1 and c1[k_start - 1] < o1[k_start - 1] and (k_end - k_start) < 4:
                            k_start -= 1
                        has_bear_ob = c1[k_end] < o1[k_end]
                        if require_cisd and not (has_bear_ob and c1[c2i] > o1[k_start]):
                            still.append(sc)
                            continue
                        fvg_hi, fvg_lo = float(l1[c3i]), float(h1[c1i])
                        if entry_mode == "ob_overlap" and has_bear_ob:
                            ob_wick, ob_body = float(h1[k_start]), float(o1[k_start])
                            ob_top = ob_wick if (fvg_lo <= ob_wick <= fvg_hi) else ob_body
                            trig = min(fvg_hi, max(fvg_lo, ob_top)) if ob_top >= fvg_lo else fvg_lo
                        else:
                            trig = fvg_hi
                        sl = sc["sl_base"] - buf
                        if trig - sl >= min_r:
                            pending.append({"side": "LONG", "trig": trig, "sl": sl, "expire": m + 20, "setup_time": tm})
                            continue
                else:
                    if h1[m] > sc["sl_base"]:
                        continue
                    gap = float(l1[c1i] - h1[c3i])
                    ok_htf = (
                        (htf_mode == "none")
                        or (htf_mode == "4h" and cur_4h == -1)
                        or (htf_mode == "1h" and cur_1h == -1)
                        or (htf_mode == "dual" and cur_4h == -1 and cur_1h == -1)
                    )
                    if (
                        ok_htf
                        and sc["choch"] is not None
                        and c1[c3i] < sc["choch"]
                        and gap >= 0.25 * a1
                        and c1[c2i] < o1[c2i]
                        and c2b >= 1.0 * a1
                    ):
                        k_end = c1i
                        while k_end >= 1 and c1[k_end] <= o1[k_end] and (c1i - k_end) <= 2:
                            k_end -= 1
                        k_start = k_end
                        while k_start >= 1 and c1[k_start - 1] > o1[k_start - 1] and (k_end - k_start) < 4:
                            k_start -= 1
                        has_bull_ob = c1[k_end] > o1[k_end]
                        if require_cisd and not (has_bull_ob and c1[c2i] < o1[k_start]):
                            still.append(sc)
                            continue
                        fvg_lo, fvg_hi = float(h1[c3i]), float(l1[c1i])
                        if entry_mode == "ob_overlap" and has_bull_ob:
                            ob_wick, ob_body = float(l1[k_start]), float(o1[k_start])
                            ob_bot = ob_wick if (fvg_lo <= ob_wick <= fvg_hi) else ob_body
                            trig = max(fvg_lo, min(fvg_hi, ob_bot)) if ob_bot <= fvg_hi else fvg_hi
                        else:
                            trig = fvg_lo
                        sl = sc["sl_base"] + buf
                        if sl - trig >= min_r:
                            pending.append({"side": "SHORT", "trig": trig, "sl": sl, "expire": m + 20, "setup_time": tm})
                            continue
                still.append(sc)
            cands = still

        for sp in sw1.get(m, []):
            if sp.kind == "high":
                last1_sh = sp.price
            else:
                last1_sl = sp.price

    return trades


def run_smc_v7_multiasset_portfolio(
    df_xau: pd.DataFrame,
    df_nsx: pd.DataFrame,
    df_btc: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    xau_cost: float = 0.25,
    nsx_cost_pts: float = 2.0,
    btc_pct_cost: float = 0.0008,
) -> dict[str, Any]:
    """Run V7 Multi-Asset Uncorrelated Portfolio across XAUUSD, NSXUSD, and BTCUSD."""
    v6 = run_smc_v6_xau_portfolio(df_xau, eval_start, eval_end, cost=xau_cost, single_position_lock=True)
    for t in v6["v6_unlocked"]:
        t["asset"] = "XAUUSD"
    for t in v6["v6_1pos_lock"]:
        t["asset"] = "XAUUSD"

    xau_15_tr = run_engine_sniper_htf(
        df_xau, eval_start, eval_end,
        asset="XAUUSD", sweep_tf="15min", sweep_k=2, min_age=2, htf_mode="dual",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=None, trail_1h_after_r=4.0, be_lock_r=1.5,
        use_killzone=True, cost=xau_cost, engine_label="XAU_15m1m_Tr1H",
    )
    xau_1h_15r = run_engine_sniper_htf(
        df_xau, eval_start, eval_end,
        asset="XAUUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="4h",
        min_risk_abs=2.0, min_risk_pct=0.0010, fixed_rr=15.0, trail_1h_after_r=None,
        use_killzone=True, cost=xau_cost, engine_label="XAU_1H1m_15R",
    )
    xau_v7_1pos = lock_single_position(v6["v5_unlocked"] + xau_15_tr + xau_1h_15r)

    df_nsx_scaled = df_nsx.copy()
    for col in ("Open", "High", "Low", "Close"):
        df_nsx_scaled[col] = df_nsx_scaled[col] / 10.0
    nsx_amd = run_engine_amd_pro(df_nsx_scaled, eval_start, eval_end, cost=nsx_cost_pts / 10.0)
    for t in nsx_amd:
        t["engine"] = "NSX_AMD"
        t["asset"] = "NSXUSD"
    nsx_1h_10r = run_engine_sniper_htf(
        df_nsx, eval_start, eval_end,
        asset="NSXUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="4h",
        min_risk_abs=10.0, min_risk_pct=0.0010, fixed_rr=10.0, trail_1h_after_r=None,
        use_killzone=True, cost=nsx_cost_pts, engine_label="NSX_1H1m_10R",
    )
    nsx_v7_1pos = lock_single_position(nsx_amd + nsx_1h_10r)

    btc_dual_15r = run_engine_sniper_htf(
        df_btc, eval_start, eval_end,
        asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        use_killzone=False, cost=0.0, pct_cost=btc_pct_cost, engine_label="BTC_1H5m_Dual15R",
    )

    v7_global_1pos = lock_single_position(v6["v6_unlocked"] + nsx_amd + btc_dual_15r)
    v7_3asset_1pos_each = sorted(
        v6["v6_1pos_lock"] + nsx_v7_1pos + btc_dual_15r,
        key=lambda x: pd.Timestamp(x["exit_time"]),
    )
    v7_unleashed_3asset = sorted(
        xau_v7_1pos + nsx_v7_1pos + btc_dual_15r,
        key=lambda x: pd.Timestamp(x["exit_time"]),
    )

    return {
        "v7_global_1pos": v7_global_1pos,
        "v7_3asset_1pos_each": v7_3asset_1pos_each,
        "v7_unleashed_3asset": v7_unleashed_3asset,
        "v6_xau_1pos": v6["v6_1pos_lock"],
        "xau_v7_1pos": xau_v7_1pos,
        "nsx_amd": nsx_amd,
        "nsx_1h_10r": nsx_1h_10r,
        "nsx_v7_1pos": nsx_v7_1pos,
        "btc_dual_15r": btc_dual_15r,
        "xau_15m_tr1h": xau_15_tr,
        "xau_1h_15r": xau_1h_15r,
    }


def run_smc_v8_multiasset_portfolio(
    df_xau: pd.DataFrame,
    df_nsx: pd.DataFrame,
    df_btc: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    xau_cost: float = 0.25,
    nsx_cost_pts: float = 2.0,
    btc_pct_cost: float = 0.0008,
) -> dict[str, Any]:
    """Run V8 Microscopy-Upgraded Multi-Asset Portfolio across XAUUSD, NSXUSD, and BTCUSD.

    Upgrades from V7 based on forensic winner/loser microscopy:
    1. XAU `V3_Pro_Clean`: Removes 13:00-14:59 UTC NY cash-open chop (PF 1.56 -> 2.29, DD 13.7R -> 7.4R).
    2. NSX `NSX_AMD_1D`: Adds causal 1D BOS alignment (PF 1.19 -> 1.51, DD 24.8R -> 13.1R).
    3. NSX `NSX_1H1m_10R`: Drops dead 07:00-08:59 UTC London hours (`min_hour_utc=9`, PF 1.41 -> 1.57).
    4. BTC `BTC_15R_BE`: Adds `BE@3.0R(+1.0R)` shield + `min_hour_utc=9` (PF 1.60 -> 2.33, DD 36.8R -> 11.9R).
    """
    v6 = run_smc_v6_xau_portfolio(df_xau, eval_start, eval_end, cost=xau_cost, single_position_lock=False)
    xau_unlk = []
    for t in v6["v6_unlocked"]:
        if t["engine"] == "V3_Pro" and pd.Timestamp(t["entry_time"]).hour in (13, 14):
            continue
        nt = dict(t)
        nt["asset"] = "XAUUSD"
        nt["cost_usd"] = xau_cost
        if nt["engine"] == "V3_Pro":
            nt["engine"] = "V3_Pro_Clean"
        xau_unlk.append(nt)
    xau_v8_1pos = lock_single_position(xau_unlk)

    df_nsx_scaled = df_nsx.copy()
    for col in ("Open", "High", "Low", "Close"):
        df_nsx_scaled[col] = df_nsx_scaled[col] / 10.0
    nsx_amd_raw = run_engine_amd_pro(df_nsx_scaled, eval_start, eval_end, cost=nsx_cost_pts / 10.0)
    ed_n, td_n = build_causal_htf_structure(df_nsx, "1D", 2)
    nsx_amd_1d = []
    for t in nsx_amd_raw:
        p1d = int(ed_n.searchsorted(pd.Timestamp(t["setup_time"]), side="right")) - 1
        d = 1 if t["side"] == "LONG" else -1
        if p1d >= 0 and int(td_n[p1d]) == d:
            nt = dict(t)
            nt["engine"] = "NSX_AMD_1D"
            nt["asset"] = "NSXUSD"
            nt["cost_usd"] = nsx_cost_pts / 10.0
            nsx_amd_1d.append(nt)

    nsx_1h_10r = run_engine_sniper_htf(
        df_nsx, eval_start, eval_end,
        asset="NSXUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="4h",
        min_risk_abs=10.0, min_risk_pct=0.0010, fixed_rr=10.0, trail_1h_after_r=None,
        use_killzone=True, min_hour_utc=9, cost=nsx_cost_pts, engine_label="NSX_1H1m_10R",
    )
    nsx_v8_1pos = lock_single_position(nsx_amd_1d + nsx_1h_10r)

    btc_15r_be = run_engine_sniper_htf(
        df_btc, eval_start, eval_end,
        asset="BTCUSD", sweep_tf="1h", sweep_k=3, min_age=4, htf_mode="dual",
        min_risk_abs=0.0, min_risk_pct=0.0020, fixed_rr=15.0, trail_1h_after_r=None,
        be_act_r=3.0, be_lock_r=1.0,
        use_killzone=False, min_hour_utc=9, cost=0.0, pct_cost=btc_pct_cost, engine_label="BTC_15R_BE",
    )

    v8_global_1pos = lock_single_position(xau_unlk + nsx_amd_1d + btc_15r_be)
    v8_3asset_1pos_each = sorted(
        xau_v8_1pos + nsx_v8_1pos + btc_15r_be,
        key=lambda x: pd.Timestamp(x["exit_time"]),
    )

    return {
        "v8_global_1pos": v8_global_1pos,
        "v8_3asset_1pos_each": v8_3asset_1pos_each,
        "xau_v8_1pos": xau_v8_1pos,
        "nsx_amd_1d": nsx_amd_1d,
        "nsx_1h_10r": nsx_1h_10r,
        "nsx_v8_1pos": nsx_v8_1pos,
        "btc_15r_be": btc_15r_be,
    }


def run_v9_multiasset_portfolio(
    df_btc_5m: pd.DataFrame,
    df_xau_5m: Optional[pd.DataFrame],
    df_nsx_5m: Optional[pd.DataFrame],
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    btc_fee_mult: float = 1.0,
    cfd_fee_mult: float = 0.5,
) -> dict[str, Any]:
    """Run V9.0 Real Multi-Asset Portfolio across BTCUSD_5m, XAUUSD_5m, and NSXUSD_5m (ZERO synthetic multipliers).

    - `BTCUSD`: V9_Session_Sweeps (`LON` + `1H_K2` + `15M_NY`) + `V8_Physics` + `V6_4H_Cognitive`
    - `XAUUSD`: V9_1H_K2 (`e4_and_tr1` alignment) + `V8_Physics` + `V6_4H_Cognitive`
    - `NSXUSD`: V9_1H_K2 (`e4_and_tr1` alignment) + `V8_Physics` (V6_4H excluded on NSX where it underperforms)
    """
    from .strategy_brain import _summarize_trades, run_v9_daily_session_backtest

    btc_tr, btc_sum = run_v9_daily_session_backtest(
        df_btc_5m,
        eval_start,
        eval_end,
        asset="BTCUSD",
        use_lon=True,
        use_1h_k2=True,
        use_15m_ny=True,
        include_v8_physics=True,
        include_v6_4h=True,
        htf_align_mode="tr4_eq_tr1",
        fee_mult=btc_fee_mult,
    )
    all_tr = list(btc_tr)

    xau_tr: List[dict] = []
    xau_sum: Dict[str, Any] = {}
    if df_xau_5m is not None and len(df_xau_5m) > 200:
        xau_tr, xau_sum = run_v9_daily_session_backtest(
            df_xau_5m,
            eval_start,
            eval_end,
            asset="XAUUSD",
            use_lon=False,
            use_1h_k2=True,
            use_15m_ny=False,
            include_v8_physics=True,
            include_v6_4h=True,
            htf_align_mode="e4_and_tr1",
            min_sl_pct=0.0005,
            max_sl_pct=0.0150,
            fee_mult=cfd_fee_mult,
        )
        all_tr.extend(xau_tr)

    nsx_tr: List[dict] = []
    nsx_sum: Dict[str, Any] = {}
    if df_nsx_5m is not None and len(df_nsx_5m) > 200:
        nsx_tr, nsx_sum = run_v9_daily_session_backtest(
            df_nsx_5m,
            eval_start,
            eval_end,
            asset="NSXUSD",
            use_lon=False,
            use_1h_k2=True,
            use_15m_ny=False,
            include_v8_physics=True,
            include_v6_4h=False,
            htf_align_mode="e4_and_tr1",
            min_sl_pct=0.0005,
            max_sl_pct=0.0150,
            fee_mult=cfd_fee_mult,
        )
        all_tr.extend(nsx_tr)

    all_tr = sorted(all_tr, key=lambda t: t["entry_time"])
    return {
        "btc_trades": btc_tr,
        "btc_summary": btc_sum,
        "xau_trades": xau_tr,
        "xau_summary": xau_sum,
        "nsx_trades": nsx_tr,
        "nsx_summary": nsx_sum,
        "real_multiasset_trades": all_tr,
        "real_multiasset_summary": _summarize_trades(all_tr),
    }


def run_v10_xau_topo_backtest(
    df_xau_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "XAUUSD",
    zig_4h: float = 0.85,
    zig_1h: float = 1.15,
    zig_15m: float = 1.00,
    zig_5m: float = 1.15,
    fvg_depth: float = 0.50,
    min_sl_pct: float = 0.0005,
    max_sl_pct: float = 0.0150,
    fee_mult: float = 0.5,
    include_v6_4h: bool = False,
) -> tuple[List[dict], Dict[str, Any]]:
    """V10.0 Topological XAUUSD_1m VisB Engine (ZERO k=2/k=3 fractals + 45/40/15 Front-Loaded Exit).

    Uses causal ATR-ZigZag topology (`zig_4h=0.85, zig_1h=1.15`) + 0.50*FVG midpoint entry +
    V10FrontLoadedCashflowExitManager (`45% @ 2.2R -> +0.35R BE`, `40% @ 4.5R -> +2.0R`, `15% @ 10R`
    + 15m Topological Protected Swing trail).
    """
    from .exit_manager import ProtectedSwingDetector, TradePositionState, V10FrontLoadedCashflowExitManager
    from .perception_engine import build_causal_topo_events, compute_atr_series
    from .strategy_brain import _summarize_trades, run_v6_cognitive_backtest

    df_sub = df_xau_1m.loc[df_xau_1m.index < eval_end]
    df5 = resample_causal_tf(df_sub, "5min")
    df15 = resample_causal_tf(df_sub, "15min")
    df1h = resample_causal_tf(df_sub, "1h")
    df4h = resample_causal_tf(df_sub, "4h")

    h1m = df_sub["High"].to_numpy(float)
    l1m = df_sub["Low"].to_numpy(float)
    c1m = df_sub["Close"].to_numpy(float)
    ts1m = df_sub.index.as_unit("ns").asi8
    atr1m = causal_atr14(h1m, l1m, c1m)

    o5, h5, l5, c5 = (df5[k].to_numpy(float) for k in ("Open", "High", "Low", "Close"))
    ts5 = df5.index.as_unit("ns").asi8
    atr5 = compute_atr_series(h5, l5, c5, 14)

    h15, l15, c15 = (df15[k].to_numpy(float) for k in ("High", "Low", "Close"))
    ts15 = df15.index.as_unit("ns").asi8
    atr15 = compute_atr_series(h15, l15, c15, 14)

    h1h, l1h, c1h = (df1h[k].to_numpy(float) for k in ("High", "Low", "Close"))
    ts1h = df1h.index.as_unit("ns").asi8
    atr1h = compute_atr_series(h1h, l1h, c1h, 14)

    h4h, l4h, c4h = df4h["High"].to_numpy(float), df4h["Low"].to_numpy(float), df4h["Close"].to_numpy(float)
    ts4h = df4h.index.as_unit("ns").asi8
    atr4h = compute_atr_series(h4h, l4h, c4h, 14)

    sw5_d = build_causal_topo_events(ts5, h5, l5, c5, atr5, zig_mult=zig_5m)
    sw15_d = build_causal_topo_events(ts15, h15, l15, c15, atr15, zig_mult=zig_15m)
    sw1h_d = build_causal_topo_events(ts1h, h1h, l1h, c1h, atr1h, zig_mult=zig_1h)
    sw4h_d = build_causal_topo_events(ts4h, h4h, l4h, c4h, atr4h, zig_mult=zig_4h)

    exit_mgr = V10FrontLoadedCashflowExitManager()
    prot15 = ProtectedSwingDetector()

    tr4h = tr1h = 0
    sh4h = sl4h = sh1h = sl1h = sh5 = sl5 = None
    act1h_hi: list = []
    act1h_lo: list = []
    p5 = p15 = p1h = p4h = 0
    sweeps: list = []
    pos: Optional[TradePositionState] = None
    pend: Optional[dict] = None
    cool = 0
    cid = 0
    trades: List[dict] = []

    eval0_ns = int(eval_start.as_unit("ns").value)
    eval1_ns = int(eval_end.as_unit("ns").value)
    hrs1m = pd.to_datetime(ts1m, utc=True).hour.to_numpy()

    for i in range(60, len(df_sub)):
        t_ns = int(ts1m[i]) + 60 * 10**9
        if t_ns >= eval1_ns:
            break

        while p4h < len(df4h) and ts4h[p4h] + 14400 * 10**9 <= t_ns:
            for s in sw4h_d.get(p4h, []):
                if s.side == 1:
                    sh4h = s.price
                else:
                    sl4h = s.price
            if sh4h is not None and c4h[p4h] > sh4h:
                tr4h = 1
            elif sl4h is not None and c4h[p4h] < sl4h:
                tr4h = -1
            p4h += 1

        while p1h < len(df1h) and ts1h[p1h] + 3600 * 10**9 <= t_ns:
            hh, hl, hc = float(h1h[p1h]), float(l1h[p1h]), float(c1h[p1h])
            for sw in act1h_lo:
                if (p1h - sw.idx) >= 3 and hl < sw.price and hc > sw.price:
                    sweeps.append((1, t_ns, hl))
            for sw in act1h_hi:
                if (p1h - sw.idx) >= 3 and hh > sw.price and hc < sw.price:
                    sweeps.append((-1, t_ns, hh))
            for s in sw1h_d.get(p1h, []):
                if s.side == 1:
                    sh1h = s.price
                    act1h_hi.append(s)
                    act1h_hi = act1h_hi[-16:]
                else:
                    sl1h = s.price
                    act1h_lo.append(s)
                    act1h_lo = act1h_lo[-16:]
            act1h_hi = [x for x in act1h_hi if hh <= x.price]
            act1h_lo = [x for x in act1h_lo if hl >= x.price]
            if sh1h is not None and hc > sh1h:
                tr1h = 1
            elif sl1h is not None and hc < sl1h:
                tr1h = -1
            p1h += 1

        while p15 < len(df15) and ts15[p15] + 900 * 10**9 <= t_ns:
            prot15.update(i, float(c15[p15]), sw15_d.get(p15, []))
            p15 += 1

        new5 = False
        while p5 < len(df5) and ts5[p5] + 300 * 10**9 <= t_ns:
            for s in sw5_d.get(p5, []):
                if s.side == 1:
                    sh5 = s.price
                else:
                    sl5 = s.price
            p5 += 1
            new5 = True

        if pos is not None:
            closed, gross_r, _ = exit_mgr.step_bar(pos, i, float(h1m[i]), float(l1m[i]), float(c1m[i]), float(atr1m[i]), prot15, None)
            if closed:
                hrs = max(0.05, (i - pos.entry_bar) / 60.0)
                t1_b = pos.meta.get("t1_bar")
                t2_b = pos.meta.get("t2_bar")
                t1_hrs = round((t1_b - pos.entry_bar) / 60.0, 2) if t1_b is not None else None
                t2_hrs = round((t2_b - pos.entry_bar) / 60.0, 2) if t2_b is not None else None
                t1_ts = (pos.entry_ts + pd.Timedelta(hours=t1_hrs)) if t1_hrs is not None else None
                cost = fee_mult * (0.0005 / max(pos.risk_dist / pos.entry_price, 1e-9))
                trades.append({
                    "cluster_id": pos.trade_id,
                    "asset": asset,
                    "entry_time": pos.entry_ts,
                    "exit_time": pd.Timestamp(t_ns, tz="UTC"),
                    "t1_time": t1_ts,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "init_sl": pos.init_sl,
                    "sl_pct": pos.risk_dist / pos.entry_price,
                    "gross_r": gross_r,
                    "net_r": gross_r - cost,
                    "is_pyramid": False,
                    "is_aplus": True,
                    "conviction": 0.78,
                    "setup": "V10_XAU_VisB",
                    "engine": "V10_XAU_VisB",
                    "outcome": pos.exit_reason,
                    "hold_hours": hrs,
                    "t1_hours": t1_hrs,
                    "t2_hours": t2_hrs,
                })
                pos = None
                cool = i + 5
            continue

        if t_ns < eval0_ns or p4h < 15 or p1h < 25 or p5 < 10:
            continue

        if pend is not None:
            if i > pend["exp"]:
                pend = None
            elif (pend["sd"] == 1 and l1m[i] <= pend["ep"]) or (pend["sd"] == -1 and h1m[i] >= pend["ep"]):
                cid += 1
                pos = TradePositionState(
                    trade_id=cid,
                    side=pend["sd"],
                    entry_bar=i,
                    entry_ts=pd.Timestamp(t_ns, tz="UTC"),
                    entry_price=pend["ep"],
                    init_sl=pend["sl"],
                    cur_sl=pend["sl"],
                    risk_dist=pend["rd"],
                    meta={"setup": "V10_XAU_VisB"},
                )
                pend = None
            continue

        if i <= cool or not new5 or p5 < 4:
            continue
        hr = int(hrs1m[i])
        if hr not in (9, 10, 12, 13, 14, 15, 16):
            continue

        sweeps = [x for x in sweeps if (t_ns - x[1]) <= 6 * 3600 * 10**9][-10:]
        a5 = float(atr5[p5 - 1])
        if a5 <= 0:
            continue
        b1, b2, b3 = p5 - 3, p5 - 2, p5 - 1
        for sd, _, sl_b in reversed(sweeps):
            if sd != tr4h or sd != tr1h:
                continue
            ep = slp = 0.0
            if sd == 1 and l5[b3] >= sl_b and sh5 is not None and c5[b3] > sh5 and (l5[b3] - h5[b1]) >= 0.25 * a5 and c5[b2] > o5[b2]:
                gap = l5[b3] - h5[b1]
                ep = float(l5[b3] - fvg_depth * gap)
                slp = min(sl_b - a5, ep - max(1.3 * a5, ep * 0.0010))
            elif sd == -1 and h5[b3] <= sl_b and sl5 is not None and c5[b3] < sl5 and (l5[b1] - h5[b3]) >= 0.25 * a5 and c5[b2] < o5[b2]:
                gap = l5[b1] - h5[b3]
                ep = float(h5[b3] + fvg_depth * gap)
                slp = max(sl_b + a5, ep + max(1.3 * a5, ep * 0.0010))
            else:
                continue
            rd = abs(ep - slp)
            if ep > 0 and min_sl_pct <= (rd / ep) <= max_sl_pct:
                pend = {"sd": sd, "ep": ep, "sl": slp, "rd": rd, "exp": i + 120}
                break

    if include_v6_4h:
        tr_v6, _ = run_v6_cognitive_backtest(df5, eval_start, eval_end, fee_mult=fee_mult)
        for _t in tr_v6:
            _t["asset"] = asset
            _t.setdefault("setup", "4H_V6_Cognitive")
            _t.setdefault("engine", "4H_V6_Cognitive")
            if _t.get("t1_time") is None:
                _t["t1_time"] = _t["exit_time"]
            trades.append(_t)

    trades = sorted(trades, key=lambda t: t["entry_time"])
    return trades, _summarize_trades(trades)


def run_v10_nsx_topo_backtest(
    df_nsx_5m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset: str = "NSXUSD",
    fee_mult: float = 0.5,
) -> tuple[List[dict], Dict[str, Any]]:
    """V10.0 NSXUSD_5m Physics Front-Loaded Engine (ZERO k=2/k=3 fractals + 45/40/15)."""
    from .strategy_brain import _summarize_trades, run_v8_intraday_backtest

    tr_nsx, _ = run_v8_intraday_backtest(
        df_nsx_5m,
        eval_start,
        eval_end,
        include_smc_sweep=False,
        fee_mult=fee_mult,
        use_killzones=True,
        min_sl_pct=0.0005,
        max_sl_pct=0.0150,
        min_ker4=0.15,
        min_rvol_entry=0.90,
        min_clearance_r=3.0,
        bank_r=2.2,
        bank_frac=0.45,
        be_lock_r=0.35,
        bank2_r=4.5,
        bank2_frac=0.40,
        be2_lock_r=2.0,
        runner_tp_r=10.0,
    )
    for _t in tr_nsx:
        _t["asset"] = asset
        orig_s = str(_t.get("setup", "V8_CompVacuum"))
        new_s = orig_s.replace("V8_", "V10_NSX_")
        _t["setup"] = new_s
        _t["engine"] = new_s
        if _t.get("t1_hours") is not None and _t.get("t1_time") is None:
            _t["t1_time"] = _t["entry_time"] + pd.Timedelta(hours=float(_t["t1_hours"]))
    tr_nsx = sorted(tr_nsx, key=lambda t: t["entry_time"])
    return tr_nsx, _summarize_trades(tr_nsx)


def run_v10_multiasset_portfolio(
    df_btc_5m: pd.DataFrame,
    df_xau_1m: Optional[pd.DataFrame],
    df_nsx_5m: Optional[pd.DataFrame],
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    include_btc_topo_sweeps: bool = True,
    include_xau_v6_4h: bool = False,
    btc_fee_mult: float = 1.0,
    cfd_fee_mult: float = 0.5,
) -> dict[str, Any]:
    """Run V10.0 Front-Loaded Cashflow Multi-Asset Portfolio across BTCUSD_5m, XAUUSD_1m, and NSXUSD_5m."""
    from .strategy_brain import _summarize_trades, run_v10_btc_frontloaded_backtest

    btc_tr, btc_sum = run_v10_btc_frontloaded_backtest(
        df_btc_5m,
        eval_start,
        eval_end,
        asset="BTCUSD",
        include_physics_45=True,
        include_v6_4h=True,
        include_topo_sweeps=include_btc_topo_sweeps,
        fee_mult=btc_fee_mult,
    )
    all_tr = list(btc_tr)

    xau_tr: List[dict] = []
    xau_sum: Dict[str, Any] = {}
    if df_xau_1m is not None and len(df_xau_1m) > 500:
        xau_tr, xau_sum = run_v10_xau_topo_backtest(
            df_xau_1m,
            eval_start,
            eval_end,
            asset="XAUUSD",
            fee_mult=cfd_fee_mult,
            include_v6_4h=include_xau_v6_4h,
        )
        all_tr.extend(xau_tr)

    nsx_tr: List[dict] = []
    nsx_sum: Dict[str, Any] = {}
    if df_nsx_5m is not None and len(df_nsx_5m) > 200:
        nsx_tr, nsx_sum = run_v10_nsx_topo_backtest(
            df_nsx_5m,
            eval_start,
            eval_end,
            asset="NSXUSD",
            fee_mult=cfd_fee_mult,
        )
        all_tr.extend(nsx_tr)

    all_tr = sorted(all_tr, key=lambda t: t["entry_time"])
    return {
        "btc_trades": btc_tr,
        "btc_summary": btc_sum,
        "xau_trades": xau_tr,
        "xau_summary": xau_sum,
        "nsx_trades": nsx_tr,
        "nsx_summary": nsx_sum,
        "real_multiasset_trades": all_tr,
        "real_multiasset_summary": _summarize_trades(all_tr),
    }


