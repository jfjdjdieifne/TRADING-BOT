# MUF V1 S1 — READINESS CORRECTION RC1
## TWO BLOCKERS ONLY — DESIGN ONLY

- References: `MUF V1 S1 FINAL IMPLEMENTATION DESIGN`
  (`deliverables/53_…`) + `S1 FINAL DESIGN HARDENING H1` (`deliverables/54_…`).
- Scope: **exactly two blockers**. Everything else in H1 is **FROZEN** for
  readiness review (price semantics, adjacency, tie-set, DisplacementRun
  deferral, intrabar lower-bound proof, direction, path metrics, DescriptorSpec,
  Transition schema, Explanation schema, performance design, certification
  boundary — all unchanged).
- No code. No tests. No MANIFEST. No S2.
- **Status: `DESIGN ONLY — READINESS REVIEW`**

---

# RC1-1 — ABSENCE REQUIRES OBSERVATION-DOMAIN AUTHORITY

## RC1-1.0 Finding — does a lawful existing completeness authority exist?

**YES — and it is reused, not invented.** The repo already contains a PUBLIC
CLOSED completeness/coverage contract with exactly the required shape: the
**Stage 4C-1 declared-grid coverage contract over sealed observations**
(`research/trajectory/trajectory_stage4c.py`, CLOSED; certified in
`docs/FINAL_VALIDATION.md` "6.2A-4 Stage 4C-1 closure boundary"):

| Existing contract element | Exact content |
|---|---|
| coverage status vocabulary | `GRID_OBSERVATIONS_COMPLETE` / `GRID_OBSERVATIONS_MISSING` / `OFF_GRID_OBSERVATIONS_PRESENT` / `GRID_OBSERVATIONS_DEFECT_BOTH` / `GRID_COMPLETENESS_UNKNOWN` / `COVERAGE_UNAVAILABLE` (`UNAVAILABLE`) |
| decision rule | "completeness decided by **timestamp-SET comparison** against the declared grid (never counts alone)"; without a declared grid coverage is `GRID_COMPLETENESS_UNKNOWN` |
| claim scope | `COVERAGE/CLAIM_SCOPE = OBSERVATIONS_VS_DECLARED_GRID_WITHIN_SEALED_DATA_ONLY` |
| explicit non-claims | `COVERAGE/NO_CLAIM = NO_FEED_COMPLETENESS_NO_MARKET_COMPLETENESS_NO_CALENDAR` |
| domain closure | observations are **sealed** (immutable sealed timeline/observation truth); later corrected artifacts are new seals, never rewrites |
| supporting rule | `causal_htf.py`: "coverage completeness is unknown without a cadence contract" |

Typed result vocabulary is **exactly** the existing `TypedState` members
(`NOT_CONFIGURED`, `UNAVAILABLE`, `UNDEFINED`, `NOT_APPLICABLE`) plus the
coverage tokens above — **no new typed state is invented**. The order's
"UNKNOWN / UNAVAILABLE / NOT_CONFIGURED" maps to the existing contract as:
`GRID_COMPLETENESS_UNKNOWN` (coverage token) / `TypedState.UNAVAILABLE` /
`TypedState.NOT_CONFIGURED` respectively.

## RC1-1.1 Conceptual authority → existing contracts (no new semantics)

`ObservationDomainClosureRef` (conceptual) is realized **by composition of
existing CLOSED contracts** — it introduces no new completeness semantics:

| Conceptual field | Existing contract anchor |
|---|---|
| `source_identity` | S0 `SchemaIdentity` of the sealed observation source |
| `dataset_identity` | sealed observation-set identity (S0 record/schema identity of the sealed dataset seal) |
| `timeline_id` | S0 InformationKey timeline |
| `cadence_contract_identity` | cadence contract (declared-grid basis; published kline cadence where integrated) |
| `covered_domain` | the **DECLARED timestamp grid** span (exact keys) |
| `closure/completeness evidence` | timestamp-SET comparison result of **sealed observations vs the declared grid** (`GRID_OBSERVATIONS_COMPLETE` / per-key `GRID_OBSERVATIONS_MISSING`; `GRID_COMPLETENESS_UNKNOWN` means no authority) |
| `availability_information_key` | the InformationKey at which the sealed coverage comparison is established (S0 availability rules) |

## RC1-1.2 Corrected absence contract (emission gate)

**Invariant of meaning:** `NOT_YET_OBSERVED ≠ PROVEN_NOT_OBSERVED_WITHIN_CLOSED_DOMAIN`.
Merely not seeing key K in the accepted stream is never sufficient.

**`ExpectedGridKeyNotObservedRecord` may be emitted ONLY under case B.**

**Case A — stream prefix advanced beyond K, but no closed-domain authority.**
(No declared grid, or no sealed coverage comparison, or coverage status
`GRID_COMPLETENESS_UNKNOWN` / `COVERAGE_UNAVAILABLE`.)

