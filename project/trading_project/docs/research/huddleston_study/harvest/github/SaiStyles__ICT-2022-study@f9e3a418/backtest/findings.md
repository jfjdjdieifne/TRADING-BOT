# Findings

Reasoning over results. **No script writes this file** - `veto_report.md` is generated
numbers, this is what they mean. DECISIONS.md section 16's tiers.

---

## 0. A cross-episode audit found three implementation errors - 2026-09-03

**Prompted by the builder asking whether the cross-episode structure had been taken into
account. It had not been, in the code.** `THE-MODEL.md` was assembled across episodes, but
`vetoes.py` collapsed back to one citation per rule. Three concrete errors:

1. **An invented window wearing his citation.** The overnight run was measured
   midnight -> 08:30. **Ep09 [12:44] states the window: 02:00-05:00 NY.** Corrected. The
   original rows 1-5 and 10-13 in `ledger.md` used the wrong definition and are kept -
   they are a real test of a wrong hypothesis, not a mistake to erase.
2. **9:30 pooled into the killzone, against the corpus's own instruction.**
   `study/ep15.md` records three episodes converging - ep09 [15:15] skip the morning after
   an overnight run, ep13 [18:53] do not chase the 9:30 move, ep15 stops do not survive
   there - and concludes *the equities open is a distinct regime and probably should be
   excluded or modelled apart rather than pooled with 8:30-11:00*. It was pooled anyway.
   Now split into 08:30-09:30 and 09:30-11:00.
3. **A six-episode contested concept coded as a one-line veto.** `midrange` cited ep32
   [04:56] alone. Equilibrium is also ep02 [35:47], ep04 [01:17] (the range is the day's
   OWN low-to-high - unavailable at 08:30 without look-ahead), ep07 [10:45] (**at
   equilibrium he says trade smaller and faster, NOT stand aside - a direct contradiction
   of the veto reading**), ep22 [10:23] (two competing definitions, logged as contested),
   and ep27 [06:58] (equilibrium as an entry precondition). Now documented in the
   docstring as one of at least three readings.

**The structural fix, so this does not recur:** `extraction/build_refinements.py` builds
`study/_refinements.md` - every concept's episode list plus all **144 revision notes** the
pages recorded about each other. Read it before implementing any rule.

It also exposed a defect in `study/` itself: **only 2 of 216 `teaches:` slugs appear
twice**, because they were written free-hand one page at a time, so `order-block` and
`order-block-formation` never join. Indexing on tokens recovers the axis, and gives the
frequency evidence DECISIONS.md section 11 said an episode-keyed brain could never
produce - **at zero quota cost**:

| theme | episodes |
|---|---|
| **fvg / imbalance** | **36 of 41** |
| order block | 20 |
| premium / discount | 20 |
| liquidity | 16 |
| market structure | 16 |

**The correction slightly HELPED his case.** With his own 02:00-05:00 window the
directional reversal gradient is stronger than it was under my invented one. The challenge
was right and the audit was worth the time.

---

## 1. The vetoes, tested on day quality alone - 2026-09-03, n = 36

### Nothing survived. That is the result.

Thirty-six hypotheses tested on `dev` (2,962 full sessions, 2010-2021). The largest
z-score on any trap-detecting measure is **+2.7**. Across 36 draws you expect a maximum
around **2.5 from pure chance alone**.

**So: zero vetoes have demonstrated an effect.** This is exactly the outcome section 14
exists to make visible - without the random-refusal control, `midrange band=0.20` raising
median efficiency from 0.466 to 0.476 while discarding 30% of sessions would have read
as a working filter. It is not one. It is what discarding 30% of anything does.

### The one large effect cuts AGAINST the rule

`overnight_run` at 25 points: **z = -18.6 on opportunity.** Not chance. Refusing those
days drops the median killzone opportunity from **32 points to 28**, because the days it
refuses are the highest-range mornings of the sample.

**Be honest about the depth of this.** It is mostly volatility autocorrelation - a big
overnight move predicts a volatile day, which predicts a wider morning range. It is a real
effect and a shallow one. What makes it decision-relevant is only this: **ep09's veto is
not free.** It discards 32% of sessions under his own window, and they are the big ones.

### ep09's stated mechanism is not visible in the data

