# Understanding card — old low (`old_low`)

Windows extracted and read in full (`±100` words) this session: **15** (target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 3, `E2_2016`: 4, `E3_2017`: 3, `E4_2019_2022`: 3, `E5_2023_2024`: 2). Meets the 15-window budget.
Claims: U3K3-153, U3K3-154, U3K3-155, U3K3-156, U3K3-157, U3K3-158, U3K3-159, U3K3-160, U3K3-161, U3K3-162, U3K3-163

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- The algorithm reprices below an old low to trigger resting sell stops from current longs and breakout sellers, engineering sell-side liquidity at a discount.
  > "ifta Will reprice the Market below an old low to promote sell stops that will be residing there for current longholders"
  `[U3K3-153]` · `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` (E3_2017) · window `W0199` · `added_words: [algorithm, longs, reprices, resting, trigger]` · note: offset accumulation purpose below an old low; [sic-asr] 'ifta' for 'IPDA'

## (b) RECOGNITION (his criteria and his rejections)
- He locates sell-side liquidity pools directly below old lows (and buy-side above old highs), looking for sweeps and rejections there.
  > "what do we look for in price the liquidity pools just above an old high and just below an old low"
  `[U3K3-154]` · `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` (E2_2016) · window `W0196` · `added_words: [buy, highs, locates, lows, rejections, sell, side, sweeps]` · note: K2 seed window deepened
- He rejects taking a short trade unless price is obviously reaching for a clear downside draw such as a fair value gap or an old low.
  > "like a fair value Gap below price or a an old low the low price if it's not obvious that it wants to go"
  `[U3K3-155]` · `ICT-Mentorship-2023-September-05-2023-Live-ES-&-NQ-Tape-Reading-001.json` (E5_2023_2024) · window `W0201` · `added_words: [clear, downside, draw, reaching, rejects, short, taking, unless]` · note: REJECTION / stand-aside when draw toward old low is not obvious

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a prior swing low on the reference timeframe (15m, 1h, daily, weekly, monthly, or outside the 20/40/60-day lookback) that has remained unviolated over intervening bars, serving either as a downside target or as an offset-accumulation ('turtle soup') reversal trigger when swept and rejected
  `candle_observable: true` · derived from `U3K3-154`, `U3K3-153`, `U3K3-160` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- whether sell stops or breakout orders actually rest below a specific old low is inferred from market structure rather than directly visible on candles
  `candle_observable: false` · derived from `U3K3-153` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- When buying below an old low (or at a bullish order block or rejection block), his rule is to enter with a buy limit order rather than a buy stop.
  > "if buying on a bullish order block rejection block or below an old low ideal entry technique is buying on a limit"
  `[U3K3-156]` · `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` (E3_2017) · window `W0209` · `added_words: [buy, enter, rather, rule]` · note: explicit order-type rule: buy limit below an old low vs buy stop on breaker/FVG
- When targeting an old low on a short, he exits near or just above the old low because price does not have to trade all the way through it.
  > "just know that that's a good level to reach for an old low but they may not have to go through it ok"
  `[U3K3-157]` · `GbpUsd-Discussion-Post-Analysis-rough-edition-001.json` (E5_2023_2024) · window `W0206` · `added_words: [exits, near, short, targeting, way]` · note: conservative target exit near an old low

## (e) COMPARING INSTANCES
- He contrasts entry order types across discount arrays: buying below an old low uses a limit order, whereas breakers, mitigation blocks, voids, and FVGs use a stop order.
  > "if buying a bullish breaker or mitigation block the ideal entry technique is buying on a stop"
  `[U3K3-158]` · `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` (E3_2017) · window `W0209` · `added_words: [blocks, breakers, contrasts, fvgs, types, uses, voids, whereas]` · note: comparative execution matrix across discount arrays

## (f) INTERACTIONS
- When the dollar index makes a lower low below an old low while GBPUSD fails to make a higher high (SMT divergence), the drop below the old low is a false move for accumulation.
  > "this shows underlying weakness in the cable and this is actually a false move below the old low this is going to be accumulated"
  `[U3K3-159]` · `ICT-Forex-The-ICT-Smart-Money-Technique-or-SMT-001.json` (E1_EARLY_SERIES) · window `W0202` · `added_words: [accumulation, divergence, drop, fails, gbpusd]` · note: interaction between old low sweep and SMT divergence
