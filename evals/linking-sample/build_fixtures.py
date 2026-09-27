#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del linking (F61)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir_3_cross_links() -> list:
    """3 IRs con links cruzados (A→B, B→C, C→A)."""
    return [
        {
            "schema_version": "1.0.0",
            "note_id": "lk0000000001",
            "title": "Nota A",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "A"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "lk0000000002", "text": "B"}}
                 ]}
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "lk0000000002",
            "title": "Nota B",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "B"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "lk0000000003", "text": "C"}}
                 ]}
            ]
        },
        {
            "schema_version": "1.0.0",
            "note_id": "lk0000000003",
            "title": "Nota C",
            "children": [
                {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
                 "source_refs": [], "children": [{"node": "text", "attrs": {"text": "C"}}]},
                {"node": "paragraph", "attrs": {}, "capability": "paragraph",
                 "source_refs": [],
                 "children": [
                     {"node": "text", "attrs": {"text": "Enlace a "}},
                     {"node": "link-note", "attrs": {"target": "lk0000000001", "text": "A"}}
                 ]}
            ]
        }
    ]


def make_ir_unresolved_link() -> dict:
    """1 IR con link-note a un note_id inexistente."""
    return {
        "schema_version": "1.0.0",
        "note_id": "lk0000000099",
        "title": "Link a nota inexistente",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "X"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Enlace a "}},
                 {"node": "link-note", "attrs": {"target": "lk-not-existe", "text": "fantasma"}}
             ]}
        ]
    }


def make_ir_no_links() -> dict:
    """IR sin link-note."""
    return {
        "schema_version": "1.0.0",
        "note_id": "lk0000000000",
        "title": "Sin links",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Solo"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Texto sin links."}}]}
        ]
    }


def make_ir_term_ref() -> dict:
    """IR con term-ref (glosario)."""
    return {
        "schema_version": "1.0.0",
        "note_id": "lk0000000010",
        "title": "Con term-ref",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Gl"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Término "}},
                 {"node": "term-ref", "attrs": {"term_id": "LGTM", "text": "LGTM"}},
                 {"node": "text", "attrs": {"text": " se define así."}}
             ]}
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

    # IRs simples.
    (out / "ir-no-links.json").write_text(
        json.dumps(make_ir_no_links(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out / "ir-unresolved-link.json").write_text(
        json.dumps(make_ir_unresolved_link(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out / "ir-term-ref.json").write_text(
        json.dumps(make_ir_term_ref(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    # IRs cross-link (multi-archivo).
    cross = make_ir_3_cross_links()
    for i, ir in enumerate(cross, start=1):
        (out / f"ir-cross-{i}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    (out / "profile-linking.yaml").write_text(make_profile(), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
