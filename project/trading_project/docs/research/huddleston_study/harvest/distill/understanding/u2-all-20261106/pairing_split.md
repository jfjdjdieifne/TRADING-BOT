# DESIGN / VALIDATION split — fixed before any data was loaded

**No market data was loaded in this session.** No price series, no candles, no CSV. The split below is
therefore fixed before any recogniser exists and before any outcome is known, which is the point.

## The rule (deterministic, stated in code first)

Implemented in `tools/task3_pairing.py` before any transcript event was read:

```
day-of-month ODD  -> DESIGN
day-of-month EVEN -> VALIDATION
```

Calendar parity was chosen because it is deterministic, needs no random seed, and cannot be tuned to
the data. It carries **no** claim that odd and even days are statistically equivalent — that is an
assumption to be checked later, not a result.

## Candidate population

`pairing_candidates.jsonl`: **71** transcripts whose filename states a specific calendar date before
2025-05-01 and which read as a market review / session review / tape reading / pair commentary.
Range **2022-09-01 → 2023-10-22**. Split: **35 DESIGN / 36 VALIDATION**.

Filenames are the date source. Where a filename carried more than one date-like token the earliest
valid date was used; that is a mechanical choice, recorded here rather than hidden.

## What was actually read

15 unique dated transcripts were opened for events across 9 dates; 13 produced a pairing card
(`pairing_index.tsv`), carrying **18 narrated events** in total. Duplicate files with identical
SHA-256 in different directories were collapsed — the same January 09 forex review appears twice in
the tree and is one transcript, not two.

**6** of the read transcripts name euro dollar / EURUSD inside a window that was actually read, so
only those are marked `usable_for_EURUSD_test=yes`:

| date | split | pair stated in a read window | events |
|---|---|---|---:|
| 2023-01-20 | VALIDATION | EURUSD | 2 |
| 2023-01-26 | VALIDATION | EURUSD+GBPUSD+DXY | 1 |
| 2023-02-25 | DESIGN | EURUSD+GBPUSD | 1 |
| 2023-02-25 | DESIGN | EURUSD | 1 |
| 2023-05-23 | DESIGN | EURUSD+DXY+ES | 1 |
| 2023-05-24 | VALIDATION | EURUSD+DXY+ES | 2 |

Three of those are DESIGN and three are VALIDATION. That is a small usable set and it is reported as
such — it is not enough to validate anything on its own.

## Honesty limits on this split

- `pair_stated` comes only from an instrument-naming window that was read. Transcripts where the
  mechanical detector saw "euro" somewhere in the text but no read window named it are marked
  `unknown`, **not** `yes`.
- Several dated reviews are dollar-index or ES reviews. They are marked `no` for a EURUSD test even
  though the concepts transfer, because the instrument he is narrating is not EURUSD.
- One transcript mentions the Euro only as a historical depeg analogy; that is marked `no`, not as a
  pair review.
- The narrated events are his words about a chart. They are **not** verified against price data, and
  nothing here is interpreted as profitability.
