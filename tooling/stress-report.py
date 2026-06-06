#!/usr/bin/env python3
"""Aggregate 'schema stress' signals across a set of instances into a markdown table.

Schema stress = evidence the current schema doesn't fit reality well. We mine it from
the instances themselves (no separate sidecar files needed):

  - "other" usage      : any enum field set to 'other' -> candidate new enum value.
  - unresolved fields  : provenance.unresolved[] entries -> facts that had no home / were unknowable.
  - extension usage    : any non-empty `extensions` object -> novelty the schema didn't model.
  - dead fields        : top-level optional sub-objects absent across ALL instances -> maybe unneeded.

Usage:
    stress-report.py <dir> [--out reports/schema-stress-v0.md]

The output feeds the v0 -> v1 refinement (M4). A stress signal recurring across >= 2
instances is the bar for a schema change (per CHANGELOG governance).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed. Run: pip install -r tooling/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent

OPTIONAL_TOP = [
    "ground_truth_sources", "aggregation", "weight_setting",
    "anti_gaming", "sub_competitions", "per_miner_state",
]


def load(path: Path):
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def walk(node, path=""):
    """Yield (json_pointer, key, value) for every scalar/string leaf."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}/{i}")
    else:
        yield path, node


def find_extensions(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "extensions" and isinstance(v, dict) and v:
                yield f"{path}/extensions"
            yield from find_extensions(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from find_extensions(v, f"{path}/{i}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    target = Path(argv[0])
    out = None
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])

    instances = sorted(p for p in target.rglob("*") if p.suffix in (".yaml", ".yml", ".json"))
    if not instances:
        print("No instances found.")
        return 2

    other_usage: Counter = Counter()          # which fields took 'other', by repo
    other_by_field: dict[str, list[str]] = defaultdict(list)
    unresolved: list[tuple[str, str]] = []     # (repo, note)
    ext_usage: dict[str, list[str]] = defaultdict(list)
    present_top: Counter = Counter()
    repos = []

    for path in instances:
        data = load(path)
        if not isinstance(data, dict):
            continue
        repo = (data.get("subnet") or {}).get("owner_repo") or path.stem
        repos.append(repo)

        for ptr, val in walk(data):
            if val == "other" and ptr.endswith(("kind", "method", "metric_kind", "cadence", "structure", "direction")):
                field = ptr.rsplit("/", 1)[0] or ptr
                other_by_field[field].append(repo)
                other_usage[field] += 1

        for note in (data.get("provenance") or {}).get("unresolved", []) or []:
            unresolved.append((repo, note))

        for ext_ptr in find_extensions(data):
            ext_usage[ext_ptr].append(repo)

        for key in OPTIONAL_TOP:
            if data.get(key):
                present_top[key] += 1

    n = len(repos)
    dead = [k for k in OPTIONAL_TOP if present_top[k] == 0]

    lines = []
    lines.append(f"# Schema stress report\n")
    lines.append(f"Instances analyzed: **{n}**  \nRepos: {', '.join(repos)}\n")

    lines.append("\n## Enum 'other' usage (candidate new enum values)\n")
    if other_by_field:
        lines.append("| field | count | repos |")
        lines.append("|---|---|---|")
        for field, cnt in other_usage.most_common():
            lines.append(f"| `{field}` | {cnt} | {', '.join(other_by_field[field])} |")
        lines.append("\n_Bar for a schema change: count >= 2._")
    else:
        lines.append("_None — no enum fell back to `other`._")

    lines.append("\n## Unresolved fields (missing-home / unknowable facts)\n")
    if unresolved:
        lines.append("| repo | note |")
        lines.append("|---|---|")
        for repo, note in unresolved:
            lines.append(f"| {repo} | {note} |")
    else:
        lines.append("_None reported._")

    lines.append("\n## Extension usage (novelty the schema didn't model)\n")
    if ext_usage:
        lines.append("| extension pointer | repos |")
        lines.append("|---|---|")
        for ptr, rs in sorted(ext_usage.items(), key=lambda kv: -len(kv[1])):
            lines.append(f"| `{ptr}` | {', '.join(rs)} |")
    else:
        lines.append("_None — no `extensions` object was populated._")

    lines.append("\n## Possibly dead optional sub-objects (absent across ALL instances)\n")
    if dead:
        for k in dead:
            lines.append(f"- `{k}`")
    else:
        lines.append("_None — every optional top-level sub-object was used at least once._")

    report = "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print(f"Wrote {out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
