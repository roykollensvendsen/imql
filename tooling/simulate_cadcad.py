#!/usr/bin/env python3
"""cadCAD incentive simulator — Monte-Carlo robustness + real chain economics.

A cadCAD model of the stylized incentive sim (`simulate.py`): each timestep is a scoring round (policy =
the strategic miners' submissions; state update = scores -> weights -> per-strategy emission). cadCAD runs
it as N independent Monte-Carlo trajectories, so a verdict comes with a *robustness* figure ("honest-
dominant in 86% of runs") instead of a single point estimate, and a parameter sweep can find the threshold
at which a mechanism flips (e.g. the registration cost that makes it sybil-resistant).

Sybil economics are grounded in real chain state where available: `tooling/chain.py` supplies the actual
registration (recycle) cost as a sybil-cost ratio, replacing the stylized constant.

Usage:
    simulate_cadcad.py <instance.yaml> [runs] [timesteps]
    simulate_cadcad.py <instance.yaml> --sweep-reg   # sweep the registration barrier, find the flip point
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import yaml
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simulate as S
import chain
from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor

_RNG = random.Random()


def _play_round(method, spec, guards, reg_cost):
    """One scoring round -> per-strategy emission increment (reuses the simulate.py primitives)."""
    ids = []
    honest_qs = [max(0.0, _RNG.gauss(0.80, 0.10)) for _ in range(S.N_HONEST_FIELD)]
    for q in honest_qs:
        ids.append(("_field", q, 1.0, None))
    for s, (k, qmean, eff, cheat) in S.STRATEGIES.items():
        for _ in range(k):
            if cheat == "plagiarism":
                q = _RNG.choice(honest_qs)
            elif cheat == "collusion":
                q = max(0.0, _RNG.gauss(qmean, 0.10)) + 0.20
            else:
                q = max(0.0, _RNG.gauss(qmean, 0.10))
            if S._caught(cheat, guards, _RNG):
                q = 0.0
            ids.append((s, q, eff, cheat))
    peer = [q for _, q, _, _ in ids]
    raw = [S._reward(spec, q, cost, cheat, peer) for _, q, cost, cheat in ids]
    w = S._weights(raw, method)
    inc = {s: 0.0 for s in S.STRATEGIES}
    for (s, _, _, _), wi in zip(ids, w):
        if s in inc:
            inc[s] += wi
    return inc


def _verdict(earned, reg_cost, timesteps):
    effort = {s: S.STRATEGIES[s][0] * (S.STRATEGIES[s][2] + reg_cost) for s in S.STRATEGIES}
    rpe = {s: earned[s] / effort[s] / timesteps for s in S.STRATEGIES}
    honest = all(rpe["honest"] >= rpe[s] - 1e-9 for s in S.STRATEGIES)
    # economic sybil-resistance: is splitting into many identities *profitable per unit effort*?
    # (the registration barrier raises sybil effort, so this is what reg_cost actually moves.)
    sybil_ok = rpe["sybil"] <= rpe["honest"] + 1e-9
    return rpe, honest, sybil_ok


def _econ(ir):
    """Resolve (method, spec, guards, reg_cost, source, chain_params) — chain-grounded where possible."""
    agg = ir.get("aggregation") or {}
    method = agg.get("method") or "proportional"
    spec = S._mech_spec(ir)
    guards = frozenset(a.get("kind") for a in (ir.get("anti_gaming") or []) if isinstance(a, dict))
    cp = chain.params((ir.get("subnet") or {}).get("netuid"))
    if cp.get("sybil_cost_ratio") is not None:
        return method, spec, guards, round(min(5.0, cp["sybil_cost_ratio"]), 3), "chain", cp
    reg = 0.5 if (S._COST_GUARDS & guards) else 0.0
    return method, spec, guards, reg, "stylized", cp


def run(ir, runs=80, timesteps=120, reg_cost=None):
    """Run the cadCAD Monte-Carlo model; return a per-run DataFrame of final `earned`."""
    method, spec, guards, reg, src, cp = _econ(ir)
    if reg_cost is not None:
        reg, src = reg_cost, "swept"
    _RNG.seed(7)

    def p_round(params, substep, history, prev):
        return {"inc": _play_round(params["method"], params["spec"], params["guards"], params["reg_cost"])}

    def s_earned(params, substep, history, prev, policy_input):
        e = dict(prev["earned"])
        for s, v in policy_input["inc"].items():
            e[s] = e.get(s, 0.0) + v
        return ("earned", e)

    exp = Experiment()
    exp.append_configs(
        initial_state={"earned": {s: 0.0 for s in S.STRATEGIES}},
        partial_state_update_blocks=[{"policies": {"r": p_round}, "variables": {"earned": s_earned}}],
        sim_configs=config_sim({"N": runs, "T": range(timesteps), "M": {
            "method": [method], "spec": [spec], "guards": [guards], "reg_cost": [reg]}}),
    )
    ctx = ExecutionContext(ExecutionMode().single_proc)
    import contextlib, io, os
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(open(os.devnull, "w")):
        records, _, _ = Executor(exec_context=ctx, configs=exp.configs).execute()   # silence cadCAD banner
    df = pd.DataFrame(records)
    finals = df[df.timestep == df.timestep.max()]
    return finals, (method, spec, guards, reg, src, cp), timesteps


def yuma_consensus(reports, stakes, kappa):
    """Bittensor Yuma consensus weight for one miner: the clipped stake-weighted median — the largest
    weight w such that the stake-weighted fraction of validators reporting >= w meets kappa
    (verified: subtensor docs/consensus.md). Validators' reports above consensus are then clipped."""
    total = sum(stakes) or 1.0
    cum = 0.0
    for w, s in sorted(zip(reports, stakes), reverse=True):
        cum += s
        if cum / total >= kappa:
            return w
    return min(reports) if reports else 0.0


