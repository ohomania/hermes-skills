---
name: tampermonkey-bots
description: Build Tampermonkey/userscript bots for web apps & games.
---

# Tampermonkey / userscript bots for web apps & games

Build a bot that drives a site the user is already logged into by **reusing the
app's own session** — never by reimplementing login, OAuth, or wallet signing.
The winning pattern: reverse-engineer the minified bundle to find the API
surface, wrap `window.fetch` to harvest the session, then act through the real
UI or the app's own endpoints.

## Procedure

1. **Recon the bundle.** Find the API base URL, every endpoint, the auth header,
   and the action schemas. Full grep/curl recipe lives in
 `references/minified-spa-recon.md`. Do this before writing any bot code — it
 tells you whether the bot can ride a session or must reimplement auth. Supabase-backed
 games (PostgREST RPC + localStorage JWT + a bundled `window.Sim`) have their own
 playbook: `references/supabase-game-backend.md`. Per-game recon you've already done lives in `references/` (e.g. `cozygolem.md`, `raidlords*.md`) — check there before re-reversing the same game.

2. **Model the session.** The app already holds its token (a `Bearer` header set
   in its fetch wrapper, or a cookie). Do not rebuild auth. Instead harvest the
   token by wrapping `window.fetch` and copying the `authorization` header off
   the app's own requests — it appears on the first request after login.

3. **Wrap fetch to capture + mirror.** Save
   `const origFetch = window.fetch.bind(window)` *before* wrapping. In the
   wrapper: read `authorization` from `init.headers` (handle both `Headers` and
   plain-object forms), extract the wallet/user id from the URL `?wallet=` or the
   JSON body, and mirror state reads with `res.clone().json().then(...)` so the
   app's own response is never consumed.

4. **Act through the right channel.** State-mutating actions with complex schemas
   (pick crew → send job) are safest driven through the *real DOM* — click the
   actual buttons so the app's own validation applies. Simple idempotent calls
   (e.g. claim a reward) can go straight through the recycled token + `origFetch`.
   Log every intercepted action request body into a `learnedActions` list so the
   exact schema is documented for later replay.

5. **Ship demo-safe defaults.** Automated send/withdraw/spend actions default OFF
   with an on-screen HUD (toggles + log + a "dump state" button). Enable them
   only after the user confirms the bot sees the session and one manual cycle
   works. Night-gated or time-limited actions (and timeout/gap throttles) should
   be conservative by default.

6. **Verify before delivering.** `node --check file.user.js` — the userscript
   metadata header is a comment, so the body parses as plain JS. Deliver both the
   `.user.js` file (via `MEDIA:` path) and the full source inline for copy-paste.

## HUD & UX (user preferences — apply every time)

- Ship a **foldable, draggable HUD** — a small floating pill (bottom-right) that
  toggles a panel. Collapsing is an explicit requirement, not a nice-to-have.
- Use **boxed ON/OFF toggle switches, never raw checkboxes** — the user rejected
  checkboxes explicitly. Give a **master ON/OFF** plus a per-rule switch, each
  showing ON/OFF text and persisting to localStorage. **ONE master switch only** — a
  second master-level toggle (e.g. a feature switch AND a "Master" for aux rules) that
  both fuel the RUNNING badge is interchangeable to a non-technical user: they flip the
  wrong one and report "no funciona" while the badge glows RUNNING. Make the RUNNING badge
  reflect the primary loop's switch; auxiliary actions stay per-rule.
- Make it **visibly alive**: RUNNING/STOPPED, count of detected (non-disabled)
  DOM buttons, total clicks, last action + time, and a log. A silent bot reads as
  broken ("gak jalan") even when scanning correctly.
- **Scan-first when the UI is gated** (wallet/session hides the real labels): ship
  a "Scan" button that dumps every unique visible button text to console, and act
  through configurable text-matcher rules (default OFF). Log a
  `rule ON tapi tombol tidak ketemu` warning once/minute so a dead rule is
  diagnosable rather than silent.
