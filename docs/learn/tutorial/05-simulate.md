# Step 5 — Simulate and read the verdict

Here's the part that makes IMML more than a notation. The simulator runs a population of **strategic
miners** — honest, lazy, sybil, plagiarist, colluder — against your mechanism's structure and tells you who
actually wins.

```bash
./.venv/bin/python tooling/simulate.py price-oracle.yaml
```

```text
# incentive simulation: price-oracle
  aggregation: proportional   burn: 0%
  guards: deterministic_check
  reward model: spec  ->  rate(submission.correct)
  reward / effort (honest = 1.00):
      honest       1.00  <- honest
      lazy         0.34
      sybil        5.00  <- GAMES IT
      plagiarist  20.00  <- GAMES IT
      colluder     3.03  <- GAMES IT
  honest-dominant?  NO
  gameable-by:      plagiarist (+1900% reward/effort), sybil (+400% reward/effort), colluder (+202% reward/effort)
  concentration:    effective Gini 0.926 (real stake+uid layer)   |   scoring-layer Gini 0.047
  sybil-resistant?  NO
```

## Reading the verdict

The key column is **reward per unit of effort, with honest set to 1.00**. Anything above 1.00 means *that
strategy out-earns honest work per unit of effort* — it pays to cheat that way.

- **`plagiarist 20.00`** — catastrophic. A plagiarist copies an honest miner's accurate forecast for almost
  no effort and, under proportional payout with no anti-copying guard, earns **20× honest reward per effort**.
- **`sybil 5.00`** — one actor splitting into many identities earns 5×.
- **`colluder 3.03`** — a coordinated group mutually inflating earns 3×.
- **`honest-dominant? NO`** — the headline. Honest work is *not* the rational strategy here. This mechanism
  would reward cheaters.

!!! danger "We have a problem — and we found it before shipping"
    This is exactly the hole we left open in [Step 1](01-design.md). A proportional payout with no
    anti-copying guard is dominated by plagiarism. Imagine discovering this *after* launch, on-chain, with
    real emission. We found it in one command.

## Fix it: add a guard

The plagiarist's whole game is *copying* good work. The counter is a guard that detects duplicates. Add two
guards to your `@guards` block — `Deduplication` to catch copying, and `Collateral` to make running many
identities cost something:

```text
    @guards {
        DeterministicCheck {
            enforcement: rejection
        }
        Deduplication {
            enforcement: penalty
        }
        Collateral {
            enforcement: barrier
        }
    }
```

Recompile and re-simulate:

```bash
./.venv/bin/python tooling/compile.py price-oracle.imml > price-oracle.yaml
./.venv/bin/python tooling/simulate.py price-oracle.yaml
```

```text
  reward / effort (honest = 1.00):
      honest       1.00  <- honest
      lazy         0.20
      sybil        2.14  <- GAMES IT
      plagiarist   0.31
      colluder     0.17
  honest-dominant?  NO
  gameable-by:      sybil (+114% reward/effort)
```

**Plagiarism is dead** — the plagiarist dropped from 20× to 0.31× (copying now gets caught and penalized),
and the colluder collapsed too. One guard closed two attacks.

## The lesson that doesn't fit in a guard

But look closely: **`sybil 2.14` still games it**. Why didn't `Collateral` kill it?

Because sybil isn't a *detection* problem — you can't catch someone for running many honest-looking
identities. It's an *economic* one: splitting pays as long as registering a new identity is cheap. The
simulator is using a stylized registration cost here; whether sybil *really* pays depends on the subnet's
actual on-chain registration cost. That's why IMML's simulator can ground itself in **real chain
economics** — and it's the boundary where structure ends and economics begin.

!!! warning "The simulator is a screen, not a proof"
    A verdict is a strong, fast hypothesis — "this design has a plagiarism hole" — not a guarantee about the
    deployed subnet. The submission model is stylized; the mechanism's *shape* is faithful. Read verdicts as
    triage: they tell you where to look. See [the full picture](../../pipeline.md) for how the chain-grounded
    modes (`--attack`, `--calibrate`, `--equilibrium`) sharpen them.

## What just happened

You used the simulator to catch a fatal flaw, fixed it with a one-line guard, and learned where a guard
*can't* help. You now know more about your mechanism than most live subnets know about theirs — before
writing a single line of scoring code.

---

**[Step 6: Where to go next →](06-next.md)**
