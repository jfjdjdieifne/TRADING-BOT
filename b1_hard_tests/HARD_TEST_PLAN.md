# B1 hard test plan — frozen before opening the implementation

## Scope and evidence

- The sole source of expected statuses is `BUILD_STEP_B1_DESIGN_V2.md` §4.3–4.8 and §5.3–5.7, with `CORRECTIONS_R3` (especially R3-b and R3-d). The earlier independent expectations and results were read as context, not used as authority over V2.
- All valid prices in every **FIXTURE** are integer ticks; all fixtures are artificial. No market data, network requests, third-party libraries, or tuning are used. The invalid-input probes deliberately violate the schema where specified.
- `i` names the middle candle C2. The window is C1=`i-1`, C2=`i`, C3=`i+1`. When an event-time API uses the index of C3, use `t=i+1`; never conflate the two conventions. Compare both direct and event-time interfaces when provided.
- A swing high/low is strict versus both neighbouring wick extremes, and C3 must be closed for confirmation. With both strict relations satisfied and C3 open, use `PENDING` for “not yet confirmed”. A tie without a conflicting failed comparison and with closed C3 is `UNDECIDED`; two strict relations with at least one failed and closed C3 give `NO`. A closed C3 and two favourable comparisons give `YES`.
- Bullish FVG: C3.low > C1.high, with ascending bounds `[C1.high,C3.low]`; bearish: C3.high < C1.low, with bounds `[C3.high,C1.low]`. Equality is `UNDECIDED`, overlap is `NO`. V2 gives no additional C3-close requirement for FVG; do not invent one. Even if touched, filled or closed through later, the invalidation field remains `INVALIDATION_UNDECIDED`.
- V2 does **not** specify a priority among `NO`, `UNDECIDED`, and `PENDING`. A tie combined with a failed comparison, or an open C3 combined with a tie or a failed comparison, is `TEXT_SILENT`, not an assertion of a priority. Every such status observation, including those in A, B, and D, is routed into **PRECEDENCE_CHOICE**, never counted as a pass or failure in its originating family. The group is keyed by swing direction, each of the two relations (`F` favourable, `E` equal, `X` unfavourable) and C3 closure. There are exactly 20 planned equivalence-group cases; every observation and the distribution of returned statuses are retained. A metamorphic equality assertion does not require choosing a priority and remains in C.
- Missing neighbours and malformed input are also `TEXT_SILENT`: record the exact question and the actual return or exception, not a fabricated expected status. The questions are below; each JSON expectation also carries its question explicitly.
- One **status case** is one concept/direction at one target index. In E a case is one input probe exercised separately against all four directions and reported on one line; in PRECEDENCE_CHOICE a case is one relation/closure group reported with its number of constituent observations. In F each individual returned record is one contract case; applicability and per-rule check counts are reported. Every exception is also checked for repeatability and input mutation, but is not a returned record.

### Exact unanswered questions

- `Q_EDGE_LEFT`: What status, or what error, should each concept return at C2 when C1 is missing?
- `Q_EDGE_RIGHT`: What status, or what error, should each concept return at C2 when C3 is missing?
- `Q_MIXED`: When one swing comparison is equal and the other strictly fails, and C3 is closed, is the status `NO` or `UNDECIDED`?
- `Q_OPEN_FAIL`: When at least one swing comparison strictly fails and C3 is open, is the status `NO` or `PENDING`?
- `Q_OPEN_EQUAL`: When at least one swing comparison is equal, neither fails, and C3 is open, is the status `UNDECIDED` or `PENDING`?
- `Q_OPEN_MIXED`: When a swing comparison is equal, the other strictly fails, and C3 is open, is the status `NO`, `UNDECIDED`, or `PENDING`?
- `Q_INVALID`: For this exact invalid fixture and index, should the interface reject it with which error, return which status, or accept it silently?

## A. Three long hand-made FIXTURE series

