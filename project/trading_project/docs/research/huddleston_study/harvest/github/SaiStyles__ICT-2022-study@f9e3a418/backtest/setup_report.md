# The gold-standard pipeline - the funnel

`dev` slice, **2,969 sessions**. Ledger n = 124. Reserve untouched, holdout SEALED.

ep41 [16:36]: `fair value gap with an order block and optimal trade entry
is the gold standard`. FVG appears in **36 of 41 episodes**.

**The funnel is the deliverable, not the P&L.** ep24 [17:41]: a setup that
never formed `is the proof, the evidence that the model has validity`.
Per-gate counts are the only way to tell a filter from decoration.

| config | candidates | killzone | liquidity | displacement | shift | discount | OB | OTE | R:R | filled | trades | win | exp R | total R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| disp=0pt | 161,484 | 7,609 | 1,867 | 1,867 | 1,867 | 1,250 | 1,250 | 706 | 706 | 341 | 341 | 35% | -0.120 | -40.8 |
| disp=10pt | 161,484 | 7,657 | 1,915 | 1,642 | 1,642 | 1,101 | 1,101 | 617 | 617 | 275 | 275 | 35% | -0.138 | -37.9 |
| disp=20pt | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| disp=40pt | 161,484 | 7,973 | 2,231 | 527 | 527 | 364 | 364 | 201 | 201 | 79 | 79 | 29% | -0.280 | -22.1 |
| disp=80pt | 161,484 | 8,067 | 2,325 | 215 | 215 | 151 | 151 | 84 | 84 | 36 | 36 | 28% | -0.388 | -14.0 |
| ob=ep03_opening_price | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 26% | -0.157 | -26.8 |
| ob=ep12_series | 161,484 | 7,934 | 2,192 | 1,225 | 1,225 | 760 | 457 | 244 | 244 | 105 | 105 | 29% | -0.316 | -33.2 |
| ob=ep17_last_opposite | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| ote_hi=0.7 | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| ote_hi=0.79 | 161,484 | 7,667 | 1,925 | 958 | 958 | 660 | 660 | 497 | 497 | 190 | 190 | 28% | -0.276 | -52.3 |
| struct_tf=5m | 161,484 | 4,570 | 1,344 | 535 | 535 | 407 | 407 | 264 | 264 | 158 | 158 | 39% | -0.076 | -11.9 |
| struct_tf=15m | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| struct_tf=60m | 161,484 | 5,880 | 1,276 | 984 | 984 | 579 | 579 | 249 | 249 | 60 | 60 | 28% | +0.031 | +1.9 |
| fvg_tf=1m | 953,428 | 23,480 | 5,780 | 2,577 | 2,577 | 1,457 | 1,457 | 485 | 485 | 199 | 199 | 20% | -0.105 | -20.8 |
| fvg_tf=5m | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| fvg_tf=15m | 50,541 | 1,732 | 487 | 300 | 300 | 228 | 228 | 154 | 154 | 73 | 73 | 33% | -0.251 | -18.3 |
| stop=gap | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| stop=leg | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 37% | -0.205 | -35.0 |
| target=leg_extreme | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| target=nearest_pivot | 161,484 | 7,821 | 2,079 | 1,112 | 1,112 | 737 | 737 | 416 | 368 | 146 | 146 | 62% | -0.156 | -22.8 |
| min_rr=0 | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| min_rr=1 | 161,484 | 7,811 | 2,069 | 1,102 | 1,102 | 733 | 733 | 415 | 356 | 134 | 134 | 30% | -0.204 | -27.4 |
| min_rr=2 | 161,484 | 7,917 | 2,175 | 1,208 | 1,208 | 743 | 743 | 418 | 212 | 61 | 61 | 23% | -0.249 | -15.2 |
| no_ob | 161,484 | 7,791 | 2,049 | 1,082 | 1,082 | 733 | 733 | 415 | 415 | 171 | 171 | 31% | -0.245 | -41.8 |
| no_ote | 161,484 | 7,539 | 1,797 | 830 | 830 | 586 | 586 | 586 | 586 | 226 | 226 | 29% | -0.146 | -33.0 |
| no_shift | 161,484 | 7,870 | 2,338 | 976 | 976 | 534 | 534 | 350 | 350 | 207 | 207 | 35% | -0.134 | -27.6 |
| skip_0930 | 161,484 | 7,461 | 1,975 | 1,051 | 1,051 | 699 | 699 | 405 | 405 | 168 | 168 | 31% | -0.247 | -41.5 |

## What each gate's REFUSED setups went on to do

ep24 [17:41]: a setup that never formed `is the proof, the evidence
that the model has validity`. **This is that claim, measured.** Each
refused candidate is given the entry, stop and 2R target the rule would
have used, then executed. Overlap is allowed - these are counterfactuals,
not a portfolio anyone could have held.

**Accepted trades: -0.245R over 171.** A gate earns
its place only if what it threw away did WORSE than that.

| gate | refused | their expectancy | win rate | verdict |
|---|---|---|---|---|
| g2_liquidity_taken | 3,571 | -0.029R | 32% | **threw away BETTER trades** |
| g3_displacement | 635 | +0.111R | 37% | **threw away BETTER trades** |
| g5_gap_in_discount | 252 | -0.089R | 31% | **threw away BETTER trades** |
| g7_ote | 117 | -0.179R | 27% | **threw away BETTER trades** |

## How to read this

**`disp=0pt` is the negative control** (DECISIONS.md 14) - the magnitude gate
switched off entirely. If results barely move across the displacement sweep,
magnitude is not what makes the model work and his structural gates are doing
the job. If they peak sharply, the edge depends on a number **he never gave**
in 41 episodes - a finding about the model, not about the market.

**The three `ob=` rows are three of HIS definitions**, not three guesses:
ep03 [24:28] the opening price of the candle that began the run; ep12 [44:02]
a consecutive series, explicitly `not one candle`; ep17 [11:10] the last
opposite-close candle's body. They are different objects and the corpus never
reconciles them.

**`ote_hi=0.70` vs `0.79`** - the ep41 caption reads `62 to 70`. 0.79 is the
wider ICT value and is not in this corpus. See study/ep41.md.

**Every number here is `dev` only.** Nothing has touched `reserve`, and the
holdout is sealed. A result that looks good here has survived one slice out
of three, with n hypotheses behind it.
