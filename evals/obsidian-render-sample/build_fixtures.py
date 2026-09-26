#!/usr/bin/env python3
"""build_fixtures.py — genera fixtures para el eval battery del renderer Obsidian (F54).

Stdlib puro, sin dependencias externas.

Uso:
    python3 evals/obsidian-render-sample/build_fixtures.py [--out-dir DIR]
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
    """IR con las 14 capacidades representadas."""
    return {
        "schema_version": "1.0.0",
        "note_id": "aabbccddee01",
        "title": "Nota con 14 capacidades",
        "children": [
            {
                "node": "section",
                "attrs": {"level": 1},
                "capability": "section-h1",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Título principal"}}]
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [{"block_id": "b1c2d3e4f5a6", "source_hash": "f" * 64}],
                "children": [
                    {"node": "text", "attrs": {"text": "Párrafo introductorio con "}},
                    {"node": "strong", "attrs": {}, "children": [
                        {"node": "text", "attrs": {"text": "negrita"}}
                    ]},
                    {"node": "text", "attrs": {"text": " y "}},
                    {"node": "em", "attrs": {}, "children": [
                        {"node": "text", "attrs": {"text": "cursiva"}}
                    ]},
                    {"node": "text", "attrs": {"text": "."}},
                    {"node": "source-ref", "attrs": {"block_id": "b1c2d3e4f5a6", "source_hash": "f" * 64}},
                ]
            },
            {
                "node": "code",
                "attrs": {"lang": "python", "text": "def hello():\n    return 'world'"},
                "capability": "code-block-fenced",
                "source_refs": [],
                "children": []
            },
            {
                "node": "admonition",
                "attrs": {"severity": "warning", "title": "Atención"},
                "capability": "callout",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Cuidado con esto."}}]
            },
            {
                "node": "collapsible",
                "attrs": {"title": "Detalles avanzados", "default_open": False},
                "capability": "collapsible",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Contenido oculto."}}]
            },
            {
                "node": "diagram",
                "attrs": {"kind": "mermaid", "text": "graph TD\n  A-->B"},
                "capability": "diagram-mermaid-block",
                "source_refs": [],
                "children": []
            },
            {
                "node": "equation",
                "attrs": {"latex": "E = mc^2", "display": True},
                "capability": "equation-block",
                "source_refs": [],
                "children": []
            },
            {
                "node": "list",
                "attrs": {"ordered": False},
                "capability": "list",
                "source_refs": [],
                "children": [
                    {"node": "list-item", "attrs": {}, "children": [
                        {"node": "text", "attrs": {"text": "Item 1"}}
                    ]},
                    {"node": "list-item", "attrs": {}, "children": [
                        {"node": "text", "attrs": {"text": "Item 2"}}
                    ]}
                ]
            },
            {
                "node": "checklist",
                "attrs": {},
                "capability": "checklist",
                "source_refs": [],
                "children": [
                    {"node": "list-item", "attrs": {"done": False}, "children": [
                        {"node": "text", "attrs": {"text": "Pendiente"}}
                    ]},
                    {"node": "list-item", "attrs": {"done": True}, "children": [
                        {"node": "text", "attrs": {"text": "Hecho"}}
                    ]}
                ]
            },
            {
                "node": "table",
                "attrs": {"headers": ["Col A", "Col B"], "rows": [["1", "2"], ["3", "4"]]},
                "capability": "table",
                "source_refs": [],
                "children": []
            },
            {
                "node": "property-block",
                "attrs": {"name": "version", "value": "1.0.0"},
                "capability": "property-table",
                "source_refs": [],
                "children": []
            },
            {
                "node": "figure",
                "attrs": {"src": "assets/diagram.png", "alt": "Diagrama", "caption": "Figura 1"},
                "capability": "figure",
                "source_refs": [],
                "children": []
            },
            {
                "node": "step",
                "attrs": {"index": 1},
                "capability": "step",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Primer paso."}}]
            },
            {
                "node": "divider",
                "attrs": {},
                "capability": "divider",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_ir_multi_note() -> list:
    """3 IRs con links cruzados (criterio 3)."""
    return [
        {
            "schema_version": "1.0.0",
            "note_id": "aa0000000001",
            "title": "Nota A",
            "children": [
                {
                    "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                    "source_refs": [], "children": [{"node": "text", "attrs": {"text": "A"}}]
                },
                {
                    "node": "paragraph", "attrs": {}, "capability": "paragraph",
                    "source_refs": [],
                    "children": [
                        {"node": "text", "attrs": {"text": "Enlace a "}},
                        {"node": "link-note", "attrs": {"target": "aa0000000002", "text": "Nota B"}}
                    ]
                }
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "aa0000000002",
            "title": "Nota B",
            "children": [
                {
                    "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                    "source_refs": [], "children": [{"node": "text", "attrs": {"text": "B"}}]
                },
                {
                    "node": "paragraph", "attrs": {}, "capability": "paragraph",
                    "source_refs": [],
                    "children": [
                        {"node": "text", "attrs": {"text": "Enlace a "}},
                        {"node": "link-note", "attrs": {"target": "aa0000000003", "text": "Nota C"}},
                        {"node": "text", "attrs": {"text": " y a "}},
                        {"node": "link-note", "attrs": {"target": "aa0000000001", "text": "Nota A"}}
                    ]
                }
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "aa0000000003",
            "title": "Nota C",
            "children": [
                {
                    "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                    "source_refs": [], "children": [{"node": "text", "attrs": {"text": "C"}}]
                }
            ]
        }
    ]


def make_ir_merged_table() -> dict:
    """IR con table que tiene rowspan/colspan (degradación fila 1 §6)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "aabbccddee02",
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
                "source_refs": [{"block_id": "c1c2c3c4c5c6", "source_hash": "f" * 64}],
                "children": []
            }
        ]
    }


