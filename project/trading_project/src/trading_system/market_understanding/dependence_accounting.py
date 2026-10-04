"""MUF V1 S7: Dependence Accounting Contracts & Causal Episode Ledger.

Implements the causal episode anchor identity, append-only membership ledger,
and span-overlap accounting contracts (D1-14, D1-17, D2-10, D2-15, D2-22, AP-1 §3.5):
- ``DependenceAccountingContract`` (I-EP-3: RESEARCH-DEBT-024 OPEN, no statistical
  independence claim)
- ``EpisodeAnchorIdentityRecord`` (I-EP-1: episode_id anchored on creation facts
  only, never the member set)
- ``EpisodeMembershipEventRecord`` & ``CausalEpisodeLedger`` (I-EP-1..2, D2-10,
  I-IKA-1: append-only membership/supersession; historical member deletion forbidden)
- ``DependenceAccountingBundle``, ``build_dependence_accounting_bundle``, and
  ``query_dependence_accounting_as_of`` (O(N) construction)
"""
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from trading_system.market_understanding.availability import require_visible_at
from trading_system.market_understanding.contracts import (
    IllegalCausalReference,
    ImmutabilityViolation,
    IncomparableInformationKeys,
    InformationKeyViolation,
    PrematureAvailability,
    SchemaIdentity,
    SchemaViolation,
    TypedState,
)
from trading_system.market_understanding.identity import (
    ArtifactIdentitySchema,
    canonical_artifact_identity,
)
from trading_system.market_understanding.policy_governance import (
    DATASET_ROLE_DEVELOPMENT_FIT,
    DATASET_ROLE_DEVELOPMENT_SELECTION,
    SelectionBlockedError,
)
from trading_system.market_understanding.records import (
    ImmutableRecord,
    PublishedRecord,
)
from trading_system.market_understanding.state_graph import (
    GenericFactualStateGraphBundle,
)
from trading_system.research.information_time import (
    InformationKey,
    InformationKeyError,
    InformationPhase,
)


S7_SCHEMA_IDENTITY = SchemaIdentity("MUF_S7_DEPENDENCE_ACCOUNTING", "V1")

# Standing epistemic constraints (D1-14, I-EP-3, AP-1 §3.5)
STATISTICAL_INDEPENDENCE_STANDING_CLAIM = "NOT_PROVEN_EPISODE_ACCOUNTING_ONLY"
RESEARCH_DEBT_024_STANDING_STATUS = "OPEN"

# Membership event types (D1-14, I-EP-1..2)
MEMBERSHIP_EVENT_ADDED = "MEMBER_ADDED"
MEMBERSHIP_EVENT_SUPERSEDED = "MEMBER_SUPERSEDED"
LEGAL_MEMBERSHIP_EVENT_TYPES = frozenset(
    {
        MEMBERSHIP_EVENT_ADDED,
        MEMBERSHIP_EVENT_SUPERSEDED,
    }
)

# Record types
S7_EPISODE_ANCHOR_RECORD_TYPE = "MUF_S7_EPISODE_ANCHOR"
S7_EPISODE_MEMBERSHIP_EVENT_RECORD_TYPE = "MUF_S7_EPISODE_MEMBERSHIP_EVENT"

# Deterministic S7 error codes
S7_INVALID_DEPENDENCE_CONTRACT = "S7_INVALID_DEPENDENCE_CONTRACT"
S7_ILLEGAL_INDEPENDENCE_CLAIM = "S7_ILLEGAL_INDEPENDENCE_CLAIM"
S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN = "S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN"
S7_INVALID_EPISODE_ANCHOR = "S7_INVALID_EPISODE_ANCHOR"
S7_INVALID_MEMBERSHIP_EVENT = "S7_INVALID_MEMBERSHIP_EVENT"
S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN = (
    "S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN"
)
S7_UNKNOWN_EPISODE_ID = "S7_UNKNOWN_EPISODE_ID"
S7_FINAL_DATASET_FORBIDDEN = "S7_FINAL_DATASET_FORBIDDEN"


