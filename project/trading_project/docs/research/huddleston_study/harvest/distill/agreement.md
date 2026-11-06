# Where the sources agree (phase 4)

Every line below lists the claim ids behind it. `NOT_INDEPENDENT` is marked when all supporting claims come from one
LLM-assisted library (see `authorship_flags.tsv`) or from the same lecture minutes apart.

## A1. Liquidity is orders, and price is drawn toward pools of them
CLM-0003 (transcript), CLM-0069 (library), CLM-0025 (library), CLM-0090 (web record). Independent sources in three
different modalities (transcript / library / third-party explainer) say the same thing: liquidity = resting buy and
sell orders, and price seeks pools.
Confidence: MULTI_SOURCE; the two library claims are NOT_INDEPENDENT of each other.

## A2. A trading range has buy-side liquidity above and sell-side below
CLM-0067, CLM-0068 (same library file family) + CLM-0002 (transcript: "reference points where there is a high
probability of..."). Range-based reasoning is stated in both. The library pair is NOT_INDEPENDENT.

## A3. Entries are internal, exits are external (range liquidity)
CLM-0013, CLM-0015 (transcript, same lecture). Also CLM-0008 (target runs on liquidity above the previous day's high).
Single speaker, so NOT_INDEPENDENT across claims but this is the clearest "how a target is chosen" statement in the
corpus and is contradicted by nothing that was read.

## A4. Stop goes beyond the array, not at an arbitrary distance
CLM-0061, CLM-0062, CLM-0063 (library) + CLM-0100 (third-party tutorial: price must grab the OB's low before
reversing, i.e. the invalidation is structural). Structural stop placement is stated in both a library and a tutorial
site. No source read gives a numeric buffer — see `OWNER_QUESTIONS.md` Q1.

## A5. After a sweep, a shift is expected before the trade is taken
CLM-0055, CLM-0056 (transcript) + CLM-0087 (tutorial, "MSS confirms the bullish intent") + CLM-0032 (library
behavioural signature: sweeps + displacement + FVG). BUT the same lecture (CLM-0057) says there are ways to enter
without waiting for the shift. Recorded as CF-08, not resolved.

## A6. FVG geometry: three candles, wick non-overlap
CLM-0027, CLM-0029 (library) + CLM-0085 (tutorial). Geometry agrees; the *displacement* requirement does not
(CF-01: CLM-0084 vs CLM-0093).

## A7. Equilibrium is the 50% of the measured range
CLM-0036 (library), CLM-0038 (library). Single-source family (NOT_INDEPENDENT). No second independent source in the
read windows states the 50% rule, so this remains SINGLE_SOURCE family in the pack.

## A8. Being wrong is normal and the monthly return is the scoreboard
CLM-0048, CLM-0049, CLM-0051, CLM-0052, CLM-0053, CLM-0054 (one lecture, NOT_INDEPENDENT internally, but it is a
verbatim speaker statement rather than a derived claim). CLM-0054 gives the only performance number in the corpus
("consistently higher than one percent" per month).

## A9. Order blocks are the institutional candle(s) before a directional move
CLM-0030 (library definition), CLM-0086 (tutorial), CLM-0014 (transcript: "bearish order block which is the last up
candle"). Agreement at the level of *role* (zone before the move); disagreement at the level of *candle selection*
(CF-02). Recorded in `conflicts.jsonl`, all four options kept.

## What is NOT agreed and was deliberately left open
CF-01 FVG displacement · CF-02 OB definition · CF-03 CHoCH existence · CF-04 killzone windows · CF-05 MSS vs BOS
wording · CF-06 FVG vs OB priority · CF-07 entry validation vs stop location · CF-08 wait-for-shift.
No conflict was merged or resolved in this run.
