_j='expire_idx';_i='Volume';_h='AMD_Pro';_g='NSX_VisB_Chop';_f='NSX_AMD_1D';_e='VisB_Pro';_d='V9_Countertrend';_c='expire_15m_idx';_b='step_locks';_a='V3_Pro_Clean';_Z='V9_Profile';_Y='VALID';_X='NOT_REQUIRED';_W='qty';_V='touched';_U='trail_after_r';_T='BTC_15R_BE';_S='extreme';_R='skip_hours';_Q='tp';_P='trig';_O='engine';_N='id';_M='created';_L='sl';_K='choch';_J='sl_base';_I='start_i';_H=1.;_G=True;_F='high';_E='low';_D=False;_C=.0;_B='side';_A=None;from AlgorithmImports import*;from collections import defaultdict,deque;import math
class C:
	def __init__(self,k=2,max_active=30):self.k=k;self.max_active=max_active;self.win=deque(maxlen=2*k+1);self.bar_idx=-1;self.last_high=_A;self.last_low=_A;self.last_high_point=_A;self.last_low_point=_A;self.trend=0;self.act_hi=[];self.act_lo=[]
	def update_hlc(self,h,l,c):
		self.bar_idx+=1;self.win.append((h,l));nh=nl=_A
		if len(self.win)==2*self.k+1:
			m=self.k;ch,cl=self.win[m][0],self.win[m][1]
			if all(ch>=self.win[i][0]for i in range(len(self.win))if i!=m)and any(ch>self.win[i][0]for i in range(len(self.win))if i!=m):
				nh=self.bar_idx-self.k,ch;self.last_high=ch;self.last_high_point=nh;self.act_hi.append(nh)
				if len(self.act_hi)>self.max_active:self.act_hi.pop(0)
			if all(cl<=self.win[i][1]for i in range(len(self.win))if i!=m)and any(cl<self.win[i][1]for i in range(len(self.win))if i!=m):
				nl=self.bar_idx-self.k,cl;self.last_low=cl;self.last_low_point=nl;self.act_lo.append(nl)
				if len(self.act_lo)>self.max_active:self.act_lo.pop(0)
		self.act_hi=[x for x in self.act_hi if h<=x[1]];self.act_lo=[x for x in self.act_lo if l>=x[1]]
		if self.last_high is not _A and c>self.last_high:self.trend=1
		elif self.last_low is not _A and c<self.last_low:self.trend=-1
		return nh,nl
	def update(self,bar):return self.update_hlc(float(bar.High),float(bar.Low),float(bar.Close))
class W:
	def __init__(self):self.prev_close=_A;self.trs=[];self.val=_C
	def update(self,h,l,c):
		tr=h-l if self.prev_close is _A else max(h-l,abs(h-self.prev_close),abs(l-self.prev_close));self.prev_close=c
		if len(self.trs)<14:self.trs.append(tr);self.val=sum(self.trs)/len(self.trs)
		else:self.val=(self.val*13.+tr)/14.
		return self.val
class F:
	def __init__(self,maxlen=20):self.cumulative=_A;self.history=deque(maxlen=maxlen);self.gap=_D
	def status(self,delta,side,required):
		B='DIVERGENT';A='UNKNOWN'
		if delta is _A:return A if required else _X
		if self.gap or self.cumulative is _A or len(self.history)==0:return A if required else _X
		candidate=self.cumulative+float(delta)
		if side==1:return _Y if delta>0 and candidate>max(self.history)else B
		return _Y if delta<0 and candidate<min(self.history)else B
	def commit(self,delta):
		if delta is _A:self.gap=_G;return
		self.cumulative=float(delta)if self.cumulative is _A else self.cumulative+float(delta);self.history.append(self.cumulative);self.gap=_D
class S:
	def __init__(self,name,symbol,leverage):self.name,self.symbol,self.leverage=name,symbol,leverage;self.sw_1d,self.sw_4h=C(2),C(2);self.sw_1h,self.sw_1h_k3=C(2),C(3);self.sw_15m,self.sw_5m,self.sw_ltf=C(2),C(2),C(2);self.a15,self.a5,self.al=W(),W(),W();self.b15,self.b5,self.bltf=deque(maxlen=140),deque(maxlen=15),deque(maxlen=5);self.c5,self.cltf,self.am=[],[],[];self.vh=deque(maxlen=100);self.fl=F(20);self.vb=deque(maxlen=180);self.vbo=deque(maxlen=180);self.vf,self.vo,self.vs=[],[],[];self.zq=0;self.bh=_A;self.bl=_A;self.pe=self.ab=self.cv=0;self.b4,self.o4=_A,_A;self.d1,self.o1=_A,_A;self.dc,self.de,self.dr,self.dl=deque(maxlen=20),_A,_C,_C;self.pt=self.pm=self.cs=_A;self.ip,self.ae,self.ax=_D,_A,0;self.ep=self.sp=self.rd=self.qty=_C;self.tpv=self.tr=self.tm=_A;self.lk,self.ta=(),_D;self.stx=self.tt=_A;self.v9_idx=0;self.li=self.i5=self.i15=self.bs=self.os=0
