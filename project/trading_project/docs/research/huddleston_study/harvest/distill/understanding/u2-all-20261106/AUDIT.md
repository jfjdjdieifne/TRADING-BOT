# AUDIT — understanding round v2, session `u2-all-20261106`

Assignment: **all four groups A+B+C+D** (owner answered "كلشي"). No engine code, no market data.

## 1. What was actually obtained

`newsqlguru/ict-index` at pinned commit `e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c`, pin read from
`harvest/github/repos_meta.jsonl` at base commit `36f2217d`. Downloaded via codeload: HTTP 200,
10,548,984 bytes, tarball SHA-256
`4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d`.
**490 transcripts, 2,549,198 words.** Every transcript carries `offsetMS`/`durationMS` and a `RefLink`
YouTube URL. Nothing was fetched from YouTube; no audio, no frames, no ASR.

## 2. Counts per task

| task | result |
|---|---|
| 0 discovery | 13,813 grams kept; 2,764 definition windows; 116 directed probes, **0 zero-hit**; 66 concepts selected; 13,761 terms excluded-or-deferred with reasons |
| 1 cards | **21 cards**, each with **15 windows** (315 concept windows); **0 THIN**; **136 claims**; 76 sections `NOT_IN_SOURCES` |
| 2 comparisons | **18** things_compared/which_wins records; 19 comparative claims of which **1** left unreduced; 3,000 raw comparative windows mined; degree-word table |
| 3 pairing | **71** dated candidates (35 DESIGN / 36 VALIDATION); 15 unique dated transcripts read; **13** pairing cards; **18** narrated events; **6** EURUSD-usable days |
| 4 gaps | `gaps.md`: deixis table, 4 parallel conflicts, image-only list, per-concept unknowns, session coverage gaps |

Totals: **359 windows logged**, **166 distinct transcript files** touched, 44 of them story-pairing
windows. 6 claims carry `[sic-asr]` flags.

## 3. Verifier

`tools/verify_claims.py` is the base-commit tool, byte-identical except one line making the corpus
root configurable. **No check was weakened.** A symlink `/tmp/dr/newsqlguru__ict-index` was created to
satisfy its expected layout rather than editing its path logic.

- CHECK 1 (hard gate, quote verbatim after lowercase + whitespace collapse only, ≤25 words):
  **136 / 136 = 100.0%**, 0 failures.
- CHECK 2 (soft): **117 warnings**. These are statement words absent from the ±100-word surroundings —
  i.e. my paraphrase used vocabulary the source window does not contain. They are reported, not
  silently rewritten. This is a real fidelity signal and the largest weakness of the claim set.
- Additionally, `tools/corpus_engine.py add` refuses any quote not located verbatim or whose hit falls
  outside a logged window. **0 claims were rejected at build time**, because quotes were selected
  from excerpts already printed from those windows.

Report: `reports/verify.md`.

## 4. Reading discipline — what "read" means here

`windows.jsonl` logs every ±250-word window (file, word range, sha256, concept). `read_log.jsonl`
separates `window_extracted` from `excerpt_read`: **the agent saw the marker-bearing excerpts inside
each window (each ≤25 words), not all 501 words.** No claim is made of having read full windows.
Every excerpt's word range was checked to reproduce the exact text and to lie inside its window
(0 mismatches).

One attribution defect was found and fixed mid-session: 9 of 136 claims had been attributed to the
first window containing the quote rather than a window pulled for that concept. They were
re-attributed to a same-concept window and the verifier re-run.

## 5. THIN concepts

**None.** All 21 carded concepts met the 15-window budget. The honest caveat is the opposite one:
**45 of the 66 selected concepts got no card at all** and are deferred, not absent. They include
`breaker`, `mitigation_block`, `rejection_block`, `consequent_encroachment`, `optimal_trade_entry`,
`imbalance`, `inefficiency`, `liquidity_void`, `turtle_soup`, `silver_bullet`, `judas_swing`,
`smt_divergence`, `market_maker`, `mean_threshold`, `ipda`, `data_range`, the swing-hierarchy terms
and `money_management`.

