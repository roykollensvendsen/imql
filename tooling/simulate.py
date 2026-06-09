#!/usr/bin/env python3
"""IMML mechanism simulator (MVP) — measure incentive-compatibility.

Instantiates a mechanism's STRUCTURE (its anti-gaming guards, aggregation method/composition, and burn)
and runs a population of strategic miners against it for N rounds, then reports whether honest effort is
the rational strategy or whether someone can game it.

This is a STYLIZED model, not a faithful per-subnet replay: we do not have each subnet's submission schema,
so a miner's output is abstracted to a (quality, effort, cheat-type) profile. What is faithful is the
mechanism's *shape* — which cheats its guards catch, how scores become weights, and how burn redirects
emission — so the directional findings (is winner-take-all sybil-prone? do the guards stop plagiarism?
does burn change concentration?) reflect the real design choices. Per-signal `spec:` evaluation
(tooling/metric_spec.evaluate) is the next refinement.

Usage:
    simulate.py instances/corpus/<subnet>.yaml [rounds]
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import yaml

# guard kind -> the cheat it neutralises (best-effort mapping over the corpus's anti_gaming vocabulary)
CATCHES = {
    "plagiarism": {"plagiarism_detection", "deduplication", "content_hash", "code_inspection", "honeypot"},
    "sybil":      {"proof_of_work", "collateral", "hardware_validation", "registration_cost", "stake"},
    "low_effort": {"liveness_check", "spot_check", "challenge_period", "deterministic_check", "commit_reveal"},
    "collusion":  {"deduplication", "peer_review", "honeypot"},
}

# strategy -> (n_identities, quality_mean, effort_per_identity, cheat_type)
#   effort is the cost the miner pays; reward/effort is the incentive signal that matters.
STRATEGIES = {
    "honest":     (1, 0.80, 1.00, None),
    "lazy":       (1, 0.30, 0.30, "low_effort"),
    "sybil":      (5, 0.50, 0.20, "sybil"),        # split one effort budget across 5 identities
    "plagiarist": (1, 0.80, 0.05, "plagiarism"),   # copies an honest output: high quality, ~no effort
    "colluder":   (3, 0.50, 0.33, "collusion"),    # coordinated group, mutually boosting
}
N_HONEST_FIELD = 10   # background honest miners (the field everyone competes in / plagiarises from)


def _caught(cheat, guard_kinds, rng):
    if cheat is None:
        return False
    guarded = CATCHES.get(cheat, set()) & guard_kinds
    return bool(guarded) and rng.random() < 0.9   # a matching guard neutralises the cheat 90% of the time


def _weights(raw, method):
    """Turn raw per-identity scores into normalized weights, per the mechanism's aggregation method."""
    n = len(raw)
    if max(raw) <= 0:
        return [0.0] * n
    if method in ("winner_take_all", "tournament_bracket"):
        w = [0.0] * n
        w[raw.index(max(raw))] = 1.0
        return w
    if method == "rank_based":
        order = sorted(range(n), key=lambda i: raw[i])
        rankw = [0.0] * n
        for rank, i in enumerate(order):
            rankw[i] = rank + 1
        s = sum(rankw)
        return [x / s for x in rankw]
    s = sum(raw)                                   # proportional (the default)
    return [x / s for x in raw]


