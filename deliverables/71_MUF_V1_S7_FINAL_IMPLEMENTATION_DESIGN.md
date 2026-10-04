# Deliverable 71 — MUF V1 S7 Final Implementation Design: Dependence Accounting Contracts & Causal Episode Ledger

## 1. Scope & Governance Authority

- **Sub-Stage**: `MUF V1 S7 — Dependence Accounting Contracts & Causal Episode Ledger`
- **Governing Authority**:
  - `deliverables/38_MUF_V1_FINAL_DESIGN_PATCH_D1.md` (`D1-14 Causal Episode Identity I-EP-1..3`, `D1-17 Estimand Before Information Claim`)
  - `deliverables/39_MUF_V1_FINAL_DESIGN_PATCH_D2.md` (`D2-10 InformationKey Everywhere I-IKA-1`, `D2-15 FrozenRepresentationBundle dependence_contract_hashes`, `D2-22 Annex B`)
  - `deliverables/42_MUF_V1_INDEPENDENT_AUDIT_PATCH_AP1.md` (`§3.5 & §4.1 S7 Dependence Accounting Contracts; RESEARCH-DEBT-024 OPEN`)

---

## 2. Target Files

- **Implementation**: `project/trading_project/src/trading_system/market_understanding/dependence_accounting.py`
- **Test Suite**: `project/trading_project/tests/test_muf_s7_dependence_accounting.py`
- **Sealed S0..S6 non-touch**: All files in `MODULE_MUF_V1_S0..S6_ACCEPTED_SRC_TESTS.sha256` remain byte-for-byte untouched.

---

## 3. Core Contracts & Invariants in `dependence_accounting.py`

1. **`DependenceAccountingContract` (`ImmutableRecord`)**:
   - `contract_id: str`, `grouping_rule_ref: str`, `overlap_rule_ref: str`, `supersession_rule_ref: str`
   - `statistical_independence_claim: str` (must equal `"NOT_PROVEN_EPISODE_ACCOUNTING_ONLY"`, `I-EP-3`)
   - `research_debt_024_status: str` (must equal `"OPEN"`, `I-EP-3`)
   - `contract_hash: str`
2. **`EpisodeAnchorIdentityRecord` (`ImmutableRecord`, `D1-14`, `I-EP-1`)**:
   - `episode_id: str` computed strictly from anchor creation facts (`timeline_id`, `anchor_wave_process_id`, `anchor_origin_key`, `episode_creation_key`, `representation_spec_hash`, `authority_policy_hash`) — **never** from the member set (`I-EP-1`).
3. **`EpisodeMembershipEventRecord` & `CausalEpisodeLedger` (`D1-14`, `I-EP-1..2`, `D2-10`, `I-IKA-1`)**:
   - Append-only membership events (`MEMBER_ADDED`, `MEMBER_SUPERSEDED`) governed by `membership_information_key`.
   - Adding members never mutates `episode_id` (`I-EP-1`).
   - Deleting historical members raises `ImmutabilityViolation(S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN)` (`I-EP-2`).
4. **`DependenceAccountingSummaryRecord` & `build_dependence_accounting_bundle`**:
   - Groups wave and state observations into causal episodes and non-overlapping span clusters in `O(N)` time, tracks `raw_observation_count`, `active_episode_count`, and `non_overlapping_span_cluster_count`, and enforces `statistical_independence_claim == "NOT_PROVEN_EPISODE_ACCOUNTING_ONLY"` (`I-EP-3`).
