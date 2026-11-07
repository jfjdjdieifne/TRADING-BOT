# Contextual decision layer V1 — decisions

Analytical decisions only.  selection_quality = NOT_ESTABLISHED.  Not trading signals; no orders; ranking provisional and unvalidated.

### decision DEC-decision-v1-0001 — as of 2025-08-02 00:00:00+00:00 (UTC)  [historical-replay]
state: UNRESOLVED
named event: the completion and causal confirmation of the first task-scale F-K leg (k=?)
next discriminating observation: the first completed task-scale leg's existence and direction
  why: required structural input is insufficient at this as-of: no completed task-scale leg exists yet
  would change: the first completed task-scale leg
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0002 — as of 2025-08-03 00:00:00+00:00 (UTC)  [historical-replay]
state: UNRESOLVED
named event: the completion and causal confirmation of the first task-scale F-K leg (k=?)
next discriminating observation: the first completed task-scale leg's existence and direction
  why: required structural input is insufficient at this as-of: no completed task-scale leg exists yet
  would change: the first completed task-scale leg
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0003 — as of 2025-08-04 00:00:00+00:00 (UTC)  [historical-replay]
state: UNRESOLVED
named event: the completion and causal confirmation of the first task-scale F-K leg (k=?)
next discriminating observation: the first completed task-scale leg's existence and direction
  why: required structural input is insufficient at this as-of: no completed task-scale leg exists yet
  would change: the first completed task-scale leg
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0004 — as of 2025-08-05 00:00:00+00:00 (UTC)  [historical-replay]
state: UNRESOLVED
named event: the completion and causal confirmation of the first task-scale F-K leg (k=?)
next discriminating observation: the first completed task-scale leg's existence and direction
  why: required structural input is insufficient at this as-of: no completed task-scale leg exists yet
  would change: the first completed task-scale leg
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0005 — as of 2025-08-06 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-03T04:00:00+00:00-2025-08-04T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-03T04:00:00+00:00-2025-08-04T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-29
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-29
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0006 — as of 2025-08-07 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-04T20:00:00+00:00-2025-08-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-04T20:00:00+00:00-2025-08-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-35
  why: no SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-35
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0007 — as of 2025-08-08 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-04T20:00:00+00:00-2025-08-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 (level 115720) on the up side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-04T20:00:00+00:00-2025-08-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-41
  why: SF-AVL-1h-decision-v1-41
  why: SF-AVL-15m-decision-v1-41
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 (4 event(s))
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE up of 115720 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00) at 2025-08-07 12:00:00+00:00
  would change: completed 4h bar CLOSE up of 115720 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00) at 2025-08-07 16:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00 (level 115720) on the up side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0008 — as of 2025-08-09 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-47
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-47
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0009 — as of 2025-08-10 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-53
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-53
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0010 — as of 2025-08-11 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=1, violation=0 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-59
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-59
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
model: provisional-unvalidated; support continuation=1/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0011 — as of 2025-08-12 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=1, violation=0 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-05T16:00:00+00:00-2025-08-08T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-65
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-65
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
model: provisional-unvalidated; support continuation=1/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0012 — as of 2025-08-13 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (level 122335) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=2 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (level 122335) on the up side
model: provisional-unvalidated; support continuation=0/violation=2
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0013 — as of 2025-08-14 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (level 122335) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=2 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (2 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00 (level 122335) on the up side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=2
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0014 — as of 2025-08-15 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-12T00:00:00+00:00-2025-08-14T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (level 118050) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-12T00:00:00+00:00-2025-08-14T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-83
  why: SF-AVL-1h-decision-v1-83
  why: SF-AVL-15m-decision-v1-83
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (1 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 118050 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00) at 2025-08-14 20:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (level 118050) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0015 — as of 2025-08-16 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-12T00:00:00+00:00-2025-08-14T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (level 118050) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=4, violation=0 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-12T00:00:00+00:00-2025-08-14T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-89
  why: SF-AVL-1h-decision-v1-89
  why: SF-AVL-15m-decision-v1-89
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (4 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 118050 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00) at 2025-08-14 20:00:00+00:00
  would change: completed 4h bar CLOSE down of 118050 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00) at 2025-08-15 16:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00 (level 118050) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=4/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0016 — as of 2025-08-17 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (level 124474) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=2 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (level 124474) on the up side
