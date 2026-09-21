#!/usr/bin/env python3
"""Genera los 5 IRs sintéticos para Fase 14.

Uso:
    python3 evals/ir-sample/generate.py

Salida:
    evals/ir-sample/canonical.json             (todos los 33 nodos)
    evals/ir-sample/minimal-postgres.json
    evals/ir-sample/minimal-kubernetes.json
    evals/ir-sample/minimal-cpp.json
    evals/ir-sample/minimal-ocr.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "evals" / "ir-sample"
OUT.mkdir(parents=True, exist_ok=True)

PG_HASH = "a8f4ce1405802cacbb35e6fb88f5e3cf138a4e872910cdfd276f378f13371657"


def block_id(label: str) -> str:
    """Deterministic 12-hex id from a label string. Matches the SDM id regex."""
    return hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def n(node: str, attrs: dict, children=None, source_refs=None, **flags) -> dict:
    out = {
        "node": node,
        "attrs": attrs,
        "source_refs": source_refs or [],
    }
    if children is not None:
        out["children"] = children
    for k, v in flags.items():
        if v is not None:
            out[k] = v
    return out


def ref(label_or_id: str, source_hash: str = PG_HASH, section_path: str = "/ch02/intro") -> dict:
    """If the arg is 12 hex chars, pass through; else derive a deterministic id."""
    bid = label_or_id if (len(label_or_id) == 12 and all(c in "0123456789abcdef" for c in label_or_id)) else block_id(label_or_id)
    return {"block_id": bid, "source_hash": source_hash, "section_path": section_path}


def write(name: str, ir: dict) -> None:
    path = OUT / name
    path.write_text(json.dumps(ir, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(REPO)}")


def minimal_postgres() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "postgres-shared-buffers",
        "title": "PostgreSQL 16 — shared_buffers",
        "layer": "l2",
        "blocks": [
            n("section", {"level": 2, "capability": "section-h2"},
              source_refs=[ref("a8f4ce140580")],
              children=[
                  n("paragraph", {"capability": "paragraph"},
                    source_refs=[ref("a8f4ce140581")],
                    children=[
                        n("text", {"text": "PostgreSQL reserva ", "capability": "text"}, source_refs=[]),
                        n("term-ref", {"text": "shared_buffers", "term_id": "shared-buffers",
                                       "capability": "link-term"}, source_refs=[]),
                        n("text", {"text": " como buffer pool. El tamaño se controla con ", "capability": "text"}, source_refs=[]),
                        n("code-inline", {"text": "shared_buffers", "capability": "code-inline"}, source_refs=[]),
                        n("text", {"text": ".", "capability": "text"}, source_refs=[]),
                    ]),
                  n("parameter-table", {"columns": ["parametro", "tipo", "default", "rango"], "capability": "parameter-table"},
                    source_refs=[ref("a8f4ce140582")],
                    children=[
                        n("text", {"text": "max_connections | integer | 100 | 1-10000", "capability": "text"}, source_refs=[]),
                    ]),
                  n("admonition", {"severity": "warning", "capability": "callout"},
                    source_refs=[ref("a8f4ce140583")],
                    children=[
                        n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                            n("text", {"text": "Cambiar ", "capability": "text"}, source_refs=[]),
                            n("code-inline", {"text": "shared_buffers", "capability": "code-inline"}, source_refs=[]),
                            n("text", {"text": " requiere reinicio.", "capability": "text"}, source_refs=[]),
                        ]),
                    ]),
              ]),
        ],
    }


def minimal_kubernetes() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "kubernetes-pod-v1",
        "title": "Kubernetes — Pod v1 API Reference",
        "layer": "l2",
        "blocks": [
            n("section", {"level": 2, "capability": "section-h2"},
              source_refs=[ref("kube00001", source_hash="b" * 64, section_path="/workload/pod-v1")],
              children=[
                  n("paragraph", {"capability": "paragraph"},
                    source_refs=[ref("kube00002", source_hash="b" * 64, section_path="/workload/pod-v1")],
                    children=[
                        n("text", {"text": "Un ", "capability": "text"}, source_refs=[]),
                        n("term-ref", {"text": "Pod", "term_id": "pod", "capability": "link-term"}, source_refs=[]),
                        n("text", {"text": " es la unidad mínima desplegable.", "capability": "text"}, source_refs=[]),
                    ]),
                  n("list", {"ordered": False, "capability": "list"},
                    source_refs=[ref("kube00003", source_hash="b" * 64, section_path="/workload/pod-v1")],
                    children=[
                        n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                            n("code-inline", {"text": "spec.containers", "capability": "code-inline"}, source_refs=[]),
                        ]),
                        n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                            n("code-inline", {"text": "spec.restartPolicy", "capability": "code-inline"}, source_refs=[]),
                        ]),
                        n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                            n("code-inline", {"text": "spec.nodeSelector", "capability": "code-inline"}, source_refs=[]),
                        ]),
                    ]),
                  n("code", {"lang": "yaml", "text": "apiVersion: v1\nkind: Pod", "capability": "code-block-fenced"},
                    source_refs=[ref("kube00004", source_hash="b" * 64, section_path="/workload/pod-v1")]),
              ]),
        ],
    }


def minimal_cpp() -> dict:
    return {
        "schema_version": "1.0.0",
        "note_id": "iso-cpp-declaration",
        "title": "ISO C++ — Declaration Syntax",
        "layer": "l2",
        "blocks": [
            n("section", {"level": 2, "capability": "section-h2"},
              source_refs=[ref("cpp00001", source_hash="c" * 64, section_path="/syntax/declaration")],
              children=[
                  n("paragraph", {"capability": "paragraph"},
                    source_refs=[ref("cpp00002", source_hash="c" * 64, section_path="/syntax/declaration")],
                    children=[
                        n("text", {"text": "A ", "capability": "text"}, source_refs=[]),
                        n("strong", {"capability": "strong"}, source_refs=[],
                          children=[n("text", {"text": "declaration", "capability": "text"}, source_refs=[])]),
                        n("text", {"text": " introduces one or more names into a scope.", "capability": "text"}, source_refs=[]),
                    ]),
                  n("diagram", {"kind": "railroad", "text": "declaration := block-declaration | function-definition | template-declaration",
                                "alt": "EBNF declaration syntax", "capability": "diagram-railroad"},
                    source_refs=[ref("cpp00003", source_hash="c" * 64, section_path="/syntax/declaration")]),
                  n("code", {"lang": "cpp", "text": "int x = 42;", "capability": "code-block-fenced"},
                    source_refs=[ref("cpp00004", source_hash="c" * 64, section_path="/syntax/declaration")]),
              ]),
        ],
    }


def minimal_ocr() -> dict:
    """OCR-hostil: confidence < 1.0, external flags."""
    bad_hash = "d" * 64
    return {
        "schema_version": "1.0.0",
        "note_id": "internet-archive-scan",
        "title": "Scanned document (OCR recovered)",
        "layer": "l2",
        "blocks": [
            n("section", {"level": 2, "capability": "section-h2"},
              source_refs=[ref("ocr00001", source_hash=bad_hash, section_path="/page-3")],
              children=[
                  n("paragraph", {"capability": "paragraph"},
                    source_refs=[ref("ocr00002", source_hash=bad_hash, section_path="/page-3")],
                    external=True,
                    children=[
                        n("text", {"text": "[OCR result with rotation; partially garbled]", "capability": "text"}, source_refs=[]),
                    ]),
                  n("code", {"lang": "python", "text": "def hello(): print('hello, world')", "capability": "code-block-fenced"},
                    source_refs=[ref("ocr00003", source_hash=bad_hash, section_path="/page-3")]),
                  n("admonition", {"severity": "external", "title": "External reconstruction", "capability": "callout"},
                    source_refs=[],
                    external=True,
                    derived=True,
                    children=[
                        n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                            n("text", {"text": "Esta interpretación es nuestra, no del documento original.", "capability": "text"}, source_refs=[]),
                        ]),
                    ]),
              ]),
        ],
    }


def canonical() -> dict:
    """1 IR con todos los 33 nodos ejercitados."""
    h = PG_HASH
    return {
        "schema_version": "1.0.0",
        "note_id": "f014-canonical-sample",
        "title": "Note IR — canonical sample covering all 33 nodes",
        "layer": "l2",
        "blocks": [
            n("section", {"level": 1, "capability": "section-h1"},
              source_refs=[ref("canon01")],
              children=[
                  n("paragraph", {"capability": "paragraph"},
                    source_refs=[ref("canon02")],
                    children=[
                        n("text", {"text": "Plain text ", "capability": "text"}, source_refs=[]),
                        n("strong", {"capability": "strong"}, source_refs=[],
                          children=[n("text", {"text": "bold", "capability": "text"}, source_refs=[])]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("em", {"capability": "em"}, source_refs=[],
                          children=[n("text", {"text": "italic", "capability": "text"}, source_refs=[])]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("code-inline", {"text": "code", "capability": "code-inline"}, source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("link-external", {"text": "site", "url": "https://example.com", "capability": "link-external"},
                          source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("link-note", {"text": "see also", "target": "other-note-id", "capability": "link-note"},
                          source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("term-ref", {"text": "MVCC", "term_id": "mvcc", "capability": "link-term"},
                          source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("source-ref", {"block_id": block_id("canon03"), "source_hash": h, "capability": "source-ref"},
                          source_refs=[ref("canon03")]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("math-inline", {"latex": "x^2", "capability": "math-inline"}, source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("footnote-ref", {"ref_id": "1", "text": "see RFC", "capability": "footnote-ref"}, source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("keyboard", {"text": "Ctrl+S", "capability": "keyboard"}, source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("placeholder", {"text": "name", "default_value": "alice", "capability": "placeholder"},
                          source_refs=[]),
                        n("text", {"text": " ", "capability": "text"}, source_refs=[]),
                        n("deleted", {"capability": "deleted"}, source_refs=[],
                          children=[n("text", {"text": "removed", "capability": "text"}, source_refs=[])]),
                    ]),

                  n("section", {"level": 2, "capability": "section-h2"},
                    source_refs=[ref("canon10")],
                    children=[
                        n("list", {"ordered": False, "capability": "list"},
                          source_refs=[ref("canon11")],
                          children=[
                              n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                                  n("text", {"text": "item 1", "capability": "text"}, source_refs=[])]),
                              n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                                  n("text", {"text": "item 2", "capability": "text"}, source_refs=[])]),
                          ]),
                        n("checklist", {"capability": "checklist"},
                          source_refs=[ref("canon12")],
                          children=[
                              n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                                  n("text", {"text": "todo item", "capability": "text"}, source_refs=[])]),
                          ]),
                        n("table", {"headers": ["name", "type"], "caption": "Parameters", "capability": "table"},
                          source_refs=[ref("canon13")],
                          children=[
                              n("text", {"text": "foo | string", "capability": "text"}, source_refs=[]),
                              n("text", {"text": "bar | integer", "capability": "text"}, source_refs=[]),
                          ]),
                        n("definition-list", {"entries": [{"term": "MVCC", "definition": "Multiversion concurrency control"}],
                                              "capability": "definition-list"},
                          source_refs=[ref("canon14")]),
                        n("code", {"lang": "sql", "text": "SELECT 1;", "capability": "code-block-fenced"},
                          source_refs=[ref("canon15")]),
                        n("console", {"lines": ["$ psql", "postgres=# SELECT 1;"], "capability": "console-block"},
                          source_refs=[ref("canon16")]),
                        n("equation", {"latex": "\\sum_{i=1}^n x_i", "display": True, "capability": "equation-block"},
                          source_refs=[ref("canon17")]),
                        n("figure", {"src": "assets/fig.png", "alt": "Figure", "caption": "Caption", "capability": "figure"},
                          source_refs=[ref("canon18")]),
                        n("diagram", {"kind": "mermaid", "text": "graph TD; A-->B", "alt": "diagram", "capability": "diagram-mermaid-block"},
                          source_refs=[ref("canon19")]),
                        n("admonition", {"severity": "warning", "title": "Caution", "capability": "callout"},
                          source_refs=[ref("canon20")],
                          children=[n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                              n("text", {"text": "warning text", "capability": "text"}, source_refs=[]),
                          ])]),
                        n("collapsible", {"title": "Detail", "default_open": False, "capability": "collapsible"},
                          source_refs=[ref("canon21")],
                          children=[n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                              n("text", {"text": "hidden", "capability": "text"}, source_refs=[]),
                          ])]),
                        n("quote", {"cite": "Author", "capability": "quote"},
                          source_refs=[ref("canon22")],
                          children=[n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                              n("text", {"text": "quoted text", "capability": "text"}, source_refs=[]),
                          ])]),
                        n("columns", {"count": 2, "capability": "columns"},
                          source_refs=[ref("canon23")],
                          children=[
                              n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                                  n("text", {"text": "left", "capability": "text"}, source_refs=[])]),
                              n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                                  n("text", {"text": "right", "capability": "text"}, source_refs=[])]),
                          ]),
                        n("divider", {"capability": "divider"},
                          source_refs=[ref("canon24")]),
                        n("property-block", {"name": "license", "value": "MIT", "capability": "property-table"},
                          source_refs=[ref("canon25")]),
                        n("question", {"prompt": "What is MVCC?", "capability": "question"},
                          source_refs=[ref("canon26")],
                          children=[n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                              n("text", {"text": "Answer text.", "capability": "text"}, source_refs=[]),
                          ])]),
                        n("step", {"index": 1, "capability": "step"},
                          source_refs=[ref("canon27")],
                          children=[n("paragraph", {"capability": "paragraph"}, source_refs=[], children=[
                              n("text", {"text": "Step text.", "capability": "text"}, source_refs=[]),
                          ])]),
                        n("parameter-table", {"columns": ["param", "type", "default"], "capability": "parameter-table"},
                          source_refs=[ref("canon28")],
                          children=[n("text", {"text": "p | int | 0", "capability": "text"}, source_refs=[])]),
                    ]),
              ]),
        ],
    }


if __name__ == "__main__":
    print("Generando IRs...")
    write("canonical.json", canonical())
    write("minimal-postgres.json", minimal_postgres())
    write("minimal-kubernetes.json", minimal_kubernetes())
    write("minimal-cpp.json", minimal_cpp())
    write("minimal-ocr.json", minimal_ocr())
    print("OK.")
