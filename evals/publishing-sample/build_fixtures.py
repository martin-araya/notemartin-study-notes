#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery del publishing (F62)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "fixtures"


def make_ir(note_id: str, title: str = "Title") -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": note_id,
        "title": title,
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": title}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [], "children": [{"node": "text", "attrs": {"text": "Body."}}]}
        ]
    }


def write_rendered(workdir: pathlib.Path, dest: str, note_id: str,
                     subdir: str, ext: str, content: str) -> None:
    target_dir = workdir / "render" / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / f"{note_id}{ext}").write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # 20 IRs para C1.
    (out / "ir-20-notes").mkdir(exist_ok=True)
    for i in range(20):
        ir = make_ir(f"pb000000{i:04d}", f"Note {i:02d}")
        (out / "ir-20-notes" / f"pb000000{i:04d}.json").write_text(
            json.dumps(ir, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # 1 IR para C3 (publicación parcial).
    (out / "ir-1-note-changed").mkdir(exist_ok=True)
    (out / "ir-1-note-changed" / "pc0000000001.json").write_text(
        json.dumps(make_ir("pc0000000001", "Changed"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 1 IR para C2 (edited by hand).
    (out / "ir-1-note-edited-by-hand").mkdir(exist_ok=True)
    (out / "ir-1-note-edited-by-hand" / "pe0000000001.json").write_text(
        json.dumps(make_ir("pe0000000001", "EditedByHand"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Profile.
    (out / "profile-publishing.yaml").write_text(textwrap.dedent("""\
        schema_version: "1.0.0"
        targets:
          active:
            - markdown
          markdown:
            enabled: true
        """), encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
