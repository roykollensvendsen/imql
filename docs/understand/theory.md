# Theory: why this framing is right

IMML's central move — treat the metric as an irreducible hole — invites a fair challenge: *is the metric
tail really irreducible, or did we just not try hard enough to systematize it?* This page is the honest
answer, grounded in primary sources (`reports/metric-language-research.md`, an adversarially-verified
literature pass).

## Compressibility, not impossibility

The right frame is **information-theoretic**: describing the metric tail is a question of *compressibility*
(how much shorter than the raw text can a faithful description be?), captured by
[Minimum Description Length / MDL](../reference/glossary.md) — **not** a question of *impossibility*.

The distinction matters, and three results pin it down:

- **No minimality proof exists.** Kolmogorov complexity — the length of the shortest program that reproduces
  a string — is *uncomputable*. So no one can prove a given metric description is the shortest possible. We
  can measure compression empirically (and [we did](metric-hole.md): ~0.7 generator-calls per tail metric),
  but not prove a lower bound.
- **Strict impossibility is false.** Every *computable* metric is, by definition, describable. So the tail is
  not "impossible to express" — which is exactly why 85% of it collapses into a few generators once you stop
  looking at surface names.
- **The diversity is expected.** No-Free-Lunch theorems explain why no single metric is universally best:
  different subnets optimize genuinely different things, so a flat, non-recurring surface tail is the
  *predicted* outcome, not a failure of design.

## Why the spec language stays total

The metric algebra is deliberately bounded to a **total** combinator set (in the sense of total functional
programming, à la Turner): every term provably terminates. That sidesteps the halting problem *by
construction* — a metric spec can't loop forever — which is what lets the evaluator and type-checker be
sound. The algebra already has this property.

## Honest boundary

The compressibility conclusions are primary-sourced and hold up. The **Bittensor- and
simulator-framework-specific** regions of the research are partly unverified — they're the engineering claims
(how the chain economics map, how faithful the cadCAD model is) rather than the information-theoretic core.
Trust the MDL framing; treat the framework specifics as well-motivated engineering, not settled theory.
