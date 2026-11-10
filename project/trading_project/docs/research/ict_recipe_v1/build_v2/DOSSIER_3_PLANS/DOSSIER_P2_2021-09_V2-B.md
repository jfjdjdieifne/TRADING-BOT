# DOSSIER P2 — 2021-09_V2-B — plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336

Raw-material dossier. Prepared from saved outputs only; no engine run. Source selection line: `{"run": "2021-09_V2-B", "why": "seeded random", "plan_id": "plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336", "r": -1.050000000000111, "meta": {"seed": 6278280326450679685, "index": 9, "n": 16}, "state": "settled_stop", "file": "CARDS/2021-09_V2-B__seeded__plan_2021-09-16T07_50_00p00_00_1h_fvg_bullish_4336.md"}`

## D1. Identity and outcome
```
plan id          plan:2021-09-16T07:50:00+00:00:1h:fvg:bullish:4336
thesis id        1h:fvg:bullish:4336:bullish
direction        bullish
setup frame      1h   (target frames 1h / 1h)
entry            1.17825  (bullish limit at the zone edge)
stop             1.17775  (far side of fvg, 5.00 pips)
T1               1.18197  (37.20 pips)
T2               1.18204  (informational only)
R:R to T1        7.440
settlement       settled_stop / stop_touched at bar 52823 (price 1.17775)
hypothetical R   -1.0500
decision time    2021-09-16T07:50:00+00:00   (bar 52819)
trigger bar      52820
```

- arming events of this thesis: **1** (thesis id is unique in `plans_final.jsonl`; the D4 guard forbids re-arming). Confirmed by counting records with the same `thesis_id`.

