# PROGRESS — understanding round v3, session K2

Start point: tip of `origin/arena/e91e69b1-trading-bot` = `f1eb0f86be86b8fc8bd55865b4e427f395eace1f`
(contains `understanding/u2-all-20261106/AUDIT.md`, verified).
Corpus: `newsqlguru/ict-index` @ `e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c`, tarball SHA-256 verified
`4213e692f7c978dab8fe5ba124d34d887f17316c89d27bb2a7406fd3776f769d`, 490 transcripts, re-downloaded to `/tmp/dr`.

| phase | status | artefact |
|---|---|---|
| 1 comparisons | **DONE** | `comparisons/` (31 records, 240 windows looked at as 25-word windows) |
| 1b expanded | **DONE** | 7 windows opened at ±300 words → 11 more records; total 42, verifier 42/42 |
| 2 concepts | **DONE (all 23 THIN)** | `concepts/` 23 cards, 39 claims, 58 windows, index.md |
| final | **DONE** | `AUDIT.md` extended; protected file checked |

Tools copied unmodified from u2: `tools/corpus_engine.py`, `tools/probe_terms.py`, `tools/verify_claims.py`,
`tools/read_window.py`. New in K2: `tools/reduce_comparisons.py` (bucket classifier over u2's 3,000 raw windows).

## Resume notes
- `/tmp/u2_comparisons_raw.jsonl` is the 3,000-window input (copy of `u2-all-20261106/comparisons_raw.jsonl`).
- `comparisons/shortlist.tsv` holds the 240 classified windows with row ids `R000`…`R239`; records cite these ids.
- Re-run verification with `python3 tools/verify_claims.py comparisons/claims_cmp.jsonl --report comparisons/verify_cmp.md`.
