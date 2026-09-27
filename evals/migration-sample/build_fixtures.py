#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery de migration (F64)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir(note_id: str, title: str, paragraphs: list,
             extra_nodes: list = None) -> dict:
    children = [
        {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
         "source_refs": [],
         "children": [{"node": "text", "attrs": {"text": title}}]}
    ]
    for p in paragraphs:
        children.append({
            "node": "paragraph", "attrs": {}, "capability": "paragraph",
            "source_refs": [],
            "children": [{"node": "text", "attrs": {"text": p}}]
        })
    if extra_nodes:
        children.extend(extra_nodes)
    return {
        "schema_version": "1.0.0",
        "note_id": note_id,
        "title": title,
        "children": children
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    ir_dir = out / "ir"
    ir_dir.mkdir(exist_ok=True)

    # 3 IRs simples para re-render.
    irs = [
        make_ir("mg0000000001", "First Migration Note",
                ["First paragraph.", "Second paragraph."]),
        make_ir("mg0000000002", "Second Migration Note",
                ["Another paragraph here."]),
        make_ir("mg0000000003", "Third Migration Note",
                ["Yet another paragraph.", "More text."]),
    ]
    for ir in irs:
        (ir_dir / f"{ir['note_id']}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

    # Profile mínimo para los renderers.
    (out / "profile.yaml").write_text(textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - obsidian
          obsidian:
            enabled: true
        """), encoding="utf-8")

    # Artifact markdown para reverse-import (estructura con secciones, listas,
    # admonitions, código, wikilinks).
    lost_note = out / "reverse-input" / "lost-note.md"
    lost_note.parent.mkdir(exist_ok=True)
    lost_note.write_text(textwrap.dedent("""\
        # Lost Note Title

        Introduction paragraph.

        ## Section Two

        - First item
        - Second item

        > [!warning] Be careful

        More content here.

        ```python
        print("hello")
        ```

        See [[target-link|alias]] for more.

        ## Final Section

        Last paragraph.
        """), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
