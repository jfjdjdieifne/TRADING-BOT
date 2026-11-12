# OWNER_QUESTIONS — gaps that block a decision

Every item is a concrete question to the repo owner. **None is answered here.** Answers will later be
recorded as claims of type `FROM_OWNER`; until then the blocked card/step stays `NOT_IN_SOURCES`.
`OQ` ids are stable.

## Blocking Phase 1 collection

- **OQ-01** — Retrieval is blocked: `fetch_page` returns `SignatureDoesNotMatch` and terminal egress
  fails with `curl (35)` for every non-GitHub/PyPI/npm host. Can you supply the PRIMARY text directly
  (files you are licensed to share), or restore retrieval? Blocks: all cards, all process steps.
- **OQ-02** — Only chunk 0 exists for Ep6, Ep3, OB16, FVG16, FVG24. Can you supply the remaining
  transcript chunks? Blocks: `time_of_day`, `equal_highs`, `order_block`, `fair_value_gap` cards.
- **OQ-03** — Do you accept the third-party mirror rendering as PRIMARY, given its provenance is
  unverified? Blocks: the 43 claims sourced from `YT_8GkQfdAXZP0_MIRROR`.

## Blocking the order-block card and Step 4

- **OQ-04** — The sources conflict: OB16 says a bullish order block is the single lowest down-close
  candle with the most open-to-close range near support [C047]; Episode 12 says it is one consecutive
  series of up closed candles and explicitly not the last candle [C017]. Which definition governs, or
  do they apply to different contexts? Blocks: `cards/order_block.md`, process Step 4, claim C050.
- **OQ-05** — How does a series of up closed candles end — what terminates it? Blocks: Step 4 Q10.
- **OQ-06** — When several fair value gaps sit inside one order block, which one is used? Blocks:
  Step 4 Q12.

## Blocking swings / intermediate-term cards and Step 3

- **OQ-07** — How many candles to the left and right define a short-term high/low? Blocks:
  `cards/intermediate_term_high.md` properties, Step 3 Q9.
- **OQ-08** — Is there any tolerance for a wick above the intermediate term high, or does any trade
  above it invalidate? [C053] says it should not trade above; no tolerance is stated. Blocks: Step 5.

## Blocking bias and Step 1

- **OQ-09** — C038 reads "if you **can't** go into your charts and line up an idea that's bullish",
  while the following sentences describe the opposite test. Is this an ASR error, and what is the
  intended test? Blocks: `cards/bias.md`, Step 1.
- **OQ-10** — How are two competing draws on liquidity ranked? Blocks: Step 1 Q3.

## Blocking targets and Step 6

- **OQ-11** — When the long-term-range target [C019] and the -1 1/2 standard-deviation projection
  [C024] disagree, which is used? Blocks: Step 6 Q15, `cards/target.md`.
- **OQ-12** — Are the numbers he states (5-day horizon [C021]; -1 1/2 [C024]) fixed rules or
  example-specific? Blocks: Step 2, Step 6, and every engine parameter.
- **OQ-13** — Is there any partial-exit or scaling rule? Blocks: Step 6.

## Blocking no-trade / being-wrong and Steps 7-8

- **OQ-14** — After cancelling an idea, what exactly re-arms it? [C052] says wait for market structure
  to get back in sync, with no observable criterion. Blocks: Step 8.3.
- **OQ-15** — Does he ever reverse on invalidation, or only stand aside? Blocks: Step 8.

## Blocking absent concepts

- **OQ-16** — `dealing range`, `premium`, `equilibrium`, `equal lows` do not occur in the stored text.
  Should these be treated as out of scope, or do you have PRIMARY material that defines them? Blocks:
  the four `NOT_FOUND_IN_SOURCES` cards.
- **OQ-17** — `time of day` is asserted as vital [C044] but no window is given anywhere in the stored
  text. Which windows, in whose words, and from which source? Blocks: `cards/time_of_day.md`,
  `cards/kill_zone.md`, and any time gate in the process.
- **OQ-18** — `invalidation` never appears as a term; only "wrong" does. Is a separate invalidation
  rule intended? Blocks: `cards/invalidation.md`.

## Blocking Phase 5 engine design

- **OQ-19** — Every detection question in `engine_representation.md` marked ENGINEERING_HYPOTHESIS
  needs your approval before it can be treated as his method. Which, if any, do you approve?
- **OQ-20** — Every item marked OWNER_DECISION_NEEDED requires a number you choose; none is chosen
  here. Blocks: all such items.
