# PROGRESS — concept-understanding round v2, session `u2-all-20261106`

Assignment: **all four groups A+B+C+D** (owner answered "كلشي" when asked to pick one).
Base commit read via `git show`: `36f2217d3e32a753f842ed8be334010e3d77c138`
(branch `arena/e91e69b1-trading-bot`, 2026-11-06 17:28:53 +0000 — the newest project branch;
`origin/main` is `e0c2234`, 2026-10-16, and contains no harvest at all).
Work branch: `arena/e6974afe-trading-bot` (fixed by the platform).

## Corpus actually obtained this session

`newsqlguru/ict-index` at pinned commit `e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c`
(pin read from `harvest/github/repos_meta.jsonl` at the base commit), downloaded via codeload:
HTTP 200, 10,548,984 bytes, tarball SHA-256
`4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d`.
Extracted to `/tmp/ictidx/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c/`.
**490 transcripts, 2,549,198 words.** Every transcript carries `offsetMS`/`durationMS` and a
`RefLink` YouTube URL, so provenance is stronger than the mirror used in earlier rounds.
No engine code, no market data, no fetch of any video.

## Phase table

| phase | state | result |
|---|---|---|
| 0 setup | DONE | branch printed; HEAD realigned to `origin/arena/e6974afe-trading-bot` with `git reset --mixed` after proving worktree identical (645 files, 0 missing, 0 mismatch, 0 extra); corpus downloaded |
| Task 0 discovery | DONE | 13,813 grams kept, 2,764 definition windows, 116 directed phrase probes (**0 zero-hit**), 66 concepts selected across A/B/C/D, 13,761 terms excluded-or-deferred with reasons |
| Task 1 cards | IN_PROGRESS | see `concepts.jsonl` / `cards_done.txt` |
| Task 2 comparisons | NOT_STARTED | |
| Task 3 story pairing | NOT_STARTED | |
| Task 4 gaps | NOT_STARTED | |
| final audit | NOT_STARTED | |

## Important correction recorded during Task 0

The n-gram filter drops any gram that starts or ends with a stop-word, so `old high`, `swing high`,
`time of day`, `no trade`, `being wrong`, `power of three`, `weekly template` never appeared in
`concept_inventory.tsv`. **NOT_IN_INVENTORY did not mean absent.** A directed phrase probe with no
stop-word filter (`tools/probe_terms.py`, `probe_terms.tsv`) found all 116 probes present, e.g.
`old high` 629/207 files, `swing high` 423/130, `time of day` 333/149, `ipda` 3/3,
`weekly template` 4/3, `daily template` 2/1. Nothing was declared absent on the strength of the
n-gram filter alone.

## Reading discipline

`windows.jsonl` logs every extracted window (file, ±250-word range, sha256, concept, marker score).
`read_log.jsonl` distinguishes `window_extracted` from `excerpt_read`: the agent saw the
marker-bearing excerpts (each ≤25 words) inside each window, **not** all 501 words. This is stated
plainly rather than implying a full read. `tools/corpus_engine.py add` refuses any claim whose quote
is not located verbatim (lowercase + whitespace collapse only) or whose hit falls outside a logged
window.

## What was deliberately kept out of the repo

`definition_hits.jsonl` (2,764 × 30-word windows) stays in `/tmp` — it exceeds the ≤25-word quote
rule and would bulk-redistribute corpus text. Example quotes in `concept_inventory.tsv` were trimmed
to `NONE` for 6,456 lower-frequency rows for the same reason (872 KB → 364 KB).

## Resume instructions

1. `CORPUS`/`DR` = `/tmp/ictidx/ict-index-e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c`; if `/tmp` was
   wiped, re-download the same pinned tarball via codeload and re-run `tools/probe_terms.py` to
   rebuild `/tmp/corpus_texts.json`.
2. `python3 tools/corpus_engine.py windows --concept X --phrase "..." --n 15` then author claims.
3. Verify: `DR=$CORPUS python3 tools/verify_claims.py claims.jsonl --report reports/verify.md`.
4. Protected file checked **only at the end**.
