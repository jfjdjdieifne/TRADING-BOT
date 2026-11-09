# ترياج الفروع المفتوحة `V1` — قراءة فقط، بلا دمج

# OPEN BRANCHES TRIAGE `V1` — read-only, no merging

**Status:** `READ-ONLY AUDIT`. Nothing merged, nothing checked out, nothing copied.
**Method:** `git ls-remote --heads`, `git merge-base`, `git rev-list --left-right --count`,
`git log <merge-base>..<ref>`, `git diff --name-status <merge-base>..<ref>`, and
`git show <ref>:<path>` reads only. Working tree untouched; `git status --porcelain` empty
before and after.

**The target this triage is judged against** is the question the project is actually asking:
*a reader that understands context* — one that takes the chart up to `t`, says what it sees,
picks the object that matters, and says what would make it wrong. A branch is "related" if it
contributes to that, directly or through the evidence a reader must cite.

---

## 0. Count reconciliation

| quantity | measured now |
|---|---|
| remote branches (`refs/heads`) | **38** (+ `origin/HEAD` → `main`) |
| already contained in `origin/arena/77604f59-trading-bot` (`fd43dc29`) | **20** |
| not contained — i.e. hold at least one commit the Era-3 tip does not | **18** rows |

The "18" is **17 arena branches + `main`**. `main` is counted as unique because of its single
`Hello → Goodbye` edit, which carries no project content; it is listed for completeness and
then excluded from the triage proper. **17 arena branches** are triaged below.

Every containment claim and every ahead/behind number below is a `git` measurement made in
this session, not a transcription.

---

## 1. Summary table

`Δ` = `git rev-list --left-right --count fd43dc29...<ref>` (Era3-only / branch-only).
"files" = `git diff --name-only <merge-base>..<ref>`.

| # | branch | head | merge-base | Δ | files | unique content | relation to the reader target |
|---|---|---|---|---|---|---|---|
| 1 | `e2c9bda8` | `aae964c` | `480e0cd` | 15/3 | 5 | `b1_teacher_test/` (cases, results, runner, frozen JSON) + the **raw** `D2` owner text | **HIGH — the only published-example ground truth in the repo** |
| 2 | `ad9c5dec` | `e1befae` | `7612afc` | 114/2 | 206 | deliverables 87–99 + 101–103 + `PROJECT_HANDOFF_AR`, u3-k1/k3 cards, `contextual_selection_v1` docs, 24 test files | **HIGH — the narrative documentation of the reader itself** |
| 3 | `a2387edd` | `b311dab` | `51ea54b` | 43/1 | 1 | `deliverables/104_INDEPENDENT_FULL_PROJECT_VERDICT_AR.md` | MEDIUM-HIGH — independent verdict on the reader |
| 4 | `5eee9692` | `780755c` | `c905f2b` | 113/4 | 31 | reports 101/102/103 + 83 only; **its code is byte-identical to Era-3** | LOW — superseded code, withdrawn reports |
| 5 | `46263b03` | `e2e68f1` | `c905f2b` | 113/2 | 4 | `k6/` transcript quote verification | LOW-MEDIUM — evidence tooling, not reader |
| 6 | `5b5d18f2` | `a5af82d` | `6f9e66b` | 41/33 | 38 | K7 B30 audit (3rd-look labels, compare, HUMAN_CHECK) | MEDIUM — a discipline precedent, no engine content |
| 7 | `acde8869` | `801c976` | `6f9e66b` | 41/15 | 67 | K7 v2 retrieval methodology (`QUERY_SPEC.md`, `retrieve.py`, gap lists) | MEDIUM — how to retrieve source claims deterministically |
| 8 | `efbf666d` | `cf6249e` | `6f9e66b` | 41/20 | 27 | K7 Phase1 B30 pilot report + coverage ledger + SHA-256 evidence table | LOW-MEDIUM |
| 9 | `fbd58b68` | `dc888a7` | `6f9e66b` | 41/6 | 29 | "تجربة أ": retrieval measurement + early-stop + quality limits | MEDIUM — a self-limit precedent |
| 10 | `e6974afe` | `88a06d6` | `e06e22c` | 60/37 | 168 | Understanding v2: 315 windows, 136 claims, 71 dated candidates, 13 pairing cards | MEDIUM — concept evidence base |
| 11 | `e91e69b1` | `ffe7add` | `e06e22c` | 60/50 | 734 | Understanding v3/K2 + large GitHub harvest (`SaiStyles…`, `mabdullahns007…`) | MEDIUM — external corpus, includes pre-registration precedent |
| 12 | `5b6d2bd5` | `4c89613` | `e06e22c` | 60/5 | 16 | `source_corpus_v2`, `forex_v1_causal_rerun_feb2025/` (5 files), 1 test | MEDIUM — an older real-data rerun |
| 13 | `b662648b` | `a3eb25e` | `e06e22c` | 60/7 | 64 | K5 trade-building gap research + u3-k3 cards | MEDIUM — the stop/target gap record |
| 14 | `bd0f0622` | `441a963` | `e06e22c` | 60/2 | 68 | u3-k1 pairing cards (32) + concept cards (23) | LOW-MEDIUM |
| 15 | `c59ec6a3` | `54185cc` | `e06e22c` | 60/7 | 59 | K4b trade-management harvest | MEDIUM — management vocabulary |
| 16 | `f3ca06dd` | `567460b` | `e06e22c` | 60/6 | 45 | u3-k3 concept cards + audit (23/23 concepts) | LOW-MEDIUM |
| 17 | `01a0f676` | `ae03f6a` | `292085d` | 115/5 | 15 | 11 PDF volumes of `zzz.txt` + index + splitter | **NONE** — documents, not code |

