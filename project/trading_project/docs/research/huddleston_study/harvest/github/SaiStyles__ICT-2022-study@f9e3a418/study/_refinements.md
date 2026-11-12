# Cross-episode index - GENERATED, do not hand-edit

`python extraction/build_refinements.py`

**No episode is self-contained.** OTE is used from ep01 and defined only in
ep41 [18:55]. Ep03/07's 3.5-4.5% risk and ep07/20's 0.25-1% turned out to be
rungs of one ladder (ep41). Ep19 [99:39] found two nested Judas swings where
ep09/10/13 had described one.

**Read the relevant rows here before implementing any rule.** Implementing from
a single episode's citation is how a six-episode contested concept becomes a
one-line predicate - which already happened to `midrange` in `backtest/vetoes.py`.

41 pages, 216 distinct concepts.

## Load-bearing concepts - taught in more than one episode

Frequency is weight. A concept taught once is a remark; one taught repeatedly is
structural, and its **latest** statement is usually the most specified.

| concept | times | episodes |
|---|---|---|
| **close-proximity-entries** | 2 | ep10, ep29 |
| **contract-rollover** | 2 | ep05, ep36 |

**Only 2 of 216 exact slugs appear twice, and that is a defect in the tags, not a fact about the corpus.** They were written free-hand one page at a time, so `order-block`, `order-block-formation` and `order-block-refined` never join. The token table below recovers the axis.

## By token - the axis the exact slugs cannot give

Every `teaches`/`depends_on` slug split into words. Crude, and it works: it is
the only view that shows a theme running through a dozen episodes.

| token | episodes | which |
|---|---|---|
| **fvg** | 36 | ep02, ep03, ep04, ep05, ep06, ep07, ep08, ep09, ep10, ep11, ep12, ep13, ep14, ep15, ep16, ep18, ep20, ep22, ep23, ep24, ep25, ep26, ep27, ep29, ep30, ep31, ep32, ep33, ep34, ep35, ep36, ep37, ep38, ep39, ep40, ep41 |
| **imbalance** | 36 | ep02, ep03, ep04, ep05, ep06, ep07, ep08, ep09, ep10, ep11, ep12, ep13, ep14, ep15, ep16, ep18, ep20, ep22, ep23, ep24, ep25, ep26, ep27, ep29, ep30, ep31, ep32, ep33, ep34, ep35, ep36, ep37, ep38, ep39, ep40, ep41 |
| **block** | 20 | ep03, ep09, ep12, ep13, ep14, ep16, ep17, ep19, ep21, ep22, ep23, ep25, ep26, ep27, ep30, ep31, ep34, ep35, ep36, ep41 |
| **discount** | 20 | ep02, ep03, ep04, ep06, ep07, ep08, ep09, ep10, ep16, ep18, ep22, ep25, ep27, ep29, ep32, ep33, ep35, ep36, ep38, ep41 |
| **order** | 20 | ep03, ep09, ep12, ep13, ep14, ep16, ep17, ep19, ep21, ep22, ep23, ep25, ep26, ep27, ep30, ep31, ep34, ep35, ep36, ep41 |
| **premium** | 20 | ep02, ep03, ep04, ep06, ep07, ep08, ep09, ep10, ep16, ep18, ep22, ep25, ep27, ep29, ep32, ep33, ep35, ep36, ep38, ep41 |
| **liquidity** | 16 | ep01, ep02, ep03, ep04, ep06, ep07, ep25, ep26, ep27, ep31, ep32, ep33, ep34, ep35, ep39, ep40 |
| **structure** | 16 | ep02, ep03, ep04, ep05, ep06, ep07, ep08, ep11, ep12, ep13, ep14, ep15, ep23, ep31, ep36, ep37 |
| **market** | 14 | ep02, ep03, ep04, ep05, ep06, ep07, ep08, ep12, ep13, ep14, ep15, ep36, ep37, ep40 |
| **swing** | 14 | ep05, ep09, ep10, ep15, ep16, ep17, ep18, ep19, ep21, ep23, ep24, ep25, ep30, ep31 |
| **three** | 13 | ep09, ep10, ep16, ep17, ep19, ep21, ep22, ep25, ep27, ep30, ep35, ep37, ep39 |
| **draw** | 12 | ep02, ep03, ep07, ep26, ep27, ep31, ep32, ep33, ep34, ep38, ep39, ep40 |
| **power** | 12 | ep09, ep10, ep16, ep17, ep19, ep21, ep22, ep25, ep27, ep30, ep37, ep39 |
| **bias** | 11 | ep07, ep10, ep11, ep12, ep15, ep18, ep22, ep26, ep37, ep38, ep40 |
| **daily** | 11 | ep05, ep07, ep10, ep11, ep12, ep15, ep18, ep22, ep37, ep38, ep40 |
| **displacement** | 11 | ep05, ep06, ep09, ep11, ep12, ep16, ep19, ep20, ep24, ep29, ep33 |
| **judas** | 11 | ep09, ep10, ep13, ep15, ep17, ep18, ep19, ep21, ep24, ep25, ep30 |
| **shift** | 10 | ep03, ep04, ep05, ep06, ep07, ep08, ep14, ep15, ep36, ep37 |
| **stop** | 9 | ep02, ep06, ep14, ep15, ep22, ep26, ep31, ep37, ep41 |
| **entry** | 7 | ep06, ep11, ep12, ep15, ep31, ep36, ep38 |
| **institutional** | 7 | ep12, ep13, ep17, ep23, ep26, ep35, ep41 |
| **opening** | 7 | ep09, ep10, ep11, ep17, ep19, ep21, ep34 |
| **range** | 7 | ep03, ep04, ep05, ep06, ep10, ep25, ep32 |
| **day** | 6 | ep15, ep18, ep25, ep31, ep32, ep39 |
| **flow** | 6 | ep12, ep13, ep23, ep26, ep35, ep41 |
| **price** | 6 | ep09, ep11, ep17, ep19, ep21, ep34 |
| **risk** | 6 | ep03, ep07, ep18, ep20, ep21, ep41 |
| **smt** | 6 | ep07, ep29, ep34, ep35, ep38, ep40 |
| **filter** | 5 | ep18, ep25, ep27, ep29, ep40 |
| **rule** | 5 | ep09, ep13, ep17, ep23, ep30 |
| **session** | 5 | ep03, ep05, ep09, ep16, ep20 |
| **setup** | 5 | ep23, ep24, ep30, ep36, ep39 |
| **contract** | 4 | ep01, ep05, ep19, ep36 |
| **high** | 4 | ep11, ep13, ep31, ep35 |
| **intermarket** | 4 | ep07, ep20, ep21, ep29 |
| **low** | 4 | ep24, ep29, ep30, ep31 |
| **narrative** | 4 | ep15, ep22, ep38, ep39 |
| **nesting** | 4 | ep11, ep12, ep13, ep31 |
| **relationships** | 4 | ep07, ep20, ep21, ep29 |
| **run** | 4 | ep09, ep23, ep24, ep35 |
| **timeframe** | 4 | ep02, ep04, ep08, ep12 |
| **trade** | 4 | ep03, ep04, ep13, ep16 |
| **volatility** | 4 | ep17, ep29, ep31, ep33 |
| **830** | 3 | ep11, ep19, ep25 |
| **930** | 3 | ep13, ep15, ep25 |
| **bodies** | 3 | ep16, ep22, ep23 |
| **buy** | 3 | ep02, ep03, ep05 |
| **close** | 3 | ep10, ep29, ep40 |
| **definition** | 3 | ep05, ep10, ep38 |
| **internal** | 3 | ep03, ep04, ep06 |
| **killzones** | 3 | ep08, ep20, ep40 |
| **level** | 3 | ep20, ep33, ep34 |
| **levels** | 3 | ep17, ep21, ep35 |
| **news** | 3 | ep15, ep17, ep40 |
| **open** | 3 | ep11, ep15, ep31 |
| **placement** | 3 | ep06, ep22, ep26 |
| **point** | 3 | ep16, ep19, ep39 |
| **projection** | 3 | ep16, ep17, ep23 |
| **required** | 3 | ep18, ep33, ep41 |
| **sell** | 3 | ep02, ep03, ep05 |
| **setups** | 3 | ep16, ep23, ep24 |
| **short** | 3 | ep11, ep22, ep24 |
| **stops** | 3 | ep02, ep03, ep05 |
| **sweep** | 3 | ep23, ep24, ep30 |
| **term** | 3 | ep11, ep22, ep24 |
| **trading** | 3 | ep15, ep26, ep27 |

