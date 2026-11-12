# DIAGNOSIS V1 — what the saved 2021-06 outputs actually say

No engine was re-run on 2021-06 for this file. Every number below is recomputed from
`REPORT_2021_06/run_summary.json` (106 settled plans) with the formula printed beside it.

## a) The three statistics, recomputed

| statistic | REPORT_2021_06 | recomputed here | formula | verdict |
|---|---|---|---|---|
| total R | −85.588 | **−85.588** | `sum(R_i)` | correct |
| longest negative streak | 25 | **25** | longest run of consecutive `R_i < 0`, plans ordered by `exit_index` | correct |
| max drawdown in R | −8.050 | **−87.629** | `min_k ( C_k − max_{j<=k} C_j )`, `C_k = sum_{i<=k} R_i` | **WRONG in v1** |

The v1 function (`report_v1.py::drawdown`) was written to take a cumulative series but was called with
the **raw per-trade R list**, so `peak` tracked the largest single R instead of the running peak:

```python
def drawdown(series):            # called as drawdown(r_ordered)  <-- raw R, not cumsum
    peak, worst = 0.0, 0.0
    for value in series:
        peak = max(peak, value); worst = min(worst, value - peak)
```

On raw R that yields −8.05 (one −1.14 R trade measured against the best +R); on the cumulative series it
yields −87.629. The owner's suspicion was right, and the number that was wrong is the drawdown. The
other two were right. With 106 plans averaging −0.807 R, a −8 R drawdown was arithmetically impossible.

## b) The plans that settled on their own entry candle

**64 plans** (the fault table said 63; that table counted the *category*, this counts
`trigger_index == exit_index`). All of them carried one of two rules: `far side of fvg` or `sweep wick`.

| measure | value (pips) |
|---|---|
| stop distance, median | **1.0** |
| stop distance, min–max | 0.2 – 6.3 |
| half-spread at decision, median | **0.15** |

So the median stop was **1 pip** and the half-spread **0.15 pip**: the cost was ~15 % of the stop before
any movement, and a single 5m bar routinely spans 1 pip.

Classification **by counting**, no thresholds invented:

| class | count | how it is identified from the record |
|---|---|---|
| (i) the entry candle crossed the whole zone to the stop | 64 | `exit_index == trigger_index` and `exit_reason == stop_touched` |
| (ii) stop inside the normal range of that candle | 64 | the same 64, because the entry candle's own `[low, high]` contains the stop by construction when (i) holds |
| (iii) other | 0 | — |

(i) and (ii) are the same 64 events seen two ways, and that is the finding: the stop was not outside
the noise, it was inside one candle.

**What is the model's assumption and what is the market's behaviour.**
- Model assumption: *entry at the zone's near edge* and *stop at the zone's far edge*, and *the
  conservative stop-first settlement on the entry bar*. Those three are v1's rules; they create (i).
- Market behaviour: the 5m bar that touched the zone also traded 1 pip further. That is not a rule,
  it is what the bar did.
- Consequence: the 1-pip stop is a **consequence of measuring the zone on 5m**. A 15m FVG is roughly
  3× wider, so the same rule places the stop ~3× further away — which is exactly the experiment.

## c) Independent theses vs arming events (D4)

| measure | value |
|---|---|
| plans written (arming events) | **106** |
| distinct zone ids | **43** |
| distinct (zone, direction) theses | **43** |
| armings on the most-repeated thesis | **21** |
| theses armed more than once | **18** of 43 |

`VARIANT_LOG.md` said "96 distinct zones"; that figure is **wrong** — recomputing the zone id from the
saved plans gives 43. The correction matters: 106 armings are 43 opinions, re-stated 2.5 times each, so
v1's R distribution is not 106 independent observations.

## d) Stop distance vs the entry candle's range (distribution only)

| | pips |
|---|---|
| all 106 plans, min / median / max | 0.2 / 1.7 / 11.0 |
| the 64 same-bar plans, min / median / max | 0.2 / 1.0 / 6.3 |

No conclusion is drawn from this; the median stop is smaller than a typical 5m range, which is
consistent with (b) and is the reason for the experiment.

## e) Dealing range and order blocks — why the reuse rows said what they said

`REUSE_DECISIONS.md` row 4 rejected `zones/dealing_range.py::CausalDealingRangeEngine` (batch pandas,
328 lines) and `ict_engine/ranges.py::dealing_range_trace` (batch, ~20 ms per 5,760-bar window) because
neither is **incremental**, and a streaming wrapper calls the primitive once per bar.

