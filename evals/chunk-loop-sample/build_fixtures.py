#!/usr/bin/env python3
"""build_fixtures.py — F107 eval fixtures para chunk_loop.

Genera 3 fixtures:
  - sdm-large.json: SDM con 250 bloques (simula ~250 páginas).
  - sdm-cross-chunk.json: SDM con 1 unidad que cruza 2 chunks.
  - audit-loads-no-full.jsonl: log de cargas SIN abrir el texto crudo.

Stdlib puro.

Uso:
    python3 evals/chunk-loop-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def write_sdm_large() -> Path:
    """SDM con 250 bloques, cada uno con anchor.page + section_path."""
    blocks = []
    for i in range(250):
        blocks.append({
            "type": "heading" if i % 10 == 0 else "text",
            "level": 1 if i % 10 == 0 else None,
            "title": f"Section {i // 10}" if i % 10 == 0 else None,
            "text": f"Block content {i}" if i % 10 != 0 else None,
            "anchor": {"section_path": f"/sec{i // 10}", "page": i + 1},
        })
    sdm = {
        "schema_version": "1.0.0",
        "source": {"id": "synthetic-large", "hash": "b" * 64},
        "blocks": blocks,
    }
    path = FIXTURES_DIR / "sdm-large.json"
    path.write_text(json.dumps(sdm, indent=2), encoding="utf-8")
    return path


def write_sdm_cross_chunk() -> Path:
    """SDM pequeño donde la unidad 'mvcc' aparece en chk01 (bloques 25-26)
    Y en chk02 (bloques 31-32). El script debe registrar la unidad una vez
    con primary_chunk=chk01 + secondary_chunks=[chk02]."""
    blocks = []
    for i in range(60):
        if 25 <= i <= 26:
            text = "MVCC definition (canonical chunk 1)"
        elif 31 <= i <= 32:
            text = "MVCC reference (secondary chunk 2)"
        else:
            text = f"Block {i}"
        blocks.append({
            "type": "text",
            "text": text,
            "anchor": {"section_path": f"/sec{i // 10}", "page": i + 1},
        })
    sdm = {
        "schema_version": "1.0.0",
        "source": {"id": "synthetic-cross-chunk", "hash": "c" * 64},
        "blocks": blocks,
    }
    path = FIXTURES_DIR / "sdm-cross-chunk.json"
    path.write_text(json.dumps(sdm, indent=2), encoding="utf-8")
    return path


def write_audit_log_clean() -> Path:
    """Audit log que NO contiene el path del texto crudo (PASS AP-CHK2)."""
    log_path = EXPECTED_DIR / "audit-loads-no-full.jsonl"
    entries = [
        {"path": "/work/sdm.json", "mode": "r"},
        {"path": "/work/chunk-state.json", "mode": "r"},
        {"path": "/work/profile.yaml", "mode": "r"},
        {"path": "/work/knowledge/ledger.json", "mode": "r"},
        {"path": "/work/ir/note-1.json", "mode": "r"},
        {"path": "/work/ir/note-2.json", "mode": "r"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n",
        encoding="utf-8",
    )
    return log_path


def write_audit_log_dirty() -> Path:
    """Audit log que SÍ contiene el path del texto crudo (FAIL AP-CHK2)."""
    log_path = FIXTURES_DIR / "audit-loads-with-full.jsonl"
    entries = [
        {"path": "/work/sdm.json", "mode": "r"},
        {"path": "/work/source/book-200p.pdf", "mode": "r"},  # VIOLACIÓN
        {"path": "/work/chunk-state.json", "mode": "r"},
    ]
    log_path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n",
        encoding="utf-8",
    )
    return log_path


def write_expected() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected = {
        "n_chunks_by_blocks_default": 9,           # ceil(250/30)
        "n_chunks_by_blocks_size_15": 17,          # ceil(250/15)
        "n_chunks_by_section_path_default": 25,    # 250/10
        "n_chunks_by_chapter_size_3": 9,           # 25 chapters / 3
        "cross_chunk_unit_count": 1,
        "cross_chunk_unit_primary": "chk01",
        "cross_chunk_unit_secondary": ["chk02"],
        "ap_chk2_dirty_loads_detected": 1,
    }
    (EXPECTED_DIR / "expected.json").write_text(
        json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    paths = [
        write_sdm_large(),
        write_sdm_cross_chunk(),
        write_audit_log_clean(),
        write_audit_log_dirty(),
    ]
    write_expected()
    for p in paths:
        sys.stdout.write(f"OK — {p.relative_to(Path.cwd())}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())