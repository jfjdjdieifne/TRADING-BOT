# Persistence recovery inventory — 2026-11-06

repo: jfjdjdieifne/TRADING-BOT
branch: arena/e6974afe-trading-bot
visibility_observed: public
user_override: push authorized regardless of public/private visibility
base_head_before_recovery_commit: 4438ac40ec770d3c96dfc0fc44bd8e8e1949b6fb

## Surviving outside-git project artifacts found this round

| outside_path | bytes | disposition | in_repo_path |
|---|---:|---|---|
| /tmp/arena-workspace/coding.patch | 121427 | pushed as small text artifact | project/trading_project/docs/research/huddleston_study/source_corpus_v2/session_artifacts/coding.patch |
| /tmp/arena-workspace/coding.diff | 121427 | pushed as small text artifact | project/trading_project/docs/research/huddleston_study/source_corpus_v2/session_artifacts/coding.diff |
| /tmp/arena-workspace/coding-numstat.txt | 1867 | pushed as small text artifact | project/trading_project/docs/research/huddleston_study/source_corpus_v2/session_artifacts/coding-numstat.txt |
| /tmp/persistence_recovery/YT_8GkQfdAXZP0/part_0.txt | 8000 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_8GkQfdAXZP0/part_0.txt |
| /tmp/persistence_recovery/YT_Bkt8B3kLATQ/part_0.txt | 8000 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_Bkt8B3kLATQ/part_0.txt |
| /tmp/persistence_recovery/YT_nQfHZ2DEJ8c/part_0.txt | 8000 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_nQfHZ2DEJ8c/part_0.txt |
| /tmp/persistence_recovery/YT_PIYh0CxoY9c/part_0.txt | 8022 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_PIYh0CxoY9c/part_0.txt |
| /tmp/persistence_recovery/YT_FgacYSN9QEo/part_0.txt | 8022 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_FgacYSN9QEo/part_0.txt |
| /tmp/persistence_recovery/YT_HhgWGduQZQY/part_0.txt | 8022 | temporary re-fetch source; copy pushed | project/trading_project/docs/research/huddleston_study/source_corpus_v2/transcripts_full/YT_HhgWGduQZQY/part_0.txt |

All pushed artifacts are text and under 1 MB each. No csv/gz data, model, audio, or video file was pushed.

## Wiped/missing outside-git directories

The following project-relevant temporary directories were verified MISSING this round. They were destroyed by the rollback/wipe and no surviving copy was found by filesystem search. They cannot be pushed because their bytes no longer exist in the workspace.

| missing_path | known_lost_content | size_information | justification_not_pushed |
|---|---|---|---|
| /tmp/ict_corpus | 12 stored transcript part files; meta.json files; attempts_log.json files; failed_attempts bodies; DEALING_RANGES_NO_SOURCE/resolution_log.json | stored parts total 92455 bytes; resolution_log.json known 7571 bytes; other log/meta sizes not recoverable | destroyed; only re-fetched part_0 files were recoverable; no reconstruction |
| /tmp/rerun_out | temporary rerun outputs | unknown | destroyed; committed audit/rerun artifacts remain in git where previously tracked |
| /tmp/fidelity_audit | temporary fidelity-audit outputs | unknown | destroyed; committed FIDELITY_AUDIT.md remains in git |
| /tmp/ict-asr | temporary ASR-related workspace | unknown | destroyed; no local ASR was used for the recovered captions |
| /tmp/forex-data | temporary forex data workspace | unknown | destroyed; data files are also excluded by push policy |
| /tmp/ict-phase1 | temporary phase-1 workspace | unknown | destroyed; no surviving copy found |
| /tmp/ict-url-resolution | temporary URL-resolution workspace | unknown | destroyed; no surviving copy found |

## Known lost stored transcript parts from tracked manifests

These are the 12 part files that existed in /tmp/ict_corpus before the wipe. Only six part_0 files were re-fetched this round; Episode 12 parts 2-7 could not be re-fetched because the watch page now collapses higher chunk requests to non-transcript UI.

| source_id | part | bytes | sha256_recorded_before_wipe | recovered_this_round |
|---|---:|---:|---|---|
| YT_8GkQfdAXZP0 | 0 | 8000 | d1ea43bfc52cbe2429f45515161e58fb74521b7788fb2b0d1030283615098282 | yes, hash changed |
| YT_8GkQfdAXZP0 | 2 | 8000 | 6595c0514c5ca88a2d903aa3515134ddb22fde6e6552669d233f3a69ba2f021e | no |
| YT_8GkQfdAXZP0 | 3 | 8000 | 3ec0ce26cf6900f8038ef93bd4677c58d03437edf55a877afa1d7cdd31b95f5e | no |
| YT_8GkQfdAXZP0 | 4 | 8000 | 63bb85e6b05951129615cf8f4ef783aa4c49c733903b25712018c2909bd15f8e | no |
| YT_8GkQfdAXZP0 | 5 | 8000 | b36f4bdca26a40da285ca913bfdc90e7d7ffce5c899526de603e28aa654a42be | no |
| YT_8GkQfdAXZP0 | 6 | 8000 | bb8313f5176e4e90b8babc4f00140573f8748614f4591ca39e8120c711c54279 | no |
| YT_8GkQfdAXZP0 | 7 | 4389 | c769f65d652f3bf5dee8cb28bfbcf42dc5825941b6772aa589074f3270289933 | no |
| YT_Bkt8B3kLATQ | 0 | 8000 | 30ec11aa8ac612c982c5fc4134ac5c968f4bace0eeda28024a910ffe6443b0ba | yes, hash matches |
| YT_nQfHZ2DEJ8c | 0 | 8000 | 910bb80a74b447e9ec0a9ec074c4bf9d2c99f49a6d40a4139c50c3fdeedd0e91 | yes, hash changed |
| YT_PIYh0CxoY9c | 0 | 8022 | 11155bbcf496442e8a670f81e379983f902fafd9b915b98e172693257cea1ce8 | yes, hash changed |
| YT_FgacYSN9QEo | 0 | 8022 | 004c103db20efc0903ac0349e46a3c7b7ad475205e1702a138b195197153fc1f | yes, hash changed |
| YT_HhgWGduQZQY | 0 | 8022 | faee2c2c0728fa8f75b05bb49cf97b812deccc01b2ebf915dbb9b08258c445cf | yes, hash changed |

## Not executed

- Step 4 read-only Episode 12 analysis prompt was not received, so it was not executed.
- No code or existing tracked file was modified by this recovery.
- No git add -A and no git reset --hard were used in this persistence round.
