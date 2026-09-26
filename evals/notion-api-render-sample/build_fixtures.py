#!/usr/bin/env python3
"""build_fixtures.py — genera fixtures para el eval battery del renderer Notion API (F55).

Stdlib puro, sin dependencias externas.

Uso:
    python3 evals/notion-api-render-sample/build_fixtures.py [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir_single_note() -> dict:
    """IR simple que ejercita 8 capacidades."""
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000001",
        "title": "Nota simple para Notion",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Título"}}]
            },
            {
                "node": "paragraph", "attrs": {}, "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Párrafo introductorio."}},
                ]
            },
            {
                "node": "admonition",
                "attrs": {"severity": "warning", "title": "Atención"},
                "capability": "callout",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Cuidado."}}]
            },
            {
                "node": "code",
                "attrs": {"lang": "python", "text": "print('hi')"},
                "capability": "code-block-fenced",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_ir_500_blocks() -> dict:
    """IR con > 500 bloques (paragraphs) para test de troceo."""
    children: list = []
    for i in range(510):
        children.append({
            "node": "paragraph", "attrs": {}, "capability": "paragraph",
            "source_refs": [],
            "children": [
                {"node": "text", "attrs": {"text": f"Párrafo {i}."}}
            ]
        })
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000500",
        "title": "Nota de 500 bloques",
        "children": children
    }


def make_ir_merged_table() -> dict:
    """IR con table de celdas combinadas (fila 2 contract §6)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000002",
        "title": "Tabla con celdas combinadas",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Tabla"}}]
            },
            {
                "node": "table",
                "attrs": {
                    "headers": ["A", "B", "C"],
                    "cells": [["X", "", ""], ["", "Y", "Z"]],
                    "matrix": [
                        [{"value": "X", "span": ""}, {"value": "", "span": "colspan=2"}],
                        [{"value": "Y", "span": ""}, {"value": "Z", "span": ""}]
                    ]
                },
                "capability": "table-merged-cells",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_ir_callouts() -> dict:
    """IR con admonitions de las 13 severidades canónicas."""
    severities = ["note", "tip", "info", "warning", "caution", "danger",
                  "example", "question", "success", "failure", "bug",
                  "quote", "abstract"]
    children = [
        {
            "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
            "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Callouts"}}]
        }
    ]
    for sev in severities:
        children.append({
            "node": "admonition",
            "attrs": {"severity": sev, "title": f"Test {sev}"},
            "capability": "callout",
            "source_refs": [],
            "children": [{"node": "text", "attrs": {"text": f"Cuerpo de {sev}."}}]
        })
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000003",
        "title": "Cobertura de callouts",
        "children": children
    }


def make_ir_properties() -> dict:
    """IR con property-blocks para test de PROPERTIES."""
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000004",
        "title": "Nota con propiedades",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Props"}}]
            },
            {
                "node": "property-block",
                "attrs": {"name": "author", "value": "alice", "type": "string"},
                "capability": "property-table",
                "source_refs": [],
                "children": []
            },
            {
                "node": "property-block",
                "attrs": {"name": "priority", "value": 3, "type": "number"},
                "capability": "property-table",
                "source_refs": [],
                "children": []
            },
            {
                "node": "property-block",
                "attrs": {"name": "is_published", "value": True, "type": "bool"},
                "capability": "property-table",
                "source_refs": [],
                "children": []
            },
            {
                "node": "property-block",
                "attrs": {"name": "url_field", "value": "https://example.com", "type": "url"},
                "capability": "property-table",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_ir_with_image() -> dict:
    """IR con figure (external URL)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "bb0000000005",
        "title": "Nota con imagen",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Img"}}]
            },
            {
                "node": "figure",
                "attrs": {"src": "https://example.com/diagram.png", "alt": "Diagrama",
                          "caption": "Figura 1"},
                "capability": "figure",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_profile_notion() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - notion_api
          notion_api:
            enabled: true
            database_id: "00000000-0000-0000-0000-000000000abc"
        """)


def make_profile_notion_legacy() -> str:
    """Perfil con nombre legacy `notion` (F11) — test del mapeo D1."""
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - notion
          notion:
            enabled: true
            database_id: "00000000-0000-0000-0000-000000000abc"
        """)


def make_profile_minimal() -> str:
    """Perfil sin database_id — test del path con page_parent_id."""
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - notion_api
          notion_api:
            enabled: true
        """)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    (out / "ir-single-note.json").write_text(
        json.dumps(make_ir_single_note(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-500-blocks.json").write_text(
        json.dumps(make_ir_500_blocks(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-merged-table.json").write_text(
        json.dumps(make_ir_merged_table(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-callouts.json").write_text(
        json.dumps(make_ir_callouts(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-properties.json").write_text(
        json.dumps(make_ir_properties(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-with-image.json").write_text(
        json.dumps(make_ir_with_image(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "profile-notion.yaml").write_text(make_profile_notion(), encoding="utf-8")
    (out / "profile-notion-legacy.yaml").write_text(make_profile_notion_legacy(),
                                                    encoding="utf-8")
    (out / "profile-minimal.yaml").write_text(make_profile_minimal(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
