# Source Reliability & Hindsight-Contamination Report — ICT Chart-Application Learning Dataset V1

Companion to `ICT_CHART_APPLICATION_LEARNING_DATASET_V1.md` (deliverable D). Date: 2026-10-11.

## 1. Scope

Two questions per source family: (a) is what we annotate reliably *about the claimed event* (channel identity, timestamps, instrument, prices), and (b) how contaminated is the record by hindsight. Per the mission, hindsight evidence is never discarded — it is quarantined behind `hindsight_class` and `decision_timestamp.provenance`, and separated from `PRE_EVENT` material.

## 2. Source-family reliability

| Source family | Identity / timestamp provenance | Content reliability | Risks recorded | Disposition |
|---|---|---|---|---|
| ICT 2022 mentorship (Ep.3) via official YouTube channel | Channel **verified official** (official-site backlink, monetization). Video page date is a platform field. | Lesson text = official primary; every price/date claim is inside the video. | Chart **day not identified** in the captured transcript → no OHLC slice can be bound. Notes layer (GitHub/Scribd) is unofficial and adds jargon not in the video. | Reused as DEV learning material with `INSUFFICIENT_SOURCE_EVIDENCE` on geometric matching. |
| ICT 2022 mentorship (Ep.12) | Same official channel. | Ep.12 primary transcript **uncaptured**; reconstruction rests on notes layers (marked as such in the record). | Same chart-day blocker + secondary-source expansion risk. | Kept, provenance-explicit. |
| ICT 2024-09-16 live lesson via ictsharks lesson notes + Scribd mirror | Two **independent** captures with a corroborating timestamp (Discourse post 2024-09-16) and the YouTube event in between. | Lesson statements high-confidence; jargon (C1/C2/C3, ORG/CE) is notes-layer, not official definition. | Chart screenshot not pixel-transcribed; NQ 2024 data unavailable. | DEV material; `INSUFFICIENT_SOURCE_EVIDENCE` until chart day + NQ data captured. |
| SXM journal (ictsharks), 2025-09 | **Forum metadata** gives the post dates (2025-09-25). Claims are the trader's own: BTC/Bybit/TradingView, journal-style entries. Pre-event clause verbatim: *"though the day just began, I expect the today's news drivers to expand price lower"*. | **Genuinely timestamped pre-event analysis exists** (post -007 contains pre-outcome expectations written during the session). Trade log (-008) is post-execution same day. | Screenshot pixels unreachable from sandbox → no chart coordinate transcription; entry price field garbled in the source (`11555`) and left UNRESOLVED; `fp.fvg` term undefined in captured sources; venue = Bybit/TradingView feed vs our Binance Spot proxy. | **Genuinely executable** with declared venue proxy; exit anchor independently verified (below). |
| Marcus journal (ictsharks), 2026-04 | **Forum metadata** gives post dates (Apr 13/14, 2026); in-text clock times ("8:24 AM NY", "7:54 AM NY") are self-stated. | Trade logs are self-reported (claimed "Win"/"BEP", claimed RR). Price math is internally consistent (2.667 vs "1:2.6"; 4.698 vs "1:4.7"). | **Feed alignment NOT established** (posted prices ~275–320 pts below vendor session range); pre-market decision times outside our RTH-only slice; broker feed/contract identity visible only on the unretrieved screenshot. | EVAL material; **not** counted as genuinely executable; no price matching performed against the slice. |
| SXM 2026-06 notes | Forum metadata (2026-06-30). | Month-end principles, verbatim text. | Retrospective by construction; no coordinates. | EVAL interpretation-evidence only. |
| GitHub futures samples (TheSnowGuru, `SDGDGFSDAD/NQ_FUTURES…`) | Public repos, hash-verified when used. | TheSnowGuru NASDAQ CSVs end **2023-09-11** (no 2026); `SDGDGFSDAD` 404. | Scale-mismatched definitions ("NV = volume net of average hourly volume") — not imported. | Dead ends; recorded here so they are not re-tried. |

## 3. Independent verification of the executable records (the SXM 2025-09-25 cycle)

Independent evidence used to test whether our annotated event is reliably *about* that market day (evidence recorded, not synthesized as new claims):

