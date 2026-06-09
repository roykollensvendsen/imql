# Why IMML exists

## The problem, in plain terms

[Bittensor](../reference/glossary.md) is a network of independent markets called **subnets**. In each
subnet, *miners* do some work — run a model, make a prediction, produce an answer — and *validators* score
that work and pay out rewards. The rule that decides **how miners are scored and paid** is the heart of
every subnet. Get it right and the subnet rewards real work; get it wrong and it rewards whoever games it
best.

Today, every subnet hand-writes that rule in its own validator code. There is no shared way to **describe**
a mechanism precisely, **compare** two of them, **check** one for holes, or **stress-test** it before
launch. The design that decides where millions in emission flow lives as undocumented Python, different in
every repo.

IMML is a language for writing that rule down — once, precisely — so it can be read, compiled, generated,
and simulated.

## The insight that makes it possible

If every mechanism were a unique snowflake, a shared language would be hopeless. The key empirical finding —
drawn from reverse-engineering **189 real subnets** — is that they aren't:

> **The structure recurs. The metric doesn't.**

Think of a recipe. Every recipe is built from the same handful of verbs — *chop, mix, heat, rest* — and the
diversity lives entirely in the **ingredients**. Mechanisms are the same. How you *aggregate* scores, *smooth*
them across rounds, *publish* weights, and *guard* against cheating — these come from a small, reusable
vocabulary that shows up again and again. Only one part is genuinely bespoke to each subnet: the **metric**,
the exact function that scores one submission.

So IMML does something deliberate: it captures all the recurring structure as reusable
[primitives](../reference/glossary.md), and it isolates the metric as a single, explicit, typed **hole** —
rather than pretending it follows a pattern it doesn't. Everything you describe sits around that hole.

--8<-- "docs/_snippets/diagram-anatomy.md"

That picture is the whole language. The [mental model](mental-model.md) page unpacks it.

## What that buys you

Once a mechanism is written in IMML, four things become possible — each one a link to where you can do it:

- **Describe** — read any subnet's incentive design at a glance instead of tracing validator code. Browse
  all 189 in the [examples gallery](../examples/index.md).
- **Compile** — turn the readable form into a schema-validated machine form (the *IR*), and back, losslessly.
- **Generate** — emit a runnable validator scaffold, with the plumbing written and the bespoke metric clearly
  marked for you to fill.
- **Simulate** — run strategic miners against the mechanism and find out, *before* launch, whether honest
  work actually wins.

## At a glance

| | |
| --- | --- |
| Real subnets the language was derived from | **189** |
| That round-trip through IMML losslessly | **100%** |
| Captured by reusable structure (the rest is the metric hole) | **95.8%** |
| Reusable primitives | **~50** |
| Combinator shapes | **4** |

---

The fastest way to understand IMML is to build one. **[Start the tutorial →](tutorial/index.md)**
