# Automated checks — SCALP v1

- Frozen sweep fixtures: **13 checks, 0 failures** (`test_scalp_fixtures.py`).
- New scalp fixtures: **36 checks, 0 failures** (`test_scalp_fixtures2.py`), including the numbered fixture supersessions.
- Python AST syntax parse for the local `*.py` files: **passed**.
- Declared statistical family: **20 declared tests; 20 report rows**.
- Five monthly run summaries: all show `reserved_months_loaded: []`; exact windows and SHA-256 values are in `RUN_MANIFEST.json`.
- Direct forbidden-window probes for 2021-03, 2021-08, 2021-12, and 2022-01: all rejected before opening/constructing any market-data bar.
- Source data SHA-256: matches the recorded owner-verified `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`.
- Answer-key digest: recomputed SHA-256 matches the committed `ANSWER_KEY.sha256`; the key commit predates the card commit.
- No pytest cache was used; fixture test scripts ran with `PYTHONDONTWRITEBYTECODE=1` and the pinned `/tmp/venv_ict` interpreter.

The scripts are the repository's direct fixture harnesses; this check did not run the repository-wide test suite. No monthly outcome rerun occurred during final report generation.

## What this does NOT establish

- Passing fixtures does not establish a working strategy, detector completeness, or HYPOTHETICAL_ profitability.
- It does not repair the run-before-code-commit process deviation documented in `README_REPORT.md`.
