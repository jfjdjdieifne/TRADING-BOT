# answers.md — round 2, question by question

Every verdict is followed by the claims that carry it. Verdict vocabulary: **ANSWERED_BY_SOURCE**, **CONFLICTING** (options listed, never resolved), **STILL_UNANSWERED**.

Windows read this session: 21 (+/-200 words each side = ~400 words per window), all logged in `read_log.jsonl` with file, pattern, word offsets and sha256. Claims: 50. Note: the `question` field in `read_log.jsonl` is the search that surfaced the window, not every question the window later answered — W012 surfaced under QG but supplied QF/QD/QL claims, W018 surfaced under QE but supplied QF/QC claims.

## QA — Q1 — stop placement and any buffer beyond the extreme

ANSWERED_BY_SOURCE (partly) — four distinct stop rules are stated by the speaker: below the OB low; raised to just below 50% of the OB range; trailed below the lowest low of the last 40 trading days (position trades); a comfortable stop below 75% of an already-rebalanced range. A fifth, from a worked plan, is a fixed 4-point static stop.
CONFLICTING — structural (WS-based) vs static-fixed (ES4 plan) stop coexist; kept as separate options, nothing resolved here. See also round-1 CF-07.
STILL_UNANSWERED — no window gives a numeric buffer (pips/ATR) beyond an extreme; the only numbers are the fixed 4 points of one plan. 5 claims, drawn from windows W003/W004 (surfaced by the QA search) and W013/W014/W017/W018 (surfaced by other searches).

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QA-0001` | SAID | For position trades the stop is trailed below the lowest low of the last 40 trading days. | "you're going to be trailing your stop loss below the lowest low in the last 40 trading days" | newsqlguru/ict-index@e8c40a8d : W004 |
| `R2QA-0002` | SAID | A second, tighter stop is just below 50% of the order block's total range, used once price has run away from the OB. | "just below the 50 percent of the order block total range is also considered to be a good location to raise the stop loss" | newsqlguru/ict-index@e8c40a8d : W014 |
| `R2QA-0003` | SAID | Inside an already-rebalanced range a stop below 75% of that range is called comfortable. | "75 of that range if my stop is below that I'm comfortable with that" | newsqlguru/ict-index@e8c40a8d : W017 |
| `R2QA-0004` | SAID | In the four-opportunities-per-month plan the stop is a static four points on every trade, not a structural one. | "we'll trade with a hard stop of Four Points this is a static stop loss for all trades" | newsqlguru/ict-index@e8c40a8d : W018 |
| `R2QA-0005` | SAID | The stop is placed at the far side of the imbalance being used as the entry, wherever within the gap the short is taken. | "you're gonna have to utilize that for your stop loss so your stop would have to be here" | newsqlguru/ict-index@e8c40a8d : W013 |

## QB — Q10 — limit at the array vs market/stop entry after the MSS

ANSWERED_BY_SOURCE — the choice is explicitly left to the trader, with the trade-off spelled out: limit orders may not fill because they demand a price; stop entries fill more often but widen entry-to-stop distance. In the 2022-model walkthroughs the trigger that validates the entry is the short-term shift in market structure, and in the four-opportunity plan the FVG is *selected* so that a 4-point stop fits.
CONFLICTING — none directly; but the choice being free means the corpus gives no default (see CF-R2-03).
STILL_UNANSWERED — whether he personally defaults to limit or stop for intraday arrays. 3 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QB-0001` | SAID | At the entry stage the choice between a stop-entry and a limit-entry is left to the trader. | "you're going to have to determine whether you're going to be a buyer on a stop or a buyer on a limit" | newsqlguru/ict-index@e8c40a8d : W003 |
| `R2QB-0002` | SAID | Limit orders risk no fill because they demand a specific price; stop orders fill more often but widen the entry-to-stop gap. | "there's a probability of you missing moves or missing your fills because you're demanding a specific price level" | newsqlguru/ict-index@e8c40a8d : W003 |
| `R2QB-0003` | SAID | The short-term shift in market structure is what validates the entry, and either entry model may be used once it appears. | "you got with the short term shift in Market structure here or if you want to use that one either one it validates it" | newsqlguru/ict-index@e8c40a8d : W009 |

