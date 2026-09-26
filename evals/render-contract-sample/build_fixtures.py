#!/usr/bin/env python3
"""build_fixtures.py — genera fixtures para el eval battery del contrato de renderer (F53).

Stdlib puro, sin dependencias externas. Reproducible: misma seed → mismos fixtures.

Uso:
    python3 evals/render-contract-sample/build_fixtures.py [--out-dir DIR]

Genera:
    fixtures/ir-with-degradations.json
    fixtures/ir-clean.json
    fixtures/profile-obsidian.yaml
    fixtures/profile-markdown.yaml
    fixtures/profile-flashcards.yaml
    fixtures/matrix.json
    fixtures/report-sample.json  (si no existe, no sobrescribe)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_ir_with_degradations() -> dict:
    """IR con 10 nodos que ejercitan las capacidades del contrato.

    Capacidades representadas: section, paragraph, table (con rowspan), admonition,
    table (consulta), admonition (con color semántico).
    """
    return {
        "schema_version": "1.0.0",
        "note_id": "note-001",
        "title": "Tabla con celdas combinadas y admonitions",
        "children": [
            {
                "node": "section",
                "attrs": {"level": 1},
                "capability": "section-h1",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Capítulo X"}}
                ]
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [{"block_id": "a1b2c3d4e5f6", "source_hash": "f" * 64}],
                "children": [
                    {"node": "text", "attrs": {"text": "Texto introductorio con dato fáctico."}}
                ]
            },
            {
                "node": "table",
                "attrs": {
                    "headers": ["Col A", "Col B", "Col C"],
                    "rowspan": [[0, 0, 2]],
                    "colspan": [[0, 1, 3]]
                },
                "capability": "table-merged-cells",
                "source_refs": [{"block_id": "b2c3d4e5f6a7", "source_hash": "f" * 64}],
                "children": []
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Más prosa."}}
                ]
            },
            {
                "node": "section",
                "attrs": {"level": 2},
                "capability": "section-h2",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Sección H2"}}
                ]
            },
            {
                "node": "admonition",
                "attrs": {"severity": "warning", "title": "Atención"},
                "capability": "callout",
                "source_refs": [{"block_id": "c3d4e5f6a7b8", "source_hash": "f" * 64}],
                "children": [
                    {"node": "text", "attrs": {"text": "Este es el contenido del callout."}}
                ]
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Texto intermedio."}}
                ]
            },
            {
                "node": "table",
                "attrs": {
                    "headers": ["Query", "Resultado"],
                    "query": "SELECT * FROM notes WHERE status='open'"
                },
                "capability": "query",
                "source_refs": [{"block_id": "d4e5f6a7b8c9", "source_hash": "f" * 64}],
                "children": []
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [],
                "children": [
                    {"node": "text", "attrs": {"text": "Más texto."}}
                ]
            },
            {
                "node": "admonition",
                "attrs": {"severity": "danger", "title": "Error crítico"},
                "capability": "semantic-color",
                "source_refs": [{"block_id": "e5f6a7b8c9d0", "source_hash": "f" * 64}],
                "children": [
                    {"node": "text", "attrs": {"text": "Color rojo semántico."}}
                ]
            }
        ]
    }


def build_ir_clean() -> dict:
    """IR sin capacidades afectadas por celdas ❌ de F8."""
    return {
        "schema_version": "1.0.0",
        "note_id": "note-002",
        "title": "Nota simple sin degradaciones",
        "children": [
            {
                "node": "section",
                "attrs": {"level": 1},
                "capability": "section-h1",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Título"}}]
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [{"block_id": "fa1b2c3d4e5f", "source_hash": "f" * 64}],
                "children": [{"node": "text", "attrs": {"text": "Texto simple."}}]
            },
            {
                "node": "section",
                "attrs": {"level": 2},
                "capability": "section-h2",
                "source_refs": [],
                "children": [{"node": "text", "attrs": {"text": "Subtítulo"}}]
            },
            {
                "node": "code",
                "attrs": {"lang": "python", "text": "print('hello')"},
                "capability": "code-block-fenced",
                "source_refs": [{"block_id": "fb2c3d4e5f6a", "source_hash": "f" * 64}],
                "children": []
            },
            {
                "node": "paragraph",
                "attrs": {},
                "capability": "paragraph",
                "source_refs": [{"block_id": "fc3d4e5f6a7b", "source_hash": "f" * 64}],
                "children": [{"node": "text", "attrs": {"text": "Cierre."}}]
            }
        ]
    }


def build_profile_obsidian() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - obsidian
          obsidian:
            enabled: true
            vault_path: /tmp/vault
            folder_schema: "{section_path}/{note_id}"
        """)


def build_profile_markdown() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - markdown
          markdown:
            enabled: true
            output_dir: ./render/markdown
            include_backlinks: true
        """)


def build_profile_flashcards() -> str:
    return textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - flashcards
          flashcards:
            enabled: true
            output_dir: ./render/flashcards
            format: anki-csv
        """)


def build_matrix() -> dict:
    """Espejo estructurado de capability-matrix.md §2.1 — solo celdas, sin prose."""
    return {
        "schema_version": "1.0.0",
        "capabilities": {
            "table-merged-cells": {
                "obsidian": "❌",
                "notion_api": "❌",
                "notion_md": "❌",
                "appflowy": "❌",
                "markdown": "❌",
                "html_pdf": "✅",
                "flashcards": "❌"
            },
            "callout": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "❌",
                "appflowy": "✅",
                "markdown": "❌",
                "html_pdf": "✅",
                "flashcards": "❌"
            },
            "collapsible": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "✅",
                "appflowy": "✅",
                "markdown": "✅",
                "html_pdf": "✅",
                "flashcards": "❌"
            },
            "link-note": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "✅",
                "appflowy": "✅",
                "markdown": "✅",
                "html_pdf": "✅",
                "flashcards": "❌"
            },
            "backlink": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "✅",
                "appflowy": "✅",
                "markdown": "❌",
                "html_pdf": "❌",
                "flashcards": "❌"
            },
            "property-block": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "❌",
                "appflowy": "✅",
                "markdown": "✅",
                "html_pdf": "✅",
                "flashcards": "✅"
            },
            "query": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "✅",
                "appflowy": "✅",
                "markdown": "❌",
                "html_pdf": "❌",
                "flashcards": "❌"
            },
            "semantic-color": {
                "obsidian": "✅",
                "notion_api": "✅",
                "notion_md": "❌",
                "appflowy": "✅",
                "markdown": "❌",
                "html_pdf": "✅",
                "flashcards": "✅"
            }
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    (out / "ir-with-degradations.json").write_text(
        json.dumps(build_ir_with_degradations(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "ir-clean.json").write_text(
        json.dumps(build_ir_clean(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    (out / "profile-obsidian.yaml").write_text(build_profile_obsidian(), encoding="utf-8")
    (out / "profile-markdown.yaml").write_text(build_profile_markdown(), encoding="utf-8")
    (out / "profile-flashcards.yaml").write_text(build_profile_flashcards(), encoding="utf-8")
    (out / "matrix.json").write_text(
        json.dumps(build_matrix(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
