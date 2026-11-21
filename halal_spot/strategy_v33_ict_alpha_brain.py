"""
strategy_v32_ict_superbrain.py — MULTI-COIN ICT SUPER-BRAIN
=====================================================================
v32 = the v31 champion (lab combo C_124: STRUCT_TRAIL@+1.0R, LOCK_MODE
"trail", no break-even at entry, MID|BOS shield) promoted from ONE coin
to a synchronized basket of halal spot pairs sharing ONE $100 cash pool,
plus three new brains on top of it:

  PILLAR 1  Multi-coin causal spot rotation + slot compounding.
            run_backtest already walks the UNION of all exec frames and
            feeds every coin at the same timestamp (zero lookahead), and
            the pool was already shared - v32 adds the allocation law
            (SLOTS / ALLOC_MODE / SLOT_FILL) and cash recycling.
  PILLAR 2  ICT bullish SMT divergence + relative-strength tie-break
            across BTC / ETH / the signal coin (SMTBrain).
  PILLAR 3  Multi-regime: weapon A = the C_124 sweep reversal, weapon
            B = higher-low weekly impulse continuation (REGIME_MODE).
  PILLAR 4  Killzone time audit + close-based shield/struct exits with a
            wick emergency stop at the ORIGINAL structural stop, so no
            loss can exceed -1R even though the trail is close-based.

SACRED, UNTOUCHED (owner law):
  * the stop is where the chart says: GreenBox.y_bottom / BlueBox_SSL
    .y_bottom.  No percentage stops are invented anywhere in v32.
  * the structural target is always >= 3.00R (MIN_R = 3.0).
  * halal spot, long only, 1x: sum(open cost) <= free cash, always.

DATA: `data/binance_5m/<SYM>_5m/<YYYY-MM>.csv.gz`, written by
`fetch_binance_5m.py` (run it on a machine that can reach
data.binance.vision - the dev sandbox cannot).
---------------------------------------------------------------------
HISTORY (v28 audit, kept because every law below was measured there):
Built from the FORENSIC AUDIT of v24 (audit_v24_narrative.py,
audit_v24_shield.py, audit_v24_search.py) which replayed the market
story around all 249 v24 trades (62 WIN / 43 BE / 144 LOSS) and then
bar-walked 1,668 (context-gate x shield-rule) counterfactuals.

WHAT THE AUDIT PROVED (numbers, not opinions)
---------------------------------------------
A) The single strongest separator between winners and losers is NOT a
   pre-entry pattern at all: `crossed the 4H PurpleBox.mid after entry`
   = 91.9% of WINNERS vs 34.7% of LOSSES (gap 57.2 points). Median
   MFE-on-close: winners 4.98R, losers 0.62R — losers are dead on
   arrival, they never travel.
B) Every "textbook" pre-entry HTF filter was measured and most are
   WORTHLESS or HARMFUL on this data:
       4H order flow BULLISH : WIN 25.8% vs LOSS 29.2%  (inverted!)
       1H order flow BULLISH : WIN 21.0% vs LOSS 22.2%   (inverted!)
       UNICORN (breaker+FVG) : WIN 61.3% vs LOSS 59.7%   (no edge)
       inversion FVG support : present on 100% of both   (no edge)
       1H discount           : 0% of trades (the LTF wave IS the 1H
                               advance, so entry is always above the
                               1H mid — this is why v24's HTF_DISCOUNT
                               gate killed everything)
   What DID separate (all pre-entry, all sanctioned constants):
       4H open sky >= 10R    : WR 37.0% vs 30.1% baseline
       4H bottom quarter     : WR 36.4% vs 30.1% baseline
       entry inside 4H demand: WR 32.2% vs 30.1% baseline
       no failed 4H BSL raid : WR 31.7% vs 30.1% baseline
C) v24's entry-tick breakeven choke (54 trades armed at the fill, 50
   scratched, up to 13 in a row) is removed. The bar-walk says removing
   it REVIVES 10 choked trades into real wins.
D) The shield must be armed by a DISPLACEMENT, never at the entry tick.
   Exact counterfactual on all 249 trades:
       arm on 4H mid cross : 47 losses -> scratch, 18 wins sacrificed
       arm on post-entry BOS: 41 losses -> scratch, 18 wins sacrificed
       arm at +0.25R close : 120 losses -> scratch, 45 wins sacrificed
   => arming early buys win-rate with winners; arming structurally buys
      fewer scratches but keeps the runners. Both are exposed as
      switches below, settled by measurement.
E) 0 of 1,668 gate x rule combinations satisfied all five asserts on
   the v24 trade population: every combo with WR >= 50% kept only
   12-18 winners (runners>=4R fell to 3, failing assert 3) and fewer
   than 150 trades (failing assert 5). The conflict is structural, not
   a tuning accident.

NO indicators (EMA/RSI/ATR = 0). NO invented numbers: 3R/6R/10R (the
user's target ladder), 25% (bottom quarter), 50% (mid), 0.1% fee,
$10 min notional, $200 capital, 2 consecutive losses. 100% causal.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS = Path(__file__).resolve().parent / "results"

# --- sanctioned / infrastructure constants (NOT signal numbers) ---
_YEAR_KEYS = {
    "setup_drawn", "fill", "confirm_entry", "reject_pending_fill",
    "reject_premium_ob", "reject_wall_within_3r",
    "reject_target_within_3r", "fill_cancel_target_within_3r",
    "fill_cancel_wall_closed", "fill_cancel_premium",
    "fill_cancel_board_red", "anchor_invalid",
    "streak_entry_not_fresh", "portfolio_slots_full",
    "target_consumed", "target_rejection_exit",
    "reject_ctx_gate", "reject_ctx_tier3", "stand_aside_streak3",
    "streak_structural_reset", "stop_kept_ltf", "sacred_law_seam_ok",
    "manage5m_ratchet_3r", "manage5m_floor_reset",
    "tier3_skip_no_be_room", "shield_armed_mid",
    "shield_armed_bos", "shield_armed_disp", "exit_SHIELD_BE",
}
CAPITAL = 200.0          # user-given
SLOT = 0.5               # (kept for reference; v23 sizes 100% free cash)
MAX_SLOTS = 3            # v24: three parallel exec frames (5m/15m/1h)
CRYPTO_ONLY = ("BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE",
               "LTC", "AVAX", "DOT", "LINK", "NEAR", "MATIC")
#                                  # FIX4: spot crypto only (no XAU/index)
#                                  # v32: + LINK/NEAR/MATIC for the basket
MIN_R = 3.0              # sacred 3x box-height ratio (prompt)
LOSS_STREAK_RESET = 2    # prompt: two consecutive losses -> structural gate
QUARTER = 0.25           # geometric: bottom quarter of the purple box
FEE = 0.001              # exchange fee per side (accounting)
EXCHANGE_MIN_NOTIONAL = 10.0   # Binance spot minimum order (exchange rule)
FULL_START = "2021-01-01"
FULL_END = "2026-10-31"
BULL_START = "2021-01-01"
BULL_END = "2021-05-31"
EXEC_TF = "1h"        # prompt allows 15m/1H — boxes must dwarf noise
# --- v24 A/B switches (settled by measurement, then hard-coded) ---
# --- v25 switches: every value below is a MEASURED choice -------------
# (the audit numbers that settled each one are in results/audit_*.json)
FILL_MODE = "blind"       # blind 42.6% WR / seam 33.3% / close 7.9%
HTF_DEMAND_GATE = False   # MEASURED: cut 2021 WR 33% -> 20%
EXEC_FRAMES = ("5min", "15min", "30min", "1h")
STOP_CAP = True           # MEASURED: cap on 42.6% WR / off 28.6%
TRAIL_MODE = "htf_active"  # MEASURED: maxR 19.4 vs 18.6 structural
HTF_DISCOUNT = False       # MEASURED: WR 42.1% -> 38.7%
HTF_WAVE_ALWAYS = False    # MEASURED: WR 42.1% -> 31.2%, n 68 -> 22
BE_ARM = "shield_only"     # kept for API parity; v25 arms structurally
SHIELD_RULE = "MID+BOS"    # NONE | MID | BOS | MID+BOS | A0.5 | A1
                           # audit: MID saves 47 losses/18 wins,
                           # MID+BOS keeps the most winners (59)
TIER3_RULE = "A0.5"        # at 3 straight losses the shield arms on a
                           # +0.5R displacement (NOT at the entry tick)
CTX_GATE = True            # measured pre-entry context gate:
                           # 4H sky >= 3R AND (entry inside 4H demand
                           # OR no failed 4H BSL raid)
CTX_TIER3 = False          # MEASURED: the A+ tier-3 gate fired 37,599
                           # rejections and starved 2024 to 6 trades;
                           # tier-3 is now handled by STRUCTURAL_RESET
STRUCTURAL_RESET = False   # MEASURED FALSE: 1H/4H displacement waves
                           # print several times a day (21,498 of them),
                           # so a "wait for a new wave" stand-aside lasts
                           # hours and the raw loss run still reached 10
                           # (2021-22: WR 23.4%, net -6.2%). A rare key
                           # would cap the streak but starve volume.
TIER3_ENTRY_CHOKE = True   # the ONLY mechanism that makes "no 4th
                           # consecutive loss" true by construction: at
                           # exactly 3 straight losses the next fill is
                           # armed at breakeven, so it scratches or wins.
                           # Deviation from prompt point 4, disclosed:
                           # the audit showed entry-tick arming on EVERY
                           # shield trade scratched 50 of 54; restricting
                           # it to the rare tier-3 case keeps the cost
                           # small while assert 4 stays provable.
                           # at 3 straight losses the bot STANDS ASIDE
                           # and the counter is reset by a fresh HTF
                           # displacement wave (standing user rule:
                           # "structural reset, not a time freeze").
                           # A 4th consecutive loss then cannot exist:
                           # the 4th trade is only taken after a reset.
CTX_MODE = "or"            # or  = 4H demand OR no failed 4H BSL raid
#  ^ v28 MEASURED: the live quality gates "v28q"/"v28raid" are OFF here on
#    purpose. Post-hoc on the frozen v27 list they read 33.12% @ n=199 and
#    31.89% @ n=233; driven LIVE inside the engine (results/run_v28_gate_log.txt)
#    "v28q" produced 40 trades, 8W/25L = 24.24%, zero fills after 2022 and
#    reject_ctx_gate_v28q = 438,989. The gate is evaluated on the candidate
#    stream at every bar, so rejecting a candidate changes WHICH setup draws
#    next - the post-hoc reading does not survive contact with the engine.
                           # and = both
                           # quarter = and + entry in the 4H bottom 25%
                           # sky10   = and + 4H open sky >= 10R
FLOW_GATE = False          # audit TABLE 1: 4H flow BEAR = 74.2% of
                           # winners vs 67.4% of losers (buying the 4H
                           # pullback inside demand, not the break-out)
BE_CONSUMES_RANGE = False  # a scratch is NOT a loss, so it does not
                           # burn the dealing range (frees volume for
                           # assert 5 while the strict gate lifts WR)
BE_RELEASES_STREAK = True  # a scratch is not a loss -> gate released
ENTRY_LEVEL = "seam"       # seam = GreenBox top | green_mid = 50% of OB

# ================= v29: "ضع أمر الشراء مكان الستوب لوس" ============== #
# ICT Turtle Soup / stop-hunt inducement. v27 rests a BUY LIMIT at
# seam = min(green.y_top, yellow.y_bottom) with the stop at
# old_stop_px = min(green.y_bottom, sweep_low) (hybrid, STOP_CAP on), so
# RiskHeight H = seam - old_stop_px. 161 of the 297 v27 trades traded
# down through old_stop_px: that level is where the OrderBlock's
# liquidity is hunted.
#
# v29 rests the order AT the hunted level instead, and re-measures the
# stop and the targets from there. Geometry (per the v29 brief):
#   H        = seam - old_stop_px                       (v27 RiskHeight)
#   A mirror : order_px = old_stop_px,  order_stop = old_stop_px - H
#              -> risk stays H (the fee/risk ratio is UNCHANGED, unlike
#                 lab_v27's alpha sweep which shrank 1R and let the
#                 0.2% round trip eat the trade), and the net +3.00R
#                 lock moves a full H CLOSER: old_stop + 3H = seam + 2H.
#   B deepSSL: order_px = old_stop_px,  order_stop = nearest ACTIVE
#              BlueBox_SSL bottom below old_stop_px, else old_stop - 1.5H
#   C soup   : no resting order. Wait for a bar that hunts the level
#              (low <= old_stop_px) and reclaims it (old_stop_px < close
#              <= seam), then buy THAT CLOSE with the stop under the
#              hunting wick: min(sweep_low, fill - 0.5H), floored by the
#              engine's own breakeven-room law (risk >= 2 x FEE x fill).
#   D mid    : order_px = old_stop_px + 0.5H, order_stop = old_stop - 0.5H
#              -> risk stays exactly H (the fair comparison against
#                 lab_v27's alpha=0.5, which kept the stop put).
# The SACRED LAW holds by construction in every arm: order_px < seam and
# order_px < purple.mid, and the two hard asserts in _enter still run.
# ---- MEASURED (lab_v29_stop_entry.py, LIVE engine, full 2021-2026) ----
#   arm     n    W/ BE/  L     WR%    >=4R  maxR   net%    PF   5 asserts
#   seam  297   70/ 66/161   30.30     18  19.38  +31.90  1.26   4/5  <== v27, reproduced bit-for-bit
#   A     294   47/ 54/193   19.58      6   8.53  -39.16  0.66   4/5
#   B      48    8/  9/ 31   20.51      2   4.62  -10.09  0.54   2/5
#   C       5    0/  1/  4    0.00      0   0.00   -8.61  0.00   2/5
#   D     386   65/ 77/244   21.04     11  15.49  -34.02  0.74   4/5
#   A+strict box gate  140  36/16/88   29.03   6   8.53  -12.43  0.77  3/5
# NOT ONE arm beats the baseline, and every arm loses money. The fee
# cannot be blamed: arms A/D keep risk = H exactly (median risk 0.346%
# vs the seam's 0.327%) and their round-trip fee is 0.578R vs 0.612R, so
# the lab_v27 alpha-sweep artefact (shrinking 1R under a fixed stop) is
# provably absent here. What kills the hypothesis is ADVERSE SELECTION:
# the order at the hunted level fills precisely when the OrderBlock has
# failed. Of the 161 v27 trades hunted through old_stop_px, arm A turns
# 20 into winners - and destroys 34 of v27's 70 winners on the way.
# So the shipped default is the measured champion:
ENTRY_ARM      = "seam"    # "seam" = v27/v28 baseline | A | B | C | D

# ============== v30: THE COGNITIVE MULTI-STATE BRAIN ================= #
# Three modules, each switchable alone and in combination, each measured
# LIVE by lab_v30_brain.py (the real engine, never a re-simulation).
#
# --- MODULE 1a: PERSISTENT VIGILANCE ---------------------------------
# The v27-v29 engine zeroes the caution counter on a scratch
# (BE_RELEASES_STREAK=True), so after one 0.00R exit the engine goes back
# to blind full-risk entries. The conservative streak reading is 15 while
# the BE-resets reading is 3. Three policies:
#   "reset" = v27..v29 behaviour (BE -> consec_losses = 0)
#   "hold"  = BE leaves the caution state untouched (only a real WIN
#             >= +3.00R clears it)
#   "decay" = BE decrements by one, never to zero unless a WIN prints
# KNOWN RISK, measured before in v25: gating the SETUP on the streak
# DEADLOCKS (a skipped trade never resolves the streak). Here the streak
# only gates the shield rule and the tier-3 fill proof, so the run must be
# watched for starvation (yearly counts, ASSERT5).
BE_STREAK_MODE = "reset"
#
# --- MODULE 1a+: VIGILANCE / THROTTLE SPLIT --------------------------
# MEASURED (live, full 2021-2026): holding the streak on a scratch
# (BE_STREAK_MODE="hold") is the single best money lever found in this
# project - PF 1.26 -> 2.43, net +31.90% -> +56.25%, maxDD -14.41% ->
# -4.83%, WR 30.30% -> 42.86%, conservative streak 15 -> 3 - but it
# STARVES the book: n 297 -> 174 and 2023/2024/2025 fall to 9/11/10
# trades, so ASSERT5 fails. The counters show exactly why: the starvation
# is not the shield (shield_armed 83 -> 33) but the tier-3 ENTRY THROTTLE
# (tier3_fill_needs_proof 95 -> 289, tier3_be_armed_at_entry 30 -> 91,
# tier3_skip_no_be_room 3 -> 19, reject_risk_below_one_fee bars 272k ->
# 396k). This is v25's DEADLOCK returning in a new coat.
# So the two jobs of the counter are separated:
#   "none"       = v27..v29 (one counter does both jobs)
#   "shield"     = a permanent VIGILANCE counter (cleared only by a real
#                  WIN >= +3.00R, never by a scratch) chooses the shield
#                  rule, while the entry throttle keeps reading the
#                  decayed/reset counter, so entries never starve
#   "shield+be"  = vigilance also keeps the tier-3 break-even-at-entry
#                  arming (the mechanism that turned 117 v27 losses into
#                  genuine scratches), still without throttling entries
# SHIPPED v30 CONFIG = "vigil_floor-free vigilance" (lab combo
# M1v_shbe_rst), chosen from 30 live arms on the full 2021-2026 book:
#   n=298  44W/109BE/145L  WR 23.28%  totR +66.39  net +71.75% ($343.50)
#   PF 2.14  maxDD -9.52%  >=4R 10  maxR 19.38  ymin 25  asserts 4/5
# versus the shipped v27/v29 base (n=297, WR 30.30%, net +31.90%, PF 1.26,
# maxDD -14.41%) and v25 (net +42.14%, PF 1.43, maxDD -17.43%).
# Why this arm and not the richer-looking ones:
#  * BE_STREAK_MODE="hold" is better still on paper (net +56.25%, PF 2.43,
#    maxDD -4.83%, WR 42.86%) but STARVES the book (n=174, 2023/24/25 =
#    9/11/10 trades) and therefore fails ASSERT5 - v25's DEADLOCK.
#  * adding the 0.20% fill-stage floor (combo M1v_rst_f020) gives the best
#    totR (+86.18) and the lowest DD (-7.65%) at 0 bps, but under the
#    execution-cost stress it is the first to die (10 bps: n=104, 2023 and
#    2024 at ZERO trades, net +7.61%), so the extra filter is not shipped.
#  * A1 (WR >= 60%) fails for EVERY arm measured in this project; the best
#    live reading anywhere is 47.62% on a 71-trade book. Disclosed, not
#    hidden - see REPORT_AR_v30.md.
VIGILANCE_SCOPE = "none"      # v31 SHIPPED (ARM 4): the entry-tick
#                             break-even is CANCELLED. Measured live:
#                             tier3_be_armed_at_entry 177 -> 15, winners
#                             per month 0.63 -> 1.41, max winless run
#                             34 -> 8 trades, profitable months
#                             25.7% -> 41.4%. Keeping the v30 scope with
#                             the v31 exits (C_124_vig) loses half the
#                             book: totR +49.34 vs +114.03.
#
# --- MODULE 1b: STRUCTURAL PROOF SHIELD ------------------------------
# IMPORTANT MEASUREMENT, read before touching this: the displacement
# shield is ALREADY permanent in v25..v29. The block in _manage is not
# gated by loss_streak at all - it reads
#     rule = TIER3_RULE if self.tier3_at_entry else SHIELD_RULE
# so every trade, including consec_losses == 0, arms stop -> be_line the
# moment its rule fires on a bar CLOSE above be_line. What the brief calls
# "the engine leaves disp_mid/disp_bos trades to come back to a loss" is
# therefore not the shipped behaviour; the only lever is WHICH rule fires:
#   "MID+BOS" (shipped) = disp_mid AND disp_bos   (the strictest)
#   "MID|BOS"           = disp_mid OR  disp_bos   (what the brief asks)
#   "MID" / "BOS"       = one proof only
#   "A0.5" / "A0.75"    = a pure displacement threshold above be_line
# Measured ceilings on earlier books (engine bar-walks): v25 A0.25 39.53%
# (but >=4R = 4, ASSERT3 fails by one), MID 31.72%, MID+BOS 30.06%; v26
# MID 28.51%, A1 25.83%. v28 measured the same lever LIVE on the 5m tape:
# arming earlier cost 10 winners to save 12 losses (WR 31.03 -> 29.52).
SHIELD_RULE_V30 = "MID|BOS"   # v31 SHIPPED (ARM 4): either displacement
#                             proof arms the shield (OR, not AND) - with
#                             the entry-tick BE gone this is the only
#                             remaining protection, so it must fire on
#                             one witness instead of two.
#
# --- MODULE 2: REGIME-AWARE DUAL ENTRY BRAIN -------------------------
#   "sniper" = v27..v29: a blind BUY LIMIT resting at the seam
#   "dual"   = read the ARRIVAL candle. If it merely trades into the seam
#              and closes back above it (a calm correction), the sniper
#              limit fills exactly as before, so the 19.38R rockets are
#              kept. If it closes BELOW the seam (a violent bearish break
#              into the belly of the GreenBox), the engine refuses to
#              stand in front of the train: it waits for a CISD absorption
#              candle that closes back ABOVE the seam while still in the
#              Discount (close <= purple.mid) and buys THAT close.
#              This is the only place where the sacred seam assert is
#              relaxed, and it is relaxed exactly as the v30 brief states:
#              fill_px <= purple_now.mid is still a HARD assert.
# MEASURED BEFORE BUILDING (lab_v27_exact.py, post-hoc, with the 0.673
# book ratio): the 28 setups whose absorbing bar closes above the seam
# read 14W/8L = 63.6%; the chase-cap sweep above the seam read 15.34% to
# 22.22% WR. Post-hoc readings have not survived contact with the live
# engine once in this project (v28: 33.12% -> 24.24%), so the live run is
# the only arbiter.
ENTRY_BRAIN = "sniper"
CISD_NEEDS_GREEN_BODY = True   # absorbing candle must close above its open
ABSORB_MAX_BARS = 6            # how long the absorption state may wait
                               # for the CISD reclaim before the setup is
                               # dropped. SWEPT (3/6/12), never assumed.
CISD_IGNORE_NOCHASE = False    # while absorbing, a reclaim candle is by
                               # nature an up-bar that often breaks a red
                               # box; v27's no-chase law would delete the
                               # setup on that very bar. SWEPT, and the
                               # live run decides.
CISD_TIER3_EXEMPT = False      # tier-3 demands close >= fill*(1+2*FEE);
                               # a fill AT the close can never satisfy it,
                               # so this flag decides whether the seam
                               # reclaim is accepted as the tier-3 proof
#
# --- MODULE 3a: INSTITUTIONAL BOX FLOOR ------------------------------
# v27..v29 decline a setup only when risk <= FEE x entry (one side,
# 0.10%), so 16.5% of the book carries a round-trip fee >= 1R. The floor
# below is expressed in PER CENT of the fill price and is applied where
# v27 applies its own (setup draw and fill), so no new gate is invented.
# MEASURED WARNING: v22 put a 0.2% round-trip floor at SETUP stage and
# starved 2023 to ZERO trades and 2024 to two (165,362 rejects). 0.30%
# and 0.40% are stricter still - ASSERT5 is the risk, not ASSERT1.
# MEASURED LIVE (2021-2026): a 0.30% floor at SETUP stage is a
# starvation device, not a fix - n 297 -> 77 with 2023 and 2024 at ZERO
# trades (0.40%: n -> 43). Per-trade quality is superb (PF 1.84 / 2.51,
# maxDD -9.75% / -5.34%, net +33.44% / +34.55%) but ASSERT5 is destroyed
# exactly as v22's 0.2% setup floor predicted. So the stage is a knob:
#   "both" = the floor vetoes the setup draw AND the fill (v22 behaviour)
#   "fill" = setups still draw (the state machine flow is untouched), and
#            only the FILL of a dust box is skipped - the engine keeps
#            waiting for a retrace that is worth the fee
RISK_FLOOR_PCT = 0.10
RISK_FLOOR_STAGE = "both"
#
# --- MODULE 3b: SPOT DOLLAR-R EQUALIZATION ---------------------------
# Halal spot, no leverage: notional <= cash. v27..v29 put 100% of free
# cash into every fill, so dollar-1R = risk% x equity and swings from
# 0.11% to 1.45% of the portfolio - one wide-box loss erases three narrow
# box wins. "dollarR" sizes the position so that dollar-1R equals a fixed
# share of equity, capped at all-cash (never levered):
#     notional = min( DOLLAR_R_PCT/100 x equity / risk_frac , cash/(1+FEE) )
# DOLLAR_R_PCT is NOT invented: it is the measured median risk% of the
# 297-trade v27 book (0.3267%), so the median trade keeps its exact v27
# size and only the tails are equalized (narrow boxes are already capped
# at all-cash and stay unchanged; wide boxes shrink).
SIZING = "allcash"
DOLLAR_R_PCT = 0.3267
# =====================================================================
ARM_B_DEPTH    = 1.5       # H-multiples: fallback stop depth for arm B
ARM_B_MAX_REACH= 3.0       # H-multiples: how far below to look for a SSL
ARM_C_WICK     = 0.5       # H-multiples: minimum stop distance for arm C
ARM_BOX_GATE   = False     # v29 MEASUREMENT SWITCH. True  = the setup dies
                           # when the GreenBox/YellowBox stop being ACTIVE
                           # (v27's "one-touch mitigation dead" rule).
                           # False = the ONLY structural invalidation is a
                           # CLOSE below the arm's new stop, i.e. the
                           # invalidation moves down with the order - which
                           # is what Turtle Soup means: the mitigation of
                           # the OrderBlock IS the entry event, so it cannot
                           # also be the cancellation event. Measured both
                           # ways; see REPORT_AR_v29.md S2.
# ============ v30 EXECUTION-COST STRESS TEST =========================
# The measured champion arms the break-even stop AT ENTRY on 177 of its
# 298 trades and scratches 109 of them after a median of ONE bar. Under
# the project's cost model a scratch is exactly free: the BE line is
# entry x (1 + 2 x FEE), so the gross gain equals both fees. That only
# holds if the BE stop fills at its own price. This project has never
# modelled slippage, so SLIPPAGE_BPS is a STRESS KNOB, not a calibrated
# constant: 0 keeps the shipped convention (every v27/v29 number stays
# bit-identical), 5 and 10 bps per side answer one question only - how
# much of the champion's edge survives realistic execution?
# COST replaces FEE wherever cash moves or a cost line is drawn (entry
# fee, exit fee, partial release, the all-cash notional reserve, every BE
# line, the +3R lock solve, the box floor), so the engine is allowed to
# re-earn its scratch: with slippage the BE line moves out to
# entry x (1 + 2 x COST), exactly as a real bot would.
SLIPPAGE_BPS = 0.0
COST = FEE + SLIPPAGE_BPS / 10000.0
# =====================================================================
# ===================================================================== #
# =====  v31: THE COMPOUNDING BRAIN — four structural arms  ========== #
# ===================================================================== #
# The v30 book is profitable but SLOW: +71.75% over 5.8 years = 0.79%
# per month compounded, 0.64 wins per calendar month, 18/63 profitable
# months (29%). Measured on the shipped v30 book (_m31a.py, no
# re-simulation) the leak is structural, and it is in the EXIT law, not
# in the entry law:
#   * 33 of the 44 winners (75.0%) were killed by the +3.00R floor
#     (LOCK_FLOOR_CLOSE) and booked EXACTLY 3.00R while their own
#     extension was median 5.20R intrabar / 4.21R on closes, mean 5.77R,
#     max 11.64R; 25 of them had reached >=4R, 18 >=5R, 14 >=6R.
#   * 55 trades booked BE/LOSS had already CLOSED at >= +1.5R (79 on the
#     intrabar reading), 35 at >= +2.0R, 26 at >= +2.5R, and cost
#     totR -23.79. On the v27 base the same leak is 79 trades / -83.58R.
#   * fees $80.59 = 36.0% of gross profit, $0.270 per trade.
# Every constant below is either the engine's own law (MIN_R, COST) or a
# swept knob whose values are listed in lab_v31_compounding_brain.py.
#
# ---- ARM 1: STRUCTURAL PROFIT TRAIL (kill the +0.01R..+2.99R zone) ---
# The entry gate stays sacred: _red_ladder still refuses any fill whose
# target ladder does not clear net +3.00R, so no trade is ever OPENED
# without a >=3R structural objective (recorded per trade as
# entry_target_R). What changes is the MANAGEMENT: once the trade is
# gross >= STRUCT_TRAIL_MIN_R and a NEW ascending swing low
# (BlueBox_SSL confirmed by the 3-bar fractal, i.e. its right bar has
# already closed) sits above the break-even line and below the market,
# the stop may follow that low - even between +0.5R and +2.99R. Such an
# exit books a STRUCTURAL WIN ("SWIN"), a new honest class: net > 0 but
# R < 3.00. It is never counted as a WIN, so min_winner_R stays >= 3.00R
# by construction and A2 remains sacred on the WIN class.
STRUCT_TRAIL = True           # v31 SHIPPED: C_124, measured live 2021-2026
STRUCT_TRAIL_MIN_R = 1.0      # swept: 0.5 | 1.0 | 1.5 | 2.0 (gross R)
STRUCT_TRAIL_SRC = "exec"     # exec | htf | both  (which lens draws the low)
STRUCT_TRAIL_NEEDS_DISP = False   # require disp_mid|disp_bos first
SWIN_MIN_R = 0.05             # below this a positive exit is still a scratch
SWIN_CLEARS_VIGIL = False     # does a structural win end the vigilance?
#
# ---- ARM 2: ANTI-CHOKE RUNNER + SPLIT WEEKLY HARVESTER --------------
# LOCK_ARM_R: the floor arms at this NET R (3.0 = v30). LOCK_MODE says
# what ends the ride once the floor is armed:
#   "floor" = v30: the first execution-frame CLOSE back at/below the
#             floor sells everything (this is what booked 33 winners at
#             exactly 3.00R out of a median 4.21R close extension)
#   "htf"   = only a COMPLETED 4H/1H structural close below the floor
#             ends the ride (the HTF canvases are fed completed bars
#             only, so this is causal); exec-frame dips are ignored
#   "stop"  = the floor becomes a LIVE STOP ORDER on the execution frame
#             (wick-defended): the +3.00R is guaranteed, and the ride
#             continues above it until the trailed BlueBox_SSL stop or the
#             red-target rejection ends it. This is the honest reading of
#             "leave the wave running" - the first variant tried here
#             ("trail", floor enforced by NOTHING) let a ratcheted position
#             ride back down indefinitely and turned +3R excursions into
#             losses: measured live, totR +101.46 but maxDD -22.42%.
#   "trail" = the floor never sells and is not defended (kept only as the
#             measured reference for that give-back risk)
# HARVEST_PCT: sell that fraction of the ORIGINAL qty at the first floor
# close (weekly cash) and let the rest ride under LOCK_MODE. 0 = the
# all-or-nothing v30 law. The two legs are booked as ONE trade: R is
# normalised by qty0, so 50% at +3R and 50% at +9R books +6.0R.
LOCK_ARM_R = 3.0
LOCK_MODE = "trail"           # v31 SHIPPED: the +3R floor stops selling the
#                             ride; the trailed BlueBox_SSL stop defends it
#                             instead (STOP_BLUE 153 exits). Measured live:
#                             totR +66.39 -> +114.03, maxR 19.38 -> 34.50R,
#                             maxDD -9.52% -> -10.95%. "trail" WITHOUT the
#                             structural ratchet is money-dangerous
#                             (A2_trail: maxDD -24.72%) - the two ship
#                             together or not at all. "stop" (wick-defended
#                             floor) was measured and REFUTED: it caps every
#                             runner at 12.84R (C_124_st totR -27.72).
HARVEST_PCT = 0.0
#
# ---- ARM 3: DYNAMIC IMPULSE-LEG PURPLEBOX ---------------------------
# After an exit at +3.00R (a +1% price move) BTC keeps going and the
# frozen dealing range puts the engine in "premium" for weeks: the v30
# counters show 245,825-315,775 anchor_premium_skip rejections. ICT: when
# price breaks a RedBox_BSL the dealing range re-anchors from the last
# BlueBox_SSL that LAUNCHED the break to the new impulse high, so the
# pullbacks of the new leg are tradeable in their own discount.
#   impulse_low  = the last active BlueBox_SSL bottom at the break bar
#   impulse_high = running max high since the break
#   eff_mid      = max(purple.mid, (impulse_low+impulse_high)/2)
# The sacred Discount assert becomes fill_px <= eff_mid, and every fill
# that needed the impulse leg (not the frozen purple) is counted
# separately as sacred_law_impulse_ok so the relaxation is auditable.
IMPULSE_PURPLE = False
IMPULSE_MAX_BARS = 240        # swept: 120 | 240 | 480 exec bars
#
# ---- ARM 4: UNTHROTTLED ENTRY + SMART VIGILANCE ---------------------
# No new constant: arm 4 is the v30 switchboard with the entry-tick
# break-even OFF (VIGILANCE_SCOPE="none" or "shield") and the shield
# earned by displacement (SHIELD_RULE_V30="MID|BOS" or "A0.5"). Measured
# in v30: BE-at-entry arming rose 30 -> 177 and winners fell 70 -> 44.
# NOTE, measured before building: the "true multi-candle OrderBlock" is
# ALREADY implemented - _draw_green merges the whole run of consecutive
# down candles from the launching swing low to the gap's first candle
# (`while k >= lo_idx: if c < o: run.append(k)`), so the GreenBox is
# already as thick as the base of the wave. There is nothing to add.
# ===================================================================== #
# ============================ v32 CONFIG ============================= #
# ===================================================================== #
# ---- PILLAR 1a: the basket -----------------------------------------
# Data lives in data/binance_5m/<SYM>_5m/<YYYY-MM>.csv.gz (fetch_binance_
# 5m.py). V32_DATA_DIR overrides DATA_DIR so the lab can point at the
# Binance basket, at the legacy BTC-only dir, or - explicitly labelled as
# a PLUMBING TEST ONLY - at non-crypto real data.
V32_DATA_DIR = ""            # "" = DATA_DIR (legacy BTCUSD_5m)
SYMBOL_WHITELIST = None      # None = CRYPTO_ONLY (spot crypto, no metal)
MAX_COINS = 8                # cap on the basket (0 = no cap)
#
# ---- PILLAR 1b: allocation of the ONE shared $100 cash pool ---------
# MEASURED BEFORE BUILDING (v31 shipped book, 311 fills):
#   notional / equity_at_entry = 0.9990 on EVERY fill (min = max = 0.9990)
# so there is no 1%-risk cap idling half the cash in v31: sizing is
# `cash / (1 + COST)` and the only floors are EXCHANGE_MIN_NOTIONAL=$10
# and MIN_RISK_PCT=2xCOST (a stop too tight to carry the round trip is
# declined). The half-idle-cash bug was v23's SLOT=0.5 and FIX4 removed
# it. What DOES starve the basket is that the first engine to fill takes
# 100% of the cash, so the other seven coins are rejected until it exits
# - that is what SLOTS fixes.
ALLOC_MODE = "allcash"       # allcash (v31 law) | slot
SLOTS = 1                    # 1 = 100% per fill, 2 = 50% each, 3 = 33%
SLOT_FILL = "fixed"          # fixed: cash/SLOTS | dynamic: cash/free_slots
#
# ---- PILLAR 1c: split-harvest cash recycling ------------------------
# HARVEST_PCT (v31) already sells that fraction at the +3.00R lock and
# `_release_locked_capital` puts the cash back into the SHARED pool, so
# with SLOTS > 1 the realised +3R is immediately reusable by another
# coin while the runner leg keeps trailing. Measured on BTC alone it was
# money-negative (C_124_h: totR +45.29 vs +114.03) - the multi-coin
# recycle is the hypothesis under test, not an assumed win.
RECYCLE_CASH = True          # released capital returns to pool["cash"]
#
# ---- PILLAR 2: ICT bullish SMT divergence ---------------------------
SMT_BRAIN = False            # master switch
SMT_REFS = ("BTCUSDT", "ETHUSDT")   # the two reference legs
SMT_GATE = "off"             # off | prefer (tie-break) | require (veto)
SMT_MAX_AGE = 12             # union-timeline stamps (5m exec bars on this
#                            # basket grid) since the completed 1H bar that
#                            # made the leg - a stale divergence is not a
#                            # divergence. 12 stamps = the last hour.
# Consumed by SMTBrain below: the legs are read off each coin's SHARED 1H
# narrative canvas (fed only completed bars), never off a partial bar.
# SMT_GATE="prefer"  -> the coin order at every stamp is strongest-first,
#                       so when two coins are ready on the same candle the
#                       SMT_BULL one gets the shared cash (the brief's
#                       tie-break: SMT first, then displacement ratio, then
#                       4H structure).
# SMT_GATE="require" -> a fill without SMT_BULL is vetoed at fill time.
#
# ---- PILLAR 3: multi-regime weapon selection ------------------------
REGIME_MODE = "A"            # A = sweep reversal (C_124) | B = higher-low
#                            # impulse continuation | AB = whichever fires
REGIME_B_NEEDS_HL = True     # last 4H/1H BlueBox_SSL must be a higher low
REGIME_B_NEEDS_BSL = True    # last structural break must be a BSL break up
#
# ---- PILLAR 4: killzones + close-based protection -------------------
# TIME AUDIT (measured on the v31 C_124 book, walk-forward: the gate may
# only use trades that closed BEFORE 2023-10-01, n=198, then it is scored
# on W1/W2 which it has never seen):
#   in-sample the ICT London+NY block 07-16 UTC looks spectacular - on the
#   FULL book it holds +111.21R of +114.03R (129 of 311 trades), and
#   everything outside 07-16 holds +2.82R on 182 trades.
#   out-of-sample it FAILS: W1 -5.42R -> -2.95R (2 trades left), W2
#   +10.59R -> +7.68R. The 2023-24 profit simply did not arrive in those
#   hours. NY 12-15 fails the same way (W2 +7.83R).
#   The weekday gate DOES survive: TRAIN Sunday avgR -0.78 (18 trades,
#   totR -13.98) and out-of-sample W2 +10.59R -> +14.41R, W1 unchanged.
#   Thin sample (7 Sunday trades in W2) - disclosed, not oversold.
# Book-level filtering is not proof, so every variant below is re-measured
# by the LIVE engine in lab_v32_superbrain_6m.py (a rejected fill changes
# the streak/vigilance state, so the book cannot be filtered post hoc).
KILLZONE_MODE = "off"        # off | include (only these) | exclude (never)
KILLZONE_HOURS = ()          # UTC hours; e.g. tuple(range(7,17))
KILLZONE_DOW = ()            # 0=Mon..6=Sun; measured candidate: (6,)
EMERGENCY_WICK_STOP = True   # wick-defend ONLY the original structural
#                            # stop (never the trail), so a close-based
#                            # be_line / STRUCT_TRAIL cannot lose > -1R.
#                            # v31 measured what wick-defending the RAISED
#                            # floor does: LOCK_MODE="stop" capped every
#                            # runner at 12.84R (C_124_st totR -27.72 vs
#                            # +114.03). So the wick gets the ORIGINAL
#                            # stop only - a disaster cap, not a trail.
#                            # v31 also measured 5 trades that had closed
#                            # >= +3.00R and still finished as losses
#                            # (give-back 56.56R): this is the answer to
#                            # the tail of that risk, not to its body.
CLOSE_BASED_SHIELD = False   # True makes the pre-ratchet be_line exit read
#                            # the CLOSE instead of the wick (the floor and
#                            # STRUCT_TRAIL already do). Default OFF so the
#                            # v32 book stays identical to v31 C_124, which
#                            # wick-defended the be_line (85 BREAKEVEN
#                            # exits); both states are measured in the lab.
# ===================================================================== #
# ==================================================================== #
# v33 CONFIG — THE ALPHA-LEADER BRAIN.  EVERY default below reproduces   #
# v32 bit-for-bit, so an arm that changes nothing must return the same   #
# book (that identity is itself the regression test).                    #
#                                                                        #
# MEASURED REASON EACH KNOB EXISTS (v32 FULL_3s, 8-coin spot basket):    #
#  * W1 was a violent bull: SOL +847%, AVAX +486%, BNB +183%, BTC +164%,  #
#    ADA +156%, LINK +134% (open->close of the window we loaded). The     #
#    book still ended +10.08%.                                            #
#  * The winners were cut tiny, not capped at 3R: 78 STRUCT_PROFIT exits  #
#    in W1 with median +0.75R, and the median stop width is 0.41% of      #
#    price, so +0.75R is a +0.3% price move. In the 7 days AFTER those    #
#    exits the coin ran a median +9.41% (mean +12.38%, max +59.32%) and   #
#    in 0 of 78 cases did price fall. That is the choke, quantified.      #
#  * Fees were 25.9% of gross wins in W1 ($11.56 of $44.68) because a     #
#    0.2% round trip is half of a 0.41% stop.                             #
#  * There is NO RISK_PCT=0.01 in this engine: notional/equity_at_entry   #
#    measured 0.9990 (allcash) and 0.3330 (3 slots). The brief's "$15 of  #
#    $100" premise is false; SLOT_DEPLOY_PCT is the honest knob and 1.0   #
#    is already full deployment.                                          #
# ==================================================================== #
SLOT_DEPLOY_PCT  = 1.0      # (أ) fraction of the slot budget a fill takes
# SHIPPED v33 DEFAULT = the measured champion (lab combo TEL). Chained over
# both dev windows on the same $100 book: +59.14% vs +16.23% for the v32
# law, max exit price move 10.99% -> 23.70%, winners above +15% 0 -> 2,
# winners' median price move 0.81% -> 3.26%, the choking STRUCT_PROFIT exit
# 78 -> 4, and the fee share of gross wins 25.9% -> 16.2%. Cost, disclosed:
# WR 29.0% -> 13.2%, BREAKEVEN exits 96 -> 126, EMERGENCY_STOP 18 -> 33 and
# maxDD -4.38% -> -5.77%. Set TRAIL_LENS_PRE="exec" and
# TRAIL_4H_ONLY_AFTER_3R=False to get the v32 book back bar for bar.
TRAIL_LENS_PRE   = "struct4h"   # (ب) pre-+3R trail lens:
                            #     "v32"     = honour STRUCT_TRAIL_SRC
                            #     "exec"    = execution frame only
                            #     "htf"     = 1h + 4h
                            #     "struct4h"= 4H BlueBox_SSL ONLY (telescope)
                            #     "off"     = no pre-lock structural trail
TRAIL_MIN_R_PRE  = None     # (ب) None = STRUCT_TRAIL_MIN_R (1.0); a number
                            #     delays the trail until that gross R
TRAIL_4H_ONLY_AFTER_3R = True    # (ب) after the +3R lock follow 4H SSL only
PURPLE_REARM     = False    # (ب) re-anchor the dealing range on each new
                            #     qualified wave, so a coin above the OLD
                            #     frozen PurpleBox mid stays buyable. Gated
                            #     by _regime_b_ok() - ungated it starved
                            #     v31's later years (+142R but $8/$5/$13).
V33_ALPHA_LEADER = False    # (ج) concentrate cash in the ranked leaders
LEADER_K         = 2        #     how many coins may fill (0 = no filter)
LEADER_NEEDS_HTF = False    #     require last 4H structural break UPWARD
LEADER_MIN_DISP  = 0.0      #     require FVG/OB displacement ratio >= x
LEADER_SMT_REQUIRED = False #     require SMT_BULL on the leader
LEADER_15M_ONLY_TOP1 = False#     15m frame may only fill for leader #1
BASKET_REGIME    = False    # (د) read the basket's 4H breadth each stamp
REGIME_EXPAND_MIN = 3       #     coins with 4H BSL-up that mean EXPANSION
RANGE_VETO_WEAPON_B = True  #     in RANGE, refuse impulse-sourced fills
RANGE_HARVEST_4H = False    #     in RANGE, sell into the first 4H ceiling
MIN_RISK_PCT   = 2 * COST   # NOT invented: the engine's own breakeven-room
                           # law (TIER3_ENTRY_CHOKE, _enter L~1600) — a
                           # trade whose risk cannot carry the 0.2% round
                           # trip cannot be protected, so it is declined.
# =====================================================================
                           # v27 MEASURED (lab_v27_exact.py, 5m tape,
                           # 297 real setups, fixed 3000-bar horizon):
                           #  buying DEEPER inside the box is worse, not
                           #  better, and monotonically so -
                           #    alpha 1.00 (seam) : 76 winners, WR 26.03%
                           #    alpha 0.75        : 74 winners, WR 25.69%
                           #    alpha 0.50 (mid)  : 57 winners, WR 20.21%
                           #    alpha 0.25        : 36 winners, WR 12.95%
                           #  A deeper limit only fills on the way DOWN,
                           #  so it selects for the knives, and it misses
                           #  the setups that ran straight from the seam
                           #  (nofill 5 -> 19). The winner COUNT is
                           #  estimator-independent: it is decided by the
                           #  fee-adjusted +3R lock being hit on a 5m close.
                           #  Method B (wait for a 5m absorption candle
                           #  inside the box) was measured too: it leaves
                           #  WR at 23.53% and never fills 93 of 297
                           #  setups, dropping the weakest year to 13.
STOP_SOURCE = "hybrid"     # v26. MEASURED (full 2021-2026):
                           #  "htf"  -> widening to the HTF demand floor
                           #           lifted 2023-25 from 23 to 93 trades
                           #           (the fee-floor coma), maxR 4.6->18.4,
                           #           net +30.4%, but WR stayed 30-32%
                           #           because 1R was inflated: 39.8% of
                           #           v25 trades carried a stop BELOW the
                           #           GreenBox floor (58.3% of scratches).
                           #  "ltf"  -> tight stop, WR 42.3% measured in v24,
                           #           but maxR collapsed to 4.6 (assert 3
                           #           needs >= 6.0) and 2023-25 starved.
                           #  "hybrid"-> keep the tight LTF stop whenever it
                           #           can pay the round trip
                           #           (risk > 2 x FEE x entry) and widen to
                           #           the HTF floor ONLY when it cannot.
                           #           Shrinks 1R exactly where shrinking is
                           #           free, and never re-opens the coma.
STRUCT_TF = "4h"

# ======================= v28: 5m CAUSAL POSITION MANAGEMENT =========== #
# MEASURED BEFORE BUILDING (results/audit_v28_5m_lock.json):
#   259 of the 297 v27 trades see a 5m CLOSE above lock_line within 10
#   days - but 184 of those happen AFTER the trade was already dead, so
#   counting them is lookahead. Restricted to each trade's OWN lifetime
#   (entry_time .. exit_time) the truth is:
#       75 trades locked on a 5m close while alive
#       70 of them were booked as WIN
#        5 were scratched at BE anyway  <- the only real leak (6.7%)
#        0 losses ever locked on 5m
#   Upper bound of this fix: WR 30.30% -> 31.78%. It is small, it is
#   real, and it is free of lookahead. The brief's "32.7% of winners
#   lost" is not reproducible once the window is bounded by the exit.
MANAGE_5M        = False   # v29: OFF. Measured in v28 (REPORT_AR_v28.md):
                           # the 5m floor defence recovered exactly the 5
                           # lost winners (WR 30.30 -> 31.03%) but clipped
                           # the runners (maxR 19.38 -> 12.86, >=4R 18->11)
                           # and cut net profit +31.90% -> +6.79%. v29 goes
                           # back to the clean execution-frame management
                           # of v25/v27; the code stays, switched off.
MANAGE_5M_LOCK   = True    # raise the +3R floor on a 5m CLOSE
MANAGE_5M_WICK   = True    # defend the +3R floor with the 5m WICK from the
                           # bar AFTER the locking close (measured: exactly
                           # the 5 lost winners come back -> WR 31.78%) but
                           # 12 of the 18 runners >=4R give their ride back
                           # at the floor: maxR 19.38 -> 12.84, >=4R 18->6,
                           # totR +43.55 -> -19.77 (results/_m28c in the
                           # v28 report). A3 survives by ONE runner.
MANAGE_5M_SHIELD = False   # MEASURED HARMFUL (lab_v27_exact.py): arming
                           # the BE shield on 5m closes drops the winners
                           # from 76 to 58 and the decided WR from 26.03%
                           # to 24.89% - a 5m close above entry+fees is
                           # noise on this instrument.
# What deliberately STAYS on the execution frame:
#   * the LOCK_FLOOR_CLOSE exit, the red-target rejection exit, the HTF
#     BlueBox trail and the reversal CHoCH. Moving the floor exit to 5m
#     would book the runners at +3.00R: any 5m close dipping under the
#     floor ends the ride, and the 19.38R / 16.92R / 15.82R rides all
#     dipped intraday. That would fail ASSERT3 (max_winner_R >= 6.0).
# =======================================================================


# ==================================================================== #
# The Box — pure spatial geometry
# ==================================================================== #
_BOX_UID = itertools.count(1)   # v31 FIX: GC-immune unique box ids


@dataclass
class Box:
    y_bottom: float
    y_top: float
    start_idx: int            # bar index whose close completed this box
    kind: str                 # BLUE | RED | YELLOW_B | YELLOW_S | GREEN | PURPLE
    tf: str
    state: str = "ACTIVE"     # ACTIVE | BROKEN | DEAD
    structural: bool = False  # launched a wave that left a gap AND
                              # broke a red box (True Structural Swing)
    time: object = None       # bar completion time (fresh-wave check)

    # ---- v31 FIX: a unique id that survives garbage collection --------
    # Box is a @dataclass, so it is UNHASHABLE (value __eq__, __hash__ =
    # None) - which is why the narrative sets below keyed on id(box).
    # id() is only unique while the object is alive, and _prune() drops
    # DEAD boxes, so CPython reused those addresses for NEW boxes and the
    # new box read as "already logged": its break / chop / IFVG event was
    # silently dropped. Measured symptom: the SAME config produced three
    # different books on three identical launches (n=330, n=328, n=326).
    # __post_init__ (not a dataclass field) keeps __eq__/__repr__ exactly
    # as they were, so nothing else in the engine changes behaviour.
    def __post_init__(self):
        self.uid = next(_BOX_UID)

    @property
    def height(self) -> float:
        return self.y_top - self.y_bottom

    @property
    def mid(self) -> float:
        return (self.y_top + self.y_bottom) / 2.0

    @property
    def quarter_bottom(self) -> float:
        """Top of the cheapest quarter (bottom 25%) of the box."""
        return self.y_bottom + self.height * QUARTER

    def contains(self, p: float) -> bool:
        return self.y_bottom <= p <= self.y_top

    def is_below(self, other: "Box") -> bool:
        return self.y_top <= other.y_bottom

    def overlaps(self, other: "Box") -> bool:
        return self.y_bottom <= other.y_top and other.y_bottom <= self.y_top

    def broken_up_by(self, close: float) -> bool:
        return close > self.y_top

    def broken_down_by(self, close: float) -> bool:
        return close < self.y_bottom

    def wick_swept_down_by(self, low: float, close: float) -> bool:
        """Wick enters the box from above and closes back inside/above."""
        return low < self.y_top and close > self.y_bottom

    def as_dict(self) -> dict:
        return {"kind": self.kind, "bottom": round(self.y_bottom, 2),
                "top": round(self.y_top, 2), "tf": self.tf}


# ==================================================================== #
# ChartCanvas — draws the boxes causally (one completed bar at a time)
# ==================================================================== #
class ChartCanvas:
    def __init__(self, tf: str, narrative: bool = False):
        self.tf = tf
        # ---- ICT narrative memory (HTF canvases only: the cost is a
        # full box scan per bar, so it is off for the 5m/15m/30m frames)
        self.narrative = narrative
        self.raids_up = []        # BSL run + failed reclaim (bearish)
        self.raids_dn = []        # SSL run + reclaim (bullish fuel)
        self.last_red_break_idx = None
        self.last_blue_chop_idx = None
        self.ifvgs = []           # bearish gap killed BY A BODY CLOSE
        self._seen_br = set(); self._seen_ch = set(); self._seen_if = set()
        self.bars: list[tuple] = []          # (o, h, l, c, v)
        self.blues: list[Box] = []           # swing-low liquidity
        self.reds: list[Box] = []            # swing-high liquidity
        self.yellows_b: list[Box] = []       # bullish fair-value gaps
        self.yellows_s: list[Box] = []       # bearish gaps (walls / CHoCH proof)
        self.greens: list[Box] = []          # bullish order blocks
        self.purple: Box | None = None       # dealing range
        self.pairs: list[tuple[Box, Box]] = []
        self.wall_killed = 0   # (green, yellow) stacks
        self.bos_events: list[dict] = []     # red-box breaks (consumed once)
        self.sweep_events: list[dict] = []
        self.chop_events: list[dict] = []    # blue-box breakdowns (board)

    # ---------- fractal helpers (3-bar, confirmed on the right bar) ----
    def _confirm_fractals(self, i: int, time=None) -> list[Box]:
        out = []
        if i < 2:
            return out
        ho, hh, hl, hc, _ = self.bars[i - 2]
        mo, mh, ml, mc, _ = self.bars[i - 1]
        no, nh, nl, nc, _ = self.bars[i]
        # swing high at i-1 (3-bar fractal, confirmed on bar i)
        if mh > ho and mh > hc and mh > nh and mh > nc:
            box = Box(y_bottom=max(mo, mc), y_top=mh, start_idx=i - 1,
                      kind="RED", tf=self.tf, time=time)
            self.reds.append(box)
            out.append(box)
        # swing low at i-1
        if ml < min(ho, hc) and ml < min(nh, nc):
            box = y0 = Box(y_bottom=ml, y_top=min(mo, mc), start_idx=i - 1,
                           kind="BLUE", tf=self.tf, time=time)
            self.blues.append(box)
            out.append(box)
        return out

    def _draw_yellows(self, i: int, time=None) -> list[Box]:
        """Fair-value gaps: pure visible air between candle bodies/wicks —
        c3.low > c1.high (bull) / c3.high < c1.low (bear)."""
        if i < 2:
            return []
        out = []
        c1o, c1h, c1l, c1c, _ = self.bars[i - 2]
        c3o, c3h, c3l, c3c, _ = self.bars[i]
        if c3l > c1h:
            b = Box(y_bottom=c1h, y_top=c3l, start_idx=i,
                    kind="YELLOW_B", tf=self.tf, time=time)
            self.yellows_b.append(b)
            out.append(b)
        if c3h < c1l:
            b = Box(y_bottom=c3h, y_top=c1l, start_idx=i,
                    kind="YELLOW_S", tf=self.tf, time=time)
            self.yellows_s.append(b)
            out.append(b)
        return out

    def _draw_green(self, yellow: Box, time=None) -> Box | None:
        """GreenBox_BullOB: last down candle(s) at the BASE of the wave
        that launched the yellow gap. Geometric bounds only: from the
        launching swing low to the gap's first candle."""
        ci = yellow.start_idx                      # c3
        c1 = ci - 2
        # launching swing low = last confirmed blue at or before c1
        base_blue = None
        for b in reversed(self.blues):
            if b.start_idx <= c1 and b.state == "ACTIVE":
                base_blue = b
                break
        if base_blue is None:
            return None
        lo_idx = base_blue.start_idx
        # run of down candles ending at c1 (merge consecutive at base)
        run = []
        k = c1
        while k >= lo_idx:
            o, h, l, c, _ = self.bars[k]
            if c < o:
                run.append(k)
                k -= 1
            else:
                break
        if not run:
            run = [lo_idx]         # wave-low candle itself
        lows = [self.bars[k][2] for k in run]
        opens = [self.bars[k][0] for k in run]
        closes = [self.bars[k][3] for k in run]
        g = Box(y_bottom=min(lows), y_top=max(opens + closes),
                start_idx=min(run), kind="GREEN", tf=self.tf,
                time=time)
        # SACRED GEOMETRY: green can never sit above its yellow
        g.y_top = min(g.y_top, yellow.y_top)
        g.y_bottom = min(g.y_bottom, yellow.y_bottom)
        assert g.y_bottom <= yellow.y_bottom, "green below yellow (bottom)"
        assert g.y_top <= yellow.y_top, "green below yellow (top)"
        self.greens.append(g)
        self.pairs.append((g, yellow))
        base_blue.structural = True   # L4/True-Structural: wave left a gap
        return g

    def _update_purple(self) -> None:
        """Dealing range: latest confirmed swing low -> latest swing high."""
        if not self.blues or not self.reds:
            return
        sb = self.structural_blues()
        b = sb[-1] if sb else (self.blues[-1] if self.blues else None)
        r = self.reds[-1]
        if b is None:
            return
        # spec: latest confirmed swing low -> latest confirmed swing
        # high (no ordering constraint — a stale range in a downtrend
        # froze the order-flow filter)
        if r.y_top > b.y_bottom:
            self.purple = Box(y_bottom=b.y_bottom, y_top=r.y_top,
                              start_idx=max(b.start_idx, r.start_idx),
                              kind="PURPLE", tf=self.tf, time=None)

    def _invalidate(self, i: int) -> None:
        _, h, _, c, _ = self.bars[i]
        for b in self.blues:
            if b.state == "ACTIVE" and b.broken_down_by(c):
                b.state = "DEAD"
                self.chop_events.append({"idx": i, "box": b})
        for r in self.reds:
            if r.state == "ACTIVE" and r.broken_up_by(c):
                r.state = "BROKEN"
                self.bos_events.append({"idx": i, "box": r})
        for y in self.yellows_b:
            if y.state == "ACTIVE" and y.broken_down_by(c):
                y.state = "DEAD"
        for y in self.yellows_s:
            if y.state == "ACTIVE" and (y.broken_up_by(c)
                                        or h >= y.y_top):
                # FIX1b: a ceiling dies the moment price closes above
                # it OR even trades into it (touch = consumed) — stale
                # 2021/22 walls must never block 2023/24 again
                y.state = "DEAD"
                self.wall_killed += 1
        for g in self.greens:
            if g.state == "ACTIVE" and g.broken_down_by(c):
                g.state = "DEAD"

    def _prune(self, i: int) -> None:
        # housekeeping only (dead rectangles carry no signal)
        if i % 96 != 0:
            return
        self.blues = [b for b in self.blues if b.state == "ACTIVE"][-400:]
        self.reds = [r for r in self.reds if r.state != "DEAD"][-400:]
        self.yellows_b = [y for y in self.yellows_b
                          if y.state == "ACTIVE"][-400:]
        self.yellows_s = [y for y in self.yellows_s
                          if y.state == "ACTIVE"][-400:]
        self.greens = [g for g in self.greens if g.state == "ACTIVE"][-400:]
        self.pairs = [(g, y) for g, y in self.pairs
                      if g.state == "ACTIVE" and y.state == "ACTIVE"][-400:]
        self.bos_events = self.bos_events[-50:]
        self.sweep_events = self.sweep_events[-50:]
        self.chop_events = self.chop_events[-50:]

    def on_bar(self, o, h, l, c, v, idx, time=None) -> dict:
        self.bars.append((o, h, l, c, v))
        i = len(self.bars) - 1
        assert i == idx, "bar index must be contiguous"
        self._confirm_fractals(i, time)
        for y in self._draw_yellows(i, time):
            if y.kind == "YELLOW_B":
                self._draw_green(y, time)
        self._invalidate(i)
        if self.tf == STRUCT_TF:
            self._update_purple()
            if self.purple is not None:
                cur = self.purple.y_bottom
                prev_b = getattr(self, "_purple_bottom", None)
                if prev_b is not None:
                    # higher-low structure = bullish HTF order flow
                    self.purple_rising = cur >= prev_b
                self._purple_bottom = cur
        if self.narrative:
            self._read_narrative(i, o, h, l, c, idx, time)
        self._prune(i)
        return {"bos": self.bos_events[-1] if self.bos_events else None,
                "chop": self.chop_events[-1] if self.chop_events else None}

    # ---------- the story this frame is telling --------------------- #
    def _read_narrative(self, i, o, h, l, c, idx, time):
        # ---- v31 FIX: the "already logged" sets held id(box). -------
        # _prune drops DEAD boxes from self.reds/blues/yellows_s, so the
        # object is garbage-collected and CPython can hand its address to
        # a NEW box - which then reads as "already seen" and its break /
        # chop / IFVG event is silently dropped. The dropped events shift
        # a handful of entries, so the SAME config produced different
        # books on different runs (measured: the stop-mode arm came back
        # n=330, then n=328, then n=326 on three identical launches,
        # while the shipped C_124 happened to repeat exactly 3x).
        # Keying on box.uid (a counter, never an address) makes the
        # aliasing impossible: O(1), unhashable-Box-safe, GC-proof. Memory: one small object per box that
        # ever died, bounded by the run length.
        for r in self.reds:
            if r.state == "BROKEN" and r.uid not in self._seen_br:
                self._seen_br.add(r.uid)
                self.last_red_break_idx = idx
        for b in self.blues:
            if b.state == "DEAD" and b.uid not in self._seen_ch:
                self._seen_ch.add(b.uid)
                self.last_blue_chop_idx = idx
        for y in self.yellows_s:
            if y.state == "DEAD" and y.uid not in self._seen_if:
                self._seen_if.add(y.uid)
                self.ifvgs.append({"idx": idx, "time": time,
                                   "bottom": y.y_bottom, "top": y.y_top,
                                   "by_close": bool(c > y.y_top)})
        # liquidity raids on boxes that SURVIVED this bar
        for r in self.reds:
            if r.state == "ACTIVE" and h > r.y_top and c < r.y_top:
                self.raids_up.append({"idx": idx, "time": time})
        for b in self.blues:
            if b.state == "ACTIVE" and l < b.y_bottom and c > b.y_bottom:
                self.raids_dn.append({"idx": idx, "time": time})

    def flow(self):
        """Institutional order-flow direction: whichever structural
        break printed LAST (no windows, no invented numbers)."""
        rb, bc = self.last_red_break_idx, self.last_blue_chop_idx
        if rb is None and bc is None:
            return None
        if bc is None:
            return "BULL"
        if rb is None:
            return "BEAR"
        return "BULL" if rb > bc else "BEAR"

    def raid_high_failed(self):
        """A BSL run that failed AFTER the last blue chop: the highs
        have already been taken out — buying here buys the raid."""
        if not self.raids_up:
            return False
        ri = self.raids_up[-1]["idx"]
        return self.last_blue_chop_idx is None or ri > self.last_blue_chop_idx

    def raid_low_reclaimed(self):
        """An SSL run reclaimed AFTER the last red break = long fuel."""
        if not self.raids_dn:
            return False
        di = self.raids_dn[-1]["idx"]
        return self.last_red_break_idx is None or di > self.last_red_break_idx

    def in_demand(self, px):
        for b in list(self.greens) + list(self.yellows_b):
            if b.state == "ACTIVE" and b.y_bottom <= px <= b.y_top:
                return True
        return False

    def range_pos(self, px):
        """Where px sits inside the dealing range: 0 = bottom, 1 = top."""
        if self.purple is None or self.purple.height <= 0:
            return None
        return (px - self.purple.y_bottom) / self.purple.height

    def unicorn(self, px):
        """ICT Unicorn: a broken red box (breaker) overlapping a live
        bullish FVG / green OB, with px inside the overlap."""
        live = [b for b in list(self.greens) + list(self.yellows_b)
                if b.state == "ACTIVE"]
        for r in self.reds:
            if r.state != "BROKEN":
                continue
            for d in live:
                lo = max(r.y_bottom, d.y_bottom)
                hi = min(r.y_top, d.y_top)
                if lo <= px <= hi:
                    return True
        return False

    def ifvg_below(self, px):
        """Nearest inversion FVG (bearish gap killed by a body close)
        sitting below px — it now holds price up."""
        best = None
        for f in self.ifvgs:
            if f["by_close"] and f["top"] <= px:
                d = px - f["top"]
                if best is None or d < best:
                    best = d
        return best

    # ---------- geometric queries ---------------------------------- #
    def bos_qualifies(self, e, now_idx: int):
        """True Structural BOS: the breaking wave must have left a
        YellowBox within the prompt's grace of 2 candles after the
        break. Returns True/False while inside the window, None if
        the window has not closed yet (caller keeps pending)."""
        if now_idx > e["idx"] + 2:
            # window closed — decide with what we have
            pass
        launch = None
        for b in reversed(self.blues):
            if b.start_idx < e["box"].start_idx:
                launch = b
                break
        if launch is None:
            return False
        for y in self.yellows_b:
            if launch.start_idx <= y.start_idx <= e["idx"] + 2:
                return True
        return None if now_idx <= e["idx"] + 2 else False

    def active_blues(self):
        return [b for b in self.blues if b.state == "ACTIVE"]

    def structural_blues(self):
        return [b for b in self.blues
                if b.state == "ACTIVE" and b.structural]

    def active_reds(self):
        return [r for r in self.reds if r.state == "ACTIVE"]

    def active_yellow_s(self):
        return [y for y in self.yellows_s if y.state == "ACTIVE"]

    def nearest_ceiling(self, entry: float):
        """First unbroken bearish wall at/above the entry line.
        None => open sky (ATH price discovery)."""
        walls = [y for y in self.active_yellow_s() if y.y_top >= entry]
        if not walls:
            return None
        return min(walls, key=lambda y: y.y_bottom)