- Absence claim **MUST NOT be emitted** — no factual missing record exists.
- Deterministic outcome: emission rejected with
  `SchemaViolation("S1_ABSENCE_REQUIRES_CLOSED_DOMAIN")`; the gap *determination*
  returns the existing typed states — `TypedState.UNAVAILABLE` (cannot decide)
  / `TypedState.NOT_CONFIGURED` (absence capability unconfigured in the given
  domain) / coverage status `GRID_COMPLETENESS_UNKNOWN` — never a fact.

**Case B — legally closed observation domain.**
A declared grid covers K; the sealed observation domain is coverage-compared
against that grid (timestamp-set comparison) by the availability key; the
comparison establishes `GRID_OBSERVATIONS_MISSING` at K **within sealed data
only**.

- Only then `EXPECTED_GRID_KEY_NOT_OBSERVED` **may be published**, carrying the
  composed `domain_closure_ref` (RC1-1.1) as required provenance, and its claim
  remains scoped: *K is not observed within the closed sealed domain D* — never
  "the market/exchange did not produce a bar" (H1-6 scope stands), never feed
  completeness, never market completeness.

**Critical invariant — future arrival never rewrites published absence.**
Absence facts are published only where the observation-domain contract makes a
future arrival of K **incompatible with the same closed domain**: the sealed
dataset D is immutable. A later corrected artifact containing K is a **new
dataset D2 with distinct dataset/provenance identity** (a new seal); D1's
published absence remains untouched domain-scoped history; corrections flow
through the higher-authority supersession/correction-event model — **never by
rewriting history**.

---

# RC1-2 — EPISODE IDENTITY ≠ MEMBERSHIP

`CausalEpisodeRecord.membership_refs[]` is **REMOVED**. It conflicts with the
accepted higher-authority MUF design (D1/D2):

```text
EpisodeAnchorIdentity ≠ EpisodeMembershipEvent   (membership may become known later)
```

## RC1-2.1 Corrected `CausalEpisodeRecord` — anchor/creation facts ONLY

| Field | Semantic | Identity? |
|---|---|---|
| `episode_identity` | S0 `compute_record_identity` over the identity fields below | **identity** |
| `schema_identity` | S0 schema hash (`MUF_S1_EPISODE_ANCHOR`, V1) | **identity** |
| `timeline_id` / `axis` | key binding | **identity** |
| `anchor_information_key` | creation/anchor key of the episode | **identity** |
| `anchor_rule_version` | the anchor/creation rule version that defines the episode | **identity** |
| `anchor_fact_ref` | `CausalRecordReference` to the anchoring fact | non-identity |
| `provenance` | creation provenance | non-identity |
| `availability_information_key` | earliest key at which the anchor is established | non-identity |

**No membership field exists on this record** (by schema: frozen payload, closed
field set — unknown fields fail closed).

## RC1-2.2 New schema: `EpisodeMembershipEvent` (append-only)

```text
EpisodeMembershipEvent {
    episode_id,                    // references CausalEpisodeRecord.episode_identity
    member_fact_ref,               // CausalRecordReference to the member fact
    membership_information_key,    // earliest lawful InformationKey at which
                                   // this membership is known
    provenance,
    event_identity,                // S0 compute_event_identity
    schema_identity                // MUF_S1_EPISODE_MEMBERSHIP, V1
}
```

Membership is **append-only** (S0 `EventKind`/`EventRecord` +
`AppendOnlyEventLedger` discipline). If correction/removal of membership is ever
required: the **higher-authority supersession/correction-event model** applies —
historical membership events are **never mutated**.

## RC1-2.3 Requirements (binding)

- **I-EP-S1-1:** adding a member **never** changes `episode_id`.
- **I-EP-S1-2:** a published `CausalEpisodeRecord` is **never mutated** to add a
  member (membership lives only in `EpisodeMembershipEvent`s).
- **I-EP-S1-3:** a membership event's availability is the **earliest lawful
  InformationKey at which that membership is known**.
- **I-EP-S1-4:** episode accounting makes **NO** statistical independence
  claim; `RESEARCH-DEBT-024` remains **OPEN**.
- **I-EP-S1-5:** S1 only **defines** these schemas; it does **NOT** populate
  market episodes.

---

# EXACT SCHEMA DELTAS

| Element | Delta |
|---|---|
| `ExpectedGridKeyNotObservedRecord` (H1-6) | + required `domain_closure_ref` (composed per RC1-1.1: source/dataset identity, timeline, cadence contract, covered declared grid, sealed coverage-comparison evidence, availability key); emission gated on **case B only** (RC1-1.2); per-key reason `EXPECTED_GRID_KEY_NOT_OBSERVED` now cites coverage evidence `GRID_OBSERVATIONS_MISSING` **within sealed data only** |
| H1-6 typed gap vocabulary | `GRID_OBSERVATION_MISSING` (singular, invented) **retired** → the existing Stage 4C token `GRID_OBSERVATIONS_MISSING` as evidence status + existing `TypedState` members for typed results; `GRID_COMPLETENESS_UNKNOWN` / `COVERAGE_UNAVAILABLE` govern case A |
| error/reason vocabulary | + `S1_ABSENCE_REQUIRES_CLOSED_DOMAIN` (case A rejection); no other error change |
| `CausalEpisodeRecord` (15.6/§12.1) | **membership_refs REMOVED**; fields = anchor/creation facts only (RC1-2.1); schema family `MUF_S1_EPISODE_ANCHOR` |
| `EpisodeMembershipEvent` | **NEW schema** (RC1-2.2), append-only, schema family `MUF_S1_EPISODE_MEMBERSHIP` |
| `MarketStateTransitionRecord` / `ExplanationRecord` | **UNCHANGED** (frozen) |
| attack/test & build-plan descriptions | per the two sections below |

