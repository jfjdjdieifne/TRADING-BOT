# HANDOFF — v26 (ICT Master: hybrid stop) and the measured WR frontier

**Branch:** `arena/d2e74635-trading-bot`
**Files:** `halal_spot/strategy_v26_ict_master.py` (hybrid stop) · `halal_spot/strategy_v25_ict_narrative.py` (HTF stop, money champion)
**Runs:** `results/run_v26_log.txt` (527 s) · `results/run_v25_log.txt` (402 s)
**Reports:** `results/REPORT_AR_v26.md` · `results/REPORT_AR_v25.md` (arithmetic corrected in place)
**New audits:** `audit_v25_to_v26.py` (CSV-level) · `audit_v25_master.py` (exact bar-walk, takes a trades CSV as argv[1]) · `audit_v26_invalidation.py`

## The single v26 change

`STOP_SOURCE = "hybrid"` — keep the tight LTF stop whenever it can pay the
round trip (`risk > 2 * FEE * entry`), widen to the HTF demand floor only when
it cannot. Counters: `stop_kept_ltf` 43,225 · `stop_widened_to_htf` 144,878.
Everything else is identical to v25 (`SHIELD_RULE="MID+BOS"`, `TIER3_RULE="A0.5"`,
`CTX_GATE=True`, `CTX_TIER3=False`, `CTX_MODE="or"`, `FLOW_GATE=False`,
`STRUCTURAL_RESET=False`, `TIER3_ENTRY_CHOKE=True`, `BE_CONSUMES_RANGE=False`).

## v26 vs v25 (both 4/5 asserts)

| | v26 hybrid | v25 htf |
|---|---|---|
| trades | **297** | 206 |
| W/BE/L | 70/66/161 | 51/48/107 |
| WR decided | 30.30% | **32.28%** |
| net | +31.90% ($263.79) | **+42.14% ($284.29)** |
| PF | 1.26 | **1.43** |
| maxDD | **-14.41%** | -17.43% |
| >=4R / >=10R / maxR | **18 / 6 / 19.38** | 13 / 3 / 19.38 |
| min year (assert 5 floor 12) | **16** | 14 |
| losing years | 2023 -8.45, 2025 -5.44 | 2023 -4.83 |
| mean win / mean loss | $4.40 / -$1.52 | **$5.51** / -$1.84 |

**v25 = money champion, v26 = robustness champion.** Pick per objective;
do not claim one dominates.

## The corrected WR arithmetic (my v25 report was WRONG)

`decided = wins + losses` (BE excluded) and `total = wins + losses + BE`
(BE included) — verified at lines 2165-2166 of the v25 file. So `65W/40L/55BE`
would pass asserts 1 and 5 together. Requirement: `losses <= 0.667 * wins`.
At v26's 70 winners that means <= 46 losses vs 161 actual: convert 71% of all
losses into scratches without destroying winners.

## The measured frontier (why 60% is not reachable here)

24 exact bar-walks (12 shield rules x 2 trade sets) + 5 causal pre-entry
filters + the v24 1,668-combo search:

- Best WR anywhere: **39.53%** (`A0.25` on the v25 set) with `>=4R` = **4**
  => assert 3 fails by ONE runner.
- On the v26 set NO shield rule exceeds **28.51%**; `A0.5` gives 23.96% and
  `A1` 25.83% (early shields destroy winners: `A0.25` killed 42 of 59).
- `MID` alone (arm at the mid-cross, no fractal wait) = +1.66 pts and -6 runners.
- Best pre-entry selectivity measured: kills 42.1% of losers / 29.4% of winners
  (`retrace_impulse >= 1.0`, WR 36.73% at n=124). 60% at n>=150 needs 68%/6%.
- **Fee/risk tension (the real constraint):** a tighter stop makes MORE winners
  (51 -> 70) but CHEAPER ones ($5.51 -> $4.40), so net falls. WR is bought with
  money at ~0.55 net points per WR point on this data.

## Rejected with numbers (do NOT re-test)

- Structural invalidation cut (close below the LTF green floor): destroys 5
  winners, recovers 11.6R, total R **+3.4 -> -6.5** (v26) / **+16.5 -> +8.4** (v25).
- Bearish-FVG-over-entry filter: present in 64.7% of winners vs 72.5% of
  died-on-arrival losers => WR 36.0% at n=61.
- `sky_r_purple >= 3R` gate: WR 32.56% vs 32.28%, ymin 7 => assert 5 fails.
  (The alleged "3R line beyond the range top" is refuted: the 4H range top sat
  a median **7.78R** above LOSERS vs 6.59R above winners.)
- Round-trip fee floor at `_seek_setup` stage: wipes 2023 to 0 trades (165,862
  rejects). Streak-conditional skips DEADLOCK.
- All v25 dead ends still apply (`CTX_MODE="and"/quarter/sky10`, `CTX_TIER3`,
  `FLOW_GATE`, `STRUCTURAL_RESET`, `SHIELD_RULE="MID|BOS"/"NONE"`).

## Recovery

```bash
cd /home/user/TRADING-BOT && git fetch origin -q \
  && git reset --hard origin/arena/d2e74635-trading-bot
pip install --user --break-system-packages numpy pandas pytest
cd halal_spot && timeout 1750 python3 strategy_v26_ict_master.py > results/run_v26_log.txt 2>&1
```
The sandbox has been wiped 10+ times: commit and push immediately after any
measurement. Runs exit 1 by design (artifacts are written before the asserts).
