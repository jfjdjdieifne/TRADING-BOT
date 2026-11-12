# جدول التغطية `C1` — أين ذهبت كل فكرة في البحث

**المسار:** `project/trading_project/docs/research/huddleston_study/engine_v1/COVERAGE_TABLE_C1.md`
**التاريخ:** 2026-11-09 (UTC)
**الالتزام الأساس:** `1a06b64fa5c4c5efd343d0ef8f6cd16a2efa5c8c`
**الطبقة:** `TIER2` في كل سطر. لا يُنسب شيء هنا إلى أي شخص.
**الحالة:** تحليل للقراءة فقط. لا شيفرة جديدة، ولا بيانات سوق، ولا تعديل على أي ملف موجود، ولا نتيجة أداء، ولا نسبة ثقة.
**الغاية:** إثبات أن كل فكرة في البحث لها مكان: إما نفّذت بدالة مسمّاة، أو رُفضت بسبب مكتوب، أو سُجّلت فجوةً بنصها، أو لم يكن لها مصدر صالح.

---

## 0. المنهج — ما فُتح فعلًا

| # | الملف | ما أُخذ منه |
|---|---|---|
| 1 | `external_sources/o_full_setup_catalog_stage1.md` | 30 مصطلحًا من القسم `C` (السطر 730: «30 terms (C1: 4, C2: 10, C3: 9, C4: 2, C5: 5)») |
| 2 | `external_sources/p_stage2_batch1_stop_target_news.md` | `V-STOP-1…17`، `V-TP-1…12`، `V-NW-1…11`، `V-RR-1…7`، و13 بلوك `CONFLICT` |
| 3 | `external_sources/q_stage2_batch2_entry_zones.md` | مجموعات الدفعة 2 — تُقرأ للمقارنة فقط، لأن `r` يلغيها |
| 4 | `external_sources/r_stage2_batch2b_corrections.md` | **الجدول النهائي `E1…E6`** (75 مجموعة) و`CONFLICT-OB-A/B/C/D` و`ALT-CONVENTION-BRK-A/B` — هو المرجع ويُلغي `q` |
| 5 | `BUILD_STEP_B1_DESIGN_V2.md` | §4 `V-A-00…04`، §5 `V-B-00…03`، §6 `V-C-01…05`، §7 `E1…E5`/`V-E-00/01`، §8 `F1…F6`/`V-D-01…04` |
| 6 | `OWNER_DECISIONS.md` | `D1` (مستوى الجرف، `V-E-EQH`، سؤال «أي تأرجح سابق») وقسم `D2 research` |
| 7 | `BUILD_STEP_C1_SPEC.md` | §§3–6 (الأبعاد والنسخ والمرجع)، §9 (سجل الأرقام)، §10 (فهرس الفجوات)، §12 (عدد الحالات) |
| 8 | `c1_catalog/order_block.py`، `liquidity_sweep.py`، `displacement.py`، `common.py`، `test_c1.py` | فُتحت سطرًا سطرًا؛ أسماء الدوال أدناه منقولة منها |
| 9 | `b1_candles/swing.py`، `b1_candles/fvg.py`، `b1_candles/candle.py` | `V-A-00` و`V-B-00` |

**تشغيل التحقق (بلا بيانات سوق):** `python3 c1_catalog/test_c1.py` ← `cases: 74`, `checks: 802`, `failures: 0`, `ALL EXPECTATIONS MET`.
توزيع الحالات: كتلة الأوامر 34، جرف السيولة 15، الإزاحة 25. حالات الرفض: 13 / 6 / 6 (المواصفة §12 تطلب ≥6 / ≥3 / ≥3 ← متحققة). حالات غير مغلقة: 1 / 1 / 2 (المواصفة تطلب ≥1 لكل مفهوم ← متحققة).

**قاعدة الوسم:** لا يُمنح `CODED_*` إلا لدالة وُجدت بالفتح. وحيث تقول المواصفة «منفّذ» ولا يوجد في الشيفرة شيء ← `MISMATCH_SPEC_CODE`. لا `PLANNED_NEXT` في هذا الجدول لأن الشجرة لا تحمل أي وثيقة خطوة لاحقة (`C2` أو `C3`) — انظر §F.

---

## A. المصطلحات الثلاثون (المرحلة 1)

حالة المصطلح: **مغطى بالكامل** = كل مجموعاته إما منفّذة أو مرفوضة بسبب مكتوب أو فجوة مطبوعة. **مغطى جزئيًا** = بعض مجموعاته منفّذ وبعضها لا. **لم يبدأ** = لا دالة ولا مجموعة منفّذة.

