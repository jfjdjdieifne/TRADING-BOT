# HANDOFF — v27 (sacred seam law) + the 5m intra-box lab

**Branch:** `arena/d2e74635-trading-bot`
**Engine:** `halal_spot/strategy_v27_ict_supreme.py` — behaviourally IDENTICAL to v26
(verified trade-for-trade: same times, classes, R and net_pnl on all 297 trades)
plus two hard runtime asserts.
**Lab:** `halal_spot/lab_v27_exact.py` (takes a trades CSV as argv[1]) -> `results/lab_v27_grid_v26.{csv,json}`
**Run:** `results/run_v27_log.txt` (356 s) · **Report:** `results/REPORT_AR_v27.md`

## v27 result: 4/5 asserts (identical to v26)

297 trades · 70W/66BE/161L · WR decided **30.30%** · PF 1.26 · net **+31.90%**
($200 -> $263.79) · maxDD **-14.41%** · min winner 3.00R · >=4R **18** · >=10R **6** ·
maxR 19.38 · streak **3** (BE-resets) / 15 (conservative) · yearly 82/68/16/47/47/37.
ASSERT1 FAILED (30.30%); ASSERT2/3/4/5 PASSED.
`sacred_law_seam_ok = 327` fills passed the hard asserts, zero violations.

## The two new hard asserts (in `_enter`, one place, all fill paths)

```python
seam = min(s.green.y_top, s.yellow.y_bottom)
assert fill_px <= seam + 1e-9, "FATAL BUG: bought ABOVE the GreenBox ceiling mid-wave"
purple_now = self.struct_canvas.purple
if purple_now is not None:
    assert fill_px <= purple_now.mid + 1e-9, "FATAL BUG: bought in PREMIUM"
```
Verified BEFORE adding them: 0 fills above green.y_top in trades_v25.csv (206)
and trades_v26.csv (297); 272/297 sit exactly ON the seam. The 7 apparent
`purple.mid` violations are CSV rounding at the half-cent level (0.0000%).

## What the 5m microscope REFUTED (do NOT re-test)

- **Deep box entry** `entry = stop + alpha*(seam-stop)`: winners fall
  monotonically **76 (a=1.0) -> 74 (0.75) -> 57 (0.5) -> 36 (0.25)**,
  WR 26.03% -> 12.95%, nofill 5 -> 19, total R -116 -> -759.
  The 19.38R runner would have been MISSED entirely (price never returned to
  the seam after the fill). Winner counts are estimator-independent.
  Second reason: a 0.106% risk makes the round-trip fee 1.9R, so a deep
  entry turns a -2.89R stop-out into **-4.78R**.
- **Method B (5m absorption candle inside the box)**: WR 23.53%, 93 of 297
  setups never fill, weakest year 13. AND it contradicts the sacred law:
  the 28 setups whose only absorption closed ABOVE the seam are the single
  best cohort in the data (**14W/8L = 63.6%** decided WR).
- **Mechanism 3 (second chance from the alive box)**: the brief's accounting
  (a collapsed re-entry nets 0.00R / "zero loss") is arithmetically false —
  the re-entry risks (re-entry - stop) again. Fake: WR 38.67% at n=292.
  Honest (leg 2 is a real trade): **WR 19.93% at n=477 with 233 losses**.
  141 hidden losses. The lab books both legs; never collapse them.
- **Buying the rejection above the seam** (breaking the sacred law by up to
  1.0R): WR 15.34%, total R -129.6. The 63.6% cohort is NOT harvestable as
  an entry rule; it is a post-hoc description of 28 trades.
- Cohort truth vs the brief: KNIVES = **19** (not 73); RETESTS = 290;
  collapses = 248 (61 BE / 140 LOSS / 47 WIN) — the brief's "61 winners from
  inside the box" are **61 breakevens**.
- Mechanism 2 (bug-free causal shield) was ALREADY implemented verbatim since
  v25: `if fired and c > be: stop_px = max(stop_px, be)` with the comment
  "a stop must sit BELOW the market". No arming bug exists.

## The win-rate frontier (five independent measurements, monotone)

| n | WR decided | source | assert 5 |
|---|---|---|---|
| 22 decided / 28 total | **63.6%** | above-the-seam absorption cohort | fails by ~5x |
| 68 | 57.1% | v24 audit `sky10&dem1`+A0.25 | fails |
| 157 | 44.8% | v24 audit `dem4&raidlow1`+A0.25 | passes |
| 206 | 32.28% | **v25 shipped (money champion)** | passes |
| 297 | 30.30% | **v26/v27 shipped (robustness champion)** | passes |

WR >= 60% EXISTS in this data at ~28 trades over 5.5 years; assert 5 demands
150 trades and >= 12 per year. The gap is a factor of ~5 in sample size.

## Lab calibration (always re-check after editing the lab)

`BOOK_RATIO = 0.673` (median booked R / mfe_close_R on shipped winners).
`ride()` ends the ride at the first close that gives back 50% of the peak gain
since the lock (50% is sanctioned), floors the estimate at MIN_R and caps it at
the peak. Validation at alpha=1.0 reproduces 55 of the engine's 70 winners;
lab maxR 13.07 vs real 19.38 (conservative). HORIZON = 3000 5m bars for EVERY
trade. Locate bars BY TIME, never by `entry_idx` (canvas-local).

## Champions

- **v25 (`strategy_v25_ict_narrative.py`, STOP_SOURCE="htf")** — money:
  +42.14%, PF 1.43, WR 32.28%, one losing year, but only +2 trades of margin
  on the assert-5 floor (2023/2024 = 14 each).
- **v27 (`strategy_v27_ict_supreme.py`, STOP_SOURCE="hybrid")** — robustness:
  297 trades, 18 runners >=4R, 6 >=10R, DD -14.41%, +4 trades of margin,
  2024/2025 alive at 47 each; costs net (+31.90%) and two losing years.

## Recovery

```bash
cd /home/user/TRADING-BOT && git fetch origin -q \
  && git reset --hard origin/arena/d2e74635-trading-bot
pip install --user --break-system-packages numpy pandas pytest
cd halal_spot && timeout 1750 python3 strategy_v27_ict_supreme.py > results/run_v27_log.txt 2>&1
```
The sandbox has been wiped 11+ times: commit and push after every measurement.
Runs exit 1 by design — artifacts are written before the asserts, never after.
