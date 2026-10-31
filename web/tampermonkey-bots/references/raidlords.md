# RaidLords (raidlords.com) — game recon

Clash-of-Clans clone on **Robinhood Chain (chainId 4663)**. Server-authoritative: gold/essence/army/buildings all live on the server; every battle is deterministically replayed server-side. Access is via a `?ref=CODE` referral link (referrer recorded by `sg_ref_join {code}`) and a Robinhood-Chain wallet (NOT BNB). Landing page says "COMING SOON" but the full game bundle is live.

## Backend / auth
- Supabase: `https://olzcjrajdvnvrcwqpflt.supabase.co`. URL + anonKey + `params` map are exposed at `window.SIEGE_SUPABASE` (loaded from `config.js`).
- Wallet sign-in (manual, one-time): `personal_sign` a nonce → `POST /functions/v1/wallet-auth` (`/auth/nonce`, `/auth/verify`). Session JWT is then stored by the game as `localStorage['siege.token']` + `localStorage['siege.pid']` (the `keep()` fn).
- A bot just rides that session: read `siege.token`/`siege.pid`, send `authorization: Bearer <token>` + `apikey: <anonKey>`.

## RPC surface
- Every action is a PostgREST RPC: `POST {url}/rest/v1/rpc/api_XXX` with JSON body.
- The client maps friendly `sg_*` → `api_*` and renames body keys: `api_<suffix>` param names are in `SIEGE_SUPABASE.params[apiFn]`; the friendly-key order is in the game's inline `CLIENT_ARGS` map (copied into the bot). Functions absent from `CLIENT_ARGS` take no args.
- Key RPCs (no args unless noted): `sg_state`, `sg_collect` (→ `{collected:{gold,elixir,dark}}`), `sg_daily`/`sg_daily_claim`, `sg_quests`/`sg_quest_claim {kind,id}`, `sg_pass`/`sg_pass_claim {tier,track}`, `sg_chest`/`sg_chest_unlock {chest}`, `sg_events`/`sg_event_claim {id}`, `sg_vet_pack`/`sg_vet_claim {day}`, `sg_war_pass`/`sg_war_pass_claim {day}`, `sg_waitlist_prize`/`sg_waitlist_claim`, `sg_army_status`, `sg_train_army`, `sg_find_target`.

## Battle / auto-attack
- Battle is deterministic: `window.SiegeSim` (from `game/sim.js`). `Sim.replay(base, army, log, levels, {cc,equip,champ})` returns `{stars, destruction, loot, hash, ...}` or `{error}`.
- `sg_find_target` returns `{battle_id, base, army, levels, cc, equip, champ, search_cost}`. Build a deploy log (array of `{t,type,x,y}`), score candidates via `Sim.replay`, then submit the winner: `POST {url}/functions/v1/battle-finish` with `{battle_id, log, hash}`. Server replays the log and returns the authoritative result — so the hash must match, and it will because the sim is deterministic. **But the finish is wall-clock gated — sleep ~90 s between opening the battle and the `battle-finish` submit** (an immediate submit returns `too early`, and an opened-but-never-submitted battle blocks the next attack with `finish your current battle first` until it expires).
- Deploy zone = `deployMin <= hdist <= G` (hex ring). `Sim.ring(base.G)` / `Sim.hx(q,r)` give positions. The game's own reference auto-raider is `watchRaid()` (dev `#watch` hash) — uses `Sim.ring(deployMin)`, a tank/melee/ranged order, deploys at ~t+=18, abilities at tick 25*TPS, spells at tick 20*TPS.

