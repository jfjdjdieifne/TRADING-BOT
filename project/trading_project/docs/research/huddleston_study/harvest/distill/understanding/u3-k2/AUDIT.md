# AUDIT — v3 / K2 (phase 1 only, so far)

## 0. Start point
- `git fetch --all`; `origin/arena/e91e69b1-trading-bot` = `f1eb0f86be86b8fc8bd55865b4e427f395eace1f`.
- That commit contains `harvest/distill/understanding/u2-all-20261106/AUDIT.md` (checked before any work).
- All u2 files were read with `git show f1eb0f86…:<path>`; nothing from u2 was edited.
- Corpus tarball re-downloaded and its SHA-256 compared to the expected value: **match** (`4213e69…f769d`).

## 1. What was actually read (phase 1)
- u2's `comparisons_raw.jsonl`: **3,000 windows** were processed *mechanically* (bucket classifier), not read by eye.
- Of those, **836** matched a decision bucket; **240** were shortlisted (60 priority, 40 target, 40 entry,
  35 stop, 35 timeframe, 30 stand-aside) and **all 240 were printed and looked at** as 25-word windows.
- **31** of them became comparison records. The other 209 were looked at and *not* reduced: they were either about a
  different subject than their bucket name suggests, or they contained the marker word without any ranking of two
  things (e.g. "the first time watching this video").
- These are 25-word windows inherited from u2, **not** ±400-word windows. Stated here rather than implied otherwise.

## 2. Verifier
- `tools/verify_claims.py` (copied from u2, unmodified): **CHECK 1 = 31/31 pass, 100%**, 0 fail.
- **CHECK 2 warnings: 0 of 31.** Reason, stated plainly: each claim's `statement` is the speaker's own verbatim
  words (the quote itself), so no statement word can be absent from its surroundings. All interpretative language was
  moved out of `statement` into a separate `reading` field, and **104 added words** across the 31 readings are listed
  per record in `added_words`. The u2 baseline was 117 CHECK 2 warnings; the number is not comparable because the
  statement/reading split is new — it is not evidence that this corpus is cleaner.

## 3. Temptations (recorded, not added)
1. **"A 30–50 pip stop"** — the quote does carry those numbers (K2C-011), but only as a conditional tied to an entry
   under the low. I did not turn it into a general stop rule or a default width.
2. **"Two percent risk"** — quoted for *new traders* (K2C-012). I resisted writing "risk 2%"; the record says what he
   says and who he says it to.
3. **"62 percent retracement"** — appears in window R116 but the quote I used is about waiting for equilibrium; the
   number was left out of the record rather than smuggled in.
4. **"OTE 0.62–0.79"** — my memory wanted to complete the equilibrium record with it. Not added; no window read states it.
5. **"Kill zone times"** — memory supplied 2:00–5:00 / 8:00–11:00. No window read here states a window, so no time
   appears in any record.
6. **"Breaker = failed order block"** — I know the phrase; the quote only ranks the breaker swing point. Definition
   left for phase 2.
7. **Ordering the stand-aside records 1..10** — he never numbers them. The ranks in `priority_lists.md` are my
   ordering of *his* sentences by strength of wording, and the file says so.

## 4. Weaknesses
- **Only 31 records from 3,000 windows (1.0%).** The reduction is honest but thin; the biggest loss is that the raw
  windows are 25 words, so most of them cannot contain both halves of a comparison.
- **`stop_choice` (2 records) is very thin.** The stop material exists but mostly as definition, not as a comparison;
  a proper job needs fresh ±400-word reads around "stop" that u2 did not store.
- **`entry_choice` (6) is thinner than `stand_aside` (10)** — the opposite of what the assignment expected.
- **Bucket assignment is mechanical** (marker words). A quote containing "avoid" in an unrelated sense can be sorted
  into `stand_aside`; every record was re-read by eye, but the *counts* in `counts.json` are of shortlisted windows.
- **No chart was opened.** Every record is text; nothing here is verified against candles.
- **No u2 concept card was re-derived**, so a few records rest on u2's concept naming (e.g. "breaker_block") without a
  fresh definition in this session.


## 1b. Phase 1b addendum (context-expanded windows)
- The assignment asked for ±300-word windows around **all 240** shortlisted windows. **I opened 7 of them**
  (`--ctx 300`, logged in `comparisons/read_log_1b.jsonl`): 4 in `stop_choice`, 3 in `entry_choice`. The remaining
  233 were not opened; they were seen only as the 25-word windows inherited from u2. This is a real shortfall, stated
  plainly, not glossed: the cause was reading-time budget, not a lack of material.
- The 7 windows produced **11 new comparison records** (`phase: "1b"`): stop choice 5, entry choice 3, target choice 3.
  Two of them carry numbers he states himself, and both are kept as his numbers, not as rules: a 17-pip stop from a
  lower-timeframe refinement (K2C-035) and "10 to 20 pip ranges above a high" (K2C-041).
