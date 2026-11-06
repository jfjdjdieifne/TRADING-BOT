# ICT 2022 Mentorship — a structured study, and what could be tested

A close reading of the 2022 *ICT Mentorship* series (41 episodes, 24.5 hours),
turned into a traceable reference, plus an attempt to mechanise the parts that
are mechanisable and measure them against 15.7 years of Nasdaq-100 futures data.

**Two deliverables:**

1. **The study** — [`study/`](study/) (41 episode analyses, every line traceable
   to a timestamp), [`THE-MODEL.md`](THE-MODEL.md) (the methodology synthesised
   across episodes rather than episode by episode), and
   [`study/_refinements.md`](study/_refinements.md) (how each concept is refined
   across the series — optimal trade entry is used from ep01 and only defined in
   ep41, eight episodes later).
2. **The tests** — 154 hypotheses run with pre-registration, matched null
   models, a multiple-comparison hurdle, and a held-out slice.

---

## What was tested, and what was not

**This is the most important section in the repository.** The results below are
narrow, and reading them as a verdict on the methodology would be wrong.

### What was tested

Individual claims, mechanised, mostly **in isolation** — is a fair value gap
revisited more often than a matched move without one; does a liquidity sweep
reverse; is 08:30–11:00 measurably different from other windows; does each gate
in the entry sequence improve what passes it.

### What was NOT tested, and could not be

- **Confluence.** The series does not teach these primitives as standalone
  signals. It teaches them stacked — a gap *with* displacement *with* a liquidity
  raid *at* a specific time *in* the direction of a higher-timeframe bias. This
  work tested primitives alone, plus one composite pipeline of my own
  construction. **An isolated primitive showing nothing is not evidence that the
  stack shows nothing.**
- **Discretion.** The series is explicit that judgement is required — *"if the
  chart is sloppy, close the charts"*, *"if you cannot say where price goes next,
  you're gambling"*. Those are real instructions and they are not codeable. They
  are catalogued in [`backtest/vetoes.py`](backtest/vetoes.py) under `DEFERRED`
  rather than approximated, because a fabricated proxy would be my rule wearing
  someone else's name.
- **The practitioner.** A discretionary method executed by the person who built
  it is not the same object as its rules run mechanically. Nothing here speaks to
  that.
- **Anything outside NQ, 2010–2024.** One instrument, one period. Parts of the
  source material are about forex and were not tested at all.

### The honest scope of every result below

> *These specific mechanised formulations, tested mostly in isolation, on NQ
> futures, over this period, in my implementation, did not show a measurable
> edge at this significance bar.*

Every qualifier in that sentence is doing work.

---

## What the measurements showed

| tested claim | source | measurement |
|---|---|---|
| A fair value gap is revisited | 36 of 41 episodes | Gaps were revisited **less** often than a matched same-size, same-hour, same-direction move retraced the same distance. 16/16 tests, z to −59.9 |
| An order block is a level price reacts from | 20 of 41 | No measurable reaction on return, across 60,000+ events |
| A liquidity sweep reverses | 16 of 41 | Held on development data (z = +3.10), **did not replicate** out of sample (z = −0.15) |
| 08:30–11:00 is a distinct window | ep02 | **It is the most volatile window of the day — and that held out of sample.** The stronger claim, that it is the *cleanest*, held in development and did not replicate |
| A 15:00–16:00 on-close effect | ep32, ep05 | Correct window, correct sign against published research, too weak on NQ to clear the bar |
| Displacement magnitude matters | ep05 | Flat across every threshold tested |
| Each gate in the entry sequence adds value | ep41 | In my implementation, none improved what passed it |

One result deserves stating on its own: **the series independently identifies the
15:00–16:00 window in which a documented cross-asset anomaly lives** — *market
intraday momentum*, Journal of Financial Economics 2021, across 60+ futures,
1974–2020. The sign matched. The magnitude on NQ was too small to trade.

