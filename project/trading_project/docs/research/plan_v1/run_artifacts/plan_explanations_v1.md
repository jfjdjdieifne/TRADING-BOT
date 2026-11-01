# Contextual trade-plan layer V1

Hypothetical analytical records only — NOT orders.  selection_quality = NOT_ESTABLISHED.

### PLAN-plan-v1-0001 — continuation scenario (up) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-08-11 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0010 | analysis: AN-9f5d9cfb4329 v10
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00', 'level': 112650.0, 'side': 'low', 'falsifying_side': 'down', 'bar': 27} end={'id': 'PTC:F-K(k=5)|high@2025-08-08T04:00:00+00:00', 'level': 117630.0, 'side': 'high', 'continuation_side': 'up', 'bar': 42}
  events observed: {'entry_bars': [54], 'invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0002 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v3 revised from PLAN-plan-v1-0002@v2)
as of: 2025-08-15 00:00:00+00:00
state detail: the invalidation condition was observed at bar 82 after the hypothetical entry (bar 76) and before the objective
decision: DEC-plan-v1-0014 | analysis: AN-9f5d9cfb4329 v14
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-11T08:00:00+00:00', 'level': 122335.16, 'side': 'high', 'falsifying_side': 'up', 'bar': 61} end={'id': 'PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00', 'level': 118050.11, 'side': 'low', 'continuation_side': 'down', 'bar': 65}
  events observed: {'entry_bars': [76, 78], 'invalidation_bars': [82], 'objective_seen': True, 'new_entry_bars': [78], 'new_invalidation_bars': [82]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0003 — continuation scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-16 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0015 | analysis: AN-9f5d9cfb4329 v15
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00', 'level': 118050.11, 'side': 'low', 'falsifying_side': 'down', 'bar': 65} end={'id': 'PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00', 'level': 124474.0, 'side': 'high', 'continuation_side': 'up', 'bar': 78}
  events observed: {'entry_bars': [], 'invalidation_bars': [82]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0004 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v2 revised from PLAN-plan-v1-0004@v1)
as of: 2025-08-19 00:00:00+00:00
state detail: the invalidation condition was observed at bar 102 before any entry (pre-record events are never re-reported as post-record)
decision: DEC-plan-v1-0018 | analysis: AN-9f5d9cfb4329 v18
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-14T04:00:00+00:00', 'level': 124474.0, 'side': 'high', 'falsifying_side': 'up', 'bar': 78} end={'id': 'PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00', 'level': 116803.99, 'side': 'low', 'continuation_side': 'down', 'bar': 88}
  events observed: {'entry_bars': [], 'invalidation_bars': [102], 'objective_seen': False, 'new_entry_bars': [], 'new_invalidation_bars': [102]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0005 — continuation scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-19 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0018 | analysis: AN-9f5d9cfb4329 v18
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00', 'level': 116803.99, 'side': 'low', 'falsifying_side': 'down', 'bar': 88} end={'id': 'PTC:F-K(k=5)|high@2025-08-17T16:00:00+00:00', 'level': 118575.0, 'side': 'high', 'continuation_side': 'up', 'bar': 99}
  events observed: {'entry_bars': [], 'invalidation_bars': [102]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0006 — continuation scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-20 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0019 | analysis: AN-9f5d9cfb4329 v19
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00', 'level': 116803.99, 'side': 'low', 'falsifying_side': 'down', 'bar': 88} end={'id': 'PTC:F-K(k=5)|high@2025-08-17T16:00:00+00:00', 'level': 118575.0, 'side': 'high', 'continuation_side': 'up', 'bar': 99}
  events observed: {'entry_bars': [], 'invalidation_bars': [102]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0007 — continuation scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-21 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0020 | analysis: AN-9f5d9cfb4329 v20
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-15T20:00:00+00:00', 'level': 116803.99, 'side': 'low', 'falsifying_side': 'down', 'bar': 88} end={'id': 'PTC:F-K(k=5)|high@2025-08-17T16:00:00+00:00', 'level': 118575.0, 'side': 'high', 'continuation_side': 'up', 'bar': 99}
  events observed: {'entry_bars': [], 'invalidation_bars': [102]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0008 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-26 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0025 | analysis: AN-9f5d9cfb4329 v25
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00', 'level': 117429.05, 'side': 'high', 'falsifying_side': 'up', 'bar': 130} end={'id': 'PTC:F-K(k=5)|low@2025-08-23T16:00:00+00:00', 'level': 114560.0, 'side': 'low', 'continuation_side': 'down', 'bar': 135}
  events observed: {'entry_bars': [], 'invalidation_bars': [141]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0009 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-27 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0026 | analysis: AN-9f5d9cfb4329 v26
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00', 'level': 117429.05, 'side': 'high', 'falsifying_side': 'up', 'bar': 130} end={'id': 'PTC:F-K(k=5)|low@2025-08-23T16:00:00+00:00', 'level': 114560.0, 'side': 'low', 'continuation_side': 'down', 'bar': 135}
  events observed: {'entry_bars': [], 'invalidation_bars': [141]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0010 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-28 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0027 | analysis: AN-9f5d9cfb4329 v27
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00', 'level': 117429.05, 'side': 'high', 'falsifying_side': 'up', 'bar': 130} end={'id': 'PTC:F-K(k=5)|low@2025-08-23T16:00:00+00:00', 'level': 114560.0, 'side': 'low', 'continuation_side': 'down', 'bar': 135}
  events observed: {'entry_bars': [], 'invalidation_bars': [141]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0011 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-08-29 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0028 | analysis: AN-9f5d9cfb4329 v28
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00', 'level': 117429.05, 'side': 'high', 'falsifying_side': 'up', 'bar': 130} end={'id': 'PTC:F-K(k=5)|low@2025-08-23T16:00:00+00:00', 'level': 114560.0, 'side': 'low', 'continuation_side': 'down', 'bar': 135}
  events observed: {'entry_bars': [], 'invalidation_bars': [141]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0012 — reversal scenario (up) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v3 revised from PLAN-plan-v1-0012@v2)
as of: 2025-09-14 00:00:00+00:00
state detail: the objective event (one completed confirmed leg in the up direction after the entry bar) is now visible; hypothetical outcome recorded for evaluation (not a profit claim)
decision: DEC-plan-v1-0044 | analysis: AN-9f5d9cfb4329 v44
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-28T16:00:00+00:00', 'level': 113485.9, 'side': 'high', 'falsifying_side': 'up', 'bar': 165} end={'id': 'PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00', 'level': 107350.1, 'side': 'low', 'continuation_side': 'down', 'bar': 174}
  events observed: {'entry_bars': [243, 246, 252, 258], 'invalidation_bars': [], 'objective_seen': True, 'new_entry_bars': [258], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0013 — continuation scenario (up) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v3 revised from PLAN-plan-v1-0013@v2)
as of: 2025-09-05 00:00:00+00:00
state detail: the objective event (one completed confirmed leg in the up direction after the entry bar) is now visible; hypothetical outcome recorded for evaluation (not a profit claim)
decision: DEC-plan-v1-0035 | analysis: AN-9f5d9cfb4329 v35
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-08-30T04:00:00+00:00', 'level': 107350.1, 'side': 'low', 'falsifying_side': 'down', 'bar': 174} end={'id': 'PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00', 'level': 109480.02, 'side': 'high', 'continuation_side': 'up', 'bar': 180}
  events observed: {'entry_bars': [192, 198, 204], 'invalidation_bars': [], 'objective_seen': True, 'new_entry_bars': [204], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0014 — continuation scenario (down) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-03 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0033 | analysis: AN-9f5d9cfb4329 v33
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00', 'level': 109480.02, 'side': 'high', 'falsifying_side': 'up', 'bar': 180} end={'id': 'PTC:F-K(k=5)|low@2025-09-01T08:00:00+00:00', 'level': 107255.0, 'side': 'low', 'continuation_side': 'down', 'bar': 187}
  events observed: {'entry_bars': [], 'invalidation_bars': [192]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0015 — continuation scenario (down) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-04 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0034 | analysis: AN-9f5d9cfb4329 v34
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-08-31T04:00:00+00:00', 'level': 109480.02, 'side': 'high', 'falsifying_side': 'up', 'bar': 180} end={'id': 'PTC:F-K(k=5)|low@2025-09-01T08:00:00+00:00', 'level': 107255.0, 'side': 'low', 'continuation_side': 'down', 'bar': 187}
  events observed: {'entry_bars': [], 'invalidation_bars': [192]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0016 — continuation scenario (down) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-06 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0036 | analysis: AN-9f5d9cfb4329 v36
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-03T20:00:00+00:00', 'level': 112575.27, 'side': 'high', 'falsifying_side': 'up', 'bar': 202} end={'id': 'PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00', 'level': 109329.12, 'side': 'low', 'continuation_side': 'down', 'bar': 207}
  events observed: {'entry_bars': [], 'invalidation_bars': [211]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0017 — continuation scenario (up) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v3 revised from PLAN-plan-v1-0017@v2)
as of: 2025-09-14 00:00:00+00:00
state detail: the objective event (one completed confirmed leg in the up direction after the entry bar) is now visible; hypothetical outcome recorded for evaluation (not a profit claim)
decision: DEC-plan-v1-0044 | analysis: AN-9f5d9cfb4329 v44
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-04T16:00:00+00:00', 'level': 109329.12, 'side': 'low', 'falsifying_side': 'down', 'bar': 207} end={'id': 'PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00', 'level': 113384.62, 'side': 'high', 'continuation_side': 'up', 'bar': 213}
  events observed: {'entry_bars': [243, 246, 252, 258], 'invalidation_bars': [], 'objective_seen': True, 'new_entry_bars': [258], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0018 — continuation scenario (down) run_context=historical-replay
state: INVALIDATED (v2 revised from PLAN-plan-v1-0018@v1)
as of: 2025-09-11 00:00:00+00:00
state detail: the invalidation condition was observed at bar 243 before any entry (pre-record events are never re-reported as post-record)
decision: DEC-plan-v1-0041 | analysis: AN-9f5d9cfb4329 v41
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00', 'level': 113384.62, 'side': 'high', 'falsifying_side': 'up', 'bar': 213} end={'id': 'PTC:F-K(k=5)|low@2025-09-06T20:00:00+00:00', 'level': 109977.0, 'side': 'low', 'continuation_side': 'down', 'bar': 220}
  events observed: {'entry_bars': [], 'invalidation_bars': [243], 'objective_seen': False, 'new_entry_bars': [], 'new_invalidation_bars': [243]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0019 — reversal scenario (up) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-09-11 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0041 | analysis: AN-9f5d9cfb4329 v41
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-09T08:00:00+00:00', 'level': 113293.29, 'side': 'high', 'falsifying_side': 'up', 'bar': 235} end={'id': 'PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00', 'level': 110766.66, 'side': 'low', 'continuation_side': 'down', 'bar': 237}
  events observed: {'entry_bars': [243], 'invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0020 — continuation scenario (up) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v3 revised from PLAN-plan-v1-0020@v2)
as of: 2025-09-20 00:00:00+00:00
state detail: the objective event (one completed confirmed leg in the up direction after the entry bar) is now visible; hypothetical outcome recorded for evaluation (not a profit claim)
decision: DEC-plan-v1-0050 | analysis: AN-9f5d9cfb4329 v50
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-09T16:00:00+00:00', 'level': 110766.66, 'side': 'low', 'falsifying_side': 'down', 'bar': 237} end={'id': 'PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00', 'level': 116665.63, 'side': 'high', 'continuation_side': 'up', 'bar': 256}
  events observed: {'entry_bars': [280, 283, 288, 294], 'invalidation_bars': [], 'objective_seen': True, 'new_entry_bars': [294], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0021 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v2 revised from PLAN-plan-v1-0021@v1)
as of: 2025-09-16 00:00:00+00:00
state detail: the invalidation condition was observed at bar 272 before any entry (pre-record events are never re-reported as post-record)
decision: DEC-plan-v1-0046 | analysis: AN-9f5d9cfb4329 v46
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00', 'level': 116665.63, 'side': 'high', 'falsifying_side': 'up', 'bar': 256} end={'id': 'PTC:F-K(k=5)|low@2025-09-13T20:00:00+00:00', 'level': 115127.27, 'side': 'low', 'continuation_side': 'down', 'bar': 262}
  events observed: {'entry_bars': [], 'invalidation_bars': [272], 'objective_seen': False, 'new_entry_bars': [], 'new_invalidation_bars': [272]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0022 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-16 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0046 | analysis: AN-9f5d9cfb4329 v46
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-12T20:00:00+00:00', 'level': 116665.63, 'side': 'high', 'falsifying_side': 'up', 'bar': 256} end={'id': 'PTC:F-K(k=5)|low@2025-09-13T20:00:00+00:00', 'level': 115127.27, 'side': 'low', 'continuation_side': 'down', 'bar': 262}
  events observed: {'entry_bars': [], 'invalidation_bars': [272]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0023 — reversal scenario (up) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-09-17 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0047 | analysis: AN-9f5d9cfb4329 v47
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-15T08:00:00+00:00', 'level': 116757.99, 'side': 'high', 'falsifying_side': 'up', 'bar': 271} end={'id': 'PTC:F-K(k=5)|low@2025-09-15T16:00:00+00:00', 'level': 114384.0, 'side': 'low', 'continuation_side': 'down', 'bar': 273}
  events observed: {'entry_bars': [280], 'invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0024 — reversal scenario (down) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v3 revised from PLAN-plan-v1-0024@v2)
as of: 2025-09-25 00:00:00+00:00
state detail: the objective event (one completed confirmed leg in the down direction after the entry bar) is now visible; hypothetical outcome recorded for evaluation (not a profit claim)
decision: DEC-plan-v1-0055 | analysis: AN-9f5d9cfb4329 v55
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-17T20:00:00+00:00', 'level': 114720.81, 'side': 'low', 'falsifying_side': 'down', 'bar': 286} end={'id': 'PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00', 'level': 117900.0, 'side': 'high', 'continuation_side': 'up', 'bar': 292}
  events observed: {'entry_bars': [312, 318, 324], 'invalidation_bars': [], 'objective_seen': True, 'new_entry_bars': [324], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0025 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v2 revised from PLAN-plan-v1-0025@v1)
as of: 2025-09-23 00:00:00+00:00
state detail: the invalidation condition was observed at bar 312 before any entry (pre-record events are never re-reported as post-record)
decision: DEC-plan-v1-0053 | analysis: AN-9f5d9cfb4329 v53
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00', 'level': 117900.0, 'side': 'high', 'falsifying_side': 'up', 'bar': 292} end={'id': 'PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00', 'level': 115100.0, 'side': 'low', 'continuation_side': 'down', 'bar': 299}
  events observed: {'entry_bars': [], 'invalidation_bars': [312], 'objective_seen': False, 'new_entry_bars': [], 'new_invalidation_bars': [312]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0026 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-23 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0053 | analysis: AN-9f5d9cfb4329 v53
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00', 'level': 117900.0, 'side': 'high', 'falsifying_side': 'up', 'bar': 292} end={'id': 'PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00', 'level': 115100.0, 'side': 'low', 'continuation_side': 'down', 'bar': 299}
  events observed: {'entry_bars': [], 'invalidation_bars': [312]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0027 — reversal scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-24 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0054 | analysis: AN-9f5d9cfb4329 v54
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-18T20:00:00+00:00', 'level': 117900.0, 'side': 'high', 'falsifying_side': 'up', 'bar': 292} end={'id': 'PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00', 'level': 115100.0, 'side': 'low', 'continuation_side': 'down', 'bar': 299}
  events observed: {'entry_bars': [], 'invalidation_bars': [312]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0028 — reversal scenario (up) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-09-25 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0055 | analysis: AN-9f5d9cfb4329 v55
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-20T00:00:00+00:00', 'level': 115100.0, 'side': 'low', 'falsifying_side': 'down', 'bar': 299} end={'id': 'PTC:F-K(k=5)|high@2025-09-23T16:00:00+00:00', 'level': 113290.5, 'side': 'high', 'continuation_side': 'down', 'bar': 321}
  events observed: {'entry_bars': [312], 'invalidation_bars': [322]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0029 — reversal scenario (down) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-09-26 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0056 | analysis: AN-9f5d9cfb4329 v56
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00', 'level': 111042.66, 'side': 'low', 'falsifying_side': 'down', 'bar': 325} end={'id': 'PTC:F-K(k=5)|high@2025-09-24T20:00:00+00:00', 'level': 113940.0, 'side': 'high', 'continuation_side': 'up', 'bar': 328}
  events observed: {'entry_bars': [334], 'invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0030 — continuation scenario (up) run_context=historical-replay
state: INVALIDATED (v1)
as of: 2025-09-27 00:00:00+00:00
state detail: the invalidation condition is already present in the as-of history before any entry (past event)
decision: DEC-plan-v1-0057 | analysis: AN-9f5d9cfb4329 v57
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-24T08:00:00+00:00', 'level': 111042.66, 'side': 'low', 'falsifying_side': 'down', 'bar': 325} end={'id': 'PTC:F-K(k=5)|high@2025-09-24T20:00:00+00:00', 'level': 113940.0, 'side': 'high', 'continuation_side': 'up', 'bar': 328}
  events observed: {'entry_bars': [], 'invalidation_bars': [334]}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0031 — continuation scenario (up) run_context=historical-replay
state: HYPOTHETICAL_ENTRY_MET (v2 revised from PLAN-plan-v1-0031@v1)
as of: 2025-09-29 00:00:00+00:00
state detail: the entry condition was observed at bar 352 after the plan record (observed_before_record=False) — a HYPOTHETICAL entry, not an order
decision: DEC-plan-v1-0059 | analysis: AN-9f5d9cfb4329 v59
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding of the leg-end reference)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|low@2025-09-26T12:00:00+00:00', 'level': 108620.07, 'side': 'low', 'falsifying_side': 'down', 'bar': 338} end={'id': 'PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00', 'level': 110300.0, 'side': 'high', 'continuation_side': 'up', 'bar': 340}
  events observed: {'entry_bars': [352], 'invalidation_bars': [], 'objective_seen': False, 'new_entry_bars': [352], 'new_invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

### PLAN-plan-v1-0032 — reversal scenario (up) run_context=historical-replay
state: CONDITION_OBSERVED (v1)
as of: 2025-09-30 00:00:00+00:00
state detail: the entry condition was already observed in the available history before this record (observed_before_record=True) — it is NOT described as a pre-event plan and no hypothetical entry is claimed
decision: DEC-plan-v1-0060 | analysis: AN-9f5d9cfb4329 v60
  entry [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the falsifier reference level on its falsifying side (SP-03 close violation — the event that supports the reversal scenario)
    source note: ICT entry technique exists (SRC-EX-01) but is NOT implemented: G-OB-P not runnable (P-N/P-W unset; owner policy required; none invented)
  invalidation [declared-research-configuration; engineering-interpretation]: the first completed task-scale bar whose CLOSE is strictly beyond the last confirmed leg's END extreme in the leg's direction (SP-03 close binding — the event that supports the continuation scenario and voids the reversal plan)
    source note: SRC-EX-01 stop concept (directly-stated) + SRC-EX-02: ICT-primary invalidation-by-close NOT in primary text (P-K)
  objective [declared-research-configuration; engineering-interpretation]: one completed, causally confirmed task-scale F-K leg in the scenario direction whose knowable time is after the entry bar
    source note: SRC-EX-03: no target definition in the verified primary text read
  levels: ref={'id': 'PTC:F-K(k=5)|high@2025-09-26T20:00:00+00:00', 'level': 110300.0, 'side': 'high', 'falsifying_side': 'up', 'bar': 340} end={'id': 'PTC:F-K(k=5)|low@2025-09-28T16:00:00+00:00', 'level': 109189.99, 'side': 'low', 'continuation_side': 'down', 'bar': 351}
  events observed: {'entry_bars': [352], 'invalidation_bars': []}
  position status: absent | selection_quality = NOT_ESTABLISHED
  hypothetical analytical record — NOT an order
---

## No-justified-plan records (specific missing evidence)

- **2025-08-02 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is UNRESOLVED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved; completed task-scale leg with a resolved end extreme — next: the first completed task-scale leg's existence and direction
- **2025-08-03 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is UNRESOLVED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved; completed task-scale leg with a resolved end extreme — next: the first completed task-scale leg's existence and direction
- **2025-08-04 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is UNRESOLVED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved; completed task-scale leg with a resolved end extreme — next: the first completed task-scale leg's existence and direction
- **2025-08-05 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is UNRESOLVED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved; completed task-scale leg with a resolved end extreme — next: the first completed task-scale leg's existence and direction
- **2025-08-06 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-03T04:00:00+00:00
- **2025-08-07 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00
- **2025-08-08 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-04T20:00:00+00:00
- **2025-08-09 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
- **2025-08-10 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-05T16:00:00+00:00
- **2025-08-15 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-12T00:00:00+00:00
- **2025-08-22 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved — next: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
- **2025-08-23 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved — next: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
- **2025-08-24 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved — next: reference resolution (AI: intrabar high/low order of the selected reference is unavailable (endpoint evidence: none); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
- **2025-08-25 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-08-22T20:00:00+00:00
- **2025-08-30 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is PRIOR_VIEW_WEAKENED_OR_INVALIDATED: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|low@2025-08-26T04:00:00+00:00
- **2025-09-05 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is EVENT_OCCURRED: model does not strictly distinguish the scenarios / input insufficient); precise falsifier reference (reference_status=unresolved — next: reference resolution (AI: intrabar high/low order of the selected reference is constrained (endpoint evidence: constrained:close-at-high); tick data (MO) or a declared ordering policy needed) or the next completed 4h bar's CLOSE
- **2025-09-09 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
- **2025-09-10 00:00:00+00:00** — missing: evidence-supported directional preference (the decision is NO_EDGE: model does not strictly distinguish the scenarios / input insufficient) — next: the next completed 4h bar's CLOSE relative to PTC:F-K(k=5)|high@2025-09-05T16:00:00+00:00
