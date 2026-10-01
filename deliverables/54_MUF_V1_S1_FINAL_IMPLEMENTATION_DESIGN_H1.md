# MUF V1 S1 — FINAL DESIGN HARDENING H1
## DESIGN PATCH — SIX BLOCKERS ONLY

- Reference: `MUF V1 S1 FINAL IMPLEMENTATION DESIGN`
  (`deliverables/53_MUF_V1_S1_FINAL_IMPLEMENTATION_DESIGN.md`, status
  `DESIGN ONLY — PENDING REVIEW`).
- Scope: **exactly six blockers**. No redesign outside them. No code, no tests,
  no MANIFEST, no S2.
- This document supersedes the corresponding base sections where marked
  **SUPERSEDES**; everything else in the base design stands unchanged.
- **Status: `DESIGN ONLY — READYNESS REVIEW`**

---

# CORRECTED SECTIONS

## H1-1 — PRICE SOURCE SEMANTICS
**(SUPERSEDES base §1.2 price labelling + §15 ACTUAL/PROXY columns)**

1. Canonical price fields are **NOT** labelled ACTUAL/PROXY. Price is typed:

   ```text
   PUBLISHED_OHLC_FACT
   ```

   = a published OHLC bar fact as delivered by an integrated source under its
   **published source contract**, carrying `source_identity` (source contract
   `SchemaIdentity`), `dataset_identity` (observation domain, see H1-6),
   `timeline_id`/`axis` key binding, and the published bar record identity as
   provenance.

2. **ACTUAL/PROXY remains reserved** for contexts where an existing public
   source contract already defines those semantics — i.e. flow
   (`ACTUAL = EXECUTED_INITIATED_FLOW_FROM_BINANCE_SPOT`). ACTUAL/PROXY may
   appear only on optional flow-context fields; never on price fields; the two
   are never merged (unchanged rule).

3. **Source-general at the price-path contract level:** the S1 price-path
   contract is parameterized over "integrated published-bar source". Binance
   Spot kline is the **currently integrated source, not the ontology**. No
   source semantics are invented; a future integrated source plugs into the
   same `PUBLISHED_OHLC_FACT` typing without changing S1 meaning.

4. **No tick-path claim:** published OHLC does **NOT** reconstruct the
   tick-by-tick market path. S1 claims only facts derivable from published bar
   facts (see H1-5: no claim that intermediate prices were traded).

## H1-2 — LAWFUL OBSERVATION ADJACENCY
**(SUPERSEDES base §8 adjacency wording; refines §2/§10)**

**Accepted observation stream** (per `timeline_id`, `axis`): a sequence of
published observations with lawful InformationKeys, ingested under a strict
causal order contract:

- each accepted key must be **strictly greater** than the previous accepted key
  under S0 lawful comparison (same timeline, same axis);
- **out-of-order key** (comparable but ≤ previous) → **REJECT**
  `SchemaViolation("S1_OUT_OF_ORDER_OBSERVATION")` — **malformed input is never
  silently sorted**;
- **duplicate key** (equal key) → **REJECT**
  `SchemaViolation("S1_DUPLICATE_OBSERVATION_KEY")` — a duplicate never creates
  a primitive and never updates one (fail-closed; idempotent replay is not an
  S1 contract);
- **incomparable keys** → `IncomparableInformationKeys` (S0) — reject;
- **cross-timeline / cross-axis** → `InformationKeyViolation` — reject;
- **same-batch ambiguity** (same `InformationBatchKey` / same causal
  coordinate): acceptance follows lawful key comparison **only as stream
  order**; every chronology-dependent semantic between them stays
  `UNDEFINED(SAME_BATCH_ORDER_UNPROVEN)` (base §10 stands).

**Definition — `OBSERVATION_ADJACENT(t−1, t)` (EXACT, stream-causal):**

> `t−1` and `t` are **consecutive accepted observations of the same accepted
> stream** under the lawful key order.

Adjacency is therefore created **only by the lawful causal stream contract —
never by row order, file order, or ingestion convenience**. `OBSERVATION_ADJACENT`
asserts stream-causal consecutiveness only; it is explicitly **not** a market
chronology claim beyond S0 key order and **not** a grid-continuity claim.

**`GRID_CONTIGUOUS`** remains a **separate, independently proven** property of
the cadence/grid contract (expected keys per cadence; `close_time = open_time +
interval − 1µs` for the integrated source) — proven only when every expected
grid key is observed (see H1-6). Never inferred from adjacency.

Permutation/out-of-order adversarial fixtures are mandatory (attacks A/B/D
below).

## H1-3 — RUNNING EXTREME TIE-SET (UNORDERED SEMANTIC SET)
**(SUPERSEDES base §6 + §15.3 "key-sorted tie-set" wording)**

