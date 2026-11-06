# verify.md

- claims checked: **69**
- CHECK 1 pass (quote verbatim, <=25 words): **69** (100.0%)
- CHECK 1 fail: **0**
- CHECK 2 warnings (statement content word absent from +/-100-word surroundings): **63**


## CHECK 2 warnings

- `U0001` missing: knowing, location, requirement, says
- `U0002` missing: locating, reading, reduces, task, whole
- `U0003` missing: holding, locating, ranks
- `U0004` missing: candidates, named
- `U0005` missing: itself, looks, named, unfilled
- `U0006` missing: arrival, identified, next, promise, tendency
- `U0007` missing: held, insists
- `U0008` missing: resides
- `U0009` missing: market
- `U0010` missing: delivery, enumeration, inefficiency, reduces, sell
- `U0011` missing: looks
- `U0012` missing: locates, says
- `U0013` missing: runs, wick
- `U0014` missing: example, shown, timeframe, worked
- `U0015` missing: says, taken, used
- `U0016` missing: anticipated
- `U0017` missing: named, place, reaches
- `U0018` missing: contrasts
- `U0019` missing: waits
- `U0020` missing: asks
- `U0021` missing: calls, couples
- `U0022` missing: ones, ties
- `U0023` missing: says
- `U0024` missing: calls
- `U0025` missing: become, dropping, says
- `U0027` missing: equates
- `U0028` missing: clears, price, reverses, sequence, worked
- `U0029` missing: creates, says
- `U0030` missing: classified, reaches
- `U0031` missing: preference, states
- `U0032` missing: reside, sell
- `U0033` missing: points
- `U0034` missing: example, expects, price
- `U0035` missing: counts, touches
- `U0036` missing: answers, asks
- `U0037` missing: gives, says, width
- `U0038` missing: hunts
- `U0039` missing: having, makes
- `U0040` missing: gaps
- `U0042` missing: names, says, uses
- `U0043` missing: names, price
- `U0044` missing: says
- `U0045` missing: rejects
- `U0046` missing: calls, elsewhere
- `U0048` missing: describes, violating
- `U0049` missing: trading
- `U0050` missing: gives, needed, takes
- `U0051` missing: allows, explicitly, trades
- `U0052` missing: dropping, shows
- `U0053` missing: price
- `U0054` missing: near, sets
- `U0055` missing: cannot
- `U0056` missing: close, gives
- `U0057` missing: alone
- `U0059` missing: looks
- `U0062` missing: points
- `U0063` missing: answers, asks, candidates, facing
- `U0064` missing: says
- `U0065` missing: comes
- `U0066` missing: calls, notes
- `U0067` missing: price, rallying, shows
- `U0068` missing: price
- `U0069` missing: divergence, points

## How the checks work

CHECK 1 is a hard gate: the quote is searched in the source file after lowercasing and whitespace collapse only — no punctuation normalisation, no edit distance, no fuzzy match. A claim whose quote is not found is not written to `claims.jsonl`.
CHECK 2 is soft and reported, never silently fixed: it lists statement content words (len>=4, not stop-words) that do not appear in the +/-100-word source window around the quote. A warning means the statement added vocabulary the source window does not contain; the wording in `claims.jsonl` is the version that passed CHECK 1, and every warning is listed above.
