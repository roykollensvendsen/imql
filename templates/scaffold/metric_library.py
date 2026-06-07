"""Canonical metric primitives — the generable score() implementations for IMML metric families.

Each function maps a metric FAMILY (and where useful, a SPECIFIC) to a real, parameterized
scoring implementation. Generated validator scaffolds import from here. Families with no closed-form
implementation expose a stub that raises NotImplementedError, surfacing the hand-write boundary.

These are reference implementations (the reusable "plumbing" the corpus proved recurs), not a
production validator. Numerics use only the stdlib so a scaffold runs without heavy deps.
"""
from __future__ import annotations

import math
from typing import Sequence


# --- risk_adjusted_ratio ---------------------------------------------------- #
def sharpe_ratio(returns: Sequence[float], rf: float = 0.0) -> float:
    r = [x - rf for x in returns]
    if len(r) < 2:
        return 0.0
    mu = sum(r) / len(r)
    sd = math.sqrt(sum((x - mu) ** 2 for x in r) / (len(r) - 1)) or 1e-9
    return mu / sd


def sortino_ratio(returns: Sequence[float], rf: float = 0.0) -> float:
    r = [x - rf for x in returns]
    if len(r) < 2:
        return 0.0
    mu = sum(r) / len(r)
    downside = [min(0.0, x) ** 2 for x in r]
    dd = math.sqrt(sum(downside) / len(r)) or 1e-9
    return mu / dd


def max_drawdown(equity_curve: Sequence[float]) -> float:
    peak, mdd = -math.inf, 0.0
    for v in equity_curve:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak if peak > 0 else 0.0)
    return mdd  # higher = worse; use as a penalty


# --- classification_quality ------------------------------------------------- #
def f1_score(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def fpr_complement(fp: int, tn: int) -> float:
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return 1.0 - fpr


def pass_rate(passed: int, total: int) -> float:
    return passed / total if total else 0.0


# --- probabilistic_forecast ------------------------------------------------- #
def crps_ensemble(samples: Sequence[float], observed: float) -> float:
    """Continuous Ranked Probability Score for an empirical ensemble (lower is better)."""
    n = len(samples)
    if n == 0:
        return float("inf")
    term1 = sum(abs(s - observed) for s in samples) / n
    term2 = sum(abs(a - b) for a in samples for b in samples) / (2 * n * n)
    return term1 - term2


# --- content_quality / similarity ------------------------------------------- #
def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


# --- financial_pnl ---------------------------------------------------------- #
def pnl(entry: float, exit_: float, size: float, direction: int = 1) -> float:
    return direction * (exit_ - entry) * size


# Registry: family -> (callable name, one-line contract). Used by the generator to wire score().
FAMILY_IMPL = {
    "risk_adjusted_ratio": ("sharpe_ratio", "sharpe_ratio(returns) — also sortino_ratio/max_drawdown"),
    "classification_quality": ("f1_score", "f1_score(tp, fp, fn) — also fpr_complement/pass_rate"),
    "probabilistic_forecast": ("crps_ensemble", "crps_ensemble(samples, observed) — lower is better"),
    "similarity_match": ("cosine_similarity", "cosine_similarity(a, b)"),
    "content_quality": ("cosine_similarity", "proxy via cosine_similarity / length heuristics"),
    "financial_pnl": ("pnl", "pnl(entry, exit_, size, direction)"),
}


def has_impl(family: str | None) -> bool:
    return family in FAMILY_IMPL
