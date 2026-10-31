# BNB Smart Chain (chain 56) endpoints & explorers

## RPC (known-good, no key)
- `https://bsc.publicnode.com` — reliable primary.
- `https://bsc-dataseed.binance.org/` / `https://bsc-dataseed1.binance.org/` — fallbacks.
- `https://rpc.ankr.com/bsc` — **requires a free API key now** (`Unauthorized: authenticate your request`); don't hit it keyless.

Use a `User-Agent` header on raw `eth_call` POSTs or the node may reject/rate-limit. Confirm chain identity first: `eth_chainId` must be `0x38` (56).

## Block explorer caveats
- **BscScan `getabi` API requires an API key** — keyless calls now return HTML/redirect, not JSON. Prefer fetching the project's own `config.js`/`abi.js` from its site.
- BscScan web pages sit behind Cloudflare; direct curl of a contract page often times out. Use on-chain `eth_call` for state instead of scraping the explorer UI.

## Cloudflare bot-walls on mint sites
Many agent-native mint pages are Cloudflare-challenged ("One moment, please…"). If the HTML/JS is walled:
- Hit the static assets directly — `config.js`, `abi.js`, or a versioned `app.js?v=N` are often served without the challenge, and they carry the contract address + real ABI + exact calldata.
- `grep -oE '0x[0-9a-fA-F]{40}'` across the JS to pull addresses; `grep` for `ethers.id(...)`, `encodeFunctionData(...)`, or hardcoded 8-hex selectors to get the function.
- When only a truncated address is visible (`0x7038…c837`), ask the user for the full address — don't brute-guess.

## Shared gate address
Agent-gated BNB NFTs share one `.ai Agent ID` registry ("SPACE ID Agent ID"). If several projects show the same extra address in their config, that's the gate — check `balanceOf(wallet)` there once.
