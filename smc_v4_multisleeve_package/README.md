# `smc_v4_multisleeve_package` — Standalone XAUUSD Zero-Lookahead SMC Portfolio (`2020–2026`)

Self-contained, reproducible package containing **all 82 monthly 1-minute `XAUUSD` archives (`2020-01` .. `2026-10`, `2,360,931` bars)**, the **3-sleeve causal SMC/ICT engine (`V4_MultiSleeve`)**, **Zero-Lookahead unit & prefix-invariance tests**, full trade logs for **`-$0.25/oz`**, **`-$0.35/oz`**, and **`-$0.50/oz`** spread/cost regimes, charts, and a complete Arabic engineering handoff (`HANDOFF_DETAILED_AR.md`).

## Summary Results (`2020-02-01` → `2026-10-16`, `6.8` Years, Zero-Lookahead)

| Variant / Cost Regime | Trades `N` | Win Rate | Net Profit | Profit Factor | Max DD | `t-stat` (`95% CI`) | Positive Years | `H1 (2020–23)` | `H2 (2023–26)` |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| **`V4_MultiSleeve (-$0.25/oz)`** | `512` | `35.35%` | **`+100.69R`** | `1.294` | `14.68R` | **`+2.66`** (`[+0.052, +0.339]`) | **`7/7`** | `+50.9R` | `+49.8R` |
| **`V4_MultiSleeve (-$0.35/oz)`** | `512` | `35.35%` | **`+93.31R`** | `1.269` | `14.95R` | **`+2.47`** (`[+0.036, +0.324]`) | **`7/7`** | `+46.6R` | `+46.7R` |
| **`V4_MultiSleeve (-$0.50/oz)`** | `512` | `35.35%` | **`+82.22R`** | `1.232` | `16.35R` | **`+2.17`** (`[+0.017, +0.311]`) | **`7/7`** | `+40.2R` | `+42.1R` |

## Directory Structure

```text
smc_v4_multisleeve_package/
├── README.md                              # Overview & quickstart
├── HANDOFF_DETAILED_AR.md                 # Full Arabic technical & trading handoff
├── requirements.txt                       # Python dependencies
├── run_v4_multisleeve_backtest.py         # End-to-end reproducibility script
├── data/
│   ├── DATA_MANIFEST.sha256               # SHA-256 checksums for all 82 monthly files
│   └── XAUUSD_1m_histdata/*.csv.gz        # 82 monthly 1m XAUUSD OHLC archives (2020-01 .. 2026-10)
├── engine/
│   ├── __init__.py
│   ├── causal_primitives.py               # Causal resampling, k-pivot swings, Wilder ATR(14), 4H/1H BOS
│   ├── smc_v3_trend_engine.py             # Sleeve 1: V3_NY (4H+1H BOS -> 15m BOS Displacement FVG)
│   └── smc_v4_portfolio.py                # Sleeve 2 (VisB) + Sleeve 3 (VisA) + V4_MultiSleeve composer
├── tests/
│   └── test_v4_zero_lookahead.py          # 7 strict causal & prefix-invariance pytest checks
└── results/
    ├── summary_v4_multisleeve.json        # Complete numerical breakdown
    ├── trades_v4_multisleeve_cost025.csv  # 512 trades @ -$0.25/oz
    ├── trades_v4_multisleeve_cost035.csv  # 512 trades @ -$0.35/oz
    ├── trades_v4_multisleeve_cost050.csv  # 512 trades @ -$0.50/oz
    └── charts/
        ├── v4_multisleeve_costs_comparison.png
        └── v4_multisleeve_yearly_bars.png
```

## Quickstart (Verify Data + Zero-Lookahead Tests + Reproduce All Results)

```bash
cd smc_v4_multisleeve_package
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1. Verify data integrity (82 files)
(cd data/XAUUSD_1m_histdata && sha256sum -c ../DATA_MANIFEST.sha256)

# 2. Run Zero-Lookahead & Prefix-Invariance test suite
.venv/bin/pytest -v tests/test_v4_zero_lookahead.py

# 3. Reproduce all backtests, CSVs, JSON, and charts from scratch
.venv/bin/python run_v4_multisleeve_backtest.py
```
