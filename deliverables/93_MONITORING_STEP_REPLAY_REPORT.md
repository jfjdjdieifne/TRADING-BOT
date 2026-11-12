# 93 — Contextual Market Reasoning + Continuous Monitoring + Causal
#      Step-by-Step Replay (BUILD REPORT)

## 1. Commits / repository state

| item | value |
|---|---|
| branch | `arena/a41fd997-trading-bot` (active) |
| current (start, verified) | `ca6806d35461b5e309b423cf23a564507c2554cd` = remote |
| **resulting code commit** | see git log (`monitor-v1: …`) |
| **resulting artifacts commit** | see git log (this report + run artifacts) |
| working tree at start | a workspace wipe (9th) had reset local HEAD to the base `c905f2b`; recovered by the proven procedure (backup tar → `git fetch` → `git reset --hard FETCH_HEAD`, untracked untouched) with **zero loss** (backup `diff -rq` clean vs restored tree); discrepancy reported before any change |
| sealed `information_time.py` | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` — untouched (verified before/after) |
| data | dataset commit `27c9be705ac9280248672c895082c057b979ebff`; `BTCUSDT_1m_2025-08.csv` `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` ✅; `BTCUSDT_1m_2025-09.csv` `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` ✅ |
| environment | python 3.11.2, numpy 1.26.4, pandas 2.2.3, pytest 8.3.5, tzdata 2026.6 |

## 2. What already existed (reused) vs what is new

**Reused, not rebuilt**: `market_understanding.price_path.`
`CausalObservationStream` (the existing strict causal observation/
ingestion interface: OHLC legality fail-closed, strictly increasing
availability keys, same-batch chronology UNPROVEN) — every consumed
observation is validated through it; `intrabar_path_metrics` (the
existing `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)` rule);
`AnalysisEngine` (deterministic boundary recomputation);
`InterpretationLedger` (immutable versions + real SP-20 propagation);
the analysis runner's completion-label frame convention and snapshot
mechanism; the decision/plan layers unchanged.

**New (the missing path)**: `ReplayObservationStream` (one-observation-
at-a-time replay; the engine sees only the prefix + approved time grid),
`MonitoringLoop` (incremental loop with WHAT-changed / WHY / WHICH-
evidence change reports, no-fabricated-change rule, same-bar sequence
unresolved notes, save/resume in a fresh process), `completed_bars_only`
(only completed bars are completed), `DATA_CAPABILITIES` /
`CONCEPT_REGISTER` / `LIVE_FEED_STATUS` registers, the step-replay
driver, `docs/research/monitor_v1/CONCEPTS_AND_LIMITS_V1.md`, 12 tests.

## 3. Exact commands

Single analysis (existing runner, reused):
```
cd project/trading_project/docs/research/analysis_v1
PYTHONPATH=../../src python run_market_analysis_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --at "2025-08-14 00:00:00+00:00"
```

Step-by-step historical replay (new):
```
cd project/trading_project/docs/research/monitor_v1
# pause at boundary T (fresh run; analysis uses only information at T)
PYTHONPATH=../../src python run_step_replay_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --stop-at "2025-08-14 00:00:00+00:00" --state /tmp/replay_state.json
# advance one completed bar (fresh process)
PYTHONPATH=../../src python run_step_replay_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --resume --state /tmp/replay_state.json --advance 1 --step bar
# advance one observation (1m, the data source's actual resolution)
PYTHONPATH=../../src python run_step_replay_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --resume --state /tmp/replay_state.json --advance 1 --step observation
```

## 4. Actual output — stopped decision and subsequent update

**Stop at 2025-08-14 00:00 UTC** (18,719 observations consumed; 18,720
steps; 77 material changes; 21 s):
```
== stopped at 2025-08-14 00:00:00+00:00 (18719 observations consumed) ==
lifecycle: INVALIDATED | state: selected
forecast FC-replay-step-v1-0002 v2: condition_observed (observed_before_record=False)
forecast FC-replay-step-v1-0004 v2: condition_observed (observed_before_record=False)
forecast FC-replay-step-v1-0001 v1: pending (observed_before_record=False)
forecast FC-replay-step-v1-0003 v1: pending (observed_before_record=False)
```
**Subsequent update** (fresh process, one completed bar):
```
== resumed /tmp/replay_state.json at cursor 18719 (2025-08-13 23:59:00+00:00) ==
[step 18960] task-boundary obs=2025-08-14 03:59 as_of=2025-08-14 04:00
  MATERIAL CHANGE (1):
   - [structural_facts] (subset) -> +5 fact(s)
     why: new completed bars/legs became available
     evidence: ['SF-DIR-…-78', 'SF-AVL-1h-…-78', 'SF-AVL-15m-…-78']
