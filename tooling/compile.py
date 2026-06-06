#!/usr/bin/env python3
"""Compile IMQL text to an IR instance (YAML on stdout).

Usage: compile.py <file.imql>           # or '-' for stdin
The emitted IR carries the structural signature; run validate.py on it to confirm schema-validity.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imql_core as C  # noqa: E402
import yaml  # noqa: E402

if len(sys.argv) != 2:
    print(__doc__)
    raise SystemExit(2)
text = sys.stdin.read() if sys.argv[1] == "-" else Path(sys.argv[1]).read_text()
ir = C.compile_text(text)
ir.setdefault("schema_version", Path(__file__).resolve().parent.parent.joinpath("schema/VERSION").read_text().strip())
ir.setdefault("instance_kind", "authored")
ir.setdefault("documentation", {"status": "sparse"})
# Required-but-prose fields the structural language doesn't carry — placeholders so the IR validates.
ir.setdefault("task", {})
ir["task"].setdefault("summary", "(authored via IMQL)")
ir["task"].setdefault("submission_format", ["signals"])
ir.setdefault("scoring_signals", [])


def _satisfy_conditionals(ir):
    """Add placeholder *_other free-text where the schema requires it (enum == 'other').
    These are prose the structural language doesn't carry; placeholders keep the IR valid."""
    PH = "(unspecified in IMQL)"
    t = ir.get("task") or {}
    if "other" in (t.get("submission_format") or []):
        t.setdefault("submission_format_other", PH)
    agg = ir.get("aggregation") or {}
    if agg.get("method") == "other":
        agg.setdefault("method_other", PH)
    for g in ir.get("ground_truth_sources") or []:
        if g.get("kind") == "other":
            g.setdefault("kind_other", PH)
    for a in ir.get("anti_gaming") or []:
        if a.get("kind") == "other":
            a.setdefault("kind_other", PH)
    sc = ir.get("sub_competitions") or {}
    if sc.get("structure") == "other":
        sc.setdefault("structure_other", PH)
    ws = ir.get("weight_setting") or {}
    if ws.get("cadence") == "other":
        ws.setdefault("cadence_other", PH)
    for s in ir.get("scoring_signals") or []:
        if s.get("metric_kind") == "other":
            s.setdefault("metric_kind_other", PH)


_satisfy_conditionals(ir)
print(yaml.safe_dump(ir, sort_keys=False, width=100))
