# HANDOFF v30 — «العقل المتداول الخارق» (The Cognitive Multi-State Brain)

Branch `arena/d2e74635-trading-bot` · engine `halal_spot/strategy_v30_ict_brain.py` ·
lab `halal_spot/lab_v30_brain.py` · report `halal_spot/results/REPORT_AR_v30.md` ·
official artefacts `results/{trades,summary,equity,asserts,anatomy,monthly,bull}_v30.*`.

## 1. What is shipped

`VIGILANCE_SCOPE="shield+be"` + `BE_STREAK_MODE="reset"` (lab combo **M1v_shbe_rst**),
everything else at the v27/v29 baseline (`ENTRY_ARM="seam"`, `FILL_MODE="blind"`,
`MANAGE_5M=False`, `ENTRY_BRAIN="sniper"`, `SHIELD_RULE_V30="MID+BOS"`,
`RISK_FLOOR_PCT=0.10`, `RISK_FLOOR_STAGE="both"`, `SIZING="allcash"`,
`SLIPPAGE_BPS=0.0`, `FEE=0.001`, `MIN_R=3.0`).

Official run (2021-01-01..2026-10-31, $200, live engine):

| metric | v30 shipped | v27 base | v25 |
|---|---|---|---|
| trades | **298** | 297 | 206 |
| W / BE / L | 44 / 109 / 145 | 70 / 66 / 161 | 51 / 48 / 107 |
| WR (W/(W+L)) | 23.28% | 30.30% | 32.28% |
| min winner | **3.00R** | 3.00R | 3.00R |
| ≥4R / maxR | 10 / 19.38R | 18 / 19.38R | 13 / 19.38R |
| totR | **+66.39** | +43.55 | — |
| net % ($ ) | **+71.75% ($343.50)** | +31.90% ($263.79) | +42.14% |
| PF | **2.14** | 1.26 | 1.43 |
| maxDD | **−9.52%** | −14.41% | −17.43% |
| streak (A4 / conservative) | 3 / **34** | 3 / 15 | 3 / — |
| yearly | {101, 79, 34, 35, 25, 24} | {82, 68, 16, 47, 47, 37} | — |
| asserts | **4/5** (A1 fails) | 4/5 (A1 fails) | 4/5 |

Asserts printed by `run_v30_log.txt`: `ASSERT1 FAILED :: 23.28%` · `ASSERT2 PASSED ::
3.00R` · `ASSERT3 PASSED :: >=4R:10 max:19.38R` · `ASSERT4 PASSED :: 3` ·
`ASSERT5 PASSED :: total:298 yearly:{101,79,34,35,25,24}` (exit 1 by design).

**Mechanism (this is the whole discovery):** arm the break-even stop **at entry**
under a *permanent vigilance* counter, but let the *entry throttle* keep reading the
forgiving counter. `tier3_be_armed_at_entry` 30 → 177, `exit_STOP_BLUE` 179 → 72,
`exit_SHIELD_BE` 0 → 83, mean loss −1.702R → **−0.933R**, loss totR −273.98 →
**−135.22**; wins fall 70 → 44 (avg 4.54 → 4.59R), ≥10R 6 → 3. Profit comes from
**cheaper losses**, not more wins. The 109 scratches cost −$0.48 in total (median
life = 1 bar) because the BE line is `entry×(1+2×COST)`.

## 2. The three modules — verdicts

* **Module 1 (vigilance)** — the only lever that paid. But *not* as briefed:
  `BE_STREAK_MODE="hold"` (never zero on a scratch) is better on paper
  (net +56.25%, PF 2.43, DD −4.83%, WR 42.86%, conservative streak **3**) yet
  **starves the book**: n=174, 2023/24/25 = 9/11/10 ⇒ **A5 fails**. Cause measured
  from the counters: `tier3_fill_needs_proof` 95→289, `reject_risk_below_one_fee`
  bars 272,575→396,324, `setup_drawn` 3,629→2,984 — **v25's DEADLOCK, verbatim**.
  Fix = separate the two jobs of the counter (`VIGILANCE_SCOPE`).
  Also measured: the displacement shield was **already permanent** in v25-v29
  (`rule = TIER3_RULE if tier3_at_entry else SHIELD_RULE` with no streak gate), and
  the `self.shield` flag is **inert** — `M1a_decay` and `M1v_shield` produced
  byte-identical books (208 trades, 48/63/97, totR 46.43) because `is_be` requires
  `R >= -0.05`.
* **Module 2 (dual CISD-belly entry) — REFUTED live.** Best +6.19% (`M2_dual_nc`),
  plain `M2_dual` +3.73% / PF 1.03 / DD −25.66% / WR 25.87%, wider absorption window
  −15.02%, tier-3 exemption −21.83% (**A4 fails: 8 straight losses**), combined with
  module 1 −6.12% (WR **12.77%**). The post-hoc 63.6% cohort (14W/8L on 28 setups)
  produced 127-198 live CISD fills at ~25%. Adverse selection again. The sacred law
  held everywhere: `sacred_law_seam_ok/sacred_law_cisd_ok` = 263/127, 259/130,
  304/198 ⇒ **zero premium buys**.
  Implementation note worth keeping: the violent arrival candle closes below the seam
  *and* below the YellowBox bottom, so `setup_box_died`/`setup_mitigated` delete the
  setup on the very bar the absorption state should start (first build armed **0**).
  The absorb state had to be moved **above** those vetoes, with `ABSORB_MAX_BARS`.
