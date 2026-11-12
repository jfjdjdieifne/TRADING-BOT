# M0 — data, timestamp convention, and causal test harness

## Scope and result

M0 is complete. This stage adds no recognizer, narrator, entry logic, profit
backtest, or story-test result. DESIGN/VALIDATION story days were not run and no
`FREEZE` file was created.

The assigned start point was resolved as
`f1eb0f86be86b8fc8bd55865b4e427f395eace1f` and imported with
`git checkout <hash> -- project`, without reset or merge.

## 1. Source directory listing (listing only)

At `mailztoganesh-civil/forex-data` commit
`56d5f04fd90b29414a70147471309f1db326aa1c`, `data/` contains:

- pair/index directories: `AUDUSD`, `EURUSD`, `GBPUSD`, `NSXUSD`, `NZDUSD`,
  `SPXUSD`, `USDCAD`, `USDCHF`, `USDJPY`, `XAUUSD`;
- a `futures` directory;
- `summary.json`.

Therefore instruments other than EURUSD **do exist**. They were listed, not
downloaded. The only market-data payloads fetched were the two files below;
the 2026 annual file was never downloaded.

| file | bytes | Git blob SHA | downloaded gzip SHA-256 |
|---|---:|---|---|
| `data/EURUSD/5m_bidask/2022.csv.gz` | 3,310,136 | `136cd05f5b6725d8517572915a2ed7dc2b05440e` | `490d4fb9f1a07a1d7909477debbd935efc568fe1885475a7704a855ade9ab17e` |
| `data/EURUSD/5m_bidask/2023.csv.gz` | 3,227,699 | `9f354ef1a06fe45214d3124826875631c19dbad0` | `4aaacd30e944b474003c5ceb595dcf74011c81a4b7841d341f02909c6a270a96` |

Reproduction uses GitHub's blob API at the pinned commit (no `raw` moving head):

```bash
gh api -H 'Accept: application/vnd.github.raw+json' \
  repos/mailztoganesh-civil/forex-data/git/blobs/136cd05f5b6725d8517572915a2ed7dc2b05440e \
  > 2022.csv.gz
gh api -H 'Accept: application/vnd.github.raw+json' \
  repos/mailztoganesh-civil/forex-data/git/blobs/9f354ef1a06fe45214d3124826875631c19dbad0 \
  > 2023.csv.gz
```

## 2. Loader and information cutoff

`trading_system.ict_engine.data` uses the standard library to stream gzip CSV.
It implements the following:

- the annual filename allowlist is exactly 2022 and 2023; a path named
  `2026.csv.gz` is rejected **before opening it**;
- the exact pinned 19-column header is required;
- `Datetime` must be timezone-aware and is converted to UTC;
- immediately after parsing each timestamp, any row at or after
  **2025-05-01 00:00:00 UTC** is skipped, before numeric parsing;
- an assertion verifies that no returned candle reaches the cutoff;
- retained timestamps must belong to the named year, align to the five-minute
  grid, and be strictly increasing; the loader never sorts errors away;
- all numeric values must be finite, OHLC envelopes valid, ASK not below BID on
  corresponding fields, and volume/spread fields non-negative;
- zero-volume/flat rows are retained rather than silently repaired or removed.

Actual input accounting:

| year | rows read | retained | dropped by cutoff | first label | last label | zero BID-and-ASK volume | missing whole UTC dates |
|---|---:|---:|---:|---|---|---:|---|
| 2022 | 105,120 | 105,120 | 0 | 2022-01-01 00:00Z | 2022-12-31 23:55Z | 30,247 | none |
| 2023 | 104,544 | 104,544 | 0 | 2023-01-01 00:00Z | 2023-12-31 23:55Z | 30,464 | 2023-04-12, 2023-10-09 |
| **total** | **209,664** | **209,664** | **0** | — | — | **60,711** | **2 dates** |

