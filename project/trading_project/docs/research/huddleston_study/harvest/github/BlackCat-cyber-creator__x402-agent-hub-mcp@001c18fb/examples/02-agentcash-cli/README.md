# Example 2 - AgentCash CLI

[AgentCash](https://github.com/Merit-Systems/agentcash/tree/master/packages/external/mcp)
is a command-line x402 wallet (npm package `agentcash`). One command reads what
an endpoint costs and wants (free), one lists everything an origin sells (free),
and one pays and calls it.

All three commands below target the same route:

```
GET https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base
```

Pinned here: `agentcash` `0.17.1` via `npx -y agentcash`. Run `check` first: it
prints the exact field names, and calling `fetch` with the wrong ones returns
`400`.

## 1. `check` - free pre-flight

```bash
npx -y agentcash check "https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base"
```

**Cost: $0.** It reads the origin's OpenAPI spec and prints the schema. No
payment is attempted.

Real output:

```json
{
  "success": true,
  "data": {
    "url": "https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base",
    "results": [
      {
        "method": "GET",
        "source": "openapi",
        "summary": "Token verdict: A-F safety grade and plain-language take on any token, from a live honeypot, tax and liquidity audit",
        "authMode": "paid",
        "estimatedPrice": "0.015 USD",
        "currency": "USD",
        "protocols": [
          "x402"
        ],
        "inputSchema": {
          "parameters": [
            {
              "name": "token",
              "in": "query",
              "required": true,
              "description": "Token contract address: 0x-prefixed on EVM chains, base58 mint on Solana.",
              "schema": {
                "type": "string",
                "example": "0x940181a94A35A4569E4529A3CDfB74e38FD98631"
              }
            },
            {
              "name": "chain",
              "in": "query",
              "required": false,
              "description": "base (default), ethereum, bsc, arbitrum, optimism, polygon, avalanche or solana.",
              "schema": {
                "type": "string",
                "example": "base"
              }
            }
          ]
        },
        "outputSchema": {
          "type": "object",
          "properties": {
            "token": {
              "type": "object"
            },
            "grade": {
              "type": "string"
            },
            "label": {
              "type": "string"
            },
            "safetyScore": {
              "type": "integer"
            },
            "verdict": {
              "type": "string"
            },
            "take": {
              "type": "string"
            },
            "redFlags": {
              "type": "array"
            },
            "keyFacts": {
              "type": "array"
            },
            "writer": {
              "type": "string"
            },
            "shareUrl": {
              "type": "string"
            },
            "cardUrl": {
              "type": "string"
            },
            "audit": {
              "type": "object"
            }
          }
        },
        "requiresPayment": true
      }
    ]
  }
}
```

The three fields that decide what happens next: `authMode: "paid"`,
`estimatedPrice: "0.015 USD"`, and the required query parameter `token`
(`chain` optional, default `base`).

Note on this machine (Windows, Node v24.2.0): the JSON above printed in full,
then the process aborted at exit with a Node/libuv assertion
(`-1073740791`, which is `0xC0000409`; Node's `close` event reports the same
status as `3221226505`). The check itself had completed and cost nothing.
`discover` below does the same, measured 2026-10-31: the whole JSON reaches
stdout, then the same abort and the same exit code. So read the exit code as
noise, not as a failure, and check instead that stdout parses as one complete
JSON document.

## 2. `discover` - free endpoint list

```bash
npx -y agentcash discover https://x402-agent-hub.x402-agent-hub.workers.dev
```

**Cost: $0.** It reads the origin's OpenAPI spec and lists every endpoint with
its price. No payment is attempted.

Real output, trimmed to the first entry, the last one and the single ownership
proof; every cut is labelled in place. The full run prints `25` endpoints:
`15804` characters on stdout, `15806` UTF-8 bytes, 347 lines, byte-identical on
three consecutive runs (SHA-256
`17bad1ca83393ee7096dbac9037fcc3ee30d64740b3abb6d21580e6e9057757f`). Measured
2026-10-31 with `agentcash` `0.17.1` on Node v24.2.0 by capturing the child
process's stdout: characters are `stdout.toString('utf8').length`, bytes are
the raw `Buffer` length. The two bytes of difference are the em dash in
`title`; a PowerShell `>` redirect is not a byte figure, it writes UTF-16 and
roughly doubles the count.

```json
{
  "success": true,
  "data": {
    "found": true,
    "origin": "https://x402-agent-hub.x402-agent-hub.workers.dev",
    "source": "openapi",
    "trustTier": "ownership_verified",
    "info": {
      ... "title" and "description" (the origin's own prose, omitted here to keep this file ASCII) ...
      "version": "1.6.0"
    },
    "endpoints": [
      {
        "path": "/v1/trading/sessions",
        "method": "GET",
        "summary": "Live ICT Killzones, Silver Bullet windows, and CFD rollover spread-danger alerts",
        "authMode": "paid",
        "price": "0.005 USD",
        "pricingMode": "fixed",
        "currency": "USD",
        "protocols": [
          "x402"
        ],
        "resourceKey": "https://x402-agent-hub.x402-agent-hub.workers.dev GET /v1/trading/sessions"
      },
      ... 23 more endpoints ...
      {
        "path": "/v1/crypto/token-verdict",
        "method": "GET",
        "summary": "Token verdict: A-F safety grade and plain-language take on any token, from a live honeypot, tax and liquidity audit",
        "authMode": "paid",
        "price": "0.015 USD",
        "pricingMode": "fixed",
        "currency": "USD",
        "protocols": [
          "x402"
        ],
        "resourceKey": "https://x402-agent-hub.x402-agent-hub.workers.dev GET /v1/crypto/token-verdict"
      }
    ],
    "ownershipProofs": ["0x... (64-byte payTo signature, trimmed)"],
    "guidanceAvailable": true,
    "guidanceTokens": 794,
    ... "guidance": the 794-token plain-text routing guide (3174 characters), omitted here ...
  }
}
```

What the list is for: `path`, `method`, `summary`, `price` and `authMode` per
endpoint, plus `source: "openapi"` (the prices came from the origin's
`/openapi.json`) and `trustTier: "ownership_verified"` for the origin - that
tier is AgentCash's own read of the origin, not a field of our spec. The origin
publishes `ownershipProofs` for it: one `0x` value of 130 hex characters (a
64-byte signature plus a recovery id) that its `payTo` wallet made over its own
URL, listed in `/openapi.json` under `x-discovery.ownershipProofs`. It is a
signature, not a transaction, so it ties the payout address to this API without
sending anything onchain. Prices run from `0.002 USD` to `0.05 USD`;
`token-verdict` is `0.015 USD`. Save the full list with
`npx -y agentcash discover <origin> > endpoints.json`.

## 3. `fetch` - this one pays

> **WARNING - this command spends real USDC.**
> `agentcash fetch` pays automatically from the local AgentCash wallet: if the
> endpoint answers `402`, the CLI signs and pays, then retries. The documented
> flow has no per-call confirmation step, and nothing in it caps the amount for
> you. `agentcash --help` does expose `-y, --yes` for prompts and
> `agentcash settings set maxAmount <usd>` for a ceiling; treat any prompt as a
> last chance, not a safeguard.
> **Agents must not run this command.** Only a human, with a wallet they
> intentionally funded with a few dollars, should.
> **This example was not run here.** No funded wallet exists in this workspace,
> so this README makes **no claim about `fetch` output**. The command and the
> cost are documented; the result is not.

```bash
# NOT RUN IN THIS REPOSITORY - spends $0.015 USDC from the local agentcash wallet
npx -y agentcash fetch "https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base"
```

**Cost: $0.015 USDC on Base**, paid from the wallet AgentCash keeps locally
(`~/.agentcash/wallet.json`, created on first use). Check the balance first
with `npx -y agentcash balance`.

What `agentcash fetch --help` says it returns: the final HTTP response, plus
response headers and the raw payment receipt proof supplied by the server when
there is one. That is the CLI's own description, quoted, not an observation of
a run.

## What was actually run here

| Command | Run | Cost | Exit code |
|---|---|---|---|
| `check <url>` | yes, 2026-10-31 | $0 | JSON printed, then a Node/libuv abort at exit on Windows (`-1073740791`) |
| `discover <origin>` | yes, 2026-10-31 | $0 | JSON printed (complete), then the same Node/libuv abort at exit on Windows (`-1073740791`) |
| `fetch <url>` | **no** | would be $0.015 | not applicable |

## If you only remember one thing

`check` and `discover` are free reads of a public spec. `fetch` is a purchase.
Run it only from a wallet you deliberately funded, and only as a human.
