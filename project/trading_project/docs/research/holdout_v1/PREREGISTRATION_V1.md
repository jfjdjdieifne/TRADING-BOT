# PRE-REGISTRATION `V1` — `HOLDOUT_V1`

**Status: FROZEN BEFORE ANY RUN. No window has been read under this file.**
**Dependency:** valid only if `OWNER_DECISION_D3.md` is signed. Until then this file is inert
and reads as a plan, not as an authorisation.

**Freeze mechanism:** this text is frozen by the commit that adds it. Any change after a
window is read is a **new file** (`PREREGISTRATION_V2.md`) committed before the next window
is opened; `V1` is never edited. A window opened under `V1` is reported under `V1` even if
`V2` later supersedes the definitions (`D3` clause A.3).

**Number discipline.** Every quantity below carries one of:

| tag | meaning |
|---|---|
| `SOURCE_NUMBER` | printed in a source, or an existing constant already in the tree (code constant, or owner-supplied date) |
| `ENGINEERING_CHOICE` | chosen here, **before** any run, for a stated non-performance reason, and frozen |
| `KNOWLEDGE_GAP` | no number; printed as a gap, never filled |
| `CALLER_INPUT` | supplied by the caller at run time; **no default exists in this file**, and the run refuses rather than substitutes one |

No number below was chosen after seeing a result, because no result exists.

---

## 1. Purpose and the one sentence that governs the phase

The phase measures three things that are separable, and reports them separately:

1. **Level 1** — reading / selection: when the reader picks one object out of `N` observable
   alternatives, was the pick *relatively* better than the alternatives by an ex-ante
   baseline declared in §4?
2. **Level 2** — plan mechanics: what happens mechanically to a hypothetical plan built on
   that pick, measured in `R` and in pips, with costs from the bid/ask data. §5.5 and §5.6 add
   two descriptions that an owner who executes manually actually needs: the size of the
   sequence in `R`, and how much the answer moves when the entry is not instantaneous.
3. **Level 3** — split into two non-substitutable parts (§6):
   **`3-MECH`**, mechanical verification by code of every factual claim the engine makes in a
   snapshot (no expert, no opinion, runs now), and **`3-JUDGE`**, interpretive correctness,
   which requires a qualified domain expert and is therefore `NOT_ESTABLISHED`.

### 1.1 Execution model this phase assumes

The engine is **not** connected to any account and no order is ever sent. The engine emits
recommendations; a human executes them manually. Consequences, fixed now:

- **no `fill` is ever asserted** — there is no execution to observe, so a filled order is not
  a fact that exists in this project (`D3` clause B keeps `fill` forbidden);
- every price is `HYPOTHETICAL_`, every `R` is the `R` of a hypothetical sequence;
- manual execution introduces latency, so §5.6 measures entry delay instead of assuming it
  away;
- the owner is the executor, **not** a judge: §6.2 keeps `3-JUDGE` at `NOT_ESTABLISHED` even
  though the owner will look at outputs as an operator.

**The governing sentence of this phase:**

> **A small judgeable sample is a valid, publishable outcome.** An evaluation that yields 40
> judgeable decisions out of 4,000 observations is reported as *40 judgeable decisions*, with
> its counts, and is not withheld, padded, re-run, or described as "insufficient data" to
> justify a second look. The only invalid outcome is a hidden one.

Level 1 and Level 2 are *not* interchangeable and may not be pooled. A better reading metric
does not rescue a plan metric, and a plan metric does not validate a reading.

---

## 2. Windows

### 2.1 The windows

| # | instrument / timeframe | role | window | tag |
|---|---|---|---|---|
| W1 | EURUSD 5m bid + ask | development | `2021-01-01` .. `2022-01-01` | `SOURCE_NUMBER` (owner-confirmed) |
| W2 | EURUSD 5m bid + ask | **blind evaluation, single run** | `2024-01-01` .. `2025-01-01` | `SOURCE_NUMBER` (owner-confirmed) |
| W3 | BTCUSDT 1m | second window, months **drawn by the procedure of §2.3** from `2020-01` .. `2024-12` | `2022-02`, `2022-09`, `2022-11`, `2023-09`, `2023-11`, `2024-07` — drawn in §2.3 (listed here chronologically; the draw order is the rank order there) | `ENGINEERING_CHOICE` (seed + count) |

Rules attached to the windows:

- **W2 is read once.** No tuning of any kind may pass through W2. A run on W2 is published
  regardless of outcome (`D3` A.2).
- **W2 is owner-confirmed unseen.** The owner states he has not viewed EURUSD `2024-01-01` ..
  `2025-01-01`. The obligation in §2.2 exists so that this stays true until the run.
- **W3 is owner-confirmed unseen.** The owner states he has not viewed any BTCUSDT month other
  than `2025-08` / `2025-09`. Every drawn month is outside those two, and `2025-08` / `2025-09`
  are excluded from the draw range by construction (the range ends `2024-12`).
- **`2026-05`** is outside the draw range and therefore cannot be drawn. Separately, an
  earlier read-only audit of this repository recorded `2026-05` as already used in an
  evaluation context. The owner's viewing state for that data is **UNKNOWN (not answered)**:
  no statement exists in which the owner says whether he viewed it, so this file does not and
  may not claim that he did not. The item is excluded by range, not by this note.
