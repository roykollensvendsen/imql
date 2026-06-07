#!/usr/bin/env python3
"""IMML metric spec-language (Layer 2) — parser + sort type-checker.

A scoring metric is modelled as a typed term over (submission, groundTruth, task, peers):
a composition of a small closed set of generators. This module PARSES such a `spec:` expression
and TYPE-CHECKS it against the generator signatures, returning the result sort. It is a standalone
analysis tool (it does NOT touch the IR/schema or round-trip) used to measure, empirically, how much
of the bespoke metric tail is expressible in the algebra — the MDL question made concrete.

Usage:
    metric_spec.py "rate(submission.spot_checks)"          # parse+check one expression
    metric_spec.py --report vocab/metric-tail-specs.yaml   # coverage report over the corpus tail
"""
from __future__ import annotations

import sys
from pathlib import Path

from lark import Lark, Transformer, v_args
from lark.exceptions import VisitError

# --------------------------------------------------------------------------- #
# sorts
# --------------------------------------------------------------------------- #
# Field is a polymorphic projection (submission.x) — we cannot know its concrete sort without a
# submission schema, so it unifies with any scalar-ish sort a generator expects.
SCALARISH = {"Num", "Bool", "Dist", "Vec", "Item", "GT", "Task", "Items", "Field"}


def _ok(expected: str, got: str) -> bool:
    """Is `got` acceptable where `expected` is wanted? Field is the wildcard; Bool coerces to Num."""
    if expected == "any" or got == "Field" or expected == "Field":
        return True
    if expected == "Num" and got == "Bool":
        return True
    return expected == got


# --------------------------------------------------------------------------- #
# generator signatures: name -> (arg_sorts, result_sort).  "*" = variadic (>=1 of last sort).
# arg sort "G" marks a named convex-generator literal (brier/log/spherical/crps/energy).
# --------------------------------------------------------------------------- #
GENERATORS = {
    # comparators
    "error":      (["any", "any"], "Num"),
    "score_rule": (["G", "any", "any"], "Num"),
    "similarity": (["any", "any"], "Num"),
    "member":     (["any", "any"], "Bool"),
    # gates / thresholds
    "gate":       (["Bool"], "Num"),
    "threshold":  (["Num", "Num"], "Bool"),
    # reductions
    "mean":       (["any"], "Num"),
    "sum":        (["any"], "Num"),
    "max":        (["any"], "Num"),
    "min":        (["any"], "Num"),
    "count":      (["any"], "Num"),
    "rate":       (["any"], "Num"),
    "share":      (["Num", "Items"], "Num"),
    # relational / peer
    "winrate":    (["Items"], "Vec"),
    "rank":       (["Items"], "Vec"),
    "softmax":    (["Vec"], "Vec"),
    "zscore":     (["Vec"], "Vec"),
    "peer_score": (["G", "any", "any"], "Num"),   # peer prediction / surrogate scoring rule
    # transforms
    "clip":       (["Num", "Num", "Num"], "Num"),
    "affine":     (["Num", "Num", "Num"], "Num"),
    "penalty":    (["Num"], "Num"),
    "neg":        (["Num"], "Num"),
    "sign":       (["Num"], "Num"),
    "normalize":  (["Num"], "Num"),
    # the genuine opaque residual
    "extern":     (["any"], "Num"),
}

CONVEX_GENERATORS = {"brier", "log", "spherical", "crps", "energy"}
SOURCES = {"submission": "Item", "groundTruth": "GT", "task": "Task", "peers": "Items"}

