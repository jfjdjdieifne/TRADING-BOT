# SUMMARY `V0` — one dev month (March 2021), one attempt, aborted by the operating system

**Status: `RUN_ABORTED_OUT_OF_MEMORY` — `plans = 0`, `decisions = 0`, `cases = 0`.**
Nothing in this folder is a trading result. `selection_quality = NOT_ESTABLISHED`.

---

## 1. What was authorised, and what was done

Authorised: one run of the existing engine on EURUSD 5m, history bars from 2021-01-01,
decisions and plans only for 2021-03-01 .. 2021-03-31, default configuration, no tuning.

Done: one attempt with those exact parameters. The process was killed by the kernel's OOM
killer during the warm-up, **before the first decision instant was reached**. No second attempt
was made (the task forbids retrying a crashed run with different settings, and repeating the
identical attempt would hit the identical limit).

### The evidence, verbatim

```text
kernel log:
  oom-kill:constraint=CONSTRAINT_NONE,...global_oom,task=python,pid=2546
  Out of memory: Killed process 2546 (python)
      total-vm:4059304kB, anon-rss:3871560kB, UID:1001

process monitor, last sample before death:
  pid 2546  elapsed 12:59  cpu-time 12:48  99.4% CPU  RSS 3,870,276 kB
  machine total memory 3,939 MB, available 84 MB

raw output directory:
  /tmp/dev_month_v0/raw/run.log   264 bytes, created 18:35:01 UTC
  cases_v1.jsonl                  not written
  summary_v1.json                 not written
```

`run.log` in full:

```text
== loaded 2021-01-01 -> 2021-04-01: open-market 5m rows 18177; decisions 2021-03-01 -> 2021-04-01
RuntimeWarning: Mean of empty slice  (numpy nanfunctions, raised inside the engine)
```

## 2. The exact command (the one attempt)

```bash
PYTHONPATH=/home/user/TRADING-BOT/project/trading_project/src \
PYTHONDONTWRITEBYTECODE=1 \
/tmp/devenv/bin/python run_dev_month_v0.py \
  --bidask-dir /tmp/hud_data \
  --history-from 2021-01-01 --decide-from 2021-03-01 --decide-to 2021-04-01 \
  --to 2021-04-01 \
  --out-dir /tmp/dev_month_v0/raw \
  --gate v1 --fill-mode next_open
```

Default configuration, unchanged: `--gate v1`, `--fill-mode next_open`, `TASK_SCALE=1h`,
`READINGS_SCALE=15m`, `K=5`, `HORIZON_BARS=12`. No threshold was lowered, no warm-up was
shortened, no window was substituted, no code in `src/`, `tests/`, `b1_candles` or `c1_catalog`
was touched.

## 3. Data record (outside the repository)

| item | value |
|---|---|
| source repository | `https://github.com/mailztoganesh-civil/forex-data` |
| commit | `56d5f04fd90b29414a70147471309f1db326aa1c` (`Futures 1m 2026-11-03`, 2026-11-03T03:41:17Z) |
| path | `data/EURUSD/5m_bidask/2021.csv.gz` |
| git blob sha (content-addressed) | `aa30247382e96bde6e3fbfa8cf94444dbdf17ec2` — reproduced locally by `git hash-object`, byte-exact |
| file sha256 | `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4` |
| size | `3,175,925` bytes |
| rows | `105,120` raw rows, `2021-01-01T00:00:00Z` .. `2021-12-31T23:55:00Z` |
| columns | `Datetime, BidOpen, BidHigh, BidLow, BidClose, BidVolume, AskOpen, AskHigh, AskLow, AskClose, AskVolume, SpreadOpen, SpreadOpenPips, SpreadHigh, SpreadHighPips, SpreadLow, SpreadLowPips, SpreadClose, SpreadClosePips` |
| rows after the loader's declared market-closed rule | `18,177` open-market 5m rows in 2021-01-01 .. 2021-04-01 |
| stored at | `/tmp/hud_data/2021.csv.gz` — **outside the repository; never committed** |

Only the 2021 file was downloaded. No other year was opened, read or fetched.

## 4. Required metrics — every one of them was **not produced**

| metric | value |
|---|---|
| plan count | **0** (no plan object exists) |
| entries (hypothetical entry met) | **0** |
| invalidations | **0** |
| ambiguous (`AMBIGUOUS_CENSORED`) | **0** |
| censored | **0** |
| `R` per plan | **not produced** |
| mean / median `R` | **not produced** |
| max drawdown in `R` | **not produced** |
| longest negative-`R` streak | **not produced** |
| reward:risk distribution | **not produced** |
| stop-distance distribution (pips) | **not produced** |
| D-locator table across cases | **no cases exist** |
| top reasons decisions did not become plans (counts) | **not produced** — `no-plan` records = 0 |