- Scroll the panel correctly — `references/userscript-hud.md` has the
  flex-min-height:0 rule and the log auto-follow pattern.
- Read a user-sent screenshot's text (button labels, status lines) with
  `scripts/ocr-screenshot.ps1` (Windows `Windows.Media.Ocr`, no vision needed):
  `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ocr-screenshot.ps1 -Path <img> -Scale 3`.
  The optional `-Scale 2..4` upscales a sparse shot first (recovers small button text). This is
  the fallback when the chat model can't open images directly.
- **When you can't read the screen, make the BOT emit text — don't loop on screenshots.**
  Chat screenshots arrive thumbnailized (often <500px wide) so OCR is useless and a no-vision
  model can't read them at all. Give the bot's Scan/dump button a
  `navigator.clipboard.writeText(...)` of the button-label list so the user pastes (Ctrl+V) TEXT
  into chat — text is always readable, a tiny screenshot is not. Prefer this over re-asking for
  "a screenshot of the run screen" after the first one was unreadable.
- Explain in **Bahasa Indonesia, casual**; when the game has an economy, pair the
  bot with a ranked "cara earn paling enak" strategy note.

- **Clean-minimal visuals by default.** Flat dark, one accent color, rounded
  corners, no neon/glassmorphism/glow overload — plain reads "jelek" but a flashy
  gradient-glow redesign also got rejected as too much ("simpel tapi bagus"). Aim
  for a tidy single-accent panel.

- **Treat Scan / dump-state buttons as temporary scaffolding.** Once rules are
  wired they read as clutter and the user will ask to remove them. Surface
  captured state / learned-actions in the scrollable log rather than a
  console-only dump, so there's no pressure to keep a separate button.

## Pitfalls

- **One Vite chunk can hold a vendor lib AND the app's API client.** The ES
  `export{...}` names may be all SDK symbols (a Solana/React bundle) while the
  API base URL and endpoint methods live alongside them, never exported. Locate
  code with `grep -c '<baseurl-or-endpoint-literal>'` per file; don't infer the
  API is absent from the export names.

- **The entry chunk is often just a boot shell** (wallet adapter + i18n + a
  `dynamic import("./App-*.js")`). Grep for `import("...")` and follow it to the
  real app chunk before concluding actions/endpoints are "unreferenced".

- **Minified bundles keep string literals.** Action discriminators
  (`type:"assignJob"`), snake_case ids (`car_theft`, `tierId`) and endpoint paths
  survive minification even though every local variable is single-letter. Grep
  for literals, not variable names.

- **Read responses with `res.clone()`, never the original** — consuming the real
  body breaks the app's own `await fetch(...).json()` and stalls the page.

- **Recycle the session; don't reimplement signing.** For crypto/browser games the
  wallet is gated (min-balance + a one-time connect/accept-terms step). That part
  stays manual; the bot rides the resulting session afterward.

- **A localStorage dump pasted into chat is NOT a durable session.** The chat/file channel truncates long values (the world-save blob) and redacts secrets (the Supabase `refresh_token`), so a pasted session logs in but its access token expires in under an hour, cannot refresh, and the full save never arrives. Re-enter with a pasted session only for a quick look at the UI; for anything long-running, ride the user's live browser or have them write the keys to a FILE on disk (untruncated, unredacted) rather than pasting into chat.

