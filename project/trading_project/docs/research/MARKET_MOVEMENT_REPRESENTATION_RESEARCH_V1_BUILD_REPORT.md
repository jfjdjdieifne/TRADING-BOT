# Market Movement Representation Research V1 — Build Report

**Status:** BUILD ONLY complete for offline software integration. This is not a market study or a suitability conclusion.

## A. Exact Git commit

Base `HEAD`: `8ddfb50ef041d178bfc42616d75791a007c48113` (`Document contextual hypothesis resolution build`) on `arena/01a10a21-trading-bot`. The implementation is a working-tree change atop this commit; no implementation commit or push has been made.

## B. Files changed by this task

- `src/trading_system/research/trajectory/market_movement_representation_research.py` — offline runner, comparisons, report, output manifest, CLI, and resource/memory reporting.
- `tests/test_market_movement_representation_research.py` — focused synthetic software-contract tests.
- `docs/research/MARKET_MOVEMENT_REPRESENTATION_RESEARCH_V1.md` — later-use offline/API guide.
- `docs/research/MARKET_MOVEMENT_REPRESENTATION_RESEARCH_V1_BUILD_REPORT.md` — this A–M build record.

No existing closed module was edited. No market data was downloaded or added.

## C. Existing APIs reused

The integration composes existing repository interfaces rather than adding substitute detectors or producers:

- `build_causal_market_context_core`, `replay_causal_market_context`, `ReplayLimits`, `CoreBundle`, and existing CMC reports/streams.
- Existing S1 price path, Stage4A, Stage4B1, Stage4B2, and Stage4C producers reached through CMC.
- `SwingPolicyConfig` with explicit existing `EmpiricalConfirmationPolicy` inputs.
- `TimeIndexedTimelineAdapter`, `InformationKey`, and the completed-row availability phase.
- S2 `adapt_detector_witness_stream`, `query_witness_surface_as_of`, `verify_prefix_witness_invariance`, and `DetectorPolicyWitnessSpec`.
- S5 `CandidateWaveRepresentationSpec`, `CandidateWaveRepresentationBundle`, `construct_candidate_wave_representation`, `DatasetIdentityArtifact`, `DatasetRoleArtifact`, `PolicyArtifact`, and policy reproduction/scope checks.
- Existing `SourceArtifactIdentity`, `SchemaIdentity`, and published OHLC source schema contract.

Stage4B1 and S2-derived swing rows are explicitly witness views; S5 records are promoted only under the supplied existing contract. References are retained as references and are not asserted to be authenticated.

## D. Available and blocked families

With no owner policy file, the CLI can run shared OHLC views: S1, Stage4A, raw Stage4C/H1, and the structure-independent Stage4B2 FVG producer. S2 can emit evidence-only witness surfaces without inventing confirmed swings. If volume is present, existing OHLCV order-flow/absorption proxies are labelled as proxies, not actual aggressor flow.

Stage4B1 and its dependent Stage4B2 liquidity, order-block, and dealing-range views require explicit authorized swing policy declarations. The current core adapter accepts the existing empirical swing-policy contract; it does not generate thresholds or prior histories. S5 families are individually reported as blocked unless an explicit valid `S5RepresentationPlan`, policy artifact, dataset identity/role, matching witness identity, scope, and configured identity-rule reference are supplied. Actual executed flow is unavailable through the OHLC-only CLI.

No S5 family or swing policy is declared universally available based solely on software support; policy eligibility is caller supplied and contract checked.

## E. Real producer dependency chains

- `CausalAdaptiveSwingDetector → ConfirmedSwingSequenceEngine → CausalStructuralBreakEngine → Stage4B1StructureSurface`.
- `Stage4B1StructureSurface → Stage4B2LiquiditySurface / Stage4B2OrderBlockSurface / Stage4B2DealingRangeSurface`.
- Shared OHLC bars feed `Stage4B2FVGSurface` and lifecycle independently of swing-policy count.
- S2 witness surfaces are constructed through `adapt_detector_witness_stream`; S5 uses those actual witness outputs and calls `construct_candidate_wave_representation`.

Downstream affected-reference JSONL rows contain core boundary/disagreement/entity/event/relationship references emitted by CMC. No downstream object or producer ID is fabricated by the adapter.

## F. Disagreement and coverage outputs

For policy-identifiable Stage4B1 views and valid S5 plans, pairwise comparisons separate:

1. exact producer turning-point/endpoint geometry;
2. operational/structure fields and explicit S5 family/scale/rule metadata;
3. confirmation/availability-key differences; and
4. task-relevant disagreement, which remains unassessed without task/outcome authority.

Reports include policy identities and references, source/timeline scope, per-domain/per-representation candidate counts, domain coverage states, actual S2 witness records with resolvable CMC/S5 consumer references, causal turning-point views, downstream CMC references, S5 representation records, resource ceilings, and incomplete-coverage markers. No proxy task score is calculated. The manifest authenticates emitted output bytes only.

## G. Task-specific suitability boundary and limits

The report keeps separate states for producer-contract validity, causal/as-of timing, observed producer-output differences, and outcome improvement. A producer can be contract-valid and causal without being useful for a task. Overall status is always `SUITABILITY_NOT_ESTABLISHED` unless a future authorized task/outcome authority is added; this runner currently provides no such authority and never selects a winner.