## QC — Q8 — risk per trade, daily loss, position sizing

ANSWERED_BY_SOURCE — worked sizing examples only: 1% of a 5,000 account per trade with 3:1 R:R and a 30% hit-rate arithmetic; a 2% variant; one e-mini contract per trade, no pyramiding, on a 25,000 account with 4 dollar commissions; 'the first thing I care about is what am I gonna risk'.
CONFLICTING — 1% vs 2% appear as two hypotheticals in the same lecture; no rule about which to use.
STILL_UNANSWERED — daily loss limit, per-day trade cap beyond 'one setup and done', and what happens after a losing streak (referenced as another module that was not read). 5 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QC-0001` | USED_IN_EXAMPLE | Worked sizing example: 1% of a $5,000 account risked per trade, with 3:1 reward-to-risk and a 30% hit rate. | "we're risking on each trade one percent of our five thousand dollar account" | newsqlguru/ict-index@e8c40a8d : W007 |
| `R2QC-0002` | USED_IN_EXAMPLE | The example targets a 3:1 reward-to-risk multiple as the baseline. | "we'll be looking for trades that are reward to risk ratio of three to one" | newsqlguru/ict-index@e8c40a8d : W007 |
| `R2QC-0003` | SAID | Priority is protecting equity, not entering: rush to save money, move slowly when trying to make it. | "there's no rush to get in there is a rush to protect your assets" | newsqlguru/ict-index@e8c40a8d : W005 |
| `R2QC-0004` | USED_IN_EXAMPLE | One contract per trade, no pyramiding, no scaling up as the account grows. | "we will trade One e-mini S P contract per trade we're not doing more we're not pyramiding" | newsqlguru/ict-index@e8c40a8d : W018 |
| `R2QC-0005` | SAID | The plan is framed as an income approach, not a growth strategy. | "all this is is an income approach that's it" | newsqlguru/ict-index@e8c40a8d : W018 |

## QD — what ends the 'anticipate, don't force' waiting state

ANSWERED_BY_SOURCE (conditionally) — the waiting ends when the short-term shift in market structure appears ('wait for it to give you your 2022 model'); when a scheduled 08:30 news driver is pending, after the news creates the setup; for a beginner, explicitly NOT at the sweep itself, which is called very difficult.
STILL_UNANSWERED — no stated expiry for the waiting state (how many candles / how long before the anticipation is abandoned). 3 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QD-0001` | SAID | New traders are told not to sell the sweep itself but to wait for the 2022 model to appear. | "you don't need to be able to do that wait for it to give you your 2022 model" | newsqlguru/ict-index@e8c40a8d : W009 |
| `R2QD-0002` | SAID | When a scheduled 8:30 news driver is pending, the setup is taken after the news, not before it. | "really it's a matter of waiting for the news to hit the market and then create the setup" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QD-0003` | SAID | The first question before a trade is the risk, then how quickly to move to break-even. | "the first thing I care about is what am I gonna risk" | newsqlguru/ict-index@e8c40a8d : W005 |

## QE — what he does when price violates the entry zone

ANSWERED_BY_SOURCE (partly) — if no FVG permits the fixed stop, 'we do nothing we do not force higher risk'; while the opposite extreme holds, the candles in between are treated as time distortion (setup not abandoned); if the early-week expectation fails, it is called 'I got it wrong' and attention moves to Thursday/Friday templates.
STILL_UNANSWERED — no window describes a live stop-out and what he does immediately after (pause, reassess, reverse or stand down). 5 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QE-0001` | SAID | The setup remains valid while the opposite extreme holds; candles in between are treated as time distortion. | "as long as you don't take out this High all of these candles in between are all time distortion" | newsqlguru/ict-index@e8c40a8d : W009 |
| `R2QE-0002` | SAID | The FVG is chosen so that its far side allows the fixed four-point stop; selection is driven by stop feasibility. | "you're selecting a fair value Gap that permits a four point stop loss" | newsqlguru/ict-index@e8c40a8d : W019 |
| `R2QE-0003` | SAID | If the early-week expectation does not materialise, attention moves to the Thursday/Friday templates. | "and it does not materialize I look for the late week scenarios on Thursday and Friday" | newsqlguru/ict-index@e8c40a8d : W011 |

