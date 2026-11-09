# قرار المالك `D3` — فتح مرحلة تقييم على بيانات حقيقية (مقترح لم يُعتمد)

**Status: PROPOSAL — NOT APPROVED. This document has no force until the owner signs §6.**

**TYPE:** `DESIGN ONLY`. No code, no market data, no edit to any existing file.
**Scope of the proposal:** the *smallest* constitutional amendment that opens one new phase
(`HOLDOUT_V1`) and nothing else. If any clause below can be dropped and the phase still
runs, drop it — the amendment is meant to be minimal, not convenient.

**Why an amendment is needed at all:** every rule quoted in §1 is currently in force and
each one of them, read literally, forbids part of the requested phase. A phase cannot be
opened by silence. It is opened by a named decision that says exactly which sentence
changes, and which sentences do **not**.

**Quote convention.** Arabic text inside `>` blocks is copied byte-for-byte from the file
and article named above it. English glosses are my translation and are marked
`(gloss)`. No quoted file is modified by this document.

| clause | opens | amends |
|---|---|---|
| A | evaluation on real data, one frozen window at a time | Art. 5 (§2.5) + §7 table row 1 |
| B | hypothetical entry / invalidation / target fields | Art. 15 (§2.15) + Constitution §11 |
| C | context-relative measurements (rank / ratio inside one chart) | Art. 1 (§2.1) |
| D | zero edits to CLOSED modules | Art. 12 (§2.12) + Art. 16 (§2.16) + Art. 20 |

---

## 1. The four clauses

### Clause A — a real-data evaluation phase

**Rule being amended — `project/trading_project/docs/handoff/AGENT_HANDOFF_DETAILED_2026-11-09.md`, §2.5 «المادة 5 — لا نتائج على بيانات حقيقية (ولهذا سببان)»:**

> 1. **أخلاقي/علمي:** لا نُعلن شيئًا عن جدوى مفهوم قبل أن يكون تعريفه مكتملًا ومدققًا.
> 2. **منهجي:** نتيجة على بيانات حقيقية قبل تجميد التعريف = `look-ahead` وتلويث الاختيار.
>
> لذلك: خطوات `B` و`C` تُختبر على شموع يدوية (`FIXTURE`) فقط، ولا تُقرأ بيانات سوق، ولا يُنتج
> أداء.

**Also amended — same file, §7 table:**

> | قراءة بيانات سوق / تشغيل على بيانات حقيقية | **ممنوع** في خطوات `B`/`C` | شموع `FIXTURE` فقط |

**Proposed text (A):**

> Reading real market data is permitted **only** inside the named phase `HOLDOUT_V1`, and
> **only** after a pre-registration file exists in the tree that fixes: the window(s), the
> metrics, the baseline, the cost model, and the stopping rules. The first such file is
> `docs/research/holdout_v1/PREREGISTRATION_V1.md`.
>
> Within `HOLDOUT_V1`:
> 1. **One look per window.** A window is used once. Re-running the same window after
>    changing anything that could affect the outcome destroys the window and must be
>    recorded as `WINDOW_BURNED` in the pre-registration file's successor.
> 2. **No tuning on the evaluation window.** Development work may touch only a declared
>    development window; the evaluation window is read exactly once, and its result is
>    published whether it is favourable, unfavourable, or empty.
> 3. **Definitions stay frozen.** If a definition must change after a window is opened,
>    the change is a new named version (`V2`, `V3` …) and the window that was opened under
>    `V1` is reported under `V1`, not silently re-run under the new version.
> 4. **No performance verdict is created by the phase.** Results are reported as measured
>    quantities with their own limits, never as an edge, an accuracy, or a claim that the
>    system "works". `selection_quality = NOT_ESTABLISHED` remains the label unless a
>    separate, pre-registered estimand exists that could establish it — and none exists
>    today.
>
> Steps `B` and `C` remain fixture-only. `HOLDOUT_V1` does not extend to them.

**Retained unchanged:** the two *reasons* in Art. 5 stay alive inside the new phase — that
is precisely why clauses (2) and (3) exist. The article is narrowed in scope, not repealed.

---

### Clause B — hypothetical entry / invalidation / target, labelled

