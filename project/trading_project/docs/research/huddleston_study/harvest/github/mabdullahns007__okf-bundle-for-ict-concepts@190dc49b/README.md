# 🧠 ICT Brain

**900+ hours of ICT (Inner Circle Trader) trading content, distilled into one AI-readable knowledge base.**

No more re-watching 3-hour mentorship videos to find one definition. No more feeding an LLM a raw transcript and hoping it doesn't hallucinate a "silver bullet" setup. This repo condenses the entire ICT catalog — mentorships, forex series, futures reviews, lectures — into a structured, cross-linked, source-cited knowledge bundle that a human can read in minutes or an AI agent can query directly.

## Why this exists

ICT (Michael J. Huddleston) is one of the most influential — and most sprawling — bodies of trading education on the internet: mentorships from 2016 through 2026, hundreds of hours across dozens of series, terminology that shifts and gets renamed release over release. Concepts like **liquidity**, **order blocks**, **fair value gaps**, **kill zones**, and the **Power of Three (AMD)** model now underpin most of what the retail trading world calls "Smart Money Concepts." Valuable — and almost impossible to hold in your head at once.

This bundle exists to fix that, in a format built for the AI era, not just human skimming:

- **Machine-readable, not just human-readable.** It's built as an **[Open Knowledge Format (OKF)](https://witscode.com/open-knowledge-format)** bundle — plain Markdown with YAML frontmatter, organized with `index.md` files for progressive disclosure. Point any coding agent, RAG pipeline, or chatbot at the root `index.md` and it can navigate straight to the concept it needs — no vector DB, no ingestion pipeline, no vendor lock-in required.
- **One source of truth, fully cited.** Every concept and playbook traces its claims back to specific source series, so you (or your agent) can verify a claim instead of trusting a paraphrase.
- **Contradictions surfaced, not smoothed over.** ICT's terminology drifts across a decade of material — "order block" alone splits into breaker, mitigation, rejection, propulsion, and suspension variants depending on the year. This bundle tracks that evolution explicitly instead of pretending the framework never changed.
- **git clone-able knowledge.** No login, no scraping 900 videos yourself, no paywall. Clone it, grep it, embed it, fine-tune on it, or wire it straight into your trading bot's context window.

## What's inside

```
├── index.md              # Start here — root entry point (progressive disclosure)
├── overview.md           # The ICT framework end-to-end, synthesized, with era-by-era evolution
├── AGENTS.md             # Bundle schema/conventions, for humans and agents extending this repo
├── log.md                # Append-only changelog
├── concepts/             # 12 core idea pages: liquidity, FVGs, order blocks, killzones, PD arrays...
├── playbooks/            # 4 step-by-step setups: OTE, Silver Bullet, Turtle Soup, Daily Bias
└── sources/              # 37 series summaries — one per source series, spanning 2016–2026
```

| | |
|---|---|
| **Source material** | ~954 video transcripts across 37 series (2016–2026) |
| **Concepts distilled** | 12 core concept pages |
| **Playbooks** | 4 step-by-step, executable setups |
| **Format** | [OKF](https://witscode.com/open-knowledge-format) — Markdown + YAML frontmatter, no proprietary tooling required |

## Quick start

**For AI agents / RAG / copilots:** point your agent at [`index.md`](index.md) as the entry point. It fans out to `concepts/`, `playbooks/`, and `sources/`, each with their own index — an agent can drill down to exactly the page it needs instead of ingesting everything at once. See [`AGENTS.md`](AGENTS.md) for the full schema and conventions if you're extending the bundle or building a query workflow on top of it.

**For traders / humans:** start at [`overview.md`](overview.md) for the framework end-to-end, then jump into:
- New to ICT? → [`new-forex-traders-guide`](sources/new-forex-traders-guide.md) → [`trading-psychology`](concepts/trading-psychology.md) → [`killzones-and-time`](concepts/killzones-and-time.md)
- Want the mechanics? → [`liquidity`](concepts/liquidity.md) → [`premium-discount`](concepts/premium-discount.md) → [`playbooks/`](playbooks/index.md)
- Want era-by-era context? → [`sources/index.md`](sources/index.md)

## Contributing

Found a gap, a mislabeled contradiction, or a newer source that should update a concept page? PRs welcome. Follow the ingest workflow and lint checklist in [`AGENTS.md`](AGENTS.md) — every page needs frontmatter, every claim needs a source, and updates get logged in `log.md`.

## Disclaimer

This is an independent, unofficial fan-made reference distilled from publicly available educational content. It is not affiliated with, endorsed by, or sponsored by Michael J. Huddleston or "The Inner Circle Trader." Nothing here is financial advice — it's a study aid and knowledge base, not a signal service. Trading involves substantial risk of loss.

## License

Distilled summaries and structure in this repo are released under [MIT](LICENSE). Underlying ICT concepts and terminology are the intellectual work of Michael J. Huddleston; this repo does not redistribute raw video or transcript content.
