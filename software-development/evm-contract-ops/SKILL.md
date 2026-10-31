---
name: evm-contract-ops
description: Use when reading or prepping EVM contract txs via RPC.
---

# EVM Contract Ops (read-only scout + verified tx prep)

For tasks like "check / mint / interact with contract X on chain Y" when the session has
NO signer (no wallet integration, no private key). The deliverable is verified on-chain
state + exact calldata + a ready-to-run script the user broadcasts with their own key —
never a fabricated transaction hash.

## Procedure (in order)

### 1. Get a working RPC
- BNB Smart Chain: `https://bsc.publicnode.com` works keyless. Confirm with
  `eth_chainId` == `0x38` (56) before building anything on it.
- Have a fallback ready; some providers (ankr) now require an API key and return
  `-32000 Unauthorized` without one.

### 2. Compute function selectors (keccak256)
Selector = first 4 bytes of keccak256 of the canonical signature string
(`name(type1,type2)`). The system python usually lacks keccak — use uv:
```bash
uv run --with pycryptodome python -c "from Crypto.Hash import keccak; k=keccak.new(digest_bits=256); k.update(b'mintFree()'); print(k.hexdigest()[:8])"
```

### 3. Encode args for the calldata
- address arg: `"0"*24 + addr[2:].lower()` (left-padded 32-byte word)
- uint256 arg: `hex(n)[2:].zfill(64)`
- `data = "0x" + selector + encoded_args`

### 4. Read view state with eth_call
JSON-RPC `eth_call` with `{"to": contract, "data": data}, "latest"`. Decode:
 bool/uint = `int(result,16)`; tuple of words = split hex into 64-char chunks;
 string = skip offset word + length word, then decode bytes.

Probe these generic selectors to identify an unknown contract fast:
`name() 0x06fdde03`, `symbol() 0x95d89b41`, `totalSupply() 0x18160ddd`,
`MAX_SUPPLY() 0x32cb6b0c`, `mintOpen() 0x24bbd049`, `totalMinted() 0xa2309ff8`,
`price() 0xa035b1fe`, `balanceOf(address) 0x70a08231`.

### 5. SIMULATE any state-changing call before advising "send"
For the function the user actually wants to call, run BOTH with `from` = the user's
wallet address: `eth_call` (returns `0x` on success) AND `eth_estimateGas`. A revert
here means the real transaction REVERTS and burns the user's gas — do not tell them to
send. This is the highest-value check and the one that catches a sold-out collection.

### 6. Decode a revert reason
A 4-byte value in the revert `data` is a custom error selector. Decode it at:
`https://api.openchain.xyz/signature-database/v1/lookup?function=0x<selector>&filter=true`
(4byte.directory does NOT index custom errors; openchain.xyz does.)

### 7. Cross-check the REAL blocker before concluding
Eligibility gates passing (`canMint` / `hasAgentId` true) does NOT mean a mint works —
supply can still be exhausted. Compare `totalMinted()`/`totalSupply()` against
`MAX_SUPPLY()`. Also check the wallet's gas balance via `eth_getBalance` — a value-0
"free" mint still needs BNB for gas.

### 8. Deliver a ready-to-run script (not a hash you cannot produce)
Write a `web3.py` script: DRY RUN by default (`SEND=1` flag to broadcast), private key
from a `PRIVATE_KEY` env var (never from chat), assert the gate checks, build the tx
with `chainId` 56 and `value` 0 or price. Run deps with `uv run --with web3`.

## Pitfalls
- **Simulation is the contract.** `eth_call`/`eth_estimateGas` with `from`=wallet
  reproduce the require/custom-error checks; a revert there = the real tx burns gas.
  Always simulate writes first.
- **Gate ≠ supply.** A wallet can pass every eligibility gate (holds the required NFT,
  mint open) and still hit `ExceedsSupply()` because `totalMinted() == MAX_SUPPLY()`.
  Check both before asserting it will work.
- **Custom errors aren't strings.** The revert reason text can come back mangled
  (e.g. `-W:U`); trust the 4-byte selector and decode via openchain, not the message.
- **free-quota tuple order is ambiguous.** A `freeQuota(address)` returning `[1,2,0]`
  may be `[category,limit,used]` or `[category,used,limit]`; confirm which word maps to
  "category → free tier" before asserting free-left = limit - used.
- **Do not shadow the rpc helper with an rpc-url variable in the same script** — name
  the URL `RPC_URL`, not `rpc`, or the `def rpc(...)` gets clobbered.
- **Cloudflare walls block curl on some mint sites.** Static hosts (surge.sh, GitHub
  Pages, Vercel) and their `config.js` / `abi.js` are directly fetchable; grep the HTML
  and linked JS for `0x[0-9a-fA-F]{40}` to recover the contract + gate-registry
  addresses. Client-side `window.CONFIG` / `window.X_ABI` vars hold the ABI; strip the
  `window.X =` prefix and `parse` the array with json.

## references/
- `references/evm-probe-snippets.md` — drop-in Python snippets for selector compute,
  arg encode, eth_call/estimateGas probing, and string/word decoding.
