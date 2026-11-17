"""Standalone higher-timeframe experiment for the V8 SMC idea.

This file is deliberately outside smc_v4_multisleeve_package/engine and does not
modify or monkey-patch any source file.  It builds a matched sweep -> CHoCH/FVG
sniper from the same causal primitives, then compares the original lower-timeframe
execution with 1H and 4H execution.

The experiment is not a replacement for the official QuantConnect file.  It is an
isolated answer to the question: does removing the 5m/15m execution noise improve
the quality of the same signal family?
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = ROOT / "smc_v4_multisleeve_package"
OUT_ROOT = Path(__file__).resolve().parent
RESULTS = OUT_ROOT / "results"

if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from engine.causal_primitives import (  # noqa: E402
    build_causal_htf_structure,
    causal_atr14,
    detect_swings_causal,
    in_killzone_utc,
    load_asset_ohlcv,
    resample_causal_tf,
)
from engine.smc_v4_portfolio import simulate_compounded_account  # noqa: E402


EV0 = pd.Timestamp("2020-02-01 00:00:00", tz="UTC")
EV1 = pd.Timestamp("2026-11-01 00:00:00", tz="UTC")


@dataclass(frozen=True)
class AssetSpec:
    name: str
    data_dir: str
    stems: tuple[str, ...]
    rr: float
    min_risk_abs: float
    min_risk_pct: float
    fixed_cost: float
    pct_cost: float
    use_killzone: bool
    min_hour_utc: int | None


@dataclass(frozen=True)
class Variant:
    name: str
    label_ar: str
    signal_tf: str
    sweep_tf: str
    context_tf: str
    sweep_k: int
    signal_k: int
    min_age_bars: int
    max_wait_hours: float
    displacement_atr: float = 1.0
    fvg_atr: float = 0.25
    sl_buffer_atr: float = 1.0


ASSETS: tuple[AssetSpec, ...] = (
    AssetSpec(
        name="XAUUSD",
        data_dir="XAUUSD_1m_histdata",
        stems=tuple(f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13))
        + tuple(f"2026-{m:02d}" for m in range(1, 11)),
        rr=10.0,
        min_risk_abs=2.0,
        min_risk_pct=0.0010,
        fixed_cost=0.25,
        pct_cost=0.0,
        use_killzone=True,
        min_hour_utc=None,
    ),
    AssetSpec(
        name="NSXUSD",
        data_dir="NSXUSD_1m_histdata",
        stems=tuple(f"{y}-{m:02d}" for y in range(2020, 2026) for m in range(1, 13))
        + tuple(f"2026-{m:02d}" for m in range(1, 11)),
        rr=10.0,
        min_risk_abs=10.0,
        min_risk_pct=0.0010,
        fixed_cost=2.0,
        pct_cost=0.0,
        use_killzone=True,
        min_hour_utc=None,
    ),
    AssetSpec(
        name="BTCUSD",
        data_dir="BTCUSD_5m",
        stems=tuple(str(y) for y in range(2019, 2027)),
        rr=15.0,
        min_risk_abs=0.0,
        min_risk_pct=0.0020,
        fixed_cost=0.0,
        pct_cost=0.0008,
        use_killzone=False,
        min_hour_utc=9,
    ),
)


VARIANTS: tuple[Variant, ...] = (
    Variant(
        name="LTF_control",
        label_ar="تحكم منخفض: 15m للذهب/الناسداك و5m للبتكوين، Sweep 1H، سياق 4H",
        signal_tf="15min",
        sweep_tf="1h",
        context_tf="4h",
        sweep_k=3,
        signal_k=2,
        min_age_bars=4,
        max_wait_hours=12.0,
    ),
    Variant(
        name="HTF_1H",
        label_ar="نسخة أعلى متوسطة: دخول 1H، Sweep 4H، سياق 1D",
        signal_tf="1h",
        sweep_tf="4h",
        context_tf="1d",
        sweep_k=3,
        signal_k=2,
        min_age_bars=4,
        max_wait_hours=24.0,
    ),
    Variant(
        name="HTF_4H",
        label_ar="نسخة 4H: الدخول وCHoCH/FVG على 4H، Sweep 4H، سياق 1D",
        signal_tf="4h",
        sweep_tf="4h",
        context_tf="1d",
        sweep_k=3,
        signal_k=2,
        min_age_bars=4,
        max_wait_hours=48.0,
    ),
)


# BTC's source is already 5m.  The control must use 5m for BTC, while XAU/NSX
# use 15m because that is the V8 V3/AMD signal scale.  The HTF variants are
# intentionally identical across assets at 1H/4H.
CONTROL_SIGNAL_TF = {"XAUUSD": "15min", "NSXUSD": "15min", "BTCUSD": "5min"}


def completed_bars(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Return completed causal bars and keep only finite OHLC rows."""
    out = resample_causal_tf(df, freq)
    out = out.loc[np.isfinite(out[["Open", "High", "Low", "Close"]]).all(axis=1)].copy()
    return out