## Referenced but taught elsewhere

`depends_on` minus `teaches`: episodes that USE a concept without teaching it.
**These are the joins.** A rule implemented only from an episode in the right-hand
column is being implemented from a page that assumed the definition.

| concept | taught in | used by |
|---|---|---|
| advanced-market-structure | ep12 | ep13 |
| buy-sell-stops | ep02 | ep03, ep05 |
| daily-bias | ep07 | ep11, ep12, ep15, ep18, ep22, ep37, ep38, ep40 |
| displacement | ep05 | ep06, ep09, ep11, ep12, ep16, ep19, ep20, ep24, ep29, ep33 |
| draw-on-liquidity | ep02 | ep03, ep07, ep26, ep27, ep31, ep32, ep33, ep34, ep39, ep40 |
| imbalance-fvg | ep02 | ep03, ep04, ep05, ep06, ep07, ep08, ep09, ep10, ep11, ep12, ep13, ep14, ep15, ep16, ep18, ep20, ep22, ep23, ep24, ep25, ep26, ep27, ep29, ep30, ep31, ep32, ep33, ep34, ep35, ep36, ep37, ep38, ep39, ep40, ep41 |
| institutional-order-flow | ep12 | ep13, ep23, ep26, ep35, ep41 |
| intermarket-relationships | ep07 | ep20, ep21, ep29 |
| internal-range-liquidity | ep03 | ep04 |
| judas-swing | ep09 | ep10, ep15, ep17, ep18, ep19, ep21, ep24, ep25, ep30 |
| killzones | ep08 | ep20, ep40 |
| market-structure-shift | ep03 | ep04, ep05, ep06, ep07, ep08, ep14, ep15, ep36, ep37 |
| narrative | **never taught - dangling** | ep38, ep39 |
| opening-price | ep09 | ep11, ep17, ep19, ep21 |
| order-block | ep03 | ep09, ep12, ep13, ep14, ep16, ep17, ep19, ep21, ep22, ep23, ep25, ep26, ep27, ep30, ep31, ep34, ep35, ep36, ep41 |
| power-three | ep09 | ep10, ep16, ep17, ep19, ep21, ep22, ep25, ep27, ep30, ep37, ep39 |
| premium-discount | ep02 | ep03, ep04, ep06, ep07, ep08, ep09, ep10, ep16, ep18, ep22, ep25, ep27, ep29, ep32, ep33, ep35, ep36, ep38, ep41 |
| run-vs-sweep | ep23 | ep24 |
| smt | **never taught - dangling** | ep34, ep35, ep38, ep40 |
| structure-nesting | ep11 | ep12, ep31 |
| swing-projection | **never taught - dangling** | ep17, ep23 |

## The change log - what each episode revised

Taken from every page's `Contradicts / refines` section. **This is the corpus's
own record of itself changing.** Where two entries disagree, the later episode is
usually the more specified - but check, because some are genuine contradictions
and belong in `THE-MODEL.md` section 7 as test variants rather than decisions.

### ep02 - "Elements To A Trade Setup": the whole model, in one lesson

- **Refines ep01 [27:19]:** the "liquidity matrix" left undefined in ep01 is defined here at [35:22] as the premium/discount 50% split. Not a mystical structure - a Fibonacci midpoint.
- **Consistent with ep01 [24:36]:** bias-over-entry-precision reappears as [33:41] `if it starts to move lower you can still get in it`.

### ep03 - "Internal Range Liquidity and Market Structure Shift"

- **Refines ep02's "break in market structure":** ep02 used *break* throughout [28:00]. Here he splits the term - intraday is a **shift**, multi-day is a **break** - and says the interchange is other people's error. **When reading ep02's step 4, read "shift".**
- **Refines ep02's entry:** ep02 entered anywhere in the gap [29:21]. Here it is sharpened to the **order block's opening price inside the gap**, as a limit order [25:23].
- **Extends ep02's session note:** ep02 gave 8:30-11:00 [42:40]. Here that is extended to noon with a hard prohibition after it [34:01].

### ep04 - Two worked examples, and the first explicit NO-TRADE

