# How to get the most out of this brain

> **STATUS 2026-09-04: ALL SIX STEPS ARE DONE.** Results in
> `backtest/findings.md` sections 3-7. Ledger n = 128, holdout still SEALED.
>
> **One thing survives: the 08:30-11:00 killzone.** Everything else tested has
> produced an absence - the FVG premise is contradicted, the on-close macro is
> too weak, and no entry gate earns its place.
>
> | step | outcome | where |
> |---|---|---|
> | 1 matched nulls | built (`nulls.py`); found the killzone result and killed two confounds | §3, DECISIONS 24 |
> | 2 FVG standalone | **premise contradicted** - gaps fill LESS than matched moves, z to -59.9 | §4 |
> | 3 on-close macro | sign right, ~93rd pctile, **too weak** at \|t\|>3.0 | §5 |
> | 4 the 3.0 hurdle | adopted, applied retroactively | DECISIONS 24 |
> | 5 gate value | **no gate earns its place**; displacement threw away better trades | §7 |
> | 6 sparsity fix | fixed, and it **sharpened the null** - more trades, worse results | §6 |
>
> Also found and fixed: `n` had been inflated 86 -> 213 by a broken dedup key,
> and the entry pipeline was asking ep29's discount gate at a moment he never
> asks it. Both are written up in `findings.md`.
>
> **What to do next is no longer in this file** - the six moves are spent. See
> "Where this leaves it" at the bottom.

Written 2026-09-03 after the first null result, with outside research.
**Reasoned tier - no script writes this.** Sources marked `[OUTSIDE]`; the
quarantine rule in `study/CONTEXT.md` still holds - none of this is backfilled
into an episode page, because he did not say it.

---

## The reframe, in one sentence

**Stop testing the corpus as a strategy. Test it as ~50 falsifiable conditional
claims, each against a properly matched null.**

The first run produced one composite number (-0.076R over 148 trades). That is
one bit of information from 41 episodes of material. The same data can yield
fifty, because the corpus's real asset is not the assembled strategy - **it is a
large set of specific, timestamped, falsifiable statements about intraday index
futures, most of which nobody has ever tested properly.**

That is rare. Strategies are cheap. Well-specified hypotheses are not.

---

## 1. THE NULL MODEL IS WRONG. Fix this before anything else.

`run_vetoes.py` compares each veto against **random days**. That is the wrong
control for a model made almost entirely of clock rules.

`[OUTSIDE]` Intraday volatility and volume follow a well-documented **U-shape**:
high at the open, a minimum around lunch, rising into the close. Time-of-day
effects in the opening period largely dissipate **within 30 minutes**.

**So a rule that says "trade 08:30-11:00 and avoid noon-13:00" will look good
against a random-day null even if it carries no information at all** - it is
selecting high-volatility hours and rejecting the daily minimum. His lunch veto
(ep05 [10:04]) and his killzone (ep02 [42:40]) may be re-describing the U-shape.

**The fix:** every null must be **time-matched, and volatility-matched**.
Compare a rule's outcome against other days *at the same clock time* and in the
same volatility regime. Anything that survives that is information; anything
that does not was diurnal seasonality wearing his vocabulary.

**This is the highest-value single change in the whole workspace.** Without it,
every future result is uninterpretable in the same way the vetoes were.

## 2. Test the load-bearing primitive ALONE - and the literature predicts we lose

`study/_refinements.md`: **FVG/imbalance appears in 36 of 41 episodes.** It is
the corpus's centre of gravity, and it has never been tested on its own here -
only inside a seven-gate pipeline where its contribution is unrecoverable.

**The experiment:** over 15.7 years of NQ, for every fair value gap by
ep02 [17:53]'s definition - does price return to it, how often, how fast, and
**what happens next**?

`[OUTSIDE]` And the prior is not favourable. Rigorous work on gaps finds they
**more often CONTINUE in their direction than fill**, with one source calling
universal gap-fill a **myth**. Separately, the three-candle FVG is a **charting
heuristic with no peer-reviewed test** - it should not be confused with the
genuine order-flow imbalance literature, where signed order imbalance really does
move price.