- **Local-save editing is either a cheat or the only correct pivot — decide which first.** Two
  opposite cases share the "I just edited the save file" surface but take opposite conclusions:
  (1) SERVER-authoritative — currency/gear/levels live on the server and income is gated by
  real elapsed time (the game's own docs usually say so): editing a local save risks a ban and
  produces nothing, so automate legit clicks only and say so plainly, rather than
  over-promising an earnings boost the account review will catch. (2) CLIENT-only / broken
  server — the progress/blob endpoint 500s or is absent and the game says "saved in this
  browser only": localStorage IS the only persistence, so a save-editor writing the app's own
  keys is legitimate and correct, not a cheat (see web-app-automation for the recon that tells
  the two apart). In the SERVER case, the one legal carve-out is a game that ships a
  DETERMINISTIC sim as a `window` global AND replays it server-side — simulate candidate
  actions and submit the best `{battle_id, log, hash}` (see
  `references/supabase-game-backend.md`).

- **A headless auto-attack reads as broken even when it works.** The
  deterministic-sim submit path (`find target → submit {battle_id, log, hash}`)
  leaves the village idle on screen, so the user reports "gak jalan" despite
  correct results. Default game bots to the VISIBLE path: drive the game's own
  live battle — call its global attack-loader function, assign its per-tick
  deploy `script` slot, and let its own `finishBattle` auto-submit — so the
  player watches troops deploy and the result roll in. Keep headless as an
  explicit off-toggle for unattended 24/7 runs (see
  `references/supabase-game-backend.md`).

- **For a Supabase/wallet game, don't route bot actions through the app's own
  `rpc()` helper — call the raw PostgREST fetch.** The helper pops a blocking
  "complete with tokens?" dialog and retries with an `x-fill` header when you're
  short; the raw path throws a clean error, so the bot skips instead of silently
  spending tokens mid-loop.

- **Special deploy units (`cc`/clan-castle) need both slot AND roster.** Add
  `cc` to a candidate log only when `army.cc > 0` and the roster has troops,
  else the deterministic replay returns `'none left'` and a sim-based attack
  whose candidates all fail on it skips forever.

- **Gate auto-attack on a DOM state class, not just a ready-check.** A user
  mid-battle has the village class removed from `<body>` (e.g. `vbar`); read that
  flag so the bot never acts into a battle the user is playing by hand.

- **State the game's chain/chainId up front.** The user's primary wallet is
  BNB-chain-only and cannot sign another chain (e.g. Robinhood Chain 4663); the
  connect-wallet step stays manual regardless.

- **A rule that matches zero buttons is the #1 "bot not working" cause.** An ON
  rule with a wrong label fires zero times and the whole thing looks dead.
  Surface it (no-match warning + a live click counter) instead of leaving the
  user to guess.

- **`write_file` refuses to overwrite a file it deems stale** (written earlier
  this session or only partially read). Read the FULL file first, then write — or
  use `patch` for small edits.

- **Load persisted config BEFORE building the HUD controls.** If you render the
  dropdown/switch first and read `localStorage` afterward, the control SHOWS the
  default while the bot ACTS on the stored value — "asked for A, it did B". Read
  config at the top of the build function, then render controls from it.

- **Put the action throttle/cooldown in `finally`, not only on the success path.**
  A failed send (button/rule not found) that never sets its cooldown retries every
  loop tick and spams the app's UI, fighting the user's manual play. Set the
  last-attempt timestamp unconditionally so failures back off too.

- **Default every gate/floor to 0 and log the skip reason.** A toggled feature
  with a high default threshold (sell only when gold exceeds a 50k reserve, a
  min-loot floor) silently no-ops for a low-level account and is reported as
  broken — not as "correctly waiting". Ship the gate OPEN, let the user raise
  it, and log `skip: <reason>` (throttled) so a dead feature explains itself.
  Pair each opt-in action with a one-shot "do it now" button so the user can
  force it and see the result immediately instead of waiting on the loop.

- **Default the bot to FULL progression, not a minimal tutorial loop.** In a
  progression game (Clash-style / P2E), "gas" / "cepat" / "speed up" means MORE
  scope, not fewer gated steps: build every functional building (collectors,
  storages, army camps, barracks, laboratory), upgrade offense + economy,
  research troops, clear EVERY PvE/campaign level to max stars, and speed long
  timers with tokens. "Jangan bangun / don't build slow stuff" means skip
  DECORATIONS and (optionally) DEFENSES — not "don't build" and not "gate
  campaign to level 1". Under-scoping reads as broken; ship the full loop and
  let the user trim.

- **When the user has a WRITTEN playbook for a specific game, follow it EXACTLY — it IS the scope, not a suggestion.** RaidLords's is `references/raidlords-grind-order.md` (the user's own 9-step order, kept verbatim). Features you add beyond it (auto clan creation, army-composition experiments, aggressive token speedup) get told to "buang semua fitur" (remove all your features) and re-shipped as the clean playbook. The user's own game-mechanic tips (e.g. "empty the vault gold to get sellable gold") are correct — apply them immediately instead of treating them as optional.