def yuma_collusion(ir):
    """Can a validator bloc skew the weight consensus? Uses the REAL on-chain stake distribution + kappa.
    A bloc holding stake fraction >= kappa can push a favored miner's consensus to its own report."""
    cp = chain.params((ir.get("subnet") or {}).get("netuid"))
    kappa = cp.get("kappa")
    k = (kappa / 65535.0) if (kappa and kappa > 1) else (kappa if kappa else 0.5)
    top1, top3 = cp.get("stake_top1"), cp.get("stake_top3")
    out = {"netuid": cp.get("netuid"), "kappa": round(k, 3), "stake_top1": top1, "stake_top3": top3,
           "stake_gini": cp.get("stake_gini"), "single": None, "top3": None, "skewed_weight": None}
    if top1 is not None:
        # demo consensus: the top-1 bloc reports a favored miner 1.0, the rest report its true 0.5
        reports = [1.0, 0.5]
        stakes = [top1, 1.0 - top1]
        out["skewed_weight"] = round(yuma_consensus(reports, stakes, k), 3)
        out["single"] = top1 >= k
        out["top3"] = (top3 is not None and top3 >= k)
    return out


def temporal(ir, rounds=120, defect_at=None):
    """Does the mechanism's smoothing let a ramp-then-defect miner free-ride? (a temporal exploit)
    Model: a defector is honest until `defect_at`, then drops effort; an EMA carries its score forward,
    so under slow smoothing it keeps earning while not working. Compares it to a steady-honest miner."""
    sm = (ir.get("weight_setting") or {}).get("smoothing") or {}
    alpha = sm.get("alpha") if sm.get("kind") == "ema" and sm.get("alpha") else None
    method = (ir.get("aggregation") or {}).get("method") or "proportional"
    da = defect_at if defect_at is not None else rounds // 2
    a = alpha if alpha else 1.0   # alpha=1 -> no memory -> no temporal window
    _RNG.seed(7)

    def p_round(params, substep, history, prev):
        t = prev["timestep"]
        st = dict(prev["st"])
        d_q, d_e = (0.80, 1.0) if t < params["da"] else (0.20, 0.1)   # defector ramps then defects
        st["def_ema"] = (1 - params["a"]) * st["def_ema"] + params["a"] * d_q
        st["hon_ema"] = (1 - params["a"]) * st["hon_ema"] + params["a"] * 0.80
        j = lambda: _RNG.gauss(0, 0.03)                              # jitter so WTA ties break fairly
        scores = [0.80 + j() for _ in range(S.N_HONEST_FIELD)] + [st["def_ema"] + j(), st["hon_ema"] + j()]
        scores = [max(0.0, s) for s in scores]
        w = S._weights(scores, params["method"])
        st["def_earn"] += w[-2]; st["hon_earn"] += w[-1]
        st["def_eff"] += d_e; st["hon_eff"] += 1.0
        return {"st": st}

    def s_st(params, substep, history, prev, pi):
        return ("st", pi["st"])

    exp = Experiment()
    exp.append_configs(
        initial_state={"st": {"def_ema": 0.0, "hon_ema": 0.0, "def_earn": 0.0, "hon_earn": 0.0,
                              "def_eff": 0.0, "hon_eff": 0.0}},
        partial_state_update_blocks=[{"policies": {"r": p_round}, "variables": {"st": s_st}}],
        sim_configs=config_sim({"N": 1, "T": range(rounds), "M": {
            "method": [method], "a": [a], "da": [da]}}),
    )
    import contextlib, io, os
    ctx = ExecutionContext(ExecutionMode().single_proc)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(open(os.devnull, "w")):
        records, _, _ = Executor(exec_context=ctx, configs=exp.configs).execute()
    st = pd.DataFrame(records).iloc[-1]["st"]
    rpe_def = st["def_earn"] / st["def_eff"] if st["def_eff"] else 0.0
    rpe_hon = st["hon_earn"] / st["hon_eff"] if st["hon_eff"] else 1e-9
    return {"alpha": alpha, "method": method, "defect_at": da, "rounds": rounds,
            "margin": round(rpe_def / rpe_hon, 2) if rpe_hon else 99.0}