| # | المصطلح | الفكرة في سطر | المجموعات التابعة | الحالة | الموضع |
|---|---|---|---|---|---|
| C1.1 | Bias (daily / HTF) | Which side of the day is traded before any setup | لا مجموعة | **لم يبدأ** | `BUILD_STEP_B1_DESIGN_V2.md` §10: `R00` بلا قاعدة انحياز ← خارج النطاق معلنًا |
| C1.2 | Draw on liquidity (DOL) | The pool price is expected to reach | لا مجموعة (يظهر أثرها في `V-TP-1`) | **لم يبدأ** | لا شيء |
| C1.3 | Premium / discount (equilibrium) | Buy below the mid of the range, sell above | `V-PDA-2`, `V-PDA-3`, `V-PDA-12`, `V-OB-17` | **لم يبدأ** | لا شيء؛ `V-OB-17` مرفوضة لغياب `dealing range` |
| C1.4 | Dealing range | The range whose 50% defines premium and discount | `V-OB-17` (تابعة) | **لم يبدأ** | لا شيء؛ `GAP_LOCATION` مطلوبة في المواصفة §10 وغير موجودة في `common.py` |
| C2.1 | Swing high / swing low | Middle candle whose wick exceeds both neighbours | `V-A-00` (منفّذ)، `V-A-01…04` | **مغطى جزئيًا** | `b1_candles/swing.py` :: `swing_at` للنسخة `V-A-00` فقط |
| C2.2 | Equal highs / equal lows | Two highs/lows within one spread are "equal" | `V-E-EQH` (موقوفة بقرار `D1`) | **لم يبدأ** | `c1_catalog/liquidity_sweep.py` :: `_evaluate` ← فرع يعيد `UNDEFINED` دائمًا |
| C2.3 | Buy-side / sell-side liquidity | Resting orders above highs and below lows | لا مجموعة مستقلة (تدخل كـ«المستوى» في `V-E-00`) | **لم يبدأ** | لا شيء |
| C2.4 | Liquidity sweep / raid | Wick through a level and body closing back inside | `V-E-00`، `V-E-01`، `V-E-EQH`، `E2` | **مغطى بالكامل** | `c1_catalog/liquidity_sweep.py` :: `sweep_at`، `sweep_at_swing_level`، `_evaluate`، `latest_swing_level` |
| C2.5 | Displacement | A candle whose body dominates its range, optionally larger than neighbours | `V-D-01…04`، `V-D-Q` | **مغطى بالكامل** | `c1_catalog/displacement.py` :: `displacement_at`، `_source_numbers_for` |
| C2.6 | MSS / BOS / CHoCH | A move that breaks the prior structure | `V-OB-13` (شرط سابق كمدخل مستدعٍ)، `V-BRK-13` (غير منفّذ) | **مغطى جزئيًا** | `c1_catalog/order_block.py` :: `_validate_prerequisites` ← لا يُحسب الكسر، يُستقبل كدليل |
| C2.7 | CISD | Change in state of delivery: closes flip side | `V-STOP-10` (طرف `CISD` المجمّد) | **لم يبدأ** | لا شيء |
| C2.8 | Power of three / AMD / Judas | Accumulation, manipulation, distribution inside a session | لا مجموعة | **لم يبدأ** | لا شيء |
| C2.9 | Inducement | A trap liquidity pocket before the real move | لا مجموعة | **لم يبدأ** | لا شيء |
| C2.10 | SMT divergence / SSMT | Two correlated instruments disagree at a swing | لا مجموعة | **لم يبدأ** | لا شيء |
| C3.1 | Fair value gap (FVG) | Three-candle imbalance, wick to wick | `V-B-00` (منفّذ)، `V-B-01…03` | **مغطى جزئيًا** | `b1_candles/fvg.py` :: `fvg_at` للنسخة `V-B-00` فقط |
| C3.2 | Consequent encroachment (CE) | The 50% midpoint of a gap as a limit level | `V-CE-1…10` | **لم يبدأ** | لا شيء (يُستشهد بادعائها `C-CE-17` فقط) |
| C3.3 | Order block + mean threshold | Last opposing candle before the move, entered at its 50% | `V-OB-1…21` | **مغطى جزئيًا** (16 من 21) | `c1_catalog/order_block.py` :: `order_block_at`، `_record`، `_validate_prerequisites` |
| C3.4 | Breaker block | Failed order block that flips polarity | `V-BRK-1…14` | **لم يبدأ** | لا شيء |
| C3.5 | Balanced price range (BPR) | Overlap of a bullish and a bearish FVG | `V-BPR-1…10` | **لم يبدأ** | لا شيء |
| C3.6 | Optimal trade entry (OTE) | 62%–79% retracement zone of the leg | `V-OTE-1…8` | **لم يبدأ** | لا شيء |
| C3.7 | PD array | A ranked list of zones used for reactions | `V-PDA-1…13` | **لم يبدأ** | لا شيء |
| C3.8 | PSP / True Open | Precision swing point and the reference open | `V-STOP-9` | **لم يبدأ** | لا شيء |
| C3.9 | Timeframe pairing | Read on the higher, enter on the lower | لا مجموعة | **لم يبدأ** | لا شيء |
| C4.1 | Kill zone / time window | Named hourly windows where setups are taken | `V-NW-9` (مركزة على البيانات) | **لم يبدأ** | لا شيء |
| C4.2 | News-day condition | Whether and how news days are traded | `V-NW-1…11` | **لم يبدأ** | لا شيء |
| C5.1 | Stop / stop placement | Where the invalidation order sits | `V-STOP-1…17`، `V-OB-19`، `V-OB-20` | **لم يبدأ** | لا شيء |
| C5.2 | Target / take profit | Which level ends the trade | `V-TP-1…12` | **لم يبدأ** | لا شيء |
| C5.3 | IRL / ERL | Internal vs external range liquidity as target class | `V-TP-2` (تابعة) | **لم يبدأ** | لا شيء |
| C5.4 | Minimum risk–reward | The floor ratio that qualifies a trade | `V-RR-1…7` | **لم يبدأ** | لا شيء |
| C5.5 | Trade management | Partials and break-even after entry | `V-TP-3`، `V-TP-10`، `V-TP-11`، `V-STOP-16` | **لم يبدأ** | لا شيء |

**مجاميع §A:** مغطى بالكامل **2** (C2.4، C2.5) · مغطى جزئيًا **4** (C2.1، C2.6، C3.1، C3.3) · لم يبدأ **24**. المجموع 30.

---

## B. كل المجموعات — الدفعات 1 و2 و2b، ثم مجموعات تصميم V2

### B1 — الدفعة 1: الوقف `V-STOP` (17 مجموعة)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-STOP-1 | Stop beyond the sweep / raid extreme | 6 | NOT_CODED | — | الوقف خارج نطاق `C1` بنص المواصفة §1 (ملاحظة نطاق)؛ لا خطوة بناء للوقف في الشجرة |
| V-STOP-2 | Stop beyond the far edge of the gap | 3 | NOT_CODED | — | كما أعلاه |
| V-STOP-3 | Stop beyond the displacement candle's extreme | 3 | NOT_CODED | — | كما أعلاه |
| V-STOP-4 | Stop beyond the swing that launched the leg | 2 | NOT_CODED | — | كما أعلاه |
| V-STOP-5 | Stop beyond the OB / breaker / PD-array extreme | 2 | NOT_CODED | — | كما أعلاه |
| V-STOP-6 | Stop below the low that built the LTF shift | 1 | NOT_CODED | — | كما أعلاه |
| V-STOP-7 | Swing stop with a CE invalidation cut | 1 | NOT_CODED | — | كما أعلاه |
| V-STOP-8 | Stop below the prior close / opening-gap bottom | 1 | NOT_CODED | — | كما أعلاه |
| V-STOP-9 | Stop at the wick extreme of the PSP candle | 1 | NOT_CODED | — | كما أعلاه؛ ولا دالة `PSP` في الشجرة |
| V-STOP-10 | Stop at the frozen CISD extreme | 1 | NOT_CODED | — | كما أعلاه؛ ولا دالة `CISD` |
| V-STOP-11 | Stop beyond C2's extreme (fractal model) | 1 | NOT_CODED | — | كما أعلاه |
| V-STOP-12 | Small buffer beyond the level for spread | 2 | NOT_CODED | — | كما أعلاه؛ والمقدار غير منصوص برقم |
| V-STOP-13 | A few ticks outside the swept level | 1 | NOT_CODED | — | كما أعلاه؛ «a few ticks» بلا رقم |
| V-STOP-14 | About half the swing length beyond the extreme | 1 | NOT_CODED | — | كما أعلاه؛ «about half» بلا حد |
| V-STOP-15 | An invalidation reference is not automatically a stop order | 1 | NO_USABLE_SOURCE | — | جملة تحذيرية عن نوع الأمر، لا قاعدة سعرية |
| V-STOP-16 | Structural stop too wide → trade smaller, do not tighten | 1 | NOT_CODED | — | «too wide» بلا عتبة، والحجم ليس حسابًا على الشموع |
| V-STOP-17 | Keep the stop off round numbers | 1 | NOT_CODED | — | «round numbers» بلا تعريف عددي |

### B1 — الدفعة 1: الهدف `V-TP` (12 مجموعة)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-TP-1 | Target = the next opposing liquidity pool | 8 | NOT_CODED | — | الهدف خارج نطاق `C1` (§1)؛ ولا خطوة بناء لاحقة معلنة |
| V-TP-2 | Two targets: internal first, external second | 1 | NOT_CODED | — | كما أعلاه؛ ولا دالة `IRL/ERL` |
| V-TP-3 | Partial at the first internal level, remainder at the final target | 5 | NOT_CODED | — | كما أعلاه؛ وإدارة المركز ليست حسابًا على الشموع |
| V-TP-4 | Target = the next visible swing high/low | 3 | NOT_CODED | — | كما أعلاه |
| V-TP-5 | Target = an opposing or higher-timeframe FVG | 2 | NOT_CODED | — | كما أعلاه |
| V-TP-6 | Target = measured-move projection 2.5×–4× | 1 | NOT_CODED | — | كما أعلاه |
| V-TP-7 | Cancel the trade if the target is swept before entry | 1 | NOT_CODED | — | كما أعلاه؛ وحالة إلغاء الأمر لا وجود لها في الشجرة |
| V-TP-8 | Target = C1's far side (fractal model) | 1 | NOT_CODED | — | كما أعلاه |
| V-TP-9 | Target = prior day high/low or prior close extreme | 2 | NOT_CODED | — | كما أعلاه؛ ولا بيانات يوم سابق في هذا المسار |
| V-TP-10 | Scale 50–80% at the first major pool | 1 | NOT_CODED | — | كما أعلاه؛ والنسب إدارة مركز |
| V-TP-11 | Take half at T1 and move to break-even | 1 | NOT_CODED | — | كما أعلاه |
| V-TP-12 | No target rule stated | 1 | NO_USABLE_SOURCE | — | صمت صريح: لا قاعدة تُنقل |