DEPENDENCE_CONTRACT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S7_DEPENDENCE_ACCOUNTING_CONTRACT",
    schema_identity=S7_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "contract_id",
        "grouping_rule_ref",
        "overlap_rule_ref",
        "supersession_rule_ref",
        "statistical_independence_claim",
        "research_debt_024_status",
    ),
)

EPISODE_ANCHOR_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_EPISODE_ANCHOR_V1",
    schema_identity=S7_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "timeline_id",
        "anchor_wave_process_id",
        "anchor_origin_key",
        "episode_creation_key",
        "representation_spec_hash",
        "authority_policy_hash",
    ),
)

EPISODE_MEMBERSHIP_EVENT_SCHEMA = ArtifactIdentitySchema(
    artifact_type="MUF_S7_EPISODE_MEMBERSHIP_EVENT",
    schema_identity=S7_SCHEMA_IDENTITY,
    identity_defining_fields=(
        "episode_id",
        "member_ref",
        "event_type",
        "membership_information_key",
        "supersedes_event_id",
    ),
)


def _require_non_empty_str(val: Any, name: str, err_code: str) -> str:
    if not isinstance(val, str) or not val.strip():
        raise SchemaViolation(f"{err_code}: {name} must be a non-empty string")
    return val


def _require_completed_key(
    val: Any, name: str, err_code: str
) -> InformationKey:
    if not isinstance(val, InformationKey):
        raise InformationKeyViolation(
            f"{err_code}: {name} must be an InformationKey"
        )
    if val.information_phase == InformationPhase.BAR_PRE_CLOSE:
        raise IllegalCausalReference(
            f"{err_code}: {name} cannot have BAR_PRE_CLOSE phase"
        )
    return val


@dataclass(frozen=True)
class DependenceAccountingContract(ImmutableRecord):
    """Dependence accounting contract enforcing I-EP-3 (episode accounting != statistical independence)."""

    contract_id: str
    grouping_rule_ref: str
    overlap_rule_ref: str
    supersession_rule_ref: str
    statistical_independence_claim: str
    research_debt_024_status: str
    contract_hash: str

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.contract_id, "contract_id", S7_INVALID_DEPENDENCE_CONTRACT
        )
        _require_non_empty_str(
            self.grouping_rule_ref,
            "grouping_rule_ref",
            S7_INVALID_DEPENDENCE_CONTRACT,
        )
        _require_non_empty_str(
            self.overlap_rule_ref,
            "overlap_rule_ref",
            S7_INVALID_DEPENDENCE_CONTRACT,
        )
        _require_non_empty_str(
            self.supersession_rule_ref,
            "supersession_rule_ref",
            S7_INVALID_DEPENDENCE_CONTRACT,
        )
        if (
            self.statistical_independence_claim
            != STATISTICAL_INDEPENDENCE_STANDING_CLAIM
        ):
            raise SchemaViolation(
                f"{S7_ILLEGAL_INDEPENDENCE_CLAIM}: statistical_independence_claim must be "
                f"{STATISTICAL_INDEPENDENCE_STANDING_CLAIM!r} (I-EP-3)"
            )
        if self.research_debt_024_status != RESEARCH_DEBT_024_STANDING_STATUS:
            raise SchemaViolation(
                f"{S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN}: research_debt_024_status must remain "
                f"{RESEARCH_DEBT_024_STANDING_STATUS!r} (I-EP-3)"
            )

        expected_hash = canonical_artifact_identity(
            DEPENDENCE_CONTRACT_SCHEMA,
            identity_payload={
                "contract_id": self.contract_id,
                "grouping_rule_ref": self.grouping_rule_ref,
                "overlap_rule_ref": self.overlap_rule_ref,
                "supersession_rule_ref": self.supersession_rule_ref,
                "statistical_independence_claim": self.statistical_independence_claim,
                "research_debt_024_status": self.research_debt_024_status,
            },
        )
        if self.contract_hash != expected_hash:
            raise SchemaViolation(
                f"{S7_INVALID_DEPENDENCE_CONTRACT}: contract_hash mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        contract_id: str,
        grouping_rule_ref: str = "ORIGIN_ANCHORED_WAVE_EPISODE_V1",
        overlap_rule_ref: str = "CAUSAL_SPAN_OVERLAP_CLUSTER_V1",
        supersession_rule_ref: str = "APPEND_ONLY_SUPERSESSION_EVENT_V1",
        statistical_independence_claim: str = STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
        research_debt_024_status: str = RESEARCH_DEBT_024_STANDING_STATUS,
    ) -> "DependenceAccountingContract":
        c_hash = canonical_artifact_identity(
            DEPENDENCE_CONTRACT_SCHEMA,
            identity_payload={
                "contract_id": contract_id,
                "grouping_rule_ref": grouping_rule_ref,
                "overlap_rule_ref": overlap_rule_ref,
                "supersession_rule_ref": supersession_rule_ref,
                "statistical_independence_claim": statistical_independence_claim,
                "research_debt_024_status": research_debt_024_status,
            },
        )
        return cls(
            contract_id=contract_id,
            grouping_rule_ref=grouping_rule_ref,
            overlap_rule_ref=overlap_rule_ref,
            supersession_rule_ref=supersession_rule_ref,
            statistical_independence_claim=statistical_independence_claim,
            research_debt_024_status=research_debt_024_status,
            contract_hash=c_hash,
        )


