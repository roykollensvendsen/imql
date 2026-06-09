# The simulator

A mechanism can be perfectly well-formed and still be a bad idea — if cheating pays better than honest work.
The simulator is what turns "looks fine" into "measured." You met it hands-on in
[Step 5 of the tutorial](../learn/tutorial/05-simulate.md); this page explains what it's actually doing and
how far to trust it.

## What it does

`tooling/simulate.py` instantiates a mechanism's structure — guards, aggregation, burn, sybil economics —
and runs a population of **strategic miners** (honest / lazy / sybil / plagiarist / colluder) against it for
N rounds, scoring each by the subnet's **actual metric spec** where it's expressible (**173/180** subnets).
It then reports: honest-dominant? gameable-by? concentration (Gini)? sybil-resistant? — and, with
`--equilibrium`, whether honest is the *evolutionary attractor* or the population collapses to a dominant
cheat.

The headline corpus finding (a stylized, directional model): **the aggregation method is the dominant
incentive lever**. Only the winner-take-all / tournament family is reliably honest-dominant (at the cost of
extreme concentration), while proportional-family methods are gameable unless guards and a real registration
barrier hold.

## Grounded in real chain economics

`tooling/chain.py` pulls *real* per-subnet economics from finney via bittensor — registration (recycle)
cost, burn, emission, on-chain stake-Gini, top-validator stake fractions — cached for offline use, so the
sybil barrier and stake distribution are no longer stylized. `tooling/simulate_cadcad.py` runs the model as
a **cadCAD** Monte-Carlo across N trajectories (a verdict reads "honest-dominant in X% of runs"). Six
analyses, none needing a real validator:

- **Monte-Carlo + reg-cost sweep** — robustness of the verdict, and the registration barrier needed for
  sybil-resistance vs the subnet's *actual* on-chain barrier (apex flips at reg_cost ~2.0 but its real
  `sybil_cost_ratio` is 0.17 → sybil-vulnerable).
- **Best-response + Goodhart** (`--attack`) — searches the attack space for the *optimal* deviation and lets
  it inflate the exact field the metric rewards; field-gaming is caught by verification guards. (apex: 5
  sybils + ×4 field-boost = 4.2× honest; affine: honest wins.)
- **Temporal** (`--temporal`) — does the real EMA smoothing let a ramp-then-defect miner free-ride? (slow
  α=0.05 → 1.28× exploit; no smoothing → safe.)
- **Yuma validator-collusion** (`--yuma`) — applies the verified clipped-median consensus to the real stake
  distribution: on netuids 1/4/8 a *single* validator (55–88% of stake) exceeds κ=50% and can unilaterally
  skew the weight consensus.
- **Chain calibration** (`--calibrate`) — concentration at two layers vs real on-chain emission Gini: the
  scoring-only Gini is uncorrelated (r ≈ 0), but the **effective Gini** — which layers the real dTAO emission
  split (validator dividends by on-chain stake + the registered-uid tail) over the scoring layer — tracks
  reality (**r ≈ 0.75** over 148 subnets).
- **Equilibrium dynamics** (`--equilibrium`) — replicator dynamics with a mutation floor: is honest the
  attractor, or does the population converge to a dominant cheat? `--equilibrium --corpus` agrees with the
  one-shot verdict on **91% of 180** mechanisms; the disagreements are the frequency-dependent cases (a cheat
  that pays only when rare, or one that self-limits once common — e.g. plagiarists need honest work to copy).

## Honest boundaries

The simulator is a **screen, not a proof**. Be precise about what each verdict is worth:

- **The economics are chain-grounded** (real registration cost, burn, stake-Gini from finney) where the chain
  is reachable. **But the submission semantics are still stylized**: there is no per-subnet schema for *what a
  miner actually delivers*, so a miner is an abstract quality/effort/cheat profile and `submission.<field>` is
  derived from one quality axis. The mechanism's *shape* and *economics* are faithful; the per-field
  submission *content* is not. Read a verdict as a strong, chain-grounded hypothesis — triage, not a proof of
  a runnable exploit.
- **Validated where it counts** (`tooling/validate_sim.py`, 148 chain-confirmed subnets): the
  **sybil-resistance verdict agrees** with the real registration barrier. Concentration is reported at two
  layers — the **scoring-only Gini is uncorrelated** with real emission Gini (r ≈ 0), because real reward
  concentration is validator-stake-driven, not scoring-driven; the **effective Gini** folds in the real
  validator-stake dividend layer + the registered-uid tail and **tracks reality (r ≈ 0.75)**. Trust the
  effective Gini and the strategic / sybil / economic verdicts; the scoring-only Gini is the within-miner
  signal, not the headline.
- **Still unvalidated**: the honest-dominant / gameable verdicts themselves — there is no clean on-chain "is
  this gamed" signal to correlate against. They're the best available screen, not ground truth.

!!! note "Not on the public site"
    The per-subnet "gameable" verdicts are reputationally sensitive, so the simulator suite is not published
    as a gallery. It's a tool you run locally (`tooling/simulate.py <instance>.yaml`), as in the
    [tutorial](../learn/tutorial/05-simulate.md).