### B1 — الدفعة 1: الأخبار `V-NW` (11 مجموعة)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-NW-1 | US 8:30 ET data sits inside the NY window and often produces the sweep | 2 | NOT_CODED | — | الأخبار خارج نطاق `C1`؛ ولا مفكرة اقتصادية ولا وحدة زمن في الشجرة |
| V-NW-2 | News creates the sweep/raid the setup trades | 4 | NOT_CODED | — | كما أعلاه |
| V-NW-3 | A news spike can be a real move | 1 | NOT_CODED | — | تصنيف نوعي بلا رقم |
| V-NW-4 | Size down or wait for the first spike to settle | 1 | NOT_CODED | — | إدارة حجم، وليست حسابًا على الشموع |
| V-NW-5 | News changes the label of a move (sweep vs run) | 1 | NOT_CODED | — | تصنيف بلا معيار كمي |
| V-NW-6 | Review the economic calendar; expect slippage | 2 | NOT_CODED | — | إجراء تشغيلي خارج هذه الطبقة |
| V-NW-7 | Prop-firm news window (five minutes either side) | 1 | NOT_CODED | — | قاعدة منصّة لا قاعدة سوق |
| V-NW-8 | News trading is permitted on the platform | 1 | NOT_CODED | — | قاعدة منصّة |
| V-NW-9 | Kill-zone timing is centred on data releases in some versions | 1 | NOT_CODED | — | إزاحة نافذة زمنية؛ ولا وحدة وقت في `engine_v1` |
| V-NW-11 | News can complete the sequence on paper without real direction | 1 | NOT_CODED | — | حكم نوعي بلا معيار |
| V-NW-10 | No news-day condition stated on the page | 6 | NO_USABLE_SOURCE | — | `SILENT`: الصمت لا يُنشئ قاعدة |

### B1 — الدفعة 1: المخاطرة/العائد `V-RR` (7 مجموعات)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-RR-1 | 3:1 minimum required | 2 | NOT_CODED | — | النسبة تحتاج وقفًا وهدفًا، وكلاهما خارج النطاق |
| V-RR-2 | 2:1 minimum | 2 | NOT_CODED | — | كما أعلاه |
| V-RR-3 | 3:1 when the opposing zone is clearly defined | 1 | NOT_CODED | — | كما أعلاه؛ و«clearly defined» بلا معيار |
| V-RR-4 | No numeric minimum; check reward against the stop | 1 | NOT_CODED | — | كما أعلاه |
| V-RR-5 | No minimum; case-by-case R multiples | 1 | NOT_CODED | — | كما أعلاه |
| V-RR-6 | An expectation stated as an average result, not a filter | 1 | NO_USABLE_SOURCE | — | وصف نتيجة لاحقة، لا قاعدة دخول |
| V-RR-7 | No minimum R:R stated | 7 | NO_USABLE_SOURCE | — | `SILENT`: الصمت لا يُنشئ قاعدة |

### B1 — بلوكات `CONFLICT` (13)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| CONFLICT-STOP-A | Which price level is the stop (gap edge / displacement candle / swing / swing+CE) | 4 sides | NOT_CODED | — | أطرافه كلها `NOT_CODED` |
| CONFLICT-STOP-B | How far beyond the extreme (ticks / half swing / 2 pips) | 3 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-STOP-C | Which extreme governs when a sweep and an LTF shift both exist | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-STOP-D | Whether the sweep extreme is a stop at all | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-TP-A | Level-based target vs measured-move projection | 2 sides | NOT_CODED | — | أطرافه `NOT_CODED` |
| CONFLICT-TP-B | The size of the first partial differs or is unstated | 3 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-TP-C | Whether a taken target voids the setup | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-NW-A | Whether the news window is traded at full size | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-NW-B | Whether trading through news is permitted | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-NW-C | Whether a news spike implies a reversal setup | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-RR-A | The floor itself differs (3:1 vs 2:1) | 2 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-RR-B | Whether a numeric floor exists at all | 4 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-RR-C | Whether the ratio filters entries or describes outcomes | 2 sides | NOT_CODED | — | كما أعلاه |

### B2 — الدفعة 2b: كتلة الأوامر `V-OB` (21 مجموعة، جدول `r` §E1)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-OB-1 | Block = the last opposing candle before the displacement | 8 | CODED_BASE | `c1_catalog/order_block.py` :: `order_block_at` — حلقة المسح الرجوعي من `displacement_start_index-1` | — |
| V-OB-2 | Bullish = last down-close candle; bearish = the mirror | 6 | CODED_BASE | `order_block.py` :: `order_block_at` — شرط `is_opposing` مع فرع `direction` | — |
| V-OB-3 | Take the last opposing candle, or group the cluster | 4 | CODED_BASE | `order_block.py` :: `order_block_at` (تؤخذ الأخيرة) + `gap("GAP_CLUSTER_BOUND")` | قراءة «تجميع الشموع» غير منفّذة: حدود التجمع غير منصوصة |
| V-OB-4 | Zone drawn high-to-low, wicks included | 2 | CODED_VARIANT | `order_block.py` :: `order_block_at` — فرع `boundaries == BOUNDARY_FULL_RANGE` | — |
| V-OB-5 | Body-only marking (open to close) | 4 | CODED_VARIANT | `order_block.py` :: `order_block_at` — فرع `BOUNDARY_BODY_ONLY` | — |
| V-OB-6 | Mean threshold = 50% of the body | 3 | CODED_VARIANT | `order_block.py` :: `order_block_at` — فرع `MT_BODY` مع `MEAN_THRESHOLD_FRACTION = 0.5` | — |
| V-OB-7 | Mean threshold = 50% of the full range | 2 | CODED_VARIANT | `order_block.py` :: `order_block_at` — فرع `MT_FULL_RANGE` | — |
| V-OB-8 | The mean threshold is the entry level | 3 | CODED_BASE | `order_block.py` :: `order_block_at` — `entry = mean_threshold if entry_level == ENTRY_MEAN_THRESHOLD` | — |
| V-OB-9 | Enter at the block candle's open price | 1 | CODED_OPTIONAL | `order_block.py` :: `order_block_at` — فرع `ENTRY_BLOCK_OPEN` | — |
| V-OB-10 | A close beyond the far edge invalidates | 5 | CODED_VARIANT | `order_block.py` :: `order_block_at` — حلقة الإبطال، فرع `INVALID_FAR_EDGE` | — |
| V-OB-11 | A close past the mean threshold invalidates | 1 | CODED_VARIANT | `order_block.py` :: `order_block_at` — فرع `INVALID_MEAN_THRESHOLD` | — |
| V-OB-12 | A close through the mean threshold is only a warning | 1 | CODED_OPTIONAL | `order_block.py` :: `order_block_at` — فرع `INVALID_MEAN_THRESHOLD_WARNING` ← `LABEL_WARNING` | — |
| V-OB-13 | A break of structure is required after the block | 4 | CODED_BASE | `order_block.py` :: `_validate_prerequisites` + حلقة الفلاتر (`basis = CALLER_INPUT`) | الكسر نفسه لا يُحسب: دليله مدخل مستدعٍ |
| V-OB-14 | An FVG inside the displacement is required | 4 | CODED_BASE | `order_block.py` :: `_validate_prerequisites` (`PREREQ_FVG`) | الفجوة لا تُحسب هنا: دليلها مدخل مستدعٍ |
| V-OB-15 | A sweep immediately before the displacement is required | 4 | CODED_BASE | `order_block.py` :: `_validate_prerequisites` (`PREREQ_SWEEP`) | الجرف لا يُستدعى: دليله مدخل مستدعٍ |
| V-OB-16 | The block must be unmitigated / first touch | 5 | CODED_BASE | `order_block.py` :: `order_block_at` — عدّ اللمسات `COMPUTED_FROM_CANDLES` | — |
| V-OB-17 | A bullish block belongs in discount, bearish in premium | 4 | NOT_CODED | — | لا دالة `dealing range` في `engine_v1`؛ والمسار القديم `src/trading_system/zones/dealing_range.py` مستثنى بنص `OLD_PIPELINE_DO_NOT_REUSE.md` |
| V-OB-18 | Displacement candle ≥ 1.5× a recent average | 2 | NOT_CODED | — | المقامان مختلفان بين الوحدتين، ولا رقم لنافذة المتوسط |
| V-OB-19 | Stop beyond the full block | 4 | NOT_CODED | — | الوقف خارج نطاق `C1` |
| V-OB-20 | Stop 1 pip beyond the mean threshold | 1 | NOT_CODED | — | كما أعلاه؛ والرقم `1 pip` من مصدر واحد |
| V-OB-21 | If the stop is too wide, cut size instead of tightening | 1 | NOT_CODED | — | الحجم ليس حسابًا على الشموع |

