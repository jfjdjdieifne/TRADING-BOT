# Process spec: blank chart → exit

Built **only** from claims of type `SAID` or `DEMONSTRATED` that were read in this session (transcripts, the library's
quoted lecture text, forum compilation). Where a step is under-specified the branch says so instead of inventing a rule.
Nothing in this file is a trading recommendation.

## Q0. Is today even tradeable?
Conditions that end the process before anything else (all verbatim speaker statements, all from the London-avoidance
lecture, so internally NOT_INDEPENDENT):
- previous day's range > 2× its five-day ADR → skip the day (CLM-0047)
- three consecutive daily up closes → no longs in London (CLM-0043)
- FOMC whipsaw the day before → skip London open (CLM-0044)
- NFP Friday → no London session at all (CLM-0045)
- day before a long weekend/holiday → avoid London (CLM-0046)
- outside killzones → "no new setup should be forced" (library, CLM-0033 — LLM_STATED, treat as flag not gate)
**Branch:** if any condition holds → exit (stand aside). If two hold at once, the ordering is not stated (Q6).

## Q1. Strip the vocabulary and look at raw structure
"no order block discussion, no breaker" (CLM-0059). First question: "whether we are working off of a swing high or a
swing low" (CLM-0010, DEMONSTRATED). Swing definition given: candle with a higher low on either side (CLM-0011) /
higher high with lower highs on either side (CLM-0058).
**Branch:** Sunday candles are skipped in the swing count (CLM-0012) — this is the only calendar exception stated.

## Q2. Which direction does the higher timeframe give?
Either the monthly or the weekly must give the directional bias (CLM-0022). Bias confluence, when MN+W+D agree, is the
highest-conviction state; when the daily disagrees it signals a possible bias flip in progress (CLM-0064, CLM-0065,
CLM-0066 — library, NOT_INDEPENDENT).
**Branch:** MN and W disagree → **no rule read** (Q3).

## Q3. Where is the liquidity, internal and external?
Use HTF institutional order flow to frame where internal-range liquidity and the buy stops sit (CLM-0016). The current
range has buy-side liquidity above the high and sell-side below the low (CLM-0067, CLM-0068).

## Q4. Which pool is the draw?
Name the specific pool price is drawn toward (CLM-0025); if you cannot, "you do not have a setup" (CLM-0026). Confirm
with PD-array confluence (CLM-0082). For Model 7 the stage is a higher-timeframe liquidity draw (CLM-0005).
**Branch:** several candidate draws → ranking not stated (Q2).

## Q5. Wait for the sweep. Then what?
"A swing low ... runs through this low, a stop hunt" (CLM-0060). After a run above relative equal highs you are
*anticipating* the shift, "not forcing it" (CLM-0055, CLM-0056). Confirm with an MSS on the lower timeframe (CLM-0087)
— but the same lecture allows selling above the level without waiting for the shift (CLM-0057) → CF-08 open.

## Q6. Where is the entry?
Two candidate answers, both live:
- fair value gap: 3-candle wick non-overlap (CLM-0027), or "none without an impulsive middle candle" (CLM-0084) vs
  "displacement was never part of the geometric definition" (CLM-0093) → CF-01 open;
- order block: last opposing candle (CLM-0086) vs 2016 extreme-range candle (CLM-0094) vs 2022 "change in the state of
  delivery" (CLM-0095) → CF-02 open. Entry requires the OB low to be grabbed and an LTF FVG/MSS (CLM-0100, CLM-0087).
Priority between FVG and OB when they overlap: CF-06 open (CLM-0097 vs CLM-0098).
**Branch:** neither array present → no trade (implied by CLM-0026, stated for the draw only).

## Q7. Where is the stop?
Beyond the PD array's invalidation extreme (CLM-0061); for a bearish OB "above this candle's high" (CLM-0062); below a
bullish OB is called "relatively safe" (CLM-0063). No numeric buffer is given by any source read (Q1).

## Q8. Where is the exit?
Exits at external-range liquidity (CLM-0013, CLM-0015); the objective is "an old high or above it, while in sync with a
higher time frame directional bias" (CLM-0023). When price reaches an FVG it has left unworked, expect a fill (CLM-0019);
a liquidity run closing in a one-candle-long-candle range is read as a gap fill (CLM-0020).

## Q9. If it goes wrong
Accept it: "you are not going to be right 100 of the time" (CLM-0048), "invite the possibility of being wrong"
(CLM-0049), exits and entries are not perfect "all the time" (CLM-0052). Scoreboard = monthly return; >1% consistently
is called exceptional (CLM-0054). **Not stated:** max loss per trade, per day, or what "consistently" means (Q8).

## Branches with no answer in the sources
Q3 (MN vs W disagreement), Q2 (draw ranking), Q1 (stop buffer), Q6 (FVG vs OB priority, displacement requirement),
Q0 (condition priority), Q8 (risk sizing, "consistently"). All are filed in `OWNER_QUESTIONS.md`.
