# corrections.md — errors made and fixed inside this round, plus findings about the base files

## My own errors during the round (all caught by the verifier, none reached a claim file)
1. **Window→file misattribution (3 claims rejected).** I recorded W017 ("75 of that range ...") against
   `Episode-40` and "If no fair value Gap allows for a four-point stop loss" against the wrong file. The verifier
   rejected both as *quote not found*; grep showed the true homes are
   `2023-...-Deep-Dive-Into-Institutional-Order-Flow-002.json` and `Ends-Series-Part-4-of-4`. Re-filed with correct paths.
2. **Word-level misquote.** "we want to have a more meaningful displacement" — the file says "i want". Rejected,
   re-filed as R2QG-0003.
3. **Truncated start of a quote.** "we're selecting a fair value Gap ..." — the file has "you're selecting". Rejected,
   re-filed as R2QE-0002.
4. **ASR duplicate kept.** "all this is is an income approach" — kept verbatim rather than smoothed (R2QC-0005).
5. **Tool bug.** `r2_claims.py` first resolved paths as `repo + "::" + path` because my batch builder reused the
   `repo::path` key format. Fixed by splitting on `::`; the 16 rejections in batch 1 were all this bug, not content.

## Findings about the base files (not edited — this file is the record)
- `distill/claims.jsonl` CLM-0071/CLM-0072 (order block definition/validation) and CLM-0061..0063 (stop placement)
  overlap in *substance* with R2QA-0002 and R2QH-0001; they are not duplicates: round 1 quoted the library's
  restatement, round 2 quotes the lecture text itself. Both kept, cross-referenced in `answers.md`.
- Round-1 `OWNER_QUESTIONS.md` Q1 (stop buffer) is now **partly** answerable: the 40-day trailing low (R2QA-0001) and
  the two-stage OB stop (R2QA-0002) are stated rules, but no pips/ATR buffer exists in any window read. Q1 stays open
  in its numeric form only.
- Round-1 Q10 (limit vs market) is **answered as a free choice** (R2QB-0001/0002); it should be removed from the
  blocking list and replaced by the narrower question "which does he default to intraday?".
- Round-1 Q4 (killzone set) is now **worse**, not better: a third definition (07:00–10:00 NY killzone) and a fourth
  (09:30–11:30 / 13:30–15:30 operating sessions) were found. See CF-R2-02.
- `verify_claims.py` CHECK 2 fires on almost every round-2 claim (48/50) because my statements are written in
  normal English while the transcripts are unpunctuated ASR. The warnings are framing words ("the", "a", "he",
  "stop" vs "stops"), not new factual terms; full list in `verify_r2_final.md`.