Full reasoning, including where I got things wrong:
[`backtest/findings.md`](backtest/findings.md).

---

## Why the method is the point

Most claims about trading methods — for and against — are argued from examples.
Examples prove nothing: you can always find a chart where a gap filled. The work
here is in making a measurement *trustworthy*.

**1. The control decides everything.** An early version compared rules against
*random days* and produced z = −18.6 — which turned out to measure volatility
autocorrelation, not the rule. Volatile days have wider mornings. Every control
is now matched on the confound: hour, move size, and direction.

**2. Time-of-day claims need time-of-day controls.** Intraday volatility is
U-shaped, so *any* rule saying "trade the morning, skip lunch" beats a random
control while carrying no information. Clock claims are ranked against other
windows of the same length on the same sessions.

**3. Counting hypotheses.** [`backtest/ledger.md`](backtest/ledger.md) records
every test ever run, failures included. At n = 154 a result needs |z| > 3.0, not
the conventional 2.0 — following Harvey, Liu & Zhu on multiple testing.

**4. Holding data back.** Split before any testing: `dev` (2010–2021),
`reserve` (2023–2024), `holdout` (2024–2026).
[`backtest/slices.py`](backtest/slices.py) *refuses* the holdout without an
explicit unsealing that writes a permanent record. **It was never opened** — it
exists to adjudicate a candidate that survived everything else, and none did.

**5. Pre-registration.** Both hypotheses taken to `reserve` were written down
before the script that tested them existed.

**The bugs are documented too**, because they are part of the reasoning: a
look-ahead in the entry sequence, a dedup key that silently inflated the
hypothesis count from 86 to 213, a z = 9.5e13 produced by an inverted control
group, and an optimal-trade-entry threshold I imported from outside the source
and recorded as though the series had stated it.

---

## Repository map

| path | what |
|---|---|
| [`study/`](study/) | 41 structured episode analyses, every line traceable to a timestamp |
| [`THE-MODEL.md`](THE-MODEL.md) | the methodology synthesised across episodes |
| [`DECISIONS.md`](DECISIONS.md) | every methodological ruling with its reasoning — 25 sections |
| [`backtest/findings.md`](backtest/findings.md) | the results and the reasoning over them |
| [`backtest/`](backtest/) | slices, matched nulls, the ledger, each experiment |
| [`bars/`](bars/) | raw market data → clean session-aligned bars |
| [`PLAN.md`](PLAN.md) | the research plan and the outside literature behind it |

## Not in this repository

- **Market data.** Databento GLBX.MDP3 NQ futures, purchased under a licence that
  does not permit redistribution.
  [`data/README-NQ-databento.md`](data/README-NQ-databento.md) records the exact
  query, so anyone with their own copy can reproduce this.
- **Video transcripts.** Caption tracks belonging to their author. The analysis in
  `study/` is original writing with short quotations for commentary; the
  wholesale source is not included.
- Credentials, and anything a script can rebuild.

## Reproducing

Python 3.12 with `databento`, `pandas`, `numpy`, `pyarrow`, and your own
Databento NQ export.

```
python bars/build_bars.py          # raw DBN -> clean midnight-New-York bars
python backtest/slices.py          # confirm the calendar; holdout refuses to load
python backtest/fvg_study.py
python backtest/run_clock.py
python backtest/primitive_study.py
```

Each script writes its own ledger rows and is idempotent.

---

## In one paragraph

A widely-taught trading methodology was read closely, written down precisely
enough to be checkable, and the mechanisable parts of it were measured against
15.7 years of futures data with pre-registration, matched controls, a counted
hypothesis budget and held-out data. **The isolated components did not show a
measurable edge in this implementation.** That is a narrow result about
mechanised primitives — not about the method as taught, or as practised by
someone applying judgement — and the distinction is kept deliberately throughout,
because the parts that resist mechanisation are the parts the source says matter
most.
