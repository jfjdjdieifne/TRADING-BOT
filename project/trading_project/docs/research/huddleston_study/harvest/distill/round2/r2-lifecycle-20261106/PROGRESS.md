# PROGRESS — round 2 (r2-lifecycle-20261106)

Base commit `462bb61068e6b184478b831dd8295a189dfeabc5`. Status: **complete** for the assignment block given.

| phase | artefact | count |
|---|---|---|
| A search | `search_log.tsv`, `search_report.txt` | 1,871 files, 13 questions |
| B read | `read_log.jsonl` | 21 windows (±200 words each side) |
| C claims | `claims_r2.jsonl`, `verify_r2_final.md` | 50 claims, 50/50 pass |
| D answers | `answers.md`, `conflicts_r2.jsonl` | 13 questions, 4 conflicts / 18 options |
| E examples | `worked_examples.jsonl`, `sequences/*.md` | 5 examples, 3 sequences |
| F fix-ups | `corrections.md` | 5 self-corrections, 4 findings about base files |

## Resume notes
- `/tmp/dr` holds the pinned re-downloads (ephemeral). Re-fetch with
  `https://codeload.github.com/<full_name>/tar.gz/<commit_sha>` from `harvest/github/repos_meta.jsonl`.
- Tools: `tools/r2_common.py`, `r2_search.py`, `r2_windows.py`, `r2_claims.py` (verifier is reused from
  `distill/tools/verify_claims.py`, unmodified).
- Next candidates if this continues: QI needs a corpus-wide `choch` sweep with a proper regex (the current grep hit
  code repos); QF needs the 2023 killzone lectures read as full files; the exit leg needs the Months 5 and 11 model files.
