#!/usr/bin/env python3
"""
build_fixtures.py — Genera 4 workdirs para evals/quality-gate-sample/.

  clean/                     — todos los issues=0; coverage=1.0; promote PASS
  with-errors/               — ≥ 1 error bloqueante; promote FAIL
  with-incomplete-coverage/  — SDM con sección sin unidad; not_covered>0
  with-debt/                 — debt registry con entradas activas + aceptadas
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# SDM helper.
def make_sdm(hash_seed: str, sections: list) -> dict:
    return {
        "source": {"hash": (hash_seed * 64)[:64]},
        "sections": sections,
    }


# ────────────────────────────────────────────────────────────────────
# clean: todo válido, coverage 100%, sin errores.
# ────────────────────────────────────────────────────────────────────
def build_clean() -> None:
    sections = [
        {"id": "a" * 12, "title": "Intro", "path": "/ch01/intro",
         "blocks": [
             {"id": "a" * 12, "anchor": {"page": 1, "section_path": "/ch01/intro"},
              "content": {"type": "prose", "text": "PostgreSQL is an ORDBMS."},
              "source": "native"},
         ]},
        {"id": "b" * 12, "title": "Parameters", "path": "/ch02/params",
         "blocks": [
             {"id": "c" * 12, "anchor": {"page": 2, "section_path": "/ch02/params"},
              "content": {"type": "parameter",
                          "name": "shared_buffers",
                          "text": "shared_buffers default 128MB"},
              "source": "native"},
         ]},
    ]
    write_json(FIX / "clean/sdm.json", make_sdm("a", sections))

    # ledger: todas las secciones cubiertas.
    write_json(FIX / "clean/knowledge/ledger.json", {
        "schema_version": "1.0.0",
        "source": {"id": "clean", "hash": "a" * 64},
        "entries": [
            {"unit_id": "u1", "source_section_path": "/ch01/intro",
             "source_block_ids": ["a" * 12], "type": "definition",
             "criticality": "must-keep", "state": "kept",
             "target_note": "clean-intro"},
            {"unit_id": "u2", "source_section_path": "/ch02/params",
             "source_block_ids": ["c" * 12], "type": "parameter",
             "criticality": "must-keep", "state": "kept",
             "target_note": "clean-params"},
        ],
    })

    # IR que referencia los bloques cubiertos.
    write_json(FIX / "clean/ir/clean-intro.note-ir.json", {
        "note_id": "clean-intro",
        "nodes": [
            {"id": "n1", "node": "paragraph",
             "text": "PostgreSQL is an ORDBMS.",
             "source_refs": [{"block_id": "a" * 12, "source_hash": "a" * 64}]},
        ],
    })
    write_json(FIX / "clean/ir/clean-params.note-ir.json", {
        "note_id": "clean-params",
        "nodes": [
            {"id": "p1", "node": "parameter",
             "attrs": {"name": "shared_buffers", "type": "size", "value": 128, "unit": "MB"},
             "source_refs": [{"block_id": "c" * 12, "source_hash": "a" * 64}]},
        ],
    })

    # Notas en formato notemark con status: published.
    note1 = """---
title: "clean-intro"
note-type: concept
status: published
summary: "intro"
reading-time-minutes: 1
---

# clean-intro

## TL;DR
x
"""
    note2 = """---
title: "clean-params"
note-type: configuration
status: published
summary: "params"
reading-time-minutes: 1
---

# clean-params

## TL;DR
x
"""
    write_text(FIX / "clean/notemark/clean-intro.nm", note1)
    write_text(FIX / "clean/notemark/clean-params.nm", note2)


# ────────────────────────────────────────────────────────────────────
# with-errors: IR con nodo fáctico sin source_refs (V-FAUDIT-01).
# ────────────────────────────────────────────────────────────────────
def build_with_errors() -> None:
    sections = [
        {"id": "d" * 12, "title": "Body", "path": "/ch01/body",
         "blocks": [
             {"id": "e" * 12, "anchor": {"page": 1, "section_path": "/ch01/body"},
              "content": {"type": "prose", "text": "Some factual text here."},
              "source": "native"},
         ]},
    ]
    write_json(FIX / "with-errors/sdm.json", make_sdm("d", sections))

    write_json(FIX / "with-errors/knowledge/ledger.json", {
        "schema_version": "1.0.0",
        "source": {"id": "with-errors", "hash": "d" * 64},
        "entries": [
            {"unit_id": "u1", "source_section_path": "/ch01/body",
             "source_block_ids": ["e" * 12], "type": "definition",
             "criticality": "must-keep", "state": "kept",
             "target_note": "err-note"},
        ],
    })

    # IR con un nodo fáctico SIN source_refs → V-FAUDIT-01 error.
    write_json(FIX / "with-errors/ir/err-note.note-ir.json", {
        "note_id": "err-note",
        "nodes": [
            {"id": "n1", "node": "paragraph",
             "text": "A factual claim with NO source_refs.",
             "external": False, "derived": False,
             "source_refs": []},   # V-FAUDIT-01
            {"id": "n2", "node": "paragraph",
             "text": "A claim with proper backing.",
             "source_refs": [{"block_id": "e" * 12, "source_hash": "d" * 64}]},
        ],
    })

    note = """---
