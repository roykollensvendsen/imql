#!/usr/bin/env python3
"""imql-fmt — the canonical formatter for IMQL (in the spirit of qmlformat / gofmt).

Reformats .imql files to the IMQL coding conventions (spec/05-imql-style.md) by parsing each file
and re-emitting it canonically. Idempotent: formatting an already-formatted file is a no-op.

  fmt.py <file.imql> [...]       print the formatted result to stdout
  fmt.py -i  <file|dir> [...]    rewrite files in place (recurses directories for *.imql)
  fmt.py --check <file|dir> [...]  exit non-zero and list files that are NOT canonically formatted
                                   (use in CI, like `gofmt -l` / `black --check`)

Note: IMQL is structural and the parser ignores `# comments`, so the formatter does not preserve
comments. Keep commentary in surrounding prose/docs, not inside canonical .imql files.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imql_core as C  # noqa: E402


def format_text(text: str) -> str:
    """Parse IMQL and re-emit it canonically."""
    return C.lift(C.compile_text(text))


def iter_files(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            yield from sorted(p.rglob("*.imql"))
        elif p.is_file():
            yield p
        else:
            print(f"imql-fmt: not found: {a}", file=sys.stderr)


def main(argv):
    check = "--check" in argv
    inplace = "-i" in argv or "--write" in argv
    targets = [a for a in argv if not a.startswith("-")]
    if not targets:
        print(__doc__)
        return 2

    n = bad = 0
    for f in iter_files(targets):
        n += 1
        src = f.read_text()
        try:
            out = format_text(src)
        except Exception as exc:  # noqa: BLE001
            print(f"imql-fmt: ERROR {f}: {exc}", file=sys.stderr)
            bad += 1
            continue
        if check:
            if src != out:
                print(f)
                bad += 1
        elif inplace:
            if src != out:
                f.write_text(out)
                print(f"formatted {f}")
        else:
            sys.stdout.write(out)

    if check and bad:
        print(f"\nimql-fmt: {bad}/{n} file(s) need formatting (run: fmt.py -i <path>)", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