## QF — Q4/Q9 — killzone & session windows and their time zone

CONFLICTING — four incompatible definitions of the trading windows: (a) 'my ict new york kill zone' starting 07:00 New York and extending to 10:00; (b) the library table NY AM 08:00–11:00 (round 1); (c) the operating sessions of the four-opportunity plan, 09:30–11:30 and 13:30–15:30 New York local time; (d) the four-name list London / NY AM / NY Lunch / NY PM (round 1). All options kept.
ANSWERED_BY_SOURCE — the time zone question: 'new york time' / 'New York local time' is stated for (a) and (c).
STILL_UNANSWERED — the time zone for the minute-group timings (round-1 Q9) is still not given by any window read. 4 claims, taken from W012 (surfaced by the QG search) and W018 (surfaced by the QE search).

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QF-0001` | SAID | The ICT New York killzone begins at 07:00 New York time. | "what is seven o'clock in the morning new york time that's the beginning of my ict new york kill zone" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QF-0002` | AMBIGUOUS | The killzone is said to extend to 10:00 in the morning (ASR gives the qualifier as '4x'). | "it's extended to 10 o'clock in the morning when it's 4x" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QF-0003` | DEFINED | AM operating window: 09:30-11:30 New York local time. | "the am session is 9 30 a.m to 11 30 a.m New York local time" | newsqlguru/ict-index@e8c40a8d : W018 |
| `R2QF-0004` | DEFINED | PM operating window: 13:30-15:30 New York local time. | "the PM session is 1 30 P.M to 3 30 PM New York local time" | newsqlguru/ict-index@e8c40a8d : W018 |

## QG — Q5 — is a displacement candle required for an FVG

ANSWERED_BY_SOURCE — on the speaker's side displacement is wanted and is defined by participation ('someone with a lot of money comes in'), and a shallow break is rejected as 'not enough' — but he applies this to the shift/setup, not as a geometric FVG criterion.
CONFLICTING — against round-1 CF-01: a tutorial says no FVG without an impulsive middle candle; the library says displacement was never part of the geometric definition. Kept as three options.
STILL_UNANSWERED — whether he would reject a geometrically valid FVG with a weak middle candle; no window shows the rejection. 3 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QG-0001` | SAID | The displacement that produces the shift is described as energetic in the same breath as the structure shift. | "so it drops down that short term low here that's your shift in market structure energetic displacement" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QG-0002` | DEFINED | Displacement is defined by who is acting (large money entering), not by candle size. | "displacement now displacement is where someone with a lot of money okay comes in the marketplace" | newsqlguru/ict-index@e8c40a8d : W002 |
| `R2QG-0003` | SAID | A shallow break is rejected as insufficient; he wants a more meaningful, energetic displacement. | "i want to have a more meaningful displacement okay we want to see something that's more energetic" | newsqlguru/ict-index@e8c40a8d : W012 |

## QH — Q6 — FVG vs OB when they overlap

CONFLICTING — two live orderings: (a) in bearish order flow the sequence is order block → shift in market structure → gap; (b) the library's reading of the Jan-2017 hierarchy puts the OB first, while a tutorial enters at the FVG for fill probability. No window states what to do when both are present at the same price.
ANSWERED_BY_SOURCE (partly) — an OB is validated only after a later candle trades through its high/low, and the OB high/low then becomes the reference for the retracement entry.
STILL_UNANSWERED — the tie-break for an overlap. 4 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QH-0001` | SAID | The down candle only becomes an order block after a later candle trades through its high; the high is then the reference. | "once that down candle or suspected bullish order blocks highs violated we can now highlight that candle's high" | newsqlguru/ict-index@e8c40a8d : W015 |
| `R2QH-0002` | SAID | In bearish order flow the sequence is order block, then shift in market structure, then the gap. | "we have a small little Gap in here after shift in Market structure after the order block" | newsqlguru/ict-index@e8c40a8d : W020 |
| `R2QH-0003` | DEMONSTRATED | Teaching example: the down candle is only called a bullish order block once a later candle trades through its high. | "now we have a validated bullish order block this candle validates the down candle as a bullish order block" | newsqlguru/ict-index@e8c40a8d : W015 |

## QI — Q12 — CHoCH vs MSS/BOS wording as used by him

