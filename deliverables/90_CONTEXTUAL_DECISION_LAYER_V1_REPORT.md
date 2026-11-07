# 90 — Contextual Decision Layer V1 (BUILD REPORT)

**Task**: build the missing contextual decision layer — for every valid
as-of snapshot produce (1) ONE primary working interpretation chosen from
the evidence (alternatives visible, never a list-only dodge), (2) ONE
explicit analytical state, (3) a concise why / opposed / would-change
explanation — using a local context-conditioned model over chronological
historical episodes of predefined observable events, with future data
used ONLY as training/evaluation labels.

---

## 1. Branch / commits

| item | value |
|---|---|
| branch | `arena/a41fd997-trading-bot` |
| task start (discovered state) | workspace had been reset to base `c905f2b` with the working tree untracked; **recovered** per the proven procedure (backup tar → `git fetch` → `git reset --hard FETCH_HEAD`, untracked files untouched) to the expected commit `a3c8bb216783b92996e8a582fab1fd83a81aaad0` (= remote). Discrepancy reported before any code change. |
| code commit (result #1) | **`07df71371d5b8cd0a1782ff7ca8de66aa79ee3a8`** — decision layer + tests + runner |
| artifacts commit (result #2) | this report + `docs/research/decision_v1/run_artifacts/` (see git log) |
| sealed `information_time.py` sha256 | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` — unchanged, verified before/after |
| `git diff --check` | clean |
| preserved | the selector, the analysis lifecycle, the ledger, all causal interfaces, all previously reported fixes and their tests — untouched (the decision layer CONSUMES their records; the earlier verification's `run_context` lesson is applied to the new records: every decision carries `run_context: "historical-replay"` and states a replay is never an actual live observation) |

## 2. Changed files

| file | what |
|---|---|
| `src/trading_system/research/contextual_selection/decision_layer.py` | **new** — events, context extraction, episode labeling, context-conditioned event model, decision function, chronological evaluation |
| `tests/test_contextual_decision_layer.py` | **new** — 8 focused tests (task-required 7 + event-definition guard; incl. a regression for the reproduced UNRESOLVED-misuse defect) |
| `docs/research/decision_v1/run_contextual_decision_v1.py` | **new** — `--at` and `--run` over the real BTCUSDT mirror |
| `docs/research/decision_v1/run_artifacts/*` | **new** — run outputs (§5) |
| `deliverables/90_CONTEXTUAL_DECISION_LAYER_V1_REPORT.md` | this report |

## 3. What the layer produces (per valid snapshot)

**Decision record** (`decisions_v1.jsonl.gz`): `decision_id`,
`analysis_id/version`, `as_of` key, `run_context`, **`state`**, **one
primary working interpretation** (+ `primary_is_baseline` flag when the
evidence does not distinguish and the structural baseline is the working
view), material alternatives, **named event** + its operational
definition, **next discriminating observation**, **explanation**
(`why` / `opposed` / `would_change`), model ranking + support counts +
status, already-observed conditions (with `observed_before_record`
flags), context tuple, `position_status: absent`,
`selection_quality: NOT_ESTABLISHED`, limitations.

**States** (one per snapshot): `SCENARIO_DEVELOPING` · `AWAITING_EVENT` ·
`EVENT_OCCURRED` (watched condition already occurred → the analysis is
updated, never awaited) · `PRIOR_VIEW_WEAKENED_OR_INVALIDATED` ·
`NO_EDGE` (evidence does not distinguish the scenarios + named next
discriminator) · `UNRESOLVED` (**only** for invalid/insufficient required
input).

**Decision method** — no recipe, no thresholds, no invented weights, no
random tie-breaker:
* **Predefined observable events** with operational detectors over the
  existing SP-03/F-K machinery:
  `E-VIOLATION` (SP-03 close beyond the falsifier reference on its
  falsifying side — the analysis layer's forecast condition) → supports
  the alternative; `E-CONTINUATION` (SP-03 close beyond the last leg's
  end extreme in the leg's direction) → supports the primary;
  `E-NONE-IN-HORIZON` / `E-AMBIGUOUS-SAME-BAR` (both bindings first on
  the same bar) → neutral/unresolved cases.
* **Context** (causal, as-of only): last completed leg direction ·
  reference status · SP-05 1h containment state · forecast status.
* **Model**: per-context event frequency table fitted on chronological
  episodes (no smoothing). Ranking is ORDINAL with support counts and is
  labeled **`provisional-unvalidated`**; probabilities are NOT emitted
  (not calibrated on a versioned out-of-sample set). Ties are explicit
  and are never broken arbitrarily — a tie yields NO_EDGE.
* **Labels**: the first predefined event in a declared research horizon
  (`EPISODE_HORIZON_BARS = 24` task-scale bars — declared experimental
  configuration, not a market rule) AFTER the as-of. Labels enter ONLY
  training/evaluation. Decisions at time T use an **expanding training
  window**: only episodes whose label windows closed strictly before T.
* **No trade profit/loss label exists anywhere**: "win/loss" in the
  evaluation means scenario continuation/violation only.

## 4. Defect reproduced and fixed (smallest fix + regression test)

The first real-data run reproduced a violation of the task rule *"Do not
return generic UNRESOLVED merely because no binding preference exists"*:
8 snapshots whose falsifier reference was merely **unresolved** (a tie
among candidates, no binding preference) were decided `UNRESOLVED`, even
though a completed leg and a directional scenario existed.

* **Smallest fix** (`decision_layer.py`): accept the analysis layer's
  `I-scenario` interpretation as the working view when `I-primary` is
  absent, and reserve `UNRESOLVED` for `INSUFFICIENT_CONTEXT` (no
  completed task-scale leg). Unresolved-reference snapshots now decide
  `NO_EDGE` with the named discriminator (the two operational bindings +
  reference resolution).
* **Regression test**: `test_no_edge_with_named_discriminator_not_vague_abstention`
  covers an unresolved-reference record (completed leg + MP-UNRESOLVED
  reason) and asserts `NO_EDGE` + both event names, while an
  insufficient-input record still asserts `UNRESOLVED`.
* After the fix, real-data `UNRESOLVED` count dropped 8 → 4 (= exactly
  the four `INSUFFICIENT_CONTEXT` boundaries).

## 5. Commands, actual output, provenance

### 5.1 The run (real BTCUSDT data, 60 daily boundaries)

```
cd project/trading_project/docs/research/decision_v1
PYTHONPATH=../../src /home/user/work/venv/bin/python run_contextual_decision_v1.py \
  --run --mirror-dir /home/user/work/data/btc/mirror \
  --from 2025-08-01 --to 2025-09-30
```

60 analysis records (19.8 s) + 60 decisions. **Decision states:**

| state | count |
|---|---|
| EVENT_OCCURRED | 20 |
| SCENARIO_DEVELOPING | 12 |
| AWAITING_EVENT | 10 |
| NO_EDGE | 7 (frequency 0.1167 — **never counted as success**) |
| PRIOR_VIEW_WEAKENED_OR_INVALIDATED | 7 |
| UNRESOLVED (insufficient input only) | 4 |

NO_EDGE reasons (reported, per task): 5 × model support
`continuation=0 vs violation=0` (context not yet in training), 2 ×
`continuation=6 vs violation=6` (explicit tie). Working interpretations
genuinely differ across contexts — the run picks `I-primary` and `I-alt`
in different snapshots (e.g. 09-01..09-08 → I-primary; 09-15..09-26 →
I-alt).

Example decision (`--at "2025-09-15 00:00:00+00:00"`):

```
### decision DEC-decision-v1-0045 — as of 2025-09-15 00:00:00+00:00 [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — the down structure is exhausted
    and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is
    strictly beyond the current falsifier reference level on the
    falsifying side (SP-03 close-based binding; equality is not a crossing)
  why: causal context: {'direction': 'down', 'ref_status': 'selected',
       'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence: continuation=6, violation=10 (ranked,
       provisional-unvalidated ranking)
  opposed: continuation without a close-based violation of
       PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — ...
model: provisional-unvalidated; support continuation=6/violation=10
position status: absent | selection_quality = NOT_ESTABLISHED
```

### 5.2 Out-of-sample evaluation (chronological; later data only)

`decision_eval_v1.json`: 32 training episodes (as_of ≤ 2025-09-10) vs
**17 strictly later** evaluation episodes (as_of ≥ 2025-09-11), 11
excluded (4 insufficient-input + 7 censored label windows — labels never
guessed).

| metric | value |
|---|---|
| coverage (strict ranking produced) | 1.00 (17/17) |
| top-1 event hits | 10 |
| misses | 7 |
| **hit rate (covered & overall)** | **0.588** |
| eval label distribution | E-VIOLATION 10 · E-CONTINUATION 6 · E-AMBIGUOUS-SAME-BAR 1 |

**Honest reading of these numbers**: the majority-class base rate on the
eval set is also 10/17 = 0.588. The model's top-1 hit rate does **not**
demonstrate discrimination beyond the base rate on 17 episodes. The
ranking is therefore reported as **PROVISIONAL and UNVALIDATED**, is
**not calibrated** (no probabilities are emitted anywhere), and the layer
is **NOT ready for trade execution**. This is the task's "bounded
decision path with provisional ranking" outcome, run and reported as
instructed — frequent NO_EDGE results are reported with reasons and are
never counted as success.

### 5.3 Provenance (`decision_manifest_v1.json`)

| item | value |
|---|---|
| dataset commit | `27c9be705ac9280248672c895082c057b979ebff` |
| `BTCUSDT_1m_2025-08.csv` sha256 | `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` ✅ matches expected |
| `BTCUSDT_1m_2025-09.csv` sha256 | `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` ✅ matches expected |
| final source commit | `07df71371d5b8cd0a1782ff7ca8de66aa79ee3a8` |
| sealed `information_time.py` | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` |
| dependency versions | python 3.11.2, numpy 1.26.4, pandas 2.2.3, pytest 8.3.5, tzdata 2026.6 |
| config | BTCUSDT, task scale 4h (k=5 research configuration), episode horizon 24 bars (declared research configuration — NOT a market rule), train fraction 2/3 chronological |

### 5.4 Tests

```
# focused (pinned env: python 3.11.2 / numpy 1.26.4 / pandas 2.2.3 /
# pytest 8.3.5 / tzdata 2026.6)
PYTHONPATH=src python -m pytest tests/test_contextual_decision_layer.py -q
→ 8 passed

# full suite
PYTHONPATH=src python -m pytest tests/ -q
→ exit 0 (all tests pass; pre-existing warnings only)
```

| task-required coverage | test |
|---|---|
| different causal contexts → different working interpretations | `test_different_contexts_different_working_interpretations` |
| valid snapshot → specific working decision (not an empty candidate list) | `test_valid_snapshot_specific_decision` |
| unresolved evidence → explicit NO_EDGE + named next discriminator (UNRESOLVED only for invalid/insufficient input) | `test_no_edge_with_named_discriminator_not_vague_abstention` |
| future data cannot alter an earlier analysis | `test_future_data_cannot_alter_earlier_analysis` (byte-identical record + decision; every fitted label window closed before the decision) |
| later evidence revises without rewriting the earlier record | `test_later_evidence_revises_without_rewriting` |
| condition already present at startup is not a pre-event prediction | `test_condition_already_present_not_predicted` |
| out-of-sample evaluation chronological + no trade-profit labels | `test_eval_chronological_no_profit_labels` |

## 6. What the layer does / does not do

**Does**: pick one working interpretation per snapshot; state the
analytical posture explicitly (incl. NO_EDGE with a named discriminator);
explain why/opposed/would-change; learn context-conditioned event
propensities from chronological episodes; evaluate on later data with
chronological separation; report coverage, results, and NO_EDGE
frequency with reasons honestly.

**Does NOT**: decide trades / create orders / connect execution / size
positions; emit probabilities (not calibrated); use fixed recipes,
invented thresholds/weights, or random tie-breakers; use trade
profit/loss (or any outcome beyond structural event identity) as truth;
let future observations enter features, analysis, or forecasts at an
earlier as-of; claim exact replication of Michael Huddleston, proven
accuracy, or profitability. Historical replay records are marked
`run_context: "historical-replay"` — a replay is never an actual live
market observation.

## 7. Remaining limitations

1. **The ranking is not validated**: 17 out-of-sample episodes; top-1
   hit rate (0.588) equals the majority base rate — no demonstrated
   discrimination. Not ready for trade execution.
2. No calibration set exists on this data span; probabilities are
   therefore not emitted at all (ordinal ranking only).
3. 11 of 60 snapshots could not form labeled episodes (4 insufficient
   input + 7 censored horizons near the data end) — reported as
   exclusions, never guessed.
4. `EPISODE_HORIZON_BARS = 24`, k=5, train fraction 2/3 are declared
   research configurations; sensitivity across these is untested.
5. Context buckets are coarse (4 categorical features); larger history
   would be needed to thicken per-context support — this is reported as
   model support counts in every decision, not hidden.

`selection_quality = NOT_ESTABLISHED` throughout.
