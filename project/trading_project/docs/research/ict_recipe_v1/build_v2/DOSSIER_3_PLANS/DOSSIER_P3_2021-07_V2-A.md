# DOSSIER P3 — 2021-07_V2-A — plan:2021-07-23T07:50:00+00:00:15m:fvg:bearish:13843

Raw-material dossier. Prepared from saved outputs only; no engine run. Source selection line: `{"run": "2021-07_V2-A", "why": "seeded random", "plan_id": "plan:2021-07-23T07:50:00+00:00:15m:fvg:bearish:13843", "r": -1.2499999999996034, "meta": {"seed": 13751166741018251497, "index": 17, "n": 26}, "state": "settled_stop", "file": "CARDS/2021-07_V2-A__seeded__plan_2021-07-23T07_50_00p00_00_15m_fvg_bearish_13843.md"}`

## D1. Identity and outcome
```
plan id          plan:2021-07-23T07:50:00+00:00:15m:fvg:bearish:13843
thesis id        15m:fvg:bearish:13843:bearish
direction        bearish
setup frame      15m   (target frames 15m / 15m)
entry            1.17753  (bearish limit at the zone edge)
stop             1.17767  (far side of fvg, 1.40 pips)
T1               1.17642  (11.10 pips)
T2               1.17627  (informational only)
R:R to T1        7.929
settlement       settled_stop / stop_touched at bar 41590 (price 1.17767)
hypothetical R   -1.2500
decision time    2021-07-23T07:50:00+00:00   (bar 41588)
trigger bar      41590
```

- arming events of this thesis: **1** (thesis id is unique in `plans_final.jsonl`; the D4 guard forbids re-arming). Confirmed by counting records with the same `thesis_id`.

