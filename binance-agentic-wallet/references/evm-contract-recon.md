# EVM contract recon (read-only, before any write)

## RPC

- Public BSC RPCs: `https://bsc.publicnode.com` and `https://bsc-dataseed.binance.org/`. Keep both — publicnode sometimes 403s on `eth_getTransactionReceipt` ("archive requests require a personal token"); use dataseed for receipts.
- Plain JSON-RPC over `urllib` (stdlib) is enough; always send a `User-Agent` header.

## Identify a contract

- `eth_getCode` — empty/near-empty means EOA, not a contract.
- `name()` `0x06fdde03`, `symbol()` `0x95d89b41`, `totalSupply()` `0x18160ddd`, `mintOpen()` `0x24bbd049`, `totalMinted()` `0xa2309ff8`, `MAX_SUPPLY()` `0x32cb6b0c`.
- String returns are ABI-encoded dynamic types: decode via offset (word 0) + length + bytes.
- A contract that REVERTS on all standard ERC20/721 views is something else (marketplace / redeem / vault) — pull its selector table to find out what it is.

## Selector math

- `keccak256(signature)[:4]` via `pycryptodome` (`Crypto.Hash.keccak.new(digest_bits=256)`).
- Encode args: address = 24 zero bytes + lowercase 20-byte address (strip `0x`); uint256 = 64-hex, zero-padded.
- Prefer the project's own `llms.txt` / `agent.json` / site JS for exact signatures + selectors — these files are written for agents and usually carry them verbatim.

## Extract a contract's function table

- `eth_getCode`, then regex `63([0-9a-f]{8})` for PUSH4 selectors (ignore the `63ffffffff` mask AND 4-byte ASCII-word false positives — Solidity strings/error literals like `0x616c6c20` ("all ") land in the code and look like selectors).
- Look up unknowns on openchain.xyz: `https://api.openchain.xyz/signature-database/v1/lookup?function=0x…&filter=true` (also `event=`).

## Resolve a proxy BEFORE pulling the function table

- Vaults / reward / claim contracts are usually PROXIES: their own bytecode shows only a thin dispatch (a handful of selectors like `implementation()` `0x5c60da1b`, `owner()` `0x8da5cb5b`, panic `0x4e487b71`) and NO business functions. Pulling selectors from the proxy is a dead end — resolve the implementation and extract ITS table instead.
- EIP-1967 transparent/UUPS: implementation lives at `eth_getStorageAt` slot `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`. If that slot is `0x……0000`, it is a BEACON proxy.
- Beacon proxy: the beacon address lives at slot `0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50`; `eth_getStorageAt` it, then `eth_call` `implementation()` (`0x5c60da1b`) ON THE BEACON (not the vault) to get the real implementation.
- Simulate / write against the PROXY (vault) address, not the implementation — the proxy holds the storage the write must touch.

## Decode a custom revert

- A revert whose `data` is a 4-byte value is a custom-error selector. Look it up on openchain (function lookup). Example: `0x2d573a55` = `ExceedsSupply()`.
- Simulate writes with `eth_call` (`{from, to, data, value}`) to see success/revert before spending gas.

## Sold-out & quota checks

- `mintOpen() == true` and `quote()==0` are NOT enough — also confirm `totalMinted() < MAX_SUPPLY()`.
- `quote(addr, qty)` returns the exact amount due; `0` = free. Re-check it right before minting (free phases end, quota gets consumed).
