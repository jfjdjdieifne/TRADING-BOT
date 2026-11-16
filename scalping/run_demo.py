#!/usr/bin/env python3
"""LAUNCH (offline): multi-coin session scalping bot on rolling local data.

This is the launchable version of the system that needs no API keys and no
network: it runs the SAME MultiSymbolBot loop (all symbols, sessions, confluence,
risk brakes, tick-free bar management) over rolling windows of the repository's
BTC 5m data transformed into stand-in symbols. It is clearly a SIMULATION —
not real coins and not a live Binance connection.

For the real paper/live bot run:
    python3 -m live.live_bot --mode paper --scan --top 8 --testnet

    python3 run_demo.py --symbols 4 --cycle-sec 60
"""

from __future__ import annotations

import argparse
import time

from scalping_engine import data
from scalping_engine.engine import EngineConfig
from live.multi_bot import MultiSymbolBot, synthetic_frames

SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=int, default=4)
    ap.add_argument("--cycle-sec", type=int, default=60)
    ap.add_argument("--bars", type=int, default=400)
    ap.add_argument("--min-confluence", type=float, default=0.5)
    a = ap.parse_args()

    syms = SYMS[:a.symbols]
    cfg = EngineConfig(entry_mode="orb", rr=1.5, sl_atr_mult=1.0, sl_min_atr=1.0,
                       max_holding_bars=24, use_breakeven=False,
                       entry_fee_pct=0.0002, exit_fee_pct=0.0005,
                       slippage_pct=0.0002, min_confluence=a.min_confluence)
    df = data.load_btc_5m([2025, 2026])
    frames = synthetic_frames(df, syms)
    total = len(frames[syms[0]])
    usable = total - a.bars - 301

    print("=" * 78)
    print("SCALPING BOT — OFFLINE MULTI-COIN LAUNCH (simulation, no keys/network)")
    print(f"symbols={syms}  window=300 bars  cycle={a.bars} bars  "
          f"mode=orb  min_confluence={a.min_confluence}")
    print("=" * 78, flush=True)

    cycle = 0
    while True:
        bot = MultiSymbolBot(cfg, symbols=syms, paper_only=True, testnet=True,
                             window=300)
        start = 301 + (cycle * a.bars) % max(1, usable)
        sliced = {s: f.iloc[start:start + 301 + a.bars] for s, f in frames.items()}
        s = bot.replay(sliced, bars=a.bars, verbose=False)
        print(f"[cycle {cycle:03d}] window={sliced[syms[0]].index[0]}.."
              f"{sliced[syms[0]].index[-1]}  bars={s['bars']}  "
              f"signals={s['signals']}  trades={s['trades']}  "
              f"WR={s['wr_pct']}%  net=${s['net_usd']}  equity=${s['equity']}",
              flush=True)
        cycle += 1
        time.sleep(a.cycle_sec)


if __name__ == "__main__":
    main()
