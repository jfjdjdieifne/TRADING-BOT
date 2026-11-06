# MANIFEST — Episode 12 Invidious caption-list response

- source_id: YT_8GkQfdAXZP0
- video_id: 8GkQfdAXZP0
- method: public Invidious instance caption API (method-ladder step 1)
- exact_url: https://inv.nadeko.net/api/v1/captions/8GkQfdAXZP0
- retrieval_date: 2026-11-06 (Asia/Damascus local date of this session)
- label: YouTube auto-captions or MIRROR - provenance unverified
- timestamps: no
- video_status: FAILED (no transcript obtained from this endpoint)
- contains_non_transcript_page_content: yes — this response is a caption-track LIST, not transcript text
- bytes: 155
- sha256: cb48f9f1b1362dc06cd89f8977b1fcb2713da5c75cbab02243977818a3727efb

The instance advertised one caption track labelled `English (auto-generated)` at the relative URL
`/api/v1/captions/8GkQfdAXZP0?label=English+%28auto-generated%29`. Fetching that advertised URL, and the
`?lang=en` variant, both failed with `Failed to fetch page (HTTP 500)` (2 attempts each). No VTT, SRV3 or
JSON3 payload was ever returned by this instance, so no per-segment timestamps were obtained.

The response was stored raw and unmodified, including the markdown code fence that the retrieval tool
returned around the JSON.
