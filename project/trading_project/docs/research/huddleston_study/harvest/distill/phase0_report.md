# PHASE 0 — verification report

## 0.1 Identity

| item | value |
|---|---|
| `git branch --show-current` at session start | `arena/e91e69b1-trading-bot` |
| `git rev-parse HEAD` at session start | `e06e22c9959a9e40e66f6b0053093ed09f424f91` (base commit; harvest folder was on disk but untracked) |
| HARVEST_HASH | `90629a8f97ec323d9c5430b61f0ca9b2d265f45b` |
| branch tip after `git merge --ff-only origin/arena/e91e69b1-trading-bot` | `782c9f6007065a041618b5e1552c3046f86c82a2` |

Before the fast-forward, all 443 harvest files present on disk were compared with
`git show 782c9f6:<path> | sha256sum`: **identical=443, diff=0, missing=0**. Only then was the
untracked copy removed and the branch fast-forwarded (no `reset --hard`, no `add -A`).

## 0.2 All 326 INDEX entries re-hashed from the commit

Method: for every record in `harvest/INDEX.jsonl`, `git show HARVEST_HASH:<path> | sha256sum` and
compare to the record's `sha256` field.

| result | count |
|---|---|
| match | **326** |
| mismatch | **0** |
| missing from commit | **0** |

## 0.3 Excerpt repositories re-downloaded at pinned commits

All **31** repositories that own excerpt files were downloaded from
`https://codeload.github.com/<full_name>/tar.gz/<commit_sha>` (HTTP 200 each; commit SHA taken from
`harvest/github/repos_meta.jsonl`) and unpacked to `/tmp/dr/<owner>__<repo>/`. Sizes ranged from
1.7 kB (`brainstrme/ICT-Trading`) to 82 MB (`Yousef-Diab/the-algorithm`).

## 0.4 Excerpt re-verification

Tool: `tools/verify_excerpts.py` (seed **20261106**, sample **100**, plus a full pass over all 1635 lines).
Checks per line: file exists → `sha256(file) == file_sha256` → quote ≤25 words → quote found in the file
after **lowercase + whitespace collapse only** (raw bytes first; if not found there, after the same
text extraction the harvest pass used: JSON string walk, HTML tag strip + entity unescape, pypdf text).

| set | lines | ok | ok in raw bytes | ok only after extraction | sha256 mismatch | file missing | quote not found | >25 words |
|---|---|---|---|---|---|---|---|---|
| all excerpt lines | 1635 | **1612** | 1062 | 550 | **0** | **0** | 23 | 0 |
| random sample (seed 20261106) | 100 | **99** | 67 | 32 | 0 | 0 | 1 | 0 |

### The 23 quote-not-found cases (all inspected)

They are **extraction artefacts, not fabricated text**: 15 come from PDFs where the text layer
re-wraps lines differently between runs (the Korean spec PDFs in `kwpark090288-pixel/ICT-AutoTrader`,
the study-book PDF in `alptheexplorer/ICT-2024-MENTORSHIP`, `aashutokalshi/pure-ict-nifty-trader`),
and 8 come from Markdown where the harvest quote joined a heading or table cells with spaces that the
raw file splits with newlines/pipes (`SrsBlack/ict-knowledge-library`,
`Rouen007/ict-2022-study-room`, `Kyle2077/ict-2022-skill-bundle`, `Yousef-Diab/the-algorithm`).
No file-level hash mismatch occurred, so no retrieved byte is in doubt; the quotes concerned are
**excluded from the claim corpus** in Phase 3 by construction (claims are built only from quotes that
pass the verifier on this session's re-download).
