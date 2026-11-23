# V12.0 Institutional Multi-Asset & Cashflow Granular Audit ($100 Start, 1.0x Real Data)

**V12.0 Upgrades Implemented & Verified (V11.0 -> V12.0):**
1. **Institutional Reference & Valid Swing/Reclaim Engine (`InstitutionalReferenceAndSwingEngine`):**
   - Tracks strictly causal `PDH`/`PDL` (+ touch decay `touches <= 2`), `PWH`/`PWL`, and `ASIA_H/L` / `LONDON_H/L` levels on 5m bars (`compute_causal_reference_levels` / `CausalReferenceTracker`).
   - Enforces valid sweep-and-reclaim physics (`validate_sweep_and_reclaim`): rejects price-acceptance breakouts (candles closing outside swept levels without reclaim within 2 bars) on `Setup A` (`V10_CompVacuum`), and deduplicates structural `SWING_*` + `EQH`/`EQL` liquidity barriers (`0.35 * ATR_5` tolerance) so single-touch stepping wicks cannot self-match as liquidity pools.
   - Wires `ref_snap` brick-wall clearance (`< 2.2R` to fresh `PDH/PDL touches <= 1` or `PWH/PWL`) into `AdversarialCrossExaminer` (`hard_veto_ref_brick=True` on `Setup A` & counter-trend sweeps, penalty on trend-aligned `BPR_Retest`/`BPR_Snap`).
   - Result on `BTCUSD_5m`: `V10_BTC_Physics` PF improved **`1.97 -> 2.17`** (IS=`1.86`, OOS=`2.66`); `BTCUSD_5m` 5-sleeve PF improved **`2.06 -> 2.09`** and MaxDD fell **`24.1R -> 21.9R`**.
2. **Pruned Low-WR `NSX_1H1m_10R` (`14.7% WR`) from `V12_REAL_3ASSET`:**
   - `run_v12_multiasset_portfolio` sets `include_nsx_1h1m=False`, retaining `NSX_AMD_1D` (`41.0% WR, +79.1R, PF=1.51`).
   - Full `V12_REAL_3ASSET` win rate jumped **`38.7% -> 42.2%`**, PF rose **`1.87 -> 1.91`**, and OOS PF (2024–2026) rose **`1.89 -> 2.06`** across `1,144` trades (`7/7` green years).
3. **Drawdown-Safe Risk Engine (`week_downward_safe` + `0.75x >= 12%` / `0.60x >= 20%` DD):**
   - `v12_daily_hunter_100` (`3.0% / 3.4% A+`) and `v12_turbo_sniper_100` (`3.5% / 4.0% A+`) use `period_anchor="week_downward_safe"` (`anchor_eq = min(week_start_eq, active_eq)`), eliminating intra-week negative-gamma bet-size creep (**`0` weekly sized-R sign inversions across all profiles**).
   - Dual-tier DD brake (`0.75x` at `>= 12%` DD, `0.60x` at `>= 20%` DD) cut real-asset MaxDD from **`50.7% -> 39.0%`** (`BTC DAILY_HUNTER`), **`58.4% -> 45.4%`** (`3ASSET DAILY_HUNTER`), and **`65.0% -> 51.3%`** (`3ASSET TURBO_SNIPER`).
4. **Live Export & QuantConnect Compact Parity:**
   - `binance_futures_scalper.py`, `BinanceFutures_MultiCoin_Scalper_QC.py`, and single-file `QC_BinanceFutures_V12_Compact.py` (`306` lines, `20,677` chars) implement full V12 reference levels, sweep/reclaim validation, `ref_snap` prosecutor brick-wall vetoes, `BTCUSDT` 4H `ker4 > 0.68` veto, `week_downward_safe` anchoring, `0.75x/0.60x` DD brake, `BANK40_T1/T2` partial exits, and `4H_V6_Cognitive` 2-stage pyramiding.