@dataclass(frozen=True)
class EpisodeAnchorIdentityRecord(ImmutableRecord):
    """Immutable episode anchor identity computed strictly from anchor facts, NEVER member set (D1-14, I-EP-1)."""

    episode_id: str
    timeline_id: str
    anchor_wave_process_id: str
    anchor_origin_position: int
    anchor_origin_key: InformationKey
    episode_creation_key: InformationKey
    representation_spec_hash: str
    authority_policy_hash: str
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.episode_id, "episode_id", S7_INVALID_EPISODE_ANCHOR
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S7_INVALID_EPISODE_ANCHOR
        )
        _require_non_empty_str(
            self.anchor_wave_process_id,
            "anchor_wave_process_id",
            S7_INVALID_EPISODE_ANCHOR,
        )
        if (
            isinstance(self.anchor_origin_position, bool)
            or not isinstance(self.anchor_origin_position, int)
            or self.anchor_origin_position < 0
        ):
            raise SchemaViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: anchor_origin_position must be >= 0"
            )
        _require_completed_key(
            self.anchor_origin_key,
            "anchor_origin_key",
            S7_INVALID_EPISODE_ANCHOR,
        )
        _require_completed_key(
            self.episode_creation_key,
            "episode_creation_key",
            S7_INVALID_EPISODE_ANCHOR,
        )
        if (
            self.anchor_origin_key.timeline_id != self.timeline_id
            or self.episode_creation_key.timeline_id != self.timeline_id
        ):
            raise InformationKeyViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: timeline mismatch"
            )
        require_visible_at(
            fact_key=self.anchor_origin_key, at_key=self.episode_creation_key
        )
        _require_non_empty_str(
            self.representation_spec_hash,
            "representation_spec_hash",
            S7_INVALID_EPISODE_ANCHOR,
        )
        _require_non_empty_str(
            self.authority_policy_hash,
            "authority_policy_hash",
            S7_INVALID_EPISODE_ANCHOR,
        )

        expected_id = canonical_artifact_identity(
            EPISODE_ANCHOR_SCHEMA,
            identity_payload={
                "timeline_id": self.timeline_id,
                "anchor_wave_process_id": self.anchor_wave_process_id,
                "anchor_origin_key": self.anchor_origin_key,
                "episode_creation_key": self.episode_creation_key,
                "representation_spec_hash": self.representation_spec_hash,
                "authority_policy_hash": self.authority_policy_hash,
            },
        )
        if self.episode_id != expected_id:
            raise SchemaViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: episode_id mismatch with canonical anchor identity"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type != S7_EPISODE_ANCHOR_RECORD_TYPE
            or self.published_record.record_identity != self.episode_id
            or self.published_record.availability_key
            != self.episode_creation_key
        ):
            raise SchemaViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: published_record mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        timeline_id: str,
        anchor_wave_process_id: str,
        anchor_origin_position: int,
        anchor_origin_key: InformationKey,
        episode_creation_key: InformationKey,
        representation_spec_hash: str,
        authority_policy_hash: str,
    ) -> "EpisodeAnchorIdentityRecord":
        ep_id = canonical_artifact_identity(
            EPISODE_ANCHOR_SCHEMA,
            identity_payload={
                "timeline_id": timeline_id,
                "anchor_wave_process_id": anchor_wave_process_id,
                "anchor_origin_key": anchor_origin_key,
                "episode_creation_key": episode_creation_key,
                "representation_spec_hash": representation_spec_hash,
                "authority_policy_hash": authority_policy_hash,
            },
        )
        pub = PublishedRecord(
            record_type=S7_EPISODE_ANCHOR_RECORD_TYPE,
            record_identity=ep_id,
            schema_identity=S7_SCHEMA_IDENTITY,
            timeline_id=timeline_id,
            availability_key=episode_creation_key,
            content={
                "episode_id": ep_id,
                "anchor_wave_process_id": anchor_wave_process_id,
                "anchor_origin_position": anchor_origin_position,
            },
        )
        return cls(
            episode_id=ep_id,
            timeline_id=timeline_id,
            anchor_wave_process_id=anchor_wave_process_id,
            anchor_origin_position=anchor_origin_position,
            anchor_origin_key=anchor_origin_key,
            episode_creation_key=episode_creation_key,
            representation_spec_hash=representation_spec_hash,
            authority_policy_hash=authority_policy_hash,
            published_record=pub,
        )


