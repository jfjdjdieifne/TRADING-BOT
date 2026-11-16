# `smc_v4_multisleeve_package` — Standalone Zero-Lookahead Multi-Asset SMC Portfolio (`V8`, `V7`, `V6`, `V5`, `V4`, `2020–2026`)

Self-contained, reproducible package containing **ALL tested multi-asset datasets directly inside `data/`**:
- **`XAUUSD_1m_histdata/`**: `82` monthly 1-minute archives (`2020-01` .. `2026-10`, `2,360,931` bars, SHA-256 verified)
- **`NSXUSD_1m_histdata/`**: `82` monthly 1-minute archives (`2020-01` .. `2026-10`, `2,277,180` bars, SHA-256 verified)
- **`BTCUSD_5m/`**: `8` annual 5-minute 24/7 archives (`2019` .. `2026`, `823,154` bars, SHA-256 verified)

Includes the **V8 Microscopy-Upgraded Multi-Asset System (`XAUUSD` + `NSXUSD` + `BTCUSD`)**, **V7 Baseline (`10R–17.4R` HTF Sniper)**, **`V6` (`5`-sleeve XAUUSD)**, **`V5` (`4`-sleeve XAUUSD)**, **`V4` (`3`-sleeve baseline)**, **`10/10` Zero-Lookahead unit & prefix-invariance tests**, `2×` cost-stress verification, 81-month `$100` compounding ledgers, charts, and full Arabic engineering & microscopy handoff (`HANDOFF_DETAILED_AR.md`).

## V8 Microscopy-Upgraded Multi-Asset Portfolio (`2020-02-01` → `2026-10-31`, `81` Months)

### 4 Structural Market Microscopy Upgrades (Derived from `1,603`-Trade Forensic Autopsy)
1. **`V3_Pro_Clean` (XAUUSD):** Drops `13:00–14:59 UTC` NY cash-open chop (`N=124` vs `261`, `+95.2R`, `PF 1.560 -> 2.288`, `DD 13.7R -> 7.4R`, `worst month -6.2R -> -3.1R`).
2. **`NSX_AMD_1D` (NSXUSD):** Enforces causal `1D BOS` alignment (`N=256` vs `504`, `+79.1R` vs `+61.8R`, `PF 1.189 -> 1.506`, `DD 24.8R -> 13.1R`, `t +1.40 -> +2.28`).
3. **`NSX_1H1m_10R >=09h` (NSXUSD):** Removes dead `07:00–08:59 UTC` London hours (`min_hour_utc=9`, `N=203`, `+97.8R` vs `+84.4R`, `PF 1.412 -> 1.540`, `DD 47.1R -> 41.6R`).
4. **`BTC_15R_BE >=09h` (BTCUSD):** Drops Asian `00:00–08:59 UTC` (`min_hour_utc=9`) + activates causal `BE@3.0R(+1.0R)` shield (`N=134`, `WR 10.3% -> 29.9%`, `+90.6R`, `PF 1.596 -> 1.906`, `DD 36.8R -> 21.5R`, `6/7` +yrs vs `4/7`).

### V8 vs V7 Portfolios (`1.0×` Realistic Cost & `2.0×` Double-Cost Stress)
| Portfolio / Mode | `N` | WR% | Net R (`Avg/mo`) | PF | Max DD | `t-stat` | `+Yrs` | `-Mo / 81` | Worst Mo | `$100 @ 1%` | `$100 @ 1.5%` | `$100 @ 2%` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`V7_Global_1Pos` (Baseline)** | `887` | `35.4%` | `+317.3R (+3.92R)` | `1.531` | `20.2R` | `+4.12` | `7/7` | `23` | `-10.1R` | `$1,794` | `$6,235` | `$19,229` |
| **`V8_Global_1Pos` (Upgraded)** | `791` | `38.0%` | **`+325.4R (+4.02R)`** | **`1.637`** | `20.3R` | **`+4.68`** | **`7/7`** | `23` | **`-8.3R`** | **`$2,044`** | **`$7,839`** | **`$27,188`** |
| **`V7_3Asset_1PosEach` (Baseline)** | `1,603` | `31.8%` | `+481.4R (+5.94R)` | `1.422` | `35.8R` | `+4.44` | `7/7` | `25` | `-17.4R` | `$7,026` | `$39,952` | `$179,790` |
| **`V8_3Asset_1PosEach` (Upgraded)** | `1,321` | `34.2%` | **`+515.8R (+6.37R)`** | **`1.570`** | **`26.1R`** | **`+5.22`** | **`7/7`** | `27` | **`-11.3R`** | **`$10,852`** (`DD 23.0%`) | **`$81,566`** (`DD 32.6%`) | **`$503,286`** (`DD 41.3%`) |
| `V8_Global_1Pos (2.0x Cost Stress)` | `791` | `38.0%` | `+291.4R (+3.60R)` | `1.548` | `23.5R` | `+4.19` | `7/7` | `27` | `-8.7R` | `$1,457` | `$4,721` | `$13,831` |
| `V8_3Asset_1PosEach (2.0x Stress)` | `1,321` | `34.2%` | `+459.2R (+5.67R)` | `1.487` | `29.9R` | `+4.65` | `7/7` | `27` | `-12.0R` | `$6,171` | `$35,007` | `$163,034` |

