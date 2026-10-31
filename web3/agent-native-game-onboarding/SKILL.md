---
name: agent-native-game-onboarding
description: Use when onboarding a new .ai-gated game mint via baw.
---

# Agent-native game onboarding (Binance Agentic Wallet)

Most "agent-native" games (Piggy, Onchain Agents, Ptah, Ghost, SAGENT, 404, AnthroBit…) ship a helper or SKILL.md that does game-specific recon + unsigned plans. The agent downloads it, reads on-chain state, plans; the user approves/executes via `baw`.

## Procedure

1. **Get the helper/skill.** Common shapes:
   - `SKILL.md` / `skill.md` at the game domain (e.g. `anthrobit.fun/skill.md`).
   - A zip "**[name]-agent-skill.zip**" or `npx skills add <repo>` bundling `scripts/*.mjs` + `references/deployment.json` + `references/contracts.json`.
   - Download to a temp dir; **inspect the .mjs before running** — grep for `child_process`/`execFileSync` (legit only to shell out to `baw`), `eval`, or reading env/secrets. Reject anything suspicious.
2. **Run `status` first.** Trust `onchain` vs `paused` over marketing text. `deployed:false` or empty `contracts` = read-only/planning only.
3. **Verify `.ai` identity** (both read on-chain): helper `identity --wallet` (resolves via `baw`) or `identity --address 0x…` (RPC only, no baw). The identity NFT is the same Binance/SPACE-ID `.ai` registry across these games: `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` on BSC.
4. **Study collection:** `account` / `inventory` / `market` (read-only). Read the game's `references/gameplay.md` for units, fees, locks before any paid action.
5. **Free actions first:** `plan-welcome` (one-time +points) and `plan-mint --multiplier 1` (first mint fee = 0). Each plan returns `transaction.{to,valueWei,data}` + a `bawPreview` snippet.
6. **Execute:** `baw contract-call preview --binanceChainId 56 --from … --to … --value … --inputData … --json` → inspect `balanceChanges` (+N only; `authorityChanges`/`allowanceChanges` MUST be empty) → `baw contract-call execute --requestId …`. Verify the receipt on-chain; never fabricate a tx hash.

## Hard lessons (from AnthroBit + others)

- **VRF mints front a refundable buffer.** A "free" 0-fee mint still sends `value = oracle cap` (e.g. 0.001 BNB) up front; the real oracle fee is tiny (~0.000017 BNB) and the excess is a claimable refund. **The wallet must hold `value + gas` to mint**, not just gas. Read the plan's `fees.oracleMaximumWei`.
- **`--max-value-wei` is the whole native budget**, and the helper checks `mintFee + oracleBudgetWei > budget → error`. Pass ≥ the oracle cap for a mint, not just the quoted fee.
- **Mint is 2-step (VRF games):** `mint` → wait for VRF result → `reveal(tokenId)` (separate tx). `recovery` lists `nextAction: reveal` items.
- **`reveal` pays +2 BP to whoever calls it** ("anyone may call"); it gets revealed from the *currently connected* wallet, not necessarily the owner.
- **Oracle overpayment is claimable:** `plan-claim-refund --source oracle` → targets the beacon/entropy contract's `claimRefund()`. Always sweep it after minting.
- **BSC gas is cheap** (~0.067 gwei observed) — the blocker is the refundable *buffer*, not gas.
- **Wallet switching mid-session:** `baw auth signout` → `baw auth signin --json` (prints `urlForWeb` + `pairingCode`, ~2 min expiry) → user picks the wallet in the Binance app → `baw auth verify --qrCodeId …`.

## Report honestly

Free mint + welcome are gas-only (plus a refundable buffer). Resale value ≈ the market's cheapest listing (e.g. ~0.0014 BNB common on AnthroBit). No guaranteed payout — say so plainly.

## References
- `references/anthrobit.md` — AnthroBit contracts, selectors, mechanics (the worked example).
