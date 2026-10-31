#!/usr/bin/env python3
"""Probe a stdio MCP server without a host application: initialize + tools/list.

Usage:
  python mcp_probe.py -- node /path/to/server.mjs mcp
  python mcp_probe.py --json -- npx -y some-mcp-server
  python mcp_probe.py --count-only --timeout 30 -- python -m my_mcp

Exit 0 = handshake ok and a non-empty tool list came back.
Stdlib only, so it runs in any venv.
"""
import argparse
import json
import queue
import subprocess
import sys
import threading

PROTOCOL = "2025-06-18"


def reader(pipe, q):
    try:
        for line in pipe:
            q.put(line)
    finally:
        q.put(None)


def next_json(q, timeout):
    """Next JSON-RPC object from stdout, skipping log lines the server prints."""
    while True:
        try:
            line = q.get(timeout=timeout)
        except queue.Empty:
            raise SystemExit("timeout waiting for a JSON-RPC reply")
        if line is None:
            raise SystemExit("server closed stdout before replying")
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except ValueError:
            continue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--json", action="store_true", help="print a JSON summary")
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--tools", type=int, default=10, help="how many tool names to show")
    ap.add_argument("cmd", nargs=argparse.REMAINDER,
                    help="server command, after --")
    args = ap.parse_args()
    cmd = [c for c in args.cmd if c != "--"]
    if not cmd:
        raise SystemExit("give the server command after --, e.g. -- node server.mjs mcp")

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8",
                            errors="replace", bufsize=1)
    q = queue.Queue()
    threading.Thread(target=reader, args=(proc.stdout, q), daemon=True).start()

    def send(obj):
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                         "clientInfo": {"name": "mcp_probe", "version": "1.0"}}})
        init = next_json(q, args.timeout)
        if "error" in init:
            raise SystemExit("initialize failed: %s" % init["error"])
        send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = next_json(q, args.timeout)
        if "error" in listed:
            raise SystemExit("tools/list failed: %s" % listed["error"])
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass

    result = init.get("result", {})
    info = result.get("serverInfo", {})
    tools = listed.get("result", {}).get("tools", [])

    if args.json:
        print(json.dumps({"serverInfo": info,
                          "protocolVersion": result.get("protocolVersion"),
                          "toolCount": len(tools),
                          "tools": [t.get("name") for t in tools]}, indent=1))
        return 0 if tools else 1

    print("server   : %s %s" % (info.get("name", "?"), info.get("version", "?")))
    print("protocol : %s" % result.get("protocolVersion"))
    print("tools    : %d" % len(tools))
    if not args.count_only:
        for t in tools[:args.tools]:
            desc = (t.get("description") or "").replace("\n", " ")
            print("  - %-38s %s" % (t.get("name"), desc[:70]))
    if not tools:
        print("RESULT   : FAIL (handshake ok, no tools listed)")
        return 1
    print("RESULT   : PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