ANSWERED_BY_SOURCE — in every window read this session he says 'shift in market structure' / 'market structure shift' / 'short-term market structure shift'. 'CHoCH' / 'change of character' does not appear in any of the 21 windows read.
CONFLICTING — a third-party explainer lists Change of Character; the round-1 library says the concept does not exist in ICT's corpus. Three options kept.
STILL_UNANSWERED — whether 'break of structure' is used with a different meaning (only 'bos' substring noise was found, mostly in code repos). 1 claim + grep evidence in search_log.tsv.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QI-0001` | SAID | The shift is defined by a swing low being taken out; he says 'market structure shift', not CHoCH. | "causes a short-term Market structure shift bearishly because there's a swing low that was taken out" | newsqlguru/ict-index@e8c40a8d : W019 |

## QJ — consequent encroachment / 50% of an FVG and its relation to 50% of a dealing range

ANSWERED_BY_SOURCE — the 50% level is applied consistently to three objects in the same windows: a wick treated as a gap (graded 75% / 50%, 'we never want to see ... lower than 50'), the midpoint of a wick which price returns to, and equilibrium of a dealing range (half of the high-to-low leg) where the reaction occurs. One window explicitly nests them: a 15-minute bearish order block sits at the consequent encroachment of the fair value gap.
CONFLICTING — none found; the objects differ but the 50% geometry does not contradict itself.
STILL_UNANSWERED — no window states whether the consequent-encroachment of one gap and the equilibrium of the containing dealing range are the same number by construction or by coincidence. 3 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QJ-0001` | SAID | A wick is treated as a gap and graded at 75% and 50% of the wick. | "it's working inside this Wick which is what a gap we do gradients on wicks 75 of the wick 50 of the wick" | newsqlguru/ict-index@e8c40a8d : W016 |
| `R2QJ-0002` | SAID | The midpoint (consequent encroachment) of a wick is treated as the gap level price returns to. | "we treat that as a gap the Mark goes right back to it there" | newsqlguru/ict-index@e8c40a8d : W016 |
| `R2QJ-0003` | SAID | A 15-minute bearish order block is described as sitting at the consequent encroachment of the fair value gap. | "a 15-minute bearish order block that is the consequent quotient of this fair value Gap" | newsqlguru/ict-index@e8c40a8d : W021 |

## QK — which timeframe is the 'lower timeframe' for the MSS

