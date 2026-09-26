#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del renderer Markdown (F58)."""

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
        "note_id": "ee0000000001",
        "title": "Nota simple Markdown",
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
    severities = ["note", "tip", "info", "warning", "danger", "success", "question", "bug"]
    children = [
        {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
         "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Admonitions"}}]}
    ]
    for sev in severities:
        children.append({
            "node": "admonition",
            "attrs": {"severity": sev, "title": f"Test {sev}",
                      "semantic_token": sev if sev in ("warning", "danger", "info",
                                                          "success", "tip") else None},
            "capability": "callout",
            "source_refs": [],
            "children": [{"node": "text", "attrs": {"text": f"Cuerpo de {sev}."}}]
        })
    return {
        "schema_version": "1.0.0",
        "note_id": "ee0000000002",
        "title": "Cobertura admonitions",
        "children": children
    }


def make_ir_with_merged_table() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ee0000000003",
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


def make_ir_with_backlinks() -> list:
    """3 IRs con links cruzados para test de backlinks (criterio 3)."""
    return [
        {
            "schema_version": "1.0.0",
            "note_id": "ee0000000011",
            "title": "Nota A (backlinks)",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "A"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "ee0000000012",
                                                     "text": "Nota B"}}
                 ]}
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "ee0000000012",
            "title": "Nota B (backlinks)",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "B"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "ee0000000013",
                                                     "text": "Nota C"}}
                 ]}
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "ee0000000013",
            "title": "Nota C (backlinks)",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "C"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "ee0000000011",
                                                     "text": "Nota A"}}
                 ]}
            ]
        }
    ]


def make_ir_with_properties() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ee0000000004",
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


def make_ir_with_query() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ee0000000005",
        "title": "Nota con query",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Query"}}]},
            {"node": "table",
             "attrs": {"headers": [], "query": "TABLE field FROM notes WHERE status='open'"},
             "capability": "query",
             "source_refs": [], "children": []}
        ]
    }


def make_ir_with_diagram() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ee0000000006",
        "title": "Nota con diagrama",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Diagrama"}}]},
            {"node": "diagram",
             "attrs": {"kind": "mermaid",
                       "text": "graph TD\n  A-->B",
                       "alt": "Diagrama A->B"},
             "capability": "diagram-mermaid-block",
             "source_refs": [], "children": []}
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - markdown
          markdown:
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
        ("ir-with-query.json", make_ir_with_query),
        ("ir-with-diagram.json", make_ir_with_diagram),
    ]:
        (out / name).write_text(
            json.dumps(fn(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    # Multi-note para backlinks.
    for i, ir in enumerate(make_ir_with_backlinks(), start=1):
        (out / f"ir-backlinks-{i}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "profile-markdown.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
