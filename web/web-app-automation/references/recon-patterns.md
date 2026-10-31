# Recon patterns for a web-app client bundle

Run these over the downloaded JS chunks (concatenate the chunk files first if convenient).
Order matters: endpoints → hosts → persistence → state shape.

## API endpoints

```python
re.findall(r'["\'`](/(?:api|v\d|mint|auth|login|me|status|claim|quest)[^"\'`]*?)["\'`]', js)
```
This is broader than it looks — the `api` alternative catches `/api/*`; the rest catch versioned
(`/v1/...`), mint, auth, and wallet-ish routes that don't start with `api`. De-dupe and sort.

## Hostnames / backends

```python
re.findall(r'https?://[^"\'`\s]{8,80}', js)
```
Reveals the real backend (Supabase project URL, RPC endpoints), CDNs (Cloudflare Turnstile =
anti-bot), and chain RPCs (e.g. `bsc-dataseed.*` = Binance Smart Chain) — even when the page
says it's "off-chain / no tokens".

## Persistence

```python
re.findall(r'localStorage\.(?:getItem|setItem|removeItem)\(\s*["\'`]([^"\'`]+)', js)
```
Also grep for template keys (`localStorage.setItem(prefix + ...` ) — those use a prefix variable
(e.g. `eP`) so the literal-key regex misses them. `sessionStorage`/`indexedDB` appear as separate
bare words — grep their count to know whether those backends are used at all.

## State shape

Find the `useState(...)` initializer — that object literal is the player/state schema. Grep for
likely field names and print with context (the bundle is one long line):

```python
re.finditer(r'\b(coins|brick|bag|studs|quest|depth|combo|gold|car|owner|placed|total|wall)\s*:', js)
```

## Rules

- Minified bundles are one line — always regex/grep with context, never full-file read.
- `curl -sSL -A "Mozilla/5.0" <chunk-url>` works to download; on Windows, passing `-o` a
  forward-slash (`/c/...`) path fails with `curl: (23) write error` — use a native `C:/...` path
  or download via Python `urllib`.
