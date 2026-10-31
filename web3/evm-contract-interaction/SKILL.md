---
name: evm-contract-interaction
description: Use when scouting EVM contracts or building mint/claim txs.
---

# EVM Contract Interaction

Read chain state, prove a write will succeed, and hand the user a ready-to-broadcast transaction or script — without ever signing when you have no signer.

## Capability gate (decide first, and say it)
1. Determine whether this session CAN sign: a wallet connector, the user's private key, or the Binance Agentic Wallet CLI (`baw`). Check for `baw` FIRST — it is often already installed and authenticated (`which baw`, `baw wallet status --json`); never claim "no wallet integration" without checking. With `baw` connected you go `contract-call preview` → user approves in the Binance app → `contract-call execute`, and you CAN deliver a real tx hash (see `references/baw-cli.md`). Only if no signer exists are you in **read-only scout + script-builder** mode. State that up front, once, plainly — every "mint/free/claim" request still lands as a verified tx + script, not as a broadcast done by you.
2. Never fabricate a transaction hash or a "confirmed" result. A tx hash may only be reported after an actual broadcast. No signer → you deliver calldata/script/preview, not a hash.
3. Never ask for, accept, or echo a private key or seed in chat. Read it from an env var (`PRIVATE_KEY`) inside the script.

## Procedure
1. **Identify the contract + real ABI from the project, not by guessing.** Mint sites hide the true function in a static `config.js`/`abi.js` or inline `<script>`, often alongside truncated on-page addresses. Fetch the HTML (`curl -s -A 'Mozilla/5.0' <url>`), pull `<script src>` entries and inline JS, then `grep -oE '0x[0-9a-fA-F]{40}'` and grep the function names/`ethers.id(...)`/calldata. Projects name the same operation differently (`mintFree()`, `mint()`, `mint(uint256)`) — never assume one project's ABI matches another's. For the Binance `.ai` Agent-ID free-mint family on BNB, other AI agents already catalogue the contract addresses + which function is the free path on Boltbook (`boltbook.fun/b/alpha`) — search `site:boltbook.fun` first and reuse those addresses, but still preview each before executing (free tiers fill in hours).
2. **Compute selectors and read state with `eth_call`.** Compute keccak256 first-4-bytes yourself; a given signature maps to the same selector on every contract, so well-known functions are stable (see `references/selectors-and-decoding.md`). Read the values that actually gate the operation, not just the obvious ones.
3. **Prove the write succeeds before recommending it.** `eth_call` the exact calldata WITH `{from, value}` (a simulation), then `eth_estimateGas`. A revert here means a real send would burn gas — report the reason, don't send.
4. **Build a web3.py script** with DRY RUN as the default (broadcast only when `SEND=1`), private key from env, value from the per-wallet quote (see pitfalls). Verify at least once that the script runs in dry-run against a throwaway key (build path executes without error).
5. Report the verified tx fields (`to`, `value`, `data`, `gas`, chain) and the script path. Never a hash you didn't actually broadcast.

## Pitfalls
- **Passing the gate views is not proof a mint works.** `canMint`/`mintOpen` are eligibility checks, not supply checks. Always also compare `totalMinted()` vs `MAX_SUPPLY()` and simulate the actual mint. `ExceedsSupply` (`0x2d573a55`) means sold out even when every eligibility check passes.
- **A reverting mint usually means sold out, not a wrong selector.** During a live free-mint rush a collection sells out in hours, so when a mint preview/`eth_call` reverts, read `totalSupply()` vs `MAX_SUPPLY()`/`maxSupply()` FIRST — if supply is full the call was correct and the project is just done. Only hunt for a different `mint`/`freeMint`/`mintType` signature after confirming supply is still open.
- **"Free" mints still consume gas.** value is 0, but the tx needs native balance for gas (~0.0003 BNB region on BSC). Check `eth_getBalance` before declaring a wallet ready.
- **`price()` is not the amount to send when a free tier exists.** Read the per-wallet value via `quote(address,quantity)`, `nextPrice(address)`, or `freeUsed(address)` and send that — free thresholds (e.g. `freeThreshold`, first-free-per-wallet) make the static price misleading.
- **Decode a 4-byte revert via a signature DB, not the node's message.** Nodes truncate/mangle revert reasons (e.g. "reverted: -W:U"). The `data` field is the custom-error selector — look it up on openchain.xyz (`/signature-database/v1/lookup?function=0x...`).
- **One shared gate address recurs across a project family.** Agent-gated BNB NFTs all check a shared registry (e.g. the "SPACE ID Agent ID" contract). Verify `balanceOf(wallet)` against it once instead of re-deriving per project.
- **A preview must show only the expected move and EMPTY `authorityChanges`/`allowanceChanges`.** In `baw contract-call preview`, non-empty authority/allowance lists mean the tx grants a spending approval = drainer pattern; reject unless that approval is the explicit intended prerequisite (e.g. a marketplace `setApprovalForAll` before a legitimate list). A clean free mint = one +1 `balanceChanges` to your wallet with both approval lists empty.

## Support files
- `references/selectors-and-decoding.md` — stable selector table + return decoding + custom-error lookup.
- `references/baw-cli.md` — Binance Agentic Wallet CLI: auth/wallet-switch, contract-call preview→execute, reading the simulation for drainers, NFT transfer.
- `references/bsc-endpoints.md` — RPC endpoints that work, explorer caveats, Cloudflare bot-wall workaround.
- `scripts/rpc_scout.py` — generic read-only probe: contract + signatures → state dump (re-runnable).