- Once liquidity inside the 60-day IPDA lookback range is exhausted, price reaches for the next old low or high just outside the 60-day boundary.
  > "where that old low that's just outside of the last 60 days looking back there's an old low that may not be on this chart"
  `[U3K3-160]` · `ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-001.json` (E3_2017) · window `W0204` · `added_words: [day, exhausted, inside, ipda, liquidity, lookback, once, reaches]` · note: interaction with 60-day IPDA lookback range

## (g) TIMEFRAME
- He marks an old low on the daily or monthly chart (W0207) and extends it onto the hourly or 15-minute chart (W0203) to frame turtle soup or OTE setups.
  > "this is that old low that i extended on the daily chart now it's being visualized on an hourly time frame"
  `[U3K3-161]` · `2022-ICT-Mentorship-Episode-25-001.json` (E4_2019_2022) · window `W0200` · `added_words: [extends, marks, minute, monthly, ote, setups, soup, turtle, w0203, w0207]` · note: cross-timeframe projection of daily old low onto 1h/15m chart

## (h) FAILURE / INVALIDATION and DISCRETION
- After running sell stops below an old monthly low, price may not reach the opposing old monthly high; he warns against demanding perfection.
  > "even if it doesn't make it to that monthly high you still have the potential to find setups that would generate momentum in that direction"
  `[U3K3-162]` · `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now-Part-2-of-4-001.json` (E1_EARLY_SERIES) · window `W0207` · `added_words: [against, demanding, opposing, running, warns]` · note: failure to reach opposing monthly extreme after old low stop run

## (i) VARIANTS (kept parallel, never merged)
- Besides acting as a downside sell-stop target or turtle-soup buy level (W0203), a broken old low from further back on the chart can act as an upside resistance reference on a rally.
  > "clearing out the buy stops rolled all the way up through to 108.65 trading back to an old low that's not shown on this chart"
  `[U3K3-163]` · `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` (E2_2016) · window `W0208` · `added_words: [act, acting, besides, broken, downside, rally, resistance, sell, soup, stop, target, turtle, upside, w0203]` · note: parallel role: downside liquidity pool / turtle soup buy (W0199/W0203) vs broken old low retested from below as resistance (W0208)

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0196` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-1-Elements-Of-A-Trade-Setup-001.json` | `2364..2565` (201w) | `17b293605788` |
| `W0197` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-4-of-5-002.json` | `6212..6413` (201w) | `edf72b311a29` |
| `W0198` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-03-Institutional-Sponsorship-001.json` | `1469..1670` (201w) | `38dd52ef429a` |
| `W0199` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-09-Bread-&-Butter-Buy-Setups-001.json` | `165..366` (201w) | `a0f805b27ddc` |
| `W0200` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-25-001.json` | `4038..4239` (201w) | `31992258fdeb` |
| `W0201` | `E5_2023_2024` | `exact_kept_tsv` | `ICT-Mentorship-2023-September-05-2023-Live-ES-&-NQ-Tape-Reading-001.json` | `4717..4918` (201w) | `af4cca959ced` |
| `W0202` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-The-ICT-Smart-Money-Technique-or-SMT-001.json` | `2222..2423` (201w) | `2643327a4ae3` |
| `W0203` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-02-Framing-Low-Risk-Trade-Setups-001.json` | `752..953` (201w) | `4741da193dcb` |
| `W0204` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Using-IPDA-Data-Ranges-001.json` | `5856..6057` (201w) | `fd247dcc7730` |
| `W0205` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Charter-Price-Action-Model-2-Amplified-Lecture-001.json` | `1508..1709` (201w) | `3fe1d012a146` |
| `W0206` | `E5_2023_2024` | `exact_kept_tsv` | `GbpUsd-Discussion-Post-Analysis-rough-edition-001.json` | `8353..8554` (201w) | `eb8eac314727` |
| `W0207` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now-Part-2-of-4-001.json` | `1166..1367` (201w) | `db246fdc36f4` |
| `W0208` | `E2_2016` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-04-Interest-Rate-Effects-On-Currency-Trades-001.json` | `2243..2444` (201w) | `c794286a1e56` |
| `W0209` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-06-The-Million-Dollar-Swing-Setup-001.json` | `2049..2250` (201w) | `49b7b198b4ff` |
| `W0210` | `E4_2019_2022` | `exact_kept_tsv` | `ICT-Emini-S&P-500-AM-Session-Review-09-06-22-001.json` | `551..752` (201w) | `0299aa67e4e9` |
