# PATCH LOG 001 — `holdout_v1/` documentation patch, 2026-11-09

Scope: **three existing documents under `holdout_v1/`**, patched under the owner's written
authorisation for this task (Phase 2). Nothing else in those files was touched. No file under
`src/`, `tests/`, `engine_v1/`, `external_sources/`, `dev_month_v0/` or any `OWNER_DECISIONS*.md`
was modified. Every replacement below was applied by exact-string match with an assertion that
the string occurred **exactly once**, so a silent second edit is impossible.

Six changes, in file order. "old lines" / "new lines" are 1-based line numbers in the file
before and after the change.

---

## P-01 — `PREREGISTRATION_V1.md`, old lines 85–88 → new lines 85–88

**Reason:** the owner never stated that he had not viewed BTCUSDT `2026-05`. The file asserted
"the owner states he has not viewed that data". That is a claim the record does not support and
must read UNKNOWN.

**Old text**

```text
- **`2026-05`** is outside the draw range and therefore cannot be drawn. Separately, an
  earlier read-only audit of this repository recorded `2026-05` as already used in an
  evaluation context, while the owner states he has not viewed that data in this repository's
  evaluation context. **Both records are kept and neither is resolved here**; the item is
  excluded by range, not by this note.
```

**New text**

```text
- **`2026-05`** is outside the draw range and therefore cannot be drawn. Separately, an
  earlier read-only audit of this repository recorded `2026-05` as already used in an
  evaluation context. The owner's viewing state for that data is **UNKNOWN (not answered)**:
  no statement exists in which the owner says whether he viewed it, so this file does not and
  may not claim that he did not. The item is excluded by range, not by this note.
```

---

## P-02 — `PREREGISTRATION_V1.md`, old line 124 → new line 124

**Reason:** same defect, second occurrence, inside the `OWNER_STATEMENT_IN_CHAT` list.

**Old text**

```text
- BTCUSDT `2026-05` — not viewed in this repository's evaluation context.
```

**New text**

```text
- BTCUSDT `2026-05` — owner's viewing state: UNKNOWN (not answered).
```

---

## P-03 — `PREREGISTRATION_V1.md`, new lines 645–668 (inserted before `## 10.`)

**Reason:** record the aborted first dev attempt and declare the next dev month **before** any
data is loaded, so the declaration cannot be adjusted after seeing a result.

**Inserted text** (new section, 24 lines)

```markdown
### 9A. Dev-run record — first attempt aborted, next dev month declared

Recorded on 2026-11-09, **before any bar of the next attempt is loaded**, so that the choice
below cannot be adjusted after the fact.

- **First dev attempt** — `EURUSD 5m`, decision month `2021-03`, history from `2021-01-01`,
  default configuration, one run. It was aborted by the operating system (out-of-memory kill of
  the Python process) after `12 min 59 s`, with resident memory at `3,870,276 kB` on a
  `3,939 MB` machine. The kill happened **during the warm-up, before the first decision
  instant**: `decisions = 0`, `plans = 0`, `cases = 0`, and the raw output directory holds a
  `264`-byte log with no result file. **No result was seen.** Record:
  `dev_month_v0/SUMMARY_V0.md`.
- **Consequence for `2021-03`.** Because nothing was observed, `2021-03` is **not burned** as an
  evaluation window in the sense of §8 — but it is also **not eligible as a blind window**,
  since its bars were read into a decision process. It is treated as `LOADED_NO_RESULT` and is
  never used as an out-of-sample window.
- **Next dev month: `2021-06`** — tag `ENGINEERING_CHOICE`, declared here before any load.
  Reason for a *new* month rather than repeating `2021-03`: a window is read once (§2.1), and
  re-reading `2021-03` under a new wrapper is a second look at the same bars even when the
  first look produced no decision.
- The next attempt is **not authorised by this record**. It requires
  `ict_recipe_v1/MEMORY_ANALYSIS_V0.md` and `ict_recipe_v1/DEV_RUN_PLAN_V1.md`, both of which
  are design only.
```

**Unchanged:** the section numbering of §10 and the closing "What this does NOT establish" list;
§9A was inserted as a sub-section so no existing section number moved.

---

## P-04 — `OWNER_DECISION_D3.md`, new lines 322–337 (inserted before "The owner is asked to decide")

