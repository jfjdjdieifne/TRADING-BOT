# DOSSIER 3 PLANS — raw material for an outside reviewer

Three dossiers, one per plan, assembled from the SAVED run outputs and the verified EURUSD 5m file.
Nothing here is judged. No engine was run; every number is either read from a saved record or recomputed
from candles by `dossier_v2.py` in this folder, which shares no settlement code with `build_v1` or
`build_v2`.

| file | plan | month | variant | outcome |
|---|---|---|---|---|
| `DOSSIER_P1_2021-09_V2-A.md` | `plan:2021-09-21T06:10:00+00:00:15m:fvg:bearish:17877` | 2021-09 | V2-A | settled_target, R +1.4667 |
| `DOSSIER_P2_2021-09_V2-B.md` | `plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336` | 2021-09 | V2-B | settled_stop, R −1.0500 |
| `DOSSIER_P3_2021-07_V2-A.md` | `plan:2021-07-23T07:50:00+00:00:15m:fvg:bearish:13843` | 2021-07 | V2-A | settled_stop, R −1.2500 |

Selection was **not** a new choice: the three are the `seeded random` entries already recorded in
`../TRADE_DETAIL_V2/SELECTION.json`.

## What this does NOT establish

- It does not establish that any reading is correct ICT; the reviewer is deliberately given no verdict.
- It does not establish that the three plans are representative; they are the seeded draw, nothing more.
- Fields the saved records do not carry are marked NOT_RECOVERABLE_WITHOUT_RERUN rather than rebuilt.
