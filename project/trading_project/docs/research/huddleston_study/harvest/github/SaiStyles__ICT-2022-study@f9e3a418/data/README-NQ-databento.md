# NQ - Databento GLBX.MDP3

Placed 2026-09-03. Verified against the corpus the same day.

## What it is

| | |
|---|---|
| Dataset | `GLBX.MDP3` - CME Globex MDP 3.0 |
| Symbols | `NQ.FUT`, `stype_in: parent` - **every NQ contract month**, not a continuous series |
| Range | **2010-06-06 -> 2026-02-26** (~15.7 years) |
| Schemas | `ohlcv-1d`, `ohlcv-1h`, `ohlcv-1m` |
| Encoding | DBN + zstd, `pretty_px: false`, `pretty_ts: false`, `map_symbols: false` |
| Job ids | 1d `HXXTYLVU7N` · 1h `DTBDRHLQQQ` · 1m `5B35EKTMK7` |
| Size | 1m is 105 MB compressed - **the only one that matters**; 1h and 1d are derivable |

**Left zipped on purpose.** The reader streams from the archive; unzipping buys nothing and doubles the footprint.

Reading it needs `databento` (installed 2026-09-03, pulls numpy/pandas/pyarrow/zstandard).
`DBNStore.to_df()` resolves symbols and scales prices on its own - the raw int64 fixed-point
and UTC nanoseconds never need handling by hand.

## Verified on arrival

Every price he quotes on camera in 2022 prints in this tape:

| corpus | level | result |
|---|---|---|
| ep06 short | 14,792.50 | traded, 39 days |
| ep06 exit | 14,647.00 | traded, 41 days |
| ep07 long | 14,505.00 | traded, 47 days |
| ep07 exit | 14,622.75 | traded, 42 days |
| ep29 draw | 12,553.25 | traded, 52 days |

2022 front months: NQH2 (12,944-16,564), NQM2 (11,036.75-16,557), NQU2 (11,068.50-16,130), NQZ2 (10,484.75-15,300).

## THREE TRAPS - read before writing a loader

### 1. Calendar spreads are mixed in with the outrights

**5,947 of 18,935 daily rows are spreads** - `NQM0-NQU0`, `NQZ2-NQH3` - and they are priced
as *differentials*, so they go **negative** (one prints at **-1.85**).

**Filter `symbol` containing `-` before anything else.** A spread left in the series poisons
every high, low, order block and fair value gap computed from it, and it will not look like
an error - it will look like a level.

### 2. The supplied daily bars are NOT his daily candles

Databento buckets `ohlcv-1d` by **UTC day**. His day is **midnight to midnight, New York**:

> ep11 [07:44] `if you're looking at the entire daily range you're going to use the
> opening price at **midnight**.`

Confirmed ep16 [06:20], ep02 [19:16] (`Monday midnight NY open to Friday close`), and used
throughout ep19/ep21 as the daily-scale Power Three anchor.

**Correction, 2026-09-03:** this note first said his daily candle was the CME session
(18:00 -> 17:00 ET). That is the natural assumption for futures and it is **wrong** - the
corpus is explicit and it is midnight NY. Caught by grepping `study/` before writing the
loader rather than after.

**So bars are resampled from the 1-minute series** on a `America/New_York` index with DST -
see `../bars/`. The supplied 1d/1h files are a cross-check only.

### 3. Contract selection deviates from his stated rule

Four quarterlies trade at once. Ep05 [04:47] says roll about a week before the third Friday
to whichever month has the larger **open interest**.

**OHLCV carries no open-interest field** - that lives in Databento's `statistics` schema,
which was not purchased. So selection will use **volume** as the proxy.

**This is a deviation from a stated rule and belongs in the ledger as one**, not in a
comment. Volume and open interest disagree most exactly at the roll, which is where the
choice bites.

### 4. Sunday evening is its own calendar day - found 2026-09-03

The midnight convention splits the CME session, so the week's opening evening
(Sunday ~18:00 ET) lands in its own calendar day with a **median of 359 bars**.
There are **805** of them, and ep02 [19:16] puts the week at `Monday midnight NY open to
Friday close` - **so that evening is outside his week.**

Read naively, a 359-bar Sunday looks like a full prior session, and "yesterday's high"
on a Monday would be six evening hours instead of a day. `nq_daily.parquet` carries
`sunday_open` and `full_session` flags so this cannot happen silently.

The only other short days are **34 US market holidays**. No unexplained gaps anywhere in
the 15.7 years.

## ES is out - RULED by the builder, 2026-09-03

> `we dont need ES. its waste of time, the SMT stuff is worst thing.`

**Settled. DECISIONS.md section 20.** Nothing below re-opens it; it is kept because a
future session will notice the ES trades in the corpus and needs to know they were seen
and ruled out deliberately, not missed.

Ep02 [01:41] names the **Nasdaq e-mini the main focus of the mentorship**, so NQ is the
right primary instrument. But a large share of the live trades *with exact quoted prices*
are **e-mini S&P**:

- ep29 [12:03] - `ES only - no NQ executions`
- ep41 [23:36] - ES multipliers; entry 3754.75, target 3780.25
- ep31 - entry 4007.75
- ep01 [23:03] - the chart shown is ES March 2022
- ep04 [00:29] - first worked example is ES
- ep40 [19:02] - ESU2022

And ep07 [22:00] is stronger than a preference: the fair value gap was **in ES**, and it
generated the **NQ** entry - `trading what's not in the chart`. The ep07 page already
flags that a faithful reproduction of those entries needs ES and YM loaded alongside.

**None of that is being bought.** The vetoes, the money-management ladder and the entry
gates all evaluate on NQ alone. What is given up: the ep07 cross-market entry is
reclassified from candidate rule to idea, and validation against his on-camera results is
partial - only the **NQ** trades (ep03, ep06, ep07, ep14) can be checked bar-for-bar.

## Not backed up

`data/raw/` is excluded from `extraction/backup.py` on purpose - gigabytes, and
re-downloadable from Databento with the job ids above. **This note is backed up; the bytes
are not.** See the header comment in that script.
