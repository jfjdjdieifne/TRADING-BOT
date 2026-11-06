# Settled decisions

Every ruling made so far, with the reasoning. A new session reads this and inherits the whole design without needing the conversation that produced it.

**How to use this file:** a decision here is law until deliberately changed. If you change one, edit it here and say why — do not leave two versions in two places. That failure has already happened once on this machine and cost a full rewrite.

## Index — read this, then only the sections your task needs

**ALWAYS load these four.** They are short, they apply to every task, and each exists because ignoring it went wrong:

| # | ruling |
|---|---|
| **1** | **Provenance.** Every claim carries `stated` / `demonstrated` / `extracted`. The builder's own views never enter the brain |
| **12** | **Pass 1 never filters.** Capture everything verifiable; relevance is judged later, over the whole corpus |
| **14** | **Negative control.** Never audit without a case where the answer is "nothing here". Two models passed every positive check and failed only this |
| **11** | **Two passes.** Extraction never interprets; nothing is judged from one window |

**Load by task:**

| doing | sections |
|---|---|
| backtesting, or reading any result | **24** (the bar and the null), 3, 4, 17 |
| touching files, moving things | 7, 9, 16 (three tiers by cost of loss) |
| curious why the extraction code is gone | **25** |
| the abandoned extraction pass, for the reasoning only | 1, 8, 10, 12, 13, 14, 15, 19 |
| **touching price data, or building bars** | **21** - three traps that corrupt silently |
| wondering about a second instrument | **20** - NQ only, ruled; do not re-open |
| about to reproduce his on-camera trades | **23** - that is a data check, not a test of the model |
| about to report ANY result | **24** - the bar is |z|>3.0 and the null must be matched |
| scope questions | 5, 6 |

Full list: 1 provenance · 2 two tiers · 3 backtester is the consumer · 4 hypothesis ledger · 5 scope · 6 indexed not exhaustive · 7 the archive · 8 pipeline limits · 9 scaffolding gate · 10 extraction fidelity · 11 two passes · 12 no filtering · 13 overlap · 14 model choice · 15 cost, and the free-tier ruling (20 req/day) · 16 the model spec + file tiers · 17 the ledger as a file · 18 why the workspace is shaped this way · 19 video vs transcript, measured · **20 NQ only, ES is out** · **21 price-data handling: spreads, the midnight day, the roll** · **22 overnight-run veto ruled out** · **23 testing the model, not checking his trades** · **24 the |z|>3.0 bar and matched nulls** · **25 the extraction pass was deleted**

---

## 1. Provenance — governs the schema

Every claim carries where it came from:

| `source` | meaning |
|---|---|
| `stated` | said explicitly, timestamp attached |
| `demonstrated` | shown on the chart, never said aloud |
| `extracted` | the model's reading of it — inference, not quotation |

**There is no fourth value. The builder's own rulings do not enter this brain.**

**Why:** a brain blending "he said this" / "I concluded this" / "an AI inferred this" is not untidy, it is *untestable*. When a rule fails a backtest, you must be able to tell whose idea failed.

`stated` and `demonstrated` are separate because a rule he only ever *shows on a chart* is the entire reason for feeding video to a model instead of reading transcripts.

### The label is CHECKED, not trusted - added 2026-09-02

Provenance was being asked for politely and answered dishonestly. Measured across the video corpus: **97 claims `stated`, 0 `extracted`** - not plausible, and it meant inference was being laundered into quotation. `extraction/verify_provenance.py` settled it by script, free, no quota (**the script was deleted with the rest of that pass - section 25; the ruling stands**):

> a `stated` claim must carry a **verbatim** span of the transcript. If the words are not there, the label is wrong.

| channel | verbatim | near-quote | words absent |
|---|---|---|---|
| transcript | **100%** | 0 | 0 |
| video | 43% | 11 | **23** |

**The mechanism behind that gap matters more than the number.** The transcript model copies text placed in front of it; the video model reconstructs speech it heard. Copying is checkable, recall is not. Two of video's "quotes" turned out to be the on-screen annotation `Sell Short Target Under The Low` filed as speech - which is also the hard proof of the `demonstrated` starvation in section 19.

### What actually fixed it

Not a better-worded plea. Three structural changes:

1. **A mechanical test, not a judgement call.** "Can you copy one unbroken span that carries the claim? Yes -> `stated`. No -> `extracted`." Asking a model to introspect on whether it is inferring produces the flattering answer; asking it whether it can copy-paste does not.
2. **`response_schema` on the API call**, with `source` as an **enum**. The categories stop depending on persuasion - the API rejects anything else. This also fixed a separate defect: the model emitted `"rule":": "value"`, malformed JSON that cost an entire chunk, and at `temperature=0` that failure is deterministic rather than a fluke.
3. **An explicit anti-overcorrection clause.** The first version swung the other way and dropped a legitimate mechanical rule rather than risk a label. Section 12 governs: capture it, label it `extracted` if unsure, never drop it.

**The tell that it is now genuinely copying:** it reproduced the transcript's stutter - `"significant only only if this run down here has traded into sell stops"` - instead of tidying it. A model that cleans up grammar is retyping from memory, not quoting.

Purity is impossible — every extraction is mediated. **Traceability** is the goal: every claim resolvable to a timestamp checkable in thirty seconds.

## 2. Two tiers — claims and models

```
CLAIM   one condition, one timestamp
        "an FVG inverts when a candle closes through it"

MODEL   a named, ORDERED assembly of claims
        "the 2022 model"  -> what the backtester actually runs
```

**Why:** a flat list of rules is a reference document. Rules plus the assemblies he already built out of them is a testable system. He has done the composition work that would otherwise take months to reconstruct.

It also gives automated search something sane to vary: start from his models as baselines and vary *within* them (swap a confirmation, shift a session, move a threshold) rather than blindly permuting every rule against every other.

## 3. The backtester is the primary consumer

The brain is the product; the backtester and any future indicator are consumers. **The schema serves machines, not readers.**

