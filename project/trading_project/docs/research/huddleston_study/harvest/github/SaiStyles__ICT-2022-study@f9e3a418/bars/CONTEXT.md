# bars - raw DBN in, clean session-aligned bars out

One job: turn `../data/raw/` into the only price series anything downstream is allowed to read.

**Everything in `output/` is generated.** Delete it and run the script; nothing is lost.
That is why it is not backed up. `build_bars.py` and this file are the real content.

## Run it

```
python bars/build_bars.py
```

Roughly a minute for the roll calendar, a few minutes to stream the 1-minute file.

## What it fixes, and why each one matters

These are DECISIONS.md **section 21**. They are here in short form; the reasoning is there.

### 1. Calendar spreads are dropped

`NQ.FUT` returns every NQ instrument, and **5,947 of 18,935 daily rows are spreads**
(`NQM0-NQU0`, `NQZ2-NQH3`). They are priced as differentials, so they go **negative** -
one prints at **-1.85**.

Outrights are selected by **positive match** (`^NQ[FGHJKMNQUVXZ]\d{1,2}$`), never by
excluding `-`. A spread that survives does not throw; it becomes a high, a low, an order
block. **Silent corruption that looks exactly like signal.**

### 2. The day runs midnight-to-midnight, New York

> ep11 [07:44] `if you're looking at the entire daily range you're going to use the
> opening price at **midnight**. but if you're going to be looking at the morning
> session, you're going to be looking at the **8:30** in the morning opening price.`

Confirmed ep16 [06:20], ep02 [19:16], and used as the daily-scale Power Three anchor
throughout ep19 and ep21.

Databento's supplied `ohlcv-1d` buckets by **UTC day** - four to five hours adrift - so it
is **not usable** for daily bias, daily order blocks or Power Three. Every timeframe here
is resampled from the 1-minute series on a `America/New_York` index **with DST**.

**Midnight and 8:30 are not interchangeable.** Midnight anchors the daily range and the
London session; 8:30 anchors the New York session (ep21 [13:21], [16:07]). They are two
nested Power Threes (ep19 [99:39]), not two guesses at one number. Nothing here should
ever collapse them.

### 3. The roll uses volume, and says so

Ep05 [04:47] rolls on **open interest**, which is not in this purchase and is not being
bought (section 20). Volume is the proxy: 3-day rolling volume per contract, argmax,
forced monotonic in expiry order so the front month can never walk backwards.

`output/roll_calendar.csv` exists so the choice is **auditable rather than implicit** -
one row per roll, with both contracts and the volumes that decided it.

**The exposure is small and must be measured, not assumed.** The model is intraday and
never holds through a roll, so a wrong roll date can only touch a level that spans the
boundary - previous-day high/low, and bias on the roll day. About **four days a year in
250**. `--roll-shift` moves every roll +/- N days; the ledger entry is not "we used volume",
it is **"we used volume and shifting it three days each way changed nothing"**. If it does
change something, that is a finding about the model, not about NQ.

## Outputs

| file | what |
|---|---|
| `output/nq_1m.parquet` | front-month 1-minute, New York tz-aware index |
| `output/nq_daily.parquet` | midnight-NY daily bars |
| `output/roll_calendar.csv` | every roll, with the volumes that chose it |
| `output/build_report.md` | counts, gaps, and the corpus price check |

### 4. Sunday evening is its own calendar day

Midnight boundaries split the CME session, so the week's opening evening (Sunday ~18:00 ET)
gets its own calendar day - **805 of them, median 359 bars**. Ep02 [19:16] runs the week
`Monday midnight NY open to Friday close`, so **that evening is outside his week.**

Read naively it looks like a full prior session, and "yesterday's high" on a Monday becomes
six evening hours. `nq_daily.parquet` carries **`sunday_open`** and **`full_session`** so
that cannot happen quietly. Anything computing a previous-day level must filter on them.

## Human check

`build_report.md` looks for prices ICT quotes on camera - 14,792.50 and 14,647.00 (ep06),
14,505.00 and 14,622.75 (ep07), 12,553.25 (ep29) - **in the front-month series**, which is
a stronger test than finding them somewhere in the raw file: it exercises the spread
filter, the roll and the timezone at once.

**Be precise about what it proves.** It confirms the level traded in the front month during
2022. It does **not** yet confirm the exact session, because the episode dates are not
recorded in `study/`. Weak corroboration that they line up: ep06's levels first print
**2022-01-20** and ep07's on **2022-01-21** - consecutive episodes on consecutive sessions.
Pinning the dates would upgrade this to a real bar-for-bar check and is worth doing before
the first backtest.

If a level goes missing, suspect the roll or the timezone before suspecting the corpus.
That is not hypothetical: the first run of this script reported all five missing, because
`groupby("symbol")` merged 2012's NQH2 with 2022's and froze the front month in 2016.
**The check is the only reason that was caught.**
