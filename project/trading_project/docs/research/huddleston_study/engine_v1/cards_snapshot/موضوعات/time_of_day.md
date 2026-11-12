# Time of day: killzones and minute groups

Every content line ends with the claim id(s) that support it. Fields the sources do not answer are marked `NOT_IN_SOURCES`.

## Essence

- A killzone is a precise multi-hour sub-window of a trading session during which ICT teaches the highest-probability setups occur, defined in NY time. (CLM-0031)
  > "A killzone is a precise multi-hour sub-window of a trading session during which ICT teaches the highest-probability setups occur — defined in NY time"
  > source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE — Definition section

## Properties

- Table row: NY AM killzone window 08:00 – 11:00 (NY time), parent session NY AM. (CLM-0076)
  > "| NY AM | 08:00 – 11:00 | NY AM |" — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
- Table row: London Open killzone window 02:00 – 05:00, parent session London. (CLM-0077)
  > "| London Open | 02:00 – 05:00 | London |" — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
- Table row: NY PM killzone window 13:30 – 16:00, parent session NY PM. (CLM-0078)
  > "| NY PM | 13:30 – 16:00 | NY PM |" — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
- Outside killzones (e.g. mid-morning Asia, 06:30 NY post-London-open, NY Lunch) the library calls it low-probability for new setups. (CLM-0033)
  > "Outside killzones (e.g. mid-morning Asia, 06:30 NY post-London-open, NY Lunch): low-probability for new setups." — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
- The hour is divided into time groups that determine entry quality. (CLM-0073)
  > "The hour is divided into time groups that determine entry quality" — noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
- Group 1 is XX:01, XX:02 and is described as entry minutes, sniper entries. (CLM-0074)
  > "**Entry minutes** — Sniper entries" — noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
- Group 2 is XX:06, XX:07, XX:08 and is described as shift minutes where most shifts in Market Structure occur. (CLM-0075)
  > "**Shift minutes** — Most shifts in Market Structure occur here" — noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
- Silver Bullet is a one-hour window around 10:00 am New York time. (CLM-0089)
  > "**Silver Bullet** — a one-hour window around 10:00 am New York time when liquidity grabs and reversals are statistically more common." — propnavi.io (harvest web record) | web/pages/009_propnavi.io_ict-trading-strategy.md | no individual byline in the retrieved page; site "PROP NAVI" | EXPLAINER

## Relations

- Behavioral signature listed: frequent sweeps + displacement + FVG sequences. (CLM-0032)
  > "Frequent sweeps + displacement + FVG sequences." — SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE

## Context

- Killzones listed as London, NY AM, NY Lunch, NY PM. (CLM-0091)
  > "Killzones — London, NY AM, NY Lunch, NY PM" — nqbacktest.online (harvest web record) | web/pages/004_nqbacktest.online_inner-circle-trader.md | no individual byline; site "NQ Replay / nqbacktest.online" | EXPLAINER

## What it is chosen over

- CONFLICTED (CF-04)

## What invalidates it

- NOT_IN_SOURCES

## Worked examples in the sources

- NOT_IN_SOURCES

## All claims tagged to this concept

- `CLM-0031` [DEFINED] A killzone is a precise multi-hour sub-window of a trading session during which ICT teaches the highest-probability setups occur, defined in NY time.
  - quote: "A killzone is a precise multi-hour sub-window of a trading session during which ICT teaches the highest-probability setups occur — defined in NY time"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
  - location: Definition section
- `CLM-0032` [DEFINED] Behavioral signature listed: frequent sweeps + displacement + FVG sequences.
  - quote: "Frequent sweeps + displacement + FVG sequences."
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
  - location: Formal Criteria -> Behavioral signatures
- `CLM-0073` [DEFINED] The hour is divided into time groups that determine entry quality.
  - quote: "The hour is divided into time groups that determine entry quality"
  - source: noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
  - location: section 1.1 'The Minute Groups' (first 1400 chars read)
- `CLM-0074` [SAID] Group 1 is XX:01, XX:02 and is described as entry minutes, sniper entries.
  - quote: "**Entry minutes** — Sniper entries"
  - source: noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
  - location: section 1.1 table rows
- `CLM-0075` [SAID] Group 2 is XX:06, XX:07, XX:08 and is described as shift minutes where most shifts in Market Structure occur.
  - quote: "**Shift minutes** — Most shifts in Market Structure occur here"
  - source: noahbate/ict-forum-time-wisdom@36fd36b9 | TIME_REVELATIONS_FULL.md | noahbate | BOOK_OR_COURSE
  - location: section 1.1 table rows
- `CLM-0076` [DEFINED] Table row: NY AM killzone window 08:00 – 11:00 (NY time), parent session NY AM.
  - quote: "| NY AM | 08:00 – 11:00 | NY AM |"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
  - location: Formal Criteria table
- `CLM-0077` [DEFINED] Table row: London Open killzone window 02:00 – 05:00, parent session London.
  - quote: "| London Open | 02:00 – 05:00 | London |"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
  - location: Formal Criteria table
- `CLM-0078` [DEFINED] Table row: NY PM killzone window 13:30 – 16:00, parent session NY PM.
  - quote: "| NY PM | 13:30 – 16:00 | NY PM |"
  - source: SrsBlack/ict-knowledge-library@9b089669 | concepts/10-killzones/killzone-overview.md | SrsBlack | BOOK_OR_COURSE
  - location: Formal Criteria table
- `CLM-0089` [SAID] Silver Bullet is a one-hour window around 10:00 am New York time.
  - quote: "**Silver Bullet** — a one-hour window around 10:00 am New York time when liquidity grabs and reversals are statistically more common."
  - source: propnavi.io (harvest web record) | web/pages/009_propnavi.io_ict-trading-strategy.md | no individual byline in the retrieved page; site "PROP NAVI" | EXPLAINER
  - location: web record, quote 7 of 10
- `CLM-0091` [SAID] Killzones listed as London, NY AM, NY Lunch, NY PM.
  - quote: "Killzones — London, NY AM, NY Lunch, NY PM"
  - source: nqbacktest.online (harvest web record) | web/pages/004_nqbacktest.online_inner-circle-trader.md | no individual byline; site "NQ Replay / nqbacktest.online" | EXPLAINER
  - location: web record, quote 5 of 10
