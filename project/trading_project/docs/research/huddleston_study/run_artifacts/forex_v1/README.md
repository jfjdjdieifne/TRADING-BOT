# ⚠️ Pre-fix artifacts — NOT results of the current causal mode

The committed artifacts in this directory (`summary_dev.json`,
`summary_eval_v1.json`, `summary_eval_b0.json`, `cases_*.jsonl`,
`dev_model.json`, `pause_step_2025-03.txt`) were produced by the
**pre-fix, non-causal close-based code** (the `2b4d23e` baseline era,
before the `next_open` fill fix and the intended-direction gate fix).

Evidence, visible in the files themselves:

- the summaries have **no `fill_mode` key** (the current runner always
  records one);
- their `limitations` still say *"close-based hypothetical fills at
  ask/bid of the actual 5m quotes"* — the old event-bar-close fills.

They are kept **unmodified for provenance only**. They must **not** be
read as results of the current causal `next_open` mode or of the fixed
direction gate. No rerun on EUR/USD 5m data has been performed in this
workspace (the data is not present here); deliverables 101–103 are
marked unreproduced for the same reason, and the 102-vs-103 trade-count
discrepancy remains unresolved.

See `HANDOFF_CURRENT.md` at the repository root for the full
verified / not-verified accounting.