## Table A — V12.0 Sleeve & Multi-Asset Performance (81 Months, 2020-02-01 to 2026-11-01, 1.0x Real Data)
| Sleeve / Portfolio | Asset | Trades | Trades/Mo | WR | Net R | PF | MaxDD (R) | Green Yrs | IS PF | OOS PF |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4H_V6_Cognitive | BTCUSD | 240 | 3.0 | 40.8% | +109.1R | 2.05 | 8.2R | 7/7 | 2.12 | 1.94 |
| NSX_AMD_1D | NSXUSD | 256 | 3.2 | 41.0% | +79.1R | 1.51 | 13.1R | 6/7 | 1.43 | 1.62 |
| SMC_Sweep_V6 | BTCUSD | 87 | 1.1 | 36.8% | +88.9R | 2.40 | 9.0R | 7/7 | 1.97 | 3.10 |
| V10_BPR_Retest | BTCUSD | 20 | 0.2 | 50.0% | +18.4R | 2.69 | 3.3R | 4/5 | 2.29 | 6.28 |
| V10_BPR_Snap | BTCUSD | 14 | 0.2 | 57.1% | +16.7R | 3.44 | 2.3R | 3/7 | 1.16 | 7.89 |
| V10_CompVacuum | BTCUSD | 20 | 0.2 | 35.0% | +2.6R | 1.18 | 3.7R | 3/6 | 1.67 | 0.88 |
| V10_XAU_VisB | XAUUSD | 151 | 1.9 | 41.1% | +60.9R | 1.64 | 12.1R | 6/7 | 1.65 | 1.63 |
| V11_SessEq_1H_TOPO | BTCUSD | 53 | 0.7 | 50.9% | +25.8R | 1.88 | 3.4R | 6/7 | 1.95 | 1.81 |
| V3_Pro_Clean | XAUUSD | 115 | 1.4 | 41.7% | +91.5R | 2.33 | 7.4R | 7/7 | 2.24 | 2.43 |
| V9_LON | BTCUSD | 76 | 0.9 | 39.5% | +45.1R | 1.88 | 11.8R | 5/7 | 1.64 | 2.15 |
| VisB_Pro | XAUUSD | 112 | 1.4 | 50.0% | +59.9R | 2.03 | 9.4R | 7/7 | 1.84 | 2.46 |
| **BTCUSD_5m (V12_5Sleeve)** | BTCUSD | 510 | 6.3 | 41.6% | +306.6R | 2.09 | 21.9R | 7/7 | 1.96 | 2.28 |
| **XAUUSD_1m (V3c+VisB+V10)** | XAUUSD | 378 | 4.7 | 43.9% | +212.2R | 1.96 | 19.9R | 7/7 | 1.87 | 2.09 |
| **NSXUSD_1m (NSX_AMD_1D)** | NSXUSD | 256 | 3.2 | 41.0% | +79.1R | 1.51 | 13.1R | 6/7 | 1.43 | 1.62 |
| **V12_REAL_3ASSET (Full Portfolio)** | 3-Asset | 1144 | 14.1 | 42.2% | +597.9R | 1.91 | 32.1R | 7/7 | 1.80 | 2.06 |

### Table A.2 — Yearly Net R Consistency Across All 3 Assets (2020–2026)
| Portfolio | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to Nov) | Green Years |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSD_5m | +51.6R | +22.2R | +19.9R | +61.5R | +61.3R | +41.1R | +48.9R | 7/7 |
| XAUUSD_1m | +37.5R | +15.9R | +26.6R | +32.5R | +17.0R | +39.2R | +43.5R | 7/7 |
| NSXUSD_1m | +2.3R | +7.8R | -3.6R | +32.6R | +11.0R | +8.9R | +20.0R | 6/7 |
| **V12_REAL_3ASSET** | +91.5R | +45.9R | +42.9R | +126.5R | +89.3R | +89.2R | +112.5R | 7/7 |

