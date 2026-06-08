# Research: formalizing the incentive-metric long tail

Consolidated findings from two adversarially-verified deep-research passes (fan-out web search →
fetch → 3-vote verification → synthesis) on how to formally describe Bittensor-style incentive
mechanisms and especially their bespoke scoring-metric **long tail**. Confidence and gaps are flagged
honestly; `[primary]` marks a primary source, `[unverified]` marks a claim no verified source backed.

---

## Part 1 — Theory: is the tail formally describable? (Track A, 25/25 claims verified 3-0)

The honest, now primary-sourced conclusion: **the long tail is a compressibility / MDL question, not a
decidability / impossibility one.** No formal impossibility theorem applies. Point by point:

1. **You can never *prove* a grammar minimal.** Kolmogorov complexity `K(x)` (length of the shortest
   program printing `x`) is **uncomputable**; no computable function approximates it, and any computable
   function that lower-bounds `K` is bounded. So the *true* minimal description size of the metric set is
   formally out of reach. [primary: Li & Vitányi; Musatov–Ishkuvatov, CiE 2019]

2. **But strict non-describability is FALSE.** Every *computable* metric is printed by *some* program, so
   a sufficiently expressive language trivially describes the whole tail. "It can't be done" does not
   hold. The real question is *how short* a reusable description is. [primary: Vitányi–Li]

3. **MDL is the right, computable frame.** The Minimum Description Length principle replaces the
   uncomputable `K` with a **two-part code** `L(M) + L(D|M)` over a *bounded* description method — a
   practical, computable compressibility measure. Our empirical result (64/75 ≈ 85 % of corpus metrics
   expressible at a mean of 0.7 generator-calls each — `tooling/metric_spec.py --report`) is exactly an
   **MDL upper bound**: it proves the tail is *at least this compressible*, which is all one can prove.
   [primary: Grünwald; arXiv:2007.14009]

4. **No-Free-Lunch explains the diversity, not inexpressibility.** Averaged over all problems, all
   optimizers (Wolpert–Macready 1997) and all learning/evaluation algorithms (Wolpert 1996, incl. when
   one is cross-validation) perform identically — there is *no a priori best* metric. So the tail's
   diversity is theoretically *expected* and justifies the typed-hole design (don't hardcode one metric);
   NFL says **nothing** about describability. [primary: Wolpert 1996 *Neural Computation* 8(7):1341;
   Wolpert–Macready 1997]

5. **Rice cuts toward *declared, not inferred* taxonomy — and toward a *bounded* spec language.** Any
   non-trivial semantic property of arbitrary programs is undecidable (Rice [secondary: Wikipedia]), so
   you cannot in general *decide* whether a bespoke metric program is proper / monotone / equivalent to
   another — hence the taxonomy tags must be **declared by the author**, not inferred from code. The
   constructive escape: **deliberately bound the spec language below Turing-completeness.** A *total
   functional* / primitive-recursive language guarantees every spec terminates and **sidesteps the
   halting problem by construction** (at the documented cost of not expressing its own interpreter /
   Ackermann-level growth). [primary: Turner, *Total Functional Programming*; Exanoke]

> **Design consequence for IMML.** The Layer-2 metric algebra (`spec/06`) is already a *bounded, total,
> non-recursive* combinator set — no loops, no general recursion. Point 5 says that is the *right* choice:
> every `spec:` provably terminates and is decidably well-formed (we type-check it), and we accept — by
> design, not by failure — that we cannot prove the generator set is the smallest possible. The MDL number
> is the honest substitute for a minimality proof.

---

## Part 2 — Prior-art landscape (Track from the first pass)

The two layers IMML needs both have concrete prior art.

**Taxonomy layer — classify metrics by computable predicates, not names.**
- Absolute vs relative (reference-free vs reference-based) and by learning-problem type. [primary:
  arXiv:2507.03392]
- Five iff-predicates over the confusion matrix (monotonicity, class sensitivity, class decomposability,
  prevalence invariance, chance correction). [primary: arXiv:2404.16958]
- Tiered scope generic / task-specific / dataset-specific. [primary: HuggingFace `evaluate`]
- Implementation template that validates IMML's `Metric` model: `metric_list` with per-entry
  `metric` / `aggregation` / `higher_is_better` + a `@register_metric` escape hatch. [primary:
  EleutherAI lm-eval-harness]

**Spec-language layer — define metrics mathematically.**
- Proper scoring rules: `S(P,x)` proper iff truthful reporting maximises expected score; every regular
  proper rule ≅ a convex generator `G` (Bregman divergence). One `G` parameterises a whole family.
  [primary: Gneiting–Raftery, JASA 2007] — implemented as `score_rule(G, …)`.
- Energy score / CRPS: one parameterised family covers a continuum of proper metrics. [primary:
  Gneiting–Raftery]
- Reference-free tail: peer prediction [primary: Miller–Resnick–Zeckhauser 2005] and Surrogate Scoring
  Rules [primary: arXiv:1802.09158] — score against peers, dominant truthfulness, no ground truth →
  the `peer_score` generator.

**Connecting architecture — separate description from valuation.**
- Composing Contracts (~12 combinators + denotational semantics; one description, swappable evaluators)
  [primary: Peyton Jones et al., ICFP 2000]; Catala law-as-code [primary]; FINOS CDM / Rune DSL
  [primary]. This is exactly IMML's split: a `spec:` *describes*, `metric_spec.evaluate` *computes*.

---

## Part 3 — Bittensor + simulation (Track B; thinner — flagged)

- **Yuma Consensus is a clipped, stake-weighted median.** The consensus weight is the largest `w` such
  that the stake-weighted fraction of validators assigning `W_ij` above `w` meets `kappa`; each
  validator's weights above consensus are clipped to `min(raw, consensus)`. [primary: subtensor
  `docs/consensus.md`] Structurally this is **robust aggregation** (a stake-weighted median with
  outlier-clipping), which maps to IMML's `aggregate` layer — **not** the metric. Whether it is best read
  as a proper-scoring-rule or a peer-prediction/output-agreement scheme is **[unverified]** (open
  question); the median-with-clipping form is closer to robust statistics than to either.
