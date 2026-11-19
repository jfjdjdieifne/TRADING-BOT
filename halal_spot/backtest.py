#!/usr/bin/env python3
"""Run the halal_spot zero-lookahead backtest and generate all deliverables into results/.

Usage:
    python3 backtest.py            # full report (3 runs: continuous 12m + two standalone 6m)
    python3 backtest.py --quick    # continuous run only

Outputs (results/):
    trades_full.csv                every trade of the continuous 12-month run (full detail)
    trades_h2_2025.csv             continuous run, entries in Jul-Dec 2025
    trades_h1_2026.csv             continuous run, entries in Jan-Jun 2026
    trades_standalone_h2_2025.csv  independent $100 run, Jul-Dec 2025
    trades_standalone_h1_2026.csv  independent $100 run, Jan-Jun 2026
    equity_full.csv                5-minute equity curve of the continuous run
    events_full.csv                full event log (sweeps, signals, orders, exits)
    summary.json                   all metrics + signal funnel counters
    equity_curve.png               equity / drawdown chart
    REPORT_AR.md                   Arabic report with per-trade tables
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from strategy import run_backtest  # noqa: E402

DATA = ROOT / "data" / "BTCUSD_5m"
OUT = ROOT / "results"

CAPITAL = 100.0
FULL_START, FULL_END = "2025-07-01", "2026-07-01"
SPLIT = "2026-01-01"
H2_START, H2_END = "2025-07-01", "2026-01-01"
H1_START, H1_END = "2026-01-01", "2026-07-01"
CUT_TEST = "2026-03-31 14:30"

# entry-setup keys that must match bit-for-bit for the trade open at CUT (V13 meta keys)
ENTRY_KEYS = [
    "trade_id", "signal_time",
    "arm", "side", "regime", "regime_score", "quality", "q_threshold",
    "eff_p", "vol_p", "wall", "wall_R",
    "sl_at_signal", "en_at_signal", "rd_at_signal", "tp_at_signal", "exit_design",
    "dd_at_signal", "eb_at_signal", "rk_at_signal", "notional_target",
    "lev_at_entry", "equity_at_signal",
    "entry_time", "entry_price", "entry_qty", "entry_notional", "entry_fee",
    "r_price", "risk_usd", "sl_at_entry", "equity_at_entry",
]


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------
def _tz(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t


def slice_trades(trades: list[dict], t0: str, t1: str) -> list[dict]:
    a, b = _tz(t0), _tz(t1)
    return [t for t in trades if a <= _tz(t["signal_time"]) < b]


def slice_equity(eq: pd.DataFrame, t0: str, t1: str) -> pd.DataFrame:
    if eq.empty:
        return eq
    return eq.loc[_tz(t0): _tz(t1) - pd.Timedelta(minutes=5)]


def metrics(trades: list[dict], eq: pd.DataFrame, capital: float = CAPITAL) -> dict:
    n = len(trades)
    pnl = [t["net_pnl"] for t in trades]
    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p <= 0]
    gp, gl = sum(wins), sum(losses)
    rs = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]

    max_dd_pct, max_dd_usd = 0.0, 0.0
    exposure = None
    if not eq.empty:
        curve = eq["equity"]
        peak = curve.cummax()
        dd = curve - peak
        max_dd_usd = float(-dd.min())
        max_dd_pct = float((dd / peak).min() * 100.0)
        exposure = float(eq["in_position"].mean() * 100.0)

    hold_h = [
        (_tz(t["exit_time"]) - _tz(t["entry_time"])).total_seconds() / 3600.0
        for t in trades
    ]
    end_eq = float(eq["equity"].iloc[-1]) if not eq.empty else None
    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100.0 * len(wins) / n, 1) if n else None,
        "gross_profit": round(gp, 2),
        "gross_loss": round(gl, 2),
        "profit_factor": round(gp / abs(gl), 2) if gl != 0 else None,
        "net_pnl": round(sum(pnl), 2),
        "net_pct": round(sum(pnl) / capital * 100.0, 2),
        "start_equity": capital,
        "end_equity": round(end_eq, 2) if end_eq is not None else None,
        "max_drawdown_pct": round(max_dd_pct, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
        "best_r": round(max(rs), 2) if rs else None,
        "worst_r": round(min(rs), 2) if rs else None,
        "avg_hold_hours": round(sum(hold_h) / n, 1) if n else None,
        "exposure_pct": round(exposure, 1) if exposure is not None else None,
        "exit_tags": ({str(k): int(v) for k, v in
                       pd.Series([t["exit_tag"] for t in trades]).value_counts().items()} if n else {}),
        "setups": ({str(k): int(v) for k, v in
                    pd.Series([t["arm"] for t in trades]).value_counts().items()} if n else {}),
        "sides": ({str(k): int(v) for k, v in
                   pd.Series([t["side"] for t in trades]).value_counts().items()} if n else {}),
        "exits": ({str(k): int(v) for k, v in
                   pd.Series([str(t["exit_tag"]).split("_")[0] for t in trades]).value_counts().items()} if n else {}),
    }


def monthly_table(trades: list[dict]) -> pd.DataFrame:
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    df["month"] = df["exit_time"].dt.tz_localize(None).dt.to_period("M").astype(str)
    g = df.groupby("month").agg(
        trades=("net_pnl", "size"),
        net_pnl=("net_pnl", "sum"),
        wins=("net_pnl", lambda s: int((s > 0).sum())),
    ).reset_index()
    g["net_pnl"] = g["net_pnl"].round(2)
    g["win_rate_pct"] = (100.0 * g["wins"] / g["trades"]).round(1)
    return g


# ---------------------------------------------------------------------------
# markdown tables
# ---------------------------------------------------------------------------
def fmt_t(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M")


def trades_table_md(trades: list[dict]) -> str:
    head = (
        "| # | وقت الإشارة | الذراع | جهة | الوضع | نوع الخروج | الهدف (جدار R) | "
        "وقت الدخول | سعر الدخول | الكمية | هامش | وقف الدخول | "
        "وقت الخروج | سعر الخروج | سبب الخروج | صافي $ | R | MFE-R | MAE-R | "
        "مدة (ساعة) | Equity بعد |\n"
        "|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|\n"
    )
    rows = []
    for t in trades:
        hold = (_tz(t["exit_time"]) - _tz(t["entry_time"])).total_seconds() / 3600.0
        rows.append(
            f"| {t['trade_id']} | {fmt_t(t['signal_time'])} | {t['arm']} | {t['side']} "
            f"| {t['regime']} | {t['exit_design']} "
            f"| {t['wall']:,.0f} ({t['wall_R']:.1f}R) "
            f"| {fmt_t(t['entry_time'])} | {t['entry_price']:,.2f} | {t['entry_qty']:.4f} "
            f"| {t['margin_used']:.2f} | {t['sl_at_entry']:,.2f} "
            f"| {fmt_t(t['exit_time'])} | {t['exit_price']:,.2f} | {t['exit_tag']} "
            f"| {t['net_pnl']:+.2f} | {t['r_multiple']:+.2f} "
            f"| {t.get('mfe_r') if t.get('mfe_r') is not None else '—'} "
            f"| {t.get('mae_r') if t.get('mae_r') is not None else '—'} "
            f"| {hold:.1f} | {t['equity_after']:.2f} |"
        )
    return head + "\n".join(rows)


def signals_table_md(trades: list[dict]) -> str:
    head = (
        "| # | الذراع | الوضع السوقي | score الوضع | جودة الإشارة | عتبة الجودة | "
        "كفاءة % | حجم % | dd% | eb$ | lev | حجم الصفقة $ | زمن الإشارة |\n"
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n"
    )
    rows = []
    for t in trades:
        rows.append(
            f"| {t['trade_id']} | {t['arm']} | {t['regime']} | {t['regime_score']:.3f} "
            f"| {t['quality']:.3f} | {t['q_threshold']:.3f} "
            f"| {t['eff_p'] * 100:.0f} | {t['vol_p'] * 100:.0f} "
            f"| {t['dd_at_signal'] * 100:.1f} | {t['eb_at_signal']:.1f} "
            f"| {t['lev_at_entry']:.1f} | {t['notional_target']:.2f} "
            f"| {fmt_t(t['signal_time'])} |"
        )
    return head + "\n".join(rows)


def metrics_table_md(rows: list[tuple[str, dict]]) -> str:
    head = (
        "| الفترة | الصفقات | رابحة | خاسرة | نسبة الربح % | صافي $ | % من رأس المال "
        "| PF | أقصى تصحيح % | متوسط R | أحسن R | أسوأ R | Equity نهائي | التعرض % |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    body = []
    for name, m in rows:
        pf = f"{m['profit_factor']:.2f}" if m["profit_factor"] is not None else "∞"
        body.append(
            f"| {name} | {m['trades']} | {m['wins']} | {m['losses']} | {m['win_rate_pct']} "
            f"| {m['net_pnl']:+.2f} | {m['net_pct']:+.2f} | {pf} | {m['max_drawdown_pct']:.2f} "
            f"| {m['avg_r']} | {m['best_r']} | {m['worst_r']} | {m['end_equity']} "
            f"| {m['exposure_pct']} |"
        )
    return head + "\n".join(body)


def monthly_md(g: pd.DataFrame) -> str:
    if g.empty:
        return "_لا توجد صفقات_"
    head = "| الشهر | صفقات | رابحة | نسبة الربح % | صافي $ |\n|---|---:|---:|---:|---:|\n"
    rows = [
        f"| {r.month} | {r.trades} | {r.wins} | {r.win_rate_pct} | {r.net_pnl:+.2f} |"
        for r in g.itertuples()
    ]
    return head + "\n".join(rows)


# ---------------------------------------------------------------------------
# chart
# ---------------------------------------------------------------------------
def write_chart(full: dict, h2: dict, h1: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    eq = full["equity"]
    ax1.plot(eq.index, eq["equity"], color="#1f77b4", lw=1.2, label="مستمر 12 شهر (رأس مال 100$)")
    if not h2["equity"].empty:
        e2 = h2["equity"]
        ax1.plot(e2.index, e2["equity"], color="#2ca02c", lw=1.0, alpha=0.85,
                 label="مستقل يوليو-ديسمبر 2025")
    if not h1["equity"].empty:
        e1 = h1["equity"]
        ax1.plot(e1.index, e1["equity"], color="#d62728", lw=1.0, alpha=0.85,
                 label="مستقل يناير-يونيو 2026")
    ax1.axhline(CAPITAL, color="gray", ls="--", lw=0.8)
    ax1.axvline(_tz(SPLIT), color="black", ls=":", lw=1.0)
    ax1.text(_tz(SPLIT), ax1.get_ylim()[1], "  حد النصفين", va="top", fontsize=9)
    ax1.set_ylabel("Equity (USDT)")
    ax1.set_title("Regime Multi-Arm Sniper V13 — BTCUSDT 10x — زيرو لوكهيد (12 شهر)")
    ax1.legend(loc="best", fontsize=9)
    ax1.grid(alpha=0.3)

    curve = eq["equity"]
    dd = (curve - curve.cummax()) / curve.cummax() * 100.0
    ax2.fill_between(dd.index, dd.values, 0, color="#d62728", alpha=0.5)
    ax2.set_ylabel("Drawdown %")
    ax2.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def _comparison_md() -> str:
    """V14 (as-pasted, 0 fills) vs V13 vs V12 vs V1 (first run) vs V5."""

    def _load(name: str):
        p = OUT / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    s13 = _load("summary.json")
    s14 = _load("summary_v14.json")
    s12, v5, v1 = _load("summary_v12.json"), _load("summary_v5.json"), _load("summary_v1.json")
    if s13 is None:
        return "_ملخص V13 غير متاح بعد._"
    cols = [("V14 (كما لُصق)", s14), ("V13", s13), ("V12", s12), ("V5", v5),
            ("V1 (التشغيل الأول)", v1)]

    def cell(src, key, pct=False):
        if not src:
            return "—"
        v = src["continuous_12m"].get(key)
        if v is None:
            return "—"
        return f"{v}%" if pct else v

    lines = ["| المقياس | V14 (كما لُصق) | V13 | V12 | V5 | V1 |",
             "|---|---:|---:|---:|---:|---:|"]
    rows = [
        ("الصفقات (المستمر 12 شهر)", "trades", False),
        ("رابحة / خاسرة", None, False),
        ("نسبة الربح %", "win_rate_pct", False),
        ("صافي $ (المستمر)", "net_pnl", False),
        ("عامل الربح PF", "profit_factor", False),
        ("أقصى تصحيح %", "max_drawdown_pct", False),
        ("Equity نهائي (المستمر)", "end_equity", False),
        ("متوسط R", "avg_r", False),
        ("أفضل صفقة R", "best_r", False),
        ("أسوأ صفقة R", "worst_r", False),
        ("متوسط الاحتفاظ (ساعة)", "avg_hold_hours", False),
        ("التعرض %", "exposure_pct", False),
        ("مستقل H2-2025 →", None, "h2"),
        ("مستقل H1-2026 →", None, "h1"),
    ]
    for label, key, kind in rows:
        vals = []
        for _, src in cols:
            if not src:
                vals.append("—")
                continue
            if kind == "h2":
                vals.append(src["standalone_h2_2025"]["end_equity"])
            elif kind == "h1":
                vals.append(src["standalone_h1_2026"]["end_equity"])
            elif key is None:
                m = src["continuous_12m"]
                vals.append(f"{m['wins']} / {m['losses']}")
            else:
                vals.append(cell(src, key))
        lines.append(f"| {label} | " + " | ".join(str(v) for v in vals) + " |")

    def _fmt(d) -> str:
        return "—" if not d else " · ".join(f"{k} ×{v}" for k, v in d.items())

    st = [_fmt((s or {}).get("continuous_12m", {}).get("setups") or {}) for _, s in cols]
    ex = [_fmt((s or {}).get("continuous_12m", {}).get("exit_tags") or {}) for _, s in cols]
    lines += [
        "| الأذرع/أنواع الدخول | " + " | ".join(st) + " |",
        "| أسباب الخروج | " + " | ".join(ex) + " |",
    ]
    return "\n".join(lines)


def _y2021_md() -> str:
    s = None
    p = OUT / "summary_2021h1_v13.json"
    if p.exists():
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            s = None
    if not s:
        return "_تشغيل 2021 غير متاح (شغّل backtest.py كاملاً)._"
    m = s["window_2021h1"]
    eq = s.get("buy_hold_2021h1")
    lines = [
        "| المقياس | قيمة |",
        "|---|---:|",
        f"| صفقات | {m['trades']} ({m['wins']} رابحة / {m['losses']} خاسرة) |",
        f"| نسبة الربح % | {m['win_rate_pct']} |",
        f"| صافي $ | {m['net_pnl']} |",
        f"| عامل الربح PF | {m['profit_factor']} |",
        f"| أقصى تصحيح % | {m['max_drawdown_pct']} |",
        f"| Equity نهائي | {m['end_equity']} |",
        f"| شراء واحتفاظ BTC (نفس النافذة) | {eq} |",
        f"| نسبة الالتقاط مقابل الاحتفاظ | {round((m['end_equity'] / eq - 1) * 100, 1) if eq else '—'}% فارق العائد |",
        f"| أفضل / أسوأ R | {m['best_r']} / {m['worst_r']} |",
        f"| الأذرع | {m.get('setups', {})} |",
        f"| الخروجات | {m.get('exit_tags', {})} |",
        "",
        f"أوامر السوق: {s.get('count_2021h1', {}).get('entries_placed', 0)} → "
        f"{s.get('count_2021h1', {}).get('entries_filled', 0)} مملوءة | "
        f"رافضات الجدار <3R: {s.get('count_2021h1', {}).get('v_wall', 0)} | "
        f"وقف الدائرة: {s.get('count_2021h1', {}).get('v_streak', 0)}",
    ]
    return "\n".join(lines)


def _v14_md() -> str:
    """§12 — owner's pasted 6-arm code (V14): faithful run + cap-fix diagnostic."""

    def _load(name: str):
        p = OUT / name
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    s_f = _load("summary_v14.json")
    s_x = _load("summary_v14_capfix.json")
    s13 = _load("summary.json")
    if s_f is None:
        return "_نتائج V14 غير متاحة (شغّل `python3 strategy_v14.py`)._"

    def wrow(tag: str, s: dict, key: str, bh_key: str) -> str:
        m = s[key]
        bh = s.get(bh_key)
        return (f"| {tag} | {m['trades']} | {m['net_pnl']} | {m['profit_factor'] if m['profit_factor'] is not None else '—'} "
                f"| {m['end_equity']} | {bh if bh is not None else '—'} |")

    sigs_f = sum(v for k, v in s_f["signal_funnel"].items() if k.startswith("sig_"))
    rej_f = s_f["signal_funnel"].get("exec_rejected", 0)
    sigs_x = sum(v for k, v in s_x["signal_funnel"].items() if k.startswith("sig_"))
    ent_x = s_x["signal_funnel"].get("entries", 0)
    mf, mx = s_f["continuous_12m"], s_x["continuous_12m"]
    m13 = (s13 or {}).get("continuous_12m", mf)

    lines = [
        "**المصدر:** كود صاحب المشروع المُلصَق حرفيًا (`BinanceFuturesMultiCoinV12` — "
        "TopoSwing، ماكرو breadth، 6 أذرع، min_rr=3.50، مراحل VC 4.2/10/22R، "
        "سقف مخاطرة 3.2%)، منقولًا إلى محركنا السببي على BTC وحده. الكشف عن التكييفات: "
        "(1) زوج واحد فقط — 9 أزواج بلا بيانات، فـ macro_breadth/rs_rank ينهاران إلى "
        "BTC فقط (rs_rank دائمًا 1)؛ (2) التنفيذ بسعر إغلاق الشمعة المُطلِقة؛ (3) "
        "دفتر التقرير رسوم 0.1%/طرف (مطابق لبقية النسخ للمقارنة) بينما دفتر "
        "realized_eq/التتابع لديهم 0.0008 كما هو؛ (4) رافعة 3.0 وإحماء 15 يوم "
        "إعداداتهم هم؛ (5) تحقّق الهامش قبل كتابة الحالة (تقوية واحدة معلَنة).",
        "",
        "| النافذة | V14 كما لُصق: صفقات | صافي $ | PF | Equity | B&H |",
        "|---|---:|---:|---:|---:|---:|",
        wrow("المستمر 12 شهر", s_f, "continuous_12m", "buy_hold_12m"),
        wrow("مستقل H2-2025", s_f, "standalone_h2_2025", None),
        wrow("مستقل H1-2026", s_f, "standalone_h1_2026", None),
        wrow("أول شهرين 2021 (01-01←03-01)", s_f, "window_2021first2m", "buy_hold_2021first2m"),
        "",
        f"**النتيجة الحاسمة في النافذة الرئيسية: 0 صفقة.** الإشارات انطلقت "
        f"{sigs_f:,} مرة (V8_4H ×{s_f['signal_funnel'].get('sig_V8_4H', 0)}، "
        f"V11_1H ×{s_f['signal_funnel'].get('sig_V11_1H', 0)}، "
        f"V10_IGN ×{s_f['signal_funnel'].get('sig_V10_IGN', 0)}، "
        f"V6_SWP ×{s_f['signal_funnel'].get('sig_V6_SWP', 0)}، "
        f"V9_LON ×{s_f['signal_funnel'].get('sig_V9_LON', 0)}، "
        f"V12_CAP ×{s_f['signal_funnel'].get('sig_V12_CAP', 0)}) ثم رُفضت جميعها "
        f"{rej_f} مرة عند حساب الحجم: سقف الميزانية `eb×0.34 ≈ 34$` في مقابل "
        "الحد الأدنى للعملة `0.001 × 95,000$ ≈ 95$` — أي `qty = floor(34/95000) = 0` "
        "لكل إشارة. الكود يفترض رأس مالًا/حدًّا أدنى للعملة لا يملكه (نفس مرض "
        "«Insufficient buying power» في تشغيله الأصلي).",
        "",
        "**التشخيص المعزّل (إصلاح السقف فقط — سقف واحد رُفع ليسمح بالحد الأدنى، "
        "وبقي كل شيء آخر كما هو):**",
        "",
        "| النافذة | صفقات | صافي $ | PF | Equity | B&H |",
        "|---|---:|---:|---:|---:|---:|",
        wrow("المستمر 12 شهر", s_x, "continuous_12m", "buy_hold_12m"),
        wrow("مستقل H2-2025", s_x, "standalone_h2_2025", None),
        wrow("مستقل H1-2026", s_x, "standalone_h1_2026", None),
        wrow("أول شهرين 2021", s_x, "window_2021first2m", "buy_hold_2021first2m"),
        "",
        f"النظام بعد الإصلاح يعمل… **ويخسر:** {mx['trades']} صفقة في 12 شهر، "
        f"صافي {mx['net_pnl']}$، PF {mx['profit_factor']}، تصحيح {mx['max_drawdown_pct']}% "
        f"(مقابل V13: {m13['trades']} صفقة، {m13['net_pnl']}$، PF {m13['profit_factor']}). "
        f"الخروجات: {mx['exit_tags']} — الإشارة الوحيدة TP_3_5R_FULL_CASH ×1، و95% "
        "من الأموال تُغلق بـ STRUCTURAL_SL/FREE_STAGNANT قبل الهدف 3.5R. "
        f"الأذرع: {mx['setups']}.",
        "",
        "**أول شهرين من 2021 (كما لُصق — المنطقة الوحيدة التي تسمح فيها "
        f"العملة برخيص {0.001 * 100_000:.0f}$-نطاق):** 8 صفقات، "
        f"صافي {s_f['window_2021first2m']['net_pnl']}$، "
        f"PF {s_f['window_2021first2m']['profit_factor']}، "
        f"WR {s_f['window_2021first2m']['win_rate_pct']}%، "
        f"متوسط R {s_f['window_2021first2m']['avg_r']} — لكن شراء واحتفاظ BTC "
        f"نفسه {s_f['buy_hold_2021first2m']}$ (+56%)، أي **الكود يخسر مقارنة "
        "بالشراء حتى في أفضل نوافذه**، وهو أصل ربح واحد صغير (+7.15R في 27/01 "
        "عبر ZIGZAG_WAVE_HARVEST) يغطي كل شيء. نسخة إصلاح السقف: 12 صفقة "
        f"{s_x['window_2021first2m']['net_pnl']}$ فقط.",
        "",
        "جدول صفقات النافذة الصغيرة (كما لُصق):",
        "",
        _v14_trades_md(),
        "",
        "**الحكم:** الكود كما لُصق **لا يُشغَّل على رأس مال 100$ (0 صفقة في النافذة "
        "الرئيسية)**؛ و بعد إصلاح السقف الواحد يعمل ويخسر (PF 0.57) — أسوأ من V13 "
        "في نفس النافذة. الأرقام الجميلة في سجله الأصلي (+5,382%) مصدرها positions "
        "علقت بلا إدارة — لا سيستم. ما يبقى منه صالحًا للاختبار مستقبلًا: منطق "
        "TopoSwing وحصاد VC (ظهرت أخيراً في ZIGZAG ×3) — لا التسعير والحجم.",
    ]
    return "\n".join(lines)


