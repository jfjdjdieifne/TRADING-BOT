# NON-PLAN SAMPLE `V0` — NOT DRAWN

**Status: `VOID — NO DECISION RECORDS EXIST`.**

The sample is specified as: 10 March decision points that produced **no plan**, drawn by a
seeded procedure, plus the 3 non-plan decisions that came closest to becoming a plan (selected
by the engine's own gate output, not by outcome).

## Why no sample is drawn

`decisions_produced = 0`. The single authorised run was killed by the operating system before
it reached the first decision instant, so the raw output contains no `no-plan` records at all:

```text
/tmp/dev_month_v0/raw/   →   run.log only   (264 bytes)
                             cases_v1.jsonl  NOT WRITTEN
                             summary_v1.json NOT WRITTEN
```

A sample cannot be drawn from an empty set. Drawing one anyway would mean inventing records,
which no rule in this project permits.

## The procedure, declared now so a later run is not free to invent one

Recorded here as a declaration, **not executed**:

```text
SEED        = 20261109                        (ENGINEERING_CHOICE)
ALGORITHM   = take the ordered list of March decision records whose kind == "no-plan";
              for each, form the string  "NONPLAN|V0|20261109|<as_of ISO timestamp>";
              compute SHA-256; sort ascending by hex; take the first 10.
REPLACEMENT = a drawn record that is mechanically unusable is replaced by the next in
              order and the replacement is logged; no other substitution is allowed.
CLOSEST-3   = the three `no-plan` records whose gate reason is nearest to a pass under the
              engine's own ladder (gate_pass then strict_pref), never by outcome.
```

## What this does NOT establish

- It establishes no property of non-plan decisions: none was observed, counted, or read.
- It does not establish a non-plan rate, a gate-rejection distribution, or which reasons
  dominate — all of those are reported as **not produced** in `SUMMARY_V0.md`.
- The procedure above is a declaration about a future run, not evidence about this one.
