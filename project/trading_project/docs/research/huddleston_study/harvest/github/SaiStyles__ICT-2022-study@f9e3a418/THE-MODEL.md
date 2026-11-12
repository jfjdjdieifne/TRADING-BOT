# THE MODEL

**The 2022 ICT Mentorship, de-linearised.** Assembled from all 40 readable episodes (ep28 excluded by ruling - DECISIONS.md section 19).

Every line traces to `study/ep<NN>.md`, which traces to `transcripts/ep<NN>.md` at a timestamp. **Nothing here is inferred from outside the corpus.** Where two episodes disagree, both are shown and the conflict is marked - never smoothed.

**Reasoned file. No script writes here.** DECISIONS.md section 16.

---

## 0. What he is actually saying

Strip away 24 hours of talking and the claim is one sentence:

> **Price moves between pools of resting orders, on a clock, and the move that takes those orders leaves a signature you can see.**

Everything else is detail. Three consequences follow, and he repeats them in every episode:

1. **Direction comes from where the orders are** (old highs, old lows, imbalances) - never from indicators, patterns, or "pressure". `it's drawing to one of two things: stops, or an imbalance` (ep02 [21:30]).
2. **Timing comes from the clock**, not from price. `algorithms, the first element they operate under is time` (ep06 [23:23]).
3. **The entry is the least important part.** `[the entry] is the easiest thing out of all the learning` (ep22 [02:24]). What is hard is knowing where price is going and refusing everything else.

**The single most repeated behaviour across 40 episodes is not entering. It is declining.** Nine separate episodes are built around a trade not taken.

---

## 1. THE MODEL, in order of operations

### Layer 1 - Before the week

| # | step | source | status |
|---|---|---|---|
| 1.1 | **Pick the market from the economic calendar.** Trade where the high/medium-impact driver is. Markets without one will be lackluster | ep40 [46:31], [21:58] | confirmed |
| 1.2 | **Forecast the WEEKLY expansion, not a daily bias.** `every day bias is unrealistic` | ep40 [20:44], [21:29] | **refines ep07/ep10/ep18** |
| 1.3 | On the weekly chart ask: running to an old low? an old high? an imbalance above or below? or no data this week -> expect nothing | ep40 [21:34] | confirmed |
| 1.4 | Note the **seasonal tendency** (e.g. late-April into May = index weakness) | ep25 [12:29] | contextual |
| 1.5 | Plot **Sunday's opening gap** across the week - above it acts as support, below as resistance | ep34 [09:44] | **contested - see 7.3** |

### Layer 2 - Before the day

| # | step | source | status |
|---|---|---|---|
| 2.1 | Daily chart: locate the **draw on liquidity** - the next pool price must reach | ep02 [16:42], ep07 [07:35] | confirmed |
| 2.2 | Establish the **dealing range** (significant high to low); Fib it; mark **equilibrium** | ep02 [35:22] | confirmed |
| 2.3 | Mark **previous day's high and low, for the last 3 days** - these are the intraday targets, *not* the daily draw | ep18 [18:12], [19:16] | confirmed |
| 2.4 | After a large expansion day, the retracement target is **the low of the day before it** | ep25 [31:33] | confirmed |
| 2.5 | Bias holds **until the draw is reached** | ep07 [07:45], ep10 [22:44] | confirmed |
| 2.6 | Check day type: **outside day + down close, then failure to reach the old low = expect chop** | ep32 [01:36] | confirmed |

### Layer 3 - The day's shape (Power Three)

**Accumulation -> Manipulation -> Distribution** (ep09 [02:50]). For a bullish day: opens near the low, fakes down, rallies, closes near the high. Inverted for bearish.

**It is nested.** Two Judas swings at two scales (ep19 [99:39]):

| anchor | governs | source |
|---|---|---|
| **Midnight NY open** | the daily range + London session | ep11 [07:44], ep21 [13:21] |
| **8:30 open** | the New York session - `last ditch for power 3` | ep19 [96:46], ep21 [16:07] |

