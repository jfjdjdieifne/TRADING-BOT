#!/usr/bin/env python3
"""Multi-coin Binance scanner — find the coins that currently satisfy the
"golden trade" conditions.

It does NOT invent signals. It ranks coins by objective, causal features:
  * volatility (ATR% — is there room to move?),
  * session (is it a strong session open?),
  * confluence score of the latest closed 5m bar (see confluence.py),
  * distance from the session mean (is it extended?),
  * 24h volume (is it tradeable?).

Then the live bot trades the top-ranked symbols. Everything is causal: only the
last *closed* 5m bar is used.

    python3 scanner.py --top 10
    python3 scanner.py --top 10 --min-volume 50      # million USDT / 24h
    python3 scanner.py --watch --interval-sec 300    # re-scan every 5 min
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scalping_engine.engine import EngineConfig, attach_indicators  # noqa: E402
from scalping_engine.sessions import session_name, SESSIONS  # noqa: E402

FAPI = "https://fapi.binance.com"
API = "https://api.binance.com"


def _get(url: str, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "scalping-scanner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def list_futures(min_volume_usdt: float = 20e6):
    data = _get(f"{FAPI}/fapi/v1/ticker/24hr")
    out = []
    for d in data:
        sym = d.get("symbol", "")
        if not sym.endswith("USDT"):
            continue
        try:
            qv = float(d.get("quoteVolume", 0))
            price = float(d.get("lastPrice", 0))
        except (TypeError, ValueError):
            continue
        if qv < min_volume_usdt or price <= 0:
            continue
        out.append({"symbol": sym, "price": price, "quote_volume": qv,
                    "change_pct": float(d.get("priceChangePercent", 0))})
    out.sort(key=lambda x: x["quote_volume"], reverse=True)
    return out


def klines(symbol: str, interval: str = "5m", limit: int = 300):
    data = _get(f"{FAPI}/fapi/v1/klines?symbol={symbol}&interval={interval}"
                f"&limit={limit}")
    rows = []
    for k in data:
        rows.append({
            "Datetime": pd.Timestamp(k[0], unit="ms", tz="UTC"),
            "Open": float(k[1]), "High": float(k[2]), "Low": float(k[3]),
            "Close": float(k[4]), "Volume": float(k[5]),
        })
    return pd.DataFrame(rows).set_index("Datetime")


def score_symbol(df: pd.DataFrame):
    if len(df) < 60:
        return None
    cfg = EngineConfig()
    ind = attach_indicators(df, cfg)
    t = len(df) - 1
    atr = ind["atr"][t]
    price = float(df["Close"].iloc[-1])
    if np.isnan(atr) or atr <= 0 or price <= 0:
        return None
    atr_pct = atr / price
    conf = float(ind["confluence"][t])
    htf = int(ind["htf_trend"][t])
    sess = session_name(df.index[-1])
    sess_strength = next((s.strength for s in SESSIONS.values() if s.name == sess), 0.2)
    # session mean (equal-weight typical) deviation
    typical = (df["High"] + df["Low"] + df["Close"]) / 3.0
    day = df.index[-1].date()
    today = typical[df.index.date == day]
    dev = float((price - today.iloc[-1]) / atr) if len(today) else 0.0
    # recent momentum: 12-bar return
    mom = float(df["Close"].iloc[-1] / df["Close"].iloc[-13] - 1.0) if len(df) >= 13 else 0.0
    # composite scalp quality: volatility room * session * confluence
    quality = (min(atr_pct / 0.004, 2.0) * 0.5 + conf * 0.35 + sess_strength * 0.15)
    return {
        "atr_pct": atr_pct, "confluence": conf, "htf": htf, "session": sess,
        "dev_atr": dev, "mom_12": mom, "quality": quality,
    }


def scan(top: int = 10, min_volume: float = 20e6):
    cands = list_futures(min_volume)
    rows = []
    for c in cands[:80]:
        try:
            df = klines(c["symbol"])
            s = score_symbol(df)
        except Exception:
            continue
        if s is None:
            continue
        rows.append({**c, **s})
    rows.sort(key=lambda r: r["quality"], reverse=True)
    return rows


def offline_scan():
    """Offline demo: score the three datasets already in this repository as
    stand-in symbols. Clearly NOT the live market — lets you verify the scanner
    without network access."""
    from scalping_engine import data
    sources = []
    for name, loader, arg in (("BTCUSD", data.load_btc_5m, [2026]),
                              ("XAUUSD", data.load_xau_1m, ["2026-10"]),
                              ("NSXUSD", data.load_nsx_1m, ["2026-10"])):
        try:
            sources.append((name, loader(arg).tail(300)))
        except Exception:  # noqa: BLE001
            continue
    rows = []
    for name, df in sources:
        s = score_symbol(df)
        if s is None:
            continue
        rows.append({"symbol": name, "price": float(df["Close"].iloc[-1]),
                     "quote_volume": 0.0, "change_pct": 0.0, **s})
    rows.sort(key=lambda r: r["quality"], reverse=True)
    return rows


def print_table(rows, top):
    print("=" * 104)
    print(f"{'symbol':12} {'price':>12} {'vol24M':>8} {'ATR%':>6} {'conf':>5} "
          f"{'htf':>4} {'sess':>8} {'devATR':>7} {'mom12%':>7} {'quality':>7}")
    print("-" * 104)
    for r in rows[:top]:
        print(f"{r['symbol']:12} {r['price']:>12.4f} {r['quote_volume']/1e6:>8.0f} "
              f"{r['atr_pct']*100:>6.2f} {r['confluence']:>5.2f} {r['htf']:>4} "
              f"{r['session']:>8} {r['dev_atr']:>7.2f} {r['mom_12']*100:>7.2f} "
              f"{r['quality']:>7.2f}")
    print("=" * 104)
    print("Ranked by scalp quality (volatility room x confluence x session).")
    print("This is a candidate filter, NOT a signal. Trade only if the strategy")
    print("engine confirms the setup on the closed bar.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-volume", type=float, default=20.0,
                    help="minimum 24h quote volume in millions USDT")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval-sec", type=int, default=300)
    ap.add_argument("--offline", action="store_true",
                    help="demo: score local repository datasets, no network")
    a = ap.parse_args()
    if a.offline:
        print("[OFFLINE DEMO] local repository data as stand-in symbols "
              "(NOT the live Binance market)")
        print_table(offline_scan(), a.top)
        return
    while True:
        try:
            rows = scan(a.top, a.min_volume * 1e6)
            print_table(rows, a.top)
        except Exception as e:  # noqa: BLE001
            print(f"[scanner] error: {e}", file=sys.stderr)
        if not a.watch:
            break
        time.sleep(a.interval_sec)


if __name__ == "__main__":
    main()