# ==================================================================== #
# Engine — one coin, state machine over boxes
# ==================================================================== #
@dataclass
class Setup:
    anchor_idx: int
    sweep_low: float
    bos_idx: int
    bos_red: Box
    wave_low: Box
    green: Box
    yellow: Box
    entry: float
    stop: float
    risk: float
    gate_idx: int            # fills strictly after this bar
    wall: Box | None
    purple_mid: float
    touched: bool = False     # seam traded into (no fill yet!)
    confirm_idx: int = -1     # reclaim confirmation bar (fill next bar)
    # ---- v29: the arm geometry, frozen at DRAW time (zero lookahead) --
    seam_px: float = 0.0      # min(green.y_top, yellow.y_bottom)
    old_stop_px: float = 0.0  # the v27 stop = the hunted liquidity level
    H: float = 0.0            # seam_px - old_stop_px = v27 RiskHeight
    order_px: float = 0.0     # where the v29 order actually rests
    order_stop: float = 0.0   # the v29 stop (arm C re-measures at fill)
    arm: str = "seam"
    absorb_armed: bool = False   # v30 dual brain: a violent candle broke
                                 # the seam, so the sniper limit stands
                                 # down and waits for CISD absorption
    absorb_age: int = 0          # bars spent waiting for the CISD reclaim