**Selection rule:** midnight governs unless it is stale; then 8:30. When bearish, use whichever is **lower**; bullish, whichever is **higher** (ep17 [18:56]). **Best case: price below both** = maximum discount (ep19 [96:58]).

**The opening range** (ep10 [13:30]): measure open->high (the Judas), project that distance **below** the open. He claims *every* short setup forms in that zone. **Falsifiable and worth testing directly.**

### Layer 4 - The setup

The sequence, bearish (invert for bullish). **Order matters.**

| # | condition | source |
|---|---|---|
| 4.1 | **Buy-side liquidity taken first** - price runs above an old high / relative equal highs | ep02 [43:13] |
| 4.2 | *(filter)* If sell-side is taken first instead, **the bearish read is void** - skip the day | ep25 [28:36] |
| 4.3 | Find the **nearest short-term low to the left**, the moment the highs are run - that is the trigger level | ep24 [32:53] |
| 4.4 | That low breaks, **with displacement** | ep02 [28:00], ep05 [18:44] |
| 4.5 | A **fair value gap** forms in the displacement leg | ep06 [20:29] |
| 4.6 | Price returns into the gap -> **entry** | ep02 [29:21] |

### Layer 5 - The four gates

**A setup must pass all four. Each is structural - none needs an invented threshold.**

| gate | test | source |
|---|---|---|
| **G1 Displacement closes** | the break must **close** beyond the level, not wick | ep06 [19:26], ep24 [23:12] |
| **G2 Moves away** | the candle after the gap must **open away** from it, not at it | ep20 [12:39] |
| **G3 Inside the leg** | the gap must sit **within** the displacement high/low | ep06 [20:29] |
| **G4 Correct half** | the gap must be in the **upper half** of the displacement leg (for a short) | ep29 [05:11] |

**No gap = no trade.** Stated as a refusal twice in ep04 [01:44], [06:40] and again in ep33 [09:23]: `if the fair value gap doesn't exist, I don't trust that level`.

### Layer 6 - Entry: the gold standard

> **Fair value gap + order block + optimal trade entry** - ep41 [16:36] `the gold standard of the ICT pattern`

| component | definition | source |
|---|---|---|
| **Fair value gap** | 3 candles; bearish: upper = c1 **low**, lower = c3 **high**, gap on c2. Bullish mirrored | ep06 [16:48], [22:56] |
| **Order block** | **a consecutive series** of same-direction close candles before a displacement that leaves an imbalance - *not* the last candle | ep12 [44:02], ep09 [07:31] |
| **Order block levels** | low / open / **mean threshold (50%)** / high - the far edge least likely to be reached | ep35 [00:38], ep21 [05:02] |
| **OTE** | the **62-79% retracement**, below equilibrium | ep41 [18:55] |

**Entry mechanics:** limit order **one tick beyond candle 3** (ep06 [35:55]). **Touching the gap is enough - full fill is not required** (ep38 [05:24]). **Close proximity entries** near but outside the gap are acceptable (ep29 [07:07]).

### Layer 7 - Stop

**Principle** (ep26 [05:00]): the stop belongs where **the structure that justified the trade** would be broken.

| form | rule | source |
|---|---|---|
| minimum | above the candle that created the gap | ep22 [17:47] |
| preferred | above the swing high (candle 1) | ep06 [36:07], ep12 [42:45] |
| **A hard stop is required** | `if you don't put a hard stop in you're not really respecting the risk` | ep41 [15:16] |

**Judged on bodies, not wicks.** A wick through the gap does not invalidate it (ep09 [25:34], ep11 [09:08], ep22 [08:59]).

### Layer 8 - Targets and exits

