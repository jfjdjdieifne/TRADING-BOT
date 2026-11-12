# O — Full-setup catalog, Stage 1 (inventory)

**Run:** 2026-11-09 (UTC). **Base:** `engine_v1/external_sources/`. **Tier:** `TIER2` only — every line below is a
publisher's claim, never a claim by Michael Huddleston. **Stage:** 1 of N. Inventory only.

**What this file is.** A catalog of how public ICT teachers describe a *complete trade*, step by step, so that Stage 2
can record every described case per term (merged where publishers agree, kept separate where they do not).
Nothing here is a decision, a ranking, or a definition we adopt.

**Rules applied while building this file**

- Read-only research. No engine code run or opened, no market data loaded, no existing file edited.
- Every term and every step comes from a page opened in this run. No outside ICT knowledge was added.
- No chatbot/AI pages, no YouTube/video pages, no login/paywall/pirated pages. Pages that merely *link* to a video
  are used only for their text.
- Quotes: verbatim, English, ≤ 25 words. Word counts were kept under the limit by shortening, not by paraphrase.
- Links and text only. No image was downloaded and no image is embedded in this repo.
- **Images: none were viewed in this run.** Every image row in Section E therefore carries `IMAGE_NOT_VIEWED` and
  the viewing-dependent columns (candles numbered / prices printed) carry `UNSTATED`. Nothing is described about
  a pixel that was not read.
- Silence of a page is not agreement and not disagreement.
- No publisher is preferred over another, and no term below is held up as a rule to adopt.

**Independence grouping used in Section D (recorded, not chosen)**

| Group id | Domains | Basis shown on the pages | Independence status |
|---|---|---|---|
| G1 | `innercircletraders.net`, `innercircletrader.net`, `theinnercircletraders.com` | All three are ICT-education sites with near-identical names; bylines seen are "Ayub Rana" (innercircletrader.net), "The Inner Circle Traders" (theinnercircletraders.com), no byline visible on innercircletraders.net. No shared author, owner or network is *shown* on any opened page. | `RELATIONSHIP_UNCLEAR` → counted as **ONE** publisher in Section D |
| G2 | `ictkillzone.com` | Byline "Michael Phillips", author page linked | independent |
| G3 | `altrady.com` | Byline "Catalin" | independent |
| G4 | `liquidityscan.io` | Byline "Hayk Muradian, Founder & Lead Analyst" | independent |
| G5 | `fxnx.com` | Byline "Fatima Al-Rashidi"; footer "Publisher FXNX Global Markets Ltd" | independent |
| G6 | `velotrade.com` | Byline "Vittorio De Angelis" | independent |
| G7 | `ninjatrader.com` | Byline "NinjaTrader Team" | independent |
| G8 | `quartersequence.com` | No author shown; site brand "Quarter Sequence"; cites a third party called "Daye" | independent (no relationship shown to any other domain here) |
| G9 | `ictflow.com` | No author shown | independent (no relationship shown) |
| G10 | `fundingpips.com` | Byline "FundingPips" (prop firm) | independent |
| G11 | `proea.app` | No author shown; page cites TTrades and describes "our Fractal Model Desk" | independent (no relationship shown) |

Independence units in this run: **11** (G1 counts once). Domains opened: **13**. Pages opened: **14**.

---

# A — Pages opened

Every row was opened and read in this run with a page-fetch tool (no browser, no login, no paywall wall hit).
"Chunks read" = how many content chunks of the page were actually read.

| id | URL | Publisher (domain, exactly) | What it covers | Date shown on page | Chunks read |
|---|---|---|---|---|---|
| A01 | https://www.ictkillzone.com/ict-2022-model | ictkillzone.com | Full ICT 2022 model: draw on liquidity → stop raid → displacement + MSS → FVG entry → opposing-liquidity target; timeframe ladder; kill-zone table; the site's own 5-step execution checklist; schematic NQ plan | Published May 2026, updated 29 Sep 2026 | 2 of 4 |
| A02 | https://www.altrady.com/blog/crypto-trading-strategies/ict-trading-strategy | altrady.com | Core ICT concepts plus a 6-step "ICT trading strategy step by step" (bias → liquidity → sweep → MSS → entry → stop/target); glossary; crypto notes | Published 05 Jul 2024, updated 21 Oct 2026 | 2 of 3 |
| A03 | https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/ | innercircletrader.net | Silver Bullet model: three one-hour windows, 10-item entry checklist (liquidity → window → MSS → displacement → FVG → premium/discount → retrace → execute → stop/target → close), worked XAU/USD example, mistakes | no date shown in read chunks | 2 of 7 |
| A04 | https://innercircletraders.net/ict-fair-value-gap/ | innercircletraders.net | FVG definition and types, CE, HTF vs LTF FVG, and a 6-step bullish FVG trade setup plus its bearish mirror (stop and target included) | Screenshots dated 2026-03 | 3 of 3 |
| A05 | https://www.theinnercircletraders.com/ict-trading-strategy-the-core-framework-explained/ | theinnercircletraders.com | "The 5-Step ICT Trading Process": daily bias → draw on liquidity → kill zone → structural confirmation → PD array entry; includes a full worked example with stop and target | Updated July 2026 | 1 of 3 |
| A06 | https://liquidityscan.io/blog/fvg-vs-order-block-which-entry-zone-should-you-trade | liquidityscan.io | FVG vs order block as entry zones: formation mechanics, comparison table (entry level, stop, invalidation), validation filters, entry tactics, stop placement, confluence | 11 Jul 2026, "updated 3mo ago" | 2 of 3 |
| A07 | https://fxnx.com/en/blog/fvg-entry-filter-mechanical-rules-htf-bias | fxnx.com | Mechanical FVG entry filter: HTF anchor, three-candle range displacement rule, CE limit and split entry, kill-zone filter, front-run rule (cancel if target swept), 5-point pre-trade checklist | 31 Jul 2026, "Updated August 2026" | 3 of 3 |
| A08 | https://velotrade.com/blog/liquidity-sweep | velotrade.com | Liquidity sweep: pool locations, the three parts of a sweep, sweep vs breakout, and a 6-step trade process ending in stop and target | 07 Oct 2026, verified 08 Oct 2026 | 2 of 3 |
| A09 | https://ninjatrader.com/futures/blogs/price-action-trading-strategies/ | ninjatrader.com | Price-action workflow on futures: concepts, patterns, and a 4-step application sequence ending in entry, stop and target | 17 Apr 2026 | 1 of 2 |
| A10 | https://quartersequence.com/the-study/psp/ | quartersequence.com | Precision Swing Point: definition, the Diverger/Peers rule, optimal entry in the wick, stop, invalidation, and a 5-step setup sequence (True Open → HTF PDA → SSMT → PSP/qCISD → stop/target) | no date shown; site shows 2026 material | 2 of 3 |
| A11 | https://quartersequence.com/the-study/ict-market-structure/ | quartersequence.com | Definitions used by A10's sequence: swing high/low (three-candle), swing confirmation on close, three swing sizes, trend, BOS | no date shown | 1 of 3 (supporting page, definitions only) |
| A12 | https://ictflow.com/blog/ict-complete-2022-trading-strategy | ictflow.com | 2022 model framework in 6 numbered steps (quarterly shift → monthly → weekly bias/DOL → daily PD array → kill-zone execution → IOFED entry), risk/target notes, failure cases | 21 May 2026 | 1 of 1 |
| A13 | https://fundingpips.com/blog/ict-2022-model | fundingpips.com | 2022 model as a four-step entry pattern, five underlying concepts, 7 numbered entry rules with stop and target, kill-zone times, daylight-saving note | 18 Oct 2026 | 1 of 3 |
| A14 | https://proea.app/en/blog/change-in-state-of-delivery | proea.app | CISD (change in state of delivery): definition, three drawing decisions, CISD vs MSS, failure case; describes "our Fractal Model Desk" entry logic | no date shown; citations dated Jun–Jul 2025 | 1 of 4 |

**Pages opened per publisher:** ictkillzone.com 1, altrady.com 1, innercircletrader.net 1, innercircletraders.net 1,
theinnercircletraders.com 1, liquidityscan.io 1, fxnx.com 1, velotrade.com 1, ninjatrader.com 1,
quartersequence.com 2, ictflow.com 1, fundingpips.com 1, proea.app 1.

**Prior-inventory domains reused (from the existing `external_sources/` registry):** ninjatrader.com, altrady.com,
innercircletraders.net, innercircletrader.net, ictkillzone.com, velotrade.com, liquidityscan.io, fxnx.com,
quartersequence.com, theinnercircletraders.com — all ten opened. **New domains added in this run:** ictflow.com,
fundingpips.com, proea.app.

---

# B — Per-publisher ordered step lists

One entry per publisher. Steps are written in the publisher's own order, with the publisher's own step name, and one
short verbatim quote each. Nothing is reordered, renamed or reconciled. Where a page gives no ordered list, the entry
says `NO_ORDERED_STEPS` and lists the parts the page names.

## B01 — ictkillzone.com (A01)

The page gives two ordered lists of its own: the model sequence, and the site's 5-step execution checklist. The page
states of the model that "the step lists you see online — including the one below — are summaries of those lessons",
and of the checklist that "The numbering and grouping are ours". Both are recorded as the publisher's own lists.

