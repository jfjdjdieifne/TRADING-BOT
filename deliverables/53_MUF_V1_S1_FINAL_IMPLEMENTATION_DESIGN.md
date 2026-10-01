# MUF V1 — S1 FINAL IMPLEMENTATION DESIGN
## PRICE PATH PRIMITIVES — DESIGN ONLY

- Task: DESIGN S1 ONLY (OWNER AUTHORIZATION). S0 is CLOSED.
- Official baseline: MANIFEST `899febb4a33c984b48176be6a972405fe6be3301faf660d54d53718216090e84`
  (196/196 OK) · project 1139/1139 · field_runner 36/36 · MUF S0 CLOSED.
- No S2 or later stage is authorized.
- **Status: `DESIGN ONLY — PENDING REVIEW`**
- Deliverable: this document only. No code, no tests, no MANIFEST, no docs closure.

---

## 0 — CORE PRINCIPLE (binding on every section)

```text
PRICE PATH FACT  ≠  TURNING POINT  ≠  WAVE  ≠  MARKET IMPORTANCE
```

S1 describes **what the observed market path did** — factually, causally, at
declared availability. S1 must NOT decide which turning point is important,
which wave is "real", which hierarchy is correct, which representation
α/β/γ/δ wins, or any predictive significance.

Standing semantics preserved verbatim: `TIE_ORDER_CONTRACT = NOT_PROVEN`;
ambiguous O/C stays ambiguous (convention witnesses are never canonical OHLC);
ZERO LOOKAHEAD; Origin ≠ Availability; kline = published bar fact; FAIL CLOSED;
PROXY ≠ ACTUAL and never merged.

---

## 1 — INPUT AUTHORITY

S1 consumes **only existing PUBLIC CLOSED market/timeline contracts**. No source
semantics are invented.

### 1.1 Required factual inputs (exact)

| Input | Contract source | Semantics |
|---|---|---|
| `open`, `high`, `low`, `close` | published bar fact (CLOSED Binance Spot kline OHLC source contract) | strict finite decimals; canonical O/C from the kline source exclusively; `open_ambiguous` / `close_ambiguous` stay ambiguous; `close_time = open_time + interval − 1µs` cadence as published |
| InformationKey / timeline identity | `research.information_time.InformationKey` | `(information_key_version, timeline_id, bar_position, event_time_utc, information_phase, deterministic_sequence)`; comparison coordinate `(bar_position, phase_rank, sequence)`; timeline identity is part of every identity |
| axis semantics | `InformationAxis` | `POSITIONAL` (bar_position only, `event_time_utc is None`) or `TIME_INDEXED` (timezone-aware UTC required) |
| source provenance | S0 `SchemaIdentity` + `compute_record_identity` | every consumed bar fact referenced by its published record identity + schema identity; no parallel hashing |

### 1.2 Volume / flow

**NOT required** to describe price path. If referenced at all it is an
**optional contextual reference** in a separate, clearly-typed field set:

- `flow_kind ∈ {ACTUAL, PROXY}` where ACTUAL means only
  `EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT` per the source's own semantics;
- ACTUAL and PROXY are stored in disjoint fields, never summed, never merged;
- no price-path primitive, descriptor, or schema record may depend on
  volume/flow. Missing volume is `TypedState.NOT_CONFIGURED`, never a failure
  of the price-path layer.

---

## 2 — DEFINITION: PRICE PATH PRIMITIVE

A **PricePathPrimitive** is a factual function of a *closed set of already
published bar facts whose availability keys are all ≤ the primitive's declared
availability key*, with:

- no swing threshold, quantile, ATR multiple, or fixed bar window;
- no future confirmation of any kind;
- no visual/semantic importance attribution;
- deterministic value (or deterministic typed UNAVAILABLE);
- `metric_semantics ∈ {EXACT, BOUND, PROXY, UNAVAILABLE}` on every metric.

### 2.1 The precise S1 primitive schema (final)

Atom: **completed bar fact** `B_t = (O_t, H_t, L_t, C_t)` at its published
availability key. Derived primitives — all adjacent-fact-closed:

| # | Primitive | Formula | Semantics | Availability | Why knowable there |
|---|---|---|---|---|---|
| P1 | `CLOSE_DISPLACEMENT(t)` | `C_t − C_{t−1}` (signed) | EXACT, **close-space** | close key of `t` (the later key) | only closes of two observed bars, both published |
| P2 | `CLOSE_PATH_STEP(t)` | `\|C_t − C_{t−1}\|` | EXACT, close-space | close key of `t` | same |
| P3 | `BAR_RANGE(t)` | `H_t − L_t` (≥ 0) | EXACT (span fact — **not** a path length) | close key of `t` | completed bar extremes |
| P4 | `OPEN_CLOSE_DISPLACEMENT(t)` | `C_t − O_t` (signed; body) | EXACT — named separately from P1 | close key of `t` | completed bar |
| P5 | `UPPER_WICK(t)` / `LOWER_WICK(t)` | `H_t − max(O_t,C_t)` / `min(O_t,C_t) − L_t` | EXACT | close key of `t` | completed bar |
| P6 | `RUNNING_HIGH_SO_FAR(T)` / `RUNNING_LOW_SO_FAR(T)` + origin tie-set | max/min over completed bars ≤ T | EXACT value; tie-set factual (§6) | T's declared snapshot key | prefix of published bars only |

Each primitive's identity is causal (§5). Any metric that would require
intrabar chronology is **not** a primitive here — see §3/§4.

---

## 3 — OHLC INTRABAR AMBIGUITY (mandatory)

OHLC does NOT reveal whether `O→H→L→C` or `O→L→H→C` (or any other order
visiting the extremes) occurred.