**Reason:** Phase 2(c). Clause (d) as written forbids any `PATCH ONLY` fix inside `HOLDOUT_V1`,
including the memory-bounding fix the aborted run makes necessary. The clause **text is
unchanged**; the note records the consequence and forces an owner decision before signing.

**Inserted text**

```markdown
> **NOTE on clause (d)** — added 2026-11-09. This note does **not** change the clause text
> above; it records a consequence the owner must weigh before signing.
>
> As written, clause (d) forbids *any* edit to an existing file inside `HOLDOUT_V1`, including a
> `PATCH ONLY` repair. The first dev attempt was killed by the operating system with resident
> memory at `3.87 GB` of a `3.94 GB` machine, before it reached a single decision
> (`dev_month_v0/SUMMARY_V0.md`). Bounding that memory without touching any existing file has
> **not** been shown to be possible; if it turns out to require an edit to a closed module,
> clause (d) as written makes the fix impossible inside the phase.
>
> The owner must therefore decide, **before signing**, one of two things:
> **(i)** such fixes are done **before** the phase opens — i.e. now, in the design phase, which
> is what `ict_recipe_v1/` sets out; or **(ii)** clause (d) is relaxed to permit `PATCH ONLY`
> inside the phase under a declared, logged procedure. Until one of the two is recorded,
> clause (d) is read literally and nothing is patched.
```

**Not changed:** the signed-text block at lines 307–320, including line 317
`(d) zero edits to existing files; new files only; CLOSED modules are imported, never patched.`

---

## P-05 — `OWNER_DECISION_D3.md`, old lines 325–326 → new lines 341–344

**Reason:** Phase 2(b). The item said the BTCUSDT month list was "currently a placeholder in
`PREREGISTRATION_V1.md` §2 — no month is invented there". That sentence is stale: §2.3 now
records a drawn list (`2022-11`, `2022-02`, `2023-11`, `2022-09`, `2024-07`, `2023-09`).

**Old text**

```text
2. if accepted, the **BTCUSDT month list** for the second window (currently a placeholder in
   `PREREGISTRATION_V1.md` §2 — no month is invented there);
```

**New text**

```text
2. if accepted, to **confirm the BTCUSDT month list** already drawn in
   `PREREGISTRATION_V1.md` §2.3 (`2022-11`, `2022-02`, `2023-11`, `2022-09`, `2024-07`,
   `2023-09`). This item is no longer a choice of months: the draw is recorded, and
   re-drawing after the fact is the failure mode pre-registration exists to prevent;
```

---

## P-06 — `OWNER_DECISION_D3_SUMMARY_AR.md`, inserted line 25 (+ blank line 26)

**Reason:** Phase 2(c) requires the Arabic summary to carry the same clause-(d) note.

**Inserted text** (one paragraph, Arabic)

```text
> **ملاحظة على البند (د):** بصيغته الحالية يمنع البند (د) أي إصلاح `PATCH ONLY` داخل المرحلة — بما في ذلك إصلاح الذاكرة الذي أوقف أول محاولة تطوير — وعلى المالك أن يقرّر قبل التوقيع: إمّا أن تُنجَز هذه الإصلاحات **قبل** فتح المرحلة، وإمّا أن يُخفَّف البند (د) ليسمح بها داخلها؛ وحتى يُسجَّل أحد القرارين يُقرأ البند (د) حرفيًا.
```

---

## Net effect on the three files

| file | before | after | change |
|---|---|---|---|
| `PREREGISTRATION_V1.md` | 682 lines | 706 lines | 2 lines replaced in place, 24 inserted |
| `OWNER_DECISION_D3.md` | 347 lines | 365 lines | 2 lines replaced by 4, 16 inserted |
| `OWNER_DECISION_D3_SUMMARY_AR.md` | 33 lines | 35 lines | 1 paragraph + 1 blank inserted |

Nothing else changed: `git diff --stat` for this patch reports
`3 files changed, 50 insertions(+), 6 deletions(-)`.

## What this does NOT establish

- It does not make `D3` approved: the clause text is untouched and `D3` remains a proposal.
- It does not resolve the `2026-05` question: it changes what the file *claims* to what is
  **known** (nothing), and no owner answer exists.
- It does not authorise, schedule or perform any run, and it loads no data.
- It does not establish that the next dev month (`2021-06`) is clean, unrepresentative, or
  comparable to `2021-03`; it is one declared dev month and nothing more.
- It does not fix the engine: the memory behaviour is unchanged and is analysed, not patched.
