# تصميم الاختيار الزوجي — «اختر منطقة واحدة من `N`»

# PAIRWISE SELECTION DESIGN `V1` — "choose 1 of N candidate zones"

**Status: DESIGN ONLY — NOT IMPLEMENTED.** No code, no test, no data. Nothing here is built.
**Precondition:** `OWNER_DECISION_D3.md` signed (clause C and clause D both constrain this
design). Without it, this document is a plan.

**Purpose.** Define how a selection among *zones* (not points) plugs into the existing kernel
**without editing any existing module**, and define honestly where the design must stop and
print a `KNOWLEDGE_GAP` instead of inventing a ranking.

---

## 1. The plug point, as it exists today

`expert_selection.apply_expert_preferences(...)` is called from exactly one runtime place:
inside `expert_structural_reference_selection()` (`expert_selection.py`, the call sits after
the eligibility filter, after the F2 role checks and after the F4 tie check). Its effective
call shape, as read from that caller:

```python
apply_expert_preferences(eligible_ids, maps, knowledge,
                         task_id=SRS_TASK_ID, scene=scene)
        -> (activated, inactive, conflicts, winner, diagnostics)
```

Ordering constraints that the new call site inherits and may not reorder:

1. **Eligibility first** — a candidate that is not eligible is never a preference winner.
2. **F2 role validity** — a missing or unknown role returns `UNRESOLVED` **before**
   preferences. A missing role never falls through to preference selection.
3. **F4 tie check** — an equal knowable-time / recency tie returns `UNRESOLVED` **before**
   preferences. A preference may never break such a tie.
4. **Preferences last**, and only from a documented preference set.

A second-order caller exists: `analysis_lifecycle.py::_select_reference()`, which is what the
monitoring lifecycle uses. It is not modified by this design; it continues to receive points
and legs only.

---

## 2. What a "candidate zone" is — the two carriers that already exist

| carrier | module | fields that matter for selection | status |
|---|---|---|---|
| `FVGRegion` | `connected_readings.py` | `region_id`, `timeframe`, `direction`, `bar1/bar2/bar3`, `lower_bound`, `upper_bound`, `observability_time`, `ce_midpoint`, `interactions`, `interpretation_notes`, `scan_floor`, and the methods `availability(as_of)` / `note_interaction(...)` / `to_record()` | exists, is **not** in the selection pool |
| `OBLikeCandidate` | `study_links.py` | `candidate_id`, `direction`, `bar_index`, `bar_time`, `open/high/low/close`, `context_ref_id`, `context_ref_level`, `eligibility`, `state`, `role`, `role_assignments`, `events`, `ordering` | exists, is **not** in the selection pool |

Both are **read-only inputs** to this design. The design does not add fields to either
dataclass, does not change `state`/`role` semantics, and does not write into
`interactions`/`events`.

### 2.1 The view object (new file, no mutation)

A new immutable view maps either carrier onto the shape the kernel understands:

```text
ZoneCandidateView(
    zone_id,            # region_id or candidate_id, verbatim
    source_class,       # "FVGRegion" | "OBLikeCandidate"
    side,               # "buy" | "sell"
    upper, lower,       # bounds; for OBLikeCandidate a zero-width level is allowed
    observability_time, # FVGRegion.observability_time | OBLikeCandidate.bar_time
    knowable_bar,       # the bar index at which the zone is first readable
    timeframe,
    geometry,           # dict: the five measurements of §4, each with its own availability tag
)
```

Construction is pure: no field of the source object is modified, and the view is serialised
to a record in the same style as `csm.candidate_record(...)` so that a run is reproducible
from JSON alone.

---

## 3. The new call site (zero edits to existing modules)

### 3.1 Placement

```text
NEW FILE : src/trading_system/research/contextual_selection/zone_selection_v1.py
```

No existing file is edited, including `contextual_selection/__init__.py` — the module is
imported by its full path, not re-exported. (Alternative the owner may prefer: a separate
package `src/trading_system/research/zone_selection_v1/` for stricter isolation. Both are new
files only; the choice is cosmetic and is deferred to the build task.)

### 3.2 Flow