---

# ATTACKS A1–A3 / B1–B3

| # | Attack | Violated contract | Minimal fixture | Expected rejection / state | Design gate |
|---|---|---|---|---|---|
| A1 | absence claimed from prefix stream without authority | RC1-1.2 case A | observed 10:00, 10:01, 10:03 in accepted stream; no declared-grid/ sealed coverage authority; attempt absence record for 10:02 | **reject** `SchemaViolation("S1_ABSENCE_REQUIRES_CLOSED_DOMAIN")`; determination = `UNAVAILABLE` / `NOT_CONFIGURED` / `GRID_COMPLETENESS_UNKNOWN`; **no factual missing record** | emission gate on `domain_closure_ref` presence + coverage status |
| A2 | lawful closed-domain authority covering 10:02; 10:02 absent | RC1-1.2 case B | same times, with declared grid covering 10:02 and sealed-domain coverage comparison establishing `GRID_OBSERVATIONS_MISSING` at 10:02 | factual `EXPECTED_GRID_KEY_NOT_OBSERVED` **allowed**, scoped to the sealed domain D only | schema requires `domain_closure_ref`; claim-scope lock ("within sealed data only") |
| A3 | later corrected dataset rewrites history | RC1-1.2 invariant | absence published under closed dataset D1; later corrected dataset D2 contains 10:02 | D1 history **not rewritten**; D2 has **distinct dataset/provenance identity** (new seal); correction via supersession/correction-event model only | immutability + dataset-identity distinctness test |
| B1 | membership mutation via later member | RC1-2 I-EP-S1-1/2 | create episode E; append member A; append member B later | **same `episode_id`**; two append-only `EpisodeMembershipEvent`s; `CausalEpisodeRecord` bytes unchanged | identity-anchor test + append-only ledger discipline |
| B2 | mutate `CausalEpisodeRecord.membership_refs` | RC1-2.1 | attempt to set/read `membership_refs` | field **does not exist** / schema reject (`SchemaViolation` on unknown field) | closed frozen-payload schema test |
| B3 | future member changes historical episode identity | RC1-2 I-EP-S1-1/3 | membership known after episode publication | **impossible/reject**: identity fields exclude membership; membership availability = earliest lawful key only | identity-field whitelist + availability rule (I-EP-S1-3) |

---

# BUILD-PLAN DELTA ONLY

| File | Delta |
|---|---|
| `path_schemas.py` | `ExpectedGridKeyNotObservedRecord` gains required `domain_closure_ref` + case-B-only emission gate; gap vocabulary aligned to existing Stage 4C tokens; `CausalEpisodeRecord` reduced to anchor fields (schema family `MUF_S1_EPISODE_ANCHOR`); **new** `EpisodeMembershipEvent` schema (family `MUF_S1_EPISODE_MEMBERSHIP`); + `S1_ABSENCE_REQUIRES_CLOSED_DOMAIN` rejection code |
| `price_path.py` | **no change** (gap *detection* remains a stream observation only — never an absence claim; detection state cannot bypass the RC1-1.2 gate) |
| `tests/test_muf_s1_path_schemas.py` | + attacks A1–A3 (absence authority battery), B1–B3 (episode identity ≠ membership battery) |
| `tests/test_muf_s1_price_path.py` | **no change** (frozen scope) |

Complexity, performance design, and public-API reuse are unchanged. S0 remains
untouched. Nothing outside the two blockers was modified.

---

# OPEN / NOT_CONFIGURED (delta to H1 list)

- **Absence feature (`ExpectedGridKeyNotObservedRecord`): CONFIGURABLE in S1 V1
  under case B only**, because a lawful completeness authority **exists**
  (Stage 4C-1 sealed-observations-vs-declared-grid coverage contract — reused,
  not invented). In domains lacking a declared grid / sealed coverage
  comparison, the capability is **NOT_CONFIGURED / UNAVAILABLE** (case A) and no
  absence fact is ever produced there.
- **Episode schemas: schema-only** (`I-EP-S1-5`) — population of market
  episodes stays NOT_CONFIGURED at S1.
- All other OPEN/NOT_CONFIGURED items from H1 remain exactly as stated
  (DisplacementRun deferred; RESEARCH-DEBT-024 OPEN; waves/turning points/
  hierarchy/α-β-γ-δ/policies/regime/narrative/edge/Model/Strategy/Signal/PnL
  out of scope).

---

## STATUS

**`DESIGN ONLY — READINESS REVIEW`**

Two blockers corrected: absence claims now require (and reuse) an existing
CLOSED observation-domain authority with a no-rewrite invariant, and episode
identity is separated from append-only membership. No code. **STOP.**
