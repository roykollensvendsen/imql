#!/usr/bin/env python3
"""IMML core: the structural signature, IR->IMML (lift), and IMML->IR (compile).

The round-trip success criterion is over the mechanism's STRUCTURAL SIGNATURE — the design:
enums, numeric params, typed primitive nodes, the metric leaves, and the composition tree.
It deliberately EXCLUDES prose and provenance (task.summary, *.notes, provenance.*, exact
free-text), which are extraction bookkeeping, not part of a design language. "100% fidelity"
means: signature(ir) == signature(compile(lift(ir))) for every corpus instance.

lift(ir)        -> IMML text capturing the full signature
compile(text)   -> a MINIMAL IR dict populated with only the structural fields
signature(ir)   -> the normalized projection used for comparison (works on full or minimal IR)
"""
from __future__ import annotations

import re
from pathlib import Path

from lark import Lark, Transformer, v_args

# --------------------------------------------------------------------------- #
# Metric ontology resolution (the canonicalization layer).
# The ontology is the canonical layer; instances keep the raw metric string
# immutable. Consumers resolve metric_family/metric_specific at read time, so
# canonicalization is non-destructive and reversible (edit the ontology, not the
# instances). An instance's own metric_family (if ever materialized) wins.
# --------------------------------------------------------------------------- #

_ONTOLOGY = None


def load_ontology() -> dict:
    global _ONTOLOGY
    if _ONTOLOGY is None:
        import yaml
        p = Path(__file__).resolve().parent.parent / "vocab" / "metric-ontology.yaml"
        _ONTOLOGY = yaml.safe_load(p.read_text()) if p.exists() else {"aliases": {}, "families": {}}
    return _ONTOLOGY


def resolve_metric(signal: dict) -> tuple:
    """Return (family, specific) for a scoring signal, resolving from the ontology when the
    instance doesn't carry them. Known metric_kind enums map to themselves at the family level
    is NOT assumed — only metric_kind == 'other' leaves are resolved via raw-string aliases."""
    fam, spec = signal.get("metric_family"), signal.get("metric_specific")
    if fam:
        return fam, spec
    if signal.get("metric_kind") == "other":
        raw = (signal.get("metric_kind_other") or "").strip().lower()
        hit = (load_ontology().get("aliases") or {}).get(raw)
        if hit:
            return hit.get("family"), hit.get("specific")
    return fam, spec

# --------------------------------------------------------------------------- #
# Structural signature
# --------------------------------------------------------------------------- #

def _num(x):
    return None if x is None else (round(float(x), 9) if isinstance(x, (int, float)) else x)


def signature(ir: dict) -> dict:
    """Normalized structural projection of an IR instance (full or minimal)."""
    sub = ir.get("subnet") or {}
    agg = ir.get("aggregation") or {}
    burn = (agg.get("burn_allocation") or {})
    ws = ir.get("weight_setting") or {}
    sm = (ws.get("smoothing") or {})
    comp = ir.get("composition") or {}
    pms = ir.get("per_miner_state") or {}
    subc = ir.get("sub_competitions") or {}

    signals = []
    for s in (ir.get("scoring_signals") or []):
        if not isinstance(s, dict):
            continue
        fam, spec = resolve_metric(s)
        signals.append((
            fam, spec,
            s.get("metric_kind"),
            bool(s.get("extern", False)),
            s.get("direction"),
            s.get("normalization"),
        ))

    gts = tuple((g.get("kind"), g.get("trust_model")) for g in (ir.get("ground_truth_sources") or []) if isinstance(g, dict))
    guards = tuple(sorted((a.get("kind"), a.get("enforcement")) for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)))

    return {
        # subnet.name is a human label, not mechanism structure -> excluded from the signature.
        "netuid": sub.get("netuid"),
        "lang": sub.get("implementation_lang"),
        "status": ir.get("mechanism_status") or "unknown",
        "submission": tuple(sorted((ir.get("task") or {}).get("submission_format") or [])),
        "shape": comp.get("shape"),
        "overlays": tuple(sorted(comp.get("overlays") or [])),
        "signals": tuple(signals),
        "ground_truth": gts,
        "agg": (
            agg.get("method"), agg.get("composition"), agg.get("normalization"),
            _num(agg.get("temperature")), _num(agg.get("decay_rate")), _num(agg.get("min_weight_floor")),
            bool(burn.get("enabled", False)), bool(burn.get("enabled", False)) and bool(burn.get("dynamic", False)),
        ),
        "weights": (
            ws.get("cadence"), ws.get("on_chain_call"),
            sm.get("kind"), _num(sm.get("alpha")), sm.get("window"),
        ),
        "guards": guards,
        "sub": (subc.get("structure"), subc.get("count")),
        "state": (bool(pms.get("tracked", False)), tuple(sorted(pms.get("state_kinds") or []))),
    }


