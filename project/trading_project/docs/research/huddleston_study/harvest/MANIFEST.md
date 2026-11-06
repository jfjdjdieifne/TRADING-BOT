# MANIFEST — counts and gaps

Retrieval date for everything here: **2026-11-06** (UTC).

## 1. What was retrieved

- GitHub repositories inspected (metadata + pinned commit SHA + full recursive tree saved in `github/_meta/`): **74**
- GitHub search API responses (`search/*.json`): **30**
- File-level hashes (`github/inventory.jsonl`): **2699** lines (every candidate text file, stored or withheld)
- `INDEX.jsonl` records: **326** — 316 GitHub objects + 10 web records
- Bytes described by `INDEX.jsonl`: **2880866** total (2859253 GitHub + 21613 web records)

## 2. Counts per source_kind × completeness

| source_kind | EXCERPT | FULL | INDEX_ONLY | total |
|---|---|---|---|---|
| BOOK_OR_COURSE | 9 | 152 | 0 | 161 |
| CODE_REPO | 16 | 114 | 0 | 130 |
| EXPLAINER | 13 | 14 | 0 | 27 |
| MICHAEL_WORDS | 3 | 0 | 0 | 3 |
| UNKNOWN | 3 | 0 | 2 | 5 |
| **total** | 44 | 280 | 2 | 326 |

How the kinds were decided (from file content only):

- `MICHAEL_WORDS` — the file itself presents the text as ICT's own speech/writing (three transcript/scraped-page sources). All are EXCERPT tier because their hosts grant no permissive licence.
- `BOOK_OR_COURSE` — structured teaching material, notes, study books, compiled glossaries by another author.
- `EXPLAINER` — single articles, tutorial pages, glossaries, course landing pages.
- `CODE_REPO` — indicator/EA/bot source and READMEs: leads only, cannot support a claim about the method.
- `UNKNOWN` — mixed authorship or content that does not identify an author (e.g. an archived wiki index page that mixes site chrome with passages attributed in-page to ICT).

## 3. Where the full-text bytes are

| repository | stored bytes | files |
|---|---|---|
| SaiStyles/ICT-2022-study | 625804 | 68 |
| luciferalive/FX-Signal-Desk | 169125 | 17 |
| Sagar4575/ICT-2024-Mentorship-AI-Skill | 146858 | 21 |
| mabdullahns007/okf-bundle-for-ict-concepts | 127244 | 61 |
| MaweuPaul/smc-strategy-lab | 107458 | 11 |
| foeed/FvgGold-EA | 87306 | 4 |
| kayasolomon/poi-liquidity-detector | 67870 | 4 |
| carlosrod723/MQL5-Trading-Bot | 63253 | 3 |
| SoCloseSociety/TradeBobbyTerminal | 61067 | 15 |
| Predestinato-source/Curso-Predestinato-FX | 57650 | 2 |
| BlackCat-cyber-creator/x402-agent-hub-mcp | 50645 | 12 |
| reuniware/Smart-Money-Sniper | 43377 | 4 |

## 4. What could not be retrieved, and why

Per-URL detail is in `ERRORS.md`. Structural gaps:

1. **Shell egress is an allowlist.** `curl`/`urllib` reach only github.com, api.github.com, codeload.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org; every other host fails with `SSL_ERROR_SYSCALL` (or `Empty reply` on port 80). Only the session's `fetch_page` tool can read other sites, and it returns converted Markdown without HTTP status codes or raw bytes — hence the sha256 of a web record is over the stored record, not over the page.
2. **Reddit blocks the fetcher**: `https://www.reddit.com/r/InnerCircleTraders/comments/1bhekzl/ict_2022_model/` and `https://old.reddit.com/...` both returned `Failed to fetch page (HTTP 403)`.
3. **Forex Factory returns no post text**: the fetcher returned only the page title (`ICT system \| Page 2 \| Forex Factory`), posts are rendered client-side. Stored as `INDEX_ONLY`.
4. **Michael Huddleston's own site is unreachable**: `https://www.innercircletrader.com/` → `Failed to fetch page`; the Wayback capture returned only the archive toolbar and the words `Too many requests`.
5. **The richest corpora are unlicensed**, so only ≤25-word quotes exist for them: `newsqlguru/ict-index` (~60 MB of video transcripts), `Klout9/ict-strat`, `SrsBlack/ict-knowledge-library` (667 text files), `Kyle2077/ict-2022-skill-bundle`, `Rouen007/ict-2022-study-room`, `Yousef-Diab/the-algorithm`. Their full inventories with sha256 are recorded so a later pass can be re-run against identical bytes.
6. **Paid/registration sources were not accessed**: `ictpdf.com` (paid PDF course), `icttradingcourse.com` (paid course), Scribd document `348443220` (lead only, not fetched), YouTube (out of scope by instruction).
7. **No ASR was run.** No audio/video downloaded, no transcription produced. Transcript text here pre-existed in the retrieved files.
8. **PDFs**: no extractor shipped with the sandbox; `pypdf` 7.0.0 was installed from PyPI and used only on PDFs that were already inside retrieved repositories.