## D2. Raw data rows (exact source-file rows, 5m)
```
timestamp                BidOpen BidHigh BidLow  BidClose BidVol  AskOpen AskHigh AskLow  AskClose AskVol  SprOpen
2021-09-16T02:50:00Z  1.18180 1.18181 1.18175 1.18181 47.2  1.18183 1.18184 1.18178 1.18184 48.3  0.000030
2021-09-16T02:55:00Z  1.18180 1.18196 1.18180 1.18189 173.5  1.18184 1.18199 1.18184 1.18192 125.6  0.000040
2021-09-16T03:00:00Z  1.18187 1.18193 1.18173 1.18180 212.3  1.18190 1.18195 1.18176 1.18183 99.1  0.000030
2021-09-16T03:05:00Z  1.18179 1.18197 1.18179 1.18188 110.1  1.18183 1.18199 1.18182 1.18191 70.2  0.000040
2021-09-16T03:10:00Z  1.18187 1.18187 1.18171 1.18173 130.2  1.18191 1.18191 1.18174 1.18177 55.8  0.000040
2021-09-16T03:15:00Z  1.18173 1.18173 1.18163 1.18165 78.2  1.18176 1.18176 1.18165 1.18169 44.2  0.000030
2021-09-16T03:20:00Z  1.18166 1.18170 1.18164 1.18165 68.8  1.18169 1.18174 1.18167 1.18168 205.8  0.000030
2021-09-16T03:25:00Z  1.18164 1.18169 1.18159 1.18161 50.4  1.18167 1.18172 1.18162 1.18163 47.1  0.000030
2021-09-16T03:30:00Z  1.18161 1.18162 1.18150 1.18151 105.8  1.18162 1.18165 1.18152 1.18154 106.6  0.000010
2021-09-16T03:35:00Z  1.18151 1.18155 1.18129 1.18130 136.2  1.18155 1.18157 1.18133 1.18134 108.2  0.000040
2021-09-16T03:40:00Z  1.18131 1.18136 1.18126 1.18130 57.2  1.18134 1.18139 1.18129 1.18133 70.2  0.000030
2021-09-16T03:45:00Z  1.18129 1.18132 1.18122 1.18124 101.0  1.18133 1.18135 1.18125 1.18128 34.2  0.000040
2021-09-16T03:50:00Z  1.18125 1.18126 1.18119 1.18121 26.8  1.18128 1.18129 1.18123 1.18124 24.6  0.000030
2021-09-16T03:55:00Z  1.18121 1.18123 1.18119 1.18121 22.1  1.18124 1.18126 1.18123 1.18125 37.6  0.000030
2021-09-16T04:00:00Z  1.18121 1.18127 1.18111 1.18112 69.8  1.18124 1.18130 1.18113 1.18113 103.0  0.000030
2021-09-16T04:05:00Z  1.18111 1.18119 1.18111 1.18119 44.3  1.18115 1.18123 1.18114 1.18123 73.1  0.000040
2021-09-16T04:10:00Z  1.18119 1.18119 1.18105 1.18105 134.0  1.18122 1.18122 1.18108 1.18108 54.0  0.000030
2021-09-16T04:15:00Z  1.18106 1.18106 1.18092 1.18096 126.7  1.18110 1.18110 1.18094 1.18099 75.3  0.000040
2021-09-16T04:20:00Z  1.18096 1.18100 1.18095 1.18099 134.1  1.18098 1.18104 1.18098 1.18103 78.2  0.000020
2021-09-16T04:25:00Z  1.18100 1.18110 1.18098 1.18101 66.0  1.18103 1.18112 1.18101 1.18105 48.1  0.000030
2021-09-16T04:30:00Z  1.18100 1.18102 1.18095 1.18102 52.2  1.18104 1.18105 1.18098 1.18104 66.3  0.000040
2021-09-16T04:35:00Z  1.18100 1.18115 1.18098 1.18112 54.7  1.18103 1.18118 1.18100 1.18116 111.6  0.000030
2021-09-16T04:40:00Z  1.18111 1.18111 1.18101 1.18103 61.4  1.18114 1.18114 1.18104 1.18107 32.6  0.000030
2021-09-16T04:45:00Z  1.18104 1.18112 1.18101 1.18104 64.7  1.18107 1.18115 1.18104 1.18108 109.8  0.000030
2021-09-16T04:50:00Z  1.18103 1.18111 1.18101 1.18111 95.7  1.18107 1.18115 1.18105 1.18115 108.6  0.000040
2021-09-16T04:55:00Z  1.18111 1.18113 1.18096 1.18096 74.3  1.18114 1.18116 1.18099 1.18100 88.7  0.000030
2021-09-16T05:00:00Z  1.18097 1.18102 1.18091 1.18096 86.5  1.18098 1.18106 1.18094 1.18100 135.5  0.000010
2021-09-16T05:05:00Z  1.18097 1.18118 1.18096 1.18111 77.3  1.18100 1.18122 1.18100 1.18115 151.8  0.000030
2021-09-16T05:10:00Z  1.18111 1.18111 1.18095 1.18101 109.7  1.18114 1.18114 1.18098 1.18104 87.4  0.000030
2021-09-16T05:15:00Z  1.18101 1.18112 1.18098 1.18107 79.7  1.18105 1.18115 1.18100 1.18110 88.8  0.000040
2021-09-16T05:20:00Z  1.18107 1.18111 1.18104 1.18111 30.8  1.18111 1.18115 1.18108 1.18115 54.4  0.000040
2021-09-16T05:25:00Z  1.18110 1.18110 1.18089 1.18090 258.0  1.18114 1.18114 1.18092 1.18093 150.9  0.000040
2021-09-16T05:30:00Z  1.18091 1.18091 1.18068 1.18071 231.1  1.18093 1.18093 1.18072 1.18076 201.4  0.000020
2021-09-16T05:35:00Z  1.18072 1.18072 1.18057 1.18061 284.8  1.18076 1.18076 1.18059 1.18065 200.2  0.000040
2021-09-16T05:40:00Z  1.18062 1.18067 1.18056 1.18061 189.7  1.18065 1.18070 1.18059 1.18065 158.7  0.000030
2021-09-16T05:45:00Z  1.18059 1.18065 1.18053 1.18055 205.8  1.18061 1.18069 1.18056 1.18058 133.2  0.000020
2021-09-16T05:50:00Z  1.18055 1.18055 1.18032 1.18042 339.5  1.18057 1.18057 1.18035 1.18046 123.9  0.000020
2021-09-16T05:55:00Z  1.18045 1.18052 1.18027 1.18027 140.2  1.18048 1.18056 1.18031 1.18031 230.5  0.000030
2021-09-16T06:00:00Z  1.18026 1.18067 1.18013 1.18067 421.6  1.18030 1.18071 1.18016 1.18071 409.8  0.000040
2021-09-16T06:05:00Z  1.18066 1.18070 1.18041 1.18048 465.7  1.18068 1.18073 1.18044 1.18051 273.5  0.000020
2021-09-16T06:10:00Z  1.18048 1.18057 1.18031 1.18052 394.2  1.18049 1.18060 1.18035 1.18056 280.2  0.000010
2021-09-16T06:15:00Z  1.18055 1.18061 1.18032 1.18057 254.8  1.18058 1.18064 1.18035 1.18060 209.6  0.000030
2021-09-16T06:20:00Z  1.18059 1.18072 1.18022 1.18042 348.0  1.18062 1.18075 1.18023 1.18045 464.8  0.000030
2021-09-16T06:25:00Z  1.18043 1.18056 1.18033 1.18048 334.7  1.18046 1.18060 1.18036 1.18051 295.1  0.000030
2021-09-16T06:30:00Z  1.18048 1.18048 1.18007 1.18029 237.2  1.18050 1.18050 1.18009 1.18032 278.2  0.000020
2021-09-16T06:35:00Z  1.18032 1.18052 1.18030 1.18051 191.1  1.18034 1.18055 1.18031 1.18054 148.2  0.000020
2021-09-16T06:40:00Z  1.18052 1.18062 1.18034 1.18058 279.6  1.18054 1.18065 1.18037 1.18060 418.9  0.000020
2021-09-16T06:45:00Z  1.18055 1.18060 1.18039 1.18041 431.5  1.18057 1.18063 1.18042 1.18044 242.4  0.000020
2021-09-16T06:50:00Z  1.18041 1.18042 1.17956 1.17956 473.2  1.18043 1.18045 1.17958 1.17958 282.8  0.000020
2021-09-16T06:55:00Z  1.17955 1.17956 1.17909 1.17917 508.9  1.17958 1.17959 1.17912 1.17920 404.1  0.000030
2021-09-16T07:00:00Z  1.17916 1.17950 1.17890 1.17948 648.7  1.17919 1.17952 1.17893 1.17951 685.6  0.000030
2021-09-16T07:05:00Z  1.17949 1.17949 1.17892 1.17907 324.3  1.17952 1.17952 1.17895 1.17910 322.8  0.000030
2021-09-16T07:10:00Z  1.17906 1.17911 1.17881 1.17886 303.1  1.17909 1.17914 1.17883 1.17888 221.2  0.000030
2021-09-16T07:15:00Z  1.17885 1.17932 1.17861 1.17928 372.3  1.17888 1.17935 1.17864 1.17931 283.1  0.000030
2021-09-16T07:20:00Z  1.17927 1.17927 1.17891 1.17892 430.7  1.17930 1.17930 1.17894 1.17895 386.4  0.000030
2021-09-16T07:25:00Z  1.17891 1.17896 1.17872 1.17892 393.1  1.17894 1.17899 1.17875 1.17895 291.3  0.000030
2021-09-16T07:30:00Z  1.17893 1.17928 1.17887 1.17928 265.3  1.17896 1.17931 1.17890 1.17929 333.3  0.000030
2021-09-16T07:35:00Z  1.17927 1.17927 1.17867 1.17870 384.4  1.17929 1.17929 1.17869 1.17872 248.8  0.000020
2021-09-16T07:40:00Z  1.17869 1.17882 1.17844 1.17845 334.8  1.17871 1.17884 1.17847 1.17848 335.1  0.000020
2021-09-16T07:45:00Z  1.17847 1.17847 1.17822 1.17838 385.7  1.17848 1.17850 1.17825 1.17840 273.7  0.000010
2021-09-16T07:50:00Z  1.17837 1.17840 1.17779 1.17781 434.1  1.17840 1.17843 1.17781 1.17783 299.2  0.000030
2021-09-16T07:55:00Z  1.17781 1.17853 1.17778 1.17814 522.8  1.17782 1.17856 1.17781 1.17817 422.0  0.000010
2021-09-16T08:00:00Z  1.17815 1.17844 1.17779 1.17844 521.5  1.17818 1.17845 1.17782 1.17845 403.7  0.000030
2021-09-16T08:05:00Z  1.17843 1.17844 1.17803 1.17821 320.2  1.17845 1.17847 1.17806 1.17824 257.7  0.000020
2021-09-16T08:10:00Z  1.17818 1.17818 1.17762 1.17763 443.3  1.17820 1.17820 1.17765 1.17766 501.2  0.000020
```
- 65 rows shown: 60 5m candles of context before the decision bar, then every 5m candle to settlement. Data file sha256 `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`.

