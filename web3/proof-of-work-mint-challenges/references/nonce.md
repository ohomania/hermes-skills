# NONCE Protocol — proof-of-work free-mint (BSC 56)

"Free mint" gated by a solver challenge, not a payment. `mintPrice=0`, `failureFee=0`; the only on-chain cost is gas on the final `mint`. Abandoning a hard challenge costs nothing.

## Deployment (re-verify against the fresh /api/mint-prompt before acting)
- FreeMint `0x7538ba8C1A82E9706dB6d2463C15f69ADc01a17e`
- NFT `0x053259A3D30E63d9447E3d90813C6a494bcB398a`
- AgentGate `0xc8D8EebAd7Fdd590edA6d23164B1eC014913Ce8f`
- .ai registry `0x60B9262456dE011F7d15a54CdD8c48bAaa8B022F`
- MCP `https://mcp.nonceprotocol.xyz/mcp` (Streamable HTTP, JSON-RPC 2.0); prompt+ABI `https://nonceprotocol.xyz/api/mint-prompt`

## MCP flow (verified, in order)
1. **Auth:** `POST {wallet}` to `https://mcp.nonceprotocol.xyz/auth/challenge` → EIP-712 typedData ("NONCE MCP Sign In"). Sign with `baw sign-message --binanceChainId 56 --signType EIP712 --message <walletRequest> --json` — the request is the WHOLE `eth_signTypedData_v4` wrapper, not just typedData. `POST {wallet, challenge, signature, signatureRecovery}` to `/auth/verify` → Bearer token (~1h).
2. **Quota:** `wallet_status({wallet})` → `remainingMints` (max 2 lifetime), `nativeBalance`, `mintPrice`.
3. **Identity:** `agent_identity({wallet})` → `agentId` (decimal string). If MCP is busy, read it on-chain instead (`handleOf(wallet)` → tokenId via the .ai registry helper).
4. **Prepare:** `prepare_attempt({wallet, beneficiary:wallet, agentId, idempotencyKey:<fresh uuid>})` → `version` + `benchmark` + `startAuthorization` + `startWalletRequest`.
5. **Start:** sign `startWalletRequest` (same EIP-712 path) → `start_attempt({attemptId:<uuid>, signature, signatureRecovery})` → `capability` (private).
6. **Read:** `inspect_fragment({attemptId, capability, fragmentId})` for `fragmentId` 0…fragmentCount-1.
7. **Submit:** `submit_artifact({attemptId, capability, artifact, nonce:"0"})`.
8. **Mint:** on VERIFIED_WIN, `mint_transaction({attemptId})` → signed calldata → verify signer + expiry → `baw contract-call preview` then `execute`.

## Challenge types are RANDOM per attempt
| version | shape | difficulty |
|---|---|---|
| `nonce-route-14` | 14-node directed-cost TSP + ordering constraints + targetCost | EASY (Held-Karp DP) |
| `nonce-logic-512` | 3-SAT, 512 var | EASY (CDCL <1 min) |
| `nonce-logic-1536` | 3-SAT, 1536 var | q-hidden → solvable |
| `nonce-logic-3072` | 3-SAT, 3072 var | q-hidden → solvable |
| `nonce-logic-balanced-384-24` | 5-SAT, 384 var | HARD |
| `nonce-logic-balanced-1536` | 5-SAT, 1536 var | HARD |

The `-balanced-` (5-SAT, ratio ≥18) types are planted near the condensation point and every generic solver stalls on them — re-roll those. The `logic-*` (3-SAT) types are planted **q-hidden** (Jia–Moore–Strain, q≈0.618), not uniform random, and solve fast with the q-hidden BP in `qhidden-sat.md`. Re-roll stays a valid zero-thought fallback, but 3-SAT is no longer a dead end.

## Decisive tactic: re-roll for an easy type
- Abandoning is free (`failureFee=0`, no on-chain tx until the final mint).
- `prepare_attempt` while any attempt is pending returns `ATTEMPT_PENDING` — wait for the pending attempt's `expiresAt` (~5–10 min) before the next roll.
- Loop: prepare → read `version` → if not `route-14`/`512`, sleep to `expiresAt` + re-roll. Confirm the type BEFORE signing `start_attempt` (the deadline only starts once started).

## Solve the q-hidden 3-SAT (`logic-*`)
The `logic-*` clauses are planted q-hidden, not uniform. Use the BP solver in `qhidden-sat.md`: clause factor weights `[0,q,q²,q³]`, anneal the inverse temperature (β), run multiple seeds, round `H>0=1`, then a local-search cleanup to zero unsat. Verified unsat=0 on synthetic q-hidden at n=1024+.

## Detect re-open (monitor admission + X)
Admission flips open/closed repeatedly — monitor BOTH signals on a `no_agent` cron and alert only on change:
- MCP `protocol_info` directly (fresh token), ~10 min.
- The project X account: render `https://x.com/<handle>` through the Jina reader proxy `https://r.jina.ai/https://x.com/<handle>` — returns markdown with NO API key (nitter mirrors are dead; the X v2 API needs paid creds). Each tweet line is `… [TIME](…/status/ID)   TEXT   [N](…in_reply_to=…)`; extract the id from `/status/` links and the text between the date-link and the reply-count link. Track the MAX status id — the pinned post renders FIRST, so the first id is NOT the newest — and fire when it grows.

## Pitfalls (each cost real time)
- **`inspect_fragment` clauses are nested**: response is `{"fragment":{"rules":…,"clauses":[[l1,l2,l3],…]}}` — read `resp["fragment"]["clauses"]`, not `resp["clauses"]` (the wrong path silently collects 0 clauses).
- **`capability` is in-memory only**: write `{attemptId, capability}` to a file the instant `start_attempt` returns. If lost, re-sign the SAME `startWalletRequest` (EIP-712 is deterministic) and re-call `start_attempt` — it re-issues the same capability; `attempt_status` shows `state:ACTIVE` + the original `deadline`.
- **`protocol_info` ≠ the actual attempt**: the challenge type is per-attempt, not per-protocol. Trust the per-attempt `version`/`benchmark`, never a cached `protocol_info`.
