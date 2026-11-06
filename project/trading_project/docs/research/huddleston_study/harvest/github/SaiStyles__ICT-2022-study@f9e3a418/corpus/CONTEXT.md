# corpus - what exists and what has been extracted

One job: be the honest answer to "which episodes are done".

No video files live here. The playlist is the source; `_index.md` is the state surface.

## Inputs
- Reference (every run): the playlist, fetched live by `../extraction/build_index.py`

## Process
1. `_index.md` is **generated**. Regenerate with `python extraction/build_index.py`.
2. **Nothing in it is hand-edited any more.** Every column is derived by scanning what exists on disk, so the file cannot drift from reality and nothing can be lost by regenerating it.

## The two columns, and why there are two

| column | channel | meaning |
|---|---|---|
| `done` | video | `[x]` when all of an episode's 240s windows exist on disk. **Deferred** - DECISIONS.md section 19 |
| `tx` | transcript | chunks extracted / chunks total. **This is the live channel.** `none` = no caption track exists |

**Read the column for the channel you are running.** After the switch to transcripts, `done` still described video only - so episodes 2-5 showed `[ ]` while their transcripts were fully extracted. A session trusting that column would have re-run finished work and burnt a day of quota.

## Why derived, not ticked

`[x]` used to be hand-set and preserved across regenerations by a regex keyed to column positions. Adding the `tx` column shifted those positions, preservation silently failed, and episode 1's completion was destroyed by a change that only meant to add a column.

Derived state cannot be lost that way, and it matches the rule the workspace already runs on: **the filesystem is the state.** If you want to know what is done, the answer is what exists in what exists on disk - and now the index just reports that rather than remembering it separately.

## Outputs
- `_index.md` - 41 episodes, 24.5 hours; 433 video windows, 128 transcript chunks

## Human check
Before starting a session, scan the `tx` column. That is the anti-repetition mechanism for the live channel: a chunk already on disk is skipped by the extractor anyway, but the column is how *you* see where to resume.

Do not trust memory for this, and do not trust a chat transcript. No session holds the corpus state - the file does.