model: provisional-unvalidated; support continuation=0/violation=2
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0017 — as of 2025-08-18 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (level 124474) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=3 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00 (level 124474) on the up side
model: provisional-unvalidated; support continuation=0/violation=3
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0018 — as of 2025-08-19 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=5, violation=0 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-107
  why: SF-AVL-1h-decision-v1-107
  why: SF-AVL-15m-decision-v1-107
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (6 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 04:00:00+00:00
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=5/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0019 — as of 2025-08-20 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=5, violation=0 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-113
  why: SF-AVL-1h-decision-v1-113
  why: SF-AVL-15m-decision-v1-113
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (12 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 04:00:00+00:00
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=5/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0020 — as of 2025-08-21 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=5, violation=1 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-15T20:00:00+00:00-2025-08-17T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-119
  why: SF-AVL-1h-decision-v1-119
  why: SF-AVL-15m-decision-v1-119
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (18 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 04:00:00+00:00
  would change: completed 4h bar CLOSE down of 116804 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00) at 2025-08-18 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00 (level 116804) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=5/violation=1
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0021 — as of 2025-08-22 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-scenario [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-20T16:00:00+00:00-2025-08-21T04:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
next discriminating observation: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
  why: causal context at this as-of: {'direction': 'none', 'ref_status': 'unresolved', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-scenario: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-20T16:00:00+00:00-2025-08-21T04:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
  why: SF-DIR-decision-v1-125
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond the reference (unresolved) on the falsifying side (SP-03)
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0022 — as of 2025-08-23 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-scenario [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-20T16:00:00+00:00-2025-08-21T04:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
next discriminating observation: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
  why: causal context at this as-of: {'direction': 'none', 'ref_status': 'unresolved', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-scenario: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-20T16:00:00+00:00-2025-08-21T04:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
  why: SF-DIR-decision-v1-131
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond the reference (unresolved) on the falsifying side (SP-03)
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0023 — as of 2025-08-24 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-scenario [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-22T16:00:00+00:00-2025-08-22T20:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
next discriminating observation: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
  why: causal context at this as-of: {'direction': 'none', 'ref_status': 'unresolved', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-scenario: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-22T16:00:00+00:00-2025-08-22T20:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
  why: SF-DIR-decision-v1-137
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond the reference (unresolved) on the falsifying side (SP-03)
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-20T16:00:00+00:00 (level 112380) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0024 — as of 2025-08-25 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-22T20:00:00+00:00-2025-08-23T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-22T20:00:00+00:00-2025-08-23T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-143
  why: no SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-143
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0025 — as of 2025-08-26 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0009 revised to condition_observed by post-record evidence (FC-decision-v1-0009@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=2, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: forecast FC-decision-v1-0009 revised to condition_observed by post-record evidence (FC-decision-v1-0009@v1 preserved)
model: provisional-unvalidated; support continuation=2/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0026 — as of 2025-08-27 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=2, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
model: provisional-unvalidated; support continuation=2/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0027 — as of 2025-08-28 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=2, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
model: provisional-unvalidated; support continuation=2/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0028 — as of 2025-08-29 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=2, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00 (level 117429) on the up side
model: provisional-unvalidated; support continuation=2/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0029 — as of 2025-08-30 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-26T04:00:00+00:00-2025-08-28T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'contained', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-26T04:00:00+00:00-2025-08-28T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-173
  why: SF-AVL-1h-decision-v1-173
  why: SF-AVL-15m-decision-v1-173
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00 (3 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 108667 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00) at 2025-08-29 16:00:00+00:00
  would change: completed 4h bar CLOSE down of 108667 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00) at 2025-08-29 20:00:00+00:00
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0030 — as of 2025-08-31 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-28T16:00:00+00:00 (level 113486) on the up side
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=3, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-08-28T16:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-28T16:00:00+00:00 (level 113486) on the up side
model: provisional-unvalidated; support continuation=3/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0031 — as of 2025-09-01 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-30T04:00:00+00:00-2025-08-31T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=5, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-30T04:00:00+00:00-2025-08-31T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-185
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-185
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=5/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0032 — as of 2025-09-02 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-30T04:00:00+00:00-2025-08-31T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=5, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-08-30T04:00:00+00:00-2025-08-31T04:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-191
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-191
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=5/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0033 — as of 2025-09-03 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-31T04:00:00+00:00-2025-09-01T08:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (level 109480) on the up side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-31T04:00:00+00:00-2025-09-01T08:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-197
  why: SF-AVL-1h-decision-v1-197
  why: SF-AVL-15m-decision-v1-197
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (6 event(s))
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE up of 109480 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00) at 2025-09-02 04:00:00+00:00
  would change: completed 4h bar CLOSE up of 109480 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00) at 2025-09-02 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (level 109480) on the up side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=6/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0034 — as of 2025-09-04 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-31T04:00:00+00:00-2025-09-01T08:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (level 109480) on the up side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-08-31T04:00:00+00:00-2025-09-01T08:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-203
  why: SF-AVL-1h-decision-v1-203
  why: SF-AVL-15m-decision-v1-203
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (12 event(s))
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE up of 109480 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00) at 2025-09-02 04:00:00+00:00
  would change: completed 4h bar CLOSE up of 109480 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00) at 2025-09-02 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00 (level 109480) on the up side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=6/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0035 — as of 2025-09-05 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-scenario [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-01T08:00:00+00:00-2025-09-03T20:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
next discriminating observation: reference resolution (AI: intrabar high/low order of the selected reference is constrained (endpoint evidence: constrained:close-at-high); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
  why: causal context at this as-of: {'direction': 'none', 'ref_status': 'unresolved', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=0 (unsupported-context, provisional-unvalidated ranking)
  why: working interpretation I-scenario: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-01T08:00:00+00:00-2025-09-03T20:00:00+00:00); the falsifier reference is NOT precisely resolved at this as-of — the scenario is monitored over the recorded reference set
  why: SF-DIR-decision-v1-209
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond the reference (unresolved) on the falsifying side (SP-03)
  would change: close-based violation of PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00 (level 112650) on the down side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=0/violation=0
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0036 — as of 2025-09-06 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-primary — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-03T20:00:00+00:00-2025-09-04T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 (level 112575) on the up side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-03T20:00:00+00:00-2025-09-04T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-215
  why: SF-AVL-1h-decision-v1-215
  why: SF-AVL-15m-decision-v1-215
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 (1 event(s))
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE up of 112575 (SP-03 close-based violation of PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00) at 2025-09-05 08:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00 (level 112575) on the up side
  would change: the watched condition already occurred before/at this record (observed_before_record flags below) — it is NOT described as a pre-event prediction; the analysis is updated instead of waiting
model: provisional-unvalidated; support continuation=6/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0037 — as of 2025-09-07 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-04T16:00:00+00:00-2025-09-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-04T16:00:00+00:00-2025-09-05T16:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-221
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-221
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=7/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0038 — as of 2025-09-08 00:00:00+00:00 (UTC)  [historical-replay]
state: AWAITING_EVENT
primary working interpretation: I-primary — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: close-based violation of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 (level 113385) on the up side
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=5 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-227
  why: no SP-03 close-based violation of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-227
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  would change: close-based violation of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 (level 113385) on the up side
model: provisional-unvalidated; support continuation=6/violation=5
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0039 — as of 2025-09-09 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=6 (tied, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-233
  why: no SP-03 close-based violation of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-233
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=6/violation=6
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0040 — as of 2025-09-10 00:00:00+00:00 (UTC)  [historical-replay]
state: NO_EDGE
primary working interpretation: I-primary [no-edge baseline — not a preferred scenario] — the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=6 (tied, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved down (C:F-K(k=5)|leg2025-09-05T16:00:00+00:00-2025-09-06T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-239
  why: no SP-03 close-based violation of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-239
  why: the model does not strictly distinguish the scenarios in this context: the explicit decision is NO_EDGE (not an abstention, not UNRESOLVED)
  opposed: a new confirmed up leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
  would change: the next completed task-scale bar's CLOSE determining which binding fires first: E-VIOLATION (SP-03 close beyond the falsifier reference PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00 on its falsifying side) or E-CONTINUATION (SP-03 close beyond the last leg's end extreme in the leg direction) — until one fires the decision stays NO_EDGE
model: provisional-unvalidated; support continuation=6/violation=6
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0041 — as of 2025-09-11 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0018 revised to condition_observed by post-record evidence (FC-decision-v1-0018@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=7 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (3 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: forecast FC-decision-v1-0018 revised to condition_observed by post-record evidence (FC-decision-v1-0018@v1 preserved)
model: provisional-unvalidated; support continuation=6/violation=7
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0042 — as of 2025-09-12 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=7 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (9 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00
model: provisional-unvalidated; support continuation=6/violation=7
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0043 — as of 2025-09-13 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=8 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (15 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00
model: provisional-unvalidated; support continuation=6/violation=8
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0044 — as of 2025-09-14 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-09T16:00:00+00:00-2025-09-12T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=8, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-09T16:00:00+00:00-2025-09-12T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-263
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-263
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=8/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0045 — as of 2025-09-15 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=10 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=6/violation=10
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0046 — as of 2025-09-16 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=11 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=6/violation=11
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0047 — as of 2025-09-17 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0021 revised to condition_observed by post-record evidence (FC-decision-v1-0021@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=12 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (2 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: forecast FC-decision-v1-0021 revised to condition_observed by post-record evidence (FC-decision-v1-0021@v1 preserved)
model: provisional-unvalidated; support continuation=6/violation=12
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0048 — as of 2025-09-18 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=13 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (3 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00
model: provisional-unvalidated; support continuation=6/violation=13
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0049 — as of 2025-09-19 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0010 revised to condition_observed by post-record evidence (FC-decision-v1-0010@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=6, violation=13 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (9 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: forecast FC-decision-v1-0010 revised to condition_observed by post-record evidence (FC-decision-v1-0010@v1 preserved)
model: provisional-unvalidated; support continuation=6/violation=13
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0050 — as of 2025-09-20 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the up structure is exhausted and price develops an active down structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=1 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the up structure is exhausted and price develops an active down structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|low@2025-09-17T20:00:00+00:00 (SP-03)
  would change: a new confirmed up leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=0/violation=1
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0051 — as of 2025-09-21 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=14 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=7/violation=14
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0052 — as of 2025-09-22 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=15 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=7/violation=15
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0053 — as of 2025-09-23 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0023 revised to condition_observed by post-record evidence (FC-decision-v1-0023@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=16 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: forecast FC-decision-v1-0023 revised to condition_observed by post-record evidence (FC-decision-v1-0023@v1 preserved)
model: provisional-unvalidated; support continuation=7/violation=16
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0054 — as of 2025-09-24 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=17 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: E-VIOLATION — a completed task-scale bar whose CLOSE is strictly beyond the current falsifier reference level on the falsifying side (SP-03 close-based binding; equality is not a crossing — TIE-CROSS-EQUAL-UNBOUND-V1)
model: provisional-unvalidated; support continuation=7/violation=17
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0055 — as of 2025-09-25 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=7, violation=17 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00 (18 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00
model: provisional-unvalidated; support continuation=7/violation=17
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0056 — as of 2025-09-26 00:00:00+00:00 (UTC)  [historical-replay]
state: EVENT_OCCURRED
primary working interpretation: I-alt — materially different alternative: the up structure is exhausted and price develops an active down structure from the current boundary
material alternatives: I-primary
named event: forecast FC-decision-v1-0020 revised to condition_observed by post-record evidence (FC-decision-v1-0020@v1 preserved)
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'escaping', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=0, violation=2 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the up structure is exhausted and price develops an active down structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 (2 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 (SP-03)
  would change: a new confirmed up leg beyond the previous extreme
  would change: forecast FC-decision-v1-0020 revised to condition_observed by post-record evidence (FC-decision-v1-0020@v1 preserved)
model: provisional-unvalidated; support continuation=0/violation=2
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0057 — as of 2025-09-27 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-24T08:00:00+00:00-2025-09-24T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=9, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-24T08:00:00+00:00-2025-09-24T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-341
  why: SF-AVL-1h-decision-v1-341
  why: SF-AVL-15m-decision-v1-341
  opposed: SP-03 close violation of PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 (8 event(s))
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00 on the falsifying side (SP-03)
  would change: completed 4h bar CLOSE down of 111043 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00) at 2025-09-25 20:00:00+00:00
  would change: completed 4h bar CLOSE down of 111043 (SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00) at 2025-09-26 00:00:00+00:00
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00
model: provisional-unvalidated; support continuation=9/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0058 — as of 2025-09-28 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-26T12:00:00+00:00-2025-09-26T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=9, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-26T12:00:00+00:00-2025-09-26T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-347
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-347
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=9/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0059 — as of 2025-09-29 00:00:00+00:00 (UTC)  [historical-replay]
state: SCENARIO_DEVELOPING
primary working interpretation: I-primary — the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-26T12:00:00+00:00-2025-09-26T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
material alternatives: I-alt
named event: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
next discriminating observation: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00
  why: causal context at this as-of: {'direction': 'up', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=9, violation=4 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-primary: the completed task-scale leg moved up (C:F-K(k=5)|leg2025-09-26T12:00:00+00:00-2025-09-26T20:00:00+00:00); the current interpretation is that the origin-of-last-confirmed-leg = PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 continues to define the boundary of that claim at this as-of (research configuration)
  why: SF-DIR-decision-v1-353
  why: no SP-03 close-based violation of PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 is present in the available as-of history
  why: SF-AVL-1h-decision-v1-353
  opposed: a new confirmed down leg (F-K k=5 completion)
  opposed: a completed bar closing beyond PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00 on the falsifying side (SP-03)
  would change: a completed 4h bar closing on the falsifying side of PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00
  would change: E-CONTINUATION — a completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's own direction (SP-03 close-based binding of the leg-end reference; equality is not a crossing)
model: provisional-unvalidated; support continuation=9/violation=4
position status: absent | selection_quality = NOT_ESTABLISHED

---

### decision DEC-decision-v1-0060 — as of 2025-09-30 00:00:00+00:00 (UTC)  [historical-replay]
state: PRIOR_VIEW_WEAKENED_OR_INVALIDATED
primary working interpretation: I-alt — materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
material alternatives: I-primary
named event: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00
next discriminating observation: the next completed 4h leg's direction
  why: causal context at this as-of: {'direction': 'down', 'ref_status': 'selected', 'sp05': 'disjoint', 'fc_status': 'pending'}
  why: model evidence (training episodes in this context): continuation=11, violation=17 (ranked, provisional-unvalidated ranking)
  why: working interpretation I-alt: materially different alternative: the down structure is exhausted and price develops an active up structure from the current boundary
  opposed: SP-03 close violation of PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00 (8 event(s))
  opposed: continuation without a close-based violation of PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00 (SP-03)
  would change: a new confirmed down leg beyond the previous extreme
  would change: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00
model: provisional-unvalidated; support continuation=11/violation=17
position status: absent | selection_quality = NOT_ESTABLISHED

---