* **Module 3 (box floor + dollar-R)** — 3a at setup stage is a **starvation device**
  (0.30% → n=77 with 2023/2024 at **zero**; 0.40% → n=43) exactly as v22's 0.2%
  floor predicted; at fill stage only it is viable (`M1v_rst_f020`: n=287, totR
  **+86.18**, DD **−7.65%**, share(fee≥1R) **0.0%**, 4/5) but dies first under
  slippage. 3b **does** equalize dollar-1R (max 1R $7.81 → $0.84, IQR/max 0.170 →
  0.894, max 3.90% → 0.42% of equity) but costs net (+31.90 → +23.90%) and **breaks
  A4** (4 straight losses); with vigilance it gives the highest totR in the whole
  sweep (+94.94) at DD −7.65%.

## 3. Execution-cost stress (read before trusting any v30 number)

`SLIPPAGE_BPS` → `COST = FEE + bps/1e4`, substituted at every cash/BE-line site
(recomputed **inside** `run_backtest`; the first build computed it at import and the
stress arms came back byte-identical — do not repeat that). 0 bps is verified
bit-identical to the pre-patch engine (smoke 46 trades, 13/8/25, totR 15.46).

| arm | 0 bps | 5 bps | 10 bps |
|---|---|---|---|
| base | n=297 +31.90% PF 1.26 DD −14.41 ymin 16 | n=177 **+46.08%** PF 1.52 ymin 13 | n=138 +24.17% PF 1.32 DD −26.47 ymin **4** |
| shipped | n=298 **+71.75%** PF 2.14 DD −9.52 ymin 25 | n=216 +28.72% PF 1.46 ymin 17 | n=132 +26.60% PF 1.53 ymin **4** |
| shipped + floor 0.20% fill | n=287 +69.59% PF 2.07 DD −7.65 | — | n=104 +7.61% ymin **0** |

**At 5 bps the base beats the shipped arm.** The v30 edge is real *inside the
project's zero-slippage cost model* (the same model every v25-v29 number was measured
in) and shrinks fast outside it. At 10 bps A5 fails for everyone.

## 4. Frontier (A1 is dead)

A1 (WR ≥ 60%) failed in **38/38** live arms. Best readings: 47.62% @ n=71,
45.12% @ n=183 (A4+A5 fail), 42.86% @ n=174 (A5 fails), 30.30% @ n=297 (base),
23.28% @ n=298 (shipped). A1 needs `L ≤ 0.667·W`; the shipped arm would need ≤29
losses instead of 145. Every cohort above 60% in this data is lookahead
(`disp_mid` 73.53%, `disp_bos` 62.50%, `be_at_entry` 100%) or post-hoc and
non-reproducible live (CISD 63.6%). v28's bounded ceiling for "lock everything
inside its own life" was 31.78%.

## 5. Lab usage

```bash
python3 lab_v30_brain.py combos                          # 38 combos + their configs
python3 lab_v30_brain.py smoke base M1v_shbe_rst         # 6-month sanity (~40 s/arm)
python3 lab_v30_brain.py run <combo> ...                 # full book (~6-10 min/arm on 2 CPUs)
python3 lab_v30_brain.py diag M1v_shbe_rst               # crosstab vs the v27 book
python3 _m30.py all                                      # independent checks (no re-simulation)
V30_SWEEP=results/lab_v30_sweepX.csv python3 lab_v30_brain.py run ...   # parallel batches
```
Saved logs: `results/lab_v30_run{A..G}_log.txt`; unified table
`results/lab_v30_table.csv` (38 arms) + `lab_v30_sweep{A..G}.csv`.
Per-combo equity curves (`results/equity_v30_*.csv`, ~27 MB × 38) are **gitignored** —
regenerable; only the official `equity_v30.csv` is tracked.

## 6. Dead ends — do not retry

CISD/belly entry in any form (5 arms); absorption windows 3/6/12; CISD tier-3
exemption; box floor at setup stage (0.20/0.30/0.40); box floor 0.30 at fill stage;
dollar-R as a profit lever; `SHIELD_RULE_V30="MID"` (+20.39%), `"A0.5"` (+9.89%,
totR −15.15), `"MID|BOS"` alone (+39.57%, DD −15.47); `M1v_best`/`M13`/`all`
(n 81/71/118, ymin 0); vigilance + dual (WR 12.77%). Plus everything inherited from
v25-v29 (see `HANDOFF_V29.md`).

## 7. Ideas that remain untested

1. **Vigilance with a bounded scratch budget** — cap consecutive BE-at-entry
   scratches so 2023 (the only losing year, −$9.01) can breathe.
2. **`VIGILANCE_SCOPE="be_only"`** — BE-at-entry from vigilance while the shield
   *rule* stays `MID+BOS` (only 50 `shield_armed_disp` fires now).
3. **Vigilance + dollar-R at a higher `DOLLAR_R_PCT`** — totR +94.94 at DD −7.65%
   suggests the equalizer is under-sized, not wrong.
4. **Real slippage measurement** on BTCUSD spot before any live money; then re-run
   `SLIP5_champ` and consider shipping the base at 5 bps.

## 8. Sandbox recovery (15 wipes so far)

```bash
cd /home/user/TRADING-BOT && git fetch origin -q && \
  git reset --hard origin/arena/d2e74635-trading-bot
pip install --user --break-system-packages numpy pandas pytest
```
