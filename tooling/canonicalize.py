#!/usr/bin/env python3
"""Canonicalize bespoke metric strings into the 3-level ontology (raw -> specific -> family).

The ontology (vocab/metric-ontology.yaml) is the canonicalization layer: instances keep the raw
metric string immutable, and consumers (coverage.py, lift.py) resolve metric_family at read time.
This tool reports resolution coverage and surfaces unmatched raw strings as promotion candidates.

  canonicalize.py --report [--out reports/vocab-candidates.md]
        Resolution coverage over the corpus; unmatched 'other' metrics -> promotion candidates.

  canonicalize.py --apply <dir>
        OPTIONAL: materialize metric_family/metric_specific into the instances (reserializes YAML;
        use only if you want the families inline). Default workflow leaves instances byte-pure and
        resolves from the ontology. Reversible with --revert.

  canonicalize.py --revert <dir>
        Strip any materialized metric_family/metric_specific (back to raw-only).

Idempotent. Never modifies metric_kind / metric_kind_other (the raw level).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imql_core as C  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed.")

ROOT = Path(__file__).resolve().parent.parent
INSTANCES = [ROOT / "instances" / "sample", ROOT / "instances" / "corpus"]


def _iter_signals():
    for d in INSTANCES:
        for f in sorted(d.glob("*.yaml")):
            ir = yaml.safe_load(f.read_text())
            if not isinstance(ir, dict):
                continue
            repo = (ir.get("subnet") or {}).get("owner_repo") or f.stem
            for s in (ir.get("scoring_signals") or []):
                if isinstance(s, dict):
                    yield repo, f, ir, s


def report(out: Path | None):
    onto = C.load_ontology()
    n_other = resolved = 0
    unmatched = Counter()
    fam_hits = Counter()
    for repo, _f, _ir, s in _iter_signals():
        if s.get("metric_kind") != "other":
            continue
        n_other += 1
        fam, spec = C.resolve_metric(s)
        if fam:
            resolved += 1
            fam_hits[fam] += 1
        else:
            unmatched[(s.get("metric_kind_other") or "").strip()] += 1

    pct = 100 * resolved / n_other if n_other else 0.0
    lines = [f"# Vocabulary candidates (ontology v{onto.get('version')})\n",
             f"Bespoke `other` metric leaves: **{n_other}**  •  resolved to a family: "
             f"**{resolved}** ({pct:.0f}%)  •  unmatched: **{len(unmatched)}**\n",
             "\n## Resolved by family\n", "| family | count |", "|---|---|"]
    for fam, c in fam_hits.most_common():
        lines.append(f"| {fam} | {c} |")
    lines.append("\n## Unmatched — promotion candidates (the irreducible tail)\n")
    lines.append("Each is a bespoke per-subnet metric with no family. A raw string recurring ≥2× across "
                 "subnets is a promotion candidate (governed: CHANGELOG + VERSION bump + re-run).\n")
    lines.append("| count | raw metric |")
    lines.append("|---|---|")
    for raw, c in unmatched.most_common():
        lines.append(f"| {c} | {raw[:100]} |")
    text = "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        print(f"Wrote {out}")
    print(f"resolved {resolved}/{n_other} ({pct:.0f}%) bespoke metrics; {len(unmatched)} unmatched")
    return 0


def apply(target: str, revert: bool):
    onto = C.load_ontology()
    aliases = onto.get("aliases") or {}
    changed = 0
    for f in sorted(Path(target).rglob("*.yaml")):
        ir = yaml.safe_load(f.read_text())
        if not isinstance(ir, dict):
            continue
        dirty = False
        for s in (ir.get("scoring_signals") or []):
            if not isinstance(s, dict):
                continue
            if revert:
                if s.pop("metric_family", None) is not None or s.pop("metric_specific", None) is not None:
                    dirty = True
            elif s.get("metric_kind") == "other" and not s.get("metric_family"):
                hit = aliases.get((s.get("metric_kind_other") or "").strip().lower())
                if hit:
                    s["metric_family"] = hit["family"]
                    s["metric_specific"] = hit.get("specific")
                    dirty = True
        if dirty:
            f.write_text(yaml.safe_dump(ir, sort_keys=False, width=100, allow_unicode=True))
            changed += 1
    print(f"{'reverted' if revert else 'applied to'} {changed} files")
    return 0


def main(argv):
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
    if "--report" in argv:
        return report(out)
    if "--apply" in argv:
        return apply(argv[argv.index("--apply") + 1], revert=False)
    if "--revert" in argv:
        return apply(argv[argv.index("--revert") + 1], revert=True)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
