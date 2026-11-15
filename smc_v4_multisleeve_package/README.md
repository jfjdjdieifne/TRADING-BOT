# `smc_v4_multisleeve_package` — Standalone Zero-Lookahead SMC Portfolio (`V6`, `V5`, `V4`, `2020–2026`)

Self-contained, reproducible package containing **all 82 monthly 1-minute `XAUUSD` archives (`2020-01` .. `2026-10`, `2,360,931` bars)**, the **5-sleeve `V6` causal SMC/ICT engine (`V3_Pro + VisB_Pro + VisA + AMD_Pro + XAU_LTF1M`)**, the **4-sleeve `V5` engine**, the legacy **3-sleeve `V4_MultiSleeve` baseline**, **`8/8` Zero-Lookahead unit & prefix-invariance tests**, full trade logs for **`-$0.25/oz`**, **`-$0.35/oz`**, and **`-$0.50/oz`** spread/cost regimes, **`$100` live-style compounding simulations**, charts, and a complete Arabic engineering handoff (`HANDOFF_DETAILED_AR.md`).

## Summary Results (`2020-02-01` → `2026-10-16`, `6.8` Years, Zero-Lookahead)

| Variant / Cost Regime | Trades `N` | Win Rate | Net Profit | Profit Factor | Max DD | `t-stat` (`95% CI`) | Positive Years | `H1 (2020–23)` | `H2 (2023–26)` |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| **`V6_XAU_1PosLock (-$0.25/oz)`** | `846` | `36.64%` | **`+239.34R`** | `1.429` | `22.75R` | **`+4.00`** (`[+0.147, +0.426]`) | **`7/7`** | `+112.8R` | `+126.5R` |
| **`V6_XAU_1PosLock (-$0.35/oz)`** | `846` | `36.64%` | **`+226.05R`** | `1.399` | `24.09R` | **`+3.78`** (`[+0.137, +0.406]`) | **`7/7`** | `+105.4R` | `+120.6R` |
| **`V6_XAU_1PosLock (-$0.50/oz)`** | `846` | `36.64%` | **`+206.12R`** | `1.356` | `26.10R` | **`+3.44`** (`[+0.107, +0.384]`) | **`7/7`** | `+94.3R` | `+111.8R` |
| **`V6_XAU_Unlocked (-$0.25/oz)`** | `1,238` | `37.56%` | **`+387.90R`** | `1.482` | `33.51R` | **`+5.40`** (`[+0.201, +0.429]`) | **`7/7`** | `+164.1R` | `+223.8R` |
| **`V5_1PosLock (-$0.25/oz)`** | `645` | `39.22%` | **`+200.65R`** | `1.496` | `21.20R` | **`+3.76`** (`[+0.150, +0.482]`) | **`7/7`** | `+87.4R` | `+113.3R` |
| **`V5_MultiSleeve (-$0.25/oz)`** | `883` | `39.07%` | **`+283.34R`** | `1.510` | `29.91R` | **`+4.54`** (`[+0.186, +0.465]`) | **`7/7`** | `+109.7R` | `+173.6R` |
| **`V4_MultiSleeve (-$0.25/oz)`** | `512` | `35.35%` | `+100.69R` | `1.294` | `14.68R` | `+2.66` (`[+0.054, +0.346]`) | `7/7` | `+50.9R` | `+49.8R` |
| **`V4_1PosLock (-$0.25/oz)`** | `455` | `35.82%` | `+97.11R` | `1.322` | `13.35R` | `+2.72` (`[+0.056, +0.367]`) | `7/7` | `+49.1R` | `+48.0R` |

