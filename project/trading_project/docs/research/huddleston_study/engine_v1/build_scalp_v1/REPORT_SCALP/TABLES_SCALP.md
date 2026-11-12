# SCALP v1 — predeclared statistical report

**Declared tests: 20; rows: 20.** All declared tests were run. Day-cluster bootstrap B=10000; paired, day-cluster sign permutation=10000; Holm correction over all 20 tests.

The experimental unit is an event; for each event, its outcome is compared with the mean of that event's same-hour, same-month matched controls. Confidence intervals and permutation preserve within-day clustering. MDE is reported as the 95% interval half-width, not a claim of detectability at a chosen effect size.

## Declared family: all 20 tests

| Month | Form | Metric | n events | n days | Event mean | Matched-control mean | Paired difference | 95% paired cluster CI | MDE (half-width) | Perm p | Holm p | LODO signs |
|---|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| 2021-06 | 1 | excess_hit | 1 | 1 | 0.4882 | -0.3118 | 0.8000 | — | — | 1.0000 | 1.0000 | [] |
| 2021-06 | 1 | mean_r | 1 | 1 | 0.9539 | -0.6092 | 1.5631 | — | — | 1.0000 | 1.0000 | [] |
| 2021-06 | 2 | excess_hit | 3 | 3 | -0.4014 | -0.2681 | -0.1333 | [-0.4000, 0.0000] | 0.2000 | 1.0000 | 1.0000 | [-1, -1, -1] |
| 2021-06 | 2 | mean_r | 3 | 3 | -1.0000 | -0.6381 | -0.3619 | [-1.0857, 0.0000] | 0.5428 | 1.0000 | 1.0000 | [-1, -1, -1] |
| 2021-07 | 1 | excess_hit | 2 | 2 | -0.1446 | -0.3446 | 0.2000 | [0.0000, 0.4000] | 0.2000 | 1.0000 | 1.0000 | [1, 1] |
| 2021-07 | 1 | mean_r | 2 | 2 | -0.3929 | -0.6358 | 0.2428 | [0.0000, 0.4857] | 0.2428 | 1.0000 | 1.0000 | [1, -1] |
| 2021-07 | 2 | excess_hit | 1 | 1 | -0.3421 | 0.2579 | -0.6000 | — | — | 1.0000 | 1.0000 | [] |
| 2021-07 | 2 | mean_r | 1 | 1 | -1.0000 | 0.7539 | -1.7539 | — | — | 1.0000 | 1.0000 | [] |
| 2021-09 | 1 | excess_hit | 6 | 4 | -0.1201 | -0.1118 | -0.0083 | [-0.2625, 0.5000] | 0.3812 | 1.0000 | 1.0000 | [1, -1, 1, -1] |
| 2021-09 | 1 | mean_r | 6 | 4 | -0.3316 | 0.0191 | -0.3507 | [-1.2200, 1.1018] | 1.1609 | 0.7583 | 1.0000 | [-1, -1, 1, -1] |
| 2021-09 | 2 | excess_hit | 3 | 2 | 0.2312 | -0.1355 | 0.3667 | [-0.4000, 0.7500] | 0.5750 | 1.0000 | 1.0000 | [-1, 1] |
| 2021-09 | 2 | mean_r | 3 | 2 | 0.8728 | -0.3075 | 1.1804 | [-0.6728, 2.1069] | 1.3899 | 1.0000 | 1.0000 | [-1, 1] |
| 2021-10 | 1 | excess_hit | 1 | 1 | -0.2182 | -0.0182 | -0.2000 | — | — | 1.0000 | 1.0000 | [] |
| 2021-10 | 1 | mean_r | 1 | 1 | -1.0000 | -0.0833 | -0.9167 | — | — | 1.0000 | 1.0000 | [] |
| 2021-10 | 2 | excess_hit | 0 | 0 | — | — | — | — | — | 1.0000 | 1.0000 | [] |
| 2021-10 | 2 | mean_r | 0 | 0 | — | — | — | — | — | 1.0000 | 1.0000 | [] |
| 2021-11 | 1 | excess_hit | 4 | 4 | -0.0224 | -0.1974 | 0.1750 | [-0.2500, 0.6000] | 0.4250 | 0.5026 | 1.0000 | [1, 1, 1, 1] |
| 2021-11 | 1 | mean_r | 4 | 4 | -0.1780 | -0.2938 | 0.1158 | [-0.9118, 0.9864] | 0.9491 | 1.0000 | 1.0000 | [-1, -1, 1, 1] |
| 2021-11 | 2 | excess_hit | 6 | 6 | -0.0952 | -0.2619 | 0.1667 | [-0.1000, 0.4667] | 0.2833 | 0.4993 | 1.0000 | [1, 1, 1, 1, 1, 1] |
| 2021-11 | 2 | mean_r | 6 | 6 | -0.3444 | -0.4349 | 0.0905 | [-0.4243, 0.5545] | 0.4894 | 0.7485 | 1.0000 | [-1, 1, 1, 1, 1, 1] |

