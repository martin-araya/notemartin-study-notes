#!/usr/bin/env python3
"""Genera fixtures para `evals/note-templates-sample/`.

Produce:
- `fixtures/sample-ir.json`: IR sintético con frontmatter completo (5 universales).
- `fixtures/cabecera-snapshot.json`: dump de los 7 outputs de `emit_cabecera`.

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skill" / "notemartin-study-notes"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
HEADER_PATH = SKILL_DIR / "scripts" / "render" / "_header.py"


def _load_header():
    spec = importlib.util.spec_from_file_location(
        "scripts.render._header_evals", HEADER_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.render._header_evals", mod)
    spec.loader.exec_module(mod)
    return mod


def _build_sample_ir() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "sample-concept",
        "title": "Arrays in PostgreSQL",
        "layer": "l2",
        "frontmatter": {
            "title": "Arrays in PostgreSQL",
            "note-type": "concept",
            "status": "published",
            "summary": "PostgreSQL arrays are 1-dimensional lists of values of the same type, useful for many-to-one relationships.",
            "reading-time-minutes": 5,
            "tags": ["type/concept", "domain/database"],
            "source": "PostgreSQL 16 Documentation",
            "source-type": "manual",
            "source-anchor": "8.15",
            "source-url": "https://www.postgresql.org/docs/16/arrays.html",
            "retrieved": "2026-09-15",
            "language": "en",
            "vendor": "PostgreSQL Global Development Group",
            "product": "PostgreSQL",
            "product-version": "16",
        },
        "blocks": [],
    }


def _build_cabecera_snapshot() -> dict:
    mod = _load_header()
    fm = _build_sample_ir()["frontmatter"]
    snapshot: dict = {}
    for dest in mod.SUPPORTED_DESTS:
        out = mod.emit_cabecera(fm, dest=dest)
        if isinstance(out, dict):
            snapshot[dest] = out
        elif isinstance(out, tuple):
            snapshot[dest] = {"anverso": out[0], "reverso": out[1]}
        else:
            snapshot[dest] = out
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true", help="Fuerza regeneración.")
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    ir_path = FIXTURES_DIR / "sample-ir.json"
    snap_path = FIXTURES_DIR / "cabecera-snapshot.json"

    if args.regen or not ir_path.exists():
        with ir_path.open("w", encoding="utf-8") as f:
            json.dump(_build_sample_ir(), f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Sample IR escrito: {ir_path}")

    if args.regen or not snap_path.exists():
        with snap_path.open("w", encoding="utf-8") as f:
            json.dump(_build_cabecera_snapshot(), f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Snapshot cabecera: {snap_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
