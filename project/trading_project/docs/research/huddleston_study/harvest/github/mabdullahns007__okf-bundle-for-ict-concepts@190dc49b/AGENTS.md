# AGENTS.md — ICT Channel Bundle Schema

OKF v0.2 bundle over the raw corpus at `../../raw/ict-channel/` (954 transcripts, 37 series folders). Raw files are immutable — read only.

## Layout

- `index.md` — root index (carries `okf_version: "0.2"`), progressive disclosure entry point
- `overview.md` — synthesis; update when major sources are added
- `sources/` — one `type: Source` concept per raw folder (slug map below)
- `concepts/` — `type: Concept` pages for core ideas
- `playbooks/` — `type: Playbook` step-by-step setups
- `log.md` — append-only, date-grouped, newest first

## Conventions

- Frontmatter minimum: `type`, plus `title`, `description`, `tags`. Sources add `resource:` pointing at the raw folder (`../../raw/ict-channel/<folder>`).
- Timestamps ISO 8601 UTC. Actor convention: `generated: { by: ox-alpha/opencode, at: <ts> }`.
- No `verified` fields unless a human actually reviews — everything is currently unverified.
- Links: bundle-absolute paths (`/concepts/liquidity.md`). Broken links are tolerated but avoid creating them deliberately.
- Per-claim attribution: footnote labels keyed to `sources[].id`.

## Source slug map (raw folder → sources/<slug>.md)

| Folder | Slug |
|---|---|
| channel-misc | channel-misc |
| emini-market-reviews | emini-market-reviews |
| ends-series | ends-series |
| ict-price-action-chronicles | price-action-chronicles |
| ict-trade-executions | trade-executions |
| 2016/2017 mentorship months | 2016-mentorship-month-01 … 2017-mentorship-month-12 |
| 2022/2023/ict-2024 mentorships, 2025 lectures, 2026 SMC lectures | mentorship-2022, mentorship-2023, mentorship-2024, lecture-series-2025, smart-money-lectures-2026 |
| 2025-shotgun-saturday / 2023-forex-reviews | shotgun-saturday-2025, forex-reviews-2023 |
| charter-content / forex-market-maker-primer-course / ote-pattern-recognition-series | charter-content, forex-market-maker-primer, ote-pattern-recognition-series |
| scout-sniper / trading-plan-development / new-or-aspiring / market-maker-forex-series | scout-sniper-field-guide, trading-plan-development, new-forex-traders-guide, market-maker-forex-series |
| mastering-scalping / micro-market-structure / precision-trading / pattern-recognition-ote | mastering-scalping-vol-1, micro-market-structure-time-price, forex-precision-trading-concepts, pattern-recognition-ote |
| if-i-could-go-back / real-money-real-results | if-i-could-go-back, real-money-real-results |

## Workflows

### Ingest (new source or per-video deep dive)
1. Read the transcript (raw captions — expect no punctuation).
2. Create/update its Source page (or add a section/link in the existing series page).
3. Update affected Concept pages — check terminology drift and note contradictions in `# Evolution`.
4. Update the relevant `index.md`(s), root `index.md` if counts change, and prepend an entry to `log.md`.

### Query
Read root `index.md` → relevant subdir index → drill into pages. Cite pages by link. File durable answers back as new concepts/playbooks with a log entry.

### Lint checklist
- Every non-reserved `.md` has YAML frontmatter with non-empty `type`.
- Index entries match actual files and descriptions.
- Orphan scan (pages with no inbound links); stale claims vs newer sources.
- Terminology drift check when adding post-2025 material.
