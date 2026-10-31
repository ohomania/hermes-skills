# Hashstone — encodePacked hash-PoW free-mint (BSC 56)

"Orbit": 9,999 crystals drawn from Bitcoin's first blocks (NFT token ID = block height). Free mint gated by a `mine(nonce)` hash-PoW; only wallets holding a .ai Agent ID can mint, 2 per Agent ID, `value 0` (BNB gas only). Live settings at `https://hashstone.dev/api/bnb/config`; full prompt at `https://hashstone.dev/api/bnb/prompt`.

## Deployment (re-verify against /api/bnb/config before acting)
- Hashstone (mint) `0x00fbc656caa753a5280835bf9e849c4c0aff9bf4`
- Market `0xd440182bd99428488b7f1aacfbafafa86b1438dc`
- USDT `0x55d398326f99059ff775485246999027b3197955`
- .ai registry `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F` (SAME registry as NONCE — any already-registered .ai wallet is eligible)
- MCP `https://hashstone.dev/mcp` — Streamable HTTP, JSON-RPC 2.0, NO sign-in. Every tool returns info or an unsigned tx for the wallet to sign.
- `/api/bnb/config` carries live `open`, `bits` (24), `target`, `maxPerWallet` (2), `feeBps`, `supply`/`inPool`/`tickets`.

## MCP tools (no auth)
- `protocol_info` — `mintOpen`, target, difficultyBits, inPool, tickets.
- `agent_status(wallet)` — agentId (0 = no .ai, can't mint), mintsUsed/mintsLeft, BNB balance. Call for EVERY candidate wallet before wasting a PoW.
- `work_spec(wallet)` — the EXACT `preimageHexPrefix` + nonce encoding + reference code. Use this verbatim as the prefix.
- `check_proof(wallet, nonce)` — computes the proof hash; returns `valid` + `proof`. Validate every nonce here.
- `mine_transaction(wallet, nonce)` — the unsigned `mine(nonce)` tx (value 0, calldata = `mine(uint256)` selector + nonce). Returns `"The mint is closed."` when `open:false`.
- `ticket_status` / `crystal` / `market_listings` / `list_transactions` / `buy_transactions` — post-mint + market.

## Proof of work (byte-exact)
```
sha256(abi.encodePacked("HASHSTONE", uint256(56), address(contract), address(wallet), uint256(nonce))) < target
```
- `target` = `0x00000100…` = 2^232 = 24 leading zero bits, so `hash < target` ⟺ the first THREE digest bytes are `0x00` → check `(h[0]|h[1]|h[2]) === 0`. Never compare via `BigInt('0x'+hex)` per iteration — the hex→BigInt conversion, not SHA-256, is what kills throughput.
- Preimage prefix byte layout: `"HASHSTONE"` (9) + `uint256(56)` (32 bytes = 64 hex chars = 62 zeros + `"38"`) + contract addr (20) + wallet addr (20) = 81 bytes, then the nonce as 32-byte big-endian appended. The off-by-one zero bug in the uint256 field (`"0".repeat(63)` vs `62`) is silent — pull the prefix from `work_spec.preimageHexPrefix` and strip `0x`, don't hand-assemble pieces.
- Nonce binds to (contract, wallet); nobody can copy the proof from the mempool.
- 24 bits ≈ 16.7M hashes. Node `crypto.createHash` runs ~450–500k hashes/s, so one nonce ≈ 30–120s (single-threaded). Speed the loop by hashing the fixed 81-byte prefix once then cloning per nonce: `baseHash = createHash('sha256').update(prefix)` … `baseHash.copy().update(nonce32).digest()` (≈2× faster than a fresh createHash).

## Flow (in order)
1. `protocol_info` → require `mintOpen:true`. `agent_status` each wallet → confirm `mintsLeft>0`.
2. Pre-mine the allowance while waiting (see SKILL.md): run the PoW per wallet (2 nonces each), persist `{wallet, nonces}` to JSON, validate each with `check_proof`.
3. On open: `mine_transaction(wallet, nonce)` → unsigned tx → send via `baw contract-call preview` → user approves → `execute`. Verify the receipt on-chain.
4. The draw is two-step: the `Mined` event gives a TICKET, but the crystal is drawn from `sha256(proof || hash(block X+2))`. Expect `Revealed` (tokenId = block height) within seconds; if none after ~1 min, call `reveal(ticket)` (anyone may, value 0).
5. Report tokenId from `Revealed` → `https://hashstone.dev/api/bnb/item/<tokenId>` for name/rarity, `https://hashstone.dev/market.html#<tokenId>` for the 3D viewer.

## Pitfalls
- **`mine_transaction` returning "The mint is closed." is the early signal.** These mints open/close in minute-scale bursts. A `no_agent` cron watching `protocol_info.mintOpen` for a false→true transition + pre-mined nonces lets the first tx fire within seconds of open.
- **Validate nonces with the MCP, not your own hash.** Your local check proves nothing against the contract — the `check_proof` result must be `valid:true`, and its returned `proof` hex should equal your computed digest byte-for-byte (that equality is what caught the prefix byte-count bug).
- **baw pairing + session both die on idle.** Issue `baw auth signin` only when you are about to mint, and have the user scan at the moment of action — re-issuing far ahead of a wait just means a stale QR and an expired session when the mint actually reopens.