```
**One observation step** (1 m):
```
[step 18961] observation obs=2025-08-14 04:00 as_of=None
  no revision required: no completed task-scale bar closed at this
  observation: incomplete bars are never used and no completed-bar fact
  changed
```
Artifacts: `run_artifacts/step_replay_stop_v1.json`,
`step_replay_resume_v1.json` (per-step reports + data capabilities +
live-feed status).

## 5. Live read-only feed?

**No.** No live market adapter exists in this repository and none was
tested or connected: `LIVE_FEED_STATUS = {"exists": False, …}`;
`LiveFeedAdapter` is an interface contract that raises
`NotImplementedError`.  The loop runs on replayed streams only; the
missing adapter is identified.  This is never described as live-market
monitoring.

## 6. Tests (12 required) — `tests/test_contextual_monitoring.py`

| requirement | test | result |
|---|---|---|
| future data cannot change saved analysis at T | `test_future_data_cannot_change_saved_analysis` | pass |
| step replay never exposes future observations | `test_step_replay_never_exposes_future` (prefix == cursor; tail excluded; record == batch-from-prefix) | pass |
| revision without rewriting previous version | `test_new_observation_revises_without_rewriting` (v1 byte-identical; v2 `revises`) | pass |
| no-change observation creates no fabricated change | `test_no_change_observation_creates_no_fabricated_change` (no analyze call; record count unchanged) | pass |
| already-observed at startup is not a prior prediction | `test_condition_already_observed_at_startup_not_predicted` (mid-move start) | pass |
| saved state resumes in a fresh process | `test_saved_state_resumes_in_fresh_process` (subprocess; same snapshot + same continuation) | pass |
| same-bar ordering unresolved | `test_same_bar_ordering_unresolved` (`AMBIGUOUS_INTRABAR_CHRONOLOGY`; duplicate keys rejected fail-closed) | pass |
| swing/HTF fact not available before confirmation | `test_swing_and_htf_facts_not_available_before_confirmation` | pass |
| same local shape, different context -> different interpretation | `test_same_local_shape_different_context` | pass |
| scale/irrelevant shape details do not decide | `test_scale_and_irrelevant_shape_do_not_decide` (×10 scaling + wick jitter) | pass |
| missing order-book/position/source info honest | `test_missing_information_reported_honestly` | pass |
| real ledger propagation updates dependencies | `test_ledger_propagation_updates_actual_dependencies` (real expert task recomputed; prior version preserved; transitive edge) | pass |

Combined focused suites: **106 passed**.  Full suite: **exit 0** (all
green; pre-existing warnings only).

Defects found and fixed during bring-up (each with a test):
(a) partial resample buckets counted as completed bars (`completed_bars_only`);
(b) engine axis rebuilt per step instead of the approved time grid;
(c) snapshot re-save dropped restored records (round-trip fix);
(d) startup with pending completions skipped analysis under the fast path.

## 7. Source passages verified / claim classes / limits

See `docs/research/monitor_v1/CONCEPTS_AND_LIMITS_V1.md` §4: the ICT
Order Blocks lesson (`https://www.youtube.com/watch?v=PIYh0CxoY9c`)
quotes (definition/validation/entry/stop) as recorded in the pinned
knowledge `jfjdjdieifne/test@6c8bf6fd…` (P1 partial transcript —
**passage times not available**; YouTube is unreachable from this
environment and timestamps were never invented); the invalidation gap
(P-K); the no-target finding (`04_LIQUIDITY`).  Claim classes recorded
(directly-stated / paraphrase / engineering-interpretation /
unsupported-or-unavailable).  Retrospective lessons teach methodology
only; later outcomes never enter earlier simulated decisions.

## 8. Explicit remaining limitations

1. **No live feed** — replayed streams only; the live adapter is missing.
2. OHLC-only: intra-bar order, resting orders, sweeps/rejections, and
   participant intent are not establishable (reported as such).
3. Order-block / FVG zone machinery NOT implemented (G-OB-P not
   runnable: P-N/P-W unset; no owner policy invented).
4. Step granularity is the source resolution (1m) or completed 4h bars;
   the loop is stateful per process but saved/resumed explicitly.
5. The decision layer's ranking remains PROVISIONAL/UNVALIDATED (17
   correlated episodes); research parameters (k=5, horizon 24, train
   fraction) remain declared configurations, never source facts.
6. Hypothetical plans remain research records; entry/objective remain
   declared research configurations (the ICT OB entry technique is
   source-stated but not implemented).

**No trades executed.  No source agreement is claimed to prove market
truth or profitability.  selection_quality = NOT_ESTABLISHED.**
