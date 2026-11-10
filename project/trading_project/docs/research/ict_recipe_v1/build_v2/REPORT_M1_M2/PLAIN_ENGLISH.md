# What was tested — in plain English

1. In the first build the trading idea was read entirely from 5-minute candles. The stop that came out of that was about one pip wide.
2. A one-pip stop sits inside a single candle, so 64 of 106 plans were closed on the very candle that opened them.
3. This build tests one change: read the zone, the stop and the targets on a **slower** chart (15-minute, or 1-hour), and use the 5-minute chart only to decide **when price touches** the zone.
4. Everything else is held still: same days, same session window, same entry rule, same costs, same code for tracking the outcome.
5. A control version (V2-0) repeats the first build with only its bookkeeping defects repaired, so the difference between it and the two new versions is the chart the idea is read on.
6. Two months were chosen by a public draw before any data was opened: September 2021 and July 2021.
7. We also ran a "null" version: same entries, same stop and target distances, but the direction flipped by a coin (fixed seed). That shows what geometry and spread alone do.
8. Result, in one table (mean R per plan, hypothetical, after cost):

| month | v1 (5m) | V2-0 (5m + repairs) | V2-A (15m setup) | V2-B (1h setup) |
|---|---|---|---|---|
| 2021-09 | -0.61 | 1.25 | 1.52 | -0.63 |
| 2021-07 | -0.95 | -0.64 | -0.28 | 0.13 |
| null (coin) | -0.39 / -0.29 | — | — | — |

9. The slower chart did what it should mechanically: the stop became wider and fewer plans died on the entry candle. Whether the money result improved is a separate question — see the comparison tables, and note that the intervals are wide and overlap.
10. Nothing here proves anything about the future, and no version is declared the winner.

## What this does NOT establish

- It does not establish that a 15-minute or 1-hour reading is the right one; it measures two months of one instrument.
- It does not establish profitability: R is hypothetical, no position was ever opened, and the sample is small.
