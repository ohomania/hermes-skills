# Enumerate wallet holdings + price them (BSC)

## 1. Full inventory from tx-history

Run `baw` via the direct node entry (see SKILL.md Windows/MSYS note), then parse the JSON. `tokenId` present → NFT; `tokenId` null → fungible token/BNB.

```python
import json, os, subprocess
node_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("HOME")
BAW = node_dir + "/hermes/node/node_modules/@binance/agentic-wallet/dist/index.js"
r = subprocess.run(["node", BAW, "wallet", "tx-history", "--binanceChainId", "56", "--json"],
                   capture_output=True, text=True, timeout=120)
data = json.loads(r.stdout[r.stdout.find("{"):])
txs = data["data"]["transactions"]

nfts_in, tokens_in, nfts_out = {}, {}, {}
for t in txs:
    for h in t.get("txHashList", []):
        ins = h.get("instructions", {})
        for r in ins.get("receive", []):
            ti = r.get("tokenInfo", {}); tok = ti.get("tokenId")
            k = (ti.get("contractAddress"), ti.get("symbol"))
            if tok is not None:
                key = (k[0], k[1], str(tok)); nfts_in[key] = nfts_in.get(key, 0) + 1
            else:
                tokens_in[k] = tokens_in.get(k, 0.0) + float(r.get("amount") or 0)
```

`receive` vs `send` tells you what is still held vs moved. Pull out `approve` entries too and flag them — read back the approval (spender + token) before reporting the wallet is clean.

## 2. Identify unknown contracts

- `name()` `0x06fdde03`, `symbol()` `0x95d89b41`, `decimals()` `0x313ce567`.
- Revert on both → likely ERC-1155 (`balanceOf(address,uint256)` `0x00fdd58e`, `uri(uint256)` `0x0e89341c`) or a proxy (read implementation: EIP-1967 slot `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`, or a custom slot extracted from the leading PUSH32 in bytecode).

## 3. Price tokens (PancakeSwap v2)

factory `0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73` · `getPair` `0xe6a43905` · `getReserves` `0x0902f1ac` · `token0` `0x0dfe1681`.

- `pair == 0` → no market.
- `pair != 0` but reserves `(0, 0)` → EMPTY pool = $0 (do not price).
- else price per unit = `reserve_ref / reserve_tok` (both 18-decimals assumed; scale if not).

## 4. Honest value framing

Most agent-native free-mint NFTs are soulbound proofs or pre-liquidity — report "$0 / speculative" up front. Only give a USD figure when a real liquidity pool or a market floor exists (e.g. AnthroBit common floor ~0.0014 BNB).