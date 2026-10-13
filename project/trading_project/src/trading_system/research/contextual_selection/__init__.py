"""Contextual Selection Method (CSM) research kernel — Phase 0, no learning.

Implements the knowledge contracts of the accepted research (jfjdjdieifne/test
@ 6c8bf6fd, knowledge_foundation files 15-19) as an operational, non-learned
selection layer over movement representations:

- CSM vocabulary: property classes F/O/S/L/U, exclusion codes X-*, unresolved
  reason codes MO/MP/AI/IC/EP/OOD (file 15).
- Seed procedures SP-01/03/05/06/07/13/14/18/19/20 (file 17).
- Task cards T-S1 structural reference, T-S2 event binding, T-S3 entry-timing
  leg, T-S5 falsifier (file 16).  T-S4/T-S6 are reported through the same
  result types but are not part of the first build scope.
- L1 turning-point generators F-K (k-bar pivot) and F-T (threshold reversal)
  with DECLARED POLICY SLOTS ONLY (O-class, no default market values), L2 legs.
- Candidate/interpretation ledger with revision propagation (IC-10/IC-11).

Design rules honored here (LRN-01..06, SWS-01..08):
- No learned scores; learning may later supply L-class preferences only.
- Nothing is silently pruned: every exclusion carries an X-* code and stays
  in the output; every unresolved state carries a reason code and evidence.
- No layer reads a higher layer (file 15 §15.10).
- Replay consistency is a property of the generators and task procedures:
  recomputing from data truncated at t must reproduce the stored output at t.
"""

from trading_system.research.contextual_selection.csm import (  # noqa: F401
    CLASS_F,
    CLASS_L,
    CLASS_O,
    CLASS_S,
    CLASS_U,
    EXCLUSION_CODES,
    KIND_AUTHORIZED,
    KIND_FACTUAL,
    KIND_PROCEDURE,
    KIND_RESEARCH,
    KIND_SOURCE,
    POLICY_KINDS,
    REASON_AI,
    REASON_EP,
    REASON_IC,
    REASON_MO,
    REASON_MP,
    REASON_OOD,
    STATUS_BROKEN,
    STATUS_CONFIRMED,
    STATUS_PROVISIONAL,
    STATUS_SUPERSEDED,
    TIE_BOUNDARIES,
    TIE_CROSS_EQUAL_BOUND_V1,
    TIE_CROSS_EQUAL_UNBOUND,
    TIE_CROSS_POLICIES,
    TIE_FT_EQ_FIRST,
    TIE_FT_EQ_LAST,
    PHASE_PRE_EVENT,
    PHASE_BINDING,
    PHASE_POST_EVENT,
    EVENT_ORDER_V1,
    X_DOM,
    X_GEOM,
    X_KNOW,
    X_POL,
    X_SCALE,
    X_STATE,
    X_SUPER,
    Exclusion,
    InterpretationLedger,
    LegCandidate,
    PointCandidate,
    PolicyRegistry,
    PropertyRecord,
    Representation,
    SelectionResult,
    StatusTransition,
    TaskCard,
    UnresolvedState,
    available_at,
    build_legs,
    candidate_record,
    require_validated_asof,
    fk_turning_points,
    ft_turning_points,
    material_same_bar_ambiguity,
    reference_state_at,
    same_bar_evidence_class,
    SharedInformationAxis,
    stable_point_id,
    stable_leg_id,
    sp01_knowability,
    sp03_binding,
    sp05_containment,
    sp06_dominance,
    sp07_consistency,
    task_s1_structural_reference,
    task_s2_event_binding,
    task_s3_entry_leg,
    task_s5_falsifier,
)

__all__ = [
    "CLASS_F", "CLASS_O", "CLASS_S", "CLASS_L", "CLASS_U",
    "REASON_MO", "REASON_MP", "REASON_AI", "REASON_IC", "REASON_EP", "REASON_OOD",
    "X_KNOW", "X_SCALE", "X_SUPER", "X_STATE", "X_GEOM", "X_DOM", "X_POL",
    "EXCLUSION_CODES",
    "STATUS_CONFIRMED", "STATUS_PROVISIONAL", "STATUS_SUPERSEDED", "STATUS_BROKEN",
    "TIE_FT_EQ_FIRST", "TIE_FT_EQ_LAST", "TIE_BOUNDARIES", "TIE_CROSS_EQUAL_UNBOUND",
    "TIE_CROSS_EQUAL_BOUND_V1", "TIE_CROSS_POLICIES",
    "PHASE_PRE_EVENT", "PHASE_BINDING", "PHASE_POST_EVENT", "EVENT_ORDER_V1",
    "KIND_RESEARCH", "KIND_AUTHORIZED", "KIND_FACTUAL", "KIND_SOURCE",
    "KIND_PROCEDURE", "POLICY_KINDS",
    "Representation", "PointCandidate", "LegCandidate", "PropertyRecord",
    "Exclusion", "UnresolvedState", "SelectionResult", "TaskCard",
    "StatusTransition",
    "PolicyRegistry", "InterpretationLedger",
    "fk_turning_points", "ft_turning_points", "build_legs",
    "available_at", "reference_state_at", "candidate_record",
    "require_validated_asof",
    "material_same_bar_ambiguity", "same_bar_evidence_class",
    "SharedInformationAxis", "stable_point_id", "stable_leg_id",
    "sp01_knowability", "sp03_binding", "sp05_containment", "sp06_dominance",
    "sp07_consistency",
    "task_s1_structural_reference", "task_s2_event_binding",
    "task_s3_entry_leg", "task_s5_falsifier",
]
