# VARIANT LOG V1 — everything the June 2021 run made me want to change, and did not

Written **after** the one authorised run, so no line here is applied. Every entry is a proposal for
a *future* run, on a *different* month, under a *new* authorisation. Nothing in
`stream_v1.py`, `plan_v1.py`, `wrapper_v1.py` or `report_v1.py` was changed after the run started.

| # | what the run showed | proposed variant | why it was not applied | evidence |
|---|---|---|---|---|
| V1 | a plan that settles on bar *t* is re-armed on the same zone at *t+1*; the same zone produced several plans within 30 minutes (`fvg:bearish:30910` twice, `fvg:bullish:33232` three times) | one plan per zone per lifetime, or a cooldown of N bars after a settlement | it changes the plan count and correlates outcomes; applying it now would be tuning on the result | 106 plans, 96 distinct zones |
| V2 | 63 of 106 plans were settled on their own entry bar because the triggering bar spanned the whole zone to the stop | enter at the zone's mean (the order block's `mean_threshold`) instead of the near edge, or require the trigger bar to close inside the zone | it is a change to the execution model, not to the reading, and it must be measured on a month nobody has looked at | fault locator category `execution assumption / stop` = 63 |
| V3 | `WINDOW_BARS = 5760` is declared, never tested (`DECLARED_CHOICES` row 1 promises a sensitivity design) | 2880 / 5760 / 11520 on the same month, plan-for-plan comparison | burning the one authorised month on a parameter sweep was refused by design | `DECLARED_CHOICES.md` row 1 |
| V4 | 5,544 of 6,336 decisions (87.5 %) fall outside `EURO_0200_0500`; the story state is idle for most of the day | a second window variant (`LONDON_0700_1000`, `NY_1200_1500`) recorded side by side, not chosen | choosing a window after seeing which one produces plans is exactly the tuning the owner forbade | SUMMARY §1 |
| V5 | 21 order blocks were *created*, 2 reached `VALID`; the prerequisite chain is nearly shut | record every prerequisite verdict per block so the chain can be read, before changing any of it | a threshold change on this evidence would be tuning | SUMMARY §2 |
| V6 | measured R:R to T2 reaches 95.0 (median 6.45) — the second draw can sit at the far end of the ranking | report T2 but flag `T2_BEYOND_PLAUSIBLE_RANGE` above a declared cutoff, or drop T2 | the cutoff would be a number invented after seeing the distribution | SUMMARY §3 |

## What this does NOT establish

- It does not establish that any of these six changes would improve anything; not one of them has
  been run.
- It does not establish that the June 2021 result is representative of anything: it is one month,
  one instrument, one reading, with 106 hypothetical plans and no execution.
- The list is not exhaustive; it is what the stored fields made visible.
