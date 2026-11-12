# Real-data causal rerun — Feb 2025 (dev Jan, eval Feb)

**Results only. No source/test file was modified. No parameter was tuned.**
Runner commit: `4098bb4f9280c4d90b146fc4c718d9a021a1762e`
(branch `arena/e6974afe-trading-bot`).

## ⚠️ NOT out-of-sample

**February 2025 was already viewed before the fixes** (it is the period
analyzed in reports 101/102/103). This rerun therefore reproduces a
previously inspected window; it is **NOT out-of-sample** and establishes
nothing about generalization or profitability. April and May were NOT run
in this round.

## Data provenance (verified)

- Cloned OUTSIDE the repo: `git clone https://github.com/mailztoganesh-civil/forex-data /tmp/forex-data`
- Pinned: `git fetch --depth 1 origin 56d5f04fd90b29414a70147471309f1db326aa1c && git checkout FETCH_HEAD`
  → HEAD `56d5f04fd90b29414a70147471309f1db326aa1c`.
- **sha256(data/EURUSD/5m_bidask/2025.csv.gz) =**
  `1fa2dca207e3a8a1de37bfcd7653b15ebcffb933c05b4d4e3a4831aaa84d9647`
  — **matches** the hash recorded in reports 101/103 and report 99.
- No raw data was copied into the repo or committed.
- venv (outside repo): pandas==2.2.3, numpy==1.26.4, tzdata, pytest==8.3.5.

## Commands executed (all exit code 0)

Runner: `project/trading_project/docs/research/huddleston_study/run_forex_intraday_v1.py`
Python: `/home/user/.venv/bin/python`. Current argparse used
(`--phase`, `--bidask-dir`, `--from`, `--to`, `--out-dir`, `--model`,
`--gate v1|b0`, `--fill-mode next_open|bar_close`). The old report-101 flags
(`--fill-convention`, `v1-legacy`) do NOT exist in this commit and were not used.

```
# (a) dev — Jan 2025 (produces the frozen model used by eval)
python run_forex_intraday_v1.py --bidask-dir /tmp/forex-data/data/EURUSD/5m_bidask \
  --phase dev --from 2025-01-01 --to 2025-02-01 --gate v1 --fill-mode next_open \
  --model /tmp/rerun_out/dev/dev_model.json --out-dir /tmp/rerun_out/dev
# exit 0 (425.3 s)

# (b) eval — Feb 2025, gate v1, causal next_open
python run_forex_intraday_v1.py --bidask-dir /tmp/forex-data/data/EURUSD/5m_bidask \
  --phase eval --from 2025-02-01 --to 2025-03-01 --gate v1 --fill-mode next_open \
  --model /tmp/rerun_out/dev/dev_model.json --out-dir /tmp/rerun_out/eval_v1_next_open
# exit 0 (300.7 s)

# (c) eval — Feb 2025, gate b0, causal next_open
python run_forex_intraday_v1.py --bidask-dir /tmp/forex-data/data/EURUSD/5m_bidask \
  --phase eval --from 2025-02-01 --to 2025-03-01 --gate b0 --fill-mode next_open \
  --model /tmp/rerun_out/dev/dev_model.json --out-dir /tmp/rerun_out/eval_b0_next_open
# exit 0 (304.1 s)

# (d) eval — Feb 2025, gate v1, bar_close (NON-CAUSAL comparison only)
python run_forex_intraday_v1.py --bidask-dir /tmp/forex-data/data/EURUSD/5m_bidask \
  --phase eval --from 2025-02-01 --to 2025-03-01 --gate v1 --fill-mode bar_close \
  --model /tmp/rerun_out/dev/dev_model.json --out-dir /tmp/rerun_out/eval_v1_bar_close
# exit 0 (307.6 s)
```

No run crashed; no traceback occurred; no code was patched.

## Numbers (as produced)

Open-market 5m rows: Jan **6336**, Feb **5760** (placeholders dropped by the
declared hygiene rule).

### (a) dev — Jan 2025
- decisions 528, strict_pref 402, gate_pass 19, plans_created 3, no_plan 508, cases_total 514
- outcomes: no-entry 3 (all 3 plans INVALIDATED before entry)
- episodes_total 528, episodes_fitted 468, censored/excluded 60
- trained_through **2025-01-31 10:00:00+00:00** (matches report 101 line 279)

### (b) eval v1 next_open (causal)
- decisions 480, strict_pref 384, gate_pass 43, plans_created 3, no_plan 433, cases_total 439
- outcomes: **win 2, no-entry 1**; ambiguous/censored **0**; losses 0; missed 0; open 0
- final_states: HYPOTHETICAL_ENTRY_MET 2, INVALIDATED 1
- Plan 0001 (reversal up, opened 2025-02-04 11:00, DEC-…-0037): entry 15:00 → fill 15:05 @ 1.03694, exit 2025-02-05 03:00 @ 1.03816 → **+12.2 pips**, amb=False
- Plan 0002 (continuation up, opened 2025-02-05 04:00): entry 08:00 → fill 08:05 @ 1.04045, exit 21:00 @ 1.04045 → **0.0 pips**, amb=False
- Plan 0003 (continuation up, opened 2025-02-05 22:00): INVALIDATED before entry → no-entry
- entered pips total **12.2**

