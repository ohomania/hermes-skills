---
name: evm-contract-operations
description: "Use for EVM on-chain work: mint, transfer, list, verify."
---

# EVM Contract Operations

Agent-native NFT mints, transfers, and listings, done on-chain. Every step follows: verify → simulate → execute → verify-again. Never claim a result from a broadcast status alone.

## Procedure
1. Identify + verify the contract before touching it: read `name()`/`symbol()`/`totalSupply()`/`mintOpen()`, and pull the project's `llms.txt` / `agent.json` / inline JS for ABI + selectors. Do not fire a pasted address + calldata until you know what the contract IS.
2. Read the wallet's actual eligibility/price: `hasAgentId(addr)`, `mintedBy(addr)`, `freeUsed(addr)`, `quote(addr, qty)`. `quote` == 0 means free, nonzero means paid. Check `totalSupply()` vs `MAX_SUPPLY()` for sold-out.
3. Simulate the exact call (raw `eth_call`, or `baw contract-call preview`).
4. On a `baw` preview, judge safety from `simulationResult`: `balanceChanges` = what moves; `authorityChanges` and `allowanceChanges` must be EMPTY for a plain mint/transfer — a non-empty allowance is a drainer red flag.
5. Execute, then VERIFY: poll the receipt (`status == 0x1`) AND read the resulting state (`balanceOf`/`ownerOf`). "BROADCASTED" is not success.
6. Report the tx hash + the verified on-chain result.

## Pitfalls
- tokenId from a preview is a SIMULATION snapshot — other mints between preview and execute shift the real id. Read the actual tokenId from the mint tx `Transfer` log (topic0 `0xddf252ad…`, `topics[3]` = tokenId) or `ownerOf`, never the preview number.
- Sold out is the #1 "can't mint" cause, and it reverts even when `mintOpen`/`canMint`/`quote` all look fine: `totalSupply() == MAX_SUPPLY()` → mint reverts `ExceedsSupply()` (selector `0x2d573a55`).
- When listing, `approve(market, tokenId)` on ONE token — never `setApprovalForAll`. Single-token approval caps the blast radius.
- web3.py rejects non-checksum addresses — wrap with `Web3.to_checksum_address()`. Use lowercase only for manual selector/calldata padding.
- Compute selectors (4-byte keccak256 of the signature) instead of guessing — see references/evm-selectors.md.
- BSC receipts: use `https://bsc-dataseed.binance.org/` for `eth_getTransactionReceipt`; `bsc.publicnode.com` handles `eth_call` but archive-restricts/403s receipts.
- "Mint all free" batches are mostly dead: sold out, unverifiable, or decoys. A URL that resolves to an unrelated page (a help doc, a Face ID page) is a decoy — verify every contract on-chain before promising anything.
- Simulate `safeTransferFrom` before transferring an NFT — some collections lock transfers until reveal/sellout and it reverts.

## Tooling that works
- Chain reads: `uv run --with web3 python script.py` (web3 + network to BSC RPC are reliable in the bash terminal).
- keccak256 for selectors: `uv run --with pycryptodome python`.
- Wallet actions: the `baw` CLI — see references/baw-agentic-wallet.md.
- Prices are in wei (1 BNB = 1e18 wei); build calldata with references/evm-selectors.md.