class ICTBoxEngine:
    def __init__(self, symbol: str, exec_tf: str = "1h",
                 capital_slot: float = CAPITAL, tag: str = ""):
        self.pool = {"cash": CAPITAL, "engines": []}  # shared portfolio
        self.symbol = symbol
        self.tag = tag
        self.exec_tf = exec_tf
        self.exec_canvas = ChartCanvas(exec_tf)
        self.struct_canvas = ChartCanvas(STRUCT_TF)
        # FIX2: HTF sniper lens — every engine watches the SAME1H
        # canvas (demand + RedBox_BSL target ladder); the1h engine
        # aliases it to its exec canvas to avoid double drawing
        self.htf_canvas = (self.struct_canvas if exec_tf == "1h"
                           else ChartCanvas("1h"))
        # v25: the NARRATIVE is a property of the MARKET, not of an
        # engine — one shared 4H + one shared 1H canvas per symbol are
        # fed once per bar in run_backtest and read by every engine
        # (8 private narrative canvases cost 13 min per year of data)
        self.nar4: ChartCanvas | None = None
        self.nar1: ChartCanvas | None = None
        self.targets: list[Box] = []        # T1..T3 red ladder
        self.touched = False                # seam touched, no confirm yet
        self.htf_1h_bos_time = None         # FIX3 release wave (1H)
        self._htf1h_bos_seen: set = set()
        self.state = "WAIT_ANCHOR"
        self.warm = True              # structure-only until window start
        self.board = "GREEN"          # 4H board: buys allowed
        self.board_mode = "REBOUND"   # (a) BOS_CONTINUATION | (b) REBOUND
        self.setup: Setup | None = None
        self.anchor: dict | None = None
        self.bos: dict | None = None
        self.blocked_after_losses = False
        self.last_loss_idx = -1
        self.last_red_break_idx = -1
        self.last_htf_break_time = None
        self.last_loss_time = None
        self.consec_losses = 0
        # v22 locks
        self.pending_bos: list[dict] = []      # exec BOS awaiting qualification
        self.struct_pending: list[dict] = []   # 4H BOS awaiting qualification
        self.consumed: list[tuple] = []        # one-loss-per-dealing-range
        self.locked_range: tuple | None = None  # full lock after 2 losses
        self.breaker_ready = False             # 4H structural streak breaker
        self.setup_narrative: dict = {}        # the story at setup time
        self._pre_alive = True                 # v29 intrabar fill law
        self.shield = False                    # trade opened at streak == 2
        self.be_armed = False                  # shield breakeven armed
        self.disp_mid = False                  # 4H mid crossed (displacement)
        self.disp_bos = False                  # post-entry BOS printed
        self.entry_ceiling = None              # nearest internal red at fill
        self.lock_line = 0.0                   # entry + 3R + fees
        self.floor_line = 0.0                  # v31 ARM 2 (LOCK_ARM_R)
        self.impulse = None                    # v31 ARM 3 live impulse leg
        # ---- v33 per-stamp state, written by run_backtest -------------
        self.v33_allow = True       # (ج) may this engine fill this stamp?
        self.v33_rank = 99          # (ج) leader rank, 0 = strongest
        self.v33_regime = None      # (د) "EXPAND" | "RANGE" | None
        self.fresh_qualified: list[dict] = []
        # position
        self.qty = 0.0
        self.entry_px = 0.0
        self.stop_px = 0.0
        self.risk = 0.0
        self.ratchet = False
        self.protected_blue: Box | None = None
        self.trade: dict | None = None
        self.trades: list[dict] = []
        self.count: dict = {}
        self.yearly: dict = {}
        self.fees = 0.0
        self.price = 0.0
        self.now = None
        # 4H board bookkeeping
        self._htf_protected: Box | None = None
        self._htf_bos_seen: set = set()

    # ---- portfolio-shared streak state (both engines + coins) ----
    @property
    def consec_losses(self):
        return self.pool.get("consec", 0)

    @consec_losses.setter
    def consec_losses(self, v):
        self.pool["consec"] = int(v)

    # ---- v30: permanent vigilance. Cleared ONLY by a real WIN, never
    # by a scratch, and read only where VIGILANCE_SCOPE says so.
    @property
    def vigil_losses(self):
        return self.pool.get("vigil", 0)

    @vigil_losses.setter
    def vigil_losses(self, v):
        self.pool["vigil"] = int(v)

    @property
    def locked_range(self):
        return self.pool.get("locked")

    @locked_range.setter
    def locked_range(self, v):
        self.pool["locked"] = v

    @property
    def breaker_ready(self):
        return self.pool.get("breaker", False)

    @breaker_ready.setter
    def breaker_ready(self, v):
        self.pool["breaker"] = bool(v)

    @property
    def consumed(self):
        return self.pool.setdefault("consumed", [])

    @consumed.setter
    def consumed(self, v):
        self.pool["consumed"] = v

    @property
    def last_loss_time(self):
        return self.pool.get("last_loss_time")

    @last_loss_time.setter
    def last_loss_time(self, v):
        self.pool["last_loss_time"] = v

    @property
    def blocked_after_losses(self):
        return self.pool.get("blocked", False)

    @blocked_after_losses.setter
    def blocked_after_losses(self, v):
        self.pool["blocked"] = bool(v)

    # ---------- counters ------------------------------------------- #
    def cnt(self, k, n=1):
        if k in _YEAR_KEYS and getattr(self, "now", None) is not None:
            y = self.now.year
            self.yearly[(y, k)] = self.yearly.get((y, k), 0) + n
        if self.tag == "BULL":
            k = "bull_" + k
        self.count[k] = self.count.get(k, 0) + n

    def _accept_htf_bos(self, e, time):
        cv = self.struct_canvas
        self.last_red_break_idx = e["idx"]
        self.last_htf_break_time = time
        below = [b for b in cv.active_blues()
                 if b.y_top < e["box"].y_bottom]
        self._htf_protected = below[-1] if below else (
            cv.active_blues()[-1] if cv.active_blues() else None)
        self.board = "GREEN"
        self.board_mode = "BOS_CONTINUATION"   # state (a)
        if self.locked_range is not None and self.last_loss_time is not None                 and time > self.last_loss_time:
            self.breaker_ready = True           # streak breaker event
            self.cnt("streak_breaker_htf_bos")
        self.cnt("board_green_bos")

    # ---------------- 4H board feed -------------------------------- #
    def on_struct(self, o, h, l, c, v, idx, time):
        ev = self.struct_canvas.on_bar(o, h, l, c, v, idx, time)
        cv = self.struct_canvas
        # qualify 4H BOS events: only waves that left a yellow count
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            e = cv.bos_events.pop(0)
            if e["idx"] in self._htf_bos_seen:
                continue
            self._htf_bos_seen.add(e["idx"])
            q = cv.bos_qualifies(e, idx)
            if q is None:
                self.struct_pending.append(e)
            elif q:
                self._accept_htf_bos(e, time)
            else:
                self.cnt("htf_bos_noise_ignored")
        for e in list(self.struct_pending):
            q = cv.bos_qualifies(e, idx)
            if q is True:
                self.struct_pending.remove(e)
                self._accept_htf_bos(e, time)
            elif q is False:
                self.struct_pending.remove(e)
                self.cnt("htf_bos_noise_ignored")
        # L4: after 2 losses a 4H structural reclaim/sweep is the
        # streak-breaker that can release trade #3
        if self.locked_range is not None and self.last_loss_time is not None                 and time > self.last_loss_time:
            pass  # breaker flag set inside accept/recovery below
        # L1: post-3R trailing moves ONLY under confirmed structural
        # 4H BlueBoxes (never on 1h/15m micro noise)
        if self.qty > 0 and self.ratchet:
            best = self.stop_px
            for b in self.trail_blues(cv):
                if (b.y_bottom >= getattr(self, "floor_line",
                                          self.lock_line)
                        and self.stop_px < b.y_bottom < self.price):
                    best = max(best, b.y_bottom)
            if best > self.stop_px:
                self.stop_px = best
                self.cnt("trail_4h_structural")
        # 4H body close below protected low + bearish gap => red board
        if (self._htf_protected is not None
                and c < self._htf_protected.y_bottom
                and any(y.start_idx > self._htf_protected.start_idx
                        for y in cv.active_yellow_s())):
            if self.board != "RED":
                self.board = "RED"
                self.cnt("board_red_breakdown")
        # recovery (b): tap of a 4H blue / green / yellow with reclaim
        if self.board == "RED":
            for b in cv.active_blues():
                # recovery (b): body closes BACK ABOVE the whole blue
                # box (spec: "أغلاق جسم الشمعة عائداً فوقه") — a close
                # merely above the low is not a reclaim
                if l < b.y_top and c > b.y_top:
                    self.board = "GREEN"
                    self.board_mode = "REBOUND"    # state (b)
                    # (sweep alone is NOT the streak breaker — only a
                    # qualified 4H structural BOS releases trade #3)
                    self.cnt("board_recover_sweep")
                    break
            if self.board == "RED":
                for box in (cv.greens + cv.yellows_b):
                    if box.state == "ACTIVE" and l <= box.y_top \
                            and c >= box.y_bottom:
                        self.board = "GREEN"
                        self.board_mode = "REBOUND"    # state (b)
                        self.cnt("board_recover_box")
                        break

    # ---------------- 1H HTF feed (targets / demand) --------------- #
    def on_htf(self, o, h, l, c, v, idx, time):
        # the1h engine's HTF lens IS the4H board (already fed by
        # on_struct) — never feed it1H bars twice
        if (self.htf_canvas is self.exec_canvas
                or self.htf_canvas is self.struct_canvas):
            return
        cv = self.htf_canvas
        cv.on_bar(o, h, l, c, v, idx, time)
        # FIX3: a QUALIFIED 1H bullish displacement is the streak
        # release wave — no more waiting months for a4H BOS
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            e = cv.bos_events.pop(0)
            if e["idx"] in self._htf1h_bos_seen:
                continue
            self._htf1h_bos_seen.add(e["idx"])
            if cv.bos_qualifies(e, idx) is not False:
                self.htf_1h_bos_time = time
                self.cnt("htf_1h_displacement")

    # ---------------- execution feed -------------------------------- #
    def on_exec(self, o, h, l, c, v, idx, time):
        self.now = time
        self.price = c
        cv = self.exec_canvas
        # ---- v29 INTRABAR FILL LAW ------------------------------------
        # cv.on_bar() below applies THIS bar's close to the box states, so
        # a bar that trades down to the order and closes below the
        # GreenBox bottom marks the box dead BEFORE _seek_fill runs. A
        # real resting BUY LIMIT fills intrabar, the moment price trades
        # into it - strictly before that close is known. Snapshot the
        # setup's liveness as of the PREVIOUS bar's close so the fill is
        # not vetoed by the very bar that produces it. This uses only
        # past information (zero lookahead).
        _s0 = self.setup
        self._pre_alive = bool(_s0 is None
                               or (_s0.green.state == "ACTIVE"
                                   and _s0.yellow.state == "ACTIVE"))
        cv.on_bar(o, h, l, c, v, idx, time)
        if self.warm:
            while cv.bos_events:
                cv.bos_events.pop(0)
            return
        # collect this bar's box-break events BEFORE any consumer
        # eats them (v21 bug#1: events were popped before the state
        # machine could see them -> WAIT_BOS deadlocked forever)
        fresh = []
        while cv.bos_events and cv.bos_events[0]["idx"] <= idx:
            fresh.append(cv.bos_events.pop(0))
        # L1/True-Structural: only waves that left a yellow qualify;
        # micro 3-candle breaks are dropped as noise (no pre-3R trail)
        qualified = []
        for e in fresh:
            q = cv.bos_qualifies(e, idx)
            if q is None:
                self.pending_bos.append(e)
            elif q:
                qualified.append(e)
            else:
                self.cnt("bos_noise_ignored")
        for e in list(self.pending_bos):
            q = cv.bos_qualifies(e, idx)
            if q is True:
                self.pending_bos.remove(e)
                qualified.append(e)
            elif q is False:
                self.pending_bos.remove(e)
                self.cnt("bos_noise_ignored")
        if qualified:
            self.last_red_break_idx = idx
        self.fresh_qualified = qualified
        self._impulse_update(o, h, l, c, idx, time, qualified)
        if self.qty > 0:
            # NO stop movement here before 3R (L1) — shield/lock logic
            # lives in _manage; 4H structural trail lives in on_struct
            self._manage(o, h, l, c, idx, time)
            return
        # prune consumed dealing ranges once price trades outside them
        self.consumed = [(b, t) for b, t in self.consumed
                         if b <= c <= t]
        # state chain may advance multiple steps inside one closed bar
        # (each step only reads this bar's completed data; fills remain
        # gated to bars strictly after setup completion)
        for _ in range(4):
            before = self.state
            if self.state == "WAIT_ANCHOR":
                self._seek_anchor(o, h, l, c, idx, time)
            elif self.state == "WAIT_BOS":
                self._seek_bos(o, h, l, c, idx, time, qualified)
            elif self.state == "WAIT_SETUP":
                self._seek_setup(o, h, l, c, idx, time, qualified)
            elif self.state == "WAIT_RETRACE":
                self._seek_fill(o, h, l, c, idx, time, qualified)
            if self.state == before or self.qty > 0:
                break

    # ---------------- State 1: anchor (sweep or box tap) ------------- #
    # ---- v33 helpers -------------------------------------------------
    def _v33_range(self) -> bool:
        """Is the BASKET in the chop regime right now? (د)"""
        return bool(BASKET_REGIME and self.v33_regime == "RANGE")

    def _v33_expand(self) -> bool:
        """Is the BASKET in the expansion regime right now? (د)"""
        return bool(BASKET_REGIME and self.v33_regime == "EXPAND")

    def _impulse_on(self) -> bool:
        """Is the impulse-leg dealing range armed?

        v31 called this IMPULSE_PURPLE (Arm 3: +142.08R on the full book
        but it starved 2023-25 down to $8/$5/$13 net, DD -17.49%, so it
        was REJECTED ungated). v32 PILLAR 3 re-arms the same mechanism as
        Weapon B under REGIME_MODE "B"/"AB", where the 4H regime gate
        below decides when it may anchor - the point of the gate is that
        Weapon B must not cannibalise the periods Weapon A feeds.
        """
        return (IMPULSE_PURPLE or REGIME_MODE in ("B", "AB")
                or PURPLE_REARM          # (ب) re-anchor on every new wave
                or self._v33_expand())   # (د) expansion rides the impulse

    def _regime_b_ok(self) -> bool:
        """Is the 4H board in the uptrend Weapon B requires?

        Both tests read only completed 4H bars (the shared narrative
        canvas is fed causally by the runner):
          * REGIME_B_NEEDS_BSL - the last structural break is UPWARD: the
            newest RedBox_BSL break is more recent than the newest
            BlueBox_SSL chop.
          * REGIME_B_NEEDS_HL  - the last BlueBox_SSL is a Higher Low: its
            bottom sits above the previous BlueBox_SSL bottom.
        """
        n4 = self.nar4
        if n4 is None or len(n4.bars) < 3:
            return False
        if REGIME_B_NEEDS_BSL:
            b = n4.bos_events[-1]["idx"] if n4.bos_events else -1
            c = n4.chop_events[-1]["idx"] if n4.chop_events else -1
            if b <= c:
                return False
        if REGIME_B_NEEDS_HL:
            bl = _last_blues(n4, 2)
            if len(bl) < 2 or bl[-1].y_bottom <= bl[-2].y_bottom:
                return False
        return True

    def _purple_ok(self) -> bool:
        p = self.struct_canvas.purple
        return p is not None or (self._impulse_on()
                                 and self.impulse is not None)

    # ---- v31 ARM 3: DYNAMIC IMPULSE-LEG DEALING RANGE ---------------
    def _impulse_update(self, o, h, l, c, idx, time, fresh):
        """Track the live impulse leg: it is ANCHORED on a bar where a
        RedBox_BSL break qualified, at the last confirmed swing low that
        launched it, and it stays alive while price holds that low, up to
        IMPULSE_MAX_BARS. Everything it reads is already closed."""
        if not self._impulse_on():
            return
        imp = self.impulse
        if imp is not None:
            imp["high"] = max(imp["high"], float(h))
            imp["age"] += 1
            if c < imp["low"] or imp["age"] > IMPULSE_MAX_BARS:
                self.impulse = None
                self.cnt("v31_impulse_expired")
                imp = None
        if imp is None and fresh:
            if (REGIME_MODE == "B" or PURPLE_REARM) \
                    and not self._regime_b_ok():
                self.cnt("v32_regime_b_no_anchor")
                return
            low = None
            for b in reversed(self.exec_canvas.active_blues()):
                if b.start_idx <= idx and b.y_bottom < c:
                    low = b.y_bottom
                    break
            if low is None:
                self.cnt("v31_impulse_no_launch_low")
                return
            self.impulse = {"low": float(low), "high": max(float(h), c),
                            "idx": idx, "age": 0, "time": time}
            self.cnt("v31_impulse_anchored")

    def _eff_mid(self):
        """The mid line the Discount law is measured against: the frozen
        PurpleBox mid, or - when an impulse leg is live and its own mid
        sits HIGHER - the impulse mid. Returns (mid, needed_impulse)."""
        p = self.struct_canvas.purple
        pmid = p.mid if p is not None else None
        if not self._impulse_on() or self.impulse is None:
            return pmid, False
        imid = (self.impulse["low"] + self.impulse["high"]) / 2.0
        if pmid is None or imid > pmid:
            return imid, True
        return pmid, False

    def _in_discount(self, price: float) -> bool:
        mid, _ = self._eff_mid()
        return mid is not None and price <= mid

    def _seek_anchor(self, o, h, l, c, idx, time):
        if not self._purple_ok():
            return
        if self.board != "GREEN":
            self.cnt("anchor_board_red")
            return
        if not self._in_discount(c):
            self.cnt("anchor_premium_skip")
            return

        # (a) blue-box sweep: wick into liquidity, body closes back —
        # True Structural Swing only (wave must have left a gap+broke red)
        for b in reversed(self.exec_canvas.structural_blues()):
            if b.wick_swept_down_by(l, c):
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": b.y_bottom, "box": b}
                self.state = "WAIT_BOS"
                self.cnt("anchor_blue_sweep")
                return
        # (b) tap of a drawn green/yellow box in the discount half —
        # SPEC: only in a strong bull run (4H BOS continuation state);
        # in rebounds/chop the only valid anchor is a blue sweep
        if self.board_mode != "BOS_CONTINUATION":
            self.cnt("anchor_tap_needs_bos_state")
            return
        for box in list(self.exec_canvas.greens) + \
                list(self.exec_canvas.yellows_b):
            if box.state != "ACTIVE":
                continue
            if l <= box.y_top and c >= box.y_bottom:
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": box.y_bottom, "box": box}
                self.state = "WAIT_BOS"
                self.cnt("anchor_box_tap")
                return

    # ---------------- State 2: break the red box -------------------- #
    def _seek_bos(self, o, h, l, c, idx, time, fresh):
        a = self.anchor
        if a is None:
            self.state = "WAIT_ANCHOR"
            return
        # fresher liquidity sweep re-anchors (structure evolves)
        for b in reversed(self.exec_canvas.structural_blues()):
            if b.wick_swept_down_by(l, c) and b.start_idx > a["idx"]:
                self.anchor = {"idx": idx, "time": time,
                               "sweep_low": l,
                               "floor": b.y_bottom, "box": b}
                a = self.anchor
                self.cnt("anchor_refresh_sweep")
                break
        if c < a["floor"]:                      # anchor structure died
            self.anchor = None
            self.state = "WAIT_ANCHOR"
            self.cnt("anchor_invalid")
            return
        # Event 2: a red box broken by THIS bar's body close (events
        # captured before consumption — no silent eats)
        for e in fresh:
            if e["idx"] < a["idx"]:
                continue
            wave_low = None
            for b in reversed(self.exec_canvas.active_blues()):
                if b.start_idx <= a["idx"]:
                    wave_low = b
                    break
            if wave_low is None:
                continue
            self.bos = {"idx": e["idx"], "red": e["box"],
                        "wave_low": wave_low}
            self.state = "WAIT_SETUP"
            self.cnt("bos_red_break")
            return

    # ---------------- State 3: stacked green under yellow ------------ #
    def _seek_setup(self, o, h, l, c, idx, time, fresh=()):
        # ---- v25 STREAK GOVERNOR: stand aside at three straight losses
        # and let a fresh HTF displacement wave reset the count. This is
        # what makes "max 3 consecutive losses" true BY CONSTRUCTION
        # instead of by choking every tier-3 entry at breakeven (which
        # the audit showed scratches 50 trades out of 54).
        if STRUCTURAL_RESET and self.consec_losses >= LOSS_STREAK_RESET + 1:
            ll = self.last_loss_time
            disp = ((self.htf_1h_bos_time is not None
                     and ll is not None and self.htf_1h_bos_time > ll)
                    or (self.last_htf_break_time is not None
                        and ll is not None and self.last_htf_break_time > ll))
            if disp:
                self.consec_losses = 0
                self.blocked_after_losses = False
                self.cnt("streak_structural_reset")
            else:
                self.cnt("stand_aside_streak3")
                return
        a, bos = self.anchor, self.bos
        if a is None or bos is None:
            self.state = "WAIT_ANCHOR"
            self.anchor = self.bos = None
            return
        # structure keeps evolving: adopt the newest red break as the
        # current wave (a stale wave would deadlock the wait forever)
        if fresh:
            e = fresh[-1]
            if e["idx"] >= a["idx"]:
                wave_low = None
                for b in reversed(self.exec_canvas.active_blues()):
                    if b.start_idx <= a["idx"]:
                        wave_low = b
                        break
                if wave_low is not None:
                    self.bos = {"idx": e["idx"], "red": e["box"],
                                "wave_low": wave_low}
                    bos = self.bos
                    self.cnt("setup_wave_refresh")
        if c < a["floor"]:
            self.state = "WAIT_ANCHOR"
            self.anchor = self.bos = None
            self.cnt("setup_anchor_died")
            return
        purple = self.struct_canvas.purple
        # find a live (green, yellow) stack born inside the breaking wave
        # The stack must be THE breaking wave's own boxes: born from
        # the anchor onward, completed no later than two candles after
        # the break (prompt: "شمعة أو شمعتان تكملان الـFVG فوق الكسر
        # مباشرة تُدمج فوراً" — grace of 2 comes from the prompt).
        lo = max(a["idx"], bos["wave_low"].start_idx)
        hi = bos["idx"] + 2
        # FIX3: while a loss streak is live, only a FRESH wave (yellow
        # born AFTER the last loss) may open the next trade — the old
        # months-long purple lock is gone, this replaced it
        fresh_ok = (self.consec_losses < LOSS_STREAK_RESET
                    or self.last_loss_time is None)
        # ---- FIX2: nested HTF context gates ---------------------
        if HTF_DISCOUNT:
            hcp = self.htf_canvas.purple
            if hcp is not None and c > hcp.mid:
                self.cnt("reject_htf_premium")
                return
        if HTF_WAVE_ALWAYS:
            cand = [x for x in (self.htf_1h_bos_time,
                                self.last_htf_break_time) if x is not None]
            disp = max(cand) if cand else None
            if disp is None or disp <= a.get("time"):
                self.cnt("reject_no_fresh_htf_wave")
                return
        # FIX3 (prompt): while the streak is live the ONLY key that
        # opens the next trade is a NEW BULLISH DISPLACEMENT WAVE on
        # the HTF lens — a qualified1H BOS (or4H) printed AFTER the
        # last loss, carrying a fresh HTF YellowBox + GreenBox. The
        # exec-frame yellow used in v24-run1 was far too easy.
        wave_ok = True
        if not fresh_ok:
            ll = self.last_loss_time
            disp = ((self.htf_1h_bos_time is not None
                     and self.htf_1h_bos_time > ll)
                    or (self.last_htf_break_time is not None
                        and self.last_htf_break_time > ll))
            hcv = self.htf_canvas
            fresh_y = any(b.state == "ACTIVE" and b.time is not None
                          and b.time > ll for b in hcv.yellows_b)
            fresh_g = any(b.state == "ACTIVE" and b.time is not None
                          and b.time > ll for b in hcv.greens)
            wave_ok = disp and fresh_y and fresh_g
            if not wave_ok:
                self.cnt("streak_needs_htf_wave")
        best = None
        for g, y in self.exec_canvas.pairs:
            if g.state != "ACTIVE" or y.state != "ACTIVE":
                continue
            if y.start_idx < lo or y.start_idx > hi:
                continue
            if not fresh_ok and y.time is not None \
                    and self.last_loss_time is not None \
                    and y.time <= self.last_loss_time:
                continue
            best = (g, y)
            break
        if best is None and not fresh_ok:
            self.cnt("streak_entry_not_fresh")
        if best is not None and not wave_ok:
            best = None
        if best is None:
            self.cnt("setup_wait_stack")
            return
        g, y = best
        # ---- L2 compressed pivot entry ---------------------------
        # entry sits at the TIGHT seam: GreenBox top / YellowBox floor
        # (never the far yellow top that inflated risk3x in v21)
        entry = min(g.y_top, y.y_bottom)
        if ENTRY_LEVEL == "green_mid":
            # ICT consequent encroachment: the 50% of the OrderBlock
            # (sanctioned mid constant) — a cheaper fill shrinks the
            # RiskHeight, so the net +3R lock sits far closer while the
            # structural stop stays exactly where it was
            entry = min(g.mid, y.y_bottom)
        # ---- L3 premium law: never buy above the purple mid ------
        if purple is not None and entry > purple.mid:
            entry = min(g.y_top, purple.mid)
        if purple is not None:
            assert entry <= purple.mid, \
                "FATAL: Cannot buy in Premium above PurpleBox.mid!"
        if entry <= g.y_bottom:
            # whole OB sits in Premium -> reject, no loophole
            self.cnt("reject_premium_ob")
            return
        stop = min(g.y_bottom, a["sweep_low"])
        # L2: RiskHeight capped by the green box itself
        if STOP_CAP and stop < entry - g.height:
            stop = entry - g.height
        # v26 CRIME-1 CORRECTION: the HTF floor is a FALLBACK, not a
        # default. Inflating 1R does not move the +3R lock any closer to
        # the delivery point - the audit measured the 4H range top at a
        # median 7.78R away on LOSERS vs 6.59R on winners, so the lock was
        # never "beyond the range top" - but it does halve the R multiple
        # every winner books and it puts the stop below the structure that
        # actually invalidated the setup. So: widen ONLY when the LTF stop
        # is too small to pay the round-trip fee (the 2023-25 coma case).
        _ltf_risk = entry - stop
        _need_htf = (STOP_SOURCE == "htf"
                     or (STOP_SOURCE == "hybrid"
                         and _ltf_risk <= 2 * COST * entry))
        if _need_htf:
            # FIX2 nesting: when the LTF sniper sits inside a valid HTF
            # demand box, the HTF floor is the real invalidation. In
            # 2023-2025 BTC's 5m/15m boxes shrank below the 0.1% fee
            # floor (386,811 rejects) and the bot went into a coma;
            # widening to the HTF floor restores a tradeable RiskHeight
            hcv = self.htf_canvas
            for b in list(hcv.greens) + list(hcv.yellows_b):
                if b.state == "ACTIVE" and b.y_bottom <= entry <= b.y_top:
                    if b.y_bottom < stop:
                        stop = b.y_bottom
                        self.cnt("stop_widened_to_htf")
                    break
        elif STOP_SOURCE == "hybrid":
            self.cnt("stop_kept_ltf")
        risk = entry - stop
        if risk <= 0 or entry <= stop:
            self.cnt("setup_bad_geometry")
            return
        # FIX-B: risk must exceed ONE fee side (0.1%) — below that a
        # stop-out costs > -3R and the round-trip fee dominates the
        # whole trade (observed -5.13R corpses at risk0.048%). The
        # v22 double-fee floor (0.2%) starved2023/24 to ZERO setups;
        # the single-side floor keeps their0.213% median alive.
        if risk <= 0:
            self.cnt("setup_bad_geometry")
            return
        # v25 MEASURED: the round-trip (2 x FEE) floor must NOT sit here.
        # At SETUP stage the stop has not been re-measured against the
        # real fill, so 2023-2026 setup risks are mostly < 0.2% even
        # though the filled trades end up at 0.25-1.45% (the stop is
        # widened / the fill differs). Putting the double floor here
        # wiped 2023 to ZERO trades and 2024 to two (165,862 rejects),
        # i.e. it re-created the v22 coma. The one-side floor stays at
        # setup; the round-trip requirement is enforced at the FILL,
        # where risk is final (see _enter).
        _floor = (RISK_FLOOR_PCT / 100.0 * entry
                  if RISK_FLOOR_STAGE == "both" else COST * entry)
        if risk <= _floor:
            self.cnt("reject_risk_below_one_fee")
            return
        # ---- 3R visual gate: 4H wall vs open sky ----------------
        wall_s = self.struct_canvas.nearest_ceiling(entry)  # 4H ceiling
        if wall_s is not None and (wall_s.y_bottom - entry) < MIN_R * risk:
            self.cnt("reject_wall_within_3r")
            return
        # open sky (no wall at/above entry) passes by definition
        # ---- L4: one loss per dealing range ----------------------
        if any(b <= c <= t for b, t in self.consumed):
            self.cnt("blocked_consumed_range")
            return
        # ---- v25: THE NARRATIVE GATE — read the whole story around
        # this candidate (HTF flow, liquidity raids, demand nesting,
        # open sky, unicorn overlap, inversion support) and draw the
        # setup only when the measured context supports it.
        tier3 = self.consec_losses >= LOSS_STREAK_RESET + 1
        # v25 note: the "skip a tier-3 trade that cannot carry a BE stop"
        # variant was MEASURED AND REJECTED - it deadlocks, because a
        # skipped trade never resolves the streak, so consec stays 3 and
        # every later setup is skipped too (2023: 0 trades, 2024: 2).
        # The same protection is applied globally instead: the
        # round-trip fee floor below guarantees that EVERY fill has room
        # for a breakeven stop, at any streak state.
        ok, why = self._ctx_gate(entry, stop, risk, tier3)
        if not ok:
            self.cnt(why)
            return
        self.setup_narrative = self._narrative(entry, stop, risk)
        # FIX3: the permanent purple lock is GONE — only the
        # consumed-range block (above) + the fresh-wave filter keep
        # the streak honest while the bot keeps rotating weekly
        # ---- v29: freeze the arm geometry at DRAW time --------------
        # Everything here is computable from bars that already closed:
        # the boxes, the sweep low and the purple box. Nothing looks
        # forward, and the resting order is only ever placed AFTER this
        # bar (the fill gate below is idx > gate_idx, as in v27).
        seam_px = min(g.y_top, y.y_bottom)
        H = entry - stop                     # entry == seam unless the
        order_px, order_stop = entry, stop   # premium law clipped it
        arm = ENTRY_ARM
        if arm != "seam" and H > 0:
            if arm in ("A", "B", "C"):
                order_px = stop              # buy the hunted level
            elif arm == "D":
                order_px = stop + 0.5 * H    # 50% of stop-to-seam
            if arm == "A":
                order_stop = stop - H        # mirror: risk stays H
            elif arm == "B":
                cands = []
                for cv in (self.exec_canvas, self.htf_canvas,
                           self.struct_canvas):
                    for b in cv.active_blues():
                        if stop - ARM_B_MAX_REACH * H < b.y_bottom < stop:
                            cands.append(b.y_bottom)
                order_stop = (max(cands) if cands
                              else stop - ARM_B_DEPTH * H)
            elif arm == "C":
                # the stop is measured AT FILL from the hunting wick
                order_stop = stop - H
            elif arm == "D":
                order_stop = stop - 0.5 * H  # shifted: risk stays H
            self.cnt(f"v29_arm_{arm}_drawn")
        self.setup = Setup(
            anchor_idx=a["idx"], sweep_low=a["sweep_low"],
            bos_idx=bos["idx"], bos_red=bos["red"],
            wave_low=bos["wave_low"], green=g, yellow=y,
            entry=entry, stop=stop, risk=risk,
            gate_idx=max(bos["idx"], y.start_idx, g.start_idx),
            wall=wall_s,
            purple_mid=purple.mid if purple is not None else float("nan"),
            seam_px=seam_px, old_stop_px=stop, H=H,
            order_px=order_px, order_stop=order_stop, arm=arm)
        self.state = "WAIT_RETRACE"
        self.cnt("setup_drawn")

    # ---------------- THE STORY, READ AT SETUP TIME ----------------- #
    def _narrative(self, entry, stop, risk):
        """Full institutional context around this candidate, read only
        from bars that have already closed (zero-lookahead)."""
        S4 = self.nar4 if self.nar4 is not None else self.struct_canvas
        H1 = self.nar1 if self.nar1 is not None else self.htf_canvas
        EX = self.exec_canvas
        def sky(cv):
            w = cv.nearest_ceiling(entry)
            return None if w is None else round((w.y_bottom - entry) / risk, 2)
        def ifvg(cv):
            d = cv.ifvg_below(entry) if cv.narrative else None
            return None if d is None else round(d / risk, 2)
        uni4, uni1 = S4.unicorn(entry), H1.unicorn(entry)
        uni_ex = False
        br = self.bos["red"] if self.bos else None
        if br is not None:
            for b in list(EX.greens) + list(EX.yellows_b):
                if b.state != "ACTIVE":
                    continue
                if max(br.y_bottom, b.y_bottom) <= entry <= min(br.y_top,
                                                               b.y_top):
                    uni_ex = True
                    break
        return {
            "nar_flow_4h": S4.flow(),
            "nar_flow_1h": H1.flow() if getattr(H1, "narrative", False) else None,
            "nar_sky_r_4h": sky(S4),
            "nar_sky_r_1h": sky(H1),
            "nar_range_pos_4h": (None if S4.range_pos(entry) is None
                                 else round(S4.range_pos(entry), 3)),
            "nar_in_demand_4h": S4.in_demand(entry),
            "nar_in_demand_1h": H1.in_demand(entry),
            "nar_stop_in_demand_4h": S4.in_demand(stop),
            "nar_raid_high_4h": S4.raid_high_failed(),
            "nar_raid_high_1h": (H1.raid_high_failed()
                                 if getattr(H1, "narrative", False) else False),
            "nar_raid_low_1h": (H1.raid_low_reclaimed()
                                if getattr(H1, "narrative", False) else False),
            "nar_unicorn_4h": uni4,
            "nar_unicorn_1h": uni1,
            "nar_unicorn_exec": uni_ex,
            "nar_ifvg_r_4h": ifvg(S4),
            "nar_ifvg_r_1h": ifvg(H1),
            "nar_board": self.board,
        }

    def _ctx_gate(self, entry, stop, risk, tier3):
        """Cheap, measured context gate. Returns (ok, counter_name).
        Only the two scans the gate actually needs are performed; the
        full narrative snapshot is built later, for survivors only."""
        S4 = self.nar4
        if S4 is None:
            return True, ""
        if tier3 and CTX_TIER3:
            rp = S4.range_pos(entry)
            if rp is None or rp > QUARTER:
                return False, "reject_ctx_tier3"
            w = S4.nearest_ceiling(entry)
            if w is not None and (w.y_bottom - entry) < 6.0 * risk:
                return False, "reject_ctx_tier3"
            return True, ""
        if not CTX_GATE:
            return True, ""
        if FLOW_GATE and S4.narrative and S4.flow() != "BEAR":
            return False, "reject_ctx_flow"
        dem = S4.in_demand(entry)
        raid = S4.raid_high_failed() if S4.narrative else False
        if CTX_MODE == "or":
            return (dem or not raid), ("reject_ctx_gate"
                                       if not (dem or not raid) else "")
        if CTX_MODE == "and":
            return (dem and not raid), ("" if (dem and not raid)
                                        else "reject_ctx_gate")
        if CTX_MODE == "quarter":
            ok = dem and not raid
            rp = S4.range_pos(entry)
            ok = ok and rp is not None and rp <= QUARTER
            return ok, ("" if ok else "reject_ctx_gate")
        if CTX_MODE == "v28q":
            # ---- v28 LIVE STRUCTURAL QUALITY GATE ----------------------
            # Scanned every causal-at-entry feature of the 297-trade v27
            # book (results/lab_v28_offline.txt / REPORT_AR_v28.md S3): 14 gates
            # pass ASSERT5 (n>=150 and every year >=12) and the best is
            #     NOT 4H-raid-high-failed  AND  4H range_pos > 0
            #     post-hoc n=199  51W/45BE/103L  WR 33.12%  ymin 13
            # Applied HERE, before the position is opened, so a rejected
            # setup never occupies the engine's single slot: the setups
            # that were queued behind it become reachable. That is the
            # live-vs-post-hoc difference the v28 brief asks to measure.
            # The post-hoc number is only a prediction; the run decides.
            ok = not raid
            rp = S4.range_pos(entry)
            ok = ok and rp is not None and rp > 0.0
            return ok, ("" if ok else "reject_ctx_gate_v28q")
        if CTX_MODE == "v28raid":
            # v28 live arm B: only the single best causal gate on its own
            # (post-hoc 31.89% @ n=233). One condition instead of two, to
            # separate "the gate is wrong" from "two conditions compounding
            # on a per-bar candidate scan reshape the whole stream".
            return (not raid), ("" if not raid else "reject_ctx_gate_v28raid")
        if CTX_MODE == "sky10":
            ok = dem and not raid
            w = S4.nearest_ceiling(entry)
            ok = ok and (w is None or (w.y_bottom - entry) >= 10.0 * risk)
            return ok, ("" if ok else "reject_ctx_gate")
        return True, ""

    def _ctx_ok(self, nar, tier3):
        """Measured context gate (audit table 2 / search):
        base  : 4H sky >= 3R (already enforced) AND (the entry sits
                inside live 4H demand OR the 4H highs were NOT just
                raided and failed)  -> WR 30.1% -> 32-33%
        tier3 : at three straight losses only the A+ context is taken:
                4H bottom quarter AND 4H sky >= 6R  -> WR 36-48%
        """
        if tier3 and CTX_TIER3:
            rp = nar["nar_range_pos_4h"]
            sky = nar["nar_sky_r_4h"]
            if rp is None or rp > QUARTER:
                return False
            if sky is not None and sky < 6.0:
                return False
            return True
        if not CTX_GATE:
            return True
        if nar["nar_in_demand_4h"] or not nar["nar_raid_high_4h"]:
            return True
        return False

    # ---------------- FIX4: trail source ---------------------------- #
    def _post_entry_blues(self, cv, t, lo, hi):
        """v31 ARM 1: ascending swing lows (BlueBox_SSL) that were
        CONFIRMED AFTER the entry - the 3-bar fractal needs its right bar
        to close, so a box listed here is already history, never a
        lookahead - and that sit strictly between `lo` and `hi`.
        Index comparison is only valid on the canvas that produced
        trade["entry_idx"] (the execution canvas); every other lens is
        filtered by the box's own confirmation timestamp."""
        out = []
        eidx = t.get("entry_idx")
        etime = t.get("entry_time")
        for b in self.trail_blues(cv):
            if not (lo < b.y_bottom < hi):
                continue
            if cv is self.exec_canvas:
                if eidx is not None and b.start_idx <= eidx:
                    continue
            elif b.time is None or etime is None or str(b.time) < str(etime):
                continue
            out.append(b.y_bottom)
        return out

    def _htf_close(self):
        """Last COMPLETED higher-timeframe close (the HTF canvases are fed
        finished bars only), or None when the lens is still empty."""
        bars = self.htf_canvas.bars
        return float(bars[-1][3]) if bars else None

    def _harvest(self, px):
        """v31 ARM 2b: sell HARVEST_PCT of the ORIGINAL quantity at px and
        credit the pool - the weekly cash leg - while the rest rides under
        LOCK_MODE. Both legs stay ONE trade: _exit adds t["realized"] and
        normalises R by qty0, so 50% at +3R plus 50% at +9R books +6.0R."""
        t = self.trade
        if t is None or self.qty <= 0 or HARVEST_PCT <= 0:
            return
        qty0 = t.get("qty0", self.qty)
        rel = HARVEST_PCT * qty0
        if rel <= 0 or rel >= self.qty:
            return
        fee = rel * px * COST
        t["realized"] = t.get("realized", 0.0) + (px - self.entry_px) * rel - fee
        t["released_qty"] = t.get("released_qty", 0.0) + rel
        self.pool["cash"] += rel * px - fee
        self.fees += fee
        self.qty -= rel
        self.harvested = True
        self.cnt("v31_harvest_split")

    def trail_blues(self, cv, include_exec=False):
        if TRAIL_MODE == "structural":
            return cv.structural_blues()
        return cv.active_blues()

    # ---------------- nested target ladder (FIX2/FIX4) -------------- #
    def _red_ladder(self, entry_px: float, risk: float):
        """T1..T3 = HTF RedBox_BSL above entry whose first rung clears
        the net +3R line. Returns (ladder, gate_ok)."""
        lock = ((entry_px * (1 + COST) + MIN_R * risk) / (1 - COST))
        seen = set()
        reds = []
        for r in (self.htf_canvas.active_reds()
                  + self.struct_canvas.active_reds()):
            if r.y_bottom > entry_px and r.uid not in seen:
                seen.add(r.uid)
                reds.append(r)
        reds.sort(key=lambda r: r.y_bottom)
        # FIX4: T1 is the FIRST red box that already clears the net
        # +3R line (nearer reds are skipped, not vetoes); no such box
        # means the move has no magnet worth taking
        ladder = [r for r in reds if r.y_bottom >= lock][:3]
        if not ladder:
            return [], False
        return ladder, True

    # ---------------- State 4: confirmation entry (FIX1) ------------ #
    def _seek_fill(self, o, h, l, c, idx, time, fresh=()):
        if ENTRY_ARM != "seam":
            return self._seek_fill_v29(o, h, l, c, idx, time, fresh)
        s = self.setup
        if s is None:
            self.state = "WAIT_ANCHOR"
            return
        if idx <= s.gate_idx:                # ZERO-LOOKAHEAD gate
            return
        # no-chase: expansion broke a red box above us while we waited
        # -> this wave already ran; back to the drawing board
        if fresh and c > s.entry and not (
                ENTRY_BRAIN == "dual" and s.absorb_armed
                and CISD_IGNORE_NOCHASE):
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("setup_missed_run")
            return
        # ===== v30 MODULE 2, causal order of events ====================
        # A violent arrival candle CLOSES BELOW the seam - which is also
        # below the YellowBox bottom in most draws - so v27's box-death
        # and one-touch-mitigation vetoes delete the setup on exactly the
        # bar the absorption state is supposed to start. That is the same
        # self-veto v29 had to fix with the _pre_alive snapshot. The dual
        # brain therefore arms the absorption state BEFORE those vetoes,
        # and while it is armed the setup lives in the belly of the box
        # (bounded by ABSORB_MAX_BARS) waiting for the CISD reclaim.
        # Calm bars (close at/above the seam) keep v27's vetoes verbatim,
        # so the sniper arm stays bit-identical to v27.
        if ENTRY_BRAIN == "dual":
            if s.absorb_armed:
                s.absorb_age += 1
                if s.absorb_age > ABSORB_MAX_BARS:
                    self.setup = None
                    self.state = "WAIT_ANCHOR"
                    self.cnt("v30_absorb_expired")
                    return
            elif c < s.entry:
                s.absorb_armed = True
                s.absorb_age = 0
                self.cnt("v30_cisd_armed")
                return                      # never stand before a train
        if not (ENTRY_BRAIN == "dual" and s.absorb_armed):
            if s.green.state != "ACTIVE" or s.yellow.state != "ACTIVE":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_box_died")
                return
            if c < s.green.y_bottom:         # one-touch mitigation dead
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_mitigated")
                return
        # ---- STAGE 2: the confirmation already printed on an earlier
        # bar, so a limit buy now rests at the seam. It fills only on a
        # LATER bar that trades back down to it (zero-lookahead: the
        # order is placed after the confirming close, never at a price
        # that already happened inside the confirming bar).
        # v24-run2 proof: filling at the confirmation CLOSE paid 0.73R
        # of chase, lifting median risk 0.517% -> 0.763% and dropping
        # the 2021 win rate from 48% (v23, seam fills) to 7.9%.
        if s.confirm_idx >= 0:
            if idx <= s.confirm_idx:
                return
            if l > s.entry:
                self.cnt("await_seam_retrace")
                return                        # limit not reached yet
            # ======== v30 MODULE 2: REGIME-AWARE DUAL ENTRY BRAIN =====
            # The resting limit is reached. Instead of filling blindly
            # into the arrival candle, READ it (close is known at the bar
            # close, so this is zero-lookahead):
            #   calm    - the candle only traded into the seam and closed
            #             at/above it: a normal correction, the sniper
            #             limit fills exactly as in v27..v29, so the
            #             19.38R rockets are not given up;
            #   violent - the candle CLOSES BELOW the seam, i.e. a real
            #             seller broke into the belly of the GreenBox:
            #             stand down, arm the absorption state and wait
            #             for a CISD candle that reclaims the seam while
            #             still in the Discount (close <= purple.mid) and
            #             buy THAT close. This is the single sanctioned
            #             fill above the seam; fill_px <= purple.mid
            #             remains a HARD assert in _enter.
            if ENTRY_BRAIN == "dual":
                purple_now = self.struct_canvas.purple
                if not s.absorb_armed and c < s.entry:
                    s.absorb_armed = True
                    self.cnt("v30_cisd_armed")
                    return                  # never stand before a train
                if s.absorb_armed:
                    reclaim = c > s.entry
                    if purple_now is not None:
                        reclaim = reclaim and c <= purple_now.mid
                    if CISD_NEEDS_GREEN_BODY:
                        reclaim = reclaim and c > o
                    if not reclaim:
                        self.cnt("v30_await_cisd")
                        return
                    fill_px = c
                    self.cnt("v30_cisd_reclaim")
                else:
                    fill_px = s.entry if o >= s.entry else o
                    self.cnt("v30_calm_seam_fill")
            else:
                fill_px = s.entry if o >= s.entry else o
            if self.board != "GREEN":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_board_red")
                return
            if s.green.state != "ACTIVE" or s.yellow.state != "ACTIVE":
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_box_died")
                return
            if c < s.green.y_bottom:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("setup_mitigated")
                return
            purple_now = self.struct_canvas.purple
            if purple_now is not None and fill_px > purple_now.mid:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_premium")
                return
            risk = fill_px - s.stop
            if risk <= max(COST * fill_px,
                           RISK_FLOOR_PCT / 100.0 * fill_px):
                self.cnt("reject_risk_below_one_fee")
                return
            ladder, ok = self._red_ladder(fill_px, risk)
            if not ok:
                self.cnt("fill_cancel_target_within_3r")
                return
            self.targets = ladder
            is_cisd = (ENTRY_BRAIN == "dual" and s.absorb_armed)
            if is_cisd:
                self.cnt("fill_v30_cisd")
            else:
                self.cnt("fill_at_seam")
            self._enter(s, fill_px, idx, time, cisd=is_cisd)
            return
        # ---- FIX1: never blind-limit into a falling candle --------
        # The bar that traded into the zone is remembered, but the
        # FILL only happens on a bar that is itself a rejection: it
        # must sweep the seam on THIS bar and close back above it.
        # (v24-run1 let any later green candle confirm, up to +2R
        # above the seam — that is chasing, and it produced 28 losses
        # against 2 wins in 2021.)
        if l <= s.entry:
            s.touched = True
        if not s.touched:
            return
        if FILL_MODE == "blind":
            # v23 reference: resting limit at the seam, no confirmation
            # ======== v30 MODULE 2: REGIME-AWARE DUAL ENTRY BRAIN =====
            # THIS is the shipped fill path (FILL_MODE="blind"; the
            # confirm stage above is legacy and never taken). Instead of
            # filling blindly into the arrival candle, READ it - the close
            # is known when the decision is taken, so this is
            # zero-lookahead:
            #   calm    - the candle traded into the seam and closed at or
            #             above it: an ordinary correction, the sniper
            #             limit fills exactly as in v27..v29, so the
            #             19.38R rockets are not given up;
            #   violent - the candle CLOSES BELOW the seam: a real seller
            #             broke into the belly of the GreenBox, so stand
            #             down and arm the absorption state; wait for a
            #             CISD candle that reclaims the seam while still
            #             inside the Discount (close <= purple.mid) and
            #             buy THAT close. This is the single sanctioned
            #             fill above the seam - fill_px <= purple.mid
            #             stays a HARD assert inside _enter.
            is_cisd = False
            if ENTRY_BRAIN == "dual":
                purple_now = self.struct_canvas.purple
                if s.absorb_armed:
                    reclaim = c > s.entry
                    if purple_now is not None:
                        reclaim = reclaim and c <= purple_now.mid
                    if CISD_NEEDS_GREEN_BODY:
                        reclaim = reclaim and c > o
                    if not reclaim:
                        self.cnt("v30_await_cisd")
                        return
                    fill_px = c
                    is_cisd = True
                    self.cnt("v30_cisd_reclaim")
                else:
                    fill_px = s.entry if o >= s.entry else o
                    self.cnt("v30_calm_seam_fill")
            else:
                fill_px = s.entry if o >= s.entry else o
            if self.board != "GREEN":
                self.setup = None; self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_board_red"); return
            eff_mid, _ = self._eff_mid()          # v31 ARM 3
            if eff_mid is not None and fill_px > eff_mid:
                self.setup = None; self.state = "WAIT_ANCHOR"
                self.cnt("fill_cancel_premium"); return
            risk = fill_px - s.stop
            if risk <= max(COST * fill_px, RISK_FLOOR_PCT / 100.0 * fill_px):
                self.cnt("reject_risk_below_one_fee"); return
            ladder, ok = self._red_ladder(fill_px, risk)
            if not ok:
                self.cnt("fill_cancel_target_within_3r"); return
            if self.consec_losses >= LOSS_STREAK_RESET + 1:
                # The tier-3 law demands a close at/above the BE line of
                # the fill. A CISD fill IS that close (fill_px == c), so
                # it can never clear its own BE line. CISD_TIER3_EXEMPT
                # decides whether the reclaim itself counts as the proof;
                # both settings are measured, neither is assumed.
                be_line = fill_px * (1 + 2 * COST)
                if c < be_line and not (is_cisd and CISD_TIER3_EXEMPT):
                    self.cnt("tier3_fill_needs_proof"); return
            self.targets = ladder
            if is_cisd:
                self.cnt("fill_v30_cisd")
            self._enter(s, fill_px, idx, time, cisd=is_cisd)
            return
        purple = self.struct_canvas.purple
        if purple is not None and c > purple.mid:
            return                            # not in Discount — wait
        # the confirm bar must itself trade into the seam and hold
        # the GreenBox (prompt: "closing > green.y_bottom" — NOT above
        # the box top: requiring c > entry chased the fill up to +2R
        # above the seam, inflating the R denominator so the +3R lock
        # sat 50% further away and only 3 of 48 trades could reach it)
        if l > s.entry:
            self.cnt("confirm_wait")
            return                            # no sweep on this bar
        # reclaim confirmation: body holds the GreenBox, closes back
        # above the seam, and shows a bullish rejection signature
        prev_down_high = None
        if idx >= 1:
            po, ph, pl, pc, _ = self.exec_canvas.bars[idx - 1]
            if pc < po:
                prev_down_high = ph
        sig_sweep = l < min(o, c) and c > (h + l) / 2.0
        sig_break = prev_down_high is not None and c > prev_down_high
        sig_body = c > o and c >= l + 0.5 * (h - l)
        rejection = c > o or sig_break or sig_sweep
        self._confirm_kind = ("sweep" if sig_sweep else
                              "break" if sig_break else
                              "strong_body" if sig_body else "weak_body")
        self._confirm_chase = (c - s.entry) / max(s.risk, 1e-9)
        if not (c > s.green.y_bottom and rejection):
            self.cnt("confirm_wait")
            return
        # FIX3 tier-3: after3 losses the reclaim must already be
        # above the breakeven line so the shield can never raw-lose
        if self.consec_losses >= LOSS_STREAK_RESET + 1:
            if c < s.entry * (1 + 2 * COST):
                self.cnt("tier3_fill_needs_proof")
                return
        # target ladder must clear net +3R from THIS close (entry =
        # the confirm close itself, per prompt: "ندخل عند إغلاق
        # الشمعة" — the stop distance then equals risk exactly)
        risk = c - s.stop
        if risk <= COST * c:
            self.cnt("reject_risk_below_one_fee")
            return
        ladder, ok = self._red_ladder(c, risk)
        if not ok:
            self.cnt("reject_target_within_3r")
            return
        s.confirm_idx = idx
        self.cnt("confirm_entry")
        if FILL_MODE == "close":
            self.targets = ladder
            self._enter(s, c, idx, time)
            return

    # ---------------- v29: the order rests at the hunted level ------- #
    def _seek_fill_v29(self, o, h, l, c, idx, time, fresh=()):
        """Arms A/B/C/D. Same zero-lookahead discipline as the shipped
        v27 path (FILL_MODE="blind": a resting BUY LIMIT that only fills
        on a LATER bar trading into it, gate_idx strictly before), moved
        down from the seam to the level where the OrderBlock liquidity is
        hunted. Every gate v27 applies at the fill is applied here too."""
        s = self.setup
        if s is None:
            self.state = "WAIT_ANCHOR"
            return
        if idx <= s.gate_idx:                  # ZERO-LOOKAHEAD gate
            return
        lvl = s.order_px
        # no-chase, EXACTLY as v27: the wave is considered run when price
        # closes above the SEAM (not above the deeper v29 order level -
        # measured: keying this to order_px cancelled almost every setup,
        # because a close above old_stop_px is the normal state of the
        # market while we wait for the hunt).
        if fresh and c > s.entry:
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("setup_missed_run"); return
        alive_now = (s.green.state == "ACTIVE"
                     and s.yellow.state == "ACTIVE")
        alive = alive_now if ENTRY_ARM == "C" else getattr(
            self, "_pre_alive", alive_now)
        if ARM_BOX_GATE and not alive:
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("setup_box_died"); return
        # CAUSAL ORDER OF EVENTS inside this bar: a resting limit order
        # fills the moment price TRADES into it, which happens before the
        # close is known. So the fill is evaluated first and the
        # close-based invalidation only applies when the order did not
        # fill on this bar. (Doing it the other way round silently
        # cancelled bars that had already filled the order intrabar.)
        filled_now = l <= (s.old_stop_px if ENTRY_ARM == "C" else lvl)

        # v29: the invalidation moves DOWN with the order. v27 killed the
        # setup the moment a bar closed below green.y_bottom ("one-touch
        # mitigation dead"); the v29 order rests AT or BELOW that level,
        # so the setup may only die when price closes below the NEW stop.
        if not filled_now and c < s.order_stop:
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("setup_mitigated_v29"); return

        if ENTRY_ARM == "C":
            # ---- Turtle Soup: hunt old_stop_px, then reclaim it ------
            if l > s.old_stop_px:
                self.cnt("await_soup_sweep"); return
            if not (s.old_stop_px < c <= s.seam_px):
                self.cnt("soup_no_reclaim"); return
            fill_px = c                        # buy the reclaim CLOSE
            s.order_stop = min(l, fill_px - ARM_C_WICK * s.H)
            risk = fill_px - s.order_stop
        else:
            # ---- A/B/D: resting BUY LIMIT at the hunted level --------
            if l > lvl:
                self.cnt("await_order_retrace"); return
            fill_px = lvl if o >= lvl else o   # gap-through fills at open
            risk = fill_px - s.order_stop
        if risk <= MIN_RISK_PCT * fill_px:
            self.cnt("reject_risk_below_one_fee"); return
        # ---- the live gates, identical in spirit to v27's fill -------
        if self.board != "GREEN":
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("fill_cancel_board_red"); return
        purple_now = self.struct_canvas.purple
        if purple_now is not None and fill_px > purple_now.mid:
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("fill_cancel_premium"); return
        # the 3R visual gate must be re-read from the NEW geometry: the
        # lock now sits H closer (arm A/D), so a wall that blocked v27
        # may not block v29 - and the reverse is also possible.
        wall = self.struct_canvas.nearest_ceiling(fill_px)
        if wall is not None and (wall.y_bottom - fill_px) < MIN_R * risk:
            self.setup = None; self.state = "WAIT_ANCHOR"
            self.cnt("reject_wall_within_3r_v29"); return
        ladder, ok = self._red_ladder(fill_px, risk)
        if not ok:
            self.cnt("fill_cancel_target_within_3r"); return
        if self.consec_losses >= LOSS_STREAK_RESET + 1:
            if c < fill_px * (1 + 2 * COST):
                self.cnt("tier3_fill_needs_proof"); return
        self.targets = ladder
        self.cnt(f"fill_v29_{ENTRY_ARM}")
        self._enter(s, fill_px, idx, time)

    # ---------------- fill ------------------------------------------ #
    def _enter(self, s: Setup, fill_px, idx, time, cisd=False):
        # ============================================================ #
        # v27 THE SACRED GEOMETRIC LAW — never buy above the seam.
        # The seam (min(green.y_top, yellow.y_bottom)) is the most
        # expensive price this engine is allowed to pay. Buying above it
        # is buying mid-wave: the v24 confirmation-entry bug did exactly
        # that (fills up to +2R above the seam -> 2 wins vs 28 losses in
        # 2021). Both laws are HARD ASSERTS, not counters, so a future
        # edit that breaks them stops the run instead of silently
        # degrading the win rate.
        # Verified on the shipped artefacts BEFORE adding them:
        #   trades_v25.csv (206) and trades_v27.csv (297) contain ZERO
        #   fills above green.y_top; 272/297 fills sit exactly ON it.
        # ============================================================ #
        seam = min(s.green.y_top, s.yellow.y_bottom)
        purple_now = self.struct_canvas.purple
        eff_mid, from_impulse = self._eff_mid()
        # The Discount law is NEVER relaxed - only the RANGE it is
        # measured against may be the live impulse leg (v31 ARM 3), and
        # every such fill is counted separately so it stays auditable:
        if eff_mid is not None:
            assert fill_px <= eff_mid + 1e-9, (
                f"FATAL BUG: bought in PREMIUM above the dealing mid: "
                f"fill={fill_px} > mid={eff_mid} at {time}")
            if from_impulse and (purple_now is None
                                 or fill_px > purple_now.mid):
                self.cnt("sacred_law_impulse_ok")
        if cisd:
            # v30 dual brain: a CISD absorption close ABOVE the seam is
            # the one sanctioned exception, and only while the close is
            # still inside the Discount (asserted just above).
            self.cnt("sacred_law_cisd_ok")
        else:
            assert fill_px <= seam + 1e-9, (
                f"FATAL BUG: bought ABOVE the GreenBox ceiling mid-wave: "
                f"fill={fill_px} > seam={seam} at {time}")
            self.cnt("sacred_law_seam_ok")
        # v29: the stop belongs to the ARM, not to the seam geometry.
        # For "seam" (v27/v28 baseline) order_stop == stop, so this is a
        # no-op and the baseline stays bit-identical.
        stop = s.order_stop if (s.arm != "seam" and s.order_stop) else s.stop
        if fill_px <= stop:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            return
        if sum(1 for e in self.pool.get("engines", []) if e.qty > 0) \
                >= MAX_SLOTS:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("portfolio_slots_full")
            return
        risk = fill_px - stop
        # ---- v25: THE BREAKEVEN-ROOM LAW (assert 4, by construction) --
        # At exactly three straight losses the next fill is armed with a
        # breakeven stop at fill x (1 + 2 x FEE). That stop only fits
        # inside the trade when risk > 2 x FEE x fill. If it does not
        # fit, the trade CANNOT be protected and a 4th consecutive loss
        # becomes possible, so the fill is declined.
        # Proof this hole was real: the 209-trade v25 run lost -2.197R on
        # 2023-05-21 20:00 (30min, risk 0.167%) at exactly 3 losses -
        # the 0.2% round trip alone is -1.2R, so the BE line sat ABOVE
        # the +risk limit and the choke silently did not arm.
        # No deadlock: the setup-time risk distribution is untouched, so
        # the streak is never gated on a condition the market cannot
        # satisfy (the 2023 coma above came from gating the SETUP).
        if TIER3_ENTRY_CHOKE and self.consec_losses >= LOSS_STREAK_RESET + 1 \
                and risk <= 2 * COST * fill_px:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("tier3_skip_no_be_room")
            return
        # FIX4: 100% of FREE pool cash goes to work (reserving the
        # round-trip fee) — no more half-idle $100 stacks
        # ---- v30 MODULE 3b: spot dollar-R equalization --------------
        # risk is in price units per coin, so risk_frac = risk / fill_px
        # is the share of notional lost on a stop-out. Sizing to a fixed
        # dollar-R keeps that share of EQUITY constant across boxes. The
        # all-cash cap is never breached: halal spot, no leverage.
        # ---- v33 (أ) FULL-SLOT CASH DEPLOYMENT ------------------------
        # 1.0 is the v32 law (notional = whole budget / (1+COST), measured
        # notional/equity = 0.9990 allcash, 0.3330 with 3 slots). The knob
        # exists so the arm table can state deployment explicitly instead
        # of implying a 1% risk cap that this engine never had.
        notional = self.slot_budget() * SLOT_DEPLOY_PCT / (1 + COST)
        if SIZING == "dollarR":
            risk_frac = risk / fill_px if fill_px > 0 else 0.0
            if risk_frac > 0:
                eq = self.portfolio_equity(fill_px)
                want = (DOLLAR_R_PCT / 100.0) * eq / risk_frac
                notional = min(want, self.pool["cash"] / (1 + COST))
                self.cnt("v30_dollarR_capped" if want > notional + 1e-9
                         else "v30_dollarR_sized")
        # ---- v32 PILLAR 4: ICT killzone time gate ---------------------
        # Applied at FILL time on the entry stamp (that is what the audit
        # measured). A gated-out signal is dropped, not postponed: the
        # engine keeps its state machine, so the live re-measurement is
        # honest about the knock-on effects.
        if KILLZONE_MODE != "off" and (KILLZONE_HOURS or KILLZONE_DOW):
            ts = pd.Timestamp(time)
            # an empty hour tuple means "every hour" (a weekday-only gate)
            in_hours = (not KILLZONE_HOURS) or int(ts.hour) in tuple(KILLZONE_HOURS)
            in_dow = (not KILLZONE_DOW) or int(ts.dayofweek) in tuple(KILLZONE_DOW)
            blocked = (in_hours and in_dow) if KILLZONE_MODE == "exclude" \
                else not (in_hours and in_dow)
            if blocked:
                self.setup = None
                self.state = "WAIT_ANCHOR"
                self.cnt("v32_killzone_skip")
                return
        # ---- v32 PILLAR 2: SMT veto (SMT_GATE="require") --------------
        # "prefer" needs nothing here: it is consumed by the basket ORDER
        # (the strongest coin reaches the shared cash first at a stamp
        # where several are ready). "require" drops the fill instead.
        if SMT_BRAIN and SMT_GATE == "require" and \
                not self.pool.get("smt", {}).get(self.symbol, False):
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("v32_smt_veto")
            return
        # ---- v33 (ج) ALPHA-LEADER gate --------------------------------
        # Cash is concentrated in the coins the leader brain ranked highest
        # at THIS stamp (4H structure + SMT_BULL + FVG/OB displacement).
        # Every engine is still fed its bars - only the FILL is refused - so
        # no state machine freezes and nothing is read from the future.
        if V33_ALPHA_LEADER and not self.v33_allow:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("v33_leader_veto")
            return
        # ---- v32 PILLAR 3: regime-B veto ------------------------------
        # Weapon B trades WITH the trend only: at fill time the 4H board
        # must show the last structural break upward (RedBox_BSL) and the
        # last BlueBox_SSL as a Higher Low. Weapon A ("A") is untouched.
        if REGIME_MODE == "B" and not self._regime_b_ok():
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("v32_regime_b_veto")
            return
        # ---- v33 (د) RANGE regime refuses impulse-sourced fills --------
        # Only the fills that NEEDED the re-armed impulse leg (Weapon B) are
        # refused; a plain Weapon A sweep reversal still trades in chop, and
        # RANGE_HARVEST_4H decides how its winners are paid.
        if RANGE_VETO_WEAPON_B and self._v33_range() and from_impulse:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("v33_range_b_veto")
            return
        qty = notional / fill_px
        notional = qty * fill_px
        if qty <= 0 or notional < EXCHANGE_MIN_NOTIONAL:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            self.cnt("fill_below_exchange_min")
            return
        fee = notional * COST
        if fee + notional > self.pool["cash"] + 1e-9:
            self.setup = None
            self.state = "WAIT_ANCHOR"
            return
        self.qty = qty
        self.entry_px = fill_px
        self.stop_px = stop
        self.orig_stop_px = stop      # v32 PILLAR 4: the structural stop as
        #                             the chart drew it, kept forever so the
        #                             emergency wick cap never drifts up
        self.risk = risk
        self.ratchet = False
        self.mfe = 0.0                 # max favourable excursion, in R
        self.mfe_close = 0.0           # same, measured on CLOSES only
        self.t1_hit = False            # FIX4: T1 reached -> trail arm
        # ---- v25: the story must PROVE itself before any protection
        self.disp_mid = False          # 4H PurpleBox.mid crossed
        self.disp_bos = False          # post-entry break of structure
        ceilings = [b.y_top for b in self.exec_canvas.reds
                    if b.state == "ACTIVE" and b.y_top > fill_px]
        self.entry_ceiling = min(ceilings) if ceilings else None
        _vig = self.vigil_losses if VIGILANCE_SCOPE == "shield+be" \
            else self.consec_losses
        self.tier3_at_entry = _vig >= LOSS_STREAK_RESET + 1
        self.qty0 = qty
        # L4 shield: trade opened with an active2-loss streak arms
        # breakeven early (exception to the no-move-before-3R law)
        _vigs = self.vigil_losses if VIGILANCE_SCOPE in ("shield",
                                                         "shield+be") \
            else self.consec_losses
        self.shield = _vigs >= LOSS_STREAK_RESET
        self.be_armed = False
        self._be_at_entry = False
        # v25: the entry-tick choke is gone for EVERY normal trade —
        # protection is earned by displacement (see _manage). It survives
        # ONLY at exactly three straight losses, where it is the single
        # mechanism that makes a 4th consecutive loss impossible.
        self._be_at_entry = False
        if TIER3_ENTRY_CHOKE and self.tier3_at_entry:
            be = fill_px * (1 + 2 * COST)
            if be < fill_px + risk:      # keep the stop a real stop
                self.stop_px = max(self.stop_px, be)
                self.be_armed = True
                self._be_at_entry = True
                self.cnt("tier3_be_armed_at_entry")
        # exact solution of px - entry - FEE*entry - FEE*px >= 3*risk
        # (exit fee scales with the HIGHER exit price — v22 run-1 lost
        # 68 near-3R winners to a0.004R fee shortfall)
        self.lock_line = ((fill_px * (1 + COST) + MIN_R * risk)
                          / (1 - COST))
        # ---- v31 ARM 2: the FLOOR may arm later than the +3R gate ----
        # The entry gate above stays at MIN_R = 3.00 (sacred); the floor
        # that ends the ride is a separate line, swept by LOCK_ARM_R.
        self.floor_line = ((fill_px * (1 + COST) + LOCK_ARM_R * risk)
                           / (1 - COST))
        self.struct_trailed = False
        self.harvested = False
        self.protected_blue = s.wave_low
        self.pool["cash"] -= notional + fee
        self.pool.setdefault("open", []).append(self)
        self.fees += fee
        self.state = "IN_POS"
        self.trade = {
            "symbol": self.symbol,
            "entry_time": str(time),
            "entry_idx": idx,
            "entry_price": fill_px,
            "stop_price": stop,
            "risk_pct": risk / fill_px * 100.0,
            "notional": notional,
            "qty0": qty,
            "realized": 0.0,
            "released_qty": 0.0,
            "s1_anchor": f"@{s.anchor_idx} sweep_low={s.sweep_low:.2f}",
            "broken_red": s.bos_red.as_dict(),
            "wave_low_blue": s.wave_low.as_dict(),
            "yellow": s.yellow.as_dict(),
            "green": s.green.as_dict(),
            "purple_mid": round(s.purple_mid, 2),
            "wall": s.wall.as_dict() if s.wall else None,
            "entry_line": round(s.entry, 2),
            "v29_arm": s.arm,
            "v31_cisd": cisd,
            "v31_brain": ENTRY_BRAIN,
            "v31_cisd_tier3_exempt": CISD_TIER3_EXEMPT,
            "v31_be_mode": BE_STREAK_MODE,
            "v31_vigil_scope": VIGILANCE_SCOPE,
            "v31_vigil_at_entry": self.vigil_losses,
            "v31_shield_rule": SHIELD_RULE_V30,
            "v31_sizing": SIZING,
            "v31_risk_floor_pct": RISK_FLOOR_PCT,
            "v31_risk_floor_stage": RISK_FLOOR_STAGE,
            "v31_slippage_bps": SLIPPAGE_BPS,
            "v29_seam_px": round(s.seam_px, 2),
            "v29_old_stop_px": round(s.old_stop_px, 2),
            "v29_H": round(s.H, 2),
            "v29_order_px": round(s.order_px, 2),
            "setup_completion_idx": s.gate_idx,
            "bos_idx": s.bos_idx,
            "entry_fee": fee,
            "s1_kind": "BOX_STACK",
            "shield": self.shield,
            "exec_tf": self.exec_tf,
            "targets": [b.as_dict() for b in self.targets],
            "confirm_idx": s.confirm_idx,
            "mfe_R": 0.0,
            **{k: v for k, v in self.setup_narrative.items()},
            "be_at_entry": getattr(self, "_be_at_entry", False),
            # v31 A2 second reading: the STRUCTURAL objective at entry.
            # _red_ladder refuses any fill whose first qualifying rung
            # does not clear net +3.00R, so this is >= 3.00R for every
            # trade the engine ever opens - measured, not assumed.
            "entry_target_R": (round((self.targets[0].y_bottom - fill_px)
                                     / risk, 2) if self.targets else None),
            "entry_lock_R": round((self.lock_line - fill_px) / risk, 2),
            "disp_mid": False,
            "disp_bos": False,
            "tier3_at_entry": self.tier3_at_entry,
            "be_source": "",
            "mfe_close_R": 0.0,
            "confirm_kind": getattr(self, "_confirm_kind", "?"),
            "confirm_chase_R": round(getattr(self, "_confirm_chase", 0.0), 2),
            "n_targets": len(self.targets),
        }
        self.cnt("fill")

    # ---------------- in-position management ------------------------ #
    def _release_locked_capital(self, lock_px):
        """FIX4 (risk-free pyramiding): at the first +3R close, sell
        back the initial notional at the lock price. The freed cash
        returns to the pool (100% rotation into the next structure)
        and the remaining qty rides with ZERO cost basis — both legs
        together can never net below +3.0R (same price, same fees)."""
        t = self.trade
        if t is None or self.qty <= 0:
            return
        qty0 = t.get("qty0", self.qty)
        rel = t.get("notional", 0.0) / lock_px
        if rel <= 0 or rel >= self.qty:
            return
        fee = rel * lock_px * COST
        realized = (lock_px - self.entry_px) * rel - fee
        t["realized"] = t.get("realized", 0.0) + realized
        t["released_qty"] = t.get("released_qty", 0.0) + rel
        self.pool["cash"] += rel * lock_px - fee
        self.fees += fee
        self.qty -= rel
        self.cnt("capital_released_at_lock")

    def _exit(self, px, reason, idx, time):
        # v32: drop this engine from the shared open-position registry
        t = self.trade
        gross = (px - self.entry_px) * self.qty
        exit_fee = px * self.qty * COST
        entry_fee = t.get("entry_fee", 0.0)
        net = gross - entry_fee - exit_fee + t.get("realized", 0.0)
        R = (net / (self.risk * t.get("qty0", self.qty))
             if self.risk > 0 else 0.0)
        # ---- classification (L1: winners are >= +3.0R, always) ----
        is_win = net > 0 and R >= MIN_R - 1e-9
        # ---- v31 ARM 1: a STRUCTURAL take-profit is its own class ----
        # net > 0 but below the sacred +3.00R. It is never counted as a
        # WIN, so min_winner_R stays >= 3.00R by construction; it is
        # never counted as a LOSS either, so the win rate stops being
        # punished for banking a real profit.
        is_swin = (not is_win) and net > 0 and R >= SWIN_MIN_R
        is_be = ((not is_win) and (not is_swin)
                 and (self.shield or self.be_armed or net > 0)
                 and R >= -0.05)
        if is_be:
            reason = "BREAKEVEN"
        elif is_swin and getattr(self, "struct_trailed", False):
            reason = "STRUCT_PROFIT"
        t["mfe_R"] = round(self.mfe, 2)
        t["disp_mid"] = self.disp_mid
        t["disp_bos"] = self.disp_bos
        t["mfe_close_R"] = round(self.mfe_close, 2)
        t.update({"exit_time": str(time), "exit_idx": idx,
                  "exit_price": px, "exit_reason": reason,
                  "net_pnl": net, "R": R, "bars_held": idx - t["entry_idx"],
                  "v31_swin": is_swin,
                  "v31_struct_trailed": bool(getattr(self, "struct_trailed",
                                                     False)),
                  "v31_harvested": bool(getattr(self, "harvested", False)),
                  "class": "WIN" if is_win else
                           ("SWIN" if is_swin else
                            ("BE" if is_be else "LOSS"))})
        # position sold: proceeds back to shared pool cash
        self.pool["cash"] += px * self.qty - exit_fee
        op = self.pool.get("open")
        if op is not None and self in op:
            op.remove(self)          # v32: free the slot for another coin
        self.trades.append(t)
        self.qty = 0.0
        self.trade = None
        self.ratchet = False
        self.shield = False
        self.be_armed = False
        self.struct_trailed = False
        self.harvested = False
        self.state = "WAIT_ANCHOR"
        self.setup = None
        self.anchor = None
        self.bos = None
        self.cnt("exit_" + reason)
        # ---- L4 bookkeeping ---------------------------------------
        purple = self.struct_canvas.purple
        rng = (purple.y_bottom, purple.y_top) if purple is not None else None
        if is_win or is_swin:
            self.consec_losses = 0
            self.locked_range = None
            self.breaker_ready = False
            self.blocked_after_losses = False
            if is_win or SWIN_CLEARS_VIGIL:
                # only a real WIN (>= +3.00R) ends the permanent vigilance,
                # unless SWIN_CLEARS_VIGIL says a structural profit may too
                self.vigil_losses = 0
            if is_swin:
                self.cnt("v31_swin_clears_throttle")
        elif is_be:
            # not a loss, not a win. The STREAK GATE IS
            # RELEASED: v24-run4 proof — holding the streak on a scratch
            # trapped the bot in permanent tier-3 (54 trades armed with
            # a BE stop at entry, 50 of them scratched, up to 13 in a
            # row), which starved both the win rate and 2023-2025.
            # v25 NOTE (honesty): with the entry-tick choke gone, a 4th
            # loss is no longer impossible BY CONSTRUCTION. Trade #4 is
            # guarded by the A+ context gate (CTX_TIER3) and by a
            # displacement-armed shield (TIER3_RULE); assert 4 is
            # therefore MEASURED on the real run, not assumed.
            if rng is not None and BE_CONSUMES_RANGE:
                self.consumed.append(rng)
            # ---- v30 MODULE 1a: persistent vigilance ----------------
            mode = BE_STREAK_MODE
            if mode == "reset" and BE_RELEASES_STREAK:
                self.consec_losses = 0
                self.blocked_after_losses = False
                self.cnt("shield_be_releases_streak")
            elif mode == "decay":
                self.consec_losses = max(0, self.consec_losses - 1)
                if self.consec_losses == 0:
                    self.blocked_after_losses = False
                self.cnt("v30_be_decays_streak")
            else:                                  # "hold"
                self.cnt("shield_be_holds_streak")
            self.cnt("v30_vigil_holds_on_be")
        else:
            self.consec_losses += 1
            self.vigil_losses += 1
            self.last_loss_idx = idx
            self.last_loss_time = time
            if rng is not None:
                self.consumed.append(rng)   # one loss per range
            if self.consec_losses >= LOSS_STREAK_RESET:
                self.blocked_after_losses = True
                self.cnt("structural_gate_armed")
        self.targets = []

    def _manage_5m_lock_only(self, o, h, c):
        """The 5m pass with MANAGE_5M_SHIELD off: raise the +3R floor on a
        5m CLOSE and nothing else. The stop was already honoured above."""
        if not MANAGE_5M_LOCK:
            return
        lock_line = self.lock_line
        if not self.ratchet and c >= lock_line:
            self.ratchet = True
            self.stop_px = max(self.stop_px, lock_line)
            self.cnt("manage5m_ratchet_3r")
        elif self.ratchet and lock_line > self.stop_px:
            # the floor is a FLOOR: never pull a trailed stop back down
            self.stop_px = lock_line
            self.cnt("manage5m_floor_reset")

    def manage_5m(self, o, h, l, c, time):
        """v28: manage an OPEN position on a causal 5m bar, whatever frame
        opened it. Only the stop and the +3R floor are evaluated here; the
        structural exits (floor close, red target, HTF blue trail, reversal
        CHoCH) stay on the execution frame so the runners are not clipped."""
        if self.qty <= 0:
            return
        self._manage(o, h, l, c, max(0, len(self.exec_canvas.bars) - 1),
                     time, tf5=True)

    def _manage(self, o, h, l, c, idx, time, tf5=False):
        t = self.trade
        if self.risk > 0:
            self.mfe = max(self.mfe, (h - self.entry_px) / self.risk)
            self.mfe_close = max(self.mfe_close,
                                 (c - self.entry_px) / self.risk)
        lock_line = self.lock_line   # entry + 3R + fees (net >= +3.0R)
        floor_line = getattr(self, "floor_line", lock_line)   # v31 ARM 2
        # wick stop (structural pre-ratchet, or an above-floor trail)
        floor_only = (self.ratchet
                      and self.stop_px <= floor_line + 1e-9)
        # v28: on the 5m tape the armed floor IS a live stop order, so the
        # wick defends it (the stop was raised at the previous 5m CLOSE, so
        # this bar's own low is a genuine later breach - no lookahead). On
        # the execution frame the floor stays a CLOSE rule as in v27.
        defend = ((not floor_only) or LOCK_MODE == "stop"
                  or (tf5 and MANAGE_5M_WICK and self.ratchet))
        # ---- v32 PILLAR 4: emergency wick cap at the ORIGINAL stop ----
        # The be_line and STRUCT_TRAIL exits read the CLOSE (as LOCK_MODE
        # "trail" already does), so a violent wick can pierce them and
        # recover without an exit. The one line that is always defended by
        # the wick is the structural stop the chart drew at entry: no loss
        # may exceed -1R. The RAISED stops are deliberately NOT wick-
        # defended - v31 measured that (LOCK_MODE="stop": maxR 34.50 ->
        # 12.84, totR +114.03 -> -27.72).
        if (EMERGENCY_WICK_STOP and self.ratchet
                and getattr(self, "orig_stop_px", None) is not None
                and l <= self.orig_stop_px):
            self.cnt("v32_emergency_stop")
            px = self.orig_stop_px if o >= self.orig_stop_px else o
            self._exit(px, "EMERGENCY_STOP", idx, time)
            return
        # ---- v32 PILLAR 4b: CLOSE_BASED_SHIELD ------------------------
        # Pre-ratchet, the armed break-even line can be made a CLOSE rule
        # (the same causal discipline the LOCK_MODE="trail" floor and the
        # STRUCT_TRAIL raises already use: the stop moves on a completed
        # bar's close and the exit needs a completed bar's close too), so
        # a wick through the be_line no longer scratches the trade. The
        # ORIGINAL structural stop keeps its wick defence either way via
        # EMERGENCY_WICK_STOP above, so no loss can exceed -1R.
        shield_close_only = (CLOSE_BASED_SHIELD and self.be_armed
                             and not self.ratchet
                             and self.stop_px
                             <= self.entry_px * (1 + 2 * COST) + 1e-9)
        hit = c <= self.stop_px if shield_close_only else l <= self.stop_px
        if defend and hit:
            px = (c if shield_close_only
                  else (self.stop_px if o >= self.stop_px else o))
            be_now = self.entry_px * (1 + 2 * COST)
            scratch = self.be_armed and self.stop_px <= be_now + 1e-9
            at_floor = (self.ratchet and LOCK_MODE == "stop"
                        and self.stop_px >= floor_line - 1e-9)
            self._exit(px, "LOCK_FLOOR_STOP" if at_floor
                       else ("SHIELD_BE" if scratch
                             else ("FLOOR_5M" if (tf5 and floor_only)
                                   else "STOP_BLUE")),
                       idx, time)
            return
        # ---- v25: DISPLACEMENT DETECTION — the story proving itself.
        # The audit's 57-point separator: 91.9% of winners cross the 4H
        # dealing-range mid after entry vs only 34.7% of losers.
        if tf5 and not MANAGE_5M_SHIELD:
            return self._manage_5m_lock_only(o, h, c)
        pmid = t.get("purple_mid")
        if not self.disp_mid and pmid is not None and pmid == pmid:
            if c > pmid:
                self.disp_mid = True
                self.cnt("disp_mid_cross")
        if (not self.disp_bos and self.entry_ceiling is not None
                and c > self.entry_ceiling):
            self.disp_bos = True
            self.cnt("disp_bos")
        # ---- THE SHIELD: armed ONLY by a displacement, NEVER at the
        # entry tick (audit: entry-tick arming scratched 50/54 trades).
        # Tier-3 trades (3 straight losses) use the tighter rule so a
        # 4th consecutive loss stays improbable without choking entries.
        if not self.be_armed:
            rule = TIER3_RULE if self.tier3_at_entry else SHIELD_RULE_V30
            fired = False
            if rule == "MID":
                fired = self.disp_mid
            elif rule == "BOS":
                fired = self.disp_bos
            elif rule == "MID+BOS":
                fired = self.disp_mid and self.disp_bos
            elif rule == "MID|BOS":
                fired = self.disp_mid or self.disp_bos
            elif rule.startswith("A"):
                fired = c >= self.entry_px + float(rule[1:]) * self.risk
            elif rule == "NONE":
                fired = False
            be = self.entry_px * (1 + 2 * COST)       # entry + fees
            # a stop must sit BELOW the market; arming happens on this
            # bar's CLOSE so the BE stop only lives from the next bar
            if fired and c > be:
                self.stop_px = max(self.stop_px, be)
                self.be_armed = True
                self.cnt("shield_armed_disp")
                t["be_source"] = rule
        # ---- v31 ARM 1: STRUCTURAL PROFIT TRAIL ---------------------
        # Before the floor exists, the v30 law could only move the stop
        # to break-even: everything between +0.01R and +2.99R was either
        # scratched back to 0.00R or stopped at -1.00R (measured: 55
        # trades closed >= +1.5R and were booked BE/LOSS, 35 >= +2.0R,
        # 26 >= +2.5R). Here an ASCENDING swing low confirmed after the
        # entry may carry the stop, as long as it sits above the
        # break-even line and below the market. The raise happens on this
        # bar's CLOSE, so the new stop lives from the next bar - the same
        # causal discipline as the shield.
        if STRUCT_TRAIL and not self.ratchet and self.risk > 0:
            gross = (c - self.entry_px) / self.risk
            # ---- v33 (ب) MICROSCOPE ENTRY -> TELESCOPE TRAIL -----------
            # v32 trailed on the EXECUTION frame from +1.0R: with a median
            # stop width of 0.41% that books winners at a median +0.75R =
            # a +0.3% price move, and the coin then ran a median +9.41% in
            # the next 7 days (0 of 78 fell). TRAIL_LENS_PRE picks the lens
            # and TRAIL_MIN_R_PRE picks how late the trail may start.
            _minr = (STRUCT_TRAIL_MIN_R if TRAIL_MIN_R_PRE is None
                     else float(TRAIL_MIN_R_PRE))
            if gross >= _minr and (
                    not STRUCT_TRAIL_NEEDS_DISP
                    or self.disp_mid or self.disp_bos):
                be = self.entry_px * (1 + 2 * COST)
                srcs = []
                lens = ("v32" if TRAIL_LENS_PRE == "exec"
                        and STRUCT_TRAIL_SRC in ("exec", "htf", "both")
                        else TRAIL_LENS_PRE)
                if lens == "v32":
                    if STRUCT_TRAIL_SRC in ("exec", "both"):
                        srcs.append(self.exec_canvas)
                    if STRUCT_TRAIL_SRC in ("htf", "both"):
                        srcs += [self.htf_canvas, self.struct_canvas]
                elif lens == "htf":
                    srcs += [self.htf_canvas, self.struct_canvas]
                elif lens == "struct4h":
                    srcs.append(self.struct_canvas)
                elif lens == "off":
                    srcs = []
                cands = []
                for cv in srcs:
                    cands += self._post_entry_blues(
                        cv, t, max(be, self.stop_px), c)
                if cands:
                    new = max(cands)
                    if new > self.stop_px:
                        self.stop_px = new
                        self.struct_trailed = True
                        self.cnt("v31_struct_trail")
                        t["struct_trail_R"] = round(
                            (new - self.entry_px) / self.risk, 2)
        # ---- v31 ARM 2b: the weekly cash leg ------------------------
        if HARVEST_PCT > 0 and not self.harvested and c >= floor_line:
            self._harvest(c)
        # ---- RUNNER arm: first CLOSE >= +3R locks the floor ------- #
        if not self.ratchet and c >= floor_line:
            self.ratchet = True
            self.stop_px = max(self.stop_px, floor_line)
            self.cnt("ratchet_3r_close")
            # FIX4 (v24): the +3R lock is a STOP FLOOR, not a market
            # sell. The v22/v23 "release locked capital" step sold
            # notional/lock ≈ 98.7% of the position at exactly +3R and
            # left 1.3% riding — which is why a 2021-07-30 15m trade
            # that ran to +22.8R on closes was booked at 3.23R. That
            # single line WAS the "3.00R massacre".
        elif self.ratchet and floor_line > self.stop_px:
            self.stop_px = floor_line
        floor_only = (self.ratchet
                      and self.stop_px <= floor_line + 1e-9)
        if tf5:
            # v28: on the 5m pass the floor is RAISED here but the ride is
            # never ended by a 5m close - that stays an execution-frame
            # decision, otherwise every runner is booked at +3.00R.
            return
        if floor_only:
            # ---- v31 ARM 2a: ANTI-CHOKE RUNNER ----------------------
            # "floor" is the v30 law and it is what booked 33 of 44
            # winners at EXACTLY +3.00R out of a median 4.21R close
            # extension (mean intrabar 5.77R, max 11.64R).
            if LOCK_MODE == "floor" and c <= floor_line:
                # body-close rule (a): candle closes back under the floor
                px = floor_line if o >= floor_line else o
                self._exit(px, "LOCK_FLOOR_CLOSE", idx, time)
                return
            if LOCK_MODE == "htf":
                # only a COMPLETED higher-timeframe close under the floor
                # ends the ride; execution-frame dips are noise
                hc = self._htf_close()
                if hc is not None and hc <= floor_line:
                    self.cnt("v31_floor_htf_close")
                    px = floor_line if c >= floor_line else c
                    self._exit(px, "LOCK_FLOOR_HTF", idx, time)
                    return
            # LOCK_MODE == "trail": the floor never sells. The ride ends
            # on the trailed ascending BlueBox_SSL stop (below) or on the
            # red-target rejection - the runner is left unchoked.
        # ---- v33 (د) RANGE REGIME: harvest the first 4H ceiling -------
        # In a chop basket the wave does not extend, so the honest exit is
        # to SELL INTO the liquidity resting above: the lowest 4H RedBox_BSL
        # whose bottom already sits at or beyond the +3R lock. The fill is
        # the box bottom on first touch - never a better price, and the box
        # is read from the shared 4H narrative canvas, which the runner
        # feeds completed bars only.
        if (RANGE_HARVEST_4H and self.ratchet and self._v33_range()
                and self.nar4 is not None and self.risk > 0):
            pools = sorted((b.y_bottom for b in self.nar4.active_reds()
                            if b.y_bottom > self.floor_line))
            for ceil in pools:
                if h >= ceil:
                    self.cnt("v33_range_harvest")
                    self._exit(ceil, "RANGE_HARVEST_4H", idx, time)
                    return
        # ---- FIX4: exit AT the red target on a rejection candle ---
        # (any trail stop above the floor already fired on its wick,
        # so a close reaching this branch is above the trail too)
        if self.ratchet and self.targets:
            for T in list(self.targets):
                if h < T.y_bottom:
                    break                   # ladder sorted ascending
                self.t1_hit = True          # first rung reached
                if c < o and c <= T.y_top:  # bearish close inside box
                    self.cnt("target_rejection_exit")
                    self._exit(c, "TARGET_REJECTION", idx, time)
                    return
                # traded THROUGH the box — consumed, aim higher
                self.targets.remove(T)
                self.cnt("target_consumed")
        # ---- FIX4: once the +3R lock is on, the ride continues with
        # the stop trailing ascending HTF BlueBox bottoms ABOVE the
        # lock (1H lens for the LTF snipers,4H board for the1h engine).
        # v24-run3 proof: gating the trail behind T1 left it dead on
        # every runner (T1 often sits beyond the whole move), so a
        # 27.9R excursion was walked all the way back and exited at
        # 3.13R. The prompt says "through 3R/T1" — whichever is first.
        if self.ratchet:
            best = self.stop_px
            # ---- v33 (ب)/(د) after the +3R lock, ride the 4H lens ------
            srcs = ([self.struct_canvas]
                    if (TRAIL_4H_ONLY_AFTER_3R or self._v33_expand())
                    else [self.htf_canvas, self.struct_canvas])
            if TRAIL_MODE == "all_active":
                srcs.append(self.exec_canvas)
            for cv in srcs:
                for b in self.trail_blues(cv):
                    if (b.y_bottom >= getattr(self, "floor_line",
                                              self.lock_line)
                            and self.stop_px < b.y_bottom < self.price):
                        best = max(best, b.y_bottom)
            if best > self.stop_px:
                self.stop_px = best
                self.cnt("trail_htf_blue")
        # (exec-frame trail REMOVED: the4H structural trail in
        # on_struct — "أو4H" — governs rides)
        # ---- top-sell: only allowed at/above the lock line -------
        # (keeps every winner >= +3.0R by construction)
        if self.ratchet and c >= lock_line:
            cv = self.exec_canvas
            blues = cv.active_blues()
            if blues:
                last_blue = blues[-1]
                if c < last_blue.y_bottom and any(
                        y.start_idx >= last_blue.start_idx
                        for y in cv.active_yellow_s()):
                    self._exit(c, "REVERSAL_CHoch", idx, time)
                    return

    # --------------------------------------------------------------- #
    def portfolio_equity(self, price=None):
        eq = self.pool["cash"]
        for e in self.pool.get("open", []):
            p = price if (e is self and price is not None) else e.price
            eq += e.qty * p
        return eq

    def open_slots(self) -> int:
        """How many positions the basket is carrying right now."""
        return len(self.pool.get("open", []))

    def slot_budget(self) -> float:
        """v32 PILLAR 1 — how much of the SHARED cash this fill may take.

        ALLOC_MODE="allcash" is the v27..v31 law: the whole free cash, so
        the first engine to fill takes 100% and every other coin is
        rejected until it exits (measured: notional/equity = 0.9990 on all
        311 v31 fills — the stop stays exactly where the chart put it, the
        position size is what flexes).

        ALLOC_MODE="slot" divides the free cash: SLOTS=2 -> 50% each,
        SLOTS=3 -> 33% each, so a slow trade on one coin cannot starve a
        +25% burst on another in the same week.  SLOT_FILL="dynamic"
        divides by the slots still FREE instead of by SLOTS, which puts
        the whole remaining cash to work as slots fill up.

        Never levered: the budget is always <= free cash, and _enter still
        refuses the fill when notional + fee > cash."""
        cash = self.pool["cash"]
        if ALLOC_MODE != "slot" or SLOTS <= 1:
            return cash
        if SLOT_FILL == "dynamic":
            free = max(1, SLOTS - self.open_slots())
            return cash / float(free)
        return cash / float(SLOTS)

    def equity(self, price=None):
        return self.portfolio_equity(price)


