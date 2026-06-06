#!/usr/bin/env python3
"""IMQL descriptive-completeness gate over the corpus.

For each instance: lift IR -> IMQL, compile IMQL -> IR', compare structural signatures.
Reports, overall and per archetype (composition.shape):
  - round-trip fidelity   : signature(ir) == signature(compile(lift(ir)))  (MUST be 100%)
  - structural-expressibility : fraction of scoring leaves that are NOT extern
  - the extern residual   : every opaque leaf listed with raw string + archetype  (= the long tail)

Gate: 100% fidelity, >=90% structural corpus-wide, >=80% within every archetype.

Usage: coverage.py <dir> [--out reports/imql-coverage.md]
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imql_core as C  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed.")

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def is_extern_leaf(s: dict) -> bool:
    # A leaf is opaque when its metric is bespoke (metric_kind 'other') and no family resolves it
    # (via the ontology), or it is explicitly flagged extern.
    if s.get("extern"):
        return True
    if s.get("metric_kind") != "other":
        return False
    fam, _ = C.resolve_metric(s)
    return not fam


def main(argv):
    target = next((a for a in argv if not a.startswith("--")), None)
    out = None
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
    if not target:
        print(__doc__)
        return 2

    files = sorted(Path(target).rglob("*.yaml"))
    n = 0
    fid_ok = 0
    broken = []           # (repo, [diffs])
    errors = []           # (repo, err)
    leaves_total = 0
    leaves_extern = 0
    extern_list = []      # (repo, shape, raw)
    by_shape = defaultdict(lambda: {"n": 0, "fid": 0, "leaves": 0, "extern": 0})

    for f in files:
        ir = yaml.safe_load(f.read_text())
        if not isinstance(ir, dict):
            continue
        repo = (ir.get("subnet") or {}).get("owner_repo") or f.stem
        shape = (ir.get("composition") or {}).get("shape") or "?"
        n += 1
        by_shape[shape]["n"] += 1
        try:
            ir2 = C.compile_text(C.lift(ir))
            diffs = C.signature_diff(ir, ir2)
        except Exception as exc:  # noqa: BLE001
            errors.append((repo, f"{type(exc).__name__}: {exc}"))
            continue
        if not diffs:
            fid_ok += 1
            by_shape[shape]["fid"] += 1
        else:
            broken.append((repo, diffs))

        for s in (ir.get("scoring_signals") or []):
            if not isinstance(s, dict):
                continue
            leaves_total += 1
            by_shape[shape]["leaves"] += 1
            if is_extern_leaf(s):
                leaves_extern += 1
                by_shape[shape]["extern"] += 1
                extern_list.append((repo, shape, s.get("metric_kind_other") or s.get("metric_kind")))

    struct_pct = 100 * (leaves_total - leaves_extern) / leaves_total if leaves_total else 100.0
    fid_pct = 100 * fid_ok / n if n else 0.0

    # ---- gate ----
    gate_fid = (fid_ok == n) and not errors
    gate_struct = struct_pct >= 90.0
    # 'opaque' is the explicit residual bucket (undocumented subnets) — excluded from the per-archetype gate.
    worst_arch = min(
        ((sh, 100 * (d["leaves"] - d["extern"]) / d["leaves"] if d["leaves"] else 100.0)
         for sh, d in by_shape.items() if sh != "opaque"),
        key=lambda x: x[1], default=("-", 100.0),
    )
    gate_arch = worst_arch[1] >= 80.0
    passed = gate_fid and gate_struct and gate_arch

    lines = ["# IMQL coverage report\n"]
    lines.append(f"Instances: **{n}**  •  round-trip fidelity: **{fid_pct:.1f}%** ({fid_ok}/{n})  "
                 f"•  structural-expressibility: **{struct_pct:.1f}%** "
                 f"({leaves_total - leaves_extern}/{leaves_total} leaves)\n")
    verdict = "PASS ✅" if passed else "FAIL ❌"
    lines.append(f"**Gate: {verdict}**  — fidelity 100% [{ 'ok' if gate_fid else 'FAIL'}], "
                 f"structural ≥90% [{'ok' if gate_struct else 'FAIL'}], "
                 f"per-archetype ≥80% [worst: {worst_arch[0]} {worst_arch[1]:.0f}% "
                 f"{'ok' if gate_arch else 'FAIL'}]\n")

    lines.append("\n## Per archetype (composition.shape)\n")
    lines.append("| shape | n | fidelity | structural-expressibility |")
    lines.append("|---|---|---|---|")
    for sh, d in sorted(by_shape.items(), key=lambda x: -x[1]["n"]):
        sp = 100 * (d["leaves"] - d["extern"]) / d["leaves"] if d["leaves"] else 100.0
        lines.append(f"| {sh} | {d['n']} | {d['fid']}/{d['n']} | {sp:.0f}% ({d['leaves']-d['extern']}/{d['leaves']}) |")

    if errors:
        lines.append("\n## Parse/round-trip ERRORS (hard fail)\n")
        for repo, e in errors:
            lines.append(f"- `{repo}`: {e}")
    if broken:
        lines.append("\n## Fidelity mismatches (signature differs after round-trip)\n")
        for repo, diffs in broken[:40]:
            lines.append(f"- `{repo}`: {'; '.join(diffs[:4])}")

    lines.append(f"\n## Long-tail residual — {leaves_extern} extern leaves\n")
    lines.append("Every opaque metric leaf (the irreducible bespoke judgment). ≥2× recurrence = ontology promotion candidate.\n")
    freq = defaultdict(int)
    for _, _, raw in extern_list:
        freq[(raw or "").lower()[:60]] += 1
    for raw, c in sorted(freq.items(), key=lambda x: -x[1])[:60]:
        lines.append(f"- {c}×  {raw}")

    report = "\n".join(lines) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print(f"Wrote {out}")

    color = GREEN if passed else RED
    print(f"{color}{verdict}{RESET}  fidelity {fid_pct:.1f}%  structural {struct_pct:.1f}%  "
          f"worst-arch {worst_arch[0]}={worst_arch[1]:.0f}%  errors={len(errors)}  mismatches={len(broken)}")
    if errors:
        for repo, e in errors[:5]:
            print(f"  {RED}ERR{RESET} {repo}: {e}")
    if broken:
        for repo, diffs in broken[:5]:
            print(f"  {YELLOW}DIFF{RESET} {repo}: {diffs[0]}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