**The reason is acceptable but not decisive.** 20 ms × 6,336 decisions ≈ 127 s, which a monthly run can
afford; rejecting the batch oracle on speed alone was weaker than the file implies. v2 keeps the local
incremental state (it must, to run on a 15m/1h frame the batch modules were never written for) and
records the weakness instead of hiding it: **a parity check between `DealingRangeState` and
`dealing_range_trace` on a random sample of decision times is still MISSING** (deferred, row H of
`DECLARED_CHOICES_V2.md`).

Order blocks in 2021-06: **21 created, 2 `VALID`**. Every one of the 21 passed the displacement test;
the rejections came from the prerequisite chain, and the chain is dominated by the **unmitigated**
prerequisite (`PREREQ_UNMITIGATED` is set `on: False` in v1, so a block that price has already returned
into fails) and by `FILTER_FAILED` on the mean-threshold requirement. v2 does **not** loosen the chain —
the counts say order blocks are rare at this granularity, and loosening a chain to manufacture zones is
the tuning the authorisation forbids.

## f) T2 — a concept question, not a cutoff question

Measured R:R to T2: median **6.45**, max **95.0**, on 96 of 106 plans.

By concept: T2 is *the second element of `rank_draws`*, and `rank_draws` was built to answer **one**
question — where is the nearest draw. The source says "all I need to know is where's the next likely
draw on liquidity" (singular; `draw_on_liquidity.md`, `U…`, window recorded in the card). Nothing in the
corpus describes a *second* objective, and a "target" 95 R away is the far end of the same ranking, not
a second plan. **T2 as built is not a meaningful second target**: it is the next pool in a list, and on
a 1-pip stop almost any pool is many R away. v2 keeps T2, reports it separately, and **settles R on T1
only** (row E).

## g) `ENGINEERING_HYPOTHESIS` inside build_v1

| where | what it labels | mapped to | action in v2 |
|---|---|---|---|
| `stream_v1.py:465` `DealingRangeState.DEFINITION_ID = "ENGINEERING_HYPOTHESIS_LATEST_ALTERNATING_CONFIRMED_SWINGS"` | the choice of *which two swings* define a dealing range | **KNOWLEDGE_GAP** — no card names a swing-pair definition | renamed `KNOWLEDGE_GAP_DEALING_RANGE_DEFINITION`; the tag `ENGINEERING_HYPOTHESIS` is not used anywhere in v2 |
| `REUSE_DECISIONS.md` rows 4 and 9 (prose) | the same definition, quoted back | KNOWLEDGE_GAP | — |

That is the **only** executable use. The owner's note ("needs owner approval") was not addressed in v1;
this file records the omission rather than retro-fitting an approval.

## h) What the sources say about frames — quoted or marked

| question | finding |
|---|---|
| (1) timeframe where the setup/zone is identified vs timeframe where entry is refined | **KNOWLEDGE_GAP.** The cards mention a frame only when describing where a pool is *visible*: "trades up to a buy side liquidity pool shown on the 15-minute timeframe" (`fair_value_gap.md` / `buy_side_liquidity.md`, `[U0044]`, `ICT-Mentorship-2023-Market-Review-June-24-2023-001.json`, window `W0090`). No card states a two-frame procedure. |
| (2) where the stop is placed | "this is where our stop loss would be which would be below the mean threshold" (`stop_loss.md`, `[U0107]`, `…Framing-Low-Risk-Trade-Setups-001.json`, `W0233`); "that down closed candle I want to have my stop loss below that low" (same card). So: stop beyond a **structural** level, never a pip count. |
| (3) how targets are chosen | "all I need to know is where's the next likely draw on liquidity so I'm stripping the market down" (`draw_on_liquidity.md`); "those old lows or highs previous weekly high or low as a draw on liquidity" (same card). One draw, chosen by liquidity, not by R:R. |

**Contradiction recorded, experiment still run:** the source's stop is *below the mean threshold of the
block* — i.e. inside the zone, not beyond its far edge. v1 and v2 both use the **far edge**. That is a
departure from the quoted sentence and is recorded here as `KNOWLEDGE_GAP: STOP_LEVEL_WITHIN_ZONE`
for a later authorisation; changing it now would be a second change on top of the frame change.

## What this does NOT establish

- It does not establish that the frame change fixes anything; (b) says the stop was 1 pip, not that a
  wider stop earns more.
- It does not establish that the drawdown formula is the only defect: it establishes that one reported
  number was arithmetically inconsistent with two others, and names the function.
- The classification in (b) is by counting record fields, not by looking at charts; the 64 are facts
  about the record, and "the bar crossed the zone" is an inference from those facts.