- **dTAO** (dynamic-TAO subnet-token mechanics) — primary references exist (Bittensor dTAO whitepaper;
  arXiv:2507.02951) but no specific claim was verified in this pass; treat as reading list, not settled.
- **Mechanism simulator.** cadCAD and TokenSPICE were fetched as primary sources but **no specific
  framework claim survived verification** [unverified]. On general grounds: cadCAD (generalized
  state-update + policy functions, Monte Carlo, parameter sweeps) is the natural substrate for the
  planned simulator — instantiate an IMML spec, drive strategic miner policies (honest/lazy/sybil/
  plagiarist/colluder), and use `metric_spec.evaluate(spec, ctx)` as the per-agent reward to *measure*
  incentive-compatibility. This recommendation is **not source-verified** and should be confirmed.

---

## Confidence & gaps

- **Part 1 (theory): high** — 25/25 claims verified 3-0 against primary sources. Rice's theorem itself is
  only secondary-sourced (Wikipedia); the conclusions that depend on it are about *design direction*
  (declare-don't-infer; bound the language), which Turner/primitive-recursion sources back directly.
- **Part 2: high** — primary sources throughout; vendor docs (HuggingFace) authoritative only for their
  own framework.
- **Part 3: mixed** — Yuma form is primary-verified; its scoring-rule classification, dTAO specifics, and
  the simulator-framework choice are **unverified** and need a dedicated pass before being relied on.

## Sources (verified primary, selected)

- Li & Vitányi, *Kolmogorov complexity* — homepages.cwi.nl/~paulv/kolmogorov.html; Musatov–Ishkuvatov
  (CiE 2019); Galbrun arXiv:2007.14009 (MDL); Grünwald (MDL).
- Wolpert 1996, *The Lack of A Priori Distinctions* — `10.1162/neco.1996.8.7.1341`; Wolpert–Macready 1997.
- Turner, *Total Functional Programming* — ncatlab.org/ufias2012/files/turner.pdf; Exanoke
  (github.com/catseye/Exanoke).
- Gneiting–Raftery 2007 (JASA); Miller–Resnick–Zeckhauser 2005 (Mgmt Sci); SSR arXiv:1802.09158.
- Peyton Jones et al., *Composing Contracts* (ICFP 2000); Catala; FINOS CDM.
- Bittensor: subtensor `docs/consensus.md`; dTAO whitepaper; arXiv:2507.02951.