**List 1 — the model, "in the order it plays out on a chart" (bearish example)**

| # | Step name as written | Quote |
|---|---|---|
| 1 | Draw on liquidity | "On the daily or 4-hour chart, decide where price is most likely heading next" |
| 2 | Stop raid | "price runs above a nearby high — a previous day high, session high or equal highs" |
| 3 | Displacement and market structure shift | "Price turns and drops hard enough to break the most recent short-term swing low." |
| 4 | Fair value gap entry | "The entry is a short on the retrace into that gap, often at its midpoint" |
| 5 | Target the opposing liquidity | "Targets are the sell-side liquidity below — first a nearer internal low" |

**List 2 — "Our 5-Step Execution Checklist"**

| # | Step name as written | Quote |
|---|---|---|
| 1 · Direction | Daily Bias — Which Direction Today | "Mark the weekly and daily dealing ranges: above the 50% level (equilibrium) is premium" |
| 2 · Phase | AMD — Has the Raid Happened Yet? | "Our rule is to enter only after the raid has finished and the MSS has printed" |
| 3 · Timing | Time Window — Is an Entry Window Open? | "the entry must happen inside one of the windows in the table above" |
| 4 · Entry zone | PD Array — Where Exactly to Enter | "The retrace must reach a PD array on the correct side of the range" |
| 5 · Management | Stop and Targets | "Stop beyond the raid extreme." |

## B02 — altrady.com (A02)

Section "An ICT Trading Strategy Step by Step", introduced with "ICT teaches several models, but most follow the same
sequence."

| # | Step name as written | Quote |
|---|---|---|
| 1 | Set the bias on a higher timeframe | "Use the daily or 4-hour chart to decide whether price is likely to seek buy-side or sell-side liquidity" |
| 2 | Mark the liquidity | "Note the obvious swing highs, swing lows and equal highs or lows where stops cluster." |
| 3 | Wait for the sweep | "Let price run the liquidity against your bias" |
| 4 | Look for a market structure shift | "wait for price to break the last swing in your direction with a strong move that leaves a fair value gap" |
| 5 | Enter on the retrace | "Place the entry where the fair value gap or order block overlaps the OTE zone, preferably inside a killzone." |
| 6 | Set the stop and target | "Put the stop beyond the swept low or high, and target the opposite liquidity" |

## B03 — innercircletrader.net (A03)

Section "Step-by-Step Silver Bullet Checklist", introduced with "This is the exact checklist I run before every Silver
Bullet session." The page numbers the items 01–10.

| # | Step name as written | Quote |
|---|---|---|
| 01 | Mark the buy-side and sell-side liquidity | "on the 15-minute chart before the window opens" |
| 02 | Wait for the Silver Bullet window to open | "03:00 AM, 10:00 AM, or 02:00 PM New York local time. Do not pre-position." |
| 03 | Drop to 1-minute or 3-minute | "The 5-minute can be used for the parent read." |
| 04 | Watch for a Market Structure Shift | "in the direction of the next draw on liquidity" |
| 05 | Confirm displacement | "the breaking candle should close decisively and leave a fair value gap behind" |
| 06 | Mark the fair value gap | "created during the displacement leg" |
| 07 | Validate the FVG sits in the correct premium or discount zone | "relative to the most recent swing" |
| 08 | Wait for price to retrace into the FVG | "Do not chase the displacement leg." |
| 09 | Execute the trade | "with stop loss beyond the candle that created the FVG and a take profit at the next liquidity pool" |
| 10 | Close the trade or trail the stop | "within the same session. The Silver Bullet is a scalp, not a swing." |

## B04 — innercircletraders.net (A04)

Section "How Do You Trade an ICT Fair Value Gap? A Step-by-Step Strategy" gives two numbered lists — "Bullish FVG Trade
Setup" and "Bearish FVG Trade Setup". Recorded verbatim as separate lists.

**Bullish FVG Trade Setup**

| # | Step name as written | Quote |
|---|---|---|
| 1 | Confirm the higher timeframe (daily or 4-hour) is in a bullish structure | "Price should be making higher highs and higher lows" |
| 2 | Wait for a clear liquidity sweep … followed by a sharp bullish displacement move | "Drop to an intermediate timeframe such as the 1-hour or 15-minute chart." |
| 3 | Identify the fair value gap created by that displacement | "Mark the zone from the high of the first candle to the low of the third candle." |
| 4 | Wait for the price to pull back into the FVG zone | "Do not enter as soon as the zone is created." |
| 5 | look for a short-term market structure shift … as your entry trigger | "On a lower timeframe such as the 5-minute chart" |
| 6 | Enter long (buy) | "Place your stop loss below the low of the FVG zone." |

**Bearish FVG Trade Setup** (same six step names, mirrored)

| # | Step name as written | Quote |
|---|---|---|
| 1 | Confirm the higher timeframe is in a bearish structure | "or at a significant supply area" |
| 2 | wait for a liquidity sweep above a recent swing high | "followed by a sharp bearish displacement" |
| 3 | Mark the bearish FVG zone | "from the low of the first candle to the high of the third candle" |
| 4 | Wait for the price to pull back up into the FVG zone | "Wait for the price to pull back up into the FVG zone." |
| 5 | look for a bearish structure shift or bearish displacement within the zone | "as your entry trigger" |
| 6 | Enter short (sell) | "Stop loss goes above the top of the FVG zone." |

## B05 — theinnercircletraders.com (A05)

Section "The 5-Step ICT Trading Process", described as "Daily Bias → Draw on Liquidity → Kill Zone Timing → Structural
Confirmation → PD Array Entry. Five steps, run in that order, every time."

| # | Step name as written | Quote |
|---|---|---|
| 01 | Determine your daily bias | "Before anything else, establish whether the higher timeframe (daily or H4) favours buys or sells." |
| 02 | Identify the draw on liquidity | "identify the specific liquidity pool price is being drawn toward" |
| 03 | Wait for the correct kill zone | "The London Open and New York Open kill zones see the highest institutional participation" |
| 04 | Confirm with market structure | "wait for a Change of Character (CHoCH) or Break of Structure (BOS) that aligns with your bias" |
| 05 | Enter at a PD array | "Stop loss goes beyond the array; target is the liquidity pool from Step 2." |

The page's own worked example runs the same five steps and ends: "Stop below FVG low, target PWH — minimum 1:3
risk-reward".

## B06 — liquidityscan.io (A06)

`NO_ORDERED_STEPS`. The page compares two entry zones and gives validation filters and entry/stop conventions, but it
does not present a numbered complete-trade sequence. The parts it names, in the page's own words:

- displacement — "displacement — a fast, body-heavy expansion that breaks structure"
- sweep first — "The highest-grade zones form directly off a sweep of obvious liquidity"
- structural consequence — "a **Break of Structure (BOS)** for continuation or a **Change of Character (CHoCH)** for reversal"
- freshness — "Both zones decay with every test."
- premium/discount location — "Demand-side zones belong in discount; supply-side zones belong in premium."
- entry at CE — "The professional entry inside a fair value gap is **Consequent Encroachment (CE)**"
- entry at OB open / mean threshold — "The **opening price** of the OB candle is the classic entry"
- stop — "Just beyond the far edge of the gap" / "the stop belongs beyond the candle's extreme"
- target — "Target: the next draw at 119,000."

## B07 — fxnx.com (A07)

Section "The Pre-Trade Filter Checklist", introduced with "Print this out and keep it next to your monitors. Do not
take an FVG trade unless it ticks all five boxes". The page numbers four boxes 1–4 and then restarts at 1 for the
fifth; the five boxes are recorded in page order without renumbering being "fixed".

| # as written | Step name as written | Quote |
|---|---|---|
| 1 | HTF Bias | "Does this M5 gap align with the Daily/H4 directional order flow?" |
| 2 | Displacement Rule | "Did the candle creating the gap close outside the previous 3-candle range with a strong body?" |
| 3 | Killzone Check | "Are we currently inside the London or NY Killzone?" |
| 4 | CE Invalidation | "will I cut the trade if an M5 candle closes beyond the 50% CE mark?" |
| 1 (page renumbers) | Liquidity Target | "Is the target liquidity still intact? (If it was already swept, cancel the trade)." |

The page also states the post-entry management it uses: "Scale out of your position (take 50-80% off) as price reaches
the first major HTF liquidity pool."

## B08 — velotrade.com (A08)

Section "How do you trade a liquidity sweep?", introduced with "A disciplined process looks like this".

| # | Step name as written | Quote |
|---|---|---|
| 1 | Mark the liquidity in advance | "note equal highs and lows, the prior day range and the session range" |
| 2 | Wait for the sweep | "Price trades through the level and closes back inside on your chosen timeframe." |
| 3 | Wait for a structure shift | "price should displace up and close above the most recent lower high" |
| 4 | Enter on a retracement | "Look for a fair value gap or an order block created by the displacement and place a limit order there." |
| 5 | Stop beyond the sweep | "the logical stop sits below the low of the sweep wick" |
| 6 | Target opposing liquidity | "The natural target is the buy-side liquidity above" |

The page adds the mirror: "The same steps work in reverse for a buy-side sweep".

## B09 — ninjatrader.com (A09)

Section "How to apply price action strategies when trading futures", introduced with "A simple workflow might look
like this".

