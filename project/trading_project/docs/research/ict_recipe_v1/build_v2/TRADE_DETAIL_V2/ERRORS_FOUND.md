# ERRORS FOUND — by counting, HYPOTHESIS on the layer

- sha256 verified: 75 files match, 0 do not

| class | count | what it means | layer to suspect (HYPOTHESIS) |
|---|---|---|---|
| ARITHMETIC | 0 | replay disagrees with the engine's R or reason | execution / accounting |
| CAUSALITY | 0 | a level used before its candle closed | facts |
| GEOMETRY | 2 | a side/level inconsistency (e.g. T1 already traded) | target / selection |
| CONVENTION | 0 | a rule applied differently from the declaration | execution |
| CONCEPT | 0 counted | needs a human expert; listed as questions in section 9 of each card | concept |
| NONE | remaining plans | — | — |

## Examples (at most three per class)

### ARITHMETIC — 0

### CAUSALITY — 0

### GEOMETRY — 2
- `2021-07_V2-A` `plan:2021-07-27T06:15:00+00:00:15m:fvg:bullish:13986`: T1 beyond entry — t1 1.18023
- `2021-07_V2-A-OFF` `plan:2021-07-13T00:15:00+00:00:15m:fvg:bearish:13011`: T1 beyond entry — t1 1.18585

### CONVENTION — 0

## What this does NOT establish

- A class count is a count of flagged records, not of real errors: a FAIL on 'T1 not already traded' may be a legitimate pool that price approached and rejected.
- Every layer assignment is a **HYPOTHESIS**; no defect was fixed and no run repeated.
- 'NONE' rows are not evidence of correctness, only of no flag.
