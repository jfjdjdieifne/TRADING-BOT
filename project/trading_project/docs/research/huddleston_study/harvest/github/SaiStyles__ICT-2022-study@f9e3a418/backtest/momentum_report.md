# His on-close macro vs the published intraday-momentum anomaly

`dev` slice, **2,969 sessions**. Ledger n = 92. Reserve untouched, holdout SEALED. Bar is |t| > 3.0 (DECISIONS.md 24).

`[OUTSIDE]` **Market intraday momentum** (JFE 2021): across 60+ futures
1974-2020, the last 30 minutes' return is positively predicted by the
return over the rest of the day. **ep32 [11:32] and ep05 [26:53] describe
the same window independently** - the corpus's only overlap with
peer-reviewed work.

`spread` = mean forward return after an up day minus after a down day.
Positive means the day's direction continues into the window.
`pctile` ranks his window against same-length windows of the same sessions.

| anchor | window | n | spread | **t** | hit rate | signed | **pctile** | best control |
|---|---|---|---|---|---|---|---|---|
| prev_close | on-close macro 1500-1600 (ep32 11:32) | 2,969 | +2.41bp | **+1.62** | 48.0% | +1.18bp | **94** | 11:30 (t=+1.64) |
| prev_close | last 30min 1530-1600 (the paper's window) | 2,969 | +1.95bp | **+1.68** | 47.3% | +0.97bp | **94** | 01:00 (t=+1.68) |
| prev_close | 1540-1600 (ep05 26:53) | 2,969 | +1.58bp | **+1.55** | 47.1% | +0.72bp | **94** | 03:30 (t=+2.19) |
| midnight | on-close macro 1500-1600 (ep32 11:32) | 2,641 | +2.63bp | **+1.68** | 48.9% | +1.29bp | **93** | 03:30 (t=+1.80) |
| midnight | last 30min 1530-1600 (the paper's window) | 2,641 | +1.76bp | **+1.43** | 47.4% | +0.88bp | **90** | 03:30 (t=+2.17) |
| midnight | 1540-1600 (ep05 26:53) | 2,641 | +1.38bp | **+1.26** | 47.3% | +0.63bp | **81** | 03:30 (t=+2.50) |

## The whole-day momentum profile (30-min windows, prev-close anchor)

**This is the test that decides it.** If momentum is concentrated in his
window, that is a finding. If it rises steadily all afternoon, the anomaly
is real and he is describing it rather than adding to it.

| window | n | spread | t | hit |
|---|---|---|---|---|
| 00:00-00:30 | 2,641 | -0.30bp | -0.78 | 46.5% |
| 00:30-01:00 | 2,963 | -1.11bp | -2.73 | 44.7% |
| 01:00-01:30 | 2,963 | +0.63bp | +1.68 | 46.2% |
| 01:30-02:00 | 2,963 | -0.83bp | -2.11 | 44.2% |
| 02:00-02:30 | 2,963 | -0.66bp | -1.48 | 46.0% |
| 02:30-03:00 | 2,963 | -1.14bp | -2.58 | 45.9% |
| 03:00-03:30 | 2,963 | +0.45bp | +0.68 | 49.4% |
| 03:30-04:00 | 2,963 | +0.66bp | +1.18 | 46.9% |
| 04:00-04:30 | 2,963 | -0.42bp | -0.73 | 47.5% |
| 04:30-05:00 | 2,963 | -0.23bp | -0.46 | 47.8% |
| 05:00-05:30 | 2,963 | -0.44bp | -0.87 | 46.2% |
| 05:30-06:00 | 2,963 | +0.20bp | +0.44 | 47.7% |
| 06:00-06:30 | 2,969 | -1.24bp | -2.59 | 45.3% |
| 06:30-07:00 | 2,969 | -2.20bp | -5.00 | 43.1% |
| 07:00-07:30 | 2,969 | -0.94bp | -1.86 | 46.9% |
| 07:30-08:00 | 2,969 | -0.80bp | -1.63 | 45.7% |
| 08:00-08:30 | 2,969 | +0.05bp | +0.07 | 48.9% |
| 08:30-09:00 | 2,969 | -1.27bp | -1.99 | 46.0% |
| 09:00-09:30 | 2,969 | +0.95bp | +1.30 | 48.3% |
| 09:30-10:00 | 2,969 | -3.89bp | -2.63 | 48.7% |
| 10:00-10:30 | 2,969 | -1.19bp | -1.02 | 47.8% |
| 10:30-11:00 | 2,969 | -2.04bp | -1.95 | 49.0% |
| 11:00-11:30 | 2,969 | +0.28bp | +0.29 | 49.4% |
| 11:30-12:00 | 2,969 | +1.22bp | +1.36 | 48.2% |
| 12:00-12:30 | 2,969 | +0.34bp | +0.43 | 48.6% |
| 12:30-13:00 | 2,969 | -0.40bp | -0.51 | 48.0% |
| 13:00-13:30 | 2,969 | -1.61bp | -2.21 | 46.0% |
| 13:30-14:00 | 2,969 | +0.57bp | +0.74 | 48.9% |
| 14:00-14:30 | 2,969 | -0.75bp | -0.92 | 47.6% |
| 14:30-15:00 | 2,969 | -0.54bp | -0.62 | 47.6% |
| 15:00-15:30 **<- his** | 2,969 | +0.33bp | +0.38 | 47.9% |
| 15:30-16:00 **<- his** | 2,969 | +1.95bp | +1.68 | 47.3% |
