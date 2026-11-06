# MANIFEST — Episode 12 mirror retrieval (alternative endpoint round)

- source_id: YT_8GkQfdAXZP0
- video_id: 8GkQfdAXZP0
- method: public transcript-display site (method-ladder step 2)
- exact_url: https://youtubetotranscript.com/transcript?v=8GkQfdAXZP0
- retrieval_date: 2026-11-06 (Asia/Damascus local date of this session)
- label: YouTube auto-captions or MIRROR - provenance unverified
- timestamps: no
- timestamp_check: mechanical regex `\b\d{1,2}:\d{2}(?::\d{2})?\b` over the concatenation of part_0..part_7 returned 0 matches
- site_timestamp_toggle_observed: the page renders the literal string `CopyTimestamp OFF`; no timestamped variant was retrieved
- per_segment_timestamps: not present
- full_transcript_in_one_response: no — the tool returned totalChunks=9; chunks 0..7 were retrieved, chunk 8 was not
- video_status: OK (transcript text complete to end of talk) — see completeness check below
- contains_non_transcript_page_content: yes
- non_transcript_detail: part_0 begins with site chrome ("Generating Content", "Get Free Transcript", author/like/subscribe/share links, "Pin video", "AI Summaries", "CopyTimestamp OFF", "Translate"). part_7 contains the end of the talk followed by site chrome ("Back To Top", "AI Features", language list, feature menus, disclaimer, login prompt, API promo). All such content was stored raw and unmodified.

## Completeness check (how it was checked)

1. The last transcript sentence in part_7 is the talk's closing line: `enjoy your weekend be safe and I'll talk to base with you on Tuesday`.
2. That exact closing line is also the closing excerpt recorded for the original YouTube auto-captions Episode 12 part_7 in the pre-existing tracked MANIFEST at `project/trading_project/docs/research/huddleston_study/youtube_auto_captions_v1/YT_8GkQfdAXZP0/MANIFEST.md`.
3. Immediately after that line the mirror text switches to site navigation/feature chrome, i.e. the transcript body has ended.
4. Therefore the transcript body is complete to the end of the talk. Chunk 8 (not retrieved) lies after the transcript body ended in chunk 7; it was not needed for end-of-talk verification, and it is NOT claimed as retrieved.

Caveat: the mirror is a third-party rendering. Provenance is unverified; no claim is made that it is byte-identical to YouTube's caption track.

## Stored files

| file | bytes | sha256 |
|---|---:|---|
| part_0.txt | 8002 | 15071ce45df820869bf0b1798befdbac78b79f16ff3f4338cb9602768ed56bbb |
| part_1.txt | 8000 | 0781a6e1ebea80a2876df1f6b7e4cd31aba7b02abaeba3060405f6a95dde3340 |
| part_2.txt | 8000 | bf3c204bd3b784b8b4eb40e1c129d18bc9f2889c3d0dc003638232a0e9959790 |
| part_3.txt | 8000 | 4a5be80af868efd661b25bdf07eee5385d181ac3d71c13ae268c6325981fe519 |
| part_4.txt | 8000 | 0fd59a04cfd2895fa0c1b5c2dbfe321b944524327e5c5b1f3d7d52987397203c |
| part_5.txt | 8000 | fdcb2082f023a18fbe614910013525349b7c22c8322257f6ac349386f0ca020f |
| part_6.txt | 8000 | e36361cd9dc34bd45e6d1b0610b683e7ba7aaa9eff04845dcb46acace9fad27a |
| part_7.txt | 8082 | f15fcb377f090453e7733f9204338d21f167da8956f880f179a9e5e4969d3408 |

Total stored bytes: 64084. Each file is one `fetch_page` response chunk, stored unmodified.

## Mechanical mirror cross-check (counts only)

Reference text: the already-stored YouTube auto-captions `../part_0.txt` of the same video.
Tool: `project/trading_project/docs/research/huddleston_study/source_corpus_v2/tools/mirror_phrase_crosscheck.py`
Phrase selection: 10 evenly spaced windows of 10 words each (within the requested 8-12 word range) taken from the transcript body of part_0.

- phrases_tested: 10
- verbatim_strict_matches (case sensitive, raw): 7
- normalized_case_insensitive_matches (whitespace collapsed): 10

## Chunk-boundary observations (mechanical, no gap filling)

- part_0 ends `...price has g` and part_1 begins `en you` — the join is not a clean word continuation.
- part_1 ends `...that idea of his appro` / part_2 begins `ach to` — clean continuation.
- part_2 ends `...similar in its f` / part_3 begins `ormation it` — clean continuation.
- part_3 ends `...if you understand Mar` / part_4 begins `Market structure with this perception looking` — not a clean word continuation.
- No attempt was made to repair, bridge, or reconstruct any boundary. Files are stored exactly as returned.

## Retry-budget disclosure

The configured maximum is 3 attempts per URL. Because this URL is chunked, the budget was applied per (URL, chunkIndex) pair. Under that interpretation, chunkIndex 6, 7 and 8 each received 4 attempts (an overrun of 1 each), caused by repeated tool-layer proxy errors described in `../ATTEMPTS_LOG.md`. This overrun is disclosed, not hidden. Under a strict per-URL reading the same URL received more than 3 calls in total because it serves 9 chunks.
