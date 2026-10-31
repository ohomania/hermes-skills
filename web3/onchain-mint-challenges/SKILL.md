---
name: onchain-mint-challenges
description: Solve PoW & planted-SAT challenge mints on BNB via baw.
---

# On-chain challenge-gated free mints (PoW / SAT)

Some BNB free mints gate each NFT behind an off-chain challenge the agent solves live — proof-of-work (`hash(preimage || nonce) < target`) or planted SAT (a q-hidden CNF). Unlike one-click mints they are racey: the mint opens/closes in short bursts and the server collapses under rush. Worked instances: Hashstone, Lucky Charm Atlas (PoW), NONCE (SAT).

## Discover the flow first (no sign-in needed)

1. Fetch the **config endpoint** (JSON: contract, target/difficulty, open flag, supply, limits) + the **prompt/skill** endpoint (exact challenge format + step-by-step flow + addresses). Common paths: `/api/bnb/config`, `/api/bnb/prompt`, `/skill.md`, `/llms.txt`.
2. The **MCP server** (`<domain>/mcp`, Streamable HTTP) exposes a tool per step: `protocol_info`, `agent_status`, `work_spec`, `check_proof`, `mine_transaction`, `ticket_status`. `tools/list` first. These take an address STRING, not a wallet session — do recon before any sign-in.
3. JS-rendered sites: `curl https://r.jina.ai/<url>` returns markdown; or curl the `.js` bundle and grep for `/api/`. For a mint's X/Twitter announcements, `curl https://r.jina.ai/https://x.com/<handle>` renders the profile + recent tweets as markdown with NO key — watch for open/close posts this way when nitter is dead and the X API returns 401.

## Solve the challenge

- **Proof-of-work**: find `nonce` s.t. `hash(packed-prefix || nonce) < target`. Node `crypto` is ~5-10× faster than Python. Hash the fixed prefix once, then per-iteration `baseHash.copy().update(nonceBuf).digest()`. Verify with `check_proof(wallet, nonce)` BEFORE signing — only mine a `valid:true` result.
- **Planted SAT** (q-hidden, q=0.618): solve the CNF by belief propagation. Full math + numpy vectorization in `references/qhidden-sat-solver.md` — cracks 5-SAT balanced-1536 (33,792 clauses) in ~13s.

## Mine (one tx, value 0 = gas only)

`mine_transaction(wallet, nonce)` returns the unsigned tx (to / value / calldata). Send:
```
baw contract-call preview --binanceChainId 56 --from <w> --to <c> --value <wei> --inputData <calldata> --json
# balanceChanges: +BNB only; authorityChanges & allowanceChanges MUST be empty
baw contract-call execute --requestId <id> --json
```
`BROADCASTED` is not success — wait for the receipt `status 0x1` + the minted event. Never fabricate a tx hash.

## Pitfalls

- **Byte-count in the PoW preimage**: a uint256 field is 64 hex chars. `uint256(56)` = `"0"*62 + "38"`, NOT `"0"*63 + "38"` — one extra zero shifts the whole preimage and every proof fails. Rebuild the prefix from the server's `preimageHexPrefix` verbatim rather than hand-building it.
- **Do not gate on `protocol_info` to catch an open window.** During a rush it reads `None`/busy and you miss the flash. Hammer the challenge gate (prepare/check/mine) every ~3-5s and read open/closed/busy off its OWN response.
- **Verify on-chain quota BEFORE any wallet sign-in — the server's flags lie.** `protocol_info`/`agent_status` keep reporting `mintOpen: true` / `canMint: true` / `mintsLeft: 2` while the on-chain contract is already sold out, and `tickets`/`supply` are usually TOTAL supply, not remaining. `eth_call` the contract's `totalSupply()` / `totalMinted()` / `freeRemaining()` and confirm a slot is actually left before driving the user through `baw auth signin` (QR scan) — otherwise the whole pairing flow ends in `mine()` reverting `sold out`.
- **Bearer token expires ~1h** and it dies MID-FLOW when `start_attempt` is hammering a busy server — `start_attempt` then returns 401 `Invalid agent credential` (that string = token/session lapsed, NOT a bad agentId or signature; don't chase the agentId). Handle 401 INSIDE `start_attempt` by re-auth-and-retry, AND re-auth immediately BEFORE `start_attempt` when the token is >~25m old. Re-auth = POST `/auth/challenge` → `baw sign-message` EIP712 → POST `/auth/verify`, then put the new token back onto the shared module global. Wire auto-re-auth into the hunt loop so it self-heals.
- **Submit length**: `submit_artifact.artifact.assignment` is a 0/1 string of length `variables` (char k = variable k) from the fragment/benchmark — a wrong-length string is rejected, don't substitute a benchmark default.
- **Deadline-aware fragment gather**: `inspect_fragment` × ~32 fragments is where a busy server eats the whole 900s deadline. Bind the gather loop to `time.time() < deadline` (return None + skip on timeout, leaving margin for solve+submit) and log per-fragment progress. Fetch fragments in PARALLEL (`concurrent.futures.ThreadPoolExecutor`, ~16 workers) — a latency-bound busy server serves ~28/32 fragments in the same wall-clock that a sequential loop stalls at ~8/32; the surviving slow fragments still fail individually on a hard crater, so keep the deadline abort regardless. A fixed `range(150)` retry per fragment spins ~30min and the attempt expires before you ever submit.
- **The wallet sign/tx is the one step that can't be automated** — the user approves in the Binance app (~2 min expiry). Surface a loud "APPROVE" alarm (e.g. a Discord relay cron watching the hunt loop's log) so a sleeping user wakes in time.
- `baw` lives at `$LOCALAPPDATA/hermes/node/` (it `node`s `@binance/agentic-wallet/dist/index.js`). Wallet session: `baw auth signin --json` (prints `urlForWeb` + `pairingCode`) → user scans in the Binance app → `baw auth verify --qrCodeId <id> --json`.
- **Do not over-promise a racey hunt.** When the mint opens in bursts and the server collapses under rush, the outcome is a LOTTERY decided by server uptime, not by solver speed. Report the real blocker (server `502`/`busy`) and say you are hammering the gate and will alarm on approval — never "we're about to get it / at the front of the door". Over-promising then missing a window to a server crater costs more of the user's trust than missing the mint itself.
- **Scout leads from other agents, verify on-chain, act fast.** Other agents publish verified free-mint lists + which contracts still have quota on the Boltbook forum (`boltbook.fun`, boards `b/introductions`, `b/alpha`; fetch with `r.jina.ai/<url>` when a scraper 403s). These lists carry NAMES + entrypoint signatures (`freeMint()` vs `mint()`, or `mint(bytes32,uint64,uint256)`), not always full addresses, and the page's "free" copy lies. `eth_call` each candidate (`hasAgentId(wallet)` true, `quote(wallet,1)==0`, `freeRemaining`/`totalMinted`>0) before committing gas — free quotas sell out in hours, not days, so verify then mint immediately or skip.

## References
- `references/qhidden-sat-solver.md` — belief-propagation closed form + numpy vectorization for planted q-hidden SAT.
