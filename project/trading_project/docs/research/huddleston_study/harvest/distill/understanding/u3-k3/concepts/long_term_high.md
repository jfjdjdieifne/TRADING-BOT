# Understanding card — long term high (`long_term_high`)

**Status: THIN on literal `kept_concepts.tsv` phrase** — The literal unhyphenated singular phrase 'long term high' in kept_concepts.tsv has 10 hits across 8 transcripts in the corpus (<15). All 8 distinct transcripts with the exact unhyphenated singular phrase (W0121..W0128) plus 7 distinct transcripts containing ASR hyphenated/plural forms ('long-term high', 'long term highs', 'long-term highs', W0129..W0135) were extracted and read in full to complete 15 windows.
Windows extracted and read in full (`±100` words) this session: **15** (**8** exact phrase + **7** hyphenated/plural ASR variant; target 15) across **15** distinct transcripts (`E1_EARLY_SERIES`: 6, `E2_2016`: 2, `E3_2017`: 3, `E4_2019_2022`: 4).
Claims: U3K3-095, U3K3-096, U3K3-097, U3K3-098, U3K3-099, U3K3-100, U3K3-101, U3K3-102, U3K3-103, U3K3-104, U3K3-105

Every quoted line below is verbatim (≤25 words) from a `±100`-word window logged and read in full this session. Per Rule 2, `statement` in `claims.jsonl` carries the verbatim quote, `reading` carries the interpretation below, and `added_words` lists every word in `reading` absent from the window. Section (c) is explicitly an `ENGINEERING_HYPOTHESIS`, not his words. Empty sections read `NOT_IN_SOURCES`.

## (a) PURPOSE
- He uses long-term, intermediate-term, and short-term highs and lows to structure price hierarchy beyond simple higher-high/higher-low trend labels.
  > "i've outlined market structure in the idea of long term high long term low short-term high short-term low and in between those two"
  `[U3K3-095]` · `2022-ICT-Mentorship-Episode-12-001.json` (E4_2019_2022) · window `W0123` · `added_words: [beyond, hierarchy, highs, labels, lows, trend, uses]` · note: purpose of three-tier swing hierarchy

## (b) RECOGNITION (his criteria and his rejections)
- He defines a long-term high as an intermediate-term high flanked by lower intermediate-term highs on both its left and right (like a head and shoulders).
  > "every time you see a enemy term high that has a lower enemy term high to the left of it and enemy term high"
  `[U3K3-096]` · `ICT-Mentorship-Core-Content-Month-05-Open-Float-001.json` (E3_2017) · window `W0122` · `added_words: [defines, flanked]` · note: structural definition of long-term high; [sic-asr] 'enemy term high' for 'intermediate term high'
- In his 2022 rebalance framing, an intermediate-term high formed at an imbalance rebalance becomes a long-term high when flanked by lower intermediate-term highs.
  > "this is a long term high intermediate term high by definition they're both enemy and term highs because they have imbalances"
  `[U3K3-097]` · `2022-ICT-Mentorship-Episode-22-001.json` (E4_2019_2022) · window `W0127` · `added_words: [2022, becomes, flanked, formed, framing, rebalance]` · note: imbalance-rebalance recognition criterion
- He rejects retail traders' habit of hunting head-and-shoulders topping patterns on lower timeframes or at lows, stating genuine ones form at intermediate or long-term highs.
  > "generally price will form these genuinely at intermediate or long-term highs only and due to the low understanding of most retail traders"
  `[U3K3-098]` · `ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Head-Shoulders-Pattern-001.json` (E2_2016) · window `W0131` · `added_words: [genuine, habit, hunting, lows, ones, rejects, stating, timeframes, traders']` · note: REJECTION of retail topping patterns outside intermediate/long-term highs

## (c) OBSERVABLES — ENGINEERING_HYPOTHESIS (needs owner approval)
- a three-level nested swing peak: a short-term high is a local 3-bar/swing high; an intermediate-term high is a swing high flanked by lower short-term highs (or formed at an imbalance rebalance); a long-term high is an intermediate-term high flanked by lower intermediate-term highs on both left and right
  `candle_observable: true` · derived from `U3K3-096`, `U3K3-097` · **ENGINEERING_HYPOTHESIS — needs owner approval**
- because the right-hand lower intermediate-term high must form after the peak, a long-term high is only confirmable with lag after subsequent lower highs print
  `candle_observable: true` · derived from `U3K3-096`, `U3K3-099`, `U3K3-104` · **ENGINEERING_HYPOTHESIS — needs owner approval**

## (d) HOW HE TREATS IT
- Once a lower high and even lower high imply a long-term high has formed, he looks for short setups aligned with quarterly shift and seasonal tendency.
  > "if it is at least implying that an intermittent term or a potential long-term high is formed then I'm going to be looking for reasons"
  `[U3K3-099]` · `ICT-Mentorship-Core-Content-Month-12-Long-Term-Top-Down-Analysis-001.json` (E3_2017) · window `W0132` · `added_words: [aligned, imply, looks, once, seasonal, setups]` · note: top-down short framing after long-term high formation

## (e) COMPARING INSTANCES
- He prefers capturing the meat of the move between intermediate-term highs and lows rather than trying to pick the exact long-term high or low.
  > "there's a lot of opportunity between intermediate term highs and lows i don't mind missing the long-term high in a long-term low"
  `[U3K3-100]` · `2022-ICT-Mentorship-Episode-19-001.json` (E4_2019_2022) · window `W0133` · `added_words: [capturing, exact, meat, move, prefers, rather]` · note: comparative preference: trading between intermediate-term swings > picking long-term tops/bottoms

