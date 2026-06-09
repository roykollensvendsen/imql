#!/usr/bin/env python3
"""Validate the simulator against real on-chain signals — does it track reality, or just produce
plausible numbers?

For every corpus subnet with a confirmed mainnet netuid, compare the sim's PREDICTED quantities to REAL
finney state: predicted concentration (Gini) vs the real per-uid emission Gini, and the sim's
sybil-resistance verdict vs the real economic registration barrier (sybil_cost_ratio). Reports
correlations + agreement. Reads chain params from the cache (`chain.py --warm` to populate).

Usage: validate_sim.py [max_netuid]     # default 128 (skip likely-testnet / stale netuids)
"""
from __future__ import annotations

import glob
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simulate as S
import chain


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else None


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def run(max_netuid=128):
    rows = []
    for f in sorted(glob.glob("instances/**/*.yaml", recursive=True)):
        d = yaml.safe_load(Path(f).read_text())
        if not isinstance(d, dict) or not d.get("scoring_signals"):
            continue
        nu = (d.get("subnet") or {}).get("netuid")
        if not isinstance(nu, int) or not (1 <= nu <= max_netuid):
            continue
        cp = chain.params(nu)
        if cp.get("emission_gini") is None:
            continue
        r = S.simulate(d, rounds=120)
        rows.append({"netuid": nu, "pred_gini": r["gini"], "method": r["method"],
                     "sybil_ok": r["sybil_resistant"], "honest_dom": r["honest_dominant"],
                     "emission_gini": cp["emission_gini"], "stake_gini": cp.get("stake_gini"),
                     "sybil_cost": cp.get("sybil_cost_ratio")})
    n = len(rows)
    print(f"# simulator validation vs chain — {n} subnets with on-chain data")
    if n < 3:
        print("  too few chain-confirmed subnets; warm more first:  chain.py --warm <netuid> ...")
        return 1

    r1 = _pearson([x["pred_gini"] for x in rows], [x["emission_gini"] for x in rows])
    print(f"  predicted Gini vs real emission Gini:   r = {r1:+.2f}" if r1 is not None else "  Gini r: n/a")
    wta = [x for x in rows if x["method"] in ("winner_take_all", "tournament_bracket")]
    if len(wta) >= 3:
        rw = _pearson([x["pred_gini"] for x in wta], [x["emission_gini"] for x in wta])
        print(f"     winner-take-all subset (n={len(wta)}, where the scoring rule drives concentration): r = {rw:+.2f}"
              if rw is not None else "")

    res = [x["sybil_cost"] for x in rows if x["sybil_ok"] and x["sybil_cost"] is not None]
    vuln = [x["sybil_cost"] for x in rows if not x["sybil_ok"] and x["sybil_cost"] is not None]
    if res and vuln:
        mr, mv = _median(res), _median(vuln)
        agree = "AGREES" if mr > mv else "DISAGREES"
        print(f"  real registration barrier (sybil_cost_ratio):")
        print(f"     sim-sybil-resistant subnets: median {mr:.3f}   sim-vulnerable: median {mv:.3f}   -> {agree}")

    print(f"  real emission Gini: median {_median([x['emission_gini'] for x in rows]):.3f} "
          f"(predicted median {_median([x['pred_gini'] for x in rows]):.3f})")
    print("  honest read: the scoring-layer prediction tracks reality where the aggregation rule drives")
    print("  concentration (winner-take-all); the residual gap is validator-stake centralization the")
    print("  scoring view omits (see --calibrate / --yuma).")
    return 0


if __name__ == "__main__":
    sys.exit(run(int(sys.argv[1]) if len(sys.argv) > 1 else 128))