1. Tie origins are an **unordered semantic set**: the semantic identity of
   `RUNNING_*_ORIGINS` is **set equality** over origin InformationKeys. Nothing
   about the tie-set semantics depends on order.
2. Any storage/serialization ordering is **canonical serialization order only**
   and is **explicitly non-semantic** — it is byte canonicalization for hashing
   (the same status `canonical_sha256` gives to sorted mapping keys), **never
   market chronology**. The base phrase "key-sorted tie-set" is retired because
   it can imply chronology.
3. **Input permutation invariance:** for the same legal facts, any permutation
   of representation/ingestion order of those facts yields the **same semantic
   and hash identity** of the tie-set (the canonical byte form is derived from
   the set, not from arrival order).
4. **`deterministic_sequence` (and every key component) can never choose a
   "first/true" extreme.** No downstream API may expose a winner: the published
   surface returns the immutable set only — no `.first`, no `.winner`, no
   tie-break, no "the origin". (`TIE_ORDER_CONTRACT = NOT_PROVEN`.)

## H1-4 — DISPLACEMENT RUN: DEFERRED / OUT OF S1 V1
**(SUPERSEDES base §5 entirely; removes run entries from §15/§18/§19 surface)**

**Default decision applied: DEFERRED / OUT OF S1 V1.**

- `DisplacementRunRecord` / `DisplacementRunExtentRecord` and the whole
  segment-identity section are **REMOVED** from S1 V1 schemas, build plan, and
  certification surface.
- Reason: (a) no required dependency in accepted S1 scope cannot be
  represented by adjacent primitives/descriptors — P1–P6 and the factual
  descriptors are complete without it; (b) S1 must not introduce unnecessary
  segmentation ontology before S2+; (c) a "maximal" forming run has
  future-sensitive extent semantics (its extent is only known later),
  conflicting with S1's adjacent-fact-closed discipline.
- **Not replaced** by any other run/segment abstraction. S1 V1 has **zero**
  segmentation entities. Entity/segment identity contracts arrive with S2+
  under separate design and authorization.
- What remains identity-bearing in S1 V1: the primitive/record identities
  (§15 schemas, S0 hashing) only.

## H1-5 — INTRABAR PATH LOWER BOUND — DISCRETE PROOF (RETAINED)
**(SUPERSEDES base §4 proof statement and wording)**

The lower bound is retained, restated **without any continuity assumption**:

**Class of sequences.** Let `𝒮(O,H,L,C)` be the set of all **finite ordered
observed/executed price sequences** `(x_0 = O, x_1, …, x_n = C)`, `n ≥ 1`, that
are **consistent with the published OHLC facts**: first value `O`, last value
`C`, attained maximum exactly `H`, attained minimum exactly `L`. Additional
intermediate observations are allowed (arbitrary refinement).

**Claim (BOUND).** For every sequence in `𝒮(O,H,L,C)`:

```text
TV(x) = Σ |x_i − x_{i−1}|  ≥  (H − L) + min( |O−H| + |L−C| , |O−L| + |H−C| )
```

**Proof.** Any such sequence contains indices `i_H` (value `H`) and `i_L`
(value `L`) — both extrema must be **visited**. If `i_H < i_L`, split the sum
at those two visits: `TV ≥ |O−H| + |H−L| + |L−C|` (triangle inequality on each
sub-segment; the middle sub-segment has total variation ≥ `|H−L|`). If
`i_L < i_H`, symmetrically `TV ≥ |O−L| + |L−H| + |H−C|`. Edge cases where `O`
or `C` coincide with an extremum collapse the corresponding term to zero. In
both orders `TV` is at least the shorter of the two visitation routes, i.e. the
stated `LB`. **Tightness:** the three-leg route sequence (monotone legs through
the two extrema in the shorter order) is itself an admissible discrete sequence
and attains `LB`; hence `LB` is the greatest valid lower bound over `𝒮`.

**Explicit non-claims.** No continuity of price is assumed. **No claim is made
that any intermediate price was traded** — the bound holds for every refinement
because total variation only grows under refinement. The published OHLC does
not reveal which sequence in `𝒮` occurred.

**Consequences.**
- `INTRABAR_PATH_LENGTH_EXACT` remains `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)`.
- `INTRABAR_PATH_LENGTH_LOWER_BOUND` = `BOUND`, carried with
  `bound_basis = "DISCRETE_TV_TRIANGLE_INEQUALITY"` in the record/DescriptorSpec.
- `INTRABAR_PATH_LENGTH_UPPER_BOUND` remains `UNAVAILABLE` (unbounded
  refinement/oscillation).
- If a future source provides trade-level observed sequences, exact path
  becomes a separate source-typed metric — **not S1 V1**.

## H1-6 — GRID OBSERVATION GAP ≠ MISSING MARKET BAR
**(SUPERSEDES base §8.1/§8.3 naming + §15.5 + related error names)**