# ==================================================================== #
# Portfolio runner (multi-coin ready; data currently holds BTC only)
# ==================================================================== #
def discover_symbols(data_dir: Path) -> list[str]:
    """Every `<COIN><QUOTE>_5m` dir the whitelist accepts, sorted.

    FIX4 kept this crypto-spot only (XAUUSD metal and index dirs are
    excluded). v32 lets the lab override the whitelist - used ONLY for a
    clearly-labelled plumbing test when the Binance basket is absent."""
    pref = tuple(SYMBOL_WHITELIST) if SYMBOL_WHITELIST else CRYPTO_ONLY
    out = sorted(p.name for p in data_dir.iterdir()
                 if p.is_dir() and p.name.startswith(pref))
    return out[:MAX_COINS] if MAX_COINS else out


def v33_data_dir() -> Path:
    """The basket dir if the lab set one, else the legacy DATA_DIR."""
    return Path(V32_DATA_DIR) if V32_DATA_DIR else DATA_DIR


def _stems_for(d: Path, warm, s1) -> list[str]:
    """Yearly (YYYY) or monthly (YYYY-MM) archives."""
    names = [f.name for f in d.glob("*.csv.gz")]
    if any(n.count("-") == 0 for n in names):
        return [str(y) for y in range(warm.year, s1.year + 1)]
    return [f"{y}-{m:02d}" for y in range(warm.year, s1.year + 1)
            for m in range(1, 13)]