- W1 and W3 exist so that definitions can be broken without burning W2. They are never
  pooled with W2 in any aggregate; each window is reported alone, and no "combined" figure
  is produced.

### 2.2 Owner obligation and attestation (signed before W2 is opened)

The owner is the only person who can keep a window blind, so the obligation is stated as an
obligation and not as an assumption:

> **Obligation.** From the signing date until the single blind run of a window, the owner does
> not view charts of that window — not a single bar, not a screenshot, not a monthly summary
> chart, not an annotated version, and not a "quick look" to check that the data loaded.

If the owner does look, the honest options are only two: declare it (and the window is burned
for that purpose, per §8) or abandon the window. There is no third option in which an
un-declared look is still blind.

```text
OWNER ATTESTATION — HOLDOUT_V1
I attest that, as of the date below, I have NOT viewed:
  [ ] W2  EURUSD 2024-01-01 .. 2025-01-01
  [ ] W3  the six BTCUSDT months recorded in §2.3
and that I will not view either window before its single blind run.
I understand that viewing a window without declaring it makes that window's result
uninterpretable, and that a declared viewing burns the window.

Signed: ______________________   Date: ______________
```

Also recorded, as `OWNER_STATEMENT_IN_CHAT` (2026-11-09), because it is the only evidence the
project can have of the pre-existing state of the owner's eyes:

- EURUSD 2024 — not viewed. (This is what makes W2 blind; the attestation above preserves it.)
- BTCUSDT — no month viewed except `2025-08` / `2025-09`.
- BTCUSDT `2026-05` — owner's viewing state: UNKNOWN (not answered).

An `OWNER_STATEMENT_IN_CHAT` is **not verifiable by the project** and is recorded as a
statement, never as a measurement.

### 2.3 W3 month draw — the exact procedure, reproducible by hand

The months are **drawn now, before any data is loaded**, and recorded in this file. The
procedure is written so that it can be re-executed with nothing but `sha256sum` and `sort`.

Declared parameters:

```text
DRAW_ENTITY   = "BTCUSDT|HOLDOUT_V1|20261109|" + month     (ASCII, vertical bars, no spaces)
DRAW_SEED     = 20261109                 tag: ENGINEERING_CHOICE
CANDIDATE_SET = 2020-01 .. 2024-12       (60 months)       tag: ENGINEERING_CHOICE (range)
N_MONTHS      = 6                        tag: ENGINEERING_CHOICE
EXCLUDED      = 2025-08, 2025-09, and any month the owner later lists as seen
                (owner's seen-list at the time of this file: none)
```

**Algorithm, in plain words**

1. Write the 60 candidate months as `YYYY-MM`, from `2020-01` through `2024-12`.
2. For each month, build the exact text `BTCUSDT|HOLDOUT_V1|20261109|YYYY-MM` — no spaces, no
   trailing newline, ASCII only.
3. Take the SHA-256 of that text (its UTF-8 bytes) and write it as 64 lowercase hex digits.
4. Sort the 60 months by their hex string, ascending, comparing character by character.
5. Take the first `N_MONTHS` = **6** months of that sorted list. That is the drawn set.
6. A month tied on the full hex string (it cannot occur, but state it) would be broken by
   comparing the month label ascending.

**Result — recorded before any data was loaded**

| rank | month | sha256 of the draw string (first 16 hex) |
|---|---|---|
| 1 | `2022-11` | `021bf67d8c3c0c90` |
| 2 | `2022-02` | `06a46f524e0267c4` |
| 3 | `2023-11` | `07a3df7ce07758e4` |
| 4 | `2022-09` | `08a65e613d4831b1` |
| 5 | `2024-07` | `0968779698e7a4a6` |
| 6 | `2023-09` | `0af0101bbdfb9b68` |

Two honest notes about this draw, recorded rather than "fixed by re-drawing":

1. **The draw clusters.** Three of six months are in 2022. Re-drawing to spread them would be
   fitting the draw to a preference, which is exactly the move pre-registration exists to
   prevent. The clustering is a **limitation of W3** and is printed with every W3 result.
2. **A later owner seen-list forces a new file, not a new draw.** If the owner later names a
   month as seen, `PREREGISTRATION_V2.md` is written **before** the next load and re-draws with
   a new seed; the months already drawn stay recorded here as drawn, and the burned ones are
   marked burned. This file is never edited after a window is read.

---

## 3. Data and cost model (fixed now)

| item | value | tag | note |
|---|---|---|---|
| price source | 5m **bid** and **ask** series, closed bars only | `SOURCE_NUMBER` (data as published) | the two series are read together, never mid-only |
| bar convention | completion-labelled; a bar may not be used before its completion label | existing convention | matches `information_time.py` semantics |
| cost per decision | **half-spread** at the decision bar, applied adversely: long pays `+ (ask−bid)/2` on entry and on exit, short pays the same on entry and on exit | `ENGINEERING_CHOICE` | reason: it is the *minimum* defensible cost, so it cannot flatter the result; full-spread is run as the §8 sensitivity, not as a switch |
| commissions / swaps / funding | not present in the bid/ask source | `KNOWLEDGE_GAP: commissions and financing` | printed with every `R` aggregate as a limitation; no number is assumed |
| pip size — EURUSD | `0.0001` | `ENGINEERING_CHOICE` (unit convention) | a unit conversion, not a parameter; BTC window reports price units, not pips |
| risk unit `R` | `1 R = |HYPOTHETICAL_ENTRY − HYPOTHETICAL_INVALIDATION|` in price units, per decision | `ENGINEERING_CHOICE` | the distance is the engine's own invalidation, not a chosen number |
| episode horizon | `24` completed bars | `SOURCE_NUMBER` (existing constant `EPISODE_HORIZON_BARS = 24` in `decision_layer.py`) | reused, not re-chosen |

