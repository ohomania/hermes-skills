# ComputeRoll (BSC) — agent-gated PoW token

`computeroll.com` — "mining" = keccak PoW, mint 10k CROLL per accepted proof. Not a free-mint; priced in compute, and the compute cost RAMPS.

## Contract + identity
- Token `ComputeRollAgentCapped` (CROLL, 18dp): `0x89dfBD9bdd2617141Fe159AB042069814F9B8F6E` — verified on BscScan, non-upgradeable.
- Identity gate = the SAME Binance `.ai` registry used by the other agent-native games: `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`. Eligibility check is `hasAgentId(wallet)` on the token contract (not just "holds .ai name").
- Submission is `value=0`, gas only, no approval/deposit/staking. Reward mints directly to the submitter.
- Authoritative manifest: `https://computeroll.com/agent-release.json` (chainId 56, `runtimeKeccak256`, economics). Verify `keccak256(getCode(contract))` against `runtimeKeccak256` before anything.

## Real ABI (from the manifest — NOT the site's inline sample)
- `mine(uint256 expectedPersonalRound, uint256 nonce, uint256 referenceEpoch)` — **3 args**. The mining-page "CPU reference" shows a STALE `mine(expectedEpoch, nonce)` (2 args) + `miningState()` (6 returns). That stale code produces reverting/unsatisfiable gas-waster candidates — ignore it.
- `miningState(address) view returns (uint256,bytes32,uint256,uint256,uint256,uint256,uint256,bool)` = `[personalRound, challenge, target, difficulty, rewardPerMine, proofsRemaining, globalMines, live]`.
  - `target = 2^256 / difficulty`; valid nonce ⇔ `keccak256(abi.encodePacked(bytes32 challenge, address miner, uint256 nonce)) < target` (**84 bytes** = 32+20+32). Confirmed byte-exact from the current `agent-miner-source.txt`; a GPU/CUDA miner must reproduce this packing. JS ethers `solidityPackedKeccak256` measures ~10k H/s → solo CPU ≈ 13 yrs/proof at ~4e12 difficulty.
  - `difficulty` matches manifest formula: `327680 + floor((1.8e13 - 327680) * min(globalMines,99999)/99999)`.
- `isValidSolution(address,uint256,uint256,uint256)`, `walletCapacity(address)` — cap 8M CROLL/wallet until `capUnlockAtGlobalMine`=50000.

## The trap: difficulty never softens
- Ramps 327,680 → 1.8e13 across the 100k-proof ceiling. At ~22k proofs it's already ~4.0e12 (~4 TRILLION hashes/proof).
- JS (ethers `solidityPackedKeccak256`) measured ~21k H/s → ~6 years/proof. Even 1 GH/s GPU ≈ ~1 hour/proof, racing farms winning every ~1s.
- Bottom line: only mineable in the FIRST few minutes on CPU; after that it's a GPU-farm race. Report this honestly — do NOT overpromise a "free mint".
