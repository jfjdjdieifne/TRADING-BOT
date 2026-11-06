# verify_r2_b1.md

- claims checked: **13**
- CHECK 1 pass (quote verbatim, <=25 words): **13** (100.0%)
- CHECK 1 fail: **0**
- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **13**


## CHECK 2 warnings

- `R2QA-0001` missing: trailed
- `R2QA-0002` missing: block's, once, second, tighter
- `R2QB-0001` missing: choice, entry, left, trader
- `R2QB-0002` missing: demand, entry, fill, often, risk, widen
- `R2QC-0001` missing: example, risked, sizing, worked
- `R2QC-0002` missing: baseline, example, multiple, targets
- `R2QC-0003` missing: entering, priority, protecting
- `R2QD-0001` missing: appear, itself, sweep, told
- `R2QD-0002` missing: pending, scheduled
- `R2QE-0001` missing: extreme, holds, opposite, remains, setup, treated, valid
- `R2QF-0001` missing: begins, killzone
- `R2QF-0002` missing: '4x', extend, gives, killzone, qualifier, said
- `R2QG-0001` missing: breath, described, produces

## How the checks work

CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.
CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.