These zeros are **absence of output**, not measurements of zero. A run that produced no plan
says nothing about how often the engine would produce one.

## 5. Where the attempt stopped, and why (mechanically)

The warm-up segment (2021-01-01 .. 2021-03-01, ≈ 1,000 hourly decision boundaries) is the
expensive part: at **every** boundary the dev phase extracts an episode and fits the model, and
the monitoring loop advances the analysis engine, which retains a record per boundary plus its
recomputation payloads and revisions. Resident memory grew monotonically from ≈ 3.1 GB at 9:40
elapsed to 3.87 GB at 12:59 on a 3.94 GB machine, and the kernel killed the process.

This is a property of the **dev-phase design at this length**, not of a parameter that could be
retuned: the same growth would occur with any gate, fill mode or decision window, because the
warm-up is what fills the memory. The honest fix is either a machine with more memory, a shorter
warm-up (which the authorisation forbids changing), or an engine-level change to bound retained
history — and engine-level change is out of scope for this task and forbidden by the `D3`
clause (d) that is not even signed.

## 6. Ranked list of "what is missing for the engine to understand and apply the idea"

This list is derived from **reading the code on HEAD** (`ICT_CAPABILITY_AUDIT_V0.md`), not from
the aborted run, because the run produced nothing to grade. It is ordered by how much each gap
blocks the question "read the chart at `t`, choose the zone that matters, say what would make it
wrong". **No case ids are attached, because no case exists** — substituting invented ids would
be worse than an empty column.

| rank | missing capability | evidence (file :: function) | blocked question |
|---|---|---|---|
| 1 | **dealing range** | absent from the package (grep) | "where does price sit in the range" cannot be answered at all |
| 2 | **equilibrium / premium / discount** | absent (grep) | the single most-cited positioning idea has no number |
| 3 | **buy-side / sell-side liquidity, equal highs/lows** | absent in the executed path; `engine_v1` has only an id returning `UNDEFINED` | no pool, so no reason to expect price to reach anywhere |
| 4 | **draw on liquidity** | absent (grep) | the target side of a plan has no liquidity referent |
| 5 | **sweep** | coded and closed in `engine_v1/c1_catalog/liquidity_sweep.py :: sweep_at`, **not imported by this runner** | the trigger most sources describe is unavailable to the run |
| 6 | **displacement** | coded and closed in `engine_v1/c1_catalog/displacement.py :: displacement_at`, **not imported** | same as 5, for the "which move is real" question |
| 7 | **order-block detector** | `study_links.py :: OBLikeCandidate` is a record type only; no detector | zones can be stored but never computed into the candidate set |
| 8 | **structure shift / break detector** | `csm.py` has a `broken` status and `ShiftWatch` crossings; no BOS/CHoCH computation | "structure changed" is bookkeeping, not an event with a level |
| 9 | **selection among candidate zones** | `expert_selection.apply_expert_preferences` exists but receives points/legs only | "choose 1 of N zones" is unimplemented, as designed in `PAIRWISE_SELECTION_DESIGN_V1.md` |
| 10 | **session windows** | `SessionClockConvention` exists but the run passes `None` | time-of-day context is off |
| 11 | **bounded memory in the dev phase** | measured: 3.87 GB at ≈1,000 warm-up boundaries | a one-month run cannot be evaluated on a 4 GB machine at all |

## 7. What this changes about the plan going forward

Nothing about the design, and everything about sequencing: the next attempt at this dev month
must either run on a machine with materially more memory, or the warm-up length must be
re-authorised, or the engine's retention must be bounded under a `PATCH ONLY` task. None of
those is a tuning decision, and none of them may be made by quietly shortening the window.

## What this does NOT establish

- It establishes **no** result: no plan, no `R`, no drawdown, no streak, no reward:risk, no
  stop distance, no gate-rejection distribution. Every metric above is absent, not zero.
- It establishes **no** evidence of edge, and nothing here is a blind result.
- It does **not** show that March 2021 is clean: March 2021 was loaded as the decision window
  and is now **partly consumed as a dev month**, so it can never be used as an out-of-sample
  window. This holds even though the run produced no decision.
- It is **one month, one attempt, one run** — and that attempt did not complete.
- It does **not** show the engine produces few plans, or many; the count is unknown, not zero.
- It does **not** show the memory limit is inherent to the engine's design; it shows the limit
  was hit at this window length on this machine.
- It does **not** modify, patch or re-tune anything: `src/`, `tests/`, `b1_candles`,
  `c1_catalog` and every pre-existing document are byte-identical to `fd43dc29`.
