#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del renderer AppFlowy (F57)."""

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
        "note_id": "dd0000000001",
        "title": "Nota simple AppFlowy",
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


def make_ir_with_callouts() -> dict:
    severities = ["note", "info", "warning", "danger", "success", "question"]
    children = [
        {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
         "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Callouts"}}]}
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
        "note_id": "dd0000000002",
        "title": "Cobertura callouts AppFlowy",
        "children": children
    }


def make_ir_with_merged_table() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "dd0000000003",
        "title": "Tabla merged",
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


def make_ir_with_diagram() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "dd0000000004",
        "title": "Nota con diagrama",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Diagrama"}}]},
            {"node": "diagram",
             "attrs": {"kind": "mermaid",
                       "text": "graph TD\n  A-->B\n  B-->C",
                       "alt": "Flujo A->B->C"},
             "capability": "diagram-mermaid-block",
             "source_refs": [],
             "children": []}
        ]
    }


def make_ir_with_properties() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "dd0000000005",
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
        ]
    }


def make_ir_with_collapsible() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "dd0000000006",
        "title": "Collapsible",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Col"}}]},
            {"node": "collapsible",
             "attrs": {"title": "Detalles", "default_open": False},
             "capability": "collapsible",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Contenido."}}]}
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - appflowy
          appflowy:
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
        ("ir-with-callouts.json", make_ir_with_callouts),
        ("ir-with-merged-table.json", make_ir_with_merged_table),
        ("ir-with-diagram.json", make_ir_with_diagram),
        ("ir-with-properties.json", make_ir_with_properties),
        ("ir-with-collapsible.json", make_ir_with_collapsible),
    ]:
        (out / name).write_text(
            json.dumps(fn(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "profile-appflowy.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