def _print(name, ir, runs, timesteps):
    finals, (method, spec, guards, reg, src, cp), T = run(ir, runs, timesteps)
    hd = sy = 0
    rpe_sum = {s: 0.0 for s in S.STRATEGIES}
    for _, row in finals.iterrows():
        rpe, honest, sybil_ok = _verdict(row["earned"], reg, T)
        hd += honest
        sy += sybil_ok
        for s in S.STRATEGIES:
            rpe_sum[s] += rpe[s]
    n = len(finals)
    base = rpe_sum["honest"] or 1e-9
    print(f"# cadCAD Monte-Carlo: {name}   ({n} runs x {T} rounds)")
    print(f"  aggregation: {method}   guards: {', '.join(sorted(guards)) or '(none)'}")
    print(f"  reward model: {'spec ' + spec if spec else 'abstract quality (proxy)'}")
    print(f"  sybil barrier (reg_cost): {reg}  [{src}]"
          + (f"  | chain: recycle {cp.get('recycle_tao')} TAO, sybil_cost_ratio {cp.get('sybil_cost_ratio')}, "
             f"on-chain stake_gini {cp.get('stake_gini')}" if src == "chain" else ""))
    print(f"  mean reward/effort (honest=1.00): "
          + ", ".join(f"{s} {rpe_sum[s]/base:.2f}" for s in S.STRATEGIES))
    print(f"  ROBUSTNESS — honest-dominant in {100*hd//n}% of runs;  sybil-resistant in {100*sy//n}% of runs")


def _sweep_reg(name, ir, runs=60, timesteps=80):
    print(f"# cadCAD reg-cost sweep: {name}   (the registration barrier needed for sybil-resistance)")
    flip = None
    for reg in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
        finals, *_ = run(ir, runs, timesteps, reg_cost=reg)
        sy = sum(_verdict(r["earned"], reg, timesteps)[2] for _, r in finals.iterrows())
        n = len(finals)
        frac = 100 * sy // n
        print(f"  reg_cost {reg:>4}: sybil-resistant in {frac:>3}% of runs")
        if flip is None and frac >= 50:
            flip = reg
    cp = chain.params((ir.get("subnet") or {}).get("netuid"))
    real = cp.get("sybil_cost_ratio")
    print(f"  -> flips sybil-resistant at reg_cost ~ {flip}"
          + (f";  REAL on-chain sybil_cost_ratio = {real}"
             f" ({'above' if (real and flip and real >= flip) else 'below'} the threshold)" if real is not None else ""))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    path = Path(args[0])
    ir = yaml.safe_load(path.read_text())
    if "--yuma" in args:
        y = yuma_collusion(ir)
        print(f"# Yuma validator-collusion (real chain stake): {path.stem}")
        if y["stake_top1"] is None:
            print("  no on-chain stake data for this subnet's netuid (warm it: chain.py --warm <netuid>)")
        else:
            print(f"  consensus threshold kappa: {int(y['kappa']*100)}%   on-chain stake-Gini: {y['stake_gini']}")
            print(f"  top-1 validator stake: {int(y['stake_top1']*100)}%   top-3: {int(y['stake_top3']*100)}%")
            print(f"  a favored miner's true weight 0.5 -> consensus {y['skewed_weight']} under a top-1 collusion")
            print(f"  single validator can skew consensus?  {'YES' if y['single'] else 'no'}"
                  + (f"   (top-3 bloc: {'YES' if y['top3'] else 'no'})"))
    elif "--temporal" in args:
        t = temporal(ir)
        print(f"# cadCAD temporal exploit: {path.stem}")
        print(f"  smoothing: {('EMA alpha=' + str(t['alpha'])) if t['alpha'] else 'none (no memory)'}"
              f"   aggregation: {t['method']}")
        print(f"  ramp-then-defect (honest until round {t['defect_at']}/{t['rounds']}, then free-ride)")
        print(f"  = {t['margin']}x steady-honest reward/effort  "
              + ("(TEMPORAL EXPLOIT — smoothing rewards free-riding)" if t["margin"] > 1.05 else "(no temporal exploit)"))
    elif "--sweep-reg" in args:
        _sweep_reg(path.stem, ir)
    else:
        nums = [int(a) for a in args[1:] if a.isdigit()]
        _print(path.stem, ir, nums[0] if nums else 80, nums[1] if len(nums) > 1 else 120)
