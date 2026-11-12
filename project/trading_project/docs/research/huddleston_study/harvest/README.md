# huddleston_study / harvest — what this folder is

Collected **text only** about the ICT / Inner Circle Trader / Smart Money Concepts trading method, retrieved from the open internet (YouTube excluded) on 2026-11-06. No interpretation, no summaries, no extracted rules, no conclusions: retrieval, labelling and indexing only.

Read in this order:

1. `REACHABILITY.md` — what the environment can reach, with exact errors.
2. `LICENSE_POLICY.md` — why some sources are full text and others only ≤25-word quotes.
3. `INDEX.jsonl` — one record per stored object (URL, date, method, bytes, sha256, completeness, source_kind, evidence quote).
4. `MANIFEST.md` — counts, and what could not be retrieved.
5. `COVERAGE.md` — mechanical keyword counts over the stored files.
6. `DEDUPE.md`, `ERRORS.md`, `UNFETCHED_LEADS.md`, `RESUME.md`.

Folders:

- `github/<owner>__<repo>@<sha8>/…` — byte-exact text files from permissively licensed GitHub repositories.
- `github/_excerpts/<owner>__<repo>@<sha8>.jsonl` — quotes only, for repositories that grant no permissive licence or host third-party course material.
- `github/inventory.jsonl` — path, bytes and sha256 of every candidate text file in every inspected repository.
- `github/_meta/` — raw GitHub git-tree API responses per repository.
- `search/` — raw GitHub search API responses.
- `web/pages/` — web records: URL, title, retrieval date, method and verbatim quotes.

Nothing here was written from memory. If a source could not be fetched, that is stated in `ERRORS.md` and no text from it appears anywhere in this folder.
