import sys, importlib.util, pandas as pd
spec=importlib.util.spec_from_file_location("lab","lab_v31_compounding_brain.py")
lab=importlib.util.module_from_spec(spec); spec.loader.exec_module(lab)
import strategy_v31_ict_compounding as S
combo=sys.argv[1]; y0,y1=sys.argv[2],sys.argv[3]
cfg=dict(lab.BASE); cfg.update(lab.COMBOS[combo])
for k,v in cfg.items(): setattr(S,k,v)
run=S.run_backtest(S.DATA_DIR,y0,y1,tag="det")
tr=pd.DataFrame(run["trades"])
print("COMBO=%s window=%s..%s n=%d totR=%.4f net$=%.4f first=%s last=%s"%(
    combo,y0,y1,len(tr),tr.R.sum(),tr.net_pnl.sum(),tr.entry_time.iloc[0],tr.entry_time.iloc[-1]))
