# FIXTURES V2 — what is frozen and what it proves

`EXPECTED_V2/EXPECTED_fx_*.json`, frozen with `python3 fixtures_v2.py --freeze`, checked with
`--check`. **12 frozen, 12 pass, 0 fail.**

| fixture | what it proves | frozen value (abridged) |
|---|---|---|
| `fx_15m_not_before_third_close` | a 15m candle does not exist while it forms | `emitted: [false, false, false]` |
| `fx_15m_emits_on_bucket_change` | it appears exactly when the next bucket opens | `first_emitted_at_push: 3` |
| `fx_no_partial_high_low_leak` | a forming candle never enters the setup window | `window_lengths_during: [0,0,0]`, `window_after_close: 1` |
| `fx_swing_needs_right_bar` | a setup-frame swing waits for its right-hand candle | `per_candle_swing_count: [0,0,0,1]` |
| `fx_d1_age_same_index_space` | pool age = frame index − pool frame index | `formed_indices: [6], ages: [1], frame_index: 7` |
| `fx_d2_minus_one_index` | a pool with no formation bar reports `NO_FORMATION_BAR` | `ages: [null,null]` |
| `fx_d3_ratio_state` | the range ratio is clamped **and labelled** | `above: (1.0, ABOVE_RANGE)` |
| `fx_stop_far_edge_vs_sweep` | stop = far edge of the zone; sleeve wick for a sweep zone | `fvg_stop 1.0990`, `sweep_stop 1.0980` |
| `fx_two_targets_and_one_target` | T1+T2 and the single-target note | `t1 1.104`, `t2 1.108`, `one_t2 null` |
| `fx_no_plan_when_stop_equals_entry` | a degenerate zone yields no plan | `error: stop equals entry; no plan` |
| `fx_thesis_identity` | D4 identity blocks the settled thesis, allows another zone | `a_blocked true`, `b_allowed true` |
| `fx_bucket_alignment` | bucket boundaries are UTC-aligned for 5m/15m/1h | `2021-03-01T10:45 / 10:45 / 10:00` |

## Known deviations from the prescribed order and from the owner's list

1. The fixtures were frozen **after** the wrapper skeleton existed and **before** any month was run.
   The owner asked for fixtures first; this is a deviation and is recorded rather than disguised.
2. The first freeze was thrown away unsent: two fixtures were vacuous (`fx_d1` compared empty lists,
   `fx_no_partial_high_low_leak` had no positive control) and `fx_d2` crashed on a missing key. They
   were rewritten, `EXPECTED_V2/` was deleted, and the freeze was re-run once. From that point no
   EXPECTED file was edited.
3. The owner's list asks for one fixture where **V2-0 and v1 must differ** and one where they **must
   agree**. Those two are **not** written as fixtures: the difference is D4 arming counts, which needs
   a stream, not a hand-made candle, and the runs answer it directly (2021-06: v1 106 armings / 43
   theses; V2-0 43 theses). This is recorded as a gap, not counted as a pass.

## What this does NOT establish

- A passing fixture proves only that the code does what the file says on hand-made candles.
- `fx_thesis_identity` tests the identity string, not the wrapper's use of it; that is exercised by the
  runs and by the arming/thesis counts in every SUMMARY.
- Nothing here says the setup-frame separation improves any outcome.
