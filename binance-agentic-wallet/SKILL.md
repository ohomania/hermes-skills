---
name: binance-agentic-wallet
description: Use when minting or listing NFTs on BNB Chain via baw CLI.
---

# Binance Agentic Wallet (baw)

The `baw` CLI is the Binance Agentic Wallet tool (usually already installed and authenticated). The agent PREPARES and VERIFIES transactions; the final approve/sign happens in the user's Binance app. Never fabricate a tx hash — report only real, on-chain-verified results. Ship the artifact/recon first; ask only for genuinely-missing parameters (addresses, tokenId, price, quantity).

## Core workflow

1. Confirm the wallet: `baw wallet status --json` (CONNECTED?), `baw wallet address --json` (per-chain address), `baw wallet agent-id --json` (.ai handle), `baw wallet balance --json` (gas sufficiency).

- **Windows/MSYS — `baw`/`flaggies` shims broken.** The shell shims mangle paths under git-bash (resolve to `…\hermes\git\Users\…\dist\index.js` → MODULE_NOT_FOUND). Always invoke the CLI entry directly: `node "$LOCALAPPDATA/hermes/node/node_modules/@binance/agentic-wallet/dist/index.js" <cmd> --json`. (`flaggies` CLI: `node "$LOCALAPPDATA/hermes/node/node_modules/flaggies-cli/src/index.js" <cmd>`.) Selector/keccak for manual calldata: require `@noble/hashes` under `…/node_modules/@binance/agentic-wallet/node_modules/@noble/hashes/sha3.js` (`keccak_256`).
2. Recon the target contract READ-ONLY first (see `references/evm-contract-recon.md`).
3. Build exact calldata (selector + ABI-encoded args).
4. `baw contract-call preview --binanceChainId 56 --from <wallet> --to <contract> --value <wei> --inputData <hex> --json` → returns `requestId` + a simulation (`balanceChanges`, `authorityChanges`, `allowanceChanges`, `risks`, `simulationCode`).
5. Inspect the preview (rules below). Then `baw contract-call execute --requestId <id> --json` → returns `txHash`.
6. Verify the receipt and resulting state on-chain (receipt `status`, `balanceOf`/`ownerOf`); only then report success.

## Signing EIP-712 messages (`baw sign-message`)

Agent-native MCP challenge mints (NONCE, Pheromone, …) require EIP-712 message signatures for auth + attempt authorization. Flow: `baw sign-message preview --binanceChainId 56 --signType EIP712 --message <wrapper> --json` → `requestId`, then `baw sign-message execute --requestId <id> --json` → `signature` + `signatureRecovery` (user approves in the Binance app).

- **The `--message` is an `eth_signTypedData_v4` JSON-RPC WRAPPER, not raw typed-data:** `{"method":"eth_signTypedData_v4","params":["<wallet>","<typed-data JSON string>"]}`. Pass the server's `walletRequest` typed-data object as `params[1]`.
- **Invoke with a subprocess LIST argv, never `shell=True` + inline JSON.** Embedding the wrapper in a shell command string mangles the nested quotes; the wallet answers 953004 "We currently don't support signing this type of message" — a quoting bug disguised as a type error. `subprocess.run([NODE, BAW, "sign-message", "preview", ..., "--message", wrapper, "--json"], ...)` fixes it.
- **Convert `uint256` message fields (expiry, issuedAt, agentId…) from decimal string to `int`** before wrapping — the server ships them as strings.
- **Recovery byte:** execute returns `signature` (128-char r‖s hex, no `0x`) + `signatureRecovery` (`"00"`/`"01"`). Form the 65-byte sig: `"0x" + sig + ("1b" if recovery == "00" else "1c")`.
- **Challenge → sign → verify in ONE script.** Auth challenges are single-use and expire in ~5 min; verify with the SAME nonce that was signed. A stale/cached nonce returns 401 `CHALLENGE_EXPIRED`/`NONCE_USED` — refetch and re-sign, do not reuse the nonce.

## Always-on safety gates

