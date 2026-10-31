# CozyGolem (play.cozygolem.xyz) — recon notes

Wallet-gated game on Robinhood Chain (chainId 4663 / 0x1237). Reversed from the
sign-in bundle + a live session; the v2.37 action loop was NOT fully mapped, so the
bot ships scan-first (edit text rules from the Scan dump). User plays via the Binance
Wallet extension (embedded wallet 0x1dc2...548e).

## Gate
- Connect any Robinhood Chain wallet, sign a free `personal_sign` challenge, pass
  Cloudflare Turnstile (sitekey in the bundle), then POST `/functions/v1/game-wallet`
  `{address, signature, ts}`. Server rejects on `low_balance` / `not_allowed` / `ip_limit`.
- Balance gate: >=1000 CZSH ("Cozy Shard", token
  `0x7f81752bc992330877e996bfabaecfb2f7306f00`, 18 decimals). Old token name GOLEMITE
  (Pons launchpad `0x3d9f1a...`). Robinhood mainnet — no faucet (testnet is 46630).

## Session / persistence
- Supabase `https://ptpcbxsschudczlenhhq.supabase.co`; anon key + SB_URL/SB_KEY are in
  the sign-in bundle.
- Session = localStorage `cg_auth` (Supabase JWT). The middleware serves the real game
  only when cookie `cg_play` (the access token) is set; the gate page's own JS writes it
  after `sb.rpc('play_allowed')` returns true.
- World save is browser-local `cozygolem-save-v1` (big JSON). Small server-synced meta
  under `cg_sv_*` (bank, stone, leaderboard, best run, upgrades). The "progress is saved
  in this browser" copy is misleading — there is a full Supabase backend syncing `cg_sv_*`.

## Re-enter fast with a session (assistant-side)
1. Set localStorage `cg_auth` to the session JSON on the origin.
2. Reload (gate JS auto-runs `play_allowed`, writes `cg_play`, reloads) or set
   `document.cookie = "cg_play=<access_token>; Secure; SameSite=Lax"` then reload.
3. The first "choose your first golem" render is a loading state — wait for the save to
   rehydrate before reading real progress.

## v2.37 surface (seen, not fully mapped)
- Menu: Play / Market / Quests / Duel / Wallet / Shop / Leaderboard / Dash; Survival event
  (prize pool by total score); limited runs/day ("Today 9/10 runs").
- Regions (Emerald Vale ...), heroes (Lira / Cinder / Fen). Controls are keyboard-ish
  ("walk into a gate", "press E to switch hero") — the old idle labels
  (Claim/Collect/Upgrade/2×) may not map; wire rules from the Scan dump.
- Run screen (in-run) shows buttons `AUTO`, `Dash`, `Quit` + a wave timer. `AUTO` is the game's
  own self-play toggle, so an auto-run bot = click Play/Survival → click AUTO once → auto-claim —
  no keyboard simulation needed. Detect phase by which buttons are visible
  (AUTO/Dash visible ⇒ in-run; Claim/Continue/Next visible ⇒ post-run; else ⇒ lobby).