No number above is a market parameter, a threshold, or a performance claim. All are units,
costs, or a horizon already in the tree.

---

## 4. Level 1 — reading / selection metrics

### 4.1 Decision unit

One decision = one evaluation instant at which the existing kernel
(`expert_structural_reference_selection`, via `apply_expert_preferences`) returns
`SELECTED`. Instants returning `UNRESOLVED` are **counted** and are not decisions.

### 4.2 The candidate set (alternatives), exactly

The alternatives are **the eligible survivors the kernel itself considered at that instant** —
never a set re-created by this phase. Concretely, the objects are the existing classes:

| class | module | role in Level 1 |
|---|---|---|
| `csm.PointCandidate` | `contextual_selection/csm.py` | the referent objects (levels) |
| `csm.LegCandidate` | `contextual_selection/csm.py` | legs used by the role policies |
| `FVGRegion` | `contextual_selection/connected_readings.py` | zone carrier — **not yet in the pool**; see 4.5 |
| `study_links.OBLikeCandidate` | `contextual_selection/study_links.py` | zone carrier — **not yet in the pool**; see 4.5 |

`N` = the count of eligible survivors printed by the kernel at that instant. No candidate is
added, dropped, or re-scored by this phase.

### 4.3 The realised reference point, declared now

For each decision at bar `t`, the realised outcome is summarised by one price:

```text
P*(t) = close of the last completed bar at or before t + 24 completed bars
        (or the last completed bar inside the window, if the window ends first)
```

This is a deliberately blunt, single-point reference. It is declared now so that it cannot
be changed to one that flatters the reader. A richer path-based reference (`P*` as the
first-touch sequence) is explicitly **not** used in `V1`; it is listed as a `V2` candidate
and changing to it burns W2.

### 4.4 The metric

For each decision, and for each eligible candidate `c`:

```text
d(c) = |level(c) − P*(t)|            (absolute distance, price units)
r(c) = rank of d(c) among the eligible set, 1 = closest
```

Per-decision result:

```text
HIT_1(t) = 1 if r(chosen) = 1 else 0                      (binary, per decision)
RANK_REL(t) = r(chosen) / N                               (RELATIVE_ONLY; 1.0 = worst)
```

Aggregates over a window: **count of decisions**, mean `RANK_REL`, median `RANK_REL`, the
`HIT_1` proportion with a Wilson 95 % interval, and the full histogram of `r(chosen)` by `N`.

`95 %` (the interval level) and `Wilson` (the interval construction) are
`ENGINEERING_CHOICE`, declared now. The interval is reported, never used as a pass/fail gate.

### 4.5 The ex-ante baselines

Two baselines, both computed from information available at `t` only:

| baseline | rule | tag |
|---|---|---|
| `B_EARLIEST` | pick the eligible candidate with the **earliest** `knowable_bar`; if tied, `UNRESOLVED` (tie is never broken by array order) | `ENGINEERING_CHOICE` — reason: it uses no price information at all beyond eligibility, so it cannot encode hindsight |
| `B_UNIFORM` | pick uniformly at random among the eligible candidates, `100` seeded draws per decision, seeds `0..99`; report the mean and the 5th–95th percentile of the drawn `HIT_1` proportion | `ENGINEERING_CHOICE` — `100` draws and seeds `0..99` declared now |

`B_EARLIEST` is the primary declared baseline; `B_UNIFORM` exists to show the null spread so
that a single favourable-looking number cannot be read as skill.

**No threshold is declared for "beats the baseline".** The comparison is reported as two
proportions with intervals and the difference of the two with its interval. A reader may
judge; the phase does not.

### 4.6 Zone selection (Level 1b) — declared `NOT_AVAILABLE_V1`

"Candidate zones" (`FVGRegion`, `OBLikeCandidate`) are **not** in the selection pool today:
`apply_expert_preferences` receives candidate ids of points and legs only. Making zones
selectable is a new call site, designed in `PAIRWISE_SELECTION_DESIGN_V1.md` and **not built**
by this phase.

Therefore:

```text
LEVEL_1B_ZONE_SELECTION = NOT_AVAILABLE_V1
```

This is printed as a limitation of every Level 1 report. It is **not** replaced by using the
nearest FVG as a stand-in, because that substitution would silently answer the very question
the phase is supposed to leave open.

---

## 5. Level 2 — plan mechanics

Measured on the same decisions as Level 1, from the plan objects that already exist
(`trade_plan.py`: `create_plan`, `observe_plan`, `evaluate_plans`).