**Why this is the best experiment available:** it is one afternoon of work, it
needs no strategy, no stops, no targets, and it tests the single assumption
36 of 41 episodes rest on. If NQ shows continuation rather than fill, a large
part of the model's premise is wrong - and knowing *that* is worth more than
another composite P&L. If it shows fill at a rate above the time-matched base,
we have found the corpus's one real edge and everything else can be built on it.

**Run the same test on order blocks and liquidity sweeps.** Three primitives,
three answers, no strategy required.

## 3. Chase the three places the corpus overlaps PUBLISHED anomalies

Prior probability matters. Where a documented effect already exists, a rule
describing it starts with a real chance of being true, instead of needing to beat
the multiple-testing hurdle from scratch.

| his rule | published effect `[OUTSIDE]` |
|---|---|
| **15:00-16:00 on-close macro** - ep32 [11:32], ep05 [26:53] | **Market intraday momentum**: across 60+ futures, 1974-2020, the last-30-minute return is positively predicted by the return over the rest of the day (Journal of Financial Economics, 2021) |
| **Midnight open anchors the daily range** - ep11 [07:44] | **The overnight drift** - a documented overnight return pattern (NY Fed Staff Report 917) |
| **No entries noon-13:00** - ep05 [10:04] | The documented **lunch minimum** in US index intraday activity |

**The first row is the strongest lead in this entire document.** He independently
describes, in ep32 and ep05, a window where a peer-reviewed cross-asset anomaly
lives. That is the one place where his teaching and the literature can
corroborate each other - and it is on the **last 30 minutes**, which the current
pipeline does not trade at all, because the killzone stops at 11:00.

**Test it directly and separately from everything else.**

## 4. Apply a real significance hurdle, and use the number we already have

`[OUTSIDE]` Harvey, Liu and Zhu documented **at least 316 factors** tested in
the search for cross-sectional return patterns, and concluded that a new factor
should clear a **t-statistic of 3.0 rather than the conventional 2.0**. Bailey
and Lopez de Prado's **deflated Sharpe ratio** adjusts the threshold explicitly
for the number of trials, plus skew and kurtosis. Industry practice is cruder and
points the same way: **discount a backtested Sharpe by ~50%**.

**We already have the input almost nobody else has: `ledger.md` knows `n`.**
That is the whole reason section 17 insisted the count be a file.

**So: adopt |z| > 3.0 as the bar, and deflate by the ledger count.** Retroactively
this is already decisive - the vetoes' best was +2.6 at n=36, and the setups'
best was the top of 25 configurations at n=139. **Neither was ever close.**
Nothing gets called a finding again below 3.0.

## 5. Mine what the model REJECTS - the output nobody else produces

ep24 [17:41]: a setup that never formed `is the proof, the evidence that the
model has validity`. The funnel already counts rejections per gate. **The step
not yet taken is asking what the rejected candidates went on to do.**

"G5 rejected 226 setups; those went on to lose 71% of the time" is a real
measurement of a filter. "G6 rejected 0 of 396" - which is what the order-block
gate actually did - is a filter that does not exist. **We found one such gate
already; there are probably others.** This is cheap and it is the most direct
test of his central claim about refusal.

## 6. Fix the sparsity - separate the gap timeframe from the structure timeframe

148 trades in 12 years is **~12 a year**. He trades most days. The pipeline is
therefore testing a narrow sliver of his behaviour, and the cause is known:
structure and gap are read on the same chart.

He does not do that. **ep05 [07:06] and ep12 [29:00]: the 15-minute is the
bellwether. ep06 [26:35]: the 1-minute is for entries. ep11/ep12: the cascade
walks 15 -> 5 -> 1.** Add `fvg_tf` separate from `struct_tf` and the sample
should grow by roughly an order of magnitude - which is the difference between
"no edge detected" and "no edge".

---

## The order to do these in