| target | rule | source |
|---|---|---|
| **Partials** | at **internal** range liquidity (the gap inside the range) | ep06 [45:33] |
| **Main target** | **external** range liquidity - stops beyond the range | ep06 [45:44] |
| **Nearest first** | `low hanging fruit is how I teach` | ep02 [48:09] |
| Previous day's high/low | the practical intraday objective | ep18 [18:12] |
| Fib projection | anchor **highest/lowest BODY** (wicks on high-volatility days), take the level coinciding with an institutional level (00/20/50/80) | ep16 [09:07], ep23 [12:14], ep17 [05:15] |

**Exit timing:**

| # | rule | source |
|---|---|---|
| 8.1 | **80% of the position off between 10:00 and 11:00** - London close creates the opposing end of the daily range | ep40 [17:36] |
| 8.2 | Remainder: **submit to time**, hold for the 3:00-4:00 delivery | ep39 [11:52] |
| 8.3 | Scale-out observed: **half at the first objective, then stop to breakeven** | ep14 [03:02] |
| 8.4 | Do **not** trail early - use the partial to quench the urge | ep06 [41:26] |
| 8.5 | Exception: trail early when volatility is exceptional | ep31 [07:41] |

### Layer 9 - Risk

**Position sizing** (ep41 [22:12]): `equity x 1% / stop-distance-in-points / point-multiplier = contracts`.

**The risk ladder** - the most mechanical rule in the corpus:

```
risk = 1%
after a loss:                 risk = risk / 2      (floor 0.25%)
after recovering 50% of loss: risk = 1%
```

Three straight losses cost **1.75%**, not 3% (ep41 [34:22]). His own trading uses 3.5-4.5% (ep03 [49:07]) - **that is not what he tells students** (ep20 [15:47]).

---

## 2. THE CLOCK

Everything above is gated by time. All New York.

| time | what happens | source |
|---|---|---|
| **Midnight** | new day begins; opening price for the daily range | ep25 [26:07], ep11 [07:44] |
| **02:00-05:00** | London killzone | ep03 [32:59] |
| **07:00-10:00** | New York killzone (**forex**) | ep08 [05:38] |
| **08:30** | news embargo lifts; session opening price; `that starts the hunt` | ep04 [03:05], ep10 [01:42] |
| **08:30-09:30** | the setup forms or is framed here | ep25 [34:43] |
| **09:30** | equities open; **first move is usually the wrong one** | ep06 [33:16], ep13 [18:53] |
| **08:30-11:00** | index trading hours; **the highest-probability window** | ep02 [42:40], ep27 [13:57] |
| **10:00-11:00** | **London close - take 80% off** | ep40 [17:36] |
| **12:00-13:00** | New York lunch. **No entries.** Its lows/highs are built as liquidity | ep05 [10:04], ep30 [11:57] |
| **13:30** | PM session begins; an algorithm macro runs | ep05 [32:35] |
| **15:00-16:00** | on-close macro (historically the bond close); the consolidation-day setup | ep32 [11:32] |
| **15:40 / 15:50 / 16:00** | market-on-close acceleration | ep05 [26:53] |

**The four setup times, named:** 8:30, 9:30, afternoon, 3:00-4:00 (ep39 [73:10]).

---

## 3. WHEN NOT TO TRADE

**This is half the model.** Nine episodes are built around a refusal.

| condition | action | source |
|---|---|---|
| Big overnight run | **skip the whole NY morning**; wait past 13:00 | ep09 [15:15] |
| Noon-13:00 | no entries (partials allowed) | ep05 [10:04], ep16 [22:15] |
| No fair value gap | no trade | ep04 [01:44] |
| Displacement absent / anemic | no trade | ep24 [23:12] |
| Sell-side taken before buy-side (bearish) | day void | ep25 [28:36] |
| Price at mid-range | 50/50 - stand aside | ep32 [04:56] |
| Reversal would break many supportive candles | **high resistance liquidity run** - reject | ep35 [12:07] |
| Chart is `sloppy` - few options, no entry mechanics | close the charts | ep19 [61:04], ep34 [07:34] |
| Cannot state where price goes next | `you're gambling` | ep19 [64:56] |
| One loss | done for the day | ep15 [06:42] |
| 4 trades | done for the day | ep16 [17:26] |
| **Wednesday NY session** | done for the week | ep37 [05:18] |
| Monthly target hit | done for the month | ep13 [02:05], ep15 [08:46] |
| FOMC / NFP days | do not trade - study only | ep23 [15:51], ep37 [04:50] |
| Uncertain macro conditions | stand down entirely | ep13 [02:05] |

