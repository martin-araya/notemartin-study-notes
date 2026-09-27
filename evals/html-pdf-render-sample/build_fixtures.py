#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del renderer HTML/PDF (F59)."""

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
        "note_id": "ff0000000001",
        "title": "Nota simple HTML",
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


def make_ir_with_quotes() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ff0000000002",
        "title": "Cita que sobrevive",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Cita"}}]},
            {"node": "quote",
             "attrs": {"cite": "Platón, La República"},
             "capability": "quote",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "La justicia es la suma de las virtudes."}}]},
            {"node": "quote",
             "attrs": {"cite": "Aristóteles, Ética a Nicómaco"},
             "capability": "quote",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Somos lo que hacemos repetidamente."}}]},
        ]
    }


def make_ir_with_table_merged() -> dict:
    """HTML/PDF es ✅ para celdas combinadas (sin degradación)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "ff0000000003",
        "title": "Tabla con rowspan/colspan",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Tabla"}}]},
            {"node": "table",
             "attrs": {
                 "headers": ["A", "B", "C"],
                 "rows": [
                     [{"value": "X", "rowspan": 2}, "Y", "Z"],
                     [None, "Y2", "Z2"]
                 ]
             },
             "capability": "table-merged-cells",
             "source_refs": [],
             "children": []}
        ]
    }


def make_ir_with_backlinks() -> list:
    return [
        {
            "schema_version": "1.0.0",
            "note_id": "ff0000000011",
            "title": "Nota A backlinks",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "A"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "ff0000000012", "text": "Nota B"}}
                 ]}
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "ff0000000012",
            "title": "Nota B backlinks",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "B"}}]}
            ]
        }
    ]


def make_ir_with_query() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ff0000000004",
        "title": "Query",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Query"}}]},
            {"node": "table",
             "attrs": {"headers": [], "query": "TABLE field FROM notes"},
             "capability": "query",
             "source_refs": [], "children": []}
        ]
    }


def make_ir_with_diagram() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "ff0000000005",
        "title": "Diagrama",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "D"}}]},
            {"node": "diagram",
             "attrs": {"kind": "mermaid", "text": "graph TD\n  A-->B",
                       "alt": "Diagrama"},
             "capability": "diagram-mermaid-block",
             "source_refs": [], "children": []}
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - html_pdf
          html_pdf:
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
        ("ir-with-quotes.json", make_ir_with_quotes),
        ("ir-with-table-merged.json", make_ir_with_table_merged),
        ("ir-with-query.json", make_ir_with_query),
        ("ir-with-diagram.json", make_ir_with_diagram),
    ]:
        (out / name).write_text(
            json.dumps(fn(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    for i, ir in enumerate(make_ir_with_backlinks(), start=1):
        (out / f"ir-backlinks-{i}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "profile-html-pdf.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