- `authorityChanges` and `allowanceChanges` in the preview MUST be empty for a mint/claim/send. A non-empty entry (setApprovalForAll, token allowance) is a drainer — stop and flag it.
- A legit mint/claim shows exactly `+N` of the target token in `balanceChanges`, no approvals, value = what `quote()` says.
- Identify the contract before trusting it: read `name()`/`symbol()`. Free-mint URL batches mix in decoys and wallet-drainers; an address that reverts on all standard ERC20/721 view functions is not a mint.
- "Voucher" / "registration" on these BSC agent-native reward vaults is an NFT balance, not a separate token: `eligibilityNFT()` is the `.ai` Agent ID registry (already held → qualified), and `registrationNFT()` is the voucher itself (`balanceOf(wallet) > 0` = voucher held). Run both read calls before assuming a registration is still pending.
- Check sold-out FIRST: `totalMinted() == MAX_SUPPLY()` makes every mint revert (`ExceedsSupply`). Per-wallet free quota is irrelevant once supply is gone.
- `quote(addr, qty)` is the authority for "is this free", not marketing copy. A wallet that already minted has its free allowance consumed (quote flips from 0 to paid).
- **`ALREADY_REGISTERED` / `ALREADY_CLAIMED` revert means the wallet already did the step — do NOT re-broadcast.** A `registerForRewards()`-style one-per-wallet call that reverts `ALREADY_REGISTERED` in preview is not a failure to power through; the wallet already registered, so executing would only burn gas on a guaranteed revert. Read the resulting state instead (`registrationNFT().balanceOf(wallet) > 0` = voucher held, `eligibilityNFT()` balances) and report "already registered / voucher already held". Same shape for `ALREADY_CLAIMED` / `ALREADY_MINTED` (free quota consumed).
- **VRF/entropy mints front a refundable oracle buffer.** A game whose mint requests Chainlink VRF (e.g. AnthroBit) sends `value = oracle CAP` (~0.001 BNB) up front even when the mint fee is 0 — the real oracle fee is ~0.000017 BNB and the excess is a claimable refund, but **the wallet must hold `value + gas` to mint, not just gas**. Read the game helper's plan `valueWei`/`oracleMaximumWei` instead of assuming gas-only because `mintPrice` is 0.
- NEVER trust the preview's tokenId for a mint. Other minters shift tokens between preview and execute. Read the real tokenId from the mint tx's `Transfer` logs (topic `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`; tokenId = `topics[3]`).
- Before transferring/lifting an NFT, simulate `safeTransferFrom` (selector `0x42842e0e`) via `eth_call` — collections often lock transfers until reveal/sellout (revert = locked).
- For NFT sales (marketplace): `ownerOf(tokenId)` must be the user's wallet first; approve the SINGLE token via `approve(market, tokenId)` (`0x095ea7b3`), never `setApprovalForAll`.
- Show the preview and get an explicit "go" before IRREVERSIBLE actions (transfer out, list, redeem/burn). Mints/claims can go preview→execute in one pass once the user has said "mint all free".

## Wallet switch

`baw auth signout` → `baw auth signin --json` (prints `urlForWeb` + `pairingCode`) → user scans QR or types code in the Binance app → `baw auth verify --qrCodeId <id>` until SUCCESS. A switch changes the on-chain address AND the .ai Agent ID; already-minted NFTs stay on the old wallet.

**The session also drops silently under heavy mint load** — `baw wallet status` flips to `UNCONNECTED` and the next sign/execute returns `Not logged in` (10003000) or `System abnormality` (100001001). Re-check status before every signature; re-pair exactly like a switch (`baw auth signin` → `baw auth verify --qrCodeId <id>`, a blocking long-poll — run it in the background with `notify` so it surfaces when scanned).

## Free-mint reality check (report honestly)

**Scout the fleet on Boltbook** (`boltbook.fun/b/alpha`) — other agents already post verified contract addresses, the exact mint function/selector, and first-free-per-wallet notes for the `.ai`-gated free mints. Cross-check on-chain anyway (`totalSupply` vs cap, `quote(wallet,1)==0`) — these collections sell out in hours and per-wallet free slots disappear first. Common direct-mint selectors: `mint()` = `0x1249c58b`, `mint(uint256)` = `0xa0712d68`, `freeMint()` = `0x5b70ea9f`.

Most "agent-native free mint" opportunities are sold-out, per-wallet-quota-exhausted, hidden-contract, or decoys. Pre-reveal collections have no secondary floor; the only price anchor is the mint price (a mint price, not a resale value). Report that plainly instead of implying value.

**Soulbound 1-per-wallet mints are engagement entries, not resellable NFTs.** A soulbound icon (identity card, proof-of-X badge) has no sale floor — its value is the follow-up mechanic it unlocks (a daily post/lottery, a future airdrop). Say so up front; don't promise resale. Offer to mint on every wallet the user holds, since each wallet is a separate entry.

## Kinds of agent-native mint — classify before promising

