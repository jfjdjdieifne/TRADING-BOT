# ICT Brain

## STOP - do this before answering anything

1. **Read the index at the top of `DECISIONS.md`**, then sections **1, 11, 12, 14** (always), plus whichever sections the index maps to your task. Every ruling carries the reasoning that produced it. Skip this and you will re-litigate settled questions or repeat mistakes that already cost money.
2. **Read `CONTEXT.md`** for the stages that were run and the commands that reproduce them.

Do not skip step 1 because the question seems small. Several rulings exist *because* a small-seeming choice went wrong.

## What this is

A falsification study of the 2022 ICT Mentorship playlist (41 episodes, 24.5 hours), tested against 15.7 years of NQ futures. **The research is finished: 154 hypotheses, nothing survived out-of-sample.** `README.md` is the summary, `backtest/findings.md` the reasoning.

**Nothing is learned into a model.** The bundle is the brain and it is entirely on disk - including every decision, because no session remembers the last one.

## How this workspace works

No methodology knowledge needed to operate it. Four rules:

- **One folder, one job**, stating its own contract in its `CONTEXT.md`.
- **Load only what the step needs** - a folder's contract and the files it names. Never crawl the tree.
- **The filesystem is the state.** What is done is what exists on disk - `study/` pages, `bars/output/`, rows in `backtest/ledger.md`. Never memory, never a transcript.
- **Generated files are never hand-edited.** `corpus/_index.md`, `study/_refinements.md` and everything in `bars/output/` and `backtest/*_report.md` are rebuilt by script.

These are not house style. Each carries something specific, and **DECISIONS.md section 18** says what - read it before "simplifying" any of them. It also covers ICM, where the skill lives, and when to invoke it.

## Where things live

| path | role | if lost |
|---|---|---|
| `DECISIONS.md`, `THE-MODEL.md` | reasoned. **No script writes here** | redo the thinking |
| `CONTEXT.md` | the pipeline, status, commands | minutes |
| `corpus/_index.md` | generated state surface | one command |
| `extraction/` | corpus tooling: fetch transcripts, build indexes, backup | an afternoon |
| `transcripts/` | the spoken channel, all 41 episodes, exact timestamps | one command, minutes |
| `study/`, `THE-MODEL.md` | **reasoned. 41 hand-written episode reads + the synthesis** | days of reading |
| `backtest/ledger.md` | **reasoned. The count of every hypothesis tested** | **unreconstructable - see section 17** |
| `data/raw/` | bought price data. Never edited, never backed up | a re-download |
| `bars/` | the script; `bars/output/` regenerates in minutes | minutes |
| `README.md`, `PUBLISHING.md` | the public summary, and what must stay out of the repo | - |

## Route by what you're doing

| If | Go to |
|---|---|
| anything at all, first | `DECISIONS.md` |
| **starting a new session** | **`README.md`, then `backtest/findings.md`** |
| why the research stopped where it did | **`PLAN.md`** - "Where this leaves it" |
| what has been tested and what survived | `backtest/findings.md`, `backtest/ledger.md` |
| **about to implement any rule** | **`study/_refinements.md`** - no episode is self-contained; a rule coded from one citation has already gone wrong three times |
| status, commands, what to run next | `CONTEXT.md` |
| asking why the extraction code is gone | `DECISIONS.md` section 25 - deleted deliberately, reasoning kept |
| assembling the model spec | `DECISIONS.md` section 16 |
| reading what he actually teaches | `THE-MODEL.md`, then `study/ep<NN>.md` for the source |
| touching price data or bars | `bars/CONTEXT.md`, then `DECISIONS.md` section 21 - **three traps that corrupt silently** |
| reading the results | `backtest/findings.md`, then `README.md` |
| tempted to add a second instrument | `DECISIONS.md` section 20 - **NQ only, ruled. Do not re-open** |
