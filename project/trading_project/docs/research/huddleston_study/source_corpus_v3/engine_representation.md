# Engine representation — DESIGN ONLY, no code

Purpose: describe how a deterministic program *could* represent the ideas that the claims actually
support. This document implements nothing and asserts nothing about profitability.

Two labels are used strictly:

- **GIVEN** — the idea is directly carried by a cited claim. The claim, not this document, is the
  authority.
- **ENGINEERING_HYPOTHESIS** — anything not directly given by a claim (in particular: how to detect
  something on candles). Each lists the claim_ids it is derived from and is marked
  **needs owner approval**. It is *never* presented as his method.
- **OWNER_DECISION_NEEDED** — a number would be required. No number is chosen here.

All shapes are expressed **relative to market structure** (this swing vs that swing, inside that
range), never in pips, points, percentages or fixed bar counts, because the sources give none.

---

## 1. Narrative / draw state

**GIVEN** — the first question is the current market narrative and what price is likely doing now
[C001, C002]; the alternatives are up for stops / down for stops / rebalance [C003, C043]; "next draw
on liquidity" is how he names where price is going next [C005].

Representation: a state variable `narrative ∈ {up_for_stops, down_for_stops, rebalance, undecided}`
plus a reference to the swing or imbalance the narrative points at. `undecided` is a first-class value
because he explicitly holds it [C036, C037].

**ENGINEERING_HYPOTHESIS** (derived from C003, C005, C042, C045; **needs owner approval**) — enumerate
candidate draws as the set of prior swing extremes and unrebalanced ranges visible on the framing
chart, then require an external decision to pick one. The sources do not give an enumeration or
ranking procedure.

**OWNER_DECISION_NEEDED** — ranking rule when two candidate draws compete (OQ-10).

---

## 2. Timeframe hierarchy

**GIVEN** — the daily is treated as the parent and lower-timeframe swings are subordinate to it
[C013]; most study time goes to the daily's next day or two [C020]; he names a 5-day horizon for a
developing student [C021]; the 15-minute gives the actual get in / get out [C025]; the example's chart
is 1 hour [C007].

Representation: an ordered list of chart scales with a `parent` pointer, and a rule that a
lower-scale observation may not override the parent's narrative. Scale-free: only the *ordering*
matters, not the specific minutes.

**ENGINEERING_HYPOTHESIS** (derived from C013, C025; **needs owner approval**) — model the hierarchy as
a tree where each node stores its own swings and inherits the parent's narrative; conflict between
scales resolves in favour of the parent. The sources state subordination but do not state a conflict
algorithm.

**OWNER_DECISION_NEEDED** — whether the 5-day horizon is a rule or example-specific (OQ-12); which
scales to instantiate.

---

## 3. Swing labelling

**GIVEN** — structure is long-term high/low, short-term high/low, intermediate term high/low between
two swing points [C006]; an intermediate term high is either a short-term high with lower short-term
highs on both sides [C027] or a swing that trades back up to rebalance an imbalance [C028]; the mirror
case for lows [C012]; once labelled, price should not trade above that high [C053].

Representation: `Swing{kind: long|intermediate|short, direction: high|low, cause: neighbour_test |
rebalance_of_imbalance, violated: bool}`. The `cause` field preserves the two classifications instead
of collapsing them.

**ENGINEERING_HYPOTHESIS** (derived from C006, C012, C027; **needs owner approval**) — detect a
short-term swing extreme as a local extremum relative to its neighbouring extremes on the same scale.
The sources never define a bar count or a lookback.

**OWNER_DECISION_NEEDED** — neighbourhood size / lookback (OQ-07); wick-vs-close tolerance for
`violated` (OQ-08).

---

## 4. Imbalance / fair value gap and rebalance

**GIVEN** — a fair value gap is a range in price delivery where one side of market liquidity is
offered, typically confirmed with a lower-timeframe liquidity void [C049]; rebalancing an old
imbalance creates the swing he labels intermediate [C010, C028]; price delivery reduces to imbalance,
rebalance, run for liquidity [C043]; gaps can be hunted inside an order block range [C018]; the
example refers to the discount level of the low end of a gap [C054].

Representation: `Range{low, high, rebalanced: bool, parent_zone}` with `rebalanced` flipping when price
returns into the range. Everything is expressed as a range on the chart, never a size threshold.

**ENGINEERING_HYPOTHESIS** (derived from C049, C018; **needs owner approval**) — detect the range from
a three-candle arrangement whose middle candle spans a gap between the outer candles' extremes, and
mark `rebalanced` on any subsequent trade into it. The stored text describes the *idea* and a
lower-timeframe confirmation, not a candle formula. Phase 3 deliberately contains no candle formulas;
this stays a hypothesis.