### 5.1 Counts (no interpretation, pure accounting)

| counter | definition |
|---|---|
| `PLANS_CREATED` | plans emitted |
| `PLANS_WITH_EXECUTABLE_GEOMETRY` | plans where `HYPOTHETICAL_ENTRY`, `HYPOTHETICAL_INVALIDATION`, `HYPOTHETICAL_TARGET` are all present and `R > 0` |
| `NO_JUSTIFIED_PLAN` | instants where the reader refused to build a plan — counted as a **result**, not a hole |
| `AMBIGUOUS` | instants where the kernel returned `UNRESOLVED` |
| `SAME_BAR_ORDER_UNKNOWN` | decisions where target and invalidation were both inside one bar's range |
| `CENSORED` | decisions where neither target nor invalidation was reached inside the horizon |
| `JUDGEABLE` | `PLANS_WITH_EXECUTABLE_GEOMETRY` minus (`SAME_BAR_ORDER_UNKNOWN` + `CENSORED`) |

`CENSORED` is reported beside `JUDGEABLE`, never inside it and never as zero, per K5 in
`OWNER_DECISION_D3.md` §2.

### 5.2 The path rule (declared now, one rule only)

```text
entry      : at the open of the bar after the decision bar, paying half-spread adversely
exit       : HYPOTHETICAL_TARGET reached  -> +target distance in R
             HYPOTHETICAL_INVALIDATION reached -> -1 R
             both inside one bar  -> SAME_BAR_ORDER_UNKNOWN (excluded from JUDGEABLE)
             neither by horizon end -> CENSORED
```

The target is the engine's own declared target component, not one this phase chooses. If a
plan has no target component, the plan is counted in `NO_JUSTIFIED_PLAN` territory and is not
scored.

### 5.3 Reported quantities

| quantity | definition | unit |
|---|---|---|
| `MEAN_R` | mean of `OUTCOME_R` over `JUDGEABLE` | `R` |
| `MEAN_R_CI` | Wilson-free normal interval? **No** — a percentile bootstrap with `2000` seeded resamples, seeds declared `0..1999` | `R` | 
| `SUM_R` | sum over `JUDGEABLE`, non-overlapping, sequential | `R` |
| `MAX_DRAWDOWN_R` | largest peak-to-trough fall of the cumulative `SUM_R` curve in decision order | `R` |
| `NEGATIVE_R_STREAK` | longest run of consecutive `OUTCOME_R < 0` (0 allowed as neutral, not negative) | count |
| `STREAK_DISTRIBUTION` | histogram: for each run length `1..L`, how many runs of that length occurred | count |
| `MEAN_PIPS` / `SUM_PIPS` | the same, converted via the pip convention | pips |
| `COST_PIPS` | mean half-spread paid per decision, both sides | pips |

`2000` bootstrap resamples and seeds `0..1999` are `ENGINEERING_CHOICE`, declared now.
`MAX_DRAWDOWN_R` and `NEGATIVE_R_STREAK` are measurements of a hypothetical sequence under
`D3` clause B; they are **not** a track record and carry the hypothetical tag on every line.

### 5.4 What Level 2 may not report

- no `WIN` / `LOSS` / `PnL` / `profitable` / `accuracy` / `edge` / `fill` — forbidden by
  `D3` clause B without exception;
- no equity curve in currency, no position sizing, no compounding;
- no ratio of wins to losses presented as a quality indicator;
- no comparison between windows;
- **no probability of anything** — not of reaching a drawdown, not of passing a program, not of
  a streak continuing. §5.5 is probability-free by construction;
- **no firm, broker, platform or program name**, and no reference to any external rule set;
- **no built-in risk default.** `TOTAL_LOSS_LIMIT` and `RISK_PER_TRADE` in §5.5 are
  `CALLER_INPUT`; this file contains no value for either, not even in an example, and a run
  without them refuses to compute that section.

### 5.5 `FUNDED_CHALLENGE_FEASIBILITY` — dev window only

**Window restriction:** computed from **W1 (development) only**. It is **never** computed on
W2 or W3. Reason: it is a description of the *size* of the sequence, not a result; running it
on the blind window would create a second consumer of the single look and would invite reading
the blind window twice.

**Inputs — `CALLER_INPUT`, no defaults, no examples with numbers:**

| input | meaning | constraint |
|---|---|---|
| `TOTAL_LOSS_LIMIT` | the fraction of the account at which the sequence would stop | `0 < limit <= 1` |
| `RISK_PER_TRADE` | the fraction of the account risked per decision | `0 < risk <= 1` |

If either is absent, the section prints `CALLER_INPUT_MISSING` and the rest of Level 2 is
unaffected. A default is never substituted — substituting one would be inventing the owner's
own risk policy for him.

**Computed and printed side by side (three numbers, no verdict between them):**