**And the argument for why this matters** (ep24 [17:41]): a setup that never formed, and a trade never taken, `is the proof, the evidence that the model has validity`.

---

## 4. READING THE MARKET'S STATE

Signals that classify the day rather than trigger a trade:

| observation | meaning | source |
|---|---|---|
| **No rally above either open on a bearish day** | extremely heavy; no fade will come; take small imbalances or miss it | ep21 [17:06] |
| **A fast move with no setup** | liquidity clearance, not delivery - the real move is still ahead | ep36 [05:57] |
| **Sell-off with no setup** | filters working; wait for the other direction | ep30 [08:03] |
| **Repeated failure to follow through after taking liquidity** | the only licence to trade against the daily bias | ep26 [04:22] |
| **Mean threshold of an order block taken** | continuation likely | ep35 [00:58] |
| **Institutional order flow** - opposing-close candles capping price | the move is intact; hold | ep12 [48:38], ep13 [13:37] |
| **SMT divergence** at 8:30/9:30/news | confirms an existing bias - **never a trigger** | ep29 [04:29], ep35 [07:27] |

---

## 5. VOCABULARY THAT CHANGES MEANING

He uses these precisely. Conflating them inverts predictions.

| term | meaning | source |
|---|---|---|
| **Sweep** | goes just beyond a level, then **reverses** | ep23 [05:32] |
| **Run** | goes through and **continues** | ep23 [05:29] |
| **Market structure shift** | intraday | ep03 [03:22] |
| **Market structure break** | multi-day | ep03 [03:17] |
| **Narrative** | what price should do, **why**, and what must be seen to prove it - from climate, calendar, available volatility | ep22 [12:20], ep38 [08:09] |
| **Displacement** | energetic move that **closes** beyond the level and **moves away** | ep05 [18:44], ep06 [19:26], ep20 [12:39] |
| **Breaker** | low, high, low - the intervening high projected forward | ep37 [00:26] |
| **Internal / external range liquidity** | inside the range (partials) / beyond it (target) | ep06 [45:33] |
| **Sloppy** | few options, entry mechanics absent - even if the move is profitable | ep34 [07:34] |

**Structure is nested** (ep11 [10:39]): short-term high = 3 candles; **intermediate-term** = a swing high flanked by lower swing highs, **or** created by a rebalance (ep12 [13:24]); long-term = one tier up. **He positions against intermediate-term highs.**

---

## 6. HOW HE SAYS TO TEST THIS

His own instruction (ep39 [74:11]):

> Count, over the last week / two weeks / month: **how many setups at these key times of day offered five points?** Then do the math.

Terms are now all defined: the setup (Layers 4-6), the times (section 2), the threshold (5 points). **This is the first entry for the hypothesis ledger** (DECISIONS section 4).

**Economics as he states them** (ep39 [72:27]): ~3 opportunities/day, **one taken live**, 5 points each is enough.

---

## 7. CONTESTED - unresolved, both sides his

Per DECISIONS section 11, a contested claim is a finding. **Do not pick silently.**

### 7.1 Order block: series or last candle?
- **ep12 [44:02]:** `a consecutive series of up closed candles - **it's not the last candle** before the down move. stop teaching that.`
- **ep17 [11:10], [16:49]:** `last up close candle ... there's your bearish order block`

Five days apart. Plausible reconciliation: the series is the zone, the last candle its edge. **He never says so.**