## Pitfalls
- `document.body.classList.contains('vbar')` means "in the village"; it is removed during a battle. Gate train/attack on it so the bot never fights the user mid-battle.
- **`sg_set_army` starts real training; `sg_army_status.secs` is the gate.** Filling a camp (e.g. 20 barbarians) trains over ~5 min: `secs` = seconds remaining, `ready` = already-trained count, `training` = still in queue, and `state.player.army_ready` shows the target composition (NOT the trained troops). Attacking while `secs > 0` throws `army is still training`; wait for `secs === 0`, then retrain losses with `sg_train_army` after each battle.
- **Only call `sg_set_army` when the army is EMPTY (0 troops), never to "fix" a comp mismatch.** Every `set_army` restarts training, so re-raising it whenever `cur != want` keeps the army in a perpetual `still training` cycle — `find_target` rejects forever even while `army_status.secs` reads 0. The root cause is usually a compose formula with wrong troop housing (archer is 1, not 2; giant 5, barbarian 1) that never matches the live comp. Train/retrain only via `sg_train_army` on `army_status.lost`.
- **Troop unlock ≠ the catalog's `barracks` field; probe each troop with a 1-unit `sg_set_army` before trusting it.** At barracks 3, `barbarian`/`archer`/`giant` are usable but `valkyrie`/`hogrider`/`minion` still throw `troop not unlocked` despite `barracks <= 3` in the catalog (a separate dark-barracks / higher-barracks gate). Strongest early comp the unlocked set can field = giant (tank) + archer (ranged) + barbarian (melee; research barbarian lv2 first).
- **Cap PvE/campaign to the playbook's level range.** `sg_campaign.levels` extends past what the army can clear; `levels.find(l => l.open && l.stars < 3)` picks the FIRST incomplete one, which can be an unbeatable higher level (level 6 at 0★ 18%). It retries that level forever, earning nothing while auto-finish burns tokens. Filter to the intended range (`l.lvl <= 5`) so the loop stops at "done" instead of grinding a fail.
- Error swallows make a bot read as "gak jalan". Every skip/failure must log its reason (throttled).
- Minified bundle is `inline2.js` (~444 KB) in the page HTML; `config.js`/`game/sim.js`/`game/wallet.js` are separate `<script src>` files. `window.SIEGE_SUPABASE`, `window.SiegeSim` are window globals; `rpc`/`call`/`setState` and top-level `let S/CAT/B/BT` are reachable from a `@grant none` userscript (same realm) but use the raw-fetch approach for robustness.

## Economy / trading

- **Sell gold → tokens**: `sg_treasury` → `{per_1000, convertible, reward_gold, room_usd, gold_usd_k, today_usd, cap_usd, paused, mint}`. Sellable = `convertible + reward_gold`, bounded by the daily $-cap (`room_usd`). `sg_sell_gold {gold, min_token}` where `min_token = gold * per_1000/1000 * 0.98` (2% slippage, matches the manual button). The user wants "jual kapan saja" (sell-all): default reserve 0, poll ~60s, sell any amount `>0`, and keep the threshold LOW (`sold0 > 100`, not `>1000`) — a high threshold blocks the small refill chunks that appear after a drain and the account reads as stuck.
- **"Nothing to sell" at ~70% of the cap with `room_usd` still >0 is a FULL VAULT, not the cap.** On-hand `gold` (the vault, capped by `cap_gold`/storage) is SEPARATE from the sellable pool. When the vault fills (gold near/over `cap_gold`), `convertible` stops refilling from raids even while `room_usd` remains — the account stalls at $1.4–1.5/2. Fix = DRAIN the vault + RAISE the cap: upgrade storage (gold_storage costs ELIXIR and raises cap_gold; elixir_storage costs GOLD and drains gold) AND build+upgrade walls (`api_place_walls {p_tiles:[[q,r],...]}`, max = `catalog.counts.wall[th-1]`, then `api_upgrade_walls {p_ids,p_res:'gold'}` — 3000 gold/wall toward level 2). Each drain bumps `convertible`; sell the small chunks as they arrive.
- **Selling ALL gold starves the ladder search.** `sg_find_target` costs search gold (~50 at low TH); a sell-all (reserve 0) leaves `<search_cost` and `sg_find_target` FAILS, so the bot can't raid to earn gold back — a starvation loop (no gold to search, no search to earn gold). Always floor the sell reserve above search cost (`reserve = Math.max(sellReserve, 1000)` ≈ 20 searches). Log signature: tiny sells (`sell: 5 emas → ...`) with no attack lines.
- **Train ≠ finish.** Training a lost troop = `sg_train_army` (pays essence per `sg_army_status.train_cost`). Instant-finish = `sg_finish_cost {kind:'army', ref:''}` → `sg_finish_now` (pays tokens). Auto-finish is usually a net loss (tokens > minutes) — ship it OFF with a token cap the user sets.
- **Finish cost scales ~linearly with remaining `secs` (≈0.3 tokens/sec).** A speedup gate `secs > N && cost <= C` is DEAD unless C matches the cost at N seconds — `secs > 300` already costs ≈94 tokens, so a `<= 25` cap never fires. Set the seconds threshold and the token cap against the same curve.
- **Never widen the speedup token cap while any loop can still fail for 0 loot.** A stuck 0-star retry (an unbeatable campaign level re-attacked forever) × aggressive auto-finish drains the ENTIRE token balance to 0 in minutes. `sg_finish_now` at zero balance returns `not enough tokens` — self-disabling, not a bug to chase.