| quantity | definition | tag |
|---|---|---|
| `CAPACITY_CONSECUTIVE_NEGATIVES` | `floor(TOTAL_LOSS_LIMIT / RISK_PER_TRADE)` — how many consecutive negative decisions the input pair would tolerate before the limit is reached | arithmetic on `CALLER_INPUT` |
| `MEASURED_LONGEST_NEGATIVE_RUN` | the longest run of consecutive `OUTCOME_R < 0` in W1 (from §5.3) | measured |
| `MEASURED_MAX_DRAWDOWN_R` | the max peak-to-trough of the cumulative `R` curve in W1 | measured |
| `RUNS_OVER_CAPACITY` | how many of W1's negative runs have a length greater than `CAPACITY_CONSECUTIVE_NEGATIVES` | counted |
| `DD_OVER_CAPACITY` | 1 if `MEASURED_MAX_DRAWDOWN_R * RISK_PER_TRADE > TOTAL_LOSS_LIMIT`, else 0 | arithmetic |
| `DECISIONS_PER_MONTH` | count of judged decisions per calendar month in W1, plus the minimum and maximum month | counted |

Under the §5.2 path rule every negative outcome is exactly `−1 R`, so a run of `n` negatives
consumes `n × RISK_PER_TRADE` of the account and the capacity formula above is exact — not an
approximation and not a model.

**Why this is probability-free:** it reports *what happened*, in `R`, and *what a given input
pair would tolerate*, as arithmetic. It does **not** estimate the chance that a future sequence
resembles W1, does not simulate, does not resample outcomes, and does not say whether the
inputs are "safe", "aggressive", "recommended" or "enough". If the reader wants a probability,
this section deliberately gives none.

### 5.6 `MANUAL_EXECUTION_SENSITIVITY` — entry delay, measured not assumed

The owner executes by hand, so the plan's `next_open` entry is a modelling choice, not a fact.
This section re-runs the **same plans** with the entry moved later and reports the difference.

**Declared now, before the run:**

```text
K_DELAYS = {1, 2, 3}     additional completed bars after the baseline entry bar
                         tag: ENGINEERING_CHOICE  (k = 0 is the baseline, = §5.2 next_open)
```

**Rules (frozen):**

1. Entry for delay `k` is the **open** of completed bar `decision_bar + 1 + k`, paying
   half-spread adversely, exactly as §5.2 does for `k = 0`.
2. `HYPOTHETICAL_INVALIDATION` and `HYPOTHETICAL_TARGET` are **unchanged** from the decision
   time. The geometry is frozen; only the clock moves. This isolates timing.
3. If the invalidation is reached **before** the delayed entry, the decision is
   `DELAYED_ENTRY_INVALIDATED` — counted separately and **excluded** from the `R` comparison,
   because the setup died before it could be entered. It is not scored as `-1 R`.
4. If the target is reached before the delayed entry, the decision is
   `DELAYED_ENTRY_MISSED_TARGET` — counted separately, also excluded from the `R` comparison.
5. Everything else keeps the §5.2 path rule and the §5.3 censoring rules.

**Reported, per `k`, beside the `k = 0` baseline:**

| quantity | form |
|---|---|
| `N_SCORED(k)` | count |
| `MEAN_R(k)` minus `MEAN_R(0)` | signed difference in `R` |
| `MEDIAN_R(k)` minus `MEDIAN_R(0)` | signed difference in `R` |
| `MAX_DRAWDOWN_R(k)` minus `MAX_DRAWDOWN_R(0)` | signed difference in `R` |
| `NEGATIVE_R_STREAK(k)` minus `NEGATIVE_R_STREAK(0)` | signed integer difference |
| `DELAYED_ENTRY_INVALIDATED(k)`, `DELAYED_ENTRY_MISSED_TARGET(k)` | counts |
| outcome-class transition matrix | (baseline class → delayed class) counts |

**Differences only.** No pass/fail cutoff, no "acceptable slippage", no tolerance number, and
no statement that a given `k` is realistic — the project has no source for how fast the owner
executes, so every `k` is reported and none is endorsed.


---

## 6. Level 3 — split into `3-MECH` and `3-JUDGE`

Level 3 has two parts that are **not substitutable**, and the split is not cosmetic:

- **`3-MECH`** — mechanical verification, by code, of every *factual* claim the engine makes in
  a snapshot. It needs no expert, no opinion and no rubric, because every check is decidable by
  recomputation. It runs now, on a **census** of the window, not on a sample.
- **`3-JUDGE`** — interpretive correctness: whether the reading is the *right* reading of the
  chart. This needs a qualified domain expert. No such expert exists for this project, so
  `3-JUDGE` is `NOT_ESTABLISHED` and stays `NOT_ESTABLISHED` until one is supplied. **The
  owner's own opinion does not count as expert judgement** and is never recorded as a score.

No number from `3-MECH` may be reported as, or converted into, a statement about interpretive
correctness. "Every cited candle really forms the claimed gap" and "the gap that mattered was
chosen" are different statements, and only the first is measured here.

### 6.1 `3-MECH` — mechanical verification (runs now, no expert needed)

Unit of verification: one **claim** inside one snapshot. A claim is any sentence the engine
emits that asserts a fact about the data. Four check families:

