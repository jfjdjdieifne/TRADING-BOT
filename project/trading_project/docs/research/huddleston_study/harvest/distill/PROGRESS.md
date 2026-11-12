# PROGRESS — distillation round (resume file)

Branch: `arena/e91e69b1-trading-bot`. HARVEST_HASH: `90629a8f97ec323d9c5430b61f0ca9b2d265f45b`.
Read everything through `git show HARVEST_HASH:<path>`. Never touch data dated 2025-05-01 or later.

| phase | status | artefact |
|---|---|---|
| 0 | DONE | `phase0_report.md`, `phase0_excerpt_verify.json` (326/326 hashes, 31 repos, seed 20261106) |
| 1 | DONE | `transcript_inventory.tsv` (490), `authorship_flags.tsv` (74) |
| 2 | DONE | `selection.md` (1392 files scored), `read_log.jsonl` (32 windows) |
| 3 | DONE | `claims.jsonl` (100 claims), `phase3_verify_report.md` (100/100 pass, 29 check-2 warnings) |
| 4 | DONE | `conflicts.jsonl` (8 conflicts / 18 options), `agreement.md` |
| 5 | DONE | `cards/` (13), `process_spec.md`, `OWNER_QUESTIONS.md` (12 gaps) |
| 6 | DONE | `knowledge_pack.jsonl` (111), `.michael_only.jsonl` (39), `.no_llm_flagged.jsonl` (64) |
| 7 | DONE | `AUDIT.md` |

## Tools
`tools/phase1_inventory.py`, `phase2_select.py`, `read_window.py`, `verify_claims.py`, `mkclaims.py`
(excerpt-repo claims, resolves files under /tmp/dr at pinned commits), `mkclaims_web.py` (harvest web records).

## If resuming
1. `/tmp/dr/` is ephemeral: re-download `https://codeload.github.com/<full_name>/tar.gz/<commit_sha>` from
   `harvest/github/repos_meta.jsonl`.
2. `python3 tools/verify_claims.py claims.jsonl --report phase3_verify_report.md` must stay at 100% pass.
3. To add claims: author JSON list, run `mk claims.py` (or `mkclaims_web.py` for `web/pages/*`), quotes <=25 words and
   verbatim from the file.
4. Open work: the 458 unread transcripts, the library's bias-invalidation / silver-bullet / breaker files, and the 12
   owner questions. Nothing further should be operationalised until the owner answers Q1–Q12.
