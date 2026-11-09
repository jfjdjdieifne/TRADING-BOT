# DEV RUN PLAN V1 — how `ict_recipe_v1` would be run on EURUSD 5m, decision month 2021-06

**Status: PLAN ONLY. Nothing in this file has been executed.** No data is loaded by this task, and
this document does not authorise a run: it describes what a run would look like so the owner can
authorise or refuse it explicitly.

---

## 1. Inputs

| item | value |
|---|---|
| instrument | EURUSD, 5m, **bid and ask** (both sides kept; cost comes from the spread) |
| file | `2021.csv.gz` — the only year file authorised, stored **outside** the repository |
| sha256 (recorded when downloaded, unchanged) | `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4` |
| rows | `105,120`, `2021-01-01T00:00:00Z` … `2021-12-31T23:55:00Z` |
| stream start | `2021-01-01` — the earliest bar the wrapper sees is 2021-01-01 |
| decisions | **`2021-06-01` … `2021-06-30` only** (`ENGINEERING_CHOICE` = the owner's next dev month, declared in `PREREGISTRATION_V1.md` §9A before any load) |
| bars after the decision month | read only as the *hindsight* stream for section B of each case, and never fed back into a decision |
| forbidden | 2022–2026 files, BTCUSDT, any other decision month, any second run of the same month |

**Why streaming from 2021-01-01 costs nothing.** The wrapper holds `WINDOW_BARS = 5,760` bars
(20 trading days). Everything older is dropped as it arrives. A decision on 2021-06-01 therefore
sees the same bounded window as a decision on 2021-12-01; memory does not depend on how long the
stream has been running. Starting at 2021-01-01 is a *convenience for the loader*, not a warm-up
requirement.

---

## 2. The exact command shape

```bash
PYTHONPATH=/home/user/TRADING-BOT/project/trading_project/src \
/usr/bin/python3 -m ict_recipe_v1.run_w0 \
  --bidask /tmp/hud_data/2021.csv.gz \
  --stream-from 2021-01-01 \
  --decide-from 2021-06-01 --decide-to 2021-07-01 \
  --hindsight-to 2021-08-01 \
  --window-bars 5760 \
  --variant sweep=D1 displacement=<declared> \
  --pip-size 0.0001 --spread-model dataset \
  --out /tmp/ict_recipe_v0/run01 \
  --sensitivity 2880,5760,11520 \
  --memory-cap-kb 1500000
```

Notes that matter:

- `--variant` values are **named source variants**, not preferences. `sweep=D1` is the owner's
  decision `D1` (sweep against the most recent confirmed swing). `displacement=<declared>` must be
  filled from an owner decision: the module refuses to choose a variant.
- `--spread-model dataset` uses the recorded `Spread*Pips` columns; the wrapper invents no
  commission (the dataset has none) and says so in every record.
- `--pip-size 0.0001` is the runner's own constant (`run_forex_intraday_v1.py:318`), carried
  unchanged.
- `--memory-cap-kb` aborts the run rather than letting the kernel do it, so a memory failure is a
  *reported* failure and not a dead process.
- `--sensitivity` produces **three labelled runs** (10 / 20 / 40 days) whose outputs are kept
  separate from the primary one. No sweep result may replace the primary.

---

## 3. Outputs (all outside the repository)

```text
/tmp/ict_recipe_v0/run01/
  MANIFEST.json          # command line, start/end UTC, sha256 of every file below,
                         # input sha256, window size, variants, code HEAD sha
  decisions.jsonl        # ONE line per decision; nothing kept in memory
  cases/CASE_<nnn>.md    # one file per plan, sections A/B/C/D
  cases/NON_PLAN_<nnn>.md# one per sampled non-plan (10, seeded), plus the 3 closest
  summary.json           # counts and distributions (below); no prose
  memory.csv             # RSS per 100 boundaries, vs the cap
  aborted.txt            # present ONLY if the run aborted, with the reason
```

Each `decisions.jsonl` line carries: `as_of`, `bar_index`, `window_first_bar`,
`bias{state, failure_reference_level, failure_ref_index}`, `range{low, high, equilibrium,
position, ratio}`, `untaken{side: [{level, formed_index, age_bars, distance_rank}]}`,
`sweep{side, answer, level, indices, gaps}`, `displacement{status, numbers, gaps}`,
`structure{state, breach_index}`, `zones[]` with their ranks, `selected_zone` or
`NO_SELECTION_STEP`, `decision_in_words`, `what_would_change`, `absent_concepts[]`,
`tags{}` mapping every number to `SOURCE_NUMBER` / `ENGINEERING_CHOICE` / `KNOWLEDGE_GAP`.

---

## 4. What is reported

**Counts first, always:** decisions; decisions with no zone; decisions with a zone and no untaken
target; plans opened; plans invalidated; plans still open at data end; censored; ambiguous
(`AMBIGUOUS_CENSORED`); `NO_SELECTION_STEP` by reason.

**Distributions, reported but never thresholded:**

- measured R:R for every plan (including any below 1), with numerator and denominator printed;
- stop distance in pips, with the pip source named;
- distance from entry to T1 and to T2 in pips and in `relative_range` units;
- `R` per plan (hindsight, section B only), the mean and median, the maximum drawdown in `R`, the
  longest negative-`R` streak;
- the three sensitivity sweeps, side by side, with **no** statement that one is better.

**Two things are printed with every number:** the denominator of any rank ("7th of 31 comparable
moves in this window") and the window first/last bar, so a reader can see exactly which bars the
number came from.

---

## 5. What counts as `NO_RESULT` (declared before the run, not after)

The dev month is reported as `NO_RESULT` — not as a finding, and never as a success or a failure —
if any one of the following holds:

1. **The run aborts**, for any reason (memory cap, exception, missing file). The `aborted.txt`
   reason is the result; the month is not described further.
2. **Any output is missing its hash** from `MANIFEST.json`, or a hash does not match the file on
   disk.
3. **The mechanical recomputation (section C) fails for any case.** A single case whose numbers
   cannot be re-derived by an independent call makes the month unreadable until the cause is
   known; the count of failures is printed and the month is `NO_RESULT`.
4. **The three sensitivity sweeps do not complete.** The primary run alone cannot be reported,
   because the reader could not see whether the declared window is doing the work.
5. **The decision window contains zero plan attempts of either kind** — i.e. every decision is
   `NO_SELECTION_STEP`. In that case the funnel counts (which step emptied first) are the result,
   and the month is `NO_RESULT` **by rule**, so that a dry month cannot later be presented as
   evidence of selectivity.

`NO_RESULT` is published, not hidden: it is the honest outcome whenever the machinery, and not
the market, is what was measured.

---

## 6. Pre-conditions that must hold before the command is ever run

1. Owner answers §7.1 of `ICT_RECIPE_SPEC_V1.md` (may the Layer-2/4 modules be imported), or the
   scope is reduced and the spec re-issued.
2. Owner answers §7.2 (clause (d)) — otherwise the streaming adaptation cannot be built.
3. `EXPECTED_W0.json` exists and the fifteen fixtures of `ICT_RECIPE_SPEC_V1.md` §6 pass **before**
   any market bar is read.
4. The input file's sha256 matches `38be0503…a6ab4` at run time, checked by the wrapper itself and
   written into `MANIFEST.json`.
5. The memory probe has been re-run on the final code and its peak is below `--memory-cap-kb` with
   margin; the probe's own output is attached to the run record.

## What this does NOT establish

- It does **not** authorise the run, and it does **not** predict what the month would show: zero
  plans and thirty plans are equally consistent with this document.
- It does **not** establish that the recipe is worth running: that question is answered by the
  cases, and the cases do not exist yet.
- It does **not** establish that 2021-06 is representative, clean of the owner's eyes, or
  comparable to 2021-03; it is one declared dev month.
- It does **not** make `R` a result about edge: `R` is a hindsight measurement of a *hypothetical*
  plan with no execution contract, and it is labelled as such everywhere it appears.
- It does **not** promise bounded memory for real data: that is measured on the fixture
  (`MEMORY_ANALYSIS_V0.md`) and must be re-measured on the final code before a run.
- It does **not** load, open or touch any market data.
