# STEP 0 — draw audit and replay cause (report only)

Nothing in this file is a run of the new strategy. Both items are computed from bytes and from saved
outputs already in the workspace.

## 0.1 The draw — the previous report had it wrong

Recomputed `sha256("EURUSD|ICT_RECIPE_V3|20261109|<YYYY-MM>")`, full digests, sorted ascending:

```
344eb8c5d7c642e6ca6efb1f699d0be2d5a526cb9dd741922131cf5b33ec1c45  2021-12
a1092f61dd411b08284855b586c5bc58b62a840144b2c8a24f848224a9aac64e  2021-11
beb02fdfcefc4aa68865b1a03ede349c907e45ffd6364f3450aa21f751b2836f  2021-10
cccee6f5b752363195d5b2937d4301853415ec4225c2d4cfc1fa9916105706b1  2021-08
```

| role | month | digest |
|---|---|---|
| **N1** | **2021-12** | `344eb8c5…33ec1c45` |
| **N2** | **2021-11** | `a1092f61…aac64e` |
| **X1 (reserved)** | **2021-10** | `beb02fdf…b2836f` |
| **X2 (reserved)** | **2021-08** | `cccee6f5…106706b1` |

**It differs from what the V3 report said, and the error is mine.** Hex sorts digit-first: `344e…`
starts with `3`, so 2021-12 comes before every `a…`/`b…`/`c…` digest. I stated "N1 = 2021-11,
N2 = 2021-10, reserved = 2021-08/2021-12". The correct reading is N1 = 2021-12, N2 = 2021-11,
X1 = 2021-10, X2 = 2021-08.

What was actually loaded and run:

| month | role per the rule | what was done | status |
|---|---|---|---|
| 2021-11 | N2 | 22 run directories (10 V3 variants + WIDE on 15m and 1h, + NULL, + V2-A/V2-B references) | **legitimate round-1 month** |
| 2021-10 | **X1 reserved** | 22 run directories, and it enters every paired table, the WIDE feature audit and the hygiene comparison | **CONTAMINATED — it has been seen** |
| 2021-12 | **N1** | never loaded (no directory, `loaded_until` never passes 2021-11-30) | **round 1 is incomplete** |
| 2021-08 | X2 reserved | never loaded | **still untouched** |

Effect on the reserved pool: from two untouched months to **one** (2021-08). 2021-10 can never again
serve as a confirmation month for this recipe — its results have been printed, read and used to rank
switches. 2021-11 is not "burnt" (it was legitimately N2), but it is now *seen* by definition.

Consequence for every number in `build_v3/REPORT_V3/`: the labels "N2 2021-10" must be read as
"**SEEN 2021-10 (X1, contaminated)**", and "N1 2021-11" as "**N2 2021-11 (correct role, renamed)**".
The *pair* of months used is therefore one legitimate round-1 month (2021-11) and one contaminated
one (2021-10). No table value is wrong as arithmetic; the *standing* of the evidence is wrong.

Proposal — **not executed, needs authorisation**:

1. Run **N1 = 2021-12** with the frozen V3 code, once per variant per frame, no retry, no change to
   code or declarations. That completes round 1 with two legitimate months (2021-12, 2021-11).
2. Re-label 2021-10 as IN_SAMPLE in any future report; exclude it from paired deltas and from the
   feature audit of any confirmation decision.
3. Treat **2021-08 as the only untouched reserve**. Any confirmation round then needs at least a
   second untouched month, which does not exist inside 2021 — that requires a new data authorisation
   (another year), and I will not reach for it on my own.
4. Keep `build_v3/` frozen: this file supersedes its draw statement rather than editing it.

## 0.2 Why the fresh replay matched only 175 of 587 while v2 reported 699/699

Two different things were being called a "replay". Measured cause, not a hypothesis: I re-ran a
parameterised replay over the 685 settled plans of all 16 saved v2/v1 runs and counted matches within
0.05 R:

```
offset=0  cost=1 half-spread   order=stop_first   match 244/685   median |dR| 0.0741
offset=0  cost=2 half-spreads  order=stop_first   match 610/685   median |dR| 0.0000
offset=1  cost=1 half-spread   order=stop_first   match 250/685   median |dR| 0.0741
offset=1  cost=2 half-spreads  order=stop_first   match 622/685   median |dR| 0.0000
offset=1  cost=2 half-spreads  order=t1_first     match 615/685   median |dR| 0.0000
```

So the 412 disagreements were almost entirely **my cost term**: `diagnose_v2.py` charged the spread
once (`spread/2` at the exit bar, the V3 declaration), while the v2 engine charges **two halves**
(`half_spread_at_decision + spread/2`). On a 2-pip stop one half-spread is ~0.07 R, which is exactly
the median error. The residual ~10 % is the first-evaluation-bar offset and intrabar ordering. And
v2's "699/699" was never an independent replay: `td_lib.replay()` was written to mirror the engine's
own settlement function and was fixed four times against it (expiry origin, the "neither" exit, the
trigger-bar offset, the F4 case) — it was calibrated, so 699/699 measures agreement with a copy, not
independence. The V3 1a *paired* delta survives this, because both arms used the same cost term; the
absolute R in that section does not.

## What this does NOT establish

- It does not establish that the V3 switch ranking would change if 2021-12 were run; that is exactly
  the open question, and it stays open until that run is authorised.
- It does not establish that 2021-10's numbers were favourable or unfavourable to any switch; the
  contamination is about standing, not about direction.
- It does not establish that the V3 engine's own cost convention (one half) is wrong; it is a declared
  choice, and it is applied identically to every V3 arm.
