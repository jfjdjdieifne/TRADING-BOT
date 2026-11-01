# 89 — Contextual Market-Analysis Engine V1 (BUILD REPORT)

**Task**: build a contextual market-analysis engine — causal trading
intelligence that reads price evidence, forms and revises traceable
interpretations, records conditional forecasts BEFORE the conditions it
awaits, recognizes conditions that already occurred (never claimed as
pre-event predictions), and explains the next awaited observation.

**Scope of this report**: implementation + tests + one real-data
analysis run + one chronological replay of real data.  This is NOT an
audit and NOT a plan; it is the implemented engine plus what it does and
does not do.

---

## 1. Branch / commits

| item | value |
|---|---|
| branch | `arena/a41fd997-trading-bot` |
| task start commit (base) | `398469157024e77550b600a21387755ebe565c00` (= `main` tip at task start; verified = remote) |
| code commit (result #1) | `f1702e9ccbee630d0564ab21bf3421009d8f67ad` — engine + tests + runner |
| artifacts commit (result #2) | see git log (this report + run artifacts) |
| sealed `information_time.py` sha256 | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` (unchanged; verified before and after) |
| `git diff --check` | clean |
| force/reset/overwrite | none (fast-forward commits only, pushed to the designated branch only; no PR) |

Prior chain preserved (not rewritten): `f040ffd` (expert selection V1) →
`9bca73b` + `856c2c3` (V1.1) → `33df36b` + `3984691` (V1.2) →
`f1702e9` (analysis engine V1).

## 2. Changed files

| file | what |
|---|---|
| `project/trading_project/src/trading_system/research/contextual_selection/analysis_lifecycle.py` | **new** — the engine: analysis records (observations → structural facts → interpretations → conditional forecasts → next awaited observation), lifecycle states, source register with claim classes, snapshot save/load, forecast versioning |
| `project/trading_project/tests/test_contextual_analysis_lifecycle.py` | **new** — 12 lifecycle tests (list in §5) |
| `project/trading_project/docs/research/analysis_v1/run_market_analysis_v1.py` | **new** — local runner: `--at` (JSON + explanation) and `--replay` (JSONL + Markdown + provenance manifest) |
| `project/trading_project/docs/research/analysis_v1/run_artifacts/*` | **new** — run outputs (see §4) |
| `deliverables/89_CONTEXTUAL_MARKET_ANALYSIS_ENGINE_V1_REPORT.md` | this report |

Nothing else changed.  The sealed information-time module, the integrity
manifests, the legacy wave-policy values, and the existing
selection/ledger modules are untouched (the engine CONSUMES their
approved interfaces).

## 3. What the engine does — and what it does NOT do

### 3.1 What it does

* **Reads price evidence** (1m mirror → 15m/1h/4h frames, availability =
  completion time; incomplete higher-timeframe bars are dropped and
  recorded as rejected, never used).
* **Observations** are recorded with as-of keys (task-bar + boundary
  time on the sealed `SharedInformationAxis`) and source identifiers.
* **Structural facts** (derived, each with an operational definition and
  explicit dependencies): the movement direction relative to the last
  completed task-scale leg (F-K k-bar confirmation; "scale" is relative
  to the declared task, never a universal wave size), per-scale
  availability counts, and SP-05 cross-scale containment states (verified
  timestamps only).
* **Interpretations** are traceable: a primary movement interpretation
  (engineering-interpretation class) with its supporting and opposed
  evidence, plus a materially different alternative (research-hypothesis
  class).  Each names its falsifier reference and lists what would
  support/weaken it and the invalidating observations.
* **Conditional forecasts are recorded BEFORE their conditions** when the
  condition has not yet occurred (`observed_before_record = false`), with
  an executable operational condition (SP-03 close-based violation;
  equality is not a crossing) and a precise if-event → loses-support
  effect.  When a recorded condition is observed later, the forecast is
  revised by **appending a new immutable version** (`revises` link,
  revision reason on the analysis record); the prior version keeps its
  original wording and status.
* **Conditions that already occurred** before the record are marked
  `observed_before_record = true` and the lifecycle state
  `CONDITION_ALREADY_OBSERVED` — never presented as pre-event prediction.
* **Lifecycle states** produced: `INSUFFICIENT_CONTEXT`,
  `INTERPRETATIONS_FORMING`, `MONITORING`, `PENDING_CONDITION`,
  `CONDITION_ALREADY_OBSERVED`, `WEAKENED`, `CONTRADICTED`,
  `INVALIDATED`, `RECONSTRUCTED`.  (`SOURCE_DEFINED_CONFIRMATION_ONLY_IF_
  DEFINED` is defined but never produced here: no source-defined
  operational confirmation event applies to this path's claims —
  trade-through validation is S-class for ORDER-BLOCK candidates and out
  of scope.  **No `CONFIRMED` state is ever claimed.**)
* **Midstream start**: `--snapshot-in` loads a saved snapshot (records +
  forecast versions + active references) and revises with new causal
  evidence while recording the prior version and the revision reason; a
  fresh process's restored state contains nothing past the saved
  boundary (covered by test).  A first run over historical data is marked
  `reconstructed` and records its missing-history limits.
* **Multi-timeframe alignment** is by availability (completion) times;
  cross-scale facts meet on verified timestamps (SP-05); no cross-domain
  index arithmetic; every as-of/availability question goes through the
  sealed `SharedInformationAxis` (the only causal clock).
* **Unavailability is explicit**: missing / future / off-grid /
  unmappable / inconsistent evidence is recorded with a reason and never
  affects the analysis.  An off-grid as-of is INVALID INPUT (ValueError,
  fail closed).
* **The next awaited observation** is named precisely (e.g. "the next
  completed 4h bar's CLOSE relative to <reference>"), alongside the
  invalidating observations.
* **Position state** is supplied / absent / unknown; here always
  `absent` with the explicit note — never inferred from price structure.
* **History**: the engine records its task results in the EXISTING
  `InterpretationLedger` with COMPLETE recomputation payloads (no
  parallel selection engine, no disconnected parallel history);
  changed-evidence propagation recomputes real dependents (test proves
  the recomputation entry + provenance survival; a dependent that cannot
  recompute is marked stale and never counted as success).
* **Claim classification** (every source in the register):
  `directly-stated | paraphrase | engineering-interpretation |
  research-hypothesis | unsupported-or-unavailable`.
* **`selection_quality = NOT_ESTABLISHED`** in every record and
  manifest.  No probabilities (not calibrated on a versioned
  out-of-sample set); no forecast expiry (no approved policy defines
  one); no invented candle counts / percentages / ATR / confidences.

### 3.2 What it does NOT do

* NOT a rigid signal bot; NOT a universal recipe ("BOS+FVG+sweep=BUY"
  does not exist anywhere in this work).
* NOT a trade executor: no live exchange orders, no backtest-as-proof,
  no profitable-trading claim.
* NOT Michael Huddleston and NOT a replication of his private judgment.
  The methodological direction is his publicly documented work; only
  verified material is attributed (see §6).
* No local or external model runs at runtime; no human labeling required;
  no large undifferentiated candidate lists (references are exact or the
  unresolved reason is explicit).
* No "big wave" universal definition: every scale statement is relative
  to the declared task (4h task scale, k=5 research configuration).

## 4. Commands run and results

### 4.1 Single as-of analysis (real BTCUSDT data)

```
cd project/trading_project/docs/research/analysis_v1
PYTHONPATH=../../src python run_market_analysis_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --at "2025-08-14 00:00:00+00:00"
```

**Result**: success.  Machine-readable record in
`run_artifacts/analysis_single_v1.json` + concise explanation in
`analysis_single_explanation_v1.txt`.  Example output (abridged):

```
### AN-9f5d9cfb4329 v1 — as of 2025-08-14 00:00:00+00:00 (UTC) [reconstructed]
lifecycle: CONDITION_ALREADY_OBSERVED
fact: the most recent completed task-scale leg ... moved down
      (F-K k=5, scale relative to the declared task)
fact: 312 completed 1h bars and 32 completed 1h legs available ...
interpretation I-primary (invalidated): the origin-of-last-confirmed-leg
      = PTC:F-K(k=5)|high@2025-08-11T08:00:00 continues to define the
      boundary of that claim (research configuration)
    opposed: SP-03 close violation of PTC:... (2 event(s))
    alternative: the down leg is exhausted and a up structure develops
forecast FC-analysis-v1-0001 v1 [already_observed, observed_before_record=True]
    if: close-based violation of PTC:...|high@2025-08-11T08:00 (level 122335)
        on the up side   then: interpretation I-primary LOSES SUPPORT
next awaited observation: the next completed 4h leg's direction
position status: absent (no authoritative position feed was supplied;
      no position is inferred from price structure)
selection_quality = NOT_ESTABLISHED
```

Note the honesty markers: the single-shot run starts `reconstructed`;
the condition predated the record, so the forecast says
`observed_before_record=True` and the state is
`CONDITION_ALREADY_OBSERVED` — no pre-event prediction is claimed.

### 4.2 Chronological replay (real BTCUSDT data, 2025-08-01 → 2025-09-30)

```
cd project/trading_project/docs/research/analysis_v1
PYTHONPATH=../../src python run_market_analysis_v1.py \
  --mirror-dir /home/user/work/data/btc/mirror \
  --replay --from 2025-08-01 --to 2025-09-30
```

**Result**: success — 60 daily boundaries on the 4h completion grid,
with visible per-boundary progress.  Outputs in `run_artifacts/`:

| artifact | content |
|---|---|
| `analysis_results_v1.jsonl.gz` | 60 machine-readable analysis records (full schema) |
| `analysis_explanation_v1.md` | per-boundary explanations |
| `analysis_manifest_v1.json` | provenance manifest (below) |
| `analysis_snapshot_v1.json.gz` | end-of-run engine snapshot (resume input) |
| `analysis_single_v1.json` / `analysis_single_explanation_v1.txt` | the `--at` outputs |

Lifecycle distribution over the 60 boundaries:

| state | count |
|---|---|
| `PENDING_CONDITION` | 31 |
| `CONDITION_ALREADY_OBSERVED` | 16 |
| `INVALIDATED` (a recorded condition observed post-record → forecast revised, prior version preserved) | 9 |
| `INSUFFICIENT_CONTEXT` (no completed task-scale leg yet) | 4 |

Observation modes: `reconstructed` for the first boundary,
`live-observed` afterwards (the engine observed the evidence between its
own boundaries in sequence).

### 4.3 Replay provenance (recorded in `analysis_manifest_v1.json`)

| item | value |
|---|---|
| dataset commit | `27c9be705ac9280248672c895082c057b979ebff` (`parshant231234-eng/BTCUSDT-Historical-Data` mirror) |
| `BTCUSDT_1m_2025-08.csv` sha256 | `15d26d2374bce8804e25012ff76e5fad976633a2fde843ffb0f487e1c90a0cf4` — **matches expected** (`15d26d23…1c90a0cf4`) |
| `BTCUSDT_1m_2025-09.csv` sha256 | `e1d5c8f350d83df866ff36c3b4d74f7e5b383db07cde7bca0ee1f200d7a48979` — **matches expected** (`e1d5c8f3…0d7a48979`) |
| final source commit | `f1702e9ccbee630d0564ab21bf3421009d8f67ad` |
| sealed `information_time.py` sha256 | `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` |
| dependency versions | python 3.11.2, numpy 1.26.4, pandas 2.2.3, pytest 8.3.5, tzdata 2026.6 |
| config | instrument BTCUSDT, task scale 4h (k=5 research configuration), fine 1h, finest 15m, role `origin-of-last-confirmed-leg`, policy `P-ORIGIN-RESEARCH` (kind `research_configuration`, never owner-approved) |
| selection_quality | NOT_ESTABLISHED |

The manifest also states the claim boundaries: the engine is an
analytical lifecycle over existing approved components, is not Michael
Huddleston, and makes no accuracy claim.

## 5. Tests

Command (focused):

```
PYTHONPATH=src python -m pytest tests/test_contextual_analysis_lifecycle.py -q
# 12 passed
```

Command (full suite, pinned env python 3.11.2 / numpy 1.26.4 /
pandas 2.2.3 / pytest 8.3.5 / tzdata 2026.6):

```
PYTHONPATH=src python -m pytest tests/ -q
# exit 0 — all tests pass (pre-existing numpy/pandas warnings only)
```

The 12 lifecycle tests map to the required coverage:

| # | requirement | test |
|---|---|---|
| 1 | append-after-T invariance | `test_append_after_t_invariance` (byte-identical record at T after appending later evidence) |
| 2 | forecast recorded before its condition + later observation updates it without rewriting the prior record | `test_forecast_recorded_before_condition_then_immutable_revision` |
| 3 | condition already observed at startup is not a pre-event prediction | `test_condition_already_observed_at_startup_not_predicted` |
| 4 | snapshot resume without leaking data past the saved boundary | `test_snapshot_resume_no_leakage` |
| 5 | midstream start = reconstructed + missing-history limits | `test_midstream_reconstructed_records_limits` |
| 6 | position absent preserved | `test_position_absent_never_inferred` |
| 7 | competing interpretations distinct | `test_competing_interpretations_distinct` |
| 8 | unresolved reference with explicit reason | `test_unresolved_reference_has_specific_reason` |
| 9 | machine-detectable conditions have operational + source/policy definitions | `test_condition_definitions_operational_and_sourced` |
| 10 | provenance survives recomputation; stale recomputes never success | `test_provenance_survives_recomputation_and_stale_never_success` |
| 11 | off-grid as-of rejected (fail closed) | `test_offgrid_asof_rejected` |
| 12 | no probabilities / no signals / NOT_ESTABLISHED | `test_no_probabilities_no_expiry_no_signal` |

Existing suites (V1/V1.1/V1.2 coverage) remain green — the engine adds
no regression: `test_contextual_selection_expert_selection.py` 35,
`test_contextual_selection_csm.py` 12,
`test_contextual_selection_final_audit_patch.py` 14.

## 6. Claim sources and methodological boundary

The source register inside the engine classifies every source
(`SOURCE_REGISTER`, carried in every record):

| source | class | basis |
|---|---|---|
| pinned knowledge `jfjdjdieifne/test@6c8bf6fd` (12_SOURCE_INDEX / 15_CONTEXTUAL_SELECTION_METHOD / 16_SWING_WAVE_SELECTION) — F-K knowability, T-S5/SP-04 falsifier semantics, SP-03 close binding, SP-05 containment, taken-state = state-not-cause | `paraphrase` | verified against the pinned register |
| the final task specification (claim-class taxonomy; URL/title ≠ evidence) | `directly-stated` | directly stated in the task |
| ICT order-block video `PIYh0CxoY9c`, FVG video `FgacYSN9QEo` (pinned partial transcripts, opening lines only) | `unsupported-or-unavailable` | partial transcript only; exact operational definitions NOT available — nothing attributed |
| ICT 2022 mentorship Ep3 `nQfHZ2DEJ8c`, Ep12 `8GkQfdAXZP0`, 2024-09-16 FVG `HhgWGduYQZQ` | `unsupported-or-unavailable` | NOT verified (no transcript/passage; not in the pinned register) — nothing attributed |
| price/volume data, event timestamps, derived structural facts | `engineering-interpretation` (facts) | deterministic computation over verified inputs |
| the alternative interpretation | `research-hypothesis` | proposed, monitored, not asserted |

**Methodological direction**: Michael Huddleston's publicly documented
work (ICT).  The engine implements ONLY what the verified material
supports (pinned knowledge register + available transcripts).  It never
claims exact replication of his private judgment, is not affiliated with
him, and has no demonstrated accuracy.

**Data note (honesty)**: `dataset_v1/` (previous session) was built from
the same mirror commits and cited London/NY session times from an
unverifiable source — this engine does not use session-time claims; the
mirror identity is recorded above and nothing else is asserted about the
data's upstream provenance.

## 7. Reserved / not established

* `selection_quality = NOT_ESTABLISHED` — no independent quality target
  has been evaluated; no accuracy, expectancy, or profitability claim is
  made or implied.
* P-ORIGIN-RESEARCH is research configuration (k=5, 4h task scale, role
  semantics), never an owner-approved analytical policy.
* Historical replay demonstrates mechanics (lifecycle, forecasts,
  revisions), not market-truth or prediction skill.
* No `CONFIRMED` interpretation state is produced on this path (no
  source-defined operational confirmation event applies here).
