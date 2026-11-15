# `smc_v4_multisleeve_package` — Standalone XAUUSD Zero-Lookahead SMC Portfolio (`V5` & `V4`, `2020–2026`)

Self-contained, reproducible package containing **all 82 monthly 1-minute `XAUUSD` archives (`2020-01` .. `2026-10`, `2,360,931` bars)**, the **4-sleeve `V5` causal SMC/ICT engine (`V3_Pro + VisB_Pro + VisA + AMD_Pro`)**, the legacy **3-sleeve `V4_MultiSleeve` baseline**, **`8/8` Zero-Lookahead unit & prefix-invariance tests**, full trade logs for **`-$0.25/oz`**, **`-$0.35/oz`**, and **`-$0.50/oz`** spread/cost regimes, **`$100` live-style compounding simulations**, charts, and a complete Arabic engineering handoff (`HANDOFF_DETAILED_AR.md`).

## Summary Results (`2020-02-01` → `2026-10-16`, `6.8` Years, Zero-Lookahead)

| Variant / Cost Regime | Trades `N` | Win Rate | Net Profit | Profit Factor | Max DD | `t-stat` (`95% CI`) | Positive Years | `H1 (2020–23)` | `H2 (2023–26)` |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| **`V5_1PosLock (-$0.25/oz)`** | `645` | `39.22%` | **`+200.65R`** | `1.496` | `21.20R` | **`+3.76`** (`[+0.151, +0.476]`) | **`7/7`** | `+87.4R` | `+113.3R` |
| **`V5_1PosLock (-$0.35/oz)`** | `645` | `39.22%` | **`+192.15R`** | `1.469` | `22.70R` | **`+3.60`** (`[+0.144, +0.462]`) | **`7/7`** | `+82.5R` | `+109.6R` |
| **`V5_1PosLock (-$0.50/oz)`** | `645` | `39.22%` | **`+179.40R`** | `1.430` | `24.96R` | **`+3.36`** (`[+0.114, +0.440]`) | **`7/7`** | `+75.3R` | `+104.1R` |
| **`V5_MultiSleeve (-$0.25/oz)`** | `883` | `39.07%` | **`+283.34R`** | `1.510` | `29.91R` | **`+4.54`** (`[+0.186, +0.460]`) | **`7/7`** | `+109.7R` | `+173.6R` |
| **`V4_MultiSleeve (-$0.25/oz)`** | `512` | `35.35%` | **`+100.69R`** | `1.294` | `14.68R` | **`+2.66`** (`[+0.052, +0.342]`) | **`7/7`** | `+50.9R` | `+49.8R` |
| **`V4_1PosLock (-$0.25/oz)`** | `455` | `35.82%` | **`+97.11R`** | `1.322` | `13.35R` | **`+2.72`** (`[+0.063, +0.374]`) | **`7/7`** | `+49.1R` | `+48.0R` |

### V5 Individual Sleeves (`-$0.25/oz`)
- **`V3_Pro`** (`N=261`, `36.02%` WR): **`+96.04R`**, `PF=1.560`, `DD=13.73R`, `t=+2.56`, `7/7` +yrs
- **`VisB_Pro`** (`N=121`, `50.41%` WR): **`+65.97R`**, `PF=2.062`, `DD=8.43R`, `t=+2.69`, `7/7` +yrs
- **`VisA`** (`N=117`, `35.04%` WR): **`+18.17R`**, `PF=1.228`, `DD=15.51R`, `t=+1.01`, `5/7` +yrs (stabilizes `2021` & cuts portfolio DD)
- **`AMD_Pro`** (`N=384`, `38.80%` WR): **`+103.16R`**, `PF=1.425`, `DD=31.39R`, `t=+2.61`, `6/7` +yrs

### `$100` Account Compounding (`V5_1PosLock`, `-$0.25/oz`, `2020-02` → `2026-10`)
- **`1.0%` Risk Compounded:** `$100.00` → **`$646.51`** (`+546.5%`, Max DD **`19.83%`**)
- **`2.0%` Risk Compounded:** `$100.00` → **`$3,215.68`** (`+3,115.7%`, Max DD **`36.87%`**)
- **`3.0%` Risk Compounded:** `$100.00` → **`$12,584.98`** (`+12,485.0%`, Max DD **`51.14%`**)

## Directory Structure

```text
smc_v4_multisleeve_package/
├── README.md                              # Overview & quickstart
├── HANDOFF_DETAILED_AR.md                 # Full Arabic technical & trading handoff (V5 + V4)
├── requirements.txt                       # Python dependencies
├── run_v4_multisleeve_backtest.py         # End-to-end reproducibility script (V5 + V4 + $100 sim)
├── data/
│   ├── DATA_MANIFEST.sha256               # SHA-256 checksums for all 82 monthly files
│   └── XAUUSD_1m_histdata/*.csv.gz        # 82 monthly 1m XAUUSD OHLC archives (2020-01 .. 2026-10)
├── engine/
│   ├── __init__.py
│   ├── causal_primitives.py               # Causal resampling, k-pivot swings, Wilder ATR(14), 4H/1H BOS
│   ├── smc_v3_trend_engine.py             # Sleeve 1: V3_NY (2.5R) & V3_Pro (0.75 ATR SL + 1H trail)
│   └── smc_v4_portfolio.py                # VisB / VisB_Pro, VisA, AMD_Pro, V4 & V5 composers, $100 sim
├── tests/
│   └── test_v4_zero_lookahead.py          # 8 strict causal & prefix-invariance pytest checks (V4 + V5)
└── results/
    ├── summary_v4_multisleeve.json        # Complete numerical breakdown (V5 + V4 + $100 sim)
    ├── trades_v5_1pos_cost025.csv         # 645 trades (V5_1PosLock @ -$0.25/oz)
    ├── trades_v5_1pos_cost035.csv         # 645 trades (V5_1PosLock @ -$0.35/oz)
    ├── trades_v5_1pos_cost050.csv         # 645 trades (V5_1PosLock @ -$0.50/oz)
    ├── trades_v5_unlocked_cost025.csv     # 883 trades (V5_MultiSleeve @ -$0.25/oz)
    ├── trades_v4_multisleeve_cost025.csv  # 512 trades (V4 baseline @ -$0.25/oz)
    ├── trades_v4_multisleeve_cost035.csv  # 512 trades (V4 baseline @ -$0.35/oz)
    ├── trades_v4_multisleeve_cost050.csv  # 512 trades (V4 baseline @ -$0.50/oz)
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

# 2. Run Zero-Lookahead & Prefix-Invariance test suite (8/8 checks)
.venv/bin/pytest -v tests/test_v4_zero_lookahead.py

# 3. Reproduce all V5 + V4 backtests, CSVs, JSON, and charts from scratch
.venv/bin/python run_v4_multisleeve_backtest.py
```
