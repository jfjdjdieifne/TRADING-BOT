# Engine v1 — fixed parameters

Status: **M0, fixed before any story test**. No recognizer, narrator, entry logic,
or profit evaluation exists at this stage.

| name | value | classification | reason / authority |
|---|---|---|---|
| `ALLOWED_YEARS` | 2022, 2023 | `USER_CONSTRAINT` | Explicit stage assignment. Loader refuses every other annual file, including 2026. |
| `DATA_CUTOFF` | 2025-05-01 00:00:00 UTC, exclusive upper bound | `USER_CONSTRAINT` | Every row at or after this instant is dropped immediately after timestamp parsing; an assertion checks the returned batch. |
| source repository / commit | `mailztoganesh-civil/forex-data` / `56d5f04fd90b29414a70147471309f1db326aa1c` | `USER_CONSTRAINT` | Immutable input identity. |
| source paths | `data/EURUSD/5m_bidask/2022.csv.gz`, `.../2023.csv.gz` | `USER_CONSTRAINT` | Only annual EURUSD BID/ASK files for the two allowed years. |
| `BAR_WIDTH` | 5 minutes | `SOURCE_DEFINITION` | Defined by the selected `5m_bidask` dataset, not tuned. |
| timestamp interpretation | UTC bar start; interval `[start, start + 5m)` | `DATA_EVIDENCE` | Event-alignment evidence and the pinned generator (`label="left", closed="left"`) are documented in `M0_DATA_AND_TIME.md`. |
| availability of bar `i` | at `bar[i].end`, exclusively | `CAUSAL_CONTRACT` | A bar cannot be used at its own opening; prefix output `i` is the state at its exclusive end. |
| prefix output cardinality | exactly one output per input candle | `ENGINEERING_CHOICE` | Gives an executable, output-by-output truncation contract; empty input gives empty output. Fixed before recognizers. |
| prefix comparison | exact value equality | `ENGINEERING_CHOICE` | Deterministic value objects must not reorder or change retrospectively; approximate matching could conceal instability. |
| timestamp diagnostic events | the 24 explicit BLS Employment Situation dates in `timestamp_evidence.py`, 08:30 Eastern Time, converted to UTC with `zoneinfo` | `ENGINEERING_CHOICE` | Pre-scheduled releases provide an external clock anchor in the candles themselves. Official calendars: [2022](https://www.bls.gov/schedule/2022/home.htm), [2023](https://www.bls.gov/schedule/2023/home.htm). All 24 releases are included; no selection by result. Dates are explicit because 2023-03-10 disproves a universal first-Friday heuristic. |
| timestamp diagnostic offsets | release `-5m`, `+0m`, `+5m`, `+10m`; BID high-low range | `ENGINEERING_CHOICE` | Under bar-start labels the first response-capable bar is `+0m`; under bar-end labels it is `+5m`. Four adjacent bars make that distinction observable. No range threshold or trade decision is used. |
| daily release-bar rank | competition rank among all bars on the release's UTC date | `ENGINEERING_CHOICE` | Relative-to-neighbours evidence with no materiality threshold. Flat bars remain in the ranking. |

No story-test parameter exists yet. Any later unavoidable recognizer lookback or
other number must be appended here, with its reason, **before** it is used in a
story test. Doctrine conflicts will be represented as parallel named variants,
not resolved by changing these engineering values.
