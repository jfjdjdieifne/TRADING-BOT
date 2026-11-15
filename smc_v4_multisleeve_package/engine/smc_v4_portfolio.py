"""SMC V4 Multi-Sleeve Portfolio Engine (Zero-Lookahead).

Combines 3 complementary institutional SMC/ICT engines:
1. Sleeve 1 (`V3_NY`): Dual 4H+1H BOS Alignment -> 15m BOS Displacement FVG in NY Killzone (12-17 UTC).
2. Sleeve 2 (`VisB`): 4H BOS Bias -> 1H Major Swing (k=3, >=4h age) Real Sweep -> 5m CHoCH + FVG.
3. Sleeve 3 (`VisA`): 15m Major Swing (k=3) Zone + 5m Rising/Falling Trendline (>=3 pivots)
                      -> Zone Tap/Sweep -> CHoCH Breakdown -> Target Trendline Origin.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .causal_primitives import (
    build_causal_htf_structure,
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
) -> dict[str, Any] | None:
    risk = (fill - sl) if side == "LONG" else (sl - fill)
    if risk <= 0:
        return None
    out_idx, out_px, out_lbl = entry_idx, fill, "EOD"
    if (side == "LONG" and l1[entry_idx] <= sl) or (side == "SHORT" and h1[entry_idx] >= sl):
        out_idx, out_px, out_lbl = entry_idx, sl, "SL"
    else:
        for j in range(entry_idx + 1, len(t1)):
            if side == "LONG":
                if l1[j] <= sl:
                    out_idx, out_px, out_lbl = j, sl, "SL"
                    break
                if h1[j] >= tp:
                    out_idx, out_px, out_lbl = j, tp, "TP"
                    break
            else:
                if h1[j] >= sl:
                    out_idx, out_px, out_lbl = j, sl, "SL"
                    break
                if l1[j] <= tp:
                    out_idx, out_px, out_lbl = j, tp, "TP"
                    break
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
) -> list[dict[str, Any]]:
    """Sleeve 2 (VisB): 4H BOS Bias -> 1H Major Swing Sweep -> 5m CHoCH + FVG."""
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
                        res = _sim_1m_path(
                            engine="VisB", side="LONG", entry_idx=m, fill=fill,
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
                        res = _sim_1m_path(
                            engine="VisB", side="SHORT", entry_idx=m, fill=fill,
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
    """Optional chronological filter allowing at most 1 open position across all 3 sleeves."""
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


def run_smc_v4_portfolio(
    df_1m: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    cost: float = 0.25,
    single_position_lock: bool = False,
) -> dict[str, Any]:
    """Run all 3 causal SMC sleeves and combine into V4_MultiSleeve."""
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
