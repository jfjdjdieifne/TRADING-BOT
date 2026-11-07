# Real-Chart Market Element Application Study V1

**Mode:** RESEARCH + PRACTICAL DATASET DESIGN.  
**Scope:** teaching and evaluating correct *contextual application* of ICT market elements (swings, waves, BOS references, liquidity candidates, FVGs, order blocks) on real charts.  
**Non-scope:** no trading recommendations, no new strategy, no scorer/weights/labels-from-profits, no model training, no CLOSED-module modification, no code committed.

**Companion files (this folder):**

- `real_chart_study/annotation_schema_v1.json` — JSON Schema (draft 2020-12) for one annotation record.
- `real_chart_study/sample_annotations_v1.jsonl` — 6 genuine, source-referenced sample records (validated against the schema shape).

---

## 0. Executive summary (عربي — مختصر)

هذا البحث يعالج المشكلة المركزية: نظام تداول قد يطبّق استراتيجية صحيحة بطريقة خاطئة لأنه يختار swings أو مراجع BOS أو مرشّحي سيولة أو FVG أو order blocks غير مناسبة للسياق. لا نبني "ledger" جديد ولا نظام فرضيات عام.

ما أُنجز: (1) تحقّق دقيق من الـ remote HEAD وفحص المصدر الفعلي على الكوميت `6d03397f` (لا checkout قديم)؛ (2) أمثلة حقيقية موثّقة بروابط — أساسها دروس ICT الأصلية (حلقة الـ 2022 Mentorship رقم 3 بتاريخ 2022-01-25 مع transcript كامل، وحلقة 12، وجلسة 2024-09-16 الحية مع شارتات موثّقة على منتدى ICT Sharks)؛ (3) تقييم جودة المصادر والتلوّث بالـ hindsight مسجّل صراحةً؛ (4) مخطّط توثيق (annotation schema) يمنع تسميات زائفة مثل `BEST_FVG` أو `TRUE_SWING` إلا بعقد تفسير مهمّة صريح؛ (5) إجراء مطابقة للمرشّحين (candidate matching) بحالات صريحة (حاضر/غائب/غير متاح وقت القرار/المرشّح موجود لكن الاختيار غير متاح/عدم تطابق التمثيل/خلاف تفسيري/أدلة غير كافية) — بدون fuzzy matching صامت؛ (6) أمثلة على فشل الاستخراج مقابل الاختيار مقابل التفسير؛ (7) إعادة استخدام قدرات الريبو الحالية (2.1A–2.2، 4.1–4.2B، S5، وresearch/trajectory stack)؛ (8) الفجوات الدقيقة في القدرات؛ (9) تجربة عملية (pilot) قابلة للتشغيل على بيانات سوق حقيقية؛ (10) معايير قبول وحدود؛ (11) أصغر مهمة تنفيذية مقترحة (كبحث فقط، لم تُنفَّذ).

الهدف ليس أن يقلّد البوت رسمات شارتات تاريخية، بل أن نفهم *لماذا* اختيرت عناصر معينة، ونختبر إن كان النظام قادرًا على اختيارات قابلة للدفاع من ملاحظات سوق فعلية.

---

## A. Exact inspected commit

| Item | Value | Evidence |
|---|---|---|
| Repository | `https://github.com/jfjdjdieifne/TRADING-BOT` | task + `git remote` |
| Session working branch | `arena/a41fd997-trading-bot` | `git branch --show-current` |
| Working-branch HEAD at inspection | `c905f2b7d4632ab9e44cc631606bfcb8a1345480` | `git log` |
| Remote default-branch HEAD (`HEAD`) | `c905f2b7d4632ab9e44cc631606bfcb8a1345480` | `git ls-remote origin HEAD` |
| Task-named branch | `arena/01a10a21-trading-bot` | task |
| Remote HEAD of task-named branch | `6d03397f3b011eca01b1c56713fb936dc518dc00` | `git ls-remote origin arena/01a10a21-trading-bot` |
| **Exact inspected source commit** | **`6d03397f3b011eca01b1c56713fb936dc518dc00`** ("Add market movement representation research V1") | fetched and inspected read-only |

Verification notes (stale-checkout control):

1. The task's "last verified remote HEAD" (`6d03397f…`) matches the *current* remote head of `arena/01a10a21-trading-bot` exactly — verified live at inspection time. It is **not** the remote default-branch head (`c905f2b7…`).
2. The local checkout (`c905f2b7…`) is **stale relative to `6d03397f…`**: `git diff --stat` shows 26 files / +22,877 lines present only at `6d03397f…` (the whole `research/trajectory` research stack and its tests, `MARKET_MOVEMENT_REPRESENTATION_RESEARCH_V1.md`, FVG-context empirical slice, contextual-hypothesis-resolution build report, FVG pilot closure doc). All inspection of "current producer outputs and the market movement representation research V1" was therefore performed on an exact read-only extraction of `6d03397f…` (`git archive … | tar -x` into a scratch directory outside the checkout), never on the stale tree.
3. **No code was committed. No CLOSED module was modified.** No branch other than the session branch was checked out or pushed. This document and its two companion files are new research files only.