@dataclass(frozen=True)
class EpisodeMembershipEventRecord(ImmutableRecord):
    """Append-only episode membership or supersession event (D1-14, I-EP-1..2, D2-10, I-IKA-1)."""

    event_id: str
    episode_id: str
    timeline_id: str
    member_ref: str
    member_availability_key: InformationKey
    membership_information_key: InformationKey
    event_type: str
    supersedes_event_id: Union[str, TypedState]
    published_record: PublishedRecord

    def __post_init__(self) -> None:
        _require_non_empty_str(
            self.event_id, "event_id", S7_INVALID_MEMBERSHIP_EVENT
        )
        _require_non_empty_str(
            self.episode_id, "episode_id", S7_INVALID_MEMBERSHIP_EVENT
        )
        _require_non_empty_str(
            self.timeline_id, "timeline_id", S7_INVALID_MEMBERSHIP_EVENT
        )
        _require_non_empty_str(
            self.member_ref, "member_ref", S7_INVALID_MEMBERSHIP_EVENT
        )
        _require_completed_key(
            self.member_availability_key,
            "member_availability_key",
            S7_INVALID_MEMBERSHIP_EVENT,
        )
        _require_completed_key(
            self.membership_information_key,
            "membership_information_key",
            S7_INVALID_MEMBERSHIP_EVENT,
        )
        require_visible_at(
            fact_key=self.member_availability_key,
            at_key=self.membership_information_key,
        )
        if self.event_type not in LEGAL_MEMBERSHIP_EVENT_TYPES:
            raise SchemaViolation(
                f"{S7_INVALID_MEMBERSHIP_EVENT}: invalid event_type {self.event_type!r}"
            )
        if self.event_type == MEMBERSHIP_EVENT_ADDED:
            if self.supersedes_event_id is not TypedState.NOT_APPLICABLE:
                raise SchemaViolation(
                    f"{S7_INVALID_MEMBERSHIP_EVENT}: MEMBER_ADDED requires supersedes_event_id = NOT_APPLICABLE"
                )
        else:
            _require_non_empty_str(
                self.supersedes_event_id,
                "supersedes_event_id",
                S7_INVALID_MEMBERSHIP_EVENT,
            )

        expected_id = canonical_artifact_identity(
            EPISODE_MEMBERSHIP_EVENT_SCHEMA,
            identity_payload={
                "episode_id": self.episode_id,
                "member_ref": self.member_ref,
                "event_type": self.event_type,
                "membership_information_key": self.membership_information_key,
                "supersedes_event_id": self.supersedes_event_id,
            },
        )
        if self.event_id != expected_id:
            raise SchemaViolation(
                f"{S7_INVALID_MEMBERSHIP_EVENT}: event_id mismatch"
            )
        if (
            not isinstance(self.published_record, PublishedRecord)
            or self.published_record.record_type
            != S7_EPISODE_MEMBERSHIP_EVENT_RECORD_TYPE
            or self.published_record.record_identity != self.event_id
            or self.published_record.availability_key
            != self.membership_information_key
        ):
            raise SchemaViolation(
                f"{S7_INVALID_MEMBERSHIP_EVENT}: published_record mismatch"
            )

    @classmethod
    def create(
        cls,
        *,
        anchor: EpisodeAnchorIdentityRecord,
        member_ref: str,
        member_availability_key: InformationKey,
        event_type: str = MEMBERSHIP_EVENT_ADDED,
        supersedes_event_id: Union[str, TypedState] = TypedState.NOT_APPLICABLE,
        event_key_override: Optional[InformationKey] = None,
    ) -> "EpisodeMembershipEventRecord":
        if not isinstance(anchor, EpisodeAnchorIdentityRecord):
            raise SchemaViolation(
                "anchor must be an EpisodeAnchorIdentityRecord"
            )
        earliest_key = (
            anchor.episode_creation_key
            if member_availability_key <= anchor.episode_creation_key
            else member_availability_key
        )
        mem_key = (
            earliest_key
            if event_key_override is None
            else event_key_override
        )
        require_visible_at(
            fact_key=anchor.episode_creation_key, at_key=mem_key
        )
        require_visible_at(fact_key=member_availability_key, at_key=mem_key)

        ev_id = canonical_artifact_identity(
            EPISODE_MEMBERSHIP_EVENT_SCHEMA,
            identity_payload={
                "episode_id": anchor.episode_id,
                "member_ref": member_ref,
                "event_type": event_type,
                "membership_information_key": mem_key,
                "supersedes_event_id": supersedes_event_id,
            },
        )
        pub = PublishedRecord(
            record_type=S7_EPISODE_MEMBERSHIP_EVENT_RECORD_TYPE,
            record_identity=ev_id,
            schema_identity=S7_SCHEMA_IDENTITY,
            timeline_id=anchor.timeline_id,
            availability_key=mem_key,
            content={
                "event_id": ev_id,
                "episode_id": anchor.episode_id,
                "member_ref": member_ref,
                "event_type": event_type,
            },
        )
        return cls(
            event_id=ev_id,
            episode_id=anchor.episode_id,
            timeline_id=anchor.timeline_id,
            member_ref=member_ref,
            member_availability_key=member_availability_key,
            membership_information_key=mem_key,
            event_type=event_type,
            supersedes_event_id=supersedes_event_id,
            published_record=pub,
        )


