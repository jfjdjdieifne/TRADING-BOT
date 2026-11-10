# KNOWN DEFECTS in the 2021-06 run — found while reading the case files, not fixed

Nothing here was changed after the run. Each item is recorded with the exact field and one example,
so a future authorised run can fix it without anyone having to trust this note.

| # | where | what is wrong | example | does it change a decision? |
|---|---|---|---|---|
| D1 | `A.3 liquidity map` in every CASE file; `untaken` in `decisions.jsonl` | the `formed_index` of a pool is a **window-local** bar index, but `age_bars` subtracts it from the **global** index, so ages are absurd | `1.22194 high relative_equal_pair, formed at bar 5759, age 25156 bars` | no — the level and the side are right, only the age label is wrong |
| D2 | `A.3`, pools seeded from the higher-timeframe extreme | such a pool carries `formed_index = -1` and therefore `age None` | `1.22542 high higher_timeframe_extreme, formed at bar -1, age None` | no |
| D3 | `A.2 dealing range`, `position_ratio` | the ratio is not clamped to `[0, 1]`; when price is outside the range it exceeds 1 | `position premium, ratio 1.0189` (high `1.22158`, close above it) | no — the `position` label is correct; only the ratio is unclamped |
| D4 | plan identity | a plan that settles on bar *t* can be re-armed on the same zone at *t+1*, so one zone yields several plans | `fvg:bearish:30910` at 06:25 and again at 06:30 on 2021-06-02 | **yes** — it inflates the plan count and correlates outcomes; recorded as variant V1 in `build_v1/VARIANT_LOG.md`, deliberately not applied |

## What this does NOT establish

- It does not establish that fixing D1–D3 changes any R: they are labels, and the entry, stop and
  targets are computed from levels, not from these fields.
- D4 does affect the counts, so the 106 plans must be read as 106 *armings*, not 106 independent reads.
- None of the four was fixed here, because a change made after seeing the month is exactly what the
  authorisation forbids.
