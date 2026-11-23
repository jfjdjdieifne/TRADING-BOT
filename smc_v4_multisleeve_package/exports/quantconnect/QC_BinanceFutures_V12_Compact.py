# QUANTCONNECT.COM - Binance Futures Multi-Coin V12.0 Compact Institutional Export
from AlgorithmImports import *
from collections import deque
import math

def _sig(x,x0=0.0,k=1.0): return 1.0/(1.0+math.exp(max(-60.0,min(60.0,-k*(x-x0)))))
def _ker(cs):
 if len(cs)<3: return 0.0
 d=sum(abs(cs[i]-cs[i-1]) for i in range(1,len(cs))); return abs(cs[-1]-cs[0])/d if d>1e-12 else 0.0

class ATR14:
 def __init__(self): self.pc=None; self.val=0.0; self.ok=False
 def upd(self,h,l,c):
  tr=(h-l) if self.pc is None else max(h-l,abs(h-self.pc),abs(l-self.pc)); self.pc=c
  self.val=tr if not self.ok else (self.val*13+tr)/14; self.ok=True; return self.val

class EMA:
 def __init__(self,n): self.a,self.v=2.0/(n+1),None
 def upd(self,x): self.v=x if self.v is None else x*self.a+self.v*(1-self.a); return self.v

class SwingK3:
 def __init__(self): self.w,self.i,self.ah,self.al=deque(maxlen=7),-1,[],[]
 def upd(self,h,l):
  self.i+=1; self.w.append((h,l))
  if len(self.w)==7:
   ch,cl=self.w[3]
   if ch>=max(x[0] for x in self.w) and any(x[0]<ch for x in self.w): self.ah=(self.ah+[(self.i-3,ch)])[-24:]
   if cl<=min(x[1] for x in self.w) and any(x[1]>cl for x in self.w): self.al=(self.al+[(self.i-3,cl)])[-24:]
  self.ah=[x for x in self.ah if h<=x[1]]; self.al=[x for x in self.al if l>=x[1]]

class TopoSwing:
 def __init__(self,m=0.80,sep=3):
  self.m,self.sep,self.i,self.d,self.pi=m,sep,-1,0,0
  self.ph=self.pl=self.rh=self.rl=self.lh=self.ll=None; self.tr,self.ah,self.al,self.atr=0,[],[],ATR14()
 def upd(self,h,l,c,a=0.0):
  self.i+=1; a=a if a>0 else self.atr.upd(h,l,c)
  if self.ph is None: self.ph=self.rh=h; self.pl=self.rl=l; self.pi=self.i; return
  self.rh,self.rl=max(self.rh,h),min(self.rl,l)
  if a>0:
   th=self.m*a
   if self.d==0:
    if h-self.pl>=th and self.i-self.pi>=self.sep: self.ll=self.pl; self.al=(self.al+[(self.pi,self.pl,(h-self.pl)/a)])[-24:]; self.d,self.ph,self.pi,self.rl=1,h,self.i,l
    elif self.ph-l>=th and self.i-self.pi>=self.sep: self.lh=self.ph; self.ah=(self.ah+[(self.pi,self.ph,(self.ph-l)/a)])[-24:]; self.d,self.pl,self.pi,self.rh=-1,l,self.i,h
    else:
     if h>self.ph: self.ph,self.pi=h,self.i
     if l<self.pl: self.pl,self.pi=l,self.i
   elif self.d==1:
    if h>=self.ph: self.ph,self.pi,self.rl=h,self.i,l
    elif self.ph-l>=th and self.i-self.pi>=self.sep: self.lh=self.ph; self.ah=(self.ah+[(self.pi,self.ph,(self.ph-self.rl)/a)])[-24:]; self.d,self.pl,self.pi,self.rh=-1,l,self.i,h
   else:
    if l<=self.pl: self.pl,self.pi,self.rh=l,self.i,h
    elif h-self.pl>=th and self.i-self.pi>=self.sep: self.ll=self.pl; self.al=(self.al+[(self.pi,self.pl,(self.rh-self.pl)/a)])[-24:]; self.d,self.ph,self.pi,self.rl=1,h,self.i,l
  self.ah=[x for x in self.ah if h<=x[1]]; self.al=[x for x in self.al if l>=x[1]]
  if self.lh and c>self.lh: self.tr=1
  elif self.ll and c<self.ll: self.tr=-1

