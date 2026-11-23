#!/usr/bin/env python3
"""Build the project's 5m archives from Binance SPOT 1m monthly CSVs.

Why this exists
---------------
Step 1 of the v32 brief asks for monthly 5m ZIPs from
`https://data.binance.vision/data/spot/monthly/klines/<SYM>/5m/`. That host
is unreachable from this sandbox (measured: curl exit 000), and GitHub
*release assets* are blocked too (302 -> release-assets.githubusercontent.com,
0 bytes). `codeload.github.com` tarballs, `api.github.com` blobs and plain
`git clone` DO work, so the data is sourced from GitHub mirrors of the very
same Binance spot archives:

  * BTCUSDT / ETHUSDT 5m monthly ZIPs, committed verbatim by
    `jainlakshay22/volatility-forecasting` (its `download_data.py` reads
    `BINANCE_URL = "https://data.binance.vision/data/spot/monthly/klines"`,
    `TIME_INTERVAL = "5m"` -> SPOT, not futures). Converted by
    `fetch_binance_5m.py --from-zips`.
  * 1m monthly CSVs for all 8 symbols from
    `parshant231234-eng/<SYM>USDT-Historical-Data`, whose `fetch.py` pulls
    `data.binance.vision/data/spot/monthly/klines/<SYM>/1m/...zip` -> SPOT.
    Resampled here to 5m.

Provenance rule (halal spot, 1x cash-only): a futures/perp feed is
disqualified. `kipopopo/autonomous-futures-bot` was rejected for exactly
that reason (its manifest declares `source: https://fapi.binance.com`).

Correctness rule
----------------
A 5m bar is a pure function of its five 1m bars:
    Open  = first 1m open      High = max of 1m highs
    Low   = min of 1m lows     Close = last 1m close
    Volume = sum of 1m volumes
No interpolation, no filling, no invented rows. Months whose 1m coverage is
incomplete are reported, never silently patched.

`--validate` proves the resampler against ground truth: for BTCUSDT and
ETHUSDT we hold the *official* Binance 5m ZIPs, so the resampled 5m bars are
compared bar-by-bar with them.

Usage
-----
    python3 build_5m_from_1m.py --src /tmp/k1m --symbols BTCUSDT ETHUSDT \
        SOLUSDT BNBUSDT XRPUSDT AVAXUSDT LINKUSDT ADAUSDT --validate
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "binance_5m"
COLS = ["Datetime", "Open", "High", "Low", "Close", "Volume"]
# months needed: 2023-08 .. 2024-10 (60-day warmup before W1 = 2023-10-01)
MONTHS = [f"{y}-{m:02d}" for y in (2023, 2024) for m in range(1, 13)
          if "2023-08" <= f"{y}-{m:02d}" <= "2024-10"]


def read_1m(src: Path, sym: str, month: str) -> pd.DataFrame | None:
    y, m = month.split("-")
    f = src / sym / "1m" / y / m / f"{sym}_1m_{month}.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    if "datetime_utc" not in df.columns:          # some mirrors name it differently
        cand = [c for c in df.columns if "time" in c.lower() and c != "timestamp"]
        if not cand:
            raise SystemExit(f"{f}: no datetime column in {list(df.columns)}")
        df = df.rename(columns={cand[0]: "datetime_utc"})
    df["Datetime"] = pd.to_datetime(df["datetime_utc"], utc=True).dt.tz_localize(None)
    out = df[["Datetime"]].copy()
    for src_col, dst in (("open", "Open"), ("high", "High"), ("low", "Low"),
                         ("close", "Close"), ("volume", "Volume")):
        if src_col not in df.columns:
            raise SystemExit(f"{f}: missing column {src_col}")
        out[dst] = df[src_col].astype(np.float64)
    return out.sort_values("Datetime").drop_duplicates("Datetime").reset_index(drop=True)


def to_5m(df1: pd.DataFrame) -> pd.DataFrame:
    """Exact 5m aggregation of 1m bars (label=left, closed=left -> bar OPEN time)."""
    g = df1.set_index("Datetime").resample("5min", label="left", closed="left")
    out = g.agg(Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"),
                Close=("Close", "last"), Volume=("Volume", "sum"),
                _n=("Open", "size")).dropna(subset=["Open", "High", "Low", "Close"])
    return out


def write_csv_gz(df5: pd.DataFrame, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    d = df5.reset_index()[COLS].copy()
    d["Datetime"] = d["Datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    with gzip.open(dest, "wt", newline="") as g:
        g.write(",".join(COLS) + "\n")
        for row in d.itertuples(index=False):
            g.write("%s,%.8f,%.8f,%.8f,%.8f,%.8f\n" % row)


def validate(sym: str, month: str, built: pd.DataFrame) -> dict:
    """Compare resampled 5m against the OFFICIAL Binance 5m archive, if held."""
    ref_path = OUT / f"{sym}_5m" / f"{month}.csv.gz.ref"
    alt = OUT / f"{sym}_5m" / f"{month}.csv.gz"
    if not ref_path.exists():
        return {"symbol": sym, "month": month, "reference": None}
    ref = pd.read_csv(ref_path, parse_dates=["Datetime"], compression="gzip")
    a, b = ref.set_index("Datetime"), built[COLS[1:]]
    both = a.index.intersection(b.index)
    res = {"symbol": sym, "month": month, "reference": str(ref_path.name),
           "ref_rows": len(a), "built_rows": len(b), "common_rows": len(both),
           "only_in_ref": int(len(a.index.difference(b.index))),
           "only_in_built": int(len(b.index.difference(a.index)))}
    if len(both):
        for c in ("Open", "High", "Low", "Close", "Volume"):
            diff = (a.loc[both, c].astype(float) - b.loc[both, c].astype(float)).abs()
            res[f"max_abs_{c}"] = float(diff.max())
            res[f"exact_{c}"] = int((diff == 0).sum())
        px = max(res["max_abs_Open"], res["max_abs_High"], res["max_abs_Low"],
                 res["max_abs_Close"])
        res["OHLC_exact"] = bool(px == 0.0)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="dir holding <SYM>/1m/<Y>/<M>/*.csv")
    ap.add_argument("--symbols", nargs="+", required=True)
    ap.add_argument("--months", nargs="*", default=MONTHS)
    ap.add_argument("--validate", action="store_true",
                    help="compare against official 5m archives (*.csv.gz.ref)")
    args = ap.parse_args()

    src = Path(args.src)
    report, missing = [], []
    for sym in args.symbols:
        d = OUT / f"{sym}_5m"
        for month in args.months:
            df1 = read_1m(src, sym, month)
            if df1 is None:
                missing.append(f"{sym} {month}")
                continue
            df5 = to_5m(df1)
            short = df5[df5["_n"] < 5]
            dest = d / f"{month}.csv.gz"
            write_csv_gz(df5, dest)
            row = {"symbol": sym, "month": month, "rows_1m": int(len(df1)),
                   "rows_5m": int(len(df5)),
                   "partial_5m_bars": int(len(short)),
                   "span": f"{df5.index[0]}..{df5.index[-1]}"}
            if args.validate:
                row.update(validate(sym, month, df5))
            report.append(row)
            print(f"  + {sym} {month}: {len(df1)} 1m -> {len(df5)} 5m "
                  f"({len(short)} partial)")

    (OUT / "BUILD_5M_REPORT.json").write_text(json.dumps(
        {"months": args.months, "missing": missing, "rows": report}, indent=1))
    print(f"\nwrote {len(report)} archives -> {OUT}")
    if missing:
        print(f"MISSING {len(missing)}: {' '.join(missing)}")

    if args.validate:
        checked = [r for r in report if r.get("reference")]
        if not checked:
            print("no official 5m references found (*.csv.gz.ref) - nothing to prove")
        else:
            bad_ohlc = [r for r in checked if not r.get("OHLC_exact", False)]
            tot = sum(r["common_rows"] for r in checked)
            print(f"\nVALIDATION vs official Binance 5m archives: "
                  f"{len(checked)} months, {tot} common bars")
            for c in ("Open", "High", "Low", "Close"):
                mx = max(r[f"max_abs_{c}"] for r in checked)
                ex = sum(r[f"exact_{c}"] for r in checked)
                print(f"  {c:6s} max|diff| = {mx:.10f}   exact bars = {ex}/{tot}")
            vmax = max(r["max_abs_Volume"] for r in checked)
            print(f"  Volume max|diff| = {vmax:.10f} (float summation order)")
            print("  OHLC bit-exact in every month" if not bad_ohlc
                  else f"  !! MISMATCH in {[ (r['symbol'], r['month']) for r in bad_ohlc ]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
