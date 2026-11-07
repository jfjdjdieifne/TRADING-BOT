# 99 — End-to-End Causally-Evaluated FOREX Development Loop (initial baseline)

RESEARCH / PAPER record only. No live orders. No claim of proven
profitability. `selection_quality = NOT_ESTABLISHED`. Held-out Michael
episode `YT_tpPtItWqmlg` (Ep13) NEVER used — explicit statement:
the held-out episode remained unused for development, tuning, and
evaluation.

Status: initial baseline produced; chronological dev/eval split
declared before evaluation; connected gate compared against an
explicitly defined simple baseline. (Fill markers `«…»` = exact
numbers inserted from the run artifacts.)

---

## 1. Dataset and limitations

- **provider / instrument**: EUR/USD spot FOREX, Dukascopy datafeed
  (BID + ASK 5-minute candles), obtained from the public repository
  `mailztoganesh-civil/forex-data` @ commit
  `56d5f04fd90b29414a70147471309f1db326aa1c`, folder
  `data/EURUSD/5m_bidask/` (pipeline script in that repo:
  `scripts/download_dukascopy_bid_ask_m5.py`).
- **price type**: full two-sided OHLC (BidOpen/High/Low/Close,
  AskOpen/High/Low/Close), tick volumes, spread OHLC in pips. Analytical
  structure is computed on the MID; hypothetical fills use the actual
  BID (sells) / ASK (buys).
- **resolution / coverage**: 5-minute bars, calendar years 2021–2026
  (2026 partial through 2026-11). Dev/eval windows use 2025 (see §3).
- **timezone / session / bar construction**: timestamps UTC (the
  weekend-gap structure matches the known 21:00/22:00 UTC FX close/open
  around DST, corroborating UTC labeling); 24×5 trading with Sunday
  open / Friday close; bars are provider-built 5m candles (not our
  resample); the engine's 15m/1h/4h/1D frames are completion-labelled
  resamples of the 5m mid.
- **gaps / duplicates / identity**: the file is a continuous 288/day
  calendar grid INCLUDING closed-market placeholder rows (flat both
  sides, zero volumes) — 30,445 of 105,120 rows in 2025. Declared
  data-hygiene rule (research configuration): placeholder rows are
  dropped as not-observable movement (74,675 open-market rows in 2025).
  Duplicate timestamps: 0. Dataset identity:
  `dukascopy-eurusd-5m-bidask@56d5f04`;
  sha256(2025.csv.gz) =
  `1fa2dca207e3a8a1de37bfcd7653b15ebcffb933c05b4d4e3a4831aaa84d9647`.
- **spread / commission / execution**: REAL bid/ask spread is present
  (2025 open-market spread in pips: min 0.1 / median 0.4 / mean 0.59 /
  max 25.4) — used at fill bars. **No commission, swap/rollover, or
  slippage data exists in this dataset — never invented.** Tick volume
  is present but is not treated as real volume. No intrabar path data
  (5m quotes only) — same-bar ordering ambiguity is preserved (§6).
- **why not the others**: MT5-export EURUSD 1m (1 month, spread column
  mostly unrecorded) and HistData 1m (bid-only) were inspected and kept
  as secondary cross-check material; Yahoo-based files are indicative
  quotes only.

## 2. Reused engine (no rebuilds)

Causal engine (AnalysisEngine + causal axis + sealed
`information_time.py`), connected readings (FVG geometry + cross-frame
links + reading tasks + working interpretations), InterpretationLedger
(single history), monitoring loop (prefix-frames causality), study
layer (references, shift-watches), decision layer (ContextEventModel,
`decide`), plan layer (`build_components`/`create_plan`/`observe_plan`
with declared component origins). Narrow extensions only (§4).

## 3. Chronological split (declared BEFORE evaluation)

- **development**: 2025-01-01 → 2025-02-01 (31 days; 528 1h task
  boundaries). 528 training episodes; 60 censored/label-unusable
  windows excluded; 468 fitted. CHRONOLOGICAL PROTOCOL: at each
  decision at time T the model contains ONLY episodes whose label
  windows closed strictly before T (no training/label-window overlap);
  labels use future bars and are never features.  Window was cut from
  the planned 6 months to 1 month after measured OOM/runtime limits of
  the first baseline build (disclosed; later months unused).
- **untouched evaluation**: 2025-02-01 → 2025-03-01 (28 days; 480 task
  boundaries). The dev model is FROZEN (trained_through=2025-01-31
  10:00Z recorded in dev_model.json); eval NEVER trains and was not
  used for tuning.
