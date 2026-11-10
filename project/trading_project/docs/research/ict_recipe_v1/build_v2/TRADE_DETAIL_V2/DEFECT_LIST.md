# DEFECT LIST V2 — found while reading plans, recorded, nothing patched

| id | where | what | effect | fixed? |
|---|---|---|---|---|
| D5 | every saved plan record | the T1 pool's **formation index is not persisted**, so "T1 untaken between its formation and arming" cannot be reconstructed from the outputs | the check is NOT_EVALUABLE for all ~700 plans; only a 288-bar proxy is available | no |
| D6 | `build_v1/wrapper_v1.py` vs `build_v2/wrapper_v2.py` | v1 evaluates a plan on its **own decision bar** (the plan can be armed and settled inside one bar); v2 evaluates from the **next** bar | the same rule produces different "settled on the entry candle" counts between variants (v1 67 on M1, V2-A 7), so that column is **not** a like-for-like measure of the frame change | no — recorded as a convention, not a bug |
| D7 | `2021-07_V2-A` and `2021-07_V2-A-OFF` | two plans carry a T1 that lies **behind** the entry price (`plan:2021-07-27T06:15…`, T1 1.18023; `plan:2021-07-13T00:15…`, T1 1.18585) | a target on the wrong side; the plan can only lose | no |
| D8 | `report_v1.py` (v1 report) | max drawdown computed on raw R instead of the cumulative series | reported −8.05 instead of −87.63 | already recorded in `build_v2/DIAGNOSIS_V1.md`; not patched |

## What this does NOT establish

- The list is what the checks could see. A record field that is absent (D5) hides its own defect.
- D6 is a difference between two code paths, not a claim that either is wrong; it does mean the
  same-bar column must not be compared across variants, which the previous report did.
