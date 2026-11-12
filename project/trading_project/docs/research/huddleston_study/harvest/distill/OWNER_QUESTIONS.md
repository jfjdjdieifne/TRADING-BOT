# OWNER_QUESTIONS — what the stored sources do not answer

Each item is a `gap` row in `knowledge_pack.jsonl` (`operationalization.definition = OWNER_DECISION_NEEDED`).
None of these numbers or orderings were invented; the deterministic engine must not run until they are decided.

| # | Question | Why it is open | Related claims / conflict |
|---|----------|----------------|---------------------------|
| Q1 | What numeric buffer, if any, goes beyond the structural stop extreme (pips, ATR fraction, none)? | Every source read gives a *structural* rule only; the library explicitly says an earlier buffer figure in its own table was invented | CLM-0061, CLM-0062, CLM-0063, CF-07 |
| Q2 | When several liquidity pools are plausible draws, how are they ranked? | The corpus says "identify which pool is the draw" but never ranks candidates in the windows read | CLM-0025, CLM-0026, CLM-0082 |
| Q3 | When the monthly and weekly bias disagree, which one governs? | Stated only that *either* MN or W must give the bias; no tie-break read | CLM-0022, CLM-0066 |
| Q4 | Which killzone set is authoritative (library's five windows vs other sources' four names)? | Two incompatible definitions; no source read reconciles them | CLM-0076/77/78 vs CLM-0091, CF-04 |
| Q5 | Is an impulsive/displacement middle candle required to call an FVG? | Directly contradictory sources | CLM-0084 vs CLM-0093, CF-01 |
| Q6 | FVG-first or OB-first when both overlap at the entry? | One source optimises for fill probability, another asserts a hierarchy | CLM-0097, CLM-0098, CF-06 |
| Q7 | How old may an order block be and still be tradeable (candles / sessions)? | No age rule appears in the read windows | CLM-0030, CLM-0094 |
| Q8 | Risk per trade, max daily loss, and what "consistently" means for the 1%/month remark | Only the remark exists; no sizing rule anywhere in the read windows | CLM-0054, CLM-0053 |
| Q9 | Are minute-group times (XX:01, XX:06–08) in exchange time or the speaker's local time? | The forum compilation lists minutes without a timezone | CLM-0073, CLM-0074, CLM-0075 |
| Q10 | After an MSS, is entry a resting limit at the array or a market entry on the close-through? | Both are implied; neither is stated as the rule | CLM-0087, CLM-0055, CF-08 |
| Q11 | If two no-trade conditions collide, or one holds and a valid setup appears, which wins? | The lecture lists conditions with "typically"/"generally", never a priority | CLM-0043…CLM-0047 |
| Q12 | Is CHoCH part of the vocabulary at all? | The library says no such ICT concept; an explainer lists it | CLM-0041 vs CLM-0099, CF-03 |

## Also unanswered (not numeric, still blocking a deterministic engine)
- What ends the "anticipate, don't force" state? No invalidation for the *waiting* plan was read.
- Which timeframe is "the lower timeframe" for the MSS — the entry TF or one above it?
- Does the 50% equilibrium rule apply to the dealing range only, or also to each FVG (consequent encroachment)?
  Both concepts exist in the sources but the relation between them was not read.