- **Refines ep02 and ep03 with a hard filter:** the fair value gap is not merely the *entry location*, it is a **necessary condition**. Ep02 [43:42] implied it; here it is used twice to reject an otherwise-complete setup [01:44], [06:40]. **A backtester must treat "no FVG" as no-trade, not as "enter at the structure break".**
- **Adds to ep03's timeframe cascade:** ep03 said 3/2/1-minute for execution [28:03]. Here the *start* is named: **5-minute** [06:13].
- **Sharpens ep04's view of 8:30:** ep02 called 8:30-11:00 the window [42:40]; ep03 called 8:30 the start of hours [33:51]. Here 8:30 is given a *function* - it is when the stop hunt fires [03:05].

### ep05 - "Intraday Order Flow and Understanding the Daily Range"

- **Refines ep03 hard.** Ep03 [23:55] made the order block the entry, requiring three conditions. Here he says [07:21] he will `stay away from order blocks` and [36:52] `you don't need an order block`. **These are not compatible as equal emphasis.** The reconciliation he gives: the order block is real but optional; the **fair value gap is the primary entry** because it repeats more.
- **Adds the missing filter to ep02/ep04.** Ep02's step 4 was "break in market structure"; ep04 gated on "is there a gap". Neither said the break must be *violent*. Displacement [18:44] is that gate, and it retroactively explains ep04's anemic rejections.
- **Extends the no-trade rule.** Ep03 [34:01] said no trades after noon. Here it is sharpened: noon-1:00 is forbidden [10:04], but **1:30-4:00 is explicitly tradeable** [32:24] - which ep03 had called out-of-scope [34:33]. He changed his mind and says so: [11:30] `I wasn't going to teach that, but because I see a lot of nonsense on YouTube, I'm going to`.

### ep06 - "The Market Efficiency Paradigm and Institutional Order Flow"

- **Resolves ep05's displacement vagueness - partially.** Ep05 defined displacement only by analogy. Here a **testable criterion** is added: the candle must **close** beyond the level [19:26], not merely wick through [21:20]. Still no magnitude threshold, but "closes beyond" is codeable.
- **Sharpens ep02's entry from a zone to a price.** Ep02 [29:21] said sell when price goes `right up inside that area`. Here it is a **limit order one tick above candle 3's high** [35:55].
- **Answers ep02's target question properly.** Ep02 said `nearest old low or imbalance` [48:02]. Ep06 splits it: **internal** range FVG = partial; **external** range stops = the trade's target [45:52].
- **Confirms ep05's de-emphasis of order blocks.** The full specification here uses **no order block at all** - only liquidity run, displacement, FVG.

### ep07 - "Daily Bias and Consolidation Hurdles"

- **He uses an order block, having said he would not.** [20:23] `I went in at 14,505, that's inside of this order block`, immediately followed by [20:25] `I promised I wasn't going to teach order blocks that much in this mentorship`. Ep05 [36:52] said `you don't need an order block`. **He trades with one here.** Third data point in an unresolved thread - log it, do not smooth it.
- **Refines ep02's weekly bias into a daily one.** Ep02 [13:04] set bias from the weekly candle. Here the working unit is the **daily** draw [07:35], with the same "expand higher or lower, not predicting the close" logic.
- **Adds the missing case to every prior episode: what if there is no setup?** Ep02-06 all assume a readable market. [10:41] is the first guidance for consolidation: smaller timeframes, liquidity only, reduced size.
- **Qualifies ep06's "every single trading day this pattern forms".** Here: [41:28] `it may not be in your asset, it may not be in your particular market, but it exists` - the daily occurrence is across the three indices, not within one.

### ep08 - "Applying Institutional Order Flow to Forex Markets"

- **Extends the model's domain in two directions at once.** Every prior episode is intraday index futures. This one proves the same rules run on **forex** and on the **daily** timeframe [01:22]. Nothing in the procedure changes - which is evidence the model is about liquidity structure, not about a market.
- **Adds a target method ep02-07 lacked.** Those all target opposing liquidity inside a known range. [08:15] handles the case where `we don't have a range to trade inside of` - standard deviation -1.
- **Session times differ from the index sessions, and both are his.** Indices: 8:30-11:00 (ep02, ep05). Forex NY killzone: **07:00-10:00** [05:38]. Not a contradiction - different asset class - but a backtester must not apply the index window to forex.

### ep09 - "Power Three: Accumulation, Manipulation, Distribution - and New York PM Session"

- **Refines the order block definition from ep03.** Ep03 [24:28] defined it abstractly as `a change in the state of delivery`. Here it is given a **recognisable shape**: the run of consecutive close-candles immediately preceding a displacement that leaves an imbalance [07:31]. Same idea, now findable on a chart.
- **He uses order blocks again, freely.** Fourth data point. Ep05 [36:52] `you don't need an order block`; here they appear in the confluence stack [06:40] and as the bonus setup [27:11]. **The honest reading across ep03/05/07/09: the order block is part of how he actually trades, and the "you don't need it" line means the FVG alone is sufficient for a beginner - not that he avoids them.**
- **Softens ep06's geometry.** Ep06 gave hard gap boundaries. Here [25:34] price trading *through* the gap does not invalidate it, judged on **candle bodies**. A backtest using strict gap boundaries will stop out of trades he holds.
- **Adds the missing "when not to trade" to ep05's day structure.** Ep05 forbade noon-1:00. This adds a **whole-morning veto** conditional on overnight range [15:15].

### ep10 - "Implementing Economic Calendar Events with the Open"

- **Supersedes ep07's bias method with a better one.** Ep07 [07:35] framed bias as "where is price drawing to". Here it is sharpened to a question about **the daily candle relative to its own open** [18:00], which is both more precise and directly codeable.
- **Gives the Judas swing a measurement.** Ep09 named it [03:33]. Here it becomes the **input to the opening range** [14:08] - the fake move is not just a warning, it is the ruler you measure the day with.
- **Confirms ep05's 3-candle swing and rejects wider definitions explicitly.** [20:31] naming the Williams fractal as wrong is unusually specific for him.
- **Refines ep02's "8:30-11:00" from a session into an anchor.** Here 8:30 is the **opening price** that the whole day's geometry hangs from [13:33], not merely the start of trading hours.

### ep11 - Market structure nesting, and which opening price to use

