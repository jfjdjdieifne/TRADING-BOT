# Monitor V1 — Concepts, Relationships, and Limits

Machine-readable registers live in
`src/trading_system/research/contextual_selection/monitoring.py`
(`DATA_CAPABILITIES`, `CONCEPT_REGISTER`, `LIVE_FEED_STATUS`).  This
document records the relationships, the source passages actually
verified, and the honesty boundaries.  `selection_quality =
NOT_ESTABLISHED`.

## 1. What the available data is (actual input schema)

Input: verified mirror CSVs of
`parshant231234-eng/BTCUSDT-Historical-Data@27c9be70` (1-minute rows;
`timestamp` = epoch ms bucket start; `datetime_utc` column).

| column | status | note |
|---|---|---|
| open/high/low/close | **direct observation** | OHLC aggregates; intra-bar path NOT observable |
| volume, quote_volume | reported aggregate | no direction/participant inference |
| trade_count, taker_buy_volume, taker_buy_quote_volume | reported aggregate | trade_count is a COUNT; individual trades are NOT in the data |
| individual trades | **unavailable** | tick paths not reconstructible |
| order book | **unavailable** | resting orders, size, participant identity/intent CANNOT be established |
| open position | **absent** | only an authoritative position source can supply one |

A prior high/low is at most a **source-supported reference for potential
liquidity** (knowledge `04_LIQUIDITY`); OHLC alone proves nothing about
resting orders.  A price crossing is an **observable binding event** —
never automatically a "successful liquidity sweep", "rejection",
"reversal", or "entry".

## 2. Concept register (implemented concepts only)

See `CONCEPT_REGISTER` (7 entries) for required inputs, availability
time, operational observable event, interpretation, source, limitations,
alternatives, and revision dependencies for: completed-bar observation;
F-K swing/leg; falsifier reference; SP-03 close-based binding;
SP-05 cross-scale containment; potential-liquidity reference;
research-only hypothetical plan.  **Not implemented** (not claimed):
order-block zone machinery (G-OB-P is recorded NOT RUNNABLE in the
pinned foundation — P-N/P-W unset), FVG zones, sweeps/rejections,
market-maker models, any ICT concept beyond the bounded slice.

## 3. Relationships (not a list of patterns)

* **reference -> timeframe/task**: the falsifier reference is selected
  for the declared task role (`origin-of-last-confirmed-leg`) on the 4h
  task scale (k=5 research configuration); fine scales (1h/15m) carry
  their own FK worlds per `SharedInformationAxis`; cross-scale relations
  are only SP-05 containment over **verified** timestamps.
* **event -> reference**: plan/forecast events are SP-03 close bindings
  of a FROZEN reference level (plan records carry the exact level and
  point id); a binding is only meaningful AFTER the referenced point
  exists (scan starts at the point's occurrence bar + 1).
* **observable sequence**: bar order is observable; **intra-bar order is
  NOT** — `intrabar_path_metrics` returns
  `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)` (high vs low unknowable),
  the S1 stream keeps same-batch chronology UNPROVEN, and the monitoring
  journal marks same-bar multi-evidence as `sequence unresolved`.
* **LTF evidence vs HTF context**: incomplete HTF bars are never used
  (only completed bars are completed; availability = completion time).
* **interpretation -> facts**: every record lists `dependencies`
  (evidence ids); revisions append versions in the existing
  `InterpretationLedger` (`revision_of`); SP-20 propagation recomputes
  actual dependents (test T12).
* **unknowable-from-OHLC**: intra-bar traversal; whether a level was
  "swept" vs merely crossed; resting-order state; participant intent.

## 4. Source passages actually verified

Pinned knowledge `jfjdjdieifne/test@6c8bf6fd10e9581322849485d175e825cea5a27f`
(checked out at the pinned commit; the repository's default branch has
moved and is NOT used).  Claim classes: directly-stated / paraphrase /
engineering-interpretation / research-hypothesis / unsupported-or-
unavailable.

| id | source URL | passage time | what is stated | class |
|---|---|---|---|---|
| SRC-EX-01-OB-ENTRY-STOP | https://www.youtube.com/watch?v=PIYh0CxoY9c (ICT, Month 04 – Orderblocks, Dec-2016 content) | **not available** (P1 partial transcript, no timestamps; auto-caption artifacts; opening section only) | OB definition ("the lowest candle or price bar with a down close that has the most range between open to close and is near a support level"); validation (trade-through of the high); entry ("when price trades higher away from the bullish order block and then returns to the bullish order block candle or price bar high"); stop ("the low of the bullish order block is the location of a relatively safe stop loss placement") — quoted in `05_FVG_ORDER_BLOCKS_ZONES.md` §5.4/§5.4a, `08_APPLIED_CHART_CASES.md` CASE-02 | directly-stated (in transcript) with provenance caveats |
| SRC-EX-02-INVALIDATION-GAP | same | not available | ICT-primary invalidation-by-close **NOT in the primary text read** (P-K); community close-through = separate S1 rule (`05` §5.4a/§5.8) | unsupported-or-unavailable / paraphrase |
| SRC-EX-03-NO-TARGET | knowledge `04_LIQUIDITY.md` (lines 21/73/77/87-88/100), `02_SWINGS_AND_WAVES.md` (line 57) | n/a (foundation text) | no target definition in verified primary text; "the available information does not select one as 'the' liquidity target without a task and a stated objective"; stop-cluster mechanism unverified (CF-05) | directly-stated (the refusal) / unsupported (mechanism) |

**Contemporaneous vs retrospective**: the OB lesson is procedural
("candles, validation, entries, stops" — `05` §5.7), not a statistical
result; no outcome-based case is used as evidence (`08` §8.3).  Any
later outcome is stored separately and never enters an earlier simulated
decision.

**Access limitation**: this environment's outbound network allows only
github.com/pypi hosts — YouTube is NOT reachable, so passage timestamps
could not be recovered; they are recorded as "not available" and never
invented.  No quotation is asserted beyond the pinned register.

## 5. Monitoring & replay honesty

* **No live read-only market feed exists** in this repository
  (`LIVE_FEED_STATUS["exists"] is False`); `LiveFeedAdapter` is an
  interface contract only, and using it raises.  The provided loop runs
  on REPLAYED streams; this module must never be described as live-market
  monitoring.  The missing piece (a live adapter) is identified.
* Reused implementations: `CausalObservationStream` (observation
  validation/ordering), `intrabar_path_metrics` (intra-bar ambiguity),
  `AnalysisEngine` (boundary recomputation), `InterpretationLedger`
  (immutable revisions + SP-20 propagation), the analysis runner's
  completion-label frame convention.  New: `ReplayObservationStream`,
  `MonitoringLoop` (step control + change reports + no-fabricated-change
  rule + save/resume), the step-replay driver, these registers.
* Step-by-step replay: the driver holds the full file; the engine at T
  receives only the prefix + the declared time grid (approved metadata);
  future outcomes are usable only after they become available.