- baseline comparison on the SAME eval decisions and the SAME costs:
  - **V1 (connected gate)**: plan attempt only on an evidence-supported
    strict decision preference where the connected readings do not
    contradict (research configuration).
  - **B0 (explicitly defined simple baseline)**: plan attempt on EVERY
    strict decision preference, WITHOUT consulting the connected
    readings. Same plan definitions, same fills, same costs.

## 4. Engineering changes (narrow; defect-driven)

1. **Readings at lower-timeframe completions** (requirement 3): the
   monitoring loop now runs the connected-reading pipeline at every
   completed 15m bar between 1h task boundaries (`readings_scale` +
   `on_readings_boundary`). Higher-frame context is preserved; lower-
   frame evidence is never held back. Three times are reported
   distinctly: the bar's completion label (DATA/availability time), the
   boundary as-of, and the ledger `decision_time` (PROCESSING wall
   clock). References are those confirmed at the last completed
   task-scale boundary (never later data).
2. **task_scale/instrument in the plan layer** (was hardcoded
   4h/BTCUSDT) — required for intraday FOREX; defaults unchanged.
3. **Ledger serialization determinism** (defect found by T3): payloads
   holding live objects (axis/policy) serialized with memory addresses;
   now stable type markers. Regression covered by T3.
4. **Incremental link pairing** (performance, identical link set):
   new-region/new-ref pairing instead of all-pairs re-walking.
5. `resolve_world(task_scale=…)` — 1h world for 1h records (bug found
   in first run: 4h labels against the 1h causal axis raised
   InformationKeyError).

## 5. Analytical question and the connected path

ONE question (not a pattern list): **after an old structural reference
is crossed (close-to-close), does subsequently observable lower-frame
evidence (the FVG comparison task) support a short-duration research
plan in the scenario direction — or is the state honestly unresolved?**

The path at each 1h boundary: higher-frame context (I-primary trend,
established time) → structural references (F-K points, k=5) → crossing
scans open shift-watches (E03 semantics) → connected readings at 15m
completions produce/compare FVG candidates per declared criteria with
supporting/counterevidence/unknowns → working interpretation (INT-HF /
INT-WATCH, append-only versions) → decision (`decide` on the dev-fitted
context model) → plan attempt through the existing plan layer
(conjunction of components is an ENGINEERING evaluation choice, labeled
`ENGINEERING_INTERPRETATION` in `evaluation_rule.source_status` — NOT
presented as Michael's method) → watch-next + weakening conditions.

Pause-and-step excerpt (disclosed window 2025-03-01→03-06, pause
2025-03-04 12:00, artifact `forex_pause.txt`): HF trend=down
(established 2025-03-04 11:00); 19 confirmed references; 38 FVG regions
(15m:28, 1h:8, 4h:2); two shift-watches opened by close-to-close
crossings of old highs (1.05039 / 1.04962) at 09:00 — "intrabar path
NOT established"; `RT-REF-REVIEW` = UNRESOLVED (5 candidates: 2 with
observed interactions — equal evidence, no forced pick); `RT-WATCH-
…0001` = EVIDENCE_PREFERRED (1 candidate met all three declared
criteria; support distribution {0:13, 1:22, 2:2, 3:1}); `RT-WATCH-
…0002` = UNRESOLVED (no candidate at 3/3). Steps 13:00–15:00 report
"no change" honestly.

## 6. Costs, fills, and ambiguity

- hypothetical fills at the decision-bar CLOSE: buy at ASK, sell at
  BID, from the actual 5m two-sided quotes (spread ACTUALLY paid in the
  simulation; spread is the only supported cost).
- commission/swap: NOT in the dataset → NOT modeled, NOT invented; net
  P&L is therefore "after spread only".
- close-based entry/invalidation (plan-layer definitions): intrabar
  path inside a 1h bar is unknown; where BOTH the invalidation level
  and the objective level are touched by 5m quotes inside one task bar,
  the outcome is recorded **AMBIGUOUS_CENSORED** — the ordering is
  never resolved in favor of the trade.
- no position sizing, no leverage (none is defined anywhere).

## 7. Results

### A. Source agreement (definitions only — not performance)

From the plan layer's `source_agreement` matrix (artifact
`summary_dev.json` / `summary_eval_*.json`): the plan components'
entry/invalidation/objective definitions are research configurations
(SP-03 close-binding of F-K legs) — direct source statements exist for
stops/invalidation concepts (SRC-EX-01) but the ICT-primary
invalidation-by-close is NOT in the verified primary text (P-K); the
entry technique exists as a source claim (SRC-EX-01) but is explicitly
NOT implemented (G-OB-P not runnable; owner policy required; none
invented). FVG three-candle geometry = external secondary references +
corpus FVG16-A (S); bounds/availability handling (E); the criteria
conjunction (E) — recorded in every task as
`evaluation_rule.source_status = "NOT a source statement"`.