| # | check | how it is decided (recomputation, never reading) | pass condition |
|---|---|---|---|
| M1 | **geometry** | the candles the claim cites are re-fed to the same `engine_v1` function that defines the concept — `b1_candles.swing.swing_at`, `b1_candles.fvg.fvg_at`, `c1_catalog.liquidity_sweep.sweep_at_swing_level` (or `sweep_at` for a caller level), `c1_catalog.displacement.displacement_at`, `c1_catalog.order_block.order_block_at` — and the returned bounds/levels must equal the numbers printed in the claim | exact equality; declared tolerance `0.0` price units (`ENGINEERING_CHOICE`) |
| M2 | **invalidation consistency** | the invalidation price cited in the narrative equals the `HYPOTHETICAL_INVALIDATION` used in the plan record for the same decision | exact equality |
| M3 | **target consistency** | the target level cited in the narrative equals the level of the cited liquidity object and equals `HYPOTHETICAL_TARGET`, and that object exists in the candidate set at `t` | exact equality **and** object exists |
| M4 | **reference integrity** | every bar index the claim cites exists, is `<= t`, and matches the `last_read` printed with the claim; every printed gap id exists in the catalog | no index `> t`, no unknown gap id |

Counters, per window, printed as a table (counts only):

```text
CLAIMS_TOTAL
M1_PASS / M1_FAIL / M1_UNDECIDABLE      (undecidable = the claim cites no candle)
M2_PASS / M2_FAIL / M2_NO_PLAN          (no plan record for that decision)
M3_PASS / M3_FAIL / M3_NO_TARGET        (the plan carries no target component)
M4_PASS / M4_FAIL
```

`UNDECIDABLE` / `NO_PLAN` / `NO_TARGET` are printed **beside** the passes, never merged into
them. A large `NO_PLAN` count is itself a finding about how often the engine makes a claim it
cannot then support.

**`3-MECH` produces no verdict word.** There is no "the engine is consistent" line — only
counts. Each failure is listed with the claim id, the claim text, the recomputed number and the
printed number, so it can be checked by hand.

This is the part of Level 3 that answers what the owner can actually use **without an expert**:
whether the engine's statements about its own citations hold up.

### 6.2 `3-JUDGE` — interpretive correctness (`NOT_ESTABLISHED`, parked)

```text
3_JUDGE_STATUS = NOT_ESTABLISHED
reason         = no qualified domain expert is available to this project
owner_role     = executor and operator, never a judge; owner opinion is not a score
```

The procedure, the quantity and the rubric below are **frozen now** so they cannot be shaped
later around whatever the engine happens to output, and are **not executed** until a qualified
expert is supplied. Until then, every Level 3 report prints the status block above verbatim.

#### 6.2.1 Procedure (when an expert exists)

1. A snapshot is a chart image **and** a machine-readable state dump, both cut at time `t`.
   Only completed bars at or before `t` are drawn. No future bar, no later level, no annotation
   derived from later data.
2. The **expert** reads the snapshot first and writes a reading in the rubric fields
   (free text per field), before seeing the engine's reading.
3. The engine's reading at the same `t` is then revealed, field by field.
4. Each field is scored against §6.2.3. `NA` is available and is counted.
5. Snapshots are drawn from W1 (development) unless the owner rules that W2 snapshots are
   permitted; if W2 is used, the snapshots are drawn **once** and are part of W2's single look.
6. The expert's identity, the date, and the fact that the expert had not seen the engine's
   output before scoring are recorded with the result.

#### 6.2.2 Quantity

```text
N_SNAPSHOTS = 40          tag: ENGINEERING_CHOICE   (declared now, not derived from power analysis)
```

`N_SNAPSHOTS` is explicitly an engineering choice: there is no source number and no power
calculation behind it (`KNOWLEDGE_GAP: required N for a human-agreement claim`). If fewer than
40 usable snapshots exist, the actual count is reported and the phase still publishes — §1.

Snapshot timestamps come from a seeded uniform draw over the window's completed bars, seed
`20261109` (`ENGINEERING_CHOICE`), and the drawn list is committed **before** any of them is
rendered. Hand-picking after seeing a chart is forbidden; a mechanically unusable draw is
replaced by the next draw and the replacement is logged.

#### 6.2.3 Rubric (frozen, use deferred)

Each criterion is scored `1` (expert's field agrees with the engine's field), `0` (disagrees), or
`NA` (the expert's own field was "no reading", or the engine printed a gap).

| # | criterion | what agreement means |
|---|---|---|
| R1 | **side / bias at `t`** | same directional reading, or both "undetermined" |
| R2 | **structure of the immediate range** | same named relationship between the last swing and the current price (above / inside / below), with the same levels quoted |
| R3 | **the referenced level** | the level the engine says it used is one the expert also names; a level not named by the expert scores `0`, not `NA` |
| R4 | **the invalidation condition** | same "what would make this wrong" in structural terms |
| R5 | **the stated unknowns** | no assertion by the engine that the expert marked as unknown; every engine gap the expert also saw counts in favour, an invented certainty counts against |

Aggregates (reported only when a judge exists): per-criterion agreement count and rate over
non-`NA` cases, plus Cohen's `kappa` per criterion (`kappa` is reported; **no cut-off** is used,
per `D3` clause C). `NA` counts are always printed beside the rates.

## 7. Brittleness test

A verdict is **stable** if it does not flip under all three perturbations below. Perturbations
are declared now and are not tuned.

