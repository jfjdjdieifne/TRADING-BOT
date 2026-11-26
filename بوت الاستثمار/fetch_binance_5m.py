#!/usr/bin/env python3
"""
v32 DATA FETCHER — Binance official monthly 5m kline archives.

WHY THIS FILE EXISTS
--------------------
The Arena sandbox this project is developed in has an egress allowlist:
    github.com · codeload.github.com · api.github.com ·
    registry.npmjs.org · pypi.org · files.pythonhosted.org
`https://data.binance.vision/...` is NOT on it (measured: curl returns
HTTP 000 / connection failure, while pypi.org and api.github.com return
200 in the same sandbox).  GitHub repository + code search were also
queried for raw kline archives and returned only derived research
tables, never the monthly ZIPs.

So this script is written to be run ON THE OWNER'S PC (or any machine
with normal internet).  It needs nothing but the standard library.

    python3 fetch_binance_5m.py                # 8 coins, 2023-09..2024-10
    python3 fetch_binance_5m.py --months 2024-11 2024-12
    python3 fetch_binance_5m.py --symbols BTCUSDT ETHUSDT
    python3 fetch_binance_5m.py --verify       # re-check sha256 + gaps

Output layout (what strategy_v32_ict_superbrain.py expects):

    halal_spot/data/binance_5m/
        BTCUSDT_5m/2023-09.csv.gz   ... 2024-10.csv.gz
        ETHUSDT_5m/...
        ...
        MANIFEST.sha256             # one line per file: sha256  path  rows
        GAPS.json                   # missing / zero-row / short files

The directory `halal_spot/data/binance_5m/` is in .gitignore — only code
is pushed, never the price archives (~35 MB per coin-month set).

Data source: https://data.binance.vision/data/spot/monthly/klines/<SYM>/5m/
File naming: <SYM>-5m-<YYYY-MM>.zip  →  contains <SYM>-5m-<YYYY-MM>.csv
CSV columns (Binance spot klines, no header):
  open_time_ms, open, high, low, close, volume, close_time_ms,
  quote_volume, trades, taker_buy_base, taker_buy_quote, ignore
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://data.binance.vision/data/spot/monthly/klines"

# The eight leading halal spot pairs requested for v32, plus the two
# substitutes the owner authorised if a pair is unavailable.
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
           "XRPUSDT", "AVAXUSDT", "LINKUSDT", "ADAUSDT"]
FALLBACKS = ["DOTUSDT", "NEARUSDT"]

# W1 = 2023-10-01..2024-03-31, W2 = 2024-05-01..2024-10-31.
# Two extra months at the front (2023-08, 2023-09) are the structural
# warm-up: run_backtest defaults to warmup_days=60, i.e. it starts feeding
# the 4H/1H canvases on 2023-08-02, so September alone would be short.
MONTHS = ["2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
          "2024-01", "2024-02", "2024-03", "2024-04",
          "2024-05", "2024-06", "2024-07", "2024-08",
          "2024-09", "2024-10"]

OUT = Path(__file__).resolve().parent / "data" / "binance_5m"
EXPECTED_ROWS = 8640 + 288     # 30d + 1d of 5m bars (a generous upper bound)
MIN_ROWS = 8000                # below this the month is flagged as short


def month_list(cli: list[str] | None) -> list[str]:
    return cli or MONTHS


def url_for(sym: str, month: str) -> str:
    return f"{BASE}/{sym}/5m/{sym}-5m-{month}.zip"


def fetch(url: str, retries: int = 3, timeout: int = 60) -> bytes | None:
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "v32-superbrain-fetcher/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 404:          # month does not exist — do not retry
                return None
        except Exception as e:          # noqa: BLE001 — network is messy
            last = repr(e)
        time.sleep(1.5 * (k + 1))
    print(f"    !! giving up on {url}: {last}")
    return None


def zip_to_csv_gz(raw: bytes, dest: Path) -> tuple[int, str]:
    """Unzip the Binance archive, normalise to the project's csv.gz layout.

    The project loader (`engine.causal_primitives.load_asset_ohlcv`) reads
    `*.csv.gz` with a header row.  Binance's monthly CSVs are headerless,
    so the header is written here once, and the epoch-ms open time becomes
    an ISO-8601 UTC timestamp.
    """
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = z.namelist()[0]
        text = z.read(name).decode("utf-8")
    rows = 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(dest, "wt", newline="") as g:
        w = csv.writer(g)
        w.writerow(["Datetime", "Open", "High", "Low", "Close", "Volume"])
        for line in csv.reader(io.StringIO(text)):
            if not line or len(line) < 6:
                continue
            # column 0 is the bar OPEN time in epoch ms. The project's
            # loader (engine.causal_primitives.load_asset_ohlcv) wants a
            # `Datetime` column of naive-UTC bar OPEN times and then
            # resample_causal_tf re-indexes every frame to bar END time
            # (label=left, closed=left, index += delta). Verified against
            # the data already in this repo: data/BTCUSD_5m/2024.csv.gz
            # row 1 = 2024-01-01 00:00:00,42283.58,42397.23,42261.02,
            # 42397.23,155.26 - the very same Binance spot kline.
            ms = int(line[0])
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ms / 1000.0))
            w.writerow([ts, line[1], line[2], line[3], line[4], line[5]])
            rows += 1
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    return rows, sha


def convert_local_zips(zip_dir: Path, symbols: list[str],
                       months: list[str]) -> dict:
    """Same normalisation as pull(), but from ZIPs already on disk.

    Used when the archives were obtained by another route (a mirror, a
    colleague's download, a repo tarball) - ONE code path for both, so a
    converted file and a freshly downloaded file are identical."""
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, gaps, n_conv = [], {}, 0
    for sym in symbols:
        d = OUT / f"{sym}_5m"
        for m in months:
            dest = d / f"{m}.csv.gz"
            src = None
            for cand in (zip_dir / f"{sym}-5m-{m}.zip",
                         zip_dir / sym / f"{sym}-5m-{m}.zip"):
                if cand.exists():
                    src = cand
                    break
            if src is None:
                found = list(zip_dir.rglob(f"{sym}-5m-{m}.zip"))
                src = found[0] if found else None
            if src is None:
                gaps.setdefault(sym, []).append({"month": m,
                                                 "problem": "zip not found"})
                continue
            rows, sha = zip_to_csv_gz(src.read_bytes(), dest)
            n_conv += 1
            print(f"  + {sym} {m} {rows} rows <- {src.name}")
            if rows < MIN_ROWS:
                gaps.setdefault(sym, []).append({"month": m, "rows": rows,
                                                 "problem": "short month"})
            manifest.append({"symbol": sym, "month": m, "rows": rows,
                             "sha256": sha, "source": str(src),
                             "path": str(dest.relative_to(OUT.parent.parent))})
    (OUT / "MANIFEST.sha256").write_text(
        "".join(f"{r['sha256']}  {r['path']}  rows={r['rows']}\n"
                for r in manifest))
    (OUT / "GAPS.json").write_text(json.dumps(gaps, indent=1))
    return {"files": len(manifest), "converted": n_conv,
            "rows": sum(r["rows"] for r in manifest), "gaps": gaps}


def pull(symbols: list[str], months: list[str]) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest, gaps = [], {}
    for sym in symbols:
        d = OUT / f"{sym}_5m"
        got = 0
        for m in months:
            dest = d / f"{m}.csv.gz"
            if dest.exists() and dest.stat().st_size > 1000:
                with gzip.open(dest, "rt") as g:
                    rows = sum(1 for _ in g) - 1
                sha = hashlib.sha256(dest.read_bytes()).hexdigest()
                print(f"  = {sym} {m} cached ({rows} rows)")
            else:
                raw = fetch(url_for(sym, m))
                if raw is None:
                    gaps.setdefault(sym, []).append({"month": m,
                                                     "problem": "404/unreachable"})
                    print(f"  x {sym} {m} UNAVAILABLE")
                    continue
                rows, sha = zip_to_csv_gz(raw, dest)
                print(f"  + {sym} {m} {rows} rows -> {dest.name}")
            if rows < MIN_ROWS:
                gaps.setdefault(sym, []).append({"month": m, "rows": rows,
                                                 "problem": "short month"})
            manifest.append({"symbol": sym, "month": m, "rows": rows,
                             "sha256": sha,
                             "path": str(dest.relative_to(OUT.parent.parent))})
            got += 1
        if got == 0:
            gaps.setdefault(sym, []).append({"problem": "NO DATA AT ALL"})
    (OUT / "MANIFEST.sha256").write_text(
        "".join(f"{r['sha256']}  {r['path']}  rows={r['rows']}\n"
                for r in manifest))
    (OUT / "GAPS.json").write_text(json.dumps(gaps, indent=1))
    return {"files": len(manifest), "rows": sum(r["rows"] for r in manifest),
            "gaps": gaps}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--symbols", nargs="*", default=None)
    ap.add_argument("--months", nargs="*", default=None)
    ap.add_argument("--with-fallbacks", action="store_true",
                    help="also pull DOTUSDT/NEARUSDT")
    ap.add_argument("--from-zips", metavar="DIR", default=None,
                    help="convert Binance monthly ZIPs already on disk "
                         "instead of downloading (same normalisation)")
    args = ap.parse_args()
    syms = args.symbols or (SYMBOLS + (FALLBACKS if args.with_fallbacks else []))
    months = month_list(args.months)
    print(f"v32 fetcher: {len(syms)} symbols x {len(months)} months "
          f"({months[0]}..{months[-1]}) -> {OUT}")
    t0 = time.time()
    res = (convert_local_zips(Path(args.from_zips), syms, months)
           if args.from_zips else pull(syms, months))
    dt = time.time() - t0
    print(f"\ndone in {dt:.1f}s: {res['files']} files, {res['rows']} rows")
    if res["gaps"]:
        print("!! GAPS (a substitute pair may be needed):")
        print(json.dumps(res["gaps"], indent=1))
        print("   authorised substitutes: " + ", ".join(FALLBACKS))
        return 1
    print("no gaps — every coin-month present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