| # | move | cost | why now |
|---|---|---|---|
| ~~**1**~~ | ~~Time- and volatility-matched nulls~~ | **DONE** | Found the killzone result and killed two confounds. Section 24 |
| ~~2~~ | ~~FVG fill vs continuation~~ **DONE - premise contradicted** | - | Tests what 36 of 41 episodes rest on; literature predicts we lose, which makes it decisive either way |
| ~~3~~ | ~~15:00-16:00 vs intraday momentum~~ **DONE - too weak to use** | - | The only place his corpus meets a peer-reviewed anomaly |
| ~~4~~ | z>3.0 hurdle + deflate by ledger n **DONE - DECISIONS 24** | - | > 3.0` + deflate by ledger `n` | an hour | Makes every past and future number honest |
| ~~5~~ | ~~What the rejected candidates did~~ **DONE - no gate earns its place** | - | ep24's own claim, and it already found a dead gate |
| ~~6~~ | `fvg_tf` separate from `struct_tf` | a day | Turns 12 trades a year into a testable sample |

**Money management (ep41's ladder) moves to the end**, not the beginning. It
needs a sequence of real trades; without one it is a Monte Carlo about sizing
arithmetic in general, which teaches us nothing about him.

**The holdout stays sealed through all six.** Nothing above touches it.

---

## Where this leaves it - written 2026-09-04, after all six

**The six moves are spent, and the answer they produced is mostly negative.**
That is a result, not a failure - it is the thing the 41 episodes were good for.

**What survives:** the **08:30-11:00 killzone** (§3), which beat every
same-length control of the same sessions on both opportunity and efficiency. It
is a percentile, not a z, and it is `dev` only.

**What does not:** the fair value gap's central claim (§4), the on-close macro at
a usable strength (§5), and every entry gate tested (§7). The displacement gate
appears actively harmful. Two of the gold standard's three elements - order block
and OTE - separate nothing at all.

### The three honest options from here

1. **Take the killzone to `reserve`.** It is the only candidate. One look, then
   the holdout. If it survives both, the defensible claim is narrow and real:
   *NQ's 08:30-11:00 is measurably the cleanest directional window of the day,
   and ICT identified it.* That is worth having and it is not nothing.
2. **Test the primitives that have not been isolated yet** - order blocks and
   liquidity sweeps, the same way §4 did the FVG. The FVG result predicts they
   will also come back negative, which makes them cheap and decisive.
3. **Stop.** The corpus has been tested at every level it offers: the clock, the
   primitives, the gates, the composite. **Continuing to search this space is
   what section 4 warns about** - at n = 128, more configurations will eventually
   produce a winner, and it will be noise.

**Option 3 deserves more weight than it is usually given.** The value already
extracted is a defensible answer to a question thousands of people argue about
without data. Grinding for a positive result after this many nulls is how a
research project turns into a curve fit.

## What "squeezing the juice" actually means here

**The realistic best outcome is not a profitable strategy.** It is a defensible,
timestamped answer to: *which parts of the most-watched trading methodology on
the internet survive contact with 15.7 years of data, and which are diurnal
seasonality wearing a vocabulary.*

`[OUTSIDE]` Critics argue much of SMC is older material renamed, wrapped in a
market-maker narrative that is difficult to falsify. **This workspace can
falsify it** - it has the corpus in checkable form, clean data, a hypothesis
count, and a sealed holdout. Almost nobody arguing about ICT online has any of
those four.

That answer is worth having whichever way it comes out, and it is the thing the
41 episodes were actually good for.

---

## Sources

- [Backtesting - Harvey & Liu (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2345489) and [the CME version](https://www.cmegroup.com/education/files/backtesting.pdf)
- [The Deflated Sharpe Ratio - Bailey & Lopez de Prado](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID2460551_code87814.pdf?abstractid=2460551)
- [Market intraday momentum - Journal of Financial Economics](https://www3.nd.edu/~zda/intramom.pdf) and [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598)
- [The Overnight Drift - NY Fed Staff Report 917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- [Volume-driven time-of-day effects in intraday volatility](https://www.oru.se/globalassets/oru-sv/institutioner/hh/workingpapers/workingpapers2025/wp-14-2025.pdf)
- [Lunch effect in US stock market indices - QuantPedia](https://quantpedia.com/lunch-effect-in-the-u-s-stock-market-indices/)
- [Smart Money Concepts research - IndicatorEdge](https://indicatoredge.io/smart-money-research)
- [Fair Value Gap - LuxAlgo library](https://www.luxalgo.com/library/concept/fair-value-gap/)
