#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_build_v37_data.py -- rebuild halal_spot/data/binance_5m from the 1m repos.

WHY
---
The 5m basket used by v32..v36 was never committed (it is in .gitignore, by
owner order: "code only is pushed").  The sandbox that produced v36 was reset,
so the archives are gone.  They are rebuilt here from the same GitHub 1m
repositories (_fetch_v37.sh), with the engine's OWN resampler
(engine.causal_primitives.resample_causal_tf) so the bars are byte-comparable
with what v36 measured.

The build is only trusted if it reproduces v36's committed trade tapes; that
check lives in _verify_v37_data.py, not here.

LAYOUT (exactly what strategy_v36_ict_champion expects)
    data/binance_5m/<SYM>_5m/YYYY-MM.csv.gz
    columns: Datetime,Open,High,Low,Close,Volume

Binance 1m CSV columns are:
    timestamp, datetime_utc, open, high, low, close, volume, ...
NOTE: the time column is `datetime_utc`, NOT `datetime`.
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine.causal_primitives import resample_causal_tf  # noqa: E402

K1 = Path("/home/user/k1m")
OUT = HERE / "data" / "binance_5m"
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
        "XRPUSDT", "AVAXUSDT", "LINKUSDT", "ADAUSDT"]


def load_1m_month(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    tcol = "datetime_utc" if "datetime_utc" in df.columns else "datetime"
    df["Datetime"] = pd.to_datetime(df[tcol], utc=True)
    for c in ("open", "high", "low", "close"):
        df[c.capitalize()] = df[c].astype(np.float64)
    df["Volume"] = df["volume"].astype(np.float64) if "volume" in df else 0.0
    df = (df[["Datetime", "Open", "High", "Low", "Close", "Volume"]]
          .sort_values("Datetime").drop_duplicates("Datetime", keep="first"))
    return df.set_index("Datetime")


END_LABEL = False   # True reproduces v36's *built* months (see LABEL LAW v36)


def to_5m(df1: pd.DataFrame) -> pd.DataFrame:
    """1m -> 5m with the engine's own causal resampler.

    resample_causal_tf returns OHLC + first/last_1m_pos, NOT Volume (this bit
    v36 twice: indexing ["Volume"] on it raises KeyError).  Volume is summed
    here from the 1m frame and re-attached, because the engine feeds Volume to
    its canvases (it never READS it -- proved in v36 by the _ab_vol A/B), so a
    real sum is both correct and free.
    """
    b = resample_causal_tf(df1, "5min")
    vol = df1["Volume"].resample("5min", label="left",
                                 closed="left").sum().reindex(b.index - pd.Timedelta("5min"))
    # ---- LABEL LAW v37 (the whole ballgame) ------------------------- #
    # PROVEN by the OLD7 discrepancy: v36's W1/W2 reproduce exactly with
    # START-labelled bars, but OLD7 does not ($106.64 in v36 vs $89.50
    # start-labelled). The v36 tape's LINK entry at "2023-01-03 17:00" and
    # price 5.6180 is the CLOSE of the 16:55..17:00 block, which the v36
    # data carried as its own 17:00 bar -> v36's months built by
    # _build_oos.py were END-labelled, while the fetch_binance_5m months
    # (2023-09..2024-10) were Binance-native and therefore START-labelled.
    # So the v36 OOS numbers (OLD7, MODERN's fetched months) sit on a
    # one-bar-shifted tape and are NOT comparable with the native months.
    # Default here = START (the only internally consistent choice);
    # --end-label reproduces the v36-built tape for a like-for-like check.
    # ---- BAR LABEL LAW (this is the whole ballgame) ------------------- #
    # resample_causal_tf returns bars indexed by their END time (00:05 for
    # the 00:00-00:05 minute block), because the ENGINE needs end-time
    # availability for causality.  Binance's own 5m archives -- and therefore
    # data/binance_5m, which v32..v36 measured -- label the same bar at its
    # START (00:00).  Writing end-labelled Datetime into the archive shifts
    # every 5m bar one stamp later, which silently breaks the 5m<->15m/1h/4h
    # alignment (measured: W1 n=159 $160.87 instead of n=181 $158.02).
    # The archive must therefore carry start_time; the engine re-derives
    # end-labelling itself.
    labels = (b.index.to_numpy() if END_LABEL      # v36's built months
              else b["start_time"].to_numpy())     # Binance native layout
    out = pd.DataFrame({
        "Datetime": labels,
        "Open": b["Open"].to_numpy(float),
        "High": b["High"].to_numpy(float),
        "Low": b["Low"].to_numpy(float),
        "Close": b["Close"].to_numpy(float),
        "Volume": np.nan_to_num(vol.to_numpy(float)),
    })
    return out


def write_month(df5: pd.DataFrame, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dest, "wt", newline="") as fh:
        df5.to_csv(fh, index=False)


def main() -> int:
    global END_LABEL
    if "--end-label" in sys.argv:
        END_LABEL = True
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    rows = []
    for sym in SYMS:
        if only and sym not in only:
            continue
        src = K1 / sym / "1m"
        if not src.exists():
            print(f"{sym}: NO 1m DATA at {src}", flush=True)
            continue
        files = sorted(src.glob("*/*/*.csv"))
        print(f"=== {sym}: {len(files)} months ===", flush=True)
        for f in files:
            ym = f"{f.parent.parent.name}-{f.parent.name}"     # YYYY/MM
            try:
                df5 = to_5m(load_1m_month(f))
            except Exception as exc:                          # noqa: BLE001
                print(f"  FAIL {sym} {ym}: {exc}", flush=True)
                continue
            if not len(df5):
                print(f"  EMPTY {sym} {ym}", flush=True)
                continue
            write_month(df5, OUT / f"{sym}_5m" / f"{ym}.csv.gz")
            rows.append({"sym": sym, "month": ym, "bars": len(df5),
                         "first": str(df5.Datetime.iloc[0]),
                         "last": str(df5.Datetime.iloc[-1]),
                         "zero_vol": int((df5.Volume <= 0).sum())})
        done = sum(1 for r in rows if r["sym"] == sym)
        print(f"    {sym}: wrote {done} months", flush=True)
    if rows:
        m = pd.DataFrame(rows)
        m.to_csv(HERE / "results" / "_build_v37_months.csv", index=False)
        print("\nTOTAL months:", len(m), " bars:", int(m.bars.sum()),
              " zero-volume bars:", int(m.zero_vol.sum()), flush=True)
        print(m.groupby("sym").bars.agg(["count", "sum"]).to_string(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
