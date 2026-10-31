# Binance Agentic Wallet CLI (`baw`)

The Binance "Agentic Wallet" is custodial: the CLI prepares contract calls and pushes them to
the user's Binance app, where the USER approves before anything is signed. The agent never
holds a key — its job is preview → show the user → execute, and report a REAL tx hash.

Check it exists first: `which baw` and `baw wallet status --json` (→ `CONNECTED`). It ships
with the Hermes node and is often already installed AND already authenticated — never claim
"no wallet integration" before running these two checks.

## Auth / wallet switch
- `baw auth signin --json` → `{qrCodeId, urlForWeb, pairingCode}`. User opens `urlForWeb`
  (or scans) and/or enters the 6-char `pairingCode` in the Binance app.
- `baw auth verify --qrCodeId <id> --json` → `SUCCESS` once they scan (poll; it blocks).
- `baw auth signout` clears the session. Switch wallets = signout then signin (fresh QR).
- `baw wallet status --json` → CONNECTED/…
- `baw wallet address --json` → per-chain addresses (BSC = `binanceChainId 56`, the EVM
  address is shared across EVM chains).
- `baw wallet agent-id --json` → the `.ai` handle (used for agent-gated mint checks).
- `baw wallet balance --json` → native balance per chain.

## Contract calls (EVM)
```
baw contract-call preview --binanceChainId 56 \
  --from <wallet> --to <contract> --value <wei> --inputData 0x... --json
```
→ returns `requestId` + a simulation you MUST read:
- `parsedTx`: `transactionType` (`ContractInteraction`, `SendNft`…), `recipient`,
  `contractAddress`, `tokenId`, `action`.
- `simulationResult.balanceChanges[]`: the tokens/NFTs that move and to whom.
- `simulationResult.authorityChanges[]` / `allowanceChanges[]`: spending approvals granted.
  **Both must be EMPTY** for a plain mint/send; non-empty = the tx grants an approval =
  drainer red flag (reject unless that approval is the explicit intended prerequisite,
  e.g. a marketplace `setApprovalForAll` before a legitimate list).
- `simulationCode` `000000000` = clean; non-zero or `simulationErrorDetail` = it reverts
  for free here (would burn gas on-chain).

Then broadcast:
```
baw contract-call execute --requestId <id> --json
```
→ `{orderId, status:"BROADCASTED", txHash}`. Then read the receipt + the state change back
from the chain before reporting done — a broadcast tx hash is not proof of success.

`--gasLimit` is a cap, not a bypass: pass only when the user specifies one; omit to let the
backend estimate.

## NFT transfer (ERC-721)
`safeTransferFrom(from,to,tokenId)` selector `0x42842e0e`, `value 0`, no approval needed
when `from` IS the connected wallet. Simulate first (`eth_call` or the preview above) to
catch a transfer-lock — many pre-reveal collections revert transfers until reveal/sellout.
Verify `ownerOf(tokenId)` afterwards; transfers are irreversible, so show the recipient
address prominently before executing.

## Read-only recon is unchanged
`baw` only signs/broadcasts. The recon half (selectors, `eth_call`, simulation) is the same
and dep-free: compute keccak / run web3 scripts via `uv run --with pycryptodome` / `--with web3`.
