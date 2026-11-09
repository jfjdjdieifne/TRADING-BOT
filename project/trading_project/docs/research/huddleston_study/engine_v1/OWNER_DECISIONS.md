# Owner Decisions

## D1 — Sweep reference and equal-high/equal-low variant

**Status: OWNER_APPROVED**

### Sweep reference level

- **Decision — ENGINEERING_CHOICE:** The sweep reference level is a swing high or swing low as defined by V-A-00: three candles, with one candle on each side.
- **Reason:** This introduces no new number.
- **Reporting:** Print the reference level with every sweep result.

### Parked variant V-E-EQH

- **Decision — ENGINEERING_CHOICE:** Two swing highs, or two swing lows, count as “equal” when the absolute price difference is less than or equal to **1 × spread**. The multiplier **1** is declared before any test.
- **Reason:** Spread is the smallest quantity the market itself quotes, so this adds no free parameter.
- **Spread definition, declared now:** Ask close minus bid close of the middle candle (c2) of the second swing.
- **Freeze rule:** This definition and multiplier will not be changed after seeing results. Any other multiplier or spread definition is a new named variant.
- **Evaluation:** Measure V-E-EQH separately; do not choose it based on results.
- **Caveat:** Spread is tiny on EUR/USD, so V-E-EQH may rarely fire. That is not a reason to change it.

### Open question — KNOWLEDGE_GAP

Which earlier swing is paired with the second one: the immediately previous swing of the same side, or any swing within a lookback? Any lookback is a number with no source. This remains undecided.

### Rejected suggestion — REJECTED, not a source

An unverified chatbot suggestion of “0.2 × ATR” is rejected because the numbers (0.2 and the ATR period) are invented and have no verified source.

### Pasted claim — IDEA_TO_VERIFY, not a source

An unverified pasted text claims that a source says equal highs are judged visually, with no pip number. This is an idea to verify, not a source.

- **External search record:** [Numeric EQH/EQL public-source search](external_sources/k_equal_highs.md).

## D2 research

- **Records, counts and pages checked for Q1–Q7:** [external_sources/l_open_questions.md](external_sources/l_open_questions.md) — one section per open question, with TEACHING and IMPLEMENTATION_CODE kept separate.
- **Full step-by-step ICT specification, every line carrying a source symbol:** [external_sources/s_ict_spec_sources_only.md](external_sources/s_ict_spec_sources_only.md) — candle elements, strength numbers with their denominators, swing, liquidity, sweep, MSS, FVG, order block, breaker, entry, stop, target, invalids, and a closed list of the points where the sources give nothing.

## D2 — Displacement variants

**Status: OWNER_APPROVED**

There is **no reference definition of displacement**. Record the following three families as separate named variants. Measure every sub-version separately; never select one because of its results and never attribute any variant to a person. These are recorded alternatives, not a default or an endorsement of a winning threshold.

- **V-D-A — body divided by candle range:**
  - **V-D-A-1:** 60–80 percent, as printed by the source.
  - **V-D-A-2:** about 75 percent, as printed by the source.
  - **V-D-A-3:** 70 percent, as printed by the source.
  - **V-D-A-4:** 80 percent, as printed by the source.
- **V-D-B — candle compared with previous candles:**
  - **V-D-B-1:** candle range at least 2× the average range of 3–5 previous candles.
  - **V-D-B-2:** candle body 2–3× the average body of the previous 10 candles.
- **V-D-C — body compared with ATR:**
  - **V-D-C-1:** candle body at least 1.5 × ATR(14). The source itself says the multiple is a choice to test.

A number supplied by the owner later would be an **additional named variant**, not a replacement chosen by results. **Displacement is not coded yet.**

## OPEN_FROM_HARD_TESTS — undecided, not owner decisions

- **Precedence:** `NO > UNDECIDED > PENDING` is an undeclared `ENGINEERING_CHOICE` of the builder, not a priority stated in V2. About 36 thousand observations depend on that choice; the hard-test report records 36,562. Which priority, if any, should be approved remains open.
- **Missing closure flag:** The candle record defaults `closed=True` when that field is missing. Whether this default is acceptable remains open.
- **Malformed candles:** Direct detector functions silently accept some malformed duck-typed candles, including examples with `high < low`, although the candle constructor rejects them. Whether direct calls must validate remains open.
- **FVG closure:** The FVG detector does not require C3 to be closed. Whether a closure requirement should be introduced remains open.