Project governance context (from `docs/STATUS.md` at the inspected commit): Layers 0–5, 6.1A/6.1B, 6.2A-0…6.2A-4 stages, 6.2B, MUF S0–S15, and `7.0` are **CLOSED**. Domain terminology status is **D1/D1.1 PRELIMINARY SOURCE AUDIT — ACCEPTED** (`docs/domain_audit/`), with an open `PRIMARY_REVIEW_BACKLOG.md`. This study is positioned as an application-level companion to D1 (D1 audits *definitions*; this study audits *selection acts*).

---

## B. Verified source examples with links

Evidence-quality-first collection. Chart images are **referenced by URL, not redistributed** (see C). Every publication timestamp below carries its provenance; nothing is invented.

### B1. Primary sources (original ICT material)

| ID | Source | URL | Identity / date provenance | Why usable |
|---|---|---|---|---|
| S1 | **2022 ICT Mentorship Episode 3** — "Internal Range Liquidity & Market Structure Shifts" | https://www.youtube.com/watch?v=nQfHZ2DEJ8c | Channel "The Inner Circle Trader"; page metadata **Uploaded at 2022-01-26** (PLATFORM_METADATA); video-details panel "Date Jan 25, 2022"; transcript opens "this is the tuesday january 25th 2022 ict mentorship" (VIDEO_STATEMENT). Length 52:27. | Full transcript retrieved this session. Contains the homework task framing, explicit alternative-reference handling, MSS context gate, OB series definition application, multiple FVGs, multi-scale liquidity. Chapter list captured (0:35 15-min chart; 2:08 structure shifts; 4:21 2-min review; 14:28 order block; 20:45 1-min; 24:19 OB revisited; 27:33 premium/discount; 41:01 live trade execution). |
| S2 | **2022 ICT Mentorship Episode 12** — "Market Structure for Precision Technicians" (title per secondary notes) | https://www.youtube.com/watch?v=8GkQfdAXZP0 | Identity confirmed via YouTube sidebar on S1's page (channel + playlist "2022 ICT Mentorship", 41 videos: https://www.youtube.com/playlist?list=PLVgHx4Z63paYiFGQ56PjTF1PGePL3r69s). Upload date **not captured** this session → left UNKNOWN. | OB definition ("change in the state of delivery"), ITH/STH nested structure classifications, 15m/5m/1m worked example. Accessed only via secondary compilations this session → quality capped at MEDIUM. |
| S3 | **ICT 2024 Mentorship live stream** — "How To Trade ICT FVGs Correctly: September 16, 2024" | https://www.youtube.com/watch?v=HhgWGduQZQY | Video title/date surfaced in YouTube sidebar and forum embed. Stream date 2024-09-16 (SELF_STATED_IN_TEXT). | Live-annotated NQ session with live-trade example; documented post-hoc with chart screenshots (S4). |

### B2. Documented community/annotation sources (secondary layer)

| ID | Source | URL | Date provenance | Why usable | Quality cap |
|---|---|---|---|---|---|
| S4 | ICT Sharks Forum notes + 5 annotated NQ chart screenshots ("NQ - CE Of ORG As Draw On Liquidity", "NQ - First Presented FVG", "Trade Entry/Exit", "Alternative Stop Loss Placement", "Stop Loss Placement And IOFED") | https://forum.ictsharks.com/t/2024-ict-mentorship-how-to-trade-ict-fvgs-correctly-september-16/601 | Discourse header "post by Daniel on Dec 31, 2024" (FORUM_METADATA) | Concrete chart-coordinate claims + operational entry/DOL rules over S3 | MEDIUM (third-party notes over primary stream) |
| S5 | "Episode 3: Market Structure Insights" (5-page annotated notes of S1) | https://www.scribd.com/document/741686453/ICT-Mentorship-2022-Episode-3-Notes | Upload date not captured (uploader `sanjibnepal99`) | Chart-time labels (9:30/10:16/10:30/11:00/11:16/11:30), price 14,540, label map (1)–(4) | MEDIUM-LOW (re-uploaded notes; may paraphrase) |
| S6 | Student notes with video minute-marks ("Order blocks (minute 14:38)", "minute 42:00 live trade example") — Studocu/Scribd "Tanja Trades" notes | https://www.studocu.com/row/document/zhejiang-university/finance/ict-2022-mentorship-notes-tanja-trades/108072076 (and scribd.com/document/666181194) | Page metadata varies (2023–2025) | Timestamped anchors into S1/S2; two-FVG handling rule | MEDIUM-LOW |
| S7 | "2022 ICT Mentorship" compilation preview (pdfcoffee) | https://pdfcoffee.com/2022-ict-mentorship-9-pdf-free.html | undated preview | Ep.12 quotes (OB series rule, ITH/STH) | MEDIUM-LOW |