Test A asked whether those mornings are *smaller*. **He never claims they are**, so a null
there proves nothing about him. His actual claim, ep09 [15:15]:

> `wait until the other side of lunch at 1:00 in the afternoon, and then anticipate the
> New York lunch lows taken out, or the New York morning session lows.`

Measured directly - his setup is the overnight running one way and the afternoon taking
the morning's extreme the other way:

Re-run with **his** window, 02:00-05:00 (ep09 [12:44]), not my invented one:

| | directional reversal | z |
|---|---|---|
| all 2,962 sessions | **41.3%** | - |
| overnight >= 25 pt (n=957) | 44.8% | **+2.6** |
| overnight >= 50 pt (n=421) | 44.5% | +1.5 |
| overnight >= 75 pt (n=205) | 46.6% | +1.6 |
| overnight >= 100 pt (n=112) | 47.7% | +1.4 |
| overnight >= 150 pt (n=38) | 31.6% | -1.2 |

**Weak, and the wrong shape.** The *rate* rises with the threshold (44.8% -> 47.7%), which
is the direction he claims. But **the significance is highest at the loosest threshold and
decays as it tightens** - which is what a thin sample looks like, not what a real effect
looks like. A genuine "bigger run, stronger reversal" would strengthen, not weaken. At 150
points it inverts entirely.

And the best z here is **+2.6 out of 36 hypotheses**, where chance alone produces a maximum
around 2.5.

**Verdict: not supported, and not refuted.** The gradient points his way and the sample is
too thin to say more. Worth re-testing properly once entry rules exist - which is a
different sentence from the one my first pass would have supported, and the difference came
entirely from using his window instead of mine.

### What this does NOT show, and the distinction matters

**It does not show ep09 is wrong.** Opportunity and efficiency are day-quality proxies,
not profit and loss. A veto's job may be to avoid *losses under a specific entry rule*,
and there is no entry rule here yet. A rule can protect one setup and be entirely
invisible to a day-level measure.

**These vetoes must be re-tested against realised trades once the entry gates exist.**
That is the correct conclusion. "The corpus's vetoes are worthless" is not supported by
anything above and should not be written down anywhere.

**A second limitation, working the same direction.** The null draws random *days*, which
ignores that volatile days cluster. Real significance is therefore *weaker* than the
z-scores printed, not stronger. Nothing above is rescued by better statistics.

### What is now known that was not before

1. **A baseline exists.** Median killzone opportunity **32 points**, median efficiency
   **0.466**, PM takes the morning low **37.4%** / the morning high **47.4%**, directional
   reversal **41.3%**. Every future claim gets measured against these.
2. **The vetoes have a price, and it is now quantified.** `wednesday_done` discards
   **39.8%** of all sessions - ep37 [05:18] is the single most expensive rule in the
   corpus. It has to earn that, and now there is a number to hold it to.
3. **The build order was right.** This was the cheapest thing available, needed no entry
   rules, and produced a decision-relevant null in one pass without touching `reserve` or
   opening the holdout.

### Deliberately not done

Three of the corpus's fifteen refusals were testable at this stage. **The other twelve are
in `vetoes.py` under `DEFERRED`, with the reason for each** - eight need entry-stage
primitives or a bias, one (`fomc_nfp`, ep23 [15:51]) needs an economic calendar we do not
have, and one (`sloppy_chart`, ep19 [61:04]) is explicitly not codeable and must not be
proxied. Fourteen of fifteen quietly becoming three is how 41 episodes of reading turns
into a toy.

---

## 2. The gold-standard pattern, full dev slice - 2026-09-03, n = 139

**148 trades over 2,969 sessions. Expectancy -0.076R, win rate 44%.**
`backtest/setup_report.md` has the full funnel.

The pipeline: FVG (ep02 [17:53]) inside a displacement leg, after liquidity is
taken, structure shifted, gap in discount (ep29 [05:11]), order block present,
price into the 0.62-0.70 OTE (ep41 [18:55]). Entry at the gap edge price touches
first, stop under the gap (ep41 [19:08]), target the displacement extreme.

### Nothing is profitable, and nothing survives the count

Best variant is `target=nearest_pivot` at **+0.086R over 118 trades**; next is
`min_rr=1` at +0.056R over 77. **Both are the best of 25 configurations at
n = 139.** That is not a result, it is the top of a distribution.

