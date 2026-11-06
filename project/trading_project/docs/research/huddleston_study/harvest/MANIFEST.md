# MANIFEST — counts and gaps

Retrieval date for everything in this folder: **2026-11-06** (UTC).

## 1. Objects retrieved

- GitHub repositories inspected (metadata + commit SHA + full file tree saved under `github/_meta/`): **74**
- GitHub search API result files (`search/*.json`, raw JSON responses): **30**
- File-level inventory lines (`github/inventory.jsonl`, every candidate text file incl. sha256): **2699**
- `INDEX.jsonl` records: **316**
- Total bytes described by `INDEX.jsonl` (stored text + excerpt files): **2859253** (2792 KiB)

## 2. Counts per source_kind × completeness

| source_kind | EXCERPT | FULL | total |
|---|---|---|---|
| BOOK_OR_COURSE | 9 | 152 | 161 |
| CODE_REPO | 16 | 114 | 130 |
| EXPLAINER | 5 | 14 | 19 |
| MICHAEL_WORDS | 3 | 0 | 3 |
| UNKNOWN | 3 | 0 | 3 |
| **total** | 36 | 280 | 316 |

Notes on the kind labels (assigned from file content only):

- `MICHAEL_WORDS`: text presented in the retrieved file as ICT's own speech/writing (transcript files, a scraped page of his site). All of these are EXCERPT tier because none of the hosting repositories grants a permissive licence.
- `BOOK_OR_COURSE`: structured teaching material / notes / study books by another author, about the method.
- `EXPLAINER`: single-page explanations, glossaries, course landing pages.
- `CODE_REPO`: code and READMEs of indicators/bots/backtesters — leads only, cannot support a claim about the method.
- `UNKNOWN`: mixed or non-identifiable authorship.

## 3. Largest stored full-text repositories

| repository | stored bytes |
|---|---|
| SaiStyles/ICT-2022-study | 625804 |
| luciferalive/FX-Signal-Desk | 169125 |
| Sagar4575/ICT-2024-Mentorship-AI-Skill | 146858 |
| mabdullahns007/okf-bundle-for-ict-concepts | 127244 |
| MaweuPaul/smc-strategy-lab | 107458 |
| foeed/FvgGold-EA | 87306 |
| kayasolomon/poi-liquidity-detector | 67870 |
| carlosrod723/MQL5-Trading-Bot | 63253 |
| SoCloseSociety/TradeBobbyTerminal | 61067 |
| Predestinato-source/Curso-Predestinato-FX | 57650 |

## 4. What could not be retrieved, and why

See `ERRORS.md` for the per-URL log. Summary of the structural gaps:

1. **The shell has an egress allowlist.** `curl`/`python urllib` reach only github.com, api.github.com, codeload.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org. Every other host fails with `SSL_ERROR_SYSCALL` (see `REACHABILITY.md`). Only the session's `fetch_page` tool can read arbitrary web pages, and it exposes no HTTP status codes or raw bytes.
2. **The richest corpora are unlicensed.** The transcript/notes repositories with the most text (`newsqlguru/ict-index` 60 MB of transcripts, `SrsBlack/ict-knowledge-library`, `Klout9/ict-strat`, `Kyle2077/ict-2022-skill-bundle`, `Rouen007/ict-2022-study-room`) carry no permissive licence, so only ≤25-word quotes are stored. Their full inventories and sha256 values are recorded so the decision can be revisited.
3. **PDFs.** No PDF text extractor existed in the sandbox by default; `pypdf` 7.0.0 was installed from PyPI and used for the few PDFs inside repositories. Web PDFs were not fetched as files.
4. **No ASR was run.** No audio or video was downloaded and no transcription was produced by this run. Transcript text stored here is text that already existed in the retrieved files.