### B2 — تعارضات كتلة الأوامر (4)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| CONFLICT-OB-A | What the 50% is taken from (body vs full range) | 3 vs 2 | CODED_VARIANT | `order_block.py` :: `order_block_at` — `V-OB-6` مقابل `V-OB-7` | — |
| CONFLICT-OB-B | Where the stop goes (beyond block vs beyond MT) | 4 vs 1 | NOT_CODED | — | الوقف خارج النطاق |
| CONFLICT-OB-C | Default zone boundary (full range vs body) | 2 vs 4 | CODED_VARIANT | `order_block.py` :: `order_block_at` — `V-OB-4` مقابل `V-OB-5` | — |
| CONFLICT-OB-D | Invalidation level (far edge vs mean threshold) | 5 vs 1 (+1 warning) | CODED_VARIANT | `order_block.py` :: `order_block_at` — `V-OB-10` / `V-OB-11` / `V-OB-12` | — |

### B3 — الدفعة 2b: الكاسر `V-BRK` (14 مجموعة، جدول `r` §E2)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-BRK-1 | A breaker is a failed order block that flips polarity | 6 | NOT_CODED | — | لا ملف شيفرة للكاسر في `c1_catalog`، ولا خطوة بناء لاحقة معلنة |
| V-BRK-2 | A liquidity sweep must precede the failure | 5 | NOT_CODED | — | كما أعلاه |
| V-BRK-3 | Mitigation block = the same flip without a sweep | 5 | NOT_CODED | — | كما أعلاه |
| V-BRK-4 | A candle close through the zone is required | 4 | NOT_CODED | — | كما أعلاه |
| V-BRK-5 | A wick through the zone is accepted by some (ALT-CONVENTION-BRK-B) | 1 | NO_USABLE_SOURCE | — | أُعيد تسميته في `r` إلى اصطلاح بديل «يُبلَّغ ولا يُتبنّى»، فلا قاعدة صالحة |
| V-BRK-6 | The zone keeps the original OB's high-to-low range | 2 | NOT_CODED | — | لا شيفرة |
| V-BRK-7 | Enter on the retest with LTF confirmation | 2 | NOT_CODED | — | لا شيفرة |
| V-BRK-8 | Stop beyond the zone or beyond the swept swing | 3 | NOT_CODED | — | لا شيفرة؛ والوقف خارج النطاق أيضًا |
| V-BRK-9 | Unicorn model = breaker overlapping an FVG | 3 | NOT_CODED | — | لا شيفرة |
| V-BRK-10 | A breaker is itself a PD array | 3 | NOT_CODED | — | لا شيفرة |
| V-BRK-11 | Many traders take only the first retest | 2 | NOT_CODED | — | لا شيفرة |
| V-BRK-12 | Bullish breaker = low, high, lower low, higher high | 1 | NOT_CODED | — | لا شيفرة |
| V-BRK-13 | A close through the zone plus a structure break the other way | 2 | NOT_CODED | — | لا شيفرة؛ ولا دالة `MSS` |
| V-BRK-14 | A close back through the breaker ends it | 2 | NOT_CODED | — | لا شيفرة |

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| ALT-CONVENTION-BRK-A | Sweep-before-breaker treated as an alternative convention | — | NOT_CODED | — | اصطلاح يُسجَّل ولا يُتبنّى؛ لا شيفرة |

### B3 — الدفعة 2b: نطاق السعر المتوازن `V-BPR` (10 مجموعات، `r` §E3)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-BPR-1 | BPR = overlap of a bullish FVG and a bearish FVG | 3 | NOT_CODED | — | لا شيفرة `BPR`، ولا خطوة لاحقة |
| V-BPR-2 | BPR high/low are the top and bottom of the overlap | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-3 | Enter at the zone boundary | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-4 | Enter at the midpoint of the BPR | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-5 | A CHoCH or displacement candle inside the zone before entry | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-6 | A close through the whole zone mitigates it | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-7 | The second FVG may come later | 1 | NOT_CODED | — | كما أعلاه؛ و«later» بلا مدى |
| V-BPR-8 | The two FVGs are consecutive | 1 | NOT_CODED | — | كما أعلاه |
| V-BPR-9 | A BPR outranks a standalone FVG | 1 | NOT_CODED | — | كما أعلاه؛ والترتيب ليس سعرًا |
| V-BPR-10 | The overlap band is "a fortress for retests" | 1 | NOT_CODED | — | عبارة وصفية بلا معيار |

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| CONFLICT-BPR-A | Entry level: zone boundary vs midpoint | 2 | NOT_CODED | — | أطرافه غير منفّذة |
| CONFLICT-BPR-B | Timing: consecutive FVGs vs later second FVG | 2 | NOT_CODED | — | كما أعلاه |

