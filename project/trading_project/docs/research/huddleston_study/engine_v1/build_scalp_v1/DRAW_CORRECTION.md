# DRAW CORRECTION — owner decisions on STEP 0

`build_v3/` stays frozen. This file is the record of the owner's decisions; it supersedes the draw
statement inside `build_v3/DECLARED_CHOICES_V3.md` and `build_v3/REPORT_V3/REPORT_V3.md`.

## The rule and its result

`sha256("EURUSD|ICT_RECIPE_V3|20261109|<YYYY-MM>")` ascending:

```
344eb8c5d7c642e6ca6efb1f699d0be2d5a526cb9dd741922131cf5b33ec1c45  2021-12   N1
a1092f61dd411b08284855b586c5bc58b62a840144b2c8a24f848224a9aac64e  2021-11   N2
beb02fdfcefc4aa68865b1a03ede349c907e45ffd6364f3450aa21f751b2836f  2021-10   X1
cccee6f5b752363195d5b2937d4301853415ec4225c2d4cfc1fa9916105706b1  2021-08   X2
```

## Owner decisions (recorded verbatim in substance, tagged SOURCE_NUMBER: OWNER_SPEC)

| id | decision |
|---|---|
| a | The draw rule gives **N1 = 2021-12, N2 = 2021-11, X1 = 2021-10, X2 = 2021-08**. |
| b | **2021-10 becomes IN_SAMPLE permanently** — it was seen and used. |
| c | **Round 1 of v3 on 2021-12 is WAIVED**: v3 is superseded; v3 is **not** run on 2021-12. This is a **declared deviation** from the pre-registered v3 rule. |
| d | **2021-08 and 2021-12 stay unloaded and reserved** for confirmation of the scalp strategy. |

## What this means for reading build_v3

- Every "N2 2021-10" label in `build_v3/REPORT_V3/` means **2021-10, IN_SAMPLE, seen**.
- Every "N1 2021-11" label means **2021-11, which the rule calls N2**.
- The v3 round therefore contains **one** legitimate round-1 month (2021-11) and **one** seen month
  (2021-10); no v3 claim is promoted, which is what the report already concluded (zero signal).

## For the scalp build

Exploratory pool (declared in DECLARED_CHOICES_SCALP.md): 2021-06, 07, 09, 10, 11 — all five are
**seen** months and none of them is evidence about the reserved months. 2021-08 and 2021-12 are never
loaded; `loaded_until` and `reserved_months_loaded: []` are written into every `run_summary.json`.

## What this does NOT establish

- It does not establish that v3's conclusions would change on 2021-12; that question was waived, not
  answered.
- It does not establish that the scalp strategy is better or worse than v3; nothing has been run yet.
- It does not restore 2021-10 to any reserve; it is seen for good.