ANSWERED_BY_SOURCE — the hunting timeframe is stated as the five minute 'or lower', refinement continues to 'the four three two or one minute charts', and the lower timeframe is chosen by which one actually produces the fair value gaps. Top-down path is given as four hours to five minutes, with the four-hour chart pulled out 'when it's necessary' because the daily is messy.
STILL_UNANSWERED — no fixed ladder; the choice is explicitly left to the trader ('I'll leave that up to you'), so the engine cannot hard-code it (Q-R2-04). 6 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QK-0001` | SAID | The hunting timeframe for the setup is the five minute 'or lower'; refinement then drops further. | "whatever time frame you're hunting whether it be the five minute or lower" | newsqlguru/ict-index@e8c40a8d : W019 |
| `R2QK-0002` | SAID | The lower timeframe is chosen by which one actually produces the fair value gaps, not by a fixed rule. | "we're looking for a time frame that produces fair value gaps that's the key" | newsqlguru/ict-index@e8c40a8d : W011 |
| `R2QK-0003` | DEFINED | The stated top-down path runs from the four-hour chart down to the five-minute chart. | "ICT short-term top-down analysis four hours to five minutes" | newsqlguru/ict-index@e8c40a8d : W010 |
| `R2QK-0004` | SAID | Timeframe is escalated on demand: the four-hour chart is used when the daily is too messy. | "I'm gonna pull out the four hour chart when it's necessary" | newsqlguru/ict-index@e8c40a8d : W020 |
| `R2QK-0005` | SAID | Dropping timeframe is justified by seeing inefficiencies and better liquidity pools, not by a fixed ladder. | "so I want to break it down into smaller more refined ranges so you can see inefficiencies and better liquidity pools" | newsqlguru/ict-index@e8c40a8d : W020 |

## QL — PROCESS from blank chart to exit, as demonstrated

ANSWERED_BY_SOURCE — an ordered routine is stated and demonstrated: day of the week first; monthly/weekly/daily analysis before the four-hour view; HTF bias then direction per weekday; wait for participation evidence at the HTF level; validate the array (OB needs a trade through its high); wait for the shift; choose the FVG that fits the stop; target external liquidity/liquidity pool. 21 windows across 9 transcripts and 2 sequences files built from these quotes.
STILL_UNANSWERED — the exit leg is under-demonstrated: only the ES4 plan gives a fixed target (5.25 points) and the round-1 claims give external liquidity; no window shows a full trade exit with reasoning. 8 claims, drawn from 10 windows across 6 transcripts; 3 sequence files in `sequences/`.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QL-0001` | SAID | The first decision in the top-down routine is the day of the week, not a price level. | "the first thing that's in my mind is the day of the week that we're trading" | newsqlguru/ict-index@e8c40a8d : W010 |
| `R2QL-0002` | SAID | The four-hour view is only taken after monthly, weekly and daily analysis is in hand. | "all monthly weekly and daily analysis is included when viewing the four hour perspective" | newsqlguru/ict-index@e8c40a8d : W010 |
| `R2QL-0003` | SAID | Directional bias plus day of week selects the direction he will look for early in the week. | "if I'm bearish from the higher time frame I look for shorts on Mondays Tuesdays and Wednesdays" | newsqlguru/ict-index@e8c40a8d : W011 |
| `R2QL-0004` | SAID | After price reaches the HTF level he waits for evidence of participation rather than trading the level itself. | "we're waiting for price to show us indications that smart money or a large body of big flows" | newsqlguru/ict-index@e8c40a8d : W015 |
| `R2QL-0005` | DEMONSTRATED | Worked day: 21 June 2022, 08:30 New York, high-impact core retail sales on a dollar/cad chart. | "at 8 30 in the morning june 21st 2022 we had a high impact news driver for core retail sales" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QL-0006` | DEMONSTRATED | Sequence on that day: short-term high created, run above it, buy-side liquidity taken. | "the market creates a short-term high then runs above that so we have buy side taken" | newsqlguru/ict-index@e8c40a8d : W012 |
| `R2QL-0007` | DEMONSTRATED | Outcome on that day: price delivered to the fair value gap and then to the sell-side pool. | "delivered to the fair value gap and delivered to the south side of koji pool" | newsqlguru/ict-index@e8c40a8d : W013 |
| `R2QL-0008` | DEMONSTRATED | Worked chart: each run into the sell-side imbalance is rejected at its low, producing another sell-off. | "it hits the low of it rejects it hard and then creates another sell-off" | newsqlguru/ict-index@e8c40a8d : W020 |

## QM — dealing range and premium/discount — demonstrated use

ANSWERED_BY_SOURCE — demonstrated twice: the high-to-low leg is named 'your dealing range', the reaction is attributed to half of it; and on another chart equilibrium is set between a high and a low with the requirement to enter short only below it (a discount array). A third window states the Fibonacci tool is used only to illustrate equilibrium.
STILL_UNANSWERED — how the leg is selected when several swings qualify (round-1 Q2/Q3 remain open). 4 claims.

| claim | type | statement | quote | source (file: window) |
|---|---|---|---|---|
| `R2QM-0001` | SAID | The dealing range is the leg from that high down to that low (ASR 'price Wing' = price swing). | "this movement lower from this high down to that low that's your price Wing that's your dealing range" | newsqlguru/ict-index@e8c40a8d : W021 |
| `R2QM-0002` | SAID | The reaction is attributed to half of that range — equilibrium of the dealing range. | "essentially half of this range right there that's why it goes right up there and stops" | newsqlguru/ict-index@e8c40a8d : W021 |
| `R2QM-0003` | SAID | The Fibonacci tool is used only to illustrate equilibrium, not as a signal. | "i'm only going to use fibonacci to illustrate equilibrium" | newsqlguru/ict-index@e8c40a8d : W001 |
| `R2QM-0004` | SAID | Equilibrium of the swing is the dividing line, and a short must be taken at an array below it. | "between this high and that low here is equilibrium so we have to find a discount array below that if we're going short" | newsqlguru/ict-index@e8c40a8d : W013 |

