# MEMORY ANALYSIS V0 — where the dev loop keeps its bytes (measured on a FIXTURE)

**Status: diagnosis only. No market data was opened.** Every number below comes from
`MEMORY_PROBE_FIXTURE_V0.py` (this folder), which generates synthetic candles from a declared
seed and measures resident memory and `tracemalloc` attribution while it drives the **same
objects** `dev_month_v0/run_dev_month_v0.py` drives.

---

## 1. What was measured, and on what

| item | value |
|---|---|
| bars | **synthetic**, `synth_bidask()` in the probe, `numpy.random.default_rng(20261109)`, 6,000 five-minute bars, weekends removed, `r ~ N(0, 1.2e-4)`, half-spread `5e-5` |
| objects driven | `ReplayObservationStream` → `MonitoringLoop(engine_factory, frames_builder, StudyReasoningLayer)` → `EpisodeExtractor` + `ContextEventModel` — the **object construction and warm-up body copied verbatim** from `run_dev_month_v0.py:159-173` and `:186-206` |
| runs | **run 2** = as-is (journal kept), **run 3** = `loop.journal.clear()` after each boundary (a change only a *new* wrapper can make) |
| boundaries | 200 task boundaries each (= 2,400 five-minute observations each) |
| sampling | `/proc/self/status VmRSS` after every boundary; `tracemalloc` snapshots (6 frames) at boundaries 50/100/150/200 |
| safety | `--rss-cap-kb 1500000`; the probe stops itself rather than letting the kernel kill it (which is what happened to the real run) |
| wall time | run 2: 562 s · run 3: 552 s (≈ 2.8 s/boundary under `tracemalloc`) |

The fixture is deliberately **low-structure**: a synthetic walk produces far fewer FVG regions and
links than real EURUSD does. That makes every figure below a **floor**, not an estimate of the real
case — §5 states the comparison explicitly.

---

## 2. The measurement

Resident memory, kB, at boundaries 1 → 200:

| segment | run 2 (journal kept) | run 3 (journal cleared) |
|---|---|---|
| 1 – 50 | 0.26 MB / boundary | 0.24 MB / boundary |
| 50 – 100 | 1.25 MB / boundary | 0.95 MB / boundary |
| 100 – 150 | 1.82 MB / boundary | 2.02 MB / boundary |
| 150 – 200 | **3.66 MB / boundary** | **3.04 MB / boundary** |
| whole run | 1.76 MB / boundary | 1.57 MB / boundary |
| RSS at boundary 1 → 200 | 90,800 → 448,760 kB | 90,540 → 410,884 kB |

**The growth is not linear, and it is not "linear with noise".** The per-boundary cost rises by a
factor of ≈ 14 between the first fifty boundaries and the last fifty, in both runs. A linear
process would show the same segment slope throughout.

Mechanism, visible in the code: each boundary compares the *current* structure against **all**
structure known so far (`ConnectedReadingsEngine.links` grows 6.11 per boundary and each new link
is a new dict that embeds both endpoints), and each element is then copied into a ledger payload
that is never released. Cost per boundary therefore grows with the number of known regions —
quadratic accumulation, linear symptom.

---

## 3. Where the bytes are, with the line that retains them

Counts are measured entity counts at boundary 200 (from the probe, not estimated):