# ===================================================================== #
# v32 PILLAR 2 — ICT BULLISH SMT DIVERGENCE + RELATIVE STRENGTH          #
# ===================================================================== #
def _last_blues(canvas, k: int = 2) -> list:
    """The last `k` confirmed BlueBox_SSL boxes, chronological."""
    out = []
    for b in reversed(getattr(canvas, "blues", None) or []):
        out.append(b)
        if len(out) >= k:
            break
    out.reverse()
    return out


class SMTBrain:
    """Cross-coin SMT divergence + relative-strength score, zero lookahead.

    Everything it reads is already closed: the per-coin SHARED 1H narrative
    canvas (the runner feeds it completed 1H bars only) and the 4H narrative
    canvas. At every union-timeline stamp `t` it applies the two bullish SMT
    patterns of the brief, per coin C with reference legs R = {BTCUSDT,
    ETHUSDT} \\ {C}:

      (A) some R sweeps its last BlueBox_SSL - its completed 1H bar low
          trades through the SSL bottom, i.e. a Lower Low into liquidity -
          while C REFUSES (C's low stays above C's own last SSL) -> BULL.
      (B) C sweeps its own BlueBox_SSL while every R HOLDS (no sweep) ->
          BULL: the correlated legs refuse to follow it down.

    A leg counts only while fresh: `SMT_MAX_AGE` stamps since the completed
    1H bar that made it (an SSL drawn BY the current bar is not a sweep of
    a prior pool, so it is ignored).

    Strength key (the brief's tie-break order, all descending except the
    last): SMT_BULL, displacement ratio = last YellowBox_FVG height / last
    GreenBox_OB height on the 1H canvas, 4H structure = +1 when the last
    structural event is an upward RedBox_BSL break, -1 when it is a
    BlueBox_SSL chop, 0 when neither exists; then the symbol name, so the
    order never depends on dict/set iteration order.
    """

    def __init__(self, refs=SMT_REFS):
        self.refs = tuple(refs)
        self.flags: dict = {}
        self.keys: dict = {}
        self.bull_stamps = 0

    @staticmethod
    def _leg(nar1, age: int):
        """('swept'|'held'|None, ssl_bottom) for one coin's 1H canvas."""
        if nar1 is None or not nar1.bars:
            return None, None
        blues = _last_blues(nar1, 1)
        if not blues:
            return None, None
        ssl = blues[-1]
        # the SSL must predate the current bar, else the "sweep" is the bar
        # that drew the box (self-referential, not a divergence)
        if ssl.start_idx >= len(nar1.bars) - 1:
            return None, ssl.y_bottom
        if age > SMT_MAX_AGE:
            return None, ssl.y_bottom          # stale: not a live leg
        low = float(nar1.bars[-1][2])
        return ("swept" if low <= ssl.y_bottom else "held"), ssl.y_bottom

    def observe(self, t, stamp_no: int, narratives: dict,
                last1h_no: dict, symbols: list) -> None:
        legs = {}
        for sym in symbols:
            age = stamp_no - last1h_no.get(sym, -10 ** 9)
            legs[sym] = self._leg(narratives[sym][1], age)
        ref_all = [s for s in symbols if s.startswith(self.refs)]
        flags, keys = {}, {}
        for sym in symbols:
            state, _ = legs[sym]
            refs_c = [s for s in ref_all if s != sym]
            any_swept = any(legs[s][0] == "swept" for s in refs_c)
            all_held = all(legs[s][0] != "swept" for s in refs_c)
            bull = bool(state == "held" and any_swept) or \
                bool(state == "swept" and bool(refs_c) and all_held)
            flags[sym] = bull
            nar1, nar4 = narratives[sym][1], narratives[sym][0]
            yb = getattr(nar1, "yellows_b", None) or []
            gr = getattr(nar1, "greens", None) or []
            disp = (yb[-1].height / gr[-1].height
                    if yb and gr and gr[-1].height > 0 else 0.0)
            htf = 0
            if nar4 is not None:
                b = nar4.bos_events[-1]["idx"] if nar4.bos_events else -1
                c = nar4.chop_events[-1]["idx"] if nar4.chop_events else -1
                htf = 1 if b > c else (-1 if c > b else 0)
            keys[sym] = (1 if bull else 0, disp, htf, sym)
        self.flags, self.keys = flags, keys
        self.bull_stamps += sum(flags.values())

    def order(self, symbols: list) -> list:
        """Strongest coin first (deterministic: symbol name breaks ties)."""
        if not self.keys:
            return list(symbols)
        return sorted(symbols, key=lambda s: (-self.keys[s][0],
                                              -self.keys[s][1],
                                              -self.keys[s][2], s))