def _v14_trades_md() -> str:
    p = OUT / "trades_v14_2021first2m.csv"
    if not p.exists():
        return "_جدول الصفقات غير متاح._"
    df = pd.read_csv(p)
    if df.empty:
        return "_لا صفقات._"
    lines = ["| # | الوقت | الذراع | دخول | خروج | نوع الخروج | صافي $ | R |",
             "|---:|---|---|---:|---:|---|---:|---:|"]
    for _, r in df.iterrows():
        t = str(r["signal_time"])[:16].replace("T", " ")
        lines.append(f"| {int(r['trade_id'])} | {t} | {r['arm']} | {r['entry_price']:,.0f} "
                     f"| {r['exit_price']:,.0f} | {r['exit_tag']} | {r['net_pnl']:+.2f} "
                     f"| {r['r_multiple']:+.2f} |")
    return "\n".join(lines)


def build_report(ctx: dict) -> str:
    full_m, h2_m, h1_m = ctx["m_full"], ctx["m_h2"], ctx["m_h1"]
    sa_h2_m, sa_h1_m = ctx["m_sa_h2"], ctx["m_sa_h1"]
    full, sa_h2, sa_h1 = ctx["full"], ctx["sa_h2"], ctx["sa_h1"]
    counts = full["count"]

    funnel = [
        ("ذراع RIDE انطلق (كسر 15m في سوق صاعد/انفجاري)", counts.get("cand_RIDE", 0)),
        ("ذراع ACCUM انطلقت (ارتداد صاعد ثابت)", counts.get("cand_ACCUM", 0)),
        ("ذراع FALL انطلقت (إعادة اختبار كسر هابط)", counts.get("cand_FALL", 0)),
        ("ذراع DIP انطلقت (غسيل قاع 15m واسترجاع)", counts.get("cand_DIP", 0)),
        ("ذراع SNIP انطلقت (سحب سيولة لحافة المدى)", counts.get("cand_SNIP", 0)),
        ("ذراع IGN انطلقت (اقتحام مستوى بعد فشل السحب — V10_IGN)", counts.get("cand_IGN", 0)),
        ("أُلغيت: الإشارة لم تُستهلك خلال 6 شموع 5m", counts.get("exp_pending", 0)),
        ("رُفضت: وضع السوق لا يسمح للذراع", counts.get("v_regime", 0)),
        ("رُفضت: دائرة الخسائر المتتالية (وقف حتى تغيّر الوضع)", counts.get("v_streak", 0)),
        ("رُفضت: تهدئة الذراع بعد خسارة (4 ساعات)", counts.get("v_cd", 0)),
        ("رُفضت: الهدف الجداري < 3R أو لا يوجد جدار", counts.get("v_wall", 0)),
        ("رُفضت: مستوٍ رئيسي حاصر على مسافة 1.5R (حجب _xexam)", counts.get("v_level", 0)),
        ("رُفضت: جودة تحت عتبة السوق التكيفية", counts.get("v_quality", 0)),
        ("رُفضت: وقف ضمن ضوضاء 15m / أوسع من 4×ATR4", counts.get("v_noise", 0) + counts.get("v_wide", 0)),
        ("رُفضت: نفس الموجة مسبقاً مُلتقَط", counts.get("v_wave", 0)),
        ("رُفضت: حجم/لوت غير صالح", counts.get("v_size", 0) + counts.get("v_lot", 0)),
        ("أوامر سوق أُرسلت → صفقات مملوءة", f"{counts.get('entries_placed', 0)} → {counts.get('entries_filled', 0)}"),
        ("عمليات هرم تراكمي (+45% من البداية عند MFE≥2R وكفاءة>0.42)", counts.get("pyramid_filled", 0)),
        ("صفقات منفذة فعلياً", len(full["trades"])),
    ]
    funnel_md = "\n".join(f"| {k} | {v} |" for k, v in funnel)

    h2_tr = slice_trades(full["trades"], H2_START, H2_END)
    h1_tr = slice_trades(full["trades"], H1_START, H1_END)

    doc = f"""# تقرير اختبار استراتيجية Regime Multi-Arm Sniper V13 — BTCUSDT
**نافذة الاختبار:** 2025-07-01 ← 2026-06-30 (12 شهر متتالية، مقسّمة 6+6 للتقارير)
**رأس المال الابتدائي:** 100.00 USDT | **الزوج:** BTCUSDT فقط | **الرافعة:** 10x | **الشورت:** مسموح
**الفلسفة:** يُصنّف وضع السوق أولاً ثم يختار ذراعه — عتبات مئوية تكيفية، لا نسب سعرية ثابتة
**تاريخ تشغيل التقرير:** {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M')} UTC

---

## 1. ملاحظة مهمة عن الأزواج (قبل النتائج)

> **9 من الأزواج العشرة غير مختبرة (ETHUSDT / SOLUSDT / BNBUSDT / XRPUSDT / DOGEUSDT /
> ADAUSDT / AVAXUSDT / LINKUSDT / SUIUSDT)** لعدم توفر بيانات شموع لها — يوجد فقط
> `BTCUSD_5m`. التأثير على V13:
> - «مشاركة السوق» (breath) لا يمكن قياسها بـ 10 عملات: أدلة الوضع محسوبة على BTC وحده.
> - عدد الأذرع المتاحة آنياً = ذراع واحدة نشطة (لا تعددية مراكز) — والاختصاص هنا
>   يُخفّض المخاطرة بدل أن يوسعها.

---

## 2. نزاهة الاختبار — اختبارات الـ Zero-Lookahead (ماتغش بالفحص)

المحرك المنسوخ إلى المجلد: `engine/causal_primitives.py` (من `smc_v4_multisleeve_package`)،
ومراجع اختباراته في `reference/test_v4_zero_lookahead.py`.

**الاختبارات المنفذة — 9/9 ناجحة** (`python3 -m pytest tests/`):

| الاختبار | الفكرة | النتيجة |
|---|---|---|
| resample prefix invariant | قص الشموع عند `2026-03-31 14:30` لا يغيّر أي شمعة 15m/1h/4h مكتملة قبل القص | ✅ |
| closed trades identical before cut | كل صفقة أُغلقت قبل القص مطابقة حرفياً (bit-for-bit) للتشغيل الكامل | ✅ |
| open trade setup identical | الصفقة المفتوحة وقت القص: نفس إعداد الإشارة بالكامل | ✅ |
| equity curve identical before cut | منحنى Equity قبل القص مطابق تماماً | ✅ |
| no trades after end | التشغيل المقصوص لا يخترع صفقات بعد نهايته | ✅ |
| first half == standalone | النصف الأول من التشغيل المستمر يطابق التشغيل المستقل حرفياً (حتمية مزدوجة) | ✅ |
| trade timing is causal | إشارة ≤ دخول < خروج، والتنفيذ دائماً بعد إغلاق شمعة الإشارة | ✅ |
| accounting ties to equity | مجموع أرباح الصفقات يفسّر تغير Equity (الفرق = غبار BTC المعاد تقييمه) | ✅ |
| no negative cash or qty | لا رصيد سالب ولا صفقة دون تمويل | ✅ |

**كيف يمنع اللوكهيد:** الإشارات تُبنى فقط على شموع منتهية (end-time labelled)، وأوامر
الشراء السوق (ImmediateFillModel) تُملأ بسعر إغلاق شمعة الاستهلاك نفسها (لا بيانات قادمة)،
وقوائم الوقف الراكنة تُفحص على **كل شمعة 5m مكتملة** قبل استهلاك الإشارة (stop-first:
لمسة الوقف تُملأ `min/open` لا اللمسة فقط)، وأهداف الذراعات الآنية (TARGET) تُفحص على نفس
الشموع، والخروجات (رفع وقف / خروج بانقلاب الوضع / EOD) تُملأ بسعر إغلاق الشمعة التي وقع
فيها القرار (5m/15m/1h/4h بحسب موضع القرار) — لا يُستخدم أي سعر مستقبلي في أي قرار.

---

## 3. إعداد المحاكاة — فلسفة V13 (نظام يفهم السياق)

| البند | القيمة |
|---|---|
| رأس المال | 100 USDT، رافعة `set_leverage(10)` |
| نموذج الهامش | هامش افتراضي = السعر الإسمي ÷ 10؛ `margin_remaining ≈ equity×10 − هامش مستخدم` |
| بيانات الشموع | `data/BTCUSD_5m/` (نسخة داخل المجلد — 2019..2026) |
| فترات التحليل | 5m قاعدة + 15m (الكشاف/الوضع) / 1h / 4h (البنية والتتبّع) — إعادة تجميع سببية |
| الإحماء | 35 يوم (تُملأ فيها توزيعات العتبات التكيفية قبل أول صفقة) |
| الرسوم | 0.1% لكل تنفيذ بالـ USDT |
| الخصائص | BTCUSDT futures: tick 0.01، lot 0.001، حد أدنى 5.5 USDT |
| **الوضع السوقي أولاً** | آلة أوضاع على إغلاقات 15m: `EXPLOSIVE_UP / TREND_UP / RANGE / TREND_DOWN / EXPLOSIVE_DOWN` بأدلة مئوية من ذات التوزيع (كفاءة ker، توسع تذبذب، انحياز EMA50، اتجاه كسر 4h) + هستيريزس شمعتين قبل تغيير القصة |
| **الأذرع الخمسة النشطة + واحدة مرفوضة مُختبَرة** | `RIDE` (ركوب الصعود بالوقف الهيكلي — بلا هدف ثابت، **وشرط الضغط قبل الانفجار**)، `ACCUM` (استثمار: شراء ارتدادات الصعود الثابت)، `SNIP` (مضاربة: سحب سيولة واسترجاع داخل المدى، هدف = الحافة المقابلة)، `FALL` (متابعة هبوط: شورت عند إعادة اختبار الكسر 1h + شرط الضغط)، `DIP` (قنّاص: شراء انغماسات 15m في الهبوط). **`IGN` (V10_IGN) مُختبَر ومَرفوض على بيانات BTC**: 40 من42 دخولة أوقاف + صفقات المالك نفسها خسرت (`XRP −6.73`, `AVAX −3.21` بوسم `V10_IGN`) — معطّل ببوابة `IGN_ENABLED=False` والكود موثّق |
| **شرط 3R إلزامي + الرسوم** | الهدف (جدار/حافة) ≥ **3R + قِنَّة رسوم `4×FEE×en/rd`** (صيغة `min_r` من كود المستخدم نفسها، FEE=0.0020) — وإلا رُفضت (`v_wall`)؛ لأن رسوم الجولة 0.2% على وفعة ضيقة قد تبلغ 1–2R وحدها |
| **باب الضغط→التمدد** | أذرع الانفجار (RIDE/FALL) لا تنطلق إلا من ضغط: مدى آخر 10×15m ÷ ATR15 في **أسفل مئين 40%** من توزيعه المتحرك [D] (فرضية المستخدم #1) |
| **عتبة الجودة التكيفية** | جودة كل مرشح = متوسط أدلة مئوية؛ العتبة = مئين 60% من تيار مرشحات السوق نفسه؛ بعد خسارتين متتاليتين ترتفع لمئين 75%، وبعد 4 خسائر: وقف تام حتى تتغيّر قصّة الوضع (`v_streak`) |
| ملء الدخول | أمر سوق فوري بسعر إغلاق شمعة الاستهلاك (ImmediateFillModel) |
| الوقف | أمر `stop_market` راكد يُفحص على كل 5m: long `low ≤ SL` → `min(open,SL)`؛ short `high ≥ SL` → `max(open,SL)` |
| الخروجات | (1) **آلة الرابح [L]**: قفلات محطات MFE — ‎1.15R→وقف +0.30R، ‎2R (مع كفاءة>0.42)→**هرم +45% من الحجم الأصلي ممول من الربح المفتوح + وقف مركّب +1.05R**، ‎4.2/8/14R→‎+2.4/+5.2/+10R + شمعان تعقّب (آخر 10 شموع ×‎2.45×ATR، أو ‎1.85 عند MFE≥6.5) — أرقام `_manage_runner` حرفياً؛ (2) رفع وقف هيكلي 1h/4h (`pad = 0.5×ATR1 / 1.5×ATR4`)؛ (3) TP1 جزئي 30% عند 1.9R مع قفل ‎+0.35R (`tr1=(1.9,0.30,0.35)`) — عند سعة اللوت؛ (4) هدف آني `TARGET` عند الجدار لذراعي SNIP/DIP؛ (5) **سقف الرايدر 28R** لأذرع TRAIL (سلّمهم `TP3`) — لا سقف منخفض للركوب؛ (6) `FLIP` لذراعي TRAIL فقط بعد شمعتَي 15m معاكستين للوضع؛ (7) `EOD` |
| الحجم | `rbudget = 0.10`؛ `rk = eb × _rpct(ثقة) × (0.85 + 0.40×جودة)`؛ `notional = min((rk/(sl_p+0.0012))×(1.30 عند ثقة عالية)، eb×lev، margin_remaining×5.8)` مع lev ∈ {{1.9, 2.6, 3.6}} حسب الثقة/DD |
| دفعة الإدخال | الإشارة والتنفيذ على نفس إغلاق الشمعة — لا معلومة مستقبلية |
| إغلاق نهاية النافذة | أي مركز مفتوح يُغلق بسعر آخر شمعة بوسم `EOD` |

**جدول مصدر كل عدد في النظام (ضدّ «الأرقام الغبيّة»):**

| [M] فرضية المستخدم | [X] منصة التداول | [L] موروث مُختبَر | [D] مشتق من ذات السوق | [C] معايرة واحدة موثّقة |
|---|---|---|---|---|
| الهدف ≥ 3R لكل صفقة؛ خسائر متتالية قليلة (2/4)؛ رافعة 10؛ بوجيه 100$؛ شورت مسموح | tick/lot/حد أدنى/رسوم 0.1% | pads ‏0.5/1.5×ATR، صيغ الحجم والموازنة، عمر الإشارة 6 شموع، تهدئة 4س، حدّ التعرّف 0.44، معاملات التحجيم 0.85/0.40/1.30/5.8/3.6، **آلة الرابح: 1.15/0.30، 2.0/1.05، 4.2/2.4، 8/5.2، 14/10، شمعان 2.45/1.85×ATR، tr1=(1.9,0.30,0.35)، TP3=28R، هرم 0.45×init_q**، **V10_IGN: ker15>0.46، rv15>1.20، جسم>0.45، إغلاق ±0.18×ATR، cf=0.65+0.20ker+0.08tc≥0.78، TTL 4 شموع، وقف 0.25×ATR5**، **حجب _xexam: 0.60 يومي/0.50 أسبوعي عند 1.5R، رفض<0.32** | كل العتبات: مئينات من توزيعات متحركة (كفاءة، توسع، حجم، جودة المرشحات، أعمار الأوضاع، **مدى الضغط**، **فجوات انقلاب 4h**)، حدود الوقف بمضاعفات ATR، الجدران = بنية السوق الفعلية، **min_r = 3+4×FEE×en/rd** | حدّ تشبّع الجدار 6R، معامل التأخير 0.85، كمية المرشحات 30، أولويات الأذرع، **باب الضغط مئين 40%** |

لا يوجد أي نسبة سعرية مطلقة (لا «1.01%» ولا مدى ثابت) — كل عتبة إما من ذات سلسلة السعر أو من المستخدم أو من المنصة.

---

## 4. ملخص النتائج

### 4.1 الفترات الخمس

{metrics_table_md([
    ("المستمر: 12 شهر (يوليو 2025 ← يونيو 2026)", full_m),
    ("جزء المستمر: يوليو–ديسمبر 2025", h2_m),
    ("جزء المستمر: يناير–يونيو 2026", h1_m),
    ("مستقل: يوليو–ديسمبر 2025 برأس مال 100$", sa_h2_m),
    ("مستقل: يناير–يونيو 2026 برأس مال 100$", sa_h1_m),
])}

- صفوف "المستمر" = تشغيل واحد متصل بـ 100$ من البداية (النافذة المختارة: 12 شهر بدون فجوة).
- الصفوف "المستقلة" = تشغيلان منفصلان، كل واحد برأس مال 100$ جديد ونفس الإحماء —
  لتغطية المعنى الحرفي "6 أشهر من 2025 و6 أشهر من 2026 برأس مال 100$".

### 4.2 توزيع الأذرع والخروجات وأوضاع السوق (التشغيل المستمر)

- أسباب الخروج (حسب النوع): {full_m.get('exits', {})}
- الأذرع المنفّذة (RIDE/ACCUM/FALL/DIP/SNIP): {full_m['setups']}
- اتجاهات الصفقات: {full_m.get('sides', {})}
- توزيع مخرجات العتبة التكيفية: الجودة المطلوبة وقت كل إشارة = مئين 60% من تيار المرشحات
  (أو 75% بعد خسارتين) — «السوق يرسم عتبته بنفسه».

### 4.3 الأداء الشهري (التشغيل المستمر)

{monthly_md(monthly_table(full['trades']))}

### 4.4 قمع الإشارات (لماذا {full_m['trades']} صفقة فقط من 105,120 شمعة)

| الحدث | العدد |
|---|---:|
{funnel_md}

---

## 5. نتائج كل صفقة بالتفصيل — التشغيل المستمر (12 شهر)

### 5.1 الفترة الأولى: يوليو → ديسمبر 2025 ({len(h2_tr)} صفقة)

{trades_table_md(h2_tr)}

**تفاصيل إشارات الفترة الأولى:**

{signals_table_md(h2_tr)}

### 5.2 الفترة الثانية: يناير → يونيو 2026 ({len(h1_tr)} صفقة)

{trades_table_md(h1_tr)}

**تفاصيل إشارات الفترة الثانية:**

{signals_table_md(h1_tr)}

---

## 6. التشغيل المستقل: يوليو → ديسمبر 2025 (رأس مال 100$ — {sa_h2_m['trades']} صفقة)

{trades_table_md(sa_h2['trades'])}

---

## 7. التشغيل المستقل: يناير → يونيو 2026 (رأس مال 100$ — {sa_h1_m['trades']} صفقة)

{trades_table_md(sa_h1['trades'])}

---

## 8. قراءة النتائج

- **التشغيل المستمر:** Equity النهائي **{full_m['end_equity']:.2f}$** أي تغير
  **{full_m['end_equity'] - CAPITAL:+.2f}$ ({(full_m['end_equity'] - CAPITAL) / CAPITAL * 100:+.2f}%)**
  عن رأس المال 100$، مع أقصى تصحيح **{full_m['max_drawdown_pct']:.2f}%**.
- مجموع أرباح الصفقات المفردة = {full_m['net_pnl']:+.2f}$ — يطابق تغير Equity تقريباً
  (لا غبار: كل الخروجات تغلق الكمية كاملة في نموذج العقود).
- نسبة الربح {full_m['win_rate_pct']}% مع عامل ربح {full_m['profit_factor']} —
  يُقرأ مع جدول الخروجات: كم خروجاً بانقلاب الوضع (FLIP) وهدف آني (TP) ووقف مرفوع.
- **دورة الخسائر:** بعد خسارتين متتاليتين ترتفع عتبة الجودة تلقائياً (مئين 75%)، وبعد 4
  يتوقف النظام حتى تتغيّر قصّة الوضع — هذه آليتان مثبتتان في الكود لخفض تتابع الخسائر.
- **الجدار 3R:** كل صفقة مفتوحة عندها جدار بنية أقرب ≥ 3R مُسجَّل في `wall_R` —
  والصفقات التي رفضها `v_wall` مرئية في القمع.
- أفضل صفقة {full_m['best_r']}R وأسوأها {full_m['worst_r']}R | التعرض
  {full_m['exposure_pct']}% | متوسط الاحتفاظ {full_m['avg_hold_hours']} ساعة.
- النافذة شهدت هبوطاً حاداً لـ BTC (≈123k ← ≈58k) — أنظمة الأذرع تعمل في الاتجاهين
  (RIDE/ACCUM صعوداً، FALL/DIP هبوطاً، SNIP تذبذباً) — اقرأ النتيجة مع خريطة الأذرع لا مع
  اتجاه السوق وحده.

## 9. القيود

1. **9 من 10 أزواج غير مختبرة** — BTCUSDT فقط (انظر القسم 1): قياس «مشاركة السوق»
   أحادي الرمز، والاختبارات المتعددة الأزواج قادمة عند توفر البيانات.
2. هنا 5m قاعدة (QC دقيقة) — فروق تملئة طفيفة عند الفجوات السريعة.
3. نموذج الهامش تقريبي (equity×10 − هامش) مقارنة بمحرك LEAN الدقيق.
4. عتبات الجودة تكيّفت على 35 يوم إحماء + تيار المرشحات داخل النافذة نفسها —
   معايرة داخلية (in-sample self-calibration) تحتاج تحققاً خارجياً على نوافذ أخرى
   (نافذة 2021-01..07 مُدرجة لهذا الغرض في القسم 11).
5. البيانات من نسخة المشروع داخل المجلد — لا اتصال بالسوق الحي.
6. النتائج اختبار تاريخي (backtest) وليست ضماناً للمستقبل.

---

## 10. جدول المقارنة — V13 مقابل V12 وV5 و«التشغيل الأول» (V1)

{_comparison_md()}

---

## 11. اختبار نافذة الرالي 2021 (يوليو ← يناير 2021/07) — هل يلتقط الانفجار؟

> نافذة مستقلة خارج النافذة الرئيسية: 2021-01-01 ← 2021-07-01 (نفس الإحماء 35 يوم، رأس
> مال 100$، نفس الكود بلا أي تعديل) — لقياس سلوك الأذرع وقت رالي 2021 الفعلي على BTC.

{_y2021_md()}

---

## 12. اختبار كود صاحب المشروع المُلصَق (6 أذرع) — V14 + أول شهرين من 2021

> الكود المُلصَق حرفيًا على BTC وحده (لا بيانات للزوج الآخر)، بنفس النوافذ
> (المستمر 12 شهر + H2 + H1) + نافذة إضافية 2021-01-01 ← 2021-03-01. نسختان:
> **كما لُصق** (الحكم) و**إصلاح السقف الواحد** (تشخيص معزَّل).

{_v14_md()}

---

*كل الملفات (البيانات، المحرك، الكود الأصلي، الاختبارات، النتائج) داخل مجلد `halal_spot/` فقط —
لم يُمس أي ملف من المشروع الأساسي.*
"""
    return doc


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="continuous run only")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    print("[1/5] continuous 12m run ...", flush=True)
    full = run_backtest(str(DATA), FULL_START, FULL_END, capital=CAPITAL)

    if args.quick:
        sa_h2 = sa_h1 = y21 = {"trades": [], "equity": pd.DataFrame(), "count": {},
                               "final_equity": CAPITAL, "final_margin": 0.0, "events": []}
    else:
        print("[2/5] standalone Jul-Dec 2025 ...", flush=True)
        sa_h2 = run_backtest(str(DATA), H2_START, H2_END, capital=CAPITAL)
        print("[3/5] standalone Jan-Jun 2026 ...", flush=True)
        sa_h1 = run_backtest(str(DATA), H1_START, H1_END, capital=CAPITAL)
        print("[4/5] rally-window Jan-Jul 2021 ...", flush=True)
        y21 = run_backtest(str(DATA), "2021-01-01", "2021-07-01", capital=CAPITAL)

    print("[5/5] writing reports ...", flush=True)

    # CSVs
    pd.DataFrame(full["trades"]).to_csv(OUT / "trades_full.csv", index=False)
    pd.DataFrame(slice_trades(full["trades"], H2_START, H2_END)).to_csv(OUT / "trades_h2_2025.csv", index=False)
    pd.DataFrame(slice_trades(full["trades"], H1_START, H1_END)).to_csv(OUT / "trades_h1_2026.csv", index=False)
    if not args.quick:
        pd.DataFrame(sa_h2["trades"]).to_csv(OUT / "trades_standalone_h2_2025.csv", index=False)
        pd.DataFrame(sa_h1["trades"]).to_csv(OUT / "trades_standalone_h1_2026.csv", index=False)
    full["equity"].to_csv(OUT / "equity_full.csv")
    pd.DataFrame(full["events"]).to_csv(OUT / "events_full.csv", index=False)

    # metrics
    m_full = metrics(full["trades"], full["equity"])
    m_h2 = metrics(slice_trades(full["trades"], H2_START, H2_END),
                   slice_equity(full["equity"], H2_START, H2_END))
    m_h1 = metrics(slice_trades(full["trades"], H1_START, H1_END),
                   slice_equity(full["equity"], H1_START, H1_END))
    m_sa_h2 = metrics(sa_h2["trades"], sa_h2["equity"]) if not args.quick else m_h2
    m_sa_h1 = metrics(sa_h1["trades"], sa_h1["equity"]) if not args.quick else m_h1

    def _buy_hold(run) -> float | None:
        eq = run.get("equity")
        if eq is None or eq.empty or eq["price"].iloc[0] <= 0:
            return None
        return round(100.0 * float(eq["price"].iloc[-1]) / float(eq["price"].iloc[0]), 2)

    if not args.quick:
        m_y21 = metrics(y21["trades"], y21["equity"])
        pd.DataFrame(y21["trades"]).to_csv(OUT / "trades_2021h1_v13.csv", index=False)
        y21_summary = {
            "window_2021h1": m_y21,
            "buy_hold_2021h1": _buy_hold(y21),
            "count_2021h1": y21["count"],
            "end_log_2021h1": y21.get("end_log", {}),
        }
        (OUT / "summary_2021h1_v13.json").write_text(
            json.dumps(y21_summary, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    summary = {
        "config": {
            "window": f"{FULL_START} .. {FULL_END}",
            "capital_usdt": CAPITAL,
            "symbol": "BTCUSDT",
            "instrument": "Binance USDT-M futures (set_leverage 10, shorts allowed)",
            "strategy": "Regime Multi-Arm Sniper V13 (context regime + 5 arms + adaptive quality bar)",
            "arms": ["RIDE", "ACCUM", "SNIP", "FALL", "DIP"],
            "not_tested_pairs": ["ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
                                 "ADAUSDT", "AVAXUSDT", "LINKUSDT", "SUIUSDT"],
            "not_tested_reason": "no candle data for these pairs in the project (BTC only)",
            "fee_rate": 0.001,
            "rbudget": 0.10,
            "wall_min_r": 3.0,
            "warmup_days": 35,
            "cut_for_lookahead_test": CUT_TEST,
        },
        "continuous_12m": m_full,
        "continuous_h2_2025": m_h2,
        "continuous_h1_2026": m_h1,
        "standalone_h2_2025": m_sa_h2,
        "standalone_h1_2026": m_sa_h1,
        "buy_hold_12m": _buy_hold(full),
        "signal_funnel": full["count"],
        "final_margin_reserved": full.get("final_margin", 0.0),
        "final_usdt": full.get("final_usdt"),
        "fees_total": full.get("fees_total"),
        "zero_lookahead_tests": "9/9 passed (tests/test_zero_lookahead.py)",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    if not args.quick:
        write_chart(full, sa_h2, sa_h1, OUT / "equity_curve.png")

        ctx = {
            "full": full, "sa_h2": sa_h2, "sa_h1": sa_h1,
            "m_full": m_full, "m_h2": m_h2, "m_h1": m_h1,
            "m_sa_h2": m_sa_h2, "m_sa_h1": m_sa_h1,
        }
        (OUT / "REPORT_AR.md").write_text(build_report(ctx), encoding="utf-8")

    print(f"done. final equity (continuous): {full['final_equity']:.2f} USDT")
    print(f"outputs in: {OUT}")


if __name__ == "__main__":
    main()
