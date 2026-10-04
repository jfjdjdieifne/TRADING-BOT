# FIELD_RUNNER_MUF_S1_BASELINE_REPIN_REPORT

- Task: FIELD RUNNER BASELINE GUARD — MUF S1 POST-CLOSURE RE-PIN — PATCH ONLY
- Authorized file: `field_runner/runner_tests/test_runner_guards.py` — ONLY
- Date: 2026-10-03
- Status: `CLOSED` (re-pin verified against all 10 adversarial/mutation probes and live test gates)

## 1. Pre-patch gate (all verified on the live tree before any write)

| Check | Required | Observed |
|---|---|---|
| MANIFEST SHA256 | `f6d0d00446c70a997d357db66a82db6237a3254fdcea3a8674a7670d5d58e3a6` | ✓ exact |
| MANIFEST lines | 202 | ✓ 202 |
| MANIFEST validation | 202 OK / 0 stale / 0 missing | ✓ exact |
| MUF S1 dedicated | 89/89 | ✓ 89 passed |
| MUF S0 dedicated | 67/67 | ✓ 67 passed |
| full project | 1228/1228 | ✓ 1228 passed |
| field_runner pre-repin | 35/36, only `test_closed_project_manifest_untouched` | ✓ exact |

**Guard SHA256 before patch:** `c7e6cf8c07b6b2ee54f422aa3b1892ddcb171282493907ad123f42dfe61238e7`

## 2. Old/new baseline pins

| | digest | lines | OK / stale / missing |
|---|---|---|---|
| OLD (retired MUF S0) | `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84` | 196 | 196 OK / 0 / 0 |
| NEW (live authority MUF S1) | `f6d0d00446c70a997d357db66a82db6237a3254fdcea3a8674a7670d5d58e3a6` | **202** | **202 OK / 0 bad / 0 stale / 0 missing** |

Patch semantics honored:
- zero-stale allowance preserved (`bad == 0`, `bad_paths == []` — fail-closed);
- the existing 10-artifact accepted performance seal preserved **verbatim** (independent digest pins, extra protection, never a stale allowance);
- fail-closed behavior preserved (any staleness fails the gate);
- **no live acceptance path** for the previous 196-line or 185-line baselines (probe 2 proves it);
- **no redundant S0/S1 per-file pins added** — the 202-line MANIFEST itself is the authoritative complete project identity.

## 3. Guard before/after

| | SHA256 |
|---|---|
| BEFORE | `c7e6cf8c07b6b2ee54f422aa3b1892ddcb171282493907ad123f42dfe61238e7` |
| AFTER | `a89057f6466342c1e8d9b45fcf2a6033ed50219c1c7c57ec1c8cde18b398638e` |

## 4. Mandatory probe results (temporary copies only — `/tmp`)

All probes executed against pristine temp copies of the tree (`/tmp/p60_pristine` → `/tmp/p60_run` per probe); the repository was never mutated and `/tmp` was cleaned up completely.

| # | Probe | Expected | Observed |
|---|---|---|---|
| 1 | exact 202 clean MUF S1 baseline | PASS | **1 passed** ✓ |
| 2 | retired 196 MUF S0 baseline (`899febb4…` reconstructed faithfully) | FAIL | **1 failed** ✓ |
| 3 | mutate one S1 MANIFEST hash (`price_path.py` line, 1 char) | FAIL | **1 failed** ✓ |
| 4 | mutate one actual S1 file (`price_path.py`) | FAIL | **1 failed** ✓ |
| 5 | mutate one actual S0 file (`records.py`) | FAIL | **1 failed** ✓ |
| 6 | mutate one accepted performance file (`core/causal_percentile.py`) | FAIL | **1 failed** ✓ |
| 7 | remove one MANIFEST line (201 lines) | FAIL | **1 failed** ✓ |
| 8 | add one unauthorized line (203 lines) | FAIL | **1 failed** ✓ |
| 9 | keep 202 lines but swap two entries | FAIL | **1 failed** ✓ |
| 10 | delete manifested S1 file (`price_path.py` missing → `bad > 0`) | FAIL | **1 failed** ✓ |

**10/10 probes behaved exactly as required.**

## 5. Post-patch tests (actual)

| Gate | Expected | Observed |
|---|---|---|
| field_runner | 36/36 | **36 passed** ✓ |
| MUF S1 dedicated | 89/89 | **89 passed** ✓ |
| MUF S0 dedicated | 67/67 | **67 passed** ✓ |
| full trading_project | 1228/1228 | **1228 passed** ✓ |

## 6. MANIFEST validation + non-touch proof

- `MANIFEST.sha256` SHA256 **unchanged**: `f6d0d00446c70a997d357db66a82db6237a3254fdcea3a8674a7670d5d58e3a6` ✓
- Validation: `202 OK / 0 stale / 0 missing` ✓
- `project/trading_project/**`: **byte-identical** before == after across all files ✓
- All other `field_runner/**` files: **byte-identical** before == after ✓

## 7. Certification boundary

Proves only that the external Field Runner baseline guard now pins the official MUF V1 S1 CLOSED 202-line baseline (`f6d0d004…`) with zero stale allowance. Does NOT certify MUF S2, turning-point quality, wave hierarchies, predictive support, statistical independence, edge, profitability, Model, Strategy, Signal, or PnL.