---

## 2. Detail on the three that matter

### 2.1 `e2c9bda8` — the teacher-example comparison (the closest thing to ground truth)

**What it holds:** four files at the repository root (`b1_teacher_test/`), plus one
modification to `engine_v1/OWNER_DECISIONS.md`. It also **contains the commit
`d9b3831` — `docs(owner): record D2 displacement decision and open B1 questions` — which is the
raw source text** that `OWNER_DECISIONS_D2.md` transcribes on the Era-3 line.

The frozen-set commit recorded inside `TEACHER_RESULTS.md` is `62d8be3`; the JSON digest is
`2e1dc9e1…64fa` and the cases-document digest is `0ea7533f…0490`. Those are the branch's own
claims about its own freeze, quoted here **as claims**, and they are checkable by reading
the file at that commit.

**What it measured** (numbers read from `TEACHER_RESULTS.md`, quoted as that file's own
measurement, not re-run here):

| quantity | value |
|---|---|
| publishers / pages sampled | 4 / 5 |
| gap judgments | 8 |
| swing judgments | 16 (6 positive, 10 collective negative) on 3 series |
| further judgments computed from the source rule | 4 |
| detector calls | 32 (= 8 gap + 24 swing) |
| inputs unchanged by the run | 32 / 32 |
| V2 expectation matches | 32 matched, 0 differ, 0 blocked by missing fields, 0 interface errors |
| gap judgments vs source | 7 agree, **1 declared rule difference** (a zero-width gap: source says "no positive-width gap", V2 leaves it `UNDECIDED`) |
| swing judgments vs source | 16 geometric agreements, 0 differences; plus 4 rule-derived agreements and 4 terminal observations with no source verdict |

**Honest limits it prints about itself** (and these are why it is useful): the examples are
one or two mirrors from a single publisher rather than independent series; prices are
abstract units, not a named market; the partial-field cases were passed to `swing_at`/`fvg_at`
directly and **do not prove** a full `Candle` constructor accepts an incomplete record;
`TradeZoro`'s third candle closure is not stated by the source and was not invented.

**A disclosed process breach, recorded in the branch:** additional searching began before four
indexed pages had been completed. The branch says so instead of hiding it, and says the later
completion does not erase the ordering breach. That is exactly the kind of statement the
reader project needs its records to contain.

**Relation to the target:** HIGH and direct. It is the only place where an *external published
reading* is compared, call by call, with what the engine returns — which is the Level 3
(§7 of `PREREGISTRATION_V1.md`) idea in miniature, already executed once, with its limits
written down.

**Recommendation:** **KEEP AS EVIDENCE.** Read it before building Level 3. Do not merge; do not
copy its JSON into the Era-3 tree without a task that owns that decision (`D3` clause D:
new files only, and `OWNER_DECISIONS.md` is not edited).

### 2.2 `a2387edd` — deliverable 104, the independent verdict

**What it holds:** exactly one new file,
`deliverables/104_INDEPENDENT_FULL_PROJECT_VERDICT_AR.md` (plus nothing else), committed one
step after `51ea54b`.