- **Cross-venue price check (proxy declaration: Binance Spot vs journal's Bybit/TradingView).** Our 1m slice for 2025-09-25: open 113,307.01, high 113,510.23, low 108,631.51, close 108,994.49 — a −3.8% crash day. The journal's posted exit **108,500** sits 131.51 (0.121%) below the slice day low, and the journal's own pre-event clause expects *"expand price lower"* — both consistent within the declared 0.2% cross-venue tolerance.
- **Liquidity-band fact.** The posted DOL target coincides with a raw-OHLC prior-lows band at 108,5xx touched 5 trading days (2025-08-29..09-02) on the slice — an OHLC fact, aligned to the journal's "DOL was good" statement without adopting any swing policy.
- **External corroboration (retrieved during verification; kept as evidence, not re-fetched):** the 2025-09-25 crypto liquidation crash is a documented market event; independent price-recap sources for BTC 2025-09-25 agree with the slice day geometry (day open ~113.3k → day low ~108.6k).
- **Verdict for SXM-2025-09-25:** the annotated event is reliably about that instrument/day; the record is **genuinely executable**. Residual risks: `fp.fvg` semantics, entry-price garbling, venue proxy.

## 4. NQ vendor-sample reliability (for the Marcus EVAL records)

Internal: 55,440 rows, monotonic unique timestamps, 0 OHLC geometry violations, but **RTH-only** (405 bars/day, 13:30–20:14 UTC; some coverage anomalies e.g. 2026-09-01 full-day). External anchors (retrieved 2026-10-11, kept as evidence): April-2026 was a historic Nasdaq-100 month (+15.7%, best in 23 years) — consistent with the vendor's April path (+13.68% first-open→last-close on partial endpoints); the vendor's July session low 27,201.5 sits 25.5 pts from the NDX 90-day low 27,176.03 (businessinsider snapshot, pageAge 2026-10-09); ForecastEX Nasdaq-100 settle strikes for 2026-04-13 (>25,200/>25,300/>25,400) are compatible with the vendor's Apr-13 RTH range (non-discriminating between scales).

**Verdict:** `CONSISTENT_WITH_EXTERNAL_ANCHORS_PARTIAL` — usable as an **NQ-family proxy** at session level. But the Marcus entries (25,120.50 / 25,662.25) fall ~275–320 pts below the same-day session lows and pre-date RTH coverage. Hypothesis on record: futures-vs-cash-ETF/CFD basis (April-2026 oil-crisis rate environment plausibly widened basis). **Not adopted** — the missing source is exact: the journal chart's broker feed/contract identity (present on the unretrieved screenshot). Until that is captured, price-coordinate matching for Marcus = `INSUFFICIENT_SOURCE_EVIDENCE`.

## 5. Hindsight contamination — per record

| Record | Write-up timing vs decision | Contamination class applied | Quarantine effect |
|---|---|---|---|
| RCA-2022-EP3-001..005 | Teaching material years later; chart day unknown | `TEACHING_RECAP_WITH_TIME_REFERENCES` | Used for interpretation/selection rationale; no decision-time timestamp claimed. |
| RCA-2022-EP3-EP12-003 | Ep.12 recap, official channel | `TEACHING_RECAP_WITH_TIME_REFERENCES` | Same. |
| RCA-2024-SEP16-006 | Lesson notes compiled after the 2024-09-16 event (Discourse posting date corroborates the window) | `TEACHING_RECAP_WITH_TIME_REFERENCES` | Selection-rationale evidence; chart day unverified. |
| RCA-2025-SEP25-SXM-007 | **During the session, before the outcome** (pre-event clause verbatim) + same-day recap | `LIVE_ANNOTATION` with pre-event span flagged in `hindsight_notes` | The expectation clause is decision-time evidence; the recap portion is not. |
| RCA-2025-SEP25-SXM-008 | After execution same day (outcome "Profit" known at write-up) | `LIVE_ANNOTATION` (selection act preceded outcome) | Outcome field never used as label; entry price left verbatim/UNRESOLVED. |
| RCA-2026-APR13-MARCUS-009 | Same day after both trades (outcome "Win" known) | `LIVE_ANNOTATION` | "Win" is context only. FOMO counter-bias trade preserved as negative selection example. |
| RCA-2026-APR14-MARCUS-010 | Same day after management ("BEP" known) | `LIVE_ANNOTATION` | Same. |
| RCA-2026-JUN30-SXM-011 | Month-end reflection | `TEACHING_RECAP_WITH_TIME_REFERENCES` | Interpretation-evidence only; excluded from extraction denominators. |

## 6. Disagreements and unresolved items (preserved, never flattened)

1. **Entry price `11555` (SXM-008):** two readings have partial support (113,55x vs 115,550); **none adopted**; recorded verbatim in `chart_region.anchors`.
2. **`fp.fvg` term:** appears in SXM's reason-for-trade line; not defined in any captured source; not mapped to any repository entity.
3. **2022-era entry anchor (Ep.3) vs SXM's 4h-FVG entry:** different operationalizations of "enter at the FVG" (OB-open-inside-FVG vs raid-into-gap) — recorded as `conflicts_with` in the records; not resolved.
4. **Marcus scale vs vendor scale:** futures-vs-cash-basis hypothesis recorded, not adopted; matching suspended.
5. **TradingView 4h binning vs our UTC-anchored 4h aggregation:** anchor offset possible; tolerance `time_bars: 3` declared at dataset level.

## 7. Source limitations that no amount of annotation can remove

- Forum screenshot pixels are not retrievable from the sandbox → all chart-coordinate transcription from images is impossible here (TEXT_ONLY / PRICE_LEVEL coordinate spaces used instead).
- The Ep.3 chart day is not stated in the transcript → the six 2022 records cannot be bound to OHLC data without the original video frame or community-tab link.
- The Marcus feed identity exists only on the chart screenshot.
- The BTC/Bybit prints (journal venue) are unavailable; Binance Spot is a declared proxy only.