### (c) eval b0 next_open (causal)
- decisions 480, strict_pref 384, gate_pass 384, plans_created 4, no_plan 96, cases_total 104
- outcomes: **win 2, no-entry 2**; ambiguous/censored **0**; losses 0; missed 0; open 0
- final_states: HYPOTHETICAL_ENTRY_MET 2, INVALIDATED 2
- Plans 0001/0002 identical to (b); Plan 0003 (2025-02-05 22:00) and Plan 0004 (2025-02-06 10:00) both INVALIDATED before entry → no-entry
- entered pips total **12.2**

### (d) eval v1 bar_close (NON-CAUSAL comparison)
- decisions 480, strict_pref 384, gate_pass 43, plans_created 3, no_plan 433, cases_total 439
- outcomes: **win 2, no-entry 1**; ambiguous/censored **0**
- Plan 0001: fill 15:00 @ 1.03694, exit 03:00 @ 1.03816 → **+12.2 pips**
- Plan 0002: fill 08:00 @ 1.04044, exit 21:00 @ 1.04045 → **+0.1 pips**
- Plan 0003: no-entry
- entered pips total **12.3**
- limitations text (verbatim): "NON-CAUSAL bar_close comparison fills at the CLOSE of the event bar itself, at ask/bid of the actual quotes; commission NOT provided by this dataset (never invented); slippage not modeled"

For (b)/(c) the limitations text (verbatim): "causal next_open hypothetical fills: both legs at the OPEN of the next 5m bar strictly after their events, at ask/bid of the actual quotes; commission NOT provided by this dataset (never invented); slippage not modeled".

## Comparison vs reports 101/102/103 (February claims)

### Matches (rerun == report)
- Report 101 line 319 / 102 line 44: `5760` rows → **5760** ✓
- Report 101 lines 323–326 / 102 lines 56–69: decisions 480, strict 384;
  V1-fixed `43 pass / 3 plans / 433 no_plan / 439 cases` → **exact match** ✓
- Report 101 line 334 / 102 line 70 / 103 line 254: V1 `3 plans -> 2 win + 1 invalidated` → **2 win + 1 no-entry (invalidated before entry)** ✓
- Report 101 line 348 / 102 line 64: B0 `4 plans (2 win + 2 invalidated)` and `2 win 2 no-entry` → **match** ✓
- Report 101 lines 366–367: `B0 next-open: 2 win 2 no-entry`, `V1-fixed next-open: 2 win 1 no-entry` → **match** ✓
- Report 102 line 150 / 103 line 252: `341 hold via FVG` → 384 strict − 43 pass = **341** ✓
- Report 103 line 253: `40 gate pass but no plan` → 43 − 3 = **40** ✓
- Report 103 lines 77–80, 104–105: Plan 0001 `DEC-…-0037`, as_of 2025-02-04 11:00, reference `1.03506`, reversal up → **match** (verified in cases) ✓
- Report 103 line 200: `(1.03816-1.03694)*10000=12.2` → **+12.2** ✓
- Report 103 lines 346–347 (فبراير مصحح): `entered 2 wins 2 losses 0 no-entry 1 open 0 ambiguous 0`, `pips close 12.2+0.1=12.3` → **match** (counts from b/c; close pips from d) ✓
- Report 101 line 279: `trained_through=2025-01-31 10:00:00+00:00` → **match** ✓

### Discrepancies (rerun != report)
1. **Report 101 line 324 — B0 cases_total.** Report: `B0 480 384 384 4 96 5`
   (cases_total **5**). Rerun (c): cases_total **104** (= 96 no-plan + 4 plan-opened + 4 plan).
   The V1 cases_total (439) matches; only the B0 cases_total differs.
2. **Report 101 lines 357–358 — Plan 2 pips under the close convention.**
   Report: `Plan 2 … => 0.0 pips`, `Total 12.2 pips`. Rerun (d) bar_close:
   Plan 2 = **0.1 pips**, total **12.3**. The 0.0/12.2 values equal the
   **next_open** result (b), not bar_close. Reports 102 (line 77) and 103
   (line 347) give the close total as **12.3**, agreeing with rerun (d);
   report 101's close-section total (12.2) differs by 0.1 pip.
3. **Report 101 line 356 — fill time label.** Report lists `fill 15:05`
   inside the close-convention pips block; the actual bar_close fill (d) is
   **15:00** (15:05 is the next_open fill time). Labeling inconsistency.
4. **V1-legacy not reproducible.** Reports 101 (line 325), 102 (lines 66–67),
   103 (lines 131–132) cite a `V1-legacy` gate (30 pass / 1 plan). The current
   runner exposes only `--gate v1|b0`; there is no legacy gate, so those
   numbers were **not run** and cannot be reproduced with this commit's flags.

### Note on the previously flagged 102-vs-103 discrepancy
The verification appendix (commit e06e22c) states a 102-vs-103 trade-count
discrepancy remains unresolved. In the February sections read this round,
102 and 103 **agree** on V1-fixed (3 plans, 2 win, 1 invalidated/no-entry) and
both match the rerun; the appendix's discrepancy was not independently
localized beyond what it states. Reports 101–103 were **not edited**.

## What was NOT run / NOT verified
- April 2025 and May 2025: **not run** (by instruction).
- V1-legacy gate: **not run** (flag absent in this commit).
- No parameter tuning; no source/test modification.
- This is a reproduction of an already-viewed window, **not** an
  out-of-sample test; no profitability or readiness claim is made.