OHLC alone does not establish intrabar ordering, tick path, hidden liquidity, intent, execution/fills, or actual aggressor flow. Hashes and schema checks are not proof of original source provenance; authorization strings are unauthenticated references. Resource limits can make a run incomplete. Relationship ceilings may leave relationships partial while preserving eligible producer candidates.

## H. Offline use

Setup, CLI invocation, input-column/timestamp requirements, explicit policy-file requirements, S5-plan contracts, output files, and Python API use are documented in `MARKET_MOVEMENT_REPRESENTATION_RESEARCH_V1.md`. The CLI only reads owner-local data; it does not download or transform it. Use an output directory outside the checkout. The default run without policy files is intentionally useful for enumerating shared OHLC views and explicitly blocked families.

## I. Tests, environment, and failures

Focused test file: `tests/test_market_movement_representation_research.py`. Synthetic fixtures only; no market evidence. The cases cover missing swing policy; CMC/S2 and S5 prefix/as-of invariance; turning-point origin versus confirmation availability; competing policy views and disagreement categories; actual downstream producer IDs; S5 policy and dataset-hash mismatch; valid S5 scope/contract behavior; S5-to-S2 witness-reference resolution in output files; candidate preservation under relationship-budget exhaustion; resource-exhaustion visibility; optional allocation measurement; non-mutating output-directory rejection; and deterministic replay fingerprints.

The focused suite passed all 14 tests after correcting a future-dependent S2 witness dataset identity, switching the downstream fixture to one that produces order-block candidates, forwarding `s5_plans` in the helper, adding explicit memory-measurement/output-directory checks, enforcing exact S5 dataset-content binding, and verifying S2 witness-reference resolution plus S5 as-of/prefix invariance. The relevant CMC/S1/S2/S3/S5/swing/Stage4A–C suites passed. The full project suite passed **1,626 tests** on the final code in 298.56 seconds with three pre-existing warnings (two NumPy percentile overflow/invalid-value warnings and one Pandas incompatible-dtype FutureWarning). CLI smoke runs completed on six synthetic bars with no policies (expected shared views, explicit blocked swing/S5 domains, 18 manifest entries) and on a separate ten-bar synthetic S5 contract fixture (one explicitly declared `ALPHA_POLICY_SCALE` plan ran and emitted four S5 turning points; other unrequested families stayed blocked). Both returned `SUITABILITY_NOT_ESTABLISHED`; these are parser/producer-contract checks, not owner authorization or market evidence. `py_compile` and CLI `--help` also succeeded.

Environment: local project virtualenv, Python 3.11, NumPy 2.4.6, Pandas 2.3.3, pytest 9.1.1. PEP 668 rejected a system-wide pip installation; editable install in the project virtualenv succeeded. An initial environment resolution selected Pandas 3.0.6: this runner's focused tests passed there, but existing Stage4C repository tests failed (empty HTF fixtures / unavailable buckets) without any Stage4C source changes. Those closed-module failures disappeared under Pandas 2.3.3, where the full suite passed. The virtualenv is task-generated and is not a deliverable.

## J. Established versus unproven

**Established by code/tests:** the adapter uses actual repository interfaces; missing authorization/policy is visible; two policies remain separately identified; producer disagreements are classified without scoring; the tested as-of/prefix views remain invariant; origin is distinct from confirmation availability; emitted downstream references originate in CMC; resource/relationship limitations are visible; output fingerprints/replay are reproducible within the tested fixtures.

**Not established:** source-origin authenticity, legitimacy of any owner policy, market meaning of a swing/FVG/order block/wave, task relevance, predictive value, risk-adjusted outcome improvement, profitability, transaction-cost effects, or suitability of any representation. No owner OHLC or empirical outcome data was used.

## K. Independent audit needs

Before empirical use, audit: input source lineage and timestamp/open-close semantics; exact policy values and authorization provenance; S5 policy/dataset/reproduction artifacts and role assignments; completeness and meaning of the target task/outcome labels; train/calibration/selection/untouched evaluation separation; the selected horizon and any task-specific exclusions; prefix/as-of invariance on owner data; CMC reference-stream joins and resource completeness; and all downstream consumer changes. If the task is execution or profitability, actual fills, fees, slippage, and applicable execution records would also require an authoritative source. No such audit has been performed here.

## L. Exact next empirical prerequisite

The next required input is **not another representation or a chosen score**. It is an owner-approved empirical-evaluation package that binds (1) the exact task/estimand and task-relevant outcome definition, (2) its authoritative labels/outcome source and observation/availability timing, and (3) a lineage-verified, non-overlapping development/calibration/selection and untouched evaluation dataset split with an explicit evaluation horizon and admissible-use policy. The owner must then supply the actual local OHLC and policy artifacts authorized for that task. Until this package exists, outcome improvement and suitability cannot be evaluated.

## M. Candidate preservation, scope, and handoff state

No eligible policy or candidate is silently dropped to meet a budget. If input/build/replay ceilings are reached, the report marks `BLOCKED_RESOURCE_EXHAUSTION` / incomplete coverage, records which candidates were not run, and does not claim completeness. Relationship-search ceilings are separately surfaced. No universal winner, recommendation, signal, trade, or execution path was added. Work remains on `arena/01a10a21-trading-bot`; no commit or push was made.