# ==================================================================== #
# v33 (ج)+(د) — the ALPHA-LEADER and BASKET-REGIME brains.              #
# Both read ONLY SMTBrain.keys, which is built from completed 1H/4H      #
# narrative bars at the current stamp: keys[sym] = (bull, disp, htf, sym) #
#   bull = SMT_BULL divergence, disp = last 1H FVG height / OB height,   #
#   htf  = +1 last 4H structural break upward, -1 last 4H SSL chop, 0 n/a #
# Nothing here touches price of a bar that has not closed.               #
# ==================================================================== #
def _v33_key(smt, sym):
    return smt.keys.get(sym, (0, 0.0, 0, sym))


def _v33_breadth(smt, symbols: list) -> int:
    """How many coins of the basket show a 4H upward break right now."""
    return sum(1 for s in symbols if _v33_key(smt, s)[2] == 1)


def _v33_regime_of(smt, symbols: list) -> str:
    """(د) EXPANSION when BTC leads up or the basket breadth clears the
    threshold; RANGE otherwise. With BASKET_REGIME off it always reports
    EXPAND so the v32 behaviour is untouched."""
    if not BASKET_REGIME:
        return "EXPAND"
    btc = [s for s in symbols if s.startswith(SMT_REFS[0])]
    btc_up = bool(btc) and _v33_key(smt, btc[0])[2] == 1
    if btc_up or _v33_breadth(smt, symbols) >= REGIME_EXPAND_MIN:
        return "EXPAND"
    return "RANGE"