*(Also includes `entry_mode="ob_overlap"` & `require_cisd=True` inside `run_engine_sniper_htf` implementing ICT `OB+/BISI + CISD`; `XAU 15m->1m + CISD + OB/BISI` improves `PF 1.526 -> 1.654` on `240` trades.)*

---

## V7 Multi-Asset Uncorrelated Sniper Results (`2020-02-01` → `2026-10-31`, `81` Months)

### Cross-Asset Monthly Return Correlation (Mathematically Uncorrelated / Inverse)
- `corr(XAUUSD_V7, NSXUSD_V7) = -0.105` (`XAU_V6` vs `NSX_V7`: `-0.160`)
- `corr(NSXUSD_V7, BTCUSD_15R) = -0.241`
- `corr(XAUUSD_V7, BTCUSD_15R) = +0.029`
- **FX Majors Rejected Empirically:** `EURUSD 1H->1m` (`-51.6R` / `-12.3R`), `USDJPY 1H->1m` (`-41.8R` / `-14.7R`) under `1.2 pip` spread; tight `1m` stops on FX majors get wiped out by spread/mean-reversion.

### V7 Multi-Asset Portfolios (`1.0×` Realistic Cost vs `2.0×` Double-Cost Stress)
| Portfolio / Mode | Trades `N` | WR% | Net R (`Avg/mo`) | `p90` / `Best Mo` | Months `>=10R` / `>=20R` | PF | Max DD | `t-stat` | `+Yrs` | `$100 @ 1%` | `$100 @ 1.5%` | `$100 @ 2%` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`V6_XAU_1Pos_Baseline`** | `846` | `36.6%` | `+239.3R (+2.95R)` | `+10.4R / +21.1R` | `10 / 1` | `1.429` | `22.8R` | `+4.00` | `7/7` | `$918` (`DD 20.9%`) | `$2,449` (`DD 29.9%`) | `$6,035` (`DD 38.1%`) |
| **`V7_XAU_Unleashed_1Pos`** | `758` | `28.5%` | `+258.4R (+3.19R)` | `+16.3R / +30.0R` | `19 / 4` | `1.458` | `31.7R` | `+3.03` | `7/7` | `$939` (`DD 27.5%`) | `$2,277` (`DD 38.4%`) | `$4,806` (`DD 47.8%`) |
| **`V7_Global_1Pos` (Strict 1 Pos Total)** | `887` | `35.4%` | **`+317.3R (+3.92R)`** | `+16.9R / +28.1R` | `17 / 5` | **`1.531`** | **`20.2R`** | **`+4.12`** | **`7/7`** | **`$1,794`** (`DD 18.5%`) | **`$6,235`** (`DD 26.6%`) | **`$19,229`** (`DD 33.9%`) |
| **`V7_3Asset_1PosEach` (1/Asset)** | `1,603` | `31.8%` | **`+481.4R (+5.94R)`** | `+18.8R / +32.3R` | **`30 / 8`** | `1.422` | `35.8R` | **`+4.44`** | **`7/7`** | **`$7,026`** (`DD 31.2%`) | **`$39,952`** (`DD 43.7%`) | **`$179,790`** (`DD 54.5%`) |
| **`V7_Unleashed_3Asset_1PosEach`** | `1,515` | `27.5%` | **`+500.4R (+6.18R)`** | **`+22.7R / +39.6R`** | **`30 / 11`** | `1.436` | `38.5R` | **`+4.02`** | **`7/7`** | **`$7,189`** (`DD 33.1%`) | **`$37,133`** (`DD 45.9%`) | **`$143,197`** (`DD 56.5%`) |
| `V7_Global_1Pos (2.0x Cost Stress)` | `887` | `35.4%` | `+279.5R (+3.45R)` | `+16.6R / +27.3R` | — | `1.449` | `21.8R` | `+3.63` | `7/7` | `$1,231` | `$3,544` | `$9,057` |
| `V7_3Asset_1PosEach (2.0x Stress)` | `1,603` | `31.8%` | `+413.9R (+5.11R)` | `+17.4R / +31.3R` | — | `1.349` | `41.5R` | `+3.82` | `7/7` | `$3,583` | `$14,554` | `$46,779` |