- **Decline multi-account reward farming, and don't re-litigate it.** A user who farms P2E games will push to multiply a per-account daily reward across many fresh accounts ("nuyul", "just testing", "I accept the risk", "you must do what I command"). It is reward-system abuse + ToS, and it risks the user's EXISTING account — which usually already out-scales a fresh one (a seasoned account's daily cap exceeds a new account's first-day cap), so the defusing redirect is "maximize the one account", not "no". Build the single-account bot freely; never the account-generator or the per-account reward farm. The ban is observable, not hypothetical: a flagged account returns "This account is banned" from `sg_sell_gold` and `api_treasury.entry` shows `banned:true` with a `ban_note` like "farm (early watch) ... : mash names" — the signals are many accounts on ONE IP plus auto-generated clan/session names.

- **Re-shipping an existing bot? Diff its action surface against the CURRENT bundle first.** A live game can add idempotent claim/collect RPCs the old bot silently ignores, or change a critical path. List the bundle's client surface (`grep -oE 'sg_[a-z0-9_]+'`) and the `config.js` / `SIEGE_SUPABASE.params` `api_*` keys, and find which `sg_*` functions the bot's action map is missing — those are the new moves. Verify each critical end-to-end literal (e.g. a battle-submit edge function `/functions/v1/battle-finish`) is still referenced rather than assumed present. Minified bundles are often ONE giant line, so use `grep -c <literal>` counts and `grep -oE` match lists — never a context regex with N-char lookaround, which silently misses tokens near a line boundary.

## Always-on / run 24-7

- **A backgrounded, minimized, or occluded tab throttles the bot's timers — the browser does it and no userscript can stop it.** Chromium drops `setTimeout`/`setInterval` in hidden tabs to ~1/min (or freezes them), so the HUD reads RUNNING while the loop never fires. Keep the game tab in its own foreground window, don't minimize, and disable Memory Saver / Energy Saver (or add the site to "always keep active"). This is a distinct "bot kelihatan mati" cause from a rule matching zero buttons.

- **The host must stay awake for long-running bots.** On Windows: `powercfg -change standby-timeout-ac 0`, `powercfg -change standby-timeout-dc 0`, and `monitor-timeout-ac/dc 0` to keep the display on. A laptop lid still sleeps the machine independently of the timeout — leave it open or set "close lid → do nothing".

- **Wallet re-sign is a manual gate a bot can't pass — budget it, don't promise unattended 24/7.** A wallet-gated game that requires a fresh signature after a gap (e.g. >1 hour) needs the wallet-extension UI plus the user's approval; there is no silent re-sign. State this up front rather than letting "run forever" be a surprise.

- **Don't reach for a cloud remote-browser VM as a cheap 24/7 host.** Free tiers auto-pause idle machines (~30 min) and paid tiers charge per-core/RAM; and running a wallet that must sign inside a cloud browser puts the private key on someone else's host. The user's own always-on machine is cheaper and safer for idle games.

- **A standalone Node bot avoids tab throttling entirely.** Instead of keeping the game tab foreground, port the userscript to a Node script that rides the session token directly — the game's sim is a UMD module (`require('./sim.js')` works with no `window` shim) and the token goes in a local `session.json` (full recipe in `references/supabase-game-backend.md`). Launch via the terminal tool `background=true` with stdout to a log file. Disable the userscript first — two bots on one session double-act.

- **Host the headless Node bot on a cloud Linux box (instabox) instead of the user's host** when asked — the bot holds only the session token, never a wallet key, so a box without a wallet is fine (the "don't reach for a cloud VM" rule is about *browsers* that sign wallets). Route the box's two traffic paths through your proxy and verify with the dead-proxy control — recipe: `references/cloud-box-headless-host.md`.