### B3 — الدفعة 2b: الدخول الأمثل `V-OTE` (7 مجموعات + مجموعة `NOT_STATED`، `r` §E4)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-OTE-1 | OTE = the 62%–79% retracement zone | 4 | NOT_CODED | — | لا شيفرة `OTE`، ولا خطوة لاحقة |
| V-OTE-2 | 70.5% is the watched sub-level | 1 | NOT_CODED | — | كما أعلاه |
| V-OTE-3 | Prefer an FVG or OB overlapping the OTE zone | 3 | NOT_CODED | — | كما أعلاه |
| V-OTE-4 | Past 79% of the leg the setup is dead | 1 | NOT_CODED | — | كما أعلاه |
| V-OTE-5 | OTE can replace the FVG entry or be used with it | 1 | NOT_CODED | — | كما أعلاه |
| V-OTE-6 | The retracement is measured from the raid extreme | 1 | NOT_CODED | — | كما أعلاه |
| V-OTE-8 | Anchor = "back into the leg that broke structure" | 1 | NO_USABLE_SOURCE | — | `PARAPHRASE_NO_QUOTE`: لا اقتباس موثّق يسند القاعدة |
| V-OTE-7 | No OTE definition stated on the pages read | 3 | NO_USABLE_SOURCE | — | مجموعة `NOT_STATED`: صمت لا قاعدة |

### B3 — الدفعة 2b: الاقتراب اللاحق `V-CE` (10 مجموعات، `r` §E5)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-CE-1 | CE = the 50% midpoint of the gap | 5 | NOT_CODED | — | لا شيفرة `CE`؛ و«الفجوة» نفسها بلا تعريف مكتوب في الكتالوج |
| V-CE-2 | Measured wick-to-wick | 3 | NOT_CODED | — | كما أعلاه |
| V-CE-3 | CE also applies to a liquidity void and a long rejection wick | 1 | NOT_CODED | — | كما أعلاه |
| V-CE-4 | CE is the limit-entry level | 3 | NOT_CODED | — | كما أعلاه |
| V-CE-5 | Split size between the near edge and CE | 1 | NOT_CODED | — | كما أعلاه؛ وإدارة موقع |
| V-CE-6 | The 50% of a breaker zone is also called CE | 1 | NOT_CODED | — | كما أعلاه؛ والكاسر غير منفّذ |
| V-CE-7 | CE = 50% of any PD array, including an OB | 1 | NOT_CODED | — | كما أعلاه |
| V-CE-8 | CE belongs to a gap; the mean threshold belongs to an OB | 1 | NOT_CODED | — | كما أعلاه |
| V-CE-9 | CE grades how deep price came into a gap (quadrants) | 1 | NOT_CODED | — | كما أعلاه |
| V-CE-10 | A wick through the gap is tolerated; the body close decides | 1 | NOT_CODED | — | كما أعلاه |

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| CONFLICT-CE-A | Which zone the 50% is taken from (3 named sides) | 3 | NOT_CODED | — | أطرافه غير منفّذة |

### B3 — الدفعة 2b: مصفوفة الخصم/العلاوة `V-PDA` (13 مجموعة، `r` §E6)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-PDA-1 | PD array = a categorised list of reaction zones | 4 | NOT_CODED | — | لا شيفرة؛ ولا دالة `dealing range` تقوم عليها |
| V-PDA-2 | Split the range at 50%; buy discount, sell premium | 8 | NOT_CODED | — | كما أعلاه |
| V-PDA-3 | The zone must sit on the correct side of the range | 3 | NOT_CODED | — | كما أعلاه |
| V-PDA-4 | FVG, OB and BPR are the arrays used for the daily entry | 2 | NOT_CODED | — | كما أعلاه |
| V-PDA-5 | Block spectrum = OB, breaker, mitigation, rejection, propulsion | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-6 | OB, FVG, breaker and old highs/lows are the listed arrays | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-7 | A BPR outranks a standalone FVG | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-8 | No array outranks another by rule | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-9 | Eight trigger tools including IFVG, unicorn, NWOG, NDOG | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-10 | Membership includes OTE and any other PD-arrangement zone | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-11 | Membership: FVG, order block, opening gap | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-12 | Premium/discount are anchored to an open, not to 50% of a range | 1 | NOT_CODED | — | كما أعلاه |
| V-PDA-13 | Membership includes rejection block, volume imbalance, NDOG | 1 | NOT_CODED | — | كما أعلاه |

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| CONFLICT-PDA-A | Which zones are members of the PD array list | 7 sides | NOT_CODED | — | لا شيفرة `PDA` |
| CONFLICT-PDA-B | Are the arrays ranked | 3 sides | NOT_CODED | — | كما أعلاه |
| CONFLICT-PDA-C | What premium/discount is measured against | 2 sides | NOT_CODED | — | كما أعلاه |

### B4 — مجموعات تصميم `V2` وقرار المالك (ليست من الدفعات)

| ID | idea (EN) | units | status | where | reason |
|---|---|---:|---|---|---|
| V-A-00 | Swing = middle candle's wick beyond both neighbours, confirmed by c3 close | 3 high / 2 low | CODED_BASE | `b1_candles/swing.py` :: `swing_at` (وسم `WEAK_SUPPORT` على جهة القاع) | — |
| V-A-01 | No fixed neighbour count; a respected reversal within one or two candles | 1 | NOT_CODED | — | «one or two candles of clear reversal» بلا قاعدة ميكانيكية |
| V-A-02 | Two candles on each side (five-candle window) | 3 (ذكر لا تبنٍّ) | NOT_CODED | — | لا مصدر يتبنّاها كتعريف |
| V-A-03 | Confirmation comes from a clear reversal after c3, not from c3's close | 1 | NOT_CODED | — | معيار نوعي بلا رقم |
| V-A-04 | Confirmation is a function of a user-chosen lookback | 1 | KNOWLEDGE_GAP | السؤال كما في `B1_DESIGN_V2` §4.5 بلا اسم شخص: `KNOWLEDGE_GAP: ما الرقم الذي يقصده A5 بـ lookback؟` | لا رقم في المصدر |
| V-B-00 | FVG = three-candle imbalance, wick to wick | 4 | CODED_BASE | `b1_candles/fvg.py` :: `fvg_at` | — |
| V-B-01 | The gap measured on bodies (close c1 to open c3) | 1 | NOT_CODED | — | لا مفتاح نسخة في `fvg_at` |
| V-B-02 | Middle candle size 1.5–2× the average candle | 1 | NOT_CODED | — | لا عتبة حجم في `fvg_at` |
| V-B-03 | Invalidation = a body close through the far edge | 1 | NOT_CODED | — | `fvg.py` يطبع الفجوة فقط، ولا إبطال |
| V-C-01 | One candle or a short cluster (design-doc name of the cluster reading) | 2 | CODED_BASE | المضمون في `order_block.py` :: `order_block_at` (تؤخذ الأخيرة)؛ والمعرّف `V-C-01` غير موجود في الشيفرة | قراءة التجمع غير منفّذة |
| V-C-02 | A prior sweep is required before the block counts | 1 | CODED_BASE | `order_block.py` :: `_validate_prerequisites` تحت المعرّف `V-OB-15` | المعرّف `V-C-02` غير موجود في الشيفرة |
| V-C-03 | Displacement ≥ 1.5× average and wick < 25% of range | 1 | NOT_CODED | — | الرقمان من مصدر واحد، ولا نافذة للمتوسط |
| V-C-04 | Boundaries = open to close (body) | 1 | CODED_VARIANT | `order_block.py` :: `order_block_at` تحت المعرّف `V-OB-5` | المعرّف `V-C-04` غير موجود في الشيفرة |
| V-C-05 | Invalidation = body close through the far edge | 1 | CODED_VARIANT | `order_block.py` :: `order_block_at` تحت المعرّف `V-OB-10` | المعرّف `V-C-05` غير موجود في الشيفرة |
| V-E-00 | Wick beyond the level and the body closes back inside, judged at the close | 4 | CODED_VARIANT | `c1_catalog/liquidity_sweep.py` :: `_evaluate` (فرع `VERSION_REFERENCE`) | — |
| V-E-01 | Body closes marginally beyond the level and the next candle reverses | 1 | CODED_VARIANT | `liquidity_sweep.py` :: `_evaluate` (فرع `VERSION_MARGINAL_BODY`) | — |
| V-E-EQH | Two highs/lows within 1× spread count as equal | 0 + قرار مالك | NOT_CODED | `liquidity_sweep.py` :: `_evaluate` ← يعيد `UNDEFINED` دائمًا | لا `ask/bid` في سجل الشمعة، والزوج المرجعي فجوة معلنة في `D1` |
| E2 | "A sharp spike with a long wick" as a sweep shape | 1 | NOT_CODED | — | لا قاعدة إغلاق ولا رقم |
| V-D-01 | Body / range ≥ 60% | 1 | CODED_VARIANT | `c1_catalog/displacement.py` :: `displacement_at` (فرع `V_D_01`) | — |
| V-D-02 | Body / range > 75% and range ≥ 2× a caller-named window | 1 | CODED_VARIANT | `displacement.py` :: `displacement_at` (فرع `V_D_02`) | — |
| V-D-03 | Body ≥ 2× the average body of the previous ten candles | 1 | CODED_VARIANT | `displacement.py` :: `displacement_at` (فرع `V_D_03`) | — |
| V-D-04 | No displacement without a gap | 1 | CODED_VARIANT | `displacement.py` :: `displacement_at` (فرع `V_D_04`) | لا يحسب شرطًا: يعيد `UNDEFINED` مع `GAP_D_GAP_DEFINITION` بحسب المواصفة §5 |
| V-D-Q | Qualitative family: "energetic", "bodies that stand out" | 3 | NOT_CODED | `displacement.py` :: `displacement_at` ← يعيد `UNDEFINED` دائمًا | كل ألفاظها نسبية بلا رقم، ومصدران يصرّحان بأنه لا حد عام |