## D2. Raw data rows (exact source-file rows, 5m)
```
timestamp                BidOpen BidHigh BidLow  BidClose BidVol  AskOpen AskHigh AskLow  AskClose AskVol  SprOpen
2021-07-23T02:50:00Z  1.17721 1.17724 1.17716 1.17722 173.0  1.17725 1.17727 1.17719 1.17727 99.2  0.000040
2021-07-23T02:55:00Z  1.17725 1.17752 1.17725 1.17742 466.2  1.17727 1.17755 1.17727 1.17746 158.6  0.000020
2021-07-23T03:00:00Z  1.17741 1.17748 1.17737 1.17742 258.8  1.17746 1.17752 1.17742 1.17744 120.9  0.000050
2021-07-23T03:05:00Z  1.17740 1.17740 1.17730 1.17737 138.6  1.17744 1.17744 1.17734 1.17740 93.3  0.000040
2021-07-23T03:10:00Z  1.17737 1.17749 1.17730 1.17747 161.4  1.17741 1.17753 1.17734 1.17752 239.0  0.000040
2021-07-23T03:15:00Z  1.17748 1.17759 1.17747 1.17748 109.2  1.17752 1.17763 1.17751 1.17753 395.4  0.000040
2021-07-23T03:20:00Z  1.17749 1.17754 1.17747 1.17751 59.5  1.17753 1.17758 1.17752 1.17754 149.8  0.000040
2021-07-23T03:25:00Z  1.17749 1.17752 1.17742 1.17747 143.0  1.17754 1.17757 1.17747 1.17752 168.9  0.000050
2021-07-23T03:30:00Z  1.17745 1.17745 1.17723 1.17728 163.8  1.17750 1.17750 1.17728 1.17733 244.8  0.000050
2021-07-23T03:35:00Z  1.17729 1.17736 1.17721 1.17727 147.4  1.17734 1.17740 1.17726 1.17731 70.6  0.000050
2021-07-23T03:40:00Z  1.17727 1.17727 1.17712 1.17717 206.2  1.17732 1.17732 1.17716 1.17722 112.2  0.000050
2021-07-23T03:45:00Z  1.17718 1.17718 1.17701 1.17706 192.1  1.17722 1.17723 1.17704 1.17710 120.9  0.000040
2021-07-23T03:50:00Z  1.17706 1.17717 1.17706 1.17713 89.0  1.17709 1.17720 1.17709 1.17717 102.0  0.000030
2021-07-23T03:55:00Z  1.17713 1.17717 1.17694 1.17696 266.3  1.17716 1.17720 1.17697 1.17698 112.8  0.000030
2021-07-23T04:00:00Z  1.17695 1.17701 1.17692 1.17701 55.7  1.17697 1.17705 1.17695 1.17704 52.3  0.000020
2021-07-23T04:05:00Z  1.17700 1.17702 1.17681 1.17685 164.2  1.17704 1.17705 1.17686 1.17689 101.9  0.000040
2021-07-23T04:10:00Z  1.17685 1.17691 1.17675 1.17683 209.0  1.17690 1.17695 1.17679 1.17686 179.5  0.000050
2021-07-23T04:15:00Z  1.17683 1.17700 1.17681 1.17697 628.9  1.17687 1.17704 1.17685 1.17702 535.7  0.000040
2021-07-23T04:20:00Z  1.17697 1.17705 1.17683 1.17697 610.4  1.17701 1.17709 1.17688 1.17702 468.9  0.000040
2021-07-23T04:25:00Z  1.17696 1.17698 1.17687 1.17696 342.0  1.17700 1.17702 1.17691 1.17701 228.6  0.000040
2021-07-23T04:30:00Z  1.17695 1.17700 1.17689 1.17697 178.7  1.17699 1.17706 1.17695 1.17702 174.5  0.000040
2021-07-23T04:35:00Z  1.17698 1.17699 1.17693 1.17696 61.2  1.17702 1.17704 1.17696 1.17702 58.6  0.000040
2021-07-23T04:40:00Z  1.17698 1.17699 1.17693 1.17693 106.7  1.17701 1.17703 1.17695 1.17695 67.2  0.000030
2021-07-23T04:45:00Z  1.17693 1.17698 1.17693 1.17697 36.1  1.17696 1.17702 1.17696 1.17701 20.2  0.000030
2021-07-23T04:50:00Z  1.17697 1.17699 1.17688 1.17693 62.6  1.17700 1.17702 1.17691 1.17696 20.1  0.000030
2021-07-23T04:55:00Z  1.17694 1.17696 1.17671 1.17679 153.1  1.17696 1.17700 1.17675 1.17680 83.6  0.000020
2021-07-23T05:00:00Z  1.17678 1.17684 1.17673 1.17683 261.7  1.17682 1.17687 1.17677 1.17687 141.6  0.000040
2021-07-23T05:05:00Z  1.17682 1.17686 1.17678 1.17683 91.3  1.17686 1.17691 1.17681 1.17688 69.3  0.000040
2021-07-23T05:10:00Z  1.17685 1.17709 1.17684 1.17705 81.1  1.17689 1.17712 1.17689 1.17708 91.4  0.000040
2021-07-23T05:15:00Z  1.17704 1.17710 1.17703 1.17709 40.0  1.17708 1.17713 1.17706 1.17712 55.7  0.000040
2021-07-23T05:20:00Z  1.17707 1.17716 1.17706 1.17714 56.1  1.17708 1.17719 1.17708 1.17717 51.4  0.000010
2021-07-23T05:25:00Z  1.17715 1.17716 1.17708 1.17709 35.0  1.17719 1.17720 1.17711 1.17712 32.5  0.000040
2021-07-23T05:30:00Z  1.17709 1.17711 1.17686 1.17692 263.2  1.17711 1.17713 1.17690 1.17697 81.0  0.000020
2021-07-23T05:35:00Z  1.17694 1.17697 1.17692 1.17695 94.7  1.17698 1.17701 1.17696 1.17699 46.8  0.000040
2021-07-23T05:40:00Z  1.17694 1.17702 1.17693 1.17701 78.7  1.17698 1.17705 1.17696 1.17704 67.2  0.000040
2021-07-23T05:45:00Z  1.17701 1.17702 1.17688 1.17688 58.2  1.17705 1.17706 1.17689 1.17691 95.9  0.000040
2021-07-23T05:50:00Z  1.17689 1.17690 1.17672 1.17673 149.3  1.17691 1.17692 1.17676 1.17677 196.3  0.000020
2021-07-23T05:55:00Z  1.17672 1.17678 1.17637 1.17644 326.1  1.17675 1.17681 1.17640 1.17648 162.0  0.000030
2021-07-23T06:00:00Z  1.17642 1.17653 1.17627 1.17652 347.3  1.17646 1.17655 1.17629 1.17655 272.1  0.000040
2021-07-23T06:05:00Z  1.17652 1.17667 1.17644 1.17666 208.7  1.17654 1.17670 1.17645 1.17669 194.9  0.000020
2021-07-23T06:10:00Z  1.17665 1.17685 1.17652 1.17684 130.7  1.17668 1.17688 1.17653 1.17687 151.8  0.000030
2021-07-23T06:15:00Z  1.17683 1.17714 1.17678 1.17701 159.1  1.17686 1.17717 1.17681 1.17704 176.2  0.000030
2021-07-23T06:20:00Z  1.17702 1.17718 1.17694 1.17714 150.2  1.17704 1.17721 1.17697 1.17717 126.2  0.000020
2021-07-23T06:25:00Z  1.17713 1.17719 1.17706 1.17715 107.1  1.17718 1.17721 1.17709 1.17717 117.2  0.000050
2021-07-23T06:30:00Z  1.17712 1.17732 1.17710 1.17719 168.4  1.17716 1.17734 1.17712 1.17722 120.9  0.000040
2021-07-23T06:35:00Z  1.17718 1.17736 1.17701 1.17734 222.4  1.17721 1.17739 1.17703 1.17737 230.7  0.000030
2021-07-23T06:40:00Z  1.17735 1.17742 1.17704 1.17704 195.0  1.17737 1.17745 1.17707 1.17708 164.4  0.000020
2021-07-23T06:45:00Z  1.17708 1.17719 1.17690 1.17697 215.7  1.17710 1.17721 1.17693 1.17701 233.4  0.000020
2021-07-23T06:50:00Z  1.17698 1.17705 1.17667 1.17676 209.7  1.17701 1.17708 1.17670 1.17678 174.1  0.000030
2021-07-23T06:55:00Z  1.17677 1.17722 1.17677 1.17715 288.5  1.17678 1.17725 1.17678 1.17719 316.6  0.000010
2021-07-23T07:00:00Z  1.17715 1.17726 1.17651 1.17661 408.5  1.17718 1.17730 1.17654 1.17664 506.9  0.000030
2021-07-23T07:05:00Z  1.17663 1.17701 1.17655 1.17684 314.9  1.17665 1.17704 1.17657 1.17686 408.3  0.000020
2021-07-23T07:10:00Z  1.17686 1.17762 1.17686 1.17752 409.6  1.17688 1.17766 1.17688 1.17759 497.2  0.000020
2021-07-23T07:15:00Z  1.17734 1.17734 1.17675 1.17698 709.8  1.17739 1.17739 1.17678 1.17702 714.7  0.000050
2021-07-23T07:20:00Z  1.17701 1.17708 1.17642 1.17665 669.1  1.17703 1.17712 1.17645 1.17669 532.9  0.000020
2021-07-23T07:25:00Z  1.17664 1.17678 1.17642 1.17665 589.0  1.17668 1.17681 1.17646 1.17675 307.9  0.000040
2021-07-23T07:30:00Z  1.17673 1.17735 1.17668 1.17730 1057.1  1.17675 1.17739 1.17671 1.17732 1146.9  0.000020
2021-07-23T07:35:00Z  1.17730 1.17745 1.17712 1.17728 438.4  1.17733 1.17748 1.17714 1.17731 396.1  0.000030
2021-07-23T07:40:00Z  1.17731 1.17736 1.17696 1.17702 407.6  1.17734 1.17739 1.17699 1.17705 380.7  0.000030
2021-07-23T07:45:00Z  1.17701 1.17747 1.17682 1.17743 302.0  1.17704 1.17750 1.17685 1.17746 462.8  0.000030
2021-07-23T07:50:00Z  1.17746 1.17772 1.17737 1.17766 358.5  1.17749 1.17775 1.17740 1.17768 729.9  0.000030
2021-07-23T07:55:00Z  1.17768 1.17791 1.17755 1.17773 450.6  1.17770 1.17794 1.17757 1.17777 332.2  0.000020
2021-07-23T08:00:00Z  1.17770 1.17797 1.17749 1.17757 348.9  1.17774 1.17800 1.17750 1.17760 353.9  0.000040
```
- 63 rows shown: 60 5m candles of context before the decision bar, then every 5m candle to settlement. Data file sha256 `38be0503fd56269686a6f3d25f5e537e2ac5682ea9a5d79af1765acd224a6ab4`.