```text
zones observed at t  (FVGRegion / OBLikeCandidate, read-only)
        │
        ├── build ZoneCandidateView per zone                       (§2.1)
        ├── eligibility filter  (identical rule; ineligible ⇒ never a candidate)
        ├── F2-style role check (no role / unknown role ⇒ UNRESOLVED, stop)
        ├── tie check           (equal knowable time ⇒ UNRESOLVED, stop)
        └── apply_expert_preferences(zone_ids, evidence_maps, knowledge, …)
                    │
                    ├── a documented preference decides  ⇒ chosen, with preference id
                    ├── preferences conflict / contradict ⇒ "criteria conflict" printed
                    └── no documented preference reaches these zones
                                             ⇒ criteria_priority = KNOWLEDGE_GAP
                                                + UNRESOLVED (never an invented order)
```

**The last branch is the honest default and is expected to be the common case in `V1`.**
There is no documented preference set for zones in the tree today. Therefore `V1` will most
often return `UNRESOLVED` with `KNOWLEDGE_GAP: criteria_priority`, which is a correct output,
not a defect.

### 3.3 What is deliberately not done

- no weighted score, no sum of z-scores, no "confidence";
- no lexicographic ordering invented to break a tie;
- no distance-normalised blend of the five comparisons;
- no silent fallback to "the nearest zone";
- no re-ranking of points and legs (their path is untouched).

---

## 4. The five relational comparisons

Each is a *description* of the relationship between one candidate zone and the chart up to
`t`. Each carries its own availability tag. A comparison whose inputs are missing is printed
as missing — it is not skipped silently.

| # | comparison | measurement (relative only, `D3` clause C) | which module supplies the geometry | availability today |
|---|---|---|---|---|
| 1 | **HTF alignment** | direction of the zone vs direction of the last confirmed structure on the higher timeframe, both measured on the same chart cut at `t` | `b1_candles.candle.build_candles` (resample to the higher scale) + `b1_candles.swing.swing_at`; higher-timeframe *bias* rule does not exist | **PARTIAL** — geometry yes, alignment rule no (`C1.1 Bias` = «لم يبدأ», `C3.9 Timeframe pairing` = «لم يبدأ») |
| 2 | **preceded by sweep / displacement** | was there a sweep of a named swing level, and/or a displacement candle, within `k` bars before the zone formed? `k` is **not** chosen here | `c1_catalog.liquidity_sweep.sweep_at_swing_level`, `latest_swing_level`, `latest_swing_reference`; `c1_catalog.displacement.displacement_at` | **AVAILABLE (geometry)** — `C2.4` and `C2.5` are «مغطى بالكامل»; the *window* `k` is `KNOWLEDGE_GAP: sweep_displacement_lookback` |
| 3 | **mitigation state** | has price traded into the zone since it became observable; how many times; at what depth | `FVGRegion.interactions` (slot exists) and `FVGRegion.availability`; `OBLikeCandidate.state` / `role_assignments` / `events` (state machine exists for OBs only) | **PARTIAL** — FVG has a slot but no mitigation state machine; "mitigated" has no numeric definition in sources |
| 4 | **position in the dealing range** | where the zone sits between the range low and high at `t` — a rank/ratio, `RELATIVE_ONLY` | **nothing** | **MISSING** — `C1.4 Dealing range` = «لم يبدأ»; `C1.3 Premium / discount` = «لم يبدأ»; `COVERAGE_TABLE_C1` §E-4 records `GAP_LOCATION` absent from `common.py` |
| 5 | **distance to target liquidity** | distance from the zone's near edge to the nearest named level in the direction of travel, as a ratio to the zone's own height | partially: `latest_swing_level` gives *named swing levels*; there is no liquidity-pool object and no draw-on-liquidity object | **MISSING** — `C2.3 Buy-side / sell-side liquidity` = «لم يبدأ», `C1.2 Draw on liquidity` = «لم يبدأ», `C5.3 IRL / ERL` = «لم يبدأ» |

**Reading of the table.** Two of five comparisons have real geometry today (2 and, in part,
1 and 3); two have none (4 and 5). A design that silently dropped 4 and 5 would be a design
that quietly answered "zone quality" with half the question missing. Hence §5.

---

## 5. Criterion priority — the honest failure mode

The rule this design enforces:

> **The priority of the five criteria comes from a source or from the owner. If neither
> supplies it, print `KNOWLEDGE_GAP: criteria_priority` and output `criteria conflict`.
> Never invent weights, never invent an order.**

