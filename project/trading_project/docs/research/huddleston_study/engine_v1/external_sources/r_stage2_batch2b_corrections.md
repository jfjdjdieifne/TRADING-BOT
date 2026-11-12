# R — Full-setup catalog, Stage 2, Batch 2b: correction and completion of Batch 2 (entry zones)

**Run:** 2026-11-09 (UTC). **Base:** `engine_v1/external_sources/`. **Tier:** `TIER2` only — every line is a
publisher's claim, never a claim by Michael Huddleston. **Stage 2, Batch 2b = correction pass on
`q_stage2_batch2_entry_zones.md` + coverage extension.**

**Terms in this batch (6):** `Order block incl. mean threshold` · `Breaker block` · `Balanced price range` ·
`OTE` · `Consequent encroachment` · `PD array`.

**Rules applied**

- Read-only research. No engine code run or opened, no market data loaded, no existing file edited
  (`q_stage2_batch2_entry_zones.md` was read, not modified).
- Every quote below is verbatim text from a page **re-opened with the page-fetch tool in this run**. No Stage-1 or
  Batch-2 quote was carried over without re-opening its page. Chunk counts are recorded per page.
- No outside ICT knowledge. No invention. Quotes verbatim, English, ≤ 25 words.
- No chatbot/AI page, no video page, no login/paywall/pirated page. (Two course/eBook banners on
  `innercircletrader.net` are advertising; the article text behind them is free and was read.)
- `NOT_STATED` = the page was read and says nothing on that dimension. Silence is never agreement and never a
  conflict. `PARTIAL` = not every chunk was read; the missing part is named.
- No ranking by popularity, no winner chosen; the word "standard" is not used as a claim.
- **Independence.** `innercircletraders.net`, `innercircletrader.net`, `theinnercircletraders.com` = three
  domains, **one** publisher, `RELATIONSHIP_UNCLEAR`, written `G1`, counted once. No page read in this run shows a
  shared author, owner or network between them.
- Images: **none viewed** — see Section D for the two methods actually available and their results.

---

# A — AUDIT OF BATCH 2 (items 1–9)

Each item: `CONFIRMED` / `NOT_CONFIRMED`, the exact page sentence that decides it, then the corrected
classification.

## A1 — V-BPR-9 ("A BPR outranks a standalone FVG") and V-PDA-7 / V-PDA-8 / CONFLICT-PDA-B

**NOT_CONFIRMED for C-BPR-13 and C-BPR-15. CONFIRMED for C-PDA-13.**

Deciding sentences, re-opened this run:

- ictkillzone.com, `https://www.ictkillzone.com/ict-2022-model` (4 of 4 chunks):
  "None of these outranks the others by rule — pick the one you will apply the same way every time."
  The three things being compared in that paragraph are the **fair value gap, the order block and the balanced
  price range**. `C-BPR-13` therefore says the **opposite** of V-BPR-9. It cannot support it.
- fxnx.com, `https://fxnx.com/en/blog/ict-smc-glossary-80-trading-terms-defined` (4 of 4 chunks):
  "The overlapping price band represents double-sided liquidity delivery, making it a fortress for retests."
  `C-BPR-15` says the band is strong for retests; it **does not compare** the BPR with a standalone FVG. It
  cannot support a ranking claim.
- G1 / theinnercircletraders.com, `https://www.theinnercircletraders.com/ict-balanced-price-range/`:
  "The Inner Circle Trader methodology uses the BPR as a premium entry zone — ranked above a standalone FVG in the
  PD array hierarchy" — `C-PDA-13` **does** support it, and the same page adds
  "A BPR is a higher-probability reaction zone than a standalone FVG because the bidirectional institutional
  interest creates stronger support".

Corrected classification:

| Variant | Old | New | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-BPR-9 | SINGLE, cases C-BPR-13 + C-BPR-15 + C-PDA-13 | **SINGLE**, cases **C-PDA-13 + C-BPR-19 + C-BPR-20** (C-BPR-13 and C-BPR-15 removed) | 3 | G1 only | SINGLE |
| V-PDA-7 | SINGLE, case C-PDA-13 | **unchanged SINGLE**, cases C-PDA-13 + C-BPR-19 | 2 | G1 only | SINGLE |
| V-PDA-8 | SINGLE, case C-PDA-08 | **SINGLE re-cited**: C-PDA-08's own words do **not** say "no array outranks another by rule". The supporting sentence is the ictkillzone "None of these outranks the others by rule" sentence (Batch 2's C-BPR-13). C-PDA-08 is re-labelled as a **membership/role** statement, not a ranking statement. | 1 | ictkillzone | SINGLE |
| CONFLICT-PDA-B | G1 + altrady vs ictkillzone | **Upheld with the citation correction above.** altrady: "Premium and discount arrays are the reaction zones ICT ranks by importance"; G1: "ranked above a standalone FVG in the PD array hierarchy"; ictkillzone: "None of these outranks the others by rule". | — | altrady + G1 vs ictkillzone | CONFLICT |

## A2 — V-BRK-12 ("many traders take only the first retest") cites C-BRK-21

**NOT_CONFIRMED that C-BRK-21 supports it. The variant survives on a different sentence from the same page.**

- Deciding sentence for the citation: tmgm.com,
  `https://www.tmgm.com/en/academy/trading-academy/breaker-block` (4 of 4 chunks):
  "In both cases the third swing is the liquidity sweep and the fourth swing is the CHoCH."
  That is swing mapping. It says nothing about retest count. `C-BRK-21` cannot support V-BRK-12.
- The real sentence exists on the same page (chunk 2 of 4):
  "The setup carries more weight when it lines up with the higher timeframe trend, and many traders only trade
  the first retest." Also chunk 2: "Trading only the first retest is a common habit and not a fixed rule, so
  treat later retests with more caution." And the validity table row: "Many traders see the first retest as the
  cleanest".

Corrected classification: **V-BRK-11** (renumbered; old V-BRK-12) keeps the statement "many traders trade only
the first retest", now cited to the **new case C-BRK-34** (with C-BRK-35 and the table row as supporting cases),
and **upgraded SINGLE → SAME** because proea.app states the same substance:
"The first retest is the first candle back into the breaker from its new side. That's where breaker traders look
for an entry." (proea.app, `https://proea.app/en/blog/breaker-block`).

## A3 — CONFLICT-OTE-A ("which swing anchors the retracement")

**NOT_CONFIRMED as a conflict. Reclassified.**

- ictkillzone.com (4 of 4 chunks): "the 62–79% retracement of the displacement leg, measured from the raid
  extreme to the low (bearish) or high (bullish) of the displacement" — an explicit anchor.
- altrady.com (3 of 3 chunks): "OTE is the zone between the 62% and 79% Fibonacci retracement of a swing" —
  anchor named only as "a swing".
- fxnx.com (4 of 4 chunks): "the **OTE (Optimal Trade Entry: 62% to 79% retracement levels)**" — no anchor.
- fundingpips.com (3 of 3 chunks): "an optimal trade entry (OTE) zone between the 62% and 79% retracement of a
  swing" — anchor named only as "a swing".

No page read in this run gives a **different explicit anchor**; three pages give none. Silence is not a conflict.

Corrected classification:
- **V-OTE-6** = SINGLE, ictkillzone, "anchor = raid extreme → displacement extreme" (case C-OTE-04).
- **V-OTE-7** = `NOT_STATED` group (altrady, fxnx, fundingpips) — recorded as silence, not as a variant and not
  as a conflict.
- **CONFLICT-OTE-A removed.** One lead, not usable as a quote: proea.app's candle-range-theory page states in
  search-result text "62% to 79% back into the leg that broke structure"; I opened that page (1 of 3 chunks) and
  the sentence is **not** in the chunk read, so it is recorded as **C-OTE-13 / PARAPHRASE_NO_QUOTE** and cannot
  support SAME or a conflict.

## A4 — V-CE-1 recount without ictflow.com, and V-CE-4 membership

- ictflow.com, `https://ictflow.com/blog/ict-complete-2022-trading-strategy` (1 of 1 chunk): the page's only CE
  sentence is "Enter at the CE." It **does not compute** CE. Correctly excluded.
- **V-CE-1 recount: 5 units** (was 6): fxnx (C-CE-01), ictkillzone (C-CE-03), liquidityscan (C-CE-05),
  fundingpips (C-CE-08), **quartersequence (C-CE-14, new)**. Mark stays **SAME**.
- **V-CE-4 recount: 3 units** (was 4): ictkillzone (C-CE-03), liquidityscan (C-CE-05), fundingpips (C-CE-08).
  Mark stays **SAME**. C-CE-09 (ictflow "Enter at the CE.") is an use-case statement only and is moved out.

## A5 — CONFLICT-BRK-A (sweep required before a block may be called a breaker)

**Reclassified as a documented alternative convention reported by one publisher. No conflict.**

- tmgm.com breaker page (4 of 4 chunks): "Some SMC traders call any broken order block a breaker block and treat
  the liquidity sweep as an optional extra. This guide follows the ICT version". tmgm reports the convention and
  explicitly does **not** adopt it.
- I then checked whether **any other publisher adopts it**. None does:
  - velotrade.com: "The sweep is the key detail."
  - fxnx.com: "A Breaker Block is an Order Block that swept a liquidity pool"; and on the second fxnx page:
    "it never sweeps the prior structural extreme" (said of the mitigation block, by contrast).
  - G1 / innercircletraders.net: "Confirm that the break involved a sweep of the lows below the order block,
    taking out retail long stop losses."
  - liquidityscan.io, `https://liquidityscan.io/blog/what-is-an-order-block`:
    "The key difference is that a breaker block must first run liquidity before failing."
  - proea.app is `NOT_STATED` on a sweep requirement (it requires a close through plus a structure break).

Corrected classification: **ALT-CONVENTION-BRK-A** — "any broken order block is a breaker block, sweep
optional", reported by tmgm.com only, adopted by no publisher in this run. `V-BRK-2` (sweep required) is
therefore **SAME across 5 units**: velotrade, tmgm, fxnx, G1, liquidityscan.