### Individual Sleeves (`-$0.25/oz`)
- **`V3_Pro`** (`N=261`, `36.02%` WR): **`+96.04R`**, `PF=1.560`, `DD=13.73R`, `t=+2.56`, `7/7` +yrs
- **`VisB_Pro`** (`N=121`, `50.41%` WR): **`+65.97R`**, `PF=2.062`, `DD=8.43R`, `t=+2.69`, `7/7` +yrs
- **`VisA`** (`N=117`, `35.04%` WR): **`+18.17R`**, `PF=1.228`, `DD=15.51R`, `t=+1.01`, `5/7` +yrs
- **`AMD_Pro`** (`N=384`, `38.80%` WR): **`+103.16R`**, `PF=1.425`, `DD=31.39R`, `t=+2.61`, `6/7` +yrs
- **`XAU_LTF1M`** (`N=355`, `33.80%` WR, `3.0R` TP): **`+104.56R`**, `PF=1.421`, `DD=12.31R`, `t=+2.93`, `6/7` +yrs (still `+84.1R`, `PF=1.321` @ `-$0.50/oz`)

### Multi-Asset Addition (`XAU_V6 + NSX_AMD_Pro` Global `1-Pos Lock`, `1.0×` → `2.0×` Cost)
- **`V6_XAU + NSX_AMD (1.0× cost)`**: `N=1,060`, `37.64%` WR, **`+291.48R`** (`+3.60R/mo`), `PF=1.425`, `DD=26.38R`, **`t=+4.30`**, **`7/7`** +yrs (`$100 @ 2%` → **`$14,209.48`**, `DD 42.3%`)
- **`V6_XAU + NSX_AMD (2.0× cost)`**: **`+251.42R`**, `PF=1.354`, `DD=28.45R`, **`t=+3.71`**, **`7/7`** +yrs

### `$100` Account Compounding (`V6_XAU_1PosLock`, `-$0.25/oz`, `2020-02` → `2026-10`)
- **`1.0%` Risk Compounded:** `$100.00` → **`$917.75`** (`+817.8%`, Max DD **`20.85%`**)
- **`2.0%` Risk Compounded:** `$100.00` → **`$6,034.73`** (`+5,934.7%`, Max DD **`38.12%`**)
- **`3.0%` Risk Compounded:** `$100.00` → **`$29,152.98`** (`+29,053.0%`, Max DD **`52.20%`**)

## Directory Structure

```text
smc_v4_multisleeve_package/
├── README.md                              # Overview & quickstart
├── HANDOFF_DETAILED_AR.md                 # Full Arabic technical & trading handoff (V6 + V5 + V4 + Multi-Asset)
├── requirements.txt                       # Python dependencies
├── run_v4_multisleeve_backtest.py         # End-to-end reproducibility script (V6 + V5 + V4 + $100 sim)
├── data/
│   ├── DATA_MANIFEST.sha256               # SHA-256 checksums for all 82 monthly files
│   └── XAUUSD_1m_histdata/*.csv.gz        # 82 monthly 1m XAUUSD OHLC archives (2020-01 .. 2026-10)
├── engine/
│   ├── __init__.py
│   ├── causal_primitives.py               # Causal resampling, k-pivot swings, Wilder ATR(14), 4H/1H BOS
│   ├── smc_v3_trend_engine.py             # Sleeve 1: V3_NY (2.5R) & V3_Pro (0.75 ATR SL + 1H trail)
│   └── smc_v4_portfolio.py                # VisB / VisB_Pro, VisA, AMD_Pro, XAU_LTF1M, V4/V5/V6, $100 sim
├── tests/
│   └── test_v4_zero_lookahead.py          # 8 strict causal & prefix-invariance pytest checks (V4 + V5 + V6)
└── results/
    ├── summary_v4_multisleeve.json        # Complete numerical breakdown (V6 + V5 + V4 + $100 sim)
    ├── trades_v6_1pos_cost025.csv         # 846 trades (V6_XAU_1PosLock @ -$0.25/oz)
    ├── trades_v6_1pos_cost035.csv         # 846 trades (V6_XAU_1PosLock @ -$0.35/oz)
    ├── trades_v6_1pos_cost050.csv         # 846 trades (V6_XAU_1PosLock @ -$0.50/oz)
    ├── trades_v6_unlocked_cost025.csv     # 1,238 trades (V6_XAU_Unlocked @ -$0.25/oz)
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

# 3. Reproduce all V6 + V5 + V4 backtests, CSVs, JSON, and charts from scratch
.venv/bin/python run_v4_multisleeve_backtest.py
```
