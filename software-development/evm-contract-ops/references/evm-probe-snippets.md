# EVM probe snippets (drop-in, stdlib + pycryptodome)

Run with `uv run --with pycryptodome python probe.py` (system python lacks Crypto).
For full tx building, `uv run --with web3 python mint.py`.

## keccak selector + arg encode
```python
from Crypto.Hash import keccak

def sel(sig):                       # selector = keccak(sig)[:4]
    k = keccak.new(digest_bits=256); k.update(sig.encode())
    return k.hexdigest()[:8]

def enc_addr(a): return "0"*24 + a[2:].lower()
def enc_uint(n): return hex(n)[2:].zfill(64)
```

## jsonrpc helper (works against any EVM RPC)
```python
import json, urllib.request
def rpc(url, method, params):
    req = urllib.request.Request(url,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
        headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())
```

## eth_call a view function / simulate a write
```python
WALLET = "0x..."
CONTRACT = "0x..."
A = enc_addr(WALLET)
# view state (no from)
res = rpc(url, "eth_call", [{"to": CONTRACT, "data": "0x"+sel("mintOpen()")}, "latest"])
# simulate a write (from = wallet) — revert here = real tx reverts
sim = rpc(url, "eth_call", [{"from": WALLET, "to": CONTRACT,
        "data": "0x"+sel("mintFree()"), "value": "0x0"}, "latest"])
est = rpc(url, "eth_estimateGas", [{"from": WALLET, "to": CONTRACT,
        "data": "0x"+sel("mintFree()"), "value": "0x0"}])
```
`sim["result"] == "0x"` => success. `"error"` present => revert (see data selector).

## decode result words / string
```python
def words(h):                      # h = result hex without '0x'
    return [int(h[i:i+64],16) for i in range(0,len(h),64)]
def dstr(h):                       # abi-encoded string
    hh = h[2:]
    if len(hh) < 128: return None
    ln = int(hh[64:128],16)
    return bytes.fromhex(hh[128:128+ln*2]).decode("utf-8","replace")
```

## decode a custom error selector
```
https://api.openchain.xyz/signature-database/v1/lookup?function=0x2d573a55&filter=true
# -> {"name":"ExceedsSupply()"}
```

## extract contract addresses from a mint site's JS config
```bash
curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "https://site.xyz/" \
  | grep -oE '0x[0-9a-fA-F]{40}' | sort -u        # addresses in HTML
# then fetch linked config.js / abi.js for the ABI and contract address
```

## Known-good BSC public RPCs (keyless)
`https://bsc.publicnode.com` (primary) — `https://bsc-dataseed.bnbchain.org`,
`https://bsc-dataseed1.defibit.io` (fallbacks). ankr requires an API key now.
