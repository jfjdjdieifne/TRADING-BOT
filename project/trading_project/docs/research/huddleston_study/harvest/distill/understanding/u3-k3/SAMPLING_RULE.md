# Deterministic Corpus Sampling Rule (Written Before Reading)

To avoid K2's alphabetical-first bias (which heavily over-sampled `2016-ICT-Private-Mentorship-Core-Content-Month-01`), session `u3-k3` uses the following deterministic, era-stratified sampling rule fixed in `tools/sample_windows.py` prior to reading any windows:

## 1. Corpus Stratification into Five Chronological/Series Eras
All 490 transcripts in `newsqlguru/ict-index@e8c40a8dae5ea6689926f28c7184ce3e2fb85b9c` are partitioned by top-level subfolder under `transcriptions/` into five eras:
1. **`E1_EARLY_SERIES`** (86 files): `ICT-Forex-*`, `ICT-Market-Maker-Forex-Series`, `ICT-Mastering-High-Probability-Scalping-Volumes-1-3`, `ICT-Micro-Market-Structure-&-Time-&-Price-Concepts-Series`, `ICT-Trade-Executions`, `If-I-Could-Go-Back-&-Tell-Myself-What-I-Know-Now`, `Real-Money-*`.
2. **`E2_2016`** (40 files): `2016-ICT-Private-Mentorship-Core-Content-Month-01` through `Month-04`.
3. **`E3_2017`** (80 files): `2017-ICT-Private-Mentorship-Core-Content-Month-05` through `Month-12`.
4. **`E4_2019_2022`** (115 files): `ICT-Charter-Content`, `ICT-OTE-Pattern-Recognition-Series`, `ICT-Pattern-Recognition-Optimal-Trade-Entry`, `2022-ICT-Mentorship`, `Ends-Series`, `Emini-Market-Reviews`.
5. **`E5_2023_2024`** (159 files): `2023-ICT-Mentorship`, `2023-Forex-Reviews`, `Live-Streams`.

## 2. Candidate Hit Identification and Non-Overlapping Windowing
- For each concept in `TODO`, we first search the exact phrase from `kept_concepts.tsv` (word-boundary matched, case-insensitive).
- Around each hit at word index `wi`, a window of **`±100` words** (`[max(0, wi - 100), min(len(words), wi + 101)]`, up to 201 words) is formed.
- Hits within the same transcript are de-duplicated so any two candidate windows in the same transcript are separated by at least 200 words (zero overlap).
- Each candidate window is scored by local marker density (`3 * definition_markers + 2 * comparative_markers + 2 * rejection_markers`), with deterministic tie-breaking via `SHA-256(f"{concept}:{rel_path}:{wi}")`.
- For the 16 concepts that had K2 skeleton windows (`u3-k2/concepts/read_log.jsonl`), K2's starting transcript hits are included first (re-extracted at `±100` words and re-read in full this session) so K3 genuinely deepens K2's starting point rather than discarding it.

## 3. Round-Robin Selection Across Eras and Subfolders
- **Pass 1 (Strict 1-window-per-transcript)**: Candidate windows (rank 0 within each unused transcript) are bucketed by era (`E1_EARLY_SERIES`, `E2_2016`, `E3_2017`, `E4_2019_2022`, `E5_2023_2024`). Within each era, candidates are ordered by subfolder diversity first, then `(marker_score DESC, tie_sha256 DESC)`. We cycle round-robin across `E1 -> E2 -> E3 -> E4 -> E5` until 15 windows from 15 distinct transcripts are chosen (or all exact hits are exhausted).
- **Pass 2 (Second non-overlapping hit in a transcript, if `<15` distinct transcripts exist)**: Same round-robin order for rank-1 hits separated by `>=200` words.
- **Pass 3 (Direct morphological/ASR punctuation variants, ONLY if exact `kept_concepts.tsv` phrase has `<15` total hits)**:
  - If the literal phrase in `kept_concepts.tsv` has `<15` hits in the entire corpus (specifically `non_farm_payroll` with 1 unhyphenated hit `"non farm payroll"`, and `long_term_high` with 10 unhyphenated singular hits `"long term high"` across 8 files), the concept is explicitly flagged **`THIN` on the literal `kept_concepts.tsv` phrase**, and we additionally sample the remaining windows needed to reach 15 from the hyphenated/plural ASR forms (`"non-farm payroll"`, `"nonfarm payroll"`, `"long-term high"`, `"long term highs"`, `"long-term highs"`) using the same round-robin rule, logging `match_type: "asr_hyphen_or_plural_variant"`.

## 4. Full-Window Reading and Logging
- Every selected `±100`-word window is printed in full to stdout and read during this session (`read_mode: "full_window_pm100"`), and logged to `windows.jsonl` and `read_log.jsonl` with `window_id`, `concept`, `repo`, `path`, `era`, `hit_word_index`, `window_words` (`[lo, hi]`), `window_word_count`, and `file_sha256`.