## D3. Aggregation provenance
- setup frame `1h` = 60 minutes; built from 5m **bid** candles. open = first 5m open, high = max of 5m highs, low = min of 5m lows, close = last 5m close; volume summed; spread fields taken from the last 5m bar (declared in DECLARED_CHOICES_V2 row B).
- bid is used because the entry, stop and targets are all bid prices in this build; the ask is carried through the data rows only for the spread.
```
setup candle #4334  open 2021-09-13T11:00:00+00:00  close 2021-09-13T12:00:00+00:00  O 1.17757  H 1.17775  L 1.17700  C 1.17739
  built from 12 5m bars: 2021-09-13T11:00:00+00:00 .. 2021-09-13T11:55:00+00:00
  high = max(1.17763, 1.17773, 1.17765, 1.17766, 1.17752, 1.17756, 1.17745, 1.17770, 1.17775, 1.17753, 1.17713, 1.17751) = 1.17775
  low  = min(1.17739, 1.17737, 1.17737, 1.17738, 1.17738, 1.17740, 1.17737, 1.17735, 1.17752, 1.17704, 1.17700, 1.17712) = 1.17700
  open = 1.17757 (first 5m open), close = 1.17739 (last 5m close)
setup candle #4335  open 2021-09-13T12:00:00+00:00  close 2021-09-13T13:00:00+00:00  O 1.17739  H 1.17866  L 1.17713  C 1.17824
  built from 12 5m bars: 2021-09-13T12:00:00+00:00 .. 2021-09-13T12:55:00+00:00
  high = max(1.17755, 1.17814, 1.17817, 1.17804, 1.17793, 1.17827, 1.17841, 1.17849, 1.17828, 1.17840, 1.17856, 1.17866) = 1.17866
  low  = min(1.17713, 1.17740, 1.17788, 1.17763, 1.17766, 1.17777, 1.17816, 1.17796, 1.17808, 1.17816, 1.17829, 1.17824) = 1.17713
  open = 1.17739 (first 5m open), close = 1.17824 (last 5m close)
setup candle #4336  open 2021-09-13T13:00:00+00:00  close 2021-09-13T14:00:00+00:00  O 1.17825  H 1.18012  L 1.17825  C 1.17999
  built from 12 5m bars: 2021-09-13T13:00:00+00:00 .. 2021-09-13T13:55:00+00:00
  high = max(1.17866, 1.17867, 1.17867, 1.17879, 1.17901, 1.17954, 1.17946, 1.17975, 1.17962, 1.17969, 1.17994, 1.18012) = 1.18012
  low  = min(1.17825, 1.17845, 1.17838, 1.17848, 1.17869, 1.17903, 1.17913, 1.17941, 1.17932, 1.17947, 1.17952, 1.17981) = 1.17825
  open = 1.17825 (first 5m open), close = 1.17999 (last 5m close)
setup candle #4337  open 2021-09-13T14:00:00+00:00  close 2021-09-13T15:00:00+00:00  O 1.18001  H 1.18109  L 1.17923  C 1.18095
  built from 12 5m bars: 2021-09-13T14:00:00+00:00 .. 2021-09-13T14:55:00+00:00
  high = max(1.18033, 1.18071, 1.18063, 1.18070, 1.18064, 1.18022, 1.17981, 1.17999, 1.17999, 1.18051, 1.18079, 1.18109) = 1.18109
  low  = min(1.17995, 1.18007, 1.18022, 1.18024, 1.18008, 1.17966, 1.17923, 1.17926, 1.17965, 1.17996, 1.18029, 1.18053) = 1.17923
  open = 1.18001 (first 5m open), close = 1.18095 (last 5m close)
```