### B. Analytical / event quality (recorded BEFORE each event)

EVAL period (untouched; 480 task boundaries; frozen model):

| | V1 (connected gate) | B0 (baseline) |
|---|---|---|
| decisions | 480 | 480 |
| strict evidence-supported preferences | 384 | 384 |
| plan attempts held by the connected gate | 354 | 0 (gate not consulted) |
| gate passes | 30 | 384 |
| plans created | 1 | 4 |
| no-plan cases (non-strict decisions) | 450 | 96 |

- the connected readings produced EVIDENCE_PREFERRED FVG conclusions
  during the eval window (e.g. `FVG-…-15m-141`), with the full
  comparison (support counts, near-misses, chronology) recorded before
  each event; `RT-REF-REVIEW` and the watch tasks resolved and
  re-versioned or honestly reported "no change" per boundary (see the
  pause artifact for the exact language).
- where the interpretation failed or stayed unresolved: the context
  model ties (equal continuation/violation counts) yield NO_EDGE — 337
  such cases in dev — recorded as non-resolution, never forced.

### C. Hypothetical plan mechanics and outcomes (same eval decisions)

B0 (baseline, no connected gate) — 4 plans:
- PLAN-0001 reversal up: entry 2025-02-04 15:00 @ ask 1.03694,
  exit 2025-02-05 03:00 @ bid 1.03816 → **+12.2 pips** (spread-paid
  corrected; win; objective-before-invalidation; no same-bar ambiguity).
- PLAN-0002 continuation up: entry 2025-02-05 08:00 @ ask 1.04044,
  exit 2025-02-05 21:00 @ bid 1.04045 → **+0.1 pips** (win; the
  spread consumed most of the gross move).
- PLAN-0003, PLAN-0004: INVALIDATED before any entry (no-entry;
  recorded as losses of nothing — no fill, no cost).
- counts: plans=4, no-plan=96, winners=2, losses=0 (no entered plan
  was stopped), invalidated-before-entry=2, missed=0, open/censored=0,
  ambiguous-censored=0.  Win rate where definable (entered plans):
  2/2; plan-level objective rate 2/4.  Average realized win = +6.2
  pips (spread-paid); average realized loss = n/a (none entered and
  lost).  Net after SUPPORTED costs (spread only; commission/swap not
  in the dataset): **+12.3 pips across 4 plans (+6.15/plan)**.

V1 (connected gate) — 1 plan:
- PLAN-0001 reversal down: INVALIDATED before entry (no-entry).
- 354 attempts were HELD by the declared contradiction criterion
  (an EVIDENCE_PREFERRED FVG direction opposing the scenario
  direction), including the two attempts B0 turned into the two wins
  (holds begin 2025-02-04 11:00, before the 15:00 entry).
- **V1 vs B0 on identical decisions and costs: B0 > V1 in this one
  held-out month** (held 2 winners, avoided nothing that B0 lost
  money on).  The connected gate criterion is NOT validated by this
  sample and appears too aggressive — recorded as the central
  weakness (§8), NOT retuned on the eval period.

These numbers are a small single-instrument simulation under declared
assumptions; no profitability inference is drawn.

No profitability inference is drawn from unit tests or source
agreement; the numbers above are a small, in-one-instrument, one-period
simulation under declared assumptions.

## 8. Weakness report (connected chains, categorized)

