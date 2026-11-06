# Example 3 - call the remote MCP server with plain Node

The hub also speaks MCP over Streamable HTTP at
`https://x402-agent-hub.x402-agent-hub.workers.dev/mcp`. This example drives it
with nothing but `fetch`: no SDK, no dependencies, Node 18+.

It makes three **free** calls and stops:

1. `initialize` - protocol handshake.
2. `tools/list` - how many tools exist, and is `token_verdict` among them.
3. `tools/call` for `token_verdict` **without** `paymentSignature` - the server
   answers `HTTP 200` with a text payload holding the 402 quote.

The point: an agent can discover the tool and read its price without a wallet.

## Run it

```bash
cd examples/03-mcp-tool
node verdict-via-mcp.mjs
```

Real output, captured from this repository:

```
MCP endpoint: https://x402-agent-hub.x402-agent-hub.workers.dev/mcp

initialize   HTTP 200  x402-agent-hub 1.6.0  protocol 2025-06-18

tools/list   HTTP 200  26 tools
token_verdict: present
  required args  token
  optional args  chain, paymentSignature

tools/call   token_verdict without paymentSignature   HTTP 200
  error  HTTP 402 Payment Required ($0.015 USDC on eip155:8453)
  howToPay
    Option 1 (1-Click Web / AgentCash): https://tryponcho.com/m/x402-agent-hub.x402-agent-hub.workers.dev
    Option 2 (Per-Call x402 Header): Sign the x402 v2 payment on your own machine and pass the base64 payload in the tool's optional 'paymentSignature' argument.
    Option 3 (Local Auto-Pay MCP): Run `npx -y github:BlackCat-cyber-creator/x402-agent-hub-mcp` with X402_BUYER_PRIVATE_KEY set locally; the key never leaves your machine.
    (1 more option in the full string)
  paymentRequiredHeaderBase64  eyJ4NDAyVmVyc2lvbiI6MiwiZXJyb3IiOiJQYXltZW50IHJlcXVpcmVkIiwicmVzb3VyY2UiOnsidXJs...  (3728 chars)
  decodes to  exact 15000 atomic USDC = $0.015 on eip155:8453, payTo 0x1721E9841257A34DbDBA407D4DBA3a727a02d072

Nothing was charged: no payment was attached, so no funds moved.
README.md shows the two ways to turn this quote into a paid verdict.
```

Exit code `0`. Nothing was paid.

What to notice:

| Line | Why it matters |
|---|---|
| `26 tools` | The remote server exposes all its tools to any MCP client, no session id, no handshake state kept between calls. |
| `paymentSignature` in optional args | Payment is a normal tool argument. The server does not need your key; you hand it a signed payload. |
| `tools/call ... HTTP 200` | An unpaid paid-tool call is not a JSON-RPC error. The result text carries the quote, so an agent can decide whether to pay. |
| `decodes to ... $0.015` | The same `payment-required` header a plain HTTP client sees, base64-encoded inside the tool result. |

## Getting a paid result (documented, not run here)

Both routes below are documented in the hub's own `howToPay` output. **Neither
was run from this workspace: there is no funded wallet here.** No paid
response is claimed.

### (i) Pass a `paymentSignature` you signed locally

Sign an x402 v2 exact-EVM payment for the requirements in
`paymentRequiredHeaderBase64` ($0.015 USDC on `eip155:8453`, `payTo`
`0x1721...d072`) on your own machine, base64-encode the payload, and pass it as
an argument:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "token_verdict",
    "arguments": {
      "token": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
      "chain": "base",
      "paymentSignature": "<base64 x402 payment payload>"
    }
  }
}
```

The key stays on your machine; the endpoint only ever sees a signed
authorization, never the key. Example 1
(`../01-http-x402-fetch/`) is the same payment flow over plain HTTP, where
`@x402/fetch` builds this payload for you.

Status here: documented, not run.

### (ii) Run the local stdio server with a key

```bash
X402_BUYER_PRIVATE_KEY=0xYOUR_DEDICATED_WALLET_KEY \
  npx -y github:BlackCat-cyber-creator/x402-agent-hub-mcp
```

That server runs on your machine, wraps `fetch` with `@x402/fetch`, and pays
each paid tool call automatically. Point your MCP host (Claude Desktop, Cursor,
Windsurf, VS Code) at the `npx` command and it behaves like any other MCP
server. The key is read from the environment locally.

Status here: documented, not run.

## Cost and safety

- `initialize`, `tools/list` and `get_hub_catalog` are free.
- An unpaid `tools/call` for a paid tool costs $0 and returns the quote.
- The paid call is **$0.015 USDC** on Base. Use a dedicated wallet with
  `$2`-`$5` in it, never a main wallet.
- Never send a private key to the remote endpoint. There is no field for one:
  payment is a signed payload, not a key.