- **Direct mints** (`mint()`, `claim()`, `mintMany(...)`) go through `baw contract-call` normally.
- **Self-contained `prepare*`-with-manifest** (e.g. 4Broker): the domain's `skill.md` IS the whole skill — no helper install. It names a manifest URL (`https://<domain>/api/manifest` → verified `*Agent` addresses + `network`) and ships a selector table + a `node -e '…'` snippet that eth_calls the `*Agent` contract. Run `status <wallet>` first (hasAgentId, whether the free claim is already consumed, quota left), then `prepare* <wallet> …` returns a JSON `string` whose `call.{from,to,value,data}` is the real tx — preview THAT via `baw contract-call preview`, verify `call.to` sits on the skill's whitelist, show the human, get the yes, then execute. Decode its ABI `string`: word0 = byte-offset, word1 = byte length, then UTF-8 bytes. These games mandate prepare→preview→explicit-yes→execute (never same-turn execute) and may also require Developer Mode (`baw wallet settings --json` → `devMode.enabled`).
- **Privacy/ZK "private rails" mints** (shielded token + local seed + ZK proof, e.g. `404.build`) are NOT a simple call. They ship their own skill (install line like `npx skills add <org>/<repo>`), need a local prover, an encrypted seed behind a `--password-file` (the password must never reach chat), and are usually Unix/WSL-only because the vault relies on `0600`/`0700` permissions. Classify which kind before promising a fast mint: grep the SPA's minified JS chunks for the contract `0x…` and any `npx skills add …` string, not the landing-page "free mint" copy. For the ZK kind, surface the platform gate + password/seed overhead to the user up front instead of starting a heavy setup download that hits a known wall.

## 'Does this token have a price?' — liquidity probe

A minted token has no secondary value until it has liquidity. Call PancakeSwap v2 factory `getPair(token, other)` (factory `0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73`, selector `0xe6a43905`; other = WBNB `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c` or USDT `0x55d398326f99059fF775485246999027B3197955`). A zero address = no market. If a pair exists, read `getReserves()` (selector `0x0902f1ac`) with `token0()` (`0x0dfe1681`) for a rough price. **A pair that exists but returns `reserve0 == reserve1 == 0` is an EMPTY pool — no real liquidity, price undefined (NaN), token effectively $0; never report a price from an empty pool.** Wrap this in a `no_agent` watchdog cron — print nothing while there is no pair, print the alert only when one appears — so the user hears about it only when the token actually lists.

## Enumerate a wallet's full holdings (NFTs + tokens), then price them

When the user asks "what do I hold", "cek semua NFT", or "harga semua", do not guess or read only the contracts you already know:

- `baw wallet tx-history --binanceChainId 56 --json` is the authoritative inventory. Parse `data.transactions[].txHashList[].instructions.{receive,send}[]` — each entry carries `tokenInfo.{contractAddress,symbol,tokenId,decimals}` plus `amount`. It lists every NFT/token the wallet has ever received/sent, including contracts you never knew to check. Broad `eth_getLogs` scans are a poor substitute (public BSC nodes return empty or reject archive-range log queries).
- Track sends too: an NFT/token with no `send` entry is still held; one appearing in both `receive` and `send` may have moved out.
- Identify unknown contracts via `name()`/`symbol()`; a revert on both usually means it is not a standard ERC-20/721 view — retry as ERC-1155 (`balanceOf(account,id)` `0x00fdd58e`, `uri(id)` `0x0e89341c`) or read the proxy's implementation slot.
- Some ERC-721 are non-enumerable: `balanceOf` works but `tokenOfOwnerByIndex` reverts (drop.ai, the SPACE-ID `.ai` registry). Get the tokenId from tx-history or the mint `Transfer` log, not by enumerating.
- Price each holding honestly: NFTs → a game market with a real floor, otherwise no floor; Tokens → PancakeSwap probe (above), where an EMPTY pool = $0. Tokens named "Bound Points"/"points" are soulbound by design → $0, don't price-hunt them.
- **A marketplace "floor" is a seller ask, not a bid.** Before quoting an NFT's value, verify buy-side demand on the same market: the contract's `openBidCount()` via eth_call, or the official API's `topOffer`/`bids` field. A floor (e.g. 0.001 BNB) with `topOffer: null` and `openBidCount()==0` means nobody is buying at that price — listable, not instantly-sellable; thin day-volume is the same signal. Report "floor X, 0 bids" instead of a dollar number.
- **Decode `approve` by target, not name.** `0x095ea7b3` is `approve(address,uint256)` for BOTH ERC-20 (spender, amount) and ERC-721 (to, tokenId); `0xa22cb465` is `setApprovalForAll` in both ERC-721 and ERC-1155. When auditing a wallet's `approve` history, read the target's `balanceOf` / `totalSupply` / `decimals` — a two-digit arg is a tokenId, not a token amount. An active `setApprovalForAll` is lingering spend authority worth flagging.

Parsing + pricing snippet lives in `references/wallet-inventory.md`.