Practically, the selection returns one of:

| outcome | when | printed fields |
|---|---|---|
| `CHOSEN` | a documented preference (an existing `ExpertPreference` object) separates exactly one candidate | `zone_id`, `preference_id`, `preference_source`, the five comparison values, and `criteria_priority = <source id>` |
| `REJECTED_WITH_REASON` | per candidate: an eligibility or preference reason excludes it | `zone_id`, `reason_code`, `reason_text`, `evidence_needed` |
| `CRITERIA_CONFLICT` | two documented preferences point in opposite directions (`conflicts` non-empty from `apply_expert_preferences`) | both preference ids, both directions, and `resolution = NONE_DECLARED` |
| `UNRESOLVED` | tie, missing role, or no documented preference reaches the zone pool | `reason_code` and the `KNOWLEDGE_GAP` text |

Every outcome record must also carry **"what would change the choice"**:

```text
would_change = [
   {"kind": "new_source_priority", "gap": "KNOWLEDGE_GAP: criteria_priority"},
   {"kind": "dealing_range_defined", "gap": "GAP_LOCATION"},
   {"kind": "liquidity_pool_named", "gap": "C2.3 not coded"}
]
```

This is a required field, not an optional one: a selection that cannot say what would change
its mind is not a selection, it is a preference dressed up as evidence.

---

## 6. What engine_v1 already supplies, and what is missing (per concept)

From `docs/research/huddleston_study/engine_v1/COVERAGE_TABLE_C1.md` §A (30 concepts),
re-stated here only as far as zone selection touches them.

**Sufficient geometry today**

| concept | where |
|---|---|
| swing high / low (`V-A-00`) | `b1_candles/swing.py :: swing_at` |
| fair value gap (`V-B-00`) | `b1_candles/fvg.py :: fvg_at` — returns bounds and mid |
| liquidity sweep (`V-E-00`, `V-E-01`) | `c1_catalog/liquidity_sweep.py :: sweep_at`, `sweep_at_swing_level`, `latest_swing_level`, `latest_swing_reference` |
| displacement (`V-D-01…04`) | `c1_catalog/displacement.py :: displacement_at`; prints `reference_variant = NONE_PER_OWNER_D2` |
| order block (`V-OB-1…21`, 16 of 21) | `c1_catalog/order_block.py :: order_block_at` — takes `boundaries`, `mean_threshold_basis`, `entry_level`, `invalidation`, `prerequisites` from the caller |
| candle construction, closed-bar rule | `b1_candles/candle.py :: build_candles`, `Candle` |

**Missing geometry that zone selection needs**

| concept | status in the coverage table | consequence |
|---|---|---|
| dealing range (`C1.4`) | «لم يبدأ» | comparison 4 cannot be computed |
| premium / discount (`C1.3`) | «لم يبدأ» (includes `V-OB-17` rejected for absence of dealing range) | same |
| buy-side / sell-side liquidity (`C2.3`) | «لم يبدأ» | comparison 5 cannot be computed |
| draw on liquidity (`C1.2`) | «لم يبدأ» | target-side relation undefined |
| consequent encroachment (`C3.2`) | «لم يبدأ» | the `ce_midpoint` field exists on `FVGRegion` but no rule uses it |
| breaker / BPR / OTE / PD array (`C3.4`–`C3.7`) | «لم يبدأ» | no ranking vocabulary for zones |
| MSS / BOS / CHoCH (`C2.6`) | «مغطى جزئيًا» — received from the caller as evidence, never computed | HTF alignment cannot be self-derived |
| stop / target / RR (`C5.1`, `C5.2`, `C5.4`) | «لم يبدأ» | the plan side of a zone choice is outside this design |
| `GAP_LOCATION` | absent from `common.py` (coverage table §E-4) | the gap that would have labelled "where in the range" cannot be printed by `c1_catalog` |

**Also on record** (`COVERAGE_TABLE_C1.md` §E-1): the *C1 spec* still names `V-D-01` as the
displacement reference while the *V2 design* declares no reference. The code was corrected by
owner decision `D2` (`NONE_PER_OWNER_D2`), so the doc/code tension is a documentation debt, not
a behaviour defect. It is not fixed here (clause D).

