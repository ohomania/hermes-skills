---
name: agent-native-challenge-solving
description: Use when solving PoW/planted-SAT gates on .ai-gated mints.
---

# Agent-native challenge solving (PoW & planted SAT)

Some "agent-native" free mints don't only need a wallet holding a .ai Agent ID — they gate the mint behind a compute challenge the agent must solve off-chain and submit alongside the mint tx. Two types:

- **Proof-of-work** (Hashstone, sidecoo CharmMine): find a `nonce` so `sha256(abi.encodePacked(TAG, uint256(chainId), address(contract), address(wallet), uint256(nonce))) < target`. See `references/pow-mint.md`.
- **Planted SAT** (NONCE): solve a q-hidden k-SAT served over MCP, submit the assignment string. See `references/qhidden-solver.md`.

The onboarding/execute side (reading a game helper, planning, `baw contract-call`) lives in `agent-native-game-onboarding`; this skill is the compute + MCP-flow side.

## Always-on rules

- **Recon the challenge before computing.** These projects expose public config + prompt + MCP: fetch `/api/<chain>/config`, `/api/<chain>/prompt`, `/skill.md`, and MCP `tools/list`. The exact PoW preimage, `target`, `variables` count, and fragment structure come from those — not from a benchmark receipt.
- **Compute locally, verify on the project's own tool BEFORE sending.** PoW: call the MCP `check_proof(wallet, nonce)`. SAT: `checkWork` / `attempt_status`. A result that *looks* valid (hash below target) can still be wrong if the preimage encoding is off-by-one — the project's verifier is the source of truth, and it costs a wasted mint window when it's wrong.
- **Respect the challenge deadline.** Every read/solve/submit loop must be deadline-aware (abort past `deadlineSeconds`). An unbounded per-fragment retry loop spins far past the deadline and the attempt lapses silently.
- **MCP `Authorization: Bearer` tokens expire fast (~1h).** Re-auth before the deadline-critical step (POST `/auth/challenge` → EIP-712 sign via `baw sign-message` → POST `/auth/verify` → new token) and treat a 401 mid-flow as "token expired, re-auth and retry", not as a bad wallet/agentId.
- **Read `variables`/clause counts live**, never from a default or an old attempt — a wrong-length assignment is rejected outright.
