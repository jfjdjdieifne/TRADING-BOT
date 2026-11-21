import json, glob, numpy as np, pandas as pd
D="data/binance_5m"; W={"W1":("2023-10-01","2024-03-31"),"W2":("2024-05-01","2024-10-31")}
SY=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","AVAXUSDT","LINKUSDT","ADAUSDT"]
px={}
for s in SY:
    f=sorted(glob.glob(f"{D}/{s}_5m/*.csv.gz"))
    d=pd.concat([pd.read_csv(x) for x in f],ignore_index=True)
    d["t"]=pd.to_datetime(d.Datetime,utc=True); d=d.set_index("t").sort_index()
    px[s]=d
print("=== (A) ACTUAL COIN MOVES FROM THE DATA WE LOADED ===")
for w,(a,b) in W.items():
    print(f"-- {w} {a}..{b}")
    for s in SY:
        d=px[s].loc[a:b]
        if not len(d): continue
        mv=(d.Close.iloc[-1]/d.Open.iloc[0]-1)*100
        wk=d.Close.resample("7D").last().pct_change().dropna()*100
        lo,hi=d.Low.min(),d.High.max()
        print(f"   {s:9s} open->close {mv:+7.1f}%   low->high {(hi/lo-1)*100:+7.1f}%   best week {wk.max():+6.1f}%  worst week {wk.min():+6.1f}%  n_weeks>{15}%: {(wk>15).sum()}")
print()
print("=== (B) CLAIM 1: does the engine really deploy only $15 of $100? ===")
for tag in ["FULL_3s_W1","FULL_3s_W2","P1_all8_W1","P1_all8_W2","P3_B_W1"]:
    f=f"results/trades_v32_{tag}.csv"
    try: tr=pd.read_csv(f)
    except Exception: continue
    eq=100.0+tr.net_pnl.cumsum().shift(1).fillna(0.0)
    r=(tr.notional/eq)
    print(f"   {tag:12s} n={len(tr):3d}  notional/equity_at_entry: min={r.min():.4f} median={r.median():.4f} max={r.max():.4f}")
    print(f"                  notional$: min={tr.notional.min():.2f} median={tr.notional.median():.2f} max={tr.notional.max():.2f}   <$10 (below Binance min): {(tr.notional<10).sum()}")
    print(f"                  risk_pct(stop width): median={tr.risk_pct.median()*100:.3f}%  min={tr.risk_pct.min()*100:.3f}% max={tr.risk_pct.max()*100:.2f}%")
print()
print("=== (C) CLAIM 2: is every winner choked at +3R? exit R distribution ===")
for tag in ["FULL_3s_W1","FULL_3s_W2","P1_all8_W1"]:
    tr=pd.read_csv(f"results/trades_v32_{tag}.csv")
    print(f"-- {tag}  n={len(tr)} maxR={tr.R.max():.2f} totR={tr.R.sum():+.2f} bars_held median={tr.bars_held.median():.0f}")
    print("   exit_reason:",dict(tr.exit_reason.value_counts()))
    sp=tr[tr.exit_reason=="STRUCT_PROFIT"]
    if len(sp):
        print(f"   STRUCT_PROFIT n={len(sp)}: R min={sp.R.min():.2f} median={sp.R.median():.2f} max={sp.R.max():.2f} | mfe_R median={sp.mfe_R.median():.2f} max={sp.mfe_R.max():.2f}")
        print(f"     of those, R>5: {(sp.R>5).sum()}  R>10: {(sp.R>10).sum()}  R>20: {(sp.R>20).sum()}")
    print("   R histogram:",{k:int(v) for k,v in pd.cut(tr.R,[-99,-1,-0.01,0.05,1,2,3,5,10,20,999]).value_counts().sort_index().items()})
    print("   by exec_tf:",dict(tr.exec_tf.value_counts()))
print()
print("=== (D) POST-EXIT CONTINUATION: how much of the wave was left on the table? ===")
for tag in ["FULL_3s_W1","FULL_3s_W2"]:
    tr=pd.read_csv(f"results/trades_v32_{tag}.csv")
    sp=tr[tr.exit_reason=="STRUCT_PROFIT"].copy()
    rows=[]
    for _,t in sp.iterrows():
        s=t.symbol.replace("_5m",""); d=px[s]
        et=pd.Timestamp(t.exit_time)
        if et.tz is None: et=et.tz_localize("UTC")
        fut=d.loc[et:et+pd.Timedelta(days=7)]
        if len(fut)<10: continue
        up=(fut.High.max()/t.exit_price-1)*100
        rows.append((s,t.R,up,t.bars_held))
    if rows:
        df=pd.DataFrame(rows,columns=["sym","R_at_exit","upside_7d_after_exit_pct","bars"])
        print(f"-- {tag}: STRUCT_PROFIT exits with 7d of future data: n={len(df)}")
        print(f"   R captured at exit: median={df.R_at_exit.median():.2f} mean={df.R_at_exit.mean():.2f}")
        print(f"   price upside in the 7 days AFTER exit: median={df.upside_7d_after_exit_pct.median():+.2f}% mean={df.upside_7d_after_exit_pct.mean():+.2f}% max={df.upside_7d_after_exit_pct.max():+.2f}%")
        print(f"   exits after which price ran > +15% within 7d: {(df.upside_7d_after_exit_pct>15).sum()}/{len(df)}   > +30%: {(df.upside_7d_after_exit_pct>30).sum()}")
        print(f"   worst: price fell after exit in {(df.upside_7d_after_exit_pct<0).sum()}/{len(df)} cases (median {df.loc[df.upside_7d_after_exit_pct<0,'upside_7d_after_exit_pct'].median() if (df.upside_7d_after_exit_pct<0).any() else 0:+.2f}%)")
print()
print("=== (E) CLAIM 3: 393 trades - who paid, who ate the fees? ===")
for tag in ["FULL_3s_W1","FULL_3s_W2"]:
    tr=pd.read_csv(f"results/trades_v32_{tag}.csv"); j=json.load(open(f"results/lab_v32_{tag}.json"))
    g=tr.groupby(tr.symbol.str.replace("_5m","")).agg(n=("R","size"),totR=("R","sum"),netusd=("net_pnl","sum"),fees=("entry_fee","sum"))
    print(f"-- {tag} n={len(tr)} fees$={j['fees']:.2f} net$={j['net']:.2f} gross_win$={tr.loc[tr.net_pnl>0,'net_pnl'].sum():.2f} gross_loss$={tr.loc[tr.net_pnl<0,'net_pnl'].sum():.2f}")
    print(g.round(2).to_string())