`sweep(pool=PDL, tf>=15m, session=0830-1100, depth>=0.2*ATR)` survives the trip downstream. "He looks for a sweep of PDL during NY AM" does not.

Every claim also carries `mechanical | contextual | discretionary`. Expect only **20–30%** to be mechanizable; the rest is context and judgement. Without this field, months get spent trying to code things that were never rules.

## 4. Hypothesis ledger — design in now, impossible to retrofit

Automated strategy search has one dominant failure mode: run 500 rule combinations and dozens will show excellent returns from **pure chance**. Not bad code — arithmetic. Enough draws, and noise produces winners.

Two defences, both cheap now:

1. **Count every hypothesis ever tested.** A backtest result is uninterpretable without it — you cannot separate a real edge from the best of 500 coin flips.
2. **Hold out data you never look at** until the very end.

## 5. Scope — 2022 only, then gap-driven

**Extract the 2022 model playlist first. Nothing else.**

**Why not more playlists:** more data helps when *estimating*, hurts when *searching*. Every extra playlist inflates the hypothesis count and raises the bar a result must clear. A wider net does not find more edge; it makes edge harder to distinguish from luck.

**Why 2022 specifically:** the builder knows it cold, so he can audit the extraction row by row. That is the only real validation instrument available, and it only exists on material already known.

**Expansion is demand-driven, not curriculum-driven.** Ignore the recommended watch order. Extract 2022, then find terms *used but never defined* — those dangling references are the reading list, ranked by how often each gap is hit. Most of the recommended sequence will turn out not to be load-bearing.

## 6. Aim indexed, not exhaustive

"All wisdom" is the right spirit, wrong target. A brain built for completeness becomes unusable. Aim **exhaustive on the mechanical rules, indexed on the rest** — layered so a session loads the slice it needs and never the whole thing.

## 7. The archive is a format reference only

`../_archive-notorious/` (22 files, hash-verified, archived 2026-08-30) is an abandoned TradingView indicator workspace.

**Never load it as a source.** Its `ict-definitions.md` blends the builder's rulings, an AI's defaults, and inferences from ambiguous phrasing into one authoritative-sounding voice with no provenance — precisely the failure `source` exists to prevent.

Kept only to show what a claim stated as a falsifiable condition looks like. **Copy the shape, never the content.**

## 8. Pipeline constraints

- Gemini free tier: **8 hours of YouTube per day**, **public videos only** (no unlisted/private). **The video allowance is not the binding limit** - 20 requests/day/model is, and it is reached at 80 minutes of video. See section 15.
- **1M tokens/minute** cap. Video bills ~300 tokens/sec, so a 1-hour video is ~1.08M tokens and will not fit one request — chunk to 20–30 min segments.
- Pro models left the free tier in April 2026. Flash / Flash-Lite only — fine for structured extraction.
- Free tier data may be used to improve Google's products. Public source material, so acceptable, but chosen knowingly.
- Cost is negligible: ~$0.11 per hour of video on Flash-Lite, ~$4–5 for a 40-hour series.

## 9. The scaffolding gate — SATISFIED 2026-08-30

**The rule was:** no `corpus/`, `extraction/`, or `bundle/` until a schema survives a test extraction on one real episode. The schema is the only decision here that is expensive to reverse — get it wrong and you find out after the whole corpus is in a shape the backtester cannot read.

**The gate was met.** Three schemas were run against the same window of episode 3 and the model-centric shape won outright; it was the only one producing ordered steps with invalidation conditions. The workspace was scaffolded after that, not before.

**The rule that survives:** a change to the schema still requires a test extraction on one real episode before it is applied to the corpus. This instance of the gate is closed; the gate itself is permanent.

## 10. Extraction fidelity — measured, not assumed

**First test, 2026-08-30.** ICT Mentorship 2022 Introduction, `gemini-3.6-flash`, whole ~30 min video in a single call. Four claims returned, three checkable, audited by the builder against material he knows cold:

| claim | source channel | result |
|---|---|---|
| speaker began trading in 1992 | audio | **correct** |
| timestamp of "what this teaches" | model-reported | **wrong** |
| on-screen text at 27:31 | **visual** | **wrong** |

**The only claim that survived came from speech. The visual claim — the entire justification for feeding video rather than transcripts — failed on first contact.**

Probable mechanism: at ~168k tokens for a ~30 min video, the model processed roughly 100 tokens/sec, i.e. subsampled to about **1 frame every 7 seconds** (documented cap ~256 frames per video). Sparse frames plus loose timestamp attribution produce confidently misplaced visual detail.

### Rules that follow

1. **Never trust a model-reported timestamp.** It got both wrong.
2. **Derive timestamps from chunk boundaries instead.** Process a known window and a claim found there is recorded as that window. Precision becomes a property of the chunking, not of the model's self-reporting.
3. **Chunk finely — it is a fidelity requirement, not just a quota workaround.** 30 min in one call is ~1 frame/7s; as 3×10 min it is ~1 frame/2.3s, for roughly the same token spend.
4. **`demonstrated` claims carry a higher verification burden than `stated`.** They failed first contact. Treat as unproven until a chart-heavy test with fine chunking says otherwise.

### Second test — PASSED, and it settles the premise

**2026-08-30.** Episode 3 (52m 27s), two 4-minute windows via `video_metadata` offsets with `fps=2.0`. Audited by the builder:

| checked | result |
|---|---|
| instrument + platform (NQ Mar-2022, TradingView) | **correct** |
| chart switches 2-min → 1-min mid-window | **correct** |
| five on-screen annotation labels | **correct, no mistakes** |
| homework slide detected in the 35–39 min window | **correct** |

The five labels are drawing annotations — text that exists **only in the visual channel**. A transcript pipeline captures none of them. `demonstrated` is a live category and the project premise holds.

The mid-window timeframe switch matters separately: catching a *transition* inside 4 minutes proves the sampling is genuinely fine-grained, not describing one representative frame.

### The proven extraction configuration

**Use this. It is the difference between the failed test and the passing one.**

