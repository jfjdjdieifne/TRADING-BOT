# QUANTCONNECT.COM - V9 Dynamic Profile 3-Asset Sniper
# Full V8.4 reference sleeves + causal Dynamic Profile / Sweep-CHoCH layer.
# Assets: XAUUSD (OANDA CFD), NAS100USD (OANDA CFD), BTCUSD (Coinbase Crypto)
#
# V8.4 sleeves are kept intact in this file. V9 adds:
#   1. Causal prior-100-bar volume z-score and prior-ATR(14) ADI.
#   2. Aggressive shallow-FVG limit entry only after volume + ADI + Spot-flow gate.
#   3. Negative Spot-flow divergence cancels aggressive mode and returns to defense.
#   4. Explicit 1H k=3 sweep -> 15m body CHoCH + speed/distance/flow validation.
#   5. Protected impulse stop at one price tick beyond the impulse candle.
#   6. Deep-OB fallback, known opposing-zone target, minimum 5R, 15m-clock expiry, and telemetry.
#
# IMPORTANT DATA CONTRACT:
# QuantConnect TradeBar.Volume is not Spot CVD. By default V9 requires an external
# Spot-flow value and therefore blocks the new aggressive gate when none is supplied.
# Set v9_use_ohlcv_proxy=1 only for a clearly-labelled OHLCV proxy experiment; it is
# not a production Spot-CVD implementation and must not be used as proof of flow.

from AlgorithmImports import *
from collections import defaultdict, deque
import math


class CausalSwingTracker:
    def __init__(self, k: int = 2, max_active: int = 30) -> None:
        self.k = k
        self.max_active = max_active
        self.win = deque(maxlen=2 * k + 1)
        self.bar_idx = -1
        self.last_high = None
        self.last_low = None
        self.last_high_point = None
        self.last_low_point = None
        self.trend = 0
        self.act_hi = []
        self.act_lo = []

    def update_hlc(self, h: float, l: float, c: float):
        self.bar_idx += 1
        self.win.append((h, l))
        nh = nl = None
        if len(self.win) == 2 * self.k + 1:
            m = self.k
            ch, cl = self.win[m][0], self.win[m][1]
            if all(ch >= self.win[i][0] for i in range(len(self.win)) if i != m) and any(
                ch > self.win[i][0] for i in range(len(self.win)) if i != m
            ):
                nh = (self.bar_idx - self.k, ch)
                self.last_high = ch
                self.last_high_point = nh
                self.act_hi.append(nh)
                if len(self.act_hi) > self.max_active:
                    self.act_hi.pop(0)
            if all(cl <= self.win[i][1] for i in range(len(self.win)) if i != m) and any(
                cl < self.win[i][1] for i in range(len(self.win)) if i != m
            ):
                nl = (self.bar_idx - self.k, cl)
                self.last_low = cl
                self.last_low_point = nl
                self.act_lo.append(nl)
                if len(self.act_lo) > self.max_active:
                    self.act_lo.pop(0)
        self.act_hi = [x for x in self.act_hi if h <= x[1]]
        self.act_lo = [x for x in self.act_lo if l >= x[1]]
        if self.last_high is not None and c > self.last_high:
            self.trend = 1
        elif self.last_low is not None and c < self.last_low:
            self.trend = -1
        return nh, nl

    def update(self, bar):
        return self.update_hlc(float(bar.High), float(bar.Low), float(bar.Close))


class WilderATR14:
    def __init__(self) -> None:
        self.prev_close = None
        self.trs = []
        self.val = 0.0

    def update(self, h: float, l: float, c: float) -> float:
        tr = (h - l) if self.prev_close is None else max(h - l, abs(h - self.prev_close), abs(l - self.prev_close))
        self.prev_close = c
        if len(self.trs) < 14:
            self.trs.append(tr)
            self.val = sum(self.trs) / len(self.trs)
        else:
            self.val = (self.val * 13.0 + tr) / 14.0
        return self.val


class SpotFlowAccumulator:
    """Causal executed-flow accumulator used by the V9 safety gate.

    ``delta`` must be signed Spot initiated volume from an external source. This
    class never infers Spot CVD from price. The optional proxy is created only
    by the explicit ``v9_use_ohlcv_proxy`` switch in the algorithm.
    """

    def __init__(self, maxlen: int = 20) -> None:
        self.cumulative = None
        self.history = deque(maxlen=maxlen)
        self.gap = False

    def status(self, delta, side: int, required: bool) -> str:
        if delta is None:
            return "UNKNOWN" if required else "NOT_REQUIRED"
        if self.gap or self.cumulative is None or len(self.history) == 0:
            return "UNKNOWN" if required else "NOT_REQUIRED"
        candidate = self.cumulative + float(delta)
        if side == 1:
            return "VALID" if delta > 0 and candidate > max(self.history) else "DIVERGENT"
        return "VALID" if delta < 0 and candidate < min(self.history) else "DIVERGENT"

    def commit(self, delta) -> None:
        if delta is None:
            self.gap = True
            return
        self.cumulative = float(delta) if self.cumulative is None else self.cumulative + float(delta)
        self.history.append(self.cumulative)
        self.gap = False


class AssetState:
    def __init__(self, name: str, symbol: Symbol, leverage: float) -> None:
        self.name, self.symbol, self.leverage = name, symbol, leverage
        self.sw_1d, self.sw_4h = CausalSwingTracker(2), CausalSwingTracker(2)
        self.sw_1h, self.sw_1h_k3 = CausalSwingTracker(2), CausalSwingTracker(3)
        self.sw_15m, self.sw_5m, self.sw_ltf = CausalSwingTracker(2), CausalSwingTracker(2), CausalSwingTracker(2)
        self.atr_15m, self.atr_5m, self.atr_ltf = WilderATR14(), WilderATR14(), WilderATR14()
        # 100 completed 15m bars are required for the V9 contextual volume gate.
        self.bars_15m, self.bars_5m, self.bars_ltf = deque(maxlen=140), deque(maxlen=15), deque(maxlen=5)
        self.cands_1h_k3_5m, self.cands_1h_k3_ltf, self.amd_manips = [], [], []
        self.v9_volume_history = deque(maxlen=100)
        self.v9_flow = SpotFlowAccumulator(20)
        self.v9_bars = deque(maxlen=180)  # (index, timestamp, open, high, low, close)
        self.v9_bodies = deque(maxlen=180)  # (index, open, close)
        self.v9_fvgs, self.v9_obs, self.v9_sweeps = [], [], []
        self.v9_zone_seq = 0
        self.v9_broken_high = None
        self.v9_broken_low = None
        self.v9_profile_evals = self.v9_aggressive_blocks = self.v9_choch_valid = 0
        self.b4h_bucket, self.b4h_ohlc = None, None
        self.b1d_date, self.b1d_ohlc = None, None
        self.d1_closes, self.d1_ema20, self.d1_er14, self.d1_last_c = deque(maxlen=20), None, 0.0, 0.0
        self.pending_ticket = self.pending_meta = self.confirm_setup = None
        self.in_position, self.active_engine, self.active_side = False, None, 0
        self.entry_price = self.sl_price = self.risk_dist = self.qty = 0.0
        self.tp_price = self.trail_after_r = self.trail_mode = None
        self.step_locks, self.trailing_active = (), False
        self.sl_ticket = self.tp_ticket = None
        self.v9_idx = 0
        self.ltf_idx = self.idx_5m = self.idx_15m = self.bars_seen = self.orders_submitted = 0


