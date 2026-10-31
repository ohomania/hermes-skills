---
name: proof-of-work-mint-challenges
description: Use when a free mint gates behind a compute challenge.
---

# Proof-of-work mint challenges

Some Web3 "free mints" keep `mintPrice=0` and `failureFee=0` but gate behind a solver challenge (SAT, route/TSP, hash). The "free" is the fee; the real cost is the compute the agent spends. This is the procedure for assessing + clearing those without burning hours on a hard instance.

## Assess before you solve
- A challenge has a TYPE and a SIZE. Read both before committing compute.
- "balanced" k-SAT and large UNIFORM-planted SAT near the k-SAT satisfiability threshold are genuinely hard: CryptoMiniSat, Glucose3, Z3, and GENERIC belief/survey propagation (uniform weighting) all stall on them. That is a property of the instance, not a bug in the solver.
- EXCEPTION — planted **q-hidden** 3-SAT (Jia–Moore–Strain, q ≈ 0.618, the golden-ratio conjugate): a `logic-*` (3-SAT) challenge is usually THIS distribution, not uniform random planted, and it IS solvable fast via a q-hidden-aware belief-propagation reweighting (clause factor weights `[0, q, q², q³]`) + rounding + a local-search cleanup, even at 1024–3072 vars. Read `references/qhidden-sat.md` before falling back to brute force or re-roll on a hard 3-SAT.
- Small variants are trivial: ≤512-var 3-SAT solves in ~30s with CryptoMiniSat; a ≤14-node route/TSP via Held-Karp DP (2^n × n ≈ 200k states).

## Solve cheap, re-roll hard
- If the type is RANDOM per attempt and abandoning is free (`failureFee=0`, no on-chain tx until the final mint), RE-ROLL for an easy type instead of solving a hard one.
- Re-rolling is throttled by a pending-attempt lock: the prepare/activation call returns a PENDING error until the prior attempt's expiry (~5–10 min). Loop: prepare → check type → if not easy, wait to expiry → re-roll.
- Confirm enough session/auth time remains before activating a timed (deadline) challenge — the clock starts at activation, not at prepare.

## Hash-PoW (sha256 nonce) — always solve, never re-roll
- The hash type is a leading-zero-bits nonce search: find a string `n` such that `sha256(challenge + ":" + n)` has `bits` leading ZERO bits. It is the easy type — `bits=20` ≈ 2^20 ≈ 1M hashes ≈ 3s in pure Python `hashlib`, and even `bits=26` is only a few minutes. Don't re-roll a hash challenge.
- Count leading zero bits by iterating the digest bytes: a `0x00` byte is 8 bits, otherwise add `8 - byte.bit_length()` and stop.
- The challenge body carries `bits`, `single_use`, and an `expires_ts`: mine IMMEDIATELY after fetching (single-use + short expiry), and never reuse a nonce across the register retry — fetch a fresh challenge if the submit fails after expiry.
- Submit the nonce WITH the target request, merged into its body, not as an auth header — most APIs want `{ "pow": {"challenge": "...", "nonce": "..."} }` added to the register/join payload (JSON body first; a `pow=` URL-encoded query param is the fallback). See `references/hashcash.md` for the full flow.
- A registration endpoint that formerly returned a global throttle ("paced globally" / 429 / "API hardening" 503) may LATER swap that throttle for a hash-PoW admission gate — when the throttle finally clears for you, re-read the error; a PoW gate is the point where onboarding became solvable again.
- Two preimage shapes exist. The hashcash/register form is `sha256(challenge + ":" + n)`. A mint contract's `mine(nonce)` form is `sha256(abi.encodePacked(prefix, uint256(chainId), address(contract), address(wallet), uint256(nonce)))` — byte-exact ABI encoding, and the nonce binds to the wallet so it can't be mempool-copied. BYTE-MATCH the service's `work_spec.preimageHexPrefix` (or the on-chain `proofOf`) instead of reconstructing from prose: an off-by-one byte in a uint256 or address field is SILENT — your local leading-zeros check passes but the contract's `proofOf`/`check_proof` returns a different hash and `mine` reverts `not enough work`.
- Validate the nonce for FREE before you broadcast. Call the protocol's `check_proof(wallet, nonce)` (or on-chain `proofOf(wallet, nonce)`) and require `valid:true` BEFORE sending `mine` — a bad nonce costs a full reverting-tx gas, the check costs nothing.
- Pre-mine nonces while the mint is closed. A `mine(nonce)` nonce binds to (wallet, nonce) and does NOT expire unless the difficulty changes — pre-mine the full allowance (2/wallet) while `open:false`, persist them, and fire the instant it reopens. These agent-native mints open/close in minute-scale bursts, so compute-ahead + a short change-detecting monitor beats re-mining on every open. Never reuse a nonce for a second mint — continue the search PAST the last found nonce to get a fresh one.

## Tooling (Python SAT solvers that install as wheels)
- `uv pip install --python <venv> pycryptosat python-sat z3-solver` → CryptoMiniSat, PySAT/Glucose, Z3 — all prebuilt wheels for CPython 3.11 win_amd64.
- `pycosat` has NO wheels (needs a MSVC C build) — use `pycryptosat` instead.
- `pycryptosat.Solver().solve()` returns `(sat, solution)` where `solution` is a 1-INDEXED tuple of bools (`solution[0] is None`). Index `solution[var]`, not `[var-1]`.

## State safety
- A challenge "capability"/"token" returned by an activation call is usually in-memory only. Persist it to a file immediately. If lost, re-sign the SAME activation payload (EIP-712 signatures are deterministic) and re-call the activation — it re-issues the same capability; the original deadline still applies.

## Report honestly
- Say plainly that a "free" PoW mint is free in FEE but priced in compute, and that a hard type may not be worth the effort.

## References
- `references/nonce.md` — NONCE Protocol (BSC): full MCP flow, challenge-type table, re-roll loop, concrete pitfalls.
- `references/hashstone.md` — Hashstone (BSC): encodePacked hash-PoW mint, MCP tools, preimage byte layout, mine flow.
- `references/qhidden-sat.md` — the q-hidden planted-3-SAT solver: BP factor weights `[0,q,q²,q³]`, the j≥1 conditioning trap, annealing + multi-seed, local-search cleanup.
- `references/computeroll.md` — ComputeRoll (BSC): agent-gated PoW token with RAMPPING difficulty (327680→1.8e13 over 100k proofs) and a stale site reference (2-arg vs real 3-arg `mine`).