def signature_diff(a: dict, b: dict) -> list[str]:
    sa, sb = signature(a), signature(b)
    return [f"{k}: {sa.get(k)!r} != {sb.get(k)!r}" for k in sa if sa.get(k) != sb.get(k)]


# --------------------------------------------------------------------------- #
# lift: IR -> IMML text
# --------------------------------------------------------------------------- #

def _s(x):
    """emit a scalar as IMML token; None -> '-'."""
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def _esc(x) -> str:
    return '"' + str(x or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


SHAPE_KW = {
    "pipeline": "Pipeline", "multiplex": "Multiplex", "gated": "Gated",
    "multiplicative": "Multiplicative", "overlay_only": "OverlayOnly", "opaque": "Opaque",
}


def _pascal(s) -> str:
    """snake_case -> PascalCase (child-object / type names, QML style)."""
    return "".join(w.capitalize() for w in str(s).split("_"))


def _snake(s) -> str:
    """PascalCase -> snake_case (inverse of _pascal for the IR's lowercase enums)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", str(s)).lower()


# word-boundary splitter: acronym run, capitalized/lower word, all-caps run, or digit run
_WORD = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")


def _camel_id(raw: str | None) -> str:
    """Derive a QML-style camelCase `id` from a human subnet name (QML: ids are camelCase)."""
    ascii_words = "".join(c if (c.isascii() and c.isalnum()) else " " for c in (raw or "mechanism"))
    words = _WORD.findall(ascii_words)
    if not words:
        return "mechanism"
    out = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    return out if out[0].isalpha() else "m" + out


def lift(ir: dict) -> str:
    sub = ir.get("subnet") or {}
    name = _camel_id(sub.get("name"))
    agg = ir.get("aggregation") or {}
    burn = agg.get("burn_allocation") or {}
    ws = ir.get("weight_setting") or {}
    sm = ws.get("smoothing") or {}
    comp = ir.get("composition") or {}
    pms = ir.get("per_miner_state") or {}
    subc = ir.get("sub_competitions") or {}
    shape = comp.get("shape") or "pipeline"
    overlays = set(comp.get("overlays") or [])

    IND, IND2 = "    ", "        "   # 4-space indentation (IMML coding conventions)

    def rv(v, quote=False):
        """render a scalar value; None -> None (omit). quote=True double-quotes strings."""
        if v is None:
            return None
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, float) and v == int(v):
            return str(int(v))
        if isinstance(v, (int, float)):
            return str(v)
        return _esc(v) if quote else str(v)

    def pb(pairs, indent=IND2):
        """grouped-property block, one property per line; nulls omitted, empty -> {}.
        `indent` is the indentation of the owning line (the closing brace aligns to it)."""
        items = [f"{k}: {r}" for k, r in pairs if r is not None]
        if not items:
            return "{}"
        inner = indent + IND
        return "{\n" + "\n".join(f"{inner}{it}" for it in items) + f"\n{indent}}}"

    # --- id, then header properties (QML: id is its own group, blank line after) ---
    L = ["Mechanism {"]
    L.append(f"{IND}id: {name}")
    L.append("")
    L.append(f"{IND}netuid: {rv(sub.get('netuid')) or '-'}")
    L.append(f"{IND}lang: {sub.get('implementation_lang') or 'python'}")
    L.append(f"{IND}status: {ir.get('mechanism_status') or 'unknown'}")
    formats = (ir.get("task") or {}).get("submission_format") or []
    # single-element lists omit the brackets (QML list convention)
    L.append(f"{IND}submission: {formats[0]}" if len(formats) == 1
             else f"{IND}submission: [{', '.join(formats)}]")

    # --- overlays (@burn, @guards, @state) ---
    ov = []
    if "burn" in overlays:
        uid = burn.get("address_or_uid")
        uidr = None if uid is None else (str(int(uid)) if isinstance(uid, int) and not isinstance(uid, bool) else _esc(uid))
        fr = "dynamic" if burn.get("dynamic") else rv(burn.get("fraction"))
        ov.append(f"{IND}@burn {pb([('uid', uidr), ('fraction', fr)], IND)}")
    if "guards" in overlays:
        guards = [a for a in (ir.get("anti_gaming") or []) if isinstance(a, dict)]

        def grender(a):
            return f"{_pascal(a.get('kind'))} {pb([('enforcement', rv(a.get('enforcement')))], IND2)}"

        if not guards:
            ov.append(f"{IND}@guards {{}}")
        else:                                     # one guard (child object) per line
            ov.append(f"{IND}@guards {{")
            ov.extend(f"{IND2}{grender(a)}" for a in guards)
            ov.append(f"{IND}}}")
    if "state" in overlays:
        ov.append(f"{IND}@state {{ {', '.join(pms.get('state_kinds') or [])} }}")
    if ov:
        L.append("")
        L.extend(ov)

    # --- combinator block ---
    L.append("")
    head = f"Multiplex<{subc.get('structure') or 'multi_mechanism'}>" if shape == "multiplex" \
        else SHAPE_KW.get(shape, "Pipeline")
    L.append(f"{IND}{head} {{")

    for s in (ir.get("scoring_signals") or []):
        if not isinstance(s, dict):
            continue
        mk = s.get("metric_kind") or "other"
        fam, spec = resolve_metric(s)
        parts = [f"metric {mk}"]
        if fam:
            parts.append(f"fam {fam}")
        if spec:
            parts.append(f"spec {spec}")
        if s.get("metric_kind_other"):
            parts.append(f"raw {_esc(s['metric_kind_other'])}")
        if s.get("extern"):
            parts.append("extern")
        L.append(f"{IND2}score: {' '.join(parts)} "
                 f"{pb([('direction', rv(s.get('direction'))), ('normalization', s.get('normalization') or 'none')])}")

    for g in (ir.get("ground_truth_sources") or []):
        if isinstance(g, dict):
            L.append(f"{IND2}gt: {_pascal(g.get('kind'))} {pb([('trust_model', rv(g.get('trust_model') or 'unknown'))])}")

    if agg:
        L.append(f"{IND2}aggregate: {_pascal(agg.get('method') or 'proportional')} "
                 f"{pb([('composition', rv(agg.get('composition'))), ('normalization', rv(agg.get('normalization'))), ('temperature', rv(agg.get('temperature'))), ('decay_rate', rv(agg.get('decay_rate'))), ('min_weight_floor', rv(agg.get('min_weight_floor')))])}")
    if sm:
        k = sm.get("kind") or "none"
        params = []
        if sm.get("alpha") is not None:
            params.append(f"alpha: {rv(sm.get('alpha'))}")
        if sm.get("window") is not None:
            params.append(f"window: {rv(sm.get('window'))}")
        ptxt = f"({', '.join(params)})" if params else ""
        L.append(f"{IND2}smooth: smoother {k}{ptxt}")
    if ws:
        L.append(f"{IND2}emit: {_pascal(ws.get('on_chain_call') or 'set_weights')} "
                 f"{pb([('cadence', rv(ws.get('cadence') or 'unknown')), ('tempo', rv(ws.get('tempo_or_interval'), quote=True))])}")
    if subc:
        L.append(f"{IND2}tracks {pb([('structure', rv(subc.get('structure') or 'none')), ('count', rv(subc.get('count')))])}")

    L.append(f"{IND}}}")
    L.append("}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# compile: IMML text -> minimal IR
# --------------------------------------------------------------------------- #

GRAMMAR = r"""
start: mechanism
mechanism: "Mechanism" "{" "id" ":" NAME header* block "}"

header: "netuid" ":" value           -> netuid
      | "lang" ":" NAME               -> lang
      | "status" ":" NAME             -> status
      | "submission" ":" "[" [NAME ("," NAME)*] "]"  -> submission
      | "submission" ":" NAME         -> submission_one
      | "@burn" propblock             -> burn
      | "@guards" "{" guarddef* "}"   -> guards
      | "@state" "{" [NAME ("," NAME)*] "}"  -> state

guarddef: NAME [propblock]

block: shape "{" item* "}"
shape: "Pipeline" -> pipeline
     | "Multiplex" "<" NAME ">" -> multiplex
     | "Gated" -> gated
     | "Multiplicative" -> multiplicative
     | "OverlayOnly" -> overlay_only
     | "Opaque" -> opaque

item: "score" ":" scorer [propblock]               -> signal
    | "gt" ":" NAME [propblock]                     -> gt          // NAME is a PascalCase type
    | "aggregate" ":" NAME [propblock]              -> aggregate   // NAME is a PascalCase type
    | "smooth" ":" "smoother" smoother              -> smooth
    | "emit" ":" NAME [propblock]                   -> emit        // NAME is a PascalCase type
    | "tracks" propblock                            -> tracks

scorer: "metric" NAME mopt* -> metric
mopt: "fam" NAME            -> mfam
    | "spec" NAME           -> mspec
    | "raw" ESCAPED_STRING  -> mraw
    | "extern"              -> mext

smoother: NAME [ "(" smparam ("," smparam)* ")" ]  -> smoothing
smparam: "alpha" ":" value  -> salpha
       | "window" ":" value -> swindow

propblock: "{" [prop (";"? prop)*] "}"  // grouped-property; one per line (newline or ';', no commas)
prop: NAME ":" value
value: SIGNED_NUMBER  -> number
     | "-"            -> nullval
     | ESCAPED_STRING -> strval
     | NAME           -> name

NAME: /[A-Za-z_][A-Za-z0-9_]*/
%import common.SIGNED_NUMBER
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
%ignore /#[^\n]*/
"""

_parser = Lark(GRAMMAR, parser="earley", maybe_placeholders=False)


def _scalar(v):
    return v  # tokens already coerced by transformer


@v_args(inline=True)
class _T(Transformer):
    # values
    def number(self, n):
        f = float(n)
        return int(f) if f == int(f) else f
    def nullval(self):
        return None
    def strval(self, s):
        return _unesc(s)
    def name(self, n):
        return str(n)
    # property blocks
    def prop(self, key, val):
        return (str(key), val)
    def propblock(self, *props):
        return dict(props)
    # headers
    def netuid(self, v):
        return ("netuid", v)
    def lang(self, v):
        return ("lang", str(v))
    def status(self, v):
        return ("status", str(v))
    def submission(self, *names):
        return ("submission", [str(n) for n in names])
    def submission_one(self, name):
        return ("submission", [str(name)])
    def guarddef(self, kind, props=None):
        return (_snake(kind), (props or {}).get("enforcement"))
    def guards(self, *gs):
        return ("guards", list(gs))
    def state(self, *names):
        return ("state", [str(n) for n in names])
    def burn(self, props):
        return ("burn", props)
    # shapes
    def pipeline(self):
        return ("pipeline", None)
    def multiplex(self, structure):
        return ("multiplex", str(structure))
    def gated(self):
        return ("gated", None)
    def multiplicative(self):
        return ("multiplicative", None)
    def overlay_only(self):
        return ("overlay_only", None)
    def opaque(self):
        return ("opaque", None)
    def shape(self, s):
        return s
    # scorer
    def mfam(self, n):
        return ("fam", str(n))
    def mspec(self, n):
        return ("spec", str(n))
    def mraw(self, s):
        return ("raw", _unesc(s))
    def mext(self):
        return ("extern", True)
    def metric(self, kind, *opts):
        m = {"kind": str(kind), "family": None, "specific": None, "raw": None, "extern": False}
        for tag, val in opts:
            m[{"fam": "family", "spec": "specific", "raw": "raw", "extern": "extern"}[tag]] = val
        return m
    # items
    def signal(self, scorer, props=None):
        p = props or {}
        return ("signal", scorer, p.get("direction"), p.get("normalization") or "none")
    def gt(self, kind, props=None):
        return ("gt", _snake(kind), (props or {}).get("trust_model"))
    def aggregate(self, method, props=None):
        return ("aggregate", _snake(method), props or {})
    def salpha(self, v):
        return ("alpha", v)
    def swindow(self, v):
        return ("window", v)
    def smoothing(self, kind, *params):
        sm = {"kind": str(kind), "alpha": None, "window": None}
        for tag, val in params:
            sm[tag] = val
        return ("smoothing", sm)
    def smooth(self, sm):
        return ("smooth", sm[1])
    def emit(self, call, props=None):
        p = props or {}
        return ("emit", _snake(call), p.get("cadence"), p.get("tempo"))
    def tracks(self, props):
        return ("tracks", props)
    def block(self, shape, *items):
        return ("block", shape, list(items))
    def mechanism(self, name, *rest):
        return ("mechanism", str(name), list(rest[:-1]), rest[-1])
    def start(self, m):
        return m


def _unesc(tok) -> str:
    s = str(tok)
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\"', '"').replace("\\\\", "\\")


def compile_text(text: str) -> dict:
    """Parse IMML text into a minimal IR dict (structural fields only)."""
    tree = _parser.parse(text)
    _, name, headers, block = _T().transform(tree)

    ir: dict = {"subnet": {"name": name.replace("_", " ")}, "task": {}, "scoring_signals": []}
    burn = {"enabled": False}
    for h in headers:
        tag = h[0]
        if tag == "netuid":
            ir["subnet"]["netuid"] = h[1]
        elif tag == "lang":
            ir["subnet"]["implementation_lang"] = h[1]
        elif tag == "status":
            ir["mechanism_status"] = h[1]
        elif tag == "submission":
            ir["task"]["submission_format"] = h[1]
        elif tag == "burn":
            props = h[1]
            fr = props.get("fraction")
            burn = {"enabled": True, "address_or_uid": props.get("uid"),
                    "dynamic": fr == "dynamic",
                    "fraction": None if fr == "dynamic" else fr}
        elif tag == "guards":
            ir["anti_gaming"] = [{"kind": k, "enforcement": e} for (k, e) in h[1]]
        elif tag == "state":
            ir["per_miner_state"] = {"tracked": True, "state_kinds": h[1]}

    _, (shape_kind, structure), items = block
    overlays = []
    if burn.get("enabled"):
        overlays.append("burn")
    if "anti_gaming" in ir:
        overlays.append("guards")
    if "per_miner_state" in ir:
        overlays.append("state")
    ir["composition"] = {"shape": shape_kind, "overlays": overlays}

    gts = []
    for it in items:
        tag = it[0]
        if tag == "signal":
            _, sc, direction, norm = it
            sig = {"name": "metric", "direction": direction, "normalization": norm,
                   "metric_kind": sc["kind"]}
            if sc["family"]:
                sig["metric_family"] = sc["family"]
            if sc["specific"]:
                sig["metric_specific"] = sc["specific"]
            if sc["raw"]:
                sig["metric_kind_other"] = sc["raw"]
            if sc["extern"]:
                sig["extern"] = True
            ir["scoring_signals"].append(sig)
        elif tag == "gt":
            gts.append({"kind": it[1], "trust_model": it[2]})
        elif tag == "aggregate":
            _, method, props = it
            agg = {"method": method, "composition": props.get("composition"),
                   "normalization": props.get("normalization"), "temperature": props.get("temperature"),
                   "decay_rate": props.get("decay_rate"), "min_weight_floor": props.get("min_weight_floor"),
                   "burn_allocation": burn}
            ir["aggregation"] = agg
        elif tag == "smooth":
            ir.setdefault("weight_setting", {})["smoothing"] = it[1]
        elif tag == "emit":
            _, call, cadence, tempo = it
            ws = ir.setdefault("weight_setting", {})
            ws.update({"on_chain_call": call, "cadence": cadence, "tempo_or_interval": tempo})
        elif tag == "tracks":
            props = it[1]
            ir["sub_competitions"] = {"structure": props.get("structure"), "count": props.get("count")}
    if gts:
        ir["ground_truth_sources"] = gts
    if "aggregation" not in ir and burn.get("enabled"):
        ir["aggregation"] = {"burn_allocation": burn}
    ir["composition"]["extern_count"] = sum(1 for s in ir["scoring_signals"] if s.get("extern"))
    return _prune(ir)


def _prune(obj):
    """Drop dict keys whose value is None (absent == null for nullable fields; required-string enums
    must not carry None). Keeps False/0/"" and empty containers."""
    if isinstance(obj, dict):
        return {k: _prune(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_prune(v) for v in obj]
    return obj
