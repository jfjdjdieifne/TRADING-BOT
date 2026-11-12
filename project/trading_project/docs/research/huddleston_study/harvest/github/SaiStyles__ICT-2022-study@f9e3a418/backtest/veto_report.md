# Veto test - do the refusals improve what is left?

`dev` slice, 2010-06-06 -> 2021-12-31. **2,962 full sessions.** Ledger n = 36. Reserve untouched, holdout SEALED.

Baseline killzone (08:30-11:00): median opportunity **32 pts**, median efficiency **0.467**.

`z` is how far the result sits outside 2,000 RANDOM refusals of the
same size. **A veto that only matches random is doing nothing**, however
good its median looks - DECISIONS.md section 14.

| veto | params | refused | efficiency all -> traded | z | opportunity all -> traded | z |
|---|---|---|---|---|---|---|
| wednesday_done | - | 40% | 0.467 -> 0.475 | **+1.3** | 32 -> 32 pt | **-2.0** |
| midrange | band=0.05 | 7% | 0.467 -> 0.468 | **+0.6** | 32 -> 32 pt | **-1.0** |
| midrange | band=0.1 | 14% | 0.467 -> 0.468 | **+0.3** | 32 -> 32 pt | **-0.8** |
| midrange | band=0.2 | 30% | 0.467 -> 0.476 | **+1.7** | 32 -> 33 pt | **+0.7** |

Each row is its own hypothesis in `ledger.md`. A sweep of five thresholds
is five, not one - reporting the best of five as a single result is the
error the ledger exists to prevent.

## Refusals he stated that are NOT tested here

Deferred, not dropped. Fourteen of fifteen quietly becoming three is how
41 episodes of reading turns into a toy.

| veto | source | why not yet |
|---|---|---|
| liquidity_order | ep25 [28:36] | Needs a BIAS, which does not exist until the entry stage. The raw observable - which of the prior high/low was taken first - is already computable and should be recorded when bias lands. |
| no_rally_above_either_open | ep21 [17:06] | Both opens are computed here; only the bias is missing. |
| high_resistance_liquidity_run | ep35 [12:07] | Needs candle-structure primitives from the entry stage. |
| no_fvg | ep04 [01:44] | An ENTRY gate, not a day veto - it is evaluated per setup. |
| no_displacement | ep24 [23:12] | Entry gate, and its magnitude has no canonical value - THE-MODEL.md 8.1. Six pre-registered sweep points in ledger.md. |
| one_loss_four_trades_monthly | ep15 [06:42], ep16 [17:26], ep13 [02:05] | Session management - needs realised trades. Belongs with the ep41 money-management ladder, which is the next build step. |
| fomc_nfp | ep23 [15:51], ep37 [04:50] | Needs an ECONOMIC CALENDAR. Not derivable from OHLCV and not in the Databento purchase. This is the one veto blocked by missing data rather than by missing code. |
| sloppy_chart | ep19 [61:04], ep34 [07:34], ep19 [64:56] | NOT CODEABLE, and must not be faked. THE-MODEL.md section 8. Any proxy invented for it would be the reader's rule wearing his name. |
