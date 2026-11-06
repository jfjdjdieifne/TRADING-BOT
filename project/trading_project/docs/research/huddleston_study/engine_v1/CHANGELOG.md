# Changelog

## M0 — before timestamp diagnostic results

- Imported the assigned project tree without reset or merge.
- Added the annual-file allowlist, immediate 2025-05-01 cutoff, immutable candle
  values, and bar-end availability semantics.
- Added an executable prefix-invariance harness and fixed its output contract.
- Fixed the timestamp diagnostic protocol in `PARAMETERS.md` before running it.

- Synthetic-only correction before inspecting real event alignment: replaced the
  invalid universal first-Friday schedule heuristic with the 24 explicit BLS
  dates (March 2023 was 10 March); corrected a float assertion in its unit test.

No story test has been run. No result-driven engine change has been made.
