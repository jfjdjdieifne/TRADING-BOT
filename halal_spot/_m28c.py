import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
from pathlib import Path
FEE=0.001; MIN_R=3.0
raw=load_asset_ohlcv(Path("data/BTCUSD_5m"), include_stems=None)
tf5=resample_causal_tf(raw,"5min"); idx=tf5.index
a=pd.read_csv("results/trades_v27.csv")

def run(mode):
    """mode wick5 : stop armed at lock after the locking 5m close, exit on a 5m LOW <= stop
       mode close5: exit on a 5m CLOSE  <= lock (engine's floor rule, moved to 5m)
       mode exec  : v27 booked result (no 5m pass)"""
    out=[]
    for _,t in a.iterrows():
        E=float(t.entry_price); SP=float(t.stop_price); risk=E-SP
        if risk<=0: continue
        lock=(E*(1+FEE)+MIN_R*risk)/(1-FEE)
        Rof=lambda px: ((px-E)-E*FEE-px*FEE)/risk
        et=pd.Timestamp(t.entry_time); xt=pd.Timestamp(t.exit_time)
        i0=idx.searchsorted(et,side="right"); i1=idx.searchsorted(xt,side="left")
        w=tf5.iloc[i0:i1] if i1>i0 else tf5.iloc[0:0]
        c=w.Close.values; l=w.Low.values; o=w.Open.values
        lk=np.where(c>=lock)[0]
        if mode=="exec" or len(lk)==0:
            out.append((t.entry_time,t["class"],t.R,t.R,None)); continue
        k=int(lk[0]); R5=None
        if mode=="wick5":
            br=np.where(l[k+1:]<=lock)[0]
            if len(br):
                j=k+1+int(br[0]); fill=lock if o[j]>=lock else o[j]; R5=Rof(fill)
        else:  # close5
            br=np.where(c[k+1:]<=lock)[0]
            if len(br):
                j=k+1+int(br[0]); R5=Rof(c[j])
        out.append((t.entry_time,t["class"],t.R, R5 if R5 is not None else t.R, k))
    return pd.DataFrame(out,columns=["entry","class","R_v27","R_new","lock_bar"])

def rep(name,d):
    R=d.R_new.values
    wins=(R>=MIN_R-1e-9)&(d.class_=="WIN") if False else (R>=MIN_R-1e-9)
    W=int(wins.sum())
    # class re-derivation: >=3R net => WIN ; -0.05<=R<3 => BE ; else LOSS
    be=int(((R<MIN_R-1e-9)&(R>=-0.05)).sum()); L=int((R<-0.05).sum())
    wr=100*W/(W+L) if W+L else 0.0
    print(f"{name:12s} n={len(d):4d}  W={W:4d} BE={be:4d} L={L:4d}  WR={wr:6.2f}%  "
          f"maxR={np.nanmax(R):6.2f}  >=4R={int((R>=4).sum()):3d}  >=6R={int((R>=6).sum()):3d}  "
          f"totR={np.nansum(R):8.2f}  minWinR={np.nanmin(R[R>=MIN_R-1e-9]) if (R>=MIN_R-1e-9).any() else float('nan'):.2f}")
    return W,be,L,wr

base=rep("v27 booked ", run("exec"))
for m in ("wick5","close5"):
    d=run(m); rep(m+"      ", d)
    w=d[(d["class"]=="WIN")]
    big=w[w.R_v27>=6]
    print(f"   runners >=6R under {m}: v27 R -> new R:")
    print(big[["entry","R_v27","R_new"]].round(2).sort_values("R_v27",ascending=False).to_string(index=False))