| setting | value | why |
|---|---|---|
| window length | **~4 minutes** | 52-min episode ≈ 13 windows |
| `fps` | **2.0** | explicitly set via `types.VideoMetadata`; accepted by the API |
| timestamps | **from window bounds, never from the model** | it got both wrong when asked |
| token density | ~158/sec (vs ~100/sec unchunked) | ~37,900 tokens per 4-min window |
| prompt rule | *"write unreadable rather than guess"* | a wrong specific is worse than an honest gap |

Whole-video single calls are banned. That configuration failed.

**Scale estimate:** ~13 requests/episode → ~520 for 40 episodes; ~20M input tokens total, a few dollars. Pacing is bound by the free tier's 8 hours of video per day, so ~5 days for the full corpus.

### Third test - conceptual, PASSED

Perceptual accuracy is not comprehension. A rule that is plausible, well-formed and wrong survives all the way into a backtest, so the concept itself had to be audited separately.

Episode 3 narrowed to four 60s sub-windows. Three returned "none" rather than inventing an order block to satisfy the question; the fourth located it and named the level correctly. Builder confirmed.

| check | result |
|---|---|
| bearish order block - which level acts as resistance | **correct** |
| declined to confabulate in windows with no order block | **3/3** |

The refusals matter as much as the hit. The first test failed *because* it guessed; the `"write unreadable rather than guess"` instruction now demonstrably holds under a leading question.

**Sub-window narrowing is also the standard audit technique.** To verify any claim, re-extract at 60s granularity - the minute is then known by construction and the human check costs one minute of video instead of scrubbing.

**The method worked in both directions.** The first test cost about two cents and surfaced a fatal flaw; the second and third confirmed the fix before anything was built on it.

## 11. Nothing is judged per-window — the two-pass architecture

**The problem, stated by the builder:** a rule extracted from one window cannot be validated in isolation. He teaches a concept partially in episode 3 and completes it in episode 12; he states something loosely early and tightens it later. Only across the whole corpus does the picture close.

**So stop trying to be right per window.** Extraction and judgement are separate passes.

```
PASS 1  extract          per window, cheap, mechanical
        ~13 windows x 40 episodes, no interpretation,
        every claim provisional

PASS 2  consolidate      per CONCEPT, across all episodes
        this is where reasoning happens
        the bundle is the output of THIS pass, not pass 1
```

### The bundle is keyed by concept, not by episode

**This is the structural decision that makes the problem tractable.** An episode-keyed bundle can never reveal that "order block" was taught fourteen times across forty episodes. A concept-keyed one accumulates every mention of a concept in one place, so disagreement becomes visible by construction rather than by anyone remembering.

