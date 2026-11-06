# AUDIT — source_corpus_v3 self-audit

## 1. Counts per tier (Phase 1)

| tier | files | distinct source_ids |
|---|---:|---:|
| PRIMARY | 14 | 7 |
| SECONDARY | 0 | 0 |
| TERTIARY | 0 | 0 |

Completeness: FULL 8, PARTIAL 6, EXCERPT 0. Total bytes 112150. Items with timestamps: 0.
Exact-content duplicates: none. **No new source was retrieved this round** — every PRIMARY byte was
already in the repository and was copied byte-identically (SHA-256 asserted equal before indexing).

## 2. Claims (Phase 2)

| metric | value |
|---|---:|
| total claims | 54 |
| verified by `tools/verify_claims.py` | 54 |
| failed | 0 |
| removed | 0 |

By type: SAID 41, DEMONSTRATED 11, AMBIGUOUS 1, CONTRADICTED-IN-SOURCES 1.
By source: `YT_8GkQfdAXZP0_MIRROR` 47, `YT_nQfHZ2DEJ8c` 2, `YT_PIYh0CxoY9c` 3, `YT_Bkt8B3kLATQ` 1,
`YT_FgacYSN9QEo` 1.

Verification is mechanical only: lowercase + whitespace collapse, quote must occur in the stored
file, `context_before` must equal the 5 preceding normalized words, quote ≤ 25 words. It does **not**
check that a statement is a fair paraphrase — that remains a human/owner review item.
Reports: `reports/claims_verification.txt` (re-run in Phase 6).

Note on how zero failures were reached: quotes were located in the normalized file text **before**
being written, and `context_before` was computed from the file rather than typed. Any quote that could
not be located was rejected at build time. This is disclosed so the 0-failure figure is not read as
independent evidence of correctness.

## 3. Cards (Phase 3)

| metric | value |
|---|---:|
| cards | 32 |
| grounded cards (≥1 claim) | 24 |
| NOT_FOUND_IN_SOURCES cards | 8 |
| relations in `relations.jsonl` | 15 |
| fields written NOT_IN_SOURCES or GAP | 206 |
| cross-concept citations (recorded, not hidden) | 16 |

Cards with the most empty fields (all 9 empty): `dealing_range`, `premium`, `equilibrium`,
`equal_lows`, `invalidation`, `sit_on_hands`, `kill_zone`, `objective`.
Grounded cards that are thinnest: `context`, `draw_on_liquidity`, `retail_ideas`, `time_of_day`,
`discount`, `intermediate_term_low`, `institutional_order_flow`, `displacement`.
Per-card counts: `reports/card_field_counts.json`.

## 4. Contradictions and ambiguities in the sources

1. **Order block, single candle vs series** — OB16 [C047, C048] vs Episode 12 [C017, C016]. Recorded as
   [C050] type CONTRADICTED-IN-SOURCES. **Not resolved**; raised as OQ-04. The engine design carries a
   `definition_id` instead of choosing.
2. **Bias test negation** — [C038] reads "if you **can't** go into your charts and line up an idea
   that's bullish" while the following sentences describe the opposite test. Type AMBIGUOUS, flagged
   possible ASR error, **not corrected**. OQ-09.
3. **Fair value gap usage differs** — FVG16 gives a definition [C049]; Episode 12 uses gaps as objects
   to hunt inside an order block [C018]. Listed as different usages in `process_spec.md`, not merged.
4. **"discount" usage differs** — Episode 12 "discount level of the low end of that fair value Gap"
   [C054] vs FVG24 "discount opening range Gap" (no claim extracted). Recorded as a gap, not merged.
5. **Time of day** — asserted vital in Ep6 [C044]; the Episode 12 worked example contains no
   time-of-day condition. The process spec therefore has **no time gate**. Not smoothed.

## 5. Places where memory would have supplied something, and a gap was recorded instead

This is the contamination log. In each case the tempting addition was **not** written.

| temptation | what was done instead |
|---|---|
| Name the familiar three-candle "fair value gap" formula | Phase 3 contains no candle formula; the detection idea is quarantined in `engine_representation.md` as ENGINEERING_HYPOTHESIS needing approval |
| Add "dealing range", "premium", "discount/equilibrium" as a premium/discount framework | `dealing_range`, `premium`, `equilibrium` cards are NOT_FOUND_IN_SOURCES; `premium` occurrences were shown to be boilerplate description text, not speech |
| Add "equal lows" as the mirror of equal highs | mechanical search: 0 hits; card NOT_FOUND_IN_SOURCES |
| Add kill zones / session windows / midnight open / 8:30 / 9:30 | 0 hits for each; `kill_zone` card NOT_FOUND; `time_gate = NULL` in the design; OQ-17 |
| Add "market structure shift" as a named formal sequence with displacement + gap | only the retrieved wording is used [C022, C026]; no sequence completed |
| Add "invalidation" as a rule with a tolerance | term absent; card NOT_FOUND; nearest wording "wrong" used instead; OQ-08, OQ-18 |
| Add "sit on hands" as his phrase | exact phrase absent; only "sitting on my hands" [C014] is quoted |
| Supply a typical stop distance, risk %, or R multiple | none written; OWNER_DECISION_NEEDED |
| Rank the fib projection against the range target | both listed, unranked [C019, C023, C024]; OQ-11 |
| Treat -1 1/2 as a general rule | quoted only as what he reads in that example [C024]; OQ-12 asks whether it generalises |
| Complete the chart-review order into a tidy checklist | Steps 1-8 carry explicit NOT_IN_SOURCES lines and an "explicitly absent" section |
| Use the repo's own study files as evidence | flagged AGENT-PRODUCED in `LEADS.md`; never cited by any claim |
| Use search snippets about his bio/method as evidence | kept in `LEADS.md` as LEAD_ONLY; no claim cites them |

## 6. What was not retrieved / not executed

- No new PRIMARY page, transcript or video was retrieved: `fetch_page` returned
  `SignatureDoesNotMatch` for every call; terminal egress fails with `curl (35) SSL_ERROR_SYSCALL`
  for all non-GitHub/PyPI/npm hosts. Exact errors in `REACHABILITY.md`.
- `theinnercircletrader.com` (his own page) — lead only, never opened.
- Ep6/Ep3/OB16/FVG16/FVG24 beyond chunk 0; Episode 12 mirror chunk 8.
- Per-segment timestamps for any video: no endpoint returned VTT/SRV3/JSON3.
- New video discovery from official playlists: no page retrieved, so **no ID was guessed**.
- GitHub repositories with transcripts/notes: **not searched**; no repo/commit/author/license recorded.
- SECONDARY/TERTIARY collection and license assessment: nothing opened, so nothing stored.
- No ASR was run. No audio, no frames. No May 2025 data. No profitability interpretation.
- 20 owner questions are open (`OWNER_QUESTIONS.md`); none was answered by the agent.

## 7. Honest overall assessment

The result is **thin**: one substantially complete lecture plus five opening fragments, 54 verified
claims, and 206 empty card fields. That thinness is the intended success condition. The largest
single risk is that 47 of 54 claims come from one third-party mirror whose provenance is unverified
(OQ-03), and the largest methodological gap is the unresolved order-block contradiction (OQ-04).