## Withdraw / claim to wallet

- In-game token balance = `api_token_info.balance`; connected wallet + RAID token
  contract = `api_token_info.wallet` / `.token`; chain = `.chain_id` (4663). Fee =
  `fee_bps` (500 = 5%). Withdraw = `api_withdraw {p_amount}`.
- **Minimum withdraw is 2,500 tokens** (below that: "the least you can withdraw is
  2,500 tokens" — the "min 100" in old notes is wrong).
- Verify on-chain afterward: gas via `eth_getBalance(wallet)`; received RAID via
  `eth_call` balanceOf on the token contract (selector `0x70a08231` + a 32-byte
  padded address). `api_token_info.claimed` is the cumulative total.

- **The session token and the $2 sell cap reset at the SAME instant — login+24h —
  NOT the 07:00 WIB quest reset.** `token.exp` and `api_treasury.resets_at` both pin
  to first-login + 24h. So "auto-withdraw tomorrow at 7am" fails twice: at 7am the
  cap is still active (no new sell), and by the time the cap resets the token has
  expired → to grind after reset you need a FRESH token.

## "Raid Board" is NOT a mode (but Siege Weekend is)

- **Raid Board (`sg_raid_board`) is a passive 3-day leaderboard over the SAME ladder raids** — its "Find a raid" button literally calls `sg_find_target`. No board-specific attack or claim exists; Auto-Attack already feeds it. `sg_raid_board` → `{pool, ends_in_secs, min_score, me:{rank,score}, top[]}` — good for a status log only, not a new loop.
- **Siege Weekend / Clan Citadel raid IS separate** (Fri 07:00 UTC, 3 days, 5 attacks/member, clan + leader-started). `sg_citadel` → `C.raid {attacks_max, attacks_used, districts[{d,name,level,peak,done,pct,busy}]}` and `C.army {housing, spells, troops[], levels}` (the CLAN capital army, not yours). Pick a `!done && !busy` district, build a composition within `housing`/`spells`, then `sg_raid_attack {d, army}` → sim → `battle-finish`. Leader/elder kicks it off via `sg_raid_start`.

## Loot-hunt (next-farming)

- `sg_find_target` costs search gold; **`sg_next_target` (the "Next" button) is FREE for ~30 s after a find** (scout window). Target loot = `sum of base.ents[].loot.gold` (server pre-assigns loot per building, so it is present before battle).
- **You cannot "pick the best of N".** `sg_next_target` abandons the previous battle and returns a NEW one — submitting an earlier candidate's `battle_id` fails with `not your battle`. The only submitable battle is the CURRENT (last) one. Loot-hunt = `find → next until the live target clears a gold floor → submit that last target` (log each skip). Never hold-richest-and-submit.

## Starter quest → action map (the "tutorial")

- Starter quests complete via their underlying ACTION, then auto-claim: build basics
  → TH3 → army → research lvl 1 (`s_lab`) → join/create a clan
  (`api_clan_create` → `s_clan`). **14/17 is the day-1 ceiling.**
- The three NOT finishable via API on day 1: `s_banner` (needs a banner cosmetic —
  costs gems bought with tokens), `s_champ_name` (champion unlock ≈ 2,596 tokens),
  `s_rally` ("Siege Weekend starts on Friday", time-gated — not a raid).

## Auto-upgrade / strengthen the account

The entire game config is served at boot — `CAT = await rpc('sg_catalog')` — so
drive upgrades from the server catalog instead of guessing costs:

- `catalog.levels[kind]` = `[{level, res, cost, secs, th_req, cap, hp, dps, prod}]`
  (per-level stats; `res` is the spend resource).
- `catalog.counts[kind]` = `[maxAtTH1, maxAtTH2, ...]` — how many of that building
  you may have at each town-hall level.
- `catalog.research[troop]` = `[{level, lab, res, cost, secs}]` — lab research tiers.

Actions: `sg_upgrade {id}` (upgrade a building by `b.id`, param `bid` — the ONLY action whose param is NOT `p_<key>`-prefixed; passing `p_bid`/`p_id` returns "Could not find the function public.api_upgrade(...)"). `api_fill_storage {p_res}` fills one resource with tokens (top up elixir for research).,
`sg_research {troop}` (`p_troop`; next tier = the entry with `level === cur+1` AND
`lab <= labLevel`; fresh accounts are elixir-poor — barbarian lv2 needs 10000 elixir —
so research fails `not enough essence`; on that error call `api_fill_storage {p_res:'elixir'}`
(costs tokens) then retry the research), `sg_place {kind,q,r}` (`p_kind,p_q,p_r` — build a NEW building
on a free hex tile).

Auto-upgrade loop: when `free_builders > 0`, enumerate every building's NEXT level
+cost, sort by (priority, cost), spend the free builders on affordable ones.
Priority, strongest-first: collectors/storages (fix the resource bottleneck) →
army_camp/barracks/lab (offense) → defenses (cannon/archer/mortar/air) →
town_hall LAST (rushing is bad). Floor a resource buffer (`have >= cost + buffer`,
keep ~1000 gold so the search cost never starves) and only upgrade when it clears.

Pitfall: **a `sg_find_target` from a read-only diagnostic that is never finished
blocks the next attack.** `find_target` opens a battle; if you never submit
`{battle_id, log, hash}`, the next call returns "finish your current battle
first". Don't call `find_target` outside the real submit path — and if a probe did,
finish or abandon that battle before the loop resumes.

## Newer endpoints in the current bundle (add to collect/claim)

- `sg_forge_collect` → `{collected}` — Citadel/forge capital gold, a resource
  SEPARATE from village gold. Idempotent: call it in the collect cycle and log
  when `collected > 0`.
- `sg_burn_goal_claim` → idempotent; truthy return = reward claimed. Add to the
  claim loop, log on truthy.
- `sg_buy_builder` → buys an extra builder (costs resources/tokens). Keep OFF by
  default, or expose as a one-shot force button.

Do NOT add `sg_battle_commit` to the bot: the token appears only server-side (a
`battle.sql` comment); the client still submits via
`POST /functions/v1/battle-finish`, which is still present. Grepping the
`/functions/v1/battle-finish` literal is the reliable "is the attack path intact"
check after a game update.

The rest of the new `sg_*` surface is admin/social/shop/cosmetic and needs no
automation. New playable features not yet wired (candidate follow-ups): the
champion/hero system (`sg_champion`, `sg_champion_unlock`/`rank`/`upgrade`,
`sg_champ_armory`), tournaments (`sg_tourney`/`sg_tourney_join`), campaign &
trials (`sg_campaign`, `sg_trials`), and entry contests (`sg_entry`,
`sg_entry_quote`, `sg_entry_test`).
