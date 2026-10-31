# Hosting a headless bot on a cloud Linux box (instabox) + proxy routing

When the user says "run it in instabox" (or any cloud box) for a game bot, port the
userscript to the headless Node script (`references/supabase-game-backend.md`) and
ship it to the box. The headless bot holds only the session token — never a wallet
key — so a box with no wallet is fine; the "don't reach for a cloud VM" rule is
about *browsers* that must sign wallets, not this.

## The box CLI is two layers — proxy each

instabox (like most npm-bootstrap CLIs) is a Node shim that onboards, then delegates
to a compiled binary. They speak different proxy dialects:

- **Node bootstrap layer** (the `npx` → `bin/*.mjs` entry) uses global `fetch`
  (undici), which ignores `HTTPS_PROXY` unless `NODE_USE_ENV_PROXY=1` is set. Set
  `HTTPS_PROXY`/`HTTP_PROXY` **and** `NODE_USE_ENV_PROXY=1`.
- **Compiled Go binary** (found by the shim's `findCli()`, e.g.
  `%LOCALAPPDATA%\Programs\instabox\instabox.exe`) honors
  `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY` natively via Go `net/http`.
- Signal it's working: an `[UNDICI-EHPA] EnvHttpProxyAgent is experimental` warning
  printed on every `instabox` call is the proof the env proxy agent took effect.

## Two paths, proxied separately

1. **CLI → API** (`api.instabox.sh`, HTTPS): the env vars above; persist in `~/.bashrc`.
2. **SSH** (`ssh.instabox.sh:2222`): the CLI spawns system `ssh`, so add a
   `ProxyCommand` under `~/.ssh/config`, keyed to the box's real HostName (read it
   from `instabox ssh-config <name>`). Use the git-bash `connect.exe` helper:
   - HTTP CONNECT: `ProxyCommand connect -H proxyhost:port %h %p`
   - SOCKS5: `ProxyCommand connect -S proxyhost:port %h %p`
   auth via env `CONNECT_USER`/`CONNECT_PASSWORD` (or `SOCKS5_USER`/`SOCKS5_PASSWORD`).
   Use the FULL `connect.exe` path (e.g.
   `C:/Users/<u>/AppData/Local/hermes/git/mingw64/bin/connect.exe`) so the block also
   works under Windows OpenSSH, not just git-bash.

## Verify the route applies (dead-proxy control)

"It connected" proves nothing — the CLI may have gone direct. Point the ProxyCommand
at a dead proxy (`connect -H 127.0.0.1:1 %h %p`), run `instabox ssh <name> -- echo ok`
and expect `Unable to connect to relay host` (failure), then restore. For the API
path the undici warning above is sufficient evidence.

## Deploy + run

- Lay out the bot folder locally (headless.js + config.js + sim.js + session.json),
  `node --check headless.js`, then `instabox push <box> rlbot --all` → lands in
  `/data/home/rlbot`.
- **Dry-run BEFORE asking for the token**: `instabox exec <box> -- 'cd rlbot && node headless.js'`
  should print `FATAL: session.json missing token`. That proves `config.js` (eval'd)
  and `sim.js` (UMD `require`) loaded clean on the box — token is the only blocker.
- Load `config.js` in Node by eval, don't re-type the anonKey:
  `new Function('window', configSrc + ';return window;')(w)` gives `w.SIEGE_SUPABASE`.
  (The anonKey is a JWT — re-typing is error-prone and it may be redacted in tool
  display; move the file and eval it instead.)
- Run detached: `instabox exec --background <box> -- 'cd rlbot && node headless.js > bot.log 2>&1'`,
  then poll `instabox jobs logs <box>` / `instabox exec <box> -- 'tail rlbot/bot.log'`.

## Free-tier reality

Free cloud boxes auto-pause (~30 min idle) and cap runtime (~480 min); a bot polling
every ~10 s is "little CPU" and may still be treated as idle. Say it is not true
24/7; resume with `instabox wake <box>`.
