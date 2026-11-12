# SCALP v1 — run and audit report

## Scope and run provenance

This is an exploratory EURUSD study on 2021-06, 2021-07, 2021-09, 2021-10, and 2021-11 only. All five months are seen/in-sample; 2021-10 is permanently IN_SAMPLE. 2021-08 and 2021-12 remained reserved and unloaded. The owner waived the v3 round on 2021-12; v3 was not run there.

The run bundles remain outside Git at `/tmp/build_scalp/<month>/`; their individual SHA-256 values are listed in `RUN_MANIFEST.json`. They report `loaded_until` as the exclusive upper bound (the first instant of the following month); the loaded interval is `[loaded_from, loaded_until)`. `reserved_months_loaded` is `[]` for every run. Source-data SHA-256 is the owner-verified `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`.

**Audit limitation:** the first successful monthly loop was followed by a second loop on the same five months after short-side code corrections; this violated the no-change-and-rerun constraint. The prior `/tmp` outputs were overwritten, and only the second bundles remain. Those completed bundles were also produced before the engine files were committed; their exact run-time working-tree snapshot was not recorded as a Git commit. This additionally violates the requested fixture → code → runs/report ordering and limits reproducibility. No monthly result was rerun after the later post-bundle engine changes. The main declared family is long / 1A / window 3 / L-RANGE; its entry, stop, target, and long 5m outcome ordering are unchanged by the later additions. Other post-run implementations and unavailable measurements are disclosed below.

## Frozen monthly summaries

| Month | Loaded from | `loaded_until` (exclusive) | Last month seen | Reserved months loaded | Settled primary plans | Target hits | Matched controls |
|---|---|---|---|---|---:|---:|---:|
| 2021-06 | 2021-06-01T00:00:00+00:00 | 2021-07-01T00:00:00+00:00 | 2021-06 | `[]` | 4 | 1 | 20 |
| 2021-07 | 2021-07-01T00:00:00+00:00 | 2021-08-01T00:00:00+00:00 | 2021-07 | `[]` | 3 | 1 | 15 |
| 2021-09 | 2021-09-01T00:00:00+00:00 | 2021-10-01T00:00:00+00:00 | 2021-09 | `[]` | 9 | 4 | 45 |
| 2021-10 | 2021-10-01T00:00:00+00:00 | 2021-11-01T00:00:00+00:00 | 2021-10 | `[]` | 1 | 0 | 5 |
| 2021-11 | 2021-11-01T00:00:00+00:00 | 2021-12-01T00:00:00+00:00 | 2021-11 | `[]` | 10 | 5 | 50 |

The control count is five per settled primary event in each run. Controls are paired to their originating event; the original run rows did not store `for_form`, so analysis joins each control to the unique primary event by its S/H indices and takes the form from that event.

## Declared statistical family

Exactly **20 declared tests = 5 months × 2 FVG forms × 2 metrics**. `TABLES_SCALP.md` and `STATS_SCALP.json` contain exactly 20 rows. The metrics are paired excess-hit and mean R; the event outcome is paired with the mean of its five same-month, same-NY-hour controls. The 95% interval is a day-cluster bootstrap (`B=10,000`); the paired sign-flip permutation uses 10,000 permutations, with Holm adjustment over all 20 tests. Per-month n events, n days, interval half-width (MDE), paired sign, leave-one-day-out signs, and first-event-per-day sensitivity are included.

Every form/metric summary is **UNDERPOWERED** under the predeclared precision rules; no month passes the CI + Holm + LODO gate, and there is no `CANDIDATE_FOR_CONFIRMATION`. Wide or unavailable intervals are not evidence of equivalence. Plain hit rate is shown next to event-specific break-even `1/(1+RR)`. R:R is recorded, never used as a filter. Target-behind-entry cases and ambiguous 5m bars are counted.

## Coverage limits and implementation notes

- The statistical table excludes expired plans; expiry counts, target-behind-entry counts, sub-pip counts, ambiguous bars, hit rates, and descriptive mean R are reported separately in `TABLES_SCALP.md`.
- Shorts are a separate secondary descriptive slice and are never pooled with longs.
- 1B run records are omitted from outcome tables: the final detector now checks that the intervening candle is bullish, but the earlier 1B bundle did not reliably enforce this. No rerun was made.
- The source now delegates bullish FVG detection to the imported frozen B1 `fvg_at`; the prior run used the equivalent strict wick comparison. Primary outcomes use the same strict rule.
- The final code declares and guards a 70%-of-RAM self-stop for future runs. No `MonitoringLoop` is used. That guard was added after these run bundles and must not be represented as an observed run-time measurement. The 1B implementation defect and disposition are recorded in `../VARIANT_LOG_SCALP.md`.
- The outcome bundles predate MAE, half-target-before-stop, next-15m-open sensitivity, and corrected 1B outcome fields. Bars-to-target is recoverable from `bars_held` for target hits; the other measures are not recoverable from these bundles. No rerun was made on seen months. `REPORT_SHA256.txt` lists file-level hashes and the deterministic bundle digest.
- The owner's half-body H-level sensitivity was omitted from the initial pre-run choices. It is recorded as not analyzed, not as a valid preregistered result. The final implementation includes it only as a future descriptive option.
- Fixture defects in committed `EXPECTED_SCALP_FIXTURES_2.json` were not edited; the two superseding cases are in `EXPECTED_SCALP_FIXTURES_3.json`. Fixture checks pass 13/0 and 36/0.

## Owner case cards

`CARDS/` contains 12 seeded cards: six Form 1 and six Form 2. Each shows OHLC through and including H only, and labels the target-source swing, swept-low swing, S, R, FVG status/confirmation where present, H, entry, stop, and target. The exact question appears once on each card. Outcomes are only in `ANSWER_KEY.json`; its SHA-256 (`a50df3a70f23f971a9f5a8aa5a5d151807a58d978610763f17919a89149453ad`) was committed in commit `9482680` before any card file was committed.

## Fault locator

- **NO_SIGNAL / UNDERPOWERED:** sparse event/day counts and broad paired intervals; no declared-family row meets the candidate gate.
- **Possible detector/interpretation doubt:** owner review of the 12 cards is still pending. No post-result detector change or rerun was made.
- **Process/reproducibility fault:** monthly run artifacts predate the code commit and have no exact run-time Git tree hash. See the audit limitation above.
- **Measurement gaps:** MAE, half-target-before-stop, next-bar-open sensitivity, corrected 1B outcomes, and the half-body H-level sensitivity were not produced.

## What this does NOT establish

- It does not establish that a working strategy exists or that hypothetical outcomes generalize.
- The exploratory months are seen; only one FX pair and one year are represented.
- `CANDIDATE_FOR_CONFIRMATION` would not mean a working strategy.
- The target buffer is an engineering choice; the owner's intent is a knowledge gap.
- Cards check the reading, not HYPOTHETICAL_ profitability.
- 2021-10 is IN_SAMPLE and the v3 round on 2021-12 was waived by owner decision.
