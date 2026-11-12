# study - one structured read per episode, then the synthesis on top

One job: turn each episode from 40 minutes of talking into a page you can actually use, **without losing the thread back to what he said.**

## The rule that governs everything here

**The 2022 transcripts are CORE. They are the food.** Every line on every page below traces to `../transcripts/ep<NN>.md` at a timestamp.

Outside sources - the web, other playlists, general trading knowledge - are allowed **only** to explain something the corpus leans on but never defines, and when used they are marked `[OUTSIDE]` on the line that uses them. An unmarked line is a claim about what HE said, and must be checkable in thirty seconds.

**Never let outside knowledge fill a gap silently.** A term he uses but never defines is a *finding* - it goes in "Referenced, never defined" and feeds the reading list (DECISIONS.md section 5). Quietly answering it from general trading knowledge destroys the finding and contaminates the corpus with things he may not believe.

**Outside research lives in ONE place: `../THE-MODEL.md` section 8.1.** Not in these pages. Displacement magnitude was researched on 2026-09-03 with the builder's permission and the result is quarantined there. **Do not backfill it into any episode page** - he did not say it, and a page that mixes his words with the internet's is no longer checkable in thirty seconds, which is the only property that makes these pages worth having.

## Inputs
- Working: `../transcripts/ep<NN>.md` - the episode being read, in full
- Reference (every run): `../DECISIONS.md` sections 1 (provenance), 5 (scope), 12 (no filtering)

## Process
1. Read one full transcript. Not a sample - the whole thing.
2. Write `ep<NN>.md` to the template below.
3. One episode per file. Never combine episodes at this stage.

## Outputs
- `ep<NN>.md` - one per episode, episode-keyed, **linear** (follows the video)
- `../THE-MODEL.md` - the synthesis, **de-linearised**, assembled once the pages exist

## Why episode-keyed here and concept-keyed later

DECISIONS.md section 11 is emphatic that the *product* must be concept-keyed - an episode-keyed brain can never reveal that order blocks were taught fourteen times. That still holds.

These pages are **not the product.** They are the working layer: a faithful, linear read of each episode, so the synthesis is assembled from something checkable rather than from memory of a video. The de-linearising happens on top, in one place, deliberately - which is exactly what "combine it properly, stripped of linear" asks for.

## Rule vs idea - keep them apart

He teaches three kinds of thing and they must not be pooled:

| kind | test | what it does in the model |
|---|---|---|
| **rule** | a condition true or false of price at a moment | it is in the model; a backtester evaluates it |
| **idea** | a way of seeing, a confirmation, a piece of context | recorded in full, **never a trigger** |
| **story** | biography, motivation, industry commentary | recorded only where it explains a design choice |

**An idea recorded as a rule is the most expensive error available here.** SMT (ep07) is the worked example: it is the most-copied concept in the public ICT ecosystem, and he says trading it as a rule blew his accounts in the 1990s. Section 3 warns the same thing generically - assuming more is mechanizable than really is costs months.

When a page marks something an idea, say so on the line, and say whose call it was: his, or the builder's.

## The template

```
---
episode: N            video_id: <id>          duration: MM:SS
teaches: [concept, concept]                   depends_on: [concept]
---

# EpNN - <what it is actually about, not the YouTube title>

**In one line:** <why this episode exists>

## The spine
The 3-6 things this episode is actually for, in order, each with a timestamp.

## Procedure taught (omit if none)
Ordered steps. Each step: trigger -> condition -> what invalidates it.
If he never states an invalidation, write "none stated" - do NOT supply one.

## Terms defined here
| term | his definition | at |

## Numbers, times, levels
Anything specific: session times, tick values, thresholds. These are where
a backtest lives or dies.

## Quotable
The two or three lines worth reading verbatim.

## Referenced, never defined
Terms he leans on and assumes you know. The reading list.

## Contradicts / refines
Where this episode changes something an earlier one said. Cite both.
```

## Human check

Open the page beside the transcript and pick any line. Can you land on the timestamp and hear him say it? If a line cannot survive that, it is the reader's invention and does not belong.

Second check: does "The spine" actually match what the episode is *for*, or does it just list what got mentioned? A page that lists is a transcript with extra steps. A page that tells you the point is the deliverable.