| # | Step name as written | Quote |
|---|---|---|
| 1 | Start by identifying the trend on a higher timeframe. | "Start by identifying the trend on a higher timeframe." |
| 2 | Mark important support and resistance levels. | "Mark important support and resistance levels." |
| 3 | Wait for a pattern to form at those levels. | "Wait for a pattern to form at those levels." |
| 4 | Plan your entry, stop, and target before taking the trade. | "Plan your entry, stop, and target before taking the trade." |

## B10 — quartersequence.com (A10, supporting A11)

Section "Where the PSP fits", five numbered steps followed by "highest-probability window - Q3 in Q3 in Q3 (≈ 09:00
to 10:30 NY)".

| # | Step name as written | Quote |
|---|---|---|
| 1 | True Open sets the bias | "the **True Open** sets the bias" |
| 2 | HTF PDA where | "a **premium/discount array** (PDA) … says where" |
| 3 | SSMT confirms the bias | "the **SSMT** confirms the bias - the crack in correlation" |
| 4 | PSP / qCISD the entry trigger | "either, or both" |
| 5 | Stop · Target | "Stop beyond the swing, target at the next liquidity." |

The page states the entry is not the level itself: "A PSP is never a trade on its own." The stop is "the wick extreme
of the PSP candle"; the target sits "at the next pool of liquidity … or at a measured-move projection of the swing
itself".

## B11 — ictflow.com (A12)

Section "The 2022 Model Framework — Step by Step".

| # | Step name as written | Quote |
|---|---|---|
| Step 1 | Quarterly Shift | "Identify the current quarterly directional bias" |
| Step 2 | Monthly Bias | "determine the current month's expected direction" |
| Step 3 | Weekly Bias and DOL | "Identify the weekly draw on liquidity — the previous week's high or low" |
| Step 4 | Daily PD Array | "Mark the specific daily PD Array (FVG, OB, or BPR)" |
| Step 5 | Killzone Execution | "wait for the AMD pattern — the manipulation phase (Judas Swing/liquidity sweep)" |
| Step 6 | Entry Model (IOFED) | "identify the displacement FVG. Enter at the CE. Stop beyond the FVG. Target: the daily DOL." |

## B12 — fundingpips.com (A13)

Section "ICT 2022 Model Entry Rules Step by Step", introduced with "The ICT 2022 model entry follows a strict order".

| # | Step name as written | Quote |
|---|---|---|
| 1 | Set the daily bias | "on the 1-hour or 4-hour chart, and identify the draw on liquidity" |
| 2 | mark the opposing liquidity | "such as a recent low if your bias is bullish" |
| 3 | Wait for price to sweep that liquidity | "trading through the level and failing to continue" |
| 4 | Wait for displacement … confirming the market structure shift | "closes beyond the most recent short-term swing" |
| 5 | Mark the fair value gap | "left by the displacement leg" |
| 6 | Place a limit order at the near edge or midpoint of the gap | "with a stop beyond the sweep's extreme" |
| 7 | Target the draw on liquidity identified in step 1 | "or take partial profit at an intermediate level" |

The page frames the whole model as "a four-step entry pattern: a liquidity sweep, a displacement move, a market
structure shift, and an entry in the fair value gap".

## B13 — proea.app (A14)

`NO_ORDERED_STEPS`. The page defines CISD and the decisions used by "our Fractal Model Desk" but does not present a
numbered complete-trade sequence. The parts it names:

- sweep — "their sweep is a wick past the last confirmed swing low (or high)"
- the line — "It's where the last run of candles began."
- the trigger — "a closed candle that finishes beyond the opening price of the run of opposite candles"
- the run that made the extreme — "Consecutive candles whose bodies point the same way"
- freeze and failure — "The first CISD freezes the line and the extreme."
- invalidation — "If price later trades beyond the frozen extreme … the CISD is marked failed"

---

# C — Term inventory

Terms are grouped by the role they play in the publishers' setups. Every term below appears as a part of a setup on
at least one opened page; no term was added from outside. Per publisher: one verbatim definition quote, or
`NOT_STATED` when that page uses the term without defining it. URLs repeat the page ids from Section A.

## C1 — Direction

### C1.1 Bias (daily bias / HTF bias)

| Publisher | Definition quote | Page |
|---|---|---|
| theinnercircletraders.com | "Daily bias is the directional read that filters every decision you make for the trading session." | A05 |
| fxnx.com | "Directional bias is non-negotiable." | A07 |
| ictkillzone.com | "Daily Bias — Which Direction Today" (heading only; no one-line definition) | A01 |
| ictflow.com | "Identify the current quarterly directional bias" | A12 |
| altrady.com | "Set the bias on a higher timeframe." | A02 |
| fundingpips.com | "Set the daily bias on the 1-hour or 4-hour chart" | A13 |
| innercircletraders.net | "Confirm the higher timeframe (daily or 4-hour) is in a bullish structure." | A04 |
| innercircletrader.net | NOT_STATED (uses "the parent read" and "the direction of the next draw on liquidity") | A03 |
| ninjatrader.com | NOT_STATED (uses "identifying the trend on a higher timeframe") | A09 |
| quartersequence.com | "the **True Open** sets the bias" | A10 |
| proea.app | NOT_STATED | A14 |
| velotrade.com | NOT_STATED ("decide which side the higher-timeframe bias favours") | A08 |
| liquidityscan.io | NOT_STATED ("once higher-timeframe bias is set") | A06 |

### C1.2 Draw on liquidity (DOL)

| Publisher | Definition quote | Page |
|---|---|---|
| ictflow.com | "Identify the weekly draw on liquidity — the previous week's high or low" | A12 |
| fundingpips.com | "identify the draw on liquidity, meaning the level price is likely heading toward" | A13 |
| theinnercircletraders.com | "the pool of buy-side or sell-side stops that price is being engineered toward" | A05 |
| ictkillzone.com | "decide where price is most likely heading next" | A01 |
| innercircletrader.net | NOT_STATED ("in the direction of the next draw on liquidity") | A03 |
| altrady.com | NOT_STATED ("decide whether price is likely to seek buy-side or sell-side liquidity next") | A02 |
| quartersequence.com | NOT_STATED ("target at the next liquidity") | A10 |
| velotrade.com | NOT_STATED | A08 |
| liquidityscan.io | NOT_STATED ("Target: the next draw at 119,000") | A06 |
| innercircletraders.net | NOT_STATED ("the nearest liquidity level above") | A04 |
| fxnx.com | NOT_STATED | A07 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C1.3 Premium / discount (equilibrium)

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "Split the current range at its 50% level. Above it is premium, below it is discount." | A02 |
| fundingpips.com | "Premium and discount divide a price range into an upper half and a lower half." | A13 |
| ictkillzone.com | "above the 50% level (equilibrium) is premium and favours shorts toward sell-side liquidity" | A01 |
| innercircletraders.net | "price is in a discount area, meaning below the midpoint of the most recent swing range" | A04 |
| liquidityscan.io | "Demand-side zones belong in discount; supply-side zones belong in premium." | A06 |
| quartersequence.com | "premium/discount array (PDA) - the higher-timeframe zone price is expected to react from" | A10 |
| fxnx.com | "An H4 or Daily PD Array (Premium/Discount Array)" | A07 |
| innercircletrader.net | NOT_STATED ("use the premium and discount framework to confirm the FVG is in the right zone") | A03 |
| ictflow.com | NOT_STATED | A12 |
| velotrade.com | NOT_STATED | A08 |
| ninjatrader.com | NOT_STATED | A09 |
| theinnercircletraders.com | NOT_STATED | A05 |
| proea.app | NOT_STATED | A14 |

### C1.4 Dealing range

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "Mark the weekly and daily dealing ranges" | A01 |
| liquidityscan.io | NOT_STATED ("the premium half of the dealing range") | A06 |
| fxnx.com | NOT_STATED | A07 |
| quartersequence.com | NOT_STATED (uses "measured-move projection" and "range equilibrium" for targets) | A10 |

## C2 — Liquidity and structure

### C2.1 Swing high / swing low

| Publisher | Definition quote | Page |
|---|---|---|
| quartersequence.com | "A swing high is three candles where the middle one has the highest high" | A11 |
| fundingpips.com | "define a short-term swing high as a candle with a lower high on each side of it" | A13 |
| proea.app | "swings confirmed by 3 candles on each side" | A14 |
| altrady.com | NOT_STATED ("Mark the obvious swing highs, swing lows") | A02 |
| ictkillzone.com | NOT_STATED ("the most recent short-term swing low") | A01 |
| innercircletraders.net | NOT_STATED ("below a recent swing low") | A04 |
| innercircletrader.net | NOT_STATED | A03 |
| theinnercircletraders.com | NOT_STATED | A05 |
| velotrade.com | NOT_STATED ("Two or more swing points at nearly the same price") | A08 |
| ninjatrader.com | NOT_STATED ("higher highs (uptrend) or lower lows (downtrend)") | A09 |
| liquidityscan.io | NOT_STATED | A06 |
| fxnx.com | NOT_STATED ("the structural swing point that initiated the gap") | A07 |
| ictflow.com | NOT_STATED | A12 |

### C2.2 Equal highs / equal lows (relative equal highs or lows)

