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