## Decision labels

| Form | Metric | Label | sign consistency | qualifying months after Holm + CI + LODO |
|---:|---|---|---:|---|
| 1 | excess_hit | **UNDERPOWERED** | 0.60 | [] |
| 1 | mean_r | **UNDERPOWERED** | 0.60 | [] |
| 2 | excess_hit | **UNDERPOWERED** | 0.50 | [] |
| 2 | mean_r | **UNDERPOWERED** | 0.50 | [] |

## Descriptive runs (outside the declared family)

Plain hit rate is shown next to event-level break-even `1/(1+RR)`. These rows do not enter the declared family.

| Month/config | n | hit rate | break-even | mean R net of spread | excess-hit | ambiguous | sub-pip | expired | mean MAE (R) | median bars to T | share reaching half T before stop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021-06|PRIMARY | 4 | 0.2500 | 0.4290 | -0.5115 | -0.1790 | 0 | 0 | 0 | — | 3 | — |
| 2021-06|window_2 | 3 | 0.3333 | 0.4554 | -0.3487 | -0.1220 | 0 | 0 | 0 | — | 3 | — |
| 2021-06|large_body | 5 | 0.4000 | 0.5079 | -0.3664 | -0.1079 | 0 | 0 | 0 | — | 4.0 | — |
| 2021-06|large_loose | 7 | 0.4286 | 0.5718 | -0.4090 | -0.1432 | 0 | 0 | 0 | — | 1 | — |
| 2021-06|shorts | 7 | 0.8571 | 0.4370 | -2.9056 | 0.4202 | 0 | 0 | 0 | — | 6.0 | — |
| 2021-07|PRIMARY | 3 | 0.3333 | 0.5438 | -0.5953 | -0.2104 | 0 | 0 | 0 | — | 8 | — |
| 2021-07|window_2 | 3 | 0.3333 | 0.5438 | -0.5953 | -0.2104 | 0 | 0 | 0 | — | 8 | — |
| 2021-07|large_body | 2 | 0.5000 | 0.6446 | -0.3929 | -0.1446 | 0 | 0 | 0 | — | 8 | — |
| 2021-07|large_loose | 5 | 0.2000 | 0.4306 | -0.7572 | -0.2306 | 1 | 0 | 0 | — | 8 | — |
| 2021-07|shorts | 3 | 0.3333 | 0.4344 | -1.3573 | -0.1011 | 0 | 0 | 0 | — | 3 | — |
| 2021-09|PRIMARY | 9 | 0.4444 | 0.4475 | 0.0699 | -0.0030 | 0 | 0 | 0 | — | 7.5 | — |
| 2021-09|window_2 | 7 | 0.4286 | 0.4814 | -0.0258 | -0.0528 | 0 | 0 | 0 | — | 7 | — |
| 2021-09|large_body | 9 | 0.3333 | 0.4094 | 0.0114 | -0.0761 | 0 | 0 | 0 | — | 7 | — |
| 2021-09|large_loose | 12 | 0.5000 | 0.4070 | 0.3976 | 0.0930 | 0 | 0 | 0 | — | 7.5 | — |
| 2021-09|shorts | 4 | 0.0000 | 0.3375 | -1.0000 | -0.3375 | 0 | 0 | 0 | — | None | — |
| 2021-10|PRIMARY | 1 | 0.0000 | 0.2182 | -1.0000 | -0.2182 | 0 | 0 | 0 | — | None | — |
| 2021-10|window_2 | 1 | 0.0000 | 0.2182 | -1.0000 | -0.2182 | 0 | 0 | 0 | — | None | — |
| 2021-10|large_body | 2 | 0.5000 | 0.3889 | -0.1065 | 0.1111 | 0 | 0 | 0 | — | 3 | — |
| 2021-10|large_loose | 7 | 0.7143 | 0.5125 | 0.1251 | 0.2018 | 0 | 0 | 0 | — | 4 | — |
| 2021-10|shorts | 6 | 0.3333 | 0.5084 | -0.7631 | -0.1750 | 0 | 0 | 0 | — | 3.0 | — |
| 2021-11|PRIMARY | 10 | 0.5000 | 0.5661 | -0.2778 | -0.0661 | 0 | 0 | 0 | — | 2 | — |
| 2021-11|window_2 | 5 | 0.2000 | 0.4705 | -0.7303 | -0.2705 | 0 | 0 | 0 | — | 3 | — |
| 2021-11|large_body | 7 | 0.7143 | 0.6259 | 0.0317 | 0.0884 | 0 | 0 | 0 | — | 2 | — |
| 2021-11|large_loose | 16 | 0.4375 | 0.4838 | -0.2412 | -0.0463 | 0 | 0 | 0 | — | 3 | — |
| 2021-11|shorts | 4 | 0.0000 | 0.3472 | -1.0000 | -0.3472 | 0 | 0 | 0 | — | None | — |

