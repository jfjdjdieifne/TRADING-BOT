# HANDOFF — strategy_v19_ict.py (ICT Pure Price Action)

**Date:** 2026-11-17 · **Branch:** `arena/d2e74635-trading-bot` · **Goal:** 50%+/month (ONLY goal).
**User's binding source:** forwarded Michael Headleston / ICT answers (A–I) — see chat + `STRATEGY_CONTEXT_V18.md`.

## What this is
A ground-up rewrite of the spot-long BTC system as PURE ZONES: no EMA/RSI/ATR/milk-ladder/
24h-freeze (grep-verified: `grep -cE "EMA_|RSI_|ATR|0\.45|32\.5|0\.952|Milk" strategy_v19_ict.py` → 0).

## Architecture (file: strategy_v19_ict.py, ~810 lines)
- `Zone(top,bottom,start,state)` — every level is a rectangle; `breaks(c)` = body close beyond.
- `StructureBook` (per timeframe): causal swings (2-right-confirm, TopoSwing-style), bullish/bearish
  FVGs with displacement (body>avg10 & vol>avg10 — relativity, no thresholds), OB = last down swing
  leg before MSS, BSL/SSL liquidity pools with overlap-merge. Housekeeping prune every 96 bars
  (inactive zones dropped, swings capped 600) — REQUIRED for speed (O(n²) otherwise).
- `ICTEngine` states: WAIT_S1 → WAIT_MSS → WAIT_RETRACE → IN_POS.
  - S1 (a): execution-frame SSL sweep that ALSO tags an active 4h SSL pool (cross-frame confluence —
    killed 941 meaningless micro-sweeps). S1 (b): entry into active 4h FVG/OB POI.
  - S2: MSS = body close above last sub-high + bullish FVG completed after break + OB left behind;
    entry gate = max(break_idx, fvg.start_idx, ob.start_idx) → fill only on strictly later bars.
  - S3: retrace touch of min(fvg.top, ob.top) as limit; stop = min(ob.bottom, sweep_low) − spread
    margin (MEASURED BEST: OB-only → risk≈0 R explodes; cluster floor → PF0.75; this → PF1.22).
  - S4: target = nearest active pool (exec then 4h BSL/4h bearish FVG) ≥3R (sacred; reject if none);
    cancel if target prints before retrace (no chase); 3R-on-displacement lock ≥2.5R;
    stagnation 192 bars (48h) instead of dead-8h; structural reset: 2 losses → block coin until
    4h BOS/SSL sweep (never time); trailing = 4h Protected-Low only (15m trail measured to chop
    winners at +0.05R — removed).
- `run_backtest`: 15m execution + 4h HTF, causal resample, 60d structure-only warmup, spot cash
  accounting with fees 0.1/side. `tag="BULL"` prefixes funnel counters.

## How to run
```bash
cd /home/user/TRADING-BOT/halal_spot
pip install --user --break-system-packages numpy pandas   # after sandbox wipes (4 so far)
python3 strategy_v19_ict.py        # ~20s; writes results/{trades,monthly,summary}_v19.json/csv
```
Outputs: `results/trades_v19.csv` (entry_time, S1/S2/S3/S4 fields, R, exit_reason),
`results/summary_v19.json`, `results/monthly_v19.csv`.

## MEASURED STATE (current code, 2021-01→2026-10, $200)
**29 trades · WR 27.6% · PF 1.22 · net +4.24% ($200→208.48) · avgR −0.09 ·
min winner +2.66R · max +3.27R · max streak 6 · DD −8.86% · fees $7.13 · months 10+/15−/44.**
Exits: SL_STRUCT 21 / STAGNATION 5 / BSL_TARGET 3. Winners all in +2.34..+7.7R band (structural).
Funnel: s1 676 → mss_break 611 → wait_no_fvg 1872 → mss_confirmed 146 → entries 29;
cancel_target_first 47 / cancel_zone_invalid 103 / reject_below_3r 26 / structural_reset_block 13.
**BULL window 2021-01→05: 0 trades** — funnel: s1 50, mss_break 45, mss_confirmed 2,
reject_below_3r 8 (no ≥3R pool), wait_no_fvg 204, cancel_target_first 2, cancel_zone_invalid 1.
→ bull failure diagnosed: stage-2/3 gates (FVG completion + 3R pool distance), not S1.

## Measured dead ends (do NOT retry)
- 15m trailing after BOS → winners at +0.05R (removed; 4h protected-low only).
- Stop = OB bottom only → risk≈0 → R up to 1.7e5 (nonsense sizing).
- Stop = cluster floor min(ob,fvg) bottoms → PF0.75 (worse).
- Stop = min(ob,sweep) with 15m trail → PF0.47 (first run).
- S1 without 4h confluence → 941 noise sweeps, WR 30% losers.
- Freshest/highest FVG entry → impossible 3R (fixed: earliest FVG, min-top entry).
- 1h frame → no FVGs (wait_no_fvg 714); 15m frame → FVGs exist.
- Zone invalidation O(n) over unpruned lists → 600s timeout (prune added).

## Known gaps vs user bar
1. WR 27.6% (user wants >60) — losers are structurally stopped, winners near-3R: the ratio is the
   problem: need entry-quality (earlier POI / better MSS) not stop tweaks.
2. Bull run 2021: 0 trades — next lever: allow S1 during bull = HTF POI retrace only (already S1b,
   was only 6 fills) or accept 3R-reject when pools far (8 setups died here).
