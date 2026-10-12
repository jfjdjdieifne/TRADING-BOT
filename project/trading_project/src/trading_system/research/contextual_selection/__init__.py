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
    REASON_AI,
    REASON_EP,
    REASON_IC,
    REASON_MO,
    REASON_MP,
    REASON_OOD,
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
    TaskCard,
    UnresolvedState,
    build_legs,
    fk_turning_points,
    ft_turning_points,
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
    "Representation", "PointCandidate", "LegCandidate", "PropertyRecord",
    "Exclusion", "UnresolvedState", "SelectionResult", "TaskCard",
    "PolicyRegistry", "InterpretationLedger",
    "fk_turning_points", "ft_turning_points", "build_legs",
    "sp01_knowability", "sp03_binding", "sp05_containment", "sp06_dominance",
    "sp07_consistency",
    "task_s1_structural_reference", "task_s2_event_binding",
    "task_s3_entry_leg", "task_s5_falsifier",
]
