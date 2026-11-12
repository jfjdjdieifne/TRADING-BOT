# RESUME — state of this harvest (for a zero-context session)

Last updated: 2026-11-06.

## How to use this file

If this run died, read this file first, then `REACHABILITY.md`, then `LICENSE_POLICY.md`, then `INDEX.jsonl` (one JSON object per stored object). Everything committed is verifiable with `git show origin/arena/e91e69b1-trading-bot:<path> | sha256sum` against the `sha256` field in `INDEX.jsonl`.

## Where everything lives

Everything in this task is inside
`project/trading_project/docs/research/huddleston_study/harvest/`.
No file outside this folder was created, modified or deleted.

```
harvest/
  REACHABILITY.md      step 0: what the environment can and cannot reach, exact errors
  LICENSE_POLICY.md    how the licence rule was applied (FULL vs EXCERPT tiers)
  INDEX.jsonl          one record per stored object (id, url, site, author, title, date,
                       method, bytes, sha256, has_text, completeness, source_kind, evidence_quote)
  MANIFEST.md          counts per source_kind x completeness, gaps
  COVERAGE.md          mechanical keyword counts over stored full-text files
  DEDUPE.md            identical sha256 across stored files
  ERRORS.md            every URL tried with exact result; licence-withheld list
  UNFETCHED_LEADS.md   YouTube URLs seen but deliberately NOT fetched
  RESUME.md            this file
  search/*.json        raw GitHub search API responses (30 queries)
  github/repos_meta.jsonl   one line per repository: full_name, html_url, default_branch,
                            license, size, pushed_at, description, commit_sha, stars
  github/_meta/*.json  raw git tree API responses per repository
  github/inventory.jsonl    every candidate text file in every repo: path, bytes, sha256, stored?
  github/_excerpts/*.jsonl  licence-restricted quotes (<=25 words each, <=3 per file)
  github/<owner>__<repo>@<sha8>/<path>  full text, byte-exact, only for permissively licensed repos
  web/EXCERPTS_*.md    web pages retrieved with the session fetcher (quotes + URLs)
```

## Channel situation (why the harvest looks like this)

- The shell can only reach `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`. Everything else: TLS `SSL_ERROR_SYSCALL`.
- The session's `fetch_page` / `web_search` tools CAN read arbitrary web pages (server-side proxy). They return converted Markdown, no HTTP status codes, no raw bytes.
- Therefore: GitHub material is byte-exact and hash-verified; web material is quotes of the fetcher's Markdown rendering.

## Progress log

- [x] Step 0 reachability, `REACHABILITY.md`, committed and pushed first.
- [x] 30 GitHub search queries, raw JSON saved.
- [x] 74 repositories: metadata + pinned commit SHA + recursive tree + tarball + per-file sha256 (`github/inventory.jsonl`, 2700+ lines).
- [x] Full text stored for 37 permissively licensed repos; quotes extracted for the rest.
- [x] `INDEX.jsonl`, `MANIFEST.md`, `COVERAGE.md`, `DEDUPE.md`, `ERRORS.md`, `UNFETCHED_LEADS.md`.
- [x] Web harvest with `fetch_page`: 10 page records in `web/pages/` (6 substantive article bodies, 1 partial, 2 no-content, 1 index-only). Reddit/forexfactory/own-site blocks recorded in `ERRORS.md` section D.
- [x] Final integrity check of `project/trading_project/src/trading_system/research/information_time.py`: sha256 `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`, size 12216 — unchanged.
- State at last commit: 32344540103eade3eb64f4d4223f10f2b1d341ac

## Rules that must not be broken by a resuming session

1. Never write text from memory. Every stored string must come from a retrieved response. If a page could not be retrieved, log it in `ERRORS.md`.
2. Never fetch YouTube pages or captions; log the URL in `UNFETCHED_LEADS.md`.
3. Keep everything inside `harvest/`. Do not touch `project/trading_project/src/`, `project/trading_project/data/`, or any tracked file outside `harvest/`.
4. Commit and push by explicit path after each batch; then `git fetch origin` and compare `git rev-parse origin/arena/e91e69b1-trading-bot` with `HEAD`.
5. No `git reset --hard`, no `git add -A`.