| Publisher | Definition quote | Page |
|---|---|---|
| velotrade.com | "Two or more swing points at nearly the same price look like strong support or resistance" | A08 |
| altrady.com | "equal highs or lows where stops cluster" | A02 |
| ictkillzone.com | "equal highs" (named as a pool; no separate definition) | A01 |
| innercircletrader.net | "Relative equal highs or lows." (listed as a liquidity reference; no definition) | A03 |
| fundingpips.com | NOT_STATED ("equal highs and equal lows") | A13 |
| liquidityscan.io | NOT_STATED ("equal lows, an old session low, a prior day's extreme") | A06 |
| innercircletraders.net | NOT_STATED ("such as a swing high, equal high") | A04 |
| theinnercircletraders.com | NOT_STATED | A05 |
| quartersequence.com | NOT_STATED | A10 |

### C2.3 Buy-side liquidity / sell-side liquidity (liquidity pools)

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "Buy-side liquidity (BSL) is the cluster of buy stops and breakout orders resting above swing highs" | A01 |
| altrady.com | "Buy-side liquidity (BSL) rests above swing highs and equal highs, where short sellers keep their stops." | A02 |
| fundingpips.com | "Buy-side liquidity sits above highs, and sell-side liquidity sits below lows." | A13 |
| velotrade.com | "**Buy-side liquidity** sits **above** highs." | A08 |
| theinnercircletraders.com | "Liquidity pools typically sit above recent swing highs (buy-side liquidity)" | A05 |
| liquidityscan.io | NOT_STATED ("a sweep of obvious liquidity") | A06 |
| innercircletraders.net | NOT_STATED | A04 |
| innercircletrader.net | NOT_STATED ("the nearest buy-side and sell-side liquidity on the 15-minute chart") | A03 |
| fxnx.com | NOT_STATED ("a major liquidity pool") | A07 |
| quartersequence.com | NOT_STATED ("the next pool of liquidity") | A10 |
| ictflow.com | NOT_STATED | A12 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C2.4 Liquidity sweep / raid / stop raid / liquidity grab

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "A raid is a brief move through one of those pools that fails to continue." | A01 |
| fundingpips.com | "A liquidity sweep is a move that trades through one of those levels, triggers the stops, and then fails to continue." | A13 |
| velotrade.com | "a fast move beyond an obvious high or low that triggers the stop and pending orders resting there" | A08 |
| proea.app | "their sweep is a wick past the last confirmed swing low (or high)" | A14 |
| altrady.com | "Let price run the liquidity against your bias" | A02 |
| innercircletraders.net | "Wait for a clear liquidity sweep below a recent swing low" | A04 |
| innercircletrader.net | NOT_STATED ("If price has already swept the liquidity on one side") | A03 |
| ictflow.com | NOT_STATED ("the manipulation phase (Judas Swing/liquidity sweep)") | A12 |
| fxnx.com | NOT_STATED ("If price sweeps your target") | A07 |
| liquidityscan.io | NOT_STATED ("a sweep of obvious liquidity") | A06 |
| theinnercircletraders.com | NOT_STATED ("Price sweeps Asian low (inducement)") | A05 |
| quartersequence.com | NOT_STATED | A10 |
| ninjatrader.com | NOT_STATED | A09 |

### C2.5 Displacement

| Publisher | Definition quote | Page |
|---|---|---|
| fundingpips.com | "Displacement is a strong, fast move away from the sweep, usually made of one or more large-bodied candles with little overlap." | A13 |
| ictkillzone.com | "Displacement is the move that proves the raid was a turning point rather than noise." | A01 |
| liquidityscan.io | "displacement — a fast, body-heavy expansion that breaks structure" | A06 |
| innercircletraders.net | "a strong displacement candle forms. This candle is noticeably larger than the candles around it" | A04 |
| fxnx.com | "must close outside the high/low range of the previous three candles" | A07 |
| velotrade.com | "Price moves away from the level with strong, directional candles" | A08 |
| innercircletrader.net | "the breaking candle should close decisively and leave a fair value gap behind" | A03 |
| altrady.com | "a strong move that leaves a fair value gap" | A02 |
| ictflow.com | NOT_STATED ("identify the displacement FVG") | A12 |
| theinnercircletraders.com | NOT_STATED | A05 |
| quartersequence.com | NOT_STATED | A10 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C2.6 Market structure shift (MSS) / break of structure (BOS) / change of character (CHoCH)

| Publisher | Definition quote | Page |
|---|---|---|
| fundingpips.com | "A market structure shift (MSS) is a break of the most recent short-term swing point in the opposite direction of the prior move." | A13 |
| ictkillzone.com | "The MSS is the displacement closing through the short-term swing that formed just before or during the raid" | A01 |
| quartersequence.com | "a forceful break of the last short-term swing, after price has first run the stops" | A11 |
| liquidityscan.io | "a **Break of Structure (BOS)** for continuation or a **Change of Character (CHoCH)** for reversal" | A06 |
| theinnercircletraders.com | "a Change of Character (CHoCH) signals a potential reversal, while a Break of Structure (BOS) confirms continuation" | A05 |
| velotrade.com | "price should displace up and close above the most recent lower high" | A08 |
| altrady.com | "a **market structure shift (MSS)**, the first break against the trend, hints at a reversal" | A02 |
| proea.app | "an MSS is a CHoCH made with displacement" | A14 |
| innercircletraders.net | "look for a short-term market structure shift to the upside" | A04 |
| innercircletrader.net | NOT_STATED ("Watch for a Market Structure Shift") | A03 |
| ictflow.com | NOT_STATED ("confirm the MSS after the sweep") | A12 |
| fxnx.com | NOT_STATED ("be formed by a strong displacement candle that breaks previous market structure") | A07 |
| ninjatrader.com | NOT_STATED | A09 |

### C2.7 Change in state of delivery (CISD)

| Publisher | Definition quote | Page |
|---|---|---|
| proea.app | "a closed candle that finishes beyond the opening price of the run of opposite candles that made the latest high or low" | A14 |
| quartersequence.com | NOT_STATED (uses "qCISD", "a qCISD close at the same level does the same job") | A10 |
| ictkillzone.com | NOT_STATED | A01 |
| innercircletraders.net | NOT_STATED | A04 |

### C2.8 Power of three / AMD (accumulation, manipulation, distribution) / Judas swing

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "ICT describes each day or week as accumulation, manipulation and distribution" | A02 |
| ictkillzone.com | "a range builds (accumulation), a raid takes one side (manipulation, often called the Judas swing)" | A01 |
| ictflow.com | "wait for the AMD pattern — the manipulation phase (Judas Swing/liquidity sweep)" | A12 |
| innercircletrader.net | NOT_STATED | A03 |
| fundingpips.com | NOT_STATED | A13 |

### C2.9 Inducement

| Publisher | Definition quote | Page |
|---|---|---|
| theinnercircletraders.com | NOT_STATED ("Price sweeps Asian low (inducement)") | A05 |

### C2.10 SMT divergence / SSMT

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "compare two closely related markets and see whether both took their liquidity" | A01 |
| quartersequence.com | "the **SSMT** confirms the bias - the crack in correlation" | A10 |
| proea.app | NOT_STATED | A14 |

## C3 — Entry

### C3.1 Fair value gap (FVG)

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "An FVG is a three-candle pattern where the middle candle moves so far" | A01 |
| altrady.com | "a three-candle pattern where a strong middle candle leaves a gap between the first candle's high and the third candle's low" | A02 |
| innercircletraders.net | "three consecutive candles where the middle candle is so large and fast that the wicks of the first and third candles do not overlap" | A04 |
| fundingpips.com | "a three-candle imbalance where the wicks of the first and third candles do not overlap" | A13 |
| fxnx.com | "a three-candle formation where a large impulse candle creates an imbalance between buyers and sellers" | A07 |
| liquidityscan.io | "In a bullish case, the gap is the space between candle one's high and candle three's low" | A06 |
| quartersequence.com | "fair value gaps appear when price breaks them with force" | A11 |
| innercircletrader.net | NOT_STATED ("the fair value gap left behind during the displacement leg") | A03 |
| theinnercircletraders.com | NOT_STATED | A05 |
| ictflow.com | NOT_STATED ("the displacement FVG") | A12 |
| velotrade.com | NOT_STATED (links to a separate FVG lesson) | A08 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C3.2 Consequent encroachment (CE)

| Publisher | Definition quote | Page |
|---|---|---|
| fxnx.com | "Consequent Encroachment (CE) is the exact 50% midpoint of the Fair Value Gap." | A07 |
| ictkillzone.com | "Consequent encroachment (CE) is the midpoint of that gap and is a common limit-entry level." | A01 |
| liquidityscan.io | "the exact 50% midpoint of the gap" | A06 |
| innercircletraders.net | "the consequent encroachment is simply the 50% midpoint of the fair value gap zone" | A04 |
| fundingpips.com | "which ICT calls consequent encroachment" | A13 |
| ictflow.com | NOT_STATED ("Enter at the CE.") | A12 |
| altrady.com | NOT_STATED | A02 |
| innercircletrader.net | NOT_STATED | A03 |
| theinnercircletraders.com | NOT_STATED | A05 |
| proea.app | NOT_STATED | A14 |
| quartersequence.com | NOT_STATED | A10 |