## 6. Conflicts kept parallel

1. **Order block start**: opening of the first candle (`U0045`) vs the last up candle (`U0046`).
2. **London kill zone**: 1am (`U0088`) vs 2am (`U0089`, `U0090`); plus an explicit refusal to call the
   New York session a kill zone (`U0094`) and a wider 8:30 variant (`U0092`).
3. **Break-even**: after first profit never before (`U0114`) vs at 75% of objective (`U0115`) vs resist
   moving at all on higher time frames (`U0112`, `U0113`).
4. **"premium"**: range position (`U0082`) vs carrying-charge market (`U0087`) — different observables.

None was resolved, averaged, or silently preferred.

## 7. Contamination log — memory temptations recorded as gaps instead

| temptation | what was done instead |
|---|---|
| Write the remembered three-candle FVG formula as *his* criterion | kept out of the quoted sections; it appears only in §(c) as ENGINEERING_HYPOTHESIS pointing at `U0036`/`U0038` |
| Declare `old high`, `swing high`, `time of day`, `ipda`, `no trade` absent because the n-gram inventory lacked them | caught the stop-word edge-filter artefact and ran a directed probe: **all present** (`old high` 629/207 files, `ipda` 3/3) |
| Supply the remembered 2am–5am London kill zone as settled | found he also says 1am; both quoted as parallel alternatives |
| Give a fixed tick tolerance for "equal" highs | expressed as near-equality relative to local swing amplitude; tolerance left open |
| Turn "energetic displacement" into a range multiple | kept as a relative-to-neighbours comparison, flagged as needing owner approval |
| Adopt his "five handles" / "20 pips" / "2%" as engine thresholds | quoted as his chart-specific remarks; `gaps.md` records that generalising them would be invention |
| Fill partial-exit fractions | he explicitly hands the quantity to the trader (`U0118`, `U0119`); left as OWNER_DECISION |
| Rank the fib projection against the range target from memory | not asserted; only his stated preferences are recorded |
| Mark a dated review as EURUSD because the detector saw "euro" somewhere | marked `unknown`/`no` unless a **read** window named the pair; one Euro mention was only a depeg analogy and is `no` |
| Smooth the 13 pairing transcripts into one canonical sequence | each transcript keeps its own ordered events; nothing merged |
| Interpret any narrated move as profitability | no profitability interpretation anywhere; no data loaded |

## 8. Numbers appearing in the output

Every number is either a count produced by a tool, or a number **he** states in a quoted window
(1am/2am/8:30/9:30/12 o'clock, five handles, 20 pips, four handles, 75%, two percent, 10 handles).
No threshold was chosen by the agent. The DESIGN/VALIDATION parity rule is a calendar rule fixed in
code before any data existed, and is labelled as carrying no statistical claim.

## 9. What was not done

- No engine code, no market data, no backtest, no CSV, no profitability interpretation.
- No YouTube fetch, no audio, no frame extraction, no ASR run.
- 45 selected concepts not carded; 2,982 of 3,000 comparative windows not reduced to records;
  58 of 71 dated candidates without pairing cards.
- `definition_hits.jsonl` (2,764 × 30-word windows) kept in `/tmp` only, and example quotes trimmed to
  `NONE` for 6,456 lower-frequency inventory rows, to respect the ≤25-word quote rule and avoid
  bulk redistribution of corpus text.
- Base commit was read via `git show`; it was **not** merged into the work branch.

## 10. Largest weaknesses, stated plainly

1. **117 CHECK 2 warnings** — paraphrase vocabulary drifts from the source window.
2. Only **excerpts** of each window were read, not full windows.
3. **21 of 66** selected concepts covered; group coverage is broad but shallow in places.
4. **6** EURUSD-usable dated transcripts is far too few to validate anything.
5. Deixis ("this high", "that low") is unresolved throughout and needs chart images.