**KNOWN:** `H` occurred, `L` occurred, `O` occurred, `C` occurred (within the
bar's interval).
**UNKNOWN:** the relative chronology of `H` vs `L` (and of the extremes vs
`O`/`C` interior) **unless the source proves it** — the kline source does not.

Contract:

1. S1 **never** constructs a fictitious intrabar traversal. No OHLC order is
   chosen for convenience.
2. Any path quantity that depends on high-before-low order is
   `UNDEFINED(AMBIGUOUS_INTRABAR_CHRONOLOGY)` (typed state), or
   `UNAVAILABLE(metric_semantics=UNAVAILABLE, reason=AMBIGUOUS_INTRABAR_CHRONOLOGY)`.
3. Lawful **bounds** are permitted only where mathematically defensible for
   **all** consistent orders (§4).
4. Requesting the chronology itself is a deterministic error (§16).

---

## 4 — PATH LENGTH (proof-based semantics)

Question: what does "distance travelled" mean when only OHLC is known?

**Forbidden:** `|O−H| + |H−L| + |L−C|` (assumes chronology) — and every other
single traversal formula.

| Metric | Value | Semantics | Proof status |
|---|---|---|---|
| `close_to_close_path_contribution(t)` | `\|C_t − C_{t−1}\|` | **EXACT** — explicitly close-space path step, never called "the" path | definitional |
| `observed_close_path_length(T)` | `Σ_{i≤T} \|C_i − C_{i−1}\|` (close series) | **EXACT** as close-space metric; cumulative sum telescopes incrementally | definitional; label forbids intrabar interpretation |
| `bar_range(t)` | `H_t − L_t` | **EXACT** span fact (not a path) | definitional |
| `intrabar_path_length_exact(t)` | — | **UNAVAILABLE** (`AMBIGUOUS_INTRABAR_CHRONOLOGY`) | chronology unknown (§3) |
| `intrabar_path_length_lower_bound(t)` | `LB = (H−L) + min(\|O−H\| + \|L−C\|,\; \|O−L\| + \|H−C\|)` | **BOUND** (exact lower bound) | **Proof:** any continuous intrabar path from `O` to `C` must visit both `H` and `L`; by the triangle inequality its total variation is at least the shorter of the two routes `O→H→L→C`, `O→L→H→C`; both routes are achievable by monotone legs, so `LB` is attained. Holds for every consistent order. |
| `intrabar_path_length_upper_bound(t)` | — | **UNAVAILABLE** (unbounded: arbitrary oscillation inside `[L,H]` is consistent with the same OHLC) | no finite bound is defensible |

Every path metric is declared `EXACT | BOUND | PROXY | UNAVAILABLE` in its
DescriptorSpec/record. Bounds are published **as bounds** — never promoted to
exact values.

---

## 5 — SEGMENT IDENTITY

S1 primitives are **naturally closed by currently observed adjacent facts**
(§2). Optional secondary entity: the `DisplacementRunRecord` (a maximal run of
same-sign close displacements) — explicitly **NOT a wave, NOT a turning point,
NOT a swing** (the CLOSED 2.1A chain is out of S1 scope entirely).

Identity contract (causal and immutable):

| Element | Rule |
|---|---|
| **origin** | the first adjacent pair of the run (both bar keys known at the run's birth) |
| **identity-defining fields** | `schema_identity`, `origin_pair_keys` (both InformationKeys incl. timeline/axis/sequence), `direction_sign`, `run_schema_version` — **nothing else**. The final endpoint is **never** identity and never enters identity retroactively. |
| **extent (non-identity)** | published later as `DisplacementRunExtentRecord` (a **new** observation/event when the run closes) — SUPERSEDE/extent never modifies the run's identity or earlier facts |
| **availability InformationKey** | existence: availability of the second close of the origin pair; extent: availability of the closing bar's key |
| **provenance** | `CausalRecordReference` list to contributing bar-fact record identities (`validate_reference_at/type` at every use) |
| **schema/version/domain hash** | `compute_schema_identity(schema_family="MUF_S1_PRICE_PATH", schema_version="V1", domain=...)` + `compute_record_identity` — **reuse S0 identities; no parallel hashing** |

---

## 6 — RUNNING EXTREMES (RUNNING_EXTREME, never TURNING_POINT)

```text
RUNNING_EXTREME ≠ TURNING_POINT. A running extreme is a prefix fact.
```

- `RUNNING_HIGH_SO_FAR(T)` = `max(H_i | i ≤ T, i completed)`; low analogously.
- **Never** described as peak/trough/confirmed extreme/turning point. Public
  schema names use `RUNNING_*` exclusively (naming is part of the contract).
- **Ties:** when a new bar ties the running value, the **tie-set is retained**:
  `RUNNING_HIGH_ORIGINS(T)` = the set of bar keys attaining the running max,
  represented as an immutable, key-sorted set of InformationKeys **with no
  semantic order** ("first is the true high" is forbidden — row order is not
  market chronology; `TIE_ORDER_CONTRACT = NOT_PROVEN`). All tied origins are
  kept (no ambiguity-set collapsing to a single "winner").
- In TIME_INDEXED space, lawful timestamps order *observations*, but a price
  tie remains a tie: both origins stay in the set.
- Forming-bar partials (`BAR_PRE_CLOSE` phase) are a **separate** typed fact
  (`FORMING_BAR_RUNNING_HIGH` etc.), never conflated with completed-bar
  running extremes (availability per phase; attack 8/attack 12 gate this).

---

## 7 — DIRECTION (observed displacement only)

| Fact | Definition | Allowed names |
|---|---|---|
| `CLOSE_TO_CLOSE_DISPLACEMENT(t)` | `C_t − C_{t−1}` (signed, EXACT) | as named |
| `CLOSE_TO_CLOSE_DIRECTION(t)` | `UP` iff displacement > 0; `DOWN` iff < 0; `FLAT` iff == 0 | `UP/DOWN/FLAT` only |
| `OPEN_CLOSE_DISPLACEMENT(t)` | `C_t − O_t` (signed, EXACT) — **separately named**, body direction separate from close-to-close direction | as named |

Forbidden vocabulary anywhere in S1 public API/records: `trend`, `bullish`,
`bearish`, `structure`, `impulse`, `correction`. Direction describes an
observed displacement and nothing else. Equal closes → `FLAT` (factual zero),
no interpretation.

---

## 8 — GAPS / MISSING BARS (mandatory fail-closed)

If bar at grid position `t` is missing and `t+1` is observed:

1. **No synthetic bar. No forward fill. No interpolation.** The missing
   interval stays explicit as `MissingIntervalRecord` (expected grid positions,
   cadence identity, reason `MISSING_GRID_BAR`).
2. `ADJACENCY_KIND ∈ {GRID_CONTIGUOUS, OBSERVATION_ADJACENT}` is typed on every
   adjacent-pair fact.
3. The numerical `C_{t+1} − C_t` is computable but is published **only** as
   `OBSERVATION_ADJACENT` displacement; a `GRID_CONTIGUOUS` claim across the
   gap is `UNDEFINED(MISSING_GRID_BAR)` and asserting it is a deterministic
   error (§16).
4. Grid membership uses the **existing cadence/grid contracts** (published
   kline cadence; `close_time = open_time + interval − 1µs`; InformationKey
   `bar_position` in POSITIONAL space). No new grid semantics are invented.
5. Cumulative close-space path length across the gap: the `OBSERVATION_ADJACENT`
   step is included **only** in the observation-adjacent accumulator; the
   grid-contiguous accumulator records `UNDEFINED(MISSING_GRID_BAR)` for the
   gap span. Both accumulators are distinct DescriptorSpecs.

---

## 9 — TIME-INDEXED vs POSITIONAL

| | POSITIONAL | TIME_INDEXED |
|---|---|---|
| timestamps | **never invented**; `event_time_utc is None` | timezone-aware UTC required (S0 InformationKey contract already enforces) |
| bar-count duration | EXACT (factual) | EXACT (factual) |
| wall-clock duration | `UNAVAILABLE(NOT_TIME_INDEXED)` | EXACT from lawful timestamps |
| axis conversion | never silent; cross-axis duration/metric comparison → `IncomparableInformationKeys` / reject | idem |

Axis is part of identity; every record declares its axis-bound keys. Naive or
invented timestamps are rejected at key construction (S0 behavior), not
repaired.

---

## 10 — SAME INFORMATION BATCH

Using S0 `InformationBatchKey` semantics: facts co-visible in one batch have
**no proven A-before-B order**. Mechanical processing order (insertion,
iteration) is engineering only and never chronology.

- Any primitive/transition/descriptor whose definition requires A-before-B must
  first compare the two InformationKeys (S0 comparison semantics);
- same causal coordinate / same batch ⇒ order **UNPROVEN** ⇒ the dependent fact
  is `UNDEFINED(SAME_BATCH_ORDER_UNPROVEN)` (or the write is rejected with
  `InformationKeyViolation` for identity-level violations);
- distinct comparable keys ⇒ the S0 order semantics apply unchanged.

---

## 11 — RUNNING DESCRIPTOR INFRASTRUCTURE

`DescriptorSpec` (registry entry, immutable once registered):

| Field | Content |
|---|---|
| `descriptor_identity` | schema identity + descriptor name + version (S0 hashing) |
| `stage` | `RUNNING_ONLY` / `FINAL_ONLY` / `BOTH_SEPARATE_FORMULAE` — separate formulae, never one formula rescaled |
| `required_inputs` | typed list of input fact kinds (price-path primitives only at S1) |
| `availability_rule` | S0 `AvailabilityRule` (axis, required basis keys, satisfaction keys) |
| `boundary_contract` | explicit data scope: `SINCE_GENESIS` / `SINCE_ORIGIN(entity)` / declared interval — **never an undeclared fixed window** |
| `missingness` | typed states per missing input (`NOT_APPLICABLE`, `MISSING_GRID_BAR`, …) |
| `denominator_semantics` | if ratio: exact denominator definition; denominator == 0 ⇒ `UNDEFINED("ZERO_DENOMINATOR")` — **no epsilon, no inf, no coercion** |
| `incremental_state` | the sufficient streaming state (bound, §14) |
| `policy_dependencies` | none permitted for factual descriptors; anything policy-derived is `POLICY_ARTIFACT` and **NOT_CONFIGURED at S1** |

S1 factual raw descriptors (RUNNING_ONLY unless noted):

- `observed_close_path_length` (Σ|Δclose|, `SINCE_GENESIS`, EXACT close-space)
- `grid_contiguous_close_path_length` (gap-aware, §8)
- `running_high_so_far` / `running_low_so_far` + origin tie-sets (§6)
- `bar_count_observed` / `bar_count_grid` (gap accounting)
- `sum_close_displacement` (= `C_T − C_0`, telescoping, EXACT)

Forbidden at S1: final-wave descriptors; future-normalized position (e.g.
"position within the final swing"); final amplitude normalization; any
ratio without declared denominator semantics.

---

## 12 — CAUSAL EPISODE / TRANSITION / EXPLANATION SCHEMAS (schemas only)

S1 delivers **contract foundations only**. S1 does NOT populate market
narratives.

### 12.1 `CausalEpisodeRecord` (schema)

Fields: `episode_identity` (origin-bound: schema identity + origin key + rule
version — extent never in identity), `membership_refs` (record identities of
member facts), `provenance`, `schema_identity`, `availability_key`,
`extent_ref` (nullable → extent is a later record). Semantics:
**accounting/provenance only**. Explicit: episode membership makes **no**
statistical independence claim — `RESEARCH-DEBT-024` remains **OPEN** and is
cited in the schema contract.

### 12.2 `MarketStateTransitionRecord` (schema)

Fields: `transition_identity` (schema + from-key + to-key + kind), `from_state`,
`to_state` (literal factual states or descriptor values only — e.g.
`CLOSE_TO_CLOSE_DIRECTION: FLAT → UP`, `running_high_origin_set` change),
`establishing_key` (InformationKey of the observation establishing the
transition), `provenance`, `schema_identity`. **No threshold-derived "regime"**
exists in the schema — regime concepts require a policy artifact
(`POLICY_ARTIFACT`, NOT_CONFIGURED at S1).

### 12.3 `ExplanationRecord` (schema)

Fields: `explanation_identity`, `subject_ref`, `referenced_fact_refs`
(fact record identities + relation kind `REFERENCES_ONLY`), `state`, provenance,
schema identity. Allowed states — **exactly**:

```text
MONITORING | PATTERN_REQUIREMENTS_SATISFIED | CONTRADICTED | SUPERSEDED
```

Explanation records **reference facts only**; they never re-derive narrative.
**No probability, no weights, no support score fields exist** (closed schema;
payloads frozen via S0 `freeze_payload`; unsupported additions fail closed).

---

## 13 — FUTURE APPEND INVARIANCE

**Contract:** for any S1 output published at availability ≤ T, appending any
legal future market data leaves all such outputs **byte/semantic identical**.

Design property: every S1 output at T is a function of facts with availability
≤ T only (prefix-measurable). Evolution = **new** records (SUPERSEDE never
rewrites the past; published records immutable via S0 `ImmutableRecord` +
`FrozenPayloadMapping`).

Designed tests (for the future build):

- primitives: emit all primitives ≤ T, snapshot canonical hashes
  (`payload_canonical_view` + `canonical_sha256` — the only hash authority),
  append legal bars, re-compute prefix ⇒ hashes identical;
- running-extreme snapshots: same, including tie-set contents;
- descriptors: every RUNNING_ONLY descriptor value at T identical after future
  appends (boundary_contract guarantees prefix scope);
- schema-only episode/transition/explanation records: emitted records (when
  later stages populate them) byte-identical; extent/appends are new records.

---

## 14 — PERFORMANCE

- **Target: O(1) amortized per new bar** for all primitives and running facts.
  Per-bar work: constant arithmetic (P1–P5), constant comparisons + tie-set
  append (P6), constant accumulator updates (descriptors).
- **No rescanning** of complete history per bar; each aggregate maintains
  declared `incremental_state` (last close, accumulators, running extremes,
  tie-sets, gap cursor).
- **Memory (explicit):** O(1) per primitive/accumulator; tie-sets O(k) where k
  = number of currently tied running-extreme origins (worst case O(n) on an
  all-tied series — retained in full; **no truncation window invented to save
  memory**); O(#registered DescriptorSpecs).
- Total build over n bars: **O(n)**. No O(n²) anywhere; the build will carry a
  deterministic operation-count gate (P2-14 style) to keep it so.

---

## 15 — OUTPUT SCHEMAS (exact typed schemas)

All records: S0 `PublishedRecord`/`EventRecord` over `freeze_payload`; payload
domain = S0 frozen value domain; **immutable after publication** (column
"Mutates?" is always NO — evolution = new record). Identity via S0
`compute_record_identity`/`compute_schema_identity` (no parallel hashing).

### 15.1 `ObservedDisplacementRecord` (adjacent pair)

| Field | Semantic | Identity? | Origin | Availability | Missingness | ACTUAL/PROXY | Mutates? |
|---|---|---|---|---|---|---|---|
| `record_identity` | S0 hash | **identity** | computed | — | never missing | — | NO |
| `schema_identity` | S0 schema hash | **identity** | computed | — | never | — | NO |
| `timeline_id` / `axis` | key binding | **identity** | keys | — | never | — | NO |
| `origin_key` / `adjacent_key` | the two bar keys (ordered by S0 key comparison) | **identity** | bar facts | — | never | — | NO |
| `adjacency_kind` | `GRID_CONTIGUOUS`/`OBSERVATION_ADJACENT` | **identity** | cadence contract | adjacent key | never | — | NO |
| `close_displacement` | `C_t − C_{t−1}` signed | non-identity | bar closes | adjacent key (later close) | `UNDEFINED(MISSING_GRID_BAR)` if grid claim across gap | price = ACTUAL published bar fact (no PROXY field exists) | NO |
| `close_path_step` | `\|Δ\|` | non-identity | same | same | same | ACTUAL | NO |
| `direction` | `UP/DOWN/FLAT` (§7) | non-identity | same | same | same | ACTUAL | NO |
| `gap_ref` | `MissingIntervalRecord` ref or `NOT_APPLICABLE` | non-identity | grid contract | adjacent key | typed | — | NO |
| `provenance_refs` | `CausalRecordReference`s to both bar facts | non-identity | sources | adjacent key | never | — | NO |

### 15.2 `BarFactDerivativesRecord` (per completed bar)

| Field | Semantic | Identity? | Origin | Availability | Missingness | ACTUAL/PROXY | Mutates? |
|---|---|---|---|---|---|---|---|
| `record_identity`, `schema_identity`, `timeline_id`, `bar_key` | binding | **identity** | bar fact | — | never | — | NO |
| `bar_range` | `H−L` (EXACT span) | non-identity | bar | close key | `UNDEFINED(NON_FINITE_PRICE)` rejected at input (§16) | ACTUAL | NO |
| `open_close_displacement` | `C−O` signed (body) | non-identity | bar | close key | rejected at input | ACTUAL | NO |
| `upper_wick` / `lower_wick` | §2 P5 | non-identity | bar | close key | rejected at input | ACTUAL | NO |
| `intrabar_path_length_exact` | — | non-identity | — | close key | `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)` constant | — | NO |
| `intrabar_path_length_lower_bound` | `LB` (§4, BOUND) | non-identity | bar | close key | rejected at input | ACTUAL | NO |
| `metric_semantics` map | `EXACT/BOUND/...` per metric | non-identity | schema | close key | never | — | NO |
| `provenance_refs` | bar fact reference | non-identity | source | close key | never | — | NO |

### 15.3 `RunningExtremeSnapshotRecord`

| Field | Semantic | Identity? | Origin | Availability | Missingness | ACTUAL/PROXY | Mutates? |
|---|---|---|---|---|---|---|---|
| `record_identity`, `schema_identity`, `timeline_id`, `snapshot_key` | binding | **identity** | keys | — | never | — | NO |
| `running_high_so_far` / `running_low_so_far` | prefix extreme values (RUNNING_EXTREME) | non-identity | completed bars ≤ T | snapshot key | `UNDEFINED(NO_COMPLETED_BARS)` at genesis | ACTUAL | NO |
| `running_high_origins` / `running_low_origins` | immutable key-sorted tie-set (no semantic order) | non-identity | bars attaining value | snapshot key | same | ACTUAL | NO |
| `scope` | `COMPLETED_BARS_ONLY` (forming-bar partials are separate records) | **identity** | schema | — | never | — | NO |

### 15.4 `DescriptorValueRecord`

| Field | Semantic | Identity? | Origin | Availability | Missingness | ACTUAL/PROXY | Mutates? |
|---|---|---|---|---|---|---|---|
| `record_identity`, `descriptor_identity`, `at_key` | binding | **identity** | spec + key | — | never | — | NO |
| `value` / `typed_state` | EXACT/BOUND value or `UNDEFINED(reason)` | non-identity | incremental state | `at_key` | typed per spec | ACTUAL unless spec says PROXY (never merged) | NO |
| `boundary_contract_echo` | declared scope | non-identity | spec | `at_key` | never | — | NO |
| `inputs_ref` | contributing fact refs | non-identity | facts | `at_key` | never | — | NO |

### 15.5 `MissingIntervalRecord`

| Field | Semantic | Identity? | Origin | Availability | Missingness | ACTUAL/PROXY | Mutates? |
|---|---|---|---|---|---|---|---|
| `record_identity`, `schema_identity`, `timeline_id`, `grid_span` (expected positions) | binding | **identity** | cadence contract | key proving absence (first observed bar after span, or declared scan key) | never | — | NO |
| `reason` | `MISSING_GRID_BAR` | non-identity | detection | same | never | — | NO |
| `cadence_identity` | grid contract ref | **identity** | source contract | — | never | — | NO |

### 15.6 Schema-only records (§12): `CausalEpisodeRecord`,
`MarketStateTransitionRecord`, `ExplanationRecord` — fields per §12; every
record immutable; population beyond literal factual transitions is
**NOT_CONFIGURED at S1** (contract foundations only).

---

## 16 — ERROR CONTRACT (deterministic, fail-closed, no silent repair)

| Condition | Error / typed result |
|---|---|
| malformed OHLC (`H < L`, `H < max(O,C)`, `L > min(O,C)`, zero/negative prices as defined by source) | `SchemaViolation("S1_INVALID_OHLC")` — never clipped/repaired |
| non-finite price | `SchemaViolation` (strict-float precedent; typed `NON_FINITE_PRICE` documented) |
| cross-timeline combination | `InformationKeyViolation` |
| illegal / invalid InformationKey | `InformationKeyViolation` |
| intrabar chronology requested (exact path / H-vs-L order) | metric APIs return `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)`; direct chronology queries raise `SchemaViolation("AMBIGUOUS_INTRABAR_CHRONOLOGY")` |
| `GRID_CONTIGUOUS` claimed across a missing grid bar | `SchemaViolation("MISSING_GRID_BAR")` (or `UNDEFINED(MISSING_GRID_BAR)` for metric slots) |
| schema/version mismatch on any record or descriptor | `SchemaViolation("SCHEMA_VERSION_MISMATCH")` + `SchemaIdentity` mismatch evidence |
| future reference (fact references availability > its own key) | `PrematureAvailability` / `IllegalCausalReference` (S0 behavior) |
| unsupported source semantics (non-published-bar input; PROXY claimed as ACTUAL; merged provenance) | `SchemaViolation("UNSUPPORTED_SOURCE_SEMANTICS")` |
| same-batch chronology demanded | `UNDEFINED(SAME_BATCH_ORDER_UNPROVEN)` / `InformationKeyViolation` |
| zero denominator | `UNDEFINED("ZERO_DENOMINATOR")` — never epsilon/inf |
| any unsupported payload object | `SchemaViolation` (S0 freeze fail-closed) |

No malformed datum is ever silently repaired, filled, or coerced.

---

## 17 — ADVERSARIAL DESIGN TEST MATRIX

| # | Attack | Violated contract | Minimal fixture | Expected rejection / state | Design gate |
|---|---|---|---|---|---|
| 1 | high/low chronology inferred from OHLC | §3 | bar `O=10,H=12,L=8,C=11`, ask "H before L?" | `SchemaViolation("AMBIGUOUS_INTRABAR_CHRONOLOGY")` | schema has no chronology field; exact-path slot is UNAVAILABLE |
| 2 | path length assumes O→H→L→C | §4 | compute `\|O−H\|+\|H−L\|+\|L−C\|=9` vs `LB=7` for the same bar | traversal value has no API; only `LB` (BOUND) accepted | `metric_semantics` enum + bound-proof fixture |
| 3 | future bar changes old primitive | §13 | emit P1..P6 ≤ T; append bars; recompute | byte-identical (canonical hashes equal) | prefix-measurability test |
| 4 | equal-high tie resolved by row order | §6 | `H_5=H_9=running max`, permute row order | tie-set = {key5, key9} both orders; no "first" winner | tie-set representation + permutation test |
| 5 | missing bar treated grid-contiguous | §8 | grid 5,7 (6 missing) | displacement = `OBSERVATION_ADJACENT` + `MissingIntervalRecord`; `GRID_CONTIGUOUS` claim → `SchemaViolation("MISSING_GRID_BAR")` | cadence adjacency check |
| 6 | positional path gets invented timestamp | §9 | POSITIONAL run, request wall-clock duration | `UNAVAILABLE(NOT_TIME_INDEXED)` | axis-typed duration fields |
| 7 | naive timestamp in TIME_INDEXED | §9 | `event_time_utc` naive | reject at key construction (`InformationKeyViolation`/`SchemaViolation`) | S0 key validation reused |
| 8 | BAR_PRE_CLOSE sees completed bar | §11/§6 | running descriptor at BAR_PRE_CLOSE reads `close_t` final | `PrematureAvailability` / typed forming-bar scope only | AvailabilityRule per DescriptorSpec |
| 9 | cross-timeline segment | §5/§16 | displacement pair with different `timeline_id` | `InformationKeyViolation` | identity binds timeline |
| 10 | zero denominator → inf/epsilon | §11 | ratio descriptor, denominator 0 | `UNDEFINED("ZERO_DENOMINATOR")` | denominator_semantics + test |
| 11 | fixed hidden window introduced | §11 | descriptor secretly over last 20 bars | registration rejected (no `boundary_contract`) | DescriptorSpec validation |
| 12 | "running extreme" mislabeled turning point | §6/§0 | API field `peak`/`trough`/`turning_point` | design lock: forbidden vocabulary test | naming contract in schema registry |
| 13 | episode membership claims independence | §12.1 | episode record with independence field | schema closed → `SchemaViolation` on unknown field | frozen payload + closed schema |
| 14 | transition invents regime threshold | §12.2 | `low_vol → high_vol` from a threshold | `SchemaViolation("POLICY_ARTIFACT_REQUIRED")` / NOT_CONFIGURED | transition states whitelist (literal facts only) |
| 15 | explanation emits probability/score | §12.3 | `support=0.8` on ExplanationRecord | `SchemaViolation` (field does not exist) | closed schema test |
| 16 | ACTUAL/PROXY merged | §1.2 | one provenance claiming both | `SchemaViolation("UNSUPPORTED_SOURCE_SEMANTICS")` | disjoint typed fields + test |
| 17 | O(n²) history scan | §14 | op-count n=500 vs 1000 vs 2000 | linear ratios (2.0/4.0 gates) | deterministic operation-count gate |
| 18 | mutable published S1 record | §15 | mutate content / `dict.__setitem__` on payload | `ImmutabilityViolation` / TypeError | S0 `FrozenPayloadMapping` reused + tests |
| 19 | same-batch order creates chronology | §10 | A,B same `InformationBatchKey`; A-before-B fact | `UNDEFINED(SAME_BATCH_ORDER_UNPROVEN)` | key comparison before ordered computation |
| 20 | future-normalized descriptor in RUNNING | §11 | "position in final swing", `stage=RUNNING_ONLY` | registration rejected | DescriptorSpec stage/input rule (RUNNING inputs must be available at T) |

---

## 18 — BUILD PLAN (proposal only — NOT implemented)

Smallest split; **S0 is not modified**.

### 18.1 Proposed new files

| File | Content | Complexity |
|---|---|---|
| `src/trading_system/market_understanding/price_path.py` | primitives P1–P6, adjacency/gap typing, direction, running extremes + tie-sets, DescriptorSpec registry, factual running descriptors, error codes | O(1) amortized/bar; O(n) total; memory per §14 |
| `src/trading_system/market_understanding/path_schemas.py` | output record schemas (§15), schema-only episode/transition/explanation contracts (§12), schema identities | O(1) per publication |
| `tests/test_muf_s1_price_path.py` | primitives, adjacency/gaps, axis, batch, running extremes, invariance (§13), complexity gate (§14) | test-time only |
| `tests/test_muf_s1_path_schemas.py` | schemas, error contract (§16), adversarial matrix 1–20 (§17) | test-time only |

### 18.2 Public CLOSED/S0 APIs reused (no re-implementation)

`InformationKey`, `InformationAxis`, `InformationBatchKey`, `InformationPhase`,
key comparison / `compare_information_keys`, `ObservationBatch*`;
`SchemaIdentity`, `compute_schema_identity`, `compute_record_identity`,
`compute_event_identity`, `IdentityBundle`; `freeze_payload`,
`FrozenPayloadMapping`, `payload_canonical_view`, `canonical_sha256` (only hash
authority); `PublishedRecord`, `EventRecord`, `EventKind`,
`AppendOnlyEventLedger`; `AvailabilityRule`, `require_visible_at`,
`determine_fact_information_key`; S0 error types + `TypedState`; published bar
fact contracts (kline OHLC source, cadence); `validate_reference_at/type`.
NOT reused by S1 semantics: the CLOSED 2.1A swing chain (turning points are out
of scope), no new hashing, no new timeline types.

### 18.3 Proposed tests (list only)

- primitives: value/semantics/availability per P1–P6; EXACT/BOUND labels;
- gaps: §8 fixtures both accumulators + MissingIntervalRecord;
- axis: §9 durations, no invented timestamps;
- batch: §10 same-batch unproven-order states;
- running extremes: tie-set permutation, forming-bar separation;
- future-append invariance (§13) over every output kind;
- operation-count linear gate (§17-17);
- error contract (§16) one test per row;
- adversarial matrix §17: one test per attack (20).

### 18.4 NOT_CONFIGURED at S1 (explicit)

wave semantics; turning-point detection/quality; hierarchy; α/β/γ/δ
representations; policies/qualifications; regime thresholds; narrative
population; statistical independence (RESEARCH-DEBT-024 OPEN); PROXY/ACTUAL
merging; volume/flow requirements; final-normalized descriptors; anything S2+.

---

## 19 — CERTIFICATION BOUNDARY

S1, even if built and closed, proves only **factual causal price-path
representation under its contract**.

It does NOT prove:

- turning-point importance
- wave correctness
- hierarchy
- predictive support
- edge
- profitability
- Model
- Strategy
- Signal
- PnL

---

## STATUS

**`DESIGN ONLY — PENDING REVIEW`**

No code. No tests. No MANIFEST. No docs closure. No S2. **STOP.**