### C3.3 Order block (OB) and mean threshold

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "An order block is the last opposite-colour candle before a strong move that breaks structure" | A02 |
| liquidityscan.io | "An **Order Block** is the last opposing candle before an impulsive move." | A06 |
| ictkillzone.com | "the last opposing candle before the displacement" (mean threshold: "50% of the order block's body (open to close)") | A01 |
| liquidityscan.io (mean threshold) | "the mean threshold — 50% of the OB's full range" | A06 |
| fxnx.com | NOT_STATED ("a major Daily order block") | A07 |
| velotrade.com | NOT_STATED (links to a separate OB lesson) | A08 |
| innercircletrader.net | NOT_STATED ("leaves behind a fair value gap and an order block") | A03 |
| innercircletraders.net | NOT_STATED ("a higher timeframe FVG or order block") | A04 |
| theinnercircletraders.com | NOT_STATED ("an Order Block, Fair Value Gap, or Breaker Block") | A05 |
| ictflow.com | NOT_STATED ("daily PD Array (FVG, OB, or BPR)") | A12 |
| quartersequence.com | NOT_STATED | A10 |
| fundingpips.com | NOT_STATED | A13 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C3.4 Breaker block

| Publisher | Definition quote | Page |
|---|---|---|
| theinnercircletraders.com | NOT_STATED (named only as one of the PD array entry zones) | A05 |
| altrady.com | NOT_STATED ("including order blocks, fair value gaps, breaker blocks and old highs and lows") | A02 |
| liquidityscan.io | NOT_STATED ("An order block broken on a closing basis often becomes a breaker block") | A06 |
| ictkillzone.com | NOT_STATED (links a separate breaker-block guide) | A01 |

### C3.5 Balanced price range (BPR)

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "A balanced price range forms where a new FVG overlaps an older opposing FVG" | A01 |
| ictflow.com | NOT_STATED ("daily PD Array (FVG, OB, or BPR)") | A12 |
| fxnx.com | NOT_STATED | A07 |

### C3.6 Optimal trade entry (OTE)

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "OTE is the zone between the 62% and 79% Fibonacci retracement of a swing, with 70.5% as the level many ICT traders watch." | A02 |
| fundingpips.com | "an optimal trade entry (OTE) zone between the 62% and 79% retracement of a swing" | A13 |
| ictkillzone.com | "the 62–79% retracement of the displacement leg, measured from the raid extreme" | A01 |
| innercircletrader.net | NOT_STATED | A03 |
| fxnx.com | NOT_STATED | A07 |

### C3.7 PD array (premium/discount array)

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "Premium and discount arrays are the reaction zones ICT ranks by importance" | A02 |
| fxnx.com | "An H4 or Daily PD Array (Premium/Discount Array)" | A07 |
| ictkillzone.com | "PD Array — Where Exactly to Enter" | A01 |
| theinnercircletraders.com | "a Premium or Discount Array — an Order Block, Fair Value Gap, or Breaker Block" | A05 |
| ictflow.com | "Mark the specific daily PD Array (FVG, OB, or BPR)" | A12 |
| innercircletraders.net | NOT_STATED ("used by many ICT traders as their primary setup timeframe") | A04 |
| quartersequence.com | "the higher-timeframe zone price is expected to react from, like a gap or an extension level" | A10 |
| liquidityscan.io | NOT_STATED | A06 |

### C3.8 Precision swing point (PSP) / True Open

| Publisher | Definition quote | Page |
|---|---|---|
| quartersequence.com (PSP) | "A PSP - a Precision Swing Point - is a three-candle swing whose middle candle closes against the other assets" | A10 |
| quartersequence.com (True Open) | "the **True Open** sets the bias" | A10 |
| ictkillzone.com (time of day) | NOT_STATED | A01 |

### C3.9 Timeframe pairing (HTF read, LTF entry)

| Publisher | Definition quote | Page |
|---|---|---|
| fundingpips.com | "Traders take the bias from the 1-hour or 4-hour chart and execute on the 1-minute to 15-minute chart" | A13 |
| innercircletrader.net | "I use the 15-minute chart as the parent chart to identify liquidity and bias." | A03 |
| ictkillzone.com | "the point is to read direction on a higher chart and time the entry on a lower one" | A01 |
| ninjatrader.com | "Start by identifying the trend on a higher timeframe." | A09 |
| altrady.com | "On a lower timeframe, wait for price to break the last swing in your direction" | A02 |
| theinnercircletraders.com | "Daily Bias … on Daily chart", "PD Array Entry … 15M / 5M" | A05 |
| innercircletraders.net | "The higher timeframe is your filter. The lower timeframe is your execution tool." | A04 |
| fxnx.com | "Wait for an H4 candle to close bullish" | A07 |
| quartersequence.com | NOT_STATED (HTF PDA only) | A10 |

## C4 — Time

### C4.1 Kill zone / time window

| Publisher | Definition quote | Page |
|---|---|---|
| altrady.com | "Killzones are session windows when ICT expects the most meaningful moves" | A02 |
| fundingpips.com | "kill zones, the windows when sessions open and liquidity peaks" | A13 |
| ictkillzone.com | "the time windows he highlights around the Asian, London and New York sessions" | A01 |
| velotrade.com | "ICT traders call these windows kill zones" | A08 |
| fxnx.com | "restrict your entries strictly to the London Killzone (02:00-05:00 EST) and the New York Killzone (07:00-10:00 EST)" | A07 |
| theinnercircletraders.com | "The London Open and New York Open kill zones see the highest institutional participation" | A05 |
| ictflow.com | "Wait for the London or New York Killzone." | A12 |
| innercircletrader.net | "The Silver Bullet happens three times every trading day" | A03 |
| quartersequence.com | "the highest-probability window is **Q3 in Q3 in Q3**" | A10 |
| ninjatrader.com | NOT_STATED | A09 |
| liquidityscan.io | NOT_STATED ("the 5m/15m gap inside a kill-zone expansion") | A06 |

### C4.2 News-day condition

| Publisher | Definition quote | Page |
|---|---|---|
| velotrade.com | "High-impact data such as the US jobs report often spikes through a nearby high or low" | A08 |
| ictkillzone.com | "8:30 AM news falls inside it" | A01 |
| fundingpips.com | "some versions use 08:30 to 11:00 ET to centre it on US data releases" | A13 |
| altrady.com | NOT_STATED | A02 |
| fxnx.com | NOT_STATED | A07 |
| ictflow.com | NOT_STATED | A12 |
| theinnercircletraders.com | NOT_STATED | A05 |
| innercircletrader.net | NOT_STATED | A03 |

## C5 — Exit

### C5.1 Stop / stop loss placement

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "Stop beyond the raid extreme." | A01 |
| altrady.com | "Put the stop beyond the swept low or high" | A02 |
| fundingpips.com | "The stop loss in the ICT 2022 model goes beyond the extreme of the liquidity sweep." | A13 |
| velotrade.com | "the logical stop sits below the low of the sweep wick" | A08 |
| liquidityscan.io | "Just beyond the far edge of the gap" | A06 |
| fxnx.com | "Stop losses should always be placed based on the structural swing point that initiated the gap." | A07 |
| innercircletraders.net | "Place your stop loss below the low of the FVG zone." | A04 |
| innercircletrader.net | "Stop loss goes above the high of the candle that created the fair value gap." | A03 |
| ictflow.com | "Stop beyond the FVG." | A12 |
| quartersequence.com | "Stop: the wick extreme of the PSP candle." | A10 |
| proea.app | "If price later trades beyond the frozen extreme … the CISD is marked failed" | A14 |
| theinnercircletraders.com | "Stop loss goes beyond the array" | A05 |
| ninjatrader.com | NOT_STATED ("Plan your entry, stop, and target") | A09 |

### C5.2 Target / take profit

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "Targets are the sell-side liquidity below — first a nearer internal low" | A01 |
| altrady.com | "target the opposite liquidity, such as the next swing high" | A02 |
| fundingpips.com | "Target the draw on liquidity identified in step 1" | A13 |
| velotrade.com | "The natural target is the buy-side liquidity above" | A08 |
| ictflow.com | "the 2022 model uses the next liquidity pool as the primary target" | A12 |
| innercircletraders.net | "Target the nearest liquidity level below, such as a swing low or equal low." | A04 |
| innercircletrader.net | "a take profit at the next liquidity pool — typically a 1:3 risk-reward target" | A03 |
| quartersequence.com | "Targets sit at the next pool of liquidity" | A10 |
| fxnx.com | "you must identify your target (usually a swing high/low or a liquidity pool)" | A07 |
| liquidityscan.io | "Target: the next draw at 119,000." | A06 |
| theinnercircletraders.com | "target is the liquidity pool from Step 2" | A05 |
| ninjatrader.com | NOT_STATED | A09 |
| proea.app | NOT_STATED | A14 |

### C5.3 Internal range liquidity (IRL) / external range liquidity (ERL)

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "First target at the nearest opposing pool inside the range (internal range liquidity, IRL)" | A01 |
| ictflow.com | "partial exits at the first FVG in the path and full exit at the ERL target" | A12 |
| fundingpips.com | NOT_STATED | A13 |
| quartersequence.com | NOT_STATED | A10 |

### C5.4 Minimum risk-reward

