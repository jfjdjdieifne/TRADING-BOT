# ICT Chart-Application Learning Dataset V1 — Build Report

**Task:** Build a small but high-quality dataset of real, source-verifiable ICT chart-application examples that teach/evaluate how market elements are selected contextually from actual OHLC observations.
**Date:** 2026-10-11 · **Branch:** `arena/a41fd997-trading-bot` (docs-only; no code committed) · **Dataset root:** `project/trading_project/docs/research/real_chart_study/dataset_v1/`

This is a research artifact. It contains **no trading recommendations**, no new market detectors, no importance scores, and no strategy development. Every element label is the **selection the source made**, evaluated against what was visible at the decision moment — never "the true/best element", never a hindsight pattern.

---

## A. Exact repository commit inspected

| Item | Value |
|---|---|
| Target commit (HEAD of task's source ref) | `3a33ab48c42ac8c224a693d4b5c656b0f3601ff4` on `arena/01a10a21-trading-bot` (checked with `gh api`; the task's `6d03397f…` was stale) |
| Diff `6d03397f → 3a33ab48` | **additive CLI only** — `field_runner.py` `--progress` flag (`parse_args`), `field_runner/core/field_pipeline.py` `on_step` callback, `progress.py` helper. Nothing else. Engine semantics unchanged. |
| Files inspected in this build | `docs/STATUS.md` (all gates CLOSED), `market_elements/D1_market_element_reliability_matrix_v1_1.json`, `contract_studies/C2_swing_policy_contract_resolution_v1.md`, `C3_selection_contract_resolution_v1.md`, `zones/fvg.py` (4.2A V1.1 contract: creation-first, strict three-bar gap, unmitigated state, FIRST_TOUCH/coverage/breach/reclaim facts), `orderflow/volume_delta.py` (3.1 V1.1: explicit "no divergence/CVD/session-reset semantics"), `zones/order_blocks.py` (4.1), `market_structure/swing_detector.py` (2.1A + persisted-state contracts), `liquidity/liquidity_map.py` (2.2), `execution_context/market_context.py`, `time_windows/session_profile.py`, `config.py`, `field_runner/config/field_run_config.json` |
| Owner-policy fact | `field_run_config.json`: `swing_quantile: null`, `swing_prior_lower_mult: null`, `swing_prior_upper_mult: null` → swing-dependent modules are **NOT_CONFIGURED** by owner declaration; no parameters were invented to run them |

## B. Dataset files and schema

All in `real_chart_study/dataset_v1/` (plus the schema itself updated in the study folder):

| File | Contents |
|---|---|
| `dataset_records_v1.jsonl` | **11 records.** The six annotations of the Real-Chart Element Application Study V1 reused **verbatim** (content unchanged; only a `dataset` block attached) + five new records from timestamped journal sources. Validated against the schema (0 errors). |
| `../annotation_schema_v1.json` (updated, additive) | Record schema v1.1: adds `element_type` values `INVALIDATION_REFERENCE`, `TARGET_REFERENCE`; adds `match_status` values `PRODUCER_BLOCKED_NO_AUTHORIZED_POLICY`, `OUT_OF_DATA_SLICE_COVERAGE`; adds optional `dataset` block (`partition`, `executability`, `data_slice_refs` with venue-relation tags). Old records remain valid (non-breaking). |
| `partitions_v1.json` | DEV/EVAL assignments, basis, near-duplicate policy, usage rules (F). |
| `coverage_report_v1.json` | Extraction/selection/interpretation coverage for the executable cases (E), computed with the repo's own engines; full engine output hash-referenced. |
| `source_reliability_hindsight_v1.md` | Deliverable D (separate file). |
| `ICT_CHART_APPLICATION_LEARNING_DATASET_V1.md` | This report (A–H). |