title: "err-note"
note-type: concept
status: published
summary: "x"
reading-time-minutes: 1
---

# err-note

## TL;DR
x
"""
    write_text(FIX / "with-errors/notemark/err-note.nm", note)


# ────────────────────────────────────────────────────────────────────
# with-incomplete-coverage: SDM con sección no cubierta.
# ────────────────────────────────────────────────────────────────────
def build_with_incomplete_coverage() -> None:
    sections = [
        {"id": "f" * 12, "title": "Covered", "path": "/ch01/covered",
         "blocks": [
             {"id": "1" * 12, "anchor": {"page": 1, "section_path": "/ch01/covered"},
              "content": {"type": "prose", "text": "Covered text."},
              "source": "native"},
         ]},
        {"id": "a" * 12, "title": "Uncovered", "path": "/ch02/uncovered",
         "blocks": [
             {"id": "2" * 12, "anchor": {"page": 2, "section_path": "/ch02/uncovered"},
              "content": {"type": "prose", "text": "Uncovered text."},
              "source": "native"},
         ]},
    ]
    write_json(FIX / "with-incomplete-coverage/sdm.json",
               make_sdm("f", sections))

    # Ledger: solo /ch01/covered cubierto.
    write_json(FIX / "with-incomplete-coverage/knowledge/ledger.json", {
        "schema_version": "1.0.0",
        "source": {"id": "with-incomplete-coverage", "hash": "f" * 64},
        "entries": [
            {"unit_id": "u1", "source_section_path": "/ch01/covered",
             "source_block_ids": ["1" * 12], "type": "definition",
             "criticality": "must-keep", "state": "kept",
             "target_note": "inc-note"},
        ],
    })

    write_json(FIX / "with-incomplete-coverage/ir/inc-note.note-ir.json", {
        "note_id": "inc-note",
        "nodes": [
            {"id": "n1", "node": "paragraph",
             "text": "Covered.",
             "source_refs": [{"block_id": "1" * 12, "source_hash": "f" * 64}]},
        ],
    })

    note = """---
title: "inc-note"
note-type: concept
status: published
summary: "x"
reading-time-minutes: 1
---

# inc-note

## TL;DR
x
"""
    write_text(FIX / "with-incomplete-coverage/notemark/inc-note.nm", note)


# ────────────────────────────────────────────────────────────────────
# with-debt: debt registry con 1 warning activa + 1 warning aceptada.
# ────────────────────────────────────────────────────────────────────
def build_with_debt() -> None:
    sections = [
        {"id": "c" * 12, "title": "Body", "path": "/ch01/body",
         "blocks": [
             {"id": "3" * 12, "anchor": {"page": 1, "section_path": "/ch01/body"},
              "content": {"type": "prose", "text": "Body text."},
              "source": "native"},
         ]},
    ]
    write_json(FIX / "with-debt/sdm.json", make_sdm("c", sections))
    write_json(FIX / "with-debt/knowledge/ledger.json", {
        "schema_version": "1.0.0",
        "source": {"id": "with-debt", "hash": "c" * 64},
        "entries": [
            {"unit_id": "u1", "source_section_path": "/ch01/body",
             "source_block_ids": ["3" * 12], "type": "definition",
             "criticality": "must-keep", "state": "kept",
             "target_note": "debt-note"},
        ],
    })

    write_json(FIX / "with-debt/ir/debt-note.note-ir.json", {
        "note_id": "debt-note",
        "nodes": [
            {"id": "n1", "node": "paragraph",
             "text": "Body.",
             "source_refs": [{"block_id": "3" * 12, "source_hash": "c" * 64}]},
        ],
    })

    # Debt registry preexistente.
    write_json(FIX / "with-debt/reports/debt.json", [
        {
            "id": "QG-DEBT-0001",
            "kind": "warning",
            "scope": "global",
            "reason": "renombrar capítulo en próximo ciclo",
            "raised_by": "human",
            "rule_id": "V-MISC-001",
            "created_at": "2026-09-01T00:00:00+00:00",
            "expires_at": "2026-12-01",
            "accepted_by": "maría",
        },
        {
            "id": "QG-DEBT-0002",
            "kind": "warning",
            "scope": "global",
            "reason": "warning pendiente de resolver",
            "raised_by": "validators",
            "rule_id": "V-MISC-002",
            "created_at": "2026-09-15T00:00:00+00:00",
            "expires_at": "2026-10-15",
            "accepted_by": None,   # NO aceptada
        },
    ])

    note = """---
title: "debt-note"
note-type: concept
status: published
summary: "x"
reading-time-minutes: 1
---

# debt-note

## TL;DR
x
"""
    write_text(FIX / "with-debt/notemark/debt-note.nm", note)


def main() -> None:
    build_clean()
    build_with_errors()
    build_with_incomplete_coverage()
    build_with_debt()
    print(f"fixtures written under {FIX}")


if __name__ == "__main__":
    main()