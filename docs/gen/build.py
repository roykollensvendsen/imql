"""Build-time documentation generation (run by mkdocs-gen-files).

Everything reference is generated from the canonical artifacts so the docs never drift:
  - schema/incentive-mechanism.schema.json  -> the primitives reference (+ corpus frequencies)
  - vocab/metric-ontology.yaml               -> the metric families reference
  - lang/imql.ebnf (core rules)              -> railroad diagrams
  - instances/*                              -> the 189-example gallery (via tooling/imql_core.lift)
  - tooling/*.py docstrings                  -> the CLI reference
  - reports/*.md                             -> the status pages
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
import mkdocs_gen_files

ROOT = Path(__file__).resolve().parents[2]  # incentive-schema/
sys.path.insert(0, str(ROOT / "tooling"))
import imql_core as C  # noqa: E402

SCHEMA = json.loads((ROOT / "schema" / "incentive-mechanism.schema.json").read_text())
ONTO = yaml.safe_load((ROOT / "vocab" / "metric-ontology.yaml").read_text())
VERSION = (ROOT / "schema" / "VERSION").read_text().strip()
ONTO_VERSION = ONTO.get("version", "?")

INSTANCE_PATHS = sorted((ROOT / "instances" / "sample").glob("*.yaml")) + \
                 sorted((ROOT / "instances" / "corpus").glob("*.yaml"))
IRS = []
for p in INSTANCE_PATHS:
    d = yaml.safe_load(p.read_text())
    if isinstance(d, dict):
        d["__path"] = p
        IRS.append(d)


def w(path: str, text: str):
    with mkdocs_gen_files.open(path, "w") as f:
        f.write(text)


# --------------------------------------------------------------------------- #
# enum + description access into the schema $defs / properties
# --------------------------------------------------------------------------- #
def enum_of(*keys):
    """Walk schema $defs/properties to an enum field; return (values, description)."""
    node = SCHEMA
    for k in keys:
        if "$defs" in node and k in node["$defs"]:
            node = node["$defs"][k]
        elif "properties" in node and k in node["properties"]:
            node = node["properties"][k]
        elif k in node:
            node = node[k]
        else:
            return [], ""
    return node.get("enum", []), node.get("description", "")


def field_descs(defname):
    d = SCHEMA["$defs"].get(defname, {})
    return {k: v.get("description", "") for k, v in d.get("properties", {}).items()}


# --------------------------------------------------------------------------- #
# corpus frequency of a value
# --------------------------------------------------------------------------- #
def freq_scalar(getter):
    c = Counter()
    for ir in IRS:
        v = getter(ir)
        if v is not None:
            c[v] += 1
    return c


def freq_list(getter):
    c = Counter()
    for ir in IRS:
        for v in getter(ir) or []:
            c[v] += 1
    return c


# =========================================================================== #
# 1. PRIMITIVES REFERENCE
# =========================================================================== #
def gen_primitives():
    agg = SCHEMA["$defs"]["aggregation"]["properties"]
    ws = SCHEMA["$defs"]["weightSetting"]["properties"]

    def table(values, descs, fc, total=len(IRS)):
        rows = ["| value | used by | description |", "|---|---|---|"]
        for v in values:
            n = fc.get(v, 0)
            rows.append(f"| `{v}` | {n} | {descs.get(v, '')} |")
        return "\n".join(rows)

    # per-value descriptions are not in the schema (enums are bare), so describe at field level.
    cats = []

    # aggregators
    methods = agg["method"]["enum"]
    fc = freq_scalar(lambda ir: (ir.get("aggregation") or {}).get("method"))
    cats.append(("Aggregators", "`aggregation.method` — how raw scores become weights.",
                 _vtable(methods, fc)))
    # composition
    comp = agg["composition"]["enum"]
    fc = freq_scalar(lambda ir: (ir.get("aggregation") or {}).get("composition"))
    cats.append(("Signal composition", "`aggregation.composition` — how multiple signals combine.",
                 _vtable(comp, fc)))
    # smoothers
    sk = ws["smoothing"]["properties"]["kind"]["enum"]
    fc = freq_scalar(lambda ir: ((ir.get("weight_setting") or {}).get("smoothing") or {}).get("kind"))
    cats.append(("Smoothers", "`weight_setting.smoothing.kind` — temporal smoothing of the final reward (the EMA home).",
                 _vtable(sk, fc)))
    # weight cadence
    cad = ws["cadence"]["enum"]
    fc = freq_scalar(lambda ir: (ir.get("weight_setting") or {}).get("cadence"))
    cats.append(("Weight cadence", "`weight_setting.cadence` — how often weights are committed on-chain.",
                 _vtable(cad, fc)))
    # on-chain call
    occ = ws["on_chain_call"]["enum"]
    fc = freq_scalar(lambda ir: (ir.get("weight_setting") or {}).get("on_chain_call"))
    cats.append(("On-chain call", "`weight_setting.on_chain_call`.", _vtable(occ, fc)))
    # guards
    gk = SCHEMA["$defs"]["antiGamingMechanism"]["properties"]["kind"]["enum"]
    fc = freq_list(lambda ir: [a.get("kind") for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)])
    cats.append(("Anti-gaming guards", "`anti_gaming[].kind` — controls against gaming/sybil/plagiarism.",
                 _vtable(gk, fc)))
    # enforcement
    enf = SCHEMA["$defs"]["antiGamingMechanism"]["properties"]["enforcement"]["enum"]
    fc = freq_list(lambda ir: [a.get("enforcement") for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)])
    cats.append(("Guard enforcement", "`anti_gaming[].enforcement`.", _vtable(enf, fc)))
    # ground truth
    gt = SCHEMA["$defs"]["groundTruthSource"]["properties"]["kind"]["enum"]
    fc = freq_list(lambda ir: [g.get("kind") for g in (ir.get("ground_truth_sources") or []) if isinstance(g, dict)])
    cats.append(("Ground-truth sources", "`ground_truth_sources[].kind` — where the 'correct answer' comes from.",
                 _vtable(gt, fc)))
    # trust model
    tm = SCHEMA["$defs"]["groundTruthSource"]["properties"]["trust_model"]["enum"]
    fc = freq_list(lambda ir: [g.get("trust_model") for g in (ir.get("ground_truth_sources") or []) if isinstance(g, dict)])
    cats.append(("Trust models", "`ground_truth_sources[].trust_model`.", _vtable(tm, fc)))
    # state kinds
    st = SCHEMA["$defs"]["perMinerState"]["properties"]["state_kinds"]["items"]["enum"]
    fc = freq_list(lambda ir: (ir.get("per_miner_state") or {}).get("state_kinds") or [])
    cats.append(("Per-miner state", "`per_miner_state.state_kinds` — state carried across rounds (debt ledgers, status enums).",
                 _vtable(st, fc)))
    # submission format
    sf = SCHEMA["properties"]["task"]["properties"]["submission_format"]["items"]["enum"]
    fc = freq_list(lambda ir: (ir.get("task") or {}).get("submission_format") or [])
    cats.append(("Submission formats", "`task.submission_format` — what miners deliver.", _vtable(sf, fc)))
    # combinator shapes
    sh = SCHEMA["$defs"]["composition"]["properties"]["shape"]["enum"]
    fc = freq_scalar(lambda ir: (ir.get("composition") or {}).get("shape"))
    cats.append(("Combinator shapes", "`composition.shape` — the top-level combinator archetype.",
                 _vtable(sh, fc)))

    body = [f"# Primitives reference\n",
            f"The closed vocabulary of IMQL — every primitive is an enum value in the IR schema "
            f"(`v{VERSION}`), governed by the same ≥2× evidence bar. The **used by** column is the "
            f"number of the {len(IRS)} corpus subnets that use each value.\n"]
    for title, blurb, tbl in cats:
        body.append(f"\n## {title}\n\n{blurb}\n\n{tbl}\n")
    w("reference/index.md", "\n".join(body))


def _vtable(values, fc):
    rows = ["| value | used by |", "|---|---|"]
    for v in sorted(values, key=lambda x: (-fc.get(x, 0), x)):
        rows.append(f"| `{v}` | {fc.get(v, 0)} |")
    return "\n".join(rows)


# =========================================================================== #
# 2. METRIC FAMILIES
# =========================================================================== #
def gen_metric_families():
    families = ONTO.get("families", {})
    aliases = ONTO.get("aliases", {})
    # count subnets per family (resolve each signal)
    fam_count = Counter()
    for ir in IRS:
        fams = set()
        for s in (ir.get("scoring_signals") or []):
            if isinstance(s, dict):
                f, _ = C.resolve_metric(s)
                if f:
                    fams.add(f)
        for f in fams:
            fam_count[f] += 1

    body = [f"# Metric families\n",
            f"The metric **type system** — the 3-level vocabulary (raw → specific → family) from "
            f"`vocab/metric-ontology.yaml` (`v{ONTO_VERSION}`). The bespoke per-subnet metric is the one "
            f"part IMQL cannot make fully structural; families are how it is typed where possible. "
            f"Unresolvable metrics stay `extern` (see the [coverage report](../status/index.md)).\n",
            "\n| family | used by | specifics | description |",
            "|---|---|---|---|"]
    for fam in sorted(families):
        d = families[fam]
        specs = ", ".join(f"`{s}`" for s in (d.get("specifics") or [])) or "—"
        body.append(f"| `{fam}` | {fam_count.get(fam, 0)} | {specs} | {d.get('description', '')} |")

    body.append(f"\n## Aliases\n\nThe canonicalizer maps {len(aliases)} raw metric strings to a "
                "`(family, specific)` pair while keeping the raw string immutable.\n")
    body.append("\n| raw metric | family | specific |\n|---|---|---|")
    for raw in sorted(aliases):
        m = aliases[raw]
        body.append(f"| {raw[:70]} | `{m.get('family')}` | `{m.get('specific')}` |")
    w("reference/metric-families.md", "\n".join(body))


# =========================================================================== #
# 3. GRAMMAR (railroad)
# =========================================================================== #
def gen_grammar():
    try:
        from railroad import Diagram, Choice, Sequence, Terminal, NonTerminal, Optional, OneOrMore
    except Exception:
        w("language/grammar.md", "# Grammar\n\nrailroad-diagrams not installed.\n")
        return

    def svg(d):
        buf = io.StringIO()
        d.writeSvg(buf.write)
        return buf.getvalue()

    diagrams = {
        "mechanism": Diagram(Sequence(
            Terminal("mechanism"), NonTerminal("ident"), Terminal("{"),
            OneOrMore(NonTerminal("header"), Terminal("")), OneOrMore(NonTerminal("overlay"), Terminal("")),
            NonTerminal("combinator"), Terminal("}"))),
        "combinator": Diagram(Choice(0,
            NonTerminal("pipeline"), NonTerminal("multiplex"), NonTerminal("gate"),
            NonTerminal("product"), NonTerminal("metric leaf"))),
        "pipeline": Diagram(Sequence(
            Terminal("pipeline"), Terminal("{"),
            Terminal("score:"), NonTerminal("scorer"),
            Terminal("aggregate:"), NonTerminal("aggregator"),
            Optional(Sequence(Terminal("smooth:"), NonTerminal("smoother"))),
            Terminal("emit:"), NonTerminal("weight_setter"), Terminal("}"))),
        "overlay": Diagram(Choice(0,
            Sequence(Terminal("@burn"), Terminal("{ … }")),
            Sequence(Terminal("@guards"), Terminal("{ … }")),
            Sequence(Terminal("@state"), Terminal("{ … }")))),
        "metric leaf": Diagram(Choice(0,
            Sequence(Terminal("metric"), NonTerminal("family"), Terminal("("), NonTerminal("specific"), Terminal(")")),
            Sequence(Terminal("metric"), NonTerminal("family"), Terminal("("), Terminal("extern"), NonTerminal("\"raw\""), Terminal(")")),
            Sequence(Terminal("extern"), NonTerminal("\"raw\"")))),
    }
    body = [f"# Grammar\n",
            f"IMQL has no control flow — the four combinators are the only composition operators. The "
            f"core productions are below; the full grammar is in "
            f"[`lang/imql.ebnf`](https://github.com/fx-integral/academia). Targets IR `v{VERSION}`.\n"]
    for name, d in diagrams.items():
        body.append(f"\n## `{name}`\n\n<div class=\"railroad\" markdown>\n{svg(d)}\n</div>\n")
    w("language/grammar.md", "\n".join(body))


# =========================================================================== #
# 4. EXAMPLES GALLERY (189, via lift)
# =========================================================================== #
def gen_examples():
    by_shape = defaultdict(list)
    rows = []
    for ir in IRS:
        sub = ir.get("subnet") or {}
        repo = sub.get("owner_repo") or ir["__path"].stem
        stem = ir["__path"].stem
        shape = (ir.get("composition") or {}).get("shape") or "?"
        lang = sub.get("implementation_lang") or "?"
        status = ir.get("mechanism_status") or "unknown"
        name = sub.get("name") or repo
        netuid = sub.get("netuid")
        try:
            imql = C.lift(ir)
        except Exception as exc:  # noqa: BLE001
            imql = f"# lift failed: {exc}"
        ir_yaml = yaml.safe_dump({k: v for k, v in ir.items() if k != "__path"}, sort_keys=False, width=100, allow_unicode=True)

        page = [f"# {name}\n",
                f"| | |\n|---|---|",
                f"| Subnet | `{repo}` |",
                f"| netuid | {netuid} |",
                f"| Archetype | `{shape}` |",
                f"| Language | `{lang}` |",
                f"| Mechanism status | `{status}` |",
                f"| Task | {(ir.get('task') or {}).get('summary', '')[:300]} |\n",
                '=== "IMQL"\n',
                "    ```text",
                *(f"    {ln}" for ln in imql.splitlines()),
                "    ```\n",
                '=== "IR (YAML)"\n',
                "    ```yaml",
                *(f"    {ln}" for ln in ir_yaml.splitlines()),
                "    ```\n"]
        w(f"examples/{stem}.md", "\n".join(page))
        by_shape[shape].append((name, stem))
        rows.append((name, netuid, shape, lang, status, stem))

    # index with a sortable-ish table
    idx = [f"# Examples\n",
           f"All **{len(IRS)}** corpus subnets, each reverse-engineered into the IR and lifted to IMQL. "
           f"Grouped in the nav by archetype. Use search to filter by name, primitive, or metric.\n",
           "\n| subnet | netuid | archetype | lang | status |",
           "|---|---|---|---|---|"]
    for name, netuid, shape, lang, status, stem in sorted(rows, key=lambda r: r[0].lower()):
        idx.append(f"| [{name}]({stem}.md) | {netuid if netuid is not None else ''} | "
                   f"`{shape}` | {lang} | {status} |")
    w("examples/index.md", "\n".join(idx))

    # nav (grouped by archetype) via a literate-nav SUMMARY for the examples dir
    nav = ["- [Gallery](index.md)"]
    for shape in sorted(by_shape):
        nav.append(f"- {shape}")
        for name, stem in sorted(by_shape[shape], key=lambda x: x[0].lower()):
            nav.append(f"    - [{name}]({stem}.md)")
    w("examples/SUMMARY.md", "\n".join(nav) + "\n")


# =========================================================================== #
# 5. TOOLCHAIN + STATUS
# =========================================================================== #
def gen_toolchain():
    import ast
    body = ["# CLI reference\n",
            "The IMQL toolchain. All scripts run under the project venv "
            "(`./.venv/bin/python tooling/<script>.py`).\n"]
    order = ["validate.py", "lift.py", "compile.py", "fmt.py", "coverage.py", "canonicalize.py",
             "generate.py", "derive-composition.py", "stress-report.py", "imql_core.py"]
    for fn in order:
        p = ROOT / "tooling" / fn
        if not p.exists():
            continue
        doc = ast.get_docstring(ast.parse(p.read_text())) or "(no module docstring)"
        body.append(f"\n## `{fn}`\n\n```\n{doc.strip()}\n```\n")
    w("toolchain/cli.md", "\n".join(body))


def gen_status():
    body = [f"# Status & reports\n",
            f"Live, auto-generated reports over the {len(IRS)}-subnet corpus.\n",
            "\n## IMQL coverage\n",
            '--8<-- "reports/imql-coverage.md"\n',
            "\n## Metric vocabulary candidates\n",
            '--8<-- "reports/vocab-candidates.md"\n',
            "\n## Corpus extraction summary\n",
            '--8<-- "reports/corpus-extraction-summary.md"\n']
    w("status/index.md", "\n".join(body))


gen_primitives()
gen_metric_families()
gen_grammar()
gen_examples()
gen_toolchain()
gen_status()

# patch the top-level nav: replace the Examples line with the grouped dir, add nothing else.
