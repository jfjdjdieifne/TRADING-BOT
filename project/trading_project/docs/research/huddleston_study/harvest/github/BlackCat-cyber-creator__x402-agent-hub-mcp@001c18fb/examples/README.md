# Examples

Three runnable clients for **x402 Agent Hub**, each one a different way in:
plain HTTP with `@x402/fetch`, the AgentCash CLI, and the remote MCP server.

They all call the same paid route, so you can compare the three paths on one
price:

```
GET /v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base
$0.015 USDC on Base (eip155:8453)
```

| Example | What it proves | Price of the call | Funded wallet needed |
|---|---|---|---|
| [01-http-x402-fetch](./01-http-x402-fetch/) | A plain `fetch` gets a machine-readable `402` quote; `@x402/fetch` signs a USDC authorization and retries. Shows the refusal path (`insufficient_funds`). | $0 to read the quote, $0.015 to buy the answer | Only for the paid run. The quote run needs no wallet. |
| [02-agentcash-cli](./02-agentcash-cli/) | The AgentCash CLI: `check` and `discover` price the service for free, `fetch` pays automatically. | $0 for `check` and `discover`, $0.015 for `fetch` | Only for `fetch`, which this repository did **not** run. |
| [03-mcp-tool](./03-mcp-tool/) | The remote MCP server answers `initialize`, `tools/list` (26 tools) and an unpaid `tools/call`, with zero dependencies. | $0 - no payment is attached | No. Both paid paths are documented, not run. |

## What runs with no wallet

Examples 1 and 3 have a no-wallet path that is the default: without a key they
print the 402 challenge and the tool list, exit `0`, and cost nothing. Example
2's `check` and `discover` are also free. Every output pasted in these READMEs
comes from one of those no-wallet runs, except the empty-wallet refusal in
example 1, which used a throwaway key that was never funded.

## What needs a funded wallet

Buying a verdict - `node verdict.mjs` with `BUYER_PRIVATE_KEY` set, or
`agentcash fetch`, or either paid MCP route - moves `$0.015` USDC on Base. None
of those paid paths was executed from this workspace, and no paid response is
shown anywhere in these files.

## The safety rule

**Use a dedicated agent wallet funded with $2-$5 of USDC on Base, never a main
wallet, and never let an agent run a paying command unless a human meant it.**

## Common shape of every x402 call

1. Request the resource.
2. Get `HTTP 402` with a `payment-required` header: network, asset, amount in
   atomic units, `payTo`, timeout.
3. Sign a USDC authorization for exactly that amount, locally, with your key.
4. Retry the same request with the signed payload in `PAYMENT-SIGNATURE` (or as
   the tool's `paymentSignature` argument).
5. Receive the answer, or a refusal. A failed call is not charged.

## Requirements

- Node.js 18 or newer for examples 1 and 3 (global `fetch`, ESM). Example 3 has
  no dependencies at all; example 1 installs `@x402/fetch`, `@x402/evm` and
  `viem`.
- Example 2 needs no local install: `npx -y agentcash ...`.
