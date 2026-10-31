# EVM selectors & calldata

## Compute (never hardcode a selector blindly)
```bash
uv run --with pycryptodome python -c "from Crypto.Hash import keccak; k=keccak.new(digest_bits=256); k.update(b'safeTransferFrom(address,address,uint256)'); print(k.hexdigest()[:8])"
```

## Encoding helpers
```python
def encAddr(a): return '0'*24 + a[2:].lower()   # 32-byte address
def encUint(n): return hex(n)[2:].zfill(64)     # 32-byte uint
calldata = '0x' + selector + encAddr(...) + encUint(...)
```

## Common selectors (verified in the field)
| function | selector |
|---|---|
| name() | 0x06fdde03 |
| symbol() | 0x95d89b41 |
| totalSupply() | 0x18160ddd |
| totalMinted() | 0xa2309ff8 |
| mintOpen() | 0x24bbd049 |
| balanceOf(address) | 0x70a08231 |
| balanceOf(address,uint256) [ERC-1155] | 0x00fdd58e |
| ownerOf(uint256) | 0x6352211e |
| tokenOfOwnerByIndex(address,uint256) | 0x2f745c59 |
| approve(address,uint256) | 0x095ea7b3 |
| getApproved(uint256) | 0x081812fc |
| safeTransferFrom(address,address,uint256) | 0x42842e0e |
| mint() | 0x1249c58b |
| mint(uint256) | 0xa0712d68 |
| mintedBy(address) | 0x3cef28d2 |
| quote(address,uint256) | 0x8f79306e |
| revealed() | 0x51830227 |

`Transfer` event topic0 = `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` — for ERC-721, `topics[3]` is the tokenId.

## Decoding a string return (name/symbol)
ABI dynamic-string layout: 32-byte offset word, then a 32-byte length, then the UTF-8 bytes.

## Finding an unknown project's ABI
Grep the site's inline JS / llms.txt / agent.json for a `SEL = { name: "0x…" }` selector map or `"function <name>(...)"` ABI strings — this beats guessing selectors. curl with a browser `User-Agent`; `web_extract` often fails on these bot-walled static sites.