class V9DynamicProfile3AssetAlgorithm(QCAlgorithm):
	ENGINE_RISK={_Z:.01,_d:.005,_e:.015,_a:.015,_T:.015,_f:.01,_g:.01,_h:.008};BTC_STEPS=(3.,_H),(5.5,2.5),(8.5,5.5),(11.5,8.5)
	def initialize(self):
		C='BTCUSD';B='NAS100USD';A='XAUUSD';self.set_time_zone(TimeZones.UTC);self.set_start_date(2020,2,1);self.set_end_date(2026,10,31);self.set_cash(100000);self.rk=float(self.get_parameter('risk_scale')or _H);self.ua=bool(int(self.get_parameter('use_amd_pro')or 0));self.e9=bool(int(self.get_parameter('enable_v9_profiles')or 1));self.rs=bool(int(self.get_parameter('v9_require_spot_cvd')or 1));self.up=bool(int(self.get_parameter('v9_use_ohlcv_proxy')or 0));self.rf=bool(int(self.get_parameter('v9_require_cool_funding')or 0));self.vz=float(self.get_parameter('v9_volume_z_threshold')or 2.5);self.at=float(self.get_parameter('v9_adi_threshold')or 3.);self.mr=float(self.get_parameter('v9_min_rr')or 5.);self.ma=int(self.get_parameter('v9_max_sweep_age')or 32);self.ms=float(self.get_parameter('v9_min_speed_ratio')or 2.);self.md=float(self.get_parameter('v9_min_distance_atr')or _H);self.xb=int(self.get_parameter('v9_pending_expiry_bars')or 20);self.ts=float(self.get_parameter('v9_tick_size')or .01);self.hw=1e5;self.set_warm_up(timedelta(days=30),Resolution.MINUTE);self.set_brokerage_model(DefaultBrokerageModel(AccountType.MARGIN));xau=self.add_cfd(A,Resolution.MINUTE,Market.OANDA,leverage=50);nsx=self.add_cfd(B,Resolution.MINUTE,Market.OANDA,leverage=50);btc=self.add_crypto(C,Resolution.MINUTE,Market.COINBASE,leverage=25);btc.set_buying_power_model(SecurityMarginModel(25.));self.xs,self.ns,self.bt=xau.symbol,nsx.symbol,btc.symbol;self.assets={self.xs:S(A,self.xs,5e1),self.ns:S(B,self.ns,5e1),self.bt:S(C,self.bt,25.)};self.tc,self.ic=defaultdict(int),defaultdict(int);self.oc=0
		for(sym,st)in self.assets.items():self.consolidate(sym,timedelta(hours=1),lambda b,s=st:self.on_1h(s,b));self.consolidate(sym,timedelta(minutes=15),lambda b,s=st:self.on_15m(s,b));self.consolidate(sym,timedelta(minutes=5),lambda b,s=st:self.on_5m(s,b))
	@staticmethod
	def _in_kz(dt):return 7<=dt.hour<=10 or 12<=dt.hour<=16
	@staticmethod
	def _in_ny(dt):return 12<=dt.hour<17
	def _cfd_blocked(self,st,dt):
		if st.symbol==self.bt:return _D
		if dt.hour>=20 or dt.hour<1:return _G
		if st.symbol==self.xs and dt.weekday()==4 and dt.hour>=18:return _G
		return _D
	@staticmethod
	def _bar(data,sym):
		if sym in data.quote_bars:return data.quote_bars[sym]
		return data.bars[sym]if sym in data.bars else _A
	def _effective_risk_pct(self,engine):eq=float(self.portfolio.total_portfolio_value);dd=(self.hw-eq)/self.hw if self.hw>0 else _C;brake=.4 if dd>=.12 else .6 if dd>=.08 else _H;return self.ENGINE_RISK.get(engine,.01)*brake*self.rk
	def _round_qty(self,sym,raw_qty,is_long):
		sp=self.securities[sym].symbol_properties;lot=float(sp.lot_size or .001);min_sz=float(sp.minimum_order_size or lot);qty=round(math.floor(abs(raw_qty)/lot)*lot,8)
		if qty<min_sz:return _C
		return qty if is_long else-qty
	def _round_px(self,sym,price):tick=float(self.securities[sym].symbol_properties.minimum_price_variation or .01);tick=tick if tick>0 else .01;return round(round(price/tick)*tick,6)
	@staticmethod
	def _v9_volume_z(st,current_volume):
		history=list(st.vh)
		if len(history)<100:return
		mean=sum(history)/len(history);variance=sum((x-mean)**2 for x in history)/len(history);std=math.sqrt(variance)
		if std<=0:
			if current_volume>mean:return float('inf')
			if current_volume<mean:return float('-inf')
			return _C
		return(current_volume-mean)/std
	def _v9_flow_delta(self,bar):
		if not self.up:return
		volume=float(getattr(bar,_i,_C)or _C);high,low,close=float(bar.High),float(bar.Low),float(bar.Close)
		if volume<=0 or high<=low:return
		location=(2.*close-high-low)/(high-low);return volume*location
	def _v9_funding_ok(self):return not self.rf
	@staticmethod
	def _v9_latest_level(tracker,side):
		point=tracker.last_high_point if side==-1 else tracker.last_low_point
		if point is not _A:return point
		price=tracker.last_high if side==-1 else tracker.last_low;return(tracker.bar_idx,price)if price is not _A else _A
	def _v9_new_fvg(self,st):
		if len(st.vb)<3:return
		b1,_,b3=list(st.vb)[-3:]
		if b3[4]>b1[3]:zone={_N:st.zq,_B:1,_E:b1[3],_F:b3[4],_M:b3[0]}
		elif b3[3]<b1[4]:zone={_N:st.zq,_B:-1,_E:b3[3],_F:b1[4],_M:b3[0]}
		else:return
		st.zq+=1;st.vf.append(zone);st.vf=st.vf[-80:];return zone
	def _v9_new_ob(self,st,side,source_event,origin_idx,current_idx):
		prior=[b for b in st.vb if origin_idx<=b[0]<current_idx];opposite=[b for b in prior if(b[5]<b[2]if side==1 else b[5]>b[2])]
		if not opposite:return
		b=opposite[-1];zone={_N:st.zq,_B:side,'source':source_event,'origin':b[0],_M:current_idx,_E:b[4],_F:b[3]};st.zq+=1;st.vo.append(zone);st.vo=st.vo[-80:];return zone
	@staticmethod
	def _v9_zone_touched(st,zone):
		if not st.vb or st.vb[0][0]>zone[_M]:return _G
		for b in st.vb:
			if b[0]<=zone[_M]:continue
			if b[3]>=zone[_E]and b[4]<=zone[_F]:return _G
		return _D
	def _v9_flow_ok(self,flow_status):return flow_status==_Y or not self.rs and flow_status==_X
	def _v9_target(self,st,side,entry,current_fvg_id=_A):
		candidates=[]
		for zone in st.vf:
			if zone[_N]==current_fvg_id or zone[_B]==side:continue
			if side==1 and zone[_F]<=entry or side==-1 and zone[_E]>=entry:continue
			if self._v9_zone_touched(st,zone):continue
			target=zone[_E]if side==1 and zone[_E]>entry else zone[_F]if side==1 else zone[_F]if zone[_F]<entry else zone[_E];candidates.append((abs(target-entry),zone[_M],target,zone[_N],_A))
		for zone in st.vo:
			if zone[_B]==side:continue
			if side==1 and zone[_F]<=entry or side==-1 and zone[_E]>=entry:continue
			if self._v9_zone_touched(st,zone):continue
			target=zone[_E]if side==1 and zone[_E]>entry else zone[_F]if side==1 else zone[_F]if zone[_F]<entry else zone[_E];candidates.append((abs(target-entry),zone[_M],target,_A,zone[_N]))
		if not candidates:return _A,_A,_A
		_,_,target,fvg_id,ob_id=min(candidates,key=lambda x:(x[0],x[1]));return target,fvg_id,ob_id
	def _v9_deep_ob(self,st,side,origin,termination,current_price):
		move=abs(termination-origin)
		if move<=0:return
		valid=[]
		for zone in st.vo:
			if zone[_B]!=side or self._v9_zone_touched(st,zone):continue
			if side==1:
				if zone[_F]>=current_price:continue
				r_lo=(termination-zone[_F])/move;r_hi=(termination-zone[_E])/move
			else:
				if zone[_E]<=current_price:continue
				r_lo=(zone[_E]-termination)/move;r_hi=(zone[_F]-termination)/move
			if r_hi>=.705 and r_lo<=.79:valid.append(zone)
		return max(valid,key=lambda z:z[_M])if valid else _A
	def _v9_speed_ratio(self,st,sweep_idx,current_idx):
		up=[x[2]-x[1]for x in st.vbo if sweep_idx<x[0]<=current_idx and x[2]>x[1]];down=[x[1]-x[2]for x in st.vbo if sweep_idx-12<=x[0]<sweep_idx and x[2]<x[1]]
		if not up or not down:return
		return sum(up)/len(up)/(sum(down)/len(down))
	def _v9_recent_sweep(self,st,side,current_idx):candidates=[s for s in st.vs if s[_B]==side and 0<=current_idx-s[_I]<=self.ma];return max(candidates,key=lambda x:x[_I])if candidates else _A
	def _v9_submit_plan(self,st,engine,side,entry,stop,target,current_idx,reason):
		if target is _A:return _D
		entry=self._round_px(st.symbol,entry);stop=self._round_px(st.symbol,stop);target=self._round_px(st.symbol,target);risk=entry-stop if side==1 else stop-entry
		if risk<=0:return _D
		rr=(target-entry)/risk if side==1 else(entry-target)/risk
		if rr<self.mr:return _D
		self._submit_entry(st,engine,side,entry,stop,tp=target,tr=2.,lk=((2.,_H),(3.,1.5)),expire_bars=self.xb,min_risk=_C,is_market=_D,require_confirm=_D,apply_floor=_D,expire_on_15m=_G)
		if st.pm is not _A:st.pm['v9_reason']=reason;st.pm['v9_plan_index']=current_idx;st.pm['v9_planned_rr']=rr;return _G
		return _D
	def _v9_profile_bar(self,st,bar,atr_before):
		if not self.e9:return
		st.v9_idx+=1;dt=self.utc_time;o,h,l,c=float(bar.Open),float(bar.High),float(bar.Low),float(bar.Close);vol=float(getattr(bar,_i,_C)or _C);st.vb.append((st.i15,dt,o,h,l,c));st.vbo.append((st.i15,o,c));volume_z=self._v9_volume_z(st,vol);current_fvg=self._v9_new_fvg(st);current_idx=st.i15;high_level=st.sw_15m.last_high;low_level=st.sw_15m.last_low;high_point=self._v9_latest_level(st.sw_15m,-1);low_point=self._v9_latest_level(st.sw_15m,1);break_up=high_level is not _A and o>high_level and c>high_level and high_point[0]!=st.bh;break_down=low_level is not _A and o<low_level and c<low_level and low_point[0]!=st.bl
		if break_up and break_down:break_up=break_down=_D
		side=1 if break_up else-1 if break_down else 0
		if side==0:st.vh.append(vol);st.fl.commit(self._v9_flow_delta(bar));return
		level=high_level if side==1 else low_level;point=low_point if side==1 else high_point
		if point is _A or point[1]is _A or atr_before<=0:st.vh.append(vol);st.fl.commit(self._v9_flow_delta(bar));return
		origin_idx,origin_price=point[0]+1,point[1];wave_n=max(1,current_idx-origin_idx+1);move=(c-origin_price)*side;adi=max(_C,move)/(wave_n*atr_before);flow_delta=self._v9_flow_delta(bar);flow_status=st.fl.status(flow_delta,side,self.rs);funding_ok=self._v9_funding_ok();st.pe+=1;is_choch=st.sw_15m.trend==-1 and side==1 or st.sw_15m.trend==1 and side==-1;sweep=self._v9_recent_sweep(st,side,current_idx)if is_choch else _A;speed=self._v9_speed_ratio(st,sweep[_I],current_idx)if sweep is not _A else _A;distance=abs(level-sweep[_S])/atr_before if sweep is not _A else _A;choch_valid=bool(is_choch and sweep is not _A and volume_z is not _A and volume_z>self.vz and speed is not _A and speed>=self.ms and distance is not _A and distance>self.md and self._v9_flow_ok(flow_status)and funding_ok)
		if choch_valid:st.cv+=1
		aggressive=bool(not is_choch and volume_z is not _A and volume_z>self.vz and adi>self.at and self._v9_flow_ok(flow_status)and funding_ok)
		if volume_z is not _A and volume_z>self.vz and adi>self.at and not aggressive:st.ab+=1
		event='CHOCH'if is_choch else'BOS';self._v9_new_ob(st,side,event,origin_idx,current_idx)
		if high_point is not _A and side==1:st.bh=high_point[0]
		if low_point is not _A and side==-1:st.bl=low_point[0]
		if current_fvg is not _A and current_fvg[_B]==side:
			tick=float(self.securities[st.symbol].symbol_properties.minimum_price_variation or self.ts);tick=tick if tick>0 else self.ts;entry=current_fvg[_F]if side==1 else current_fvg[_E];stop=l-tick if side==1 else h+tick;target,_,_=self._v9_target(st,side,entry,current_fvg[_N])
			if aggressive:self._v9_submit_plan(st,_Z,side,entry,stop,target,current_idx,'AGGRESSIVE_SHALLOW_FVG_PROTECTED_IMPULSE_STOP')
			elif choch_valid:stop=sweep[_S]-tick if side==1 else sweep[_S]+tick;self._v9_submit_plan(st,_d,side,entry,stop,target,current_idx,'HTF_SWEEP_BODY_CHOCH_SPEED_DISTANCE_FLOW')
		if volume_z is not _A and not aggressive and not choch_valid:
			deep=self._v9_deep_ob(st,side,origin_price,c,c)
			if deep is not _A:tick=float(self.securities[st.symbol].symbol_properties.minimum_price_variation or self.ts);tick=tick if tick>0 else self.ts;entry=deep[_F]if side==1 else deep[_E];stop=origin_price-tick if side==1 else origin_price+tick;target,_,_=self._v9_target(st,side,entry);self._v9_submit_plan(st,_Z,side,entry,stop,target,current_idx,'DEFENSIVE_DEEP_OB_ORIGIN_STOP')
		st.vh.append(vol);st.fl.commit(flow_delta)
	def _clamp_qty(self,st,raw_qty,px):
		if px<=0:return raw_qty
		max_notional=max(_C,float(self.portfolio.margin_remaining))*st.leverage*.85;return min(abs(raw_qty),max_notional/px)if max_notional>0 else _C
	def _cancel_pending(self,st):
		if st.pt is not _A and st.pt.status not in(OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.INVALID):st.pt.cancel()
		st.pt=st.pm=st.cs=_A
	def _try_lock_sl(self,st,lock_px,cur_c):
		lp=self._round_px(st.symbol,lock_px);sec=self.securities[st.symbol];ref_long=float(getattr(sec,'bid_price',_C)or _C);ref_short=float(getattr(sec,'ask_price',_C)or _C);ref_long=ref_long if ref_long>0 else cur_c;ref_short=ref_short if ref_short>0 else cur_c
		if st.ax==1 and lp>st.sp and lp<ref_long or st.ax==-1 and lp<st.sp and lp>ref_short:st.sp=lp;st.stx.update_stop_price(lp)
	def _floor_sl(self,st,side,trig,sl,min_r,cur_px):
		floor_r=max(min_r,1e-06)
		if st.symbol==self.xs:floor_r=max(floor_r,cur_px*.002)
		if st.a5.val>0:floor_r=max(floor_r,1.5*st.a5.val)
		raw_r=trig-sl if side==1 else sl-trig
		if raw_r<floor_r:sl=trig-floor_r if side==1 else trig+floor_r
		return sl
	def _submit_entry(self,st,engine,side,trig,sl,tp=_A,tr=_A,lk=(),expire_bars=20,min_risk=_C,skip_hours=_A,is_market=_D,require_confirm=_D,apply_floor=_G,expire_on_15m=_D):
		if self.is_warming_up or st.ip or st.pt is not _A or st.cs is not _A:return
		if not self.is_market_open(st.symbol)or self._cfd_blocked(st,self.utc_time):return
		if self.portfolio[st.symbol].invested:self.transactions.cancel_open_orders(st.symbol);self.liquidate(st.symbol,tag='PRE_ENTRY_SYNC');self.oc+=1;return
		cur_px=float(self.securities[st.symbol].price)
		if cur_px<=0:return
		trig_px=cur_px if is_market else self._round_px(st.symbol,trig)
		if apply_floor:sl=self._floor_sl(st,side,trig_px,sl,min_risk,cur_px)
		sl_px=self._round_px(st.symbol,sl);risk=trig_px-sl_px if side==1 else sl_px-trig_px
		if risk<=max(min_risk,1e-06):return
		if not is_market and(side==1 and trig_px>cur_px or side==-1 and trig_px<cur_px):return
		if require_confirm and not is_market:st.cs={_O:engine,_B:side,_P:trig_px,_L:sl_px,_Q:self._round_px(st.symbol,tp)if tp is not _A else _A,_U:tr,_b:lk,'exp':st.li+expire_bars,_R:skip_hours,_V:_D};return
		risk_usd=float(self.portfolio.total_portfolio_value)*self._effective_risk_pct(engine);qty=self._round_qty(st.symbol,self._clamp_qty(st,risk_usd/risk,trig_px),side==1)
		if qty==_C:return
		st.pm={_O:engine,_B:side,_P:trig_px,_L:sl_px,_Q:self._round_px(st.symbol,tp)if tp is not _A else _A,'risk':risk,_W:qty,_U:tr,_j:st.li+expire_bars,_c:st.i15+expire_bars if expire_on_15m else _A,_R:skip_hours};st.os+=1;ticket=self.market_order(st.symbol,qty,tag=engine)if is_market else self.limit_order(st.symbol,qty,trig_px,tag=engine)
		if ticket.status==OrderStatus.INVALID:st.pm=st.pt=_A;return
		if st.pm is not _A:st.pt=ticket
	def _push_1d(self,st,h,l,c):
		st.sw_1d.update_hlc(h,l,c);st.dc.append(c);st.dl=c;k=2./21.;st.de=c if st.de is _A else c*k+st.de*(_H-k)
		if len(st.dc)>=15:arr=list(st.dc)[-15:];den=sum(abs(arr[j]-arr[j-1])for j in range(1,len(arr)));st.dr=abs(arr[-1]-arr[0])/den if den>0 else _C
	def _update_utc_htf(self,st,dt,o,h,l,c):
		ref=dt-timedelta(minutes=1);b4_key=ref.date(),ref.hour//4
		if st.b4 is not _A and b4_key!=st.b4 and st.o4 is not _A:st.sw_4h.update_hlc(st.o4[1],st.o4[2],st.o4[3]);st.o4=_A
		if st.o4 is _A:st.o4=o,h,l,c
		else:st.o4=st.o4[0],max(st.o4[1],h),min(st.o4[2],l),c
		st.b4=b4_key
		if dt.hour%4==0 and dt.minute==0:st.sw_4h.update_hlc(st.o4[1],st.o4[2],st.o4[3]);st.o4=_A
		d_key=ref.date()
		if st.d1 is not _A and d_key!=st.d1 and st.o1 is not _A:self._push_1d(st,st.o1[1],st.o1[2],st.o1[3]);st.o1=_A
		if st.o1 is _A:st.o1=o,h,l,c
		else:st.o1=st.o1[0],max(st.o1[1],h),min(st.o1[2],l),c
		st.d1=d_key
		if dt.hour==0 and dt.minute==0:self._push_1d(st,st.o1[1],st.o1[2],st.o1[3]);st.o1=_A
	def on_1h(self,st,bar):
		A='level';h,l,c,o=float(bar.High),float(bar.Low),float(bar.Close),float(bar.Open);self._update_utc_htf(st,self.utc_time,o,h,l,c);k3=st.sw_1h_k3
		for(idx_s,p_lo)in list(k3.act_lo):
			if k3.bar_idx+1-idx_s>=4 and l<p_lo and c>p_lo:
				if self.e9:st.vs.append({_B:1,_I:st.i15,A:p_lo,_S:l});st.vs=st.vs[-30:]
				if st.symbol==self.xs or st.symbol==self.ns and st.dr<.25:st.c5.append({_B:1,_I:st.i5,_J:l,_K:st.sw_5m.last_high})
				elif st.symbol==self.bt:st.cltf.append({_B:1,_I:st.li,_J:l,_K:st.sw_ltf.last_high})
		for(idx_s,p_hi)in list(k3.act_hi):
			if k3.bar_idx+1-idx_s>=4 and h>p_hi and c<p_hi:
				if self.e9:st.vs.append({_B:-1,_I:st.i15,A:p_hi,_S:h});st.vs=st.vs[-30:]
				if st.symbol==self.xs or st.symbol==self.ns and st.dr<.25:st.c5.append({_B:-1,_I:st.i5,_J:h,_K:st.sw_5m.last_low})
				elif st.symbol==self.bt:st.cltf.append({_B:-1,_I:st.li,_J:h,_K:st.sw_ltf.last_low})
		nh,nl=st.sw_1h.update(bar);st.sw_1h_k3.update(bar)
		if st.ip and st.ta and st.tm=='1h'and st.stx is not _A:
			if st.stx.status not in(OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.INVALID):
				if st.ax==1 and nl is not _A:self._try_lock_sl(st,max(st.sp,float(nl[1])),c)
				elif st.ax==-1 and nh is not _A:self._try_lock_sl(st,min(st.sp,float(nh[1])),c)
	def on_15m(self,st,bar):
		D='si';C='r_lo';B='r_hi';A='ext';st.i15+=1;dt=self.utc_time;h,l,c,o=float(bar.High),float(bar.Low),float(bar.Close),float(bar.Open);atr_before=st.a15.val;a15=st.a15.update(h,l,c);st.b15.append((dt,o,h,l,c))
		if st.symbol==self.xs and len(st.b15)>=3 and self._in_ny(dt)and dt.hour not in(13,14):
			b1,b2,b3=st.b15[-3],st.b15[-2],st.b15[-1];c2b,buf=abs(b2[4]-b2[1]),max(_H,.75*a15)
			if st.sw_4h.trend==1 and st.sw_1h.trend==1 and st.sw_15m.last_high is not _A:
				bos_up=b2[4]<=st.sw_15m.last_high<b3[4]or b1[4]<=st.sw_15m.last_high<b2[4]
				if bos_up and b3[3]-b1[2]>=max(.2,.3*a15)and b2[4]>b2[1]and c2b>=a15:self._submit_entry(st,_a,1,b3[3],min(b1[3],b2[3])-buf,tr=2.5,expire_bars=300,min_risk=_H,skip_hours=(13,14))
			elif st.sw_4h.trend==-1 and st.sw_1h.trend==-1 and st.sw_15m.last_low is not _A:
				bos_dn=b2[4]>=st.sw_15m.last_low>b3[4]or b1[4]>=st.sw_15m.last_low>b2[4]
				if bos_dn and b1[3]-b3[2]>=max(.2,.3*a15)and b2[4]<b2[1]and c2b>=a15:self._submit_entry(st,_a,-1,b3[2],max(b1[2],b2[2])+buf,tr=2.5,expire_bars=300,min_risk=_H,skip_hours=(13,14))
		run_amd=st.symbol==self.ns or st.symbol==self.xs and self.ua
		if run_amd and len(st.b15)>=10 and a15>0:
			box=list(st.b15)[-9:-1];box_hi,box_lo=max(b[2]for b in box),min(b[3]for b in box)
			if box_hi-box_lo<=2.5*a15:
				if l<box_lo and c>=box_lo-.8*a15:st.am.append({_B:1,B:box_hi,C:box_lo,A:l,D:st.i15})
				if h>box_hi and c<=box_hi+.8*a15:st.am.append({_B:-1,B:box_hi,C:box_lo,A:h,D:st.i15})
			b1,b2,b3=st.b15[-3],st.b15[-2],st.b15[-1];c2b=abs(b2[4]-b2[1]);is_nsx=st.symbol==self.ns;min_r=5. if is_nsx else .5;eng=_f if is_nsx else _h;still=[]
			for mp in st.am:
				if st.i15-mp[D]>8:continue
				if mp[_B]==1:
					mp[A]=min(mp[A],l);ok_1d=not is_nsx or st.sw_1d.trend==1 and st.dr>=.2 and st.de is not _A and st.dl>st.de
					if ok_1d and c>mp[B]and b3[3]-b1[2]>=.25*a15 and b2[4]>b2[1]and c2b>=.8*a15 and st.sw_1h.trend==1 and self._in_kz(dt):self._submit_entry(st,eng,1,b3[3],mp[A]-.5*a15,tr=2.,expire_bars=300,min_risk=min_r,require_confirm=not is_nsx);continue
				else:
					mp[A]=max(mp[A],h);ok_1d=not is_nsx or st.sw_1d.trend==-1 and st.dr>=.2 and st.de is not _A and st.dl<st.de
					if ok_1d and c<mp[C]and b1[3]-b3[2]>=.25*a15 and b2[4]<b2[1]and c2b>=.8*a15 and st.sw_1h.trend==-1 and self._in_kz(dt):self._submit_entry(st,eng,-1,b3[2],mp[A]+.5*a15,tr=2.,expire_bars=300,min_risk=min_r,require_confirm=not is_nsx);continue
				still.append(mp)
			st.am=still
		self._v9_profile_bar(st,bar,atr_before);st.sw_15m.update(bar)
	def on_5m(self,st,bar):
		st.i5+=1;dt=self.utc_time;h,l,c,o=float(bar.High),float(bar.Low),float(bar.Close),float(bar.Open);a5=st.a5.update(h,l,c);st.b5.append((dt,o,h,l,c));is_xau=st.symbol==self.xs;is_nsx_chop=st.symbol==self.ns and st.dr<.25
		if(is_xau or is_nsx_chop)and len(st.b5)>=3 and self._in_kz(dt):
			b1,b2,b3=st.b5[-3],st.b5[-2],st.b5[-1];c2b=abs(b2[4]-b2[1]);buf=max(_H if is_xau else 4.,.5*a5);min_fvg=max(.2,.2*a5)if is_xau else .2*a5;v_eng=_e if is_xau else _g;v_min_r=_H if is_xau else 5.;still=[]
			for sc in st.c5:
				if st.i5-sc[_I]>12:continue
				if sc[_B]==1:
					if l<sc[_J]:continue
					if st.sw_4h.trend==1 and sc[_K]is not _A and c>sc[_K]and b3[3]-b1[2]>=min_fvg and b2[4]>b2[1]and c2b>=.8*a5:self._submit_entry(st,v_eng,1,b3[3],sc[_J]-buf,tr=1.5,expire_bars=90,min_risk=v_min_r);continue
				else:
					if h>sc[_J]:continue
					if st.sw_4h.trend==-1 and sc[_K]is not _A and c<sc[_K]and b1[3]-b3[2]>=min_fvg and b2[4]<b2[1]and c2b>=.8*a5:self._submit_entry(st,v_eng,-1,b3[2],sc[_J]+buf,tr=1.5,expire_bars=90,min_risk=v_min_r);continue
				still.append(sc)
			st.c5=still
		elif st.symbol==self.ns and st.c5:st.c5=[sc for sc in st.c5 if st.i5-sc[_I]<=12]
		st.sw_5m.update(bar)
		if st.symbol==self.bt:st.a5.val=a5;self._ltf_bar(st,bar,9,_C,.002,15.,self.BTC_STEPS,_T,_G)
	def on_data(self,data):
		for(sym,st)in self.assets.items():
			bar=self._bar(data,sym)
			if bar is _A:continue
			st.bs+=1
			if not self.is_warming_up and not st.ip and st.pt is _A and self.portfolio[sym].invested:self.transactions.cancel_open_orders(sym);self.liquidate(sym,tag='ORPHAN_SYNC');self.oc+=1
			if sym!=self.bt:self._ltf_bar(st,bar,_A,_C,_C,_C,(),'',_D)
	def _check_confirm_setup(self,st,dt,o,h,l,c):
		cs=st.cs
		if cs is _A or st.ip or st.pt is not _A:return
		if st.li>cs['exp']or self._cfd_blocked(st,dt)or cs[_R]and dt.hour in cs[_R]or(l<=cs[_L]if cs[_B]==1 else h>=cs[_L]):st.cs=_A;return
		if not cs[_V]and(l<=cs[_P]if cs[_B]==1 else h>=cs[_P]):cs[_V]=_G
		if cs[_V]:
			ok_c=c>o and c>cs[_P]if cs[_B]==1 else c<o and c<cs[_P]
			if ok_c:st.cs=_A;self._submit_entry(st,cs[_O],cs[_B],c,cs[_L],tp=cs[_Q],tr=cs[_U],lk=cs[_b],is_market=_G)
	def _ltf_bar(self,st,bar,min_hr,min_abs,min_pct,fixed_rr,lk,eng,allow_entries):
		st.li+=1;dt=self.utc_time;o,h,l,c=float(bar.Open),float(bar.High),float(bar.Low),float(bar.Close);a1=st.al.update(h,l,c);st.bltf.append((dt,o,h,l,c))
		if st.ip and st.rd>0 and st.stx is not _A:
			if st.stx.status not in(OrderStatus.FILLED,OrderStatus.CANCELED,OrderStatus.INVALID):
				for(act_r,lk_r)in st.lk:
					hit=h>=st.ep+act_r*st.rd if st.ax==1 else l<=st.ep-act_r*st.rd
					if hit:self._try_lock_sl(st,st.ep+st.ax*lk_r*st.rd,c)
				if st.tr is not _A and not st.ta:
					hit_tr=h>=st.ep+st.tr*st.rd if st.ax==1 else l<=st.ep-st.tr*st.rd
					if hit_tr:st.ta,st.tm=_G,'1h';self._try_lock_sl(st,st.ep+st.ax*st.rd,c)
		if st.pt is not _A and st.pm is not _A:
			pm=st.pm;expires=st.i15>pm[_c]if pm.get(_c)is not _A else st.li>pm[_j]
			if expires or self._cfd_blocked(st,dt)or(l<=pm[_L]if pm[_B]==1 else h>=pm[_L])or pm[_R]and dt.hour in pm[_R]:self._cancel_pending(st)
		if not self.is_warming_up:self._check_confirm_setup(st,dt,o,h,l,c)
		if allow_entries and len(st.bltf)>=3 and(min_hr is _A or dt.hour>=min_hr)and not self.is_warming_up:
			b1,b2,b3=st.bltf[-3],st.bltf[-2],st.bltf[-1];c2b,buf,min_r=abs(b2[4]-b2[1]),a1,max(min_abs,c*min_pct);still=[]
			for sc in st.cltf:
				if st.li-sc[_I]>60:continue
				if sc[_B]==1:
					if l<sc[_J]:continue
					if st.sw_4h.trend==1 and st.sw_1h.trend==1 and sc[_K]is not _A and b3[4]>sc[_K]and b3[3]-b1[2]>=.25*a1 and b2[4]>b2[1]and c2b>=a1:
						trig,sl=b3[3],sc[_J]-buf;sl=self._floor_sl(st,1,trig,sl,min_r,c)
						if eng!=_T or(trig-sl)/max(_H,c)<.018:self._submit_entry(st,eng,1,trig,sl,tp=trig+fixed_rr*(trig-sl),lk=lk,expire_bars=20,min_risk=min_r)
						continue
				else:
					if h>sc[_J]:continue
					if st.sw_4h.trend==-1 and st.sw_1h.trend==-1 and sc[_K]is not _A and b3[4]<sc[_K]and b1[3]-b3[2]>=.25*a1 and b2[4]<b2[1]and c2b>=a1:
						trig,sl=b3[2],sc[_J]+buf;sl=self._floor_sl(st,-1,trig,sl,min_r,c)
						if eng!=_T or(sl-trig)/max(_H,c)<.018:self._submit_entry(st,eng,-1,trig,sl,tp=trig-fixed_rr*(sl-trig),lk=lk,expire_bars=20,min_risk=min_r)
						continue
				still.append(sc)
			st.cltf=still
		st.sw_ltf.update(bar)
	def on_order_event(self,oe):
		if oe.symbol not in self.assets:return
		st=self.assets[oe.symbol]
		if oe.status==OrderStatus.INVALID:
			self.ic[st.name]+=1
			if self.ic[st.name]<=5:self.debug(f"INVALID {st.name} (id={oe.order_id}): {oe.message}")
			if st.pm is not _A and not st.ip:st.pt=st.pm=_A
			elif st.ip:self.transactions.cancel_open_orders(oe.symbol);self.liquidate(oe.symbol);st.ip=_D;st.stx=st.tt=_A
			return
		if oe.status==OrderStatus.CANCELED:
			if st.pt is not _A and oe.order_id==st.pt.order_id:st.pt=st.pm=_A
			return
		if oe.status!=OrderStatus.FILLED:return
		if(st.pt is not _A and oe.order_id==st.pt.order_id or st.pm is not _A and not st.ip)and st.pm is not _A:
			pm=st.pm;st.pt=st.pm=_A;fill_px=float(oe.fill_price);st.ip,st.ae,st.ax=_G,pm[_O],pm[_B];st.ep,st.sp,st.tpv=fill_px,pm[_L],pm[_Q];st.rd,st.tr,st.lk=abs(fill_px-pm[_L]),pm[_U],pm[_b];st.ta,st.tm,st.qty,st.stx,st.tt=_D,_A,pm[_W],_A,_A;self.tc[st.name,pm[_O]]+=1
			if st.rd<=0:self.liquidate(st.symbol);st.ip=_D;return
			st.stx=self.stop_market_order(st.symbol,-pm[_W],pm[_L],tag=f"{pm[_O]}_SL")
			if st.ip and pm[_Q]is not _A:st.tt=self.limit_order(st.symbol,-pm[_W],pm[_Q],tag=f"{pm[_O]}_TP")
			return
		self.transactions.cancel_open_orders(oe.symbol);st.ip=_D;st.stx=st.tt=_A
		if self.portfolio[oe.symbol].invested:self.liquidate(oe.symbol,tag='OCO_STRAY_CLEANUP');self.oc+=1
		eq_now=float(self.portfolio.total_portfolio_value)
		if eq_now>self.hw:self.hw=eq_now
	def on_end_of_algorithm(self):
		self.log(f"=== V9 Asset Telemetry (oco_cleanups={self.oco_cleanups}) ===")
		for st in self.assets.values():self.log(f"  {st.name:10s} | bars={st.bars_seen} | submitted={st.orders_submitted} | invalid={self.invalid_counts[st.name]} | V9_profile_evals={st.v9_profile_evals} | V9_aggressive_blocks={st.v9_aggressive_blocks} | V9_valid_choch={st.v9_choch_valid}")
		self.log('=== V9 / V8 Trade Breakdown by (Asset, Engine) ===')
		for((asset,eng),cnt)in sorted(self.tc.items()):self.log(f"  {asset:10s} | {eng:14s}: {cnt} trades")