def gini(xs):
    xs = sorted(x for x in xs if x >= 0)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def simulate(ir: dict, rounds: int = 200, seed: int = 7) -> dict:
    rng = random.Random(seed)
    agg = ir.get("aggregation") or {}
    method = agg.get("method") or "proportional"
    composition = agg.get("composition")
    burn = agg.get("burn_allocation") or {}
    burn_frac = 0.0
    if burn.get("enabled") or "burn" in set((ir.get("composition") or {}).get("overlays") or []):
        bf = burn.get("fraction")
        burn_frac = 0.5 if (bf is None or burn.get("dynamic")) else float(bf)
    guard_kinds = {a.get("kind") for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)}

    earned = {s: 0.0 for s in STRATEGIES}          # total emission per strategy
    effort = {s: STRATEGIES[s][0] * STRATEGIES[s][2] for s in STRATEGIES}
    all_identity_totals = []

    for _ in range(rounds):
        ids = []   # (strategy, raw_quality)
        # background honest field
        honest_qs = [max(0.0, rng.gauss(0.80, 0.10)) for _ in range(N_HONEST_FIELD)]
        for q in honest_qs:
            ids.append(("_field", q))
        # the strategic test miners
        for s, (k, qmean, _eff, cheat) in STRATEGIES.items():
            for _ in range(k):
                if cheat == "plagiarism":
                    q = rng.choice(honest_qs)                       # copy a real honest output
                elif cheat == "collusion":
                    q = max(0.0, rng.gauss(qmean, 0.10)) + 0.20      # mutual boost
                else:
                    q = max(0.0, rng.gauss(qmean, 0.10))
                if _caught(cheat, guard_kinds, rng):
                    q = 0.0
                ids.append((s, q))

        raw = [q for _, q in ids]
        w = _weights(raw, method)   # burn scales every miner equally -> it doesn't change relative
        for (s, _), wi in zip(ids, w):   # incentives or concentration, so it is reported, not applied
            if s in earned:
                earned[s] += wi
            all_identity_totals.append(wi)

    # incentive report
    rpe = {s: (earned[s] / effort[s] / rounds) for s in STRATEGIES}   # reward per unit effort, per round
    base = rpe["honest"] or 1e-9
    rel = {s: rpe[s] / base for s in STRATEGIES}                      # honest == 1.0
    honest_dominant = all(rpe["honest"] >= rpe[s] - 1e-9 for s in STRATEGIES)
    gameable = sorted(((s, rel[s]) for s in STRATEGIES if s != "honest" and rel[s] > 1.0),
                      key=lambda kv: -kv[1])
    sybil_resistant = earned["sybil"] <= earned["honest"] + 1e-9
    return {
        "method": method, "composition": composition, "burn_fraction": round(burn_frac, 3),
        "guards": sorted(guard_kinds),
        "reward_per_effort_rel": {s: round(rel[s], 2) for s in STRATEGIES},
        "honest_dominant": honest_dominant,
        "gameable_by": [(s, round(r, 2)) for s, r in gameable],
        "gini": round(gini(all_identity_totals), 3),
        "sybil_resistant": sybil_resistant,
    }


def _print(name: str, r: dict):
    print(f"# incentive simulation: {name}")
    print(f"  aggregation: {r['method']}" + (f" / {r['composition']}" if r['composition'] else "")
          + f"   burn: {int(r['burn_fraction']*100)}%")
    print(f"  guards: {', '.join(r['guards']) or '(none)'}")
    print(f"  reward / effort (honest = 1.00):")
    for s, v in r["reward_per_effort_rel"].items():
        flag = "  <- honest" if s == "honest" else ("  <- GAMES IT" if v > 1.0 else "")
        print(f"      {s:11} {v:>5.2f}{flag}")
    print(f"  honest-dominant?  {'yes' if r['honest_dominant'] else 'NO'}")
    if r["gameable_by"]:
        print("  gameable-by:      " + ", ".join(f"{s} (+{int((v-1)*100)}% reward/effort)" for s, v in r["gameable_by"]))
    print(f"  concentration:    Gini {r['gini']}")
    print(f"  sybil-resistant?  {'yes' if r['sybil_resistant'] else 'NO'}")


def _corpus(root: str, rounds: int = 120) -> None:
    """Aggregate incentive findings across a directory of instances, broken down by aggregation method."""
    import glob
    from collections import Counter, defaultdict
    paths = sorted(glob.glob(f"{root}/**/*.yaml", recursive=True))
    n = 0
    dom = 0
    sybil_ok = 0
    exploiter = Counter()
    by_method = defaultdict(lambda: [0, 0])   # method -> [count, honest_dominant_count]
    for p in paths:
        ir = yaml.safe_load(Path(p).read_text())
        if not isinstance(ir, dict) or not (ir.get("scoring_signals")):
            continue
        r = simulate(ir, rounds)
        n += 1
        dom += r["honest_dominant"]
        sybil_ok += r["sybil_resistant"]
        for s, _ in r["gameable_by"]:
            exploiter[s] += 1
        m = by_method[r["method"]]
        m[0] += 1
        m[1] += r["honest_dominant"]
    print(f"# corpus incentive sweep — {n} mechanisms, {rounds} rounds each (STYLIZED model)")
    print(f"  honest-dominant:   {dom}/{n} ({100*dom//n}%)")
    print(f"  sybil-resistant:   {sybil_ok}/{n} ({100*sybil_ok//n}%)")
    print(f"  exploited by:      " + ", ".join(f"{s} {c}" for s, c in exploiter.most_common()))
    print(f"  honest-dominant by aggregation method:")
    for m, (c, d) in sorted(by_method.items(), key=lambda kv: -kv[1][0]):
        print(f"      {m:22} {d:>3}/{c:<3} ({100*d//c if c else 0}%)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--corpus":
        _corpus(args[1] if len(args) > 1 else "instances")
    elif args:
        path = Path(args[0])
        rounds = int(args[1]) if len(args) > 1 else 200
        _print(path.stem, simulate(yaml.safe_load(path.read_text()), rounds))
    else:
        print(__doc__)