### 7.2 Premium/discount: two definitions
- **Range-based** (ep02 [35:47]): above/below the 50% of a dealing range.
- **Liquidity-based** (ep22 [11:30]): above an old high / below an old low.

**They can point opposite ways, and he uses both in one episode.** Implement as two separate flags. Further loosened by ep33: measured against *whichever* dealing range is relevant [14:33], and skipped entirely when the higher-timeframe draw is strong [13:44].

### 7.3 Levels: tradeable or only locational?
- **ep33 [09:06]:** `**NOT** ... the old low broken acting as resistance. if the fair value gap doesn't exist, I don't trust that level`
- **ep34 [09:44]:** the Sunday gap opening as `dynamic support resistance` - he jokes about the blasphemy himself

His *practice* in ep34 stays consistent with ep33 (he still requires a gap at the level). His *teaching* does not. **Safe implementation: ep33's form.**

### 7.4 Structure break: required or not?
- **ep02 [43:21] / ep06:** the break is step 4 of the setup.
- **ep12 [37:12]:** the aggressive entry - `**I don't need a swing low broken**`

**These are two different systems.** Test separately; pooling hides both.

### 7.5 Order blocks: needed or not?
ep03 makes them the entry; ep05 [36:52] `you don't need an order block`; ep07/ep09/ep13 use them anyway; ep25 [08:46] the FVG is the focus; ep41 [16:36] they are part of the gold standard. **Consistent reading: the FVG is the entry mechanism, the order block is supporting context.**

---

## 8. WHAT CANNOT BE CODED FROM THIS CORPUS

Honest limits. Each is a place a backtester must invent something he never supplied.

| gap | why it matters |
|---|---|
| **Displacement magnitude** | The four gates (5.G1-G4) are structural, but "energetic" has no number. This is the largest discretionary hole and it decides most rejections. **See 8.1 - researched, and the gap is confirmed rather than closed** |
| **"A big overnight run"** | ep09's morning-veto threshold is undefined |
| **Fib level values** | The anchoring is explained (ep16) but the numeric settings are only ever **shown on screen** (ep12 [33:08]) |
| **"Climate"** | One of narrative's three inputs; never explained |
| **Which dealing range** | ep33 permits premium/discount against any relevant range - including 1-minute |

### 8.1 Displacement magnitude - researched outside the corpus, 2026-09-03

`[OUTSIDE]` **Everything in this subsection comes from outside the 2022 corpus.** Researched on the builder's explicit permission. It is quarantined here and must not be read back into any `study/` page as if he said it.

**The finding is negative, and that is the useful part: there is no canonical ICT threshold. The wider ICT/SMC community treats displacement as deliberately discretionary.**

> `[OUTSIDE]` *"There is no fixed threshold. Displacement is judged relative to the surrounding tape: candle bodies noticeably larger than recent ones, small wicks, consecutive one-directional closes, imbalances left unfilled."* - LuxAlgo concept library
>
> `[OUTSIDE]` *"If you have to squint, it probably is not displacement - the concept is meant to mark moves that are obviously different from the surrounding tape."*

**This confirms the corpus is not deficient.** He never gave a number because the concept, as practised, does not have one. **The hole is real, universal, and must be parameterised rather than looked up.**

#### Candidate parameterisations to TEST, not to adopt

Where practitioners need a number for automation, these are the conventions that recur. **Each is someone else's invention, not his.**

| candidate | value cited | notes |
|---|---|---|
| **Body-to-range ratio** | **>= 0.60**, commonly 0.60-0.70 | The most consistently cited. Separates directional commitment from indecision. `Below ~60%, downgrade the setup` |
| **ATR multiple** | body > **ATR(14) x 1.5** | Adapts to prevailing volatility - attractive because it self-scales across instruments and regimes |
| **Relative to recent bodies** | conspicuously larger than the last **~20** bars | Closest to his own language (`larger than the surrounding tape`) |
| **Consecutive closes** | **2+** meaningful, **3+** strong, same direction | Matches his `big beefy candle` framing (ep06 [21:33]) |
| **Gap size** | FVG itself larger than an ATR multiple | Filters trivial gaps |

