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
Work ONLY on branch arena/a41fd997-trading-bot (or the Arena session
branch bound to your chat, if the platform binds you to one — never
push to any other branch).

Fetch explicitly first:
  git fetch origin refs/heads/arena/a41fd997-trading-bot:refs/remotes/origin/arena/a41fd997-trading-bot
  git rev-parse origin/arena/a41fd997-trading-bot
Sync your index to that ref WITHOUT `reset --hard` (verify equality or
fast-forward only). Read code via `git show <ref>:<path>` when auditing.

Never use `git add -A`; stage by explicit path. Commit and push EVERY
turn that changes files. Never modify the protected time-contract file
(information_time.py); verify its SHA-256 and size only (see
HANDOFF_CURRENT.md). Do not install packages or run anything needing
EUR/USD market data unless explicitly asked; a throwaway venv lives
outside the repo.
```