The same logic applies to **CONFLICT-BRK-B** (wick vs close), which item 9 surfaced: G1 reports
"Some ICT traders accept a wick through the zone as a violation" and then recommends the close; every publisher
that states a rule states the close (G1, tmgm, liquidityscan, proea). proea reports wick-based rules only at
tool level ("[Order Blocks by Flux Charts] turns an order block into a breaker as soon as price trades past its
far edge, by wick by default"), i.e. again reported, not adopted. **CONFLICT-BRK-B → ALT-CONVENTION-BRK-B.**
Breaker therefore ends with **0 CONFLICT groups and 2 recorded alternative conventions**.

## A6 — Missed conflicts on the OB / breaker / BPR dimensions

### A6.1 The missed conflict named in the brief — where the OB stop goes

**CONFIRMED as a conflict. Added as CONFLICT-OB-B.**

- fxnx.com (4 of 4 chunks), step 5 of the execution pipeline:
  "Place your stop-loss precisely 1 pip beyond the Mean Threshold (50%) of the Order Block or beyond the high of
  the manipulation swing." → **V-OB-20** ("stop at / 1 pip beyond the mean threshold"), SINGLE, fxnx.
- velotrade.com (3 of 3 chunks), "Common order block mistakes" → "**Stops inside the block.**":
  "Stops inside the block. A stop at the mean threshold gets hit on normal noise. Stop beyond the full block or
  skip the trade." → **V-OB-19** ("stop beyond the full block"), now SAME across 4 units: velotrade,
  ictkillzone ("Stops go beyond the full candle wick in both cases."), liquidityscan ("For order blocks there is
  far less debate: the stop belongs beyond the candle's extreme, with a small buffer"), tmgm ("Most traders
  place the stop loss just beyond the order block").

Named variants: **V-OB-20** (fxnx) vs **V-OB-19** (velotrade + ictkillzone + liquidityscan + tmgm).
Note recorded honestly: fxnx's sentence offers **two** options ("or beyond the high of the manipulation swing");
the conflict is between its mean-threshold option and the other publishers' full-block rule.

### A6.2 Other cross-publisher contradictions on the same dimensions that Batch 2 missed

| New id | Dimension | Side 1 (publisher / quote) | Side 2 (publisher / quote) |
|---|---|---|---|
| **CONFLICT-OB-C** | Which part of the candle **is** the zone (default) | proea.app: "Its body, open to close, is the zone." | tmgm.com: "mark a box from the high to the low of that last bearish candle, wicks included" |
| **CONFLICT-OB-D** | At what level an OB is **invalidated** | fxnx.com: "If a candle body closes past the Mean Threshold, the block is considered invalidated." | tmgm.com "Traders usually treat an order block as invalid once a candle closes beyond its far edge"; liquidityscan "Candle close beyond the OB extreme"; G1 "the violation is a candle close below the low of the zone"; ictkillzone "Only a candle body closing beyond the zone boundary constitutes full mitigation."; proea "From that close on, the zone is invalid." |
| **CONFLICT-CE-A (extended)** | Which zone the 50% is taken from | old sides kept: FVG wick-to-wick (fxnx, ictkillzone, liquidityscan, fundingpips, quartersequence) vs breaker zone (tmgm); **new side added**: G1 / innercircletrader.net "The 50% retracement level (midpoint) of an FVG, order block or any PD array." | quartersequence states the opposite split explicitly: "He keeps it apart from mean threshold, the halfway line of an order block." |
| **CONFLICT-PDA-C (new)** | What premium/discount is measured **against** | 50% of the dealing range — altrady "Split the current range at its 50% level."; ictkillzone "above the 50% level (equilibrium) is premium"; fundingpips "Premium and discount divide a price range into an upper half and a lower half"; G1 "The area above the 50% line on the chart is the premium zone."; velotrade "below 50%"; liquidityscan premium/discount filter; proea "below the 50% line of the leg that broke structure" | quartersequence: "Price above an open: the market can afford to be sold — a short bias, with discount as the target." (anchored to an open, not to the 50% of a range) |
| **CONFLICT-PDA-A (extended)** | Which zones are members of the list | Batch-2 sides kept (FVG/OB/BPR; +mitigation/rejection/propulsion; +old highs/lows) | **New sides:** G1 "The PD Array contains the following eight ICT trigger tools" (FVG, IFVG, OB, breaker, mitigation, unicorn, NWOG, NDOG); G1 "The collective name for FVG, order block, breaker, mitigation, OTE and any other PD-arrangement zones used as entries"; quartersequence "such as a fair value gap, an order block or an opening gap". **Recorded, not resolved:** G1's own three pages give three different lists. |

No contradiction was found on BPR boundaries, BPR invalidation or BPR confirmation: each of those is stated by
G1 alone, so the other publishers are `NOT_STATED`, not opposed.

## A7 — C-PDA-16 and other cases without a verbatim quote

- **C-PDA-16 (tmgm).** Relabelled. The Batch-2 cell was a paraphrase. Re-opened
  `https://www.tmgm.com/en/academy/trading-academy/order-block` (4 of 4 chunks); the verbatim sentence is
  "**The order block lines up with the higher timeframe trend**, so a bullish order block sits in an uptrend and
  a bearish order block sits in a downtrend." Because the sentence is about **trend alignment, not premium or
  discount**, C-PDA-16 is re-classified as `NOT_STATED` on PD arrays **with a verbatim quote for what it does
  say**, and is removed from any SAME support.
- **C-BPR-16 (ictflow).** Verbatim now confirmed on the re-opened page: "Mark the specific daily PD Array (FVG,
  OB, or BPR)". BPR is named, not defined. Stays `NOT_STATED` on formation/boundaries/entry; **not**
  `PARAPHRASE_NO_QUOTE`.
- **C-CE-11 (G1 / BPR midpoint).** Verbatim confirmed this run: "a bullish CHoCH or an aggressive displacement
  candle closing above the BPR midpoint". It names a midpoint but never calls it CE → stays `NOT_STATED` on
  whether the BPR midpoint is a CE. Not `PARAPHRASE_NO_QUOTE`.
- **C-BRK-32, C-BRK-33, C-BPR-17, C-BPR-18, C-OTE-11, C-OTE-12, C-CE-12, C-CE-13, C-PDA-18, C-PDA-19** are
  no-text / `NOT_STATED` / `NOT_OPENED` rows by design; they carry no quote and support nothing.
- **C-OTE-13 (new, proea)** is the only case in this file labelled **`PARAPHRASE_NO_QUOTE`** (see A3).

## A8 — Page-count honesty: "pages opened" vs "pages with content"

- **tmgm.com Judas swing page** (`https://www.tmgm.com/en/academy/trading-academy/judas-swing`): re-opened,
  1 of 3 chunks. It mentions a fair value gap and an order block only in passing
  ("Traders may then monitor a bearish Fair Value Gap or order block for a potential short entry") and
  **defines none of the six terms**. Counted as **opened, no content**.
- **ninjatrader.com** (`https://ninjatrader.com/futures/blogs/price-action-trading-strategies/`): re-opened
  2 of 2 chunks. Generic price-action blog index; **no content on any of the six terms**.
- **tradingstrategyguides.com** (`https://tradingstrategyguides.com/`): re-opened 2 of 2 chunks. Homepage index
  of generic strategy guides; **no ICT entry-zone article, no content on the six terms**.
- Batch 2's two dead links (`tmgm.com/.../fair-value-gap` 404, `tradingstrategyguides.com/order-blocks/`
  redirect) were **not re-opened** in this run and are carried over as recorded, not used.

Both counts are given separately in Section B.

## A9 — Re-check of every remaining SAME group in Batch 2 (sections D1–D6)

