# Selectors & return decoding

Compute a 4-byte selector from a signature (keccak256, first 4 bytes):

```bash
uv run --with pycryptodome python -c "from Crypto.Hash import keccak; k=keccak.new(digest_bits=256); k.update(b'MINT_SIG'); print('0x'+k.hexdigest()[:8])"
```

A signature maps to the same selector on every EVM contract, so these well-known ones are stable:

| signature | selector |
|---|---|
| `name()` | `0x06fdde03` |
| `symbol()` | `0x95d89b41` |
| `balanceOf(address)` | `0x70a08231` |
| `totalSupply()` | `0x18160ddd` |
| `MAX_SUPPLY()` | `0x32cb6b0c` |
| `maxSupply()` | `0xd5abeb01` |
| `mintOpen()` | `0x24bbd049` |
| `totalMinted()` | `0xa2309ff8` |
| `mintedBy(address)` | `0x3cef28d2` |
| `price()` | `0xa035b1fe` |
| `mint(uint256)` | `0xa0712d68` |
| `mint()` | `0x1249c58b` |
| `freeMint()` | `0x5b70ea9f` |
| `MAX_PER_WALLET()` | `0x0f2cdd6c` |
| `quote(address,uint256)` | `0x8f79306e` |
| `owner()` | `0x8da5cb5b` |

## Return decoding (raw hex from `eth_call`)
- **bool**: `int(hex,16) != 0`
- **uint256**: `int(hex,16)`
- **string**: first word = offset (`0x20`), second word = length, rest = UTF-8 bytes.
- **tuple / multiple returns**: strip `0x`, split into 32-byte (64-char) words, each an int.

`freeQuota(address)`-style returns (e.g. `[category, limit, used]`) come back as 3 words — read them all, don't assume the order matches the docs; cross-check against the project's stated tiers (limit 2 vs 5 vs category).

## Decoding a custom error / revert
Nodes truncate/mangle revert strings ("reverted: -W:U"). Trust the `data` field, not the message: it's the 4-byte custom-error selector. Look it up:

```
GET https://api.openchain.xyz/signature-database/v1/lookup?function=0x2d573a55&filter=true
```

`{"ok":true, ... "0x2d573a55":[{"name":"ExceedsSupply()"}]}` ⇒ the mint reverts because the collection is sold out, not because of the wallet.