### B5 — أبعاد فجوة معلنة (لا تُحتسب كمجموعات، ولا تُضاف إلى مجاميع §C)

| ID | idea (EN) | source | status | where | question |
|---|---|---|---|---|---|
| OB-D19 | Bounds of the move that breaks structure | 0 | KNOWLEDGE_GAP | `order_block.py` ← `GAP_OB_MOVE_BOUNDS` | أي شموع تُعدّ «الحركة»، وما أول شمعة فيها وآخرها؟ |
| E-D4 | Minimum penetration distance and speed of a sweep | 0 | KNOWLEDGE_GAP | `liquidity_sweep.py` ← `GAP_SWEEP_DISTANCE` | ما مقدار الاختراق الأدنى وما سرعته؟ |
| E-D5 | A body closing exactly at the sweep level | 0 | KNOWLEDGE_GAP | `liquidity_sweep.py` ← `GAP_SWEEP_EQUAL_CLOSE` | ما حكم الإغلاق عند المستوى بالضبط؟ |
| D-D6 | Is a short cluster a displacement | 0 | KNOWLEDGE_GAP | `displacement.py` ← `GAP_D_CLUSTER` | هل التجمع القصير إزاحة أم شمعة واحدة؟ |
| D-D7 | Is a prior sweep a condition of displacement | 0 | KNOWLEDGE_GAP | `displacement.py` ← `GAP_D_PRIOR_SWEEP` | هل الجرف السابق شرط؟ |
| EQH-PAIR | Which earlier swing is paired with the second | 0 | KNOWLEDGE_GAP | `OWNER_DECISIONS.md` §D1 (سؤال مفتوح) و`liquidity_sweep.py` ← `GAP_SWEEP_EQH_BASIS` | أي تأرجح سابق يُقارَن، وبأي مدى بحث؟ |
| CLUSTER-BOUND | Start and end of an opposing-candle cluster | 0 | KNOWLEDGE_GAP | `order_block.py` ← `GAP_CLUSTER_BOUND` | كيف تُحدّ حدود تجمع الشموع المعارضة؟ |

---

## C. الأعداد بحسب الحالة — لكل عائلة على حدة

كل صف أدناه **عائلة واحدة فقط**. ولا يُجمع بين عائلتين في رقم واحد إلا في سطر «المجموع» الظاهر مع أجزائه.

### C.1 مجموعات الدفعة 1 (`p`)

| العائلة | مجموع | CODED_BASE | CODED_VARIANT | CODED_OPTIONAL | NOT_CODED | NO_USABLE_SOURCE | KNOWLEDGE_GAP | PLANNED_NEXT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `V-STOP` | 17 | 0 | 0 | 0 | 16 | 1 | 0 | 0 |
| `V-TP` | 12 | 0 | 0 | 0 | 11 | 1 | 0 | 0 |
| `V-NW` | 11 | 0 | 0 | 0 | 10 | 1 | 0 | 0 |
| `V-RR` | 7 | 0 | 0 | 0 | 5 | 2 | 0 | 0 |
| **مجموع الدفعة 1** | **47** | **0** | **0** | **0** | **42** | **5** | **0** | **0** |
| بلوكات `CONFLICT` (STOP 4 + TP 3 + NW 3 + RR 3) | 13 | 0 | 0 | 0 | 13 | 0 | 0 | 0 |

### C.2 مجموعات الدفعة 2b (`r` — النهائية)

| العائلة | مجموع | CODED_BASE | CODED_VARIANT | CODED_OPTIONAL | NOT_CODED | NO_USABLE_SOURCE | KNOWLEDGE_GAP | PLANNED_NEXT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `V-OB` | 21 | 8 | 6 | 2 | 5 | 0 | 0 | 0 |
| `V-BRK` | 14 | 0 | 0 | 0 | 13 | 1 | 0 | 0 |
| `V-BPR` | 10 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| `V-OTE` | 7 | 0 | 0 | 0 | 6 | 1 | 0 | 0 |
| `V-CE` | 10 | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| `V-PDA` | 13 | 0 | 0 | 0 | 13 | 0 | 0 | 0 |
| **مجموع الدفعة 2b** | **75** | **8** | **6** | **2** | **57** | **2** | **0** | **0** |
| بلوكات `CONFLICT` (OB 4 + BPR 2 + CE 1 + PDA 3) | 10 | 0 | 3 | 0 | 7 | 0 | 0 | 0 |
| `ALT-CONVENTION-BRK-A` + مجموعة `V-OTE-7` (`NOT_STATED`) | 2 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |

### C.3 مجموعات تصميم `V2` وقرار المالك

| العائلة | مجموع | CODED_BASE | CODED_VARIANT | CODED_OPTIONAL | NOT_CODED | NO_USABLE_SOURCE | KNOWLEDGE_GAP | PLANNED_NEXT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `V-A` (تأرجح) | 5 | 1 | 0 | 0 | 3 | 0 | 1 | 0 |
| `V-B` (فجوة) | 4 | 1 | 0 | 0 | 3 | 0 | 0 | 0 |
| `V-C` (كتلة بالاسم القديم) | 5 | 2 | 2 | 0 | 1 | 0 | 0 | 0 |
| `V-E` (جرف) | 4 | 0 | 2 | 0 | 2 | 0 | 0 | 0 |
| `V-D` (إزاحة) | 5 | 0 | 4 | 0 | 1 | 0 | 0 | 0 |
| **مجموع V2/Owner** | **23** | **4** | **8** | **0** | **10** | **0** | **1** | **0** |