- **Resolves an ambiguity, not a contradiction.** Ep09 [06:26] and ep10 [13:33] both anchor on 8:30 without qualification. Ep11 [07:44] says that is correct **for the morning session only**, and the **midnight** open governs the daily range. Any backtest of the ep10 opening range must pick the right one for the timeframe it is testing.
- **Deepens ep05/ep10's three-candle swing.** Those defined a swing. This one **stacks** them into a hierarchy [10:39], which is what makes "which high matters" answerable rather than arbitrary.
- **Reinforces ep09's tolerance.** Ep09 [25:34] said a wick through a gap does not invalidate it. Here the same principle governs entry [09:08] - bodies confirm, wicks are ignored.

### ep12 - "Market Structure for Precision Technicians"

- **Settles the order block question that has run since ep03.** Ep03 defined it abstractly, ep05 said `you don't need` it, ep07/09 used one anyway. Here he gives the definitive form - **a consecutive series** [44:02] - and attacks the single-candle version directly. **Read this as the authoritative statement; ep05's dismissal was about beginner sufficiency, not about validity.**
- **Adds the invalidation the corpus was missing.** Ep02-11 give stops but almost no *idea-invalidation*. [41:54] gives one: a short-term high exceeding the intermediate-term high cancels the thesis. This is the single most useful addition for a backtester after ep06's geometry.
- **Refines ep11's nesting with a mechanism.** Ep11 classified swings by shape. Ep12 says the **rebalance event** creates the classification [13:24] - a cause, not just a pattern.
- **Contradicts the ep02/ep06 requirement for a structure break.** [37:12] `I don't need a swing low broken` for the aggressive entry. Ep02's step 4 and ep06's step 3 both require it. **Both are his: the aggressive entry trades structure without confirmation, the classic waits for it.** Two models, not one.

### ep13 - "Advanced Price Action Theory in Action"

- **Reduces ep03's order block to a formula.** Ep03 [23:55] gave three conditions (gap, liquidity taken, structure shift). Ep13 [18:11] gives three *different* ones: **gap + close-candle + narrative**. The structure shift is replaced by *narrative/draw*. **These are not the same test** - ep03 requires an event to have happened, ep13 requires a directional thesis. Log both; ep13 is later and stated as the definitive determination.
- **Confirms ep12's order flow rule and makes it operational.** Ep12 [48:38] stated it; here it is used as the live reason not to exit [22:56].
- **Extends the Judas swing to 9:30.** Ep09 placed it in London and New York session [03:33]; ep10 anchored it to the 8:30 open. Here 9:30 - the *equities* open - produces its own [18:53]. **Three different Judas anchors now exist across the corpus.**

### ep14 - A single live execution, narrated

- **Supplies the money-management mechanics the corpus keeps gesturing at.** Ep06 [45:52] said `partials - internal range; external range - your trade` but never said *how much*. Here: **half the position**, at the first objective, then **stop to breakeven** [03:02]. First concrete scale-out ratio in the corpus.
- **Consistent with ep07's use of a correlated market**, but weaker - here ES is a confidence check [03:36], not the entry trigger it was in ep07 [22:00].
- **Shows discretion overriding the plan.** He exits early against his own stated target because of proximity to the gap [03:52]. **A backtest cannot reproduce this**, and it is worth noting that his live results include such overrides.

### ep15 - Vacation-month live entry at the 9:30 open

