import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
from pathlib import Path
FEE=0.001; MIN_R=3.0
raw=load_asset_ohlcv(Path("data/BTCUSD_5m"), include_stems=None)
tf5=resample_causal_tf(raw,"5min"); idx=tf5.index
a=pd.read_csv("results/trades_v27.csv")
rows=[]
for _,t in a.iterrows():
    E=float(t.entry_price); SP=float(t.stop_price); risk=E-SP
    if risk<=0: continue
    lock=(E*(1+FEE)+MIN_R*risk)/(1-FEE)
    def Rof(px): return ((px-E)-E*FEE-px*FEE)/risk
    et=pd.Timestamp(t.entry_time); xt=pd.Timestamp(t.exit_time)
    i0=idx.searchsorted(et,side="right"); i1=idx.searchsorted(xt,side="left")
    if i1<=i0: rows.append((t.entry_time,t["class"],t.R,np.nan,np.nan,0,0)); continue
    w=tf5.iloc[i0:i1]; c=w.Close.values; l=w.Low.values; o=w.Open.values
    lk=np.where(c>=lock)[0]
    if len(lk)==0: rows.append((t.entry_time,t["class"],t.R,np.nan,np.nan,0,len(w))); continue
    k=int(lk[0]); br=np.where(l[k:]<=lock)[0]
    if len(br)==0: rows.append((t.entry_time,t["class"],t.R,np.nan,np.nan,len(w)-k,len(w)-k)); continue
    j=k+int(br[0]); fill=lock if o[j]>=lock else o[j]
    rows.append((t.entry_time,t["class"],t.R,Rof(fill),j-k,len(w)-k,len(w)))
d=pd.DataFrame(rows,columns=["entry","class","R_v27","R_5m","bars_to_break","after_lock","nbars"])
print("sanity: lock R at lock_line ->", round(((lock-E)-E*FEE-lock*FEE)/risk,4))
for cls in ("WIN","BE","LOSS"):
    s=d[d["class"]==cls]; lk5=s[s.R_5m.notna() & (s.bars_to_break.notna())]
    print(f"{cls:5s} n={len(s):4d}  locked-on-5m-inside-life={int(s.bars_to_break.notna().sum()):4d}"
          f"  5m-floor-break-before-v27-exit={int(((s.bars_to_break.notna())&(s.R_5m<s.R_v27-1e-9)).sum()):4d}")
w=d[d["class"]=="WIN"]; clip=w[(w.bars_to_break.notna())&(w.R_5m<w.R_v27-1e-9)]
print(f"\nWINNERS CLIPPED by a 5m floor break: {len(clip)} of {len(w)}")
print(clip[["entry","R_v27","R_5m","bars_to_break"]].round(2).to_string(index=False))
newR=np.where(d.bars_to_break.notna() & d.R_5m.notna(), d.R_5m, d.R_v27)
print(f"\nmaxR   : v27 {d.R_v27.max():7.2f}  ->  5m-floor-exit {np.nanmax(newR):7.2f}")
print(f">=4R   : v27 {(d.R_v27>=4).sum():7d}  ->  {(newR>=4).sum():7d}")
print(f">=6R   : v27 {(d.R_v27>=6).sum():7d}  ->  {(newR>=6).sum():7d}")
print(f">=3R   : v27 {(d.R_v27>=3-1e-9).sum():7d}  ->  {(newR>=3-1e-9).sum():7d}")
print(f"totR   : v27 {d.R_v27.sum():8.2f}  ->  {np.nansum(newR):8.2f}")