### C.4 المجموع الكلي — بأجزائه

| الجزء | صفوف | CODED_BASE | CODED_VARIANT | CODED_OPTIONAL | NOT_CODED | NO_USABLE_SOURCE | KNOWLEDGE_GAP | PLANNED_NEXT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| مجموعات الدفعة 1 | 47 | 0 | 0 | 0 | 42 | 5 | 0 | 0 |
| بلوكات تعارض الدفعة 1 | 13 | 0 | 0 | 0 | 13 | 0 | 0 | 0 |
| مجموعات الدفعة 2b | 75 | 8 | 6 | 2 | 57 | 2 | 0 | 0 |
| بلوكات تعارض الدفعة 2b | 10 | 0 | 3 | 0 | 7 | 0 | 0 | 0 |
| اصطلاح بديل + مجموعة `NOT_STATED` | 2 | 0 | 0 | 0 | 1 | 1 | 0 | 0 |
| مجموعات V2/Owner | 23 | 4 | 8 | 0 | 10 | 0 | 1 | 0 |
| **المجموع** | **170** | **12** | **17** | **2** | **130** | **8** | **1** | **0** |

> `170 = 12 + 17 + 2 + 130 + 8 + 1`. و`MISMATCH_SPEC_CODE = 0` في هذا العدّ لأن حالات عدم التطابق في §E تصف مواضع في المواصفة لا صفوفًا مستقلة؛ ولكل موضع منها صفّه أعلاه بحالته الحقيقية.
> أبعاد الفجوة في §B5 (**7**) لا تدخل في هذا الجدول: ليست مجموعات ولا نسخًا.

### C.5 الحصيلة بجملة

- **المنفّذ فعلًا** (بأي نوع `CODED_*`): **31 صفًّا** = 12 `CODED_BASE` + 17 `CODED_VARIANT` + 2 `CODED_OPTIONAL`. وكلها في ثلاثة ملفات: `order_block.py`، `liquidity_sweep.py`، `displacement.py`، ومعها `b1_candles/swing.py` و`fvg.py` للنسختين `V-A-00` و`V-B-00`.
- **غير المنفّذ بسبب مكتوب**: 130 `NOT_CODED`.
- **بلا مصدر صالح**: 8 `NO_USABLE_SOURCE`.
- **فجوة معرفة مطبوعة**: 1 مجموعة + 7 أبعاد (§B5).
- **مخطّط لخطوة لاحقة**: 0 — لعدم وجود وثيقة خطوة لاحقة.

---

## D. أفكار موجودة في البحث وليست في أي صف

الأفكار التالية عُثر عليها بالفتح، وليست في جدول من الجداول أعلاه لأنها لم تُحوَّل قط إلى معرّف مجموعة:

| # | الفكرة | موضعها في البحث | لماذا لا صفّ لها | الحكم |
|---|---|---|---|---|
| 1 | عائلة إزاحة بعتبة `ATR(14)`: «body ≥ 1.5 × ATR of the prior 14 candles» | `external_sources/l_open_questions.md` — السجلات `Q1-01` (QuantumAlgo)، `Q1-02` (FundingPips)، `Q1-13` | لم تُرقَّ إلى معرّف نسخة في `BUILD_STEP_B1_DESIGN_V2.md` §8 (الذي يقتصر على `F1…F6`)، ولا في المواصفة `C1`، ولا في الشيفرة | **KNOWLEDGE_GAP**: ما مصدر العتبة `ATR(14)` وهل تُعتمد عائلة نسخة مستقلة `V-D-ATR`؟ — لا قرار مالك |
| 2 | نسبة المخاطرة من الحساب (1%) | `OLD_PIPELINE_DO_NOT_REUSE.md` (سطر `config_btc_recommendations.json:4`) و`VARIANT_PLAN.md` («ما لا يصبح متغيرًا الآن») | مستثناة بنصّين صريحين: تعارض `Q11-C05`/`Q11-C06`، ولا حساب أموال في `engine_v1` | **NO_USABLE_SOURCE** (مستثناة بقرار مكتوب) |
| 3 | أرقام وقف 30–50 نقطة، و17 نقطة | `VARIANT_PLAN.md` («ما لا يصبح متغيرًا الآن») | أمثلة سياقية لا قاعدة محمولة على الزوج | **NO_USABLE_SOURCE** |
| 4 | الكسور الجزئية الجبرية للخروج | `OLD_PIPELINE_DO_NOT_REUSE.md` (`causal_ict_lifecycle.py:421-449`) و`VARIANT_PLAN.md` | `U0119` و`U0120` ترفضان تحديد النسب؛ والجزئي في `V-TP-3`/`V-TP-10`/`V-TP-11` بلا رقم | **NO_USABLE_SOURCE** في الطبقة الحالية |
| 5 | ترتيب الأسبوعي/الشهري في أولوية الأهداف | `VARIANT_PLAN.md` | المؤيد هو اليومي فوق الأدنى فقط؛ لا قاعدة أسبوعية | **NO_USABLE_SOURCE** |
| 6 | ثلاث نقاط في `l_open_questions.md` (تقارب القمم Q3، وحجم الفجوة بـ `0.5×ATR` Q5) | `external_sources/l_open_questions.md` | `OWNER_DECISIONS.md` §D1 يرفض «0.2 × ATR» رفضًا صريحًا، ولا مصدر يتبنّى `0.5×ATR` كحد في الكتالوج | **KNOWLEDGE_GAP** مسجّل في `D1` كسؤال مفتوح للتأرجح، والرقم مرفوض |
| 7 | روابط `R00` الستة (الانحياز، شرط الإعداد، الدخول، الهدف، الوقت، الخروج) | `BUILD_STEP_B1_DESIGN_V2.md` §10 | خارج نطاق المفاهيم الخمسة المعلنة | **NO_USABLE_SOURCE** لهذه الخطوة |

**نتيجة §D:** لا توجد فكرة في الدفعات `o`/`p`/`q`/`r` بلا صف. السبع أعلاه كلها من طبقات أقدم (`l_open_questions.md`، `VARIANT_PLAN.md`، `OLD_PIPELINE_DO_NOT_REUSE.md`) أو من قرار مالك، ولكل منها حكم مكتوب هنا. الفجوة الحقيقية الوحيدة غير المسجّلة سابقًا هي **#1 (عائلة `ATR(14)`)**.

---

## E. التعارضات بين المواصفة/الشيفرة وقرارات المالك ووثيقة تصميم `V2`

> تقرير فقط. لم يُصلَح شيء في هذا الالتزام.