- **Directly qualifies ep09's gap-tolerance rule.** Ep09 [25:34] said a wick through the gap does not invalidate it, judged on bodies. Here he goes further - price took out the swing low *entirely* and he stayed, justified by **narrative** [03:21], not by candle bodies. **This is the loosest invalidation standard anywhere in the corpus.**
- **Contradicts his own stop discipline.** Ep06 [36:07], ep09 [22:05] and ep12 [42:45] all specify a resting stop. Here there is none [04:46]. He flags the inconsistency himself and restricts it to the 9:30 open.
- **Adds a session-level risk rule the setup episodes lack.** [06:42] one loss -> done for the day; [08:46] monthly target hit -> done for the month. Together with ep13 [02:05] (uncertain conditions -> don't trade live), this is now a consistent pattern: **he stops trading far more readily than any "setup" episode implies.**

### ep16 - Multiple setups per session, and how to actually anchor the Fibonacci

- **Completes ep12's targeting method.** Ep12 [32:53] gave `-1.5 standard deviation` anchored intermediate-term-high to long-term-low, settings unspoken. Ep16 supplies **the anchoring rule in words** - highest/lowest **body** [09:07]. Together these are now *nearly* reproducible; only the numeric Fib levels remain visual-only.
- **Confirms ep11's two opening prices** [05:32] and adds that the candle interval is irrelevant - only the 8:30 timestamp matters.
- **Consistent with ep09/ep11's body-over-wick principle**, now extended from *invalidation* to *measurement*. This is the third distinct use of the same idea: bodies confirm entries (ep11), bodies define invalidation (ep09), bodies anchor projections (ep16). **Treat "bodies, not wicks" as a corpus-wide rule.**
- **Adds a hard trade-count limit** [17:26] that no earlier episode states. Combined with ep15's one-loss-then-stop and ep13's monthly cap, his risk framework is materially tighter than the setup episodes imply.

### ep17 - The model on Forex, and the "use the lower open" rule

- **CONTRADICTS ep12 on the order block, directly.** Ep12 [44:02] was emphatic: `the order block is one consecutive series of up closed candles - **it's not the last candle before the down move** ... stop teaching that`. Here, twice: [11:10] `displacement, fair value gap, **last up close candle** touches it - there's your bearish order block`, and [16:49] `bearish order block, **last up close candle**, the body`. **Five days apart, both his.** The reconciliation that fits the evidence: the *series* is the full order block zone, and the *last* candle is the practical touch-point / entry edge within it. But he does not say that - he states each as the definition. **Log as contested; do not pick one silently.**
- **Refines the body-over-wick rule again.** [16:39] `I don't like to use these long tails and wicks ... I prefer to look to price returning back to **the body** of the candle`. Fourth consistent use of bodies-over-wicks (entries, invalidation, projections, now order-block edges).
- **Adds a target-selection criterion the earlier episodes lacked.** Ep12 and ep16 produced Fib levels but chose among them by narrative. Here the tiebreaker is explicit: **coincidence with an institutional price level** [06:46].
- **Confirms ep11's two-opens distinction and then supersedes it with a decision rule.** Ep11 said which open governs which timeframe. Ep17 says what to do when both apply: **take the lower (bearish) / higher (bullish)** [18:56].

### ep18 - The chart layout, and previous day's highs and lows

- **Adds a target layer the corpus was missing.** Ep02 [48:02] said nearest old low/imbalance; ep06 [45:44] said external range liquidity; ep16 [11:30] said the Fib/order-block convergence. **None of them said "previous day's high and low"** - which is simpler, always available, and is what he actually frames the day with here [18:12].
- **Softens the R:R framing throughout the corpus.** Ep09 [22:48] worked a ~3.5:1 example. Here he says R:R is not required at all [13:34]. Not a contradiction of the arithmetic, but a correction of emphasis: **his edge claim is directional accuracy plus liquidity targets, not a reward ratio.**
- **Materially qualifies every live-account result shown since ep02.** [10:40] Some executions exist to demonstrate psychological points for paying students, not because a setup was present. **Any attempt to evaluate the model from his account statements must account for this**, and he says the statements `[10:55] isn't going to mean anything to you unless you understand what I'm really illustrating`.

### ep19 - The longest episode: nested Power Three, and when to do nothing

- **Supersedes ep17's lower-of-two-opens rule with a cleaner one.** Ep17 [18:56] said take the *lower* open when bearish. Ep19 [96:46] gives the reasoning and the general form: **midnight governs unless it is no longer a factor, then 8:30 is the last ditch** - and the strongest signal is price below *both*. Compatible, but ep19 explains *why* and is more general.
- **Adds a second Judas swing the earlier episodes conflated.** Ep09/ep10/ep13 all referred to "the" Judas swing at 8:30 or 9:30. Ep19 says there are **two, nested**: the daily one below midnight and the session one below 8:30 [99:39]. **This resolves the "three different Judas anchors" problem flagged in ep13.**
- **Reinforces and extends the do-nothing rule.** Ep13 [02:05] skipped live trading for a month; ep15 [06:42] one loss then done; ep16 [17:26] max four trades. Ep19 goes furthest: **entire markets left alone for months** [61:41].
- **Qualifies the "every single day" claim** made in ep06 [22:05] and ep07 [41:28]. Here [98:03] it explicitly means *across markets*, not within one.

### ep20 - The London setup he called the night before

- **Sharpens displacement into a testable condition.** Ep05 gave the elephant analogy; ep06 added "must close beyond"; ep20 adds the decisive one: **the next candle must OPEN AWAY from the gap, not at it** [12:39]. That is fully codeable and it is the first criterion that disqualifies a gap on *structure* rather than on feel.
- **Confirms ep07's intermarket method and inverts its role.** Ep07 used ES as an entry *trigger* for NQ. Here DXY is a **barometer** that identifies a *false breakout* in EUR [10:46] - i.e. a filter, not a signal. Consistent with the ep07 warning that correlation confirms rather than generates.
- **Tightens the risk numbers again.** Ep07 [04:52] said students should risk under 1%. Ep20 [15:47] makes 1% the stated **maximum** with 0.25-0.5% preferred. His own 3.5-4.5% (ep03, ep07) remains a separate, personal figure.
- **He explicitly walls this off from the model.** [03:11] `this is **not** the model for my daughter, this is **not** an addition to the model - I'm just answering questions`. **Do not fold the London/forex material into the core spec on the strength of this episode.**

### ep21 - Risk on / risk off, and what it means when the Judas swing never comes

- **Confirms ep19's nested Power Three and assigns the sessions explicitly.** Midnight -> London + daily range; 8:30 -> New York session [13:21], [16:07]. Ep19 established the nesting; ep21 names which session each anchors.
- **Adds a *negative* reading of the same structure.** Every prior episode uses the Judas swing as the setup. Ep21 uses its **absence** as information about trend strength [17:24]. **This is new and it inverts the logic** - the same observation now produces a conclusion whether it happens or not.
- **Adds order-block internal levels.** Ep03/ep12/ep13 treated the order block as an opening price or a candle series. Ep21 gives it **four levels** - low, open, mean threshold, high - with the high least likely to be reached [05:02].
- **Reinforces the honest-error thread.** Ep13 (skipped the month), ep15 (no stop), ep18 (demonstration trades), ep20 (slept through it), ep21 (wrong about the rally, missed $10k to a school run). **Cumulatively this is a consistent and unusually candid record of the gap between the model and its operator.**

### ep22 - Narrative, finally defined

- **TWO DEFINITIONS OF PREMIUM/DISCOUNT NOW EXIST, AND THEY CAN DISAGREE.** - **Range-based** (ep02 [35:47], ep04, ep10, ep16): above/below the **50% of a dealing range**. - **Liquidity-based** (ep22 [11:30]): above an **old high** / below an **old low**. These are not the same test and can point opposite ways - price can be above an old high (short-term premium) while still below the 50% of a larger range (discount). **Log as contested.** The reconciliation that fits: the range definition is *positional* within a dealing range; the liquidity definition is *event-based* and short-term. He uses both in this same episode - the range one at [10:23], the liquidity one at [11:03].
- **Defines the term that ep07, ep12, ep13, ep15, ep16 and ep19 all leaned on.** Every one of those used `narrative` as the deciding factor. [12:20] is the definition; **backfill it into all of them.** In particular ep13's order-block formula (gap + candle + *narrative*) becomes far more tractable: the third term is now *climate + calendar + volatility*, which is at least partially codeable.
- **Refines the stop rule.** Ep06 [36:07] said above candle 1 or 2; ep12 [42:45] said above the swing high. Ep22 [17:47] resolves it as a **minimum** (above the gap-creating candle) and a **preference** (above the swing high) - and explicitly argues *for* the wider stop [18:02].

### ep23 - Live FOMC, and the vocabulary he has been using precisely all along

- **Resolves the wicks/bodies question that has run since ep16.** Ep16 [09:07] said anchor on bodies, emphatically - `the wicks and the tails are all distractions`. Ep23 [12:14] gives the **exception**: on high-volatility scheduled events, use the extremes. **Not a contradiction - a conditional rule that ep16 stated unconditionally.** Backfill: ep16's rule is the default, ep23 supplies the switch.
- **Sharpens all prior uses of "run" and "sweep".** [04:40] They are distinct predictions: a **sweep** implies reversal (the ep02-06 liquidity-raid setups), a **run** implies continuation. Re-reading earlier pages with this distinction changes what some passages mean - e.g. ep02's `run above the old high` before a reversal is properly a **sweep**.
- **Adds an explicit exclusion to the trade count.** Ep16 [17:26] capped the day at four trades. Here he counts **eight** available setups but stresses you take only the ones matching your own model [15:00]. **Not a contradiction: eight exist, you take one or two.**
- **Confirms institutional order flow as the hold rule** [16:18], consistent with ep12 [48:38] and ep13 [13:37].

### ep24 - The setup that didn't form, and why that proves the model

- **Supplies the trigger-selection rule that ep02-23 left implicit.** Which short-term low? [32:53] answers it: **the nearest one to the left, identified the moment the highs are run.** Every prior episode says "a short-term low" without saying which. This is directly codeable and removes a real ambiguity.
- **Confirms ep20's displacement disqualifier from the opposite direction.** Ep20 [12:39] said the gap fails if the next candle opens *at* it. Ep24 [23:27] adds the level-based version: after sweeping a level, price must **displace back through it** - `melting` back is not displacement. **Two independent disqualifiers now exist; both are structural, neither needs a magnitude threshold.**
- **Reinforces the do-nothing thread** (ep19, ep21) with the strongest framing yet: the absence of a trade is *evidence for* the model [17:41], not a failure of it.
- **Restates ep22's point that the entry is the easy part** - here as `price marks where, time marks when` [21:52].

### ep25 - Which liquidity gets taken first, and rebalancing yesterday's range

- **Adds a bias-invalidation test no earlier episode states.** Ep12 [41:54] invalidated on a structure violation; ep24 [23:12] on missing displacement. Ep25 [28:36] invalidates on **sequence**: wrong liquidity first = wrong read. **This is directly codeable and is a filter, not a trigger** - it tells you when to stop looking for shorts today.
- **Adds a daily-scale target that is simpler than any prior method.** Ep16's Fib projection and ep18's previous-day levels both require construction. `The low of the day before a large expansion day` [31:33] is a lookup - and he says it is where the retracement terminates.
- **Reinforces ep21's order-block ranking** - the high of a bearish order block is `the most unlikely level to be traded to` [08:04].
- **Re-states the FVG-over-order-block priority** [08:46], consistent with ep05 [36:52] and ep16, and against the emphasis of ep03. **The corpus is now clearly weighted: the fair value gap is the core; the order block is supporting.**

### ep26 - "Example of Tape Reading Practice" - trading AGAINST his own daily bias

- **He trades against his own bias, which ep18 said bias exists to prevent.** Ep18 [12:12] framed bias as a filter that excludes half the market. Here he takes the excluded side [00:11]. **The reconciling condition is his own:** three failed attempts at sell-side follow-through [04:22]. That is a stated, checkable licence - but it is a genuine exception to the ep18 rule and should be logged as such.
- **Gives the clearest stop-placement *reasoning* in the corpus.** Ep06/ep09/ep12/ep22 all say *where* to put the stop. [05:00] says *why*: it must sit where the structure supporting the idea would be broken - inside the gap's far edge and beyond the relevant short-term high. **That is the generalisable principle behind all the specific stop rules.**
- **Confirms ep21's "no follow-through = information" reading** from the other direction. Ep21: no rally on a bearish day = very heavy. Ep26: **no continuation after taking sell-side = the sellers have failed**, so fade them.
- **First explicit statement that his concepts have become crowded** [10:00]. He is now fading traders using the imbalance idea he popularised. **This has a real consequence for backtesting: the edge he describes may behave differently after 2022 as the pattern became widely known.** Worth flagging in the hypothesis ledger.

### ep27 - "Counter Trend Ideas"

- **Ranks the model's variants for the first time.** [13:45] The **8:30-9:30 session model is the highest-probability form**; counter-trend is a valid but secondary framing. Ep26 took a counter-bias trade without saying where it sat in the hierarchy; ep27 places it. **When the spec is assembled, the 8:30-9:30 version is the primary model and everything else is an extension.**
- **Adds equilibrium as an entry gate.** Ep02/ep16 used the 50% to define premium/discount for *targeting*. [06:58] uses it as a **precondition for entry** - price must be below equilibrium to buy. This is the range-based definition (not ep22's liquidity-based one), used as a filter.
- **Extends ep14 and ep20's honesty about execution.** Ep14 exited early on judgement; ep20 slept through the setup; ep27 fumbled the order type and missed the target price entirely [11:40]. **Three separate episodes where the recorded result diverges from the plan for operational reasons.**
- **Reinforces ep18's phone rule** [12:11] - and here it costs him money, which ep18 only warned about.

### ep29 - SMT gets its name, and the 50%-of-displacement filter

- **Adds a fair-value-gap location filter that no earlier episode states.** Ep06 [20:29] required the gap to be **inside the displacement range**. Ep29 [05:11] tightens it: the gap must be in the correct **half** of that range - **above 50% for a short**, below for a long. **This is strictly stronger than ep06 and it rejects setups ep06 would accept.** Log it as a refinement and test it separately - it is exactly the kind of filter that changes a backtest's trade count materially.
- **Confirms the builder's SMT ruling with the source's own naming.** The concept is now traceable end to end: unnamed in ep07 [24:54], named here [04:29], reused in ep35 and ep38. Its role never changes - confirmation of an existing bias, never a trigger.
- **Formalises "close proximity entries"** which ep10 [15:13] named in passing. Here it is demonstrated with real fills outside the gap and the heat measured [11:00].
- **Adds a volatility-regime rule.** Ep17 said news creates volatility; ep29 [03:15] says the **day before** a Fed speaker suppresses it. Together these bracket the calendar: know when volatility arrives *and* when it will not.

### ep30 - Sweep the lunch lows, then run

- **Turns ep05/ep22's lunch observations into an actionable rule.** Ep05 [10:04] said do not trade noon-1:00. Ep22 [19:05] said expect a retracement after 1:30. Ep30 [11:57] says what to *do* with it: **the lunch lows are the liquidity that fuels the afternoon continuation.** That is a specific, locatable target rather than a time to wait out.
- **Reinforces ep24's non-setup argument with a different shape.** Ep24: the setup never formed, so no trade. Ep30: a **real sell-off occurred** and still produced no qualifying setup [08:03]. **Together they establish that "price moved" and "the model fired" are independent** - which is exactly what a filter is supposed to achieve.
- **Adds 3:00 PM to the intraday clock.** Ep05 had 3:40/3:50/4:00 for market-on-close; ep22 had 1:30 for the PM re-entry. **3:00 PM as the spool toward the day's liquidity target** [05:11] sits between them and is new.
- **Consistent with ep21's honesty about missed fills** - [05:48] he wanted the imbalance entry and was too slow.

### ep31 - "I'm the scout, you're the sniper"

- **Qualifies ep06's "don't rush the stop" rule with a stated exception.** Ep06 [41:26] warned that trailing early gets you stopped out. Ep31 [07:41] trails early and gives the condition: **exceptional volatility**. Both are his; the discriminator is the regime, not preference.
- **Answers the session-only reading of the model.** Ep27 [13:57] said the 8:30-9:30 window is the *highest-probability* configuration. Ep31 [04:55] makes explicit that it is not the *only* one - a fair value gap later in the day is tradeable if the draw is intact. **Consistent, and worth noting: high-probability ≠ exclusive.**
- **Clarifies what his public calls mean** - relevant to how the whole corpus is read. When he points at a level, it is [03:45] `where we're aiming`, not a prediction of support. Several earlier episodes (ep19, ep20, ep24) contain such calls; read them all as **targets**.
- **Reinforces the ep24/ep30 discipline:** he skipped the entire afternoon [09:18] having taken one trade.

### ep32 - Consolidation days, and how to see one coming

- **Adds a day-type classifier the corpus lacked.** Ep19 and ep21 taught recognising a *heavy* day; ep32 [01:36] gives the signature of a **choppy** one, in advance, from two observable facts: outside day + down close, then failure to reach the old low. **Codeable from daily bars alone.**
- **Explains the 3:00 PM spool from ep30.** Ep30 [05:11] observed the 3:00 PM move without a reason. Ep32 [11:32] supplies it: on-close orders, historically anchored to the bond close. **Same phenomenon, now with a mechanism.**
- **Adds "avoid the middle" as an explicit filter.** Ep02/ep16 used the 50% for premium/discount; ep27 used it as an entry gate. Ep32 [04:56] states the consequence directly - **mid-range is where edge decays to nothing.** That is a useful negative rule and it is consistent with the premium/discount logic rather than additional to it.
- **Third documented rejection in three episodes** (ep24, ep30, ep32). The pattern is now firmly established and worth carrying into the spec as a testable expectation.

### ep33 - "If the fair value gap doesn't exist, I don't trust that level"

- **Settles what the levels are FOR.** Across ep02-32 he marks old highs, old lows, relative equal highs, previous-day extremes. Ep33 [12:47] says plainly: those levels **locate liquidity**; they are not tradeable in themselves. **The gap is the trade.** This is the cleanest available answer to the recurring "isn't this just support and resistance?" objection, and it has a direct coding consequence: **no gap, no trade, regardless of how good the level looks.**
- **Adds a volatility-scaled aggression rule.** Ep31 [07:41] trailed stops early because of volatility; ep33 [11:02] demands a *larger structural break* for the same reason. **Consistent principle: volatility raises the evidentiary bar.**
- **Qualifies the premium/discount requirement twice.** First, premium is measured against **whichever dealing range is relevant**, including a 1-minute one [14:33]. Second, when a strong higher-timeframe draw is in play, **the retracement may never reach premium and that is expected** [13:44]. **Both qualifications loosen a rule that ep02/ep27 stated absolutely** - log them, because a backtest enforcing premium strictly will reject valid setups.
- **Fourth consecutive episode with an explicit refusal to trade** (ep24, ep30, ep32, ep33). Here the refusal is *temporal* - not "no setup" but "not yet".

### ep34 - The Sunday gap opening, and the one time he admits to talking retail

- **TENSION WITH EP33, AND HE FLAGS IT HIMSELF.** Ep33 [09:06] was emphatic: `**NOT** go back to the old low broken and act as resistance ... if the fair value gap doesn't exist, I don't trust that level`. Ep34 [09:33] then teaches the Sunday gap opening as **dynamic support and resistance** and jokes about the blasphemy. **The reconciliation that fits the evidence:** in ep34 he never enters on the level alone - every entry still requires a fair value gap or order block *at* the level [07:03]. So the Sunday gap **locates** the reaction, consistent with ep33's `the level highlights where the liquidity would be`. But he does describe it in support/resistance language, and the two episodes are one day apart. **Log as contested; note the reconciliation but do not treat it as settled.**
- **Adds a weekly-scale level the corpus lacked.** Everything prior is daily (ep18's previous-day extremes, ep25's pre-expansion low) or intraday. The Sunday gap is the first **weekly** reference, and it costs nothing to plot.
- **Defines "sloppy" after using it for 30 episodes.** [07:34] - and importantly decouples it from profitability: a move can deliver and still be untradeable by his mechanics.
- **Consistent with ep32's consolidation-day framing** - both say the choppy environment needs different tools, and both point to specific structural levels rather than momentum.

### ep35 - Mean threshold, and why some reversals never happen

- **Completes ep21's mean threshold.** Ep21 [05:02] listed it among four order-block levels with no definition. Ep35 [00:56] defines it as the 50% of the order block candle **and gives it a signal**: taken = continuation likely. **Now codeable.**
- **Sharpens ep07's and ep29's SMT warnings into a mechanism.** Ep07 said divergence alone blew his accounts; ep29 said it confirms an existing bias. Ep35 [07:36] explains *why it fails*: **the divergence can simply disappear** as the instruments re-converge. That is a concrete failure mode and it explains the earlier warnings rather than repeating them.
- **Adds a reversal-rejection filter no earlier episode provides.** The corpus is rich in entry filters; [12:02] is the first that says **when not to expect a turn at all** - because the structural cost of reversing is too high. It pairs naturally with ep12's institutional order flow (opposing-close candles as speed bumps): the more of them stacked, the higher the resistance.
- **Reinforces ep33's premium/discount flexibility** with the ladder [10:19] - each new dealing range redefines discount, so "discount" is continuously re-measured as the move develops.

### ep36 - "No model entry here - that's telling"

- **Third and strongest form of the "no setup" argument.** Ep24 [17:41]: absence proves the model filters. Ep30 [08:03]: a real sell-off produced nothing. Ep36 [05:57]: **the absence itself is directional information** - a move without a setup is a move in a hurry, and that urgency tells you what it is doing (clearing liquidity) and therefore what comes next. **This is the most sophisticated use of a rejection in the corpus.**
- **Answers "which structure shift?" - a genuine ambiguity across ep02-35.** [05:19] The answer is procedural: **define your dealing range first**, and the shift is the one that breaks inside it. Every earlier episode assumed the reader would pick the right one.
- **Adds a weekly stopping rule to the risk framework.** The corpus already had: max 4 trades/day (ep16), one loss then stop (ep15), monthly target then stop (ep13, ep15), skip the day after an overnight run (ep09). **Done by Wednesday** [08:04] is the weekly-scale version, and the stated reason is the absence of a clear objective, not a profit target.
- **Adds a news-window inference.** [05:45] If 8:30 did not produce the expected move, do not expect it later. **Consistent with ep17's treatment of news as a timing device rather than an information source.**

### ep37 - The breaker, defined - and why he stops trading on Wednesday

- **He now uses a breaker, having excluded it from the model.** Ep03 [37:23] listed `no breakers` as evidence the model was stripped down. Ep37 [00:24] identifies one on the daily and uses it as context. **Not a contradiction of substance** - the entry is still the fair value gap - but the exclusion claim from ep03 no longer holds literally. Log it.
- **Completes ep36's Wednesday rule.** Ep36 [08:04] said `done by Wednesday` as personal preference. Ep37 [05:18] makes it a **teaching**, gives the boundary (**Wednesday's NY session**), the measurement window (**from Sunday's open**), and the reason (**precision degrades on NFP-week Thursdays and Fridays**).
- **Provides the corpus's own answer to "is this curve-fitting?"** [10:52] The argument is explicitly empirical: avoid periods where `your **proven walk-forward real trading results** have been diminished`. **He is describing regime selection based on realised performance** - which is exactly what a hypothesis ledger (DECISIONS section 4) is designed to keep honest.
- **Reinforces ep25's "midnight starts the day" with a weekly analogue** - the trading week is measured **from Sunday's open** [11:37], consistent with ep34's Sunday gap level.

### ep38 - Narrative, again - and why the gap does not need to fill

- **Resolves an ambiguity that runs through the whole corpus: how much of the gap must fill?** Ep06 gave exact boundaries; ep09 tolerated wicks through; ep33 required the gap to exist. Ep38 [05:24] settles it: **entering the gap at all is sufficient** - `coming down into this area, or inside this area`. **Full rebalance is explicitly not required**, and he names it as the difference between his method and Chris Lorie's. **Coding consequence:** the entry trigger is *touch of the gap's near edge*, not fill to the far edge. A backtest requiring full fill will miss most of his entries.
- **Second definition of narrative, compatible with the first.** Ep22 = inputs; ep38 = structure. Together they make the term operational: **state the expectation, state why, and enumerate the confirmations you would need to see.** That third part is new and is the most testable component - it turns narrative into a checklist rather than a feeling.
- **Adds bias-abandonment criteria the corpus lacked.** Ep18 [12:01] said hold the bias `unless you're proven clearly that you're absolutely wrong` without saying what that looks like. Ep38 [03:46] gives a concrete signature: **repeated liquidity taken + no qualifying setup + the objective never reached**. And crucially [03:00], the correct response is often **the sidelines, not a reversal.**
- **Consistent with ep33 on support/resistance, with one honest concession.** [10:00] `this is one of the instances where resistance broken turns support - **but it digs a little bit past that**`. He immediately reframes [10:14]: `I'm not looking at support and resistance, I'm looking at the fact that we went through this short-term high, **created an imbalance**, and then traded into that`. **The imbalance is still the object; the level is still just its location.**

### ep39 - The four times of day, and a backtest he tells you to run

- **Names the setup times explicitly for the first time.** The clock has been assembled piecemeal across ep02-ep36. [73:10] states it as a list: **8:30, 9:30, afternoon, 3:00-4:00**. Everything else in the corpus is consistent with it; this is the compact statement.
- **Adds a hold rule tied to the clock rather than to structure.** Ep06 [41:26] and ep12 [48:38] tied holding to structure and candles. [11:52] adds: **hold until the delivery window (3:00-4:00)**, because that is when the daily range completes. **A time-based exit condition, which the corpus otherwise lacks.**
- **Explicitly corrects a widespread misreading of his own work** [06:27] - that equal lows always reverse. **Relevant to the corpus: several earlier episodes could be read that way in isolation.** He says narrative decides, not the pattern.
- **Consistent with every stopping rule so far** and adds the per-loss version [79:56]: after a loss, stop for the day; do not chase.

### ep40 - Weekly expansion over daily bias, and the 10-11 exit

- **Substantially revises the daily-bias teaching of ep07, ep10 and ep18.** Those built a *daily* bias from the daily chart. Ep40 [20:44] says attempting that **every day** is unrealistic and that he does not do it - he forecasts the **weekly expansion direction** and lets the day resolve within it. **This is the most significant late revision in the corpus.** It does not invalidate ep10's opening-range mechanics, but it changes what those mechanics are applied to.
- **Adds a time-based exit that overrides target-based exits.** Ep02 said take the nearest objective; ep39 said submit to time until 3:00-4:00. Ep40 [17:36] says **most of the position should be off by 11:00**. Read with ep39, the shape is: **80% off by 11:00, remainder held for the 3:00-4:00 delivery.**
- **Turns SMT into a selection tool, not just a confirmation.** Ep07/ep29/ep35 used it to confirm a bias. [46:34] uses it to **choose which instrument to trade** among correlated pairs. New function, same mechanic.
- **Makes the economic calendar the first step, not a caution.** Ep10 and ep17 treated it as a volatility warning. [46:31] makes it the **market-selection filter**: trade where the driver is.

### ep41 - FINAL. Money management, and OTE finally defined

- **Resolves the corpus's biggest open term.** OTE appears from ep01 onward as a component of confluence and is never explained; ep08 [09:06] even points *outside* the corpus for it. [18:55] closes it. **Backfill this definition into every earlier page that lists OTE as confluence.**
- **Reconciles the scattered risk figures into one system.** Ep03/ep07 gave his personal 3.5-4.5%; ep07/ep20 told students 0.25-1%. Ep41 makes it a **ladder**: start at 1%, halve after a loss, quarter after two, and restore only after recovering half the loss. **The student figures were the rungs of this ladder all along.**
- **Contradicts ep15's stopless entry, deliberately.** Ep15 [04:46] traded the 9:30 open without a stop. Ep41 [15:16] says a hard stop is what respecting risk *means*. **Ep15 was framed as an exception at the time; ep41 is the rule.** Take ep41 as authoritative.
- **Completes the gold-standard pattern.** Across the corpus the entry has been stated as: the gap (ep06), the gap + order block (ep13), and here **gap + order block + OTE** [16:36]. This is the final, most-specified form.