## Exclusions and sensitivities

- 2021-06|PRIMARY: events=7, excluded=3, TARGET_BEHIND_ENTRY=3, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-06|shorts: events=10, excluded=3, TARGET_BEHIND_ENTRY=3, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-07|PRIMARY: events=8, excluded=5, TARGET_BEHIND_ENTRY=5, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-07|shorts: events=8, excluded=5, TARGET_BEHIND_ENTRY=5, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-09|PRIMARY: events=18, excluded=9, TARGET_BEHIND_ENTRY=9, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-09|shorts: events=9, excluded=5, TARGET_BEHIND_ENTRY=5, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-10|PRIMARY: events=5, excluded=4, TARGET_BEHIND_ENTRY=4, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-10|shorts: events=7, excluded=1, TARGET_BEHIND_ENTRY=1, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-11|PRIMARY: events=10, excluded=0, TARGET_BEHIND_ENTRY=0, NO_TARGET_SWING=0, expired=0, sub-pip=0.
- 2021-11|shorts: events=7, excluded=3, TARGET_BEHIND_ENTRY=3, NO_TARGET_SWING=0, expired=0, sub-pip=0.

First-event-per-day paired-difference sensitivity:

- 2021-06|form1|excess_hit: n=1, paired difference=0.8.
- 2021-06|form1|mean_r: n=1, paired difference=1.5631396776956092.
- 2021-06|form2|excess_hit: n=3, paired difference=-0.13333333333333336.
- 2021-06|form2|mean_r: n=3, paired difference=-0.3618876617188264.
- 2021-07|form1|excess_hit: n=2, paired difference=0.20000000000000004.
- 2021-07|form1|mean_r: n=2, paired difference=0.24283133100379778.
- 2021-07|form2|excess_hit: n=1, paired difference=-0.6.
- 2021-07|form2|mean_r: n=1, paired difference=-1.7539388669840423.
- 2021-09|form1|excess_hit: n=4, paired difference=0.13749999999999998.
- 2021-09|form1|mean_r: n=4, paired difference=0.28783035944223756.
- 2021-09|form2|excess_hit: n=2, paired difference=0.175.
- 2021-09|form2|mean_r: n=2, paired difference=0.7170616389479327.
- 2021-10|form1|excess_hit: n=1, paired difference=-0.2.
- 2021-10|form1|mean_r: n=1, paired difference=-0.916720668890176.
- 2021-10|form2|excess_hit: n=0, paired difference=None.
- 2021-10|form2|mean_r: n=0, paired difference=None.
- 2021-11|form1|excess_hit: n=4, paired difference=0.17500000000000004.
- 2021-11|form1|mean_r: n=4, paired difference=0.11579934087905841.
- 2021-11|form2|excess_hit: n=6, paired difference=0.16666666666666666.
- 2021-11|form2|mean_r: n=6, paired difference=0.09051927595472821.

## Measurement availability and fault locator

The five frozen exploratory run bundles predate added MAE / half-target fields, next-bar-open reruns, and the half-body H-level sensitivity. Do not rerun these already-seen months: those measures are unavailable here (bars-to-target is recoverable as bars_held for target hits); they are not silently imputed. The half-body H-level owner sensitivity was omitted from the initial pre-run declarations and is recorded now as not analyzed, not as a valid preregistered result.
The shorts calculation was corrected before the five run bundles were made; its secondary outcomes are included separately, not pooled. The 1B diagnostic implementation now enforces the intervening bullish candle; the earlier 1B records do not reliably establish that condition and are omitted from outcome tables.
The primary family is sparse (many month/form cells have few events or days); MDE intervals are wide and generally do not exclude zero. This is NO_SIGNAL or UNDERPOWERED, not evidence of equivalence.
The detector should be checked against the owner case cards. Any suspected detector issue must be entered in VARIANT_LOG_SCALP.md; no changes or reruns on these seen months are permitted.

## What this does NOT establish

- It does not establish a working strategy, HYPOTHETICAL_ profitability, or performance outside these exploratory samples.
- The exploratory months are seen; one currency pair and one year are represented.
- CANDIDATE_FOR_CONFIRMATION, if ever assigned, would not mean a working strategy.
- The target buffer is an engineering choice and its intent is a knowledge gap.
- MAE, the half-target-before-stop measure, next-bar-open sensitivity, corrected 1B outcomes, and half-body H-level sensitivity were not generated in the frozen runs; no rerun was made on seen months.
- Cards check whether the owner pattern was read correctly, not HYPOTHETICAL_ profitability.
- 2021-10 is IN_SAMPLE; the v3 round on 2021-12 was waived by owner decision.
