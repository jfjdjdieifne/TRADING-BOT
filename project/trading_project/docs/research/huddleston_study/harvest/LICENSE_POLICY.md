# LICENSE_POLICY — how the licence rule was applied

Source of the rule: the task brief ("The repo is PUBLIC. Respect licences ..."). This file records exactly how it was operationalised, because it determines what is stored as full text and what is stored only as short quotes.

## Tier FULL (full text stored verbatim)

A GitHub repository is stored as full text **only if** a `LICENSE`/`LICENCE`/`COPYING` file in the repository grants a permissive licence: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense, CC0, CC-BY/CC-BY-SA.

The licence was read from the licence file in the downloaded tarball, not from the GitHub API's `spdx_id`. That mattered: the API reports `NOASSERTION` (or `null`) for several repositories that do contain a plain MIT `LICENSE` file (e.g. `SaiStyles/ICT-2022-study`, `SoCloseSociety/TradeBobbyTerminal`, `NadirAliOfficial/STAR-EA-v11.20`, `cecehj/ICT-Learning-Hub`). Those were stored as FULL after reading the file.

## Tier EXCERPT (no full text; short quotes only)

Full text is **not** stored when:

- there is no licence file in the repository (default copyright — most of the ICT notes/transcript repositories), or
- the licence is copyleft and therefore outside the permissive list used here (GPL-3.0: `newsqlguru/ict-index`, `tickets2themoon/ICTFVG`; MPL-2.0: `Sagar4575/Sessions-and-Killzones`, `samuelharting/bandz-po3-stdv-cisd`, `cedinvest/sm-radar-pine`, `jericoquek/MTF-Liquidity-Dealing-Range`), or
- the repository is a hosting place for a third party's copyrighted book/course material (e.g. PDFs of ICT mentorships, extracted lesson books). A repository owner cannot license someone else's speech or course text, so the hosted material is treated as the original author's copyrighted work regardless of the repo licence.

For Tier EXCERPT the run stores, per source file:

- the file path, byte size and sha256 of the retrieved file,
- the blob URL pinned to the retrieved commit,
- at most **3** verbatim quotes per file, each **≤25 words**.

Those records live in `github/_excerpts/<owner>__<repo>@<short_sha>.jsonl`, one JSON object per quote. `github/inventory.jsonl` additionally lists **every** candidate text file in every repository (path, bytes, sha256, whether stored verbatim) so that a later pass with a different licence policy can be run against known-identical bytes.

## Tier FULL contents are unmodified

Files in `github/<owner>__<repo>@<short_sha>/...` are byte-identical copies taken from the codeload tarball of the pinned commit. No editing, reformatting, spelling fixes or summaries. sha256 is recorded per file in `INDEX.jsonl` and `github/inventory.jsonl`.

## Web pages (second channel)

Web pages retrieved with the session's page fetcher are copyrighted by their authors. This run therefore stores, for each web page, the URL, the page title, the retrieval date, and **short verbatim quotes (≤25 words)** in `web/EXCERPTS_*.md`, with `completeness=EXCERPT` in `INDEX.jsonl`. Pages whose own text or site terms show a permissive/CC licence are the only ones that may be stored as longer text; if such a page is found, the licence statement is quoted in the same record.

## What is never stored

Code files are not copied (the brief limits stored text to .md/.txt/.pdf/.srt/.vtt/.json/.jsonl and code is "leads only"). Price-data CSVs and generated chart HTML are excluded. YouTube pages and captions are never fetched (see `UNFETCHED_LEADS.md`).