| # | perturbation | magnitude | tag |
|---|---|---|---|
| P1 | decision bar shifted | `±1` completed bar | `ENGINEERING_CHOICE` |
| P2 | cost model | half-spread → full-spread | `ENGINEERING_CHOICE` |
| P3 | candidate set | drop the single earliest-knowable eligible candidate (leave-one-out) | `ENGINEERING_CHOICE` |

Reporting rule:

```text
STABLE      : the direction of every reported comparison is unchanged under P1, P2, P3
BORDERLINE  : at least one direction flips, and the flip is inside the reported interval
UNSTABLE    : at least one direction flips and the flip is outside the reported interval
```

`BORDERLINE` and `UNSTABLE` are **results**, printed with both the original and the perturbed
number side by side. A `BORDERLINE` outcome is never rounded into `STABLE` by widening an
interval, and never re-run with a different perturbation set.

---

## 8. Stopping rules

1. **One look per window.** W2 is opened once. When the run starts, the window is
   `BURNED` in the log, whether it completes or not.
2. **No interim peeking.** No partial result from W2 is inspected for any purpose other than
   detecting a mechanical failure from the `NO_RESULT` code list below.
3. **Abort and publish `NO_RESULT`** if: the protected-file hash differs
   (`72b03ca6…4d74ace` / `12216` bytes); a source file's hash differs from the recorded
   one; the data set has a gap larger than the declared tolerance (tolerance:
   `zero missing bars`, i.e. any gap aborts — `ENGINEERING_CHOICE`); an exception escapes;
   or a `SAME_BAR_ORDER_UNKNOWN` count exceeds the judgeable count (a sign the horizon or
   the geometry is mis-scaled, not a result to publish).
4. **No stopping for "interesting" results, and none for "boring" ones.** A null result is
   published with the same structure as a non-null one.
5. **No second window substitution.** If W2 aborts, the phase reports W2 as `NO_RESULT` with
   the abort code; it does not silently open another window to replace it.

### `NO_RESULT` codes

| code | meaning |
|---|---|
| `NO_RESULT_HASH_MISMATCH` | protected or source file changed |
| `NO_RESULT_DATA_GAP` | bars missing beyond `0` tolerance |
| `NO_RESULT_NO_JUDGEABLE` | every decision was `CENSORED` or `SAME_BAR_ORDER_UNKNOWN` |
| `NO_RESULT_MECHANICAL` | exception or environment failure; traceback kept |
| `NO_RESULT_WINDOW_ALREADY_USED` | window was opened before under any version |
| `NO_RESULT_DRAW_ORDER_BREACH` | a W3 month was loaded **before** the drawn list in §2.3 was committed — the draw is void and must be re-made in a new file |
| `NO_RESULT_ATTESTATION_MISSING` | the §2.2 attestation for the window was not signed before the run |

Two section-level codes, which do **not** abort a window:

| code | meaning |
|---|---|
| `CALLER_INPUT_MISSING` | §5.5 inputs were not supplied; §5.5 is printed as skipped and Level 2 continues |
| `3_JUDGE_NOT_ESTABLISHED` | §6.2 has no qualified judge; printed as a status line, never as a zero score |

A `NO_RESULT` is a published outcome and is not a failure of the phase.

---

## 9. Registry of every number introduced by this file

| # | number | where used | tag |
|---|---|---|---|
| 1 | `2021-01-01` .. `2022-01-01` | W1 | `SOURCE_NUMBER` (owner) |
| 2 | `2024-01-01` .. `2025-01-01` | W2 | `SOURCE_NUMBER` (owner) |
| 3 | W3 draw range `2020-01` .. `2024-12` (60 months) | W3 | `ENGINEERING_CHOICE` |
| 3a | `N_MONTHS = 6` | W3 | `ENGINEERING_CHOICE` |
| 3b | draw seed `20261109`, string `BTCUSDT|HOLDOUT_V1|<seed>|<YYYY-MM>`, sort by sha256 | W3 | `ENGINEERING_CHOICE` |
| 3c | drawn months `2022-02`, `2022-09`, `2022-11`, `2023-09`, `2023-11`, `2024-07` | W3 | result of 3a/3b, recorded before any load |
| 4 | `24` bars | horizon | `SOURCE_NUMBER` (code constant) |
| 5 | `0.0001` | EURUSD pip unit | `ENGINEERING_CHOICE` |
| 6 | half-spread | cost | `ENGINEERING_CHOICE` |
| 7 | `95 %` / Wilson | interval | `ENGINEERING_CHOICE` |
| 8 | `100` draws, seeds `0..99` | `B_UNIFORM` | `ENGINEERING_CHOICE` |
| 9 | `2000` resamples, seeds `0..1999` | `MEAN_R_CI` | `ENGINEERING_CHOICE` |
| 10 | `40` snapshots | `3-JUDGE` quantity | `ENGINEERING_CHOICE` |
| 11 | seed `20261109` | snapshot draw (`3-JUDGE`) | `ENGINEERING_CHOICE` |
| 12 | `±1` bar | P1 | `ENGINEERING_CHOICE` |
| 13 | zero-gap tolerance | abort | `ENGINEERING_CHOICE` |
| 14 | `kappa` (no cut-off) | Level 3 | `ENGINEERING_CHOICE` |
| 15 | commissions / financing | cost gap | `KNOWLEDGE_GAP` |
| 16 | required `N` for a human-agreement claim | `3-JUDGE` | `KNOWLEDGE_GAP` |
| 17 | geometry tolerance `0.0` price units | `3-MECH` M1 | `ENGINEERING_CHOICE` |
| 18 | `K_DELAYS = {1, 2, 3}` bars | §5.6 | `ENGINEERING_CHOICE` |
| 19 | `TOTAL_LOSS_LIMIT` | §5.5 | `CALLER_INPUT` (no default, no example) |
| 20 | `RISK_PER_TRADE` | §5.5 | `CALLER_INPUT` (no default, no example) |
| 21 | owner seen-list for W3 at time of writing: **none** | §2.3 | `OWNER_STATEMENT_IN_CHAT` |

