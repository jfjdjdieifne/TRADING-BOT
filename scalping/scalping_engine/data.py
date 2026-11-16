"""Data loaders for the scalping package.

Local archives (already in this repository):
  * BTCUSD 5m  : smc_v4_multisleeve_package/data/BTCUSD_5m/*.csv.gz
  * XAUUSD 1m  : smc_v4_multisleeve_package/data/XAUUSD_1m_histdata/*.csv.gz
  * NSXUSD 1m  : smc_v4_multisleeve_package/data/NSXUSD_1m_histdata/*.csv.gz

All are UTC OHLCV CSVs. Nothing is downloaded implicitly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "smc_v4_multisleeve_package" / "data"


def _load_dir(path: Path, stems: list[str] | None = None) -> pd.DataFrame:
    files = sorted(path.glob("*.csv.gz"))
    if stems is not None:
        want = {f"{s}.csv.gz" for s in stems}
        files = [f for f in files if f.name in want]
    if not files:
        raise FileNotFoundError(f"no archives in {path}")
    parts = []
    for f in files:
        df = pd.read_csv(f)
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True)
        parts.append(df)
    out = pd.concat(parts, ignore_index=True)
    out = out.sort_values("Datetime").drop_duplicates("Datetime", keep="first")
    out = out.set_index("Datetime")
    for col in ("Open", "High", "Low", "Close"):
        out[col] = out[col].astype(np.float64)
    if "Volume" not in out.columns:
        out["Volume"] = 0.0
    out["Volume"] = out["Volume"].astype(np.float64)
    return out


def load_btc_5m(years: list[int] | None = None) -> pd.DataFrame:
    stems = None if years is None else [str(y) for y in years]
    return _load_dir(PKG / "BTCUSD_5m", stems)


def load_xau_1m(months: list[str] | None = None) -> pd.DataFrame:
    return _load_dir(PKG / "XAUUSD_1m_histdata", months)


def load_nsx_1m(months: list[str] | None = None) -> pd.DataFrame:
    return _load_dir(PKG / "NSXUSD_1m_histdata", months)


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load an arbitrary UTC OHLCV CSV/CSV.GZ (columns Datetime,Open,...)."""
    df = pd.read_csv(path)
    tcol = "Datetime" if "Datetime" in df.columns else df.columns[0]
    df[tcol] = pd.to_datetime(df[tcol], utc=True)
    df = df.set_index(tcol).sort_index()
    for col in ("Open", "High", "Low", "Close"):
        df[col] = df[col].astype(np.float64)
    if "Volume" not in df.columns:
        df["Volume"] = 0.0
    df["Volume"] = df["Volume"].astype(np.float64)
    return df
