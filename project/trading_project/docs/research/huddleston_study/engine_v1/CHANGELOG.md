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

- Ran the fixed diagnostic on 2022/2023: 23/24 release-labelled bars were the
  largest of the four offsets; 2022-03-04 was the disclosed +5m exception.
  Added documentation and an opt-in regression test for this pinned evidence.
  No protocol value, loader rule, or engine behaviour was changed after seeing
  the real alignment result.

No story test has been run. No result-driven engine change has been made.
