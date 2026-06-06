#!/usr/bin/env python3
"""Validate incentive-mechanism YAML instances against the canonical JSON Schema.

Usage:
    validate.py <path-or-dir> [<path-or-dir> ...]

A path may be a single .yaml/.json instance or a directory (validated recursively).
Exits non-zero if any instance fails validation or if its `schema_version` does not
match schema/VERSION. Designed to be the CI-style gate for the project.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed. Run: pip install -r tooling/requirements.txt")

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("jsonschema not installed. Run: pip install -r tooling/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "incentive-mechanism.schema.json"
VERSION_PATH = ROOT / "schema" / "VERSION"

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def load_instance(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def iter_instances(targets: list[str]):
    for t in targets:
        p = Path(t)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix in (".yaml", ".yml", ".json") and f.name != "VERSION":
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"{YELLOW}skip (not found): {t}{RESET}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text())
    version = VERSION_PATH.read_text().strip()
    validator = Draft202012Validator(schema)

    targets = list(iter_instances(argv))
    if not targets:
        print(f"{YELLOW}No instances found.{RESET}")
        return 2

    n_ok = n_fail = 0
    for path in targets:
        rel = path.relative_to(ROOT) if ROOT in path.parents else path
        try:
            instance = load_instance(path)
        except Exception as exc:  # noqa: BLE001
            print(f"{RED}PARSE FAIL{RESET} {rel}: {exc}")
            n_fail += 1
            continue

        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
        sv = instance.get("schema_version") if isinstance(instance, dict) else None
        version_mismatch = sv is not None and sv != version

        if not errors and not version_mismatch:
            print(f"{GREEN}OK{RESET}       {rel}")
            n_ok += 1
            continue

        n_fail += 1
        print(f"{RED}FAIL{RESET}     {rel}")
        if version_mismatch:
            print(f"  {YELLOW}schema_version {sv!r} != schema/VERSION {version!r}{RESET}")
        for err in errors:
            loc = "/" + "/".join(str(p) for p in err.absolute_path)
            print(f"  {DIM}{loc}{RESET}: {err.message}")

    print()
    total = n_ok + n_fail
    color = GREEN if n_fail == 0 else RED
    print(f"{color}{n_ok}/{total} valid{RESET}  (schema {version})")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