| Publisher | Definition quote | Page |
|---|---|---|
| ictflow.com | "ICT teaches using at least a 3:1 minimum R:R for any 2022 model trade" | A12 |
| innercircletrader.net | "a take profit at the next liquidity pool — typically a 1:3 risk-reward target" | A03 |
| theinnercircletraders.com | "Stop below FVG low, target PWH — minimum 1:3 risk-reward" | A05 |
| velotrade.com | "Check the trade still offers a sensible reward relative to the stop" | A08 |
| liquidityscan.io | NOT_STATED (gives R multiples for one worked case only) | A06 |
| fxnx.com | NOT_STATED | A07 |

### C5.5 Trade management (partials, break-even)

| Publisher | Definition quote | Page |
|---|---|---|
| ictkillzone.com | "Our default is to take half at the first target and move the stop to break-even." | A01 |
| ictflow.com | "partial exits at the first FVG in the path and full exit at the ERL target" | A12 |
| fxnx.com | "Move your stop to break even only after price has created a new structural swing in your favour." | A07 |
| innercircletrader.net | "Close the trade or trail the stop within the same session." | A03 |
| fundingpips.com | "or take partial profit at an intermediate level" | A13 |

**Term count:** 30 terms (C1: 4, C2: 10, C3: 9, C4: 2, C5: 5).

---

# D — Overlap table

Information only. No decisions, no winner, no merge beyond `SAME` / `SINGLE` / `CONFLICT`. Two conditions are `SAME`
only when two or more **independence groups** (Section preamble, G1–G11) state the condition. Because G1 is
`RELATIONSHIP_UNCLEAR` and counted as one publisher, conditions carried only by innercircletraders.net,
innercircletrader.net and theinnercircletraders.com together are marked `SINGLE (G1 only)`.

## D1 — Bias

| Condition | Publishers stating it | Mark |
|---|---|---|
| Bias is taken from a higher timeframe (daily / H4 / 1H) before looking for entries | ictkillzone, altrady, fundingpips, fxnx, ninjatrader, G1 | SAME |
| No setups against the HTF bias | ictkillzone, fxnx, G1 | SAME |
| Bias ladder from quarterly → monthly → weekly → daily | ictflow only | SINGLE |
| Bias must be written down before the session | ictkillzone only | SINGLE |
| Unclear bias (weekly vs daily disagree) means stand aside | ictkillzone only | SINGLE |
| Bias requires an H4 close to confirm | fxnx only | SINGLE |
| Bias anchor is a "True Open" level | quartersequence only | SINGLE |

## D2 — Draw on liquidity

| Condition | Publishers stating it | Mark |
|---|---|---|
| Target is named before entry, from an HTF pool | ictkillzone, fundingpips, G1, ictflow, altrady | SAME |
| DOL is the previous week's high/low or an HTF PD array | ictflow only | SINGLE |
| No DOL = no trade | G1 only | SINGLE (G1 only) |
| DOL doubles as the profit target | fundingpips, ictkillzone, ictflow | SAME |

## D3 — Buy-side / sell-side liquidity

| Condition | Publishers stating it | Mark |
|---|---|---|
| BSL above highs, SSL below lows | ictkillzone, altrady, fundingpips, velotrade, G1 | SAME |
| Pools cluster at equal highs/lows, prior day, session extremes | velotrade, ictkillzone, fundingpips, altrady | SAME |
| Seven liquidity references in a stated priority order | innercircletrader.net only | SINGLE (G1 only) |
| Which pool was taken decides which pool is next | ictkillzone, innercircletrader.net | SAME (two independence groups) |
| Rank of pool strength by resting-order count | innercircletrader.net only | SINGLE (G1 only) |

## D4 — Swing high / swing low

| Condition | Publishers stating it | Mark |
|---|---|---|
| Three-candle swing, middle candle is the extreme | quartersequence, fundingpips | SAME |
| Swing exists only after the next candle closes | quartersequence only | SINGLE |
| Swing confirmed by three candles on each side | proea only | CONFLICT (with the three-candle definition above) |
| A five-candle swing is what many tools use instead | quartersequence only | SINGLE |
| Swing sizes ranked short / intermediate / long term | quartersequence only | SINGLE |

## D5 — Liquidity sweep

| Condition | Publishers stating it | Mark |
|---|---|---|
| Wick beyond the level, then a close back inside | velotrade, ictkillzone, fundingpips | SAME |
| The move must fail to continue | ictkillzone, fundingpips | SAME |
| Only pre-marked levels count as sweeps | velotrade only | SINGLE |
| The sweep on its own is not an entry | ictkillzone, velotrade, G1 | SAME |
| Sweep must sit inside a kill zone | ictkillzone, ictflow, innercircletrader.net | SAME |
| Sweep = the Judas swing / manipulation phase | ictkillzone, ictflow | SAME |
| Breakout vs sweep decided by the close and the retest | velotrade only | SINGLE |

## D6 — Displacement

