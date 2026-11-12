# ICT CAPABILITY AUDIT `V0` — what the engine can actually compute, on HEAD, by reading the code

**Type:** read-only audit, written **before** any data was loaded or any run was started.
**Commit audited:** `fd43dc29a9139aa088724b0e0f11b3d97cba431f` (HEAD at audit time).
**Scope:** only the code path the authorised run actually touches.
**No file outside this folder was created, edited or deleted for this audit.**

---

## 0. Constitution conflict recorded (required by the task block)

The owner authorisation for this run is a real-data run. The project constitution forbids that
until the phase opener is signed, and `OWNER_DECISION_D3.md` is a proposal, **not signed**.
The conflict, quoted:

> **`docs/handoff/AGENT_HANDOFF_DETAILED_2026-11-09.md`, §2.5 «المادة 5 — لا نتائج على بيانات حقيقية (ولهذا سببان)»**
>
> > 1. **أخلاقي/علمي:** لا نُعلن شيئًا عن جدوى مفهوم قبل أن يكون تعريفه مكتملًا ومدققًا.
> > 2. **منهجي:** نتيجة على بيانات حقيقية قبل تجميد التعريف = `look-ahead` وتلويث الاختيار.
> >
> > لذلك: خطوات `B` و`C` تُختبر على شموع يدوية (`FIXTURE`) فقط، ولا تُقرأ بيانات سوق، ولا يُنتج
> > أداء.

> **`AI_COLLABORATION_CONSTITUTION_CURRENT.md` §21 / handoff §2.20:**
> «إذا كانت الوحدة CLOSED، لا نعدلها دون versioned authorization.»

**How the conflict is handled:** the run is executed because the owner is the closure
authority and has given an explicit, written, single-run authorisation for the **development**
window only. `D3` remains unsigned throughout; nothing in this folder treats the run as a
result about edge, and no CLOSED module is modified. The conflict is recorded here rather than
resolved by assumption. **`selection_quality` stays `NOT_ESTABLISHED`.**

---

## 1. Tooling decision and exact command line

### 1.1 Candidates examined

| candidate | can it produce March-2021 decisions from Jan-2021 history? | verdict |
|---|---|---|
| `docs/research/huddleston_study/run_forex_intraday_v1.py` (`--phase dev`) | **No.** `run_phase()` decides at **every** task boundary inside `--from .. --to`. There is no flag separating a history window from a decision window. Pointing `--from` at 2021-03-01 gives no warm-up; pointing it at 2021-01-01 emits decisions and plans for January and February, which the authorisation forbids. | used **as a library**, not as the entry point |
| `docs/research/monitor_v1/run_step_replay_v1.py` | No. It is a BTC-shaped 1m step replay with its own state file and no dev/eval/plan layer. | rejected |
| `MonitoringLoop` / `decision_layer.decide` / `trade_plan` directly | Yes, and these are exactly what the runner drives. | driven by the wrapper |
| `ict_engine` | No. `src/trading_system/ict_engine/data.py:20` `ALLOWED_YEARS = frozenset({2022, 2023})` and `:21 DATA_CUTOFF = datetime(2025, 5, 1, tzinfo=timezone.utc)`. 2021 is refused at `:202` and `:268`. | **not in the path** (imported by nothing in this run) |

**Verified not in the path:** `src/trading_system/ict_engine/data.py` is imported by
`ict_engine/__init__.py`, `timestamp_evidence.py`, and its own tests. The runner imports
`trading_system.research.contextual_selection.*` only, and defines its **own**
`load_bidask()` at `run_forex_intraday_v1.py:90`, which has **no year allow-list** and no
cutoff. Therefore `ALLOWED_YEARS` / `DATA_CUTOFF` cannot block 2021 in this run, and neither
file was modified.

### 1.2 The wrapper (Phase 3e)

`dev_month_v0/run_dev_month_v0.py` — **new file**, drives the same loop with the same objects,
imports the runner as a module and reuses `load_bidask`, `mid_rows`, `frames_builder`,
`engine_factory`, `outcome_for`, `model_state`, and the two gate functions copied verbatim
(`gate_v1`, `gate_b0`). It adds exactly one thing: a decision window. Nothing is re-tuned; no
constant is redefined; the copy is declared in the file header so a later reader can diff it.

Warm-up semantics: episodes are extracted and the model is fitted from the first boundary
(causal — only episodes whose label window closed strictly before `t`), and `decide()` /
`create_plan()` are called **only** inside the decision window.

### 1.3 Exact command (the one run)

```bash
PYTHONPATH=/home/user/TRADING-BOT/project/trading_project/src \
/tmp/devenv/bin/python run_dev_month_v0.py \
  --bidask-dir /tmp/hud_data \
  --history-from 2021-01-01 --decide-from 2021-03-01 --decide-to 2021-04-01 \
  --to 2021-04-01 \
  --out-dir /tmp/dev_month_v0/raw \
  --gate v1 --fill-mode next_open
```