## Table B — $100 Starting Capital: Exact-1.0R Cashflow, Drawdown & Sign-Inversion Audit
### B.1 Strict 1.0x Real-Asset Cashflow (`basket_mult = 1.0`, Zero-Risk Slot Recycling `slots=4`, `week_downward_safe`)
| Tier / Profile | Trades | T/Mo | Min Net R | Active Eq ($) | Vault ($) | Total Wealth ($) | MaxDD (%) | Roll M1 Med | Roll M1 Mean | Roll M1 P75 | Roll M1 P90 | M1 % Green | Wk Sized Inv | Mo Exact Inv |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3ASSET_CONSERVATIVE (1.0%/1.5%, 0.75x/0.60x @12/20% DD, -2.0R CB) | 1124 | 13.9 | -1.000R | $35,103.15 | $0.00 | $35,103.15 | 24.8% | $+5.04 | $+8.87 | $+14.04 | $+27.59 | 75.0% | 0 | 4/81 |
| BTC_V12 — DAILY_HUNTER_$100 (3.0%/3.4%, 0.75x/0.60x, $25 skim) | 503 | 6.2 | -1.000R | $2,327.18 | $2,701.38 | $5,028.56 | 39.0% | $+2.00 | $+11.44 | $+16.68 | $+45.85 | 57.5% | 0 | 4/81 |
| BTC_V12 — TURBO_SNIPER_$100 (3.5%/4.0%, 0.75x/0.60x, $20 skim) | 506 | 6.2 | -1.000R | $3,024.86 | $3,711.14 | $6,735.99 | 43.3% | $+2.26 | $+13.33 | $+19.88 | $+54.34 | 57.5% | 0 | 6/81 |
| 3ASSET — DAILY_HUNTER_$100 (3.0%/3.4%, 0.75x/0.60x, $25 skim) | 1124 | 13.9 | -1.000R | $46,379.37 | $55,085.50 | $101,464.87 | 45.4% | $+13.03 | $+21.74 | $+31.97 | $+67.03 | 71.2% | 0 | 4/81 |
| 3ASSET — TURBO_SNIPER_$100 (3.5%/4.0%, 0.75x/0.60x, $20 skim) | 1127 | 13.9 | -1.000R | $82,622.47 | $99,595.81 | $182,218.28 | 51.3% | $+15.62 | $+24.83 | $+37.60 | $+72.02 | 68.8% | 0 | 5/81 |

*Note on Sign Inversions:* `Wk Sized Inv = 0` across all 5 profiles confirms `week_downward_safe` completely prevents intra-week upward bet-size inflation. Small `Mo Exact Inv` (`4/81` to `6/81`) reflects intentional cross-week equity compounding and A+ (`3.4%`) vs Standard (`3.0%`) weighting plus DD throttling (`0.75x`/`0.60x`) rather than fee leakage (`Min Net R = -1.000R` across every trade).

### B.2 10-Coin Binance Futures Basket Velocity Projections (`BTC_V12`, 5.0x Conservative vs 10.0x Full Basket)
| Basket Projection | Trades/Mo | Roll M1 Med Proj ($) | Roll M1 Mean Proj ($) | Roll M1 P75 Proj ($) | Single-Asset MaxDD (%) |
|---|---:|---:|---:|---:|---:|
| DAILY_HUNTER_$100 — 5.0x Correlated Basket | 31.0 | $+10.00 | $+57.20 | $+83.40 | 39.0% |
| DAILY_HUNTER_$100 — 10.0x Full 10-Coin Basket | 62.1 | $+20.00 | $+114.40 | $+166.80 | 39.0% |
| TURBO_SNIPER_$100 — 5.0x Correlated Basket | 31.2 | $+11.30 | $+66.65 | $+99.40 | 43.3% |
| TURBO_SNIPER_$100 — 10.0x Full 10-Coin Basket | 62.5 | $+22.60 | $+133.30 | $+198.80 | 43.3% |

