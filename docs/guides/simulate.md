# Simulate a mechanism

Find out whether honest work actually wins — before you ship.

```bash
./.venv/bin/python tooling/simulate.py <instance>.yaml
```

This runs a population of strategic miners (honest / lazy / sybil / plagiarist / colluder) against the
mechanism's structure and prints a verdict.

## Reading the verdict

The key column is **reward per unit of effort, with honest = 1.00**. Anything above 1.00 is a strategy that
out-earns honest work — it pays to cheat that way.

- **`honest-dominant?`** — the headline. `NO` means some strategy beats honest effort.
- **`gameable-by:`** — which strategies win, and by how much.
- **`concentration:`** — how unequally reward is distributed (the **effective Gini** is the credible one; see
  [the simulator](../understand/simulator.md)).
- **`sybil-resistant?`** — whether splitting into many identities pays.

[Step 5 of the tutorial](../learn/tutorial/05-simulate.md) reads a real verdict in full and fixes a flaw it
finds.

## The deeper modes

| command | asks |
| --- | --- |
| `simulate.py --attack <i>` | what's the *optimal* attack (best-response + Goodhart field-gaming)? |
| `simulate.py --equilibrium <i>` | is honest the *evolutionary attractor*, or does the population collapse to a cheat? |
| `simulate.py --calibrate <i>` | does predicted concentration match the real on-chain emission Gini? |
| `simulate_cadcad.py --sweep-reg <i>` | what registration barrier makes it sybil-resistant? |
| `simulate_cadcad.py --temporal <i>` | does EMA smoothing let a ramp-then-defect miner free-ride? |
| `simulate_cadcad.py --yuma <i>` | can a validator stake-bloc skew the weight consensus? |

`simulate.py --corpus instances` runs the whole corpus at once.

!!! warning "A screen, not a proof"
    Verdicts are strong, chain-grounded *hypotheses* — triage, not a guarantee about the deployed subnet. The
    mechanism's shape and economics are faithful; the submission content is stylized. The
    [simulator explainer](../understand/simulator.md) covers exactly what's validated and what isn't.