class CausalEpisodeLedger:
    """Append-only episode anchor and membership ledger (D1-14, I-EP-1..2)."""

    def __init__(self) -> None:
        self.__anchors_by_id: dict[str, EpisodeAnchorIdentityRecord] = {}
        self.__events: list[EpisodeMembershipEventRecord] = []

    def register_anchor(
        self, anchor: EpisodeAnchorIdentityRecord
    ) -> EpisodeAnchorIdentityRecord:
        if not isinstance(anchor, EpisodeAnchorIdentityRecord):
            raise SchemaViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: expected EpisodeAnchorIdentityRecord"
            )
        anchors = object.__getattribute__(
            self, "_CausalEpisodeLedger__anchors_by_id"
        )
        if anchor.episode_id in anchors:
            raise ImmutabilityViolation(
                f"{S7_INVALID_EPISODE_ANCHOR}: duplicate episode_id {anchor.episode_id!r}"
            )
        anchors[anchor.episode_id] = anchor
        return anchor

    def append_membership_event(
        self, event: EpisodeMembershipEventRecord
    ) -> EpisodeMembershipEventRecord:
        if not isinstance(event, EpisodeMembershipEventRecord):
            raise SchemaViolation(
                f"{S7_INVALID_MEMBERSHIP_EVENT}: expected EpisodeMembershipEventRecord"
            )
        anchors = object.__getattribute__(
            self, "_CausalEpisodeLedger__anchors_by_id"
        )
        if event.episode_id not in anchors:
            raise SchemaViolation(
                f"{S7_UNKNOWN_EPISODE_ID}: unknown episode_id {event.episode_id!r}"
            )
        events = object.__getattribute__(self, "_CausalEpisodeLedger__events")
        events.append(event)
        return event

    def delete_member(self, episode_id: str, member_ref: str) -> None:
        """Historical member deletion is strictly forbidden (D1-14, I-EP-2)."""
        raise ImmutabilityViolation(
            f"{S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN}: historical removal of member "
            f"{member_ref!r} from episode {episode_id!r} is forbidden; use a MEMBER_SUPERSEDED event (I-EP-2)"
        )

    def anchors(self) -> Tuple[EpisodeAnchorIdentityRecord, ...]:
        anchors = object.__getattribute__(
            self, "_CausalEpisodeLedger__anchors_by_id"
        )
        return tuple(anchors.values())

    def membership_events(self) -> Tuple[EpisodeMembershipEventRecord, ...]:
        events = object.__getattribute__(self, "_CausalEpisodeLedger__events")
        return tuple(events)


