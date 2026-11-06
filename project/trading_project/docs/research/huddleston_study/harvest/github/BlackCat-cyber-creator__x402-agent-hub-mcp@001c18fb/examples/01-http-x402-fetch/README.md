# Example 1 - pay for one x402 call over plain HTTP

This is the smallest real x402 client: one `fetch`, one `402`, one signed
USDC authorization, one answer. It calls the **token verdict** route:

```
GET /v1/crypto/token-verdict?token=<address>&chain=base
$0.015 USDC on Base (eip155:8453)
```

AERO (`0x940181a94A35A4569E4529A3CDfB74e38FD98631`) on Base is the address in
the example. Change `TOKEN` / `CHAIN` with environment variables to price any
other token.

## What it proves

- An unpaid request is a normal `HTTP 402` with a machine-readable quote in the
  `payment-required` header. You can read it with curl and no wallet.
- The same request with a key in the environment is paid automatically by
  `@x402/fetch`: it signs an EIP-3009 USDC authorization locally and retries.
  The key never leaves the machine and is never sent to the server.
- A refused payment (for example an empty wallet) is reported, not hidden, and
  **nothing is charged**.

## Prerequisites

- Node.js 18 or newer (global `fetch`, ESM).
- For the paid path only: a dedicated wallet holding `$2`-`$5` of USDC on Base
  mainnet, and its private key available as an environment variable.

## Run it

```bash
cd examples/01-http-x402-fetch
npm install
node verdict.mjs
```

`npm install` adds the three direct dependencies (`@x402/fetch`, `@x402/evm`,
`viem`) plus their transitive packages: 17 packages in total.

### Without a key: read the 402 quote (free)

Real output from the verification run (Node v24.2.0 on Windows):

```
No BUYER_PRIVATE_KEY set, so this run is the unpaid path: it reads the 402 quote only.

GET https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base
HTTP 402 Payment Required
body: {"error":"Payment required"}

decoded payment-required header:
  network           eip155:8453
  scheme            exact
  asset             0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
  amount            15000 atomic units = $0.015 USDC
  payTo             0x1721E9841257A34DbDBA407D4DBA3a727a02d072
  maxTimeoutSeconds 300
  resource          https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base

To buy this answer, put a dedicated wallet's key in the environment (never in a file),
fund it with $2-5 USDC on Base, and run the same command again:

  BUYER_PRIVATE_KEY=0x...  node verdict.mjs

A call that fails is not charged.
```

Exit code `0`. Nothing was paid, and no wallet was needed.

Reading those fields:

| Field | Meaning |
|---|---|
| `network` | `eip155:8453` is Base mainnet. |
| `asset` | The USDC contract on Base. |
| `amount` | `15000` atomic units. USDC has 6 decimals, so `15000 / 1e6` = `$0.015`. |
| `payTo` | The address that receives the payment. |
| `maxTimeoutSeconds` | How long the signed authorization stays valid. |
| `resource` | The exact URL being paid for; the signature is bound to it. |

### With a key: pay and get the verdict

Set the key in the environment only. Never in a file, never in the code.

```bash
# bash / zsh
export BUYER_PRIVATE_KEY=0xYOUR_DEDICATED_WALLET_KEY
node verdict.mjs
```

```powershell
# PowerShell
$env:BUYER_PRIVATE_KEY = "0xYOUR_DEDICATED_WALLET_KEY"
node verdict.mjs
```

The script accepts `BUYER_PRIVATE_KEY` or `X402_BUYER_PRIVATE_KEY`, with or
without the `0x` prefix, and prints only the wallet **address**.

#### What happens with an empty wallet (measured)

A random, never-funded throwaway wallet was used to prove the wiring. Real
output:

```
Paying wallet: 0xe9d229114B7bFaA90Eda6B284694214a20Ba0a6e
(the key stays in this process; only the address is printed)
GET https://x402-agent-hub.x402-agent-hub.workers.dev/v1/crypto/token-verdict?token=0x940181a94A35A4569E4529A3CDfB74e38FD98631&chain=base
HTTP 402
Payment refused: insufficient_funds - this wallet has no USDC on Base to pay with.
server said: {"error":"insufficient_funds: contract call failed: unable to call contract: execution reverted"}

Nothing was charged: an unpaid or refused call never moves funds.
```

Exit code `0`. This is the one failure mode worth knowing: an unfunded wallet is
refused up front, the error is named (`insufficient_funds`) instead of
swallowed, and no money moves.

#### What a funded run returns (documented, not run here)

With USDC in the wallet the same command returns `HTTP 200` and the verdict
JSON. The published response schema has these fields:

| Field | Content |
|---|---|
| `token` | `chain`, `address`, `name`, `symbol` |
| `grade` | `A`-`F` safety grade, computed from the audit, never from the AI |
| `label` | short grade label, for example `MOSTLY CLEAN` |
| `safetyScore` | `0`-`100` |
| `verdict` | one-line verdict |
| `take` | a short plain-language explanation |
| `redFlags`, `keyFacts` | arrays of supporting strings |
| `shareUrl`, `cardUrl` | public verdict page and PNG card |
| `audit` | the full audit the grade came from |

This workspace has no funded wallet, so no success body is shown here. The
script prints `grade`, `label`, `safetyScore`, `verdict`, `take`, `shareUrl`,
`cardUrl`, any `redFlags`, then the full JSON.

## Wallet safety

- Use a **dedicated** wallet for agents. Never a main or savings wallet.
- Fund it with `$2`-`$5` of USDC on Base. That is hundreds of calls at this
  price and caps the loss if the key leaks.
- Keep the key in the environment or your host's secret store, not in this
  directory and not in git.
- Never send a key to the remote endpoint. The signature is made locally and
  the key stays local.

## Cost and failure

- A successful call costs **$0.015 USDC** on Base.
- Unpaid requests, refused payments and failed reads cost **$0**. The route
  says so in its own metadata, and the empty-wallet run above confirms the
  refused-payment case.
