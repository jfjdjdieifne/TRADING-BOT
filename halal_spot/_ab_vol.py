"""A/B: does the engine READ Volume at all?

Runs the shipped champion on data/binance_5m (real Binance volume) twice:
  REAL      -> as on disk
  ZERO      -> every Volume column forced to 0.0 before the engine sees it
Identical trades => Volume is inert.  That is what licenses the 32 rebuilt
OOS months, which were resampled from 1m OHLC and carry Volume=0.0.
"""
import sys
import pandas as pd
import strategy_v36_ict_champion as S

S.V32_DATA_DIR = "data/binance_5m"
ZERO = "--zero-vol" in sys.argv
if ZERO:
    _orig = S.pd.read_csv
    S.pd.read_csv = lambda p, *a, **k: (
        lambda d: (d.assign(Volume=0.0) if "Volume" in d.columns else d))(
            _orig(p, *a, **k))

run = S.run_backtest(S.v34_data_dir(), "2024-06-01", "2024-07-31", tag="abvol")
tr = pd.DataFrame(run["trades"])
print(("ZERO" if ZERO else "REAL"),
      "n=", len(tr),
      "totR=", round(float(tr.R.sum()), 6),
      "net=", round(float(tr.net_pnl.sum()), 6),
      "fees=", round(float(run["fees"]), 6),
      flush=True)