@dataclass(frozen=True)
class DependenceAccountingAsOfView(ImmutableRecord):
    """Causal as-of projection of DependenceAccountingBundle at ``query_key``."""

    timeline_id: str
    query_key: InformationKey
    contract_hash: str
    visible_anchors: Tuple[EpisodeAnchorIdentityRecord, ...]
    visible_membership_events: Tuple[EpisodeMembershipEventRecord, ...]
    active_members_by_episode: Mapping[str, Tuple[str, ...]]
    raw_active_member_count: int
    distinct_episode_count: int
    non_overlapping_span_cluster_count: int
    statistical_independence_claim: str
    research_debt_024_status: str


@dataclass(frozen=True)
class DependenceAccountingBundle(ImmutableRecord):
    """Complete S7 Dependence Accounting Bundle over an S6 GenericFactualStateGraphBundle."""

    contract: DependenceAccountingContract
    state_graph_bundle: GenericFactualStateGraphBundle
    episode_anchors: Tuple[EpisodeAnchorIdentityRecord, ...]
    membership_events: Tuple[EpisodeMembershipEventRecord, ...]
    non_overlapping_span_cluster_count: int
    statistical_independence_claim: str
    research_debt_024_status: str


def _count_non_overlapping_span_clusters(
    spans: Sequence[Tuple[int, int]]
) -> int:
    """Count merged non-overlapping [start_pos, end_pos] span clusters in O(K log K)."""
    if len(spans) == 0:
        return 0
    sorted_spans = sorted(spans, key=lambda s: (s[0], s[1]))
    clusters = 1
    curr_end = sorted_spans[0][1]
    for idx in range(1, len(sorted_spans)):
        st, en = sorted_spans[idx]
        if st > curr_end:
            clusters += 1
            curr_end = en
        elif en > curr_end:
            curr_end = en
    return clusters