No `SOURCE_NUMBER` for any of items 5–21 exists, and none is invented. Items 19–20 have **no
value in this file at all** — not even a placeholder — because a placeholder becomes a default
the first time someone is in a hurry.

---

### 9A. Dev-run record — first attempt aborted, next dev month declared

Recorded on 2026-11-09, **before any bar of the next attempt is loaded**, so that the choice
below cannot be adjusted after the fact.

- **First dev attempt** — `EURUSD 5m`, decision month `2021-03`, history from `2021-01-01`,
  default configuration, one run. It was aborted by the operating system (out-of-memory kill of
  the Python process) after `12 min 59 s`, with resident memory at `3,870,276 kB` on a
  `3,939 MB` machine. The kill happened **during the warm-up, before the first decision
  instant**: `decisions = 0`, `plans = 0`, `cases = 0`, and the raw output directory holds a
  `264`-byte log with no result file. **No result was seen.** Record:
  `dev_month_v0/SUMMARY_V0.md`.
- **Consequence for `2021-03`.** Because nothing was observed, `2021-03` is **not burned** as an
  evaluation window in the sense of §8 — but it is also **not eligible as a blind window**,
  since its bars were read into a decision process. It is treated as `LOADED_NO_RESULT` and is
  never used as an out-of-sample window.
- **Next dev month: `2021-06`** — tag `ENGINEERING_CHOICE`, declared here before any load.
  Reason for a *new* month rather than repeating `2021-03`: a window is read once (§2.1), and
  re-reading `2021-03` under a new wrapper is a second look at the same bars even when the
  first look produced no decision.
- The next attempt is **not authorised by this record**. It requires
  `ict_recipe_v1/MEMORY_ANALYSIS_V0.md` and `ict_recipe_v1/DEV_RUN_PLAN_V1.md`, both of which
  are design only.

## 10. What this does NOT establish

- It establishes **no result of any kind**. No window has been read; no data was opened to
  write this file.
- It does **not** claim the metrics are the right metrics. They are declared, not validated;
  `P*(t)` in §4.3 is explicitly blunt and chosen to be hard to tune.
- It does **not** make `HOLDOUT_V1` methodologically sufficient. `selection_quality` remains
  `NOT_ESTABLISHED` after the phase unless a separate pre-registered estimand is written and
  run — none exists.
- It does **not** authorise zone selection. `LEVEL_1B_ZONE_SELECTION = NOT_AVAILABLE_V1`, and
  no stand-in is substituted.
- It does **not** license `WIN` / `LOSS` / `PnL` / `accuracy` / `edge` / `fill` language, even
  under `D3` clause B.
- It does **not** propose that `40` snapshots or `2000` resamples are statistically
  motivated. Both are labelled `ENGINEERING_CHOICE`; the underlying power question is a
  `KNOWLEDGE_GAP`.
- It does **not** verify the BTC window history claim in §2 (the `2026-05` note). That line
  is carried over from an earlier audit and is marked `UNVERIFIED in this session`.
- It does **not** guarantee that the existing kernel can supply `N`, `knowable_bar`,
  `level` and a target component for every decision without a new adapter. That is a build
  question for `PAIRWISE_SELECTION_DESIGN_V1.md`, not a result here.
- It does **not** establish interpretive correctness of any reading, and cannot: `3-JUDGE` is
  `NOT_ESTABLISHED` with no qualified expert, and the owner is recorded as executor, not judge.
  `3-MECH` passing every claim would still say nothing about whether the right object was read.
- It does **not** make `3-MECH` a quality score. It reports counts of claims that fail to
  describe their own citations. A perfect count is a consistency statement, not a truth claim.
- It does **not** verify that the owner's eyes are in the state the §2.2 attestation asserts.
  That is unverifiable by construction and is recorded as an attestation, never as evidence.
- It does **not** claim the W3 draw is representative, balanced or independent. It is one
  deterministic draw that clusters three of six months in 2022; the clustering is printed, not
  corrected.
- It does **not** supply, imply or recommend any risk fraction or loss limit. §5.5 is arithmetic
  on `CALLER_INPUT` with no default, and it answers "how many consecutive negatives would this
  input pair tolerate", never "which input pair should be used".
- It does **not** estimate any probability — not of a streak, not of a drawdown, not of
  anything else — and contains no simulation or resampling of outcomes.
- It does **not** say how fast the owner executes, so no `K_DELAYS` value is endorsed as
  realistic; §5.6 reports differences for each `k` and picks none.
