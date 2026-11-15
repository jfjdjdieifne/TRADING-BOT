"""Sleeve 1 (V3_NY): Dual 4H+1H BOS Structure + 15m BOS Displacement FVG (Zero-Lookahead)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from .causal_primitives import (
    build_causal_htf_structure,
    causal_atr14,
    detect_swings_causal,
    in_killzone_utc,
    resample_causal_tf,
)


@dataclass(frozen=True)
class SMCV3Config:
    timeframe: Literal["15m", "5m"] = "15m"
    killzone_mode: Literal["ny", "both", "london"] = "ny"
    htf_swing_k: int = 2
    ltf_swing_k: int = 2
    require_dual_htf: bool = True
    disp_body_atr: float = 1.0
    min_fvg_atr: float = 0.30
    min_fvg_usd: float = 0.20
    sl_buffer_usd: float = 1.00
    sl_buffer_atr_mult: float = 0.50
    rr_target: float = 2.5
    max_wait_bars: int = 20
    allow_long: bool = True
    allow_short: bool = True
    round_trip_cost_usd: float = 0.25


def _kz_allowed(ts: pd.Timestamp, mode: str) -> bool:
    if mode == "both":
        return in_killzone_utc(ts)
    if mode == "london":
        return 7 <= ts.hour < 11
    if mode == "ny":
        return 12 <= ts.hour < 17
    raise ValueError(f"Unknown killzone_mode: {mode}")


def run_smc_v3_backtest(
    df_1m: pd.DataFrame,
    cfg: SMCV3Config,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
) -> dict[str, Any]:
    tf = resample_causal_tf(df_1m, cfg.timeframe)
    o = tf["Open"].to_numpy()
    h = tf["High"].to_numpy()
    l = tf["Low"].to_numpy()
    c = tf["Close"].to_numpy()
    end_t = tf.index
    st_t = tf["start_time"]
    f1m = tf["first_1m_pos"].to_numpy()
    l1m = tf["last_1m_pos"].to_numpy()
    atr = causal_atr14(h, l, c)
    sw = detect_swings_causal(h, l, end_t, cfg.ltf_swing_k)

    e4, t4 = build_causal_htf_structure(df_1m, "4h", cfg.htf_swing_k)
    e1, t1h = build_causal_htf_structure(df_1m, "1h", cfg.htf_swing_k)

    o1 = df_1m["Open"].to_numpy()
    h1 = df_1m["High"].to_numpy()
    l1 = df_1m["Low"].to_numpy()
    t1 = df_1m.index
    n1 = len(t1)

    p4, cur_4h = 0, 0
    p1, cur_1h = 0, 0
    last_sh: float | None = None
    last_sl: float | None = None

    pending: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    busy_until_1m = -1
    warmup_start = eval_start - pd.Timedelta(hours=12)

    for i in range(len(tf)):
        te = end_t[i]
        ts = st_t.iloc[i]

        while p4 < len(e4) and e4[p4] <= te:
            cur_4h = int(t4[p4])
            p4 += 1
        while p1 < len(e1) and e1[p1] <= te:
            cur_1h = int(t1h[p1])
            p1 += 1

        next_pending: list[dict[str, Any]] = []
        for st in pending:
            if i > st["expire"]:
                continue
            ps, pe = int(f1m[i]), int(l1m[i])
            trig = st["trig"]
            dead = False
            for m in range(ps, pe + 1):
                tm = t1[m]
                if st["side"] == "LONG":
                    if o1[m] <= st["sl"] or o1[m] >= st["tp"]:
                        dead = True
                        break
                    if l1[m] <= trig:
                        if m <= busy_until_1m or not _kz_allowed(tm, cfg.killzone_mode):
                            if l1[m] <= st["sl"] or h1[m] >= st["tp"] or m <= busy_until_1m:
                                dead = True
                                break
                            continue
                        if tm < eval_start or tm >= eval_end:
                            continue
                        fill = min(float(o1[m]), trig)
                        risk = fill - st["sl"]
                        if risk <= 0:
                            dead = True
                            break
                        out_idx, out_px, out_lbl = m, fill, "EOD"
                        if l1[m] <= st["sl"]:
                            out_idx, out_px, out_lbl = m, st["sl"], "SL"
                        else:
                            for j in range(m + 1, n1):
                                if l1[j] <= st["sl"]:
                                    out_idx, out_px, out_lbl = j, st["sl"], "SL"
                                    break
                                if h1[j] >= st["tp"]:
                                    out_idx, out_px, out_lbl = j, st["tp"], "TP"
                                    break
                        gross_usd = out_px - fill
                        net_usd = gross_usd - cfg.round_trip_cost_usd
                        busy_until_1m = out_idx
                        trades.append({
                            "engine": "V3_NY",
                            "side": "LONG",
                            "setup_time": str(st["setup_time"]),
                            "entry_time": str(tm),
                            "exit_time": str(t1[out_idx]),
                            "entry_idx": m,
                            "exit_idx": out_idx,
                            "entry_price": float(fill),
                            "sl_price": float(st["sl"]),
                            "tp_price": float(st["tp"]),
                            "exit_price": float(out_px),
                            "outcome": out_lbl,
                            "gross_usd": float(gross_usd),
                            "net_usd": float(net_usd),
                            "gross_r": float(gross_usd / risk),
                            "net_r": float(net_usd / risk),
                            "risk_usd": float(risk),
                            "planned_rr": float(cfg.rr_target),
                        })
                        dead = True
                        break
                    if h1[m] >= st["tp"]:
                        dead = True
                        break
                else:
                    if o1[m] >= st["sl"] or o1[m] <= st["tp"]:
                        dead = True
                        break
                    if h1[m] >= trig:
                        if m <= busy_until_1m or not _kz_allowed(tm, cfg.killzone_mode):
                            if h1[m] >= st["sl"] or l1[m] <= st["tp"] or m <= busy_until_1m:
                                dead = True
                                break
                            continue
                        if tm < eval_start or tm >= eval_end:
                            continue
                        fill = max(float(o1[m]), trig)
                        risk = st["sl"] - fill
                        if risk <= 0:
                            dead = True
                            break
                        out_idx, out_px, out_lbl = m, fill, "EOD"
                        if h1[m] >= st["sl"]:
                            out_idx, out_px, out_lbl = m, st["sl"], "SL"
                        else:
                            for j in range(m + 1, n1):
                                if h1[j] >= st["sl"]:
                                    out_idx, out_px, out_lbl = j, st["sl"], "SL"
                                    break
                                if l1[j] <= st["tp"]:
                                    out_idx, out_px, out_lbl = j, st["tp"], "TP"
                                    break
                        gross_usd = fill - out_px
                        net_usd = gross_usd - cfg.round_trip_cost_usd
                        busy_until_1m = out_idx
                        trades.append({
                            "engine": "V3_NY",
                            "side": "SHORT",
                            "setup_time": str(st["setup_time"]),
                            "entry_time": str(tm),
                            "exit_time": str(t1[out_idx]),
                            "entry_idx": m,
                            "exit_idx": out_idx,
                            "entry_price": float(fill),
                            "sl_price": float(st["sl"]),
                            "tp_price": float(st["tp"]),
                            "exit_price": float(out_px),
                            "outcome": out_lbl,
                            "gross_usd": float(gross_usd),
                            "net_usd": float(net_usd),
                            "gross_r": float(gross_usd / risk),
                            "net_r": float(net_usd / risk),
                            "risk_usd": float(risk),
                            "planned_rr": float(cfg.rr_target),
                        })
                        dead = True
                        break
                    if l1[m] <= st["tp"]:
                        dead = True
                        break
            if not dead:
                next_pending.append(st)
        pending = next_pending

        if i >= 2 and _kz_allowed(ts, cfg.killzone_mode) and warmup_start <= te < eval_end:
            c1i, c2i, c3i = i - 2, i - 1, i
            a_i = float(atr[c3i])
            if np.isfinite(a_i) and a_i > 0:
                c2_body = abs(float(c[c2i] - o[c2i]))
                buf = max(cfg.sl_buffer_usd, cfg.sl_buffer_atr_mult * a_i)

                if cfg.allow_long and cur_4h == 1 and (not cfg.require_dual_htf or cur_1h == 1):
                    gap_l = float(l[c3i] - h[c1i])
                    bos_up = (
                        last_sh is not None
                        and ((c[c2i] <= last_sh and c[c3i] > last_sh) or (c[c1i] <= last_sh and c[c2i] > last_sh))
                    )
                    if (
                        gap_l >= cfg.min_fvg_usd
                        and c[c2i] > o[c2i]
                        and c2_body >= cfg.disp_body_atr * a_i
                        and gap_l >= cfg.min_fvg_atr * a_i
                        and bos_up
                    ):
                        trig = float(l[c3i])
                        sl = float(min(l[c1i], l[c2i])) - buf
                        risk = trig - sl
                        if risk > 0:
                            pending.append({
                                "side": "LONG",
                                "trig": trig,
                                "sl": sl,
                                "tp": trig + cfg.rr_target * risk,
                                "expire": i + cfg.max_wait_bars,
                                "setup_time": te,
                            })

                if cfg.allow_short and cur_4h == -1 and (not cfg.require_dual_htf or cur_1h == -1):
                    gap_s = float(l[c1i] - h[c3i])
                    bos_dn = (
                        last_sl is not None
                        and ((c[c2i] >= last_sl and c[c3i] < last_sl) or (c[c1i] >= last_sl and c[c2i] < last_sl))
                    )
                    if (
                        gap_s >= cfg.min_fvg_usd
                        and c[c2i] < o[c2i]
                        and c2_body >= cfg.disp_body_atr * a_i
                        and gap_s >= cfg.min_fvg_atr * a_i
                        and bos_dn
                    ):
                        trig = float(h[c3i])
                        sl = float(max(h[c1i], h[c2i])) + buf
                        risk = sl - trig
                        if risk > 0:
                            pending.append({
                                "side": "SHORT",
                                "trig": trig,
                                "sl": sl,
                                "tp": trig - cfg.rr_target * risk,
                                "expire": i + cfg.max_wait_bars,
                                "setup_time": te,
                            })

        for sp in sw.get(i, []):
            if sp.kind == "high":
                last_sh = sp.price
            else:
                last_sl = sp.price

    return {"trades": trades, "n_trades": len(trades)}