| retained structure | declared / appended at | growth per boundary | at 200 boundaries | read by the decision path? |
|---|---|---|---|---|
| `MonitoringLoop.journal` — one `dataclasses.asdict(StepReport)` **per 5-min observation** | `monitoring.py:607` (`self.journal: List[dict] = []`), appended at `:646`, `:653`, `:663`, `:725`, `:928` | **11.94** | **2,400** | **no** — read only by `state_dict()` (`:753`) and `restore()` (`:792`); verified by reading every occurrence of `.journal` in the package (no others) |
| `AnalysisEngine.records` — one `AnalysisRecord` per boundary | `analysis_lifecycle.py:544` (`self.records: List[AnalysisRecord] = []`) | 0.99 | 200 | **yes** — `len(self.records)` sets `version=` at `:893`, `:913`, `:1021`, `:1066`, `:1106` |
| `InterpretationLedger.results` + `.versions` — every `SelectionResult` and its payload versions | `csm.py:2425` (`self.results`), `:2446` `record()` appends result and version payloads | with events | — | **yes** — `gate_v1` reads `study.readings.tasks` / `.regions`, which are built from ledger content |
| `ConnectedReadingsEngine.links` | `connected_readings.py:385` (`self.links: List[FrameLink]`) | **6.11** | **1,221** | yes (`_seen_links`, `.interps`) |
| `ConnectedReadingsEngine.regions` — `FVGRegion` objects, each with an `interactions` list | `connected_readings.py:384` | 1.41 | 283 | yes (`scan_fvgs` cursor, `gate_v1` region lookup) |
| `ConnectedReadingsEngine.seq_facts` | `connected_readings.py:388` | 4.29 | 858 | partly |
| `StudyReasoningLayer.seq_facts` | `study_links.py` (`self.seq_facts`) | **8.11** | **1,622** | partly (`shift_watches` feed `gate_v1`'s "hold the attempt" branch) |
| `StudyReasoningLayer.shift_watches` / `_last_ref_records` / `candidates` | `study_links.py` | 0.16 / 0.46 / 0.15 | 32 / 92 / 30 | yes (`shift_watches`) |
| `StudyReasoningLayer._row_buffer` / `hf_context` | `study_links.py` | bounded | 12 / 4 | yes |
| `ContextEventModel.counts` | `decision_layer.py` | bounded | 4 | yes |
| wrapper `episodes` (one `Episode` per boundary) | `dev_month_v0/run_dev_month_v0.py:198` (`episodes.append(ep)`) | 0.99 | 200 | **no** — only `len(episodes)` is ever used (`:328`) |

`tracemalloc` attribution, growth between boundary 50 and boundary 200 (top sites):

| growth | site | what it is |
|---|---|---|
| **+20.2 MB** (184,003 objects) | `study_links.py:1796` (`_jsonable`, dict branch) | JSON-safe copies of study payloads |
| **+15.6 MB** (148,228 objects) | `connected_readings.py:165` (`_jsonable`, dict branch) | JSON-safe copies of reading payloads |
| **+10.9 MB** (116,504 objects) | `study_links.py:1794` (`_jsonable`, `str(Timestamp)`) | timestamp strings inside those copies |
| **+6.8 MB** (17,768 objects) | `csm.py:3082` (coverage-row dict) | one row per candidate per boundary, retained in the record |
| **+5.0 MB** (62,459 objects) | `study_links.py:1474` (`recorded_event_times`) | event-time strings in shift-watch payloads |
| **+4.4 MB** (35,082 objects) | `csm.py:3108` (status-transition dict) | lifecycle rows inside the same coverage rows |
| **+4.0 / +4.0 / +3.7 MB** | `connected_readings.py:811`, `:863`, `:167` | candidate strings and list copies |
| **+2.9 / +2.5 MB** | `study_links.py:1514`, `connected_readings.py:866` | candidate event strings and role options |

Total traced at boundary 200: **104.4 MB** (7.4 MB at boundary 50). RSS is higher (448 MB) because
tracemalloc sees only Python allocations, and pandas/numpy buffers and the interpreter's arena are
outside it.

**The dominant cost is not a computation — it is serialization that is never released.** Four of
the top five sites are the two `_jsonable` helpers, i.e. the engine copying its own records into
"JSON-safe" dicts and then keeping both copies.

---

## 4. Can a NEW wrapper bound this without editing a closed module?

Three candidate interventions, each with the effect measured or argued:

**(a) Drop `MonitoringLoop.journal` from the wrapper — measured, 8.4 % saving.**
`loop.journal.clear()` after each boundary is a one-line change in a *new* file; `journal` is
appended by the loop and read only by `state_dict()`/`restore()`, so no decision depends on it.
Measured: RSS at boundary 200 falls from 448.8 MB to 410.9 MB, and the late-segment slope from
3.66 to 3.04 MB/boundary. **Equivalence: decisions unchanged, exported state changed.** This is an
argument from the code — `journal` has no reader on the decision path — and it is **not**
demonstrated by a decisions diff, because the probe never runs `decide()`.

**(b) Drop the wrapper's own `episodes` list — safe by construction.** `run_dev_month_v0.py` keeps
one `Episode` per boundary but only uses `len(episodes)` (`:328`). A new wrapper keeping a counter
instead removes 200 objects; the saving is small (the model already holds what it needs) but it is
free.

**(c) Bound the study layer, the ledger, or the engine records — NOT possible without editing
them.** `ConnectedReadingsEngine.regions/.links`, `StudyReasoningLayer.seq_facts/.shift_watches`,
`InterpretationLedger.results/.versions` and `AnalysisEngine.records` are all **read** by the
decision path (`gate_v1`'s contradiction check walks `study.readings.tasks` and `.regions`;
`analysis_lifecycle.py` reads `len(self.records)` into a `version` field). Trimming them changes
what the decision sees. Verdict: **UNKNOWN at best, and almost certainly CHANGED.**

**Therefore:** after (a) and (b) the wrapper still inherits ≈ 90 % of the growth. The only clean
way to bound memory is to **not run `MonitoringLoop` at all** — which is exactly what
`ICT_RECIPE_SPEC_V1.md` proposes: a new streaming wrapper that keeps a fixed window of 5m bars and
re-runs the *batch* engines on it, holding no history of its own. That design pays CPU instead of
memory, and its cost is bounded by the window, not by the month.

What a closed module would have to change, if the owner prefers fixing the existing loop instead
(this is a **decision**, not a recommendation):

| change | where | effect |
|---|---|---|
| journal as a ring buffer / write-through to disk | `monitoring.py:607`, `:646`, `:653`, `:663`, `:725`, `:928` | removes 12 entries per boundary |
| ledger payload retention policy (keep last N per task) | `csm.py:2425`, `:2446` | removes the dominant serialization copies |
| links/regions pruning by causal age | `connected_readings.py:384-388` | removes the quadratic term |
| record list bounded, version counter separated from `len(records)` | `analysis_lifecycle.py:544` + the five `len(self.records)` reads | keeps versioning correct while bounding storage |

Each of the four is a `PATCH ONLY` change **inside** `HOLDOUT_V1` — i.e. precisely what clause (d)
of `D3` forbids until the owner rules (see `holdout_v1/PATCH_LOG_001.md` P-04).

---

## 5. Bytes per boundary, stated as a range and not as a constant

| source | value | status |
|---|---|---|
| fixture, boundaries 1–50 | 0.26 MB/ boundary | measured |
| fixture, boundaries 150–200 | 3.0–3.7 MB/ boundary | measured |
| fixture, whole 200-boundary run | 1.57–1.76 MB/ boundary | measured |
| **real EURUSD, aborted run** | **≈ 3.8 MB/ boundary** (3,870,276 kB reached over ≈ 1,000 warm-up boundaries, `dev_month_v0/SUMMARY_V0.md`) | measured coarsely, from the RSS timeline of a run that died |

The two agree in **order of magnitude** and disagree in **shape**: the real run reached the
fixture's *late-run* rate almost immediately, which is what "more structure per boundary" predicts.
The honest statement is therefore: **cost per boundary is not a constant, it is a function of how
much structure the data contains, and it grows as the run proceeds.** Any capacity plan that
multiplies one number by the number of boundaries will be wrong in the unsafe direction.

---

## 6. Answer to the design question, in one paragraph

A new wrapper **can** remove its own accumulators and the loop's journal (measured: ≈ 8–10 % of
growth, decisions unchanged by argument), and it **can** avoid the whole problem by not using the
streaming loop at all (the `ICT_RECIPE_SPEC_V1` design: fixed window, batch engines, no history).
It **cannot** make the existing loop's memory bounded from the outside, because the structures that
grow are the ones the decision reads. Whether to bound them inside the loop is an owner decision
under clause (d), and it is the first item in `ICT_RECIPE_SPEC_V1.md` §7.

## What this does NOT establish

- It does **not** measure real market data: the fixture is synthetic and low-structure, so every
  per-boundary figure here is a **floor** for the real case, and the real case is quoted from the
  earlier aborted run's own timeline rather than re-measured.
- It does **not** prove that `journal.clear()` leaves decisions unchanged — it argues it from the
  absence of any reader, which a decisions diff has not confirmed (the probe never decides).
- It does **not** establish that the `ICT_RECIPE_SPEC_V1` design will fit in a given machine: its
  window is bounded by construction, but the batch engines' own peak is unmeasured.
- It does **not** establish that the aborted run's death was caused by the specific structures
  listed; it establishes that these structures grow superlinearly in the same loop, which is the
  mechanism, not the death certificate.
- It does **not** authorise any patch: §4's table is a list of decisions, not a plan of work.
- It contains **no result about trading**: no plan, no `R`, no edge, and nothing here is a blind
  result — one month, one aborted attempt, one synthetic probe.
