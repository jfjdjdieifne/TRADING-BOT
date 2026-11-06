# COVERAGE — mechanical keyword counts only

Corpus counted: 280 FULL-tier stored text files (excerpt records are excluded from these counts).
Counting method: Python `re.search` case-insensitive over the raw stored file text, one hit per file per pattern. No interpretation; a mention is not evidence that the file endorses or explains the term.

| keyword family (regex used) | files mentioning | % of files |
|---|---|---|
| liquidity / draw (`liquidit|draw on liquid`) | 155 | 55.4% |
| stops (stop / stop loss) (`\bstops?\b|stop[- ]?loss`) | 131 | 46.8% |
| equal highs / equal lows (`equal high|equal low`) | 44 | 15.7% |
| imbalance / FVG / rebalance (`imbalance|fair value gap|\bfvg\b|rebalanc`) | 144 | 51.4% |
| order block (`order block|\bob\b(?![a-z])`) | 100 | 35.7% |
| market structure shift / displacement (`market structure shift|\bmss\b|displacement`) | 74 | 26.4% |
| dealing range (`dealing range`) | 22 | 7.9% |
| premium / discount / equilibrium (`premium|discount|equilibrium`) | 101 | 36.1% |
| killzone / time of day (`kill ?zone|killzone|time of day|session time`) | 92 | 32.9% |
| target / objective (`\btarget|objective`) | 110 | 39.3% |
| stop / invalidation (`invalidat`) | 53 | 18.9% |
| entry (`\bentry\b|entries`) | 158 | 56.4% |
| no-trade (`no[- ]?trade`) | 20 | 7.1% |
| being wrong (`being wrong|wrong\b`) | 52 | 18.6% |

## Same counts split by source_kind (files only, not percentages)

| keyword family | CODE_REPO | EXPLAINER | BOOK_OR_COURSE |
|---|---|---|---|
| liquidity / draw | 40 | 5 | 110 |
| stops (stop / stop loss) | 43 | 1 | 87 |
| equal highs / equal lows | 5 | 1 | 38 |
| imbalance / FVG / rebalance | 39 | 5 | 100 |
| order block | 33 | 6 | 61 |
| market structure shift / displacement | 15 | 2 | 57 |
| dealing range | 0 | 0 | 22 |
| premium / discount / equilibrium | 20 | 4 | 77 |
| killzone / time of day | 31 | 0 | 61 |
| target / objective | 27 | 1 | 82 |
| stop / invalidation | 9 | 0 | 44 |
| entry | 41 | 2 | 115 |
| no-trade | 7 | 1 | 12 |
| being wrong | 12 | 0 | 40 |
