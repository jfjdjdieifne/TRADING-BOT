# Research Questions L — open ICT-style concepts, computable definitions

**Created:** 2026-11-08
**Base path:** `project/trading_project/docs/research/huddleston_study/engine_v1/`
**Output of this task:** `external_sources/l_open_questions.md`

**Scope rule.** For each concept we need definitions a computer can execute. A number alone is useless.
For every number found we need: OF WHAT it is measured, COMPARED TO WHAT, over HOW MANY candles,
on WHICH timeframe and instrument. If the page does not say, write UNSTATED. No gap is filled in here.

**Forbidden material:** YouTube or any video page/transcript/mirror; paywalled or login-only pages;
pirated or leaked material; chatbot or AI-generated answers; forum posts without a named author
unless clearly labelled; anything dated after 2025-04-30 is allowed only as web text but never as
market data.

**GitHub rule.** Open-source indicator or library code is an IMPLEMENTATION, not a teacher's
definition. Record it under type `IMPLEMENTATION_CODE`, with repo URL, commit hash, file path,
line numbers, and license if visible. Do not copy code. A description of at most 25 words in our own
words plus the exact numeric constant or formula name is enough. Never mix `IMPLEMENTATION_CODE`
with `TEACHING` counts.

**No market data. No 2023. No code. No pandas.** Do not modify `engine_v1/b1_candles/` or
`b1_independent_check/`. Do not judge, rank, average or choose between numbers. Do not use our own
ICT knowledge.

---

## QUESTIONS (verbatim)

Q1 Displacement. (a) How is "strong/energetic move" measured? (b) Of what is a body percentage taken (candle range? something else)? (c) Compared to what (previous N candle bodies, ATR, fixed pips, nothing)? (d) How many candles may form one displacement? (e) Must it leave a fair value gap? Must it break a swing? (f) Re-open our existing displacement evidence (external_sources/ files for F1, F2, F5, F3, F4, F6) and extract the exact denominator and baseline from each quote first; mark UNSTATED where absent.

Q2 Liquidity sweep, "price returns quickly". (a) How many candles may pass before price is back inside? (b) Is a wick beyond the level enough, or must a candle close back inside? (c) Which level counts (swing, equal highs, session high/low, previous day high/low)? Record each source's answer separately.

Q3 Equal highs / lows pairing. Between two highs to be called equal: (a) maximum number of candles or distance apart? (b) must the highs be consecutive swings? (c) must there be no higher high between them? Also record again any tolerance number, with its unit and what it is measured against (pips, ATR multiple, percent, spread).

Q4 Order block boundaries. Which candle, and which prices form the zone: body only, body plus wick, open to extreme, other? Which part is the entry level (full zone, 50 percent, open)?

Q5 Fair value gap. (a) Is there a minimum size and measured against what? (b) When is a gap considered invalid or used up (touched, 50 percent filled, fully filled, candle closes through)? Record each source's answer separately.

Q6 Stop placement. Where exactly does the stop go relative to the setup (which price), and is there a buffer, in what unit? Only quotes that state it for forex; futures points = record with label FUTURES_UNITS, do not convert.

Q7 Target. How is the target defined (previous swing, liquidity pool, fixed multiple of risk, other)? State any number with unit and what it is measured against.

---

## WHERE TO SEARCH (verbatim)

Public web pages and public GitHub repositories (README, docs, wiki, issues). Use many different search phrasings per question. Check at least 10 distinct pages per question; list every page checked even when it yields nothing.

---

## RECORD FORMAT (verbatim)

RECORD FORMAT (one record per finding), in external_sources/l_open_questions.md, one section per question:
 id; question; URL (or repo+hash+path+lines); publisher; author if shown; page date if shown; type = TEACHING or IMPLEMENTATION_CODE or NO_NUMBER; quote of at most 25 words verbatim in English (QUOTE_VERIFIED only if really on the fetched page); number and unit; OF_WHAT; COMPARED_TO_WHAT; HOW_MANY_CANDLES; TIMEFRAME; INSTRUMENT; independence from sources already in external_sources/ and EXTERNAL_SOURCES_LOG.md (state which); any reason the source gives for the number (quote it, or write NO_REASON_GIVEN). Label TIER2.
At the end of each question section: a plain table counting independent publishers per exact version (same number AND same OF_WHAT AND same COMPARED_TO_WHAT). Counts only, no recommendation. If nothing found for a question: NO_SOURCE_FOUND plus list of pages checked.

---

## Per-question record skeleton (fixed field order)

```
### <ID> — <publisher short name>
- id: <ID>
- question: <Qn (letter)>
- URL: <page URL, or repo + commit hash + file path + line numbers>
- publisher: <domain / org>
- author if shown: <name or UNSTATED>
- page date if shown: <date string or UNSTATED>
- type: TEACHING | IMPLEMENTATION_CODE | NO_NUMBER
- quote (<=25 words, English, verbatim): "<...>" — QUOTE_VERIFIED | QUOTE_NOT_FOUND
- number and unit: <number + unit, or NONE>
- OF_WHAT: <what the number is measured on, or UNSTATED>
- COMPARED_TO_WHAT: <baseline, or UNSTATED>
- HOW_MANY_CANDLES: <n, range, or UNSTATED>
- TIMEFRAME: <tf, or UNSTATED>
- INSTRUMENT: <symbol/class, or UNSTATED>
- independence: INDEPENDENT_OF_PRIOR_SOURCES | NOT_INDEPENDENT_OF_<id/prior entry> (state which prior entry in external_sources/ or EXTERNAL_SOURCES_LOG.md)
- reason given by source: "<quote>" | NO_REASON_GIVEN
- tier: TIER2
```

Section tail (per question):

```
#### Counts — exact versions (number AND OF_WHAT AND COMPARED_TO_WHAT identical)
| exact version | independent publishers |
|---|---|
```

If a question yields nothing: `NO_SOURCE_FOUND` plus the list of pages checked.

---

## Status

- Step 0 (this file): committed alone.
- Step 1: `external_sources/l_open_questions.md` written, then one pointer line added under heading
  `D2 research` in `OWNER_DECISIONS.md`, committed as a second commit.