def build_dependence_accounting_bundle(
    state_graph_bundle: GenericFactualStateGraphBundle,
    *,
    contract: DependenceAccountingContract,
) -> DependenceAccountingBundle:
    """Build a DependenceAccountingBundle in O(N) over a GenericFactualStateGraphBundle (D1-14, I-EP-1..3)."""
    if not isinstance(state_graph_bundle, GenericFactualStateGraphBundle):
        raise SchemaViolation(
            "state_graph_bundle must be a GenericFactualStateGraphBundle"
        )
    if not isinstance(contract, DependenceAccountingContract):
        raise SchemaViolation(
            "contract must be a DependenceAccountingContract"
        )
    wb = state_graph_bundle.wave_bundle
    if wb.dataset_role not in (
        DATASET_ROLE_DEVELOPMENT_FIT,
        DATASET_ROLE_DEVELOPMENT_SELECTION,
    ):
        raise SelectionBlockedError(
            f"{S7_FINAL_DATASET_FORBIDDEN}: S7 dependence accounting forbidden on {wb.dataset_role!r}"
        )

    ledger = CausalEpisodeLedger()
    anchor_by_wp: dict[str, EpisodeAnchorIdentityRecord] = {}
    for wi in wb.wave_identity_records:
        anc = EpisodeAnchorIdentityRecord.create(
            timeline_id=wi.timeline_id,
            anchor_wave_process_id=wi.wave_process_id,
            anchor_origin_position=wi.origin_position,
            anchor_origin_key=wi.origin_key,
            episode_creation_key=wi.wave_identity_information_key,
            representation_spec_hash=wb.representation_spec.representation_spec_hash,
            authority_policy_hash=wb.policy_artifact.policy_hash,
        )
        ledger.register_anchor(anc)
        anchor_by_wp[wi.wave_process_id] = anc

    # Append running observations and descriptor observations as episode members without mutating episode_id
    for ro in wb.running_wave_observations:
        anc = anchor_by_wp[ro.wave_process_id]
        ev = EpisodeMembershipEventRecord.create(
            anchor=anc,
            member_ref=ro.observation_id,
            member_availability_key=ro.observation_key,
            event_type=MEMBERSHIP_EVENT_ADDED,
        )
        ledger.append_membership_event(ev)

    for dobs in state_graph_bundle.descriptor_observations:
        anc = anchor_by_wp[dobs.wave_process_id]
        ev = EpisodeMembershipEventRecord.create(
            anchor=anc,
            member_ref=dobs.observation_id,
            member_availability_key=dobs.observation_key,
            event_type=MEMBERSHIP_EVENT_ADDED,
        )
        ledger.append_membership_event(ev)

    spans = [
        (fg.start_origin_position, fg.end_origin_position)
        for fg in wb.finalized_wave_geometries
    ]
    cluster_cnt = _count_non_overlapping_span_clusters(spans)

    return DependenceAccountingBundle(
        contract=contract,
        state_graph_bundle=state_graph_bundle,
        episode_anchors=ledger.anchors(),
        membership_events=ledger.membership_events(),
        non_overlapping_span_cluster_count=cluster_cnt,
        statistical_independence_claim=STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
        research_debt_024_status=RESEARCH_DEBT_024_STANDING_STATUS,
    )