Each line is a manually written expectation for that index, not an oracle-generated answer. Columns are `i | low..high | swing high | swing low | bullish FVG | bearish FVG | one-line reason`. For each `low..high`, the complete candle is `open=low`, `high=high`, `low=low`, `close=high`, `closed=true`. Thus all prices are integer ticks. The machine-readable copy preserves each individual reason and question. Boundary questions apply separately to all four status cells. `Q_MIXED` cells are counted in PRECEDENCE_CHOICE.

### A1 — alternating inside/outside candles with a single spike (30)

| i | FIXTURE low..high | SH | SL | bull | bear | Reason |
|---:|---|---|---|---|---|---|
| 0 | 4..16 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_LEFT: C1 is absent. |
| 1 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 2 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 3 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 4 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 5 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 6 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 7 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 8 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 9 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 10 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 11 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 12 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 13 | 7..13 | NO | NO | NO | NO | Inside ordinary and spiked neighbours; endpoints overlap. |
| 14 | 1..20 | YES | YES | NO | NO | Single extreme wick spike outside both neighbours; endpoints overlap. |
| 15 | 7..13 | NO | NO | NO | NO | Inside spiked and ordinary neighbours; endpoints overlap. |
| 16 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 17 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 18 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 19 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 20 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 21 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 22 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 23 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 24 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 25 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 26 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 27 | 7..13 | NO | NO | NO | NO | Inside both neighbours; endpoint ranges overlap. |
| 28 | 4..16 | YES | YES | NO | NO | Outside both neighbours; endpoint ranges overlap. |
| 29 | 7..13 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_RIGHT: C3 is absent. |

### A2 — rising and falling disjoint price jumps (30)

| i | FIXTURE low..high | SH | SL | bull | bear | Reason |
|---:|---|---|---|---|---|---|
| 0 | 0..1 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_LEFT: C1 is absent. |
| 1 | 3..4 | NO | NO | YES | NO | Strict rise; C3.low 6 > C1.high 1. |
| 2 | 6..7 | NO | NO | YES | NO | Strict rise; C3.low 9 > C1.high 4. |
| 3 | 9..10 | NO | NO | YES | NO | Strict rise; C3.low 12 > C1.high 7. |
| 4 | 12..13 | NO | NO | YES | NO | Strict rise; C3.low 15 > C1.high 10. |
| 5 | 15..16 | NO | NO | YES | NO | Strict rise; C3.low 18 > C1.high 13. |
| 6 | 18..19 | NO | NO | YES | NO | Strict rise; C3.low 21 > C1.high 16. |
| 7 | 21..22 | NO | NO | YES | NO | Strict rise; C3.low 24 > C1.high 19. |
| 8 | 24..25 | NO | NO | YES | NO | Strict rise; C3.low 27 > C1.high 22. |
| 9 | 27..28 | NO | NO | YES | NO | Strict rise; C3.low 30 > C1.high 25. |
| 10 | 30..31 | NO | NO | YES | NO | Strict rise; C3.low 33 > C1.high 28. |
| 11 | 33..34 | NO | NO | YES | NO | Strict rise; C3.low 36 > C1.high 31. |
| 12 | 36..37 | NO | NO | YES | NO | Strict rise; C3.low 39 > C1.high 34. |
| 13 | 39..40 | NO | NO | YES | NO | Strict rise; C3.low 42 > C1.high 37. |
| 14 | 42..43 | NO | NO | YES | NO | Strict rise; C3.low 45 > C1.high 40. |
| 15 | 45..46 | YES | NO | NO | NO | Peak high exceeds both; low is not a trough; endpoint ranges coincide. |
| 16 | 42..43 | NO | NO | NO | YES | Strict fall; C3.high 40 < C1.low 45. |
| 17 | 39..40 | NO | NO | NO | YES | Strict fall; C3.high 37 < C1.low 42. |
| 18 | 36..37 | NO | NO | NO | YES | Strict fall; C3.high 34 < C1.low 39. |
| 19 | 33..34 | NO | NO | NO | YES | Strict fall; C3.high 31 < C1.low 36. |
| 20 | 30..31 | NO | NO | NO | YES | Strict fall; C3.high 28 < C1.low 33. |
| 21 | 27..28 | NO | NO | NO | YES | Strict fall; C3.high 25 < C1.low 30. |
| 22 | 24..25 | NO | NO | NO | YES | Strict fall; C3.high 22 < C1.low 27. |
| 23 | 21..22 | NO | NO | NO | YES | Strict fall; C3.high 19 < C1.low 24. |
| 24 | 18..19 | NO | NO | NO | YES | Strict fall; C3.high 16 < C1.low 21. |
| 25 | 15..16 | NO | NO | NO | YES | Strict fall; C3.high 13 < C1.low 18. |
| 26 | 12..13 | NO | NO | NO | YES | Strict fall; C3.high 10 < C1.low 15. |
| 27 | 9..10 | NO | NO | NO | YES | Strict fall; C3.high 7 < C1.low 12. |
| 28 | 6..7 | NO | NO | NO | YES | Strict fall; C3.high 4 < C1.low 9. |
| 29 | 3..4 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_RIGHT: C3 is absent. |