This is also what [§4](#4-hypothesis-ledger--design-in-now-impossible-to-retrofit) needs: no session ever holds the whole corpus, so contradiction detection must be a property of the filing, not of the reader's memory.

### Claim status — the lifecycle

Every claim carries a status, and pass 2 is what moves it:

| status | meaning |
|---|---|
| `provisional` | extracted once, unconfirmed — the default, always |
| `confirmed` | restated consistently in a later episode |
| `refined` | a later episode supersedes it; link to what replaced it |
| `contested` | a later episode conflicts and neither is clearly primary |

A `contested` claim is a finding, not a bug. It is often where the real understanding is.

### Re-extraction is cheap, so nothing is final

The full corpus costs a few dollars and a few days. **If pass 2 shows the schema missed something, re-extract all forty episodes.** This is not a one-shot pipeline and must not be treated like one — the anxiety of "getting it right first time" is misplaced when the reset button costs about five dollars.

## 12. Pass 1 does not filter. Ever.

**Extraction captures everything it can verify. It never decides what is worth keeping.**

Origin: the assistant flagged the model logging "8:30 AM" as a *definition* and called it noise, on the reasoning that a time is not a concept. The builder corrected this - time is central to the framework, and 8:30 carries meaning that extends into premium/discount framing.

**The correction generalises.** Relevance judgements made during pass 1 are made by whoever is least qualified to make them - a model with no framework, or an assistant reasoning from outside the domain. Anything filtered at pass 1 is invisible forever, because nobody knows to go looking for it.

Rules:
- No relevance filtering in the extraction prompt. Capture, tag, move on.
- The only pass-1 filter is **verifiability**: if it cannot be read or heard, omit it. That is an honesty rule, not a relevance rule.
- Filtering happens in pass 2, over the whole corpus, where a term appearing thirty times is visibly load-bearing and one appearing once is visibly not. That evidence does not exist at pass 1.

**Do not "clean up" extraction output.** Apparent noise from outside the framework is often signal from inside it.

## 13. Windows overlap by 30 seconds

240s windows on a 210s stride. A concept taught across a boundary would otherwise be split, with neither window seeing the whole thing and both reporting a fragment confidently.

Costs about 8% more windows (391 -> ~420). Duplicate claims from the overlap are harmless: pass 2 is concept-keyed, so the same rule extracted twice merges - and a claim appearing in two adjacent windows is weak evidence of consistency rather than a problem.

## 14. Model choice - gemini-3.6-flash, and the cheap models are disqualified

`gemini-3.6-flash` was originally reached by accident: 2.5-flash was blocked for new keys, 3.7-flash returned 503, 3.6 worked. That is not a reason, so it was tested properly against the cheaper alternatives on the checks the builder had already verified by hand.

| model | labels | platform | tf switch | names the open | **honesty** | corpus |
|---|---|---|---|---|---|---|
| 3.1-flash-lite | 5/5 | yes | yes | yes | **FAIL** | $4.44 |
| 3.5-flash-lite | 5/5 | yes | yes | yes | **FAIL** | $5.48 |
| **3.6-flash** | 5/5 | yes | yes | yes | **pass** | **$13.15** |

**The honesty check is the load-bearing test.** Asked about a window containing no order block, both flash-lite models answered "Yes" and described one. 3.6-flash correctly returned "none".

**This also invalidates their apparent conceptual pass.** Both named "the open" as the resistance level - correctly - but they would name it for *any* window, because they are answering from general trading knowledge rather than from the clip. Perceptual accuracy plus conceptual fluency can coexist with not actually looking. Only the negative case separates them.

**Rule: every model audit must include a negative control** - a window where the correct answer is "nothing here". A test made only of questions with real answers cannot detect confabulation, and confabulation is the failure mode that matters.

Cost of learning this: about three cents. Cost of not learning it: 433 windows of confident fiction, indistinguishable from signal, discovered at pass 2 or never.

**Do not switch models to save money.** The $8.70 saving buys a poisoned corpus.

## 15. Cost - RULED 2026-09-01: free tier only. $0, ~22 days

**The builder's decision: not a dime goes to Gemini.** The paid arithmetic below stays as reference, but it is not the plan. Read the free-tier subsection before acting on any figure in this section.

**The binding constraint is 20 requests per day per model - not the 8 hours of video.** Measured, see below. That makes *requests* the scarce resource, which changes which levers matter: dollars-per-token is now irrelevant and calendar time is everything.

Corpus arithmetic, measured not estimated: **428 windows remaining x ~38,000 input tokens** = ~16.3M input, ~0.21M output.

| approach | cost | status |
|---|---|---|
| interactive, gemini-3.6-flash | **$13.00** | works today |
| **batch mode, same model** | **~$6.50** | **NOT YET TESTED - do this first** |
| batch + fps 1.0 | ~$4.00 | requires re-validation, see below |

### Take: batch mode - now a THROUGHPUT question, not a discount

Same model, same prompt, same `fps=2.0`, same validated config. The audit in section 14 transfers untouched. Turnaround is asynchronous (24h target), which costs us nothing because the corpus runs over days regardless.

**Under the free-tier ruling the 50% saving is meaningless - we are paying nothing either way.** The reason to test batch is now entirely different: **does it draw on a separate quota pool from `generate_content_free_tier_requests`?** If it does, it is the single biggest lever on the 22 days. If it draws on the same 20, it is worth nothing here. Worth one test as soon as quota resets - it is the highest-value question open.

**Untested risk:** the docs say batch supports the same modalities as interactive, but do not explicitly confirm YouTube `file_data` URLs, and there are reports of jobs stuck PENDING past 24h. Batch may also simply not be offered on the free tier. **Test on ~5 windows before committing 428.**

### Only with a passing negative control: fps 2.0 -> 1.0

Frames are ~80% of each window's tokens, so halving fps cuts ~40%. But `fps=2.0` is the exact parameter that fixed the original confabulation (section 10). Test it against the window confirmed to contain **no** order block. If it invents one, stay at 2.0 - the $4 saving is not worth a corpus that lies.

### Rejected, with reasons - do not revisit these

- **Media resolution.** Already at the floor. 158 tokens/sec at fps 2.0 is ~63 tokens/frame, which *is* the low-resolution rate. We already buy the cheapest frames available and they still read on-screen labels correctly. No lever exists.
- **Prompt caching.** The repeated prompt is ~400 tokens x 428 = ~$0.13 total.
- **Output tokens.** ~$0.81 of the $13. Negligible.
- **Dropping the 30s overlap.** Saves ~$1.30, reintroduces concepts split across window boundaries. False economy.
- **Longer windows.** ~7% saving, but risks the frame cap at longer durations and coarsens audit granularity.
- **Skipping "low-value" episodes.** Violates section 12, and load-bearing-ness is unknowable before the corpus closes.

### Free tier vs billing

**RULED: stay free. Billing is not being enabled.** Enabling it generally ends the free tier on that project, and the builder has ruled the spend out entirely.

**Throughput is now measured, and it is 20 requests/day.** The old note here said nobody knew whether the free path was 11 days or 3 months. It is neither - it is about 22 days:

```
quotaId    GenerateRequestsPerDayPerProjectPerModel-FreeTier
quotaValue 20            model gemini-3.6-flash
428 windows / 20 per day = 22 days, at $0
```

**This corrects section 8.** The free-tier limit that actually bites is not the 8 hours of YouTube per day - 20 windows is 80 minutes of video, so the video allowance is never approached. Any plan pacing itself against hours of video is pacing against the wrong number.

**One request = one window, regardless of length.** This is why the request cap changes the economics of window length: under a *dollar* budget, longer windows saved ~7% and were rejected (above). Under a *request* budget, window length divides the calendar directly - 480s windows would halve 22 days to 11. **That is not licence to change it.** Section 10 makes fine chunking a fidelity requirement, and section 9's gate stands: a schema or config change requires a test extraction with a negative control first, and that test now costs quota rather than cents. Raise it as a deliberate experiment, never as an optimisation in passing.

**The 429 is not the same event twice.** Free tier enforces a per-day *and* a per-minute request quota; the `quotaId` in the error names which. Per-day means stop, per-minute means wait. `extract.py` distinguishes them - conflating them either aborts a day with quota left, or grinds through hundreds of doomed calls.

**Retry hints on a per-day quota are noise.** The API returned "retry in 28s", then "retry in 7s", with the day genuinely exhausted both times. Trust the `quotaId`, never the `retryDelay`.

### A RETRY COSTS A REQUEST - measured 2026-09-03

It is tempting to reason that a refused call cannot consume the allowance it was refused by. **That reasoning is wrong, and it was believed here until the arithmetic contradicted it.**

A run capped at 20 "requests" hit the daily quota after **16 windows**. Six retries had each spent a call: 15 saved + 6 retries ~= 21, against a ceiling of 20.

**So the ceiling must count API CALLS, not units of work.** Counting windows promises a limit it does not enforce - the same defect class as counting a per-minute 429 as the daily cap. `extract_transcript.py` now gates on `tally["api_calls"]`.

**And on a 20/day budget, a refused call is exactly as expensive as a useful one.** That inverts the usual instinct about retries: retrying aggressively does not cost latency, it costs *corpus*. Six wasted calls is 30% of a day. Hence `--sleep` was raised from 5s to 12s - paying seconds to avoid paying requests.

### Do NOT run preflight on a routine day - it costs 2 of the 20

`preflight.py` makes a text call and a video call, so it spends **10% of the daily allowance** to tell you the allowance exists. Over 22 days that is ~44 requests - **more than two full days of extraction, burned on asking permission.**

That was the right trade when a request cost money and a bad batch cost $13. Under the free tier it is inverted: **`extract.py` is already the probe.** It reads the `quotaId`, aborts cleanly on a per-day 429, saves everything finished, and re-bills nothing - and unlike preflight, the request it spends finding out does real work.

**Rule: the routine day is `extract.py` alone.** Run `preflight.py` only when something is actually wrong - after changing the model or key, or when extract fails in a way the quota does not explain.

**Quota is per-model, not per-account.** A 429 on one model does not mean the key is dead - `3.6-flash` was exhausted while both flash-lite models still answered. Always probe per model before concluding anything.

**To check quota status, run `extraction/preflight.py`.** It probes the pinned model with both a text and a video call and reports plainly. Do not reason about reset times - measure.

## 16. The pass-2 deliverable is ONE assembled model spec

**The 2022 mentorship teaches a single model across 41 episodes.** So the product is not 200 loose concept pages - it is **one ordered spec**, with the concept pages beneath it as the evidence layer.

Target: **`THE-MODEL.md` at the workspace root** - beside `CLAUDE.md` and `DECISIONS.md`. **Never inside `bundle/`.**

### Three tiers, by what it costs to lose

| tier | location | rebuilt how | never |
|---|---|---|---|
| **raw** | `extraction/output/*.json` | only by paying again (~$13) | never deleted, never edited, append-only |
| **generated** | `bundle/` | `consolidate.py`, seconds | never hand-edited |
| **reasoned** | root: `DECISIONS.md`, `THE-MODEL.md` | only by re-doing the thinking | **no script ever writes here** |

`consolidate.py` overwrites everything it generates in `bundle/`. A hand-reasoned file sitting in that folder survives only until a generator learns its name. Reasoned **products** therefore live at the root, where nothing automated writes - the same place the decisions live, for the same reason.

### Folder contracts are the exception, and they stay put

`corpus/CONTEXT.md`, `extraction/CONTEXT.md` and `bundle/CONTEXT.md` are hand-written and live inside generated folders. That is correct and must not be "fixed" by moving them to the root - a folder states its own job in a file inside itself, and a contract elsewhere is not a contract.

They are safe because **every generator writes an explicit, closed list of filenames** and none of those lists contains `CONTEXT.md`.

So the real rule is not "reasoned work never sits in a generated folder". It is:

> **A generator may only write filenames it owns, declared explicitly in its source. It must never glob-and-overwrite a folder.**

Before adding an output to any script, check its filename against the contracts. `bundle/CONTEXT.md` is the one most likely to be clobbered by a future feature.

Every step carries four things:

| field | content |
|---|---|
| `condition` | stated so it is codeable, not a topic label |
| `taught in` | every episode that teaches it - all of them |
| `status` | confirmed / refined / contested |
| `invalidation` | the stated exit, or an explicit "none stated in any episode" |

### Every mention is recorded. Nothing is deduplicated.

If a condition appears in episodes 3, 12, 19 and 27, **all four are rows on the concept page.** Never collapsed, never summarised as "mentioned repeatedly".

**Repetition is the evidence.** Frequency is the only signal for what is load-bearing versus incidental, and it exists only if every instance was kept. Deduplicating destroys the measurement. The 30s window overlap also produces duplicates near boundaries - keep those too.

The assembled spec states each condition **once** and cites all its episodes. The underlying evidence rows stay complete underneath it.

### Disagreement is preserved, never resolved by the assembler

Where episodes conflict, both versions go in marked `contested`, with their episodes. Smoothing them into one confident answer is exactly the failure provenance exists to prevent, and contested steps are usually where the real understanding sits. **Settling them is the builder's judgement, not the assembler's.**

### Not this

Not a transcript, not a summary, not the source material at length. Conditions in plain language with short evidence phrases pointing back to a timestamp. The structure is the asset; the video stays the source.

### Timing

**Cannot be assembled early.** From a handful of windows it would be invention, not convergence. It requires the corpus closed.

## 17. The hypothesis ledger is a FILE

Section 4 states the principle. This states the mechanism, because a principle nobody can execute is decoration.

`backtest/ledger.md` - one row per hypothesis ever tested:

| field | why |
|---|---|
| `n` | the running count. **This is the whole point** |
| `date` | when |
| `hypothesis` | the rule or model combination |
| `params` | thresholds, sessions, timeframes |
| `data` | symbol and date range used |
| `result` | what it returned |

**It must be a file, not anyone's memory - including Claude's.** No session persists; each one starts cold. A file makes the count survivable and lets any future session read "this is attempt 437" and do the arithmetic before getting excited.

**Human memory fails here in a specific direction:** it keeps the winner and quietly deletes the forty failures. That is not carelessness, it is how remembering works. Hence: write it at the time, every time, including the rubbish ones.

**Paired discipline: a holdout.** A slice of price data never looked at, not once, until a candidate has survived everything else. After you look, every later choice is contaminated and you cannot un-look.

**Neither can be retrofitted.** You cannot reconstruct how many things you tried, and you cannot un-peek. Both start on day one of backtesting or they are worthless.

## 18. Why this workspace is shaped the way it is

**The constraint: no session remembers the last one.** Weights never update; a closed chat takes its context with it. So the workspace has to be the memory. Every rule below is a consequence of that, not house style, and none of them should be "simplified" by a session that does not know what they carry.

Built on **ICM** (Interpretable Context Methodology), installed globally at `~/.claude/skills/icm-architect/`. **Never copy it into this project** - it is the method, installed once, available in every chat.

**Invoke the skill only for structural work** - adding a folder, restructuring, auditing the layout. Routine extraction, consolidation and analysis need none of it. A session that reads `CLAUDE.md` and the relevant `CONTEXT.md` files has everything required to operate here.

### The four operating rules, and what each is load-bearing for

| rule | exists because |
|---|---|
| One folder, one job, stating it in its own `CONTEXT.md` | a cold session must orient from the folder it lands in, not from memory of a conversation |
| Load only what the step needs | context is finite; slurping the workspace crowds out the actual task |
| The filesystem is the state | "what is done" survives a closed chat; a transcript does not |
| Generated files are never hand-edited | a scripted index cannot drift, a hand-curated one always does |

### The audit is the walk test, and it must be derived

Walk the workspace cold and check: can a session answer *where am I* and *where do I go* from the entry file plus two reads; does every folder that holds a kind of thing carry a contract; is any routing file holding content payload; is any fact in two places; do all references resolve.

**Derive the folder list from the tree, never hardcode it.** A check written from memory of what was built can only confirm what was built - it will never find the folder you forgot. That exact mistake passed a clean audit here while two folders had no contract.

### Known failure modes, observed on this project

- **Writing a description where an instruction is needed.** "A new session reads this and inherits the design" is a hope; "STOP - read `DECISIONS.md` first" is a rule. The first one silently failed a real cold-start test.
- **Fixing an entry file by making it bigger.** When a routing file fails, the instinct is to add completeness. The correct move is to push payload down a layer - the catalog is small on purpose.
- **Asserting where measuring is cheap.** Cost, quota, and model quality were each stated confidently and each wrong. Every one was settled in minutes by a probe. Prefer the probe.

## 19. The video channel has not earned its cost - MEASURED 2026-09-01

**Do not re-argue this from first principles. It was measured. Extend the measurement instead.**

The premise of this project was that feeding video beats reading transcripts, because he *shows* things he never says (section 10). That premise was tested against 22 extracted windows of episodes 1-2, checking every video-produced item against the transcript of the same episode:

| | |
|---|---|
| video items checked | 64 |
| evidence also present in the transcript | **59 (92%)** |
| genuinely visual-only | **2** - `Bought +1 /ESH22@4567.75`, `Sold -1 @4573.75` |

The other 3 "misses" were threshold artifacts at 0.67 word-overlap; their words are in the transcript.

**Both true visual-only items are his personal fills. Neither is a rule.** The measured marginal value of video, in rules a backtester can use, is **zero so far**.

**Worse: the transcript is richer than the video extraction of the same minutes.** Episode 1 at 24:08-24:17 states "four ticks or one full handle... 50 per handle... every one tick is twelve dollars and fifty cents" - a precise mechanical spec. The video extraction of that exact window returned three claims and captured none of it.

**Caption quality is not the risk it was assumed to be.** "optimal trade entry", "buy stops", "directional bias", "handles" all transcribe correctly. Auto-captions lack punctuation and space their numbers ("45 67" = 4567), which is a parsing detail, not a comprehension problem.

### Why transcripts are also ~10x faster

Section 10's fine chunking exists for two reasons that **both vanish** on text: model-reported timestamps were unreliable, and long videos subsample to ~1 frame/7s. Transcript timestamps come from YouTube per line, and text does not subsample. So transcript extraction does not need 240s windows.

```
video       433 windows / 20 req per day  = ~21 days
transcript  ~41-120 requests              = ~2-6 days
```

### What is NOT settled

1. **Episodes 1-2 are the least visual in the corpus.** Section 10's second test read **five** drawing annotations in a single window of episode 3; all 22 windows here contain **one**. Chart-heavy episodes may change this materially. **Re-run the comparison after episode 3 exists in both channels.**
2. **Deixis is untested.** "above this high is buy stops" loses its referent in text. The *rule* survives; the *instance* does not. A backtester needs the rule, so this may not matter - but nobody has checked.
3. The comparison measured video against what video extracted, not against what a transcript pipeline *would* extract. The one manual check suggests transcript wins that too.

### The ruling - RULED 2026-09-01 by the builder

**Transcripts are the primary channel now. Video is DEFERRED, not abandoned.** Build the transcript pass; come back to video later. Do not spend 21 days of quota on the assumption that video wins - that assumption is measured, and it lost.

### The deferred video experiment - what to run when video comes back

**Do not simply resume `extract.py --all`.** That prompt asks *"what rule is being taught here"*, and section 19 shows the answer is in the transcript 92% of the time. Resuming it buys nothing.

The one thing video can reach and text cannot is **what he consistently DOES but never SAYS**:

- does he draw the FVG box from the wick or the body?
- does he mark the swing high before or after the sweep?
- has every setup he shows already taken out a session high?

These are behavioural regularities. They are invisible in a transcript, and they are load-bearing for an indicator.

**The current pipeline cannot find them and never could**, for two structural reasons:

1. The prompt asks what is *taught*, not what is *done*.
2. It works in isolated 240s windows. A regularity is by definition a pattern *across* windows, and nothing in pass 1 sees across them.

So the experiment is a **different prompt**, not more of the same: take chart-heavy windows from one episode and ask *"what does he do every single time, that he never states aloud?"* One day of quota settles it. Nothing back but "he draws lines" - visual is closed for good. Three consistent behaviours - that is the thing no transcript will ever give you.

### Episode 28 is out of the corpus - RULED 2026-09-03 by the builder

**Episode 28 has no caption track.** Asked three times; `TranscriptsDisabled` every time - a different error class from episode 41's `IpBlocked`, which was a rate limit and recovered on retry. This one is permanent.

It is **156 seconds** - one video window, 0.2% of the corpus by runtime. Video is the only channel that reaches it, and the builder ruled it not worth the request.

**So the corpus is 40 of 41 episodes, deliberately.** A future session finding a gap at episode 28 has not found a bug and should not spend quota closing it. The transcript ceiling is **132 chunks across 40 episodes**; `corpus/_index.md` shows `none` in its `tx` column for exactly this reason.

### And note what never reaches the reasoning layer

`video -> Gemini (subsampled frames) -> JSON -> Claude`. **No session has ever seen a frame of this footage.** Anything visual is already a text rendering by a second model before it is reasoned over - and `CLAUDE.md` is explicit that nothing is learned into a model, the brain is the files. So a visual insight must survive being written as a sentence to exist here at all. That is not an argument against video; it is the reason the *question asked of it* has to change.


---

## 20. Instrument scope: NQ only. ES is out - RULED 2026-09-03 by the builder

> `we dont need ES. its waste of time, the SMT stuff is worst thing.`

**The model is backtested on NQ alone.** No ES data will be bought, loaded, or waited on.

**What the corpus says, so nobody re-opens this by "discovering" it:**

Ep02 [01:41] names the Nasdaq e-mini `the main focus of this mentorship`, so NQ is the corpus's own primary instrument and this ruling agrees with it.

But a real share of the live trades **with exact quoted prices** are e-mini S&P - ep29 [12:03] `ES only - no NQ executions`, ep41's entire sizing walkthrough (entry 3754.75, ES multipliers $50/$5), ep31 (4007.75), ep01 [23:03] (the chart shown is ES March 2022), ep04 [00:29], ep40 [19:02]. And ep07 [22:00] is stronger than a preference: the fair value gap was **in ES** and it produced the **NQ** entry - `trading what's not in the chart`. The ep07 page flags that reproducing those specific entries needs ES and YM loaded together.

**All of that is now knowingly out of scope.** Three consequences, accepted:

1. **The ep07 cross-market entry is not testable** and is reclassified from candidate rule to idea. It was always discretionary - ep20 [10:46] already demoted correlation to a filter rather than a signal.
2. **SMT is out**, consistent with the earlier ruling `its not a rule, its an idea`. It needs two instruments by construction, so this ruling closes it permanently rather than by preference.
3. **Validation against his on-camera results is partial** - only the NQ trades (ep03, ep06, ep07, ep14) can be checked bar-for-bar. The ES ones stand as unverified narrative.

**Why this is the right call anyway:** the build order is vetoes, then money management, then entry gates. **None of the three needs a second instrument.** Adding ES would buy verification of trades in a model whose rules we would still be testing on NQ - a second data bill to check someone else's arithmetic.

## 21. Price data: three handling rulings - 2026-09-03

The Databento NQ set (`data/README-NQ-databento.md`) carries three traps. Each is settled here because each one, left alone, produces wrong numbers that look like right numbers.

### 21.1 Calendar spreads must be filtered out first

`NQ.FUT` with `stype_in: parent` returns **every** NQ instrument - and **5,947 of 18,935 daily rows are calendar spreads** (`NQM0-NQU0`, `NQZ2-NQH3`). Spreads are priced as *differentials*: one prints at **-1.85**.

**Select outrights by positive match** - `^NQ[FGHJKMNQUVXZ]\d$` - never by excluding `-`. A spread left in the series does not raise an error; it becomes a high, a low, an order block, a fair value gap. **Silent corruption, indistinguishable from signal.**

### 21.2 The daily candle is MIDNIGHT NEW YORK - not the CME session, not UTC

This was nearly ruled wrong. The first reading assumed the CME session (18:00 -> 17:00 ET), which is the natural assumption for futures and is **not what he uses**:

> ep11 [07:44] `if you're looking at the entire daily range you're going to use the opening price at **midnight**. but if you're going to be looking at the morning session, you're going to be looking at the 8:30 in the morning opening price.`

Confirmed at ep16 [06:20] (midnight for index futures' daily range), ep02 [19:16] (weekly = Monday midnight NY open to Friday close), and used throughout ep19 and ep21 as the daily-scale Power Three anchor.

**So: daily bars are built midnight-to-midnight America/New_York, with DST.** Databento's supplied `ohlcv-1d` buckets by **UTC day** - four to five hours off - and is therefore **not usable** for daily bias, daily order blocks, or the Power Three. Bars are resampled from the 1-minute series instead; the supplied 1d/1h files are a cross-check only.

The corpus keeps midnight and 8:30 strictly apart, and so must the code: **midnight anchors the daily range and the London session; 8:30 anchors the New York session** (ep21 [13:21], [16:07]). They are two nested Power Threes (ep19 [99:39]), not two candidates for one number.

### 21.3 Contract rolling uses VOLUME, because open interest was not bought

Ep05 [04:47] says roll about a week before the third Friday to whichever month carries larger **open interest**. Open interest lives in Databento's `statistics` schema, which is not in this purchase, and buying it is out of scope under section 20's logic.

**Volume is the proxy**, and this is a deviation from a stated rule - it goes in the ledger as a named assumption, not a comment.

**Its blast radius is small and measurable, which is why the proxy is acceptable.** The model is intraday - it never holds through a roll. The roll can only affect a level that *spans* the boundary: previous-day high/low, and daily bias on the roll day itself. That is roughly **four days a year out of ~250**. The honest treatment is to make the roll date a parameter, shift it +/- 3 days, and measure whether any result moves. If nothing moves, the proxy never mattered; if something moves, that is a finding about the model's fragility, not about NQ.

## 22. The overnight-run veto is OUT - RULED 2026-09-03 by the builder

> `i give you permission to erradicate the overnight run thing. forget it. I know.`

Ep09 [15:15] - `if there's a big run overnight, avoid the New York session ... wait until the other side of lunch at 1:00` - is **removed from the backtest**. `backtest/vetoes.py` carries it under `RULED_OUT`, not `DEFERRED`. It is closed, not pending.

**What it cost to find out: ten parameter points across two definitions of "overnight"** - ledger rows 1-5, 10-14 and 23-36. It never separated from chance on any of them.

**The ledger rows STAY.** They record a real test of a real hypothesis. Deleting them would shrink `n` and make every surviving result look better than it earned - precisely the failure section 4 exists to prevent.

### The scope of this ruling, which matters

**It governs the BACKTEST, not the brain.** Section 1: the builder's own rulings never enter the corpus. So `THE-MODEL.md` section 3 and `study/ep09.md` still carry the rule exactly as he stated it, **because he did state it.** What changed is what we test, not what he said.

A future session re-reading ep09, finding the overnight rule, and noticing it absent from `backtest/` has **not found a gap.** Do not re-implement it.

### The incidental value it left behind

Testing it produced the audit that found three cross-episode implementation errors - an invented overnight window wearing his citation, 9:30 pooled into the killzone against `study/ep15.md`'s explicit finding, and a six-episode contested concept coded from one episode. That audit produced `study/_refinements.md`. **The rule failed; the machinery that caught the failure is the asset.**

## 23. We are TESTING the model, not CHECKING his trades - 2026-09-03

The builder drew this line and it is worth keeping:

> `you arent backtesting exactly his trades right lol that had be checking not testing`

**Correct, and deliberate.** Reproducing his on-camera trades bar-for-bar is a **data-integrity check** - it confirms the tape, the roll and the timezone line up. `bars/build_bars.py` does exactly that with five quoted levels, and that is the whole of its job.

**It is not evidence about the model.** He shows roughly ten trades across 41 episodes. Ten is not a sample. A perfect reproduction of all ten would establish that the transcription was faithful and nothing else - and they are days he *selected to teach with*, so they are the least representative available.

**The test is the rules, over 2,962 sessions he never saw**, with every hypothesis counted and a sealed holdout. That is why episode dates are a nice-to-have rather than a blocker (`CONTEXT.md` open question 8).

## 24. The significance bar is |z| > 3.0, and every null must be MATCHED - 2026-09-03

Two rulings, both from `PLAN.md`'s outside research. They govern every number this workspace will ever produce.

### 24.1 The bar is 3.0, not 2.0

`[OUTSIDE]` Harvey, Liu and Zhu documented **at least 316 factors** tested in the search for cross-sectional return patterns and concluded a new one must clear a **t-statistic of 3.0**, not the conventional 2.0. Bailey and Lopez de Prado's **deflated Sharpe ratio** adjusts the threshold explicitly for the number of trials plus skew and kurtosis. Industry practice is cruder and points the same way: discount a backtested Sharpe by about **50%**.

**We have the input almost nobody else has: `ledger.md` knows `n`.** That is why section 17 insisted the count be a file rather than anyone's memory.

**So: nothing is called a finding below |z| = 3.0.** Applied retroactively this is already decisive and it costs us our two best-looking results - the vetoes peaked at +2.6 at n = 36, and the setups' best was the top of 25 configurations at n = 139. **Neither was ever close.** Say so plainly rather than quoting the number that looked good.

### 24.2 A random null is the WRONG null, and a bad null is worse than none

A badly chosen control produces confident numbers measuring the wrong thing, and they look exactly like findings. Two confounds have already done this here:

**Volatility.** `overnight_run` selected days with a large 02:00-05:00 range. Volatile days have wider mornings. Its **z = -18.6 on opportunity** was measuring volatility autocorrelation, not the rule. Matching controls on the prior day's range - known before the session opens, so not a peek - removes it by construction, and the effect vanished.

**Time of day.** `[OUTSIDE]` Intraday volume and volatility are U-shaped: high at the open, a minimum around lunch, rising into the close. So *any* rule saying "trade the morning, skip lunch" beats a random-time null while carrying zero information. **Testing a clock rule requires other windows of the same sessions as the control, and they must be THE SAME LENGTH** - maximum favourable excursion grows sub-linearly with time, so opportunity-per-minute mechanically rewards short windows. The first run of `run_clock.py` ranked his 60-minute London close first for that reason alone.

**`backtest/nulls.py` owns both controls.** It also refuses to return a z when the null has too little spread to support one - the first matched run produced **z = 9.5e13** because the selection was the majority class and the control pool could not vary. A tool that returns `nan` is telling the truth; one that returns 9.5e13 is not.

### 24.3 What survived, as of this ruling

**One thing.** The **08:30-11:00 AM killzone** (ep02 [42:40]) beat every same-length control of the same sessions on **both** opportunity and efficiency. Efficiency is a ratio, so it is not inflated by volatility the way opportunity is - the U-shape explains one column and not the other.

**It is not settled.** Overlapping controls are not independent draws, a percentile is not a z, and it is `dev` only. It is the first candidate for `reserve`.

## 25. The automated extraction pass was DELETED - 2026-09-04

`extraction/output/`, `bundle/`, seven scripts (`extract.py`,
`extract_transcript.py`, `consolidate.py`, `preflight.py`, `stats.py`,
`compare_models.py`, `verify_provenance.py`) and the `.env` credential they used
were removed when the repository was prepared for publication.

**Why they went.** The automated pass reached ten episodes. The hand-written
`study/` pages cover all forty available ones and superseded it completely -
nothing downstream ever read `bundle/` again. In a finished repository the code
was not an asset, it was noise that invited a reader to think it mattered.

**What was kept, and it is the part that cost something.** The *reasoning* stays
in this file, because that is where the value was:

- **Section 19** measured video against transcript rather than arguing about it:
  92% of video claims were already present in the transcripts, 43% provenance
  clean against 100%, 21 days against 7. That measurement is the reason the
  project took the path it did.
- **Section 1** records provenance moving from *asked for politely* to *checked
  by script* - 97 claims labelled `stated` and 0 `extracted` was not plausible,
  and a mechanical test rather than a plea is what fixed it.
- **Sections 10, 12, 13, 14, 15** carry the extraction rulings, the free-tier
  measurement (20 requests/day), and the negative-control discipline that later
  governed the whole backtest.

**It is not recoverable, and that is deliberate.** The `_backups/` snapshots that
held it were deleted on 2026-09-04 as well, once the repository was published and
git took over as history. **Do not go looking for it.** What the pass produced
that mattered is written into this file - sections 1, 10, 12, 13, 14, 15 and 19 -
and that was always the part worth keeping.

**The credential.** `.env` held a free-tier Gemini key. It was never committed,
never appeared in any published file, and - verified by scanning all 48 archives,
4,924 entries - **never appeared in a backup either**, because `backup.py` never
globbed it. That rule held from the first snapshot.

**Deleting the file was housekeeping, not security. Revoke the key at the
provider.** A key that has only ever lived in one local file is still a key that
exists.