#### How this composes with what he DID say

His own criteria are structural and already codeable - **the magnitude test is the only thing missing, and it slots in as one extra gate**:

| gate | source | type |
|---|---|---|
| G1 closes beyond the level | ep06 [19:26] | **his** - structural |
| G2 next candle opens away | ep20 [12:39] | **his** - structural |
| G3 gap inside the displacement leg | ep06 [20:29] | **his** - structural |
| G4 gap in the correct half of the leg | ep29 [05:11] | **his** - structural |
| **G5 magnitude** | `[OUTSIDE]` | **invented - must be swept** |

#### The instruction that follows

**Do not pick one and build on it.** Treat G5 as a **swept parameter** in the first backtest: run body-ratio 0.5/0.6/0.7 and ATR multiple 1.0/1.5/2.0, and report results as a surface, not a number.

**Two outcomes, both worth having:**
- **Results are flat across the sweep** -> magnitude barely matters, his structural gates (G1-G4) are doing the work, and the discretion he could not articulate was never load-bearing.
- **Results are sharply peaked** -> the model's edge depends on a number he never gave, which is a finding about the *model*, not about the market - and DECISIONS section 4 requires that every point on the sweep counts toward the hypothesis tally.

`[OUTSIDE]` **Sources:** LuxAlgo concept library (displacement); backtrex.com; thesimpleict.com; ictkillzone.com; smartmoneytrader.co; TradingView indicator descriptions (FibAlgo ICT Displacement, Candle Displacement D4A). None is ICT primary material; all are third-party interpretations.

---

## 9. HOW TO READ HIS RESULTS

Recorded plainly, because it bears on using his account as evidence:

- **Some executions are demonstrations**, not setups - manufactured to answer paid students' questions (ep18 [10:40])
- **He trades without a stop at the 9:30 open** (ep15 [04:46]) while teaching that a hard stop is mandatory (ep41 [15:16])
- **He exits early on judgement** (ep14 [03:52]), **misses fills** (ep20 [11:09], ep30 [05:48]), **fumbles order types** (ep27 [11:40]), and **misses whole moves to real life** (ep21 [17:56])
- **He is explicitly fading traders using his own published concepts** (ep26 [10:00]) - so the historical edge should not be assumed to persist unchanged

**None of this is concealed - he states all of it.** But it means the account curve is not a backtest of the model.

---

## 10. THE ONE-PARAGRAPH VERSION

> Pick the market where this week's news is. Read the weekly chart for the direction of expansion and the pool it is reaching for. Each day, mark the midnight and 8:30 opens, the previous three days' highs and lows, and the day's dealing range. Between 8:30 and 11:00, wait for price to take liquidity **in the right order**, break structure **with a close and with follow-through**, and leave a **fair value gap in the correct half of that leg**. Enter on a limit into the gap - better if an order block and the 62-79% retracement sit there too. Stop where the structure that justified you would break. Take partials at internal liquidity, **80% off by 11:00**, hold the rest for the 3:00-4:00 delivery toward external liquidity. Risk 1%, halve it after a loss, restore it after recovering half. **And on most days, do none of this** - because there was no gap, or the wrong liquidity went first, or it is lunch, or it is Thursday, or you already traded this week.

---

## Provenance

Assembled 2026-09-03 from `study/ep01-ep41.md` (ep28 excluded, DECISIONS section 19). Every claim carries its episode and timestamp; every timestamp is checkable in `transcripts/` in about thirty seconds. Where the corpus disagrees with itself, section 7 says so rather than choosing.

**Not yet done:** nothing here has been backtested. Section 6 is the first experiment; section 8 lists what must be invented before it can run; DECISIONS section 4 requires the hypothesis count to start on day one.
