# verify.md

- claims checked: **266**
- CHECK 1 pass (quote verbatim, <=25 words): **266** (100.0%)
- CHECK 1 fail: **0**
- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **0**


## How the checks work

CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.
CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.