1. **Rename/redefine.** `MissingIntervalRecord` is renamed
   **`ExpectedGridKeyNotObservedRecord`**. Its claim type is exactly:

   ```text
   EXPECTED_GRID_KEY_NOT_OBSERVED   (per expected grid key)
   GRID_OBSERVATION_MISSING         (typed unavailability reason)
   ```

   and **nothing stronger**.

2. **Claim scope.** The record asserts only: *an expected grid key was not
   observed* **within a specific observation domain**
   (`source_identity` × `dataset_identity` × `timeline_id` ×
   `cadence_contract`). It must **NOT** claim — and its schema/text must never
   state — that "the market/exchange did not produce a bar". Missingness is
   **data/source observation missingness**, and it is **never directional
   market evidence**.

3. **Required provenance fields** (identity-bearing): `source_identity`,
   `dataset_identity`, `timeline_id`, `cadence_contract_identity` (interval +
   close-time rule), `expected_grid_keys` (the span); plus non-identity
   `detection_key` (the lawful InformationKey at which non-observation within
   the dataset domain is proven).

4. **Adjacency effects.** `GRID_CONTIGUOUS` = **false/unavailable** whenever an
   expected key in the span is not observed (asserting contiguity raises
   `SchemaViolation("S1_GRID_CONTIGUITY_UNPROVEN")` with the typed reason
   `GRID_OBSERVATION_MISSING`). `OBSERVATION_ADJACENT` **remains factual**
   between consecutive lawful observations across the gap (H1-2) and is
   labelled as such.

5. **Unchanged fail-closed rules:** no synthetic bar; no forward-fill; no
   interpolation; gap spans propagate only as typed
   `NOT_APPLICABLE` / `GRID_OBSERVATION_MISSING` states.

---

# IMPACTED SCHEMA DELTAS

| Schema / element | Delta |
|---|---|
| price fields everywhere (15.1–15.4) | typed `PUBLISHED_OHLC_FACT` + `source_identity`/`dataset_identity`; ACTUAL/PROXY **removed** from price; ACTUAL/PROXY only on optional flow-context fields (never required, never merged) |
| `ObservedDisplacementRecord` (15.1) | `adjacency_kind` semantics now cite the H1-2 stream-causal definition; `gap_ref` → `ExpectedGridKeyNotObservedRecord` ref or `NOT_APPLICABLE`; price typing per above; identity fields unchanged |
| `BarFactDerivativesRecord` (15.2) | `intrabar_path_length_lower_bound` gains `bound_basis = "DISCRETE_TV_TRIANGLE_INEQUALITY"` (H1-5); exact path stays `UNAVAILABLE(AMBIGUOUS_INTRABAR_CHRONOLOGY)`; upper bound stays `UNAVAILABLE`; price typing per above |
| `RunningExtremeSnapshotRecord` (15.3) | `running_high_origins` / `running_low_origins` = **unordered semantic set**; canonical serialization order documented as **non-semantic**; no winner/first API exists; hash identity permutation-invariant (H1-3) |
| `DescriptorValueRecord` (15.4) | input typing per above; no other field change |
| `MissingIntervalRecord` (15.5) | **renamed** `ExpectedGridKeyNotObservedRecord`; + identity provenance `source_identity`, `dataset_identity`, `cadence_contract_identity`, `expected_grid_keys`; `reason ∈ {EXPECTED_GRID_KEY_NOT_OBSERVED}`; typed gap unavailability = `GRID_OBSERVATION_MISSING` (H1-6) |
| `DisplacementRunRecord` / `DisplacementRunExtentRecord` (base §5) | **REMOVED — DEFERRED** (H1-4); episode/transition/explanation schemas keep membership/refs to primitive/record facts only |
| `CausalEpisodeRecord` / `MarketStateTransitionRecord` / `ExplanationRecord` (15.6/§12) | unchanged fields and states; only reference set restricted to the surviving S1 V1 records |
| error/reason vocabulary | `MISSING_GRID_BAR` **retired** → `EXPECTED_GRID_KEY_NOT_OBSERVED` (record reason) / `GRID_OBSERVATION_MISSING` (typed unavailability); + `S1_OUT_OF_ORDER_OBSERVATION`, `S1_DUPLICATE_OBSERVATION_KEY`, `S1_GRID_CONTIGUITY_UNPROVEN`; `UNSUPPORTED_SOURCE_SEMANTICS` now also fires on ACTUAL/PROXY applied to price fields |

---

# UPDATED ADVERSARIAL ATTACKS

Base matrix (§17) stands with these amendments: row 2 uses the **discrete jump
sequence** fixture (attack F); row 4 wording uses the unordered-set identity
(attack D); row 5 wording is dataset-domain (attack C); row 16 is scoped to
flow-only ACTUAL/PROXY (attack E). **New mandatory attacks:**