## D4. Higher-frame context used for the bias
```
daily  2021-09-14  O 1.18095 H 1.18458 L 1.18000 C 1.18023  completed/available at 2021-09-15T00:00:00+00:00
daily  2021-09-15  O 1.18024 H 1.18318 L 1.17991 C 1.18190  completed/available at 2021-09-16T00:00:00+00:00
weekly 2021-W36  O 1.18854 H 1.18857 L 1.18019 C 1.18115  completed/available at 2021-09-13T00:00:00+00:00
```
- bias as recorded at the decision: daily `UP`, weekly `DOWN`, resolved `UP`, conflict `True`.
- rule: `stream_v1.HtfState.bias` returns `UP` when the completed bucket's close is above its open, `DOWN` below, `FLAT` when equal. The recorded source string in every decision row is `ict_engine.htf aggregation, completion-labelled`. Direction for the plan = the **daily** value (DECLARED_CHOICES row 9), weekly recorded as context.

## D5. Dealing range
```
range low  1.18151  (swing candle #478)
range high 1.18197  (swing candle #478)
midpoint   1.18174
entry position ratio 0.0000  label `discount`  state `BELOW_RANGE`
```
- the swing indices printed above are **window-local positions** in the rolling buffer at read time (`stream_v1.swing_now` stores `candle_indices['c2']` from the window, not an absolute candle index). Their timestamps and right-side confirmation candles are therefore **NOT_RECOVERABLE_WITHOUT_RERUN** — recorded as defect D11. What is certain from the record is that both swings were confirmed before the decision, because the range existed at the decision bar and the buffer holds only closed candles.

