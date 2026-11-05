# Transcript acquisition manifest — incomplete round

Retrieval date: 2026-11-05. Branch: arena/5b6d2bd5-trading-bot.
No interpretation, engine/code changes, market data changes, or May 2025 access.

## Visibility safety check

`gh repo view --json visibility` failed: `Unknown JSON field: "visibility"` (installed gh lists isPrivate instead).
`gh repo view --json isPrivate,nameWithOwner` returned `{"isPrivate":false,"nameWithOwner":"jfjdjdieifne/TRADING-BOT"}`.
Repository is PUBLIC. This batch contains metadata and failure logs only, no transcripts, frames, audio or video.

## Scope limitation

The requested source-of-URL files SOURCE_CATALOG.md and sources_index.jsonl contain only one individual primary video: P04 / Episode 3. Episode 12, Dealing Ranges and Episode 6 were named in the task/conversation but have no individual URL record in those catalog files. Their retrieval was NOT attempted in this round, to respect the requested catalog-only URL constraint. No catalog edits or guessed URLs.
P03 is a playlist page, not a retrieved list of individual video records. No playlist expansion performed.

| Requested video | Status | Real transcript parts seen / expected | Transcript files stored | Caption type | Frames |
|---|---|---|---|---|---|
| Episode 12 | NOT ATTEMPTED — catalog URL missing | 0 / unknown | 0 | unknown | 0 |
| Dealing Ranges | NOT ATTEMPTED — catalog URL missing | 0 / unknown | 0 | unknown | 0 |
| Episode 6 | NOT ATTEMPTED — catalog URL missing | 0 / unknown | 0 | unknown | 0 |
| Episode 3 / P04 | PARTIAL access; complete acquisition FAILED | 1 / 6 in first response | 0 | unknown | 0 |

## P04 attempts

1. Installed yt-dlp 2026.10.26 into /tmp/ict_corpus/tools. Not a repository dependency change.
2. Ran `python3 -m yt_dlp --skip-download --write-subs --write-auto-subs --sub-langs en --sub-format vtt` against the exact P04 URL, with output under /tmp/ict_corpus/P04. Exit 1. Exact output is embedded unmodified in P04/meta.json. Both webpage and initial API requests each exhausted yt-dlp's three internal retries: `TLS/SSL connection has been closed (EOF) (_ssl.c:992)`.
3. fetch_page chunk 0 returned a real transcript prefix and metadata, totalChunks=6, without line timestamps. The text was seen in tool output but NOT saved as a raw part; no hash for that content is claimed.
4. fetch_page chunk 1: three calls using the exact same URL all returned chunkIndex=0 / totalChunks=1, YouTube UI, not transcript. Exact displayed error:

> Error 401 (Bad Request)!!1
>
> 401. That’s an error.
>
> The server cannot process the request because it is malformed. It should not be retried. That’s all we know.

5. Alternative same-video URL with `&t=0s`, chunk 1: same UI / Error 401. No transcript.
6. Stopped before chunks 2–5; they were NOT attempted. No fabricated completion or timestamps. The full per-part retry ladder was NOT completed.

## Media / ASR

No audio/video download attempted after source access failed. No claim that captions do not exist. No Whisper installation or transcription. ffmpeg lookup returned no executable. No scene detection or frames, hence no frame INDEX. No transcript_plain.txt and no rolling-caption processing. No proxies, cookies, login or access-control circumvention.
/tmp/ict_corpus contains tools and diagnostic logs, NOT a complete corpus. No full transcript persisted anywhere by this round.

## Stored files

| File | Bytes | SHA-256 |
|---|---:|---|
| P04/meta.json | 4635 | `a54f75678da3ad89775000e45a7e5cfa5d35cd803c798f30aede1c7d43f6fb3c` |

MANIFEST.md intentionally has no self-hash. Zero transcript/media bytes in repository. Status PARTIAL means only partial content was observed, NOT that a usable timestamped transcript was saved. This round did not achieve the complete-transcript goal.
