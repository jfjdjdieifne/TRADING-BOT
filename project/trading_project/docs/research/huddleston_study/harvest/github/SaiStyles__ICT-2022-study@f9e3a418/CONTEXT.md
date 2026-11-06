# ICT Brain - the pipeline that was actually run

**The research is complete.** This file records what was built, in what order,
and where each stage's output lives. `README.md` is the public summary;
`backtest/findings.md` is the reasoning; `DECISIONS.md` is every ruling.

## The stages, in the order they happened

| # | stage | reads | writes | human check |
|---|---|---|---|---|
| 1 | **fetch transcripts** | `corpus/_index.md` | `transcripts/ep<NN>.md` | open a chart-heavy stretch: is the jargon intact? |
| 2 | **study** - one structured read per episode | `transcripts/` | `study/ep<NN>.md` | pick any line: can you land on the timestamp? |
| 3 | **synthesise** - de-linearise across episodes | `study/` | `THE-MODEL.md`, `study/_refinements.md` | every step traceable to the episodes that taught it |
| 4 | **bars** - raw DBN to clean session-aligned price | `data/raw/` | `bars/output/` | do the prices he quotes on camera appear in the front month? |
| 5 | **backtest** - test the rules, count every attempt | `bars/output/`, `THE-MODEL.md` | `backtest/findings.md`, `backtest/ledger.md` | does `n` match every result anyone has mentioned? |

**Stages 2, 3 and 5 are hand-written reasoning, not model output.**

### A stage that was tried and abandoned

An automated extraction pass (Gemini over video frames, then over transcript
chunks) ran for three days before being overtaken by stage 2. **Its code and
output were removed on 2026-09-04** - the hand-written `study/` pages cover all
40 available episodes while the automated pass reached ten, so nothing depended
on it. **The reasoning it produced is kept**, because it was the expensive part:
DECISIONS.md sections 10, 12, 13, 14, 15 and especially **19** (video vs
transcript, measured rather than argued) and **1** (provenance made checkable by
script rather than trusted). See section 25 for what was deleted and why.

## Final state

**154 hypotheses tested. Nothing survived out-of-sample.**

- `study/` - 41 pages covering all 40 available episodes. Ep28 excluded (156s, no captions).
- `THE-MODEL.md` - the synthesis: 9 layers, the clock, when not to trade, contested items, what cannot be coded.
- `bars/output/` - **5,319,303** front-month 1-minute bars, midnight-New-York, spreads filtered, 64 rolls, verified against five prices quoted on camera.
- `backtest/ledger.md` - every hypothesis ever tested, **n = 154**.
- **`reserve` spent once** (`backtest/reserve_used.md`). **Holdout never opened, and it stays that way** - it adjudicates a candidate that survived everything else, and none did.

**Do not re-open:** the holdout (findings 9), ES (section 20), the overnight-run
veto (section 22), episode 28 (section 19), the video pass (section 19), billing
(section 15), the removed extraction code (section 25).

### Every claim tested, and its verdict

| claim | source | verdict |
|---|---|---|
| **08:30-11:00 killzone** | ep02 [42:40] | **HALF SURVIVED.** Opportunity held on reserve (100th pctile) - but that is the volatility U-shape. Efficiency, the part that meant something, went **100th -> 26th pctile**. See findings 9 |
| 08:30-09:30 is where the setup forms | ep25 [34:43] | **Contradicted** - 13th percentile on efficiency. The value is all after 09:30 |
| London killzone 02:00-05:00 | ep03 [32:59] | **Contradicted for NQ** - 32nd percentile. ep08 [05:38] treats London as forex, so this is evidence against applying it to the index |
| Lunch is a trap | ep05 [10:04] | Ordinary hour - 63rd/33rd. Defensible as chop-avoidance, not special |
| Vetoes (Wednesday, mid-range) | ep37, ep32 | Right direction, **z = -2.65 best**, does not clear 3.0 |
| Displacement magnitude | ep05 [18:44] | **Flat across the whole sweep.** The number he never gives is not where the edge is. Question retired |
| Gold-standard pattern (FVG+OB+OTE) | ep41 [16:36] | **No edge.** -0.076R over 148 trades; after the timeframe and sequencing fixes, **-0.245R over 171**. More trades, worse result |
| Overnight-run veto | ep09 [15:15] | **RULED OUT by the builder**, section 22. Do not re-implement |
| **Fair value gap fills** | ep02 [17:53], 36 of 41 eps | **CONTRADICTED.** Gaps fill LESS than a matched same-size, same-hour, same-direction move retraces the same distance. 16 of 16 rows, z to **-59.9** |
| **Liquidity sweep reverses** | ep25 [28:36] | **FAILED OUT OF SAMPLE.** dev z = +3.10 -> reserve z = **-0.15**. Was best-of-12 on dev, which is what this looks like out of sample |
| **Order block is a level price reacts from** | ep17 [11:10], ep12 [44:02] | **No signal anywhere.** As a filter it rejects 0 of 396 (only ep12's "consecutive series" definition filters at all); as a gate z = -0.04; on return it is anti-predictive, z to **-9.35** |
| On-close macro | ep32 [11:32] | Right window (93rd pctile), sign matches published work, **too weak** at \|t\|>3.0 |
| Every entry gate | ep41 [16:36] | **None earns its place.** All four discarded better setups than they kept; displacement worst at z = -2.60 |

## Commands

Run with `%LOCALAPPDATA%\Programs\Python\Python312\python.exe` - Python is not on PATH.
Requires `databento`, `pandas`, `numpy`, `pyarrow`.

| command | does |
|---|---|
| `bars/build_bars.py` | raw DBN -> clean midnight-NY front-month bars. A few minutes. Regenerable, so `bars/output/` is not backed up |
| `bars/build_bars.py --roll-shift 3` | sensitivity run for the volume roll proxy - section 21.3 |
| `backtest/slices.py` | prints the slice calendar and holdout status. **Every test gets its data through `load()`**, which refuses the holdout |
| `backtest/fvg_study.py` | the fair value gap test - findings 4 |
| `backtest/primitive_study.py` | liquidity sweep and order block - findings 8 |
| `backtest/run_clock.py` | his named windows vs same-length controls; vetoes vs volatility-matched nulls - findings 3 |
| `backtest/run_setups.py` | the gold-standard pipeline and the funnel - findings 6 |
| `backtest/gate_value.py` | what each gate's refusals went on to do - findings 7 |
| `backtest/run_momentum.py` | the on-close macro vs published intraday momentum - findings 5 |
| `backtest/run_reserve.py` | **the reserve look. Already spent.** No new test may be added to it |
| `extraction/build_refinements.py` | rebuilds `study/_refinements.md` - the cross-episode index. **Read it before implementing any rule** |
| `extraction/fetch_transcripts.py` | re-fetches caption tracks (free, no key) |
| `extraction/backup.py` | verified zip into `_backups/`. There was no git here until 2026-09-04, so this was the only history |

**Every test script writes its own ledger rows and is idempotent** - re-running
does not inflate `n`.

## The standing risk, kept because it still applies

A result is only as good as its control. Two nulls in this project produced
confident nonsense before being fixed: random-day controls measuring volatility
autocorrelation (z = -18.6), and an inverted control group producing z = 9.5e13.
**Always audit with a negative control** - DECISIONS.md sections 14 and 24.
