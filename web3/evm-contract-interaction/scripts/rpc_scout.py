#!/usr/bin/env python
"""Generic read-only EVM contract scout.

Dumps identity + common supply/mint view state for a contract, and the
wallet's balance/quota rows. Reads only — never sends a tx.

usage:  uv run --with pycryptodome python rpc_scout.py <contract> [wallet] [rpc]
"""
import json, sys, urllib.request
from Crypto.Hash import keccak


def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return "0x" + k.hexdigest()[:8]


def duint(h):
    return int(h, 16) if h else None


def dstr(h):
    if not h:
        return None
    hh = h[2:]
    if len(hh) < 128:
        return None
    ln = int(hh[64:128], 16)
    try:
        return bytes.fromhex(hh[128:128 + ln * 2]).decode("utf-8", "replace")
    except Exception:
        return None


def words(h):
    hh = (h or "")[2:]
    return [int(hh[i:i + 64], 16) for i in range(0, len(hh), 64)]


def main():
    if len(sys.argv) < 2:
        print("usage: python rpc_scout.py <contract> [wallet] [rpc]")
        sys.exit(1)
    contract = sys.argv[1]
    wallet = sys.argv[2] if len(sys.argv) > 2 else None
    rpc = sys.argv[3] if len(sys.argv) > 3 else "https://bsc.publicnode.com"

    def call(method, params):
        req = urllib.request.Request(
            rpc,
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())

    def eth_call(sig, args=""):
        res = call("eth_call", [{"to": contract, "data": sel(sig) + args}, "latest"])
        return res.get("result")

    code = call("eth_getCode", [contract, "latest"])["result"]
    print("contract   :", contract)
    print("code bytes :", len(code) // 2 - 1)
    print("name/symbol:", dstr(eth_call("name()")), "/", dstr(eth_call("symbol()")))
    for sig in ["totalSupply()", "MAX_SUPPLY()", "maxSupply()", "mintOpen()", "totalMinted()", "price()", "MAX_PER_WALLET()"]:
        print(f"  {sig:22s} = {duint(eth_call(sig))}")
    if wallet:
        a = "0" * 24 + wallet[2:].lower()
        for sig in ["balanceOf(address)", "mintedBy(address)", "freeUsed(address)"]:
            print(f"  {sig}(wallet) = {duint(eth_call(sig, a))}  words {words(eth_call(sig, a))}")


if __name__ == "__main__":
    main()
