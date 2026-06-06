#!/usr/bin/env python3
"""IMQL core: the structural signature, IR->IMQL (lift), and IMQL->IR (compile).

The round-trip success criterion is over the mechanism's STRUCTURAL SIGNATURE — the design:
enums, numeric params, typed primitive nodes, the metric leaves, and the composition tree.
It deliberately EXCLUDES prose and provenance (task.summary, *.notes, provenance.*, exact
free-text), which are extraction bookkeeping, not part of a design language. "100% fidelity"
means: signature(ir) == signature(compile(lift(ir))) for every corpus instance.

lift(ir)        -> IMQL text capturing the full signature
compile(text)   -> a MINIMAL IR dict populated with only the structural fields
signature(ir)   -> the normalized projection used for comparison (works on full or minimal IR)
"""
from __future__ import annotations

from lark import Lark, Transformer, v_args

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
        signals.append((
            s.get("metric_family"),
            s.get("metric_specific"),
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
# lift: IR -> IMQL text
# --------------------------------------------------------------------------- #

def _s(x):
    """emit a scalar as IMQL token; None -> '-'."""
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
    "pipeline": "pipeline", "multiplex": "multiplex", "gated": "gated",
    "multiplicative": "multiplicative", "overlay_only": "overlay_only", "opaque": "opaque",
}


def lift(ir: dict) -> str:
    sub = ir.get("subnet") or {}
    raw_name = (sub.get("name") or "Mechanism").replace(" ", "_")
    name = "".join(c for c in raw_name if c.isascii() and (c.isalnum() or c == "_"))
    if not name or not name[0].isalpha():
        name = "M_" + name
    name = name or "Mechanism"
    agg = ir.get("aggregation") or {}
    burn = agg.get("burn_allocation") or {}
    ws = ir.get("weight_setting") or {}
    sm = ws.get("smoothing") or {}
    comp = ir.get("composition") or {}
    pms = ir.get("per_miner_state") or {}
    subc = ir.get("sub_competitions") or {}
    shape = comp.get("shape") or "pipeline"
    overlays = set(comp.get("overlays") or [])

    L = [f"mechanism {name} {{"]
    L.append(f"  netuid: {_s(sub.get('netuid'))}")
    L.append(f"  lang: {_s(sub.get('implementation_lang') or 'python')}")
    L.append(f"  status: {_s(ir.get('mechanism_status') or 'unknown')}")
    L.append(f"  submission: [{', '.join((ir.get('task') or {}).get('submission_format') or [])}]")

    if "burn" in overlays:
        uid = burn.get("address_or_uid")
        uidtok = "-" if uid is None else (str(int(uid)) if isinstance(uid, int) and not isinstance(uid, bool) else _esc(uid))
        L.append(f"  @burn {{ uid: {uidtok}, "
                 f"fraction: {'dynamic' if burn.get('dynamic') else _s(burn.get('fraction'))} }}")
    if "guards" in overlays:
        gl = " ".join(f"{a.get('kind')} {{ enforcement: {a.get('enforcement')} }}"
                      for a in (ir.get("anti_gaming") or []) if isinstance(a, dict))
        L.append(f"  @guards {{ {gl} }}")
    if "state" in overlays:
        L.append(f"  @state {{ {', '.join(pms.get('state_kinds') or [])} }}")

    # shape block header
    if shape == "multiplex":
        L.append(f"  multiplex<{subc.get('structure') or 'multi_mechanism'}> {{")
    else:
        L.append(f"  {SHAPE_KW.get(shape, 'pipeline')} {{")

    # signals — leaf carries metric_kind (always) + optional family/specific/raw/extern
    for s in (ir.get("scoring_signals") or []):
        if not isinstance(s, dict):
            continue
        mk = s.get("metric_kind") or "other"
        parts = [f"metric {mk}"]
        if s.get("metric_family"):
            parts.append(f"fam {s['metric_family']}")
        if s.get("metric_specific"):
            parts.append(f"spec {s['metric_specific']}")
        if s.get("metric_kind_other"):
            parts.append(f"raw {_esc(s['metric_kind_other'])}")
        if s.get("extern"):
            parts.append("extern")
        L.append(f"    score: {' '.join(parts)} {{ direction: {_s(s.get('direction'))}, "
                 f"normalization: {_s(s.get('normalization') or 'none')} }}")

    # ground-truth sources (emitted as standalone lines; order preserved)
    for g in (ir.get("ground_truth_sources") or []):
        if isinstance(g, dict):
            L.append(f"    gt: {g.get('kind')} {{ trust_model: {_s(g.get('trust_model') or 'unknown')} }}")

    # aggregate
    if agg:
        L.append(f"    aggregate: aggregator {_s(agg.get('method') or 'proportional')} {{ "
                 f"composition: {_s(agg.get('composition'))}, normalization: {_s(agg.get('normalization'))}, "
                 f"temperature: {_s(agg.get('temperature'))}, decay_rate: {_s(agg.get('decay_rate'))}, "
                 f"min_weight_floor: {_s(agg.get('min_weight_floor'))} }}")
    # smooth — carry kind + any alpha/window present (independent of kind)
    if sm:
        k = sm.get("kind") or "none"
        params = []
        if sm.get("alpha") is not None:
            params.append(f"alpha: {_s(sm.get('alpha'))}")
        if sm.get("window") is not None:
            params.append(f"window: {_s(sm.get('window'))}")
        ptxt = f"({', '.join(params)})" if params else ""
        L.append(f"    smooth: smoother {k}{ptxt}")
    # emit
    if ws:
        L.append(f"    emit: {_s(ws.get('on_chain_call') or 'set_weights')} {{ "
                 f"cadence: {_s(ws.get('cadence') or 'unknown')}, tempo: {_esc(ws.get('tempo_or_interval'))} }}")
    # tracks (multiplex bookkeeping)
    if subc:
        L.append(f"    tracks {{ structure: {_s(subc.get('structure') or 'none')}, count: {_s(subc.get('count'))} }}")

    L.append("  }")
    L.append("}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# compile: IMQL text -> minimal IR
# --------------------------------------------------------------------------- #

GRAMMAR = r"""
start: mechanism
mechanism: "mechanism" NAME "{" header* block "}"

header: "netuid" ":" scalar          -> netuid
      | "lang" ":" NAME               -> lang
      | "status" ":" NAME             -> status
      | "submission" ":" "[" [NAME ("," NAME)*] "]"  -> submission
      | "@burn" "{" "uid" ":" uidval "," "fraction" ":" fracval "}"   -> burn
      | "@guards" "{" guarddef* "}"   -> guards
      | "@state" "{" [NAME ("," NAME)*] "}"  -> state

guarddef: NAME "{" "enforcement" ":" NAME "}"
uidval: ESCAPED_STRING -> uidstr
      | SIGNED_NUMBER  -> uidnum
      | "-"            -> nullval
fracval: "dynamic" -> dynamic
       | scalar    -> fracnum

block: shape "{" item* "}"
shape: "pipeline" -> pipeline
     | "multiplex" "<" NAME ">" -> multiplex
     | "gated" -> gated
     | "multiplicative" -> multiplicative
     | "overlay_only" -> overlay_only
     | "opaque" -> opaque

item: "score" ":" scorer "{" "direction" ":" scalar "," "normalization" ":" NAME "}" -> signal
    | "gt" ":" NAME "{" "trust_model" ":" NAME "}"                     -> gt
    | "aggregate" ":" "aggregator" NAME "{" "composition" ":" scalar "," "normalization" ":" scalar "," "temperature" ":" scalar "," "decay_rate" ":" scalar "," "min_weight_floor" ":" scalar "}"  -> aggregate
    | "smooth" ":" "smoother" smoother                                 -> smooth
    | "emit" ":" NAME "{" "cadence" ":" NAME "," "tempo" ":" ESCAPED_STRING "}" -> emit
    | "tracks" "{" "structure" ":" NAME "," "count" ":" scalar "}"     -> tracks

scorer: "metric" NAME mopt* -> metric
mopt: "fam" NAME            -> mfam
    | "spec" NAME           -> mspec
    | "raw" ESCAPED_STRING  -> mraw
    | "extern"              -> mext

smoother: NAME [ "(" smparam ("," smparam)* ")" ]  -> smoothing
smparam: "alpha" ":" scalar  -> salpha
       | "window" ":" scalar -> swindow

scalar: SIGNED_NUMBER -> number
      | "-"           -> nullval
      | NAME          -> name
      | "true"        -> true
      | "false"       -> false

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
    # scalars
    def number(self, n):
        f = float(n)
        return int(f) if f == int(f) else f
    def nullval(self):
        return None
    def name(self, n):
        return str(n)
    def true(self):
        return True
    def false(self):
        return False
    def dynamic(self):
        return "dynamic"
    def fracnum(self, v):
        return v
    def uidstr(self, s):
        return _unesc(s)
    def uidnum(self, n):
        f = float(n)
        return int(f) if f == int(f) else f
    # headers
    def netuid(self, v):
        return ("netuid", v)
    def lang(self, v):
        return ("lang", str(v))
    def status(self, v):
        return ("status", str(v))
    def submission(self, *names):
        return ("submission", [str(n) for n in names])
    def guarddef(self, kind, enf):
        return (str(kind), str(enf))
    def guards(self, *gs):
        return ("guards", list(gs))
    def state(self, *names):
        return ("state", [str(n) for n in names])
    def burn(self, uid, frac):
        return ("burn", uid, frac)
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
    def signal(self, scorer, direction, norm):
        return ("signal", scorer, direction, str(norm))
    def gt(self, kind, trust):
        return ("gt", str(kind), str(trust))
    def aggregate(self, method, comp, norm, temp, decay, floor):
        return ("aggregate", str(method), comp, norm, temp, decay, floor)
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
    def emit(self, call, cadence, tempo):
        return ("emit", str(call), str(cadence), _unesc(tempo))
    def tracks(self, structure, count):
        return ("tracks", str(structure), count)
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
    """Parse IMQL text into a minimal IR dict (structural fields only)."""
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
            _, uid, frac = h
            burn = {"enabled": True, "address_or_uid": uid,
                    "dynamic": frac == "dynamic",
                    "fraction": None if frac == "dynamic" else frac}
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
            _, method, comp, norm, temp, decay, floor = it
            agg = {"method": method, "composition": comp, "normalization": norm,
                   "temperature": temp, "decay_rate": decay, "min_weight_floor": floor,
                   "burn_allocation": burn}
            ir["aggregation"] = agg
        elif tag == "smooth":
            ir.setdefault("weight_setting", {})["smoothing"] = it[1]
        elif tag == "emit":
            _, call, cadence, tempo = it
            ws = ir.setdefault("weight_setting", {})
            ws.update({"on_chain_call": call, "cadence": cadence, "tempo_or_interval": tempo})
        elif tag == "tracks":
            ir["sub_competitions"] = {"structure": it[1], "count": it[2]}
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