Defaults inherited, unchanged: `--gate v1` (default) and `--fill-mode next_open` (default).
Raw outputs are written **outside the repository**, under `/tmp/dev_month_v0/raw/`.

---

## 2. What a single decision already carries (no new code needed)

| what the task asks for | field that already carries it | file:line |
|---|---|---|
| reason for | `ContextualDecision.explanation["why"]` | `decision_layer.py:512` (field), built in `decide()` |
| reason against | `ContextualDecision.explanation["opposed"]` | same |
| what would change it | `ContextualDecision.explanation["would_change"]` + `next_discriminating_observation` | `decision_layer.py:511-512` |
| competing hypotheses | `alternative_interpretation_ids` + `model_ranking` + `model_support` | `decision_layer.py:508,513,514` |
| invalidation | `TradePlan.current.levels["reference"]["level"]` (frozen at plan creation) + `components["invalidation"]` | `trade_plan.py:396,395` |
| story memory | `InterpretationLedger` versions, `WorkingInterpretation.versions`, `RevisionLog` through `AnalysisEngine` | `analysis_lifecycle.py` (`AnalysisRecord.interps`) |
| context at t | `ContextualDecision.context` (dict of as-of facts, e.g. direction) | `decision_layer.py:518` |
| missing evidence | `PlanVersion.missing_evidence`, `TradePlan.no_plan_reasons` | `trade_plan.py:404,423` |

So the per-decision narrative required by Phase 5 exists in the record **before** any wrapper
work; the wrapper only had to stop the loop from deciding outside March.

---

## 3. Concept inventory — grepped on HEAD, not taken from coverage tables

Status vocabulary: **AVAILABLE** = a function computes it and the run reaches it;
**PARTIAL** = a data type / bookkeeping exists but no detector computes the concept;
**MISSING** = nothing in the executed path.

| # | concept | status | file :: function (line) | what it returns | causal? | module state |
|---|---|---|---|---|---|---|
| 1 | swing | **AVAILABLE** | `csm.py :: fk_turning_points` (887) | F-K turning points, `k=5`, with `knowable_bar`/`knowable_time`, on the task scale | yes — reads `bars[:t+1]`, stamps knowability | `contextual_selection` (IMPLEMENTED, pending audit) |
| 1b | swing (alternate, **not in path**) | exists, unused | `engine_v1/b1_candles/swing.py :: swing_at` (52) | `V-A-00` three-candle swing | yes | CLOSED (handoff §7: «مغلقة») |
| 2 | dealing range | **MISSING** | — (grep: no `dealing_range`, no `dealing range` in the package) | — | — | — |
| 3 | equilibrium / premium / discount | **MISSING** | — (grep: nothing) | — | — | — |
| 4 | buy-side / sell-side liquidity, equal highs/lows | **MISSING** in path | — (grep: nothing); `engine_v1` has the id only: `c1_catalog/liquidity_sweep.py :: _evaluate` returns `UNDEFINED` for `V-E-EQH` by owner decision | `UNDEFINED` always (engine_v1) | n/a | C1/C1b complete (engine_v1), not called here |
| 5 | sweep | **MISSING** in path | `engine_v1/c1_catalog/liquidity_sweep.py :: sweep_at` (279) exists but is not imported by this run | sweep record vs a swing level or a caller level | yes (`candles[:t+1]`, prints `last_read`) | C1 complete; **not in path** |
| 6 | displacement | **MISSING** in path | `engine_v1/c1_catalog/displacement.py :: displacement_at` (176) exists, not imported; `study_links.py` mentions "displacement" only as narrative text (line 696, 709) | variants; `reference_variant = NONE_PER_OWNER_D2` | yes | C1 complete; **not in path** |
| 7 | FVG | **AVAILABLE** | `connected_readings.py :: ConnectedReadings.scan_fvgs` (399) | `FVGRegion(lower_bound, upper_bound, bar1..bar3, observability_time, ce_midpoint)` per timeframe, only after `b3` closes | yes — region becomes observable at `b3` completion label | IMPLEMENTED |
| 8 | order block | **PARTIAL** | `study_links.py :: OBLikeCandidate` (292) + `assign_role` (449) | a *record type* with `state`/`role`/`events`; **no detector builds it from bars** | record is causal by construction; no computation exists | IMPLEMENTED (type only) |
| 9 | structure shift / break | **PARTIAL** | `csm.py` `STATUS_BROKEN = "broken"` (82); `study_links.py :: ShiftWatch` (649); `AnalysisEngine` interpretation states (`WEAKENED/CONTRADICTED/INVALIDATED`) | crossing records and interpretation state changes; **no BOS/CHoCH detector** | yes (state transitions are time-stamped) | IMPLEMENTED (bookkeeping) |
| 10 | higher-timeframe bias | **AVAILABLE** | `study_links.py :: StudyReasoningLayer.hf_context` (714ff) via `HigherFrameHypothesis` (373) | `{trend, established_at}` plus alternatives | yes — established only from completed HTF bars | IMPLEMENTED |
| 11 | draw on liquidity | **MISSING** | — (grep: nothing) | — | — | — |
| 12 | stop placement | **AVAILABLE** as a plan component | `trade_plan.py :: build_components` (296) + `create_plan` (474) | invalidation component bound to a frozen reference level | yes — level frozen at plan creation, not revised by later price | IMPLEMENTED |
| 13 | target selection | **AVAILABLE** as a plan component | `trade_plan.py :: _objective_exists` (626) + plan objective component | objective = leg-end level; existence checked causally | yes | IMPLEMENTED |
| 14 | session windows | **PARTIAL / DISABLED by default** | `study_links.py :: SessionClockConvention` (247), `US_INDEX_FIRST_GAP_SESSION_CLOCK` (264) | a session clock convention; `StudyReasoningLayer.__init__` takes `session_clock: Optional[...] = None` (725) and the runner passes nothing | convention is fixed to a US-index first-gap 9:30/9:31 rule, explicitly session-scoped | IMPLEMENTED, **off in this run** |
| 15 | selection among several candidate zones | **PARTIAL** | `expert_selection.py :: expert_structural_reference_selection` (1006) + `apply_expert_preferences` (~1219); task conclusions `EVIDENCE_PREFERRED` / `UNRESOLVED_NO_EDGE` | one selected reference among candidates, or an explicit unresolved state with exclusion reasons | yes | IMPLEMENTED (points/legs only; **zones are not selectable**) |

