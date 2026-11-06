# HANDOFF_CURRENT

Strictly factual handoff. Supersedes nothing: the old `real hand off`
file is kept untouched.

## Branch / head

- Arena session branch: `arena/e6974afe-trading-bot` (this session is
  bound to it; pushes to any other branch are not permitted from here).
- Upstream source branch: `arena/a41fd997-trading-bot`.
- Last known good / base of this work:
  `e06e22c9959a9e40e66f6b0053093ed09f424f91`
  ("Fix intrabar ambiguity test fixture; mark reports 101-103 as
  unreproduced"). At the time of writing, HEAD and
  `origin/arena/a41fd997-trading-bot` were both exactly this commit and
  the working tree was clean (index already in sync; no reset used).
- The commit that adds this file is a direct child of `e06e22c` on
  `arena/e6974afe-trading-bot`. `origin/arena/a41fd997-trading-bot`
  remains at `e06e22c` unless a maintainer fast-forwards it (the new
  commit is a fast-forward candidate).

## Branch history

`2b4d23e` -> `2befb6c` -> `e06e22c` (`arena/a41fd997-trading-bot`)
-> `43a1b56` (`arena/e6974afe-trading-bot`).

- `2b4d23e` — forex-intraday-loop-v1: initial causally-evaluated
  baseline (report 99); EURUSD 5m bid/ask, dev/eval split, V1 vs B0.
- `2befb6c` — unify Forex branch with Builder fixes; intended-direction
  gate fix; causal `next_open` exits.
- `e06e22c` — fix intrabar ambiguity test fixture; mark reports 101–103
  as unreproduced.
- `43a1b56` (`43a1b5630be893b8fd11d1f641530b5380352010`) — docs and test
  hardening after the independent audit; this handoff file added.

`arena/a41fd997-trading-bot` stayed at `e06e22c` because the session
could not push to it (sessions are bound to their own branch).
`43a1b56` is a direct child of `e06e22c` on
`arena/e6974afe-trading-bot`, so it is a fast-forward candidate for
`arena/a41fd997-trading-bot` if a maintainer chooses to advance it.

## What was verified, and how

Independent read-only audit round (at `e06e22c`, all code read via
`git show origin/arena/a41fd997-trading-bot:<path>`):

- Explicit fetch + `git rev-parse` matched the expected commit.
- Full diffs reviewed: runner `2b4d23e -> e06e22c`; test fixture
  `2befb6c -> e06e22c`.
- Reachability proven by stdlib AST parsing of BOTH committed snapshots
  (`2b4d23e` and `e06e22c`): `gate_v1`/`gate_b0` nested in `run_phase`,
  the `while` loop a direct child of `run_phase`, and no statement after
  any terminal `return/raise/break/continue` anywhere in the file.
- Causal `next_open` exits confirmed by reading: fill = first 5m row
  strictly after the event's as-of time; long entry/short exit at ask,
  short entry/long exit at bid; `bar_close` only via the explicit,
  NON-CAUSAL-labeled `--fill-mode bar_close`.
- Fixture fix confirmed by a pure-Python arithmetic replication: the
  old two-batch extremes give ambiguity=False (old test would fail);
  the single-batch extremes give True with unchanged assertions.

This modification round (throwaway venv OUTSIDE the repo at
`/home/user/.venv`: pandas==2.2.3, numpy==1.26.4, tzdata, pytest==8.3.5):

- `python test_forex_direction_gate_fix.py` (plain runner):
  **10/10 passed, 0 skipped, 0 failed — exit code 0** (synthetic data
  only; includes the real `run_phase` gate path driven with fakes).
- Full suite `python -m pytest` from `project/trading_project`
  (its configured `testpaths=["tests"]`):
  **1833 passed, 0 failed, 24 warnings — exit code 0** (~5 min).
- Changes this round: summary `limitations` text now reflects the
  actual `fill_mode`; `same_bar_ambiguity` groups by `TASK_SCALE`
  instead of a hardcoded "1h" (identical behavior, TASK_SCALE=="1h");
  negative-control test (two different 1h batches -> not ambiguous);
  test locking that `extract_context` yields direction ONLY from
  I-primary; README next to the pre-fix artifacts; this file.

## What is NOT verified

- **No EUR/USD 5m data exists in this workspace; no real-market run was
  performed.** Dev/eval phases were never rerun on real data here.
- **Reports 101–103 are unreproduced**, and the **102-vs-103 trade-count
  discrepancy remains unresolved** (the reports carry the 2026-11-05
  verification appendix saying exactly this).
- The committed `run_artifacts/forex_v1/` summaries/cases were produced
  by the **pre-fix non-causal close-based code** (no `fill_mode` key);
  they are NOT results of the current causal mode (see the README added
  next to them).
- **Ambiguity detection is broader than `trade_plan.py` semantics**:
  `same_bar_ambiguity` censors on intrabar ask/bid TOUCHES of both
  levels within one task bar, while the plan layer resolves
  entry/invalidation by SP-03 task-scale CLOSE bindings and the
  objective by completed-leg knowability. The overlay is conservative
  (only censors, never flips to a win) but is not the same event model.
- **Label-convention assumption**: 5m rows are assumed to be labeled by
  bar START (the resample+shift logic depends on it). Not verified
  against the external CSV dataset.
- Latent mapping fragility (now locked by a test, not reconciled):
  `_intended_direction` treats I-scenario as continuation while
  `create_plan` treats any pid != I-primary as reversal; today this is
  neutralized because `extract_context` reads direction only from
  I-primary (I-scenario-only records yield "none" and the gate holds).

## run_phase indentation bug — scope note

The `run_phase` indentation bug existed only in the builder branch
(commit `5eee9692`) and never in this branch: AST verification of this
branch's committed snapshots (`2b4d23e` and `e06e22c`) shows the gate
and the loop were reachable in both. (`5eee9692` is not part of this
branch's history and was not fetched here; the builder-branch attribution
is per the builder branch record.)

## Protected file rule

`project/trading_project/src/trading_system/research/information_time.py`
is the protected time-contract file: **never modify it; verify hash/size
only.**

- SHA-256: `72b03ca6d2333080e0df6dc18b1928147e877b41175f132c7bf08eb4e4d74ace`
- Size: `12216` bytes

## First-message template for new chats

```text
Sessions on Arena are bound to their OWN branch (shown by
`git branch --show-current`); you cannot push to any other branch.

Start by syncing to the LAST KNOWN GOOD COMMIT HASH provided by the
user — pin by hash, never by branch name:
  git fetch origin <last-known-good-commit-hash>
  git rev-parse HEAD    # must equal that hash; sync the working
                        # tree/index WITHOUT `reset --hard` (verify
                        # equality or fast-forward only); if it cannot
                        # be matched, stop and report.

Work, then commit and push to YOUR OWN session branch every turn that
changes files. Never use `git add -A`; stage by explicit path only.

Never modify the protected time-contract file (information_time.py);
verify its SHA-256 and size only (see the Protected file rule section).

END EVERY REPLY by printing:
  git branch --show-current
  git rev-parse HEAD
```
