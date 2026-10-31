# RaidLords withdraw / claim mechanics (reverse-engineered from game/api.js)

Withdrawal = two game calls + ONE on-chain transaction submitted by the account's own wallet.

## Sign-in (wallet → session token)
The account IS a wallet, not a username. Fresh account = sign-in with a wallet (the bot can do this with the burner key):
1. `POST {SB.url}/functions/v1/wallet-auth` body `{wallet}` (headers: `apikey: anonKey`, `authorization: Bearer anonKey` — no session yet) → `{message}`.
2. `personal_sign` the message with the wallet key → `signature`.
3. `POST .../wallet-auth` body `{wallet, signature}` → `{player (pid), token}` → save as the session (`{pid, token}`).

The nonce vs verify branch is decided by the presence of `signature` in the body; both map to the same `/functions/v1/wallet-auth` edge function.

## Withdraw (two game calls, then the tx)
1. `sg_withdraw {amount}` → `api_withdraw {p_amount}` → marks the withdrawal "owed"; returns `{net, banned, ...}` (net = after 5% fee).
2. `POST {SB.url}/functions/v1/vault` body `{action:"sign"}` (with session `Bearer` header) → a signed voucher `{wallet, to, data, cumulative, deadline, amount}`. `to` is the `RaidClaim` contract; `data` is the calldata for `RaidClaim.claim(...)`.
3. The account's OWN wallet sends `eth_sendTransaction {to, data, gas}` — the claim pays `cumulative - claimed[account]` and is idempotent (an old/used voucher reverts `0x969bf728` NothingToClaim).

## Constraints (server vault model)
- Min withdraw **2500 RAID**; **5% fee** (half burned, half to reward pool).
- Fresh accounts are **24h-locked for EARNED tokens** (`earn_from`); deposited tokens withdraw any time.
- A voucher is valid ~1h (`deadline`).
- The claim tx MUST come from the wallet that signed in — `/vault sign` vouchers that wallet, and `vaultClaim` rejects a mismatched sender.
- Gas: `estimateGas * 1.5`, floor **180000** (the bare estimate runs out when the vault state moves in the same block).

## Burner wallet for auto-withdraw
Generate a fresh key ON the box (`ethers` `Wallet.createRandom()` → `{address, key}` to a chmod-600 file), sign the account in WITH it (so claim tx + destination are both the burner), fund it ~0.001 ETH for gas. Keeps the user's main wallet key off the server. The key file should never be echoed into chat — print only the address.