def _trend_at(end_times: pd.DatetimeIndex, trend: np.ndarray, ts: pd.Timestamp) -> int:
    pos = int(end_times.searchsorted(ts, side="right")) - 1
    return int(trend[pos]) if pos >= 0 else 0


def _reprice_cost(trades: list[dict[str, Any]], fixed_cost: float, pct_cost: float, multiplier: float = 1.0) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in trades:
        nt = dict(t)
        cost = multiplier * (float(fixed_cost) + float(pct_cost) * float(t["entry_price"]))
        nt["net_usd"] = float(nt["gross_usd"] - cost)
        nt["net_r"] = float(nt["net_usd"] / nt["risk_usd"])
        nt["cost_usd"] = cost
        out.append(nt)
    return out


def _simulate_fixed_rr(
    *,
    bars: pd.DataFrame,
    entry_idx: int,
    side: str,
    fill: float,
    sl: float,
    rr: float,
    fixed_cost: float,
    pct_cost: float,
    setup_time: pd.Timestamp,
    asset: str,
    engine: str,
) -> dict[str, Any] | None:
    """Conservative completed-signal-bar execution model.

    A pending limit is only filled on a bar after the setup bar.  Once filled,
    same-bar SL wins over TP when both are touched; this avoids optimistic
    OHLC assumptions.
    """
    risk = (fill - sl) if side == "LONG" else (sl - fill)
    if risk <= 0 or not np.isfinite(risk):
        return None
    tp = fill + rr * risk if side == "LONG" else fill - rr * risk
    hi = bars["High"].to_numpy(dtype=float)
    lo = bars["Low"].to_numpy(dtype=float)
    times = bars.index
    out_idx = len(bars) - 1
    out_px = float(bars["Close"].iloc[-1])
    outcome = "EOD"
    for j in range(entry_idx, len(bars)):
        if side == "LONG":
            if lo[j] <= sl:
                out_idx, out_px, outcome = j, float(sl), "SL"
                break
            if hi[j] >= tp:
                out_idx, out_px, outcome = j, float(tp), "TP"
                break
        else:
            if hi[j] >= sl:
                out_idx, out_px, outcome = j, float(sl), "SL"
                break
            if lo[j] <= tp:
                out_idx, out_px, outcome = j, float(tp), "TP"
                break
    gross = (out_px - fill) if side == "LONG" else (fill - out_px)
    cost = float(fixed_cost) + float(pct_cost) * float(fill)
    net = gross - cost
    return {
        "asset": asset,
        "engine": engine,
        "side": side,
        "setup_time": str(setup_time),
        "entry_time": str(times[entry_idx]),
        "exit_time": str(times[out_idx]),
        "entry_idx": int(entry_idx),
        "exit_idx": int(out_idx),
        "entry_price": float(fill),
        "sl_price": float(sl),
        "tp_price": float(tp),
        "exit_price": float(out_px),
        "outcome": outcome,
        "gross_usd": float(gross),
        "net_usd": float(net),
        "gross_r": float(gross / risk),
        "net_r": float(net / risk),
        "risk_usd": float(risk),
        "planned_rr": float(rr),
        "cost_usd": float(cost),
    }


