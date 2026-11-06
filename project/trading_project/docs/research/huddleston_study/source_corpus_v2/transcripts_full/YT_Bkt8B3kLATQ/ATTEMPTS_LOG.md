# Attempts log + status — Episode 6 (Bkt8B3kLATQ), alternative-endpoint round, 2026-11-06

- source_id: YT_Bkt8B3kLATQ
- video_id: Bkt8B3kLATQ (not guessed; taken from the tracked Episode 6 MANIFEST)
- label: YouTube auto-captions or MIRROR - provenance unverified
- video_status this round: FAILED — no new response body was obtained, so nothing was stored
- timestamps: not applicable (no payload retrieved)
- bytes stored this round: 0

## Attempts made

| # | intended exact URL | attempts | exact observed result |
|---:|---|---:|---|
| 1 | `https://www.youtube.com/api/timedtext?v=Bkt8B3kLATQ&lang=en&kind=asr&fmt=vtt` | 1 | tool-layer proxy error `SignatureDoesNotMatch` (see below); target host never reached |
| 2 | `https://inv.nadeko.net/api/v1/captions/Bkt8B3kLATQ?lang=en` | 1 | tool-layer proxy error `SignatureDoesNotMatch`; target host never reached |
| 3 | `https://youtubetotranscript.com/transcript?v=Bkt8B3kLATQ` (chunkIndex 0) | 3 | tool-layer proxy error `SignatureDoesNotMatch` on all 3 attempts; retry budget for this URL exhausted, stopped |

Exact error body returned by the retrieval layer on every attempt above:

```
<Code>SignatureDoesNotMatch</Code>
<Message>The request signature we calculated does not match the signature you provided. Check your key and signing method.</Message>
<EC>0002-00000040</EC>
```

Host returned by the tool: `routify-file-proxy-sg.oss-ap-southeast-1.aliyuncs.com`.
This is a retrieval-layer failure, not a response from YouTube / Invidious / youtubetotranscript.com.
Because no target-site response body was received, there is nothing to store for this video, and no
transcript, mirror text, or timestamp claim is made.

Ladder step 3 (previous watch-page approach) was NOT EXECUTED for Episode 6 this round.

## Read-only provenance answer requested by the user

Question: the exact playlist URL and exact title string from which video ID Bkt8B3kLATQ was obtained.

Surviving evidence — tracked file
`project/trading_project/docs/research/huddleston_study/youtube_auto_captions_v1/YT_Bkt8B3kLATQ/MANIFEST.md`:

- line 5, exact title string: `2022 ICT Mentorship Episode 6`
- line 7, exact recorded line: `- url_resolution: user-authorized official playlist extraction; 2022 ICT Mentorship playlist PLVgHx4Z63paYiFGQ56PjTF1PGePL3r69s, index 6`

Determination:

- Playlist ID: `PLVgHx4Z63paYiFGQ56PjTF1PGePL3r69s` — recorded.
- Playlist position: index 6 — recorded.
- Exact title string of the video entry: `2022 ICT Mentorship Episode 6` — recorded.
- Exact playlist URL **string** as originally fetched: **cannot be determined** from surviving records.
  The MANIFEST records the playlist ID, not a full URL. A repository-wide grep for `playlist?list=`
  across the tracked caption manifests returned only one hit, in the unrelated
  `DEALING_RANGES_NO_SOURCE/MANIFEST.md` (the disclosed invalid probe
  `https://www.youtube.com/playlist?list=PLVgHx4Z63paZnKv9Y9Y9Y9Y9Y9Y9Y9Y9Y9Y`).
  The original `attempts_log.json` that would have carried the literal request URL was destroyed in
  the earlier `/tmp` wipe. A URL can be constructed from the recorded ID, but a constructed URL is not
  evidence of the original request string, so it is not asserted here.