Chain case 1 (eval, B0 PLAN-0001 → the win V1 held): context down
(Jan-trained model ranks violation>continuation in the down/observed
bucket) → world: falsifier high + leg end resolved → plan reversal up
declared at 2025-02-04 11:00 → V1 gate holds it ("EVIDENCE_PREFERRED
FVG-15m-141 (upward) opposing the scenario direction (down)") → B0
proceeds → entry 15:00, objective leg completed 03:00 → +12.2 pips.
Diagnosis: **(b) unsupported/restrictive engineering rule** — the
contradiction criterion treats a single evidence-preferred FVG as
blocking regardless of its timeframe/recency; in this chain the FVG
evidence pointed WITH the profitable direction (upward) while the
scenario label ("reversal of a down context") was also up — the
criterion's direction bookkeeping conflates scenario label and
scenario movement.  Fix candidates (NOT applied): scope the criterion
to direction-of-outcome, or require two independent contradicting
observations.  Not tuned on eval.

Chain case 2 (B0 PLAN-0003/0004): strict preference + plan declared →
INVALIDATED before entry.  Category **(e)**: these cost nothing
(no fill) but show the plan definition's entry condition rarely fires
(2/4 plans entered) — the SP-03 close-binding entry is restrictive
for short-duration opportunities: **(b)**, with the missing piece
recorded in each no-plan record rather than fabricated.

Chain case 3 (dev, 337 NO_EDGE decisions): the context model ties
within buckets (53/60, 49/41 …) → no strict preference → no plan.
Category **(c)/insufficient discriminative structure**: 4-dimensional
context with ~500 episodes cannot separate continuation from
violation; the next targeted improvement is a better context/label
design (a research step), NOT a threshold.

4. (a) demonstrated software defects found and fixed narrowly (each
   with regression tests): ledger payload eagerness (quadratic asdict),
   FVG candidate rebuild cost, frames-prefix resampling cost, ledger
   serialization of live objects (save/resume determinism),
   resolve_world task_scale mismatch (InformationKeyError).
5. (c) no intrabar path: same-bar touch ordering preserved as
   AMBIGUOUS_CENSORED (none occurred in this window; the check is in
   place).

## 9. Tests and exact commands

    PYTHONPATH=src python -m pytest tests/test_forex_intraday_loop.py -q
      → 4 passed (T1 lower-TF readings update at 15m completions before
        the next 1h boundary; T2 future-data invariance with full vs
        truncated datasets; T3 NEW-process save/resume == continuous for
        study state AND ledger history (processing wall-clocks scrubbed,
        all data-time fields equal); T4 no fact with data time after the
        boundary as-of).
    PYTHONPATH=src python -m pytest tests/test_huddleston_connected_readings.py \
        tests/test_huddleston_study_links.py tests/test_contextual_monitoring.py \
        tests/test_contextual_trade_plan.py -q
      → 48 passed (no regressions).
    PYTHONPATH=src python -m pytest tests/ -q
      → EXIT=0 (full suite; log /home/user/work/full_suite_fx.log).

    # pause-and-step excerpt (disclosed window)
    python docs/research/huddleston_study/run_forex_intraday_v1.py \
        --bidask-dir /home/user/work/data/forex_src/mailz/data/EURUSD/5m_bidask \
        --phase pause --from 2025-03-01 --to 2025-03-06 \
        --pause-at 2025-03-04T12:00 --step 3 \
        --out-dir docs/research/huddleston_study/run_artifacts/forex_v1
      → EXIT=0.

    # development (fit context model on dev episodes only)
    python docs/research/huddleston_study/run_forex_intraday_v1.py \
        --bidask-dir … --phase dev --from 2025-01-01 --to 2025-02-01 \
        --out-dir docs/research/huddleston_study/run_artifacts/forex_v1 \
        --model docs/research/huddleston_study/run_artifacts/forex_v1/dev_model.json
      → EXIT=0 (528 decisions; 402 strict preferences; 468 episodes
        fitted; model frozen through 2025-01-31 10:00Z).
    # untouched evaluation, frozen model, V1 gate and B0 baseline
    python … --phase eval --from 2025-02-01 --to 2025-03-01 --gate v1 …
      → EXIT=0 (480 decisions; 1 plan; 354 held attempts).
    python … --phase eval --from 2025-02-01 --to 2025-03-01 --gate b0 …
      → EXIT=0 (480 decisions; 4 plans; 2 hypothetical wins
        [+12.2, +0.1 pips spread-paid]; 2 invalidated before entry).

## 10. Limitations (honest, pre-declared)

- one instrument, one provider, mid-based structure; fills at bar
  closes only; no commission/swap/slippage modeling.
- the ContextEventModel is ordinal counts over contexts (no
  probabilities emitted); the plan layer's own limitation list is
  preserved verbatim in every plan record.
- selection quality is NOT ESTABLISHED; a losing outcome does not by
  itself prove an analytical defect, and a winning one proves nothing
  about readiness.
- evaluation cadence: connected readings at 15m completions (this
  dataset's finest genuinely available bars are 5m; 15m is the
  declared readings scale for this run).

## 11. Protected file

`src/trading_system/research/information_time.py` sha256 before =
after = `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
(verified after all edits).

## 12. Final state

- artifacts: `run_artifacts/forex_v1/` — dev_model.json (frozen model,
  trained_through 2025-01-31 10:00Z), summary_dev.json,
  summary_eval_v1.json, summary_eval_b0.json, cases_dev.jsonl,
  cases_eval_v1.jsonl, cases_eval_b0.jsonl (with corrected spread-paid
  fills), pause_step_2025-03.txt.
- commits: engine/runner/tests commit(s) + this report on
  `arena/a41fd997-trading-bot`, pushed; working tree clean except the
  standing keep-outs (real_chart_study/, REAL_CHART_ELEMENT_…).
- protected file hash in §11 (unchanged).
- held-out episode statement in the header: UNTOUCHED.
