#!/usr/bin/env python3
"""build_fixtures.py — fixtures para el eval battery de cross_target (F63)."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


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


def write_md(out_path: pathlib.Path, note_id: str, title: str,
              paragraphs: list) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "---\n"
        f'note_id: "{note_id}"\n'
        "target: markdown\n"
        "---\n\n"
        f"# {title}\n\n"
    )
    for p in paragraphs:
        content += f"{p}\n\n"
    out_path.write_text(content, encoding="utf-8")


def write_obsidian(out_path: pathlib.Path, note_id: str, title: str,
                    paragraphs: list) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "---\n"
        f'note_id: "{note_id}"\n'
        "target: obsidian\n"
        "---\n\n"
        f"# {title}\n\n"
    )
    for p in paragraphs:
        content += f"{p}\n\n"
    out_path.write_text(content, encoding="utf-8")


def write_html(out_path: pathlib.Path, note_id: str, title: str,
                paragraphs: list) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = ""
    for p in paragraphs:
        body += f"<p>{p}</p>\n"
    content = (
        "<!DOCTYPE html>\n<html><head>"
        f"<title>{title}</title></head><body>\n"
        f"<h1>{title}</h1>\n"
        f"{body}"
        "</body></html>\n"
    )
    out_path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    ir_dir = out / "ir"
    ir_dir.mkdir(exist_ok=True)
    render_dir = out / "render"
    reports_dir = out / "reports"
    reports_dir.mkdir(exist_ok=True)

    # ============================================================
    # Caso 1: clean equivalence (C1) — todas las unidades aparecen en
    # los artifacts, sin degradaciones.
    # ============================================================
    clean_notes = [
        ("ct0000000001", "Clean Note One",
         ["First paragraph with text.", "Second paragraph here."]),
        ("ct0000000002", "Clean Note Two",
         ["Another paragraph.", "Yet another paragraph."]),
        ("ct0000000003", "Clean Note Three",
         ["Paragraph in third note."]),
    ]
    for note_id, title, paragraphs in clean_notes:
        (ir_dir / f"{note_id}.json").write_text(
            json.dumps(make_ir(note_id, title, paragraphs), indent=2,
                      ensure_ascii=False) + "\n", encoding="utf-8")
        write_md(render_dir / "markdown" / f"{note_id}.md",
                 note_id, title, paragraphs)
        write_obsidian(render_dir / "obsidian" / f"{note_id}.md",
                       note_id, title, paragraphs)
        write_html(render_dir / "html_pdf" / f"{note_id}.html",
                   note_id, title, paragraphs)

    # ============================================================
    # Caso 2: with-degradations — unidades marcadas en report con
    # content_intact: true; los artifacts no las contienen.
    # ============================================================
    degraded_ir = {
        "schema_version": "1.0.0",
        "note_id": "ct0000000010",
        "title": "Degraded Note",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Degraded Note"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "This paragraph has a special token XYZ123."}}
             ]},
            {"node": "admonition", "attrs": {"severity": "warning", "title": "Heads up"},
             "capability": "callout",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Be careful."}}]}
        ]
    }
    (ir_dir / "degraded.json").write_text(
        json.dumps(degraded_ir, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    # Artifacts sin el contenido exacto de la admonition pero con sufijo.
    for dest in ["obsidian", "markdown"]:
        if dest == "obsidian":
            content = (
                "---\n"
                "note_id: \"ct0000000010\"\n"
                "target: obsidian\n"
                "---\n\n"
                "# Degraded Note\n\n"
                # Paragraph also lost (artifact skip).
                "> [!warning] Heads up\n"
            )
        elif dest == "markdown":
            content = (
                "---\n"
                "note_id: \"ct0000000010\"\n"
                f"target: {dest}\n"
                "---\n\n"
                "# Degraded Note\n\n"
                "This paragraph has a special token XYZ123.\n\n"
                "> Heads up\n"
                "> Be careful.\n"
            )
        else:
            content = ""
        write_md(render_dir / dest / "ct0000000010.md",
                 "ct0000000010", "Degraded Note",
                 ["This paragraph has a special token XYZ123."])
        # Override with custom content.
        (render_dir / dest / "ct0000000010.md").write_text(content, encoding="utf-8")

    # Report con degradaciones para ct0000000010.
    (reports_dir / "render-degradation.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "target": "obsidian",
        "source_hash": "0" * 64,
        "totals": {"ir_nodes": 3, "degradations": 2, "content_loss": 0},
        "degradations": [
            {
                "id": "deg-ct-1",
                "node_path": "0/1",
                "node_type": "paragraph",
                "capability": "paragraph",
                "alternative": "Degradación justificada para párrafo",
                "evidence": "rg pattern exit 0",
                "content_intact": True
            },
            {
                "id": "deg-ct-2",
                "node_path": "0/2",
                "node_type": "admonition",
                "capability": "callout",
                "alternative": "Callout como blockquote con emoji",
                "evidence": "rg pattern exit 0",
                "content_intact": True
            }
        ]
    }, indent=2) + "\n", encoding="utf-8")

    # ============================================================
    # Caso 3: real-loss — un párrafo no aparece en el artifact y NO
    # está en el report de degradaciones.
    # ============================================================
    loss_ir = {
        "schema_version": "1.0.0",
        "note_id": "ct0000000020",
        "title": "Lossy Note",
        "children": [
            {"node": "section", "attrs": {"level": 1}, "capability": "section-h1",
             "source_refs": [],
             "children": [{"node": "text", "attrs": {"text": "Lossy Note"}}]},
            {"node": "paragraph", "attrs": {}, "capability": "paragraph",
             "source_refs": [],
             "children": [
                 {"node": "text", "attrs": {"text": "Real critical content that should appear."}}
             ]}
        ]
    }
    (ir_dir / "lossy.json").write_text(
        json.dumps(loss_ir, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")

    # Artifact sin el párrafo crítico.
    lossy_content = (
        "---\n"
        "note_id: \"ct0000000020\"\n"
        "target: obsidian\n"
        "---\n\n"
        "# Lossy Note\n\n"
        "Just a title.\n"
    )
    for dest in ["obsidian", "markdown"]:
        (render_dir / dest).mkdir(parents=True, exist_ok=True)
        (render_dir / dest / "ct0000000020.md").write_text(lossy_content,
                                                        encoding="utf-8")

    # Report SIN degradaciones (vacío).
    (reports_dir / "render-degradation.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "target": "obsidian",
        "source_hash": "0" * 64,
        "totals": {"ir_nodes": 2, "degradations": 0, "content_loss": 0},
        "degradations": []
    }, indent=2) + "\n", encoding="utf-8")

    print(f"Fixtures escritos en {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
