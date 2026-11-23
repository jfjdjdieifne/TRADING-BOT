import sys; sys.path.insert(0,'.')
import strategy_v35_ict_surgical_shield as S
from pathlib import Path
def probe(tag, **kw):
    for k,v in dict(ALLOC_MODE="slot",SLOTS=1,SLOT_FILL="fixed",MAX_OPEN_POSITIONS=1,
                    FULL_100_DEPLOY=True,SMT_BRAIN=True,SMT_GATE="prefer",
                    KILLZONE_MODE="exclude",KILLZONE_DOW=(6,),
                    MIN_STOP_PCT=0.0,NO_FALL_CLOSE=False,PER_COIN_COOLDOWN=0).items():
        setattr(S,k,v)
    for k,v in kw.items(): setattr(S,k,v)
    r=S.run_backtest(Path('data/binance_5m'),'2024-05-01','2024-10-31',tag=tag)
    c=r["count"]; n=len(r['trades']); net=sum(t['net_pnl'] for t in r['trades'])
    print(f"{tag:10s} n={n:3d} net=${net:+7.2f} dust={c.get('v35_dust_box_veto',0):5d} "
          f"fall={c.get('v35_fall_close_veto',0):4d} flash={c.get('v35_flash_seller_veto',0):4d}", flush=True)
probe("base")
probe("dust", MIN_STOP_PCT=0.25)
probe("fall", NO_FALL_CLOSE=True)
probe("flash", FLASH_SELLER_VETO=True)
