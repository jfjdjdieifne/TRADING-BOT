#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K7 B30 blind audit — deterministic sample builder (A1-01).

Reads ONLY LEDGER.json (READ_FULL chunk ids) and CHUNK_INDEX.jsonl (word counts),
and writes SAMPLE.json. Reproducible: python3 make_sample.py.

Rule (declared in PARAMETERS.md section A1 before any reading):
  - strata = top_folder of the chunk (from LEDGER.json per_file mapping)
  - strata processed in alphabetical order of top_folder
  - within each stratum: ids sorted lexicographically; a FRESH random.Random(20261108)
    is constructed per stratum and applied to the sorted list via random.sample
  - draws: 2 from 2023-ICT-Mentorship, 2 from 2022-ICT-Mentorship, 1 from 2023-Forex-Reviews
"""
import json
import os
import random

B30 = os.path.join(
    "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study",
    "harvest/distill/understanding/playbook/k7/phase1/B30",
)
SEED = 20261108
DRAWS = {
    "2022-ICT-Mentorship": 2,
    "2023-Forex-Reviews": 1,
    "2023-ICT-Mentorship": 2,
}


def main():
    led = json.load(open(os.path.join(B30, "LEDGER.json"), encoding="utf-8"))
    # chunk_id -> top_folder from per_file mapping
    folder = {}
    for pf in led["per_file"]:
        for cid in pf["chunk_ids_this_batch"]:
            folder[cid] = pf["top_folder"]
    read_full = []
    for pf in led["per_file"]:
        read_full.extend(pf["chunk_ids_read"])
    assert len(read_full) == led["chunks_read_full"] == 16, "population must be the 16 READ_FULL chunks"

    # word counts per chunk from CHUNK_INDEX.jsonl
    words = {}
    with open(
        "/home/user/TRADING-BOT/project/trading_project/docs/research/huddleston_study/"
        "harvest/distill/understanding/playbook/k7/CHUNK_INDEX.jsonl",
        encoding="utf-8",
    ) as f:
        for line in f:
            r = json.loads(line)
            words[r["chunk_id"]] = r["words"]

    strata = {}
    for cid in read_full:
        strata.setdefault(folder[cid], []).append(cid)

    out_strata = {}
    sample = []
    for s in sorted(strata):  # alphabetical stratum order
        ids = sorted(strata[s])
        rng = random.Random(SEED)
        pick = sorted(rng.sample(ids, DRAWS[s]))
        out_strata[s] = {
            "population": ids,
            "population_size": len(ids),
            "draw": DRAWS[s],
            "selected": pick,
            "selected_words": [words[c] for c in pick],
        }
        sample.extend(pick)
    sample.sort()

    out = {
        "batch_id": "B30",
        "audit": "K7 PHASE 1 BLIND AUDIT — stratified re-read sample",
        "date": "2026-11-08",
        "seed": SEED,
        "rng_rule": "fresh random.Random(seed) per stratum; lexicographically sorted chunk ids within stratum; random.sample; strata processed alphabetically; selections sorted ascending",
        "population": {
            "source": "k7/phase1/B30/LEDGER.json per_file chunk_ids_read",
            "size": len(read_full),
            "chunk_ids": sorted(read_full),
        },
        "strata": out_strata,
        "sample": sample,
        "words_in_sample": sum(words[c] for c in sample),
        "blindness_note": "Blindness is by instruction only and cannot be proven: the auditor is the same kind of AI as the original reader, in a session that later (after the audit records are pushed) sees the originals.",
        "integrity": "This file is committed BEFORE any sample chunk text is read.",
    }
    dst = os.path.join(B30, "audit", "SAMPLE.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", dst)
    print("sample:", sample)
    for s, v in out_strata.items():
        print(f"  {s}: {v['population_size']} -> {v['selected']}")


if __name__ == "__main__":
    main()
