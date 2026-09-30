#!/usr/bin/env python3
"""
build_fixtures.py — Genera fixtures para evals/fidelity-audit-sample.

Crea 5 workdirs con defectos inyectados:
  - ir-no-source-refs/         nodo fáctico con source_refs=[]
  - ir-invented-parameter/     parameter.name inventado
  - ir-invented-error-code/    error-code inventado
  - ir-missing-backward/       bloque SDM must-keep no cubierto
  - ir-no-unit/                valor numérico sin attrs.unit

Y 2 golden del repo:
  - golden-clean/  (no debe disparar error)
  - golden-uses-unit/  (valor con unidad correcta)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures"
GOLDEN = ROOT / "golden"

SDM_TEXT_FOR_FIXTURES = (
    "PostgreSQL is an ORDBMS. The default shared_buffers is 128MB. "
    "The parameter work_mem defaults to 4MB. "
    "Error code FATAL 534 occurs when configuration is invalid. "
    "Version 16 introduced scram-sha-256 as default password_encryption."
)


def write(rel: str, content: str) -> None:
    p = FIX / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def write_at(base: Path, rel: str, content: str) -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def json_write(rel: str, obj) -> None:
    write(rel, json.dumps(obj, indent=2, ensure_ascii=False))


def golden_write(rel: str, obj) -> None:
    p = GOLDEN / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


# ────────────────────────────────────────────────────────────────────
# ir-no-source-refs: IR con nodo paragraph sin source_refs.
# ────────────────────────────────────────────────────────────────────
def build_no_source_refs() -> None:
    sdm = {
        "source": {"hash": "a" * 64},
        "sections": [
            {"id": "a1" * 4 + "abcd", "title": "Intro",
             "blocks": [
                 {"id": "abc123456789", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    json_write("ir-no-source-refs/sdm.json", sdm)
    ir = {
        "note_id": "test-note",
        "nodes": [
            {"id": "n1", "node": "paragraph",
             "text": "Some factual claim that should reference the SDM block.",
             "external": False, "derived": False,
             "source_refs": []},   # V-FAUDIT-01
            {"id": "n2", "node": "paragraph",
             "text": "Another claim with proper backing.",
             "external": False, "derived": False,
             "source_refs": [{"block_id": "abc123456789", "source_hash": "a" * 64}]},
        ],
    }
    json_write("ir-no-source-refs/ir/test.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# ir-invented-parameter: parameter.name no aparece en SDM.
# ────────────────────────────────────────────────────────────────────
def build_invented_parameter() -> None:
    sdm = {
        "source": {"hash": "b" * 64},
        "sections": [
            {"id": "b1" * 4 + "abcd", "title": "Intro",
             "blocks": [
                 {"id": "def123456789", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    json_write("ir-invented-parameter/sdm.json", sdm)
    ir = {
        "note_id": "test-param",
        "nodes": [
            {"id": "p1", "node": "parameter",
             "attrs": {"name": "custom_param_X42", "type": "string"},   # V-FAUDIT-03
             "source_refs": [{"block_id": "def123456789", "source_hash": "b" * 64}]},
            {"id": "p2", "node": "parameter",
             "attrs": {"name": "shared_buffers", "type": "size"},   # OK
             "source_refs": [{"block_id": "def123456789", "source_hash": "b" * 64}]},
        ],
    }
    json_write("ir-invented-parameter/ir/test.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# ir-invented-error-code: error-code.code inventado.
# ────────────────────────────────────────────────────────────────────
def build_invented_error_code() -> None:
    sdm = {
        "source": {"hash": "c" * 64},
        "sections": [
            {"id": "c1" * 4 + "abcd", "title": "Errors",
             "blocks": [
                 {"id": "fab123456789", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    json_write("ir-invented-error-code/sdm.json", sdm)
    ir = {
        "note_id": "test-err",
        "nodes": [
            {"id": "e1", "node": "error-code",
             "attrs": {"code": "E_FAKE_999"},   # V-FAUDIT-04
             "source_refs": [{"block_id": "fab123456789", "source_hash": "c" * 64}]},
        ],
    }
    json_write("ir-invented-error-code/ir/test.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# ir-missing-backward: SDM tiene bloque parameter no cubierto.
# ────────────────────────────────────────────────────────────────────
def build_missing_backward() -> None:
    # SDM con 2 bloques parameter; sólo uno está referenciado en el IR.
    sdm = {
        "source": {"hash": "d" * 64},
        "sections": [
            {"id": "d1" * 4 + "abcd", "title": "Parameters",
             "blocks": [
                 {"id": "111222333444", "anchor": {"page": 1},
                  "content": {"type": "parameter",
                              "name": "shared_buffers",
                              "text": "shared_buffers default 128MB"},
                  "source": "native"},
                 {"id": "555666777888", "anchor": {"page": 1},
                  "content": {"type": "parameter",
                              "name": "work_mem",
                              "text": "work_mem default 4MB for sort operations"},
                  "source": "native"},
             ]},
        ],
    }
    json_write("ir-missing-backward/sdm.json", sdm)
    ir = {
        "note_id": "test-coverage",
        "nodes": [
            # Sólo referencia shared_buffers; work_mem queda no cubierto.
            {"id": "n1", "node": "paragraph",
             "text": "shared_buffers is the cache.",
             "source_refs": [{"block_id": "111222333444", "source_hash": "d" * 64}]},
        ],
    }
    json_write("ir-missing-backward/ir/test.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# ir-no-unit: valor numérico sin attrs.unit.
# ────────────────────────────────────────────────────────────────────
def build_no_unit() -> None:
    sdm = {
        "source": {"hash": "e" * 64},
        "sections": [
            {"id": "e1" * 4 + "abcd", "title": "Defaults",
             "blocks": [
                 {"id": "999aaa111bbb", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    json_write("ir-no-unit/sdm.json", sdm)
    ir = {
        "note_id": "test-no-unit",
        "nodes": [
            {"id": "u1", "node": "default",
             "attrs": {"value": 128, "unit": "MB"},   # OK
             "source_refs": [{"block_id": "999aaa111bbb", "source_hash": "e" * 64}]},
            {"id": "u2", "node": "default",
             "attrs": {"value": 4},   # V-FAUDIT-02
             "source_refs": [{"block_id": "999aaa111bbb", "source_hash": "e" * 64}]},
        ],
    }
    json_write("ir-no-unit/ir/test.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# Golden — clean IR con todos los source_refs correctos.
# ────────────────────────────────────────────────────────────────────
def build_golden_clean() -> None:
    sdm = {
        "source": {"hash": "f" * 64},
        "sections": [
            {"id": "f1" * 4 + "abcd", "title": "Body",
             "blocks": [
                 {"id": "aaabbb111222", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    golden_write("clean/sdm.json", sdm)
    ir = {
        "note_id": "golden-clean",
        "nodes": [
            {"id": "g1", "node": "paragraph",
             "text": "PostgreSQL is an ORDBMS.",
             "source_refs": [{"block_id": "aaabbb111222", "source_hash": "f" * 64}]},
        ],
    }
    golden_write("clean/ir/golden.note-ir.json", ir)


# ────────────────────────────────────────────────────────────────────
# Golden — uses unit correctly.
# ────────────────────────────────────────────────────────────────────
def build_golden_uses_unit() -> None:
    sdm = {
        "source": {"hash": "1" * 64},
        "sections": [
            {"id": "1" * 8 + "abcd", "title": "Body",
             "blocks": [
                 {"id": "bbbccc222333", "anchor": {"page": 1},
                  "content": {"type": "prose", "text": SDM_TEXT_FOR_FIXTURES},
                  "source": "native"},
             ]},
        ],
    }
    golden_write("uses-unit/sdm.json", sdm)
    ir = {
        "note_id": "golden-unit",
        "nodes": [
            {"id": "gu1", "node": "default",
             "attrs": {"value": 128, "unit": "MB"},
             "source_refs": [{"block_id": "bbbccc222333", "source_hash": "1" * 64}]},
        ],
    }
    golden_write("uses-unit/ir/golden.note-ir.json", ir)


def main() -> None:
    build_no_source_refs()
    build_invented_parameter()
    build_invented_error_code()
    build_missing_backward()
    build_no_unit()
    build_golden_clean()
    build_golden_uses_unit()
    print(f"fixtures written under {FIX}")


if __name__ == "__main__":
    main()