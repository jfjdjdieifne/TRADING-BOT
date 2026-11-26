"""Zero-lookahead (no future information) tests for the halal_spot backtest.

Two layers of proof, same philosophy as smc_v4_multisleeve_package/tests/test_v4_zero_lookahead.py
(copied into reference/ for provenance):

1. Causal resampling: every completed HTF bar must be reproducible from a data prefix —
   truncating the raw candles at a cut can never change bars that closed before the cut.
2. Full backtest prefix-invariance: running the strategy on data truncated at `CUT` must
   produce *bit-for-bit* the same closed trades as the full run for everything that closed
   on or before CUT, and the same entry setup for the position that was still open at CUT.
   The equity curve up to CUT must be identical as well.

If any signal, fill, stop or sizing decision peeked at future data, these tests fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf  # noqa: E402
from strategy import run_backtest  # noqa: E402

DATA_DIR = ROOT / "data" / "BTCUSD_5m"
START = "2025-07-01"
FULL_END = "2026-07-01"
CUT = "2026-03-31 14:30"          # 15m-aligned cut inside the window
CAPITAL = 100.0

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
# 1. causal resampling on real candles
# ---------------------------------------------------------------------------
def test_resample_prefix_invariant():
    cut_ts = pd.Timestamp(CUT, tz="UTC")
    df = load_asset_ohlcv(DATA_DIR, include_stems=["2026"])
    window = df.loc[pd.Timestamp("2026-01-01", tz="UTC"): pd.Timestamp("2026-04-05", tz="UTC")]

    # raw prefix: every 5m bar that CLOSED at or before the cut
    prefix = window.loc[: cut_ts - pd.Timedelta(minutes=5)]
    assert prefix.index.max() < cut_ts

    for freq in ("15min", "1h", "4h"):
        full_bars = resample_causal_tf(window, freq)
        pre_bars = resample_causal_tf(prefix, freq)

        # (a) every HTF bar completed before/on the cut is identical from the prefix
        completed_full = full_bars.loc[:cut_ts]
        completed_pre = pre_bars.loc[:cut_ts]
        assert len(completed_pre) == len(completed_full), freq
        pd.testing.assert_frame_equal(completed_pre, completed_full)

        # (b) end-time labelling: consecutive bins differ by exactly the timeframe
        deltas = completed_full.index.to_series().diff().dropna().unique()
        assert len(deltas) == 1 and deltas[0] == pd.Timedelta(freq), freq
        assert (completed_full.index == completed_full.index.round("min")).all()


# ---------------------------------------------------------------------------
# 2. full backtest prefix-invariance (module-scoped: each run executes once)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def full_run():
    return run_backtest(str(DATA_DIR), START, FULL_END, capital=CAPITAL)


@pytest.fixture(scope="module")
def cut_run():
    return run_backtest(str(DATA_DIR), START, CUT, capital=CAPITAL)


def test_closed_trades_identical_before_cut(full_run, cut_run):
    cut_ts = pd.Timestamp(CUT, tz="UTC")
    g1_full = [t for t in full_run["trades"] if t["exit_time"] <= cut_ts]
    g1_cut = [t for t in cut_run["trades"] if t["exit_tag"] != "EOD"]
    assert len(g1_full) >= 10, "window should contain a meaningful number of trades"
    assert g1_cut == g1_full, (
        "closed trades before the cut differ between truncated and full run — "
        "lookahead detected"
    )


def test_open_trade_at_cut_has_identical_setup(full_run, cut_run):
    cut_ts = pd.Timestamp(CUT, tz="UTC")
    g2_full = [t for t in full_run["trades"] if t["entry_time"] <= cut_ts < t["exit_time"]]
    g2_cut = [t for t in cut_run["trades"] if t["exit_tag"] == "EOD"]
    assert len(g2_cut) == len(g2_full) <= 3, (
        f"open-at-cut mismatch: full={len(g2_full)} cut={len(g2_cut)}"
    )
    for a, b in zip(g2_cut, g2_full):
        for k in ENTRY_KEYS:
            assert a.get(k) == b.get(k), f"entry-setup key {k!r} diverged at cut"


def test_equity_curve_identical_before_cut(full_run, cut_run):
    cut_ts = pd.Timestamp(CUT, tz="UTC")
    eq_full = full_run["equity"].loc[:cut_ts]
    eq_cut = cut_run["equity"]
    assert len(eq_cut) > 1000
    pd.testing.assert_frame_equal(eq_cut, eq_full)


def test_no_orders_or_trades_after_end_without_data(full_run, cut_run):
    # the truncated run must not invent anything past its own end
    cut_ts = pd.Timestamp(CUT, tz="UTC")
    assert all(t["exit_time"] <= cut_ts for t in cut_run["trades"])
    assert cut_run["equity"].index.max() <= cut_ts


# ---------------------------------------------------------------------------
# 3. causality invariants inside the full run
# ---------------------------------------------------------------------------
def _tz(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tzinfo is None else t


@pytest.fixture(scope="module")
def standalone_h2():
    """Independent $100 run over Jul-Dec 2025 (same start & warmup as the continuous run)."""
    return run_backtest(str(DATA_DIR), "2025-07-01", "2026-01-01", capital=CAPITAL)


def test_first_half_equals_standalone(full_run, standalone_h2):
    """Determinism cross-check: identical start + warmup + data => bit-identical first half.

    The continuous run's first six months must match the standalone Jul-Dec 2025 run
    exactly (same trades closed before 2026-01-01, same equity rows).
    """
    split = _tz("2026-01-01")
    cont_closed = [t for t in full_run["trades"] if _tz(t["exit_time"]) <= split]
    sa_closed = [t for t in standalone_h2["trades"] if t["exit_tag"] != "EOD"]
    assert len(cont_closed) >= 10
    assert cont_closed == sa_closed

    eq_sa = standalone_h2["equity"]
    eq_cont = full_run["equity"].loc[: eq_sa.index.max()]
    pd.testing.assert_frame_equal(eq_sa, eq_cont)


def test_trade_timing_is_causal(full_run):
    for t in full_run["trades"]:
        # market fill at the signal bar's own close: fill time == signal bar end (no future data)
        assert t["signal_time"] <= t["entry_time"] <= t["exit_time"], t["trade_id"]
        # non-EOD exits happen on a later bar (stop/TP/EOD-flatten is never before entry)
        if t["exit_tag"] != "EOD":
            assert t["entry_time"] < t["exit_time"], t["trade_id"]
        if t.get("tp1_time") is not None:
            # resting TP1 fills strictly after placement (never on the signal bar itself)
            assert t["entry_time"] < t["tp1_time"] <= t["exit_time"], t["trade_id"]
        if t["risk_usd"]:
            assert t["risk_usd"] > 0


def test_accounting_ties_to_equity(full_run):
    """Σ per-trade PnL must explain the equity change up to dust re-valuation noise."""
    trades = full_run["trades"]
    assert len(trades) > 0
    sum_pnl = sum(t["net_pnl"] for t in trades)
    eq_change = full_run["final_equity"] - CAPITAL
    # gap = wallet dust re-valued at the final price vs at its trade's exit + entry mark noise
    assert abs(sum_pnl - eq_change) < 1.5, f"sum_pnl={sum_pnl:.2f} eq_change={eq_change:.2f}"


def test_no_negative_cash_or_qty(full_run):
    # equity must stay positive and every trade funded
    eq = full_run["equity"]["equity"]
    assert eq.min() > 0
    for t in full_run["trades"]:
        assert t["entry_qty"] > 0 and t["entry_notional"] >= 5.5
