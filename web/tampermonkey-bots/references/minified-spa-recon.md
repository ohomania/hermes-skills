# Minified SPA recon — find a web app's API from its bundle

Order of operations that reliably surfaces the API of a Vite/React (or similar)
minified app when you cannot run a browser — only `curl` + `grep`/`read_file`.

## 1. Get the real file list
- `curl -sL -A "<desktop UA>" https://site/ -o home.html`
- Read `home.html`: the `<script type="module" src="/assets/main-<hash>.js">` is the
  entry; `<link rel="modulepreload">` lists the static chunks.

## 2. Find the dynamic chunks
- `grep -oE 'import\("\./[^"]*"\)' main.js | sort -u` → the `App-*.js` and view
  chunks. Fetch each. A ~2MB App chunk is normal; view chunks are small. The
  entry `main.js` may itself contain almost no app logic (boot + i18n), so this
  step is where the real code surfaces.

## 3. Locate the API base URL
- `grep -oE '"https?://[^"]*"' *.js | sort -u | grep -vE '(fonts|googleapis|...)'`
  → the server origin (e.g. `https://app-xyz.onrender.com`).
- `grep -oE 'base[Uu]rl[^,;]{0,80}' *.js` to see how it is assigned.

## 4. Enumerate the endpoints
- `grep -oE '"/([a-z][a-z0-9_./-]{1,40})"' *.js | sort -u` → raw path literals.
- `grep -oE '[a-zA-Z_$]+:\(?[^)]*\)?=>_?\("/[^"]*"' *.js` → the API-client method
  map (name → path → method/body). This one grep usually yields the whole surface.

## 5. Recover the auth model
- `grep -oE '.{40}authorization.{80}' *.js` → the `Bearer ${token}` header setup.
- `grep -oE 'new WebSocket|wss?://' *.js` → live/sync channels (separate from REST).

## 6. Recover action schemas
- `grep -oE 'type:"[a-zA-Z]+"' app.js | sort -u` → action discriminators.
- `grep -oE '.{60}<discriminator>.{180}'` → payload field names around each action.
- snake_case constants (`grep -oE '"[a-z_]{3,25}"' | sort -u`) → enum ids
  (job kinds, tier ids, settings keys).

## 7. Verify with curl
- Hit unauthenticated GETs to confirm base URL + shape:
  `curl -s -m 20 "$BASE/features"`, `$BASE/chain/config`, `$BASE/season/board`
  (an auth-gated route returning `{"error":"no session"}` confirms the base is right).
- `curl -s -o /dev/null -w "%{http_code}" "$BASE/assets/main-<hash>.js.map"` → 404
  means no sourcemap, so grep is your only source.

## Display / button labels
- The i18n dictionary is the EN→lang map, so the **EN keys ARE the rendered button
  text**: `"Send crew":"派出团队"` means the EN UI shows "Send crew". Grep the
  translation blob for the verb/title you need (`grep -oE '"[A-Z][a-z]+ [a-z]+":'`)
  to recover exact button labels after the API recon — you cannot click what you
  cannot name, and guessing the label is the #1 cause of a silent dead rule.

## Gotchas
- A `global-<hash>.js` chunk may contain BOTH a vendor SDK (Solana, React) AND the
  app's API client; `grep -c` per file to see which file actually owns the base URL
  and endpoints.
- `.fieldName` hits are frequent false positives inside the i18n dictionary
  (`"hud.cash"` matches a search for `.cash`). Anchor with `[a-zA-Z_$]?.field` and
  cross-check against the localization blobs before trusting state-field names.
- A `403` whose body says `error code: 1010` (Cloudflare-fronted hosts, e.g. Discord's API) is a **browser-signature ban, not an auth rejection** — the token is fine. Python `urllib`/`requests` default UAs and bare `curl` trigger it. Retry with `-A "<desktop UA>"` plus an `Accept: application/json` header before concluding the credential is bad.
