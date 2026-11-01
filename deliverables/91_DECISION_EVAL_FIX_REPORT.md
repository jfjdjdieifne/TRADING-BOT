# 91 — Decision-Layer Evaluation Fix (MINIMAL CHANGE REPORT)

**Task**: fix the two REVISE findings of the read-only review (9386a3e):
(1) evaluation-window leakage between training label windows and the
first evaluated decisions; (2) formalize an ex-ante baseline derived
only from the training period. Plus: disclose/examine the 24-bar research
horizon, preserve honest NO_EDGE decisions, rerun everything.

---

## 1. Commits / hashes / environment

| item | value |
|---|---|
| branch | `arena/a41fd997-trading-bot` (no reset, no force, no PR) |
| audited artifact commit (start) | `9386a3e6d54a3c95f6cba64fd18acc8aab984e17` |
| **fix commit (code + tests)** | **`b4e42fd17e8a766bd8f8b7bdb89aa865a5a79863`** |
| artifacts commit (this report + rerun) | see git log (parent = `b4e42fd`) |
| sealed `information_time.py` sha256 | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` — untouched (verified before/after) |
| `git diff --check` | clean |
| data | dataset commit `27c9be705ac9280248672c895082c057b979ebff`; `BTCUSDT_1m_2025-08.csv` sha256 `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` ✅; `BTCUSDT_1m_2025-09.csv` sha256 `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` ✅ (both match expected) |
| environment | python 3.11.2, numpy 1.26.4, pandas 2.2.3, pytest 8.3.5, tzdata 2026.6 |
| preserved | decision layer, analysis lifecycle, selector, sealed interfaces, all prior tests — untouched. **Decisions JSONL byte-identical to the audited artifact `9386a3e`** (verified with `cmp` against `git show`) |

## 2. Changes (minimal)

| file | change |
|---|---|
| `src/trading_system/research/contextual_selection/decision_layer.py` | `chronological_split(..., return_purged=True)`: purge rule + purged list; `evaluate_ex_ante_baseline()`; `HORIZON_DISCLOSURE` constant |
| `tests/test_contextual_decision_layer.py` | 3 new tests (T8 leakage purge, T9 ex-ante baseline, T10 horizon disclosure) + user-facing NO_EDGE/baseline text assertions in T3 |
| `docs/research/decision_v1/run_contextual_decision_v1.py` | purge reporting, baseline beside model, horizon disclosure in eval json + manifest |

Nothing else changed. No duplication of the sealed causal foundation.

## 3. Finding 1 — evaluation-window leakage: FIXED

**Rule now enforced**: a training episode is fitted for a reported
evaluation ONLY if its label window closed **strictly before the first
evaluated decision**. Overlapping episodes are **purged and reported**.

Real-data purge (`run_artifacts/decision_eval_v1.json →
purged_overlapping_train_episodes`):

| episode | as_of | window_end | verdict |
|---|---|---|---|
| EP-decision-v1-0037 | 2025-09-07 00:00 | 2025-09-11 00:00 | purged (window closes at first eval decision) |
| EP-decision-v1-0038 | 2025-09-08 00:00 | 2025-09-12 00:00 | purged |
| EP-decision-v1-0039 | 2025-09-09 00:00 | 2025-09-13 00:00 | purged |
| EP-decision-v1-0040 | 2025-09-10 00:00 | 2025-09-14 00:00 | purged |

Separation after purge: `train as_of ≤ 2025-09-06 < eval as_of ≥
2025-09-11; max fitted window_end = 2025-09-10 00:00 < first evaluated
decision`. Fitting set 32 → **28** episodes (eval 17, excluded 11
unchanged).

**Test that fails under the old as-of-only split** —
`test_eval_split_purges_overlapping_train_windows`: fixture episodes
EP-a..EP-e where the as-of-only split trains on [a,b,c] and **b, c leak**
(windows close 01-06/01-07 ≥ first eval 01-05). Demonstrated red state
against the exact 9386a3e logic (leaks = [EP-b, EP-c]); the fixed split
returns train=[EP-a], purged=[EP-b, EP-c] with timestamps, and asserts
the invariant `max(window_end of fitted) < first eval as_of`. Under the
old code the test errors/fails (no `return_purged`; invariant violated).

## 4. Finding 2 — ex-ante baseline: FORMALIZED

`evaluate_ex_ante_baseline(train, eval)`: baseline class = **training-
period plurality**, derived strictly before evaluation outcomes exist;
deterministic (a training tie yields an explicit no-call, never a random
or arbitrary tie-break); the evaluation-set majority is never consulted.
Per-episode predictions and results are reported **beside the model on
the same 17 evaluation episodes** (`ex_ante_baseline` + `model_vs_baseline`
in `decision_eval_v1.json` and the manifest).

**Rerun results (real BTCUSDT data, 17 out-of-sample episodes):**

| | derivation | predicted | hit / n | hit rate |
|---|---|---|---|---|
| model (fit on purged 28-episode train) | context-conditioned event frequencies | per-context ranking | 10 / 17 | 0.5882 |
| **ex-ante baseline** | train labels only {CONT 14, VIOL 13, NONE 1} | `E-CONTINUATION` (all episodes) | 6 / 17 | 0.3529 |

**Honest reading (required)**: the baseline class rests on a **one-
episode margin** (14 vs 13) in a 28-episode training set — a single
reclassification flips it. The model's 0.588 also equals simply
predicting the evaluation-period dominant event (10/17), and the 17
evaluation episodes have **mutually overlapping label windows**
(correlated). **No predictive quality is claimed from this small sample**;
the ranking remains PROVISIONAL and UNVALIDATED, not calibrated
(probabilities still not emitted), and the layer is NOT ready for trade
execution. `selection_quality = NOT_ESTABLISHED`.

Test: `test_ex_ante_baseline_derived_from_train_only` uses a fixture
where the train majority ≠ eval majority and asserts the baseline
predicts the TRAIN majority; a tie fixture asserts deterministic
no-call.

## 5. Horizon disclosure (24 bars)

`HORIZON_DISCLOSURE` (module constant, emitted in every eval json and
manifest): **EPISODE_HORIZON_BARS = 24 is NOT source-grounded, NOT
owner-approved, and NOT a market rule** — a declared engineering
parameter for bounded episode labeling. It determines each label as the
FIRST predefined observable event whose binding occurs on a completed
task-scale bar inside the half-open window
`(as_of_bar, as_of_bar + 24]`. **Censored episodes** (window past the
available data) are excluded and reported — 3 × `2025-09-28/29/30 00:00`
("the realized label is unknown and is never guessed"), plus 8 excluded
for no selected reference/no completed leg (2025-08-02..05, 08-22..24,
09-05). **Sensitivity across alternative horizons remains UNTESTED**: no
other defensible, explicitly declared configuration exists in this
project, and no alternative values were invented or searched to improve
the result (test `test_horizon_disclosure_declared_not_grounded`).

## 6. Honest decisions preserved (item 4)

The decision path was not modified. Verified: `decisions_v1.jsonl.gz`
from the rerun is **byte-identical** to the audited artifact at
`9386a3e`. Decision states unchanged: 20 EVENT_OCCURRED · 12
SCENARIO_DEVELOPING · 10 AWAITING_EVENT · 7 NO_EDGE (frequency 0.1167,
never counted as success) · 7 PRIOR_VIEW_WEAKENED_OR_INVALIDATED ·
4 UNRESOLVED. User-facing NO_EDGE text assertions added (T3): output
contains `NO_EDGE`, `no-edge baseline`, and `not a preferred scenario` —
no forced directional selection anywhere.

## 7. Commands and results

```
cd project/trading_project
PYTHONPATH=src /home/user/work/venv/bin/python -m pytest \
    tests/test_contextual_decision_layer.py -q        → 11 passed