**OWNER_DECISION_NEEDED** — what fraction of the range counts as rebalanced; minimum range size;
whether lower-timeframe confirmation is mandatory (all unanswered in the sources).

---

## 5. Order block

**GIVEN, with an unresolved contradiction** — Episode 12: one consecutive series of up closed candles,
explicitly not the last candle before the down move [C017, C016]; OB16: the lowest down-close candle
with the most open-to-close range near support, validated when a later candle trades through its high
[C047, C048]. Recorded as [C050]; **not resolved**.

Representation: `Zone{definition_id: series_2022 | single_candle_2016, low, high, validated: bool}`.
The program must carry `definition_id` explicitly and refuse to silently pick one.

**ENGINEERING_HYPOTHESIS** (derived from C017, C035, C048; **needs owner approval**) — for
`series_2022`, group maximal runs of same-direction closes preceding a displacement; for
`single_candle_2016`, select the extreme down-close candle by open-to-close range within a lookback
and mark validated on a later trade through its high.

**OWNER_DECISION_NEEDED** — which definition governs (OQ-04); what terminates a run (OQ-05); the
lookback and the meaning of "near a support level".

---

## 6. Entry, stop, target

**GIVEN** — two entry variants: aggressive without a swing low being broken [C029], and the classic
return back to an order block after trading below it [C030]; stop above that candle's high in the
example [C031]; the long-term high/low range is used for targeting [C019]; the example anchors a fib
from the intermediate term high to the long-term low [C023] and reads -1 1/2 standard deviation
[C024].

Representation: `Setup{entry_variant, zone_ref, stop_ref: swing_extreme, target_candidates: [...]}`.
`target_candidates` is a **list**, because the sources give more than one and do not rank them.

**ENGINEERING_HYPOTHESIS** (derived from C029, C030, C031; **needs owner approval**) — express the stop
as "beyond the extreme of the candle that produced the entry trigger", i.e. structurally rather than
as a distance. Express targets as projections of a structure-defined range so they stay scale-free.

**OWNER_DECISION_NEEDED** — target selection when candidates disagree (OQ-11); whether -1 1/2 is a
rule or an example value (OQ-12); partial exits (OQ-13).

---

## 7. Invalidation and standing aside

**GIVEN** — violation of the key high/low means the idea is wrong and is cancelled [C032]; do not
force it again [C051]; wait for market structure to get back in sync [C052]; a stop-out is risk
management, not evidence the model is flawed [C015]; neutral / do nothing is an explicit state
[C036, C037]; having time and an open account does not justify acting [C040]; in the example he stands
aside for the rest of February [C041].

Representation: a state machine `idea → active → {cancelled | neutral}` where `cancelled` cannot
self-transition back to `active`; re-arming requires an external event that the sources do not define.

**ENGINEERING_HYPOTHESIS** (derived from C032, C052, C053; **needs owner approval**) — re-arm only when
a new intermediate-term swing forms in the direction of the parent narrative. This is a guess about
"back in sync" and is explicitly not his stated rule.

**OWNER_DECISION_NEEDED** — the re-arm criterion (OQ-14); whether reversal is allowed (OQ-15); any
stand-aside duration.

---

## 8. What the engine must refuse to represent

Because no claim supports them, the design must leave these **absent**, not defaulted:
dealing range, premium, equilibrium, equal lows, session/kill-zone time gates, position sizing, risk
percentage, news handling. `time of day` is asserted as vital [C044] but **no window is given**, so the
design contains a `time_gate = NULL` placeholder and a blocking question (OQ-17) rather than an
invented session.

---

## Approval ledger

| item | label | derived from | state |
|---|---|---|---|
| candidate-draw enumeration | ENGINEERING_HYPOTHESIS | C003, C005, C042, C045 | needs owner approval |
| timeframe conflict resolution | ENGINEERING_HYPOTHESIS | C013, C025 | needs owner approval |
| swing-extremum detection | ENGINEERING_HYPOTHESIS | C006, C012, C027 | needs owner approval |
| gap detection + rebalance flag | ENGINEERING_HYPOTHESIS | C049, C018 | needs owner approval |
| order-block grouping / validation | ENGINEERING_HYPOTHESIS | C017, C035, C048 | needs owner approval |
| structural stop + projection targets | ENGINEERING_HYPOTHESIS | C029, C030, C031 | needs owner approval |
| re-arm after cancellation | ENGINEERING_HYPOTHESIS | C032, C052, C053 | needs owner approval |
| draw ranking, lookbacks, tolerances, gap thresholds, target choice, -1 1/2 status, stand-aside duration | OWNER_DECISION_NEEDED | — | no number chosen |