class RefTracker:
 def __init__(self): self.d=self.w=self.pdh=self.pdl=self.pwh=self.pwl=self.dh=self.dl=self.wh=self.wl=self.ash=self.asl=self.loh=self.lol=None; self.pt=[0,0]
 def upd(self,dt,h,l,c,a):
  d,w,hm=dt.date(),dt.isocalendar()[:2],dt.hour+dt.minute/60.0
  if self.w!=w:
   if self.w is not None: self.pwh,self.pwl=self.wh,self.wl
   self.w,self.wh,self.wl=w,h,l
  else: self.wh,self.wl=max(self.wh,h),min(self.wl,l)
  if self.d!=d:
   if self.d is not None: self.pdh,self.pdl=self.dh,self.dl
   self.d,self.dh,self.dl,self.ash,self.asl,self.loh,self.lol,self.pt=d,h,l,None,None,None,None,[0,0]
  else: self.dh,self.dl=max(self.dh,h),min(self.dl,l)
  if hm<7: self.ash=h if self.ash is None else max(self.ash,h); self.asl=l if self.asl is None else min(self.asl,l)
  elif hm<12.5: self.loh=h if self.loh is None else max(self.loh,h); self.lol=l if self.lol is None else min(self.lol,l)
  tol=0.20*max(a,c*0.001)
  if self.pdh and h>=self.pdh-tol: self.pt[0]+=1
  if self.pdl and l<=self.pdl+tol: self.pt[1]+=1
  return (self.pdh,self.pdl,self.pwh,self.pwl,self.ash if hm>=7 else None,self.asl if hm>=7 else None,self.loh if hm>=12.5 else None,self.lol if hm>=12.5 else None,self.pt[0],self.pt[1])

class Coin:
 def __init__(self,tk,sym,lev):
  self.tk,self.sym,self.lev=tk,sym,lev
  self.sw4,self.sw1,self.sw5=TopoSwing(0.80,3),TopoSwing(0.80,3),TopoSwing(0.70,3)
  self.t4,self.t1,self.t15,self.t5,self.k3=TopoSwing(1.25,1),TopoSwing(1.15,1),TopoSwing(1.15,1),TopoSwing(0.50,1),SwingK3()
  self.a4,self.a1,self.a5,self.e20d,self.e50d=ATR14(),ATR14(),ATR14(),EMA(20),EMA(50)
  self.c4,self.dh4,self.dl4,self.b5,self.v5=deque(maxlen=25),deque(maxlen=20),deque(maxlen=20),deque(maxlen=40),deque(maxlen=20)
  self.ref=RefTracker(); self.ker4=self.br4=0.0; self.dir4=self.i4=self.cd4=self.i5=self.cd5=0
  self.p4o=self.p4c=self.p4h=self.p4l=self.ld=self.lh=self.ll=None
  self.lsw,self.c1h,self.clon,self.ck3,self.lv9=[False,False],[],[],[],{1:-999,-1:-999}
  self.ptk=self.pm=self.sltk=self.tptk=self.partk=self.eng=self.tp=self.trl=None
  self.in_pos=self.t1ok=self.t2ok=self.parm=False; self.sd=self.pst=0
  self.ep=self.sl=self.rd=self.qty=self.iqty=self.best=0.0; self.cids,self.sllk=set(),()
  self.br=self.bf=self.lk1=self.br2=self.bf2=self.lk2=0.0

