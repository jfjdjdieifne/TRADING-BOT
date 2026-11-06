# Before this goes public - read once

Written 2026-09-04. Two things to decide yourself, and the steps to publish.

## 1. What is deliberately excluded, and why

`.gitignore` keeps three categories out. **Verify these are absent after your
first push**, because unwinding a published commit is painful.

| excluded | reason |
|---|---|
| `data/raw/` | **Databento GLBX.MDP3, purchased.** The licence does not permit redistribution. `data/README-NQ-databento.md` records the exact query, so the work stays reproducible by anyone with their own copy |
| `bars/output/` | Parquet of the same price series - redistribution by another name |
| `.env` | Credentials. Scanned: no secret-shaped string appears in any publishable file |
| `transcripts/` | 41 full caption tracks belonging to someone else |
| `extraction/output/`, `bundle/` | Deleted outright on 2026-09-04 - see DECISIONS.md section 25. The `.gitignore` entry remains as a guard |
| `_backups/` | Snapshots, and they contain the above |

## 2. The judgement call you should make, not me

**`study/` contains 41 pages of analysis built on someone else's videos.** They
are original writing - a structured read, a synthesis, criticism - but they quote
the source directly and often, because a claim that cannot be traced to a
timestamp is worthless for this purpose.

Short quotation for commentary and criticism is the ordinary shape of writing
about a work, and this is much closer to a literature review than to a
reproduction. **But you are the one publishing under your name, and you are
about to start a postgraduate programme.** Three options, in increasing caution:

1. **Publish `study/` as is.** It is analysis, it names its source clearly, and
   it does not substitute for watching the videos.
2. **Publish `study/` with quotations shortened** where a page quotes several
   consecutive sentences.
3. **Publish only `THE-MODEL.md` and `backtest/`**, and describe `study/` as an
   intermediate artefact. The results stand without it; the traceability weakens.

I would take option 1, and I am not the one carrying the consequence.

## 3. Claims to keep out of any description of this

You asked to be honest, so here are the three overstatements available and worth
avoiding:

**"We used the ICM architecture."** ICM here is **a local working convention** -
one folder one job, each declaring its own contract - not a published or
recognised standard. Describing it as an established architecture would be a
claim someone can check and find unsupported. Say what it is: a folder
convention that kept a long multi-session project coherent, which is true and is
enough.

**"We proved ICT does not work."** Not supported, and not what was measured.

Three reasons it overreaches, and they are worth being able to state:

1. **Primitives were tested mostly in isolation.** The series teaches confluence
   - a gap WITH displacement WITH a liquidity raid AT a time IN the direction of
   a higher-timeframe bias. An isolated primitive showing nothing is not evidence
   that the stack shows nothing.
2. **The discretionary parts were excluded, not solved.** The source says plainly
   that judgement is required. Those instructions are catalogued in
   `backtest/vetoes.py` under `DEFERRED` rather than approximated - a fabricated
   proxy would be our rule wearing his name.
3. **A method run mechanically is not the method as practised.** Nothing here
   speaks to the person applying it.

What IS supported: *these specific mechanised formulations, mostly in isolation,
on NQ, over this period, in this implementation, did not show a measurable edge
at this bar.* Every qualifier is doing work - `reserve` is 300 sessions against
dev's 2,970, and a null on a tenth of the data is weaker evidence than a positive
would have been.

**Say it that way and it is unarguable. Say it the short way and someone who
knows the material will take it apart, correctly.**

**"We built a backtesting engine / trading system."** It is a research harness
for falsifying claims. It has no live component, no execution modelling, and no
position sizing that was ever validated. Calling it a trading system invites the
first question you cannot answer.

**What you CAN claim, and it is the stronger claim anyway:** you took an informal
body of knowledge that millions of people argue about without data, made it
falsifiable, and tested it with pre-registration, matched null models, a counted
hypothesis budget, and held-out data that was never opened. **That is a
methodology result, and it does not depend on the answer having been positive.**

## 4. Publishing steps

**The repository is already initialised and committed locally** (2026-09-04),
with `.gitignore` verified against the working tree *before* the first commit -
no `data/`, no `transcripts/`, no `_backups/`, no credential.

To publish: create an empty repository on GitHub — **no README, no .gitignore,
no licence**, they would collide with what is already here — then:

```
git branch -M main   # already done
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Or GitHub Desktop: `File > Add local repository`, point it at this folder,
then Publish. It reads the existing history.

**Before pushing, run this and confirm it prints nothing:**

```
git ls-files | grep -Ei "data/raw|transcripts/|\.env|_backups"
```

That is the last moment where excluding a 106 MB licensed dataset is free.

## 5. The licence

`LICENSE` is MIT and covers **the code and written analysis in this repository
only**. It does not and cannot grant anything over:

- the Databento market data (purchased, excluded, not redistributable),
- the source videos or their transcripts (someone else's, excluded),
- quoted material inside `study/`, which is quotation for commentary and stays
  the property of its author.

That distinction is worth keeping straight if anyone asks.