| # | Attack | Violated contract | Minimal fixture | Expected rejection / state | Design gate |
|---|---|---|---|---|---|
| A | shuffled input rows change lawful adjacency silently | H1-2 | legal stream keys k1<k2<k3 ingested as k1,k3,k2 | `SchemaViolation("S1_OUT_OF_ORDER_OBSERVATION")` at k3→k2 — adjacency set unchanged; **no silent sort** | strict-monotonic ingestion contract + test |
| B | duplicate InformationKey creates a primitive | H1-2 | same key ingested twice | `SchemaViolation("S1_DUPLICATE_OBSERVATION_KEY")`; no second primitive, no update | duplicate rejection test |
| C | missing expected grid key reported as "market bar absent" | H1-6 | dataset domain missing grid key 6 | record says `EXPECTED_GRID_KEY_NOT_OBSERVED` within the declared domain only; any "market bar absent" wording/field → `SchemaViolation` | schema claim-scope test + wording lock |
| D | same tie-set under different ingestion ordering has different identity | H1-3 | tie-set {k5, k9} built/serialized in both orders | same semantic identity and same canonical hash; no winner exposed | permutation-invariance test + no-winner API check |
| E | price field uses flow-style ACTUAL/PROXY | H1-1 | price field labelled `ACTUAL` or a merged provenance | `SchemaViolation("UNSUPPORTED_SOURCE_SEMANTICS")` | `PUBLISHED_OHLC_FACT` typing test (price fields carry no ACTUAL/PROXY) |
| F | intrabar lower bound tested via continuity | H1-5 | fixture computes `LB` on a **discrete jump sequence** (O,H,L,C as attained values) and on a refined sequence with extra points | both give `TV ≥ LB`; no continuity premise anywhere in the metric contract; any continuous-path claim → `SchemaViolation` | `bound_basis` field + discrete-proof unit fixture |
| G | DisplacementRun/segment sneaks back into S1 V1 | H1-4 | search/AST over proposed S1 modules for `DisplacementRun`, segment/run entity classes, or run-organizing logic | zero hits — nothing planned; any hit is a design violation | build-plan lock + AST/search gate in the future build |

---

# UPDATED BUILD PLAN (deltas only)

| File | Delta |
|---|---|
| `src/trading_system/market_understanding/price_path.py` | + strict-monotonic ingestion contract (reject duplicates/out-of-order/incomparable/cross-timeline — never sort); + `RunningExtremeOrigins` as **unordered semantic set** with non-semantic canonical serialization; + `bound_basis = "DISCRETE_TV_TRIANGLE_INEQUALITY"` on the LB metric; **explicitly contains NO run/segment implementation** (attack G) |
| `src/trading_system/market_understanding/path_schemas.py` | `ExpectedGridKeyNotObservedRecord` replaces `MissingIntervalRecord` (+ domain provenance fields); price typing `PUBLISHED_OHLC_FACT`; ACTUAL/PROXY vocabulary restricted to flow-context fields; run/segment schemas deleted (H1-4) |
| `tests/test_muf_s1_price_path.py` | + permutation/out-of-order fixtures (A), duplicate-key (B), tie-set permutation identity (D), discrete LB fixture (F) |
| `tests/test_muf_s1_path_schemas.py` | + dataset-domain gap wording (C), price-typing scan (E), AST/search no-segment gate (G) |

Complexity and public-API reuse are unchanged from base §18 (O(1) amortized per
bar; S0/CLOSED APIs only). S0 remains untouched.

---

# REMAINING OPEN / NOT_CONFIGURED (explicit)

**DEFERRED (design decision recorded):**
- `DisplacementRun` / any run or segment ontology → **out of S1 V1**, S2+ under
  separate design and authorization (H1-4). No replacement abstraction exists
  in S1 V1.

**NOT_CONFIGURED at S1 V1 (unchanged from base, restated):**
- wave semantics; turning-point detection/quality/importance; hierarchy;
  α/β/γ/δ representations; policies/qualifications; regime thresholds;
  narrative population beyond the four explanation states; statistical
  independence (RESEARCH-DEBT-024 **OPEN**); merging of ACTUAL/PROXY; any
  volume/flow requirement; final-normalized/future-normalized descriptors;
  tick-by-tick path reconstruction claims; trade-level exact intrabar path
  (future source-typed metric under separate authorization).

**OPEN:**
- base design remains `DESIGN ONLY — PENDING REVIEW`;
- this H1 hardening patch is `DESIGN ONLY — READYNESS REVIEW`.

---

## STATUS

**`DESIGN ONLY — READYNESS REVIEW`**

Six blockers corrected; schemas, errors, attacks, and build plan cross-checked
and updated without scope expansion. No code. **STOP.**
