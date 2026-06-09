#!/usr/bin/env python3
"""Live Bittensor chain adapter — real per-subnet economic params (cached, offline-friendly).

Pulls the real registration (recycle) cost, burn, emission, neuron count, and kappa for a subnet from
finney via bittensor, and derives a dimensionless **sybil-cost ratio** = registration cost / per-neuron
emission per epoch — the real economic barrier to running many identities. Results are cached to
`vocab/chain-params.json` so the simulator and CI run offline; `--warm` pre-populates the cache.

This grounds the simulator's previously-stylized sybil economics in actual chain state (it does not need
torch or a full per-neuron metagraph download — one `get_metagraph_info` call per subnet).

Usage:
    chain.py <netuid> [--refresh]          # fetch (and cache) one subnet's params
    chain.py --warm <netuid> [<netuid>...] # pre-populate the cache for several subnets
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_CACHE = Path(__file__).resolve().parent.parent / "vocab" / "chain-params.json"
_NETWORK = "finney"


def _f(x):
    """Balance / number / None -> float (or None)."""
    if x is None:
        return None
    try:
        return float(getattr(x, "tao", x))
    except (TypeError, ValueError):
        return None


def _sum(lst):
    return sum(_f(x) or 0.0 for x in lst) if isinstance(lst, (list, tuple)) else (_f(lst) or 0.0)


def _gini(vals):
    vals = sorted(v for v in vals if v is not None and v >= 0)
    n = len(vals)
    if n == 0 or sum(vals) == 0:
        return None
    cum = sum((i + 1) * v for i, v in enumerate(vals))
    return round((2 * cum) / (n * sum(vals)) - (n + 1) / n, 3)


def _load() -> dict:
    try:
        return json.loads(_CACHE.read_text())
    except Exception:        # noqa: BLE001
        return {}


def _save(c: dict) -> None:
    _CACHE.write_text(json.dumps(c, indent=1, sort_keys=True) + "\n")


def fetch(netuid: int, network: str = _NETWORK) -> dict:
    """Query finney for one subnet's economic params (raises if the chain is unreachable)."""
    import bittensor as bt
    sub = bt.Subtensor(network=network)
    info = sub.get_metagraph_info(netuid)
    recycle = _f(sub.recycle(netuid))                  # registration cost, TAO
    price = _f(getattr(info, "moving_price", None))    # subnet token price (TAO per alpha)
    burn = _f(getattr(info, "burn", None))
    num = int(getattr(info, "num_uids", 0) or 0)
    emission_alpha = _sum(getattr(info, "emission", None))         # total alpha emitted to uids / epoch
    stakes = sorted((_f(x) for x in (getattr(info, "total_stake", []) or []) if (_f(x) or 0) > 0), reverse=True)
    stake_gini = _gini(stakes)                                     # real concentration
    tot = sum(stakes) or 1.0
    topf = lambda k: round(sum(stakes[:k]) / tot, 3) if stakes else None   # top-k stake fraction (collusion bloc)
    # real, unit-consistent sybil barrier: registration cost (converted to alpha) per neuron's emission.
    reg_alpha = (recycle / price) if (recycle and price) else None
    per_uid = (emission_alpha / num) if (emission_alpha and num) else None
    sybil_cost_ratio = round(reg_alpha / per_uid, 4) if (reg_alpha and per_uid) else None
    return {
        "netuid": netuid,
        "block": sub.get_current_block(),
        "recycle_tao": recycle,
        "moving_price": price,
        "burn": burn,
        "emission_alpha": round(emission_alpha, 4) if emission_alpha else None,
        "num_uids": num,
        "kappa": _f(getattr(info, "kappa", None)),
        "stake_gini": stake_gini,
        "stake_top1": topf(1),
        "stake_top3": topf(3),
        "stake_top5": topf(5),
        "sybil_cost_ratio": sybil_cost_ratio,
    }


def params(netuid, refresh: bool = False) -> dict:
    """Cached real params for a subnet. Returns {} if offline and not cached (caller falls back)."""
    if netuid is None:
        return {}
    cache = _load()
    key = str(netuid)
    if not refresh and key in cache:
        return cache[key]
    try:
        p = fetch(int(netuid))
    except Exception:        # noqa: BLE001 — offline / unreachable -> whatever is cached, else empty
        return cache.get(key, {})
    cache[key] = p
    _save(cache)
    return p


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--warm":
        ok = 0
        for nu in args[1:]:
            p = params(int(nu), refresh=True)
            ok += bool(p)
            print(f"  netuid {nu}: {p or 'unreachable'}")
        print(f"warmed {ok}/{len(args)-1} into {_CACHE.name}")
    elif args:
        refresh = "--refresh" in args
        nu = int(args[0])
        print(json.dumps(params(nu, refresh=refresh), indent=1))
    else:
        print(__doc__)