def run_scaled_sniper(
    df_raw: pd.DataFrame,
    eval_start: pd.Timestamp,
    eval_end: pd.Timestamp,
    *,
    asset_spec: AssetSpec,
    variant: Variant,
    signal_tf: str | None = None,
) -> list[dict[str, Any]]:
    """Run a causal scale-matched sweep -> CHoCH/FVG engine.

    For each completed signal bar:
      1. update the completed context trend;
      2. detect a confirmed sweep on `sweep_tf`;
      3. wait for a signal-timeframe CHoCH + displacement + FVG;
      4. place a limit at the FVG edge;
      5. use the same R target and cost model for all timeframe variants.

    The only intentional changes between variants are signal/sweep/context
    timeframes and the time-equivalent waiting window.
    """
    sig_tf = signal_tf or variant.signal_tf
    signal = completed_bars(df_raw, sig_tf)
    sweep = completed_bars(df_raw, variant.sweep_tf)
    context_end, context_trend = build_causal_htf_structure(df_raw, variant.context_tf, 2)

    oh = signal["Open"].to_numpy(dtype=float)
    hh = signal["High"].to_numpy(dtype=float)
    ll = signal["Low"].to_numpy(dtype=float)
    cc = signal["Close"].to_numpy(dtype=float)
    st = signal.index
    atr = causal_atr14(hh, ll, cc)
    sig_swings = detect_swings_causal(hh, ll, st, variant.signal_k)
    sweep_swings = detect_swings_causal(
        sweep["High"].to_numpy(dtype=float),
        sweep["Low"].to_numpy(dtype=float),
        sweep.index,
        variant.sweep_k,
    )
    sh = sweep["High"].to_numpy(dtype=float)
    sl = sweep["Low"].to_numpy(dtype=float)
    sc = sweep["Close"].to_numpy(dtype=float)
    sweep_end = sweep.index

    # A sweep level is kept alive until it is invalidated or reaches a generous
    # age.  This mirrors the active-level logic of the core sniper, but uses a
    # time-based cap so 1H and 4H variants are not accidentally given 1m limits.
    max_sweep_age = 120 if variant.sweep_tf == "1h" else 60
    active_highs: list[Any] = []
    active_lows: list[Any] = []
    last_sig_high: float | None = None
    last_sig_low: float | None = None
    sweep_ptr = 0
    pending: list[dict[str, Any]] = []
    sweep_candidates: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    busy_until = -1
    # Keep the waiting budget in elapsed time so the three variants are
    # comparable: 15m/5m get more bars, while 4H gets fewer bars.
    bar_minutes = pd.Timedelta(sig_tf).total_seconds() / 60.0
    wait_bars = max(1, int(round(variant.max_wait_hours * 60.0 / bar_minutes)))
    warmup = eval_start - pd.Timedelta(days=30)

    for i, tm in enumerate(st):
        # Bring all completed sweep bars up to this signal-bar end time into the
        # causal state.  A sweep creates a candidate, never an instant fill.
        while sweep_ptr < len(sweep_end) and sweep_end[sweep_ptr] <= tm:
            k = sweep_ptr
            for sp in active_lows:
                if (k - sp.candle_idx) >= variant.min_age_bars and sl[k] < sp.price and sc[k] > sp.price:
                    start_i = int(st.searchsorted(sweep_end[k], side="left"))
                    sweep_candidates.append(
                        {
                            "side": "LONG",
                            "start_i": start_i,
                            "sweep_time": sweep_end[k],
                            "sl_base": float(sl[k]),
                            "choch": last_sig_high,
                        }
                    )
            for sp in active_highs:
                if (k - sp.candle_idx) >= variant.min_age_bars and sh[k] > sp.price and sc[k] < sp.price:
                    start_i = int(st.searchsorted(sweep_end[k], side="left"))
                    sweep_candidates.append(
                        {
                            "side": "SHORT",
                            "start_i": start_i,
                            "sweep_time": sweep_end[k],
                            "sl_base": float(sh[k]),
                            "choch": last_sig_low,
                        }
                    )
            active_highs = [sp for sp in active_highs if sh[k] <= sp.price and (k - sp.candle_idx) <= max_sweep_age]
            active_lows = [sp for sp in active_lows if sl[k] >= sp.price and (k - sp.candle_idx) <= max_sweep_age]
            for sp in sweep_swings.get(k, []):
                if sp.kind == "high" and np.max(sh[sp.candle_idx + 1 : k + 1]) <= sp.price:
                    active_highs.append(sp)
                elif sp.kind == "low" and np.min(sl[sp.candle_idx + 1 : k + 1]) >= sp.price:
                    active_lows.append(sp)
            sweep_ptr += 1

        context_dir = _trend_at(context_end, context_trend, tm)
        kz_ok = (not asset_spec.use_killzone or in_killzone_utc(tm)) and (
            asset_spec.min_hour_utc is None or tm.hour >= asset_spec.min_hour_utc
        )

        # Manage existing limits on completed signal bars.
        next_pending: list[dict[str, Any]] = []
        for order in pending:
            if i > order["expire_i"]:
                continue
            if order["side"] == "LONG":
                # A bar opening below the stop or touching the stop before the
                # limit is filled invalidates the pending setup.
                if oh[i] <= order["sl"]:
                    continue
                if ll[i] <= order["trig"]:
                    if i <= busy_until or not kz_ok or not (eval_start <= tm < eval_end):
                        if ll[i] <= order["sl"] or i <= busy_until:
                            continue
                        next_pending.append(order)
                        continue
                    fill = min(float(oh[i]), float(order["trig"]))
                    risk = fill - float(order["sl"])
                    if risk < max(asset_spec.min_risk_abs, fill * asset_spec.min_risk_pct):
                        continue
                    result = _simulate_fixed_rr(
                        bars=signal,
                        entry_idx=i,
                        side="LONG",
                        fill=fill,
                        sl=float(order["sl"]),
                        rr=asset_spec.rr,
                        fixed_cost=asset_spec.fixed_cost,
                        pct_cost=asset_spec.pct_cost,
                        setup_time=pd.Timestamp(order["setup_time"]),
                        asset=asset_spec.name,
                        engine=variant.name,
                    )
                    if result is not None:
                        busy_until = int(result["exit_idx"])
                        trades.append(result)
                    continue
            else:
                if oh[i] >= order["sl"]:
                    continue
                if hh[i] >= order["trig"]:
                    if i <= busy_until or not kz_ok or not (eval_start <= tm < eval_end):
                        if hh[i] >= order["sl"] or i <= busy_until:
                            continue
                        next_pending.append(order)
                        continue
                    fill = max(float(oh[i]), float(order["trig"]))
                    risk = float(order["sl"]) - fill
                    if risk < max(asset_spec.min_risk_abs, fill * asset_spec.min_risk_pct):
                        continue
                    result = _simulate_fixed_rr(
                        bars=signal,
                        entry_idx=i,
                        side="SHORT",
                        fill=fill,
                        sl=float(order["sl"]),
                        rr=asset_spec.rr,
                        fixed_cost=asset_spec.fixed_cost,
                        pct_cost=asset_spec.pct_cost,
                        setup_time=pd.Timestamp(order["setup_time"]),
                        asset=asset_spec.name,
                        engine=variant.name,
                    )
                    if result is not None:
                        busy_until = int(result["exit_idx"])
                        trades.append(result)
                    continue
            next_pending.append(order)
        pending = next_pending

        # Do not form a setup before the evaluation warm-up.  The daily/4H
        # structure itself is still allowed to warm up causally before EV0.
        if i >= 2 and warmup <= tm < eval_end and kz_ok and context_dir != 0:
            a = float(atr[i]) if np.isfinite(atr[i]) and atr[i] > 0 else np.nan
            if np.isfinite(a) and a > 0:
                c1i, c2i, c3i = i - 2, i - 1, i
                body = abs(float(cc[c2i] - oh[c2i]))
                bull_gap = float(ll[c3i] - hh[c1i])
                bear_gap = float(ll[c1i] - hh[c3i])
                keep_candidates: list[dict[str, Any]] = []
                for cand in sweep_candidates:
                    age = i - int(cand["start_i"])
                    if i <= int(cand["start_i"]) or age > wait_bars:
                        if age <= wait_bars:
                            keep_candidates.append(cand)
                        continue
                    side = cand["side"]
                    if side == "LONG":
                        if ll[i] < cand["sl_base"]:
                            continue
                        ok = (
                            context_dir == 1
                            and cand["choch"] is not None
                            and cc[c3i] > float(cand["choch"])
                            and bull_gap >= variant.fvg_atr * a
                            and cc[c2i] > oh[c2i]
                            and body >= variant.displacement_atr * a
                        )
                        if ok:
                            trig = float(ll[c3i])
                            stop = float(cand["sl_base"] - variant.sl_buffer_atr * a)
                            risk = trig - stop
                            if risk >= max(asset_spec.min_risk_abs, trig * asset_spec.min_risk_pct):
                                pending.append(
                                    {
                                        "side": "LONG",
                                        "trig": trig,
                                        "sl": stop,
                                        "setup_time": tm,
                                        "expire_i": i + max(1, int(round(wait_bars / 2))),
                                    }
                                )
                                continue
                    else:
                        if hh[i] > cand["sl_base"]:
                            continue
                        ok = (
                            context_dir == -1
                            and cand["choch"] is not None
                            and cc[c3i] < float(cand["choch"])
                            and bear_gap >= variant.fvg_atr * a
                            and cc[c2i] < oh[c2i]
                            and body >= variant.displacement_atr * a
                        )
                        if ok:
                            trig = float(hh[c3i])
                            stop = float(cand["sl_base"] + variant.sl_buffer_atr * a)
                            risk = stop - trig
                            if risk >= max(asset_spec.min_risk_abs, trig * asset_spec.min_risk_pct):
                                pending.append(
                                    {
                                        "side": "SHORT",
                                        "trig": trig,
                                        "sl": stop,
                                        "setup_time": tm,
                                        "expire_i": i + max(1, int(round(wait_bars / 2))),
                                    }
                                )
                                continue
                    keep_candidates.append(cand)
                sweep_candidates = keep_candidates

        # Swing confirmations become visible only after the current signal bar is
        # complete.  Thus the current bar cannot use its own newly confirmed
        # swing as CHoCH input.
        for sp in sig_swings.get(i, []):
            if sp.kind == "high":
                last_sig_high = float(sp.price)
            else:
                last_sig_low = float(sp.price)

    trades.sort(key=lambda t: pd.Timestamp(t["exit_time"]))
    return trades