**Rule being amended — `AGENT_HANDOFF_DETAILED_2026-11-09.md`, §2.15 «المادة 15 — اللغة والادعاءات المحظورة»:**

> قبل وجود عقد تنفيذ كامل، ممنوع في أي مخرج: `WIN` / `LOSS` / `profitable` / `PnL` /
> `entry` / `fill` / `stop` / `target` / `trade result`.
> المسموح: مصطلحات وصفية محايدة (`direction_favorable_excursion`, `CONTRADICTED`,
> `RIGHT_CENSORED_AS_OF_BOUNDARY`, `RESEARCH_REFERENCE_MARK`, …).

**Also amended — `docs/handoff/AI_COLLABORATION_CONSTITUTION_CURRENT.md`, §11 «اللغة والادعاءات المحظورة»:**

> قبل وجود trade contract كامل، ممنوع:
>
> ```text
> WIN / LOSS
> profitable / unprofitable
> PnL
> entry
> fill
> stop
> target
> trade result
> ```
>
> مسموح فقط factual neutral terms مثل:
>
> ```text
> research_reference_price
> direction_favorable_excursion
> direction_adverse_excursion
> CONTRADICTED
> SUPERSEDED
> OBSERVED_DIRECTION_ESTABLISHED
> RIGHT_CENSORED_AS_OF_BOUNDARY
> ```

**Note on the current state:** the trigger condition in both quotes is *"before a complete
trade contract exists"*. No such contract exists in the tree. `trade_plan.py` produces
`TradePlan` / `PlanVersion` objects with components, but a plan object is not a trade
contract with defined execution, sizing and cost. So the prohibition is in force, and
clause B is what lifts it **for one layer only**.

**Proposed text (B):**

> A field that denotes a hypothetical entry price, hypothetical invalidation price, or
> hypothetical target level is permitted **only** when all four of the following hold in
> the same output record:
>
> 1. the field name carries the prefix `HYPOTHETICAL_` (e.g. `HYPOTHETICAL_ENTRY`,
>    `HYPOTHETICAL_INVALIDATION`, `HYPOTHETICAL_TARGET`);
> 2. the record carries `selection_quality = NOT_ESTABLISHED`;
> 3. the record carries `reference_is_execution_price = False` and a cost field computed
>    from the same bid/ask source as the price, never zero by assumption;
> 4. the record carries `contract_status = HYPOTHETICAL_NO_EXECUTION_CONTRACT`.
>
> Permitted additionally, in the same records only: `R` (risk-multiple of the declared
> invalidation distance), `MAX_DRAWDOWN_R`, `NEGATIVE_R_STREAK`, and per-decision
> `OUTCOME_R`. These are measurements of a hypothetical sequence, not trade results.
>
> Still forbidden everywhere, in every layer, with no exception created by this clause:
> `WIN` / `LOSS` / `profitable` / `unprofitable` / `PnL` / `accuracy` / `edge` /
> `confidence %` / `fill` (a fill is an assertion about an execution that did not happen).
> A streak of negative `R` is reported as `NEGATIVE_R_STREAK`; it is never renamed a
> losing streak in a machine-readable field.
>
> Clause B expires automatically the moment a real execution contract exists: at that
> point the label must be replaced by a genuine contract, not extended.

---

### Clause C — context-relative measurements

**Rule being amended — `AGENT_HANDOFF_DETAILED_2026-11-09.md`, §2.1 «المادة 1 — لا رقم بلا مصدر»:**

> كل رقم في الشيفرة يجب أن يكون واحدًا من:
>
> | التصنيف | المعنى | مثال حقيقي في الشيفرة |
> |---|---|---|
> | `SOURCE_NUMBER` | رقم مطبوع حرفيًا في مصدر، مع معرّف الادعاء | `0.60`, `0.75`, `0.80`, `2.0`, `3.0`, `10`, `1.5`, `14`, `0.5` |
> | `ENGINEERING_CHOICE` | قرار بناء **معلن قبل الشيفرة**، مسببه صراحة "أقل مدخلات/أبسط حساب" لا "أفضل" | نافذة المقارنة تُطلب صراحةً من المستدعي، ولا تُختار من مدى `3–5` |
> | `KNOWLEDGE_GAP` | لا رقم، يُطبع السؤال | `KNOWLEDGE_GAP: ATR formula …` |
> | `FIXTURE` | رقم في ملف اختبار فقط، مصنوع يدويًا | كل أسعار `EXPECTED_*.json` |
>
> **ممنوع تمامًا:** متوسط بين رقمين، أو تقريب عتبة، أو "قيمة افتراضية معقولة"، أو
> `0.5%` أو `ATR` أو `2 pips` لأنها "شائعة في السوق".

