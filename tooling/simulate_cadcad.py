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
    if "--sweep-reg" in args:
        _sweep_reg(path.stem, ir)
    else:
        nums = [int(a) for a in args[1:] if a.isdigit()]
        _print(path.stem, ir, nums[0] if nums else 80, nums[1] if len(nums) > 1 else 120)
