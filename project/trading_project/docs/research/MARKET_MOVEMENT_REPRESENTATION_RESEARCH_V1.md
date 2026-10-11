# Market Movement Representation Research V1

## Purpose and limits

This is a deterministic, offline comparison adapter over supplied OHLC. It composes existing repository contracts; it does **not** add a swing detector, wave definition, generic scorer, selector, signal, recommendation, or execution path. It never downloads, sorts, fills, resamples, or regenerates market data.

The adapter preserves representation/policy identity, timeline scope, intrinsic scale and identity-rule references, source timestamps, turning-point origin versus confirmation/availability, ambiguity, and missingness. A Stage4B1 output is labelled a witness view; S5 records are called authoritative only under the exact supplied S5 policy/dataset contracts. Neither label authenticates owner authorization or source origin.

No outcome authority or task-specific empirical labels are supplied. The report therefore returns `SUITABILITY_NOT_ESTABLISHED`, does not choose a universal winner, and leaves task relevance and outcome improvement unassessed.

## Repository location and public entry points

- Runner: `src/trading_system/research/trajectory/market_movement_representation_research.py`
- Focused tests: `tests/test_market_movement_representation_research.py`
- Python entry point: `run_market_movement_representation_research(...)`
- CLI entry point: `python -m trading_system.research.trajectory.market_movement_representation_research`
- Replay prefix check: `verify_replay_prefix_invariance(...)`

The runner uses the existing `CausalMarketContextCore` builder/replay interface, `SwingPolicyConfig`, the existing Stage4A/Stage4B1/Stage4B2/Stage4C producers, `TimeIndexedTimelineAdapter`, S2 `adapt_detector_witness_stream` / `query_witness_surface_as_of` / `verify_prefix_witness_invariance`, and S5 `CandidateWaveRepresentationSpec`, governance artifacts, and `construct_candidate_wave_representation`. It does not emulate those producers.

## Offline setup and CLI

From the repository root, use a local virtual environment and the existing project dependencies:

```bash
python -m venv project/trading_project/.venv
project/trading_project/.venv/bin/python -m pip install -e 'project/trading_project[dev]' 'pandas>=2.0,<3'
project/trading_project/.venv/bin/python -m trading_system.research.trajectory.market_movement_representation_research --help
```

The `pandas<3` constraint is deliberate for the current repository baseline: under Pandas 3.0.6, existing Stage4C/HTF tests produced empty buckets without an exception. The runner itself passed its focused tests there, but that would not establish complete H1 coverage; use the tested Pandas 2.3.3 line unless/until the existing producer compatibility is independently corrected and audited. No closed producer was changed for this integration.

Supply an existing local CSV with a timezone-aware timestamp column (default `close_time_utc`) and numeric `open`, `high`, `low`, `close`; `volume` is optional. The CLI uses the timestamps as given, parses them to UTC, and does not sort or repair them. The timestamp is an observation-time label; confirm that its open/close semantics match the source contract. The declared source period is checked against one-minute bar open times in the existing core. Missing bars remain missing; no gap is filled. No repository fixture is treated as market evidence.

Example shape (replace every value with owner-provided metadata):

```bash
project/trading_project/.venv/bin/python -m trading_system.research.trajectory.market_movement_representation_research \
  --csv /path/to/owner-local-bars.csv \
  --symbol OWNER_SYMBOL \
  --period-start-utc OWNER_START_UTC \
  --period-end-utc OWNER_END_UTC \
  --output-dir /path/outside/checkout/movement-run
```

The output directory must be new/empty and outside the Git checkout. Without `--swing-policy-json` and `--s5-plan-json`, swing-dependent representations are explicitly blocked; shared OHLC-only producers still run. `--measure-python-allocations` opt-in enables `tracemalloc`, adds overhead, and does not measure all native NumPy/Pandas allocations. Process peak RSS is reported when the host exposes a supported unit convention; it is a process high-water mark, not an isolated per-run delta.

### Owner policy declarations

`--swing-policy-json` accepts schema version `MOVEMENT_SWING_POLICY_DECLARATIONS_V1` with a `policies` array. Each declaration must provide exactly:

- `policy_id`
- `quantile`
- `prior_continuation_reversals` (explicit JSON array)
- `prior_confirmed_reversals` (explicit JSON array)
- `owner_authorization_ref` (nonempty reference)

No quantile, history, or authorization reference is supplied by this runner. An empty history is valid only if that is the owner's explicit policy; it is never substituted by the runner. The authorization reference is retained but not authenticated. Invalid or incomplete candidates are reported as blocked and are not silently dropped from coverage accounting.

### Optional S5 plans

`--s5-plan-json` requires `MOVEMENT_S5_AUTHORIZED_PLAN_SET_V1`, a `dataset` object, and `representations` array. The dataset declaration includes dataset ID, dataset role, role-assignment position, permitted/prohibited operations, and a nonempty authorization reference; optional `content_hash`, if provided, must match the exact local input-file SHA-256. Each representation points to a policy ID declared in the swing-policy file and supplies the existing S5 family, representation ID, intrinsic-scale key, identity-rule reference, and a complete policy-artifact declaration. The current CLI builder expects policy-artifact fields `policy_id`, `effective_from_position`, `calibration_provenance_kind`, `reproduction_recipe_hash`, `recomputed_recipe_hash`, and a nonempty `owner_authorization_ref`; development-fit provenance additionally requires the existing fit dataset/objective/experiment/role-hash fields. `authority_kind` is an optional existing contract value. The exact accepted family names, enums, and validations are enforced by the repository's `CandidateWaveRepresentationSpec`, `PolicyArtifact`, and `DatasetRoleArtifact` constructors.

