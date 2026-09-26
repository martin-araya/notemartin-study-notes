#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del renderer Notion import (F56)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir_single_note() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "cc0000000001",
        "title": "Nota simple para Notion import",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Título"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Párrafo."}}]},
            {"node": "code",
             "attrs": {"lang": "python", "text": "print('hi')"},
             "capability": "code-block-fenced",
             "source_refs": [], "children": []},
        ]
    }


def make_ir_with_admonitions() -> dict:
    severities = ["note", "tip", "info", "warning", "caution", "danger",
                  "example", "success", "bug"]
    children = [
        {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
         "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Admonitions"}}]}
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
        "note_id": "cc0000000002",
        "title": "Cobertura de admonitions",
        "children": children
    }


def make_ir_with_merged_table() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "cc0000000003",
        "title": "Tabla con celdas combinadas",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Tabla"}}]},
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


def make_ir_with_properties() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "cc0000000004",
        "title": "Nota con propiedades",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Props"}}]},
            {"node": "property-block",
             "attrs": {"name": "author", "value": "alice", "type": "string"},
             "capability": "property-table", "source_refs": [], "children": []},
            {"node": "property-block",
             "attrs": {"name": "priority", "value": 3, "type": "number"},
             "capability": "property-table", "source_refs": [], "children": []},
            {"node": "property-block",
             "attrs": {"name": "is_published", "value": True, "type": "bool"},
             "capability": "property-table", "source_refs": [], "children": []},
        ]
    }


def make_ir_with_collapsible() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "cc0000000005",
        "title": "Nota con collapsible",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Col"}}]},
            {
                "node": "collapsible",
                "attrs": {"title": "Detalles", "default_open": False},
                "capability": "collapsible",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Contenido oculto."}}]
            }
        ]
    }


def make_ir_with_links() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "cc0000000006",
        "title": "Nota con links",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Links"}}]},
            {
                "node": "paragraph", "attrs": {}, "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Enlace a "}},
                    {"node": "link-note", "attrs": {"target": "cc9999999999",
                                                    "text": "existente"}}
                ]
            },
            {
                "node": "paragraph", "attrs": {}, "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Otro a "}},
                    {"node": "link-note", "attrs": {"target": "cc0000000001",
                                                    "text": "single"}}
                ]
            }
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - notion_md
          notion_md:
            enabled: true
        """)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    for name, fn in [
        ("ir-single-note.json", make_ir_single_note),
        ("ir-with-admonitions.json", make_ir_with_admonitions),
        ("ir-with-merged-table.json", make_ir_with_merged_table),
        ("ir-with-properties.json", make_ir_with_properties),
        ("ir-with-collapsible.json", make_ir_with_collapsible),
        ("ir-with-links.json", make_ir_with_links),
    ]:
        (out / name).write_text(
            json.dumps(fn(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "profile-notion-md.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