def _run_one_asset(df: pd.DataFrame, spec: AssetSpec, variant: Variant) -> list[dict[str, Any]]:
    signal_tf = CONTROL_SIGNAL_TF[spec.name] if variant.name == "LTF_control" else variant.signal_tf
    return run_scaled_sniper(df, EV0, EV1, asset_spec=spec, variant=variant, signal_tf=signal_tf)


def summarize(trades: list[dict[str, Any]], *, risk_pct: float = 0.01) -> dict[str, Any]:
    if not trades:
        return {
            "n": 0,
            "wr_pct": 0.0,
            "net_r": 0.0,
            "pf": 0.0,
            "max_dd_r": 0.0,
            "t_stat": 0.0,
            "avg_r": 0.0,
            "median_r": 0.0,
            "positive_years": 0,
            "total_years": 0,
            "max_consecutive_losses": 0,
            "avg_hold_hours": 0.0,
            "compound_100_1pct": simulate_compounded_account([], start_capital=100.0, risk_pct=risk_pct, compound=True),
        }
    ordered = sorted(trades, key=lambda x: pd.Timestamp(x["exit_time"]))
    rs = np.asarray([float(t["net_r"]) for t in ordered], dtype=float)
    wins = rs[rs > 0]
    losses = rs[rs < 0]
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) else 999.0
    cum = np.cumsum(rs)
    peak = np.maximum.accumulate(np.insert(cum, 0, 0.0))[1:]
    dd = peak - cum
    years = pd.Series(rs, index=pd.DatetimeIndex([pd.Timestamp(t["entry_time"]) for t in ordered])).groupby(lambda x: x.year).sum()
    consecutive = 0
    max_consecutive = 0
    for r in rs:
        if r < 0:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
        else:
            consecutive = 0
    holds = [
        (pd.Timestamp(t["exit_time"]) - pd.Timestamp(t["entry_time"])).total_seconds() / 3600.0
        for t in ordered
    ]
    return {
        "n": int(len(rs)),
        "wr_pct": round(float(100.0 * np.mean(rs > 0)), 2),
        "net_r": round(float(rs.sum()), 2),
        "pf": round(pf, 3),
        "max_dd_r": round(float(np.max(dd)), 2),
        "t_stat": round(float(rs.mean() / (rs.std(ddof=1) / np.sqrt(len(rs)))) if len(rs) > 1 and rs.std(ddof=1) > 0 else 0.0, 2),
        "avg_r": round(float(rs.mean()), 4),
        "median_r": round(float(np.median(rs)), 4),
        "positive_years": int((years > 0).sum()),
        "total_years": int(len(years)),
        "yearly_r": {str(int(k)): round(float(v), 2) for k, v in years.items()},
        "max_consecutive_losses": int(max_consecutive),
        "avg_hold_hours": round(float(np.mean(holds)), 2),
        "compound_100_1pct": simulate_compounded_account(ordered, start_capital=100.0, risk_pct=risk_pct, compound=True),
    }