---

## 7. Output schema (frozen before build)

One JSONL record per `(decision_bar, zone)`, one summary record per run:

```text
run record
  schema_version        "zone_selection_v1"
  commit                <sha of the code that produced it>
  as_of                 <timestamp>
  decision_bar          <int>
  zones_observed        <int>
  zones_eligible        <int>
  outcome               CHOSEN | REJECTED_WITH_REASON | CRITERIA_CONFLICT | UNRESOLVED
  chosen_zone_id        <id or null>
  preference_id         <id or null>
  criteria_priority     <source id or "KNOWLEDGE_GAP: criteria_priority">
  comparisons           { htf_alignment: …, sweep_displacement: …, mitigation: …,
                          dealing_range: …, target_liquidity: … }
  would_change          [ … ]                     (required)
  selection_quality     "NOT_ESTABLISHED"         (always)
  limitations           [ … ]                     (always includes LEVEL_1B offset notes)
```

`selection_quality` is a constant in `V1`. Nothing in this design may set it to anything else.

---

## 8. Test plan (fixtures only, expectations frozen first)

Per Art. 4 the order is: spec → `EXPECTED_ZONE_SELECTION.json` → code.

| test | what it asserts |
|---|---|
| `Z1` no-mutation | after a selection run, every source `FVGRegion` / `OBLikeCandidate` object is field-for-field identical to before (deep copy compare) |
| `Z2` causal | the view built at `t` is unchanged when candles after `t` are appended, mutated, or truncated (`D3`/Art. 10 battery) |
| `Z3` tie | two zones with equal `knowable_bar` ⇒ `UNRESOLVED`, never ordered by list position |
| `Z4` role missing | zone without a role ⇒ `UNRESOLVED` before any preference is consulted |
| `Z5` no-priority | no documented preference ⇒ `CRITERIA_CONFLICT`/`UNRESOLVED` with `KNOWLEDGE_GAP: criteria_priority`, **never** a `CHOSEN` |
| `Z6` missing comparison | with no dealing-range geometry available, `comparisons.dealing_range = NOT_AVAILABLE`, printed, not omitted |
| `Z7` determinism | identical inputs ⇒ identical bytes of output |
| `Z8` no forbidden vocabulary | no `WIN`/`LOSS`/`PnL`/`accuracy`/`edge` in any output field |
| `Z9` import-only | the new module imports `csm`, `expert_selection`, `connected_readings`, `study_links`; it edits none of them (checked by `git diff --name-only` being exactly the new files) |

---

## 9. Open build risks (stated, not hidden)

| risk | status |
|---|---|
| `apply_expert_preferences` may assume point/leg id semantics (e.g. `knowable_bar` lookups) that a zone id does not satisfy | **UNVERIFIED** — needs a read-through of its internals before build; if it does, the new call site must supply a compatible id map, **not** patch the kernel |
| `ExpertPreference` objects may not exist for zones at all, making every call `UNRESOLVED` | likely; this is the expected `V1` behaviour, not a blocker |
| `FVGRegion.interactions` is a mutable list shared by reference | `Z1` exists for exactly this; if mutation is unavoidable, the view must copy |
| the OB state machine's `role` vocabulary may not map onto the zone role the kernel expects | **UNVERIFIED** — needs mapping table before build |

---

## 10. What this does NOT establish

- It does **not** implement anything. No file in `src/` is touched; the new module path is a
  proposal.
- It does **not** define "the best zone", and it explicitly refuses to. Where priority is
  missing, the output is `KNOWLEDGE_GAP: criteria_priority`.
- It does **not** claim the five comparisons are the right five, or that they are complete.
  They are the five the owner named, mapped onto what the tree can and cannot compute.
- It does **not** produce a score, weight, confidence, probability or ranking.
- It does **not** validate `FVGRegion` or `OBLikeCandidate` semantics; both are taken as found.
- It does **not** establish that `apply_expert_preferences` is safe to call with non-point ids
  — that is flagged **UNVERIFIED** in §9 and must be settled by reading, not by assuming.
- It does **not** change `selection_quality`; every record must carry
  `NOT_ESTABLISHED`.
- It does **not** touch points/legs selection, `analysis_lifecycle`, or monitoring.