Zero actual cutoff drops are expected because these inputs end in 2023. A
synthetic test injects two sealed rows with deliberately invalid numeric fields;
both are dropped before numeric parsing, proving the cutoff path. The two
missing 2023 dates are disclosed, not filled or interpolated. Reloading each
file produced exactly equal immutable batches.

## 3. Timestamp convention: evidence, not an assumption

### Conclusion

`Datetime` is the **UTC bar start**. A candle labelled `13:30` represents
`[13:30, 13:35)` and becomes decision-available at `13:35`, not at `13:30`.

### Why adjacent open/close equality is insufficient

A uniform five-minute shift preserves within-file OHLC ordering and most
open/close continuity. Such continuity alone cannot distinguish bar-start from
bar-end labels. The diagnostic therefore anchors the candles to independently
scheduled release times and then checks the pinned generator.

### Pre-declared data diagnostic

The protocol and offsets were committed before inspecting the real event
results. It uses all 24 US Employment Situation releases in the two years at
08:30 Eastern Time, converted with `zoneinfo`. Dates come from the official BLS
calendars: [1](https://www.bls.gov/schedule/2022/home.htm) and
[2](https://www.bls.gov/schedule/2023/home.htm). They are explicit rather than
a first-Friday heuristic; March 2023 was 10 March.

For each release, BID high-low range is compared at labels `-5m`, `0m`, `+5m`,
and `+10m`. With bar-start labels, the first response-capable candle is `0m`;
with bar-end labels it is `+5m`. No size threshold is used. The release candle
is also ranked against every candle on its UTC date.

Ranges below are in pips; `rank` is the release (`0m`) candle's competition rank
within its UTC day. **The single disagreement is retained and disclosed.**

| release (UTC) | -5m | 0m | +5m | +10m | largest offset | 0m day rank |
|---|---:|---:|---:|---:|---:|---:|
| 2022-01-07 13:30 | 6.4 | 26.0 | 16.4 | 10.7 | 0m | 1 |
| 2022-02-04 13:30 | 6.7 | 30.1 | 17.6 | 14.8 | 0m | 1 |
| 2022-03-04 13:30 | 13.3 | 18.4 | 25.1 | 18.1 | **+5m** | 5 |
| 2022-04-01 12:30 | 6.7 | 17.8 | 12.3 | 5.0 | 0m | 3 |
| 2022-05-06 12:30 | 9.9 | 25.6 | 13.3 | 10.6 | 0m | 3 |
| 2022-06-03 12:30 | 4.7 | 23.0 | 21.4 | 8.8 | 0m | 1 |
| 2022-07-08 12:30 | 8.9 | 35.5 | 25.5 | 12.8 | 0m | 1 |
| 2022-08-05 12:30 | 7.8 | 64.9 | 15.0 | 14.6 | 0m | 1 |
| 2022-09-02 12:30 | 16.1 | 49.8 | 18.4 | 22.1 | 0m | 1 |
| 2022-10-07 12:30 | 9.0 | 49.0 | 27.6 | 11.6 | 0m | 1 |
| 2022-11-04 12:30 | 8.6 | 38.2 | 36.7 | 17.7 | 0m | 1 |
| 2022-12-02 13:30 | 7.3 | 96.5 | 22.8 | 28.7 | 0m | 1 |
| 2023-01-06 13:30 | 6.6 | 48.5 | 26.3 | 30.8 | 0m | 1 |
| 2023-02-03 13:30 | 4.9 | 82.7 | 18.0 | 20.1 | 0m | 1 |
| 2023-03-10 13:30 | 5.1 | 42.1 | 16.5 | 24.7 | 0m | 1 |
| 2023-04-07 12:30 | 3.8 | 27.7 | 13.0 | 9.1 | 0m | 1 |
| 2023-05-05 12:30 | 6.4 | 39.4 | 17.7 | 11.2 | 0m | 1 |
| 2023-06-02 12:30 | 5.8 | 28.8 | 13.3 | 18.6 | 0m | 1 |
| 2023-07-07 12:30 | 6.5 | 37.8 | 17.8 | 16.5 | 0m | 1 |
| 2023-08-04 12:30 | 5.3 | 43.7 | 9.4 | 25.4 | 0m | 1 |
| 2023-09-01 12:30 | 4.4 | 43.6 | 10.7 | 17.4 | 0m | 1 |
| 2023-10-06 12:30 | 7.1 | 57.4 | 15.6 | 14.0 | 0m | 1 |
| 2023-11-03 12:30 | 6.3 | 42.2 | 15.5 | 17.0 | 0m | 1 |
| 2023-12-08 13:30 | 3.0 | 47.6 | 10.9 | 24.0 | 0m | 1 |

Aggregate: `0m` is strictly larger than `+5m` in **23/24** releases and is the
largest of all four offsets in those same 23. `+5m` is largest in **1/24**
(2022-03-04). The `0m` candle is in the day's top ten in **24/24** releases;
in 2023 it is rank one in 12/12. This strongly supports bar-start labels while
honestly leaving ordinary post-release variation visible.

### Independent generator confirmation

At the same data commit, `scripts/download_dukascopy_bid_ask_m5.py`
(Git blob `d1bb086e351f387d6c3d91478cb8089baa90181b`, SHA-256
`e4e8dcd1fb1b5c01ecc879f1f72b25d7c7fa068aa6a16697d69ed03d41995294`),
lines 116–122, aggregates one-minute candles with:

```python
frame.resample("5min", label="left", closed="left")
```

In pandas this explicitly means a left/bar-start label and left-closed interval.
The candle evidence and the generator agree. This does not claim tick-level
precision or that every news response must occur immediately.

## 4. Prefix-invariance harness

`trading_system.ict_engine.causal.assert_prefix_invariance` requires a pure
function to return one output per candle, where output `i` is available at
`candles[i].end`. It checks:

```text
function(candles[:n]) == function(candles)[:n]
```

including the empty prefix and exact output ordering. A deliberate final-close
lookahead function fails the unit test; a running-maximum function passes.
See `PREFIX_INVARIANCE.md` for the binding contract for M1 and M2.

The running-maximum smoke function also passed on each real annual file at
prefixes `0, 1, 288`, the first release index and its successor, the penultimate
index, and the full length:

- 2022: `0, 1, 288, 1890, 1891, 105119, 105120`;
- 2023: `0, 1, 288, 1602, 1603, 104543, 104544`.

These checks exercise the harness; they are not recognizer results.

## 5. Tests and reproducibility

Synthetic tests live inside the new package. Real-data checks never download
anything and are skipped unless the local directory is explicitly supplied:

```bash
PYTHONPATH=project/trading_project/src python -m pytest -q \
  project/trading_project/src/trading_system/ict_engine/tests

ICT_ENGINE_M0_DATA_DIR=/path/containing/2022-and-2023-only \
PYTHONPATH=project/trading_project/src python -m pytest -q \
  project/trading_project/src/trading_system/ict_engine/tests
```

Final executed results:

- **23/23 M0 tests passed** with the two real files supplied (19 synthetic +
  4 parameterized real-data checks).
- **1,856/1,856 total tests passed**: 1,833 pre-existing project tests plus the
  23 M0 tests. Final failure count: **0**.
- Final environment: Python 3.11, `numpy 1.26.4`, `pandas 2.3.3`,
  `pytest 9.2.0`. Warnings from the pre-existing suite remain warnings, not
  failures.

An initial full-suite attempt with the newest `pandas 3.1.1` / `numpy 2.4.6`
failed in pre-existing dtype and compatibility contracts. No pre-existing source
was changed to conceal that incompatibility. Re-running with the compatible
2.x/1.x generation gave the clean 1,856-test result above.

Protected-file verification is performed independently at milestone close; its
required identity is SHA-256
`72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
and size 12,216 bytes.
