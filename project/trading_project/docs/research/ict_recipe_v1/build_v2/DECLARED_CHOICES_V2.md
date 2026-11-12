# DECLARED CHOICES V2 — every number and rule, tagged, before the runs

Tags used: `SOURCE_NUMBER` (a number printed in a source), `ENGINEERING_CHOICE` (a build decision),
`KNOWLEDGE_GAP` (the source does not say), `FIXTURE`. The tag `ENGINEERING_HYPOTHESIS` is **not used
anywhere in v2** (the owner forbade it); the one v1 use is re-tagged `KNOWLEDGE_GAP` in
`DIAGNOSIS_V1.md` section g.

| row | decision | value | tag | why / what it does NOT change |
|---|---|---|---|---|
| A | variants kept parallel | **V2-0** (5m + repairs), **V2-A** (15m setup), **V2-B** (1h setup), each with a **SESSION_OFF** counterpart for A and B | ENGINEERING_CHOICE | No variant is merged and none is called the winner. The frame is chosen **before** the runs, never by looking at R. |
| A2 | what stays fixed across variants | session window, entry rule, cost model, tracker, expiry, bias source, ranking criteria | ENGINEERING_CHOICE | One change at a time: the frame of the thesis. |
| B | multi-frame causality | a setup candle exists only after its **last** 5m bar closed; zones, swings and pools appear only then; a forming candle's partial high/low is never exposed | ENGINEERING_CHOICE (implemented by construction in `frame_v2.FrameAggregator`) | Fixtures `fx_15m_not_before_third_close`, `fx_15m_emits_on_bucket_change`, `fx_no_partial_high_low_leak`, `fx_swing_needs_right_bar` test exactly this. |
| C | entry | unchanged from v1: the plan is armed when the decision bar's **close** is inside the setup-frame zone (`gates`), entry = the zone edge nearest the direction | ENGINEERING_CHOICE (inherited) | Fill convention unchanged (limit at the edge; no next-open assumption added). When the touching bar also reaches the stop, v1's conservative same-bar rule settles it — **counted** in every summary as `same-bar`. |
| D | stop | the far edge of the setup-frame zone (sweep zones: the sweep wick). No pip minimum, no maximum, no filter | ENGINEERING_CHOICE, with `KNOWLEDGE_GAP: STOP_LEVEL_WITHIN_ZONE` recorded (the source says "below the mean threshold", i.e. inside the zone) | Stop distance is recorded in pips and as a fraction of the setup candle's range. Changing the stop rule as well would be a second change. |
| E | targets | T1 = nearest untaken opposing pool beyond entry; T2 = the next one; `None` if only one. For V2-A the pool list is the union of 15m and 1h pools, each labelled with its frame; for V2-B it is 1h only; for V2-0 it is 5m only | ENGINEERING_CHOICE; concept from `draw_on_liquidity.md` ("where's the next likely draw") | R is settled on **T1 only**; T2 is reported as an informational outcome and flagged by the frame relation of the pool (`t2_frame`), never by a numeric cutoff. |
| F | D4 one thesis = one plan | thesis id = `setup_frame:zone_id:direction`; a settled or already-armed id is never re-armed; armings and theses are counted separately | ENGINEERING_CHOICE (repair of the v1 defect found in `DIAGNOSIS_V1` c) | In v1 the same zone was armed up to **21** times; that is why 106 plans were 43 opinions. |
| G | D1/D2/D3 repairs | D1: pool age = frame index − pool frame index; D2: `formed_index < 0` → `age None`, state `NO_FORMATION_BAR`; D3: `position_ratio` clamped with state `ABOVE_RANGE` / `BELOW_RANGE` / `INSIDE_RANGE` | ENGINEERING_CHOICE | None of the three can change a decision: they are labels on records. The fixtures assert the labels, not the outcome. |
| H | dealing range | keep the local incremental `DealingRangeState`, computed on the **setup frame** | `KNOWLEDGE_GAP: DEALING_RANGE_DEFINITION` (no card names which two swings) | `REUSE_DECISIONS` row 4 rejected the batch engines as "not incremental"; `DIAGNOSIS_V1` e says that reason is acceptable but not decisive. A parity check against `ict_engine/ranges.py::dealing_range_trace` is **DEFERRED** and listed as missing. |
| I | order blocks | used, unchanged chain, **not loosened** | ENGINEERING_CHOICE | 21 created / 2 VALID in 2021-06 (`DIAGNOSIS_V1` e). Loosening the chain to manufacture zones would be tuning. |
| J | session window | `EURO_0200_0500` as in v1; SESSION_OFF variants run with the window gate forced open | ENGINEERING_CHOICE (v1 row 10) | Reported separately; the owner asked for both. |
| K | zone ranking | (i) bias agreement, (ii) freshness, (iii) context-relative distance; a conflict of (i) and (iii) ⇒ `criteria_conflict` and **no plan** | `KNOWLEDGE_GAP: ZONE_RANKING_PRIORITY` | Unchanged from v1 so the frame is the only difference. |
| L | window | 20 trading days expressed in time: 5,760 × 5m = 1,920 × 15m = 480 × 1h | ENGINEERING_CHOICE | The `WINDOW_BARS` sensitivity sweep is **DEFERRED**: running it on M1/M2 would test two changes at once and would invite picking the window that looks best. |
| M | statistics | per run: plan count, mean R, median R, and a bootstrap interval of the mean R — `B = 2000` resamples, 95 % percentile interval, `random.Random(20261109)` | ENGINEERING_CHOICE (B, level, seed) | The interval is reported whether or not it contains 0, and it is stated in words that a small number of plans makes it wide. |
| N | null baseline | same decision bars, same stop distance, same T1 distance, direction drawn by `random.Random(20261109)`; settled by the same conservative rule and the same spread cost | ENGINEERING_CHOICE | Shows what geometry plus spread alone produce; it is not a strategy and is never compared as one. |

## What v2 does NOT change

- The data (one file, sha256-verified), the history start (2021-01-01), the decision cadence (one per
  closed 5m bar), the bias source (completed daily/weekly buckets from the 5m stream), the cost model
  (half the spread each side), the 288-bar expiry, the stop-first settlement, and the ranking criteria.
- No rule, threshold or number is imported from the old pipeline; only modules are imported.

## What this does NOT establish

- It does not establish that these are the right choices; each is a declared position, not a finding.
- It does not establish that one change at a time isolates the cause: D4 alone changed the number of
  plans by a factor of three (see `COMPARISON_M1.md`), so the control is a different population of
  plans, not the same plans with a different stop.
- The deferred items (H parity check, L sensitivity) are missing evidence, not evidence.