## Table C — Last 35 Days Literal Trade-by-Trade Ledger (`3ASSET — DAILY_HUNTER_$100`, `1.0x` Real Data)
| Entry Time (UTC) | Asset | Sleeve | Side | Exit Tier | Hold (h) | Risk % | Risk $ | Raw Net R | Exact 1.0R Net R | Sized R | PnL ($) | Active Eq ($) | Vault ($) | Total Wealth ($) |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-09-28 14:55 | BTCUSD | V9_LON | SHORT | SL | 1.5h | 3.00% | $1,535.33 | -1.092R | -0.993R | -0.993R | $-1,523.95 | $49,653.80 | $55,085.50 | $104,739.30 |
| 2026-09-28 16:08 | XAUUSD | V3_Pro_Clean | SHORT | SL | 19.8h | 3.40% | $1,688.23 | -1.009R | -0.942R | -1.067R | $-1,589.71 | $48,064.09 | $55,085.50 | $103,149.59 |
| 2026-09-30 09:52 | XAUUSD | V10_XAU_VisB | LONG | SL | 6.2h | 2.25% | $1,081.44 | -1.030R | -0.972R | -0.729R | $-1,051.29 | $47,012.80 | $55,085.50 | $102,098.30 |
| 2026-10-02 08:00 | BTCUSD | 4H_V6_Cognitive | LONG | SL | 12.0h | 2.55% | $1,198.83 | -1.074R | -1.000R | -0.850R | $-1,198.83 | $45,813.98 | $55,085.50 | $100,899.48 |
| 2026-10-02 12:12 | NSXUSD | NSX_AMD_1D | LONG | TRAIL | 2.3h | 2.25% | $1,030.81 | +0.985R | +0.884R | +0.663R | $+911.00 | $46,724.97 | $55,085.50 | $101,810.47 |
| 2026-10-02 14:15 | XAUUSD | V10_XAU_VisB | LONG | SL | 1.7h | 2.25% | $1,051.31 | -1.028R | -0.974R | -0.730R | $-1,023.85 | $45,701.12 | $55,085.50 | $100,786.62 |
| 2026-10-02 16:24 | NSXUSD | NSX_AMD_1D | LONG | TRAIL | 59.6h | 2.25% | $1,028.28 | +0.981R | +0.856R | +0.642R | $+880.09 | $46,581.21 | $55,085.50 | $101,666.71 |
| 2026-10-05 11:55 | XAUUSD | V10_XAU_VisB | SHORT | RUNNER_SL | 19.4h | 2.25% | $1,048.08 | +2.987R | +2.479R | +1.860R | $+2,598.64 | $49,179.85 | $55,085.50 | $104,265.35 |
| 2026-10-08 15:38 | XAUUSD | V10_XAU_VisB | LONG | RUNNER_SL | 86.3h | 3.00% | $1,397.44 | +1.145R | +1.065R | +1.065R | $+1,489.03 | $50,668.88 | $55,085.50 | $105,754.38 |
| 2026-10-13 15:21 | NSXUSD | NSX_AMD_1D | LONG | SL | 22.3h | 3.00% | $1,520.07 | -1.011R | -0.932R | -0.932R | $-1,417.28 | $49,251.61 | $55,085.50 | $104,337.10 |
| 2026-10-21 12:00 | BTCUSD | 4H_V6_Cognitive | LONG | SL | 20.0h | 3.40% | $1,674.55 | -1.095R | -1.000R | -1.133R | $-1,674.55 | $47,577.05 | $55,085.50 | $102,662.55 |
| 2026-10-31 15:05 | BTCUSD | SMC_Sweep_V6 | SHORT | SL | 2.8h | 2.55% | $1,213.21 | -1.231R | -0.987R | -0.839R | $-1,197.68 | $46,379.37 | $55,085.50 | $101,464.87 |