**What it claims:** that the reader-shaped layer is not a proposal but 12,291 lines of
existing code under `src/trading_system/research/contextual_selection/`, and that the CLI
`run_btc_causal_recommendations.py` is the top-level interface of *this* engine rather than a
separate project.

**Verification performed here:** the line count is **correct** —
`wc -l src/trading_system/research/contextual_selection/*.py` = **12,291** in the Era-3 tree.
The claim about the CLI was not re-derived in this session and stands as the report's claim.

**Relation to the target:** MEDIUM-HIGH. It is a second, independent reading of what the
repository already is — useful precisely because it disagrees with the framing that "the
reader still has to be built".

**Recommendation:** **KEEP AS EVIDENCE**, read for its corrections list. Note that it was
written *before* the 43 commits that added `b1_candles`, `c1_catalog`, the D2 transcription and
the handoff documents, so its picture of the tree is 43 commits stale.

### 2.3 `5eee9692` — superseded, and provably so

**What it holds:** 4 commits beyond `c905f2b`, of which the code content is **already in
Era-3**. Verified: `git diff --stat origin/arena/5eee9692-trading-bot HEAD --
src/trading_system/research/trajectory src/trading_system/research/contextual_selection`
returns **nothing** — byte-identical. Its only unique files are the reports
`83_HANDOFF_VERIFICATION_AND_DIRECTION_DIAGNOSIS_REPORT.md`,
`101_FOREX_DIRECTION_FIX_AND_FILL_CONVENTION_REPORT.md`,
`102_MARKET_LEVEL_INVESTIGATION_EXTENDED_REPORT.md`,
`103_DETAILED_RECONSTRUCTION_AND_LTF_EXPERIMENT.md`.

**Caution:** an earlier read-only audit of this repository recorded reports 101 and 103 as
**withdrawn** because they predate the `next_open` fill fix. That finding is **carried over and
not re-derived here**. Treat these four reports as historical, not as results.

**Recommendation:** **SUPERSEDED.** Nothing to merge; nothing to copy.

---

## 3. The remaining fourteen, in one pass

| branch | unique content, plainly | recommendation |
|---|---|---|
| `46263b03` | `k6/K6_LEAD_VERIFICATION.md`, `K6_QUOTES.jsonl`, `verify_quotes.py`, and a stray file literally named `real hand off` | **LOW** — the quote verifier is a small, reusable evidence tool; the stray file is lint. Read the verifier only. |
| `5b5d18f2` | K7 B30 audit: `AUDIT_REPORT.md`, `AUDIT_THIRD_LOOK.jsonl` (labelled 3rd look), `COMPARE_RESULT.md`, `HUMAN_CHECK.md` (12 statements, seeded selection), a repaired entry-index bug | **MEDIUM** — the third-look labelling and "audit records untouched" discipline is a model for how to report a re-read after a fix. |
| `acde8869` | K7 v2: `QUERY_SPEC.md` written **before** the search, `retrieve.py` (deterministic, 50-word window), 3 gap lists of 2,440 segments each | **MEDIUM** — the only deterministic retrieval implementation in the tree; relevant if the reader must cite source text. |
| `efbf666d` | K7 Phase1 B30 pilot report + coverage ledger (16/25 chunks, 450/450 quotes) + SHA-256 evidence table | **LOW-MEDIUM** — evidence formatting, no engine content. |
| `fbd58b68` | "تجربة أ": criteria frozen before reading, partial-coverage log, retrieval measurement, early stop documented with its quality limits | **MEDIUM** — a worked example of stopping early *and publishing the stop*. |
| `e6974afe` | Understanding v2 tasks 1–4: 315 windows over 21 concepts, 136 claims, 71 dated candidates, 13 pairing cards, 18 narrated events | **MEDIUM** — the concept evidence base the reader's vocabulary should cite. |
| `e91e69b1` | Understanding v3/K2 (23 THIN cards, 39 claims, 58 windows; verifier 42/42) **plus** a large external harvest (`SaiStyles…@f9e3a418`, `mabdullahns007…@190dc49b`) — 734 files | **MEDIUM** — largest corpus addition; includes a public study that itself pre-registers and reports flats. Read its README before trusting any statistic inside it. |
| `5b6d2bd5` | `source_corpus_v2` (5 files), `forex_v1_causal_rerun_feb2025/` (5 files: results of a dev-Jan / eval-Feb run), one test hardening | **MEDIUM** — an earlier real-data rerun. Its Feb-2025 window is **not** out-of-sample (carried-over finding), so it is history, not evidence. |
| `b662648b` | K5 trade-building gap research (`playbook/k5`, 19 files) + u3-k3 cards | **MEDIUM** — this is the record of what the sources do **not** say about building a trade; the `KNOWLEDGE_GAP` inventory that `D3` clause C depends on. |
| `bd0f0622` | u3-k1: 32 pairing cards + 23 concept cards + tools | **LOW-MEDIUM** — card formatting and pairing method. |
| `c59ec6a3` | K4b trade-management harvest (14 files) + u3-k3 | **MEDIUM** — management vocabulary; relevant only to a later phase, since management is `C5.5` = «لم يبدأ». |
| `f3ca06dd` | u3-k3 final audit: 23/23 concepts, 266/266 checks, `AUDIT.md`, `gaps.md` | **LOW-MEDIUM** — a completeness record, not a capability. |
| `ad9c5dec` | deliverables 87–99 and 101–103, `PROJECT_HANDOFF_AR.md`, 24 test files, u3-k1/k3 cards, `contextual_selection_v1` design docs (11 files) | **HIGH** — the only branch that documents the reader's own modules (87–96) *and* ships their tests. Read the `contextual_selection_v1` documents before designing anything on top of those modules. |
| `01a0f676` | 11 PDF volumes of `zzz.txt` + `zzz_parts_INDEX.md` + splitter script | **NONE for this target.** Documents, and the repo policy already forbids pushing archives. Do not merge PDFs. |