3. Streak 6 (user old spec ≤3; prompt's structural reset is the binding rule — 13 blocks fired).
4. Goal 50%/mo: current +4.24% over 5.8 YEARS — nowhere near; honest state.

## Next steps (in order)
1. Attack reject_below_3r in bull (8/10 setups): widen target search (pool merge on exec frame?)
   or accept smaller-risk entries only when stop is near (cluster guard: reject if risk>1.5%).
2. Entry quality: require S1 sweep depth > X% of pool? (measurable) or1h MSS instead of15m.
3. Multi-coin 2–3 slots (BTC only today; prompt portfolio rule) — biggest structural win left.
4. Re-run, deliver MONTHLY, keep all 5 report sections.

## Ops
- Push: `git add halal_spot && git commit -m "..." && git push origin arena/d2e74635-trading-bot`
- Folder: https://github.com/jfjdjdieifne/TRADING-BOT/tree/arena/d2e74635-trading-bot/halal_spot
- Wipes: deliverables must be committed same session; pip reinstall after each wipe;
  recover worktree via `git fetch && git reset --hard origin/<branch>` then restore files from commits.


---

# HANDOFF ADDENDUM — strategy_v21_boxes.py (Visual Box Engine, 2026-11-17)

## What changed vs v19 (the five "crimes" fixed)
1. OB (GreenBox) built at the WAVE BASE (last down candle(s) before the
   launch), clipped + **asserted under the YellowBox** (v19 drew it above
   the broken high). asserts at lines 184-185.
2. FVG (YellowBox) = pure visible gap `c3.low > c1.high` — no avg/vol
   displacement filter; stack checked on the breaking wave itself with
   prompt-grace of 2 candles after the break (no20-bar wait counter).
3. 3R gate = 4H wall distance vs OPEN SKY: if no unbroken bearish 4H box
   sits at/above the entry line (ATH expansion), the trade passes without
   an old-high requirement (fixes bull-run rejections).
4. NO hard TP, NO stagnation timer: structural trail under Protected Blue
   after each BOS; at >=3R lock under a box (>=3R); top-sell only on
   ratchet + bearish CHoCH + bearish FVG (none fired; all exits
   STOP_BLUE/lock — measured max_R 9.88).
5. Portfolio-ready (slot = 50% equity, max 2 slots, cash compounding);
   data folder holds ONLY BTCUSD_5m (8 yearly csv.gz) so single-coin run.
   HTF order-flow filter: releases after2 losses require purple-box
   higher-low (rising) — blocked12 releases in measured run.

## Architecture
- `Box(y_bottom, y_top, start_idx, kind, tf)` with height/mid/
  quarter_bottom/contains/is_below/overlaps/broken_up/down/wick_swept.
- `ChartCanvas` (per tf): 3-bar fractal blues/reds, pure-gap yellows
  (bull+bear), green OB from wave base, purple dealing range
  (latest swing low -> latest swing high), bos/sweep/chop events,
  prune every96 bars.
- `ICTBoxEngine`: WAIT_ANCHOR (blue sweep | box-tap in BOS-continuation
  state) -> WAIT_BOS (fresh red break) -> WAIT_SETUP (stack born from the
  anchor, wall gate, third-loss gate) -> WAIT_RETRACE (fill strictly
  after gate_idx; board/premium/wall re-checked AT fill) -> IN_POS.
- EXEC_TF = "1H" (prompt allows15m/1H;15m measured PF0.75/WR27 —
  boxes smaller than noise), STRUCT_TF = "4h".
- Third-loss gate: fresh 4H red break (time-compared) + entry in the
  bottom quarter of purple + board GREEN + purple rising.

## MEASURED (2021-01 -> 2026-10, $200, BTC only)
**77 trades | WR36.4% | PF1.63 | net +10.09% (200 -> 220.19) |
DD -4.8% | avg win +2.47R / avg loss -1.13R | max_R +9.88 |
max_consecutive_losses = 11 (FAIL vs required <=3 — OPEN GAP) |
fees 8.22 | years: 2021 +9.3 / 2022 +3.7 / 2023 +0.5 / 2024 +7.1 /
2025 -2.1 / 2026 +1.7 | months 22+/26-/22zero.
BULL 2021-01..05: 9 trades, max_R 4.08, runners >=10R: 0 (vs v19 = 0
trades — fixed; big runners still absent).**

## Measured dead ends in v21 (do not retry)
- EXEC15m: PF0.57-0.75, streak15-27 (noise eats0.4% stops).
- Direct green-yellow overlap as a release gate: freezes the engine
  (31k blocked,5 trades total).
- Order-flow gate at ANCHOR (all entries): net drops +10.09 -> +6.79.
- Box-tap anchors in every board state: garbage entries (restricted to
  BOS_CONTINUATION).
- Board recovery with close > blue bottom only: board flips green in
  waterfalls (needs close > blue TOP).
- Purple update requiring red.start >= blue.start: purple freezes in
  downtrends, order-flow filter goes blind.
- Event-consumption before state machine / state stuck IN_POS after
  first exit / 4H-index vs15m-index gate comparison — all fixed
  (each froze the engine to0-1 trades).

## Open gaps (next session)
1. max_consecutive_losses11 >3: streaks cluster in release clusters
   (2021-04, 2022-09). Candidate: require release stack yellow.bottom
   <= quarter (full stack cheap, not just entry) or1H board mode at
   release — measure, do not guess.
2. Bull runners >=10R still 0: lock/exit path never lets go early but
   nothing in the9 bull trades rode past4.08R — inspect whether trail
   stops at protected blue are too close during expansion.
3. Multi-coin: only BTCUSD_5m exists in data/ — portfolio code is
   ready (discover_symbols + SLOT/MAX_SLOTS) when more data arrives.
4. 2025 -2.1%: check board RED/recovery cadence in that year.
