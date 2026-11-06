# REACHABILITY — step 0 results

Session: 2026-11-06 (UTC). Branch `arena/e91e69b1-trading-bot`.
All commands were run from `/home/user/TRADING-BOT`. Raw results only; no interpretation.

## 1. Terminal (curl) egress — three real pages attempted

Command shape: `curl -sS -o /dev/null -m 15 -w "%{http_code} %{size_download}b" <url>`

| URL | HTTP code | bytes | curl error |
|---|---|---|---|
| https://en.wikipedia.org/wiki/Market_trends | 000 | 0 | `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to en.wikipedia.org:443` |
| https://www.babypips.com/learn/forex | 000 | 0 | `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to www.babypips.com:443` |
| https://www.innercircletrader.com/ | 000 | 0 | `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to www.innercircletrader.com:443` |

Additional terminal probes, same shape:

| URL | Result |
|---|---|
| https://github.com | `200 527225b 0.377s` |
| https://api.github.com/rate_limit | `200 1917b 0.310s` |
| https://pypi.org/simple/ | `200 48178804b 0.293s` |
| https://codeload.github.com | `301 0b` |
| https://registry.npmjs.org | `200 2b` |
| https://files.pythonhosted.org | `404 10b` |
| https://raw.githubusercontent.com | `curl: (35) OpenSSL SSL_connect: SSL_ERROR_SYSCALL in connection to raw.githubusercontent.com:443` |
| https://objects.githubusercontent.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://archive.org | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://web.archive.org | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://www.forexfactory.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://www.reddit.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://medium.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://www.google.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| https://duckduckgo.com | `curl: (35) ... SSL_ERROR_SYSCALL ...:443` |
| http://en.wikipedia.org/wiki/Market_trends (port 80, plain HTTP) | `curl: (52) Empty reply from server`, code `000` |

Python probe: `urllib.request.urlopen('https://en.wikipedia.org/wiki/Market_trends', timeout=10)`
→ `ERR URLError <urlopen error TLS/SSL connection has been closed (EOF) (_ssl.c:992)>`

DNS resolves (`getent hosts en.wikipedia.org` → `2620:0:863:ed1a::1 dyna.wikimedia.org`, exit 0); the block is at the TLS/connection layer, not DNS.
No proxy environment variables are set (`env | grep -Ei 'proxy'` → none).

**Conclusion from the terminal:** the shell has an egress allowlist only. Reachable: `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`. Everything else fails with TLS `SSL_ERROR_SYSCALL` (or `Empty reply` on port 80).

## 2. Built-in session tools

### 2a. `fetch_page` (server-side page fetcher, returns Markdown)
- `fetch_page https://en.wikipedia.org/wiki/Market_trends` → `status: success`, `title: "Market trend - Wikipedia"`, `totalChunks: 17`, returned Markdown text of the article (chunk 0). **Works.**
- `fetch_page https://www.babypips.com/learn/forex` → `status: success`, `title: "Learn Forex Trading at School of Pipsology - Babypips.com"`, `totalChunks: 3`. **Works.**
- `fetch_page https://www.innercircletrader.com/` → `{"error":"Failed to fetch page","status":"error"}`. **Fails** for that host (no HTTP code exposed by the tool).

Behaviour: returns page text already converted from HTML to Markdown, in numbered chunks (`chunkIndex`), with `hasMore`/`totalChunks`. It does not expose HTTP status codes, response headers, or raw bytes. Long pages must be read chunk by chunk.

### 2b. `web_search`
- Query `Inner Circle Trader Michael Huddleston order block fair value gap notes`, depth 1 → `status: success`, 3 results with titles, URLs, `pageAge`, and long extracted text snippets. **Works.**
- Behaviour: returns result title, URL and extracted page text (not just snippets), no HTTP codes, no pagination control observed.

## 3. Consequence for this harvest

The shell cannot reach the open web, but the session's own `fetch_page` and `web_search` tools can. Therefore this run is **not** limited to the GitHub-only fallback (step 0B). Two retrieval channels are used, and each stored file records which one produced it:

- `method: fetch_page` — page text as returned by the session fetcher (HTML already converted to Markdown by the tool; no further edits made by me).
- `method: curl/api.github.com` — raw bytes fetched in the shell from GitHub, byte-exact, sha256 computed in the shell.

GitHub channel is additionally available in the shell (`api.github.com` + `git clone` over `github.com`), so GitHub-hosted text is stored byte-exact.

Blocked for the shell and therefore only reachable through `fetch_page`/`web_search`: Wikipedia, babypips.com, forexfactory.com, reddit.com, medium.com, archive.org / web.archive.org, raw.githubusercontent.com, and every other non-allowlisted host. This means **no way to `curl` raw bytes for those hosts**; their stored text is the fetcher's Markdown rendering, and this is stated per-file in `INDEX.jsonl`.
