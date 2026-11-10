# SAMPLING RULE — declared before any plan was opened

Written and committed **before** a single plan id was read. Nothing below depends on any result.

## Population

The 12 M1/M2 runs (`2021-09`, `2021-07` × `v1`, `V2-0`, `V2-A`, `V2-B`, `V2-A-OFF`, `V2-B-OFF`)
and, for aggregate checks only, the three IN_SAMPLE `2021-06` runs. Each run's population is its
`plans_final.jsonl` (one record per arming event).

## Three plans per run, `ENGINEERING_CHOICE`

| pick | rule |
|---|---|
| (a) random | the plan at index `random.Random(seed_a).randrange(n)` of the population sorted by `plan_id`, where `seed_a = int(sha256("TRADE_DETAIL_V2|<run_id>|random")[:8], 16)` and `run_id = "<month>_<variant>"` |
| (b) best | the plan with the **highest** `r_measured`; ties broken by the smaller `plan_id` |
| (c) same-bar | the plan at index `random.Random(seed_c).randrange(m)` of the subset with `trigger_index == exit_index`, sorted by `plan_id`, where `seed_c = int(sha256("TRADE_DETAIL_V2|<run_id>|same_bar")[:8], 16)`; **if that subset is empty**, the plan with the **lowest** `r_measured`, ties to the smaller `plan_id` |

- A plan already selected for the same run is skipped and the draw advances by one index
  (`(index + 1) mod n`) until an unselected plan is found.
- A run with fewer than three plans contributes all of its plans.
- Maximum 36 cards (12 runs × 3).

The seeds are reproduced in `SELECTION.json` beside the cards, with the draw indices and the plan ids,
so anyone can recompute the selection from the saved `plans_final.jsonl` files.

## What this does NOT establish

- It does not make the sample representative: (b) is deliberately an extreme, and (c) over-represents
  the failure mode that motivated the experiment.
- It does not authorise inference: three cards describe three plans, not a run.