## D3. Aggregation provenance
- setup frame `15m` = 15 minutes; built from 5m **bid** candles. open = first 5m open, high = max of 5m highs, low = min of 5m lows, close = last 5m close; volume summed; spread fields taken from the last 5m bar (declared in DECLARED_CHOICES_V2 row B).
- bid is used because the entry, stop and targets are all bid prices in this build; the ask is carried through the data rows only for the spread.
```
setup candle #13841  open 2021-07-23T01:30:00+00:00  close 2021-07-23T01:45:00+00:00  O 1.17792  H 1.17804  L 1.17767  C 1.17773
  built from 3 5m bars: 2021-07-23T01:30:00+00:00 .. 2021-07-23T01:40:00+00:00
  high = max(1.17793, 1.17804, 1.17782) = 1.17804
  low  = min(1.17789, 1.17784, 1.17767) = 1.17767
  open = 1.17792 (first 5m open), close = 1.17773 (last 5m close)
setup candle #13842  open 2021-07-23T01:45:00+00:00  close 2021-07-23T02:00:00+00:00  O 1.17774  H 1.17783  L 1.17749  C 1.17749
  built from 3 5m bars: 2021-07-23T01:45:00+00:00 .. 2021-07-23T01:55:00+00:00
  high = max(1.17783, 1.17776, 1.17763) = 1.17783
  low  = min(1.17772, 1.17763, 1.17749) = 1.17749
  open = 1.17774 (first 5m open), close = 1.17749 (last 5m close)
setup candle #13843  open 2021-07-23T02:00:00+00:00  close 2021-07-23T02:15:00+00:00  O 1.17752  H 1.17753  L 1.17729  C 1.17735
  built from 3 5m bars: 2021-07-23T02:00:00+00:00 .. 2021-07-23T02:10:00+00:00
  high = max(1.17753, 1.17752, 1.17746) = 1.17753
  low  = min(1.17749, 1.17730, 1.17729) = 1.17729
  open = 1.17752 (first 5m open), close = 1.17735 (last 5m close)
setup candle #13844  open 2021-07-23T02:15:00+00:00  close 2021-07-23T02:30:00+00:00  O 1.17736  H 1.17738  L 1.17706  C 1.17718
  built from 3 5m bars: 2021-07-23T02:15:00+00:00 .. 2021-07-23T02:25:00+00:00
  high = max(1.17738, 1.17732, 1.17727) = 1.17738
  low  = min(1.17722, 1.17711, 1.17706) = 1.17706
  open = 1.17736 (first 5m open), close = 1.17718 (last 5m close)
```

