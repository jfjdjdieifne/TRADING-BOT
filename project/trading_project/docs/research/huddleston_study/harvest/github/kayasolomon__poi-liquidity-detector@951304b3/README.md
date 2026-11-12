# poi-liquidity-detector

Non-repainting detection of points of interest and liquidity features on OHLCV
candles: **order blocks** validated by structure breaks and an ATR impulse filter,
**fair value gaps** with fill tracking, **equal highs/lows** (resting liquidity),
**liquidity sweeps**, and the classic **sweep → CHoCH reversal** confluence.
Built on [`market-structure-engine`](../market-structure-engine) for swing and
BOS/CHoCH detection. Part of the **Visor** chart intelligence stack — the overlay
adapter emits plain, typed data shapes (boxes, price lines, markers) ready for
lightweight-charts-style rendering, with no charting dependency.

## Method

Every detector below emits and transitions **only on confirmed closes**, and every
emission records the bar at which it became known (`createdAtIndex`, `atIndex`,
`mitigatedAtIndex`, …). The test suite proves the prefix property: re-running on
the first *n* candles reproduces exactly the full run's outputs known by bar *n*.

### Order blocks

The last opposite-direction candle before an impulsive move that breaks structure:

1. The internal `StructureEngine` (confirmed-close mode) reports a BOS or CHoCH at
   bar *b*.
2. Scan back from *b* (up to `obLookback` bars, default 20) for the most recent
   candle whose body opposes the break — bearish candle for a bullish break, and
   vice versa.
3. Impulse filter: with break price *p* and the OB candle's body edge *e*
   (its close — the far end of the body in break direction),
   `impulse = |p − e|` must satisfy `impulse ≥ minImpulseATR × ATR(atrPeriod)`
   (defaults 1.5 × ATR(14), Wilder smoothing) measured at bar *b*.

Zone bounds are the candle **body** by default (`zoneMode: 'body'`, i.e.
`[min(open,close), max(open,close)]`) or the full wick range (`'full'`). The zone
becomes known at the break bar (`createdAtIndex = b`) — never earlier.

### Fair value gaps

Three-candle displacement gap, knowable at candle 3's close:

- bullish: `candle1.high < candle3.low` → gap `[candle1.high, candle3.low]`
- bearish: `candle1.low > candle3.high` → gap `[candle3.high, candle1.low]`

Fill tracking (`fillState`): fresh → **partial** at first penetration → **filled**
at full traversal. Penetration is measured by wick extremes by default
(`fvgFillMode: 'wick'`) or by closes (`'close'`); `filledFraction` records the
deepest penetration (0–1, monotonic).

### Equal highs / equal lows

Confirmed swing points (from `market-structure-engine`) of the same kind cluster
when a new swing lands within `tolerance = equalTolATR × ATR` (default 0.25 × ATR(14))
of a cluster's mean. Two members make the cluster a reported **EqualLevel** —
created at the second member's confirmation bar. The level's `extreme` (outermost
member price) is where the resting liquidity actually sits: a close through it
marks the level **broken**; a wick through it that closes back inside marks it
**swept** and emits a `Sweep`. A lone first swing (1-member candidate) is only
consumed when price runs more than `tolerance` beyond it — a second high a hair
above the first can still cluster, which is how equal highs form in practice.

### Liquidity sweeps and SweepReversal

A **sweep** is a wick through a liquidity level with the close back inside:
equal-level extremes (source `eqh`/`eql`) and the most recent confirmed lone swing
extreme (source `swing`; skipped when that swing is already broken, already swept,
or accounted for inside a reported equal level). A close *through* the level is a
structure break instead — never both.

**SweepReversal**: when a CHoCH confirms within `sweepReversalMaxBars` (default 20)
of a sweep on the matching side (high sweep → bearish CHoCH, low sweep → bullish
CHoCH), the sweep and CHoCH are paired into a composite marker — the classic
liquidity-grab reversal confluence. Each sweep pairs at most once.

### Zone lifecycle