PYTHONPATH=src /home/user/work/venv/bin/python -m pytest tests/ -q
                                                      → exit 0 (all green)

cd docs/research/decision_v1
PYTHONPATH=../../src /home/user/work/venv/bin/python run_contextual_decision_v1.py \
    --run --mirror-dir /home/user/work/data/btc/mirror \
    --from 2025-08-01 --to 2025-09-30
    → 60 records/decisions; purge 4 (reported with timestamps);
      train 28 / eval 17 / excluded 11;
      model 10/17 (0.5882) vs ex-ante baseline 6/17 (0.3529);
      manifest final_source_commit = b4e42fd…
```

## 8. Limitations

1. 17 evaluation episodes, mutually overlapping label windows — nothing
   here establishes predictive quality; ranking provisional/unvalidated.
2. Ex-ante baseline class margin is 14:13 (one episode) — fragile; a
   tie would yield no-call (deterministic rule).
3. Horizon sensitivity untested (§5); k=5 and train fraction 2/3 also
   declared research parameters without sensitivity analysis.
4. Per-decision expanding-window training (unchanged, and already
   leakage-free) differs from the fixed evaluation split; the purge now
   aligns the evaluation with the same strictness.

**No market accuracy, profitability, or replication of Michael
Huddleston is claimed.  No trades executed. 
selection_quality = NOT_ESTABLISHED.**
