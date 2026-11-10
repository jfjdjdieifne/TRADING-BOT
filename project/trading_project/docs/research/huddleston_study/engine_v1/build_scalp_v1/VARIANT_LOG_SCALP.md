# SCALP v1 — variant/fault log

## VLOG-01: 1B intermediary-candle condition

- **Observed:** review of the 1B implementation after the monthly bundles showed the required extra candle between R and H was not checked for bullish direction.
- **Owner rule:** 1B is R, one more bullish candle, then H.
- **Disposition:** added the explicit bullish-candle condition in the final code. Existing 1B plans/outcomes are omitted from the report because they do not reliably satisfy the declared rule.
- **Seen data action:** no change-and-rerun on any exploratory month. The original 1B output remains in the external frozen bundle and its hash is preserved in `REPORT_SCALP/RUN_MANIFEST.json`; it is not treated as valid evidence.
- **Scope:** this does not affect the primary 1A configuration or its paired 20-test table.

## VLOG-02: Card-review status

- No other concrete primary-detector defect was established by the fixture suite or the current run review.
- Owner review of the 12 case cards remains pending. Any future interpretation question belongs here; do not modify and rerun on the already-seen months.

## What this does NOT establish

- It does not establish that the event detector is complete or that HYPOTHETICAL_ outcomes generalize.
- It does not establish a working strategy or HYPOTHETICAL_ profitability.
