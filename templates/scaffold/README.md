# Generation scaffold

`tooling/generate.py` compiles an IMQL IR instance into a runnable Python validator scaffold here's
shape:

- `metric_library.py` — canonical, reusable `score()` primitives keyed by metric **family**
  (Sharpe/Sortino, F1/FPR, CRPS, cosine similarity, PnL …). These are the generable "plumbing" the
  corpus proved recurs. Generated scaffolds `import metric_library`.
- A generated `validator_<name>.py` contains: one `score_i()` per scoring signal (a real primitive
  call when the metric family resolves, else a `NotImplementedError` hand-write stub for the bespoke
  long-tail metric), an `aggregate()` implementing the aggregation method, a `smooth()` (EMA/SMA), a
  `run_epoch()` wiring it to the weight-setter, and anti-gaming/burn hooks.

The generated file embeds `MECHANISM = json.loads(...)` — its structural signature — so the
regeneration test (`generate.py --check`) can confirm the scaffold faithfully carries the IR's
structure (and that it is valid Python). It does NOT carry the bespoke judgment: every `extern` leaf
is a visible `NotImplementedError`, never silently wrong.

Scope: the dominant `pipeline` archetype. Other archetypes generate a best-effort flat pipeline with a
header note; `opaque` mechanisms generate stub-only.