## (f) INTERACTIONS
- He links the formation of intermediate-term and long-term highs and lows to 12-month extremes in commercial traders' COT net positions and SMT divergence (W0132).
  > "trade with the trend of commercial traders okay because they they set in motion all of the intermediate term and long term highs and lows"
  `[U3K3-101]` · `ICT-W-E-N-T-Series-4-of-5-002.json` (E1_EARLY_SERIES) · window `W0130` · `added_words: [cot, divergence, formation, links, smt, traders', w0132]` · note: interaction with COT commercial extremes and SMT divergence

## (g) TIMEFRAME
- In top-down analysis he marks intermediate and long-term highs and lows on the monthly chart, while also nesting the same hierarchy on 1-hour charts (W0123).
  > "the monthly chart is we're looking at key levels we're looking at uh intermediate and long term highs and lows"
  `[U3K3-102]` · `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` (E2_2016) · window `W0129` · `added_words: [hierarchy, hour, marks, nesting, w0123]` · note: K2 seed claim verified in full window; monthly and fractal 1-hour application

## (h) FAILURE / INVALIDATION and DISCRETION
- When a monthly long-term high is swept, intraday 10–30 pip sweep rules fail to bound the move (which ran 400+ pips); he admits he has no exact science for the magnitude.
  > "obviously we can't use a 10 to 20 or 30 pip sweep idea let me deal with intraday charts looking for movements beyond"
  `[U3K3-103]` · `ICT-Forex-Time-&-Price-Theory-001.json` (E1_EARLY_SERIES) · window `W0124` · `added_words: [admits, bound, exact, fail, monthly, ran, rules, swept]` · note: honest caveat: no exact science for sweep magnitude beyond a monthly long-term high
- In real time, a newly formed high is ambiguous between a long-term high and an intermediate-term high until subsequent flanking swings form.
  > "now that tie made here could be a long-term high or it could be an enemy term high we don't know"
  `[U3K3-104]` · `ICT-Trading-Plan-Development-2-001.json` (E1_EARLY_SERIES) · window `W0134` · `added_words: [ambiguous, flanking, form, formed, intermediate, newly, real, subsequent, swings, until]` · note: real-time classification ambiguity noted by speaker

## (i) VARIANTS (kept parallel, never merged)
- In the 2022 public mentorship he states he simplified his teaching language to avoid requiring students to classify every short-, intermediate-, and long-term high.
  > "how do i classify this swing high is any term high versus a short term high in a long term high how does he know"
  `[U3K3-105]` · `2022-ICT-Mentorship-Episode-13-001.json` (E4_2019_2022) · window `W0125` · `added_words: [2022, avoid, every, intermediate, mentorship, simplified, states, students]` · note: pedagogical variant: 2022 simplified model vs full Larry Williams nested swing hierarchy (W0122)

## Windows Logged and Read This Session (`±100` words each)
| Window | Era | Match | Transcript | Word Range | SHA-256 (prefix) |
|---|---|---|---|---|---|
| `W0121` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Trading-Plan-Development-6-001.json` | `5489..5690` (201w) | `50e1d39cb18e` |
| `W0122` | `E3_2017` | `exact_kept_tsv` | `ICT-Mentorship-Core-Content-Month-05-Open-Float-001.json` | `2640..2841` (201w) | `50c77a3c28ea` |
| `W0123` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-12-001.json` | `867..1068` (201w) | `b9c3df11f891` |
| `W0124` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-Forex-Time-&-Price-Theory-001.json` | `1831..2032` (201w) | `4e2f48cb5422` |
| `W0125` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-13-001.json` | `6099..6300` (201w) | `90114d87b4e6` |
| `W0126` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `ICT-W-E-N-T-Series-Part-3-of-5-001.json` | `4579..4780` (201w) | `26f15a6078d4` |
| `W0127` | `E4_2019_2022` | `exact_kept_tsv` | `2022-ICT-Mentorship-Episode-22-001.json` | `3940..4141` (201w) | `6ba00c1b4561` |
| `W0128` | `E1_EARLY_SERIES` | `exact_kept_tsv` | `Essentials-To-ICT-Market-Structure-001.json` | `4591..4792` (201w) | `fd6ee5d895f2` |
| `W0129` | `E2_2016` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-02-The-Secrets-To-Selecting-High-Reward-Setups-001.json` | `5278..5479` (201w) | `04fe064cf1e5` |
| `W0130` | `E1_EARLY_SERIES` | `asr_hyphen_or_plural_variant` | `ICT-W-E-N-T-Series-4-of-5-002.json` | `4203..4404` (201w) | `edf72b311a29` |
| `W0131` | `E2_2016` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-03-Market-Maker-Trap-Head-Shoulders-Pattern-001.json` | `103..304` (201w) | `ec79d7c05993` |
| `W0132` | `E3_2017` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-12-Long-Term-Top-Down-Analysis-001.json` | `4229..4430` (201w) | `e7905426fe98` |
| `W0133` | `E4_2019_2022` | `asr_hyphen_or_plural_variant` | `2022-ICT-Mentorship-Episode-19-001.json` | `3282..3483` (201w) | `8b3b8f780b72` |
| `W0134` | `E1_EARLY_SERIES` | `asr_hyphen_or_plural_variant` | `ICT-Trading-Plan-Development-2-001.json` | `1880..2081` (201w) | `7ae84e6d25c1` |
| `W0135` | `E3_2017` | `asr_hyphen_or_plural_variant` | `ICT-Mentorship-Core-Content-Month-05-Ideal-Seasonal-Tendencies-001.json` | `695..896` (201w) | `5ebe55e23ca7` |
