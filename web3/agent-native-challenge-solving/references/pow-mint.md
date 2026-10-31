# PoW mints (sha256 nonce < target) — Hashstone / sidecoo CharmMine

Gate: find `nonce` such that `sha256(abi.encodePacked("HASHSTONE", uint256(56), address(contract), address(wallet), uint256(nonce)))` is below `target`. `target = 0x000001…00` == `2^232` == 24 leading zero bits == ~2^24 hashes expected.

## Recon
1. `GET /api/<chain>/config` → `{deployed, chainId, <contract>, target, bits, open/mintOpen, maxPerWallet, feeBps}` and `GET /api/<chain>/prompt` → full mint instruction (exact preimage, verify list, submit steps). Many serve plain JSON at those paths.
2. Confirm the contract == the one published on the site + Sourcify (name-squatting copies exist).
3. Read `status(wallet)` / `agent_status(wallet)`: `hasAgentId`, `mintsUsed` vs `max`, `quote`/`price` (0 = free), `open`.

## Miner (Node — hash the prefix once, `copy()` per nonce)

```js
const crypto = require('crypto');
const prefix = Buffer.from(prefixHex, 'hex');           // "HASHSTONE" + uint256 + addr + addr (81 bytes)
const baseHash = crypto.createHash('sha256').update(prefix);
const nonceBuf = Buffer.alloc(32);
let nonce = 0;
while (true) {
  nonceBuf.writeUInt32BE(nonce >>> 0, 28);              // nonce < 2^32 → last 4 bytes of the uint256
  const h = baseHash.copy().update(nonceBuf).digest();
  if ((h[0] | h[1] | h[2]) === 0) { break; }            // 24 zero bits == < 2^232
  nonce++;
}
```

- `baseHash.copy()` reuses the hashed 81-byte prefix state; re-creating the hash object per nonce is ~10x slower.
- Test `< target` as `(h[0] | h[1] | h[2]) === 0` for a 24-bit target — no per-iteration BigInt/hex string work.
- Node does ~0.5M hashes/sec this way; 2^24 ≈ tens of seconds per nonce (unlucky runs longer).

## Trap (costly)
- **`abi.encodePacked` field widths are exact.** `uint256(56)` is 32 bytes = 64 hex chars = `"0".repeat(62) + "38"`. Using `"0".repeat(63)` (one extra zero = 65 chars) shifts every later field and still yields hashes that look valid (< target) but FAIL the server's `check_proof` with `valid:false`. Always `check_proof(wallet, nonce)` (or the contract's `proofOf`) and confirm `valid:true` before building the `mine` calldata.
- The nonce is bound to (preimage, wallet); it does not expire unless `target` changes, so pre-mine nonces while the mint is closed and keep them ready.