### A3 — repeated high/low plateaux and conflicting ties (30)

| i | FIXTURE low..high | SH | SL | bull | bear | Reason |
|---:|---|---|---|---|---|---|
| 0 | 8..12 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_LEFT: C1 is absent. |
| 1 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes improve on C1 and tie C3; endpoints overlap. |
| 2 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie both neighbours; endpoints overlap. |
| 3 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie C1 and improve on C3; endpoints overlap. |
| 4 | 8..13 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 5 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 6 | 10..11 | NO | NO | NO | NO | Inside both neighbours; endpoints overlap. |
| 7 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 8 | 8..13 | YES | UNDECIDED | NO | NO | High exceeds both; low improves on C1 and ties C3; endpoints overlap. |
| 9 | 8..12 | TEXT_SILENT | UNDECIDED | NO | NO | Q_MIXED: high fails C1 and ties C3; low ties both; endpoints overlap. |
| 10 | 8..12 | TEXT_SILENT | TEXT_SILENT | NO | NO | Q_MIXED: both extremes tie C1 and fail against C3; endpoints overlap. |
| 11 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes improve on C1 and tie C3; endpoints overlap. |
| 12 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie both neighbours; endpoints overlap. |
| 13 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie C1 and improve on C3; endpoints overlap. |
| 14 | 8..13 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 15 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 16 | 10..11 | NO | NO | NO | NO | Inside both neighbours; endpoints overlap. |
| 17 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 18 | 8..13 | YES | UNDECIDED | NO | NO | High exceeds both; low improves on C1 and ties C3; endpoints overlap. |
| 19 | 8..12 | TEXT_SILENT | UNDECIDED | NO | NO | Q_MIXED: high fails C1 and ties C3; low ties both; endpoints overlap. |
| 20 | 8..12 | TEXT_SILENT | TEXT_SILENT | NO | NO | Q_MIXED: both extremes tie C1 and fail against C3; endpoints overlap. |
| 21 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes improve on C1 and tie C3; endpoints overlap. |
| 22 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie both neighbours; endpoints overlap. |
| 23 | 7..14 | UNDECIDED | UNDECIDED | NO | NO | Both extremes tie C1 and improve on C3; endpoints overlap. |
| 24 | 8..13 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 25 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 26 | 10..11 | NO | NO | NO | NO | Inside both neighbours; endpoints overlap. |
| 27 | 9..12 | NO | NO | NO | NO | Both extremes lie strictly between neighbours; endpoints overlap. |
| 28 | 8..13 | YES | UNDECIDED | NO | NO | High exceeds both; low improves on C1 and ties C3; endpoints overlap. |
| 29 | 8..12 | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | TEXT_SILENT | Q_EDGE_RIGHT: C3 is absent. |

## B. Shape traps — all FIXTURE prices are integer ticks