**Also relevant — same file, §2.8, on printing gaps rather than resolving them by silence, and
`engine_v1/COVERAGE_TABLE_C1.md` §E, which records every place a spec promises a number the
sources do not print.**

**Proposed text (C):**

> A measurement that is **relative to the same chart up to the same time `t`** does not
> require a `SOURCE_NUMBER`, provided it introduces no new constant. Permitted forms are
> exactly:
>
> - a **rank** of one observable object among the set of objects observable at `t`;
> - a **ratio** of two lengths measured on the same chart at `t` (e.g. distance to level
>   `X` divided by distance to level `Y`);
> - a **percentile position** of a value within the distribution of that same value
>   computed on data at or before `t`.
>
> Conditions attached to every such number:
>
> 1. it is printed with `RELATIVE_ONLY = True` and with its **denominator** (what set it
>    is ranked or divided within), because a rank without its set is a hidden threshold;
> 2. it is **never** converted into a fixed cutoff. `>= 0.5`, `>= 3`, `top 2` and their
>    relatives remain forbidden unless a source prints them;
> 3. it is computed from `candles[:t+1]` only and the `last_read` index is printed with it
>    (Art. 10 is unchanged);
> 4. it never enters a `live` decision path without the same label; it is permitted first
>    in the research and holdout layers.
>
> Where a comparison needs a *decision* (this zone over that zone), that decision is a
> `KNOWLEDGE_GAP` until a source or the owner supplies priority — see
> `PAIRWISE_SELECTION_DESIGN_V1.md` §5. A relative number describes; it does not rank.

---

### Clause D — zero edits to CLOSED modules, new files only

**Rule being amended — `AGENT_HANDOFF_DETAILED_2026-11-09.md`, §2.12 «المادة 12 — الإغلاق والتدقيق»:**

> - أي تعديل بعد الإغلاق = `PATCH ONLY Module X Vn → Vn+1`.

**And §2.16 «المادة 16 — الانضباط على الشجرة (Git)»:**

> - لا `git add -A` أبدًا؛ **التزم بمسار صريح** لكل ملف.
> - **كل جولة تغيّر ملفات تُلتزم وتُدفع** (لا عمل معلّق في الشجرة).
> - لا إعادة كتابة تاريخ (`force push`, `reset --hard`, `rebase` على تاريخ منشور).
> - الملفات المحمية لا تُلمس، ويُتحقق منها `SHA-256` + الحجم في نهاية العمل.

**And the decisive table, §7:**

> | تعديل `b1_candles/**` | **ممنوع** | مغلقة؛ أي تغيير يبدأ بخطوة جديدة |
> | تعديل `src/trading_system/**` أو `tests/**` | **ممنوع** | إلا `PATCH ONLY` بتصريح + ترقيم إصدار |
> | تعديل `information_time.py` | **ممنوع مطلقًا** | يُتحقق `sha256` + الحجم في النهاية |

**Proposed text (D):**

> The `HOLDOUT_V1` phase adds **files only**. It edits nothing that exists at the commit
> that opens the phase, including but not limited to:
>
> - CLOSED `src/trading_system/research/information_time.py` (protected: hash + size, §3);
> - CLOSED `docs/research/huddleston_study/engine_v1/b1_candles/**`;
> - `docs/research/huddleston_study/engine_v1/c1_catalog/**`;
> - `src/trading_system/research/contextual_selection/**` (consumed by import, never
>   patched: the new call site lives in a **new** module, see
>   `PAIRWISE_SELECTION_DESIGN_V1.md` §3);
> - `docs/research/huddleston_study/engine_v1/OWNER_DECISIONS.md`,
>   `OWNER_DECISIONS_D2.md`, `external_sources/**`.
>
> If a genuine defect is found in a CLOSED module, the phase **stops** and reports it. It
> does not fix it. Repair is a separate `PATCH ONLY` task with its own version bump, and
> that task is not authorised by `D3`.
>
> This clause narrows the `PATCH ONLY` escape in Art. 12 rather than removing it: the
> escape remains available, but not inside this phase.

