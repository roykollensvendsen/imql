#!/usr/bin/env python3
"""Lift an IR instance (YAML) to IMML text. Usage: lift.py <instance.yaml> [...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imml_core as C  # noqa: E402
import yaml  # noqa: E402

if len(sys.argv) < 2:
    print(__doc__)
    raise SystemExit(2)
for p in sys.argv[1:]:
    ir = yaml.safe_load(Path(p).read_text())
    if len(sys.argv) > 2:
        sys.stdout.write(f"# === {p} ===\n")
    sys.stdout.write(C.lift(ir))   # already newline-terminated (canonical form)