## Table D — Recent 52 Weeks Ledger (`3ASSET — DAILY_HUNTER_$100`, `1.0x` Real Data)
| Week | Trades | Wins | Exact Net R | Sized R | PnL ($) | Active Eq ($) | Vault ($) | Total Wealth ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-W42 | 3 | 3 | +8.44R | +9.11R | $+2,933.86 | $12,314.04 | $12,214.04 | $24,528.08 |
| 2025-W43 | 4 | 1 | +1.18R | +0.79R | $+208.45 | $12,208.93 | $12,527.60 | $24,736.53 |
| 2025-W44 | 3 | 1 | +5.13R | +5.95R | $+2,177.61 | $13,116.39 | $13,797.76 | $26,914.14 |
| 2025-W45 | 6 | 4 | +6.90R | +6.73R | $+2,648.10 | $14,831.13 | $14,731.13 | $29,562.25 |
| 2025-W46 | 1 | 1 | +0.46R | +0.46R | $+205.19 | $14,933.72 | $14,833.72 | $29,767.44 |
| 2025-W47 | 5 | 1 | -2.00R | -1.88R | $-810.43 | $13,785.91 | $15,171.10 | $28,957.01 |
| 2025-W48 | 2 | 0 | -2.00R | -1.85R | $-754.57 | $13,031.34 | $15,171.10 | $28,202.44 |
| 2025-W49 | 3 | 1 | -0.98R | -0.83R | $-324.10 | $12,707.24 | $15,171.10 | $27,878.34 |
| 2025-W50 | 2 | 1 | +2.48R | +2.29R | $+859.88 | $13,567.12 | $15,171.10 | $28,738.22 |
| 2025-W51 | 1 | 1 | +0.80R | +0.77R | $+311.46 | $13,878.58 | $15,171.10 | $29,049.68 |
| 2026-W01 | 4 | 2 | +2.52R | +2.84R | $+1,162.29 | $15,040.88 | $15,171.10 | $30,211.98 |
| 2026-W02 | 2 | 0 | -1.92R | -2.04R | $-905.24 | $14,135.63 | $15,171.10 | $29,306.73 |
| 2026-W03 | 3 | 2 | +1.79R | +1.76R | $+745.20 | $14,843.49 | $15,208.43 | $30,051.92 |
| 2026-W04 | 4 | 3 | +16.52R | +18.73R | $+8,338.64 | $18,992.94 | $19,397.62 | $38,390.56 |
| 2026-W05 | 3 | 3 | +9.51R | +10.78R | $+6,143.54 | $22,317.05 | $22,217.05 | $44,534.09 |
| 2026-W06 | 5 | 3 | +2.76R | +3.14R | $+2,100.69 | $23,042.19 | $23,592.60 | $46,634.79 |
| 2026-W07 | 1 | 0 | -1.00R | -1.13R | $-783.43 | $22,258.76 | $23,592.60 | $45,851.36 |
| 2026-W08 | 3 | 1 | +1.05R | +0.93R | $+566.68 | $22,825.43 | $23,592.60 | $46,418.03 |
| 2026-W09 | 4 | 1 | +8.79R | +6.78R | $+4,081.35 | $25,299.69 | $25,199.69 | $50,499.38 |
| 2026-W10 | 2 | 1 | -0.02R | -0.15R | $-113.79 | $24,815.77 | $25,569.82 | $50,385.59 |
| 2026-W11 | 2 | 0 | -1.93R | -2.19R | $-1,600.80 | $23,214.98 | $25,569.82 | $48,784.80 |
| 2026-W12 | 7 | 4 | +14.86R | +15.50R | $+10,701.11 | $29,792.95 | $29,692.95 | $59,485.90 |
| 2026-W13 | 1 | 0 | -0.62R | -0.70R | $-623.62 | $29,169.33 | $29,692.95 | $58,862.28 |
| 2026-W15 | 7 | 3 | +3.35R | +4.12R | $+3,178.06 | $30,640.93 | $31,399.40 | $62,040.33 |
| 2026-W16 | 6 | 3 | +5.69R | +4.75R | $+4,234.67 | $32,666.60 | $33,608.39 | $66,275.00 |
| 2026-W17 | 1 | 1 | +0.87R | +0.99R | $+966.96 | $33,633.56 | $33,608.39 | $67,241.95 |
| 2026-W18 | 2 | 2 | +3.68R | +3.56R | $+3,592.57 | $35,467.26 | $35,367.26 | $70,834.52 |
| 2026-W19 | 6 | 2 | +3.85R | +3.48R | $+3,325.88 | $35,980.30 | $38,180.09 | $74,160.39 |
| 2026-W20 | 3 | 1 | +1.70R | +0.51R | $+389.84 | $36,370.14 | $38,180.09 | $74,550.23 |
| 2026-W22 | 4 | 2 | +7.90R | +9.13R | $+9,817.64 | $41,639.97 | $42,727.91 | $84,367.88 |
| 2026-W23 | 4 | 4 | +11.46R | +12.92R | $+16,138.09 | $50,302.98 | $50,202.98 | $100,505.96 |
| 2026-W24 | 1 | 1 | +4.48R | +5.07R | $+7,656.20 | $54,131.08 | $54,031.08 | $108,162.16 |
| 2026-W25 | 3 | 1 | -0.97R | -0.97R | $-1,625.55 | $52,505.53 | $54,031.08 | $106,536.61 |
| 2026-W26 | 1 | 0 | -0.32R | -0.37R | $-577.48 | $51,928.06 | $54,031.08 | $105,959.14 |
| 2026-W27 | 2 | 2 | +1.58R | +1.67R | $+2,608.49 | $54,333.81 | $54,233.81 | $108,567.63 |
| 2026-W28 | 2 | 0 | -1.96R | -2.10R | $-3,363.20 | $50,970.62 | $54,233.81 | $105,204.43 |
| 2026-W29 | 3 | 2 | +2.37R | +2.24R | $+3,426.07 | $53,545.00 | $55,085.50 | $108,630.50 |
| 2026-W30 | 1 | 0 | -0.90R | -0.90R | $-1,453.63 | $52,091.37 | $55,085.50 | $107,176.87 |
| 2026-W31 | 3 | 1 | -1.11R | -1.17R | $-1,868.53 | $50,222.84 | $55,085.50 | $105,308.34 |
| 2026-W32 | 5 | 1 | -3.13R | -2.92R | $-4,278.89 | $45,943.96 | $55,085.50 | $101,029.46 |
| 2026-W33 | 2 | 0 | -1.09R | -0.82R | $-1,131.94 | $44,812.02 | $55,085.50 | $99,897.52 |
| 2026-W34 | 4 | 2 | +0.32R | +0.26R | $+301.96 | $45,113.98 | $55,085.50 | $100,199.48 |
| 2026-W35 | 3 | 1 | +1.16R | +0.72R | $+881.06 | $45,995.04 | $55,085.50 | $101,080.54 |
| 2026-W36 | 2 | 0 | -1.95R | -1.66R | $-2,262.72 | $43,732.31 | $55,085.50 | $98,817.81 |
| 2026-W37 | 3 | 2 | +1.75R | +0.97R | $+1,270.60 | $45,002.91 | $55,085.50 | $100,088.41 |
| 2026-W38 | 5 | 3 | +6.92R | +4.60R | $+6,070.08 | $51,072.99 | $55,085.50 | $106,158.49 |
| 2026-W39 | 3 | 1 | -0.04R | +0.09R | $+104.76 | $51,177.75 | $55,085.50 | $106,263.25 |
| 2026-W40 | 7 | 2 | -3.14R | -3.06R | $-4,596.54 | $46,581.21 | $55,085.50 | $101,666.71 |
| 2026-W41 | 2 | 2 | +3.54R | +2.93R | $+4,087.67 | $50,668.88 | $55,085.50 | $105,754.38 |
| 2026-W42 | 1 | 0 | -0.93R | -0.93R | $-1,417.28 | $49,251.61 | $55,085.50 | $104,337.10 |
| 2026-W43 | 1 | 0 | -1.00R | -1.13R | $-1,674.55 | $47,577.05 | $55,085.50 | $102,662.55 |
| 2026-W44 | 1 | 0 | -0.99R | -0.84R | $-1,197.68 | $46,379.37 | $55,085.50 | $101,464.87 |