---

## 2. Explicitly KEEP untouched

These are not amended, not narrowed, and not reinterpreted by `D3`. Each is quoted so that
a later reader cannot claim ambiguity.

| # | rule | file + article | quote |
|---|---|---|---|
| K1 | causal reads only | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.10 | «دالة تُقيّم عند الفهرس `t` تقرأ `candles[:t+1]` **فقط**، وتطبع `last_read` مع النتيجة.» / «لا `shift(-1)`، ولا `centered rolling`، ولا تعديل صف تاريخي بعد معرفة لاحقة.» |
| K1b | causal reads only | `AI_COLLABORATION_CONSTITUTION_CURRENT.md` §4 | «```text output[i] may depend only on information available at or before i ```» |
| K2 | pre-registration before results | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.4 | «```text (1) مواصفة (2) ملف توقعات EXPECTED_*.json   ← يُلتزم ويُدفع وحده (3) شيفرة                        ← تُكتب لتطابق التوقعات ```» |
| K3 | no editing expectations after a failure | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.4 | «ملف التوقعات **لا يُعدَّل بعد رؤية فشل**. إن فشل اختبار فإما تُصلح **الشيفرة** (لأن التوقّع هو العقد)، أو تُسجّل الحالة في "قائمة عدم التطابق" وتتركها ظاهرة.» |
| K3b | same rule, table form | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §7 | «| تعديل ملف توقعات بعد فشل | **ممنوع** | أصلح الشيفرة أو سجّل عدم التطابق |» |
| K4 | same-bar order unknown | `AI_COLLABORATION_CONSTITUTION_CURRENT.md` §10 | «إذا OHLC bar يحمل favorable وadverse extremes معاً: ```text SAME_BAR_ORDER_UNKNOWN ```» |
| K5 | censored ≠ failure | `AI_COLLABORATION_CONSTITUTION_CURRENT.md` §13 | «- censored ليس failure أو zero.» / «- B1 censored لا يُعدل عند B2 maturity.» |
| K6 | protected file hash | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §4.4 | `path : project/trading_project/src/trading_system/research/information_time.py` / `sha256: 72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace` / `size  : 12216 bytes` |
| K7 | final rule, verbatim | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.20 / `AI_COLLABORATION_CONSTITUTION_CURRENT.md` §21 | «إذا لم يكن الشيء معروفاً عند information time t، فلا يدخل قرار t. / إذا كان الشيء outcome من المستقبل، يبقى في research world. / إذا لم يكن العقد معرفاً، لا نخترع default. / إذا كانت الوحدة CLOSED، لا نعدلها دون versioned authorization. / إذا نجحت الاختبارات، هذا لا يعني الإغلاق. / إذا لم نستطع إثبات claim، نصرّح بالحدود أو نتوقف.» |
| K8 | old code is not a source | `engine_v1/OLD_PIPELINE_DO_NOT_REUSE.md` + Art. 18 | «ولا تُنقل قاعدة ولا رقم ولا عتبة من هذه الملفات إلى `engine_v1`» |
| K9 | no code copied from other branches | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.19 | «**يُقرأ للمقارنة، ولا يُنسخ منه كود.**» |
| K10 | tests passing ≠ closure | `AGENT_HANDOFF_DETAILED_2026-11-09.md` §2.12 | «نجاح الاختبارات **ليس** إغلاقًا.» |

**Consequence of K5 for this phase:** a decision whose outcome is not knowable inside the
window is `CENSORED`. It is not a failure, not a zero, and not a negative `R`. It is counted
separately and excluded from `R` aggregates. Clause B does not change this.

**Consequence of K4 for this phase:** when one bar contains both the hypothetical target and
the hypothetical invalidation, the decision is `SAME_BAR_ORDER_UNKNOWN`, is excluded from
the judgeable set, and is counted. It is never resolved by loop order.

**Consequence of K2/K3 for this phase:** `PREREGISTRATION_V1.md` is the `EXPECTED_*` file of
this phase. It is committed **before** the first read of any window, and it is not edited
after a result is seen. A needed change is a new file, `PREREGISTRATION_V2.md`, and the
burned window is recorded as burned.