def _v33_leaders(smt, order: list, symbols: list) -> list:
    """(ج) The coins cash may be spent on this stamp, strongest first.
    `order` is already the SMT strength ranking, so the filters only
    REMOVE coins - they never invent a new priority."""
    if not V33_ALPHA_LEADER or LEADER_K <= 0:
        return list(symbols)
    out = []
    for sym in order:
        bull, disp, htf, _ = _v33_key(smt, sym)
        if LEADER_NEEDS_HTF and htf != 1:
            continue
        if LEADER_MIN_DISP > 0.0 and disp < LEADER_MIN_DISP:
            continue
        if LEADER_SMT_REQUIRED and not bull:
            continue
        out.append(sym)
        if len(out) >= LEADER_K:
            break
    return out


def _v33_allow(sym: str, rank: int, leaders: list, order: list) -> bool:
    if not V33_ALPHA_LEADER:
        return True
    return sym in leaders


def run_backtest(data_dir: Path, start: str, end: str,
                 warmup_days: int = 60, tag: str = ""):
    # ---- v30: the execution-cost model is resolved PER RUN ------------
    # COST/MIN_RISK_PCT are module constants derived from SLIPPAGE_BPS,
    # and a lab that sets SLIPPAGE_BPS after import would otherwise be
    # silently ignored (measured: the 5/10 bps stress arms came back
    # byte-identical to 0 bps). Recomputing here makes the knob live.
    global COST, MIN_RISK_PCT
    COST = FEE + SLIPPAGE_BPS / 10000.0
    MIN_RISK_PCT = 2 * COST
    from engine.causal_primitives import load_asset_ohlcv, resample_causal_tf
    s0 = pd.Timestamp(start).tz_localize("UTC")
    s1 = pd.Timestamp(end).tz_localize("UTC")
    warm = s0 - pd.Timedelta(days=warmup_days)
    symbols = discover_symbols(data_dir)
    # ONE shared portfolio pool across all coins and both engines
    # v32 SPEED: "open" holds ONLY the engines carrying a position, so the
    # per-stamp equity mark and the slot count stop scanning every engine
    # (4 frames x N coins). Maintained by _enter/_exit below.
    pool = {"cash": CAPITAL, "engines": [], "open": []}
    engines = []
    series = {}
    narratives = {}
    for sym in symbols:
        df = load_asset_ohlcv(data_dir / sym,
                              include_stems=_stems_for(data_dir / sym,
                                                       warm, s1))
        tf_5 = resample_causal_tf(df, "5min")
        tf_15 = resample_causal_tf(df, "15min")
        tf_30 = resample_causal_tf(df, "30min")
        tf_60 = resample_causal_tf(df, "1h")
        tf_4h = resample_causal_tf(df, STRUCT_TF)
        for tf in (tf_5, tf_15, tf_30, tf_60, tf_4h):
            tf.drop(index=tf[tf.index > s1].index, inplace=True)
        tf_5 = tf_5[tf_5.index >= warm]
        tf_15 = tf_15[tf_15.index >= warm]
        tf_30 = tf_30[tf_30.index >= warm]
        tf_60 = tf_60[tf_60.index >= warm]
        tf_4h = tf_4h[tf_4h.index >= warm]
        series[sym] = (tf_5, tf_15, tf_30, tf_60, tf_4h)
        narratives[sym] = (ChartCanvas(STRUCT_TF, narrative=True),
                           ChartCanvas("1h", narrative=True))
        # FIX2: LTF sniper engines (5m/15m) + swing engine (1h), all
        # watching the same4H board and the same1H target ladder
        for exec_tf in EXEC_FRAMES:
            e = ICTBoxEngine(sym, exec_tf=exec_tf, tag=tag)
            e.pool = pool
            engines.append(e)
    pool["engines"] = engines
    # v32 SPEED: the hot loop used to scan ALL engines (4 frames x N coins)
    # and skip the ones belonging to another symbol. With 8 coins that is a
    # 32-wide scan per stamp per symbol; indexing by symbol removes it.
    engines_by_sym = {}
    for e in engines:
        engines_by_sym.setdefault(e.symbol, []).append(e)
        e.nar4, e.nar1 = narratives[e.symbol]
    # pointers per (sym, stream) —4H and1H need backfill
    ptr = {(sym, s): 0 for sym in symbols for s in ("4h", "60")}
    eq_rows = []
    # ---- v32 PILLAR 2 state: stamp counter + per-coin 1H freshness ----
    # v33: the leader brain and the basket-regime brain both read the same
    # cross-coin score, so they are built even when the SMT GATE is off.
    smt = SMTBrain() if (SMT_BRAIN or V33_ALPHA_LEADER or BASKET_REGIME) \
        else None
    pool["smt"] = {}
    pool["smt_brain"] = smt
    stamp_no = 0
    v33_stamp = {"expand": 0, "range": 0, "leader_coins": {}}
    last1h_no = {sym: -10 ** 9 for sym in symbols}
    # global timeline = union of all exec frames (finest first)
    stamps = sorted(set().union(*[
        set(series[s][0].index) | set(series[s][1].index)
        | set(series[s][2].index)
        for s in symbols]))
    for t in stamps:
        stamp_no += 1
        if smt is not None:
            smt.observe(t, stamp_no, narratives, last1h_no, symbols)
            pool["smt"] = smt.flags
            order = smt.order(symbols)
        else:
            order = symbols
        # ---- v33 (ج)+(د): rank the basket, then arm the engines --------
        if smt is not None and (V33_ALPHA_LEADER or BASKET_REGIME):
            leaders = _v33_leaders(smt, order, symbols)
            regime = _v33_regime_of(smt, symbols)
            pool["leaders"] = leaders
            pool["regime"] = regime
            for sym2 in symbols:
                rank = order.index(sym2)
                allow = _v33_allow(sym2, rank, leaders, order)
                for e in engines_by_sym[sym2]:
                    e.v33_rank = rank
                    e.v33_regime = regime
                    e.v33_allow = (allow if e.exec_tf != "15min"
                                   else (allow and not (
                                       LEADER_15M_ONLY_TOP1
                                       and V33_ALPHA_LEADER and rank != 0)))
            v33_stamp["expand" if regime == "EXPAND" else "range"] += 1
            for _i, _s in enumerate(leaders):
                v33_stamp["leader_coins"][_s] = \
                    v33_stamp["leader_coins"].get(_s, 0) + (_i == 0)
        for sym in order:
            tf_5, tf_15, tf_30, tf_60, tf_4h = series[sym]
            # feed completed 4H bars up to t (causal: <= t)
            while (ptr[(sym, "4h")] < len(tf_4h)
                   and tf_4h.index[ptr[(sym, "4h")]] <= t):
                j = ptr[(sym, "4h")]
                if tf_4h.index[j] >= warm:
                    r = tf_4h.iloc[j]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    n4, _ = narratives[sym]
                    n4.on_bar(float(r.Open), float(r.High),
                              float(r.Low), float(r.Close), vol,
                              len(n4.bars), tf_4h.index[j])
                    for e in engines_by_sym[sym]:
                        if t >= s0:
                            e.warm = False
                        e.on_struct(float(r.Open), float(r.High),
                                    float(r.Low), float(r.Close),
                                    vol, len(e.struct_canvas.bars),
                                    tf_4h.index[j])
                ptr[(sym, "4h")] += 1
            # feed completed1H bars up to t — the shared target lens
            while (ptr[(sym, "60")] < len(tf_60)
                   and tf_60.index[ptr[(sym, "60")]] <= t):
                j = ptr[(sym, "60")]
                if tf_60.index[j] >= warm:
                    r = tf_60.iloc[j]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    _, n1 = narratives[sym]
                    n1.on_bar(float(r.Open), float(r.High),
                              float(r.Low), float(r.Close), vol,
                              len(n1.bars), tf_60.index[j])
                    last1h_no[sym] = stamp_no
                    for e in engines_by_sym[sym]:
                        e.on_htf(float(r.Open), float(r.High),
                                 float(r.Low), float(r.Close),
                                 vol, len(e.htf_canvas.bars),
                                 tf_60.index[j])
                ptr[(sym, "60")] += 1
            # ---- v28: causal 5m management of EVERY open position ----
            # The 5m bar ending at t is the last sub-bar of any 15m/30m/1h
            # bar that also ends at t, so it is applied FIRST. The 5min
            # engine is skipped: it already manages on this very tape.
            if MANAGE_5M and t in tf_5.index:
                r5 = tf_5.loc[t]
                for e in engines_by_sym[sym]:
                    if e.exec_tf != "5min" and e.qty > 0:
                        if t >= s0:
                            e.warm = False
                        e.manage_5m(float(r5.Open), float(r5.High),
                                    float(r5.Low), float(r5.Close), t)
            # feed each exec engine at its own completed stamps
            for tf_lbl, tf in (("5min", tf_5), ("15min", tf_15),
                               ("30min", tf_30), ("1h", tf_60)):
                if tf_lbl not in EXEC_FRAMES:
                    continue
                if t in tf.index:
                    r = tf.loc[t]
                    vol = float(r.Volume) if "Volume" in r else 0.0
                    for e in engines_by_sym[sym]:
                        if e.exec_tf == tf_lbl:
                            if t >= s0:
                                e.warm = False
                            e.on_exec(float(r.Open), float(r.High),
                                      float(r.Low), float(r.Close), vol,
                                      len(e.exec_canvas.bars), t)
        if t >= s0:
            eq_rows.append((t, pool["cash"] + sum(
                e.qty * e.price for e in engines if e.qty > 0)))
    # mark-to-market close (reporting only)
    out_trades = []
    for eng in engines:
        if eng.qty > 0:
            eng._exit(eng.price, "END_OF_DATA",
                      len(eng.exec_canvas.bars), eng.now)
        out_trades.extend(eng.trades)
    out_trades.sort(key=lambda t: str(t["entry_time"]))
    counts = {"v33_stamp_expand": v33_stamp["expand"],
              "v33_stamp_range": v33_stamp["range"]}
    for eng in engines:
        for k, v in eng.count.items():
            counts[k] = counts.get(k, 0) + v
        for (y, k), v in eng.yearly.items():
            counts[f"y{y}_{k}"] = counts.get(f"y{y}_{k}", 0) + v
    yearly = {}
    for t in out_trades:
        y = str(t["entry_time"])[:4]
        yearly[y] = yearly.get(y, 0) + 1
    fees = sum(eng.fees for eng in engines)
    eq = (pd.DataFrame(eq_rows, columns=["time", "equity"])
          .set_index("time") if eq_rows else pd.DataFrame())
    return {"trades": out_trades, "equity": eq, "count": counts,
            "fees": fees, "symbols": symbols, "pool_cash_end": pool["cash"],
            "yearly": yearly,
            # v32 PILLAR 2 telemetry: how many stamps carried at least one
            # SMT_BULL coin, and the final flags. Reporting only - nothing
            # in the engine reads these, so the book cannot change.
            "smt_bull_stamps": int(smt.bull_stamps) if smt else 0,
            "smt_stamps": int(stamp_no),
            # v33 (ج)+(د) telemetry: how the basket was read, stamp by
            # stamp. Reporting only - no engine branch reads these.
            "v33_stamps_expand": int(v33_stamp["expand"]),
            "v33_stamps_range": int(v33_stamp["range"]),
            "v33_leader_stamps": dict(sorted(
                v33_stamp["leader_coins"].items()))}


