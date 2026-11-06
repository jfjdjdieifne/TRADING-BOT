# Round report — caption retrieval via alternative endpoints (2026-11-06)

Branch: `arena/e6974afe-trading-bot`
Start HEAD (verified equal to `origin/arena/e6974afe-trading-bot`): `cbd90fe4c5346fd64f9e502f24f699e754911698`
No `git reset` of any kind was needed or performed this round. No existing tracked file or code file
was modified. Every new file was committed by explicit path and pushed immediately, then verified
against the remote by SHA-256.

## Per-video outcome

| order | source_id | status | method that worked | timestamps | bytes stored | detail |
|---:|---|---|---|---:|---:|---|
| 1 | YT_8GkQfdAXZP0 (Episode 12) | OK — transcript body complete to end of talk | public transcript-display site `youtubetotranscript.com/transcript?v=8GkQfdAXZP0` | no | 64084 | chunks 0-7 of 9 stored raw; chunk 8 not retrieved (after transcript body ended) |
| 1b | YT_8GkQfdAXZP0 (Invidious list) | FAILED (list only, no transcript) | `inv.nadeko.net/api/v1/captions/8GkQfdAXZP0` | no | 155 | caption-track list JSON stored raw; the advertised track URL returned HTTP 500 |
| 2 | YT_Bkt8B3kLATQ (Episode 6) | FAILED | none | n/a | 0 | retrieval layer returned `SignatureDoesNotMatch` on all 5 attempts; see its ATTEMPTS_LOG |
| 3 | YT_nQfHZ2DEJ8c (Episode 3) | NOT EXECUTED | — | — | 0 | not attempted; see below |
| 4 | YT_PIYh0CxoY9c (OB16) | NOT EXECUTED | — | — | 0 | not attempted; see below |
| 5 | YT_FgacYSN9QEo (FVG16) | NOT EXECUTED | — | — | 0 | not attempted; see below |
| 6 | YT_HhgWGduQZQY (FVG24) | NOT EXECUTED | — | — | 0 | not attempted; see below |

## Why targets 3-6 were not executed

After Episode 12 was completed, the `fetch_page` retrieval layer began returning the Alibaba OSS
`SignatureDoesNotMatch` error document instead of reaching the requested host, on every call,
including single (non-parallel) calls. Episode 6 consumed its full 3-attempt budget on the mirror URL
plus one attempt each on timedtext and Invidious, all with the same layer error. No target-site
response body was received for Episode 6.

Targets 3-6 were therefore not attempted: no video ID was guessed, no request was fabricated, and no
status is claimed for them beyond NOT EXECUTED. They remain exactly as the pre-existing tracked
manifests describe them (PARTIAL, part_0 only).

## Method-ladder coverage actually reached

- Step 1 YouTube timedtext: tried for Episode 12 in four variants (`lang=en`; `kind=asr&fmt=vtt`;
  `fmt=srv3`; `kind=asr&fmt=json3`) — all `Failed to fetch page (HTTP 500)`. Tried once for Episode 6 —
  retrieval-layer error. No timedtext payload was ever obtained for any video.
- Step 1 Invidious/Piped: six instances tried for Episode 12. Only `inv.nadeko.net` returned a real
  API body, and only the caption **list**; its track URL returned HTTP 500. `yewtu.be` and
  `invidious.nerdvpn.de` returned anti-bot interstitials, `invidious.f5.si` a Cloudflare Tunnel error,
  `invidious.privacyredirect.com` an error page, `pipedapi.kavin.rocks` a fetch failure, and
  `pipedapi.adminforge.de` a 403. No VTT/SRV3/JSON3 payload with per-segment timestamps was obtained
  from any instance.
- Step 2 transcript-display sites: `youtubetotranscript.com` worked for Episode 12 and produced the
  complete transcript body. It did not expose timestamps in the retrieved rendering.
- Step 3 previous watch-page approach: not used this round for any video.

## Preference requested by the user

The user preferred sources returning per-segment timestamps and the full transcript in one response.
No such source was reachable. The one successful source returns the full transcript body but split
across tool chunks and with **no timestamps**. This is stated rather than compensated for.

## Integrity notes

- Every stored file is one raw `fetch_page` response, unmodified, including site chrome, menus,
  disclaimers and login prompts where present. This is flagged in the per-method MANIFEST.
- No memory, no secondary explainers, no gap filling, no interpretation, no ASR run, no market data.
- Mechanical cross-check counts and completeness check for Episode 12 are in
  `transcripts_full/YT_8GkQfdAXZP0/mirror_youtubetotranscript/MANIFEST.md`.
- Retry-budget overrun for Episode 12 mirror chunks 6, 7, 8 (4 attempts each vs. max 3) is disclosed
  in that MANIFEST and in the Episode 12 ATTEMPTS_LOG.
