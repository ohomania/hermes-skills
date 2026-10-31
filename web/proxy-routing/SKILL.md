---
name: proxy-routing
description: Use when routing a CLI, API, or SSH through a proxy.
---

# Routing a tool through a proxy

Send a tool's API traffic and/or SSH through an HTTP/SOCKS proxy (e.g. a
residential proxy) by reusing the tool's own env vars and SSH config — never by
patching the tool.

## Procedure

1. **Identify the runtime — it decides the mechanism.** `file <bin>` plus
   `head -c 4000 <bin> | grep -a 'Go build ID'`:
   - Compiled Go/Rust binaries and curl honor `HTTPS_PROXY`/`HTTP_PROXY` natively.
   - Node's global `fetch` (undici) does NOT read proxy env vars by default: also
     set `NODE_USE_ENV_PROXY=1` (enables EnvHttpProxyAgent; its `[UNDICI-EHPA]
     experimental` warning is proof the proxy IS being used).

2. **Set the env vars** — persist in `~/.bashrc` so new shells inherit:
   ```
   export HTTPS_PROXY="http://user:pass@host:port"
   export HTTP_PROXY="$HTTPS_PROXY"
   export NO_PROXY="localhost,127.0.0.1"
   ```

3. **SSH goes through `ProxyCommand`, not env vars.** In `~/.ssh/config`:
   ```
   Host <destination-host>
       ProxyCommand C:/path/to/connect.exe -H proxyhost:port %h %p
   ```
   - `connect` (mingw64) tunnels via HTTP CONNECT (`-H`) or SOCKS5 (`-S`).
   - Auth: `connect` reads `CONNECT_USER`/`CONNECT_PASSWORD` (HTTP) or
     `SOCKS5_USER`/`SOCKS5_PASSWORD` (SOCKS) from the environment — export them
     alongside the URL vars. `-H` takes no inline user; `-S [user@]host` does.
   - Use the FULL Windows path to `connect.exe` so both git-bash ssh (`sh -c`)
     and Windows OpenSSH (`cmd`) can resolve it.

4. **Prove it actually routes — dead-proxy control.** A happy connection is NOT
   proof the proxy was used. Point the ProxyCommand at `127.0.0.1:1` and re-run:
   it must fail (`Unable to connect to relay host`). If it still succeeds the tool
   bypasses your config; never claim "proxied" without this check.

## Pitfalls

- **Node ignores proxy env silently.** A Node tool "works" but egresses directly
  if `NODE_USE_ENV_PROXY` is unset. Set it and watch for the EnvHttpProxyAgent
  warning as confirmation.
- **Rotating residential = a new IP per connection.** A one-off `closed by remote
  host` / broken pipe is a bad IP; retry recovers. For a long-lived SSH session
  use a sticky session (append session/time tokens to the username) where the
  provider supports it.
- **Read creds from the provider API, not the dashboard DOM.** Dashboards are JS
  SPAs that yield nothing to curl; the provider usually has a Bearer-token API
  returning `username/password/host/protocols` (see `references/novaproxy.md`).
