# TASK 4 — GAPS

Everything here is a gap, not an answer. Nothing below is filled from memory.

## 1. Deixis: "here", "this high", "that low" without a named level

This is the dominant gap in the corpus and it is structural, not incidental. He narrates against a
chart the reader cannot see. Concrete instances from windows read this session:

| claim | wording | what is missing |
|---|---|---|
| `U0051` | "even though this is not an order block by" | the criterion after "by" is outside the window — the actual rejection rule is unrecovered |
| `U0045` | "the order block really begins at this candle's opening not this last one" | which candle is "this" — needs the chart image |
| `U0071` | "i want to use this most recent one and this is my dealing range" | which two legs were on screen |
| `U0063` | "which one's the shift in market structure well i'm playing the run up here" | the two candidate breaks are not identified in text |
| `W0335` (pairing) | "we have a higher low and then we have this low here so we Wick down into this" | three separate deictic lows, none named |
| `W0347` (pairing) | "between the scandals high and this candle is low" | which candle; also an ASR corruption |
| `U0009` | "Right Above This high would be buy side liquidity" | the high is not named |

**Only a chart image would settle these.** The transcripts carry `RefLink` YouTube URLs with
`&t=` seconds, so the frame is in principle locatable — but frame extraction was out of scope and was
not run.

## 2. Concepts with no comparison language found in the windows read

`purpose` is empty for most cards (7 purpose claims across 21 concepts). Concepts where no
comparative/preference statement was recovered at all:

- `equilibrium` — he defines and locates it, never ranks two equilibria in the windows read.
- `being_wrong` — no ranking of two ways of being wrong.
- `time_of_day` — overlap is described, but no statement of which window wins over another.
- `sell_side_liquidity` has comparative wording about persistence but none ranking two pools.
- `stop_loss` compares order types, not two candidate stop levels.

## 3. Conflicts kept parallel (never merged, never averaged)

1. **Order block start** — `U0045` "really begins at this candle's opening not this last one" vs
   `U0046` "this last up candle that's the bearish order block". Both quoted. Unresolved.
2. **London kill zone start** — `U0088` "begins at 1am New York time" vs `U0089`/`U0090` "two o'clock"
   / "2 a.m.". Both quoted. Unresolved. Note `U0094` explicitly *declines* to call the New York session
   a kill zone at all, and `U0092` gives a wider 8:30 window as "not the ict new york kill zone".
3. **Break-even trigger** — `U0114` "after first profit is taking never before" vs `U0115` "at 75% of
   the expected profit objective stop must be at break even"; and `U0112`/`U0113` say to *resist*
   moving to break even on higher time frames. Three positions, all kept.
4. **"premium"** — range position (`U0082`) vs carrying-charge market (`U0087`). Same word, different
   observable; the second needs contract data, not candles.

## 4. What only a chart image (or the video) would settle

- Every deictic reference in §1.
- Whether "very clean equal highs" (`U0022`) means near-identical price, few intervening bars, or both.
- What "energetic" displacement looks like relative to neighbouring candles (`U0055`) — he gives the
  contrast ("lethargic") but no measurable criterion.
- Which of two fair value gaps he favoured (`U0040`) — the preference is stated, the two objects are not.
- What the "logical levels" for partials are in a given instance (`U0120`).

## 5. Per-concept unknowns that block a deterministic recogniser

| concept | the specific unknown |
|---|---|
| `order_block` | the rejection criterion cut off at "not an order block by" |
| `displacement` | no measurable definition of energetic; only a contrast |
| `shift_in_market_structure` | no tie-break when two candidate breaks exist |
| `dealing_range` | "market structure has provided a means for a trading opportunity" is not reduced to candles |
| `fair_value_gap` | his "five handles" remark is chart-specific; generalising it would be invention |
| `partials` | quantity explicitly left to the trader (`U0118`, `U0119`) — no number exists to recover |
| `kill_zone` | conflicting bounds; also a stated refusal of the label for New York |
| `bias` | non-exclusive: a bias to buy does not forbid the other side working (`U0103`) |
| `risk` | no single percentage he applies universally; the 2% remark is a warning about exceeding it |
| `being_wrong` | he says to identify the characteristics, but does not enumerate them in the windows read |

## 6. Coverage gaps of this session (not of the corpus)

- 66 concepts were selected in `kept_concepts.tsv`; **21** received cards. The other **45** are
  deferred, not absent — including `breaker`, `mitigation_block`, `rejection_block`,
  `consequent_encroachment`, `optimal_trade_entry`, `imbalance`, `inefficiency`, `liquidity_void`,
  `turtle_soup`, `silver_bullet`, `judas_swing`, `smt_divergence`, `market_maker`, `mean_threshold`,
  `ipda`, `data_range`, the swing-hierarchy terms and `money_management`.
- Task 2 mined 3000 comparative windows mechanically but only **18** were reduced to
  things_compared/which_wins records; the rest are uninterpreted in `comparisons_raw.jsonl`.
- Task 3 detected 71 dated candidates; only 13 got pairing cards and only 6 are EURUSD-usable.
- 76 card sections are `NOT_IN_SOURCES`. The thinnest cards are `risk` (6 empty), and
  `being_wrong`, `break_even`, `equilibrium`, `kill_zone` (5 each).