S5 runs are development-only in this adapter. The dataset content hash must bind the exact supplied source bytes (CLI) or canonical normalized frame (Python API); a mismatch is blocked before that S5 plan's policy can be reused to build Stage4B1. A final-evaluation dataset role, a missing identity rule, a timeline/dataset mismatch, or a policy-witness mismatch is blocked; the runner does not repair it or promote a substitute. `identity_rule_ref` is preserved as a reference and is not interpreted as a wave definition. Consult the constructors in `market_understanding/wave_representation.py` and `market_understanding/policy_governance.py`; no example policy values or wave anchors are provided here.

### Python API

The public entry point takes a timezone-aware, increasing OHLC `DataFrame`, a repository `SourceArtifactIdentity`, and an explicit stable `timeline_id`. `swing_policies` must contain existing `DeclaredSwingPolicy` wrappers over existing `SwingPolicyConfig` values; `s5_plans` must contain exact `S5RepresentationPlan` objects with existing contracts. For an S5 plan, set `source_file_sha256` to the exact input-file hash or bind `DatasetIdentityArtifact.content_hash` to the exact core canonical-frame hash `canonical_sha256(domain="CORE_CALLER_FRAME_HASH_V1", payload=frame_with_UTC_nanosecond_index)` when there is no file hash. No policy default is created. `output_dir` is optional for API use; when omitted the returned `MovementResearchRun` retains available records, the exact S2 witness bundles used by each S5 representation, and S5 bundles in memory. Supplying an output directory streams the core output and final report artifacts to disk.

## What is compared

1. **OHLC / S1 / Stage4A / Stage4C:** existing core views and coverage are enumerated, including OHLCV-derived proxy domains. Proxy outputs are not represented as actual aggressor flow.
2. **FVG:** existing shared, structure-independent Stage4B2 FVG candidates and lifecycle are counted once, not copied per swing policy.
3. **Stage4B1:** each explicitly declared empirical swing configuration builds a separately identified producer surface. Pairwise comparisons separate exact producer turning-point geometry, operational/structure fields, confirmation/availability fields, and policy-evidence fields. Field disagreement is not treated as task relevance.
4. **Liquidity, order block, dealing range:** traced through the actual Stage4B1-dependent Stage4B2 surfaces. They are unavailable/blocked without an authorized swing configuration; no candidates are inferred from OHLC by this adapter.
5. **S2 witnesses:** public witness records are as-of queryable. Historical availability is the confirmation key, never the origin position. S2 dataset identity does not incorporate future rows of the current replay interval.
6. **S5:** only explicitly supplied and contract-valid representation plans are passed to the existing constructor. Family/scale/scope/rule references and turning-point origin/availability are retained. Pairwise geometric, operational, and availability differences are descriptive only.
7. **Actual executed flow:** unavailable unless an existing validated source is supplied through the underlying public core API; the CLI accepts OHLC only.

Downstream reference rows point to IDs emitted by the existing core (`BOUNDARY-*`, `DIFF-*`, entity, event, and relationship streams). They are not fabricated IDs. `candidate_universe_pruned` is false; if a resource ceiling prevents a complete run, coverage is marked incomplete and candidates are not silently removed to fit the budget.

## Outputs

The output directory contains:

- `movement_representation_report.json` — coverage, policy status, causal turning points, disagreements, downstream references, suitability axes, limits, and measurements.
- `movement_research_manifest.json` — SHA-256 and byte length for emitted artifacts (the manifest excludes itself).
- `causal_turning_point_records.jsonl` — actual S2 swing-event witness records for CMC and S5 consumers, Stage4B1 witness views, and valid S5 authoritative-under-contract turning points. Stage4B1/S5 witness references resolve to the emitted S2 record identities.
- `s5_representation_records.jsonl` — records actually emitted by the existing S5 constructor.
- `disagreement_affected_references.jsonl` — references to core disagreement boundary and producer records.
- `causal_market_context_core/` — the existing core replay streams and summary.

Manifest hashes authenticate these output bytes only; they do not authenticate the original source, policy, or owner authorization. The deterministic report fingerprint excludes runtime/measurement fields and output-path fields. Core prefix-chain hashes and record identities remain part of replay audit data.

## Suitability boundary and limitations

The report has separate statuses for producer-contract validity, causal/as-of timing, observed producer-output differences, and outcome improvement. Even when producer contracts and causal timing pass, `SUITABILITY_NOT_ESTABLISHED` remains the overall state until there is an owner-approved, task-specific objective and valid outcome authority. It does not rank policies by swing count, geometric proximity, complexity, scale, or generic wave score.

OHLC does not prove intrabar order, a tick path, hidden liquidity, intent, fills, or actual aggressor activity. Source timestamps, hashes, and schema validation do not authenticate provenance. Owner authorization strings are references, not verified signatures. Structural/liquidity/OB coverage is policy-dependent. Relationship search may be partial under explicit query or relationship limits, even when producer candidate rows were preserved. A reported process RSS high-water mark can include earlier process use. `tracemalloc` excludes some native allocations.

## Verification

Focused software-contract tests are in `tests/test_market_movement_representation_research.py`. They use synthetic repository fixtures only and cover: missing swing policy; replay and S2 prefix/as-of invariance; origin versus confirmation availability; competing policy views and disagreement categories; actual downstream producer IDs; S5 policy mismatch and valid scoped S5 construction; candidate preservation under relationship-budget exhaustion; resource-exhaustion visibility; and deterministic replay fingerprints. These tests establish adapter/software behavior, not market validity, prediction, profitability, or the suitability of any owner policy.
