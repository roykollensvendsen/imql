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

Concentration is reported at two layers. The *scoring-layer* Gini measures inequality among the active
miners the scoring rule sees — but that alone is uncorrelated with real on-chain emission Gini (validation:
r~0). The *effective* Gini layers the real dTAO emission split (18% owner / 41% validators by stake / 41%
miners by score, from chain.py's measured stake concentration) over the full registered-uid set, capturing
the validator-stake dividend layer + the inactive tail that actually drive real concentration (r~0.7).

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

# guards that catch a FABRICATED / inflated submission (Goodhart field-gaming) — verification of the work.
_GAME_GUARDS = {"deterministic_check", "code_inspection", "spot_check", "challenge_period", "honeypot",
                "commit_reveal", "liveness_check", "proof_of_work"}


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


# dTAO per-block emission split (verified: docs.learnbittensor.org/learn/emissions): each subnet's
# emission is split 18% subnet owner / 41% validators (dividends, by stake) / 41% miners (incentive, by
# score). The scoring layer the sim models is only the 41% miner share; real per-uid concentration is
# dominated by the stake-weighted dividend layer and the large registered-but-inactive tail.
#
# These are the flat protocol constants, kept on purpose. A per-subnet validator/miner split derived from
# chain (chain.py's validator_emission_frac, shrunk toward the 50/50 prior) was implemented and A/B-tested
# over 148 subnets: it left the fit unchanged (effective-Gini r 0.750 -> 0.746, median 0.945 -> 0.946).
# The split is second-order — stake concentration and the registered-uid tail dominate — and a single
# metagraph snapshot of the dividend share is mid-epoch noisy, so the constants are retained.
EMIT_OWNER, EMIT_VALIDATOR, EMIT_MINER = 0.18, 0.41, 0.41


def _stake_shares(cp: dict, n: int) -> list:
    """Reconstruct a per-uid validator stake-share vector (length n, sums to 1) from the REAL measured
    top-k stake fractions (chain.py's stake_top1/3/5) plus a geometrically-decaying tail for the
    remainder, so the dividend layer carries the actual on-chain validator concentration — not a fit."""
    t1 = cp.get("stake_top1") or 0.0
    t3 = cp.get("stake_top3") or t1
    t5 = cp.get("stake_top5") or t3
    head = [t1, (t3 - t1) / 2, (t3 - t1) / 2, (t5 - t3) / 2, (t5 - t3) / 2]
    rest = max(0.0, 1.0 - t5)
    nrest = max(1, n - len(head))
    tail = [0.5 ** (i / max(1.0, nrest / 4)) for i in range(nrest)]   # decaying remainder of the stake
    ts = sum(tail) or 1.0
    shares = (head + [rest * x / ts for x in tail])[:n]
    s = sum(shares) or 1.0
    return [x / s for x in shares]


def _effective_gini(miner_shares: list, cp: dict):
    """Concentration of REAL per-uid emission — not just the scoring layer. Layers the dTAO emission split
    over the full registered uid set: the owner takes a fixed cut (one uid), validators earn dividends by
    the real stake concentration, the mechanism's own scoring distribution spreads the miner incentive,
    and the large registered-but-inactive tail earns ~0 — which is what drives real emission Gini to ~0.98.
    Returns None when there is no on-chain data for the subnet (caller falls back to the scoring Gini)."""
    nu = cp.get("num_uids")
    if not nu or cp.get("stake_top1") is None:
        return None
    vec = [0.0] * nu
    vec[0] += EMIT_OWNER                                          # owner cut -> one uid
    for i, p in enumerate(_stake_shares(cp, nu)):                # dividends by real validator stake
        vec[i] += EMIT_VALIDATOR * p
    ms = sum(miner_shares) or 1.0                                # incentive by the mechanism's scoring shape
    for i, x in enumerate(miner_shares):
        vec[i % nu] += EMIT_MINER * x / ms
    return round(gini(vec), 3)


def simulate(ir: dict, rounds: int = 200, seed: int = 7, chain_layer: bool = True) -> dict:
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
    slot_totals = None                             # per-identity emission, in fixed slot order (the miner
                                                   # incentive distribution -> the effective-Gini layer)

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
        if slot_totals is None:                # incentives or concentration, so it is reported, not applied
            slot_totals = [0.0] * len(ids)
        for idx, ((s, _, _, _), wi) in enumerate(zip(ids, w)):
            if s in earned:
                earned[s] += wi
            all_identity_totals.append(wi)
            slot_totals[idx] += wi

    # incentive report
    rpe = {s: (earned[s] / effort[s] / rounds) for s in STRATEGIES}   # reward per unit effort, per round
    base = rpe["honest"] or 1e-9
    rel = {s: rpe[s] / base for s in STRATEGIES}                      # honest == 1.0
    honest_dominant = all(rpe["honest"] >= rpe[s] - 1e-9 for s in STRATEGIES)
    gameable = sorted(((s, rel[s]) for s in STRATEGIES if s != "honest" and rel[s] > 1.0),
                      key=lambda kv: -kv[1])
    sybil_resistant = earned["sybil"] <= earned["honest"] + 1e-9

    # effective concentration: layer the real validator-stake dividend + the registered-uid tail over the
    # scoring layer. The scoring Gini alone is uncorrelated with real emission Gini (validation: r~0);
    # the effective Gini folds in the stake layer that actually drives it (r~0.7).
    cp = {}
    if chain_layer:
        try:
            import chain
            cp = chain.cached((ir.get("subnet") or {}).get("netuid")) or {}   # cache-only: fast + silent
        except Exception:    # noqa: BLE001 — offline / no netuid -> scoring Gini only
            cp = {}
    return {
        "method": method, "composition": composition, "burn_fraction": round(burn_frac, 3),
        "guards": sorted(guard_kinds),
        "reward_model": "spec" if spec else "abstract quality (proxy)",
        "spec": spec,
        "reward_per_effort_rel": {s: round(rel[s], 2) for s in STRATEGIES},
        "honest_dominant": honest_dominant,
        "gameable_by": [(s, round(r, 2)) for s, r in gameable],
        "gini": round(gini(all_identity_totals), 3),                 # scoring layer (within active miners)
        "effective_gini": _effective_gini(slot_totals or [], cp),   # real per-uid, stake+tail layered
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
    if r.get("effective_gini") is not None:
        print(f"  concentration:    effective Gini {r['effective_gini']} (real stake+uid layer)"
              f"   |   scoring-layer Gini {r['gini']}")
    else:
        print(f"  concentration:    scoring-layer Gini {r['gini']}   (no chain data for effective Gini)")
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


# --------------------------------------------------------------------------- #
# best-response attack search + Goodhart field-gaming (no real validator needed):
# instead of testing 5 fixed strategies, SEARCH the attack space for the most profitable deviation, and
# let the attacker inflate the exact `submission.<field>` the metric rewards (gaming the proxy).
# --------------------------------------------------------------------------- #
def _rewarded_field(spec):
    import re
    if not spec:
        return None
    m = re.search(r"submission\.([A-Za-z_]\w*)", spec)
    return m.group(1) if m else None


def _reg_cost(ir, guards):
    try:
        import chain
        cp = chain.params((ir.get("subnet") or {}).get("netuid"))
        if cp.get("sybil_cost_ratio") is not None:
            return round(min(5.0, cp["sybil_cost_ratio"]), 3), "chain"
    except Exception:        # noqa: BLE001
        pass
    return (0.5 if (_COST_GUARDS & guards) else 0.0), "stylized"


def _attacker_round(method, spec, guards, field, n_id, effort, boost, rng):
    """One round: honest field + a reference honest miner + an attacker's n_id identities."""
    ids = []   # (tag, quality, field-overrides)
    field_qs = [max(0.0, rng.gauss(0.80, 0.10)) for _ in range(N_HONEST_FIELD)]
    for q in field_qs:
        ids.append(("field", q, {}))                              # honest field, effort 1.0 (the baseline)
    gaming_caught = boost > 1.0 and bool(_GAME_GUARDS & guards)    # a verification guard catches inflation
    for _ in range(n_id):
        q = max(0.0, rng.gauss(0.30 + 0.5 * effort, 0.10))         # quality rises with effort
        caught = gaming_caught and rng.random() < 0.9
        ov = ({} if caught else ({field: q * boost} if field else {}))  # Goodhart: scale the rewarded field
        ids.append(("attacker", 0.0 if caught else q, ov))         # caught inflation -> submission rejected
    peer = [q for _, q, _ in ids]
    raw = []
    for tag, q, ov in ids:
        if spec:
            ctx = {"submission": _Q(q, **ov), "groundTruth": _Q(1.0), "task": _Q(1.0), "peers": peer}
            try:
                r = max(0.0, float(metric_spec.evaluate(spec, ctx)))
            except Exception:    # noqa: BLE001
                r = q
        else:
            r = q * boost if (tag == "attacker" and q > 0) else q
        raw.append(r)
    w = _weights(raw, method)
    att = sum(wi for (t, _, _), wi in zip(ids, w) if t == "attacker")
    field_w = [wi for (t, _, _), wi in zip(ids, w) if t == "field"]
    hon = (sum(field_w) / len(field_w)) if field_w else 0.0       # per honest-field-miner (effort 1.0)
    return att, hon


def best_response(ir, rounds=50, seed=7):
    """Grid-search the attack space for the most profitable deviation vs honest."""
    agg = ir.get("aggregation") or {}
    method = agg.get("method") or "proportional"
    spec = _mech_spec(ir)
    guards = frozenset(a.get("kind") for a in (ir.get("anti_gaming") or []) if isinstance(a, dict))
    field = _rewarded_field(spec)
    reg, reg_src = _reg_cost(ir, guards)
    best = None
    for n_id in (1, 2, 5, 8):
        for effort in (0.1, 0.3, 0.6, 1.0):
            for boost in (1.0, 2.0, 4.0):
                rng = random.Random(seed)                  # same field draw for every attack -> fair
                att = hon = 0.0
                for _ in range(rounds):
                    a, h = _attacker_round(method, spec, guards, field, n_id, effort, boost, rng)
                    att += a
                    hon += h
                att_effort = n_id * (effort + reg + 0.05 * (boost - 1))
                att_rpe = (att / att_effort) if att_effort else 0.0
                margin = min(99.0, att_rpe / hon) if hon > 1e-9 else 99.0   # cap when honest fully starved
                cand = {"n_id": n_id, "effort": round(effort, 2), "field_boost": boost, "margin": round(margin, 2)}
                if best is None or cand["margin"] > best["margin"]:
                    best = cand
    best.update({"method": method, "spec": spec, "rewarded_field": field, "reg_cost": reg, "reg_src": reg_src})
    return best


def calibrate(ir, rounds=200):
    """Compare the sim's predicted concentration to the REAL on-chain emission concentration, at both
    layers: the scoring-only Gini (uncorrelated with reality, r~0) and the effective Gini that folds in
    the real validator-stake dividend layer + the registered-uid tail (the credible one, r~0.7)."""
    r = simulate(ir, rounds)
    try:
        import chain
        cp = chain.params((ir.get("subnet") or {}).get("netuid"))
    except Exception:        # noqa: BLE001
        cp = {}
    return {"predicted_gini": r["gini"], "effective_gini": r.get("effective_gini"),
            "real_emission_gini": cp.get("emission_gini"), "real_stake_gini": cp.get("stake_gini"),
            "method": r["method"]}


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--corpus":
        _corpus(args[1] if len(args) > 1 else "instances")
    elif args and "--calibrate" in args:
        path = Path(args[0])
        c = calibrate(yaml.safe_load(path.read_text()))
        print(f"# calibration vs chain: {path.stem}")
        print(f"  scoring-layer Gini ({c['method']}): {c['predicted_gini']}"
              + (f"   |   effective Gini (stake+uid layered): {c['effective_gini']}"
                 if c["effective_gini"] is not None else ""))
        if c["real_emission_gini"] is None:
            print("  no on-chain data for this netuid (warm it: chain.py --warm <netuid>)")
        else:
            print(f"  REAL on-chain emission Gini: {c['real_emission_gini']}   (stake Gini {c['real_stake_gini']})")
            eff = c["effective_gini"]
            if eff is not None:
                gap = c["real_emission_gini"] - eff
                how = "tracks" if abs(gap) <= 0.1 else ("under-predicts" if gap > 0 else "over-predicts")
                print(f"  effective vs real: {gap:+.2f}  -> the stake-layered prediction {how} reality"
                      + " (the scoring layer alone misses the validator-stake dividend that drives it).")
            gap0 = c["real_emission_gini"] - c["predicted_gini"]
            print(f"  scoring-only vs real: {gap0:+.2f}  -> scoring concentration alone is uncorrelated"
                  + " with real emission concentration (validator stake, not the metric, drives it).")
    elif args and "--attack" in args:
        path = Path(args[0])
        b = best_response(yaml.safe_load(path.read_text()))
        print(f"# best-response attack search: {path.stem}")
        print(f"  aggregation: {b['method']}   reward: {b['spec'] or 'quality proxy'}")
        print(f"  Goodhart target (rewarded field): submission.{b['rewarded_field'] or '(quality)'}")
        print(f"  sybil barrier reg_cost: {b['reg_cost']}  [{b['reg_src']}]")
        print(f"  >>> optimal attack: {b['n_id']} identities, effort {b['effort']}, field-boost x{b['field_boost']}")
        print(f"      = {b['margin']}x honest reward/effort  " + ("(GAMEABLE)" if b["margin"] > 1.0 else "(honest wins)"))
    elif args:
        path = Path(args[0])
        rounds = int(args[1]) if len(args) > 1 else 200
        _print(path.stem, simulate(yaml.safe_load(path.read_text()), rounds))
    else:
        print(__doc__)