Baseline is **negative**, and so is nearly everything else.

### Three things that ARE informative

**1. The order-block gate rejects NOTHING.** 396 candidates in, 396 out. As
literally implemented, ep17's `last opposite-close candle body` is satisfied
almost always - there is nearly always an opposite-close candle in the preceding
twelve bars. `no_ob` and `baseline` are byte-identical. **So the flagship
pattern's middle element is, in this implementation, decoration.**

Only ep12 [44:02]'s definition - `a consecutive series of same-direction close
candles, not one candle` - actually filters (396 -> 170), and it has the best
win rate of the three (49%) on a third of the trades. **The corpus's three
order-block definitions are not stylistic variants. Two of them do no work.**

**2. The displacement sweep is FLAT, exactly as pre-registered.**

| threshold | trades | expectancy |
|---|---|---|
| 0 pt (negative control) | 266 | -0.134R |
| 20 pt | 148 | -0.076R |
| 40 pt | 70 | -0.048R |
| 80 pt | 31 | -0.162R |

`ledger.md` pre-registered the reading before the run: *flat across the sweep ->
magnitude barely matters and his structural gates are doing the work.* It is
flat. **The number he never gives in 41 episodes turns out not to be where the
edge is hiding** - which retires the question rather than leaving it open.

**3. Removing OTE IMPROVES it** (-0.076 -> +0.024). The gate the corpus took
eight episodes to define, and calls part of the gold standard, costs expectancy
here. Inside noise, but it is the opposite of the expected sign.

### The limitation that matters more than any of the above

**148 trades in 12 years is ~12 a year. He trades most days.** So this is not a
test of his model; it is a test of a narrow slice of it, and the sparsity has a
identifiable cause: **structure and the gap are read on the same timeframe.**
He does not do that - ep05 [07:06] and ep12 [29:00] put structure on the
15-minute, ep06 [26:35] puts entries on the 1-minute, and the cascade in ep11/
ep12 walks 15 -> 5 -> 1. Detecting the FVG on a lower timeframe than the
structure leg is the single highest-value fix and is the next thing to build.

**So the honest headline is not "his model loses money."** It is: *this
implementation of the gold-standard pattern, at 12 trades a year, has no edge on
dev, and the three sub-findings above are more useful than the P&L.*

---

## 3. His clock, tested properly for the first time - 2026-09-03, n = 165

**PLAN.md step 1.** Every earlier result was measured *inside* the killzone,
which assumes the answer. This ranks each of his named windows against
**same-length windows of the same sessions**.

Two corrections made the test valid, and both changed the answer:

- **Length must match.** Maximum favourable excursion grows sub-linearly with
  time, so opportunity-per-minute mechanically rewards short windows. The first
  run ranked his 60-minute London close first for pure arithmetic reasons.
- **The veto null was inverted.** Testing the *traded* set - 60-93% of the data -
  left almost no pool to draw matched controls from; the null collapsed to
  near-zero variance and z came out as **9.5e13**. `nulls.py` now refuses to
  print a z when the null has no spread, and the test asks the natural question
  instead: are the days he REFUSES different from similar-volatility days?

### THE AM KILLZONE IS REAL. It is the first thing in this corpus that is.

| his window | opportunity | **pctile** | efficiency | **pctile** |
|---|---|---|---|---|
| **AM killzone 08:30-11:00** (ep02 [42:40]) | 32.2pt | **100** | 0.467 | **100** |
| **09:30-11:00** (ep06 [33:16]) | 30.5pt | **100** | 0.479 | **100** |
| London close 10:00-11:00 (ep40 [17:36]) | 22.2pt | 93 | 0.467 | 90 |
| on-close macro 15:00-16:00 (ep32 [11:32]) | 15.8pt | 83 | 0.456 | 73 |
| PM 13:30-16:00 (ep41 [06:20]) | 23.8pt | 68 | 0.451 | 40 |
| LUNCH 12:00-13:00 (ep05 [10:04]) | 13.8pt | 63 | 0.442 | 33 |
| 08:30-09:30 (ep25 [34:43]) | 10.8pt | 50 | 0.435 | **13** |
| London killzone 02:00-05:00 (ep03 [32:59]) | 15.5pt | 32 | 0.453 | 59 |
| pre-08:30 05:00-08:30 (ep09 [12:44]) | 15.5pt | 10 | 0.440 | **5** |

**08:30-11:00 beat every same-length control on BOTH measures.** That matters
because **efficiency is a ratio** - |net move| / range - so it is not
mechanically inflated by volatility the way opportunity is. Price moves more
*directionally* in his window than in any other 150 minutes of the day. That is
not the U-shape; the U-shape explains the opportunity column, not this one.

**Honest limits.** The controls step every 30 minutes, so they overlap heavily
and are nowhere near independent - the effective number of draws is far below
the ~13 counted, and "100th percentile" is not a z-score. It does not clear
|z| > 3.0, because a percentile cannot. It is `dev` only. **Treat it as the
first thing worth taking to `reserve`, not as settled.**

### Three of his own windows are contradicted

- **08:30-09:30 sits at the 13th percentile on efficiency.** Ep25 [34:43] says
  the setup forms or is framed there. On this measure it is one of the choppiest
  hours of the day, and **the killzone's entire value sits after 09:30** - which
  is where ep06 [33:16] warns the first move is usually the wrong one.
- **London killzone 02:00-05:00: 32nd percentile.** Ep03 [32:59] names it. On
  NQ it is a below-average window. Fair caveat: ep08 [05:38] treats London as a
  forex concept, so this is evidence against applying it to the index, not
  against the idea itself.
- **Pre-08:30 is 10th percentile on opportunity and 5th on efficiency** - the
  worst window tested, which is at least consistent with him telling you not to
  trade it.

**And lunch is not special.** 63rd on opportunity, 33rd on efficiency. The
no-entry rule (ep05 [10:04]) is defensible as chop-avoidance, but lunch is an
ordinary hour, not a trap.

### The vetoes, volatility-matched: right direction, not significant

| veto | refused-day efficiency | vs traded | matched z |
|---|---|---|---|
| `wednesday_done` (ep37 [05:18]) | 0.459 | 0.475 | **-2.65** |
| `midrange` band=0.20 (ep32 [04:56]) | 0.455 | 0.476 | **-2.30** |
| `midrange` band=0.10 | 0.460 | 0.468 | -0.69 |
| `midrange` band=0.05 | 0.439 | 0.468 | -1.23 |

**All four point his way** - the days he refuses really are less efficient than
similar-volatility days he would trade. **None clears |z| > 3.0**, and this is
the best of four at n = 165. Not a finding. But unlike section 1, it is no
longer a flat null either, and the volatility confound that produced the old
z = -18.6 is gone.

---

## 4. The fair value gap does NOT attract price - 2026-09-04, n = 86

**PLAN.md step 2, and the biggest result so far.** FVG/imbalance appears in
**36 of 41 episodes**. It had never been tested on its own - only inside a
seven-gate pipeline where its contribution could not be recovered.

### The design, because it is what makes the answer mean anything

A gap only forms after a fast three-bar move. **"Gaps fill 70% of the time"
therefore says nothing** - price retraces after any fast move. So every gap is
paired with a control bar that had a **same-sized move, in the same direction, at
the same hour, that left no gap**, and the identical measurement runs on both.

Sign-matching was not in the first version and nearly produced a spectacular
false result: without it a bullish gap is compared against a mix of up- and
down-moves, so `fill` silently averages a retracement question with a
continuation question, and NQ's 2010-2021 uptrend drags the controls' signed
return negative. Adding it flipped several columns.

### Result: 16 of 16 rows say gaps fill LESS, not more

| tf | dir | horizon | gaps | fill | matched ctrl | z |
|---|---|---|---|---|---|---|
| 5m | bullish | +20min | 89,106 | **48.0%** | 62.1% | **-59.9** |
| 5m | bearish | +20min | 81,307 | **50.0%** | 64.2% | **-57.9** |
| 5m | bullish | +120min | 80,829 | 75.5% | 82.2% | -32.6 |
| 15m | bullish | +60min | 28,010 | 47.5% | 60.4% | -30.7 |
| 15m | bearish | +60min | 24,302 | 49.8% | 63.8% | -31.2 |
| 60m | bullish | +240min | 6,358 | 46.4% | 61.2% | -16.8 |
| 60m | bearish | +720min | 2,601 | 74.7% | 81.2% | -5.6 |

Every timeframe, both directions, every horizon, `touch` and `fill` alike:
**negative, and enormous.** The bar is |z| > 3.0. These reach **-59.9**.

**The claim 36 of 41 episodes rest on is that price returns to the gap. On NQ
over 15.7 years it returns LESS than to an equally distant level after an
equivalent move.**

### And the forward return says the move is damped, not extended

Signed in the direction that made the gap:

| | gap | matched ctrl | z |
|---|---|---|---|
| 5m bearish +20min | -0.05pt | -0.35pt | **+4.7** |
| 60m bearish +240min | -0.23pt | -4.22pt | **+4.2** |
| 15m bullish +360min | +1.15pt | +3.00pt | **-3.3** |

Bearish gaps fall **less** than matched down-moves; bullish gaps rise **less**
than matched up-moves. **In both directions the gap predicts LESS movement, not
more.** Price after a gap does less of everything - less retracement and less
continuation. It consolidates.

**Which is exactly what he says in ep09 [12:21]:**
> `whenever you see a big run up or a big run down there's a consolidation that
> takes place shortly after`

So the corpus has the *behaviour* right and the *mechanism* wrong.

### What the gap actually is

**A gap means the three bars did not overlap - the move was clean and
impulsive.** The matched control had the same-sized move WITH overlap - the same
distance travelled choppily. So the finding restates as: **a clean impulsive move
retraces less than a choppy move of the same size.**

That is real information, and it is worth having. **It is just not the
information the model claims.** The gap is a *description of how the move
happened*, not a level that pulls price back.

### Honest limits

`[OUTSIDE]` The published gap literature expects **continuation**, and we do not
find that either - we find damping. So this agrees with the literature against
gap-fill, and disagrees with it on what replaces it.

Measurement pairs on **absolute distance**, which is the right control for "did
price travel this far", but a gap's near edge is a level price traded moments
ago while the control's level may not be. That bias would make gaps look MORE
touched, not less - so it works against the finding rather than producing it.

`dev` only. Not yet seen on `reserve` or the holdout.

---

## 5. The published intraday-momentum anomaly does not replicate on NQ - 2026-09-04, n = 92

**PLAN.md step 3.** `[OUTSIDE]` Market intraday momentum (JFE 2021): across 60+
futures 1974-2020, the last 30 minutes' return is positively predicted by the
return over the rest of the day. **ep32 [11:32] and ep05 [26:53] describe the
same window independently** - the corpus's only overlap with peer-reviewed work,
and the one place a rule of his starts with a real prior.

### The sign is right. The magnitude is not.

| window | anchor | spread | **t** | hit rate | pctile of controls |
|---|---|---|---|---|---|
| on-close macro 15:00-16:00 (ep32) | prev close | +2.41bp | **+1.62** | 48.0% | **94** |
| last 30min 15:30-16:00 (the paper's) | prev close | +1.95bp | **+1.68** | 47.3% | **94** |
| 15:40-16:00 (ep05 [26:53]) | prev close | +1.58bp | **+1.55** | 47.1% | **94** |
| on-close macro 15:00-16:00 | midnight | +2.63bp | **+1.68** | 48.9% | **93** |

**Every spread is positive - the direction the paper predicts.** None comes close
to |t| > 3.0. On NQ over 2010-2021 the effect is present in sign and absent in
strength.

**His windows rank ~93rd percentile** against same-length controls, so he did
locate the right part of the day. But the whole distribution is weak: the best
control tops out around t = +2.5.

### The dominant intraday pattern on NQ is mild MEAN REVERSION

Scanning all 32 half-hour windows, most spreads are **negative** - the day's
direction tends not to continue:

| window | spread | t |
|---|---|---|
| 09:30-10:00 | **-3.89bp** | -2.63 |
| 10:30-11:00 | -2.04bp | -1.95 |
| 13:00-13:30 | -1.61bp | -2.21 |
| **15:30-16:00 (his)** | **+1.95bp** | +1.68 |

**And hit rates are 43-49% in every single window** - below a coin flip
everywhere. So whatever momentum exists lives in the *size* of moves, not their
frequency. That is worth knowing before anyone builds a directional rule on
"the day's bias continues".

### The strongest number in the table is not his, and not momentum

**06:30-07:00 shows spread -2.20bp at t = -5.00** - strong *reversal*. It is the
only cell in the table that clears |t| > 3.0.

**Do not call this a finding.** It is the best of 32 windows scanned without
pre-registration, in a thin pre-market hour the corpus never discusses, and
best-of-32 produces surprising t-values on its own. **It is hereby pre-registered
for a single test on `reserve`** - if it survives there, it is real and it came
from the data rather than from him.

### Honest limits, and they matter here

**Non-replication on one instrument over one sub-period is not a refutation of
the paper.** It tested 60+ futures over 1974-2020 with regular-session
definitions; this is NQ alone, 2010-2021, on a 24-hour contract with
midnight and prev-close anchors. The correct statement is: **the anomaly is not
strong enough on this instrument, in this period, to support a rule** - not that
the published result is wrong.

**What it means for the corpus:** ep32's on-close macro is not a mistake - it
points at the right window, and the sign agrees with published work. It just is
not tradable at this strength. **Verdict: located correctly, too weak to use.**

---

## 6. The sparsity is fixed, and it sharpened the null - 2026-09-04, n = 124

**PLAN.md step 6.** Two corrections, and the second mattered more.

**Timeframe split.** The gap is now read on a finer chart than the structure -
`fvg_tf=5m` under `struct_tf=15m`, the cascade of ep05 [07:06], ep12 [29:00] and
ep06 [26:35]. Reading both on one frame was why only ~12 trades a year formed.

**THE SEQUENCE WAS WRONG, and that was the bigger bug.** The old code tested each
gap *the instant it formed*. But a gap forms **during** the displacement, while
the leg is still extending - so the leg high is barely above it and ep29
[05:11]'s "must sit in the discount half" gate rejected almost everything: 121
candidates down to 6. **That was not his rule failing; it was the rule being
asked at a moment he never asks it.** ep41's procedure is displacement ->
structure shift -> price *returns* to the gap. The leg is now only evaluated once
it is complete.

| | before | after |
|---|---|---|
| candidates | 50,541 | **161,484** |
| reached OTE | 282 | **415** |
| trades | 148 | **171** |
| trades at `disp=0pt` | 266 | **341** |
| baseline expectancy | -0.076R | **-0.245R** |

**More trades, and worse.** Of 28 configurations exactly one is positive -
`struct_tf=60m` at +0.031R on 60 trades, which is noise. `fvg_tf=1m` gives 199
trades at -0.105R; `disp=0pt` gives 341 at -0.120R.

**The fix did its job: it turned "too few trades to conclude" into a conclusion.**

## 7. No gate earns its place - 2026-09-04, n = 128

**PLAN.md step 5, and the cleanest result of the project.** ep24 [17:41]:

> `this is the proof, the evidence that the model has validity`

Every refused candidate is given the entry and stop the rule would have used and
executed anyway. **Both sides use the same 2R target**, so selection is the only
thing that differs - the first version had the refused setups on 2R and the
accepted ones on the rule's own target, which would have proved nothing.

**Accepted: 171 trades at -0.185R, win 27%.**

| gate | refused | their expectancy | win | z | verdict |
|---|---|---|---|---|---|
| `g3_displacement` | 635 | **+0.111R** | 37% | **-2.60** | threw away better trades |
| `g2_liquidity_taken` | 3,571 | -0.029R | 32% | -1.54 | threw away better trades |
| `g5_gap_in_discount` | 252 | -0.089R | 31% | -0.73 | threw away better trades |
| `g7_ote` | 117 | -0.179R | 27% | **-0.04** | does nothing at all |

`z` is accepted-minus-refused, so **negative means the gate discarded the better
setups.** All four are negative.

**Nothing clears |z| > 3.0, so no gate is *provably* harmful.** But not one is
positive, and the pattern is unanimous across four independent filters:

- **`g3_displacement` is the worst.** The setups it refused made **+0.111R**
  while the ones it approved made **-0.185R**. That is the same conclusion the
  displacement sweep reached from the other direction - flat across every
  threshold - and the same one section 4 reached about gaps: **the "energetic
  move" is not where the edge is.**
- **`g7_ote` has a z of -0.04.** The gate that took eight episodes to define, and
  that ep41 [16:36] calls part of the gold standard, separates nothing whatever.
  Combined with `no_ob` being byte-identical to baseline, **two of the gold
  standard's three elements are inert.**

### The honest limit

These are counterfactuals: overlap is allowed, so the refused set is not a
portfolio anyone could have held. And -0.185R accepted vs +0.111R refused is a
comparison between 171 trades and 635 - the accepted sample is small enough that
its expectancy is not precisely known.

**What it does support:** there is no evidence any of these four gates adds
value, and one has a 2.6-sigma hint of subtracting it. **After 128 hypotheses
that is not a finding - it is an absence of one, which is what the corpus's
central pattern has produced at every level tested so far.**

---

## 8. Liquidity sweep and order block, isolated - 2026-09-04, n = 152

Same matched design that settled the FVG: every event paired with a
**same-sized move, same direction, same hour, no event**.

### The liquidity sweep is the first primitive with a positive signal

ep25 [28:36] and the whole Judas structure: price runs an old level to take the
stops, **then reverses**. Signed so positive = reversed as claimed.

| event | tf | horizon | n | event | matched ctrl | z |
|---|---|---|---|---|---|---|
| **sweep of prev HIGH** | 5m | +120min | 5,510 | +0.447pt | -1.378pt | **+3.10** |
| sweep of prev HIGH | 5m | +60min | 5,672 | +0.187pt | -0.451pt | +1.57 |
| sweep of prev HIGH | 15m | +360min | 3,088 | +0.236pt | -2.151pt | +1.86 |
| sweep of prev LOW | 5m | +120min | 3,885 | +0.710pt | +1.033pt | -0.36 |
| sweep of prev LOW | 15m | +180min | 2,465 | +1.968pt | +2.178pt | -0.16 |

**One cell clears |z| > 3.0.** After taking out the previous session's high,
price then *falls* ~0.45pt on average over two hours, while a matched up-move
that took no level *rises* ~1.38pt. That is the corpus's mechanic, visible.

**Two reasons not to celebrate yet.** It is the **best of 12** sweep cells, and
the same test on the 15-minute frame gives only +1.86. And it is **asymmetric**:
sweeping the previous LOW shows nothing at all (-0.36 to +0.96 across six
cells). A mechanic that works on highs and not lows in a market that rose for
the whole sample is exactly what a drift artefact looks like - though the
controls are sign-matched, which is the defence against that.

**Pre-registered for one test on `reserve`:** sweep of prev high, 5m, +120min.
Declared now, before looking, so it cannot be chosen after the fact.

### The order block is anti-predictive

Findings 7 showed order-block *formation* is near-universal and carries no
information. This measures the claim that survives that: **when price RETURNS to
the zone, does it react in the direction the block predicts?**

**11 of 12 cells negative, and not marginally:**

| block | tf | horizon | n | event | matched ctrl | z |
|---|---|---|---|---|---|---|
| bearish | 5m | +60min | 65,637 | -0.211pt | +0.849pt | **-9.35** |
| bearish | 15m | +90min | 23,459 | -0.386pt | +1.562pt | **-8.64** |
| bullish | 5m | +30min | 67,578 | +0.035pt | +0.655pt | **-7.58** |
| bullish | 15m | +90min | 24,371 | +0.192pt | +1.532pt | **-5.82** |

Price returning to an order block does **less** of what the block predicts than
a matched move does. Consistent across both timeframes, both directions, nearly
every horizon, on 60,000+ events.

**The honest caveat, and it is a real one.** The event is conditioned on price
having *come back* to a level; the control is a bar with a matched local move but
no such history. Some of the gap may be "price that has just retraced behaves
differently" rather than anything about order blocks. The control matches the
return bar's own 3-bar move, which handles part of this - not all of it.

**What it does not support:** any version of "the order block is a level price
reacts from". Across every test now run - formation (findings 7: rejects nothing),
gate value (findings 7: z = -0.04 for OTE, no contribution for OB), and reaction
on return (here) - **the order block has not produced a single positive number.**

### Where the three primitives now stand

| primitive | episodes | verdict |
|---|---|---|
| fair value gap | 36 of 41 | **premise contradicted** - fills LESS than matched moves, z to -59.9 |
| order block | 20 of 41 | **no signal anywhere**, anti-predictive on return, z to -9.35 |
| liquidity sweep | 16 of 41 | **the one survivor** - prev-high sweeps reverse, z = +3.10, but best of 12 and asymmetric |

---

## 9. THE RESERVE LOOK - both candidates failed - 2026-09-04, n = 154

One pass, two hypotheses, both declared before the script existed. `reserve` is
2023-01-01..2024-02-29, 300 sessions, never previously read.

| test | dev | reserve | held? |
|---|---|---|---|
| killzone opportunity | 100th pctile | **100th pctile** | **yes** |
| killzone **efficiency** | 100th pctile | **26th pctile** | **NO** |
| prev-HIGH sweep reverses | z = **+3.10** | z = **-0.15** | **NO** |

### The killzone half-survived, and it lost the half that mattered

Opportunity held perfectly - 08:30-11:00 is still the widest 150 minutes of the
day. **But that was always the trivial half.** `[OUTSIDE]` intraday volatility is
U-shaped, so the morning being the biggest window is the U-shape, not ICT.

**The efficiency result was the whole argument, and it did not replicate.**
Efficiency is |net move| / range - a ratio, not inflated by volatility - and on
`dev` his window was the cleanest of the day at the 100th percentile. That was
the single reason to say the killzone carried information beyond volatility.
On `reserve` it comes in at the **26th percentile: below average.**

So the honest statement collapses to: **08:30-11:00 is the most volatile window
of the NQ day. It is not the cleanest one.** The first half is real and was never
in doubt. The second half is gone.

### The sweep did not replicate at all

`dev`: +3.10. `reserve`: **-0.15**. Event -3.678pt against a matched control at
-3.092pt - the two are indistinguishable, and both are negative because 2023 was
a rising market.

**This is exactly what a best-of-12 result does out of sample**, and it is why
findings 8 flagged it as fragile rather than calling it an edge.

### The fair caveat, which does not rescue either

`reserve` is **300 sessions against dev's 2,970**, and the sweep had 531 events
against 5,510. Lower power: failing to replicate on a tenth of the data is not
proof of absence. A larger out-of-sample slice might have shown the sweep at,
say, +1.5 rather than -0.15.

**But nothing here argues the other way either.** The point estimate did not
weaken - it went to zero. And the killzone efficiency result had no power problem
at all: 300 sessions is plenty to rank one window against 23 controls, and it
ranked 26th.

### What this closes

**Nothing from the 2022 corpus has survived out-of-sample testing.** The clock's
volatility profile survives, and that was never his claim - it is a documented
property of index futures that predates the videos by decades.

**The holdout was never opened, and now does not need to be.** It exists to
adjudicate a candidate that survived everything else. Neither did. Opening it now
would be spending the last clean slice on hypotheses that already failed - which
is the opposite of what it is for. **It stays SEALED.**

---

## Ledger integrity: n was inflated 86 -> 213, and is corrected - 2026-09-04

Found while running step 2. **Two bugs, both in the dedup key:**

1. **`data` carried the realised sample count.** Control selection is random, so
   the count moved by one or two between runs and every re-run of the same
   hypothesis logged as new. `data` is now the slice only; sample size lives in
   `result`.
2. **`params` contained a literal `|`** (in `|3-bar move|`). The ledger is a
   markdown table, so the row split into extra columns and the dedup read the
   wrong fields entirely. Every runner now passes each field through `_clean()`.

The FVG study alone had **48 rows for 16 questions** - one set per spelling of
its own params text.

**Removing duplicates is the honest direction, and it is not a section 17
violation.** Section 17 forbids deleting a hypothesis that was really tested,
because that flatters the survivors. Counting ONE hypothesis three times does not
give it three chances at a false positive - it *overstates* the multiple-testing
burden. Verified idempotent across three consecutive runs at **n = 86**.

Nothing qualitative changes: the killzone result was a percentile, not a z, and
nothing else came near 3.0 at either count.

---

## Next

**Money management** - ep41's ladder against flat 1% sizing. Pure arithmetic, needs no
entry model to be correct, pre-registered in `ledger.md`. Then the entry gates, and only
then are the vetoes re-tested against realised trades, which is the test that can actually
settle them.