class V9DynamicProfile3AssetAlgorithm(QCAlgorithm):
    ENGINE_RISK = {
        "V9_Profile": 0.010,
        "V9_Countertrend": 0.005,
        "VisB_Pro": 0.015,
        "V3_Pro_Clean": 0.015,
        "BTC_15R_BE": 0.015,
        "NSX_AMD_1D": 0.010,
        "NSX_VisB_Chop": 0.010,
        "AMD_Pro": 0.008,
    }
    BTC_STEPS = ((3.0, 1.0), (5.5, 2.5), (8.5, 5.5), (11.5, 8.5))

    def initialize(self) -> None:
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2020, 2, 1)
        self.set_end_date(2026, 10, 31)
        self.set_cash(100000)
        self.risk_scale = float(self.get_parameter("risk_scale") or 1.0)
        self.use_amd_pro = bool(int(self.get_parameter("use_amd_pro") or 0))
        self.enable_v9_profiles = bool(int(self.get_parameter("enable_v9_profiles") or 1))
        # Safe default: no V9 aggressive entry without declared external Spot CVD.
        self.v9_require_spot_cvd = bool(int(self.get_parameter("v9_require_spot_cvd") or 1))
        self.v9_use_ohlcv_proxy = bool(int(self.get_parameter("v9_use_ohlcv_proxy") or 0))
        self.v9_require_cool_funding = bool(int(self.get_parameter("v9_require_cool_funding") or 0))
        self.v9_volume_z_threshold = float(self.get_parameter("v9_volume_z_threshold") or 2.5)
        self.v9_adi_threshold = float(self.get_parameter("v9_adi_threshold") or 3.0)
        self.v9_min_rr = float(self.get_parameter("v9_min_rr") or 5.0)
        self.v9_max_sweep_age = int(self.get_parameter("v9_max_sweep_age") or 32)
        self.v9_min_speed_ratio = float(self.get_parameter("v9_min_speed_ratio") or 2.0)
        self.v9_min_distance_atr = float(self.get_parameter("v9_min_distance_atr") or 1.0)
        self.v9_pending_expiry_bars = int(self.get_parameter("v9_pending_expiry_bars") or 20)
        self.v9_tick_size = float(self.get_parameter("v9_tick_size") or 0.01)
        self.hwm_equity = 100000.0
        self.set_warm_up(timedelta(days=30), Resolution.MINUTE)
        self.set_brokerage_model(DefaultBrokerageModel(AccountType.MARGIN))

        xau = self.add_cfd("XAUUSD", Resolution.MINUTE, Market.OANDA, leverage=50)
        nsx = self.add_cfd("NAS100USD", Resolution.MINUTE, Market.OANDA, leverage=50)
        btc = self.add_crypto("BTCUSD", Resolution.MINUTE, Market.COINBASE, leverage=25)
        btc.set_buying_power_model(SecurityMarginModel(25.0))

        self.xau_sym, self.nsx_sym, self.btc_sym = xau.symbol, nsx.symbol, btc.symbol
        self.assets = {
            self.xau_sym: AssetState("XAUUSD", self.xau_sym, 50.0),
            self.nsx_sym: AssetState("NAS100USD", self.nsx_sym, 50.0),
            self.btc_sym: AssetState("BTCUSD", self.btc_sym, 25.0),
        }
        self.trade_counts, self.invalid_counts = defaultdict(int), defaultdict(int)
        self.oco_cleanups = 0
        for sym, st in self.assets.items():
            # UTC-exact 4H and 1D bars are aggregated inside on_1h using self.utc_time
            self.consolidate(sym, timedelta(hours=1), lambda b, s=st: self.on_1h(s, b))
            self.consolidate(sym, timedelta(minutes=15), lambda b, s=st: self.on_15m(s, b))
            self.consolidate(sym, timedelta(minutes=5), lambda b, s=st: self.on_5m(s, b))

    @staticmethod
    def _in_kz(dt) -> bool:
        return (7 <= dt.hour <= 10) or (12 <= dt.hour <= 16)

    @staticmethod
    def _in_ny(dt) -> bool:
        return 12 <= dt.hour < 17

    def _cfd_blocked(self, st: AssetState, dt) -> bool:
        if st.symbol == self.btc_sym:
            return False
        if dt.hour >= 20 or dt.hour < 1:
            return True
        if st.symbol == self.xau_sym and dt.weekday() == 4 and dt.hour >= 18:
            return True
        return False

    @staticmethod
    def _bar(data: Slice, sym: Symbol):
        if sym in data.quote_bars:
            return data.quote_bars[sym]
        return data.bars[sym] if sym in data.bars else None

    def _effective_risk_pct(self, engine: str) -> float:
        eq = float(self.portfolio.total_portfolio_value)
        dd = (self.hwm_equity - eq) / self.hwm_equity if self.hwm_equity > 0 else 0.0
        brake = 0.40 if dd >= 0.12 else (0.60 if dd >= 0.08 else 1.0)
        return self.ENGINE_RISK.get(engine, 0.010) * brake * self.risk_scale

    def _round_qty(self, sym: Symbol, raw_qty: float, is_long: bool) -> float:
        sp = self.securities[sym].symbol_properties
        lot = float(sp.lot_size or 0.001)
        min_sz = float(sp.minimum_order_size or lot)
        qty = round(math.floor(abs(raw_qty) / lot) * lot, 8)
        if qty < min_sz:
            return 0.0
        return qty if is_long else -qty

    def _round_px(self, sym: Symbol, price: float) -> float:
        tick = float(self.securities[sym].symbol_properties.minimum_price_variation or 0.01)
        tick = tick if tick > 0 else 0.01
        return round(round(price / tick) * tick, 6)

    @staticmethod
    def _v9_volume_z(st: AssetState, current_volume: float):
        history = list(st.v9_volume_history)
        if len(history) < 100:
            return None
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance)
        if std <= 0:
            if current_volume > mean:
                return float("inf")
            if current_volume < mean:
                return float("-inf")
            return 0.0
        return (current_volume - mean) / std

    def _v9_flow_delta(self, bar):
        # No production Spot-CVD feed is silently fabricated here. The proxy is
        # opt-in for research only and is explicitly marked in telemetry.
        if not self.v9_use_ohlcv_proxy:
            return None
        volume = float(getattr(bar, "Volume", 0.0) or 0.0)
        high, low, close = float(bar.High), float(bar.Low), float(bar.Close)
        if volume <= 0 or high <= low:
            return None
        location = (2.0 * close - high - low) / (high - low)
        return volume * location

    def _v9_funding_ok(self):
        # This V8 universe has no funding-rate subscription. Fail closed only
        # when the owner explicitly requires a cool funding observation.
        return not self.v9_require_cool_funding

    @staticmethod
    def _v9_latest_level(tracker, side: int):
        # Structure breaks must be keyed to the actual latest swing point, not
        # the current tracker index after the swing has already been broken.
        point = tracker.last_high_point if side == -1 else tracker.last_low_point
        if point is not None:
            return point
        price = tracker.last_high if side == -1 else tracker.last_low
        return (tracker.bar_idx, price) if price is not None else None

    def _v9_new_fvg(self, st: AssetState):
        if len(st.v9_bars) < 3:
            return None
        b1, _, b3 = list(st.v9_bars)[-3:]
        # tuple: (index, timestamp, open, high, low, close)
        if b3[4] > b1[3]:
            zone = {"id": st.v9_zone_seq, "side": 1, "low": b1[3], "high": b3[4], "created": b3[0]}
        elif b3[3] < b1[4]:
            zone = {"id": st.v9_zone_seq, "side": -1, "low": b3[3], "high": b1[4], "created": b3[0]}
        else:
            return None
        st.v9_zone_seq += 1
        st.v9_fvgs.append(zone)
        st.v9_fvgs = st.v9_fvgs[-80:]
        return zone

    def _v9_new_ob(self, st: AssetState, side: int, source_event: str, origin_idx: int, current_idx: int):
        prior = [b for b in st.v9_bars if origin_idx <= b[0] < current_idx]
        opposite = [b for b in prior if (b[5] < b[2] if side == 1 else b[5] > b[2])]
        if not opposite:
            return None
        b = opposite[-1]
        zone = {
            "id": st.v9_zone_seq,
            "side": side,
            "source": source_event,
            "origin": b[0],
            "created": current_idx,
            "low": b[4],
            "high": b[3],
        }
        st.v9_zone_seq += 1
        st.v9_obs.append(zone)
        st.v9_obs = st.v9_obs[-80:]
        return zone

    @staticmethod
    def _v9_zone_touched(st: AssetState, zone) -> bool:
        # A bounded QC export cannot prove that a zone is still unmitigated
        # once the bars preceding it have rolled out of the audit window.
        # Fail closed rather than reusing an old zone as a falsely-known target.
        if not st.v9_bars or st.v9_bars[0][0] > zone["created"]:
            return True
        for b in st.v9_bars:
            if b[0] <= zone["created"]:
                continue
            if b[3] >= zone["low"] and b[4] <= zone["high"]:
                return True
        return False

    def _v9_flow_ok(self, flow_status: str) -> bool:
        return flow_status == "VALID" or (
            not self.v9_require_spot_cvd and flow_status == "NOT_REQUIRED"
        )

    def _v9_target(self, st: AssetState, side: int, entry: float, current_fvg_id=None):
        candidates = []
        for zone in st.v9_fvgs:
            if zone["id"] == current_fvg_id or zone["side"] == side:
                continue
            if (side == 1 and zone["high"] <= entry) or (side == -1 and zone["low"] >= entry):
                continue
            if self._v9_zone_touched(st, zone):
                continue
            target = zone["low"] if side == 1 and zone["low"] > entry else zone["high"] if side == 1 else zone["high"] if zone["high"] < entry else zone["low"]
            candidates.append((abs(target - entry), zone["created"], target, zone["id"], None))
        for zone in st.v9_obs:
            if zone["side"] == side:
                continue
            if (side == 1 and zone["high"] <= entry) or (side == -1 and zone["low"] >= entry):
                continue
            if self._v9_zone_touched(st, zone):
                continue
            target = zone["low"] if side == 1 and zone["low"] > entry else zone["high"] if side == 1 else zone["high"] if zone["high"] < entry else zone["low"]
            candidates.append((abs(target - entry), zone["created"], target, None, zone["id"]))
        if not candidates:
            return None, None, None
        _, _, target, fvg_id, ob_id = min(candidates, key=lambda x: (x[0], x[1]))
        return target, fvg_id, ob_id

    def _v9_deep_ob(self, st: AssetState, side: int, origin: float, termination: float, current_price: float):
        move = abs(termination - origin)
        if move <= 0:
            return None
        valid = []
        for zone in st.v9_obs:
            if zone["side"] != side or self._v9_zone_touched(st, zone):
                continue
            if side == 1:
                if zone["high"] >= current_price:
                    continue
                r_lo = (termination - zone["high"]) / move
                r_hi = (termination - zone["low"]) / move
            else:
                if zone["low"] <= current_price:
                    continue
                r_lo = (zone["low"] - termination) / move
                r_hi = (zone["high"] - termination) / move
            if r_hi >= 0.705 and r_lo <= 0.790:
                valid.append(zone)
        return max(valid, key=lambda z: z["created"]) if valid else None

    def _v9_speed_ratio(self, st: AssetState, sweep_idx: int, current_idx: int):
        up = [x[2] - x[1] for x in st.v9_bodies if sweep_idx < x[0] <= current_idx and x[2] > x[1]]
        down = [x[1] - x[2] for x in st.v9_bodies if sweep_idx - 12 <= x[0] < sweep_idx and x[2] < x[1]]
        if not up or not down:
            return None
        return (sum(up) / len(up)) / (sum(down) / len(down))

    def _v9_recent_sweep(self, st: AssetState, side: int, current_idx: int):
        candidates = [s for s in st.v9_sweeps if s["side"] == side and 0 <= current_idx - s["start_i"] <= self.v9_max_sweep_age]
        return max(candidates, key=lambda x: x["start_i"]) if candidates else None

    def _v9_submit_plan(self, st: AssetState, engine: str, side: int, entry: float, stop: float, target: float, current_idx: int, reason: str):
        if target is None:
            return False
        # Re-check the hard R:R gate after exchange tick rounding.  A plan that
        # is 5R in raw floats must not become sub-5R at the broker precision.
        entry = self._round_px(st.symbol, entry)
        stop = self._round_px(st.symbol, stop)
        target = self._round_px(st.symbol, target)
        risk = entry - stop if side == 1 else stop - entry
        if risk <= 0:
            return False
        rr = (target - entry) / risk if side == 1 else (entry - target) / risk
        if rr < self.v9_min_rr:
            return False
        self._submit_entry(
            st, engine, side, entry, stop, tp=target, trail_after_r=2.0,
            step_locks=((2.0, 1.0), (3.0, 1.5)), expire_bars=self.v9_pending_expiry_bars,
            min_risk=0.0, is_market=False, require_confirm=False,
            apply_floor=False, expire_on_15m=True,
        )
        if st.pending_meta is not None:
            st.pending_meta["v9_reason"] = reason
            st.pending_meta["v9_plan_index"] = current_idx
            st.pending_meta["v9_planned_rr"] = rr
            return True
        return False

    def _v9_profile_bar(self, st: AssetState, bar, atr_before: float) -> None:
        if not self.enable_v9_profiles:
            return
        st.v9_idx += 1
        dt = self.utc_time
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        vol = float(getattr(bar, "Volume", 0.0) or 0.0)
        st.v9_bars.append((st.idx_15m, dt, o, h, l, c))
        st.v9_bodies.append((st.idx_15m, o, c))

        volume_z = self._v9_volume_z(st, vol)
        current_fvg = self._v9_new_fvg(st)
        current_idx = st.idx_15m
        high_level = st.sw_15m.last_high
        low_level = st.sw_15m.last_low
        high_point = self._v9_latest_level(st.sw_15m, -1)
        low_point = self._v9_latest_level(st.sw_15m, 1)
        break_up = high_level is not None and o > high_level and c > high_level and high_point[0] != st.v9_broken_high
        break_down = low_level is not None and o < low_level and c < low_level and low_point[0] != st.v9_broken_low
        if break_up and break_down:
            break_up = break_down = False

        side = 1 if break_up else -1 if break_down else 0
        if side == 0:
            st.v9_volume_history.append(vol)
            st.v9_flow.commit(self._v9_flow_delta(bar))
            return

        level = high_level if side == 1 else low_level
        point = low_point if side == 1 else high_point
        if point is None or point[1] is None or atr_before <= 0:
            st.v9_volume_history.append(vol)
            st.v9_flow.commit(self._v9_flow_delta(bar))
            return
        # CausalSwingTracker is zero-based and has already committed only
        # prior bars; V9's completed-bar index is one-based because on_15m
        # increments idx_15m before this method runs.
        origin_idx, origin_price = point[0] + 1, point[1]
        wave_n = max(1, current_idx - origin_idx + 1)
        move = (c - origin_price) * side
        adi = max(0.0, move) / (wave_n * atr_before)
        flow_delta = self._v9_flow_delta(bar)
        flow_status = st.v9_flow.status(flow_delta, side, self.v9_require_spot_cvd)
        funding_ok = self._v9_funding_ok()
        st.v9_profile_evals += 1
        is_choch = (st.sw_15m.trend == -1 and side == 1) or (st.sw_15m.trend == 1 and side == -1)
        sweep = self._v9_recent_sweep(st, side, current_idx) if is_choch else None
        speed = self._v9_speed_ratio(st, sweep["start_i"], current_idx) if sweep is not None else None
        distance = abs(level - sweep["extreme"]) / atr_before if sweep is not None else None
        choch_valid = bool(
            is_choch and sweep is not None and volume_z is not None and volume_z > self.v9_volume_z_threshold
            and speed is not None and speed >= self.v9_min_speed_ratio
            and distance is not None and distance > self.v9_min_distance_atr
            and self._v9_flow_ok(flow_status) and funding_ok
        )
        if choch_valid:
            st.v9_choch_valid += 1

        aggressive = bool(
            not is_choch and volume_z is not None and volume_z > self.v9_volume_z_threshold
            and adi > self.v9_adi_threshold and self._v9_flow_ok(flow_status) and funding_ok
        )
        if volume_z is not None and volume_z > self.v9_volume_z_threshold and adi > self.v9_adi_threshold and not aggressive:
            st.v9_aggressive_blocks += 1

        event = "CHOCH" if is_choch else "BOS"
        self._v9_new_ob(st, side, event, origin_idx, current_idx)
        if high_point is not None and side == 1:
            st.v9_broken_high = high_point[0]
        if low_point is not None and side == -1:
            st.v9_broken_low = low_point[0]

        if current_fvg is not None and current_fvg["side"] == side:
            tick = float(self.securities[st.symbol].symbol_properties.minimum_price_variation or self.v9_tick_size)
            tick = tick if tick > 0 else self.v9_tick_size
            entry = current_fvg["high"] if side == 1 else current_fvg["low"]
            stop = l - tick if side == 1 else h + tick
            target, _, _ = self._v9_target(st, side, entry, current_fvg["id"])
            if aggressive:
                self._v9_submit_plan(st, "V9_Profile", side, entry, stop, target, current_idx, "AGGRESSIVE_SHALLOW_FVG_PROTECTED_IMPULSE_STOP")
            elif choch_valid:
                stop = sweep["extreme"] - tick if side == 1 else sweep["extreme"] + tick
                self._v9_submit_plan(st, "V9_Countertrend", side, entry, stop, target, current_idx, "HTF_SWEEP_BODY_CHOCH_SPEED_DISTANCE_FLOW")

        if volume_z is not None and not aggressive and not choch_valid:
            deep = self._v9_deep_ob(st, side, origin_price, c, c)
            if deep is not None:
                tick = float(self.securities[st.symbol].symbol_properties.minimum_price_variation or self.v9_tick_size)
                tick = tick if tick > 0 else self.v9_tick_size
                entry = deep["high"] if side == 1 else deep["low"]
                stop = origin_price - tick if side == 1 else origin_price + tick
                target, _, _ = self._v9_target(st, side, entry)
                self._v9_submit_plan(st, "V9_Profile", side, entry, stop, target, current_idx, "DEFENSIVE_DEEP_OB_ORIGIN_STOP")

        st.v9_volume_history.append(vol)
        st.v9_flow.commit(flow_delta)

    def _clamp_qty(self, st: AssetState, raw_qty: float, px: float) -> float:
        if px <= 0:
            return raw_qty
        max_notional = max(0.0, float(self.portfolio.margin_remaining)) * st.leverage * 0.85
        return min(abs(raw_qty), max_notional / px) if max_notional > 0 else 0.0

    def _cancel_pending(self, st: AssetState) -> None:
        if st.pending_ticket is not None and st.pending_ticket.status not in (
            OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID
        ):
            st.pending_ticket.cancel()
        st.pending_ticket = st.pending_meta = st.confirm_setup = None

    def _try_lock_sl(self, st: AssetState, lock_px: float, cur_c: float) -> None:
        lp = self._round_px(st.symbol, lock_px)
        sec = self.securities[st.symbol]
        ref_long = float(getattr(sec, "bid_price", 0.0) or 0.0)
        ref_short = float(getattr(sec, "ask_price", 0.0) or 0.0)
        ref_long = ref_long if ref_long > 0 else cur_c
        ref_short = ref_short if ref_short > 0 else cur_c
        if (st.active_side == 1 and lp > st.sl_price and lp < ref_long) or (
            st.active_side == -1 and lp < st.sl_price and lp > ref_short
        ):
            st.sl_price = lp
            st.sl_ticket.update_stop_price(lp)

    def _floor_sl(self, st: AssetState, side: int, trig: float, sl: float, min_r: float, cur_px: float) -> float:
        floor_r = max(min_r, 1e-6)
        if st.symbol == self.xau_sym:
            floor_r = max(floor_r, cur_px * 0.0020)
        if st.atr_5m.val > 0:
            floor_r = max(floor_r, 1.5 * st.atr_5m.val)
        raw_r = (trig - sl) if side == 1 else (sl - trig)
        if raw_r < floor_r:
            sl = (trig - floor_r) if side == 1 else (trig + floor_r)
        return sl

    def _submit_entry(self, st: AssetState, engine: str, side: int, trig: float, sl: float,
                      tp: float = None, trail_after_r: float = None, step_locks=(),
                      expire_bars: int = 20, min_risk: float = 0.0, skip_hours=None,
                      is_market: bool = False, require_confirm: bool = False,
                      apply_floor: bool = True, expire_on_15m: bool = False) -> None:
        if self.is_warming_up or st.in_position or st.pending_ticket is not None or st.confirm_setup is not None:
            return
        if not self.is_market_open(st.symbol) or self._cfd_blocked(st, self.utc_time):
            return
        if self.portfolio[st.symbol].invested:
            self.transactions.cancel_open_orders(st.symbol)
            self.liquidate(st.symbol, tag="PRE_ENTRY_SYNC")
            self.oco_cleanups += 1
            return
        cur_px = float(self.securities[st.symbol].price)
        if cur_px <= 0:
            return
        trig_px = cur_px if is_market else self._round_px(st.symbol, trig)
        if apply_floor:
            sl = self._floor_sl(st, side, trig_px, sl, min_risk, cur_px)
        sl_px = self._round_px(st.symbol, sl)
        risk = (trig_px - sl_px) if side == 1 else (sl_px - trig_px)
        if risk <= max(min_risk, 1e-6):
            return
        if not is_market and ((side == 1 and trig_px > cur_px) or (side == -1 and trig_px < cur_px)):
            return
        if require_confirm and not is_market:
            st.confirm_setup = {
                "engine": engine, "side": side, "trig": trig_px, "sl": sl_px,
                "tp": self._round_px(st.symbol, tp) if tp is not None else None,
                "trail_after_r": trail_after_r, "step_locks": step_locks,
                "exp": st.ltf_idx + expire_bars, "skip_hours": skip_hours, "touched": False,
            }
            return

        risk_usd = float(self.portfolio.total_portfolio_value) * self._effective_risk_pct(engine)
        qty = self._round_qty(st.symbol, self._clamp_qty(st, risk_usd / risk, trig_px), side == 1)
        if qty == 0.0:
            return
        st.pending_meta = {
            "engine": engine, "side": side, "trig": trig_px, "sl": sl_px,
            "tp": self._round_px(st.symbol, tp) if tp is not None else None,
            "risk": risk, "qty": qty, "trail_after_r": trail_after_r,
            "expire_idx": st.ltf_idx + expire_bars,
            "expire_15m_idx": st.idx_15m + expire_bars if expire_on_15m else None,
            "skip_hours": skip_hours,
        }
        st.orders_submitted += 1
        ticket = self.market_order(st.symbol, qty, tag=engine) if is_market else self.limit_order(st.symbol, qty, trig_px, tag=engine)
        if ticket.status == OrderStatus.INVALID:
            st.pending_meta = st.pending_ticket = None
            return
        if st.pending_meta is not None:
            st.pending_ticket = ticket

    def _push_1d(self, st: AssetState, h: float, l: float, c: float) -> None:
        st.sw_1d.update_hlc(h, l, c)
        st.d1_closes.append(c)
        st.d1_last_c = c
        k = 2.0 / 21.0
        st.d1_ema20 = c if st.d1_ema20 is None else (c * k + st.d1_ema20 * (1.0 - k))
        if len(st.d1_closes) >= 15:
            arr = list(st.d1_closes)[-15:]
            den = sum(abs(arr[j] - arr[j - 1]) for j in range(1, len(arr)))
            st.d1_er14 = abs(arr[-1] - arr[0]) / den if den > 0 else 0.0

    def _update_utc_htf(self, st: AssetState, dt, o: float, h: float, l: float, c: float) -> None:
        ref = dt - timedelta(minutes=1)
        b4_key = (ref.date(), ref.hour // 4)
        if st.b4h_bucket is not None and b4_key != st.b4h_bucket and st.b4h_ohlc is not None:
            st.sw_4h.update_hlc(st.b4h_ohlc[1], st.b4h_ohlc[2], st.b4h_ohlc[3])
            st.b4h_ohlc = None
        if st.b4h_ohlc is None:
            st.b4h_ohlc = (o, h, l, c)
        else:
            st.b4h_ohlc = (st.b4h_ohlc[0], max(st.b4h_ohlc[1], h), min(st.b4h_ohlc[2], l), c)
        st.b4h_bucket = b4_key
        if dt.hour % 4 == 0 and dt.minute == 0:
            st.sw_4h.update_hlc(st.b4h_ohlc[1], st.b4h_ohlc[2], st.b4h_ohlc[3])
            st.b4h_ohlc = None

        d_key = ref.date()
        if st.b1d_date is not None and d_key != st.b1d_date and st.b1d_ohlc is not None:
            self._push_1d(st, st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None
        if st.b1d_ohlc is None:
            st.b1d_ohlc = (o, h, l, c)
        else:
            st.b1d_ohlc = (st.b1d_ohlc[0], max(st.b1d_ohlc[1], h), min(st.b1d_ohlc[2], l), c)
        st.b1d_date = d_key
        if dt.hour == 0 and dt.minute == 0:
            self._push_1d(st, st.b1d_ohlc[1], st.b1d_ohlc[2], st.b1d_ohlc[3])
            st.b1d_ohlc = None

    def on_1h(self, st: AssetState, bar) -> None:
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        self._update_utc_htf(st, self.utc_time, o, h, l, c)
        k3 = st.sw_1h_k3
        for idx_s, p_lo in list(k3.act_lo):
            if (k3.bar_idx + 1 - idx_s) >= 4 and l < p_lo and c > p_lo:
                if self.enable_v9_profiles:
                    st.v9_sweeps.append({"side": 1, "start_i": st.idx_15m, "level": p_lo, "extreme": l})
                    st.v9_sweeps = st.v9_sweeps[-30:]
                if st.symbol == self.xau_sym or (st.symbol == self.nsx_sym and st.d1_er14 < 0.25):
                    st.cands_1h_k3_5m.append({"side": 1, "start_i": st.idx_5m, "sl_base": l, "choch": st.sw_5m.last_high})
                elif st.symbol == self.btc_sym:
                    st.cands_1h_k3_ltf.append({"side": 1, "start_i": st.ltf_idx, "sl_base": l, "choch": st.sw_ltf.last_high})
        for idx_s, p_hi in list(k3.act_hi):
            if (k3.bar_idx + 1 - idx_s) >= 4 and h > p_hi and c < p_hi:
                if self.enable_v9_profiles:
                    st.v9_sweeps.append({"side": -1, "start_i": st.idx_15m, "level": p_hi, "extreme": h})
                    st.v9_sweeps = st.v9_sweeps[-30:]
                if st.symbol == self.xau_sym or (st.symbol == self.nsx_sym and st.d1_er14 < 0.25):
                    st.cands_1h_k3_5m.append({"side": -1, "start_i": st.idx_5m, "sl_base": h, "choch": st.sw_5m.last_low})
                elif st.symbol == self.btc_sym:
                    st.cands_1h_k3_ltf.append({"side": -1, "start_i": st.ltf_idx, "sl_base": h, "choch": st.sw_ltf.last_low})
        nh, nl = st.sw_1h.update(bar)
        st.sw_1h_k3.update(bar)
        if st.in_position and st.trailing_active and st.trail_mode == "1h" and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                if st.active_side == 1 and nl is not None:
                    self._try_lock_sl(st, max(st.sl_price, float(nl[1])), c)
                elif st.active_side == -1 and nh is not None:
                    self._try_lock_sl(st, min(st.sl_price, float(nh[1])), c)

    def on_15m(self, st: AssetState, bar) -> None:
        st.idx_15m += 1
        dt = self.utc_time
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        atr_before = st.atr_15m.val
        a15 = st.atr_15m.update(h, l, c)
        st.bars_15m.append((dt, o, h, l, c))

        if st.symbol == self.xau_sym and len(st.bars_15m) >= 3 and self._in_ny(dt) and dt.hour not in (13, 14):
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b, buf = abs(b2[4] - b2[1]), max(1.0, 0.75 * a15)
            if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and st.sw_15m.last_high is not None:
                bos_up = (b2[4] <= st.sw_15m.last_high < b3[4]) or (b1[4] <= st.sw_15m.last_high < b2[4])
                if bos_up and (b3[3] - b1[2]) >= max(0.20, 0.30 * a15) and b2[4] > b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", 1, b3[3], min(b1[3], b2[3]) - buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, skip_hours=(13, 14))
            elif st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and st.sw_15m.last_low is not None:
                bos_dn = (b2[4] >= st.sw_15m.last_low > b3[4]) or (b1[4] >= st.sw_15m.last_low > b2[4])
                if bos_dn and (b1[3] - b3[2]) >= max(0.20, 0.30 * a15) and b2[4] < b2[1] and c2b >= a15:
                    self._submit_entry(st, "V3_Pro_Clean", -1, b3[2], max(b1[2], b2[2]) + buf,
                                       trail_after_r=2.5, expire_bars=300, min_risk=1.0, skip_hours=(13, 14))

        run_amd = (st.symbol == self.nsx_sym) or (st.symbol == self.xau_sym and self.use_amd_pro)
        if run_amd and len(st.bars_15m) >= 10 and a15 > 0:
            box = list(st.bars_15m)[-9:-1]
            box_hi, box_lo = max(b[2] for b in box), min(b[3] for b in box)
            if (box_hi - box_lo) <= 2.5 * a15:
                if l < box_lo and c >= box_lo - 0.8 * a15:
                    st.amd_manips.append({"side": 1, "r_hi": box_hi, "r_lo": box_lo, "ext": l, "si": st.idx_15m})
                if h > box_hi and c <= box_hi + 0.8 * a15:
                    st.amd_manips.append({"side": -1, "r_hi": box_hi, "r_lo": box_lo, "ext": h, "si": st.idx_15m})
            b1, b2, b3 = st.bars_15m[-3], st.bars_15m[-2], st.bars_15m[-1]
            c2b = abs(b2[4] - b2[1])
            is_nsx = (st.symbol == self.nsx_sym)
            min_r = 5.0 if is_nsx else 0.5
            eng = "NSX_AMD_1D" if is_nsx else "AMD_Pro"
            still = []
            for mp in st.amd_manips:
                if st.idx_15m - mp["si"] > 8:
                    continue
                if mp["side"] == 1:
                    mp["ext"] = min(mp["ext"], l)
                    ok_1d = (not is_nsx) or (
                        st.sw_1d.trend == 1 and st.d1_er14 >= 0.20 and st.d1_ema20 is not None and st.d1_last_c > st.d1_ema20
                    )
                    if ok_1d and c > mp["r_hi"] and (b3[3] - b1[2]) >= 0.25 * a15 and b2[4] > b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == 1 and self._in_kz(dt):
                        self._submit_entry(st, eng, 1, b3[3], mp["ext"] - 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                else:
                    mp["ext"] = max(mp["ext"], h)
                    ok_1d = (not is_nsx) or (
                        st.sw_1d.trend == -1 and st.d1_er14 >= 0.20 and st.d1_ema20 is not None and st.d1_last_c < st.d1_ema20
                    )
                    if ok_1d and c < mp["r_lo"] and (b1[3] - b3[2]) >= 0.25 * a15 and b2[4] < b2[1] and c2b >= 0.8 * a15 and st.sw_1h.trend == -1 and self._in_kz(dt):
                        self._submit_entry(st, eng, -1, b3[2], mp["ext"] + 0.5 * a15, trail_after_r=2.0,
                                           expire_bars=300, min_risk=min_r, require_confirm=(not is_nsx))
                        continue
                still.append(mp)
            st.amd_manips = still
        # V9 consumes the completed 15m bar before the new swing is committed;
        # this preserves body-break and prior-ATR causality.
        self._v9_profile_bar(st, bar, atr_before)
        st.sw_15m.update(bar)

    def on_5m(self, st: AssetState, bar) -> None:
        st.idx_5m += 1
        dt = self.utc_time
        h, l, c, o = float(bar.High), float(bar.Low), float(bar.Close), float(bar.Open)
        a5 = st.atr_5m.update(h, l, c)
        st.bars_5m.append((dt, o, h, l, c))

        is_xau = st.symbol == self.xau_sym
        is_nsx_chop = st.symbol == self.nsx_sym and st.d1_er14 < 0.25
        if (is_xau or is_nsx_chop) and len(st.bars_5m) >= 3 and self._in_kz(dt):
            b1, b2, b3 = st.bars_5m[-3], st.bars_5m[-2], st.bars_5m[-1]
            c2b = abs(b2[4] - b2[1])
            buf = max(1.0 if is_xau else 4.0, 0.5 * a5)
            min_fvg = max(0.20, 0.20 * a5) if is_xau else 0.20 * a5
            v_eng = "VisB_Pro" if is_xau else "NSX_VisB_Chop"
            v_min_r = 1.0 if is_xau else 5.0
            still = []
            for sc in st.cands_1h_k3_5m:
                if st.idx_5m - sc["start_i"] > 12:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == 1 and sc["choch"] is not None and c > sc["choch"] and (b3[3] - b1[2]) >= min_fvg and b2[4] > b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, v_eng, 1, b3[3], sc["sl_base"] - buf, trail_after_r=1.5, expire_bars=90, min_risk=v_min_r)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and sc["choch"] is not None and c < sc["choch"] and (b1[3] - b3[2]) >= min_fvg and b2[4] < b2[1] and c2b >= 0.8 * a5:
                        self._submit_entry(st, v_eng, -1, b3[2], sc["sl_base"] + buf, trail_after_r=1.5, expire_bars=90, min_risk=v_min_r)
                        continue
                still.append(sc)
            st.cands_1h_k3_5m = still
        elif st.symbol == self.nsx_sym and st.cands_1h_k3_5m:
            st.cands_1h_k3_5m = [sc for sc in st.cands_1h_k3_5m if st.idx_5m - sc["start_i"] <= 12]

        st.sw_5m.update(bar)
        if st.symbol == self.btc_sym:
            st.atr_5m.val = a5
            self._ltf_bar(st, bar, 9, 0.0, 0.0020, 15.0, self.BTC_STEPS, "BTC_15R_BE", True)

    def on_data(self, data: Slice) -> None:
        for sym, st in self.assets.items():
            bar = self._bar(data, sym)
            if bar is None:
                continue
            st.bars_seen += 1
            if not self.is_warming_up and not st.in_position and st.pending_ticket is None and self.portfolio[sym].invested:
                self.transactions.cancel_open_orders(sym)
                self.liquidate(sym, tag="ORPHAN_SYNC")
                self.oco_cleanups += 1
            if sym != self.btc_sym:
                self._ltf_bar(st, bar, None, 0.0, 0.0, 0.0, (), "", False)

    def _check_confirm_setup(self, st: AssetState, dt, o: float, h: float, l: float, c: float) -> None:
        cs = st.confirm_setup
        if cs is None or st.in_position or st.pending_ticket is not None:
            return
        if st.ltf_idx > cs["exp"] or self._cfd_blocked(st, dt) or (cs["skip_hours"] and dt.hour in cs["skip_hours"]) or ((l <= cs["sl"]) if cs["side"] == 1 else (h >= cs["sl"])):
            st.confirm_setup = None
            return
        if not cs["touched"] and ((l <= cs["trig"]) if cs["side"] == 1 else (h >= cs["trig"])):
            cs["touched"] = True
        if cs["touched"]:
            ok_c = (c > o and c > cs["trig"]) if cs["side"] == 1 else (c < o and c < cs["trig"])
            if ok_c:
                st.confirm_setup = None
                self._submit_entry(st, cs["engine"], cs["side"], c, cs["sl"], tp=cs["tp"],
                                   trail_after_r=cs["trail_after_r"], step_locks=cs["step_locks"], is_market=True)

    def _ltf_bar(self, st: AssetState, bar, min_hr, min_abs: float, min_pct: float,
                 fixed_rr: float, step_locks, eng: str, allow_entries: bool) -> None:
        st.ltf_idx += 1
        dt = self.utc_time
        o, h, l, c = float(bar.Open), float(bar.High), float(bar.Low), float(bar.Close)
        a1 = st.atr_ltf.update(h, l, c)
        st.bars_ltf.append((dt, o, h, l, c))

        if st.in_position and st.risk_dist > 0 and st.sl_ticket is not None:
            if st.sl_ticket.status not in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.INVALID):
                for act_r, lk_r in st.step_locks:
                    hit = (h >= st.entry_price + act_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - act_r * st.risk_dist)
                    if hit:
                        self._try_lock_sl(st, st.entry_price + st.active_side * lk_r * st.risk_dist, c)
                if st.trail_after_r is not None and not st.trailing_active:
                    hit_tr = (h >= st.entry_price + st.trail_after_r * st.risk_dist) if st.active_side == 1 else (l <= st.entry_price - st.trail_after_r * st.risk_dist)
                    if hit_tr:
                        st.trailing_active, st.trail_mode = True, "1h"
                        self._try_lock_sl(st, st.entry_price + st.active_side * st.risk_dist, c)

        if st.pending_ticket is not None and st.pending_meta is not None:
            pm = st.pending_meta
            expires = (
                st.idx_15m > pm["expire_15m_idx"]
                if pm.get("expire_15m_idx") is not None
                else st.ltf_idx > pm["expire_idx"]
            )
            if expires or self._cfd_blocked(st, dt) or ((l <= pm["sl"]) if pm["side"] == 1 else (h >= pm["sl"])) or (pm["skip_hours"] and dt.hour in pm["skip_hours"]):
                self._cancel_pending(st)

        if not self.is_warming_up:
            self._check_confirm_setup(st, dt, o, h, l, c)

        if allow_entries and len(st.bars_ltf) >= 3 and (min_hr is None or dt.hour >= min_hr) and not self.is_warming_up:
            b1, b2, b3 = st.bars_ltf[-3], st.bars_ltf[-2], st.bars_ltf[-1]
            c2b, buf, min_r = abs(b2[4] - b2[1]), a1, max(min_abs, c * min_pct)
            still = []
            for sc in st.cands_1h_k3_ltf:
                if st.ltf_idx - sc["start_i"] > 60:
                    continue
                if sc["side"] == 1:
                    if l < sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == 1 and st.sw_1h.trend == 1 and sc["choch"] is not None and b3[4] > sc["choch"] and (b3[3] - b1[2]) >= 0.25 * a1 and b2[4] > b2[1] and c2b >= a1:
                        trig, sl = b3[3], sc["sl_base"] - buf
                        sl = self._floor_sl(st, 1, trig, sl, min_r, c)
                        if eng != "BTC_15R_BE" or (trig - sl) / max(1.0, c) < 0.018:
                            self._submit_entry(st, eng, 1, trig, sl, tp=trig + fixed_rr * (trig - sl), step_locks=step_locks, expire_bars=20, min_risk=min_r)
                        continue
                else:
                    if h > sc["sl_base"]:
                        continue
                    if st.sw_4h.trend == -1 and st.sw_1h.trend == -1 and sc["choch"] is not None and b3[4] < sc["choch"] and (b1[3] - b3[2]) >= 0.25 * a1 and b2[4] < b2[1] and c2b >= a1:
                        trig, sl = b3[2], sc["sl_base"] + buf
                        sl = self._floor_sl(st, -1, trig, sl, min_r, c)
                        if eng != "BTC_15R_BE" or (sl - trig) / max(1.0, c) < 0.018:
                            self._submit_entry(st, eng, -1, trig, sl, tp=trig - fixed_rr * (sl - trig), step_locks=step_locks, expire_bars=20, min_risk=min_r)
                        continue
                still.append(sc)
            st.cands_1h_k3_ltf = still
        st.sw_ltf.update(bar)

    def on_order_event(self, oe: OrderEvent) -> None:
        if oe.symbol not in self.assets:
            return
        st = self.assets[oe.symbol]
        if oe.status == OrderStatus.INVALID:
            self.invalid_counts[st.name] += 1
            if self.invalid_counts[st.name] <= 5:
                self.debug(f"INVALID {st.name} (id={oe.order_id}): {oe.message}")
            if st.pending_meta is not None and not st.in_position:
                st.pending_ticket = st.pending_meta = None
            elif st.in_position:
                self.transactions.cancel_open_orders(oe.symbol)
                self.liquidate(oe.symbol)
                st.in_position = False
                st.sl_ticket = st.tp_ticket = None
            return
        if oe.status == OrderStatus.CANCELED:
            if st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id:
                st.pending_ticket = st.pending_meta = None
            return
        if oe.status != OrderStatus.FILLED:
            return

        if ((st.pending_ticket is not None and oe.order_id == st.pending_ticket.order_id) or (st.pending_meta is not None and not st.in_position)) and st.pending_meta is not None:
            pm = st.pending_meta
            st.pending_ticket = st.pending_meta = None
            fill_px = float(oe.fill_price)
            st.in_position, st.active_engine, st.active_side = True, pm["engine"], pm["side"]
            st.entry_price, st.sl_price, st.tp_price = fill_px, pm["sl"], pm["tp"]
            st.risk_dist, st.trail_after_r, st.step_locks = abs(fill_px - pm["sl"]), pm["trail_after_r"], pm["step_locks"]
            st.trailing_active, st.trail_mode, st.qty, st.sl_ticket, st.tp_ticket = False, None, pm["qty"], None, None
            self.trade_counts[(st.name, pm["engine"])] += 1
            if st.risk_dist <= 0:
                self.liquidate(st.symbol)
                st.in_position = False
                return
            st.sl_ticket = self.stop_market_order(st.symbol, -pm["qty"], pm["sl"], tag=f"{pm['engine']}_SL")
            if st.in_position and pm["tp"] is not None:
                st.tp_ticket = self.limit_order(st.symbol, -pm["qty"], pm["tp"], tag=f"{pm['engine']}_TP")
            return

        self.transactions.cancel_open_orders(oe.symbol)
        st.in_position = False
        st.sl_ticket = st.tp_ticket = None
        if self.portfolio[oe.symbol].invested:
            self.liquidate(oe.symbol, tag="OCO_STRAY_CLEANUP")
            self.oco_cleanups += 1
        eq_now = float(self.portfolio.total_portfolio_value)
        if eq_now > self.hwm_equity:
            self.hwm_equity = eq_now

    def on_end_of_algorithm(self) -> None:
        self.log(f"=== V9 Asset Telemetry (oco_cleanups={self.oco_cleanups}) ===")
        for st in self.assets.values():
            self.log(
                f"  {st.name:10s} | bars={st.bars_seen} | submitted={st.orders_submitted} "
                f"| invalid={self.invalid_counts[st.name]} | V9_profile_evals={st.v9_profile_evals} "
                f"| V9_aggressive_blocks={st.v9_aggressive_blocks} | V9_valid_choch={st.v9_choch_valid}"
            )
        self.log("=== V9 / V8 Trade Breakdown by (Asset, Engine) ===")
        for (asset, eng), cnt in sorted(self.trade_counts.items()):
            self.log(f"  {asset:10s} | {eng:14s}: {cnt} trades")