GRAMMAR = r"""
start: expr
expr: term (BINOP term)*
term: call | source | literal | "(" expr ")"
call: NAME "(" [arg ("," arg)*] ")"
arg: NAME ":" literal   -> named
   | expr               -> positional
source: SRC ("." NAME)*
literal: SIGNED_NUMBER  -> num
       | ESCAPED_STRING -> str
       | NAME           -> ident
SRC: "submission" | "groundTruth" | "task" | "peers"
BINOP: "+" | "-" | "*" | "/"
NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.SIGNED_NUMBER
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

_parser = Lark(GRAMMAR, parser="earley", maybe_placeholders=False)


class SpecError(Exception):
    pass


# a metric ultimately yields a per-miner Num/Bool, or a Vec (the per-population score vector,
# for relational metrics like winrate/rank before reduction), or a projected Field.
VALID_TOP = {"Num", "Bool", "Vec", "Field"}


@v_args(inline=True)
class _Check(Transformer):
    """Returns the result sort of each node (a sort string, or ('ident', name) for a bare symbol);
    raises SpecError on an unknown/ill-typed term."""
    def num(self, _):
        return "Num"
    def str(self, _):
        return "Field"
    def ident(self, n):
        return ("ident", str(n))   # bare identifier: a convex-generator name (brier) or a symbol
    def named(self, _name, _lit):
        return "any"               # named params (e.g. τ: 0.5) don't constrain the result
    def positional(self, sort):
        return sort
    def source(self, *parts):
        base = SOURCES.get(str(parts[0]), "Field")
        return "Field" if len(parts) > 1 else base   # a `.field` projection -> polymorphic Field
    def term(self, x):
        return x                   # pass through (sort or ('ident', name))
    def expr(self, *parts):
        return "Num" if len(parts) > 1 else parts[0]   # term BINOP term ... -> Num
    def call(self, name, *args):
        g = str(name)
        if g not in GENERATORS:
            raise SpecError(f"unknown generator '{g}'")
        sig, result = GENERATORS[g]
        args = [a for a in args if a is not None]
        if len(args) != len(sig):
            raise SpecError(f"{g}: expected {len(sig)} args, got {len(args)}")
        for i, want in enumerate(sig):
            got = args[i]
            if want == "G":
                if not (isinstance(got, tuple) and got[1] in CONVEX_GENERATORS):
                    raise SpecError(f"{g}: arg {i} must be a convex generator {sorted(CONVEX_GENERATORS)}")
                continue
            got_sort = "Field" if isinstance(got, tuple) else got   # a bare symbol -> Field
            if not _ok(want, got_sort):
                raise SpecError(f"{g}: arg {i} expected {want}, got {got_sort}")
        return result
    def start(self, sort):
        return sort


def check(spec: str) -> str:
    """Parse + type-check a spec expression; return its result sort, or raise SpecError."""
    try:
        tree = _parser.parse(spec)
    except Exception as e:  # noqa: BLE001 — lark raises many parse error types
        raise SpecError(f"parse error: {e}") from e
    try:
        sort = _Check().transform(tree)
    except VisitError as e:
        if isinstance(e.orig_exc, SpecError):
            raise e.orig_exc from None
        raise
    s = "Field" if isinstance(sort, tuple) else sort
    if s not in VALID_TOP:
        raise SpecError(f"metric must reduce to Num/Bool/Vec, got {s}")
    return s


def generators_used(spec: str) -> list[str]:
    """The generator names invoked in a spec (for usage frequency)."""
    import re
    return re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", spec)


def _report(path: str) -> int:
    import yaml
    rows = yaml.safe_load(Path(path).read_text()) or []
    total = len(rows)
    expressible = extern = bad = 0
    gen_freq: dict[str, int] = {}
    lengths = []
    for r in rows:
        if r.get("extern"):
            extern += 1
            continue
        spec = r.get("spec")
        try:
            check(spec)
            expressible += 1
            gens = generators_used(spec)
            lengths.append(len(gens))
            for g in gens:
                gen_freq[g] = gen_freq.get(g, 0) + 1
        except SpecError as e:
            bad += 1
            print(f"  ✗ {r.get('raw','?')[:50]!r}: {e}", file=sys.stderr)
    avg = sum(lengths) / len(lengths) if lengths else 0
    print(f"metric tail: {total} distinct")
    print(f"  expressible in the algebra: {expressible} ({100*expressible//total}%)")
    print(f"  genuine extern residual:    {extern} ({100*extern//total}%)")
    if bad:
        print(f"  FAILED to type-check:       {bad}  <-- fix spec or generator table")
    print(f"  mean generators / term:     {avg:.1f}   (the MDL upper bound)")
    print("  generator usage:", dict(sorted(gen_freq.items(), key=lambda kv: -kv[1])))
    return 1 if bad else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--report":
        sys.exit(_report(args[1]))
    elif args:
        try:
            print(check(args[0]))
        except SpecError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(__doc__)
