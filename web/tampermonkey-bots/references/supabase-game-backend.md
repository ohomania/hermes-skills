# Supabase-backed games: ride the session + deterministic sims

Many web3 idle/P2E games (Clash-style, P2E) run on **Supabase**: a PostgREST
backend reached through `POST {url}/rest/v1/rpc/<fn>`, authenticated with a JWT
the app keeps in localStorage. The minified bundle usually exposes the config as
a bare global:

    window.SUPABASE = { url, anonKey, params: { "api_collect": [], "api_upgrade": ["p_id"], ... } }

and ships the game's own simulation as a second global (`window.Sim`).

## Ride the session (no reimplemented auth)

1. Read the token straight from localStorage (`siege.token` / `<app>.token` /
   `sb-<ref>-auth-token`). RPC calls auth with `authorization: Bearer <token>` +
   `apikey: <anonKey>`.
2. Reconstruct the router. Bundles name the client fn `sg_collect` but call the
   server fn `api_collect`, renaming friendly keys to `p_*` named params. There
   are two tables to copy:
   - `params` (in the config global): `api_fn -> ["p_first", ...]` (ordered).
   - a client-arg map (a literal object in the bundle): `sg_fn -> ["friendlyKey", ...]`.
   Rebuild: `POST {url}/rest/v1/rpc/api_<x>` with body
   `{ p_first: body.friendlyKey, ... }`. Copy the arg map into the userscript
   verbatim; don't re-derive it.
3. Use `@grant none` so the userscript shares the page's global scope and can read
   `window.SUPABASE` / `window.Sim` directly. Depend only on `window.*` globals +
   localStorage, never the bundle's module-scope closures, so the bot survives
   scope isolation.

Safety: a user may paste a 64-hex private key in chat ("I've registered this").
They will often keep re-offering it — "it's a fresh account", "I trust you",
"make a skill to store it". The decline on the key is unconditional: never use,
sign with, or store it (a stored key is a live drain on their wallet), and warn
them it is exposed-and-compromised. Break the loop with the concrete redirect —
the bot only needs the SESSION token, so have them connect the wallet themselves
and paste `localStorage['<app>.token']` (console:
`copy(JSON.stringify({token: localStorage['siege.token'], pid: localStorage['siege.pid']}))`),
then PROVE the bot runs from nothing but that token. The key stays in the wallet
extension, never in the bot.

## Don't call the app's rpc() wrapper for bot actions

A well-built game wraps its RPC call in a helper that, on "short on gold", pops a
blocking **"complete with tokens?"** dialog and retries with an `x-fill` header.
For a bot, call the raw fetch path instead (throws a clean error on shortage), so
it never auto-spends tokens or pops UI over the user's play.

## Deterministic client+server sim = legal action optimization

When the game ships its battle/economy sim as a `window` global AND the server
replays the same sim to validate outcomes, the bot can:

1. fetch a target/round (e.g. `api_find_target` ->
   `{battle_id, base, army, levels, cc, equip, champ}`),
2. generate several candidate action logs, run each through
   `window.Sim.replay(base, army, log, levels, opts)`, score them
   (stars/destruction/loot), and
3. submit the best `{battle_id, log, hash: result.hash}` to the finish edge
   function (e.g. `/functions/v1/battle-finish`).

Determinism means the submitted hash matches the server's own replay, so the move
is accepted. **But the finish is wall-clock gated — sleep ≈90 s between opening the battle and the `battle-finish` submit** (an immediate submit returns `too early`; an opened-but-never-submitted battle then blocks the next attack with `finish your current battle first` until it expires). It is **optimization, not inflation** — the result is still bounded
by the game's rules. Keep auto-attack OFF by default and gate it on a DOM state
class (the village/not-in-battle flag) so the bot never fights a battle the user
is playing by hand.

Make candidates differ on POSITION and ORDER, not just count — a flat spread-drop
scores poorly. Funnel: tanks (`pref 'def'` or housing ≥ 5) dead-center, fast
melee (hog/miner/goblin/valk/wallbreaker) wide on the flanks, ranged/healers tied
behind (stagger `t += 8` so they trail the tanks instead of bunching), heroes
with the push. Deploy on the inner `deployMin` ring, not the outer edge. Stagger
spells on a delay toward the core (rage/heal near the advancing push, poison/
lightning/quake on the keep) — dropping them at `t=0` wastes them during the walk.
Score `stars*1e6 + destruction*1e3 + loot.gold`, try ~4 attack angles, and feed
the winning log into the live UI through the per-tick `script` slot (convert
`{t, type, x, y}` entries to `deploy(B, type, x, y)` at `tick >= t`).

Pitfall: special deploy units (`cc`/clan-castle) — add `cc` to a candidate log
only when BOTH `army.cc > 0` (the deploy slot) AND the `cc` roster holds troops;
otherwise `Sim.replay` returns `'none left'` and an attack whose candidates all
fail on `cc` is skipped forever.