## D4. Higher-frame context used for the bias
```
daily  2021-07-21  O 1.17811 H 1.18046 L 1.17518 C 1.17922  completed/available at 2021-07-22T00:00:00+00:00
daily  2021-07-22  O 1.17925 H 1.18304 L 1.17572 C 1.17722  completed/available at 2021-07-23T00:00:00+00:00
weekly 2021-W28  O 1.18722 H 1.18802 L 1.17717 C 1.18125  completed/available at 2021-07-19T00:00:00+00:00
```
- bias as recorded at the decision: daily `DOWN`, weekly `DOWN`, resolved `DOWN`, conflict `False`.
- rule: `stream_v1.HtfState.bias` returns `UP` when the completed bucket's close is above its open, `DOWN` below, `FLAT` when equal. The recorded source string in every decision row is `ict_engine.htf aggregation, completion-labelled`. Direction for the plan = the **daily** value (DECLARED_CHOICES row 9), weekly recorded as context.

## D5. Dealing range
```
range low  1.17642  (swing candle #1918)
range high 1.17762  (swing candle #1918)
midpoint   1.17702
entry position ratio 0.5000  label `premium`  state `INSIDE_RANGE`
```
- the swing indices printed above are **window-local positions** in the rolling buffer at read time (`stream_v1.swing_now` stores `candle_indices['c2']` from the window, not an absolute candle index). Their timestamps and right-side confirmation candles are therefore **NOT_RECOVERABLE_WITHOUT_RERUN** — recorded as defect D11. What is certain from the record is that both swings were confirmed before the decision, because the range existed at the decision bar and the buffer holds only closed candles.