def make_ir_dataview() -> dict:
    """IR con table.query (degradación Dataview)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "aabbccddee03",
        "title": "Nota con Dataview",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "DV"}}]
            },
            {
                "node": "table",
                "attrs": {
                    "headers": [],
                    "query": "TABLE field FROM #note WHERE status='open'"
                },
                "capability": "query",
                "source_refs": [],
                "children": []
            }
        ]
    }


def make_ir_unknown_severity() -> dict:
    """IR con severidad no mapeada en SEVERITY_TO_CALLOUT."""
    return {
        "schema_version": "1.0.0",
        "note_id": "aabbccddee04",
        "title": "Severidad desconocida",
        "children": [
            {
                "node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Sev"}}]
            },
            {
                "node": "admonition",
                "attrs": {"severity": "fictional-severity", "title": "Test"},
                "capability": "callout",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Body"}}]
            }
        ]
    }


def make_profile() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - obsidian
          obsidian:
            enabled: true
            vault: ~/Documents/vault
            folder: notes/
        """)


def make_profile_dataview() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - obsidian
          obsidian:
            enabled: true
            vault: ~/Documents/vault
            folder: notes/
        rendering:
          dataview: true
        """)


def make_profile_simple_folder() -> str:
    """Perfil sin folder explícito (test del default)."""
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - obsidian
          obsidian:
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
    for i, ir in enumerate(make_ir_multi_note(), start=1):
        (out / f"ir-multi-{i}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    (out / "ir-merged-table.json").write_text(
        json.dumps(make_ir_merged_table(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-dataview.json").write_text(
        json.dumps(make_ir_dataview(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-unknown-severity.json").write_text(
        json.dumps(make_ir_unknown_severity(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "profile-obsidian.yaml").write_text(make_profile(), encoding="utf-8")
    (out / "profile-dataview-enabled.yaml").write_text(make_profile_dataview(), encoding="utf-8")
    (out / "profile-simple.yaml").write_text(make_profile_simple_folder(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
