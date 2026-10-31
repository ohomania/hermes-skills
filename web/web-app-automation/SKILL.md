---
name: web-app-automation
description: Use when the user wants a bot or automation for a web app.
---

# Web App Automation (reverse-engineer → bot)

Turn "make a bot for this site/game" into a working headless client. The landing-page
copy lies; the client-side JS bundle is the truth. Recon first, then build only what the
real API actually supports — and say so honestly when it does not.

## Procedure

1. **Fetch the page when extracted markdown is empty.** `curl -sSL -A "Mozilla/5.0" <url>`
   returns the real HTML. Identify the stack — Next.js/Vercel (per `X-Vercel-*` /
   `/_next/static/immutable/chunks/*.js`) means the logic lives in minified JS chunks
   referenced in the HTML, not in the SSR text.
2. **Download the JS chunks and grep them** (concrete regexes in `references/recon-patterns.md`)
   for: API endpoints (`/api/...`, `fetch(`), hostnames (`https://...` → Supabase/RPC/chain),
   localStorage keys (the real persistence), and the state shape (the `useState(...)`
   initializer object is the schema).
3. **Extract the auth flow before building.** Wallet apps use nonce/verify: `POST
   /api/auth/nonce {address}` → sign the returned `message` raw bytes → `POST
   /api/auth/verify {address, nonce, signature}` → session cookie. For headless
   Solana-style auth use Node's built-in ed25519 — no external deps.
4. **Decide client-authoritative vs server-validated BEFORE designing the bot.** POST a
   fabricated state blob, then GET it back. Echoed unchanged = you can farm/set directly;
   rejected or transformed = you must simulate real play.
5. **Verify the persistence endpoint returns 200 early.** A 500 (not 401) on an authed call
   means the handler itself errors — the backend is half-wired and there is nothing to farm
   server-side. Stop, report that, and pivot (localStorage edit, browser automation, or wait).

## Pitfalls

- **Page copy lies about architecture** — the site claimed "prototype, saved in browser only"
  while a full Supabase backend + wallet auth existed. Trust the `fetch` targets and
  localStorage keys, never the marketing text.
- **Minified bundles are one giant line** — grep with context for the symbol/pattern, never
  `read_file` the whole chunk; it floods context with one ~100k-char line.
- **Node ed25519 has no direct raw-pubkey export** — `publicKey.export({format:'jwk'}).x` is
  the raw 32 bytes (base64url), which you base58 into the address; sign with
  `sign(null, Buffer.from(msg,'utf8'), createPrivateKey(pem))`.
- **Recurring job on Windows when Hermes cron needs a gateway that isn't running** — use
  `schtasks /Create /SC HOURLY /MO 1 /TR "C:\path\run.bat"`. Three traps: (1) the task runs
  with CWD `C:\Windows\System32`, so any relative path in the child (e.g. a cache dir) hits
  EPERM — pass absolute paths and set `cwd` in spawn; (2) "interactive only" tasks silently
  skip while the machine sleeps/locks — log gaps are the tell, not a crash; (3) a bare
  `fetch()` with no timeout hangs a scheduled run forever — add `AbortSignal.timeout(N)`.

- **Real-time 3D "game" (three.js/WebGL) is closure-locked, not React-locked.** The scene,
  player position, and voxel/terrain map live in a minified module closure — traversing the
  React fiber tree (or `window`) surfaces no three.js objects because they were never attached
  to either. Without a vision model to read the screen, blind WASD+dig input cannot travel from
  spawn to the goal, so a true auto-play farm is infeasible. The correct fallback is a
  localStorage save-editor: write the same keys the game loads at startup (valid when its server
  persistence is broken/ignored), producing the "already played" result with zero navigation.
  Deliver it as a save-editor and say so — do not dress it up as auto-play, and skip it only when
  the economy is genuinely server-authoritative (the user's standing rule).

## Outcome

Deliver the working artifact (key files + authed client) AND the honest finding, even when
the finding is "the backend is broken, so server-side automation is not possible yet." A
working auth client with a documented blocker is a real deliverable, not a failure.
