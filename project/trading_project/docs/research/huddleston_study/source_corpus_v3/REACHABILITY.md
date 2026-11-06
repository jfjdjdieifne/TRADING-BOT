# Reachability probe — Phase 1 (2026-11-06)

## Terminal (curl, 12s timeout each)

| URL | exact result |
|---|---|
| https://github.com | HTTP 200 |
| https://pypi.org | HTTP 200 |
| https://registry.npmjs.org | HTTP 200 |
| https://www.youtube.com | HTTP 000; `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to www.youtube.com:443` |
| https://duckduckgo.com | HTTP 000; `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to duckduckgo.com:443` |
| https://www.google.com | HTTP 000; curl exit 35 |
| https://youtubetotranscript.com | HTTP 000; `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to youtubetotranscript.com:443` |
| https://inv.nadeko.net | HTTP 000; curl exit 35 |
| https://web.archive.org | HTTP 000; curl exit 35 |
| https://www.bing.com | HTTP 000; curl exit 35 |

Tooling: Python 3.11.2, git 2.39.5. No ffmpeg/whisper/torch used; no ASR was run in this round.

## fetch_page tool

Every `fetch_page` call made in this round returned the same retrieval-layer error document instead of
reaching the requested host. Exact body:

```
<Code>SignatureDoesNotMatch</Code>
<Message>The request signature we calculated does not match the signature you provided. Check your key and signing method.</Message>
<EC>0002-00000040</EC>
```

Host returned by the tool: `routify-file-proxy-sg.oss-ap-southeast-1.aliyuncs.com`.

| intended URL | attempts this round | result |
|---|---:|---|
| https://youtubetotranscript.com/transcript?v=Bkt8B3kLATQ | 1 | retrieval-layer `SignatureDoesNotMatch` |
| https://theinnercircletrader.com/ | 1 | retrieval-layer `SignatureDoesNotMatch` |

Consequence: **no new PRIMARY text could be collected in this round.** Phase 1 therefore indexes only
PRIMARY text already stored in the repository from earlier rounds, copied byte-identically into
`primary/`. Search-engine results obtained through the `web_search` tool are recorded in `LEADS.md`
as leads only; none of them was opened, so none of them is a source and none supports any claim.

Sites NOT probed this round (budget): Piped instances other than those already recorded in
`../source_corpus_v2/transcripts_full/YT_8GkQfdAXZP0/ATTEMPTS_LOG.md`, archive.org capture endpoints,
GitHub code search for transcript repositories. Their earlier exact errors, where they exist, are in
that v2 attempts log.