The JSON gives the complete candle tuples, exact target indices and four manually entered expected statuses. Exercise each listed target with all four concepts; never hide an unasserted direction. For the high and low plateaux, exercise each of the three plateau candles. For adjacent candidates, exercise both adjacent indices. For back-to-back gaps, exercise each of the four consecutive centres and also verify their bounds overlap. For the two later-touch/fill scenarios, compare the original gap at its centre before and after each later candle, and check `INVALIDATION_UNDECIDED` at every stage.

| FIXTURE | Candle low..high sequence | i | SH, SL, bull, bear | Reason |
|---|---|---|---|---|
| high plateau | 0..8, 0..10, 0..10, 0..10, 0..8 | 1,2,3 | UNDECIDED, UNDECIDED, NO, NO | Equal highs on three candles, equal lows; endpoint ranges overlap. |
| low plateau | 3..10, 1..10, 1..10, 1..10, 3..10 | 1,2,3 | UNDECIDED, UNDECIDED, NO, NO | Equal lows on three candles, equal highs; endpoint ranges overlap. |
| staircase up | 2..4, 3..5, 4..6 | 1 | NO, NO, UNDECIDED, NO | Strict rise; bullish endpoints touch exactly. |
| staircase down | 4..6, 3..5, 2..4 | 1 | NO, NO, NO, UNDECIDED | Strict fall; bearish endpoints touch exactly. |
| zigzag | 4..8, 2..11, 4..8 | 1 | YES, YES, NO, NO | Both middle extremes strictly exceed their neighbours outward. |
| inside bar | 2..10, 4..8, 2..10 | 1 | NO, NO, NO, NO | Middle range lies inside both endpoint ranges. |
| outside bar | 4..8, 2..10, 4..8 | 1 | YES, YES, NO, NO | Middle range encloses both neighbours. |
| doji | 3..7, 2..8, 3..7 | 1 | YES, YES, NO, NO | Middle open and close both 5; wick extremes alone matter. |
| jump | 1..3, 7..9, 11..13 | 1 | NO, NO, YES, NO | Ranges jump upward; bullish bounds are 3 and 11. |
| last candle open | 4..8, 2..10, 4..8 | 1 | PENDING, PENDING, NO, NO | Both swing comparisons strict but C3 is not closed; FVG has no closure rule. |
| missing first/last | 4..8, 2..10, 4..8 | 0,2 | TEXT_SILENT in each direction | Q_EDGE_LEFT / Q_EDGE_RIGHT: the required neighbour is absent. |
| upper wick spike | 5..10, 5..20, 5..11 | 1 | YES, UNDECIDED, NO, NO | Only the high spikes; equal lows are unresolved. |
| adjacent opposite candidates | 4..10, 5..12, 2..10, 4..11 | 1 | YES, NO, NO, NO | First candidate is a strict high; endpoint ranges overlap. |
| adjacent opposite candidates | same sequence | 2 | NO, YES, NO, NO | Next candidate is a strict low; endpoint ranges overlap. |
| overlapping consecutive gaps | 0..2, 3..5, 6..8, 9..11, 12..14, 15..17 | 1,2,3,4 | NO, NO, YES, NO | Consecutive bullish zones are [2,6], [5,9], [8,12], [11,15]. |
| bull gap touched/filled later | 1..3, 4..6, 7..9, 6..10, 1..8, 0..2 | 1 | NO, NO, YES, NO | Original zone [3,7] is touched, filled, then closed through; no reference invalidation rule. |
| bear gap touched/filled later | 17..19, 14..16, 11..13, 10..14, 12..19, 18..20 | 1 | NO, NO, NO, YES | Original zone [13,17] is touched, filled, then closed through; no reference invalidation rule. |

## C. Metamorphic tests

Run on every complete interior window in all three A series, all four directions; also run on the full shape fixtures where a complete window exists. Count each relation as one case and check every returned record under F.