---

## 4. Patterns worth recording (and one correction)

1. **Everything in the "K" and "u3" families is document work about sources,** not engine
   work. It matters to the reader because a reader that cannot cite a source cannot claim a
   reading — but none of it changes behaviour.
2. **The corpus families** (`e6974afe`, `e91e69b1`) are additive evidence, and both disclose
   their own verification counts. They do not contain thresholds to import.
3. **The engine code on every branch is either Era-3 code or older Era-3 code.** No branch
   carries a competing implementation of `contextual_selection`; `5eee9692` was checked
   byte-for-byte, and it is identical.
4. **Correction to an earlier note in this project's own audit trail:** the path
   `research/trajectory/*` does exist, at
   `project/trading_project/src/trading_system/research/trajectory/` — **17 files** in the
   Era-3 tree. It is not absent. The four modules that were searched for by the name
   `trade_plan.py` / `monitoring.py` / `decision_layer.py` / `analysis_lifecycle.py` live in
   `src/trading_system/research/contextual_selection/`, not in `trajectory/`.

---

## 5. What the triage does and does not recommend

**Does:** reading four of these before building anything —
`e2c9bda8` (published-example ground truth), `ad9c5dec` (the reader's own documentation and
tests), `acde8869` (`QUERY_SPEC.md` discipline for source-cited retrieval), and `a2387edd`
(independent verdict, with the 43-commit staleness caveat).

**Does not:** merge, rebase, cherry-pick, copy code, copy expectations, or open a PR. Every
read was `git show <ref>:<path>` — read-only. Per Art. 19, other branches are read for
comparison; code is never copied from them.

---

## 6. What this does NOT establish

- It does **not** verify the content of any branch's claims beyond the specific items marked
  as checked (`e2c9bda8`'s numbers are that file's own; `a2387edd`'s 12,291-line claim was
  re-measured here; `5eee9692`'s code equality was re-measured here). Everything else is
  described from commit subjects and file paths.
- It does **not** run any branch's tests. Only the Era-3 tree's own fixtures were run, and
  those counts are reported in the final message, not here.
- It does **not** judge whether any branch's research is true. "23/23 concepts verified" is a
  claim about internal consistency, not about the market.
- It does **not** assess the 20 already-contained branches (they add nothing new relative to
  `fd43dc29` by definition).
- It does **not** assess `main` beyond noting its single trivial commit.
- It does **not** endorse merging `e2c9bda8` or `ad9c5dec`; it recommends **reading** them.
  Under `D3` clause D, any import of their content is a new task with its own authorisation.
- It does **not** establish that the carried-over withdrawal finding for reports 101/103 is
  correct — that is flagged as carried over and unverified in this session.