Pitfall: `set_army` is not instant — it queues real training that spans minutes
(a full camp of troops trains at ~15 s apiece). `army_status.secs` is the
remaining-training countdown, and `find_target` / `campaign_attack` reject with
`still training` until `secs <= 0` — so poll `army_status` and wait for
`secs <= 0` before opening a battle; the `ready` count is already-trained
troops, not the attack gate. Opening a battle CONSUMES the ready army (it returns
to training afterward), so a battle left un-submitted re-trains the whole army:
always submit, never probe-and-abandon. Defer to the server for the final word —
catch its domain error to decide "wait" rather than pre-gating on a stale read.
And when you DO skip, log the reason (throttled) — a bot whose every skip/failure
is silently swallowed reads as "gak jalan" even though it is running correctly.

## Visual vs headless — default VISUAL

The headless submit path above is correct but invisible: the user watches an idle
village and reports "gak jalan". Make the bot play on screen by driving the
game's own battle machinery, which a `@grant none` userscript can reach:

- The attack loader is a top-level `function` (a `window` global), e.g.
  `await window.startAttack(() => api('find_target'))`. It sets `mode`, the board
  object `B`, and the target `BT` — but ONLY after it awaits its asset preload,
  so `await` it, then check `mode === 'battle'` before reading the board.
- The frame loop already steps the sim every tick and calls a `script(B.tick)`
  deploy callback when one is assigned. Assign the game's per-tick `script` slot
  (a top-level `let`) with your deploy plan; copy the game's own `#watch`
  auto-raider for order/timing (tanks → melee → ranged → heroes; abilities at
  tick `25*tps`; spells at `20*tps`).
- Its own `finishBattle()` submits on `B.over`. Auto-click the "return home"
  button a few seconds after the result modal appears so the loop can attack
  again.

Pitfall (visual): the game's attack loader swallows a `still training` error from
your `find_target` callback and calls its OWN `armyTraining()` — which opens the
training panel over the user's play, so "just call find_target and treat
still-training as wait" pops a blocking panel every loop. In the visual path,
(1) pre-check `sg_army_status` for `secs || lost` and SKIP before calling the
loader, and (2) wrap the fetch callback to throw a quiet error (`e.quiet =
true`, message NOT matching `/still training|train your army/`) so the loader
neither toasts nor opens the panel.

Top-level `let`/`const` globals (`mode`, `B`, `BT`, `script`) are same-realm
reachable from a `@grant none` userscript — not just `window.*` properties.

**`next_target` abandons the previous battle — neither path can "pick the best of N".** `next_target` returns a NEW battle and invalidates the one just seen; submitting an earlier candidate's `battle_id` fails with `not your battle`. The only submitable battle is the CURRENT (last) one, so "loot-hunt" = "next until the live target clears a gold floor, then submit that last target" — never hold-the-richest-and-submit.

## Run it as a standalone Node script (no browser, no tab throttling)

A `@grant none` userscript still needs the game tab open and focused — hidden tabs
throttle timers, a minimized window can freeze the loop. For a 24/7 bot the user
wants "you" to run, port the same logic to a standalone Node script:

1. **The game's sim is usually a UMD module.** `sim.js` wraps itself as
   `(function(root,factory){ if(typeof module==='object'&&module.exports) module.exports=factory(); else root.SiegeSim=factory(); })(this,function(){...})`.
   So `const Sim = require('./sim.js')` works in plain Node with **no `window`
   shim and no external deps** — check the wrapper before assuming a headless
   browser is needed. The module returns `{TPS, TROOPS, SPELLS, replay, hx, ring, ...}`.
2. **Reuse the game's own `config.js` for backend params; `session.json` only
   holds `{token, pid}`.** `config.js` sets `window.SIEGE_SUPABASE =
   {url, anonKey, params}` — in Node, `new Function('window', src + ';return
   window;')({})` and read the object, so you never hand-type the anonKey (tool
   output redacts it, truncating the JWT to `eyJhbG...`). The token is game-scoped,
   not a private key: it cannot withdraw funds (that still needs a fresh wallet
   signature) and it dies in ~1 day — base64url-decode the JWT's middle segment and
   read `exp`. Re-paste on expiry.
3. **Reuse the SAME `api()`/`battleFinish()` fetch helpers** — they are pure HTTP
   (PostgREST RPC + the finish edge function), no browser globals. Keep the param
   map (`CLIENT_ARGS['sg_*']` friendly keys → `params['api_*']` `p_*` names) and
   drive each action from a `while` loop with per-action cooldown timestamps.
4. **Launch it with the terminal tool** `background=true`, stdout redirected to a
   log file you then `read_file`/`tail`. The agent's terminal runs on the user's
   host, so a backgrounded Node bot there IS "running the bot for the user" — no
   cloud host, no browser tab.

To run it inside the game's own cloud box (the "agent box" the user set up): copy
the folder up with the box's file-copy command (`cp`/`push`), then start it
detached. A foreground `exec` has a short default timeout (~60 s) and killing it
mid-battle orphans the battle — use `exec --timeout N` for short probes and
`exec --background` (then poll `jobs logs`/`jobs kill`) for the loop, redirecting
stdout to a log file since a detached job's own stdout is not captured. Never
open a battle in a one-off diagnostic you don't submit.

Pitfall: **two bots on one session fight each other.** If the user's userscript is
still live in the browser, a Node bot on the same token double-acts
(collect/attack/sell twice) and the two stomp each other's state reads. Have the
user close the tab / disable the userscript before starting the Node bot.
