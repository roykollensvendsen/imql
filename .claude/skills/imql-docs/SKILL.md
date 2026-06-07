---
name: imql-docs
description: >-
  Build, preview, and deploy the IMQL documentation site (Material for MkDocs, Qt-style). Use when the
  user wants to serve the docs locally, edit a page, regenerate the auto-generated reference/examples, or
  deploy a versioned site to GitHub Pages. Most reference is generated from the schema/ontology/grammar/
  instances at build time, so it never drifts.
---

# imql-docs — the documentation site

A Material for MkDocs site under `docs/`, configured in `mkdocs.yml`. It auto-generates most reference
from the canonical artifacts via `docs/gen/build.py` (mkdocs-gen-files), so editing the schema/ontology/
grammar/instances updates the docs on the next build.

## Setup & preview
```bash
./.venv/bin/pip install -r requirements-docs.txt     # mkdocs-material, gen-files, literate-nav, mike, railroad-diagrams
./.venv/bin/mkdocs serve                             # http://localhost:8000 (live reload)
./.venv/bin/mkdocs build --strict                    # the gate: 0 warnings, ~205 pages
```

## What is hand-written vs generated
- **Hand-written** (reuse `spec/` via `--8<--` snippets, base_path `.`): the guide and language pages
  (`docs/guides/*`, `docs/language/index.md` ← spec/04, `docs/language/style.md` ← spec/05), plus
  `docs/index.md` and `docs/guides/quick-start.md`. **Keep `.imql` examples canonical** — they must
  compile (`compile.py`) and pass `fmt.py --check`; the live grammar uses `gt:` items, not
  `from groundtruth`.
- **Generated** by `docs/gen/build.py` (do NOT hand-edit generated pages):
  - `reference/index.md` — primitives from the schema enums + corpus frequencies.
  - `reference/metric-families.md` — from `vocab/metric-ontology.yaml`.
  - `language/grammar.md` — railroad SVGs (railroad-diagrams) for the core productions.
  - `examples/*` — all 189 subnets lifted via `imql_core.lift` (IMQL/IR tabs), grouped in nav by
    archetype (`examples/SUMMARY.md`).
  - `toolchain/cli.md` — from `tooling/*.py` module docstrings (add new scripts to the `order` list).
  - `status/index.md` — embeds the live `reports/*.md`.
- Nav: `docs/SUMMARY.md` (mkdocs-literate-nav). Theme/railroad CSS: `docs/assets/custom.css`.

## Deploy (versioned, GitHub Pages)
`.github/workflows/docs.yml` builds `--strict` and `mike deploy`s to `gh-pages` on push to main; the
version label tracks `schema/VERSION`. Live at **https://roykollensvendsen.github.io/imql/** (Pages is
enabled, source = `gh-pages`). To deploy by hand:
```bash
mike deploy --push --update-aliases "$(cut -d. -f1,2 schema/VERSION)" latest
```

## After a schema/ontology/grammar change
Just rebuild — the generators re-read the canonical sources. Verify `mkdocs build --strict` is clean and
the examples gallery renders the new formatting.