| Group | Batch-2 mark | Verdict this run | Action |
|---|---|---|---|
| V-OB-1 which candle | SAME, 7 units | **CONFIRMED**, and extended to 8 units (proea added) | kept SAME |
| V-OB-2 direction wording | SAME, 5 units | **CONFIRMED**, extended to 6 units (ictkillzone added) | kept SAME |
| V-OB-3 several candles | SAME, units "velotrade, liquidityscan, tmgm, **G1**" | **NOT_CONFIRMED for G1** — no G1 case was cited for it. Correct unit list: velotrade, liquidityscan, tmgm, **ictkillzone** ("the last opposing candle (or small cluster of candles) before a significant displacement move"). | kept SAME, unit list corrected |
| V-OB-4 full-range boundaries | SAME, tmgm + velotrade | **CONFIRMED** (2 units) | kept SAME |
| V-OB-5 body-only refinement | SAME, velotrade + liquidityscan | **CONFIRMED**, extended to 4 units (+ proea "Its body, open to close, is the zone."; + ictkillzone "Entry zone: full candle body") | kept SAME, 4 units |
| V-OB-6 MT on body | SAME, ictkillzone + fxnx | **CONFIRMED**, extended to 3 units (+ quartersequence "The mean threshold is the halfway line of an order block, which his Core Content lesson measures on the candle body, open to close") | kept SAME |
| V-OB-7 MT on full range | SAME, liquidityscan + velotrade | **CONFIRMED** | kept SAME |
| V-OB-8 entry at MT | SAME, 5 units via C-OB-18…22, 24, 25 | **NOT_CONFIRMED at 5.** C-OB-22 is the open-price/mean-threshold either-or case (moved to V-OB-9 only); C-OB-24 is a **stop** sentence, not an entry sentence; C-OB-25 ("Place the entry where the fair value gap or order block overlaps the OTE zone") is an **OTE-overlap** rule, not a mean-threshold rule. Correct units: ictkillzone, velotrade, liquidityscan. | **downgraded 5 → 3 units**, still SAME; C-OB-22/24/25 moved |
| V-OB-9 OB open-price entry | SINGLE, liquidityscan | **CONFIRMED** | kept SINGLE |
| V-OB-10 invalidation on close beyond far edge | SAME, tmgm + liquidityscan + G1 | **CONFIRMED**, extended to 5 units (+ ictkillzone, + proea) | kept SAME |
| V-OB-11 invalidation "close through MT is the failure warning" | SAME, fxnx + velotrade | **NOT_CONFIRMED.** fxnx: "If a candle body closes past the Mean Threshold, the block is considered invalidated." = invalidation. velotrade: "a candle that closes through the mean threshold is a warning that it may be failing" = warning only. Invalidated ≠ warning. | **split**: V-OB-11 = SINGLE fxnx (member of CONFLICT-OB-D); V-OB-12 = SINGLE velotrade (not a conflict) |
| V-OB-12 BOS required | SAME, velotrade + tmgm + liquidityscan | **CONFIRMED**, extended to 4 units (+ proea "No break, no order block.") | kept SAME |
| V-OB-13 FVG required | SAME, velotrade + tmgm | **CONFIRMED**, extended to 4 units (+ liquidityscan, + ictkillzone) | kept SAME |
| V-OB-14 sweep required | SAME, velotrade + tmgm | **CONFIRMED**, extended to 4 units (+ ictkillzone "No sweep, no valid OB.", + liquidityscan) | kept SAME |
| V-OB-15 unmitigated | SAME, velotrade + tmgm + liquidityscan | **CONFIRMED**, extended to 5 units (+ ictkillzone, + proea) | kept SAME |
| V-OB-16 discount/premium location | SAME, ictkillzone + velotrade + liquidityscan | **CONFIRMED**, extended to 4 units (+ proea) | kept SAME |
| V-OB-17 1.5× displacement | SINGLE, liquidityscan | **Upgraded to SAME**: ictkillzone "the displacement candle should be at least 1.5x the average size of the candles in the preceding consolidation". **Caveat recorded:** the denominators differ (recent average range vs average candle size in the preceding consolidation). | **SINGLE → SAME**, renumbered V-OB-18 |
| V-OB-18 smaller size instead of tighter stop | SINGLE, ictkillzone | **CONFIRMED** | kept SINGLE, renumbered V-OB-21 |
| V-BRK-1 definition | SAME, 5 units | **CONFIRMED**, extended to 6 units (+ proea) | kept SAME |
| V-BRK-2 sweep required | SAME, 4 units | **CONFIRMED**, extended to 5 units (+ liquidityscan "must first run liquidity before failing") | kept SAME |
| V-BRK-3 mitigation block | SAME, 3 units | **CONFIRMED**, extended to 5 units (+ liquidityscan, + proea) | kept SAME |
| V-BRK-4 close-based violation | SAME, 3 units | **CONFIRMED**, extended to 4 units (+ proea "Only closes do.") | kept SAME |
| V-BRK-6 boundaries | SAME, G1 + tmgm | **CONFIRMED** | kept SAME |
| V-BRK-7 entry on retest + LTF confirmation | SAME, G1 + tmgm | **CONFIRMED** (2 units). proea's "first retest" sentence is a retest-count statement, not an LTF-confirmation statement, so proea joins V-BRK-11 instead. | kept SAME |
| V-BRK-8 stop beyond zone / swept swing | SAME, G1 + tmgm | **CONFIRMED**, extended to 3 units (+ proea) | kept SAME |
| V-BRK-9 Unicorn model | SAME, tmgm + liquidityscan + ictkillzone | **CONFIRMED** (3 units) | kept SAME |
| V-BRK-10 breaker is a PD array | SAME, G1 + fxnx + altrady | **CONFIRMED** (G1 counted once although both G1 pages state it) | kept SAME |
| V-BPR-1 formation | SAME, G1 + ictkillzone + fxnx | **CONFIRMED** (3 units; G1's own verbatim definition re-read on the BPR page) | kept SAME |
| V-OTE-1 62–79% | SAME, altrady + ictkillzone + fxnx + fundingpips | **CONFIRMED** (4 units) | kept SAME |
| V-OTE-3 overlap with FVG/OB | SAME, altrady + fundingpips | **CONFIRMED**, extended to 3 units (+ ictkillzone "When the FVG sits inside the OTE zone the two agree") | kept SAME |
| V-PDA-1 definition | SAME, fxnx + G1 + altrady | **CONFIRMED**, extended to 4 units (+ quartersequence) | kept SAME |
| V-PDA-2 premium/discount at 50% | SAME, 6 units | **CONFIRMED**, extended to 7 units (+ proea) — but see new **CONFLICT-PDA-C** (quartersequence dissents) | kept SAME, conflict added |
| V-PDA-3 selection rule | SAME, ictkillzone + liquidityscan | **CONFIRMED**, extended to 3 units (+ G1 "the right tool in the right zone is the entry") | kept SAME |
| V-PDA-4 membership FVG/OB/BPR | SAME, ictkillzone + ictflow | **CONFIRMED** (2 units) | kept SAME |

**Downgrades issued (complete list):**
1. `V-OB-8` — SAME 5 units → SAME 3 units (C-OB-22, C-OB-24, C-OB-25 removed).
2. `V-OB-11` — SAME 2 units → **split into two SINGLEs** (V-OB-11 fxnx, V-OB-12 velotrade).
3. `V-OB-3` — SAME → SAME with corrected unit list (G1 replaced by ictkillzone).
4. `V-BRK-12` — SINGLE → **moved and upgraded** (V-BRK-11, SAME) with a corrected citation.
5. `CONFLICT-BRK-A` — CONFLICT → **ALT-CONVENTION-BRK-A** (0 conflicts).
6. `CONFLICT-BRK-B` — CONFLICT → **ALT-CONVENTION-BRK-B** (0 conflicts).
7. `CONFLICT-OTE-A` — CONFLICT → **removed**; V-OTE-6 SINGLE + V-OTE-7 `NOT_STATED`.
8. `C-PDA-16` — removed from PD-array support; re-cited with a verbatim quote and marked `NOT_STATED`.
9. `V-BPR-9` — SINGLE with two unsupported cases removed and two supported cases added (no mark change).
10. `V-PDA-8` — SINGLE re-cited (C-PDA-08 → the "None of these outranks the others by rule" sentence).

---

# B — PAGES OPENED (this run)

`chunks read N of N` counts page-fetch chunks. "Content" = the page states something on at least one of the six
terms in the chunks read.

| id | Publisher (domain exactly) | URL | Chunks read | Content on the 6 terms? | Terms covered |
|---|---|---|---|---|---|
| R01 | ictkillzone.com | https://www.ictkillzone.com/ict-2022-model | 4 of 4 | YES | OB, MT, BPR, OTE, CE, PD array |
| R02 | ictkillzone.com | https://www.ictkillzone.com/ict-order-block | 1 of 3 (PARTIAL — chunks 2–3 not read) | YES | OB, MT, prerequisites, stop, location |
| R03 | ictkillzone.com | https://www.ictkillzone.com/ict-pd-array | **not opened** | — | coverage debt |
| R04 | altrady.com | https://www.altrady.com/blog/crypto-trading-strategies/ict-trading-strategy | **3 of 3** (Batch-2 chunk 3 completed) | YES | OB, OTE, PD array, premium/discount, breaker (list only) |
| R05 | liquidityscan.io | https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade | 2 of 3 (PARTIAL — chunk 3 = related-reading footer, not read) | YES | OB, MT, CE, breaker, premium/discount, stop, invalidation |
| R06 | liquidityscan.io | https://liquidityscan.io/blog/what-is-an-order-block | 1 of 2 (PARTIAL — chunk 2 not read) | YES | OB, breaker, mitigation, PD-array context |
| R07 | velotrade.com | https://velotrade.com/blog/order-block | **3 of 3** | YES | OB, MT, boundaries, breaker, mitigation, stop, premium/discount |
| R08 | fxnx.com | https://fxnx.com/en/blog/ict-smc-glossary-80-trading-terms-defined | 4 of 4 | YES | OB, MT, CE, BPR, OTE, PD array, breaker, mitigation |
| R09 | fxnx.com | https://fxnx.com/en/blog/breaker-block-vs-mitigation-block-vs-propulsion-block | 1 of 4 (PARTIAL — chunks 2–4 not read) | YES | breaker, mitigation, MT vs CE |
| R10 | innercircletraders.net (G1) | https://innercircletraders.net/ict-breaker-block/ | 3 of 3 | YES | breaker, OB, PD array |
| R11 | theinnercircletraders.com (G1) | https://www.theinnercircletraders.com/ict-balanced-price-range/ | 1 of 3 (PARTIAL — chunks 2–3 not read) | YES | BPR, PD array, MT-vs-CE context |
| R12 | tmgm.com | https://www.tmgm.com/en/academy/trading-academy/order-block | 4 of 4 | YES | OB, boundaries, prerequisites, invalidation, stop |
| R13 | tmgm.com | https://www.tmgm.com/en/academy/trading-academy/breaker-block | **4 of 4** (Batch-2 chunks 3–4 completed) | YES | breaker, mitigation, CE, boundaries, entry, stop |
| R14 | tmgm.com | https://www.tmgm.com/en/academy/trading-academy/judas-swing | 1 of 3 (PARTIAL) | **NO** — FVG and OB named only in passing, none of the six defined | — |
| R15 | fundingpips.com | https://fundingpips.com/blog/ict-2022-model | **3 of 3** (Batch-2 chunks 2–3 completed) | YES | CE, OTE, premium/discount |
| R16 | ictflow.com | https://ictflow.com/blog/ict-complete-2022-trading-strategy | 1 of 1 | YES | PD array (daily), CE (named only), BPR (named only) |
| R17 | ninjatrader.com | https://ninjatrader.com/futures/blogs/price-action-trading-strategies/ | **2 of 2** (Batch-2 last chunk completed) | **NO** — `NOTHING_ON_TERMS` | — |
| R18 | tradingstrategyguides.com | https://tradingstrategyguides.com/ | **2 of 2** (Batch-2 last chunk completed) | **NO** — homepage index, no ICT entry-zone article | — |
| R19 | quartersequence.com | https://quartersequence.com/the-study/glossary/ | 3 of 5 (PARTIAL — chunks 4–5 not read; letters after "Q" missing) | YES | CE, PD array, FVG, premium, discount, BISI/SIBI |
| R20 | quartersequence.com | https://quartersequence.com/the-study/what-is-ict/ | 1 of 3 (PARTIAL — chunks 2–3 not read) | YES | OB (overview), PD array context |
| R21 | quartersequence.com | https://quartersequence.com/the-study/ict-fair-value-gap/ | 2 of 4 (PARTIAL — chunks 3–4 not read) | YES | CE, MT-vs-CE distinction |
| R22 | proea.app | https://proea.app/en/blog/breaker-block | 2 of 3 (PARTIAL — chunk 3 not read) | YES | breaker, boundaries, violation, entry, stop |
| R23 | proea.app | https://proea.app/en/blog/how-to-identify-order-blocks | 2 of 2 | YES | OB, boundaries, invalidation, premium/discount |
| R24 | proea.app | https://proea.app/en/blog/mitigation-block | 1 of 3 (PARTIAL — chunks 2–3 not read) | YES | mitigation block, breaker-vs-mitigation |
| R25 | proea.app | https://proea.app/en/blog/candle-range-theory | 1 of 3 (PARTIAL) | **NO in the chunk read** — the OTE sentence appears later in the page and was not reached | — |
| R26 | innercircletrader.net (G1) | https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/ | 1 of 4 (PARTIAL) | YES | PD array (8 tools), premium/discount, membership |
| R27 | innercircletrader.net (G1) | https://innercircletrader.net/tutorials/ict-abbreviations/ | 1 of 4 (PARTIAL) | YES | OB, MT, CE, BPR, PD array |
| R28 | innercircletrader.net (G1) | https://innercircletrader.net/tutorials/ict-hangman-pd-array/ | 1 of 3 (PARTIAL) | YES | CE, PD array, BPR (list) |

**Totals: 27 pages opened; 23 pages with content on the six terms; 4 opened without content (R14, R17, R18,
R25).**

## B.1 Pages opened vs pages with content, per publisher

| Publisher | Pages opened | Pages with content | Ids | Target met? |
|---|---|---|---|---|
| ictkillzone.com | 2 | 2 | R01, R02 | **NO — 2 of 3** |
| altrady.com | 1 | 1 | R04 | **NO — 1 of 3** |
| liquidityscan.io | 2 | 2 | R05, R06 | **NO — 2 of 3** |
| velotrade.com | 1 | 1 | R07 | **NO — 1 of 3** |
| fxnx.com | 2 | 2 | R08, R09 | **NO — 2 of 3** |
| G1 (innercircletraders.net + theinnercircletraders.com + innercircletrader.net) | 5 | 5 | R10, R11, R26, R27, R28 | YES — 5 of 3 (one publisher, three domains) |
| tmgm.com | 3 | **2** (R14 has no content) | R12, R13, R14 | **NO — 2 of 3 with content** |
| fundingpips.com | 1 | 1 | R15 | **NO — 1 of 3** |
| ictflow.com | 1 | 1 | R16 | **NO — 1 of 3** |
| ninjatrader.com | 1 | **0** | R17 | **NO — 0 of 3** |
| tradingstrategyguides.com | 1 | **0** | R18 | **NO — 0 of 3** |
| quartersequence.com | 3 | 3 | R19, R20, R21 | **YES — 3 of 3** |
| proea.app | 4 | **3** (R25 has no content in the chunk read) | R22, R23, R24, R25 | **YES — 3 of 3** |
| **Total** | **27** | **23** | | **3 of 15 publishers reach 3 content pages** |

Known-but-unopened second/third pages, recorded as debt (index/listing pages excluded):
`ictkillzone.com/ict-pd-array`, `/ict-balanced-price-range`, `/ict-ote`, `/ict-consequent-encroachment`,
`/ict-breaker-block`; `liquidityscan.io/blog/consequent-encroachment-the-50-fvg-rule`,
`/blog/3-high-probability-order-block-entry-models`, `/blog/the-ict-unicorn-model-breaker-fvg-confluence`,
`/blog/breaker-block-explained-the-ict-reversal-entry`; `velotrade.com/blog/fair-value-gap`,
`/blog/smart-money-concepts`; `fxnx.com/en/blog/when-optimal-trade-entry-fails-ote-invalidation-rules`;
`innercircletrader.net/tutorials/ict-order-block/`, `/tutorials/ict-consequent-encroachment/`,
`/tutorials/ict-breaker-block-trading/`, `/tutorials/ict-balanced-price-range-bpr/`.

---

# C — NEW CASES FOUND IN THIS RUN

Same format as `q_stage2_batch2_entry_zones.md`: one publisher statement per case; `SOURCE_NUMBER` marks a
quantity quoted with the page's own sentence.

## C1 — ORDER BLOCK

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-OB-46 | ictkillzone.com | R02 | "No sweep, no valid OB." | Validity criterion 1 | — | Which counts as "a sweep" |
| C-OB-47 | ictkillzone.com | R02 | "the displacement candle should be at least 1.5x the average size of the candles in the preceding consolidation" | Criterion 2, measurable guideline | "1.5x" → `SOURCE_NUMBER` | The averaging window |
| C-OB-48 | ictkillzone.com | R02 | "Only a candle body closing beyond the zone boundary constitutes full mitigation." | Criterion 3 | — | — |
| C-OB-49 | ictkillzone.com | R02 | "A bullish order block is worth trading only when price is in the discount zone" | Criterion 4, HTF alignment | "50%" equilibrium → `SOURCE_NUMBER` | Which range the HTF equilibrium is measured on |
| C-OB-50 | ictkillzone.com | R02 | "Stops go beyond the full candle wick in both cases." | Diagram caption, bullish and bearish | — | Buffer size |
| C-OB-51 | ictkillzone.com | R02 | "An ICT Order Block (OB) is the last opposing candle before a significant displacement move." | Definition | — | Cluster handling in this sentence |
| C-OB-52 | proea.app | R23 | "An order block is the last candle that closed against a move right before that move broke structure." | Definition, both directions | — | Cluster handling |
| C-OB-53 | proea.app | R23 | "Its body, open to close, is the zone." | Marking, this page's default | — | — |
| C-OB-54 | proea.app | R23 | "Pick one and keep it. The body, open to close, gives a tighter zone." | Body vs wick choice | — | — |
| C-OB-55 | proea.app | R23 | "From that close on, the zone is invalid." | After a close beyond the far edge | — | Buffer |
| C-OB-56 | proea.app | R23 | "No break, no order block." | Headline rule | — | — |
| C-OB-57 | proea.app | R23 | "a bullish order block below the 50% line of the leg that broke structure is in discount." | Premium/discount filter | "50%" → `SOURCE_NUMBER` | Whether other anchors are allowed |
| C-OB-58 | liquidityscan.io | R06 | "A bullish order block is the final down-close candle before an aggressive up-move." | Direction wording | — | Cluster handling |
| C-OB-59 | liquidityscan.io | R06 | "Without an FVG, it is not a high-probability order block." | FVG as a mandatory filter | — | Whether it is mandatory or only "high-probability" |
| C-OB-60 | liquidityscan.io | R05 | "For order blocks there is far less debate: the stop belongs beyond the candle's extreme, with a small buffer" | Stop placement | — | Buffer size |
| C-OB-61 | G1 / innercircletrader.net | R27 | "**OB** — ICT Order Block. The last opposing candle before the displacement that produced a structural break." | Glossary definition | — | Boundaries |
| C-OB-62 | G1 / innercircletrader.net | R27 | "**MT** — Mean Threshold. The 50% retracement level of an ICT Order Block." | Glossary definition of the mean threshold | "50%" → `SOURCE_NUMBER` | **Body or full range — `NOT_STATED`** |

## C2 — BREAKER BLOCK

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-BRK-34 | tmgm.com | R13 | "and many traders only trade the first retest." | Validity paragraph, breaker blocks | — | Why the first retest |
| C-BRK-35 | tmgm.com | R13 | "Trading only the first retest is a common habit and not a fixed rule" | Immediately after the validity table | — | — |
| C-BRK-36 | proea.app | R22 | "A breaker block is an order block that failed." | Definition | — | — |
| C-BRK-37 | proea.app | R22 | "A wick through the zone doesn't make one. Only closes do." | Violation trigger | — | — |
| C-BRK-38 | proea.app | R22 | "A close through the zone alone is a failed order block. Until structure breaks the same way, it isn't a breaker." | Second required condition | — | Which structure break counts |
| C-BRK-39 | proea.app | R22 | "Put the stop beyond the breaker's new far edge, and write down the close that cancels the idea." | Stop + invalidation | — | Buffer |
| C-BRK-40 | proea.app | R22 | "The first retest is the first candle back into the breaker from its new side. That's where breaker traders look for an entry." | Entry timing | — | — |
| C-BRK-41 | proea.app | R24 | "A wick below the low that closes back is a liquidity sweep, not a new low, so the block stays a mitigation block." | Wick vs close in the breaker/mitigation split | — | — |
| C-BRK-42 | liquidityscan.io | R06 | "A breaker block is a \\*failed\\* order block." | Definition | — | Boundaries on this page |
| C-BRK-43 | liquidityscan.io | R06 | "The key difference is that a breaker block must first run liquidity before failing." | Sweep requirement, vs mitigation block | — | — |
| C-BRK-44 | fxnx.com | R09 | "A **Breaker Block** begins its life as the last opposing candle (or series of candles) before a decisive liquidity sweep." | Formation | — | Boundaries on this page |
| C-BRK-45 | fxnx.com | R09 | "**it never sweeps the prior structural extreme**" | Mitigation block, the contrast | — | — |
| C-BRK-46 | proea.app | R24 | "the up candle at a lower high, once a drop from it fails to make a new low and price closes back above the high" | Mitigation block definition | — | — |
| C-BRK-47 | proea.app | R24 | "A breaker fails like any zone: on a close. One that's been closed back through is finished." | Breaker invalidation | — | — |

## C3 — BALANCED PRICE RANGE

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-BPR-19 | G1 / theinnercircletraders.com | R11 | "The Inner Circle Trader methodology uses the BPR as a premium entry zone — ranked above a standalone FVG in the PD array hierarchy" | Ranking claim | — | The full hierarchy |
| C-BPR-20 | G1 / theinnercircletraders.com | R11 | "A BPR is a higher-probability reaction zone than a standalone FVG because the bidirectional institutional interest creates stronger support" | Why it outranks | — | Sample size / evidence |
| C-BPR-21 | G1 / innercircletrader.net | R27 | "**BPR** — Balanced Price Range. The overlap area between two opposite-direction fair value gaps in the same zone." | Glossary definition | — | Boundaries, entry, stop, invalidation |

## C4 — OTE

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-OTE-13 | proea.app | R25 | **PARAPHRASE_NO_QUOTE** — "62% to 79% back into the leg that broke structure" (seen in search-result text; **not present in the 1 of 3 chunks read**) | CRT pullback entry | "62% to 79%" → `SOURCE_NUMBER` | Cannot be used for SAME or CONFLICT |

## C5 — CONSEQUENT ENCROACHMENT

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-CE-14 | quartersequence.com | R19, R21 | "Consequent encroachment (CE) is ICT's name for the halfway line of a fair value gap, midway between its top and its bottom." | Definition, both directions | — | Entry level, stop |
| C-CE-15 | quartersequence.com | R19, R21 | "He keeps it apart from mean threshold, the halfway line of an order block." | CE vs MT, explicit distinction | — | — |
| C-CE-16 | quartersequence.com | R21 | "CE belongs to a gap, drawn wick to wick." | Measurement basis | — | — |
| C-CE-17 | quartersequence.com | R21 | "The mean threshold is the halfway line of an order block, which his Core Content lesson measures on the candle body, open to close" | MT basis, from the CE section | — | — |
| C-CE-18 | quartersequence.com | R21 | "ICT uses CE to judge how deep price has come into a gap. He splits the gap into quadrants and grades price by them" | CE used as a grading level | — | The grading rule itself |
| C-CE-19 | G1 / innercircletrader.net | R27 | "The 50% retracement level (midpoint) of an FVG, order block or any PD array." | Glossary definition of CE | "50%" → `SOURCE_NUMBER` | Measurement basis |
| C-CE-20 | G1 / innercircletrader.net | R28 | "The Consequent Encroachment is simply the 50% midpoint of an ICT PD Array such as a Fair Value Gap." | CE stated at PD-array level | "50%" → `SOURCE_NUMBER` | Whether it is the same line for every array type |

## C6 — PD ARRAY

| Case | Publisher | Page | Verbatim quote | Condition | Numbers | NOT_STATED |
|---|---|---|---|---|---|---|
| C-PDA-20 | G1 / innercircletrader.net | R26 | "The PD Array contains the following eight ICT trigger tools" | Membership list (FVG, IFVG, OB, breaker, mitigation, unicorn, NWOG, NDOG) | "eight" → `SOURCE_NUMBER` | Whether the list is exhaustive |
| C-PDA-21 | G1 / innercircletrader.net | R26 | "Plot the fibonacci from an established old high to an established old low." | Premium/discount computation, anchors | — | Which high/low when several qualify |
| C-PDA-22 | G1 / innercircletrader.net | R26 | "The area above the 50% line on the chart is the **premium zone**." | Premium/discount split | "50%" → `SOURCE_NUMBER` | — |
| C-PDA-23 | G1 / innercircletrader.net | R26 | "the right tool in the right zone is the entry" | Selection rule | — | Which tool wins when several sit in the zone |
| C-PDA-24 | G1 / innercircletrader.net | R27 | "The collective name for FVG, order block, breaker, mitigation, OTE and any other PD-arrangement zones used as entries." | Glossary definition of PD Array | — | Whether the list is exhaustive |
| C-PDA-25 | quartersequence.com | R19 | "Short for premium and discount array: a price zone traders expect a reaction from, such as a fair value gap, an order block or an opening gap." | Definition | — | Whether the list is exhaustive |
| C-PDA-26 | quartersequence.com | R19 | "Price above an open: the market can afford to be sold — a short bias, with discount as the target." | Premium, anchored to an **open** | — | Which open |
| C-PDA-27 | quartersequence.com | R19 | "Price below an open: the market can afford to be bought — a long bias, with premium as the target." | Discount, anchored to an **open** | — | Which open |
| C-PDA-28 | G1 / innercircletrader.net | R28 | "The Hangman is not another independent PD Array. It works alongside existing arrays" | Membership note, with the list FVG, breaker, BPR, OB, rejection block, volume imbalance, NDOG | — | Whether the list is exhaustive |
| C-PDA-29 | proea.app | R23 | "a bullish order block below the 50% line of the leg that broke structure is in discount." | Premium/discount computation, anchored to the leg that broke structure | "50%" → `SOURCE_NUMBER` | Whether other anchors are allowed |

**New `NOT_STATED` rows established this run:** quartersequence.com — `NOT_STATED` on order-block boundaries,
mean-threshold basis for entry, OTE anchor, BPR boundaries; proea.app — `NOT_STATED` on mean threshold, OTE,
CE, BPR; innercircletrader.net — `NOT_STATED` on order-block boundaries and on whether MT is taken on the body
or the full range; liquidityscan.io — `NOT_STATED` on OTE, CE on the second page.

---

# D — IMAGES

## D1 — Methods actually available in this session, and their results

**Method 1 — page-fetch tool on the image URL.** `fetch_page` on
`https://tmgm-cdn2.com/images/2026-10-22/jBCkbPLmyZ.webp` returned **`Failed to fetch page (HTTP 500)`**. No
pixels, no caption, nothing.

**Method 2 — image-search tool + file read.** The image-search tool does reach publisher CDNs: one query
returned `https://tmgm-cdn2.com/images/2026-10-22/2PI6zFMQ4f.webp` (the tmgm order-block page's
"order block boxed from candle high to low inside a wider demand zone" figure) and saved it into the workspace.
I then read that file with the file-read tool. The session answered:
**"[An image was provided here, but you do not have vision capabilities.]"**
So the bytes were reachable but **no image content was perceived**.

**Consequence: no image in this file was viewed. 0 of 36.** Every entry is `IMAGE_NOT_VIEWED`.

**This is not the owner's browser.** Nothing was downloaded, saved, copied or embedded in the repository: the
single file the image-search tool wrote was deleted immediately after the read attempt
(`rm -rf image-search`), and `git ls-files` shows no image file in the tree (see the final report). Image URLs
appear below as **links only**.

Because I cannot see any figure, the "page's own caption" column quotes **the page's text**, not a description
by me. Where the page gives no caption, the cell says so.

## D2 — Image inventory (36 entries: 14 carried from Batch 2 + 22 new)

| id | Page | Image URL (link only) | Status | Page's own caption / alt text (not my description) |
|---|---|---|---|---|
| IMG-01 | R12 tmgm OB | https://tmgm-cdn2.com/images/2026-10-22/jBCkbPLmyZ.webp | IMAGE_NOT_VIEWED | "Candlestick chart of a bullish order block, with the last bearish candle boxed from high to low before an impulsive move up" |
| IMG-02 | R12 tmgm OB | https://tmgm-cdn2.com/images/2026-10-22/GivnrSVW2p.webp | IMAGE_NOT_VIEWED | "Side by side charts of a bullish order block as a demand zone below price and a bearish order block … above price" |
| IMG-03 | R12 tmgm OB | https://tmgm-cdn2.com/images/2026-10-22/CstnTyTWfH.webp | IMAGE_NOT_VIEWED | "Chart showing four steps to identify an order block, from finding the BOS to marking the candle high to low and waiting for the retest" |
| IMG-04 | R12 tmgm OB | https://tmgm-cdn2.com/images/2026-10-22/L4jEqBEzER.webp | IMAGE_NOT_VIEWED | "Chart of a valid order block after a liquidity sweep, followed by a BOS, with a three candle inset showing the fair value gap" |
| IMG-05 | R12 tmgm OB | https://tmgm-cdn2.com/images/2026-10-22/RGbTdTg5Di.webp | IMAGE_NOT_VIEWED | "Illustrative order block trade with a BOS, a retest and rejection candle, entry at its close, stop loss below the zone and swing high target" |
| IMG-06 | R12 tmgm OB (**new**) | https://tmgm-cdn2.com/images/2026-10-22/2PI6zFMQ4f.webp | IMAGE_NOT_VIEWED | "Chart of an order block boxed from candle high to low inside a wider demand zone built from several base candles" |
| IMG-07 | R12 tmgm OB (**new**) | https://tmgm-cdn2.com/images/2026-10-22/Qfmeaj3CUj.webp | IMAGE_NOT_VIEWED | "Five step order block trading flow from checking the trend and marking a valid order block to the retest, confirmation and entry" |
| IMG-08 | R13 tmgm breaker | https://tmgm-cdn2.com/images/2026-10-26/Ihw4l7eIcw.webp | IMAGE_NOT_VIEWED | "Bearish breaker block in four stages, from the order block and liquidity sweep above a swing high to the candle close through and the retest" |
| IMG-09 | R13 tmgm breaker | https://tmgm-cdn2.com/images/2026-10-26/3VRmNuMZed.webp | IMAGE_NOT_VIEWED | "Bullish and bearish breaker blocks side by side, showing the swing sequence, liquidity sweep and failed order block flipping to support or resistance" |
| IMG-10 | R13 tmgm breaker | https://tmgm-cdn2.com/images/2026-10-26/cEPAetpDKR.webp | IMAGE_NOT_VIEWED | "Breaker block trade plan chart with entry on the retest, a stop loss beyond the zone or beyond the swept swing, and a target at the next high" |
| IMG-11 | R13 tmgm breaker | https://tmgm-cdn2.com/images/2026-10-26/PS3A46JDfU.webp | IMAGE_NOT_VIEWED | "Unicorn model chart where a bullish breaker block overlaps a three candle fair value gap, with the liquidity sweep and retest marked" |
| IMG-12 | R13 tmgm breaker (**new**) | https://tmgm-cdn2.com/images/2026-10-26/oRtwlOzk7a.webp | IMAGE_NOT_VIEWED | "Bullish breaker block example where price sweeps the earlier low, closes above the zone with a CHoCH, then retests it, with entry, stop loss and target" |
| IMG-13 | R13 tmgm breaker (**new**) | https://tmgm-cdn2.com/images/2026-10-26/TF1Rg9Up8k.webp | IMAGE_NOT_VIEWED | "Breaker block vs mitigation block charts, where the breaker block sweeps the low first and the mitigation block makes a higher low instead" |
| IMG-14 | R10 G1 breaker | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.15.08-AM.png (**new**) | IMAGE_NOT_VIEWED | "Mark All Active Order Blocks" |
| IMG-15 | R10 G1 breaker | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.16.06-AM.png | IMAGE_NOT_VIEWED | "Watch for a Violation" |
| IMG-16 | R10 G1 breaker | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.17.02-AM.png | IMAGE_NOT_VIEWED | "Wait for the Return" |
| IMG-17 | R10 G1 breaker (**new**) | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.18.03-AM.png | IMAGE_NOT_VIEWED | "Bearish Breaker Block Trade Setup" |
| IMG-18 | R10 G1 breaker (**new**) | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.18.59-AM.png | IMAGE_NOT_VIEWED | "Bullish Breaker Block Trade Setup" |
| IMG-19 | R11 G1 BPR | (no image URL returned; figures named "Figure 1", "Figure 2", "Figure 3") | IMAGE_NOT_VIEWED | "Figure 1 — BPR anatomy: … The price ranges of FVG1 and FVG2 overlap — this overlap is the Balanced Price Range, marked with the denser cross-hatch. BPR High and BPR Low (dashed lines) define the precise overlap boundaries." |
| IMG-20 | R08 fxnx (**new**) | https://cdn.sanity.io/images/1tyytg47/production/1b72f0bdc72ef9717f739517e5de8cd3fdf20400-1200x896.png | IMAGE_NOT_VIEWED | "Comparison of a 3-candle Fair Value Gap (BISI) formation and market structure rules for a body close BOS versus a wick liquidity sweep." |
| IMG-21 | R08 fxnx (**new**) | https://cdn.sanity.io/images/1tyytg47/production/48c42717281d8154e723c879f53d7409fe473054-1200x896.png | IMAGE_NOT_VIEWED | "Timeline infographic mapping key ICT daily trading sessions, killzones, and macro intervals." |
| IMG-22 | R08 fxnx (**new**) | https://cdn.sanity.io/images/1tyytg47/production/bc45826f892fe12257acffc0c547873a2cf4ec05-1200x896.png | IMAGE_NOT_VIEWED | "A five-stage trade execution process shows higher timeframe DOL analysis through lower timeframe structure shift, FVG, OTE, and targets." |
| IMG-23 | R09 fxnx (**new**) | https://cdn.sanity.io/images/1tyytg47/production/f4c2e23841bcea217306d43498aa83eead1a17ff-1376x768.png | IMAGE_NOT_VIEWED | "Breaker Block vs Mitigation Block vs Propulsion Block" (hero, no candle-level caption) |
| IMG-24 | R26 G1 PD array (**new**) | https://www.innercircletrader.net/wp-content/uploads/2024/01/ICT-PD-array-1.png | IMAGE_NOT_VIEWED | "ICT PD Array Matrix diagram showing premium and discount zones with the eight institutional trigger tools" |
| IMG-25 | R26 G1 PD array (**new**) | https://innercircletrader.net/wp-content/uploads/2024/01/ICT-PD-arrays.png | IMAGE_NOT_VIEWED | "ICT PD Arrays diagram showing the premium zone above 50% and the discount zone below 50% with the institutional tools arranged in each" |
| IMG-26 | R26 G1 PD array (**new**) | https://www.innercircletrader.net/wp-content/uploads/2024/01/ICT-PD-array.png | IMAGE_NOT_VIEWED | "ICT PD Array fibonacci setup chart showing premium zone above 50% and discount zone below 50% on the dealing range" |
| IMG-27 | R27 G1 abbreviations (**new**) | https://innercircletrader.net/wp-content/uploads/2024/06/ICT-Abbreviations-List.png | IMAGE_NOT_VIEWED | "ICT Abbreviations List — alphabetical glossary of ICT and SMC concepts including AMD, BISI, BOS, CHOCH, CISD, CRT, FVG, IOFED, IPDA, MSS, NWOG, OTE and more" |
| IMG-28 | R28 G1 hangman (**new**) | https://innercircletrader.net/wp-content/uploads/2026/07/ict-hangman-pd-array-2.png | IMAGE_NOT_VIEWED | "ICT Hangman PD Array diagram showing a wick trading beyond the Consequent Encroachment while the candle body closes back inside the PD Array" |
| IMG-29 | R28 G1 hangman (**new**) | https://innercircletrader.net/wp-content/uploads/2026/07/ICT-Hangman-Pattern.png | IMAGE_NOT_VIEWED | "ICT Hangman pattern example, a wick spikes past the Consequent Encroachment of a PD Array before the candle body closes back inside and price continues in the original direction" |
| IMG-30 | R06 liquidityscan (**new**) | https://liquidityscan.io/blog/images/what-is-an-order-block-hero.png | IMAGE_NOT_VIEWED | Hero image, title only, no caption text |
| IMG-31 | R05 liquidityscan | https://liquidityscan.io/blog/images/fvg-vs-order-block-which-entry-zone-should-you-trade-hero.png?v=1786196820 | IMAGE_NOT_VIEWED | Hero image, title only, no caption text |
| IMG-32 | R04 altrady (**new**) | https://cdn-web.altrady.com/ict_body_2_workflow_v2_dc13137c89.png | IMAGE_NOT_VIEWED | "The ICT sequence: structure, liquidity, imbalance, then entry in the OTE zone." |
| IMG-33 | R04 altrady (**new**) | https://cdn-web.altrady.com/ict_body_3_zones_v2_7940b8cc8e.png | IMAGE_NOT_VIEWED | "Premium and discount around the range midpoint, and a fair value gap that price later revisits." |
| IMG-34 | R04 altrady (**new**) | https://cdn-web.altrady.com/ict_fvg_ote_diagram_bae3b076b0.webp | IMAGE_NOT_VIEWED | "A fair value gap and the OTE zone, the two entry tools ICT models use most." |
| IMG-35 | R15 fundingpips (**new**) | https://images.ctfassets.net/4jb7onvr59r3/3d4fvg1Kawut9oVhYpgkTK/007a8bddf21dca3575aa290595bd9517/The-ICT-2022-Model-Explained.jpg | IMAGE_NOT_VIEWED | Hero image, title only, no caption text |
| IMG-36 | R07 velotrade | https://velotrade.com/_next/image?url=%2Fimages%2Fblog%2Forder-block%2Fhero.webp&w=3840&q=75 | IMAGE_NOT_VIEWED | Page labels this only as "Order Block Trading: Bullish, Bearish and Breaker Blocks" (hero, no candle-level caption) |

**Counts: 36 image entries recorded · 0 viewed · 36 `IMAGE_NOT_VIEWED`.** proea.app's figures are replay
animations with no static image URL in the page text; quartersequence.com's figures are inline illustrations with
no direct URL; the ictkillzone order-block anatomy diagram returned no URL in the chunk read. None of them could
have been viewed in any case.

## D3 — OWNER_CHECK (10 items, chosen by how informative each is for zone boundaries)

Each question is answerable **YES / NO / CANNOT_SEE** by the owner looking at the image in a normal browser.

| # | Page URL | Image URL | Question (YES / NO / CANNOT_SEE) |
|---|---|---|---|
| 1 | https://www.tmgm.com/en/academy/trading-academy/order-block | https://tmgm-cdn2.com/images/2026-10-22/jBCkbPLmyZ.webp | Is the box drawn from the candle's wick high to its wick low (rather than from body open to body close)? |
| 2 | https://www.tmgm.com/en/academy/trading-academy/order-block | https://tmgm-cdn2.com/images/2026-10-22/2PI6zFMQ4f.webp | Does the order-block box end exactly at the single candle's high and low, with the wider demand-zone box drawn around several candles? |
| 3 | https://www.tmgm.com/en/academy/trading-academy/order-block | https://tmgm-cdn2.com/images/2026-10-22/L4jEqBEzER.webp | Is the order-block box drawn on the last opposing candle only, with the FVG inset showing a separate zone inside the impulse? |
| 4 | https://www.tmgm.com/en/academy/trading-academy/breaker-block | https://tmgm-cdn2.com/images/2026-10-26/Ihw4l7eIcw.webp | Is the breaker block box the same high-to-low range as the failed order block, or is it redrawn tighter? |
| 5 | https://www.tmgm.com/en/academy/trading-academy/breaker-block | https://tmgm-cdn2.com/images/2026-10-26/TF1Rg9Up8k.webp | Does the mitigation-block panel draw its zone on the same candle as the breaker panel, with only the prior low differing? |
| 6 | https://www.tmgm.com/en/academy/trading-academy/breaker-block | https://tmgm-cdn2.com/images/2026-10-26/PS3A46JDfU.webp | Does the fair-value-gap box visibly overlap the breaker block box, i.e. share price area? |
| 7 | https://innercircletraders.net/ict-breaker-block/ | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-16-at-2.18.03-AM.png | Are the stop-loss and entry levels printed as price labels on the chart, and is the stop above the zone's high? |
| 8 | https://www.theinnercircletraders.com/ict-balanced-price-range/ | (Figure 1 of that page — IMG-19) | Are the two dashed lines (BPR High / BPR Low) drawn exactly at the intersection of the two FVG boxes, not at either FVG's outer edge? |
| 9 | https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/ | https://www.innercircletrader.net/wp-content/uploads/2024/01/ICT-PD-array.png | Is the 50% line drawn as the midpoint of a Fibonacci retracement taken from an old high down to an old low? |
| 10 | https://innercircletrader.net/tutorials/ict-hangman-pd-array/ | https://innercircletrader.net/wp-content/uploads/2026/07/ICT-Hangman-Pattern.png | Does the wick cross the 50% (CE) line while the candle body closes back on the original side of it? |

---

# E — CORRECTED MERGE TABLE

Rules: `SAME` = two or more **independence units** state the same substance, each with a verbatim quote;
one unit = `SINGLE` with its own named variant; `CONFLICT` = different explicit answers to the **same** dimension
from **different** publishers. Old variant names are given where they changed.

## E1 — ORDER BLOCK (incl. mean threshold) — 21 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-OB-1 | Which candle | The block is the last opposing candle before the displacement | C-OB-01…08, 51, 52, 61 | ictkillzone, liquidityscan, velotrade, tmgm, fxnx, altrady, G1, proea | **SAME** |
| V-OB-2 | Direction wording | Bullish = last down-close candle; bearish = last up-close (mirror) | C-OB-03, 05, 06, 07, 11, 58 | ictkillzone, liquidityscan, tmgm, fxnx, altrady, G1 | **SAME** |
| V-OB-3 | Several candles | Take the last opposing candle, or group the cluster | C-OB-09, 10, 11, C-OB-51 parenthetical | velotrade, liquidityscan, tmgm, ictkillzone (unit list corrected: G1 removed) | **SAME** |
| V-OB-4 | Boundaries (default) | Zone drawn high-to-low, wicks included | C-OB-13, 14 | tmgm, velotrade | **SAME** |
| V-OB-5 | Boundaries (refined) | Body-only marking (open to close) | C-OB-15, 16, 17, 53, 54 | velotrade, liquidityscan, proea, ictkillzone | **SAME** |
| V-OB-6 | Mean-threshold basis | MT = 50% of the **body** (open to close) | C-OB-18, 19, C-CE-17 | ictkillzone, fxnx, quartersequence | **SAME** |
| V-OB-7 | Mean-threshold basis | MT = 50% of the **full range** (high to low) | C-OB-20, 21 | liquidityscan, velotrade | **SAME** |
| V-OB-8 (re-scoped: was 5 units) | Entry level | The mean threshold is an OB entry level | C-OB-18, C-OB-21 entry line, C-OB-20 | ictkillzone, velotrade, liquidityscan | **SAME** |
| V-OB-9 | Entry level | Enter at the OB candle's **open price** | C-OB-22 | liquidityscan | SINGLE |
| V-OB-10 | Invalidation | A candle **close** beyond the far edge of the block | C-OB-37, 38, 42, 48, 55 | tmgm, liquidityscan, G1, ictkillzone, proea | **SAME** |
| V-OB-11 (split from old V-OB-11) | Invalidation | A close past the **mean threshold invalidates** the block | C-OB-39 | fxnx | SINGLE |
| V-OB-12 (split from old V-OB-11) | Invalidation | A close through the mean threshold is only a **warning** | C-OB-40 | velotrade | SINGLE |
| V-OB-13 | Prerequisite | A break of structure after the block | C-OB-26, 30, 35, 56 | velotrade, tmgm, liquidityscan, proea | **SAME** |
| V-OB-14 | Prerequisite | A fair value gap left inside the displacement | C-OB-27, 31, 59 | velotrade, tmgm, liquidityscan, ictkillzone | **SAME** |
| V-OB-15 | Prerequisite | A liquidity sweep immediately before the displacement | C-OB-28, 32, 46 | velotrade, tmgm, ictkillzone, liquidityscan | **SAME** |
| V-OB-16 | Prerequisite | The block must be unmitigated / first touch | C-OB-29, 33, 36 | velotrade, tmgm, liquidityscan, ictkillzone, proea | **SAME** |
| V-OB-17 | Location | A bullish block belongs in discount, bearish in premium | C-OB-43, 44, 45, 49, 57 | ictkillzone, velotrade, liquidityscan, proea | **SAME** |
| V-OB-18 (was V-OB-17, SINGLE→SAME) | Displacement filter | Displacement candle ≥ 1.5× a recent average | C-OB-34, 47 | liquidityscan, ictkillzone (denominators differ — recorded) | **SAME** |
| V-OB-19 (**new**) | Stop placement | Stop **beyond the full block** | C-OB-41, 50, 60, tmgm stop sentence | velotrade, ictkillzone, liquidityscan, tmgm | **SAME** |
| V-OB-20 (**new**) | Stop placement | Stop **1 pip beyond the mean threshold** | C-OB-24 | fxnx | SINGLE |
| V-OB-21 (was V-OB-18) | Size | If the OB stop is too wide, cut size instead of tightening | C-OB-23 | ictkillzone | SINGLE |

**CONFLICT-OB-A** — "what the mean threshold is 50% of": V-OB-6 (body: ictkillzone, fxnx, quartersequence) vs
V-OB-7 (full range: liquidityscan, velotrade). G1 is `NOT_STATED` on the basis (C-OB-62) and joins neither.
**CONFLICT-OB-B (new)** — "where the OB stop goes": V-OB-20 (fxnx, 1 pip beyond MT) vs V-OB-19
(velotrade + ictkillzone + liquidityscan + tmgm, beyond the full block).
**CONFLICT-OB-C (new)** — "which part of the candle is the zone by default": V-OB-5 (proea: body) vs V-OB-4
(tmgm: high-to-low, wicks included).
**CONFLICT-OB-D (new)** — "at what level the OB is invalidated": V-OB-11 (fxnx: MT close) vs V-OB-10
(5 units: close beyond the far edge). V-OB-12 (velotrade: warning only) is outside this conflict.

## E2 — BREAKER BLOCK — 14 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-BRK-1 | Definition | A breaker is a failed order block that flips polarity | C-BRK-01…04, 10, 14, 17, 28, 36, 42 | G1, velotrade, fxnx, tmgm, liquidityscan, proea | **SAME** |
| V-BRK-2 | Required condition | A liquidity sweep must precede the failure | C-BRK-13, 14, 17, 18, 43 | velotrade, tmgm, fxnx, G1, liquidityscan | **SAME** |
| V-BRK-3 | Sibling concept | Mitigation block = the same flip **without** a sweep | C-BRK-11, 12, 15, 41, 45, 46 | velotrade, fxnx, tmgm, liquidityscan, proea | **SAME** |
| V-BRK-4 | Violation trigger | A candle **close / body close** through the zone is required | C-BRK-06, 23, 28, 37 | G1, tmgm, liquidityscan, proea | **SAME** |
| V-BRK-5 | Violation trigger | A **wick** through the zone is accepted by some traders | C-BRK-05 | G1 (reported, not adopted) | SINGLE → **ALT-CONVENTION-BRK-B** |
| V-BRK-6 | Boundaries | The zone keeps the original OB's high-to-low range | C-BRK-03, 04, 22 | G1, tmgm | **SAME** |
| V-BRK-7 | Entry | Enter on the retest, with a lower-timeframe confirmation inside the zone | C-BRK-07, 24, 26 | G1, tmgm | **SAME** |
| V-BRK-8 | Stop | Stop beyond the zone, or beyond the swing that swept liquidity | C-BRK-08, 25, 39 | G1, tmgm, proea | **SAME** |
| V-BRK-9 | Confluence model | The Unicorn model = breaker overlapping a fair value gap | C-BRK-27, 29, 30 | tmgm, liquidityscan, ictkillzone | **SAME** |
| V-BRK-10 | Classification | A breaker is itself a PD array | C-BRK-09, 16, 31, C-PDA-20 list | G1, fxnx, altrady | **SAME** |
| V-BRK-11 (was V-BRK-12, SINGLE→SAME, citation corrected) | Retest count | Many traders take only the first retest | **C-BRK-34**, 35, 40 | tmgm, proea | **SAME** |
| V-BRK-12 (was V-BRK-11) | Swing sequence | Bullish breaker = low, high, lower low, higher high (4 labelled swings) | C-BRK-20, 21 | tmgm | SINGLE |
| V-BRK-13 (**new**) | Formation | A close through the zone **plus** a structure break the other way | C-BRK-23 + CHoCH row, 38 | tmgm, proea | **SAME** |
| V-BRK-14 (**new**) | Invalidation | A close back through the breaker ends it | C-BRK-26, 47 | tmgm, proea | **SAME** |

**ALT-CONVENTION-BRK-A** (was CONFLICT-BRK-A) — "any broken order block is a breaker block, sweep optional":
reported by tmgm.com only ("Some SMC traders call any broken order block a breaker block"); adopted by no
publisher read this run.
**ALT-CONVENTION-BRK-B** (was CONFLICT-BRK-B) — "a wick through the zone counts as the violation": reported by
G1 only, and reported at tool level by proea; adopted by no publisher read this run.
**Breaker CONFLICT count: 0.**

## E3 — BALANCED PRICE RANGE — 10 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-BPR-1 | Formation | BPR = the overlap of a bullish FVG and a bearish FVG | C-BPR-01, 11, 14, 21 | G1, ictkillzone, fxnx | **SAME** |
| V-BPR-2 | Boundaries | BPR high/low are the top and bottom of the overlap intersection | C-BPR-02, 03, 04 | G1 | SINGLE |
| V-BPR-3 | Entry level | Enter at the zone boundary (BPR low for longs, BPR high for shorts) | C-BPR-06, 07 | G1 | SINGLE |
| V-BPR-4 | Entry level | Enter at the **midpoint** of the BPR | C-BPR-12 | ictkillzone | SINGLE |
| V-BPR-5 | Confirmation | A CHoCH or displacement candle inside the zone before entry | C-BPR-08 | G1 | SINGLE |
| V-BPR-6 | Invalidation | A close through the whole zone mitigates it | C-BPR-09 | G1 | SINGLE |
| V-BPR-7 | Timing | The second FVG may come later — "not necessarily the immediate next move" | C-BPR-05 | G1 | SINGLE |
| V-BPR-8 | Timing | "immediately followed and intersected" — the two FVGs are consecutive | C-BPR-14 | fxnx | SINGLE |
| V-BPR-9 (cases corrected) | Rank | A BPR outranks a standalone FVG | **C-PDA-13, C-BPR-19, C-BPR-20** (C-BPR-13 and C-BPR-15 removed) | G1 | SINGLE |
| V-BPR-10 (**new**, moved out of V-BPR-9) | Why the zone matters | The overlap band is "a fortress for retests" | C-BPR-15 | fxnx | SINGLE |

**CONFLICT-BPR-A** — "where inside the BPR the entry goes": V-BPR-3 (boundary; G1, which explicitly prefers the
BPR low over the midpoint) vs V-BPR-4 (midpoint; ictkillzone).
**CONFLICT-BPR-B** — "how soon the second FVG must form": V-BPR-7 (later allowed; G1) vs V-BPR-8 (immediate;
fxnx).

## E4 — OTE — 7 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-OTE-1 | Levels | OTE = the 62%–79% retracement zone | C-OTE-01, 04, 07, 09 | altrady, ictkillzone, fxnx, fundingpips | **SAME** |
| V-OTE-2 | Sub-levels | 70.5% is the level many traders watch inside the zone | C-OTE-02 | altrady | SINGLE |
| V-OTE-3 | Confluence | Prefer an FVG or OB that overlaps the OTE zone | C-OTE-03, 10, C-OTE-06 | altrady, fundingpips, ictkillzone | **SAME** |
| V-OTE-4 | Invalidation | Past 79% of the leg, the setup is dead | C-OTE-08 | fxnx | SINGLE |
| V-OTE-5 | Role | OTE can replace the FVG entry, or be used with it | C-OTE-05, 06 | ictkillzone | SINGLE |
| V-OTE-6 (**new**, replaces CONFLICT-OTE-A) | Anchor | The retracement is measured from the raid extreme across the displacement leg | C-OTE-04 | ictkillzone | SINGLE |
| V-OTE-8 (**new**) | Anchor | Anchor = "back into the leg that broke structure" | C-OTE-13 | proea | SINGLE — **PARAPHRASE_NO_QUOTE**, cannot support SAME |

**V-OTE-7 (`NOT_STATED` group, not a variant):** altrady, fxnx and fundingpips name the anchor only as
"a swing" and give no computation. Silence is recorded, never counted as agreement or as a conflict.
**OTE CONFLICT count: 0** (old CONFLICT-OTE-A removed; see A3).

## E5 — CONSEQUENT ENCROACHMENT — 10 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-CE-1 (recounted: 6 → 5 units) | Computation | CE = the 50% midpoint of the gap | C-CE-01, 03, 05, 08, 14 | fxnx, ictkillzone, liquidityscan, fundingpips, quartersequence | **SAME** |
| V-CE-2 | Measurement basis | Measured wick-to-wick (candle 1's wick to candle 3's wick) | C-CE-02, 04, 16 | fxnx, ictkillzone, quartersequence | **SAME** |
| V-CE-3 | Scope | CE also applies to a liquidity void and a long rejection wick | C-CE-01 | fxnx | SINGLE |
| V-CE-4 (recounted: 4 → 3 units) | Use | CE is the limit-entry level | C-CE-03, 05, 08 | ictkillzone, liquidityscan, fundingpips | **SAME** |
| V-CE-5 | Use | Split size between the near edge and CE | C-CE-06, 07 | liquidityscan | SINGLE |
| V-CE-6 | Scope | The 50% of a **breaker zone** is also called consequent encroachment | C-CE-10 | tmgm | SINGLE |
| V-CE-7 (**new**) | Scope | CE = 50% of **any PD array**, including an order block | C-CE-19, 20 | G1 | SINGLE |
| V-CE-8 (**new**) | Distinction | CE belongs to a gap; the mean threshold belongs to an order block | C-CE-15, 17 | quartersequence | SINGLE |
| V-CE-9 (**new**) | Use | CE is used to grade how deep price has come into a gap (quadrants) | C-CE-18 | quartersequence | SINGLE |
| V-CE-10 (**new**) | Failure | A wick through the gap is tolerated; the body close decides | — (page text, R21) | quartersequence | SINGLE |

**CONFLICT-CE-A** — "which zone the 50% is taken from": V-CE-1/V-CE-2 (the fair value gap, wick-to-wick:
fxnx, ictkillzone, liquidityscan, fundingpips, quartersequence) vs V-CE-6 (the breaker block zone: tmgm) vs
V-CE-7 (any PD array including an order block: G1). The G1-vs-quartersequence contradiction is head-on:
G1 "The 50% retracement level (midpoint) of an FVG, order block or any PD array." vs quartersequence
"He keeps it apart from mean threshold, the halfway line of an order block."

## E6 — PD ARRAY — 13 groups

| Variant | Dimension | Statement | Cases | Units | Mark |
|---|---|---|---|---|---|
| V-PDA-1 | Definition | PD array = a categorised list of institutional price zones used as reaction levels | C-PDA-01, 04, 09, 25 | fxnx, G1, altrady, quartersequence | **SAME** |
| V-PDA-2 | Premium/discount | Split the range at 50%; buy discount, sell premium | C-PDA-02, 06, 11, 14, 15, 17, 21, 22, 29 | fxnx, ictkillzone, altrady, velotrade, liquidityscan, fundingpips, G1, proea | **SAME** |
| V-PDA-3 | Selection rule | The zone must sit on the correct side of the range for the trade direction | C-PDA-06, 15, 23 | ictkillzone, liquidityscan, G1 | **SAME** |
| V-PDA-4 | Membership | FVG, OB and BPR are the arrays used for the daily entry | C-PDA-07, 08, 12 | ictkillzone, ictflow | **SAME** |
| V-PDA-5 | Membership | The block spectrum is OB, breaker, mitigation, rejection, propulsion | C-PDA-03 | fxnx | SINGLE |
| V-PDA-6 | Membership | OB, FVG, breaker and *old highs and lows* are the listed arrays | C-PDA-10 | altrady | SINGLE |
| V-PDA-7 (re-cited) | Ranking | A BPR outranks a standalone FVG in the hierarchy | C-PDA-13, C-BPR-19 | G1 | SINGLE |
| V-PDA-8 (re-cited) | Ranking | No array outranks another by rule | ictkillzone "None of these outranks the others by rule" | ictkillzone | SINGLE |
| V-PDA-9 (**new**) | Membership | Eight trigger tools: FVG, IFVG, OB, breaker, mitigation, unicorn, NWOG, NDOG | C-PDA-20 | G1 | SINGLE |
| V-PDA-10 (**new**) | Membership | FVG, OB, breaker, mitigation, **OTE** and any other PD-arrangement zone | C-PDA-24 | G1 | SINGLE |
| V-PDA-11 (**new**) | Membership | FVG, order block, opening gap | C-PDA-25 | quartersequence | SINGLE |
| V-PDA-12 (**new**) | Premium/discount | Premium and discount are anchored to an **open**, not to the 50% of a range | C-PDA-26, 27 | quartersequence | SINGLE |
| V-PDA-13 (**new**) | Membership | FVG, breaker, BPR, OB, rejection block, volume imbalance, NDOG | C-PDA-28 | G1 | SINGLE |

`C-PDA-16` (tmgm) is **removed** from this table: it is a higher-timeframe-trend-alignment statement with a
verbatim quote (see A7) and is `NOT_STATED` on PD arrays.

**CONFLICT-PDA-A** — "which zones are members of the list": V-PDA-4 (FVG/OB/BPR), V-PDA-5 (+mitigation,
rejection, propulsion), V-PDA-6 (+old highs/lows), V-PDA-9 (eight tools), V-PDA-10 (+OTE), V-PDA-11 (+opening
gap), V-PDA-13 (+rejection block, volume imbalance, NDOG). No page claims its list is exhaustive. **Recorded,
not resolved.** Also recorded: G1 alone publishes three different lists on three of its own pages.
**CONFLICT-PDA-B** — "are the arrays ranked": V-PDA-7 (G1: BPR above FVG) and the ranking claim in C-PDA-09
(altrady: "ranks by importance") vs V-PDA-8 (ictkillzone: "None of these outranks the others by rule").
**CONFLICT-PDA-C (new)** — "what premium/discount is measured against": V-PDA-2 (the 50% of the range / of the
leg that broke structure: 8 units) vs V-PDA-12 (an open: quartersequence).

---

# F — COUNTS, AND CHANGES VS BATCH 2

Cases (publisher statements) and groups (variants) are counted separately and never added together.

| Term | Cases | Groups | SAME | SINGLE | CONFLICT |
|---|---|---|---|---|---|
| Order block (incl. mean threshold) | 62 | 21 | 16 | 5 | 4 |
| Breaker block | 47 | 14 | 12 | 2 | **0** (+2 alternative conventions) |
| Balanced price range | 21 | 10 | 1 | 9 | 2 |
| OTE | 13 | 7 | 2 | 5 | **0** (+1 `NOT_STATED` group) |
| Consequent encroachment | 20 | 10 | 3 | 7 | 1 |
| PD array | 29 | 13 | 4 | 9 | 3 |
| **Batch 2b totals** | **192 cases** | **75 groups** | **38 SAME** | **37 SINGLE** | **10 CONFLICT** |

Group lists by mark:

- **Order block — SAME (16):** V-OB-1, 2, 3, 4, 5, 6, 7, 8, 10, 13, 14, 15, 16, 17, 18, 19.
  **SINGLE (5):** V-OB-9, 11, 12, 20, 21. **CONFLICT (4):** OB-A (MT basis), OB-B (stop placement),
  OB-C (zone boundary default), OB-D (invalidation level).
- **Breaker — SAME (12):** V-BRK-1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 13, 14.
  **SINGLE (2):** V-BRK-5 (reported alternative), V-BRK-12. **CONFLICT (0):**
  ALT-CONVENTION-BRK-A, ALT-CONVENTION-BRK-B.
- **BPR — SAME (1):** V-BPR-1. **SINGLE (9):** V-BPR-2, 3, 4, 5, 6, 7, 8, 9, 10.
  **CONFLICT (2):** BPR-A (entry level), BPR-B (timing).
- **OTE — SAME (2):** V-OTE-1, V-OTE-3. **SINGLE (5):** V-OTE-2, 4, 5, 6, 8 (8 = `PARAPHRASE_NO_QUOTE`).
  **CONFLICT (0).** `NOT_STATED` group V-OTE-7 (altrady, fxnx, fundingpips).
- **CE — SAME (3):** V-CE-1, V-CE-2, V-CE-4. **SINGLE (7):** V-CE-3, 5, 6, 7, 8, 9, 10.
  **CONFLICT (1):** CE-A (which zone the 50% is taken from; 3 named sides).
- **PD array — SAME (4):** V-PDA-1, 2, 3, 4. **SINGLE (9):** V-PDA-5, 6, 7, 8, 9, 10, 11, 12, 13.
  **CONFLICT (3):** PDA-A (membership), PDA-B (ranking), PDA-C (premium/discount anchor).

## F1 — CHANGES VS BATCH 2

| Term | Cases old → new | Groups old → new | SAME old → new | SINGLE old → new | CONFLICT old → new |
|---|---|---|---|---|---|
| Order block | 45 → **62** | 18 → **21** | 15 → **16** | 3 → **5** | 1 → **4** |
| Breaker block | 33 → **47** | 12 → **14** | 9 → **12** | 3 → **2** | 2 → **0** |
| Balanced price range | 18 → **21** | 9 → **10** | 1 → **1** | 8 → **9** | 2 → **2** |
| OTE | 12 → **13** | 5 → **7** | 2 → **2** | 3 → **5** | 1 → **0** |
| Consequent encroachment | 13 → **20** | 6 → **10** | 3 → **3** | 3 → **7** | 1 → **1** |
| PD array | 19 → **29** | 8 → **13** | 4 → **4** | 4 → **9** | 2 → **3** |
| **Totals** | **140 → 192** | **58 → 75** | **34 → 38** | **24 → 37** | **9 → 10** |

## F2 — Old variant name → new variant name

| Old | New | Change |
|---|---|---|
| V-OB-8 | V-OB-8 | re-scoped, 5 units → 3 |
| V-OB-11 | **V-OB-11 + V-OB-12** | split (fxnx invalidation / velotrade warning) |
| V-OB-17 | V-OB-18 | SINGLE → SAME |
| V-OB-18 | V-OB-21 | renumbered |
| — | V-OB-19, V-OB-20 | new: stop beyond the full block / stop at the MT |
| V-BRK-11 | V-BRK-12 | renumbered |
| V-BRK-12 | V-BRK-11 | SINGLE → SAME, citation corrected to C-BRK-34 |
| — | V-BRK-13, V-BRK-14 | new: structure-break requirement; breaker invalidation |
| CONFLICT-BRK-A | **ALT-CONVENTION-BRK-A** | conflict → reported alternative convention |
| CONFLICT-BRK-B | **ALT-CONVENTION-BRK-B** | conflict → reported alternative convention |
| V-BPR-9 | V-BPR-9 | cases corrected (C-BPR-13 and C-BPR-15 removed; C-BPR-19, C-BPR-20 added) |
| — | V-BPR-10 | new: fxnx "fortress for retests" moved out of V-BPR-9 |
| CONFLICT-OTE-A | **removed** → V-OTE-6 (SINGLE) + V-OTE-7 (`NOT_STATED`) | silence is not a conflict |
| — | V-OTE-8 | new, `PARAPHRASE_NO_QUOTE` |
| V-PDA-8 | V-PDA-8 | re-cited to the sentence that actually says it |
| C-PDA-16 | — | removed from PD-array support; re-cited with a verbatim quote, marked `NOT_STATED` |
| — | V-CE-7, V-CE-8, V-CE-9, V-CE-10 | new CE groups |
| — | V-PDA-9, V-PDA-10, V-PDA-11, V-PDA-12, V-PDA-13 | new PD-array groups |
| — | CONFLICT-OB-B, CONFLICT-OB-C, CONFLICT-OB-D, CONFLICT-PDA-C | new conflicts |

---

# G — LIMITS

1. **Coverage is still below the 3-content-pages-per-publisher target.** Reached: **27 pages opened, 23 with
   content, across 12 independence units (G1 counted once) + 2 new publishers.** Only **3 of 15** publishers
   reach three content pages: G1 (5 pages), quartersequence.com (3), proea.app (3). Shortfalls with the number
   reached: ictkillzone.com 2, liquidityscan.io 2, fxnx.com 2, tmgm.com **2 with content** (the third page, the
   Judas swing guide, has none), altrady.com 1, velotrade.com 1, fundingpips.com 1, ictflow.com 1,
   **ninjatrader.com 0**, **tradingstrategyguides.com 0**. Known unopened candidate URLs are listed in B.1.
2. **14 of 27 pages are `PARTIAL`.** Missing chunks are named in Section B. A statement that lives only in an
   unread chunk is absent from Section C. Fully read pages: R01, R04, R07, R08, R10, R12, R13, R15, R16, R17,
   R18, R23.
3. **No image was viewed — 0 of 36.** Two methods were available and both failed: the page-fetch tool returns
   HTTP 500 on image URLs, and the image-search + file-read path returns
   "[An image was provided here, but you do not have vision capabilities.]". I therefore cannot state candle
   counts, printed prices, label positions or whether a caption matches its figure. Every image entry is
   `IMAGE_NOT_VIEWED`, and the only image text quoted is the publisher's own caption. This is not the owner's
   browser; the one file the image-search tool wrote was deleted, and `git ls-files` shows no image in the tree.
4. **G1 remains `RELATIONSHIP_UNCLEAR`.** All three G1 domains were opened this run (R10, R11, R26, R27, R28).
   No page shows a shared author, owner or network, so G1 still counts once. Consequence: G1 contributes one
   unit to any SAME group even when three of its pages say the same thing, and G1's own three different
   PD-array membership lists are an internal inconsistency, not a cross-publisher conflict.
5. **One case is `PARAPHRASE_NO_QUOTE`** (C-OTE-13, proea). Its sentence was seen in search-result text but not
   in the chunk read, so it supports nothing.
6. **Two dead links carried over from Batch 2 and not re-tested:** `tmgm.com/.../fair-value-gap` (404) and
   `tradingstrategyguides.com/order-blocks/` (redirects to the homepage). They are recorded, not used.
7. **`innercircletrader.net` carries paid-course and paid-eBook banners.** The article text is free and was
   read; no paywalled page was used.
8. **No number was recomputed.** Every `SOURCE_NUMBER` is the page's own text. Where two publishers both give
   "1.5×" (C-OB-34 and C-OB-47) the denominators differ and this is recorded rather than harmonised.
9. **Nothing was decided.** 38 SAME groups, 37 SINGLE groups and 10 CONFLICT blocks are inventory. No zone
   definition, mean-threshold basis, stop rule, CE rule or PD-array order is proposed for the engine here.
10. **Batch 2 was not edited.** All corrections live in this file. The five `CATALOG_MISMATCH` items in
    Batch 2's Section F were not re-audited here except where they overlap with the six terms; that audit is
    still open.