## D6. Liquidity and sweep
```
level    side   kind                        frame  formed_bar  age_bars  state
1.18197  high   relative_equal_pair         1h            479      3922  untaken
1.18204  high   relative_equal_pair         1h            479      3922  untaken
1.18226  high   relative_equal_pair         1h            479      3922  untaken
1.18318  high   relative_equal_pair         1h            479      3922  untaken
1.18458  high   relative_equal_pair         1h            479      3922  untaken
1.17700  low    relative_equal_pair         1h            479      3922  untaken
```
- sweep reference at the decision: high `{'answer': 'NO', 'level': 1.1819700000000002}` · low `{'answer': 'NO', 'level': 1.18151}`. The zone's own formation index is `4336`; for a `sweep_level` zone the sweep candle is that index, otherwise the sweep did not define this zone.
- ranked target pools at the decision: `[{'level': 1.1819700000000002, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 9.043478260867424}, {'level': 1.1820400000000002, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 9.195652173910892}, {'level': 1.18226, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 9.673913043475732}, {'level': 1.18318, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 11.673913043474766}]`
- why T1 and not the pools between: T1 is the first entry of `rank_draws` among the pools on the trade's side that lie beyond the entry price; T2 is the second. Pools behind the entry are excluded by `plan_v1.targets_ahead` (`ahead = level > entry` for bullish). The formation index of each target pool is **NOT_RECOVERABLE_WITHOUT_RERUN** (defect D5) — the plan record stores only the level, kind and frame.