### New V7 HTF-Target Sniper Sleeves (`1.0×` Cost)
- **`XAU_15m1m_Tr1H`** (`15m_k2` Sweep -> `1m` Sniper, Delayed `1H@4.0R` Trail `+1.5R` lock): `N=335`, **`+136.2R`**, `PF=1.526`, `DD=20.6R`, max **`17.4R`**
- **`XAU_1H1m_15R`** (`1H_k3` Major Sweep -> `1m` Sniper, Fixed `15.0R` TP): `N=230`, **`+128.6R`**, **`PF=1.597`**, `DD=35.6R`, `23` trades hit `15R`
- **`NSX_AMD_Pro`** (`15m` AMD Manipulation -> `1H` Trail): `N=504`, **`+61.8R`**, `PF=1.189`, `DD=24.8R`
- **`NSX_1H1m_10R`** (`1H_k3` Major Sweep -> `1m` Sniper, Fixed `10.0R` TP): `N=226`, **`+84.4R`**, `PF=1.412`, `DD=47.1R`
- **`BTC_1H5m_Dual15R`** (`4H+1H` BOS -> `1H_k3` Sweep -> `5m` Sniper, `24/7`, Fixed `15.0R` TP, `0.08%` cost): `N=165`, **`+94.7R`**, **`PF=1.596`**, `DD=36.8R`

---

