# `baw` — Binance Agentic Wallet CLI

Check connection first: `baw wallet status --json` → `CONNECTED`. The BSC address comes from `baw wallet address --json` (chain `56`).

## Read
```bash
baw wallet status --json      # CONNECTED?
baw wallet address --json     # EVM address per chain (BSC = 56)
baw wallet agent-id --json    # claimed .ai handle
baw wallet balance --json     # BNB/token balances + USD value
```

## Contract call (the core flow)
```bash
baw contract-call preview --binanceChainId 56 --from <wallet> --to <contract> --value 0 --inputData 0x… --json
baw contract-call execute --requestId <id> --json
```
`preview` returns `requestId` + `simulationResult`:
- `simulationCode "000000000"` = passes simulation; the revert reason shows in `simulationErrorDetail`.
- `balanceChanges[]` = the exact token movements (owner, tokenType, tokenId, change).
- `authorityChanges[]` / `allowanceChanges[]` = approvals. EMPTY for a plain mint/transfer. An `allowanceChanges` entry is EXPECTED on an `approve()` tx (it sets the single-token spender) — that is the one time it is not a red flag.
- `requireConfirmation: false` → `execute` goes straight to `BROADCASTED` + `txHash`.
- `requireConfirmation: true` → the user must approve in the Binance app before `execute` lands.

## Switch wallet
```bash
baw auth signout --json
baw auth signin --json              # → qrCodeId, urlForWeb, pairingCode
baw auth verify --qrCodeId <id> --json   # poll until SUCCESS
```
Give the user the `pairingCode` + `urlForWeb` (they scan/enter in the Binance app), then poll `verify` (may already return SUCCESS if they scan fast).

## NFT send
Call `safeTransferFrom(from, to, tokenId)` on the NFT contract (value 0). `baw` recognizes it as `SendNft` and shows the recipient + tokenId in `parsedTx`.

## Notes
- `--from` is the wallet's EOA on chain 56 (never the host machine user).
- Build `--inputData` with references/evm-selectors.md. `--value` is wei (1 BNB = 1e18).
- `--gasLimit` is a cap, not a bypass; omit it to let the backend estimate.