**Summary:** of the 15 concepts, 4 are usable as computed facts (swing, FVG, HTF bias,
stop/target as plan components), 4 are partial bookkeeping (OB, structure shift, session
clock, selection), and 6 are absent from the executed path (dealing range, equilibrium,
liquidity pools, sweep, displacement, draw on liquidity). Note the split: **sweep and
displacement are coded and closed in `engine_v1/c1_catalog`, but this runner does not import
them.** The run therefore does *not* see sweep or displacement, even though the repository
contains them.

---

## 4. Hard-coded numbers in the default configuration (inherited, not changed)

| # | number | file:line | meaning |
|---|---|---|---|
| 1 | `TASK_SCALE = "1h"` | `run_forex_intraday_v1.py:81` | decision/plan bar |
| 2 | `READINGS_SCALE = "15m"` | `:82` | connected-readings bar |
| 3 | `K = 5` | `:83` | F-K fractal half-width |
| 4 | `HORIZON_BARS = 12` | `:85` | episode label horizon, task bars |
| 5 | `EPISODE_HORIZON_BARS = 24` | `decision_layer.py:179` | module default (overridden to 12 by the runner) |
| 6 | `task_scale="4h"` default | `monitoring.py:578`, `monitoring.py:773` | module default (overridden to `1h`) |
| 7 | pip factor `1e4` | `run_forex_intraday_v1.py:318` | pip conversion |
| 8 | `round(pips, 2)` | `:320` | output rounding |
| 9 | first-gap clock 9:30/9:31 | `study_links.py:264-265` | session convention (**disabled**, §3 row 14) |
| 10 | `k >= 1`, `tau > 0` policy slots | `csm.py:910`, `csm.py:1014` | no default; must be supplied |

**No minimum reward:risk gate, no rank cutoff, no cost-in-R constant and no warm-up bar count
was found in this path** (grep over `trade_plan.py` for `reward|risk_reward|min_rr|ratio` finds
no threshold; `run_forex_intraday_v1.py` has no warm-up constant — warm-up is whatever history
is loaded). The default run inherits all of the above **unchanged**.

---

## 5. What the run will and will not emit

- **Will emit:** one `cases_*.jsonl` record per March decision (`plan-opened`, `plan`,
  `no-plan`), each with the decision record (why / opposed / would_change / alternatives /
  model ranking / context), and for each closed plan an `outcome` with next-open bid/ask fills,
  pips, `AMBIGUOUS_CENSORED` flag, and the plan's frozen levels.
- **Will not emit:** any selection among candidates *of zones* (not implemented), any sweep or
  displacement fact (not imported), any dealing-range or premium/discount number (not
  implemented), any session window (disabled), any commission (not in the dataset).

---

## 6. What this does NOT establish

- It does not establish that the concepts marked AVAILABLE are implemented *correctly*; it
  establishes only that a function exists on HEAD and is reachable from this run.
- It does not establish that the missing concepts are missing from the repository — sweep and
  displacement exist in `engine_v1/c1_catalog` and are simply not imported here.
- It does not validate the hard-coded numbers against any source; it lists them so that the
  reader knows what the default run inherits.
- It does not establish that the model layer is meaningful: the model is fitted on episodes
  from a three-month warm-up and is labelled `provisional-unvalidated` by its own module.
- It does not resolve the Article 5 conflict in §0; it records it, and the owner remains the
  only authority who can grant the exception.
- It establishes nothing about edge, profitability or selection quality; one dev month, one
  run.