def query_dependence_accounting_as_of(
    bundle: DependenceAccountingBundle,
    *,
    at_key: InformationKey,
) -> DependenceAccountingAsOfView:
    """Project a DependenceAccountingBundle causally at ``at_key``."""
    if not isinstance(bundle, DependenceAccountingBundle):
        raise SchemaViolation("bundle must be a DependenceAccountingBundle")
    _require_completed_key(at_key, "at_key", S7_INVALID_DEPENDENCE_CONTRACT)
    wb = bundle.state_graph_bundle.wave_bundle
    if at_key.timeline_id != wb.timeline_id:
        raise InformationKeyViolation("at_key timeline mismatch with bundle")
    if not (wb.observation_keys[0] <= at_key <= wb.observation_keys[-1]):
        raise PrematureAvailability("at_key outside bundle observation_keys")

    vis_anchors = tuple(
        a for a in bundle.episode_anchors if a.episode_creation_key <= at_key
    )
    vis_events = tuple(
        e
        for e in bundle.membership_events
        if e.membership_information_key <= at_key
    )

    superseded_event_ids: set[str] = {
        str(e.supersedes_event_id)
        for e in vis_events
        if e.event_type == MEMBERSHIP_EVENT_SUPERSEDED
    }
    active_by_ep: dict[str, list[str]] = {
        a.episode_id: [] for a in vis_anchors
    }
    raw_cnt = 0
    for e in vis_events:
        if (
            e.event_type == MEMBERSHIP_EVENT_ADDED
            and e.event_id not in superseded_event_ids
            and e.episode_id in active_by_ep
        ):
            active_by_ep[e.episode_id].append(e.member_ref)
            raw_cnt += 1

    vis_spans = [
        (fg.start_origin_position, fg.end_origin_position)
        for fg in wb.finalized_wave_geometries
        if fg.wave_end_confirmed_key <= at_key
    ]
    vis_clusters = _count_non_overlapping_span_clusters(vis_spans)

    return DependenceAccountingAsOfView(
        timeline_id=wb.timeline_id,
        query_key=at_key,
        contract_hash=bundle.contract.contract_hash,
        visible_anchors=vis_anchors,
        visible_membership_events=vis_events,
        active_members_by_episode={
            k_id: tuple(v_list) for k_id, v_list in active_by_ep.items()
        },
        raw_active_member_count=raw_cnt,
        distinct_episode_count=len(vis_anchors),
        non_overlapping_span_cluster_count=vis_clusters,
        statistical_independence_claim=STATISTICAL_INDEPENDENCE_STANDING_CLAIM,
        research_debt_024_status=RESEARCH_DEBT_024_STANDING_STATUS,
    )


__all__ = [
    "CausalEpisodeLedger",
    "DEPENDENCE_CONTRACT_SCHEMA",
    "DependenceAccountingAsOfView",
    "DependenceAccountingBundle",
    "DependenceAccountingContract",
    "EPISODE_ANCHOR_SCHEMA",
    "EPISODE_MEMBERSHIP_EVENT_SCHEMA",
    "EpisodeAnchorIdentityRecord",
    "EpisodeMembershipEventRecord",
    "LEGAL_MEMBERSHIP_EVENT_TYPES",
    "MEMBERSHIP_EVENT_ADDED",
    "MEMBERSHIP_EVENT_SUPERSEDED",
    "RESEARCH_DEBT_024_STANDING_STATUS",
    "S7_EPISODE_ANCHOR_RECORD_TYPE",
    "S7_EPISODE_MEMBERSHIP_EVENT_RECORD_TYPE",
    "S7_FINAL_DATASET_FORBIDDEN",
    "S7_HISTORICAL_MEMBER_DELETION_FORBIDDEN",
    "S7_ILLEGAL_INDEPENDENCE_CLAIM",
    "S7_INVALID_DEPENDENCE_CONTRACT",
    "S7_INVALID_EPISODE_ANCHOR",
    "S7_INVALID_MEMBERSHIP_EVENT",
    "S7_RESEARCH_DEBT_024_MUST_REMAIN_OPEN",
    "S7_SCHEMA_IDENTITY",
    "S7_UNKNOWN_EPISODE_ID",
    "STATISTICAL_INDEPENDENCE_STANDING_CLAIM",
    "build_dependence_accounting_bundle",
    "query_dependence_accounting_as_of",
]