Every zone (order block, FVG) tracks
`fresh → mitigated (first touch) → invalidated (close through the far edge)`,
with the transition bars recorded. Transitions are decided on closed bars only and
are never revised.

### Confirmation lags (honesty table)

| detection | knowable at |
|---|---|
| order block | the structure-break bar (swing behind it confirms `fractalK` bars after its pivot) |
| fair value gap | close of candle 3 |
| equal level | confirmation bar of its 2nd member (pivot + `fractalK`) |
| sweep | close of the sweeping bar |
| SweepReversal | close of the CHoCH bar |
| zone/level state change | the closing bar that caused it |

## Install

```bash
npm install poi-liquidity-detector
```

Node 20+. Runtime dependency: `market-structure-engine` only.

## Quickstart

```ts
import { PoiDetector } from 'poi-liquidity-detector';

const detector = new PoiDetector({ zoneMode: 'body', minImpulseATR: 1.5 });

// batch over history…
const { orderBlocks, fvgs, equalLevels, sweeps, sweepReversals } =
  detector.process(candles);

// …then stream live closed bars
const step = detector.update(nextClosedCandle);
for (const reversal of step.newSweepReversals) {
  console.log('sweep→CHoCH', reversal.direction, 'at', reversal.atTime);
}
```

Batch and incremental modes produce identical output for the same candles (tested).

## API

### `new PoiDetector(options?)`

| option | default | meaning |
|---|---|---|
| `fractalK` | `2` | swing confirmation half-width (structure engine) |
| `zoneMode` | `'body'` | order-block zone bounds: body or full wick range |
| `minImpulseATR` | `1.5` | minimum break impulse in ATR multiples |
| `obLookback` | `20` | max bars to scan back for the OB candle |
| `atrPeriod` | `14` | Wilder ATR period (impulse filter + equal tolerance) |
| `fvgFillMode` | `'wick'` | FVG fill measured by wicks or closes |
| `equalTolATR` | `0.25` | equal-level tolerance as a fraction of ATR |
| `sweepReversalMaxBars` | `20` | max sweep→CHoCH distance for the composite |

- `process(candles): PoiResult` — reset + run over the whole array.
- `update(candle): PoiUpdate` — feed one closed candle; returns only what it added
  (`newOrderBlocks`, `newFvgs`, `newEqualLevels`, `newSweeps`, `newSweepReversals`,
  plus the structure engine's own increment). Previously returned zones/levels
  mutate in place as their lifecycle advances.
- getters: `orderBlocks`, `fvgs`, `equalLevels`, `sweeps`, `sweepReversals`,
  `state`; `reset()`.

Lower-level pieces are exported too: `Atr`, `detectFvg` / `advanceFvgFill`,
`advanceZone`, `EqualLevelTracker`.

### Overlay adapter

Typed data shapes only — render however you like:

- `toOrderBlockBoxes(obs, timeAt?)` / `toFvgBoxes(fvgs, timeAt?)` — boxes with
  state-dependent `styleKey`s (`ob-bullish-fresh`, `fvg-bearish-filled`, …).
- `toEqualLevelLines(levels, timeAt?)` — extreme + mean price-line pairs
  (`eqh-active`, `eql-swept`, …).
- `toSweepMarkers(sweeps)` / `toSweepReversalMarkers(reversals)` — markers at the
  sweeping / CHoCH bar.

## Demo

```bash
npm install && npm --prefix ../market-structure-engine run build
npm run demo   # detections on 1000 real BTCUSDT 1h candles, as tables
```

## Tests

```bash
npm test
```

Hand-built synthetic candles asserting exact zones for each detector, lifecycle
transitions, wick-vs-close rules, ATR reference values, the non-repaint prefix
property on real + synthetic data (with lifecycle-aware normalisation), batch ≡
incremental equivalence, and a real-fixture snapshot.

## Screenshots

_Chart overlays coming soon._

---

Educational and analytical tooling. Not investment advice, not a trading signal
service, and not a financial promotion.
