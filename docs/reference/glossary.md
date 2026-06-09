# Glossary

Plain-English definitions for the terms IMML uses. If a word in the docs trips you up, it's probably here.
Terms in *italics* have their own entry.

### aggregate
The pipeline stage that turns per-miner *scores* into a weight vector — the rule for *who gets paid how
much*. Examples: proportional, winner-take-all, rank-based. See the [primitives](index.md).

### Bittensor
The decentralized network IMML describes mechanisms for. It is split into *subnets*, each an independent
market where *validators* score *miners* and the chain pays out emission accordingly.

### burn
An *overlay* that diverts a fraction of a subnet's emission to nobody (it is destroyed) instead of paying
miners — used to throttle inflation or penalize a whole subnet.

### combinator
The skeleton of a mechanism — one of four shapes (`pipeline`, `multiplex`, `gate`/`product`, `leaf`) that
says how scoring is structured. See [the mental model](../learn/mental-model.md).

### emission
The TAO/alpha a *subnet* pays out each epoch, split between miners (incentive), validators (dividends), and
the subnet owner.

### extern
An explicit marker in IMML for the bespoke part of a metric that the language deliberately does **not**
model — the *hole*. A clean compile with an `extern` leaf means "this judgment must be hand-written."

### gameable
A mechanism is gameable if some strategy earns more reward per unit of effort than honest work — i.e. it
pays to cheat. The [simulator](../understand/simulator.md) measures this.

### ground-truth source
What a *score* is measured against: a dataset, a reference model, on-chain data, human review, or peer
consensus. Carries a *trust model* (how much the source itself can be trusted).

### guard
An anti-gaming rule, applied as an *overlay* (`@guards`). A guard can reject, penalize, or barrier a
submission — e.g. deduplication, deterministic checks, commit-reveal, collateral. See the
[primitives](index.md).

### IR
The **i**ntermediate **r**epresentation: the schema-validated YAML a mechanism compiles to. IMML (the
readable surface) and the IR (the machine form) are two views of the same thing, converted by *lift* and
*compile*.

### lift / compile
The two halves of the round-trip. **compile** turns IMML text into the *IR* YAML; **lift** turns the IR
back into IMML. They are exact inverses over a mechanism's structure (*round-trip* fidelity).

### MDL
Minimum Description Length — the information-theoretic idea behind IMML's central claim: the *metric* tail
is irreducible not because metrics are impossible to describe, but because they don't compress (each is
genuinely distinct). See [the theory](../understand/theory.md).

### metric
The function that scores one miner's *submission* — the `score` stage. The one part of a mechanism that is
bespoke to every subnet; IMML treats it as the *hole*. See the
[metric spec language](../language/metric-spec.md).

### metric hole
IMML's core design move: isolate the *metric* as a single explicit, typed gap in an otherwise fully-specified
mechanism, rather than pretending it follows a general pattern. The reason the language exists — see
[Why IMML](../learn/why.md).

### miner
A participant in a *subnet* that does the work (runs a model, produces an answer) and is scored for reward.

### multiplex
A *combinator* shape where several scoring tracks run in parallel and are then combined.

### overlay
A cross-cutting rule that wraps the whole *combinator* — `@guards`, `@burn`, or `@state`. See
[the mental model](../learn/mental-model.md).

### pipeline
The most common *combinator* shape (≈89% of subnets): one line of work, `score → aggregate → smooth →
publish`.

### primitive
A reusable building block drawn from a closed vocabulary — an aggregator, a smoother, a guard, a
ground-truth source, etc. The opposite of the bespoke *metric*. Browse them in the [reference](index.md).

### round-trip
Compiling IMML to the *IR* and lifting it back yields the same structure. IMML guarantees 100% round-trip
fidelity across all 189 corpus subnets — the invariant that keeps the two forms honest.

### score
The pipeline stage that rates a single *submission* (the *metric*). Also used loosely for the number it
produces.

### smooth
The pipeline stage that blends this round's scores with history (e.g. an exponential moving average) before
weights are published.

### submission
What a *miner* sends in to be scored — a prediction, a file, an answer, a model output.

### subnet
An independent market within *Bittensor*, identified by a `netuid`, with its own incentive mechanism.

### sybil
An attack where one actor runs many identities to capture more reward than a single honest participant.
Countered by economic *guards* (registration cost, collateral) rather than detection.

### validator
A participant in a *subnet* that scores *miners* and sets the on-chain weights that determine *emission*.

### Yuma consensus
Bittensor's mechanism for combining many validators' weight reports into one consensus, by stake-weighted
clipped median. Relevant to whether a validator bloc can skew rewards — see [the simulator](../understand/simulator.md).
