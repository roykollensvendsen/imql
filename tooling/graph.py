#!/usr/bin/env python3
"""IMML mechanism -> Mermaid dataflow graph (top-down: what's tested at the top, final score at the bottom).

A complement to the railroad (grammar) diagrams: this shows the *computation* — how data flows from the
miner's submission and the ground truth, through guards / metrics / aggregation / smoothing / burn, to the
weights set on chain. Each `Metric` with a `spec:` is expanded into its own little sub-graph.

Usage:
    graph.py instances/corpus/<subnet>.yaml        # print a Mermaid flowchart for one subnet
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from imml_core import _pascal
import metric_spec


def _lbl(s: str) -> str:
    return str(s).replace('"', "'").replace("\n", " ")


def mechanism_mermaid(ir: dict) -> str:
    comp = ir.get("composition") or {}
    overlays = set(comp.get("overlays") or [])
    shape = comp.get("shape") or "pipeline"
    signals = [s for s in (ir.get("scoring_signals") or []) if isinstance(s, dict)]
    gts = [g for g in (ir.get("ground_truth_sources") or []) if isinstance(g, dict)]
    agg = ir.get("aggregation") or {}
    ws = ir.get("weight_setting") or {}
    sm = ws.get("smoothing") or {}
    guards = [a for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)]
    burn = agg.get("burn_allocation") or {}

    L = ["flowchart TD"]
    E: list[tuple[str, str]] = []

    # --- inputs (top) ---
    L.append('  SUB(["submission"]):::in')
    if gts:
        L.append(f'  GT(["groundTruth: {_lbl(", ".join(_pascal(g.get("kind")) for g in gts[:3]))}"]):::in')

    # submission passes through guards first
    src = "SUB"
    if guards and "guards" in overlays:
        L.append(f'  G{{{{"@guards: {_lbl(", ".join(_pascal(a.get("kind")) for a in guards[:3]))}"}}}}:::ov')
        E.append(("SUB", "G"))
        src = "G"

    # --- metrics ---
    metric_ids = []
    for i, s in enumerate(signals):
        mid = f"M{i}"
        fam = s.get("metric_family") or s.get("metric_kind") or "other"
        spec = (s.get("extensions") or {}).get("spec")
        L.append(f'  {mid}["Metric: {_lbl(fam)}"]')
        E.append((src, mid))
        if gts:
            E.append(("GT", mid))
        if spec:                                  # expand the spec's own dataflow into a subgraph
            try:
                body, root = metric_spec.to_mermaid(spec, prefix=f"m{i}_")
                L.append(f'  subgraph sg{i} ["spec: {_lbl(spec[:48])}"]')
                L.append("  " + body.replace("\n", "\n  "))
                L.append("  end")
                E.append((root, mid))
            except Exception:                     # noqa: BLE001 — never let a bad spec break the graph
                pass
        metric_ids.append(mid)
    if not metric_ids:
        metric_ids = [src]                        # degenerate: no metric -> flow straight through

    # --- aggregate -> smooth -> burn -> publish -> out (bottom) ---
    L.append(f'  AGG["aggregate: {_lbl(_pascal(agg.get("method") or "proportional"))}"]')
    for m in metric_ids:
        E.append((m, "AGG"))
    last = "AGG"
    if sm and (sm.get("kind") or "none") != "none":
        L.append(f'  SM["smooth: {_lbl(_pascal(sm.get("kind")))}"]')
        E.append((last, "SM"))
        last = "SM"
    if "burn" in overlays and burn:
        L.append('  BURN{{"@burn: redirect a fraction"}}:::ov')
        E.append((last, "BURN"))
        last = "BURN"
    L.append(f'  PUB["publish: {_lbl(_pascal(ws.get("on_chain_call") or "set_weights"))}"]')
    E.append((last, "PUB"))
    L.append('  OUT(["weights on-chain = final score"]):::out')
    E.append(("PUB", "OUT"))
    if "state" in overlays:                       # state is a side-channel, drawn as a note
        L.append('  ST(["@state: carried across rounds"]):::note')
        E.append(("ST", "AGG"))

    L += [f"  {a} --> {b}" for a, b in E]
    L += ["  classDef in fill:#e6f0ff,stroke:#5b8;",
          "  classDef out fill:#e6ffe6,stroke:#3a3;",
          "  classDef ov fill:#fff3d6,stroke:#caa;",
          "  classDef note fill:#f3f3f3,stroke:#bbb;"]
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    ir = yaml.safe_load(Path(sys.argv[1]).read_text())
    print(mechanism_mermaid(ir))