def _portfolio_lock_one_global(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(trades, key=lambda x: (pd.Timestamp(x["entry_time"]), pd.Timestamp(x["exit_time"])))
    kept: list[dict[str, Any]] = []
    busy = pd.Timestamp.min.tz_localize("UTC")
    for t in ordered:
        entry = pd.Timestamp(t["entry_time"])
        if entry > busy:
            kept.append(t)
            busy = pd.Timestamp(t["exit_time"])
    return sorted(kept, key=lambda x: pd.Timestamp(x["exit_time"]))


def _summary_with_cost_stress(trades: list[dict[str, Any]], specs: dict[str, AssetSpec]) -> dict[str, Any]:
    by_asset: dict[str, list[dict[str, Any]]] = {a: [] for a in specs}
    for t in trades:
        by_asset.setdefault(str(t["asset"]), []).append(t)
    stressed: list[dict[str, Any]] = []
    for asset, rows in by_asset.items():
        spec = specs[asset]
        stressed.extend(_reprice_cost(rows, spec.fixed_cost, spec.pct_cost, multiplier=2.0))
    return summarize(stressed)


def make_chart(all_trades: dict[str, list[dict[str, Any]]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - chart is optional
        print(f"[chart skipped] {exc}")
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    colors = {"LTF_control": "#64748b", "HTF_1H": "#2563eb", "HTF_4H": "#16a34a"}
    for name, trades in all_trades.items():
        if not trades:
            continue
        d = pd.DataFrame(trades)
        d["exit_dt"] = pd.to_datetime(d["exit_time"], utc=True)
        d = d.sort_values("exit_dt")
        eq = d["net_r"].cumsum()
        peak = np.maximum.accumulate(np.insert(eq.to_numpy(), 0, 0.0))[1:]
        dd = eq.to_numpy() - peak
        ax1.plot(d["exit_dt"], eq, label=name, color=colors.get(name), linewidth=1.8)
        ax2.plot(d["exit_dt"], dd, label=name, color=colors.get(name), linewidth=1.5)
    ax1.set_title("Matched sweep → CHoCH/FVG: cumulative net R")
    ax1.set_ylabel("Net R")
    ax2.set_title("Matched experiment: drawdown path")
    ax2.set_ylabel("Drawdown (R)")
    for ax in (ax1, ax2):
        ax.grid(alpha=0.25)
        ax.legend()
        ax.set_xlabel("UTC")
    fig.tight_layout()
    fig.savefig(RESULTS / "ltf_vs_htf_equity_dd.png", dpi=160)
    plt.close(fig)


def write_report(summary: dict[str, Any]) -> None:
    official = summary["official_v8_reference"]
    variants = summary["variants"]
    lines = [
        "# تجربة رفع الفريمات للاستراتيجية — بدون لمس الملفات الأساسية",
        "",
        "> هذه تجربة مستقلة. لم يتم تعديل `V8_3Asset_1PosEach_QC.py` أو `engine/smc_v4_portfolio.py` أو أي ملف مصدر داخل الحزمة.",
        "",
        "## السؤال",
        "هل إزالة إشارات 5m/15m واستبدالها بإشارة 1H أو 4H تجعل نفس عائلة Sweep → CHoCH → Displacement/FVG أفضل؟",
        "",
        "## النتيجة المختصرة",
        "",
    ]
    for name in ("LTF_control", "HTF_1H", "HTF_4H"):
        p = variants[name]["portfolio_3asset_1pos_each"]
        lines.append(
            f"- **{name}**: N={p['n']}, WR={p['wr_pct']}%, Net={p['net_r']}R, "
            f"PF={p['pf']}, MaxDD={p['max_dd_r']}R, t={p['t_stat']}, "
            f"سنوات موجبة={p['positive_years']}/{p['total_years']}, "
            f"متوسط مدة الصفقة={p['avg_hold_hours']} ساعة."
        )
    lines += [
        "",
        "## مقارنة مرجع V8 الرسمي",
        "",
        f"مرجع `summary_v8_multiasset.json` للـ`V8_3Asset_1PosEach`: N={official['n']}، WR={official['wr_pct']}%، Net={official['net_r']}R، PF={official['pf']}، MaxDD={official['max_dd_r']}R، t={official['t_stat']}.",
        "",
        "هذا المرجع ليس نفس محرك التجربة حرفياً؛ هو نتيجة V8 الرسمية الموجودة في الحزمة. أما المقارنة بين LTF وHTF هنا فهي مقارنة matched داخل نفس المحرك التجريبي وبنفس قواعد الدخول/الخروج والتكلفة.",
        "",
        "## حدود المطابقة مع ملف QC",
        "",
        "هذه ليست إعادة تشغيل لملف QuantConnect داخل محرك QC. ملف QC الأصلي ينفذ minute data مع bid/ask وOrder Events وtrailing وstep locks، بينما هذا الاختبار يعزل سؤال الفريم فقط باستخدام OHLC مكتمل، أهداف R ثابتة، وملء محافظ على فريم الإشارة. لذلك لا يجوز استبدال نتيجة الاختبار بنتيجة V8 الرسمية؛ المقارنة الصالحة هنا هي LTF_control مقابل HTF_1H/HTF_4H داخل نفس التجربة فقط.",
        "",
        "## جدول النتائج لكل أصل",
        "",
        "| النسخة | الأصل | N | WR% | Net R | PF | MaxDD R | t-stat | سنوات موجبة | 2x cost Net R |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("LTF_control", "HTF_1H", "HTF_4H"):
        for asset in ("XAUUSD", "NSXUSD", "BTCUSD"):
            p = variants[name]["by_asset"][asset]
            s = variants[name]["by_asset_2x_cost"][asset]
            lines.append(
                f"| {name} | {asset} | {p['n']} | {p['wr_pct']} | {p['net_r']} | {p['pf']} | {p['max_dd_r']} | {p['t_stat']} | {p['positive_years']}/{p['total_years']} | {s['net_r']} |"
            )
    lines += [
        "",
        "## ماذا تغيّر بالضبط؟",
        "",
        "| النسخة | فريم الإشارة | فريم السويب | فريم السياق | نافذة انتظار |",
        "|---|---|---|---|---|",
        "| LTF control | XAU/NSX 15m، BTC 5m | 1H | 4H | 12 ساعة |",
        "| HTF 1H | 1H | 4H | 1D | 24 ساعة |",
        "| HTF 4H | 4H | 4H | 1D | 48 ساعة |",
        "",
        "قواعد الدخول بقيت: Sweep مؤكد causal، ثم CHoCH، ثم displacement بجسم لا يقل عن 1 ATR، ثم FVG لا يقل عن 0.25 ATR، ثم Limit عند طرف FVG. الوقف خلف extreme السويب مع buffer = 1 ATR. الأهداف بقيت ثابتة: XAU/NSX = 10R وBTC = 15R، والتكاليف بقيت أصلية لكل أصل.",
        "",
        "## ملاحظات منهجية مهمة",
        "",
        "1. التجربة تستخدم completed bars فقط؛ لا تستخدم إغلاق شمعة 4H قبل انتهاء الشمعة.",
        "2. إذا لمس نفس الـbar الوقف والهدف بعد التعبئة، حُسب الوقف أولاً، وهو افتراض محافظ.",
        "3. التعبئة تتم على فريم الإشارة نفسه، وليس على minute tick؛ لذلك لا نقول إن هذا يعادل fill QuantConnect.",
        "4. استخدمنا نفس الفترة `2020-02-01 .. 2026-10-31` ونفس البيانات المحلية المتاحة.",
        "5. `1PosEach` يسمح بمركز لكل أصل؛ النتائج المجمعة ليست global one-position.",
        "6. `2x cost` إعادة تسعير للتكاليف فقط، لا تعني أن السبريد الحقيقي ثابت أو أن الانزلاق مضمون.",
        "",
        "## الحكم",
        "",
        "الفريم الأعلى لا يصبح خارقاً تلقائياً. الحكم الصحيح يكون من خلال Net R مع PF وMaxDD وWR وt-stat وعدد الصفقات واستقرار السنوات، لا من خلال compounding وحده. إذا تحسن PF وDD لكن انهار عدد الصفقات أو Net R، فهذه نسخة أنظف بصرياً وليست بالضرورة أفضل تجارياً. وإذا تحسن Net R فقط مع تراجع 2x-cost، فغالباً النتيجة حساسة للتكلفة.",
        "",
        "الملفات الناتجة موجودة في مجلد `htf_timeframe_experiment/results/`، والسكربت المستقل هو `htf_timeframe_experiment/run_experiment.py`.",
    ]
    (OUT_ROOT / "REPORT_AR.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("Loading local data (read-only) ...", flush=True)
    frames: dict[str, pd.DataFrame] = {}
    specs = {s.name: s for s in ASSETS}
    for spec in ASSETS:
        path = PKG_ROOT / "data" / spec.data_dir
        print(f"  {spec.name}: {path.name}", flush=True)
        frames[spec.name] = load_asset_ohlcv(path, list(spec.stems))
        frames[spec.name] = frames[spec.name].loc[
            (frames[spec.name].index >= pd.Timestamp("2019-01-01", tz="UTC"))
            & (frames[spec.name].index < EV1)
        ]
        print(f"    {len(frames[spec.name]):,} source bars", flush=True)

    all_trades: dict[str, list[dict[str, Any]]] = {}
    summary: dict[str, Any] = {
        "experiment": "same causal sweep -> CHoCH/FVG with higher signal timeframe",
        "evaluation_window": {"start": str(EV0), "end": str(EV1)},
        "variants_config": {v.name: asdict(v) for v in VARIANTS},
        "official_v8_reference": json.loads((PKG_ROOT / "results" / "summary_v8_multiasset.json").read_text(encoding="utf-8"))["portfolios_1x"]["V8_3Asset_1PosEach"],
        "variants": {},
    }

    for variant in VARIANTS:
        print(f"\nRunning {variant.name}: {variant.label_ar}", flush=True)
        per_asset: dict[str, list[dict[str, Any]]] = {}
        for spec in ASSETS:
            print(f"  {spec.name} ...", flush=True)
            trades = _run_one_asset(frames[spec.name], spec, variant)
            per_asset[spec.name] = trades
            pd.DataFrame(trades).to_csv(RESULTS / f"trades_{variant.name}_{spec.name}.csv", index=False)
            print(f"    {len(trades)} trades", flush=True)
        portfolio = sorted(
            [t for rows in per_asset.values() for t in rows],
            key=lambda x: pd.Timestamp(x["exit_time"]),
        )
        all_trades[variant.name] = portfolio
        pd.DataFrame(portfolio).to_csv(RESULTS / f"trades_{variant.name}_3asset_1pos_each.csv", index=False)
        portfolio_global = _portfolio_lock_one_global(portfolio)
        summary["variants"][variant.name] = {
            "by_asset": {asset: summarize(rows) for asset, rows in per_asset.items()},
            "by_asset_2x_cost": {
                asset: summarize(
                    _reprice_cost(rows, specs[asset].fixed_cost, specs[asset].pct_cost, multiplier=2.0)
                )
                for asset, rows in per_asset.items()
            },
            "portfolio_3asset_1pos_each": summarize(portfolio),
            "portfolio_3asset_1pos_each_2x_cost": _summary_with_cost_stress(portfolio, specs),
            "portfolio_global_1pos": summarize(portfolio_global),
            "trade_counts": {asset: len(rows) for asset, rows in per_asset.items()},
        }
        p = summary["variants"][variant.name]["portfolio_3asset_1pos_each"]
        print(
            f"  portfolio: N={p['n']} WR={p['wr_pct']}% Net={p['net_r']}R PF={p['pf']} DD={p['max_dd_r']}R t={p['t_stat']}",
            flush=True,
        )

    (RESULTS / "summary_htf_experiment.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    make_chart(all_trades)
    write_report(summary)
    print(f"\nSaved experiment artifacts under {OUT_ROOT}", flush=True)


if __name__ == "__main__":
    main()
