#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del renderer Flashcards (F60)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir_single_question() -> dict:
    """1 question node → 1 card."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000001",
        "title": "Una pregunta simple",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Pregunta"}}]},
            {"node": "question",
             "attrs": {"prompt": "¿Cuál es la capital de Francia?"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "París"}}]}
        ]
    }


def make_ir_multi_questions() -> dict:
    """3 question nodes → 3 cards."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000002",
        "title": "Tres preguntas",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Quiz"}}]},
            {"node": "question",
             "attrs": {"prompt": "¿2+2?"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "4"}}]},
            {"node": "question",
             "attrs": {"prompt": "¿Capital de España?"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Madrid"}}]},
            {"node": "question",
             "attrs": {"prompt": "¿Quién escribió Don Quijote?"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Cervantes"}}]}
        ]
    }


def make_ir_atomic_definitions() -> dict:
    """3 nodos definition con is_atomic_card=true → 3 cards."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000003",
        "title": "Glosario atómico",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Glosario"}}]},
            {"node": "definition",
             "attrs": {"term": "Función", "is_atomic_card": True},
             "capability": "definition",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Relación entre conjuntos."}}]},
            {"node": "definition",
             "attrs": {"term": "Algoritmo", "is_atomic_card": True},
             "capability": "definition",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Secuencia finita de pasos."}}]},
            {"node": "formula",
             "attrs": {"name": "E=mc²", "latex": "E = mc^2", "is_atomic_card": True},
             "capability": "formula",
             "source_refs": [],
             "children": []}
        ]
    }


def make_ir_prose_only() -> dict:
    """Solo paragraph + section → 0 cards, 2+ descartados por prosa."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000004",
        "title": "Solo prosa narrativa",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Sec"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Esta es una prosa narrativa larga que no debería generar tarjetas de repaso porque contiene múltiples hechos mezclados en una sola descripción."}}
             ]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Otro párrafo narrativo extenso con varios hechos entrelazados."}}
             ]}
        ]
    }


def make_ir_compound_facts() -> dict:
    """Question con prompt de 3 cláusulas → discarded por compound-fact."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000005",
        "title": "Hecho compuesto",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Comp"}}]},
            {"node": "question",
             "attrs": {"prompt": "Uno, dos, tres, cuatro"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "x"}}]}
        ]
    }


def make_ir_merged_table() -> dict:
    """Tabla con celdas combinadas → linearización (fila 6 contract §6)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000006",
        "title": "Tabla con celdas combinadas",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Tabla"}}]},
            {"node": "table",
             "attrs": {
                 "headers": ["A", "B", "C"],
                 "cells": [["X", "", ""], ["X", "Y", "Z"]]
             },
             "capability": "table-merged-cells",
             "source_refs": [],
             "children": []}
        ]
    }


def make_ir_mixed() -> dict:
    """Mezcla de question, atomic, prose."""
    return {
        "schema_version": "1.0.0",
        "note_id": "fa0000000007",
        "title": "Mezcla",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Mix"}}]},
            {"node": "question",
             "attrs": {"prompt": "¿Verdadero o falso: el agua hierve a 100°C?"},
             "capability": "question",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Verdadero (a nivel del mar)"}}]},
            {"node": "definition",
             "attrs": {"term": "pKa", "is_atomic_card": True},
             "capability": "definition",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Medida de acidez."}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Prosa que debería descartarse por no ser atómica."}}
             ]}
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - flashcards
          flashcards:
            enabled: true
        """)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    for name, fn in [
        ("ir-single-question.json", make_ir_single_question),
        ("ir-multi-questions.json", make_ir_multi_questions),
        ("ir-atomic-definitions.json", make_ir_atomic_definitions),
        ("ir-prose-only.json", make_ir_prose_only),
        ("ir-compound-facts.json", make_ir_compound_facts),
        ("ir-merged-table.json", make_ir_merged_table),
        ("ir-mixed.json", make_ir_mixed),
    ]:
        (out / name).write_text(
            json.dumps(fn(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "profile-flashcards.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
