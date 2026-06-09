#!/usr/bin/env python3
"""IMML mechanism simulator (MVP) — measure incentive-compatibility.

Instantiates a mechanism's STRUCTURE (its anti-gaming guards, aggregation method/composition, and burn)
and runs a population of strategic miners against it for N rounds, then reports whether honest effort is
the rational strategy or whether someone can game it.

This is a STYLIZED model, not a faithful per-subnet replay: we do not have each subnet's submission schema,
so a miner's output is abstracted to a (quality, effort, cheat-type) profile. What is faithful is the
mechanism's *shape* — which cheats its guards catch, how scores become weights, and how burn redirects
emission — so the directional findings (is winner-take-all sybil-prone? do the guards stop plagiarism?
does burn change concentration?) reflect the real design choices.

When a subnet's metric is expressible in the spec algebra — either authored (`extensions.spec`) or looked
up from vocab/metric-tail-specs.yaml — the per-miner raw score is computed by actually evaluating that
spec (tooling/metric_spec.evaluate), so the metric's own structure (gate / penalty / share / score_rule)
shapes the reward, not just an abstract quality. Relational reductions (winrate/rank) and any spec that
fails to evaluate fall back to the quality proxy. The report says which reward model was used.

Usage:
    simulate.py instances/corpus/<subnet>.yaml [rounds]
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import yaml

import metric_spec

# metrics written out in the spec algebra: the 75 one-off `other` raws + the 20 named-kind families
_ROOT = Path(__file__).resolve().parent.parent


def _load(name, key):
    try:
        return {r[key]: r["spec"] for r in (yaml.safe_load((_ROOT / "vocab" / name).read_text()) or [])
                if isinstance(r, dict) and r.get("spec")}
    except Exception:    # noqa: BLE001
        return {}


_TAIL = _load("metric-tail-specs.yaml", "raw")
_KIND = _load("metric-kind-specs.yaml", "kind")

# population-vector reductions that collapse per-miner -> skip (the FOCAL forms beats/rank_of/zscore_of
# are per-miner and evaluate fine, so they are deliberately NOT here).
_RELATIONAL = {"winrate", "rank", "zscore", "softmax"}

# guards that make a sybil identity COSTLY (a registration barrier) rather than catchable — modelled as a
# per-identity cost, not a rejection: many identities are valid, just expensive to run at scale.
_COST_GUARDS = {"proof_of_work", "collateral", "hardware_validation", "stake_weighting", "registration_cost"}


class _Q(dict):
    """A submission/task/groundTruth view: any unknown field falls back to a default value."""
    def __init__(self, default, **known):
        super().__init__(**known)
        self._d = default
    def __missing__(self, _k):
        return self._d


def _signal_spec(sig: dict) -> str | None:
    return ((sig.get("extensions") or {}).get("spec")
            or _TAIL.get(sig.get("metric_kind_other"))
            or _KIND.get(sig.get("metric_kind")))


def _mech_spec(ir: dict) -> str | None:
    for s in (ir.get("scoring_signals") or []):
        if isinstance(s, dict) and _signal_spec(s):
            return _signal_spec(s)
    return None


def _reward(spec, q, cost, cheat, peer_qs):
    """Per-miner raw score from the actual metric spec; falls back to the abstract quality when the spec
    is absent, relational (focal-miner not modelled), or fails to evaluate."""
    if not spec or (set(metric_spec.generators_used(spec)) & _RELATIONAL):
        return q
    ctx = {
        "submission": _Q(q, valid=(cheat is None or cheat == "collusion"), cost=cost, api_cost=cost, stake=q),
        "groundTruth": _Q(1.0),
        "task": _Q(1.0),
        "peers": list(peer_qs),
    }
    try:
        v = float(metric_spec.evaluate(spec, ctx))
        return max(0.0, v) if v == v else q   # clamp >=0 for weighting; NaN -> fallback
    except Exception:        # noqa: BLE001 — any eval gap -> fall back, never crash a sim
        return q

# guard kind -> the cheat it neutralises (best-effort mapping over the corpus's anti_gaming vocabulary)
CATCHES = {
    "plagiarism": {"plagiarism_detection", "deduplication", "content_hash", "code_inspection", "honeypot"},
    "low_effort": {"liveness_check", "spot_check", "challenge_period", "deterministic_check", "commit_reveal"},
    "collusion":  {"deduplication", "peer_review", "honeypot"},
    # 'sybil' is intentionally absent — a registration barrier makes sybils COSTLY, not invalid (see _COST_GUARDS)
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
    spec = _mech_spec(ir)                          # the subnet's actual metric, if expressible

    # a registration barrier adds a per-identity cost -> multi-identity strategies (sybil/colluder) pay
    # it K times, so running many identities is expensive exactly when the mechanism makes it so.
    reg_cost = 0.5 if (_COST_GUARDS & guard_kinds) else 0.0
    earned = {s: 0.0 for s in STRATEGIES}          # total emission per strategy
    effort = {s: STRATEGIES[s][0] * (STRATEGIES[s][2] + reg_cost) for s in STRATEGIES}
    all_identity_totals = []

    for _ in range(rounds):
        ids = []   # (strategy, quality, cost, cheat)
        # background honest field
        honest_qs = [max(0.0, rng.gauss(0.80, 0.10)) for _ in range(N_HONEST_FIELD)]
        for q in honest_qs:
            ids.append(("_field", q, 1.0, None))
        # the strategic test miners
        for s, (k, qmean, eff, cheat) in STRATEGIES.items():
            for _ in range(k):
                if cheat == "plagiarism":
                    q = rng.choice(honest_qs)                       # copy a real honest output
                elif cheat == "collusion":
                    q = max(0.0, rng.gauss(qmean, 0.10)) + 0.20      # mutual boost
                else:
                    q = max(0.0, rng.gauss(qmean, 0.10))
                if _caught(cheat, guard_kinds, rng):
                    q = 0.0
                ids.append((s, q, eff, cheat))

        peer_qs = [q for _, q, _, _ in ids]
        raw = [_reward(spec, q, cost, cheat, peer_qs) for _, q, cost, cheat in ids]
        w = _weights(raw, method)   # burn scales every miner equally -> it doesn't change relative
        for (s, _, _, _), wi in zip(ids, w):   # incentives or concentration, so it is reported, not applied
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
        "reward_model": "spec" if spec else "abstract quality (proxy)",
        "spec": spec,
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
    print(f"  reward model: {r['reward_model']}" + (f"  ->  {r['spec']}" if r.get('spec') else ""))
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
    spec_used = 0
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
        spec_used += bool(r["spec"])
        for s, _ in r["gameable_by"]:
            exploiter[s] += 1
        m = by_method[r["method"]]
        m[0] += 1
        m[1] += r["honest_dominant"]
    print(f"# corpus incentive sweep — {n} mechanisms, {rounds} rounds each (STYLIZED model)")
    print(f"  reward model:      real spec for {spec_used}/{n}, abstract-quality proxy for the rest")
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