1. Add integer `137` to open/high/low/close: same statuses and translated bounds.
2. Multiply all four prices by positive integer `7`: same statuses and scaled bounds.
3. Mirror about integer `K=200`: open/close become `K-price`; high becomes `K-old_low`, low becomes `K-old_high`. Compare SH↔SL and bull↔bear at the same index, with reversed transformed FVG bounds.
4. Prepend three FIXTURE candles with ranges `-9..-7`, `-6..-4`, `-3..-1`: existing complete-window indices shift by three; statuses and bounds remain unchanged. Originally missing-neighbour observations are not asserted to stay unchanged when a neighbour is supplied.
5. Append FIXTURE ranges `60..62`, `63..65`, `66..68`: every earlier complete window stays unchanged. Separately, an open strict-swing C3 remains pending when an unrelated candle is merely appended; after C3 is explicitly closed and a candle is appended, the strict result resolves to YES. An absent neighbour is not silently reclassified as PENDING.
6. Fixed seed `56789`: for each A series run 50 trials, select `t` from `1..length-3`, replace *all* candles strictly after `t+1` with fresh valid integer FIXTURE candles, and compare all four results at every complete index `1..t`. This checks no lookahead beyond the required C3, not merely an unchanged last candle.

## D. Brute-force independent oracle

Implement the reference inside the runner from §4/§5, without importing or copying implementation predicates. It returns a status or the explicit text-silence question; FVG bounds are independently computed only for `YES`. Check the handwritten A/B values against the text during plan review, not by retrospectively editing them. Do not turn a PRECEDENCE_CHOICE observation into a match or mismatch.

- Exhaustive: each candle has `1 <= low <= high <= 4`, both values integers; `open=low`, `close=high`, and independently `closed=false/true` for **each** of C1, C2 and C3. This is `20^3 = 8000` three-candle FIXTURE windows, four concept observations each. Test all, including the 8 closure combinations.
- Random: local `random.Random(12345)`; 2000 FIXTURE series; length `randint(5,40)`; for each candle in order: `low=randint(1,40)`, `high=randint(low,low+12)`, `open=randint(low,high)`, `close=randint(low,high)`, and `closed=choice([True,False])`. Compare all four concepts at every complete middle index. Record the total and all status/bounds mismatches. Group any priority-dependent observations in PRECEDENCE_CHOICE.
- Report whether every **text-decided** observation agreed, and separately report the number of priority-dependent observations for which the text provides no oracle answer. Do not claim agreement on the latter.

## E. Invalid / underspecified input

Exercise each probe against all four directions, catch and report the actual error or status without changing engine code. One line per probe includes all four outcomes, with `Q_INVALID` tailored to the exact probe. Probes: high < low; each of open/high/low/close/closed missing; each numeric price field non-numeric; `None` list, `None` candle, `None` high and `None` low; empty list; one candle; two candles; indices `-1`, length, and `99`. Classify explicit errors, returned statuses, and silently accepted malformed inputs without declaring the text prescribes one. Examine both input immutability and repeated-run determinism, even on errors.

## F. Output and execution contracts

On **every** returned record from every test and each repeated invocation: `TIER2`, appropriate source IDs present (SH A1/A4/A5; SL A1/A5; FVG B1/B2/B3/B4), no forbidden name in its serialized form, `WEAK_SUPPORT` on every SL and `INVALIDATION_UNDECIDED` on every FVG. Check full input deep equality before and after, and identical outputs/errors on two runs. Any violation is a separate F failure with expected versus actual. Check all event-time results and direct results when both exist, and do not suppress F checks for TEXT_SILENT status observations.

## Execution and reporting

Commit this plan and `hard_expectations.json` alone before reading any code. Do not edit either afterward. Then inspect the implementation read-only, write an offline standard-library runner, and write `HARD_RESULTS.md`: per-family counts and one line per failure, E probe, and PRECEDENCE_CHOICE group, including expected versus actual or exact unanswered question and observed returns. Store voluminous per-observation logs outside the repository and include their SHA-256. Commit only the runner and results in the second commit.