| Condition | Publishers stating it | Mark |
|---|---|---|
| Large bodies, little overlap between candles | ictkillzone, fundingpips, velotrade, G1 | SAME |
| Displacement must break structure | liquidityscan, fundingpips, ictkillzone | SAME |
| Displacement must leave an FVG | ictkillzone, altrady, G1, ictflow | SAME |
| Quantified threshold: body ≥ 1.5× ATR(14) | fundingpips only | SINGLE |
| Quantified threshold: expansion ≥ 1.5× recent average range | liquidityscan only | CONFLICT (with fundingpips' ATR measure) |
| Quantified threshold: middle candle closes outside the prior three candles' range | fxnx only | CONFLICT (with the other two measures) |
| Judged by eye, "not by a formula" | ictkillzone only | CONFLICT (with the three numeric rows above) |
| Small wicks relative to the bodies | ictkillzone, fxnx | SAME |

## D7 — Market structure shift

| Condition | Publishers stating it | Mark |
|---|---|---|
| Close through the most recent short-term swing, against the prior move | ictkillzone, fundingpips, velotrade, altrady | SAME |
| MSS must be produced by displacement | ictkillzone, proea, innercircletrader.net | SAME |
| BOS = continuation, CHoCH = reversal, as two separate labels | liquidityscan, G1, quartersequence | SAME |
| CHoCH is only the SMC label for a similar idea, not a separate event | ictkillzone only | CONFLICT (with the row above) |
| Entry trigger may be a CISD instead of an MSS | proea only | CONFLICT (with rows requiring an MSS) |
| Trigger may be a PSP or a qCISD instead | quartersequence only | SINGLE |
| MSS is not required if the sweep fails | — no page states this | not applicable (no row) |

## D8 — Fair value gap

| Condition | Publishers stating it | Mark |
|---|---|---|
| Three-candle pattern, wicks of candle 1 and 3 do not overlap | ictkillzone, altrady, G1, fxnx, fundingpips, liquidityscan | SAME |
| Bullish gap runs from candle 1's high to candle 3's low | ictkillzone, G1, altrady, liquidityscan | SAME |
| Gap must be created by displacement | ictkillzone, altrady, G1, ictflow, fundingpips | SAME |
| HTF gap as target, LTF gap as entry | G1, fxnx | SAME |
| Gap must sit in premium (short) / discount (long) | ictkillzone, G1, liquidityscan, fxnx | SAME |
| Gap boundaries are mechanical, needing no refinement | liquidityscan only | SINGLE |
| Gap must be the first one after the MSS | ictkillzone only | SINGLE |
| Partially filled gaps distrusted | liquidityscan only | SINGLE |

## D9 — Consequent encroachment

| Condition | Publishers stating it | Mark |
|---|---|---|
| CE = exact 50% midpoint of the gap | fxnx, ictkillzone, liquidityscan, G1, fundingpips | SAME |
| Limit entry is placed at CE | ictkillzone, fxnx, liquidityscan, ictflow, fundingpips | SAME |
| Near edge of the gap is an acceptable alternative entry | ictkillzone, fundingpips | SAME |
| Split the entry: half at the near edge, half at CE | fxnx only | SINGLE |
| A close beyond CE invalidates the setup | fxnx only | SINGLE |
| CE is the stop reference | G1 only | SINGLE (G1 only) |

## D10 — Order block

| Condition | Publishers stating it | Mark |
|---|---|---|
| OB = last opposing candle before the displacement | altrady, liquidityscan, ictkillzone | SAME |
| OB entry at the candle's open price | liquidityscan only | SINGLE |
| OB entry at the mean threshold | ictkillzone, liquidityscan | SAME |
| Mean threshold = 50% of the OB **body** (open to close) | ictkillzone only | CONFLICT (with the row below) |
| Mean threshold = 50% of the OB's **full range** | liquidityscan only | CONFLICT (with the row above) |
| OB is an alternative to the FVG entry, not a requirement | ictkillzone, altrady | SAME |
| OB zone may be refined to the body on HTF | liquidityscan only | SINGLE |
| A broken OB becomes a breaker block | liquidityscan only | SINGLE |

## D11 — Premium / discount

| Condition | Publishers stating it | Mark |
|---|---|---|
| Range split at its 50% level; above = premium, below = discount | ictkillzone, altrady, fundingpips, G1 | SAME |
| Buy in discount, sell in premium | altrady, ictkillzone, fundingpips, liquidityscan, G1 | SAME |
| The range measured is the weekly/daily dealing range | ictkillzone only | CONFLICT (with the row below) |
| The range measured is the most recent swing range | G1 only | CONFLICT (with the row above) |
| Equilibrium is the page's name for the 50% level | ictkillzone only | SINGLE |
| A zone on the wrong side of the range is skipped | ictkillzone, fxnx | SAME |

## D12 — Optimal trade entry

| Condition | Publishers stating it | Mark |
|---|---|---|
| OTE = the 62%–79% retracement zone | altrady, fundingpips, ictkillzone | SAME |
| 70.5% is a watched level inside the zone | altrady only | SINGLE |
| Measured from the raid extreme to the displacement extreme | ictkillzone only | CONFLICT (with the row below) |
| Measured on "a swing" without naming the anchors | altrady, fundingpips | CONFLICT (with the row above) |
| OTE is optional / one of several entry tools | ictkillzone, altrady | SAME |

## D13 — Kill zone / time window

| Condition | Publishers stating it | Mark |
|---|---|---|
| London and New York are the windows that matter | ictkillzone, altrady, fundingpips, fxnx, velotrade, ictflow, G1 | SAME |
| London window = 02:00–05:00 New York time | ictkillzone, fundingpips, fxnx | SAME |
| New York window = 07:00–09:00 ET | ictkillzone only | CONFLICT (with the two rows below) |
| New York window = 07:00–10:00 ET | fundingpips, fxnx | CONFLICT (with the rows above and below) |
| New York window = 08:30–11:00 ET | fundingpips only | CONFLICT (with the rows above) |
| Silver Bullet windows = 03:00–04:00, 10:00–11:00, 14:00–15:00 NY | innercircletrader.net, ictkillzone | SAME |
| Entries outside the window do not qualify | fxnx, ictflow, G1, ictkillzone | SAME |
| Asian session only builds the range, no entries there | ictkillzone only | SINGLE |
| Highest-probability window is Q3-in-Q3-in-Q3, ≈ 09:00–10:30 NY | quartersequence only | SINGLE |
| DST shifts the local clock, not the New York labels | fundingpips, G1, ictkillzone | SAME |

## D14 — Power of three / AMD / Judas swing

| Condition | Publishers stating it | Mark |
|---|---|---|
| Day or week = accumulation, manipulation, distribution | altrady, ictkillzone, ictflow | SAME |
| The manipulation leg is the Judas swing | ictkillzone, ictflow | SAME |
| AMD applies to a day **and** a week | altrady only | SINGLE |

## D15 — SMT / SSMT

| Condition | Publishers stating it | Mark |
|---|---|---|
| SMT compares two closely related markets at the same level | ictkillzone only | SINGLE |
| SMT is optional, not part of the core sequence | ictkillzone only | SINGLE |
| SSMT = sweep failure in correlation, used as bias confirmation | quartersequence only | SINGLE |
| Divergence decides **which** asset to trade (the Diverger) | quartersequence only | SINGLE |

## D16 — Internal / external range liquidity

| Condition | Publishers stating it | Mark |
|---|---|---|
| First target = nearest pool inside the range (IRL) | ictkillzone only | SINGLE |
| Final target = external range liquidity (ERL) | ictkillzone, ictflow | SAME |
| Partial exit at the first internal level on the way | ictkillzone, ictflow | SAME |

## D17 — Stop

| Condition | Publishers stating it | Mark |
|---|---|---|
| Stop beyond the sweep extreme | ictkillzone, altrady, fundingpips, velotrade | SAME |
| Stop beyond the FVG candle / FVG zone | G1 | SINGLE (G1 only) |
| Stop beyond the structural swing that launched the leg | fxnx, liquidityscan | SAME |
| Stop just beyond the far edge of the gap | liquidityscan only | SINGLE |
| Stop beyond the OB extreme | liquidityscan only | SINGLE |
| Stop beyond the PSP wick extreme | quartersequence only | SINGLE |
| Add a buffer for spread / for the sweep wick | fundingpips, G1, liquidityscan | SAME |
| Stop must be sized to survive the raid, not tightened blindly | ictkillzone, fundingpips | SAME |
| Structural stop too wide → trade fewer contracts | ictkillzone only | SINGLE |

## D18 — Target

| Condition | Publishers stating it | Mark |
|---|---|---|
| Target = the next opposing liquidity pool | ictkillzone, altrady, fundingpips, velotrade, ictflow, G1, quartersequence, fxnx, liquidityscan | SAME |
| Partial at the first internal pool, rest at the DOL | ictkillzone, ictflow, fxnx | SAME |
| Minimum 3:1 reward-to-risk required | ictflow, G1 | SAME |
| Target may be a measured-move projection (2.5×–4×) | quartersequence only | CONFLICT (with liquidity-pool targets above) |
| Cancel the trade if the target is swept before entry | fxnx only | SINGLE |

## D19 — News-day condition

| Condition | Publishers stating it | Mark |
|---|---|---|
| News releases are a stated context for sweeps | velotrade, ictkillzone, fundingpips | SAME |
| 8:30 ET news sits inside the New York window | ictkillzone, fundingpips | SAME |
| Size down or wait for the first spike to settle on news | velotrade only | SINGLE |
| News trading is allowed but the stop can fill away from its price | velotrade only | SINGLE |

## D20 — Trade management

| Condition | Publishers stating it | Mark |
|---|---|---|
| Take partial profit at the first pool | ictkillzone, ictflow, fxnx | SAME |
| Move the stop to break-even after the first target | ictkillzone only | SINGLE |
| Move to break-even only after a new structural swing | fxnx only | CONFLICT (with the row above) |
| Close or trail within the same session | G1 only | SINGLE (G1 only) |

## D21 — CISD / PSP / infrastructure terms

| Condition | Publishers stating it | Mark |
|---|---|---|
| CISD closes through the open of the run into the extreme | proea only | SINGLE |
| CISD line freezes on first print and can be marked failed | proea only | SINGLE |
| CISD can fire before the MSS | proea only | CONFLICT (with the MSS-required rows in D7) |
| PSP requires a three-candle swing pivot plus a divergent close | quartersequence only | SINGLE |
| True Open sets bias and premium/discount | quartersequence only | SINGLE |
| Inducement is a sweep of a minor level before the real move | G1 only | SINGLE (G1 only) |

---

# E — Image index

**Status of every image in this file: `IMAGE_NOT_VIEWED`.** No image was opened, rendered or downloaded in this run;
the page-fetch tool returned text only. Consequently, for every row:
`candles numbered = UNSTATED`, `prices printed = UNSTATED`, `viewed = IMAGE_NOT_VIEWED`.
"Real market vs illustration" is filled only where the **page text** says so, and `UNSTATED` otherwise — that column
describes the page's claim, not a pixel inspection.

| Term | Image link | Caption / alt quote (page text) | Real vs illustration (as page says) | Candles numbered | Prices printed | Viewed | Negative? |
|---|---|---|---|---|---|---|---|
| OTE, FVG | https://cdn-web.altrady.com/ict_fvg_ote_diagram_bae3b076b0.webp | "Diagram of a bullish fair value gap … and an optimal trade entry zone between the 62% and 79% retracement" | illustration ("Diagram") | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Full setup sequence | https://cdn-web.altrady.com/ict_body_2_workflow_v2_dc13137c89.png | "The ICT sequence: structure, liquidity, imbalance, then entry in the OTE zone." | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Premium/discount, FVG | https://cdn-web.altrady.com/ict_body_3_zones_v2_7940b8cc8e.png | "Premium and discount around the range midpoint, and a fair value gap that price later revisits." | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Building blocks (structure, OB, FVG, P/D, OTE) | https://cdn-web.altrady.com/ict_body_1_takeaways_v2_54fa7451bb.png | "The five building blocks most ICT setups combine." | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Hero | https://cdn-web.altrady.com/ict_trading_explained_2026_a4979d58b5.png | "ict-trading-explained-2026.png" (file name only) | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Silver Bullet windows (time) | https://www.innercircletrader.net/wp-content/uploads/2023/12/Supply-and-Demand-trading-strategy-3.png | "ICT Silver Bullet strategy diagram showing the three one-hour windows" | illustration ("diagram") | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Sweep → MSS → FVG (whole setup) | https://innercircletrader.net/wp-content/uploads/2023/12/ICT-Silver-Bullet-Trading-Strategy.png | "liquidity sweep, market structure shift, and FVG entry inside the one-hour window" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Liquidity sweep (buy-side raid) | https://innercircletrader.net/wp-content/uploads/2023/12/Silver-Bullet-1.png | "price runs above relative equal highs and Asian high, taking buy-side liquidity" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| MSS + displacement + FVG/OB | https://innercircletrader.net/wp-content/uploads/2023/12/Silver-Bullet-2.png | "market structure shift to the downside after liquidity raid, leaving FVG and order block behind" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Entry, stop, target | https://innercircletrader.net/wp-content/uploads/2023/12/Silver-Bullet-3.png | "stop loss above the FVG candle high, take profit at previous low for 1:3 risk-reward" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| FVG definition | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.22.13-AM.png | "What Exactly is an ICT Fair Value Gap?" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| FVG formation | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.24.42-AM.png | "How Does an ICT Fair Value Gap Form on a Chart?" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Bullish FVG | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.26.14-AM.png | "Bullish Fair Value Gap" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Bearish FVG | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.27.06-AM.png | "Bearish Fair Value Gap" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Consequent encroachment | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.27.48-AM.png | "Consequent Encroachment (CE) of the FVG (sensitive area for price )" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| HTF vs LTF FVG | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.29.13-AM.png | "Higher Time Frame FVG vs Lower Time Frame FVG" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| HTF vs LTF FVG (second) | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.30.06-AM.png | "Higher Time Frame FVG vs Lower Time Frame FVG" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Bullish FVG trade setup | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.31.08-AM.png | "Bullish FVG Trade Setup" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Bearish FVG trade setup | https://innercircletraders.net/wp-content/uploads/2026/03/Screen-Shot-2026-03-11-at-2.32.09-AM.png | "Bearish FVG Trade Setup" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| FVG vs OB hero | https://liquidityscan.io/blog/images/fvg-vs-order-block-which-entry-zone-should-you-trade-hero.png | "FVG vs Order Block: Which Entry Zone Should You Trade?" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| HTF alignment (negative vs positive) | https://cdn.sanity.io/images/1tyytg47/production/5be4bf6b4c0bcc4f87b894a28119fd295533f907-1200x896.png | "On the left: a random M5 FVG failing (Liquidity Trap). On the right: an M5 FVG anchored to an H4 Order Block" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | **NEGATIVE (left panel, per caption)** |
| Displacement three-candle range rule | https://cdn.sanity.io/images/1tyytg47/production/42d0a04f744d54d79731ff87d1ad704d852c6d32-1200x896.png | "A diagram illustrating the 'Three-Candle Range Rule' for displacement." | illustration ("diagram") | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| CE / split entry / stop | https://cdn.sanity.io/images/1tyytg47/production/96ea823a741d9af2efca3bb74f301b3903ebfc33-1200x896.png | "Order A at the start of the gap, Order B at the 50% Consequent Encroachment (CE) line" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Five-filter checklist | https://cdn.sanity.io/images/1tyytg47/production/a5b8bdf85506941c58ce7018939c27ed3afa4f20-1200x896.png | "summarizing the HTF Bias, Displacement Rule, Killzone, CE Invalidation, and Target Liquidity" | illustration ("infographic") | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| FVG entry filter hero | https://fxnx.com/_next/image?url=https%3A%2F%2Fcdn.sanity.io%2Fimages%2F1tyytg47%2Fproduction%2F1c20f2e92e226ed5370c39266952e8fb377b99c2-1376x768.png&w=3840&q=75 | "FVG Entry Filter: Mechanical Rules for HTF Bias" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| 2022 model hero | https://images.ctfassets.net/4jb7onvr59r3/3d4fvg1Kawut9oVhYpgkTK/007a8bddf21dca3575aa290595bd9517/The-ICT-2022-Model-Explained.jpg | "The-ICT-2022-Model-Explained" (file name only) | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| 2022 model framework | https://ictflow.com/_next/image?url=%2Fimages%2Famd.png&w=1200&q=75 | "ICT 2022 Model: Setup Rules, Context and Limitations" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Site graphic (not a chart) | https://innercircletraders.net/wp-content/uploads/2025/11/heading-bird.png | no caption text | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Site graphic (not a chart) | https://innercircletraders.net/wp-content/uploads/2025/11/1000510057.jpg | no caption text | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Author avatar (not a chart) | https://www.ictkillzone.com/assets/author-michael-phillips.jpg | "Michael Phillips, author of ICTKillzone.com" | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Author avatar (not a chart) | https://liquidityscan.io/blog/authors-photos/haykpp.jpg | author photo | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Author avatar (not a chart) | https://cdn.sanity.io/images/1tyytg47/production/940a425f883b5eeaa5c49a041bee6332e6f5fb83-1024x1024.jpg | author photo | UNSTATED | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |
| Editorial photo (not a chart) | https://ninjatrader.com/media/getmedia/9c320d08-ec6d-4ab8-af3a-9c1129bcd27b/Man-in-wheelchair-at-home-desk.jpg | "Man in a wheelchair trading at a desktop computer in a home office" | photo, not a chart | UNSTATED | UNSTATED | IMAGE_NOT_VIEWED | no |

## E2 — Charts on opened pages that have **no image URL** in the page text

These exist as inline rendered charts or schematics in the fetched text; they cannot be listed as links, so they are
recorded by caption only, all `IMAGE_NOT_VIEWED`.

| Term | Page | Caption quote as written | Real vs illustration | Negative? |
|---|---|---|---|---|
| Stop / target / IRL / ERL | A01 ictkillzone.com | "Schematic of the hypothetical example below, not a real chart." | illustration, per page ("not a real chart") | no |
| Sweep anatomy | A08 velotrade.com | "Illustrative prices." (sell-side sweep chart) | illustration, per page ("Illustrative prices") | no |
| Sweep vs breakout | A08 velotrade.com | "**Breakdown, not a sweep.**" | UNSTATED | **NEGATIVE (per caption)** |
| Premium/discount, True Open | A10 quartersequence.com | "Illustrative" | illustration, per page | no |
| CISD replay | A14 proea.app | "SIM · 15m · simulated" | illustration, per page ("simulated") | no |
| CISD failure case | A14 proea.app | "In the lesson's failure case, a wick reaches 95 by 09:20" | UNSTATED | **NEGATIVE (per text)** |
| 5-step flowchart | A05 theinnercircletraders.com | "Five sequential boxes labelled: Step 1 Daily Bias on Daily chart…" | illustration ("flowchart") | no |

No numeric case file was created in this stage.

---

# F — Limits (what could not be opened or seen)

1. **No image was viewed anywhere.** Every image row is `IMAGE_NOT_VIEWED`. No method (direct or search
   intermediary) can be reported for any image, and no claim is made about whether candles are numbered or prices
   are printed. This is not the owner's browser and no image was fetched outside the page text.
2. **No video was watched or opened.** Several pages link to video (ictkillzone links the 2022 mentorship playlist;
   quartersequence and proea cite video timestamps). Only page text was used. The video timestamps quoted inside
   those pages were not checked against the videos.
3. **Chunk coverage is partial.** Each page was read in content chunks; the chunks read are recorded in Section A.
   For A01, A02, A03, A05, A08, A09, A10, A11, A13, A14 the later chunks were not read, so a term used only in an
   unread chunk would be missing from Section C. For A06, A07, A04 and A12 the read coverage was effectively
   complete. This is the main risk of omission in this stage.
4. **A03 (innercircletrader.net) shows a paid course promotion** ("Enrol — $149", paid PDF). The article text itself
   was fully readable without login, so the page was used; the paid material behind those links was not opened and
   is not used.
5. **No login, paywall or pirated page was opened.** One previously-registered URL (`scribd.com` notes document) was
   deliberately not opened in this run.
6. **Independence could not be resolved for G1.** No opened page shows a shared author, owner or network across
   innercircletraders.net, innercircletrader.net and theinnercircletraders.com, so they are counted as one publisher
   and marked `RELATIONSHIP_UNCLEAR`. If Stage 2 can establish they are separate, several `SINGLE (G1 only)` rows
   become `SAME`.
7. **Four publishers gave no ordered step list** (liquidityscan.io, proea.app) — marked `NO_ORDERED_STEPS`; and one
   page (fxnx.com) numbers its checklist inconsistently (1–4 then 1 again), recorded as written rather than
   renumbered.
8. **Silence is not recorded as agreement.** Many `NOT_STATED` cells in Section C mean the page either does not use
   the term or uses it without defining it; the two cases were not distinguished beyond the parenthetical note.
9. **No page dated after 2026-11-09 was encountered.** Several pages are 2026-dated and were used as web text only;
   no market data was read, no chart was measured, and no result claimed by any publisher was verified.
10. **Nothing was generated for Stage 2.** The `G` list below is a proposed grouping of terms only, with no decisions.

---

# G — Proposed batches of terms for Stage 2 (list only, no decisions)

Grouping is by the role the term plays in the step lists of Section B. Order within a batch is alphabetical, not
priority.

**Batch 1 — Direction and context (4 terms)**
`Bias (daily/HTF bias)`, `Draw on liquidity`, `Dealing range`, `Premium / discount (equilibrium)`

**Batch 2 — Liquidity and structure (7 terms)**
`Swing high / swing low`, `Equal highs / equal lows`, `Buy-side / sell-side liquidity`, `Liquidity sweep / raid`,
`Internal / external range liquidity (IRL/ERL)`, `Inducement`, `SMT divergence / SSMT`

**Batch 3 — Displacement and structure break (3 terms)**
`Displacement`, `Market structure shift (MSS/BOS/CHoCH)`, `Change in state of delivery (CISD)`

**Batch 4 — Entry zones (7 terms)**
`Fair value gap (FVG)`, `Consequent encroachment (CE)`, `Order block (OB) and mean threshold`, `Breaker block`,
`Balanced price range (BPR)`, `Optimal trade entry (OTE)`, `PD array`

**Batch 5 — Timing (2 terms)**
`Kill zone / time window`, `Power of three / AMD / Judas swing`

**Batch 6 — Trade construction (5 terms)**
`Timeframe pairing`, `Stop / stop loss placement`, `Target / take profit`, `Minimum risk-reward`,
`Trade management (partials, break-even)`

**Batch 7 — Conditional and model-specific (2 terms)**
`News-day condition`, `Precision swing point (PSP) / True Open`

Total: 30 terms in 7 batches. No term is assigned a definition, a winner or a merged rule in this stage.
