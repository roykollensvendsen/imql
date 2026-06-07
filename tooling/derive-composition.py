#!/usr/bin/env python3
"""Backfill the `composition` block on incentive-mechanism instances.

The composition (the IMML combinator structure) is almost entirely DERIVABLE from fields the
extraction already produced — so we compute it rather than re-extract. To keep the carefully
formatted, provenance-bearing instance files intact, this tool does NOT re-serialize the YAML:
it parses read-only to compute the values, then APPENDS a top-level `composition:` block as text
(only if the instance has none). Existing bytes are untouched; the diff is purely additive.

Derivation:
  shape:
    opaque        if aggregation.method == 'undocumented', or no aggregation AND no scoring_signals
    multiplex     if sub_competitions.structure in {multi_mechanism, per_task_type, multi_asset,
                                                     ladder, tiered, tournament}
    multiplicative if aggregation.composition == 'multiplicative'
    gated         if aggregation.composition == 'gated'
    overlay_only  if no scoring_signals and no aggregation but burn/guards/state present
    pipeline      otherwise (the dominant case)
  overlays:  burn  if mechanism_status in {partial_burn, full_burn} or burn_allocation.enabled
             guards if anti_gaming is non-empty
             state  if per_miner_state.tracked
  extern_count: provisional = count of scoring_signals with metric_kind == 'other'
                (the bespoke leaves; tooling/coverage.py recomputes the authoritative value once
                 metric_family resolution exists).

Usage:
    derive-composition.py <dir-or-file> [...]      # appends where missing
    derive-composition.py --dry-run <dir-or-file>  # report only
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed. Run: pip install -r tooling/requirements.txt")

MULTIPLEX = {"multi_mechanism", "per_task_type", "multi_asset", "ladder", "tiered", "tournament"}


def derive(d: dict) -> dict:
    agg = d.get("aggregation") or {}
    sub = d.get("sub_competitions") or {}
    signals = d.get("scoring_signals") or []
    ms = d.get("mechanism_status")
    burn = (agg.get("burn_allocation") or {}).get("enabled", False)
    anti = d.get("anti_gaming") or []
    state = (d.get("per_miner_state") or {}).get("tracked", False)

    has_agg = bool(agg)
    if agg.get("method") == "undocumented" or (not has_agg and not signals):
        shape = "opaque"
    elif sub.get("structure") in MULTIPLEX:
        shape = "multiplex"
    elif agg.get("composition") == "multiplicative":
        shape = "multiplicative"
    elif agg.get("composition") == "gated":
        shape = "gated"
    elif not signals and not has_agg and (burn or anti or state):
        shape = "overlay_only"
    else:
        shape = "pipeline"

    overlays = []
    if ms in ("partial_burn", "full_burn") or burn:
        overlays.append("burn")
    if anti:
        overlays.append("guards")
    if state:
        overlays.append("state")

    extern_count = sum(1 for s in signals if isinstance(s, dict) and s.get("metric_kind") == "other")
    return {"shape": shape, "overlays": overlays, "extern_count": extern_count}


def render(comp: dict) -> str:
    ov = "[" + ", ".join(comp["overlays"]) + "]"
    return (
        "\ncomposition:\n"
        f"  shape: {comp['shape']}\n"
        f"  overlays: {ov}\n"
        f"  extern_count: {comp['extern_count']}   # provisional; coverage.py recomputes\n"
    )


def iter_files(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            yield from sorted(f for f in p.rglob("*.yaml"))
        elif p.is_file():
            yield p


def main(argv):
    dry = "--dry-run" in argv
    targets = [a for a in argv if a != "--dry-run"]
    if not targets:
        print(__doc__)
        return 2
    n_added = n_skip = 0
    for f in iter_files(targets):
        text = f.read_text()
        d = yaml.safe_load(text)
        if not isinstance(d, dict):
            continue
        if d.get("composition") is not None:
            n_skip += 1
            continue
        comp = derive(d)
        if dry:
            print(f"{f.name}: shape={comp['shape']} overlays={comp['overlays']} extern={comp['extern_count']}")
        else:
            if not text.endswith("\n"):
                text += "\n"
            f.write_text(text + render(comp))
        n_added += 1
    verb = "would add" if dry else "added"
    print(f"\ncomposition {verb}: {n_added}   already present (skipped): {n_skip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