| # | التعارض | الطرف الأول | الطرف الثاني | الحكم |
|---|---|---|---|---|
| E-1 | **الإزاحة: هل لها نسخة مرجعية؟** | `BUILD_STEP_B1_DESIGN_V2.md` §8.2 و§8.7: «لا مرجع — تعادل»، «النسخة: لا مرجع — تعادل» | `BUILD_STEP_C1_SPEC.md` §5 و§6 و§7.3: `V-D-01` هي المرجع، بوسم `FLAGGED_FOR_OWNER_OVERRIDE` | **قائم ولم يُحسم.** الشيفرة تطبّع المواصفة: `displacement.py` :: `REFERENCE_VARIANT = V_D_01` ويُطبع `reference_variant` مع كل نتيجة. أي أن المحرك اليوم يعلن مرجعًا لبُعد صرّحت وثيقة التصميم أنه بلا مرجع |
| E-2 | **قسم المالك `D2` المزعوم** | طلب البناء: `D2` يسمّي عائلات `V-D-A` و`V-D-B` و`V-D-C` | `OWNER_DECISIONS.md` في هذه الشجرة: `D1` ثم `D2 research` (إحالات مراجع، لا قرار). لا وجود لـ`V-D-A/B/C` في أي ملف | **القسم غير موجود.** المعرّفات `V-D-A/B/C` لا تظهر في الشجرة إلا داخل تنبيه المواصفة §1 نفسها. الشيفرة تستخدم `V-D-01…04` و`V-D-Q` فقط |
| E-3 | **عائلة `ATR(14)`** | `external_sources/l_open_questions.md`: سجلات `Q1-01`, `Q1-02`, `Q1-13` تقول «1.5 × ATR of the prior 14 candles» | لا معرّف نسخة لها في `B1_DESIGN_V2` §8، ولا في المواصفة `C1`، ولا في `displacement.py` | **غير منفّذة وغير مسجّلة كنسخة.** لا دالة `ATR` في `engine_v1` أصلًا |
| E-4 | **فهرس الفجوات: المواصفة 17، الشيفرة 12** | المواصفة §10: 17 معرّف فجوة | `c1_catalog/common.py` :: `GAPS`: 12 معرّفًا | **عدم تطابق.** ناقص في الشيفرة 6: `GAP_STOP_AND_SIZE`, `GAP_WICK_INVALIDATION`, `GAP_LOCATION`, `GAP_OB_DISPLACEMENT_FILTER`, `GAP_SWEEP_QUALITATIVE`, `GAP_D_SWEEP_LEVEL`. وزائد فيها 1: `GAP_EQUAL_THRESHOLD` (معلَّق في الشيفرة بأنه أُضيف معها ولم يكن في §10) |
| E-5 | **فجوة موعودة لا يمكن أن تُطبع** | المواصفة §3.1 (`OB-D10`, `OB-D15`, `OB-D16`)، §4 (`E-D7`)، §5 (`D-D7`): «تُطبع فجوة/سطر فجوة» | لا دالة للفجوة، ولا نصّ فجوة في `GAPS` | **عدم تطابق تنفيذي.** الفجوة الموعودة لا تظهر أبدًا لأن البُعد كله بلا دالة |
| E-6 | **اسمان لنفس أبعاد الكتلة** | `BUILD_STEP_B1_DESIGN_V2.md` §6.4: `V-C-01…05` | `q`/`r`: `V-OB-1…21`، وهي المستخدمة في المواصفة والشيفرة | **ازدواج تسمية.** `V-C-01…05` غير موجودة في الشيفرة؛ تُقرأ اليوم كأنها نسخ مهجورة |
| E-7 | **تصنيف `V-E-EQH`** | المواصفة §4 (`E-D6`): «OPTIONAL_SWITCH / NOT_CODED» | `liquidity_sweep.py` :: `VARIANTS` تضمّها، و`_evaluate` يعالجها بإرجاع `UNDEFINED` | **فرق تصنيف لا فرق سلوك.** النتيجة مطابقة لقرار `D1` (موقوفة)، لكن الوسم «غير منفّذة» غير دقيق: المعرّف مقبول ويُرجع `UNDEFINED` |
| E-8 | **حقول خرج زائدة على المخطط** | المواصفة §7.1 و§7.3 تحدد الحقول | `order_block.py` يضيف `basis_low`/`basis_high`/`far_edge` داخل `numbers`؛ `displacement.py` يضيف `reference_variant` و`flags` | **زيادة لا تناقض.** الشيفرة أوسع من المخطط؛ يُسجَّل ولا يُعدّل |
| E-9 | **معنى `swing_index`** | المواصفة §7.2: `swing_index: int` بلا تعريف | `liquidity_sweep.py` :: `latest_swing_level` يعيد فهرس شمعة التأكيد `c3`، بينما المستوى مأخوذ من فتيل الشمعة الوسطى `c3-1` | **التباس تسمية.** القارئ قد يظن أن الفهرس هو شمعة القمة/القاع |
| E-10 | **سطر التجميع في `V-OB-3`** | المواصفة §3.1: «ويُطبع سطر تجميع لأسفل» | `order_block.py` :: `order_block_at` يطبع `GAP_CLUSTER_BOUND` فقط إذا كانت الشمعة السابقة معارضة أيضًا | **أضيق من النص**: التجميع لا يُنبَّه عليه إلا في حالة واحدة |
| E-11 | **`OB-D1` يقول 8 وحدات** | المواصفة §3.1: 8 وحدات مع 11 معرّف ادعاء | `order_block.py` :: `CLAIM_IDS["V-OB-1"]` = 11 معرّفًا | **متسق عدديًا** (8 وحدات ← 11 ادعاء)؛ يُذكر لأنه قد يُقرأ خطأً كتعارض |

**قائمة `MISMATCH_SPEC_CODE`:** `E-4`، `E-5`، `E-7`، `E-9`، `E-10` فقط (مواضع تقول المواصفة فيها شيئًا والشيفرة تفعل غيره أو لا تفعله). أما `E-1`، `E-2`، `E-3`، `E-6` فهي تعارضات وثائق لا تعارضات شيفرة، و`E-8` و`E-11` تسجيل لا تعارض.

---

## F. الحدود

1. **قراءة فقط.** لم تُضف شيفرة، ولم تُعدَّل أي دالة، ولم تُقرأ بيانات سوق، ولم تُنتج نتيجة أداء ولا رسم. الملف الجديد هو هذا الملف وحده.
2. **أعداد الوحدات منقولة.** عمود `units` هو عدد الناشرين في جداول `p`/`r` كما هي، لم أُعد التحقق من الاقتباسات نفسها ولا من استقلال الناشرين؛ ذلك عمل الدفعتين السابقتين.
3. **§A اجتهاد تصنيفي معلن.** ربط المجموعات بالمصطلحات الثلاثين مبني على نص كل مجموعة؛ لا يوجد في الشجرة جدول ربط جاهز بهذا الشكل. وحيث كانت المجموعة تابعة لمصطلحين (مثل `V-OB-17` لـ«الخصم/العلاوة» و«نطاق التداول») ذُكرت في الاثنين.
4. **لا خطوة لاحقة في الشجرة.** لا يوجد `BUILD_STEP_C2` ولا `C3`؛ لذلك `PLANNED_NEXT = 0`، ولم أُسمِّ خطوة مستقبلية من عندي.
5. **المسار القديم مستثنى.** `src/trading_system/zones/dealing_range.py` و`order_blocks.py` و`fvg.py` موجودة، لكن `OLD_PIPELINE_DO_NOT_REUSE.md` يمنع نقل أي قاعدة أو رقم منها إلى `engine_v1`، فلا تُحتسب `CODED_*` هنا.
6. **الشيفرة القديمة لم تُفتح للتحقق.** استُشهد بها من ملف الاستثناء فقط، وهذا حدّ معلن.
7. **`MISMATCH_SPEC_CODE` لا يعني خطأً في الحساب.** الخمسة المسجّلة مواضع نصية/تصنيفية؛ ولم يظهر أي فشل في `test_c1.py` (802 فحصًا، 0 فشل).
8. **لم يُحسم أي تعارض.** كل ما في §E تقرير؛ التصحيح يحتاج قرار مالك وخطوة بناء لاحقة.
