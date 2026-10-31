# q-hidden planted 3-SAT — solver

A challenge that hands you a 3-SAT instance whose clause/variable ratio sits near the k-SAT threshold is rarely uniform-random: it is usually **planted q-hidden** (Jia–Moore–Strain). That one fact changes the solver from "hopeless" to "trivial". Applies to NONCE `logic-*` and any challenge built on the same construction.

## What q-hidden is
- A hidden assignment σ ∈ {0,1}^n is drawn first. Each clause = 3 distinct vars + random signs; `j` = number of its literals TRUE under σ.
- **Planted (j ≥ 1):** keep the clause only when `j ≥ 1`, with probability `q^(j-1)` for `q = 0.6180339887…` (golden-ratio conjugate). Clause weights for j=1,2,3 are `[1, q, q²]`.
- σ is the (near-unique) solution the challenge verifies. Recover σ, round to bits, submit.

## The trap that makes naive BP produce nothing
- If you generate with "keep probability `q^j`" **allowing j=0**, the likelihood factor is `q^j = q^[σ1=t1] · q^[σ2=t2] · q^[σ3=t3]` — it FACTORIZES into per-literal terms, so the clause→variable BP message collapses to a CONSTANT `log q` regardless of the beliefs. Constant message = zero information about σ. This is exactly why generic BP / Survey Propagation "stalls" on these: the non-conditioned weighting flattens the signal.
- Fix: condition on **j ≥ 1** (`q^(j-1)`), which sets the j=0 slot to 0 and breaks the factorization, making the message informative. Remember this whenever a planted generator you write fails to inform BP.

## The BP (clause factor weights `[0, q, q², q³]`)
For the other two literals a,b in the clause, let `pa, pb` be their "true" probabilities and `fa = 1-pa, fb = 1-pb` the "false" ones. The message from the clause to literal r is:
- μ(true)  = `fa·fb + q·(fa·pb + pa·fb) + q²·pa·pb`
- μ(false) = `(fa·pb + pa·fb) + q·pa·pb`   ← the j=0 term (`fa·fb`) is dropped here

Then `h = β · log(μ_true / μ_false)`, clamp to ±4. Accumulate `+h` on variable v for a POSITIVE literal, `−h` for a negative one. Update `H_v = damp·H_v + (1−damp)·field_v`.

- The weights `[0, q, q², q³]` are EQUIVALENT to `[0, 1, q, q²]` — a global scale cancels in the log-ratio. Don't fret which table an implementation uses; only the j=0 slot MUST be 0.
- Init H small-random (±0.01–0.1), damping 0.5–0.7, a few hundred iterations.

## q=0.618 is CRITICAL → anneal + multi-seed
At the golden-ratio q the BP sits at a phase transition: the informative (plant) fixpoint and a paramagnetic one coexist, so a random init lands on the plant only ~1 in 4 tries (that run shows ≥96% agreement with σ; the rest show ~35–40% agreement and many unsat). Two moves make it land right:
1. **Anneal the inverse temperature β** from ~0.3 up to ~2.0 across the iterations — ramps past the paramagnetic basin instead of freezing in it.
2. **Run multiple seeds**, keep the result with the FEWEST unsatisfied clauses (the plant fixpoint is unmistakably lower).

## Round + clean up
- Round `H_v > 0 → 1` else 0. A correct landing leaves single-digit unsat clauses out of thousands.
- **Local-search cleanup** reaches unsat=0 in <1s from a ≥96%-agree point: repeatedly pick an unsatisfied clause, flip the literal that breaks the FEWEST currently-satisfied clauses. Maintain per-clause satisfied flags + variable→clause occurrence lists and update them INCREMENTALLY — a naive full re-count per flip (O(m)) is too slow and stalls a 200k-flip loop.

## Generalizing to k-SAT (4-SAT / 5-SAT "-balanced") + a 260x numpy speedup
- `-balanced-` 5-SAT is the SAME q-hidden construction with k literals/clause — NOT a different hard distribution. Planted F(j)=q^(j-1) for j=1..k, F(0)=0. The identical BP recovers σ for k=3,4,5.
- **Closed-form message** (replaces the O(k²) DP for j-distribution): for the k-1 other literals i with false-prob f_i and true p_i=1-f_i:
  - μ_true  = Π_i (f_i + q·p_i)
  - μ_false = (μ_true − Π_i f_i) / q
  - h = clamp(log(μ_true/μ_false), ±4). For k=3 this reduces to the pair of formulas above — expand to verify.
- **Vectorize with numpy** (this is what makes n=1536 feasible): build an (m,k) int matrix of signed literals → `sign`, `var` arrays; per-literal logits `H[var]*sign`; `p=sigmoid`, `f=1-p`, `gp=f+q*p`; `tot=gp.prod(axis=1,keepdims=True)`, `tot_f=f.prod(axis=1,keepdims=True)`; `μ_true=tot/gp`, `μ_false=(μ_true−tot_f/f)/q`; then `np.add.at(field, var.ravel(), (clip(h)*sign).ravel())`. Pure-Python loop 263s → numpy **1.0s at n=384, 12.7s at n=1536** (5-SAT ratio 22): 100% agreement, unsat=0.

## When it still fails
- If a seed still lands a paramagnetic fixpoint, anneal β (0.3→2.0) + multi-seed as above; the local-search cleanup closes single-digit unsat. Re-roll only as a last resort now that `-balanced-` is solvable.
- Verified unsat=0 on synthetic q-hidden at n≥1024. Take the `variables` count from the fragment/`rules` field before submitting — a wrong length is rejected by the verifier regardless of correctness.