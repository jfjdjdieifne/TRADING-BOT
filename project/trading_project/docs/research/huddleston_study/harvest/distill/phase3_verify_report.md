# phase3_verify_report.md

- claims checked: **100**
- CHECK 1 pass (quote verbatim, <=25 words): **100** (100.0%)
- CHECK 1 fail: **0**
- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **29**


## CHECK 2 warnings

- `CLM-0009` missing: topic
- `CLM-0010` missing: whether
- `CLM-0012` missing: skipped
- `CLM-0017` missing: asked, question
- `CLM-0019` missing: exists
- `CLM-0023` missing: objective
- `CLM-0024` missing: looked
- `CLM-0028` missing: library, quotes
- `CLM-0029` missing: left
- `CLM-0032` missing: listed, signature
- `CLM-0033` missing: calls, library
- `CLM-0035` missing: used
- `CLM-0040` missing: library, records, using
- `CLM-0041` missing: library
- `CLM-0042` missing: comes, quoted, takes
- `CLM-0058` missing: described
- `CLM-0059` missing: asks, student
- `CLM-0074` missing: described
- `CLM-0075` missing: described
- `CLM-0076` missing: table
- `CLM-0077` missing: table
- `CLM-0078` missing: table
- `CLM-0080` missing: reason
- `CLM-0083` missing: library, says
- `CLM-0091` missing: listed
- `CLM-0092` missing: described
- `CLM-0093` missing: note, says
- `CLM-0096` missing: library, says
- `CLM-0098` missing: library, states

## How the checks work

CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.
CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.
