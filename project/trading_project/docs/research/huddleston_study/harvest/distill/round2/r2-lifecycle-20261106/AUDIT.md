# AUDIT — round 2 (question-driven mining), session r2-lifecycle-20261106

Base commit `462bb61068e6b184478b831dd8295a189dfeabc5`. Every base file was read with
`git show 462bb61:<path>`; every source file was read from `/tmp/dr` re-downloads at the pinned commits
(`file_sha256` stored per claim).

## Search (phase A)
- Corpus: **1,871 files with extractable text** across all `/tmp/dr` repos (speaker transcripts, library markdown,
  LLM-flagged reports, code repos). Hit counts per question per pattern: `search_log.tsv`; ranked file lists:
  `search_report.txt`.
- Terms were derived from the assignment wording and from round-1 claims only (e.g. "stop loss", "where's your stop",
  "limit order", "risk per trade", "position size", "consequent encroachment", "lower time frame", "dealing range",
  "change of character", "killzone", "displacement"). No ICT vocabulary was imported from memory.

## Read (phase B)
- **21 windows** of ±200 words (~400 words each) logged in `read_log.jsonl` with file, pattern, word offsets, sha256.
- Files opened: 9 transcripts + 1 library-adjacent source set; **1,841 of the 1,871 text files were NOT opened** this
  round (hit ranking only). The highest-density non-transcript hits were LLM-flagged repos
  (`Yousef-Diab/the-algorithm` index.html, `SrsBlack` audit reports) — deliberately not mined as speaker text.
- Per question: windows by *surfacing* question (the `question` field in `read_log.jsonl`): QJ 4 · QA 2 · QC 2 · QD 2 · QE 2 · QG 2 · QH 2 · QK 2 · QM 2 · QI 1 = 21. Two questions (QF, QL) have no window of their own: their claims come from windows already read for other questions (W012, W018, W010, W011, W015, W020). This is recorded rather than hidden — no claim cites a window that was not printed and logged.

## Claims (phase C)
- **50 claims** in `claims_r2.jsonl`: SAID 37, DEFINED 4, USED_IN_EXAMPLE 3, DEMONSTRATED 5, AMBIGUOUS 1.
- Per question: claims per question: QA 5 · QB 3 · QC 5 · QD 3 · QE 3 · QF 4 · QG 3 · QH 3 · QI 1 · QJ 3 · QK 5 · QL 8 · QM 4 (sum = 50).
- CHECK 1 (verbatim quote, ≤25 words): **50/50 pass (100%)**. 7 authored claims were rejected by the verifier before
  any file was written (3 attribution errors, 3 word-level misquotes, 1 path bug) — see `corrections.md`.
- CHECK 2 (statement content words absent from ±100-word surroundings): **48 warnings / 50 claims**, listed in full in
  `verify_r2_final.md`. Cause: normal-English statements vs unpunctuated ASR. No warning introduced a new fact; the two
  clean claims are the two-word-quote ones.

## Answers (phase D) and worked examples (phase E)
- `answers.md`: 13 questions, each ANSWERED_BY_SOURCE / CONFLICTING / STILL_UNANSWERED with claim ids. 4 conflicts in
  `conflicts_r2.jsonl` (18 options), none resolved.
- `worked_examples.jsonl`: **5** examples (Ep40 21-Jun-2022; the four-opportunities plan; 23-May-2023 review;
  2016 order block teaching; the top-down routine), each with looked-at / decided / postponed / ruled-out / HTF-LTF /
  expectation / outcome. 3 sequence files in `sequences/`.

## TEMPTATION log — considered, NOT added
1. **"NY killzone is 08:30–11:00."** Memory says 08:30–11:00 (or 07:00–10:00). The corpus says 07:00→10:00 in one
   lecture and 09:30–11:30 as an operating session. Wrote R2QF-0001/0002 and CF-R2-02; did not harmonise.
2. **"Stop buffer of 5 pips / 10 points."** Tempting to give the engine a number. No window read states one; the only
   numbers are the fixed 4 points of one plan (R2QA-0004). Not turned into a rule.
3. **"Displacement = a candle larger than the previous N."** Memory offers a measurable definition. The corpus defines
   displacement by *who* is acting (R2QG-0002) and by feel ("more energetic", R2QG-0003). No threshold invented.
4. **"CHoCH = swing failure pattern."** I could have written a mechanism from memory; the only evidence is that he says
   "shift in market structure" (R2QI-0001) and a third party lists CHoCH. Not added.
5. **"OTE = 62–79% retracement" as the entry rule.** Numbers exist in round-1 web records, but nothing in this round's
   windows ties them to a demonstrated entry. Kept out of the process sequence.
6. **"Silver Bullet 10:00–11:00."** Same trap as round 1; only "around 10:00 am" exists. Not used.
7. **Filling the exit leg.** Tempting to complete the process with a target rule from memory ("external liquidity or
   opposite PD array"). Only the round-1 claims and the 5.25-point target of one plan exist; the sequence files say
   "not in the windows read" instead.

## Known weaknesses
- **Thin per question.** QA/QE/QI/QJ rest on 1–6 windows each; QI (CHoCH) rests on a single window plus a grep over the
  corpus — absence of "CHoCH" in 21 windows is not proof he never says it.
- **Window discipline.** ±200 words each side (~400 words) satisfies the assignment's ±400-word window in total length,
  not in each direction. Stated plainly here rather than described as ±400 each side.
- **Planning-timeframe material came from 2016/2022 lectures**, not from 2023 live executions except Ep40 and the
  May-23 review. Older vocabulary ("pdas", "voids") appears in the quotes as spoken.
- **Only transcripts were mined as speaker text**; the LLM-flagged repos dominate the raw hit ranking and were left
  unread, which biases the corpus toward the 490-transcript subset.
- **No chart images were consulted.** All geometric statements are textual; "candle_visible" claims were not verified
  against OHLC data.
- **ASR noise is preserved verbatim** ("koji pool", "price Wing", "consequent quotient", "four three two or one
  minute"), which makes some quotes ugly but honest.