**Schema summary.** Each record carries: `source` (URL, forum/video metadata, `publication_timestamp.provenance`, `decision_timestamp.provenance`, access/rights notes), `decision_context` (task, evidence-available-at-decision list, `hindsight_class`), `market` (instrument/venue/timeframes with confidence + evidence), `chart_region` (coordinate space, verbatim-price anchors, chart-image reference with retrieval status), `element` (type, direction, `selection_claim`, `operational_definition` with provenance + `conflicts_with`, `observable_vs_interpretive` split), `alternatives` (competing candidates with explicit status and why-not), `explanation` (trader's explanation with verbatim quotes), `task_contract` (the task-relative correctness clause + forbidden interpretations), `matching` (per-repo-producer rows: status, evidence, representation gap, tolerance), `evaluation_limits`, `dataset` (partition + executability + slice refs).

**Record inventory (labels are selections, not market truth):**

| Record | Element (the selection) | Why-it-matters (mission priority) | Partition | Executability |
|---|---|---|---|---|
| RCA-2022-EP3-001 | SWING pair (2022→current dealing range) | swing/wave selection + "not all equal" | DEV | NOT_EXECUTABLE |
| RCA-2022-EP3-002 | STRUCTURAL_BREAK_REFERENCE (STH/STL change + event confirmation) | structural reference chosen for a specific task | DEV | NOT_EXECUTABLE |
| RCA-2022-EP3-EP12-003 | WAVE set + ORDER_BLOCK (OB = FVG zone + dominant candle) | wave selection + multi-candle OTE rule (Ep.12) | DEV | NOT_EXECUTABLE |
| RCA-2022-EP3-004 | FVG (displacement-created) + entry anchor = OB open inside it | why the FVG region, with explicit alternative annotations | DEV | NOT_EXECUTABLE |
| RCA-2022-EP3-005 | LIQUIDITY_LEVEL/BUFFER (session PDH/PDL + midnight open ±10%) | liquidity level as anchor, tolerance rule stated | DEV | NOT_EXECUTABLE |
| RCA-2024-SEP16-006 | SWING pair + invalidation concept + ORG/CE references | swing selection before liquidity extraction; stop-placement lesson | DEV | NOT_EXECUTABLE |
| RCA-2025-SEP25-SXM-007 | FVG (4h entry array, raided-and-rejected interior) | **why this element** vs the abandoned deep-OTE alternative; pre-event expectation | DEV | **EXECUTABLE** |
| RCA-2025-SEP25-SXM-008 | LIQUIDITY_LEVEL (DOL = old lows 108,5xx) + FVG entry | target-element selection with an explicit rejected alternative; exit anchor verified | DEV | **EXECUTABLE** |
| RCA-2026-APR13-MARCUS-009 | INVALIDATION_REFERENCE (SL 25112.25) + target ref | invalidation selection + documented FOMO counter-selection | EVAL | PARTIALLY_EXECUTABLE |
| RCA-2026-APR14-MARCUS-010 | INVALIDATION_REFERENCE (SL 25651.50) + target ref | invalidation selection + management deviation from target | EVAL | PARTIALLY_EXECUTABLE |
| RCA-2026-JUN30-SXM-011 | OTHER (selection principles: structure>HTF-bias>SMT) | **why a trader selects one reference family over another** | EVAL | NOT_EXECUTABLE (evidence only) |

**Element-type coverage vs the mission's priority list:** swing/wave ✓ (001, 003, 006) · structural reference ✓ (002, 009 bias+DOL) · liquidity level/cluster ✓ (005, 008) · FVG ✓ (004, 007, 008) · order block ✓ (003) · **invalidation reference ✓ (006 concept, 009/010 numeric)**. Genuine **liquidity clusters/pairs** (sweeps of paired highs/lows) remain a documented gap (no source captured that names a cluster with coordinates in a window we can verify) — reported as empty rather than filled with plausible-but-unverifiable material.

**New records — source provenance (exact):**
- **007/008** — SXM journal (ictsharks Discourse): `https://forum.ictsharks.com/t/sxms-public-trading-journal/717/5` and `/6`, posts dated **2025-09-25** (forum metadata). Pre-event clause captured verbatim in 007.
- **009/010** — Marcus journal: `https://forum.ictsharks.com/t/marcus-trading-journal/737/6` and `/7`, posts dated **2026-04-13 / 2026-04-14** (forum metadata); in-text decision clock times 8:24 AM / 7:54 AM NY (self-stated).
- **011** — SXM notes: `https://forum.ictsharks.com/t/sxms-public-trading-journal/717/39`, **2026-06-30**.

## C. Genuinely executable examples (against verified OHLC slices)

**Count: 2** — `RCA-2025-SEP25-SXM-007` and `RCA-2025-SEP25-SXM-008`.

Both bind to `SLICE-BTCUSDT-1M-2025-08-09` (Binance BTCUSDT 1m, complete months Aug+Sep 2025; sha256 in `coverage_report_v1.json`; venue relation **VENUE_PROXY** — the journal's venue is Bybit/TradingView). Executability means: the named element family can be tested against the slice with the repo's own engines at the decision date, with alternatives and selection reasoning preserved.

Two more are **partially executable** (Marcus 009/010): session-level slice facts and producer universes computed, but decision-time price matching is blocked (see H). The six reused 2022/2024 records are **not executable** (chart day / data window blockers, preserved as-is). Nothing was filled with plausible-but-unverifiable examples; where nothing is executable for a claim, the claim is recorded as blocked.

## D. Source reliability & hindsight report

See **`dataset_v1/source_reliability_hindsight_v1.md`**. Headline verdicts:
- SXM-2025-09-25 cycle: **genuinely timestamped pre-event analysis exists** (the "expand price lower" clause predates the session outcome) and the event is independently verified across venues (posted exit 108,500 vs Binance day low 108,631.51 = 0.121%; crash day matches the pre-event quote). → records 007/008 are reliable about their claimed event.
- Marcus-2026: self-reported logs with internally consistent price math (2.667 vs "1:2.6"; 4.698 vs "1:4.7") but **feed alignment NOT established** (posted entries ~275–320 pts below the vendor's same-day session lows; decision times pre-RTH). Futures-vs-cash-basis hypothesis recorded, **not adopted**.
- All hindsight classes quarantined per record; outcome fields ("Win"/"BEP"/"Profit") are context only and are excluded from any label.

## E. Extraction / selection / interpretation coverage (executable cases)

Computed with the repo's own engines only — `CausalFVGEngine` (4.2A V1.1) and `CausalVolumeDeltaEngine` (3.1 V1.1, OHLCV_PROXY) — over verified slices. Full output: `dataset_v1/coverage_report_v1.json` (complete engine artifact: `/home/user/work/coverage_executable_v1.json`, sha256 `34c300bf…b67f`).

| Axis | RCA-2025-SEP25-SXM-007 | RCA-2025-SEP25-SXM-008 |
|---|---|---|
| **Extraction** | **CANDIDATE_PRESENT (family).** 4h UTC-anchored: 366 bars, 81 FVGs created (40B/41B); **73 existed before the decision day**; **33** of those overlap the 110k–114k band where the decision day traded | **CANDIDATE_PRESENT + OHLC-fact verified.** 1m: **564 gaps created on the trade date** (306 before 13:00 UTC) — the intraday selection problem is quantified; 108,5xx prior-lows band touched 5 days 2025-08-29..09-02 (raw OHLC facts); exit anchor 108,500 vs day low 108,631.51 within the declared 0.2% cross-venue tolerance |
| **Selection** | CANDIDATE_PRESENT_BUT_SELECTION_UNAVAILABLE + **AMBIGUOUS_MATCH** (no chooser in the stack — constraint; no gap coordinates in source → nothing declared correct) | **AMBIGUOUS_MATCH** (564 same-day candidates; `fp.fvg` undefined → no binding) |
| **Interpretation** | GAP: "raid-and-reject inside the gap" has no 4.2A counterpart; 90min BTC/ETH **SMT has no producer** | GAP: no **DOL** entity; 2.2 blocked (owner swing policy) |

For the partially executable Marcus cases: 4.2A universes computed (81 FVGs on 04-13, 92 on 04-14; 3.1 ran 405 rows in explicit OHLCV_PROXY mode) → **extraction works**; selection = `OUT_OF_DATA_SLICE_COVERAGE`; interpretation = `OUT_OF_CONTRACT` ("CVD divergence" is explicitly outside 3.1 V1.1's contract). `RCA-2026-JUN30-SXM-011` is excluded from extraction denominators (principles-level record).

## F. Development / evaluation partition design

From `dataset_v1/partitions_v1.json`:
- **DEV** (learning): the six reused records (2022 mentorship + 2024 lesson) + SXM-2025 (`-007`, `-008`). Sources: ICT official lessons + notes layer + SXM 2025 journal. Period 2022→2025.
- **EVAL** (chronological holdout, distinct authors): Marcus-2026 (`-009`, `-010`) + SXM-2026 notes (`-011`). Period 2026.
- **No near-duplicates across partitions:** same-lesson records (Ep.3 facets; the Sep-25 analysis+log pair; the Apr-13/14 same-template logs) are each confined to one partition; SXM appears on both sides but with different content types and periods (2025 trades vs 2026 principles).
- Usage rule: EVAL must not tune anything in V1; it is the honest default test set once a selection model exists.

## G. Minimum next learning / evaluation step

1. **Freeze the selection problem before any model work.** The repo's selection module is deliberately unfilled pending *owner* swing-policy declaration (`swing_quantile` etc. are null). The dataset's next learning step is therefore not "train a selector" but **define the task contract first** (mission/Deed line: *"Defining the task contract must come before model work"*), using these records as the specification of the decision acts to be modeled.
2. **Unblock the three swing-dependent probes** by declaring the owner policy values in `field_run_config.json` (policy, not code) → run 2.1A/2.2/4.1 against the SXM-2025 slice to upgrade `PRODUCER_BLOCKED_NO_AUTHORIZED_POLICY` rows to real candidate sets.
3. **Pin the Ep.3 chart day** (original video frame / community-tab link) → makes the five richest learning records bindable to OHLC.
4. **Capture the Marcus chart screenshot metadata** (broker feed + contract month) → resolves the feed-alignment blocker and unlocks price-coordinate evaluation for the EVAL partition.
5. Only then: a first selection model (e.g., the contract-resolved w2 minimal selector implied by C3), evaluated on DEV, untouched on EVAL until freeze.

## H. Exact blockers & limitations

| # | Blocker | Exact missing source | Records affected | Effect |
|---|---|---|---|---|
| 1 | Owner swing policy not declared | `field_run_config.json`: `swing_quantile`, `swing_prior_lower_mult`, `swing_prior_upper_mult` (all null) | 001–006 (partially), 008 (2.2 rows), 009–010 | 2.1A/2.1B/2.1C/2.2/4.1/4.2B probes = `PRODUCER_BLOCKED_NO_AUTHORIZED_POLICY` (engines deliberately not run) |
| 2 | Ep.3 chart day unidentified | Original Ep.3 video frame / ICT's community-tab link naming the chart day | 001–005 | Cannot bind OHLC slices; records kept as learning material |
| 3 | Chart pixels unreachable | Forum attachment bytes (upload URLs return no content from sandbox) | 007–010 (and reused records) | No image-coordinate transcription; TEXT_ONLY / PRICE_LEVEL coordinate spaces used |
| 4 | Marcus feed identity unknown | The journal chart's broker feed + contract month (visible on screenshot 1835×881) | 009–010 | Price matching = `INSUFFICIENT_SOURCE_EVIDENCE`; feed-alignment hypothesis not adopted |
| 5 | NQ 2024-09-16 data absent | QL2M NQ 1m archive (paid Kaggle/Exchange reports) or any verified free NQ 1m 2024-09-16 slice | 006 | `OUT_OF_COVERAGE` vs available samples |
| 6 | SXM entry price garbled | None resolvable — source field reads `11555`; both candidate readings recorded | 008 | Entry-level matching skipped; verbatim preserved |
| 7 | `fp.fvg` undefined | Any ICT/SXM definition note for the term | 008 | No interpretation mapping; kept verbatim |
| 8 | SMT has no producer | N/A — cross-asset entity is outside the current stack | 007, 011 | `INTERPRETATION` gap recorded (no detector added — constraint) |
| 9 | Liquidity-cluster example absent | A source naming a paired-liquidity cluster with coordinates in a verifiable window | (gap) | Priority element type remains uncovered; not filled with synthetic examples |
| 10 | Ep.12 primary transcript uncaptured | YouTube auto-transcript of Ep.12 (transcript endpoint failed) | 003 | Notes-layer provenance retained and labeled |

## Integration classification (producer contracts)

Per the mission's classification for selected elements (representable / produced under authorized policy / available at claimed decision time / among competing candidates / missing due to definition mismatch / unavailable due to source limitations):

| Element claim | Representable? | Produced under authorized policy? | Available at decision time? | Among competing candidates? | Missing (definition mismatch) | Unavailable (source limits) |
|---|---|---|---|---|---|---|
| SXM 4h FVG (007) | Yes (4.2A) | Yes (4.2A needs no swing policy) | Yes (73 as-of; 33 in band) | Yes — **ambiguous**, none correct | "raid-and-reject inside" qualifier | pixels |
| SXM DOL old-lows (008) | Partially (2.2) | **No** (swing policy null) | Yes (band established prior days) | n/a (blocked) | "DOL" entity absent | pixels |
| SXM 1m `fp.fvg` (008) | Yes (4.2A) | Yes | Yes (564 same-day) | Yes — ambiguous | **`fp.fvg` undefined** | pixels |
| SXM exit anchor (008) | Yes (OHLC fact) | n/a | Yes | matched within 0.2% | — | Bybit prints (proxy used) |
| Marcus SL/TP refs (009/010) | **No entity** in stack | No (swing-dependent mapping blocked) | **No** (pre-RTH; slice lacks the moment) | n/a | invalidation/target entity absent | feed identity |
| Marcus "CVD divergence" (009) | **No** (3.1 excludes CVD semantics) | n/a | n/a | n/a | outside all contracts | Quantower data |
| Ep.3 swings/FVG/OB (001–005) | Partly (4.2A yes; OB no) | OB/liquidity **No** | Unknown (day unpinned) | n/a | multi-candle OB definition | chart day, pixels |
| SXM principles (011) | n/a (text) | n/a | n/a | n/a | "structure> SMT" precedence unrepresentable | — |

---

### Provenance & integrity notes
- Six reused records keep their original source references, operational-definition provenance, alternatives, uncertainty notes, and hindsight flags unchanged (additive `dataset` block only).
- All verbatim price strings are preserved as posted; no coordinate was invented, normalized, or "fixed" (`11555` stays `11555`).
- The coverage probe ran only closed, public engine contracts (4.2A, 3.1 OHLCV_PROXY). No new detector, no generic importance score, no strategy, no recommendations.
- Label contract (carried from the study): the human-selected candidate is task-correct **for the source's stated act**; `BEST_FVG`/`TRUE_SWING` style labels are forbidden.
