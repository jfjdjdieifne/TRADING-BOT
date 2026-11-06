# PROGRESS — knowledge distillation round (resume file)

Branch: `arena/e91e69b1-trading-bot`. Session start HEAD was `e06e22c` (the base commit) with the
harvest folder present on disk but untracked; `git merge --ff-only origin/arena/e91e69b1-trading-bot`
fast-forwarded the branch to `782c9f6` after verifying that all 443 harvest files on disk were
byte-identical to that commit (`git show <commit>:<path> | sha256sum` per file: identical=443, diff=0).

- **HARVEST_HASH = `90629a8f97ec323d9c5430b61f0ca9b2d265f45b`** (`git log --all -1 --format=%H -- .../harvest/INDEX.jsonl`).
  The branch tip `782c9f6` adds only `harvest/FILES_CREATED.txt` on top of it.
- All harvest content is read through `git show HARVEST_HASH:<path>` / `git show 782c9f6:<path>`.

## Phase status

| phase | state | artefacts |
|---|---|---|
| 0 verify | DONE | `phase0_report.md`, `phase0_excerpt_verify.json`, `tools/verify_excerpts.py` |
| 1 inventory | TODO | `transcript_inventory.tsv`, `authorship_flags.tsv` |
| 2 selection | TODO | `selection.md`, `/tmp` window dumps |
| 3 claims | TODO | `claims.jsonl`, `tools/verify_claims.py`, `phase3_verify_report.md` |
| 4 conflicts | TODO | `conflicts.jsonl`, `agreement.md` |
| 5 cards/process/questions | TODO | `cards/*.md`, `process_spec.md`, `OWNER_QUESTIONS.md` |
| 6 knowledge pack | TODO | `knowledge_pack*.jsonl` |
| 7 audit | TODO | `AUDIT.md` |

## Resume instructions (zero-context)

1. `git fetch --all`; `HARVEST_HASH=90629a8`; read harvest files via `git show`.
2. Re-download excerpt repos to `/tmp/dr/<owner>__<repo>` from
   `https://codeload.github.com/<full_name>/tar.gz/<commit_sha>` (commit SHAs are in
   `harvest/github/repos_meta.jsonl`). If `/tmp` is gone, re-run:
   `python3 project/trading_project/docs/research/huddleston_study/harvest/distill/tools/verify_excerpts.py`
   after downloading; it reports missing repos explicitly.
3. Only quotes that pass `tools/verify_claims.py` may appear in claims/cards/pack.

## Hard rules in force

- No invention; every statement traced to a verified quote; temptations logged in `AUDIT.md`.
- Never store full text of EXCERPT repos; quotes ≤25 words + pinned commit + path only.
- Nothing outside `harvest/distill/` is created or modified.