class BinanceFuturesMultiCoinV12(QCAlgorithm):
 TICKERS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","AVAXUSDT","LINKUSDT","SUIUSDT")

 def initialize(self):
  self.set_time_zone(TimeZones.UTC); self.set_start_date(2021,1,1); self.set_end_date(2026,10,31)
  cash=float(self.get_parameter("start_cash") or 100.0); self.set_account_currency("USDT",cash)
  self.hwm=self.skanc=self.wkeq=cash; self.vault,self.wk=0.0,None
  self.small=str(self.get_parameter("small_account_mode") or ("true" if cash<=500 else "false")).lower()=="true"
  self.prof=str(self.get_parameter("v10_profile") or "DAILY_HUNTER").upper()
  self.r_std,self.r_ap,self.skstep,self.cbr=(0.035,0.040,20.0,-2.5) if self.prof=="TURBO_SNIPER" else (0.030,0.034,25.0,-2.0)
  self.lev,self.maxp,self.feert,self.rday,self.rpnl=(15.0 if self.small else 10.0),(4 if self.small else 3),0.0010,None,0.0
  self.set_warm_up(timedelta(days=65),Resolution.MINUTE); self.set_brokerage_model(BrokerageName.BINANCE_FUTURES,AccountType.MARGIN)
  self.coins={}
  for tk in self.TICKERS:
   sec=self.add_crypto_future(tk,Resolution.MINUTE,Market.BINANCE,leverage=int(self.lev)); s=Coin(tk,sec.symbol,self.lev); self.coins[sec.symbol]=s
   for td,fn in ((timedelta(days=1),lambda b,s=s:(s.e20d.upd(float(b.Close)),s.e50d.upd(float(b.Close)))),(timedelta(hours=4),lambda b,s=s:self._on4h(s,b)),(timedelta(hours=1),lambda b,s=s:self._on1h(s,b)),(timedelta(minutes=15),lambda b,s=s:s.t15.upd(float(b.High),float(b.Low),float(b.Close))),(timedelta(minutes=5),lambda b,s=s:self._on5m(s,b))):
    self.consolidate(sec.symbol,td,fn)

 def _ae(self): return max(1.0,float(self.portfolio.total_portfolio_value)-(self.vault if self.small else 0.0))
 def _anceq(self):
  ae=self._ae(); wk=self.utc_time.isocalendar()[:2]
  if self.wk!=wk: self.wk,self.wkeq=wk,ae
  return min(self.wkeq,ae)

 def _rpct(self,ap):
  ae=self._ae(); dd=(self.hwm-ae)/self.hwm if self.hwm>0 else 0.0
  return ((self.r_ap if ap else self.r_std) if self.small else (0.020 if ap else 0.015))*(0.60 if dd>=0.20 else (0.75 if dd>=0.12 else 1.0))

 def _btc_ok(self,s,sd):
  if s.tk=="BTCUSDT" or sd==0: return True
  btc=next((c for c in self.coins.values() if c.tk=="BTCUSDT"),None)
  return not (btc and btc.ker4>0.68 and btc.dir4 and btc.dir4!=sd)

 def _can(self,s):
  d=self.utc_time.date()
  if self.rday!=d: self.rday,self.rpnl=d,0.0
  oc=sum(1 for c in self.coins.values() if c.ptk or (c.in_pos and not ((c.sd==1 and c.sl>=c.ep) or (c.sd==-1 and c.sl<=c.ep))))
  return not self.is_warming_up and not s.in_pos and not s.ptk and self.rpnl>self.cbr and s.i5>=s.cd5 and oc<self.maxp and float(self.securities[s.sym].price)>0

 def _rq(self,sym,rq,lng):
  sp=self.securities[sym].symbol_properties; lot,mn=float(sp.lot_size or 0.001),float(sp.minimum_order_size or 0.001)
  q=round(math.floor((abs(rq)/lot)+1e-9)*lot,8); return (q if lng else -q) if q>=mn else 0.0

 def _rp(self,sym,px):
  tk=float(self.securities[sym].symbol_properties.minimum_price_variation or 0.01) or 0.01; return round(round(px/tk)*tk,8)

 def _sub(self,s,eng,sd,trig,sl,tpr,mkt,ap,trl=None,br=2.2,bf=0.45,lk1=0.35,br2=4.5,bf2=0.40,lk2=2.0,sllk=(),mult=1.0,pyr=0):
  if pyr==0 and not self._can(s): return
  pf,cur,tx,sx=self.portfolio,float(self.securities[s.sym].price),self._rp(s.sym,trig),self._rp(s.sym,sl)
  rd=(tx-sx) if sd==1 else (sx-tx)
  if rd<=0 or cur<=0 or (not mkt and ((sd==1 and tx>cur) or (sd==-1 and tx<cur))): return
  mn=min(max(0.0,float(pf.margin_remaining))*s.lev*0.85,float(pf.total_portfolio_value)*s.lev*(0.85 if self.small else 0.30))
  q=self._rq(s.sym,min((self._anceq()*self._rpct(ap)*mult)/(rd+tx*self.feert),mn/tx),sd==1)
  if q==0.0: return
  s.pm=(eng,sd,sx,None if trl else self._rp(s.sym,tx+sd*tpr*rd),rd,trl,s.i5+(20 if eng=="SMC_Sweep_V6" else 8),br,bf,lk1,br2,bf2,lk2,sllk,pyr)
  tk=self.market_order(s.sym,q,tag=eng) if mkt else self.limit_order(s.sym,q,tx,tag=eng)
  if tk.status!=OrderStatus.INVALID and s.pm: s.ptk=tk
  else: s.pm=s.ptk=None

 def _pros(self,sd,s,ep,rd,sc,ref,rv,href=False,mcv=0.55):
  if sd!=s.sw4.tr and s.ker4>0.45 and ((s.dir4==-sd and s.br4>=0.55) or s.sw4.tr==-sd): return False,0.0
  bw=max([0.0]+[(3.0-((w-ep)*sd)/rd)/3.0 for _,w in (s.sw1.ah[-6:] if sd==1 else s.sw1.al[-6:]) if rd>0 and 0<((w-ep)*sd)/rd<3.0])
  pdh,pdl,pwh,pwl,_,_,_,_,pt,lt_c=ref
  for rw in (([pdh] if pdh and pt<=1 else [])+([pwh] if pwh else []) if sd==1 else ([pdl] if pdl and lt_c<=1 else [])+([pwl] if pwl else [])):
   r=((rw-ep)*sd)/max(rd,1e-12)
   if 0<r<2.2:
    bw=max(bw,(2.2-r)/2.2)
    if sd!=s.sw4.tr or href: return False,0.0
  ws={"sw":1.1,"dp":1.2,"vc":1.0,"k4":1.0,"rv":0.7}
  num=sum(ws[k]*math.log(max(1e-4,min(1-1e-4,sc[k]))/(1-max(1e-4,min(1-1e-4,sc[k])))) for k in sc if k in ws)
  den=sum(ws[k] for k in sc if k in ws); pc=0.85*bw+(0.65 if sd!=s.sw4.tr and s.ker4>0.35 else 0.0)+(0.25 if rv<0.85 else 0.0)
  cv=_sig(2.4*(num/den if den else 0.0)-2.6*pc-0.35); return cv>=mcv,cv

 def _on4h(self,s,b):
  s.i4+=1; o,h,l,c=float(b.Open),float(b.High),float(b.Low),float(b.Close); a4=s.a4.upd(h,l,c)
  s.ker4=_ker(list(s.c4)[-19:]+[c]) if len(s.c4)>=19 else 0.0; s.br4,s.dir4=abs(c-o)/max(h-l,1e-12),(1 if c>o else -1)
  if s.in_pos and s.trl and a4>0 and s.sltk:
   s.best=max(s.best,h) if s.sd==1 else min(s.best,l); mfe=((s.best-s.ep)*s.sd)/max(s.rd,1e-12); op=((c-s.ep)*s.sd)/max(s.rd,1e-12)
   if s.pst==0 and mfe>=2.0: s.parm=True; self._rpl(s,s.ep+s.sd*0.35*s.rd,c)
   tm=2.0 if op>=14.0 else (s.trl-((op-10.0)/4.0)*(s.trl-2.0) if op>=10.0 else s.trl)
   self._rpl(s,(s.best-tm*a4) if s.sd==1 else (s.best+tm*a4),c)
   if s.parm and s.pst==0 and s.p4c and ((s.sd==1 and l<=s.p4c and c>o and c>s.ep) or (s.sd==-1 and h>=s.p4c and c<o and c<s.ep)):
    self._sub(s,"4H_V6_Cognitive",s.sd,c,c-s.sd*1.5*a4,0,True,True,s.trl,mult=0.50,pyr=1)
   elif s.pst==1 and op>=4.2 and s.ker4>0.40 and s.p4c and ((s.sd==1 and c>o and c>max(s.p4c,s.p4o or s.p4c)) or (s.sd==-1 and c<o and c<min(s.p4c,s.p4o or s.p4c))):
    self._rpl(s,s.ep+s.sd*2.0*s.rd,c); self._sub(s,"4H_V6_Cognitive",s.sd,c,c-s.sd*1.4*a4,0,True,True,s.trl,mult=0.35,pyr=2)
  t1d=1 if (s.e20d.v and s.e50d.v and s.e20d.v>s.e50d.v) else (-1 if (s.e20d.v and s.e50d.v) else 0)
  hn,ln=(max(s.dh4) if len(s.dh4)==20 else None),(min(s.dl4) if len(s.dl4)==20 else None)
  if not self.is_warming_up and not s.in_pos and a4>0 and s.i4>=s.cd4 and s.p4c and t1d and hn:
   sd=1 if (t1d==1 and c>hn and s.p4c<=s.p4h) else (-1 if (t1d==-1 and c<ln and s.p4c>=s.p4l) else 0)
   if sd and s.ker4>=0.25 and s.br4>=0.45 and self._btc_ok(s,sd): self._sub(s,"4H_V6_Cognitive",sd,c,c-sd*1.75*a4,0,True,True,3.5)
  s.p4o,s.p4c,s.p4h,s.p4l=o,c,hn,ln; s.dh4.append(h); s.dl4.append(l); s.c4.append(c); s.t4.upd(h,l,c,a4); s.sw4.upd(h,l,c,a4)

 def _on1h(self,s,b):
  h,l,c=float(b.High),float(b.Low),float(b.Close); a1=s.a1.upd(h,l,c)
  for cd in s.ck3:
   if (cd[0]==1 and c<cd[2]) or (cd[0]==-1 and c>cd[2]): cd[4]+=1
  for isw,pl in list(s.k3.al):
   if s.k3.i+1-isw>=4 and l<pl and c>pl: s.ck3.append([1,s.i5,l,s.sw5.lh,0])
  for isw,ph in list(s.k3.ah):
   if s.k3.i+1-isw>=4 and h>ph and c<ph: s.ck3.append([-1,s.i5,h,s.sw5.ll,0])
  s.c1h=[x for x in s.c1h if s.i5-x[1]<=60][-10:]
  for _,pl,pr in s.t1.al:
   if pr>=1.20 and l<pl and c>pl: s.c1h.append((1,s.i5,l))
  for _,ph,pr in s.t1.ah:
   if pr>=1.20 and h>ph and c<ph: s.c1h.append((-1,s.i5,h))
  s.t1.upd(h,l,c,a1); s.sw1.upd(h,l,c,a1); s.k3.upd(h,l)

 def _clean(self,s):
  for tk in (s.sltk,s.tptk):
   if tk and tk.status not in (OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.INVALID): s.cids.add(tk.order_id); tk.cancel()
  s.sltk=s.tptk=None

 def _rpl(self,s,nsl,c):
  lp=self._rp(s.sym,nsl)
  if (s.sd==1 and lp>=c) or (s.sd==-1 and lp<=c): self._clean(s); self.liquidate(s.sym,tag=f"{s.eng}_TRAIL_MKT"); self._reset(s); return False
  if (s.sd==1 and lp>s.sl) or (s.sd==-1 and lp<s.sl):
   self._clean(s); s.sl=lp; s.sltk=self.stop_market_order(s.sym,-s.qty,lp,tag=f"{s.eng}_SL")
   if s.tp: s.tptk=self.limit_order(s.sym,-s.qty,s.tp,tag=f"{s.eng}_TP")
  return True

 def _bank(self,s,fr,rr,lk,tag,c):
  pq=self._rq(s.sym,min(abs(s.qty),s.iqty*fr),s.sd==1); rq=self._rq(s.sym,abs(s.qty)-abs(pq),s.sd==1)
  if abs(pq)>0 and abs(rq)>0: s.partk=self.market_order(s.sym,-pq,tag=f"{s.eng}_{tag}"); s.qty=rq; self.rpnl+=fr*(rr-(s.ep*self.feert)/s.rd)
  return self._rpl(s,s.ep+s.sd*lk*s.rd,c)

 def _on5m(self,s,b):
  s.i5+=1; dt,o,h,l,c,v=self.utc_time,float(b.Open),float(b.High),float(b.Low),float(b.Close),float(getattr(b,"Volume",0.0) or 0.0)
  a5=s.a5.upd(h,l,c); s.v5.append(v); s.b5.append((o,h,l,c)); ref=s.ref.upd(dt,h,l,c,a5)
  if s.ld!=dt.date(): s.ld,s.lh,s.ll,s.lsw=dt.date(),None,None,[False,False]
  if 7<=dt.hour<12: s.lh=h if s.lh is None else max(s.lh,h); s.ll=l if s.ll is None else min(s.ll,l)
  s.clon=[x for x in s.clon if s.i5-x[1]<=60][-6:]
  if dt.hour>=12 and s.ll and not s.lsw[0] and l<s.ll and c>s.ll: s.lsw[0]=True; s.clon.append((1,s.i5,l))
  if dt.hour>=12 and s.lh and not s.lsw[1] and h>s.lh and c<s.lh: s.lsw[1]=True; s.clon.append((-1,s.i5,h))
  if s.in_pos and s.rd>0 and s.sltk and not s.trl:
   if (s.sd==1 and l<=s.sl) or (s.sd==-1 and h>=s.sl): self._clean(s); self.liquidate(s.sym,tag=f"{s.eng}_SL_EXIT"); self._reset(s); return
   s.best=max(s.best,h) if s.sd==1 else min(s.best,l); mfe=((s.best-s.ep)*s.sd)/s.rd
   if s.bf>0 and not s.t1ok and mfe>=s.br:
    s.t1ok=True
    if not self._bank(s,s.bf,s.br,s.lk1,"BANK40_T1",c): return
   if s.bf2>0 and s.t1ok and not s.t2ok and mfe>=s.br2:
    s.t2ok=True
    if not self._bank(s,s.bf2,s.br2,s.lk2,"BANK40_T2",c): return
   if s.t2ok and mfe>=4.5:
    cand=(s.t15.al[-1][1] if s.t15.al else s.t15.ll) if s.sd==1 else (s.t15.ah[-1][1] if s.t15.ah else s.t15.lh)
    if cand and ((s.sd==1 and cand<l) or (s.sd==-1 and cand>h)): self._rpl(s,cand,c)
   for ar,lkr in s.sllk:
    if (h>=s.ep+ar*s.rd if s.sd==1 else l<=s.ep-ar*s.rd) and not self._rpl(s,s.ep+s.sd*lkr*s.rd,c): return
  if s.ptk and s.pm and (s.i5>s.pm[6] or (l<=s.pm[2] if s.pm[1]==1 else h>=s.pm[2])):
   if s.ptk.status not in (OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.INVALID): s.ptk.cancel()
   s.ptk=s.pm=None
  if not self.is_warming_up and a5>0 and s.ker4>=0.15 and len(s.b5)>=30 and self._can(s):
   rv5=v/(sum(s.v5)/len(s.v5)) if s.v5 else 1.0; bars=list(s.b5); b1,b2=bars[-3],bars[-2]; tol=0.35*a5
   b_hi,b_lo=[x[1] for x in s.sw1.ah[-8:]],[x[1] for x in s.sw1.al[-8:]]
   pdh,pdl,pwh,pwl,ash,asl,loh,lol,pt,lt_c=ref
   r_hi=[x for x,ok in ((pdh,pt<=2),(pwh,True),(ash,True),(loh,True)) if ok and x]
   r_lo=[x for x,ok in ((pdl,lt_c<=2),(pwl,True),(asl,True),(lol,True)) if ok and x]
   v_hi=[p for i,p in enumerate(b_hi) if any(i!=j and 1e-6<abs(p-q)<=tol for j,q in enumerate(b_hi)) or any(abs(p-r)<=tol for r in r_hi)]+r_hi
   v_lo=[p for i,p in enumerate(b_lo) if any(i!=j and 1e-6<abs(p-q)<=tol for j,q in enumerate(b_lo)) or any(abs(p-r)<=tol for r in r_lo)]+r_lo
   sig=None
   if abs(c-o)>=1.05*a5 and s.sw4.tr:
    sd=s.sw4.tr; sx=min(x[2] for x in bars[-6:]) if sd==1 else max(x[1] for x in bars[-6:])
    if ((c>max(x[1] for x in bars[-6:-1])) if sd==1 else (c<min(x[2] for x in bars[-6:-1]))) and any(((sx<lv<c) if sd==1 else (c<lv<sx)) for lv in (v_lo if sd==1 else v_hi)):
     sig=("V10_CompVacuum",sd,(sx-a5) if sd==1 else (sx+a5),0.72,True)
   if not sig and s.sw4.tr and s.sw4.tr==s.sw1.tr and abs(b2[3]-b2[0])>=1.2*a5:
    sd=s.sw4.tr; sx=min(x[2] for x in bars[-12:]) if sd==1 else max(x[1] for x in bars[-12:])
    if (sd==1 and c>b1[1] and l-b1[1]>=0.12*a5 and any(sx<lv<b2[3] for lv in b_lo)) or (sd==-1 and c<b1[2] and b1[2]-h>=0.12*a5 and any(b2[3]<lv<sx for lv in b_hi)):
     sig=("V10_BPR_Snap",sd,(sx-a5) if sd==1 else (sx+a5),0.78,False)
   if sig and 0.0045<=abs(c-sig[2])/c<=0.0180 and rv5>=0.90 and self._btc_ok(s,sig[1]):
    ok_p,cv=self._pros(sig[1],s,c,abs(c-sig[2]),{"sw":0.72,"dp":_sig(abs(c-o)/a5,1.2,2.2),"vc":sig[3],"k4":_sig(s.ker4,0.25,9.0),"rv":_sig(rv5,1.3,2.0)},ref,rv5,href=sig[4])
    if ok_p: self._sub(s,sig[0],sig[1],c,sig[2],10.0,False,sig[0]=="V10_BPR_Snap" or cv>=0.72); s.t5.upd(h,l,c,a5); s.sw5.upd(h,l,c,a5); return
   if abs(b2[3]-b2[0])>=1.15*a5:
    for tag,cl,ok_h,is_ap,bc in (("V11_SessEq_1H_TOPO",s.c1h,dt.hour>=9 and rv5>=1.10,True,(1.8,0.50,0.25,3.2,0.35,1.25,6.5)),("V9_LON",s.clon,dt.hour>=12 and rv5>=1.15,False,(2.2,0.45,0.35,4.5,0.40,2.00,10.0))):
     if not ok_h: continue
     for sd,_,sl_b in reversed(cl):
      if sd==s.t1.tr==s.t4.tr and s.i5-s.lv9[sd]>=12 and self._btc_ok(s,sd):
       if sd==1 and l>=sl_b and s.t5.lh and c>s.t5.lh and l-b1[1]>=0.30*a5 and b2[3]>b2[0]: s.lv9[sd]=s.i5; self._sub(s,tag,1,l,min(sl_b-a5,c-max(1.5*a5,c*0.002)),bc[6],False,is_ap,None,*bc[:6]); break
       if sd==-1 and h<=sl_b and s.t5.ll and c<s.t5.ll and b1[2]-h>=0.30*a5 and b2[3]<b2[0]: s.lv9[sd]=s.i5; self._sub(s,tag,-1,h,max(sl_b+a5,c+max(1.5*a5,c*0.002)),bc[6],False,is_ap,None,*bc[:6]); break
   s.ck3=[x for x in s.ck3 if s.i5-x[1]<=60 and ((x[0]==1 and l>=x[2]) or (x[0]==-1 and h<=x[2]))]
   if dt.hour>=9 and abs(b2[3]-b2[0])>=a5 and s.ck3:
    for sd,_,sl_b,ch,ba in reversed(s.ck3):
     if ba<=1 and sd==s.sw4.tr==s.sw1.tr and ch and self._btc_ok(s,sd):
      slp=min(sl_b-a5,c-max(1.5*a5,c*0.002)) if (sd==1 and c>ch and l-b1[1]>=0.25*a5 and b2[3]>b2[0]) else (max(sl_b+a5,c+max(1.5*a5,c*0.002)) if (sd==-1 and c<ch and b1[2]-h>=0.25*a5 and b2[3]<b2[0]) else None)
      if slp and self._pros(sd,s,c,abs(c-slp),{"sw":0.65,"dp":_sig(abs(b2[3]-b2[0])/a5,1.2,2.2),"k4":_sig(s.ker4,0.25,9.0),"rv":_sig(rv5,1.6,2.2)},ref,rv5,mcv=0.35)[0]:
       self._sub(s,"SMC_Sweep_V6",sd,c,slp,10.0,False,True,None,0.0,0.0,0.0,0.0,0.0,0.0,((3.0,1.0),)); break
  s.t5.upd(h,l,c,a5); s.sw5.upd(h,l,c,a5)

 def on_order_event(self,oe):
  if oe.symbol not in self.coins: return
  s=self.coins[oe.symbol]
  if oe.order_id in s.cids and oe.status==OrderStatus.CANCELED: s.cids.discard(oe.order_id); return
  if oe.status in (OrderStatus.INVALID,OrderStatus.CANCELED) and s.ptk and oe.order_id==s.ptk.order_id: s.ptk=s.pm=None; return
  if oe.status!=OrderStatus.FILLED or (s.partk and oe.order_id==s.partk.order_id):
   if s.partk and oe.order_id==s.partk.order_id: s.partk=None
   return
  if s.pm and not s.in_pos and abs(float(oe.fill_quantity))>0:
   pm=s.pm; s.ptk=s.pm=None; s.in_pos=True
   s.eng,s.sd,s.sl,s.tp,s.rd,s.trl=pm[0],pm[1],pm[2],pm[3],pm[4],pm[5]
   s.br,s.bf,s.lk1,s.br2,s.bf2,s.lk2,s.sllk=pm[7],pm[8],pm[9],pm[10],pm[11],pm[12],pm[13]
   s.ep=s.best=float(oe.fill_price); s.qty=float(oe.fill_quantity); s.iqty=abs(s.qty)
   s.t1ok=s.t2ok=s.parm=False; s.pst=0
   s.sltk=self.stop_market_order(s.sym,-s.qty,s.sl,tag=f"{s.eng}_SL")
   if s.tp: s.tptk=self.limit_order(s.sym,-s.qty,s.tp,tag=f"{s.eng}_TP")
  elif s.pm and s.in_pos and s.pm[14]>0:
   pm=s.pm; s.ptk=s.pm=None; s.pst=pm[14]; s.qty+=float(oe.fill_quantity); self._rpl(s,pm[2],float(oe.fill_price))
  elif s.in_pos:
   rf=max(0.0,1.0-(s.bf if s.t1ok else 0.0)-(s.bf2 if s.t2ok else 0.0))
   self.rpnl+=rf*(((float(oe.fill_price)-s.ep)*s.sd)/max(s.rd,1e-12)); self._clean(s)
   if self.portfolio[s.sym].invested: self.liquidate(s.sym,tag="RESIDUAL_CLOSE")
   s.cd5,s.cd4=s.i5+4,s.i4+1; self._reset(s); ae=self._ae()
   if self.small and ae>=self.skanc+self.skstep: sk=(ae-self.skanc)*0.50; self.vault+=sk; ae-=sk; self.skanc=self.hwm=ae
   elif ae>self.hwm: self.hwm=ae

 @staticmethod
 def _reset(s):
  s.in_pos=s.t1ok=s.t2ok=s.parm=False; s.pst=s.sd=0; s.sllk=()
  s.eng=s.tp=s.trl=s.sltk=s.tptk=s.partk=None; s.ep=s.sl=s.rd=s.qty=s.iqty=s.best=0.0