### B3. Alternative market-structure interpretations (comparison set)

| ID | Source | URL | Date provenance | Contribution |
|---|---|---|---|---|
| S8 | **Lo, Mamaysky & Wang (2000), "Foundations of Technical Analysis"**, Journal of Finance 55(4) | https://web.mit.edu/people/wangj/pap/LoMamayskyWang00.pdf (mirror: cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf) | publication 2000 (journal) | Operationalizes technical patterns on **smoothed-price local extrema** (kernel regression) — a parameterized alternative to "swings"; patterns defined as sequences of 5 extrema with explicit tolerances. Shows how the same chart yields different extrema sets under different smoothing — the textbook form of "selection depends on representation". |
| S9 | **Smart Money Concepts [LuxAlgo]** (open-source TradingView script) | https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/ | description claims "Updated Sep 23, 2025" (PAGE_METADATA; search-index age conflicts — recorded, not resolved) | Operationalizes internal vs swing structure, BOS/CHoCH, equal highs/lows, OB, FVG with a **configurable pivot lookback (default 50 bars)** and an optional "liquidity sweep requirement" toggle — a widely used *different* structure contract. |
| S10 | Community restatements with divergent OB rules — e.g. TradingView "ICT Concepts for FX and GOLD traders" ("an order block is the last bullish or bearish candle before a major price move", published Mar 30, 2025 per page metadata) https://www.tradingview.com/chart/EURUSD/4Pwu94h1-ICT-Concepts-for-FX-and-GOLD-traders-2025-edition/ ; ForexFactory "Market Structure (MSS & CHoCH) in ICT" thread (2025) | linked | page metadata | Documented **definitional conflict** vs S2's "series of consecutive candles / change in the state of delivery" and vs repo 4.1's single opposite-body candle. |
| S11 | Repo domain audit D1/D1.1 | `docs/domain_audit/` at inspected commit | repo-internal | Preliminary ICT terminology audit + open primary-review backlog; explicitly flags BOS/CHoCH as non-canonical ICT attributions. |

### B4. The sample set (diversity map)

The practical sample is stored as schema-validated records in `real_chart_study/sample_annotations_v1.jsonl` (6 records). Required diversity coverage:

| Study requirement | Record(s) |
|---|---|
| Multiple plausible swing selections | `RCA-2022-EP3-001` (relative equal highs vs 5:00 high — both accepted by source, one preferred by stated rule) |
| Conflicting structural interpretations | `RCA-2022-EP3-002` (context-gated MSS vs unconditional break vs multi-day BOS) + `RCA-2022-EP3-EP12-003` (three competing OB definitions) |
| FVG candidates within different movements | `RCA-2022-EP3-004` (10:30 bullish-shift gap vs 11:30 bearish-shift gap vs upper gap) |
| Liquidity references across scales | `RCA-2022-EP3-005` (London session levels, intraday lows, structural low, range midpoint) |
| Order-block selection ambiguity | `RCA-2022-EP3-EP12-003` (series vs single candle; boundary choice; indecision-candle inclusion) |
| Live/pre-event documented example | `RCA-2024-SEP16-006` (live-streamed session, live trade, "first presented" FVG, ORG-CE draw) |

**Not collected, and why (honest limits):** pixel coordinates of chart images (not transcribed this session; images not copied — rights); tick/depth data behind any example (never public in these sources); the Ep.3 chart *date* (not stated in audio/notes; must be read from the video frame or the community-tab homework link that the lecture references); ICT's X/Twitter pre-market posts (platform not technically accessible this session). No substitute examples were fabricated to fill these gaps.

---

## C. Source-quality and hindsight assessment

Grading per record lives in `evaluation_limits.annotation_uncertainty` and `decision_context.hindsight_class`. Cross-cutting assessment:

1. **Primary vs secondary.** S1 is primary (official channel, transcript retrieved). S2 content arrived only through secondary compilations this session → every S2-derived clause is marked MEDIUM/secondary in `RCA-2022-EP3-EP12-003` until the primary transcript is captured (it is on the repo's `PRIMARY_REVIEW_BACKLOG` spirit). S4/S5/S6 are secondary notes; where they paraphrase, records store `is_quote:false` and say so.
2. **Timestamp discipline.** S1 has a three-way provenance chain (upload metadata 2022-01-26 / video-details 2022-01-25 / audio statement "tuesday january 25th 2022"). All three are stored; none is silently normalized. Unknown timestamps are `null` + `provenance: UNKNOWN` (S2 upload date; Ep.3 chart day; all claimed decision times of teaching recaps).
3. **Hindsight contamination classes used:**
   - `TEACHING_RECAP_WITH_TIME_REFERENCES` (S1/S2 examples): the lecturer annotates a *finished* session. Contamination: selection was made knowing the outcome. Mitigation preserved in the data: the sources state *rules* ("significant only if…", "whenever I see equal highs like this…") that can be evaluated as decision-time rules regardless of the outcome, and they explicitly name alternatives. Any outcome-based reading of these records is forbidden by their `task_contract`.
   - `LIVE_ANNOTATION` (`RCA-2024-SEP16-006`): live-streamed, live-traded session — hindsight contamination of the *act* is low; but the *notes* layer is post-hoc (2024-12-31) and the image pixels were not transcribed → uncertainty MEDIUM, coordinates TEXT_ONLY.
   - `PRE_EVENT_ASSIGNMENT_REVIEWED_LATER`: the S1 homework itself ("go through this particular chart and look for reasons that provided the market structure shift and the buy side and sell side liquidity") was assigned *before* the lecture (community-tab link "sent out the other day"); the lecture is the answer key. This is the repo-friendly teaching protocol and the basis of Pilot I.
4. **Transcript uncertainty.** YouTube auto-transcripts flatten timing and can mis-hear symbols/numbers ("old love" for "old low" in the raw transcript). Records store quotes verbatim and flag this in `data_availability_limitations`. The S5 notes version of the same passages differs in label numbering from the video — both labelings are kept (annotation_uncertainty MEDIUM).
5. **Outcome contamination firewall.** No record contains a label derived from what price did afterwards. Where the source itself reveals the outcome (e.g. the S1 short later succeeds), the record's `forbidden_interpretations` block explicitly bans reading selection quality from that outcome.
6. **Rights.** Chart screenshots (S4) and notes page-images (S5) are copyrighted derivative material. They are referenced by URL only (`chart_image_ref.retrieval_status: REFERENCED_ONLY`). If the owner later needs local chart media for annotation, retrieval must be justified per-source; the dataset stores coordinates + quotes, not pixels.
7. **Source-quality red flags observed (kept, not silently fixed):** a popular TradingView FVG post (Golden_Star1994, Jan 18 2024, https://www.tradingview.com/chart/EURUSD/2zEqoFl6-Fair-Value-Gap-Trading-Strategy/) describes EURUSD while citing price levels "44240–44280" that cannot be EURUSD — an instrument/level inconsistency that would poison annotation if ingested uncritically. It is therefore **excluded from the sample** and recorded here as a cautionary case of `INSUFFICIENT_SOURCE_EVIDENCE`-grade material.

---

## D. Proposed annotation schema

File: `real_chart_study/annotation_schema_v1.json` (JSON Schema 2020-12). One record = **one analytical selection act** on a real chart by a named source.

Required top-level blocks: `source`, `decision_context`, `market`, `chart_region`, `element`, `explanation`, `matching`, `evaluation_limits` (+ optional `task_contract`, `alternatives`, `annotator`). Field-by-field coverage of the task requirements:

| Task requirement | Schema field(s) |
|---|---|
| Source URL and source identity | `source.url`, `source.source_id`, `source.source_kind`, `source.author_or_channel`, `source.is_primary_source` |
| Publication and decision timestamps | `source.publication_timestamp{value,provenance,note}`, `source.decision_timestamp`, `decision_context.claimed_decision_time_utc` — every timestamp carries provenance; `null` is legal, fabrication is not |
| Instrument and venue | `market.instrument{value,confidence,evidence}`, `market.venue`, `market.contract_period`, `market.chart_date` |
| Timeframe and source-data resolution | `market.timeframes{primary,stack}`, `market.source_data_resolution` |
| Chart coordinates and annotated regions | `chart_region.coordinate_space` (CHART_TIME_LABEL / PRICE_LEVEL / BAR_RELATIVE / VIDEO_TIMESTAMP / PAGE_IMAGE_REGION / TEXT_ONLY / UNKNOWN), `chart_region.anchors[]` (each anchor: kind, value, unit, quote/paraphrase + `is_quote`), `chart_region.chart_image_ref` |
| Market-element type | `element.element_type` (SWING, SWING_SEQUENCE, STRUCTURAL_BREAK_REFERENCE, LIQUIDITY_LEVEL, LIQUIDITY_PAIR_OR_CLUSTER, FVG, ORDER_BLOCK, DEALING_RANGE, SESSION_LEVEL, WAVE, DISPLACEMENT_LEG, OTHER) + `direction` |
| Operational definition provenance | `element.operational_definition{definition_text,provenance,era,confidence,conflicts_with[]}` — conflicts are stored as an array and never auto-resolved |
| Alternative candidate references | `alternatives[]` with status EXPLICIT_IN_SOURCE / VISIBLE_ON_CHART / IMPLIED_BY_DEFINITION / NOT_ASSESSED + `why_not_selected` |
| Explanation and supporting evidence | `explanation{trader_explanation, supporting_evidence[], explanation_class}` |
| Hindsight/pre-event classification | `decision_context.hindsight_class` (6 values incl. CONTESTED_PROVENANCE) + `hindsight_notes` |
| Annotation uncertainty | `evaluation_limits.annotation_uncertainty{level,reasons}` |
| Data-availability limitations | `evaluation_limits.data_availability_limitations[]`, `evaluation_limits.not_evaluable_from_ohlc[]` |
| Observable vs interpretive split | `element.observable_vs_interpretive{observable[],interpretive[]}` |

**Label contract (mandatory).** Labels such as `BEST_FVG`, `TRUE_SWING`, `CORRECT_SWING` are **forbidden** unless the record carries a `task_contract` with: `contract_id`, `correctness_clause` (naming source, era, rule, and task), and `forbidden_interpretations`. The contract defines correctness as *replication of the source's stated rule for the stated task* — never market truth, never profitability. Labels must never be derived from future profits or later price paths. Records without `task_contract` support extraction/coverage analysis only.

---

## E. Candidate-matching procedure

Purpose: decide, mechanically and auditably, what the repository's candidate universe can and cannot say about each annotated selection act. Statuses are exhaustive and mutually exclusive per match-row:

| Status | Meaning |
|---|---|
| `CANDIDATE_PRESENT` | An exact/tolerance-equal candidate exists in the producer output as of the decision time (prefix-causal). |
| `CANDIDATE_ABSENT` | The element as defined by the source is not emitted by any targeted producer. |
| `CANDIDATE_NOT_YET_AVAILABLE_AT_DECISION_TIME` | A candidate matching the annotation appears in later output but its **confirmation/availability** is after the claimed decision time (origin-vs-availability, repo S2 semantics). |
| `CANDIDATE_PRESENT_BUT_SELECTION_UNAVAILABLE` | Candidates exist; no mechanism in the stack can pick this one over the others for this task. |
| `REPRESENTATION_MISMATCH` | The source's element is a different *kind of entity* than any producer entity (e.g. multi-candle OB series vs single-candle zone), even if geometry is nearby. |
| `INTERPRETATION_DISAGREEMENT` | Producer classification exists but contradicts the source's operational definition contract (recorded as disagreement, not as producer error). |
| `INSUFFICIENT_SOURCE_EVIDENCE` | The annotation lacks coordinates/data precise enough to test (e.g. chart day unknown). |
| `AMBIGUOUS_MATCH` | More than one candidate satisfies the declared tolerance — reported as ambiguity, never resolved silently. |
| `PENDING` | Matching not yet run (data not obtained). |

**Procedure (per record):**

1. **Freeze the annotation** (record bytes → SHA-256) before any matching, so results cannot retro-edit labels.
2. **Resolve the market slice**: instrument, venue, chart date, resolution. If unresolvable → `INSUFFICIENT_SOURCE_EVIDENCE` with the missing item named. **Do not guess the date.**
3. **Obtain real OHLC** with source identity (`SourceArtifactIdentity`), same discipline as `market_movement_representation_research.py` (timestamps as given, no gap-filling, no fixtures as evidence).
4. **Enumerate candidates prefix-causally** at each `claimed_decision_time` using the existing producers (G). Turn origin/confirmation split into a hard gate for the `NOT_YET_AVAILABLE` status.
5. **Match with declared tolerance only** (`matching.tolerance`: time_bars / price_abs / price_frac). The tolerance converts a stated coordinate into an equality test; it is not a similarity score. Within-tolerance ties → `AMBIGUOUS_MATCH`. There is **no fuzzy path that declares a candidate correct**.
6. **Evaluate selection availability**: is there any task-contract-gated mechanism that could choose the annotated candidate among the enumerated set at the decision time? If no → `CANDIDATE_PRESENT_BUT_SELECTION_UNAVAILABLE` (this is the expected honest answer for most records today).
7. **Compare interpretation contracts** independently of geometry: if the producer's label (e.g. `BOS_UP`) would be assigned where the source's rule withholds significance (e.g. liquidity precondition unmet), record `INTERPRETATION_DISAGREEMENT` against the *named* contract. Never merge contracts.
8. **Emit a match report** listing every candidate ID considered (from actual producer runs — never fabricated IDs), the status per row, the representation gap text, and the record hash. Coverage accounting must show every candidate; no silent pruning (`candidate_universe_pruned: false` discipline inherited from the movement research runner).

What matching **must not** do: upgrade a status because the trade would have worked; downgrade because it failed; treat human labels as truth; resolve definitional conflicts; or fill missing coordinates from "reasonable" reconstruction.

---

## F. Extraction vs selection vs interpretation failures — concrete examples

All three failure families occur *within the same genuine source*, which is exactly the study's point.

**F1. Extraction failure — multi-candle order block (`RCA-2022-EP3-EP12-003`).**  
The source's entity is "one continuous order block" = a *series* of consecutive down-close candles (10:16 + consequent candles), bounded by the series open and the lowest candle's low, indecision candles included. Repo 4.1 emits **single** opposite-body-candle zones created on 2.1C break rows, searching `[boundary, creation)`. Even with perfect data and a perfect swing policy, the annotated entity is **not in the candidate universe** → `CANDIDATE_ABSENT` (multi-candle entity) + `REPRESENTATION_MISMATCH` (selector rule). This is an extraction/representation gap, not a selection error.

**F2. Selection failure — liquidity reference choice (`RCA-2022-EP3-001`).**  
Both candidates (relative-equal-highs cluster; 5:00 single high) are within reach of 2.2's per-swing level candidates. The source states a preference rule (equal highs higher than an old high). The stack has no task-gated selector and no pair/cluster entity; any arbitrary pick (e.g. "most recent swing high") would produce a *valid, extracted* reference that is still the wrong selection for the task → `CANDIDATE_PRESENT_BUT_SELECTION_UNAVAILABLE`. The failure is choosing without the context rule, not failing to draw a line.

**F3. Interpretation failure — the MSS context gate (`RCA-2022-EP3-002`).**  
2.1C will happily emit the first close breach of the 10:16 short-term high and classify it via its pre-state table (`BOS_UP`/`CHOCH_*`/`UNCLASSIFIED_BREAK`). The source's rule accepts that break as significant **only if** the prior run-down traded into sell-side liquidity under an old low — a cross-producer conjunction (2.1C × 2.2) that 2.1C's interpretation never consults. Result: correct extraction, correct local classification, **contextually wrong interpretation** vs the source contract. The same event also shows the scale-semantic trap: "shift" (intraday draw) vs "break" (multi-day) — a labeling choice most SMC restatements collapse.

The taxonomy this yields for evaluator dashboards: **E-fail** (candidate missing), **S-fail** (candidate present, wrong/no chooser), **I-fail** (label/contract mismatch), each counted separately. An S-fail must never be reported as an E-fail and vice versa.

---

## G. Current repository capabilities reused (at `6d03397f…`)

| Capability | Module | Reuse in this study |
|---|---|---|
| Adaptive swing candidates with confirmation policy (quantile over continuation/failed episode history), origin vs confirmation | `structure/swing_detector.py` (2.1A) | swing candidate universe + availability gate |
| Same-type swing sequence classes (HH/HL/LH/LL/EH/EL lineage) | `structure/swing_sequence.py` (2.1B) | sequence context for structural interpretation |
| First wick/close breach facts + explicit minimal interpretation (BOS/CHOCH operational labels, latest-reference semantics, AMBIGUOUS_DOUBLE_BREAK) | `structure/structural_breaks.py` (2.1C) | structural-break candidates; honesty about labels already documented in D1 |
| Immutable liquidity level candidates + lifecycle (touch/wick/close/reclaim), nearest-distance percentile | `liquidity/liquidity_map.py` (2.2) | liquidity candidate universe; equal-highs *pair* gap identified here (H) |
| Single-candle OB candidates + displacement evidence | `zones/order_blocks.py` (4.1) | OB candidate universe; multi-candle mismatch documented (F1) |
| Strict three-bar FVG candidates + lifecycle | `zones/fvg.py` (4.2A) | FVG candidate universe for `RCA-2022-EP3-004` |
| Dealing range + premium/discount geometry | `zones/dealing_range.py` (4.2B) | range midpoint comparisons vs source's ad-hoc "50% of 10:16–11:30 range" |
| HTF/MTF aggregation | `multitimeframe/` (5.1/5.2) | cross-scale frames for `RCA-2022-EP3-005` |
| Candidate wave representation families (ALPHA/BETA/GAMMA/DELTA) with as-of views | `market_understanding/wave_representation.py` (MUF S5) | wave-level candidate universe for future records |
| Representation-comparison research runner (no-winner, `SUITABILITY_NOT_ESTABLISHED`) | `research/trajectory/market_movement_representation_research.py` | the harness pattern + replay-prefix invariance for the pilot |
| Causal market-context core / as-of evidence / verified-context hypothesis resolution (authorization-gated, exact-value discriminators) | `research/trajectory/causal_market_context_core.py`, `contextual_hypothesis_resolution_core.py` | the only lawful future home for task-contract-gated selection evaluation (no new generic hypothesis layer built here) |
| Trajectory stack (Stage4A/4B1/4B2/4C, S2 witnesses, timeline two-clock semantics) | `research/trajectory/*` | decision-time vs availability-time discipline for `NOT_YET_AVAILABLE` |
| Information-time firewall / outcome observer / eligibility / dataset builder | `research/information_time.py`, `outcome_observer.py`, `eligibility.py`, `dataset_builder.py` | keep axis-4 evaluation causal and label-clean |
| Domain source audit + backlog | `docs/domain_audit/*` | definition provenance baseline; this study extends it from definitions to selection acts |

---

## H. Exact missing capabilities

Each item is a *representation or mechanism* gap evidenced by a sample record — not a wishlist:

1. **Chart-region annotation ingestion**: no loader/validator for the annotation schema; no chart-coordinate model (`chart_region`) anywhere in the stack. Blocks everything downstream. (`D`)
2. **Multi-candle order-block entity** ("one continuous order block" series with series-open/lowest-low boundaries, indecision candles included): 4.1 is single-candle by contract. (`F1`, `RCA-2022-EP3-EP12-003`)
3. **Liquidity pair/cluster entity** (relative equal highs/lows as one reference, with proximity rule): 2.2 keeps per-level records and nearest-distance statistics but no pair object; the source's selection act *is* pair-level. (`RCA-2022-EP3-001`)
4. **Session/derived level families as liquidity candidates** (London 2:00–5:00 AM high/low, prior-day high/low, Opening-Range-Gap and its CE midpoint): 1.2 has session *context*; 2.2 has swing levels only; ORG/CE does not exist as an entity. (`RCA-2022-EP3-005`, `RCA-2024-SEP16-006`)
5. **Movement-membership relation between structure events and zones**: which FVG/OB "belongs to the MSS displacement leg" is the core selection act; Stage4B2 attaches zones to trajectories but exposes no leg-membership/`first_presented` ordering w.r.t. a session open. (`RCA-2022-EP3-004`)
6. **Cross-producer context gates**: acceptance rules of the form "break is significant only if prior run traded into liquidity" require conjunctions over 2.1C × 2.2 facts at a decision time; no mechanism evaluates them. (`RCA-2022-EP3-002`)
7. **Task-contract-gated selection layer** (research-only): given a declared task contract + candidate set, report whether the annotated reference is selectable — *without* any generic hypothesis/strategy engine. The existing `contextual_hypothesis_resolution_core` is authorization-gated and pair-discriminator based; a thin, contract-declared selection evaluation would sit beside it, not inside CLOSED modules.
8. **Era-tagged definition registry with conflict preservation**: D1 exists but S2-level qualifiers (OB series, ITH/STH nesting, MSS vs BOS era semantics) remain on `PRIMARY_REVIEW_BACKLOG`; the dataset needs machine-readable `operational_definition` entries keyed by era.
9. **Study-journal / blinded two-pass protocol tooling** for prospective annotation (needed for Pilot I's hindsight-drift measurement).
10. **Pixel-anchor capture** (optional, rights-gated): mapping PAGE_IMAGE_REGION coordinates to bar coordinates.

---

## I. One practical pilot (runnable on real market data)

**PILOT-1 — "Selection-ambiguity replay + blinded study journal" (research only).**

Data (real market data, owner-supplied; the repo's `project/data/raw` currently holds no market data — only a README — and repository fixtures are explicitly *not* market evidence):

- **Primary slice:** /NQ (E-mini Nasdaq 100) 1-minute bars for the Ep.3 chart day — obtainable once the chart date is read from the video frame or the community-tab homework link. Source identity required (CME data vendor of record).
- **Fallback slice (method pilot, explicitly NOT a replication of the ICT example):** BTCUSDT 1-minute bars via the repo's existing Binance Spot kline adapter over an owner-declared window (the field-runner config already targets BTCUSDT 2026-05). All outputs labeled `METHOD_PILOT_NOT_SOURCE_REPLICATION`.

Protocol (no strategy, no recommendations):

1. **Freeze** `sample_annotations_v1.jsonl` (SHA-256) and the 7-status matching table of E.
2. **Run the existing producers** over the slice exactly as `market_movement_representation_research.py` does: shared OHLC producers always; two explicitly declared swing policies (`MOVEMENT_SWING_POLICY_DECLARATIONS_V1`, owner-authorization references as non-empty strings, values owner-supplied — none invented); S5 optional and off by default.
3. **Match** each annotation per procedure E at its decision time (or at a declared study-time for the fallback slice). Emit per-record status + candidate IDs + representation gaps.
4. **Blinded two-pass study journal** (the Ep.3 homework pattern, generalized): pick 10 decision moments in the slice (fixed before viewing outcomes — e.g. session opens). Pass A: an evaluator annotates swings/liquidity/FVG/OB/MSS references from data truncated at the decision time (the repo's as-of projection machinery enforces the truncation). Pass B, ≥48h later: the same evaluator annotates the same moments from the full chart. **Measure self-agreement (A vs B) as a hindsight-drift statistic.** Self-agreement is replication evidence, not correctness.
5. **Report** four separated numbers (J) and the full status table. No composite score. No ranking of swing policies (the movement research runner's `SUITABILITY_NOT_ESTABLISHED` boundary is preserved).

What the pilot establishes: whether the candidate universe covers the annotated acts (extraction), whether anything in the stack could *select* the annotated reference (selection availability), and how much human selections drift when hindsight leaks in (drift). What it does **not** establish: market correctness, predictive edge, or profitability.

---

## J. Acceptance criteria and limitations

**Acceptance criteria (this study):**

1. A — exact inspected commit recorded and remote-HEAD-verified (done: `6d03397f…`, table in A).
2. B — every sample record resolves to a real URL with publication-timestamp provenance or an explicit `UNKNOWN`; no fabricated dates (validated in the JSONL).
3. C — hindsight class + uncertainty level present on every record; chart media referenced-only with rights notes.
4. D — schema file exists, is valid JSON Schema 2020-12 shape, and all sample records satisfy its required blocks (checked programmatically).
5. E — the 9 statuses are exhaustive and mutually exclusive; the procedure bans silent fuzzy correctness; match rows never carry invented candidate IDs.
6. F — at least one concrete, source-grounded example per failure family (extraction / selection / interpretation) — F1–F3.
7. G/H — reused capabilities and missing capabilities each map to inspected modules or sample records.
8. I — pilot is executable against real market data with existing tooling, defines its four separated measurements, and declares its fallback slice honestly.
9. No CLOSED module modified; no code committed; no trading recommendation; no new strategy; no importance score; no profit-derived labels.

**Acceptance criteria (PILOT-1, when run later):**

1. Every frozen record ends in exactly one non-PENDING status with evidence text; unmatched records name the missing data/representation precisely.
2. `AMBIGUOUS_MATCH` rows enumerate all tied candidates; zero silent resolutions.
3. Coverage reported per element type (extraction axis), selection-availability per task contract (selection axis), contract-level agreement per named contract with conflicts preserved (fidelity axis); axis 4 left `NOT_ESTABLISHED` unless pre-registered factual objectives (6.2A-1/2/3 machinery) are actually run.
4. Two-pass drift statistic reported with its protocol (evaluator, interval, moment list frozen beforehand).

**Limitations (hard):**

- Human annotations replicate a human interpretation; agreement with them is not proof of market correctness, and this study never treats them as ground truth.
- Teaching-recap sources are hindsight-contaminated as *acts*; only their stated decision-time rules are evaluable, and only as contract replication.
- Secondary notes may paraphrase or err; Ep.12 primary transcript is still uncaptured; auto-transcripts mis-hear.
- The Ep.3 chart day is unidentified → the flagship example cannot yet be matched to OHLC (`INSUFFICIENT_SOURCE_EVIDENCE` until fixed).
- Chart pixels are not in the dataset; TEXT_ONLY/CHART_TIME_LABEL anchors are what the sources state.
- OHLC cannot evaluate: resting orders, intent, institutional causation, intrabar ordering, or "easiest target" as counterparty fact (`not_evaluable_from_ohlc` on every record).
- CME /NQ data licensing is a real barrier; the fallback BTCUSDT slice tests the method, not the ICT example.

---

## K. Recommended smallest implementation task (only if genuinely necessary)

**Yes, one — and only one:** a read-only **annotation matching harness** (new file under `src/trading_system/research/trajectory/`, e.g. `real_chart_matching_harness.py`, plus focused tests), which:

1. loads and validates `REAL_CHART_ELEMENT_ANNOTATION_V1` JSONL (schema checks only — no labels logic);
2. runs the existing producers through the existing `CausalMarketContextCore` replay interface over an owner-supplied CSV (same constraints as `market_movement_representation_research.py`;
3. enumerates candidates as of each record's decision time (S2 availability semantics reused);
4. applies declared tolerances and emits the 9-status match report + manifest hashes.

Scope exclusions (explicit): no selector, no scorer, no policy defaults, no chart-image handling, no new entities (multi-candle OB / pair-cluster remain documented gaps until separately approved), no CLOSED-module edits. If only one vertical slice can be funded, do **4.2A FVG + 2.2 liquidity** first — they cover 4 of the 6 sample records' producer targets and keep the pilot runnable.

Everything larger (entity additions, selection layer, era registry) should wait for pilot evidence of which gap actually blocks the most records.

---

*Research only. No trading recommendations. No new strategy. No CLOSED-module modifications. No code committed.*
