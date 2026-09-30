#!/usr/bin/env python3
"""build_fixtures.py — F109 eval fixtures para consolidate.

Genera un workdir sintético con:
  - 6 IRs:
    * a (concept, links a nonexistent → broken-wikilink)
    * b (concept, normal)
    * c (concept, sin incoming → orphan-note)
    * d (procedure, normal)
    * f (cheatsheet, normal)
    * g (glossary-term, normal)
  - glossary.json con 1 colisión R3 (alias "mv" en 2 términos)
  - manifest.json vacío (lo crea consolidate)

Stdlib puro.

Uso:
    python3 evals/consolidation-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
WORKDIR = FIXTURES_DIR / "workdir"
IR_DIR = WORKDIR / "ir"
KNOWLEDGE_DIR = WORKDIR / "knowledge"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _write_ir(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_irs() -> None:
    if IR_DIR.exists():
        shutil.rmtree(IR_DIR)
    IR_DIR.mkdir(parents=True)
    # IR `a`: tiene link a "nonexistent" → broken-wikilink.
    _write_ir(IR_DIR / "a.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "a", "title": "A",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "A", "note-type": "concept"},
        "blocks": [{
            "node": "paragraph", "attrs": {"capability": "paragraph"},
            "source_refs": [],
            "children": [
                {"node": "link-note",
                 "attrs": {"target": "nonexistent", "capability": "link-note",
                            "text": "x"},
                 "source_refs": []},
            ],
        }],
    })
    # IR `b`: normal (recibe link de a y de d).
    _write_ir(IR_DIR / "b.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "b", "title": "B",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "B", "note-type": "concept"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Body B", "capability": "text"},
                    "source_refs": []}],
    })
    # IR `c`: orphan-note (sin incoming links).
    _write_ir(IR_DIR / "c.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "c", "title": "C",
        "layer": "l2", "note_type": "concept",
        "frontmatter": {"title": "C", "note-type": "concept"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Body C", "capability": "text"},
                    "source_refs": []}],
    })
    # IR `d`: procedure normal con link a b.
    _write_ir(IR_DIR / "d.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "d", "title": "D",
        "layer": "l2", "note_type": "procedure",
        "frontmatter": {"title": "D", "note-type": "procedure"},
        "blocks": [{
            "node": "paragraph", "attrs": {"capability": "paragraph"},
            "source_refs": [],
            "children": [
                {"node": "link-note",
                 "attrs": {"target": "b", "capability": "link-note",
                            "text": "b"},
                 "source_refs": []},
            ],
        }],
    })
    # IR `f`: cheatsheet (pase 4 detecta).
    _write_ir(IR_DIR / "f.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "f", "title": "F",
        "layer": "l1", "note_type": "cheatsheet",
        "frontmatter": {"title": "F", "note-type": "cheatsheet",
                          "source-anchor": "12.1"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Cheatsheet F", "capability": "text"},
                    "source_refs": []}],
    })
    # IR `g`: glossary-term (recibe link de b para evitar orphan).
    _write_ir(IR_DIR / "g.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "g", "title": "G",
        "layer": "l1", "note_type": "glossary-term",
        "frontmatter": {"title": "G", "note-type": "glossary-term"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Glossary G", "capability": "text"},
                    "source_refs": []}],
    })
    # IR `x`: orphan-note (sin incoming).
    _write_ir(IR_DIR / "x.note-ir.json", {
        "schema_version": "1.0.0", "note_id": "x", "title": "X",
        "layer": "l1", "note_type": "concept",
        "frontmatter": {"title": "X", "note-type": "concept"},
        "blocks": [{"node": "text",
                    "attrs": {"text": "Body X", "capability": "text"},
                    "source_refs": []}],
    })


def build_glossary() -> None:
    if KNOWLEDGE_DIR.exists():
        shutil.rmtree(KNOWLEDGE_DIR)
    KNOWLEDGE_DIR.mkdir(parents=True)
    # Glossary con R3 violation: alias "mv" en 2 términos.
    glossary = {
        "schema_version": "1.0.0",
        "source": {"id": "s", "vendor": "postgres"},
        "terms": [
            {"canonical": "mvcc",
             "definition": "Multi-Version Concurrency Control.",
             "domain": "postgres",
             "aliases": [{"alias": "mv", "kind": "acronym"}],
             "definitions": []},
            {"canonical": "wal",
             "definition": "Write-Ahead Logging.",
             "domain": "postgres",
             "aliases": [{"alias": "mv", "kind": "acronym"}],
             "definitions": []},
        ],
        "build_metadata": {"built_at": "2026-01-01T00:00:00Z", "term_count": 2},
    }
    (KNOWLEDGE_DIR / "glossary.json").write_text(
        json.dumps(glossary, indent=2), encoding="utf-8"
    )


def write_expected() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected = {
        "broken_wikilink_count": 1,
        "orphan_note_count": 2,
        "missing_target_count": 0,
        "r3_violation_count": 1,
        "r3_violation_alias": "mv",
        "r3_violation_terms": ["mvcc", "wal"],
        "cheatsheet_count": 1,
        "consistency_candidate_count": 0,
        "total_notes": 7,
    }
    (EXPECTED_DIR / "expected.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    build_irs()
    build_glossary()
    write_expected()
    sys.stdout.write(
        f"OK — 7 IRs; glossary; expected/expected.json\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())