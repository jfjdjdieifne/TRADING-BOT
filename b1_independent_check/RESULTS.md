# Independent B1 check results

Source files were imported/read-only; no code under `engine_v1/b1_candles/` was modified.

## Per-case results

- MATCH | swing_high_at_c2 | SH-ABOVE-ABOVE-C3_CLOSED | expected=YES; actual=YES
- MATCH | swing_high_at_c2 | SH-ABOVE-ABOVE-C3_OPEN | expected=PENDING; actual=PENDING
- MATCH | swing_high_at_c2 | SH-ABOVE-EQUAL-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_high_at_c2 | SH-ABOVE-EQUAL-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_high_at_c2 | SH-ABOVE-BELOW-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_high_at_c2 | SH-ABOVE-BELOW-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_high_at_c2 | SH-EQUAL-ABOVE-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_high_at_c2 | SH-EQUAL-ABOVE-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_high_at_c2 | SH-EQUAL-EQUAL-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_high_at_c2 | SH-EQUAL-EQUAL-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- TEXT_SILENT | swing_high_at_c2 | SH-EQUAL-BELOW-C3_CLOSED | code returned NO; question: عند اجتماع علاقة مساواة غير محسومة مع إخفاق صارم، هل تكون النتيجة NO أم UNDECIDED؟
- TEXT_SILENT | swing_high_at_c2 | SH-EQUAL-BELOW-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_high_at_c2 | SH-BELOW-ABOVE-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_high_at_c2 | SH-BELOW-ABOVE-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- TEXT_SILENT | swing_high_at_c2 | SH-BELOW-EQUAL-C3_CLOSED | code returned NO; question: عند اجتماع علاقة مساواة غير محسومة مع إخفاق صارم، هل تكون النتيجة NO أم UNDECIDED؟
- TEXT_SILENT | swing_high_at_c2 | SH-BELOW-EQUAL-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_high_at_c2 | SH-BELOW-BELOW-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_high_at_c2 | SH-BELOW-BELOW-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-ABOVE-ABOVE-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_low_at_c2 | SL-ABOVE-ABOVE-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- TEXT_SILENT | swing_low_at_c2 | SL-ABOVE-EQUAL-C3_CLOSED | code returned NO; question: عند اجتماع علاقة مساواة غير محسومة مع إخفاق صارم، هل تكون النتيجة NO أم UNDECIDED؟
- TEXT_SILENT | swing_low_at_c2 | SL-ABOVE-EQUAL-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-ABOVE-BELOW-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_low_at_c2 | SL-ABOVE-BELOW-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- TEXT_SILENT | swing_low_at_c2 | SL-EQUAL-ABOVE-C3_CLOSED | code returned NO; question: عند اجتماع علاقة مساواة غير محسومة مع إخفاق صارم، هل تكون النتيجة NO أم UNDECIDED؟
- TEXT_SILENT | swing_low_at_c2 | SL-EQUAL-ABOVE-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-EQUAL-EQUAL-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_low_at_c2 | SL-EQUAL-EQUAL-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-EQUAL-BELOW-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_low_at_c2 | SL-EQUAL-BELOW-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-BELOW-ABOVE-C3_CLOSED | expected=NO; actual=NO
- TEXT_SILENT | swing_low_at_c2 | SL-BELOW-ABOVE-C3_OPEN | code returned NO; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-BELOW-EQUAL-C3_CLOSED | expected=UNDECIDED; actual=UNDECIDED
- TEXT_SILENT | swing_low_at_c2 | SL-BELOW-EQUAL-C3_OPEN | code returned UNDECIDED; question: هل تُقدَّم حالة NO أو UNDECIDED على PENDING عندما لا تكون الشمعة الثالثة مغلقة؟
- MATCH | swing_low_at_c2 | SL-BELOW-BELOW-C3_CLOSED | expected=YES; actual=YES
- MATCH | swing_low_at_c2 | SL-BELOW-BELOW-C3_OPEN | expected=PENDING; actual=PENDING
- MATCH | fvg_bullish | FVG-BULL-LOW_C3_VS_HIGH_C1-ABOVE | expected=YES; actual=YES
- MATCH | fvg_bullish | FVG-BULL-LOW_C3_VS_HIGH_C1-EQUAL | expected=UNDECIDED; actual=UNDECIDED
- MATCH | fvg_bullish | FVG-BULL-LOW_C3_VS_HIGH_C1-BELOW | expected=NO; actual=NO
- MATCH | fvg_bearish | FVG-BEAR-HIGH_C3_VS_LOW_C1-ABOVE | expected=NO; actual=NO
- MATCH | fvg_bearish | FVG-BEAR-HIGH_C3_VS_LOW_C1-EQUAL | expected=UNDECIDED; actual=UNDECIDED
- MATCH | fvg_bearish | FVG-BEAR-HIGH_C3_VS_LOW_C1-BELOW | expected=YES; actual=YES

## Counts

- swing_high_at_c2: MATCH 8, MISMATCH 0, TEXT_SILENT 10
- swing_low_at_c2: MATCH 8, MISMATCH 0, TEXT_SILENT 10
- fvg_bullish: MATCH 3, MISMATCH 0, TEXT_SILENT 0
- fvg_bearish: MATCH 3, MISMATCH 0, TEXT_SILENT 0
- Combined FVG: MATCH 6, MISMATCH 0, TEXT_SILENT 0

## Cross-cutting checks

- Swing-low WEAK_SUPPORT: PASS (18/18 results)
- FVG INVALIDATION_UNDECIDED: PASS (6/6 results)
- No word Michael in serialized result records: PASS
- Future append invariance at t=2 (swing high/low, bullish/bearish FVG): PASS (4/4)
- Input candle list unchanged (all four functions): PASS (4/4)
- Two identical runs (all four functions): PASS (4/4)

## Step 4 static findings

- test_fixtures.py: contains the word Michael (case-insensitive)
- Word Michael: test_fixtures.py: contains the word Michael (case-insensitive)
- Imported modules: candle.py:__future__, candle.py:dataclasses, candle.py:typing, fvg.py:__future__, swing.py:__future__, swing.py:candle, test_fixtures.py:__future__, test_fixtures.py:json, test_fixtures.py:os, test_fixtures.py:sys, test_fixtures.py:candle, test_fixtures.py:fvg, test_fixtures.py:swing, test_fixtures.py:ast
- Forbidden/network/pandas imports: none
- Old pipeline imports: none found; the token information_time occurs only in test_fixtures.py's forbidden-import guard list, not as an import
- File reads: test_fixtures.py:43: open(); test_fixtures.py:150: open()
- Module-level numeric assignments (includes test-harness state): fvg.py:25 GAP_CANDLES=3; swing.py:28 NEIGHBOURS_EACH_SIDE=1; test_fixtures.py:32 checks=0
- Threshold/ratio/default-named assignments: none
- Numeric interpretation: NEIGHBOURS_EACH_SIDE=1 is the V2 source number; GAP_CANDLES=3 is the V2 three-candle FVG structure. Other numeric literals found in implementation are fixed index/window offsets and validation (t-2, t-1, t+1, t<2), not price thresholds or ratios. Defaults found: Candle.closed=True and from_mapping(...).get('closed', True).
- Future-candle access: swing_at and fvg_at both use candles[:t+1], then c1=t-2, c2=t-1, c3=t; no access after index t found.
