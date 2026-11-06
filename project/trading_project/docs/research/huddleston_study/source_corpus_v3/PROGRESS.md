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
| 3 cards | DONE | 32 cards (24 grounded, 8 NOT_FOUND), 15 relations, 206 NOT_IN_SOURCES fields |
| 4 process spec | DONE | 8 steps, every step cited; differences listed not merged; 20 owner questions |
| 5 engine design | NOT_STARTED | |
| 6 audit | DONE | AUDIT.md; verifier re-run 54/54/0; contamination log recorded |

## Next step

Round complete. Nothing is pending except the 20 owner questions in OWNER_QUESTIONS.md.

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
- phase 2: `42bebbf6b9b4a9f3f90dbf899259b3b709693fae`
- phase 3: `c678c18de7808e5ad7a4717ee4a59d0794789e5c`
- phases 4-6: see `git log -1 --format=%H`