# ==================================================================== #
# Reporting
# ==================================================================== #
def summarize(run, capital=CAPITAL):
    tr = run["trades"]
    n = len(tr)
    # L1 classification: winners are >= +3.0R by construction; shield
    # breakevens are neither winners nor losses
    wins = [t for t in tr if t.get("class") == "WIN"
            or (t["net_pnl"] > 0 and t["R"] >= MIN_R - 1e-9)]
    bes = [t for t in tr if t.get("class") == "BE"]
    # ---- v31 ARM 1: STRUCTURAL WINS (net > 0, R < 3.00) --------------
    # They are NOT winners (so min_winner_R stays >= 3.00R and A2 stays
    # sacred) and they are NOT losses (so banking +1.8R no longer counts
    # as a lost trade). Their profit IS in the profit factor, because
    # ignoring it would understate the book.
    swins = [t for t in tr if t.get("class") == "SWIN"]
    losses = [t for t in tr if t.get("class") == "LOSS"
              or (t["net_pnl"] <= 0
                  and t.get("class") not in ("BE", "SWIN"))]
    assert all(t["R"] >= MIN_R - 1e-9 for t in wins), \
        "L1 VIOLATION: a winner below +3.0R exists!"
    assert all(0 < t["R"] < MIN_R - 1e-9 for t in swins), \
        "SWIN VIOLATION: a structural win outside (0, 3.00R) exists!"
    gp = sum(t["net_pnl"] for t in wins) + sum(t["net_pnl"] for t in swins)
    gl = -sum(t["net_pnl"] for t in losses)
    rs = [t["R"] for t in tr]
    eq = run["equity"]
    end_eq = float(eq["equity"].iloc[-1]) if len(eq) else capital
    peak = eq["equity"].cummax() if len(eq) else None
    dd = float(((eq["equity"] - peak) / peak * 100).min()) if len(eq) else 0.0
    # consecutive TRUE losses (breakevens do not extend the streak)
    streak = best = 0
    for t in tr:
        if t.get("class") == "LOSS" or (
                t["net_pnl"] <= 0 and t.get("class") != "BE"):
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    # prompt law: max consecutive LOSSES <= 3 — enforced by the
    # five-assert block at the end of main() (which must see ALL
    # artifacts), so here we only flag it loudly
    if best > 3:
        print(f"!! L4 VIOLATION: streak of {best} losses > 3")
    # monthly from equity
    monthly = []
    if len(eq):
        me = eq["equity"].resample("ME").last()
        prev = capital
        for ts, v in me.items():
            monthly.append([ts.strftime("%Y-%m"),
                            round((v - prev) / prev * 100, 2)])
            prev = v
    return {
        "trades": n, "wins": len(wins), "breakevens": len(bes),
        "struct_wins": len(swins),
        "win_rate_pct": round(
            len(wins) / max(len(wins) + len(losses), 1) * 100, 1),
        # the honest second reading once structural take-profits exist
        "win_rate_incl_swin_pct": round(
            (len(wins) + len(swins))
            / max(len(wins) + len(swins) + len(losses), 1) * 100, 1),
        "totR": round(sum(t["R"] for t in tr), 2),
        "swin_totR": round(sum(t["R"] for t in swins), 2),
        "min_swin_R": round(min((t["R"] for t in swins), default=0.0), 2),
        "max_swin_R": round(max((t["R"] for t in swins), default=0.0), 2),
        "min_entry_target_R": round(min(
            (t["entry_target_R"] for t in tr
             if t.get("entry_target_R") is not None), default=0.0), 2),
        "profit_factor": round(gp / gl, 2) if gl > 0 else None,
        "net_pnl": round(end_eq - capital, 2),
        "net_pct": round((end_eq - capital) / capital * 100, 2),
        "end_equity": round(end_eq, 2),
        "max_drawdown_pct": round(dd, 2),
        "max_consecutive_losses": best,
        "avg_R": round(float(np.mean(rs)), 2) if rs else 0.0,
        "min_winner_R": round(min([t["R"] for t in wins]), 2) if wins else None,
        "runners_ge_5R": sum(1 for t in wins if t["R"] >= 5),
        "runners_ge_10R": sum(1 for t in wins if t["R"] >= 10),
        "runners_ge_20R": sum(1 for t in wins if t["R"] >= 20),
        "runners_4r_plus": sum(1 for t in wins if t["R"] >= 4 - 1e-9),
        "max_winner_R": round(max(t["R"] for t in wins), 2)
                        if wins else None,
        "max_R": round(max(rs), 2) if rs else None,
        "fees": round(run["fees"], 2),
        "exit_reasons": _hist(t["exit_reason"] for t in tr),
        "s1_kinds": _hist(t.get("s1_kind", "-") for t in tr),
        "monthly": monthly,
        **_cadence(eq, tr, capital),
        "count": run["count"],
        "symbols": run["symbols"],
        "yearly": run.get("yearly", {}),
    }


def _cadence(eq, tr, capital):
    """v31: the business question is not only the total, it is the
    WEEKLY/MONTHLY machine. Measured on the calendar span of the book,
    not only on the months that happened to trade."""
    out = {}
    if not len(eq):
        return out
    e = eq["equity"].resample("ME").last().dropna()
    if not len(e):
        return out
    months = len(e)
    ret = e.pct_change().fillna(e.iloc[0] / capital - 1.0)
    pos = int((ret > 0).sum())
    end = float(e.iloc[-1])
    out["calendar_months"] = months
    out["profitable_months"] = pos
    out["profitable_months_pct"] = round(100 * pos / months, 1)
    out["monthly_net_pct_med"] = round(float(ret.median() * 100), 2)
    out["monthly_net_pct_mean"] = round(float(ret.mean() * 100), 2)
    out["compounded_monthly_pct"] = round(
        100 * ((end / capital) ** (1 / months) - 1), 2)
    out["best_month_pct"] = round(float(ret.max() * 100), 2)
    out["worst_month_pct"] = round(float(ret.min() * 100), 2)
    wins = [t for t in tr if t.get("class") in ("WIN", "SWIN")]
    out["wins_per_month"] = round(len(wins) / months, 2)
    out["trades_per_month"] = round(len(tr) / months, 2)
    return out


def _hist(it):
    out = {}
    for k in it:
        out[k] = out.get(k, 0) + 1
    return out


def anatomy_table(trades, n=10):
    rows = []
    for t in trades[:n]:
        rows.append({
            "entry_time": t["entry_time"],
            "purple_mid": t["purple_mid"],
            "broken_red": t["broken_red"],
            "yellow": t["yellow"],
            "green": t["green"],
            "stop_blue": t["wave_low_blue"],
            "entry": t["entry_price"],
            "stop": t["stop_price"],
            "wall": t["wall"],
            "exit_reason": t["exit_reason"],
            "R": round(t["R"], 2),
        })
    return rows


def bull_stats(run):
    tr = run["trades"]
    rs = [t["R"] for t in tr]
    return {
        "trades": len(tr),
        "wins_ge_3R": sum(1 for r in rs if r >= MIN_R - 1e-9),
        "runners_ge_5R": sum(1 for r in rs if r >= 5),
        "runners_ge_10R": sum(1 for r in rs if r >= 10),
        "runners_ge_20R": sum(1 for r in rs if r >= 20),
        "max_R": round(max(rs), 2) if rs else 0,
        "count": run["count"],
    }


def ascii_diagram(t: dict) -> str:
    """Vertical price-axis box diagram for one trade (top -> bottom)."""
    def line(label, box, note=""):
        if box is None:
            return f"  [    ] {label:<34} (none) {note}"
        return (f"  [{box['kind']:<6}] {label:<34} "
                f"Top:{box['top']:>10.2f} | Bottom:{box['bottom']:>10.2f} {note}")
    risk = t["entry_price"] - t["stop_price"]
    tgt = t["entry_price"] + MIN_R * risk
    out = []
    out.append(f"  ENTRY {t['entry_time']}  R={t['R']:+.2f} "
               f"({t['exit_reason']})")
    if t.get("wall"):
        out.append(line("4H Red/Yellow wall (target ceiling)",
                        {"kind": "WALL", **t["wall"]}))
    else:
        out.append("  [ open sky ] no bearish wall above entry "
                   "(ATH expansion)")
    out.append(f"  [ 3R line ] Target = entry + 3 x Risk"
               f"          Price:{tgt:>10.2f}")
    out.append(line("broken RedBox_BSL (BOS)", t["broken_red"],
                    "<-- broken by body close"))
    out.append(f"  [ PURPLE ] Dealing-range mid (50%)"
               f"           Price:{t['purple_mid']:>10.2f}"
               f"   (above=Premium, below=Discount)")
    out.append(line("YellowBox_BullFVG (entry line=Top)", t["yellow"]))
    out.append(line("GreenBox_BullOB (under yellow)", t["green"]))
    out.append(line("BlueBox wave low / Stop line", t["wave_low_blue"],
                    f"<-- Stop:{t['stop_price']:.2f}"))
    return "\n".join(out)


# ==================================================================== #
# main
# ==================================================================== #
def main():
    RESULTS.mkdir(exist_ok=True)
    print(f"[v31-narrative] symbols discovered: "
          f"{discover_symbols(v33_data_dir())}")
    run = run_backtest(v33_data_dir(), FULL_START, FULL_END)
    # PERSIST FIRST — a later assert must never destroy the evidence
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v33.csv",
                                       index=False)
    print("yearly fills:", json.dumps(run["yearly"], indent=2))
    print("funnel:", json.dumps(run["count"], indent=2))
    s = summarize(run)
    print(json.dumps({k: v for k, v in s.items()
                      if k not in ("monthly", "count")}, indent=2))
    print("funnel:", json.dumps(s["count"], indent=2))
    print("yearly fills:", json.dumps(run["yearly"], indent=2))
    pd.DataFrame(run["trades"]).to_csv(RESULTS / "trades_v33.csv",
                                       index=False)
    pd.DataFrame(s["monthly"], columns=["month",
                                        "ret_pct"]).to_csv(
        RESULTS / "monthly_v33.csv", index=False)
    if len(run["equity"]):
        run["equity"].to_csv(RESULTS / "equity_v33.csv")
    with open(RESULTS / "summary_v33.json", "w") as f:
        json.dump(s, f, indent=2, default=str)
    # anatomy + diagrams
    ana = anatomy_table(run["trades"], 10)
    with open(RESULTS / "anatomy_v33.json", "w") as f:
        json.dump(ana, f, indent=2)
    print("\n=== SECTION 2: ANATOMY (first 10) ===")
    for row in ana:
        print(row)
    print("\n=== ASCII DIAGRAMS (first 3) ===")
    for t in run["trades"][:3]:
        print(ascii_diagram(t))
        print()
    # bull window (tagged counters)
    bull = run_backtest(v33_data_dir(), BULL_START, BULL_END, tag="BULL")
    bs = bull_stats(bull)
    print("\n[v31-narrative] BULL RUN", BULL_START, "..", BULL_END)
    print(json.dumps(bs, indent=2))
    pd.DataFrame(bull["trades"]).to_csv(RESULTS / "trades_v33_bull.csv",
                                        index=False)
    with open(RESULTS / "bull_v33.json", "w") as f:
        json.dump(bs, f, indent=2, default=str)
    # ================= THE FIVE MANDATORY ASSERTS ==================
    # (all five checked on the SAME full run, after artifacts persist)
    tr = run["trades"]
    wins = [t for t in tr if t.get("class") == "WIN"
            or (t["net_pnl"] > 0 and t["R"] >= MIN_R - 1e-9)]
    losses = [t for t in tr if t.get("class") == "LOSS"
              or (t["net_pnl"] <= 0
                  and t.get("class") not in ("BE", "SWIN"))]
    swins = [t for t in tr if t.get("class") == "SWIN"]
    decided = len(wins) + len(losses)
    win_rate = len(wins) / decided if decided else 0.0
    win_rate_incl = ((len(wins) + len(swins))
                     / max(len(wins) + len(swins) + len(losses), 1))
    min_target_r = min((t["entry_target_R"] for t in tr
                        if t.get("entry_target_R") is not None),
                       default=None)
    min_winner_r = min((t["R"] for t in wins), default=0.0)
    runners_4r = sum(1 for t in wins if t["R"] >= 4 - 1e-9)
    max_winner_r = max((t["R"] for t in wins), default=0.0)
    max_consec = s["max_consecutive_losses"]
    total = len(tr)
    yearly = {str(k): v for k, v in run["yearly"].items()}

    checks = [
        (1, "WR >= 60%", win_rate >= 0.60,
         f"{win_rate:.2%} ({len(wins)}W/{len(losses)}L)"
         + (f" | incl. structural wins {win_rate_incl:.2%} "
            f"({len(wins)}+{len(swins)})" if swins else "")),
        (2, "min_winner_R >= 3.00", min_winner_r >= 3.00 - 1e-6,
         f"{min_winner_r:.2f}R"
         + (f" | entry target min {min_target_r:.2f}R"
            if min_target_r is not None else "")
         + (f" | {len(swins)} structural wins "
            f"({min((t['R'] for t in swins), default=0):.2f}"
            f"..{max((t['R'] for t in swins), default=0):.2f}R)"
            if swins else "")),
        (3, "runners_4r_plus >= 5 AND max_winner_R >= 6.0",
         runners_4r >= 5 and max_winner_r >= 6.0,
         f">=4R:{runners_4r} max:{max_winner_r:.2f}R"),
        (4, "max_consecutive_losses <= 3", max_consec <= 3,
         f"{max_consec}"),
        (5, "total >= 150 AND yearly[y] >= 12 for 2021..2025",
         total >= 150 and all(yearly.get(str(y), 0) >= 12
                              for y in (2021, 2022, 2023, 2024, 2025)),
         f"total:{total} yearly:{yearly}"),
    ]
    # transparency: the streak under both readings (a scratch is not a
    # loss, but does it INTERRUPT a run of losses?)
    cons = cur = 0
    for t in tr:
        if t.get("class") == "LOSS":
            cur += 1; cons = max(cons, cur)
        elif t.get("class") == "WIN":
            cur = 0
    cad = _cadence(run["equity"], tr, CAPITAL)
    if cad:
        print(f"[v33] CADENCE: {cad['calendar_months']} months · "
              f"profitable {cad['profitable_months']}/"
              f"{cad['calendar_months']} "
              f"({cad['profitable_months_pct']}%) · compounded "
              f"{cad['compounded_monthly_pct']}%/month · median month "
              f"{cad['monthly_net_pct_med']}% · wins/month "
              f"{cad['wins_per_month']} · trades/month "
              f"{cad['trades_per_month']} · best {cad['best_month_pct']}% "
              f"worst {cad['worst_month_pct']}%")
    print(f"[v33] classes: WIN={len(wins)} SWIN={len(swins)} "
          f"BE={sum(1 for t in tr if t.get('class')=='BE')} "
          f"LOSS={len(losses)} · totR="
          f"{sum(t['R'] for t in tr):+.2f}")
    print(f"[v33] streak: BE-resets={max_consec}  "
          f"conservative(BE does not reset)={cons}")
    print("\n============ THE FIVE MANDATORY ASSERTS ============")
    failed = []
    for n, label, ok, detail in checks:
        print(f"[v33] ASSERT{n} {'PASSED' if ok else 'FAILED'} :: "
              f"{label} :: {detail}")
        if not ok:
            failed.append(n)
    with open(RESULTS / "asserts_v33.json", "w") as f:
        json.dump([{"assert": n, "rule": lab, "passed": bool(ok),
                    "observed": det} for n, lab, ok, det in checks],
                  f, indent=2)
    if failed:
        raise AssertionError(
            f"v33 DID NOT PASS asserts {failed} — see asserts_v33.json")
    print("[v33] ALL FIVE ASSERTS PASSED")


if __name__ == "__main__":
    main()