- New totals: **42 records**, verifier **42/42 CHECK 1 = 100%**, **CHECK 2 = 0 warnings** (same reason as before:
  `statement` is his words; interpretation lives in `reading` with `added_words`).
- What the ±300 context changed: three of the eleven would have been wrong or impossible from 25 words alone —
  the stop-out/re-entry logic (K2C-033, K2C-034) only makes sense with the paragraph before it, and the rejection of
  other teachers' 50-level entry (K2C-038) needs the whole sentence to see whose view he is rejecting.
- Still thin after 1b: `priority` (4), `timeframe_choice` (5). `stop_choice` is now the strongest bucket (8).


## Phase 2 (concept cards)
- Deferred set derived mechanically: u2 `kept_concepts.tsv` has 66 concepts, u2 shipped 21 cards, so **46 deferred**
  (gaps.md says 45 — the difference is one concept whose card name and tsv name differ by suffix). Even positions of the
  alphabetical sort = **23 concepts**.
- **23 cards** in `concepts/cards/`, index in `concepts/index.md`, **39 claims** in `concepts/claims.jsonl`
  (ids `K2P-001…039`), **58 probe windows** logged in `concepts/read_log.jsonl` (±85–90 words each).
- **Every card is marked THIN.** The brief asked for ≥15 windows per concept; the actual is 2–3. I did not pad the
  cards to look complete: sections that no window supports say `NOT_IN_WINDOWS_READ (this session)`.
- Verifier on the phase-2 claims: **39/39 CHECK 1 pass = 100%**, **CHECK 2 = 0 warnings**.
  Two planned quotes could not be recovered verbatim from the logged windows (`inefficiency`, `pd_array` second quote);
  those concepts still carry one verified claim each, and the missing quote was dropped rather than paraphrased.

## Totals for the session (both phases)
| item | phase 1 | phase 1b | phase 2 | total |
|---|---|---|---|---|
| windows read | 240 (25-word) | 7 (±300) | 58 (±85–90) | 305 |
| verified claims | 31 | 11 | 39 | **81** |
| records/cards | 31 | 11 | 23 cards | 42 records + 23 cards |
| CHECK 1 pass | 31/31 | 11/11 | 39/39 | **81/81 = 100%** |
| CHECK 2 warnings | 0 | 0 | 0 | **0** (u2 baseline: 117) |

## More temptations (phase 2), all refused
8. **"Silver bullet = 10:00–11:00 NY window."** The window I read uses "silver bullet" only as a dismissive metaphor
   for a secret weapon (K2P-037). No time, no pattern, nothing added.
9. **"Judas swing = the first candle of the session always."** I know the phrase; the windows give it as manipulation
   driven by a news event (K2P-019/020). Mechanism not added.
10. **"Asian range = midnight–02:00."** No clock times in the Asian-range windows read. The two clock facts I do have
    come from other windows (midnight drop, 8pm projection) and are recorded as those, not generalised.
11. **"Volume imbalance = the gap between bodies."** The window says the magnet behaviour holds while no body is laid
    across it (K2P-048/049). I did not define its geometry.
12. **"Money management = 1–2% rule."** The window is about interest-rate triads and professional money movement
    (K2P-028/029); no sizing rule appears in it, and none was written.
13. **"Time distortion = X bars."** No number exists in the window (K2P-045/046).
14. **Ordering the seasonal-tendency inversion.** The quote gives the inversion for one pair; I did not turn it into a
    general rule for all USD pairs.

## Weaknesses (session overall)
- **The ±300 expansion asked for 240 windows and got 7.** The reason is reading budget; the effect is that 233
  shortlisted windows were never seen beyond 25 words, so comparisons they contained remain unreduced.
- **Phase-2 cards are stubs.** One or two windows per concept cannot carry PURPOSE→VARIANTS; nine of the ten required
  sections are `NOT_IN_WINDOWS_READ` on most cards. Treat them as placeholders that point at real quotes, not as cards.
- **`non_farm_payroll` has exactly 1 corpus hit**, so its card rests on a single window by necessity; `long_term_high`
  has 10 hits and `time_distortion` 34 — these concepts are thin *in the corpus*, not only in my reading.
- **Probe windows are chosen by first-match in alphabetical file order**, which biases every card toward the 2016
  mentorship folder. A better card needs random or era-stratified sampling.
- **No chart, no data, no engine code** — as instructed. Nothing here was tested against price.
- **/tmp is wiped between calls in this sandbox**; every reading call re-downloaded the corpus and verified its tarball
  SHA first (`tools/ensure_corpus.sh`). If it is wiped again, re-run that script.