## D6. Liquidity and sweep
```
level    side   kind                        frame  formed_bar  age_bars  state
1.17762  high   relative_equal_pair         15m          1919     11946  untaken
1.17804  high   relative_equal_pair         15m          1919     11946  untaken
1.18304  high   relative_equal_pair         15m          1919     11946  untaken
1.17642  low    relative_equal_pair         15m          1919     11946  untaken
1.17627  low    relative_equal_pair         15m          1919     11946  untaken
1.17617  low    relative_equal_pair         15m          1919     11946  untaken
1.17574  low    relative_equal_pair         15m          1919     11946  untaken
1.17572  low    relative_equal_pair         15m          1919     11946  untaken
```
- sweep reference at the decision: high `{'answer': 'NO', 'level': 1.17762}` · low `{'answer': 'NO', 'level': 1.17642}`. The zone's own formation index is `13843`; for a `sweep_level` zone the sweep candle is that index, otherwise the sweep did not define this zone.
- ranked target pools at the decision: `[{'level': 1.17642, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.0333333333335555}, {'level': 1.17627, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.1583333333336479}, {'level': 1.1761700000000002, 'kind': 'relative_equal_pair', 'frame': '15m', 'distance_ratio': 1.2416666666667961}, {'level': 1.1761700000000002, 'kind': 'relative_equal_pair', 'frame': '1h', 'distance_ratio': 1.2416666666667961}]`
- why T1 and not the pools between: T1 is the first entry of `rank_draws` among the pools on the trade's side that lie beyond the entry price; T2 is the second. Pools behind the entry are excluded by `plan_v1.targets_ahead` (`ahead = level > entry` for bullish). The formation index of each target pool is **NOT_RECOVERABLE_WITHOUT_RERUN** (defect D5) — the plan record stores only the level, kind and frame.

## D7. Displacement and structure
```
displacement   {'answer': 'NO', 'ratio': 0.3766233766235676}
sweep high     {'answer': 'NO', 'level': 1.17762}
sweep low      {'answer': 'NO', 'level': 1.17642}
structure      None
order block    None
```
- displacement variant is `V-D-01`: body/range above 60 (`SOURCE_NUMBER`, claim F1), equality → UNDECIDED, read over `candles[:t+1]`. The ratio printed above is the value the module returned.

## D8. Zone and candidate list
```
zone id     15m:fvg:bearish:13843
kind        fvg   direction bearish
lower/upper 1.17753 / 1.17767
formed at   setup candle #13843
existed from 2021-07-23T02:15:00+00:00 (that candle's close); decision 2021-07-23T07:50:00+00:00 → OK
```
- forming candle #13841: 2021-07-23T01:30:00+00:00 O 1.17792 H 1.17804 L 1.17767 C 1.17773
- forming candle #13842: 2021-07-23T01:45:00+00:00 O 1.17774 H 1.17783 L 1.17749 C 1.17749
- forming candle #13843: 2021-07-23T02:00:00+00:00 O 1.17752 H 1.17753 L 1.17729 C 1.17735

