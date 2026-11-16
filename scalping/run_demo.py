#!/usr/bin/env python3
"""LAUNCH: the MOMENTUM-X strategy, scanning ALL coins, running continuously.

What runs here is the SAME loop as the live Binance bot (`live/multi_bot.py`),
but offline: no API keys, no network, no money at all. Coins are clearly
labelled stand-in price paths derived from the repository's real BTC 5m data
(they are NOT real coins) so the whole multi-symbol pipeline can be exercised
and verified without an exchange connection.

Each cycle takes a different window across 2019-2026 so you see both risk-on
windows (trades fire) and risk-off windows (the BTC regime gate keeps us flat).

    python3 run_demo.py                       # continuous launch (default)
    python3 run_demo.py --symbols 4 --bars 300 --cycle-sec 30

For REAL free paper trading on Binance public market data (no deposit, see STRATEGY.md):
    python3 -m live.live_bot --mode paper --scan --top 8 --entry-mode momentum --market futures
"""

from __future__ import annotations

import argparse
import time

from scalping_engine import data
from scalping_engine.engine import EngineConfig
from live.multi_bot import MultiSymbolBot, synthetic_frames

SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
HISTORY_BARS = 20000          # ~69 days of 5m history per cycle (for the 50d trend)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=int, default=3)
    ap.add_argument("--cycle-sec", type=int, default=30)
    ap.add_argument("--bars", type=int, default=300)
    ap.add_argument("--entry-mode", default="momentum")
    ap.add_argument("--min-confluence", type=float, default=0.4)
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    a = ap.parse_args()

    syms = SYMS[:a.symbols]
    cfg = EngineConfig(entry_mode=a.entry_mode, rr=2.0, sl_atr_mult=1.0,
                       sl_min_atr=1.0, max_holding_bars=24,
                       use_breakeven=False, min_confluence=a.min_confluence,
                       entry_fee_pct=0.0002, exit_fee_pct=0.0005,
                       slippage_pct=0.0002)
    df = data.load_btc_5m()
    need = HISTORY_BARS + a.bars + 1
    max_start = len(df) - need

    print("=" * 88)
    print("MOMENTUM-X  |  OFFLINE MULTI-COIN LAUNCH  (simulation — no keys, no network)")
    print(f"universe={syms}  strategy={a.entry_mode}  conditions=12  "
          f"session=London/NY  window={a.bars} bars/cycle")
    print("=" * 88, flush=True)

    cycle = 0
    while True:
        # sweep different regimes across 2019-2026, then wrap
        start = (cycle * a.bars * 7) % max(1, max_start)
        src = df.iloc[start:start + need]
        frames = synthetic_frames(src, syms, max_bars=HISTORY_BARS + a.bars)
        bot = MultiSymbolBot(cfg, symbols=syms, paper_only=True, testnet=True,
                             window=300)
        s = bot.replay(frames, bars=a.bars, verbose=False)
        regime = "ON" if (bot.btc_daily is not None and len(bot.btc_daily) > 51
                          and float(bot.btc_daily.iloc[-1]) >
                          float(bot.btc_daily.iloc[-51:-1].mean())) else "OFF"
        print(f"[cycle {cycle:03d}] {src.index[0].date()}..{src.index[-1].date()}  "
              f"BTC_regime={regime}  bars={s['bars']}  golden_signals={s['signals']}  "
              f"trades={s['trades']}  WR={s['wr_pct']}%  net=${s['net_usd']}  "
              f"equity=${s['equity']}", flush=True)
        cycle += 1
        if a.cycles and cycle >= a.cycles:
            break
        time.sleep(a.cycle_sec)


if __name__ == "__main__":
    main()
