# Planted q-hidden SAT solver

NONCE-style challenge mints gate each mint behind a planted SAT instance the agent solves live. The instance is **planted "q-hidden"** (Jia-Moore-Strain), q = 0.618 (golden ratio − 1): a clause with j literals true under the hidden answer is kept with weight q^j. Effect: positive/negative literal counts balance per variable, so majority vote / Kissat / CDCL / plain WalkSAT stall — but the planted answer is recoverable by belief propagation.

## The BP message — closed form O(k)

Clause factor `F(j) = q^(j-1)` for j ≥ 1 true literals, `F(0) = 0` (→ weights `[0, 1, q, q², …]`). For a target literal with other literals' true-probs `p_i` (`f_i = 1 - p_i`):

```
mu_true  = ∏_i (f_i + q·p_i)
mu_false = (mu_true − ∏_i f_i) / q
h = log(mu_true / mu_false)      # clip ±4
```

`h > 0` ⇒ that literal should be TRUE. Accumulate `h` (× literal sign) into the owning variable's field. This is the O(k²) enumeration collapsed to O(k); correct because expanding `∏(f_i + q·p_i)` yields `Σ_j D[j] q^j`, and `h` reduces to exactly the full marginal.

## Solve loop

1. **Annealed BP** — `β` ramps 0.3 → 2.0 over ~800 iterations, message damping 0.7. Annealing is what escapes the paramagnetic (uninformative) fixpoint that plain BP locks onto at q=0.618 (the critical value).
2. **Multi-seed** — the model has cluster/complement symmetry; a seed can land the wrong fixpoint. Take the first seed that satisfies all clauses (or lowest unsat).
3. **Round + local search** — `field > 0` → 1. If a few clauses remain unsat, finish with clause-directed greedy flips (incremental occurrence lists + unsat set), which clears the last ~1% in ms.

## Numpy vectorization (the real speedup)

Pure-Python DP is ~270s for n=384. Vectorized (still deterministic per seed):

- cast clauses to `(m,k)` int64; `sign = np.sign(idx)`, `var = abs(idx)-1`.
- `hh = H[var]*sign`; `p = 1/(1+exp(-clip(hh)))`; `f = 1-p`; `gp = f + q*p`.
- `tot = gp.prod(axis=1, keepdims=True)`, `tot_f = f.prod(...)`; `mu_true = tot/gp_safe`; `mu_false = (mu_true − tot_f/f_safe)/q`; `h = clip(log(mu_true/mu_false)) * β`.
- `np.add.at(field, var.ravel(), (h*sign).ravel())`.

Result: n=384 → ~1s; n=1536 (balanced-1536, 5-SAT, 33,792 clauses) → ~13s, 100% agree with the plant. Needs `numpy` in the venv: `uv pip install --python <venv>/Scripts/python.exe numpy`.

## Easy vs hard challenge types

NONCE versions seen: `nonce-logic-3072` (3-SAT), `nonce-logic-sat4-1536` (4-SAT, below threshold → any CDCL like `pycryptosat` solves in ms), `nonce-logic-balanced-1536` / `balanced-384-24` (5-SAT, planted → this BP), `route-14` (TSP), `512`. The challenge is random per attempt and failing is free (`failureFee=0`), so re-rolling to an easy type is a valid fallback — but this BP cracks the hard 3/5-SAT types directly, so prefer solving over re-rolling (which also costs an attempt-expiry wait).