---

## 3. Protected file — current measured state

Measured in this session, after the fast-forward that opened this work:

```text
path   : project/trading_project/src/trading_system/research/information_time.py
sha256 : 72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace
size   : 12216 bytes
```

`sha256sum` and `wc -c` were run on the file in the working tree, not on a memory of it.
This block is a copy of a measurement, not an instruction to trust a previous report.
`D3` does not touch this file, and clause D forbids touching it inside the phase.

---

## 4. What `D3` deliberately does not authorise

| item | status | why |
|---|---|---|
| tuning any parameter on an evaluation window | **forbidden** | would make the window non-blind; Art. 5's methodological reason, kept by clause A.3 |
| a second look at the same window | **forbidden** | a second look is a first look with extra information |
| inventing a threshold to make a comparison decidable | **forbidden** | Art. 1 stands; clause C forbids fixed cutoffs |
| editing any CLOSED module, including the 10 `contextual_selection` modules | **forbidden** | clause D |
| creating a new engine or a second structure state machine | **forbidden** | Constitution §13: «لا second structure state machine.» |
| merge, rebase, or copy from any other branch | **forbidden** | Art. 16, Art. 19 |
| a "win rate", "accuracy", "profitability" or "edge" statement | **forbidden** | clause B keeps these forbidden without exception |
| pushing this phase's outputs into the live path | **forbidden** | Constitution §5 (`LIVE WORLD` / `RESEARCH WORLD` separation) |
| changing `reference_variant` or any D1/D2 decision | **forbidden** | owner decisions are not amended by a phase opener |

---

## 5. Text the owner is asked to sign

If the owner accepts, the amendment becomes `D3` with the following effective text, and a
copy is appended to a **new** file (not to `OWNER_DECISIONS.md`, per clause D):

```text
D3 — HOLDOUT_V1 phase opener
Status: OWNER_APPROVED
(a) real-data evaluation permitted in HOLDOUT_V1 only, one frozen window at a time,
    published regardless of outcome, no tuning on the evaluation window.
(b) HYPOTHETICAL_ entry / invalidation / target fields permitted with
    selection_quality = NOT_ESTABLISHED, contract_status = HYPOTHETICAL_NO_EXECUTION_CONTRACT,
    cost from bid/ask included; WIN / LOSS / PnL / accuracy / edge / fill remain forbidden.
(c) context-relative rank / ratio / percentile within the same chart up to t permitted,
    printed with RELATIVE_ONLY and its denominator; never a fixed cutoff.
(d) zero edits to existing files; new files only; CLOSED modules are imported, never patched.
Unchanged: causal reads only, pre-registration before results, no editing expectations after
failures, SAME_BAR_ORDER_UNKNOWN, censored is not failure or zero, protected file hash.
```

The owner is asked to decide, in this order:

1. accept / reject `D3`;
2. if accepted, the **BTCUSDT month list** for the second window (currently a placeholder in
   `PREREGISTRATION_V1.md` §2 — no month is invented there);
3. whether `HOLDOUT_V1` may read the EURUSD 2024 window before or after the BTC window.

---

## 6. What this does NOT establish

- It does **not** amend anything yet. No rule quoted above has changed; the file is a
  proposal and is inert until signed.
- It does **not** claim the phase is scientifically adequate. Clause A.4 states the opposite:
  no estimand exists today that could establish `selection_quality`.
- It does **not** create, and cannot create, a profitability or accuracy claim. Those words
  remain forbidden by clause B itself.
- It does **not** decide any metric, baseline, window or cost model. Those live in
  `PREREGISTRATION_V1.md` and are labelled there as `SOURCE_NUMBER` / `ENGINEERING_CHOICE` /
  `KNOWLEDGE_GAP`.
- It does **not** verify that any of the ten `contextual_selection` modules are correct. They
  are consumed as found.
- It does **not** authorise a patch to any CLOSED module, and it explicitly refuses the
  `PATCH ONLY` escape inside the phase.
- It does **not** assert that the protected file is unchanged since the previous session —
  only that it measures `72b03ca6…4d74ace` / `12216` bytes at the time of this file.
