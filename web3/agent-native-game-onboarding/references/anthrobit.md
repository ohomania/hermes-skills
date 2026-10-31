# AnthroBit (BSC chain 56) — worked example

Helper is a read-only Node CLI (`node scripts/anthrobit.mjs <cmd> …`), Node 22+.

- SKILL.md: `https://anthrobit.fun/skill.md`
- Skill zip: `https://anthrobit.fun/anthrobit-agent-skill.zip` (bundles `scripts/anthrobit.mjs`, `references/deployment.json`, `references/contracts.json`, `references/gameplay.md`)
- Extract then run from its dir. Run `status` first; `onchain` = game open.

## Commands
`status`, `identity`, `inventory`, `account`, `plan-welcome`, `plan-mint`, `plan-work`, `plan-claim-work`, `plan-claim-emission`, `plan-fuse`, `plan-rename`, `arena`, `plan-arena-*`, `market`, `plan-buy`, `plan-list`, `plan-cancel`, `plan-claim-market`, `recovery`, `plan-recover --kind mint|fuse|job --id <id>`, `plan-claim-refund --source oracle|arena|mint`.

Read-only commands accept `--address 0x…` (no baw) or `--wallet` (resolves via baw).

## Key contracts (BSC 56)
- AnthroBitCore (mint/reveal/getCard): `0xc7b7593Aa572701d26301D9707E93b0c511e636A`
- BinanceAgentRegistry: `0xE6484031D58857624C80fD166AF5BFCa686e57ec`
- AnthroBitPoints (BP): `0x6EEe003e2aEBE75bE551Ac509Eb485cc25E404Fb`
- ABIT (token): `0x742605891d8Aa624745745429171e36308f52394`
- EntropyBeacon (oracle refund): `0xd9FF2a5084bfa8f485a8e4143a5E6b5E1F9fA445`
- AnthroBitMarket: `0xf6218E96A1D5e3D4952F54965417A06Fd76ba31b`
- AnthroBitWork: `0xfE6d3B09849c06625f6badf00eE2188d109511D5`
- AnthroBitArena: `0x1c3FB713579Dd8a9B88C3B625345889184c419D2`
- Identity NFT (.ai registry): `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`

## Selectors (verified)
- `claimWelcome` = `0x608aee89`
- `mint(uint8,uint256)` = `0xf26748e2`
- `reveal(uint256)` = `0xc2ca0ac5`
- `claimRefund()` (EntropyBeacon) = `0xb5545a3c`

## Mechanics
- **Welcome**: `claimWelcome()` → +500 BP, one-time, activates the .ai identity in-registry. Gas ~202k.
- **Mint**: multipliers 1/2/4/8, ≤10/UTC day. First ×1 has 0 mint fee but sends `value = oracle cap` (0.001 BNB) up front; oracle excess refundable. Free/paid queues have one-birth-per-minute; creature usable after `bornAt`.
- **Rarity**: Common 75% / Rare 20% / Epic 4.5% / Legendary 0.5%. Stat ranges per tier; Common INT/PAT/CHA/WIS/SNK caps ~65.
- **Work**: 3 duty slots, `startWork(tokenId,stat,hours)` 6/12/24h; fees in BP (30/66/144 early) + oracle value. Earns BP + training + ABIT emission.
- **Fusion**: 3 same-tier → next tier; escrow 200/1000/5000 ABIT (C/R/E); success 50/35/20%.
- **Arena**: stake 100 BP, Elo, predictions.
- **Market**: list/buy/cancel; seller fee 15→3% by holding time; floor (common) ~0.0014 BNB observed.
- **Refunds**: oracle overpayment via `claimRefund`; arena deposit via `claimOracleRefund`; cancelled mint via `claimCancelledMintRefund`.
