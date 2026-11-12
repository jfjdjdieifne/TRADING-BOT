# PREREGISTRATION V2 — the month draw, recorded before any 2021-07..12 bar was loaded

The draw follows §2.3 of `holdout_v1/PREREGISTRATION_V1.md` exactly (the "W3 procedure"), with the
entity and study changed and nothing else.

```text
DRAW_ENTITY   = "EURUSD|ICT_RECIPE_V2|20261109|" + month   (ASCII, vertical bars, no spaces)
DRAW_SEED     = 20261109                    tag: ENGINEERING_CHOICE
CANDIDATE_SET = 2021-07 .. 2021-12          (6 months)     tag: ENGINEERING_CHOICE (the owner's range)
N_MONTHS      = 2                           tag: ENGINEERING_CHOICE (owner: "TWO new months")
EXCLUDED      = 2021-06 (already seen, IN_SAMPLE only)
```

Algorithm: for each candidate month build the exact text, take SHA-256 of its UTF-8 bytes, sort the six
months by that hex string ascending, take the first two.

| rank | month | sha256 prefix | draw string |
|---|---|---|---|
| 1 | `2021-09` | `1574d03fd2cbb895` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-09` |
| 2 | `2021-07` | `73bb5bdeb802c38e` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-07` |
| 3 | `2021-10` | `b897f08f3c6dc6fe` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-10` |
| 4 | `2021-12` | `c68fec6bd2467c44` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-12` |
| 5 | `2021-08` | `e6620cf675b47d2d` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-08` |
| 6 | `2021-11` | `f18457a3e9a6420f` | `EURUSD\|ICT_RECIPE_V2\|20261109\|2021-11` |

**M1 = `2021-09`** (rank 1), **M2 = `2021-07`** (rank 2). Recorded here before any bar of either month
was read. The two months are adjacent-ish in the year and not contiguous; no re-draw was attempted for
spread, and none will be.

Re-execute by hand:

```bash
for m in 2021-07 2021-08 2021-09 2021-10 2021-11 2021-12; do
  printf 'EURUSD|ICT_RECIPE_V2|20261109|%s' "$m" | sha256sum | sed "s|-| $m|"
done | sort | head -2
```

## What this does NOT establish

- It does not establish that two months represent 2021 H2, or that the draw is balanced: two months of
  one instrument is a description of two months.
- It does not establish that the owner has not seen 2021-07 or 2021-09 in some other form; it records
  only that no chart of either was shown in this work before the runs.
- It does not bind the analysis: if the two months disagree, the disagreement is the result.