Candidates considered at the arming moment, in the order the engine ranked them:
```
15m:fvg:bearish:13843              fvg         [1.17753, 1.17767]  fresh=False  bias_agrees=True  distance_ratio=0.0500
15m:fvg:bearish:13801              fvg         [1.17792, 1.17824]  fresh=False  bias_agrees=True  distance_ratio=0.3500
15m:fvg:bearish:13796              fvg         [1.17981, 1.18136]  fresh=False  bias_agrees=True  distance_ratio=2.4375
```
- criteria in the order applied: `{"i": {"name": "bias agreement with completed daily bias", "tag": "ENGINEERING_CHOICE", "value": true}, "ii": {"name": "freshness (never closed through)", "tag": "ENGINEERING_CHOICE", "value": false}, "iii": {"name": "context-relative distance (rank_draws ratio)", "tag": "SOURCE_NUMBER", "value": 0.05000000000014803}}`
- criteria conflict logged: **False** (a conflict ⇒ no plan, so a plan implies no conflict)
- why this zone won: first by bias agreement, then freshness, then the smallest context-relative distance (`rank_zones` in `build_v1/plan_v1.py`).

## D9. Decision trace
Decision rows at the setup-frame closes between the zone formation and the arming:
```
time                      decision      reason
2021-07-23T01:45:00+00:00  setup candle #13841 closed
2021-07-23T02:00:00+00:00  setup candle #13842 closed
2021-07-23T02:15:00+00:00  setup candle #13843 closed
2021-07-23T07:50:00+00:00  ARMED         V2-A / V2-A
```
- the per-candle sub-decisions (every gate answer between those closes) are written to `decisions.jsonl` at the **5m decision cadence**, not at setup-frame closes; the saved run writes one row per 5m bar. The set of gate answers at the exact setup closes is **NOT_RECOVERABLE_WITHOUT_RERUN** only for bars outside the decision window; inside it every 5m row is saved and the rows at the closing 5m bars carry the question and answer.
- 5m touch: first touching bar **41590** (2021-07-23T08:00:00+00:00); fill convention = limit at the zone edge (v1 convention), fill price 1.17753.

## D10. Levels and costs
```
stop            1.17767   rule: `far side of fvg` (DECLARED_CHOICES_V2 row D: the far edge of the setup-frame zone; sweep zones use the sweep wick; no pip minimum, no filter)
stop distance   1.40 pips = 0.1818 of the setup candle's range
half-spread     0.15 pips = 0.2143 of the stop
T1 distance     11.10 pips
T2 distance     12.60 pips
R:R T1 / T2     7.929 / 9.000
```

## D11. Candle-by-candle execution
```
bar    time                   bid O/H/L/C                 ask O/H/L/C                 touch  in-zone  stop  T1   spread
41589  2021-07-23T07:55:00+00:00  1.17768/1.17791/1.17755/1.17773  1.17770/1.17794/1.17757/1.17777  no     no       YES   no   0.000020
41590  2021-07-23T08:00:00+00:00  1.17770/1.17797/1.17749/1.17757  1.17774/1.17800/1.17750/1.17760  yes    yes      YES   no   0.000040
41591  2021-07-23T08:05:00+00:00  1.17760/1.17797/1.17742/1.17791  1.17762/1.17799/1.17745/1.17793  yes    no       YES   no   0.000020
```
```
independent replay (this file does not import settlement code):
  for each 5m bar from decision+1, up to 288 bars:
    if not triggered: skip unless low <= entry <= high; if 288 bars pass -> expired, R = 0
    if stop reached (bullish low <= stop / bearish high >= stop) -> settle at stop
    elif T1 reached (bullish high >= T1 / bearish low <= T1) -> settle at T1
    cost = half_spread_at_decision + spread_of_exit_bar/2 ; R = (gross - cost)/|entry-stop|
  result: stop_touched at bar 41590 price 1.17767 -> R -1.250000
  engine: stop_touched at bar 41590 price 1.17767 -> R -1.250000
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
1. Is this fvg on the 15m frame a valid zone, and are these the candles you would use?
2. Was the bearish expectation right for this session window and this dealing-range position (`premium`)?
3. Would you place the stop at the far edge of the zone (1.17767) or inside it at the mean threshold, as the source's sentence suggests?

## D14. What this does NOT establish

- It does not establish that the reading is correct ICT: nothing here is judged, only reported.
- It does not establish the plan's merit: R is hypothetical under one stated fill convention.
- The dossier is assembled from saved records plus recomputed aggregation; anything the records do not carry is marked NOT_RECOVERABLE_WITHOUT_RERUN rather than reconstructed.
