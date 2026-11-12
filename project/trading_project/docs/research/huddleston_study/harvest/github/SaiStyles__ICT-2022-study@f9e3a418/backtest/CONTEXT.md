# backtest - where the model finally gets to be wrong

One job: test the rules in `../THE-MODEL.md` against `../bars/output/`, and **count every
attempt**, including the rubbish ones.

## Read before touching anything here

`../DECISIONS.md` sections **3** (the backtester is the consumer), **4** (hypothesis
ledger), **17** (the ledger is a file), **20** (NQ only), **21** (price-data handling).

## The two defences. Both start now or they are worthless.

Section 17 is blunt about this: **neither can be retrofitted.** You cannot reconstruct how
many things you tried, and you cannot un-look at data.

### 1. `ledger.md` - one row per hypothesis ever tested

Every run. The failures especially. Run 500 rule combinations and dozens will show
excellent returns from **pure chance** - that is arithmetic, not bad code. A result is
uninterpretable without the count that produced it.

**Write the row at the time, every time.** Memory fails in one specific direction here: it
keeps the winner and quietly deletes the forty failures. That is not carelessness, that is
how remembering works.

### 2. The holdout - sealed, and enforced by code

`slices.py` owns the calendar. It will not hand out the holdout without an explicit
unsealing that **writes a permanent record to `holdout_opened.md`**. That is deliberate:
a rule that depends on remembering a rule is not a rule.

| slice | dates | what it is for |
|---|---|---|
| `dev` | 2010-06-06 -> 2021-12-31 | **free rein.** Sweep, iterate, break things |
| `corpus` | 2022 | **sanity only.** Does the machinery find the setups he points at? |
| `reserve` | 2023-01-01 -> 2024-02-29 | **one look**, after dev is frozen |
| `holdout` | 2024-03-01 -> 2026-02-25 | **sealed.** Opened once, at the very end |

**Why 2022 can never produce a performance number.** The rules were derived by watching him
trade 2022. Measuring them on 2022 is measuring how well we transcribed him. It is a
**wiring check** - if the gates cannot find the ep06 or ep07 setup, the code is broken -
and it is never evidence of edge.

**Why the holdout is the most recent two years**, not a random slice: it is the closest
thing on disk to the conditions the model would actually meet next.

## The build order - vetoes, then money, then entries

Ruled after reading all 41 episodes. Not the obvious order, and it is deliberate.

1. **Vetoes first.** Lunch, no-Judas days, consolidation days, the overnight-run rule
   (ep09 [15:15]). Ep41's closing note: **the single most repeated behaviour across the
   corpus is refusing to trade** - ep13, 21, 24, 27, 30, 32, 36, 38, 41. If the edge lives
   anywhere, the corpus says it lives here.
2. **Money management second.** The ep41 ladder - 1% -> 0.5% -> 0.25%, restore after
   recovering half the loss. **Pure arithmetic, no prediction.** It can be measured against
   flat sizing without any entry model being correct, which makes it the cheapest real
   result available.
3. **Entry gates last**, even though it is the fun one. It is the largest surface for
   inventing something he never said.

## Gates are booleans, and every rejection is logged

A candidate walks a hallway of doors; each asks one yes/no question; **the door that stops
it is recorded.** That is not bookkeeping - it is the measurement ep24 asks for:

> `this is the proof, the evidence that the model has validity`

Without per-gate rejection counts you cannot tell a filter from decoration. With them you
can say "G4 rejected 340 candidates, and those candidates went on to lose 71% of the time."

**Yes/no, never a score.** He never says a setup is 7 out of 10; he says no displacement,
no trade. A weighted score would be a system he does not have.

**Where a threshold genuinely does not exist** - "meaningful displacement" is the known case
(`THE-MODEL.md` 8.1, researched and found to have no canonical value) - the gate takes a
**parameter that gets swept**, and every point of the sweep is its own ledger row. Do not
fake crispness; make the fuzziness measurable.

## Contested items are variants, not decisions

`THE-MODEL.md` section 7 lists five places the corpus contradicts itself. **Do not resolve
them by preference.** Each becomes two configurations and the ledger records both.

## Human check

Open `ledger.md`. Does `n` match the number of results anyone has talked about? If someone
can describe a result that has no row, **the ledger has already failed** and the count is
no longer usable for judging anything.
