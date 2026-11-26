"""Build data/binance_5m_oos/ : the dev months (from the validated 5m set)
plus the fetched 1m months resampled to 5m with the SAME resampler."""
import sys, shutil
from pathlib import Path
import pandas as pd
sys.path.insert(0, '.')
from engine.causal_primitives import resample_causal_tf

SRC5 = Path('data/binance_5m'); OUT = Path('data/binance_5m_oos')
K1 = Path('/home/user/k1m')
SYMS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","AVAXUSDT","LINKUSDT","ADAUSDT"]
NEW = [f"2023-{m:02d}" for m in range(1,8)] + \
      [f"2024-{m:02d}" for m in (11,12)] + \
      [f"2025-{m:02d}" for m in range(1,13)] + \
      [f"2026-{m:02d}" for m in range(1,12)]
rows=[]
for sym in SYMS:
    d = OUT/f"{sym}_5m"; d.mkdir(parents=True, exist_ok=True)
    # 1) copy the already-validated dev months
    for f in sorted((SRC5/f"{sym}_5m").glob("*.csv.gz")):
        target = d/(f.name if f.name.endswith('.csv.gz') else f.name+'.csv.gz')
        if not target.name.endswith('.csv.gz'): continue
        if 'BUILD' in f.name: continue
        shutil.copyfile(f, target)
    have = {f.name.split('.')[0] for f in d.glob("*.csv.gz")}
    # 2) resample the fetched 1m months
    made=0
    for mth in NEW:
        if mth in have: continue
        y, mm = mth.split('-')
        f1 = K1/sym/"1m"/y/mm/f"{sym}_1m_{mth}.csv"
        if not f1.exists():
            rows.append((sym, mth, "MISSING_1M", 0)); continue
        raw = pd.read_csv(f1)
        cols = {c.lower(): c for c in raw.columns}
        tcol = cols.get('datetime_utc') or cols.get('datetime') or cols.get('open_time') or list(raw.columns)[0]
        raw[tcol] = pd.to_datetime(raw[tcol], utc=True, format='mixed')
        raw = raw.set_index(tcol).sort_index()
        ren = {}
        for want, cands in (("Open",("open",)),("High",("high",)),("Low",("low",)),
                            ("Close",("close",)),("Volume",("volume",))):
            for c in raw.columns:
                if c.lower() in cands: ren[c]=want; break
        raw = raw.rename(columns=ren)
        raw = raw[["Open","High","Low","Close","Volume"]].astype(float)
        tf = resample_causal_tf(raw, "5min")   # OHLC only (the engine's own
        #                                        resampler records positions,
        #                                        not volume; volume is unused)
        tf = tf[["Open","High","Low","Close"]].copy()
        tf["Volume"] = 0.0
        tf = tf.reset_index().rename(columns={"end_time":"Datetime"})
        tf.to_csv(d/f"{mth}.csv.gz", index=False, compression="gzip")
        made+=1; rows.append((sym, mth, "ok", len(tf)))
    tot = len(list(d.glob("*.csv.gz")))
    print(f"{sym}: copied+made={tot}  new_this_run={made}", flush=True)
print("DONE", len(rows))