## Legacy V6 / V5 / V4 Summary (`XAUUSD` Only, `2020-02-01` → `2026-10-16`)

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
├── README.md                                  # Overview & quickstart (V7 + V6 + V5 + V4)
├── HANDOFF_DETAILED_AR.md                     # Full Arabic technical & trading handoff
├── requirements.txt                           # Python dependencies
├── run_v4_multisleeve_backtest.py             # Reproduces XAUUSD V6 + V5 + V4 backtests
├── run_v7_multiasset_backtest.py              # Reproduces Multi-Asset V7 (XAU + NSX + BTC) + 2x stress + charts
├── run_v8_multiasset_backtest.py              # Reproduces Multi-Asset V8 Microscopy + monthly $100 ledger + 2x stress
├── data/
│   ├── DATA_MANIFEST.sha256                   # SHA-256 checksums for 82 XAUUSD 1m files
│   ├── NSXUSD_MANIFEST.sha256                 # SHA-256 checksums for 82 NSXUSD 1m files
│   ├── BTCUSD_MANIFEST.sha256                 # SHA-256 checksums for 8 BTCUSD 5m files
│   ├── XAUUSD_1m_histdata/*.csv.gz            # 82 monthly 1m XAUUSD archives (2020-01..2026-10)
│   ├── NSXUSD_1m_histdata/*.csv.gz            # 82 monthly 1m NSXUSD archives (2020-01..2026-10)
│   └── BTCUSD_5m/*.csv.gz                     # 8 annual 5m BTCUSD archives (2019..2026)
├── engine/
│   ├── __init__.py
│   ├── causal_primitives.py                   # Multi-asset loader, causal resampling, k-swings, ATR, HTF BOS
│   ├── smc_v3_trend_engine.py                 # Sleeve 1: V3_NY & V3_Pro (0.75 ATR SL + 1H trail)
│   └── smc_v4_portfolio.py                    # VisB_Pro, VisA, AMD_Pro, XAU_LTF1M, Sniper_HTF (OB/CISD+BE), V4..V8
├── tests/
│   └── test_v4_zero_lookahead.py              # 10 strict causal & prefix-invariance pytest checks (V4..V8 + ICT OB)
└── results/
    ├── summary_v8_multiasset.json             # Complete V8 microscopy summary (1x & 2x stress)
    ├── trades_v8_global_1pos.csv              # 791 trades (V8_Global_1Pos)
    ├── trades_v8_3asset_1pos_each.csv         # 1,321 trades (V8_3Asset_1PosEach)
    ├── monthly_breakdown_v8_from_100usd.csv   # Full 81-month $100 compounding ledger (1%, 1.5%, 2%)
    ├── v8_vs_v7_equity_and_dd.png
    ├── v8_monthly_r_and_yearly.png
    ├── summary_v7_multiasset.json             # Complete V7 multi-asset numerical summary (1x & 2x stress)
    ├── trades_v7_global_1pos.csv              # 887 trades (V7_Global_1Pos)
    ├── trades_v7_3asset_1pos_each.csv         # 1,603 trades (V7_3Asset_1PosEach)
    ├── trades_v7_unleashed_3asset.csv         # 1,515 trades (V7_Unleashed_3Asset_1PosEach)
    ├── v7_multiasset_equity_and_correlation.png
    ├── v7_multiasset_yearly_and_monthly_r.png
    ├── summary_v4_multisleeve.json            # XAUUSD V6 + V5 + V4 summary
    ├── trades_v6_*.csv / trades_v5_*.csv / trades_v4_*.csv
    └── charts/
        ├── v4_multisleeve_costs_comparison.png
        └── v4_multisleeve_yearly_bars.png
```

## Quickstart (Verify All 3 Datasets + Zero-Lookahead Tests + Reproduce V8 & V7)

```bash
cd smc_v4_multisleeve_package
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1. Verify data integrity across all 3 instruments
(cd data/XAUUSD_1m_histdata && sha256sum -c ../DATA_MANIFEST.sha256)
(cd data/NSXUSD_1m_histdata && sha256sum -c ../NSXUSD_MANIFEST.sha256)
(cd data/BTCUSD_5m && sha256sum -c ../BTCUSD_MANIFEST.sha256)

# 2. Run Zero-Lookahead & Prefix-Invariance test suite (10/10 checks)
.venv/bin/pytest -v tests/test_v4_zero_lookahead.py

# 3. Reproduce V8 Microscopy-Upgraded Multi-Asset (XAU + NSX + BTC), 2x stress, $100 ledger & charts
.venv/bin/python run_v8_multiasset_backtest.py

# 4. Reproduce V7 Multi-Asset & XAUUSD V6 + V5 + V4 backtests
.venv/bin/python run_v7_multiasset_backtest.py
.venv/bin/python run_v4_multisleeve_backtest.py
```

## V9 Dynamic Profile Research Layer (kept separate from the V8 reference)

`engine/dynamic_profile.py` is the first implementation of the requested
contextual profile switcher. It is a sequential, zero-lookahead planner, not a
replacement for the frozen `exports/quantconnect/V8_3Asset_1PosEach_QC.py`.

It includes:

- prior-100-bar volume z-score and prior-ATR(14) ADI;
- hard `AGGRESSIVE` gate requiring volume, velocity, and declared Spot
  executed-flow/CVD convergence;
- causal three-candle FVGs, body-confirmed BOS/CHoCH, explicit HTF sweep input;
- shallow-FVG entry, protected impulse stop, deep-OB fallback, target/R:R gate,
  and monotonic trailing-stop primitive;
- no broker submission and no implicit OHLCV-as-CVD fallback.

Run its focused tests from the package root:

```bash
.venv/bin/pytest -q tests/test_dynamic_profile.py
```

The Arabic design, source limits, and live-readiness checklist are in
`V9_DYNAMIC_PROFILE_DESIGN_AR.md`. `V9_DYNAMIC_PROFILE_EXAMPLE.py` is a
synthetic offline example only.
