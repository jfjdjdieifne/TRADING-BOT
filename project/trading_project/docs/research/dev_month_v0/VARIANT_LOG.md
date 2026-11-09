# VARIANT LOG — dev month `V0`

| # | variant | configuration | status |
|---|---|---|---|
| 1 | **R0 default configuration, no changes** | gate `v1`, fill mode `next_open`, `TASK_SCALE=1h`, `READINGS_SCALE=15m`, `K=5`, `HORIZON_BARS=12`; no threshold, rank cutoff, risk or cost constant altered | attempted once on 2021-03; run aborted by the kernel (out of memory) before the first decision — see `SUMMARY_V0.md` |

No second entry exists. No variant was run twice. No parameter was changed after the attempt.

## What this does NOT establish

- It does not establish that `R0` was executed: the attempt produced no decision and no plan.
- It does not establish that any other variant would fit in the available memory; none was tried,
  and trying one after a failed run is exactly what the task forbids.
