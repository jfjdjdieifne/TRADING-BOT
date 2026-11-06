# AUDIT — distillation round

## What this run actually did
- HARVEST_HASH `90629a8f97ec323d9c5430b61f0ca9b2d265f45b`; everything was read through `git show HARVEST_HASH:<path>`.
- Phase 0: 326/326 INDEX rows re-hashed, 0 mismatches, 0 missing. 31 excerpt repos re-downloaded at pinned commits
  (codeload), 1612/1635 excerpt quotes pass (23 fail on PDF text-layer / markdown heading joins — none used).
  Random sample of 100, seed 20261106, 99 pass.
- Phase 1: 490 transcripts inventoried (all timestamped; 157 with caption artefacts). 74 repos flagged:
  4 LLM_STATED, 1 HUMAN_STATED, 69 NO_SIGNAL.
- Phase 2: 1392 files scored over 11 topics; top files per topic in `selection.md`.
- Phase 3: **100 claims** in `claims.jsonl`. CHECK 1 (quote verbatim after lowercase + whitespace collapse, ≤25 words):
  **100/100 pass**. CHECK 2 (statement content words present in the ±100-word surroundings):
  29 warnings, all of them framing words I wrote rather than speaker words (`library`, `described`, `table`, `asks`,
  `topic`, `whether`). No warning touches a factual term; the full list is in `phase3_verify_report.md`.
- Phase 4: 8 conflicts, 18 options, none merged or resolved; `agreement.md` with 9 agreement clusters and explicit
  NOT_INDEPENDENT marks where claims share one LLM_STATED library.
- Phase 5: 13 concept cards, `process_spec.md` (questions/branches only), `OWNER_QUESTIONS.md` (12 numbered gaps).
- Phase 6: `knowledge_pack.jsonl` 111 rows (13 concept, 33 property, 53 condition, 1 decision, 11 gap);
  `knowledge_pack.michael_only.jsonl` 39 rows (all claim ids from MICHAEL_WORDS sources);
  `knowledge_pack.no_llm_flagged.jsonl` 64 rows (no LLM_STATED repo).

## What was read vs not read
Read: 32 logged windows via `read_window.py` on newsqlguru/ict-index transcripts (Month-01 Liquidity Runs,
Month-04 Reinforcing Liquidity Concepts, Month-08 When To Avoid The London Session, 2022 Mentorship Ep-03 and Ep-05,
"If I Could Go Back Part 4"), Klout9 Month 04/05 markdown, and ad-hoc `head`/`grep` reads of ~12 SrsBlack library
concept files (definition sections plus the audit notes above them), plus 6 harvest web records.
**Not read** in this session: 458 of the 490 transcripts; the Charter model bodies beyond their opening pages; the
library's bias-invalidation, silver-bullet and breaker files; the PDF-only sources; Yousef-Diab, Rouen007 and
Kyle2077 repos beyond their authorship flags.
That is why the corpus is 100 claims and not thousands: no claim was written for a file I did not open.

## Counts per phase
| phase | artefact | count |
|---|---|---|
| 0 | INDEX records verified | 326/326 |
| 1 | transcripts / repos flagged | 490 / 74 |
| 2 | files scored | 1392 |
| 3 | claims / verifier pass | 100 / 100 (100%) |
| 4 | conflicts / options | 8 / 18 |
| 5 | cards / process branches / owner questions | 13 / 9 / 12 |
| 6 | pack rows (all / michael / no-llm) | 111 / 39 / 64 |

## TEMPTATION log — considered and NOT added
1. **Stop buffer.** I "knew" ICT uses a small fixed buffer beyond the extreme. Wrote it as gap Q1 instead.
2. **Silver Bullet window 10:00–11:00.** Memory says NY 10:00–11:00. The source read only says "a one-hour window
   around 10:00 am New York time" (CLM-0089). The end time was not written.
3. **OTE is the 62–79% retracement.** Two web records give the numbers (CLM-0088, CLM-0092) — recorded as *their*
   statement, not operationalised: no source read says which leg or how to anchor it.
4. **IPDA data ranges (20/40/60 days).** Not present in any window read. Not added.
5. **CHoCH = swing failure / character change mechanism.** Memory has a definition; the corpus here only has a library
   statement that the term does not exist (CLM-0041) and an explainer listing it (CLM-0099). Definition not written.
6. **"Wait for the second leg" / "turtle soup entry" rules.** Tempting to fill the after-sweep branch; the read windows
   only give "anticipate, don't force". Nothing added.
7. **Judas swing at session open.** Appears only inside a list in one web record; no behavioural rule read, so it is
   neither a card nor a claim.
8. **Risk 1% per trade.** The corpus says 1% *monthly* return is exceptional (CLM-0054). Turning that into a 1%-per-trade
   rule would be invented; filed as gap Q8.

## Known weaknesses
- **Coverage is thin and skewed.** 100 claims over 13 concepts; `target_selection`, `entry_zones` and `no_trade` are
  reasonably covered; `dealing_range` worked examples, killzone chart examples and stop numeric examples are absent.
- **Source mix is uneven.** Many concepts rest on the LLM_STATED SrsBlack library (24 pack rows are NOT_INDEPENDENT).
  The transcripts are few but are the only verbatim speaker text; the `michael_only` pack exists for that reason.
- **Second-hand quoting.** The library quotes 2016/2022 lectures at minute marks that were not re-verified against the
  audio or a transcript in this session (only against the library file itself).
- **CHECK 2 is a weak test.** It only flags content words missing from the surroundings; a paraphrase that stays inside
  the vocabulary passes even if it overstates. Manual reading of each card was still required.
- **No chart was ever seen.** Every geometric concept (FVG, OB, MSS) is defined in text; no candle image was verified,
  so "candle_visible" in the pack means "expressible from OHLC", not "verified on a chart".
- **Conflicts are unresolved by design.** The engine cannot act on CF-01/02/04/06 until the owner picks an option.
- **Not read ≠ not existing.** Thin areas may be thick in the 458 unread transcripts; the gaps reflect this run, not ICT.