## D7. Displacement and structure
```
displacement   {'answer': 'YES', 'ratio': 0.6687116564418223}
sweep high     {'answer': 'NO', 'level': 1.1819700000000002}
sweep low      {'answer': 'NO', 'level': 1.18151}
structure      {'direction': 'DOWN', 'level': 1.18151, 'level_index': 478}
order block    None
```
- displacement variant is `V-D-01`: body/range above 60 (`SOURCE_NUMBER`, claim F1), equality → UNDECIDED, read over `candles[:t+1]`. The ratio printed above is the value the module returned.

## D8. Zone and candidate list
```
zone id     1h:fvg:bullish:4336
kind        fvg   direction bullish
lower/upper 1.17775 / 1.17825
formed at   setup candle #4336
existed from 2021-09-13T14:00:00+00:00 (that candle's close); decision 2021-09-16T07:50:00+00:00 → OK
```
- forming candle #4334: 2021-09-13T11:00:00+00:00 O 1.17757 H 1.17775 L 1.17700 C 1.17739
- forming candle #4335: 2021-09-13T12:00:00+00:00 O 1.17739 H 1.17866 L 1.17713 C 1.17824
- forming candle #4336: 2021-09-13T13:00:00+00:00 O 1.17825 H 1.18012 L 1.17825 C 1.17999

Candidates considered at the arming moment, in the order the engine ranked them:
```
1h:fvg:bullish:4336                fvg         [1.17775, 1.17825]  fresh=False  bias_agrees=True  distance_ratio=0.4130
1h:fvg:bullish:4337                fvg         [1.17866, 1.17923]  fresh=False  bias_agrees=True  distance_ratio=2.4674
```
- criteria in the order applied: `{"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.41304347826056526}}`
- criteria conflict logged: **False** (a conflict ⇒ no plan, so a plan implies no conflict)
- why this zone won: first by bias agreement, then freshness, then the smallest context-relative distance (`rank_zones` in `build_v1/plan_v1.py`).

## D9. Decision trace
Decision rows at the setup-frame closes between the zone formation and the arming:
```
time                      decision      reason
2021-09-13T12:00:00+00:00  setup candle #4334 closed
2021-09-13T13:00:00+00:00  setup candle #4335 closed
2021-09-13T14:00:00+00:00  setup candle #4336 closed
2021-09-16T07:50:00+00:00  ARMED         V2-B / V2-B
```
- the per-candle sub-decisions (every gate answer between those closes) are written to `decisions.jsonl` at the **5m decision cadence**, not at setup-frame closes; the saved run writes one row per 5m bar. The set of gate answers at the exact setup closes is **NOT_RECOVERABLE_WITHOUT_RERUN** only for bars outside the decision window; inside it every 5m row is saved and the rows at the closing 5m bars carry the question and answer.
- 5m touch: first touching bar **52820** (2021-09-16T07:55:00+00:00); fill convention = limit at the zone edge (v1 convention), fill price 1.17825.

## D10. Levels and costs
```
stop            1.17775   rule: `far side of fvg` (DECLARED_CHOICES_V2 row D: the far edge of the setup-frame zone; sweep zones use the sweep wick; no pip minimum, no filter)
stop distance   5.00 pips = 0.3067 of the setup candle's range
half-spread     0.15 pips = 0.0600 of the stop
T1 distance     37.20 pips
T2 distance     37.90 pips
R:R T1 / T2     7.440 / 7.580
```

