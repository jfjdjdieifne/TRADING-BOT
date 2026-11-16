# QUANTCONNECT.COM - V9 Dynamic Profile support core
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


class V9ProfileMixin:
    """V9 profile/data layer kept below QuantConnect's per-file size limit."""

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
