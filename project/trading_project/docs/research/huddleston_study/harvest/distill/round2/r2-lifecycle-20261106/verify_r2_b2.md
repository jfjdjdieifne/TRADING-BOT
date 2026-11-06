# verify_r2_b2.md

- claims checked: **42**
- CHECK 1 pass (quote verbatim, <=25 words): **42** (100.0%)
- CHECK 1 fail: **0**
- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **40**


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
- `R2QA-0003` missing: already, called, rebalanced
- `R2QA-0004` missing: every, opportunities, plan, structural
- `R2QB-0003` missing: appears, once, used
- `R2QC-0004` missing: grows, scaling
- `R2QI-0001` missing: 'market, choch, defined, says, shift'
- `R2QK-0001` missing: drops, further, lower', refinement, setup, timeframe
- `R2QK-0002` missing: actually, chosen, fixed, rule, timeframe
- `R2QK-0003` missing: path, runs, stated
- `R2QL-0001` missing: decision, level, price, routine
- `R2QL-0002` missing: hand, taken, view
- `R2QL-0003` missing: direction, early, plus, selects
- `R2QL-0004` missing: evidence, itself, participation, rather, reaches, trading, waits
- `R2QH-0001` missing: becomes, reference
- `R2QJ-0001` missing: graded, treated
- `R2QJ-0002` missing: level, price, returns, treated
- `R2QJ-0003` missing: described, encroachment, sitting
- `R2QM-0001` missing: 'price, swing, wing'
- `R2QM-0002` missing: attributed, dealing, equilibrium, reaction
- `R2QK-0004` missing: demand, escalated, messy, timeframe, used
- `R2QK-0005` missing: dropping, fixed, justified, ladder, seeing, timeframe
- `R2QH-0002` missing: sequence
- `R2QG-0002` missing: acting, candle, defined, entering, large, size
- `R2QM-0003` missing: signal, tool, used
- `R2QD-0003` missing: move, question, trade
- `R2QA-0005` missing: imbalance, placed, taken, used, wherever
- `R2QM-0004` missing: dividing, line, swing, taken
- `R2QG-0003` missing: break, insufficient, rejected, shallow, wants

## How the checks work

CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.
CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.