## D11. Candle-by-candle execution
```
bar    time                   bid O/H/L/C                 ask O/H/L/C                 touch  in-zone  stop  T1   spread
52820  2021-09-16T07:55:00+00:00  1.17781/1.17853/1.17778/1.17814  1.17782/1.17856/1.17781/1.17817  yes    yes      no    no   0.000010
52821  2021-09-16T08:00:00+00:00  1.17815/1.17844/1.17779/1.17844  1.17818/1.17845/1.17782/1.17845  yes    no       no    no   0.000030
52822  2021-09-16T08:05:00+00:00  1.17843/1.17844/1.17803/1.17821  1.17845/1.17847/1.17806/1.17824  yes    yes      no    no   0.000020
52823  2021-09-16T08:10:00+00:00  1.17818/1.17818/1.17762/1.17763  1.17820/1.17820/1.17765/1.17766  no     no       YES   no   0.000020
52824  2021-09-16T08:15:00+00:00  1.17762/1.17774/1.17741/1.17741  1.17765/1.17776/1.17743/1.17744  no     no       YES   no   0.000030
```
```
independent replay (this file does not import settlement code):
  for each 5m bar from decision+1, up to 288 bars:
    if not triggered: skip unless low <= entry <= high; if 288 bars pass -> expired, R = 0
    if stop reached (bullish low <= stop / bearish high >= stop) -> settle at stop
    elif T1 reached (bullish high >= T1 / bearish low <= T1) -> settle at T1
    cost = half_spread_at_decision + spread_of_exit_bar/2 ; R = (gross - cost)/|entry-stop|
  result: stop_touched at bar 52823 price 1.17775 -> R -1.050000
  engine: stop_touched at bar 52823 price 1.17775 -> R -1.050000
  verdict: MATCH (tolerance 1e-9, floating point only)
```

## D12. What the engine did not look at (checked in the code path)
```
item                          used?  evidence
weekly/monthly FVG or OB      no     build_v2/wrapper_v2.py gathers zones only from the setup
                                     frame's gaps/blocks/sweep (gather_zones call, line ~330)
session context beyond flag   partial gates() reads only ctx['session']['in_window']
                                     (build_v1/plan_v1.py gates, first condition)
volume                        no     no volume field is read after loading; grep 'bid_volume'
                                     in build_v2 = only the Bar constructor
previous-day high/low         no     HtfState produces daily open/high/low/close; only the
                                     bias (close vs open) is consumed
equal highs/lows as pools     partial LiquidityState.push_swings forms relative_equal_pair
                                     without an equality cutoff (KNOWLEDGE_GAP)
news / calendar               no     no such source exists in the repository path
other instruments             no     one data file, one symbol
```

## D13. Defects observed and questions for an expert
```
D5  T1/T2 pool formation index not saved        -> that check is NOT_RECOVERABLE_WITHOUT_RERUN
D6  v1 evaluates on the decision bar, v2 on the next bar (does not affect this plan: variant
    V2-*)
D9  cards show setup candle 0 when formed_index is None (sweep zones only)
D10 NOT_EVALUABLE rendered as PASS in the card checklist
D11 swing level_index/confirm_index are window-local -> swing timestamps not recoverable from
    the record without a re-run
```
Questions for an ICT expert — NOT JUDGED BY THE AGENT:
1. Is this fvg on the 1h frame a valid zone, and are these the candles you would use?
2. Was the bullish expectation right for this session window and this dealing-range position (`discount`)?
3. Would you place the stop at the far edge of the zone (1.17775) or inside it at the mean threshold, as the source's sentence suggests?

## D14. What this does NOT establish

- It does not establish that the reading is correct ICT: nothing here is judged, only reported.
- It does not establish the plan's merit: R is hypothetical under one stated fill convention.
- The dossier is assembled from saved records plus recomputed aggregation; anything the records do not carry is marked NOT_RECOVERABLE_WITHOUT_RERUN rather than reconstructed.
