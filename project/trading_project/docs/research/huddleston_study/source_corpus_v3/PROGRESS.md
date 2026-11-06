# PROGRESS — source_corpus_v3 (ICT/Huddleston source-grounded understanding spec)

Branch: `arena/e6974afe-trading-bot`
Pin (last known good): `a3089e335e34b455a5bcc03cc936e6195b4401d2`

## Hard rule in force

No statement may appear in any output unless it traces to a verbatim quote in a stored source file.
Model memory about ICT / Michael Huddleston is treated as contaminated and is NOT used — not for
naming concepts, not for organising, not for filling gaps. Missing material is recorded as a gap.

## Phase status

| phase | status | note |
|---|---|---|
| 0 setup | DONE | HEAD == pin == origin; worktree clean; no `reset` of any kind needed |
| 1 collection | DONE | 14 PRIMARY files / 7 source_ids indexed; 0 SECONDARY, 0 TERTIARY; no new retrieval possible |
| 2 claims | DONE | 54 claims, 54 verified, 0 failed, 0 removed |
| 3 cards | IN_PROGRESS | |
| 4 process spec | NOT_STARTED | |
| 5 engine design | NOT_STARTED | |
| 6 audit | NOT_STARTED | |

## Next step

Phase 3: build concept cards from claims only, then relations.jsonl.

## Resume instructions for a fresh session

1. `git branch --show-current`, `git fetch origin`, compare HEAD with the last commit hash below.
2. Read this file, then `MANIFEST.md`, then `INDEX.jsonl`.
3. PRIMARY text lives in `primary/<source_id>/`. Claims live in `claims.jsonl`. The verifier is
   `tools/verify_claims.py`; run it before trusting any claim.
4. Nothing required by this study lives only in `/tmp`.

## Last commit hash for this corpus

`a3089e335e34b455a5bcc03cc936e6195b4401d2` (phase 0 baseline; updated at each phase below)

## Commit log (this round)

- phase 0 baseline: `a3089e335e34b455a5bcc03cc936e6195b4401d2`
- phase 1: `065c2d1353b4488fae06b230528d9b273adc1880`
