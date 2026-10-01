# FIELD_RUNNER_MUF_S0_BASELINE_REPIN_REPORT

- Task: FIELD RUNNER BASELINE GUARD — MUF S0 POST-CLOSURE RE-PIN — PATCH ONLY
- Authorized file: `field_runner/runner_tests/test_runner_guards.py` — ONLY
- Date: 2026-09-30
- Status: `PATCHED — PENDING RE-AUDIT`

## 1. Pre-patch gate (all verified on the live tree before any write)

| Check | Required | Observed |
|---|---|---|
| MANIFEST SHA256 | `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84` | ✓ exact |
| MANIFEST lines | 196 | ✓ 196 |
| MANIFEST validation | 196 OK / 0 stale / 0 missing | ✓ exact |
| full project | 1139/1139 | ✓ 1139 passed |
| field_runner pre-repin | exactly 35/36, only `test_closed_project_manifest_untouched` | ✓ exact |

**Guard SHA256 before patch:** `7bb599f0276a31f919c788a50f7bb51337664aa122d8d5f42e22ef4baf5801c2`

## 2. Old/new baseline pins

| | digest | lines | OK / stale / missing |
|---|---|---|---|
| OLD (retired) | `12c66abe6f18300f2e00cb5c4befeafe1e3dc67c2ca50bc71db74db9ba8b367d` | 185 | 185 OK / 0 / 0 |
| NEW (live authority) | `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84` | **196** | **196 OK / 0 bad / 0 stale / 0 missing** |

Patch semantics honored:

- zero-stale allowance preserved (`bad == 0`, `bad_paths == []` — fail-closed);
- the existing 10-artifact accepted performance seal preserved **verbatim**
  (independent digest pins, extra protection, never a stale allowance);
- fail-closed behavior preserved (any staleness fails the gate);
- **no live acceptance path** for the previous 185 baseline (probe 2 proves it);
- **no redundant S0 per-file pins added** — the new MANIFEST itself is the
  authoritative complete project identity (per the existing guard architecture:
  A digest pin + B full validation + C performance seals).

## 3. Guard before/after

| | SHA256 |
|---|---|
| BEFORE | `7bb599f0276a31f919c788a50f7bb51337664aa122d8d5f42e22ef4baf5801c2` |
| AFTER | `c7e6cf8c07b6b2ee54f422aa3b1892ddcb171282493907ad123f42dfe61238e7` |

Changes inside the file (patch only): `test_closed_project_manifest_untouched`
docstring (baseline history), `closed_manifest_sha256` pin, and the two count
assertions (`manifest_lines == 196`, `ok == 196`). Nothing else.

## 4. Mandatory probe results (temporary copies only — `/tmp`)

All probes executed against pristine temp copies of the tree
(`/tmp/p4_pristine` → `/tmp/p4_run` per probe); the repository was never
mutated (post-probe residue check: clean).

| # | Probe | Expected | Observed |
|---|---|---|---|
| 1 | exact 196 clean baseline | PASS | **1 passed** ✓ |
| 2 | old 185 baseline (real pre-closure MANIFEST from git) | FAIL | **1 failed** ✓ |
| 3 | mutate one S0 MANIFEST hash (records.py line, 1 char) | FAIL | **1 failed** ✓ |
| 4 | mutate one actual S0 file (records.py) | FAIL | **1 failed** ✓ |
| 5 | mutate one previously accepted performance file (core/causal_percentile.py) | FAIL | **1 failed** ✓ |
| 6 | remove one MANIFEST line (195 lines) | FAIL | **1 failed** ✓ |
| 7 | add unauthorized line (197 lines) | FAIL | **1 failed** ✓ |
| 8 | keep 196 lines but substitute path/hash (swap two entries) | FAIL | **1 failed** ✓ |
| 9 | validation state bad > 0 (delete manifested identity.py → missing) | FAIL | **1 failed** ✓ |

**9/9 probes behaved exactly as required.** Probe scripts lived only in `/tmp`;
no probe artifacts remain in the repository.

## 5. Post-patch tests (actual)

| Gate | Expected | Observed |
|---|---|---|
| field_runner | 36/36 | **36 passed** ✓ |
| full trading_project | 1139/1139 | **1139 passed** ✓ |
| S0 dedicated | 67/67 | **67 passed** ✓ |

## 6. MANIFEST validation (post-patch)

- SHA256 **unchanged**: `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84` ✓
- 196 OK / 0 stale / 0 missing (196 lines) ✓

## 7. Exact changed files + non-touch proof

| File | State |
|---|---|
| `field_runner/runner_tests/test_runner_guards.py` | **CHANGED (the only one)** |

- `trading_project/**`: before/after snapshot comparison — **byte-identical**
  (all paths).
- other `field_runner/**` files: **byte-identical**.
- Non-allowed set checked: 261/261 files identical; zero diffs.
- No change to `MANIFEST.sha256`, S0 src/tests, docs, closure milestone/seal,
  or any other field_runner file. No cleanup, no refactor, no S1, no MUF
  implementation change.

## FINAL STATE

**PATCHED — PENDING RE-AUDIT**

The external Field Runner baseline guard now pins the official MUF V1 S0 CLOSED
baseline (196 lines / `899febb4…` / 196 OK, zero stale) with the performance
seal preserved and no acceptance path for the retired 185 baseline. All nine
mandatory probes behaved correctly; field_runner is back to 36/36; the project
test suites are unchanged and green. No S1. STOP.
