#!/usr/bin/env python3
"""build_fixtures.py — F106 eval fixtures para book_mode.

Genera un SDM sintético de 10 capítulos, una batería de notas concept por
capítulo, y un caso negativo de redefinición (AP-BM1) más un caso de mapa
generado tarde (AP-BM2). Stdlib puro.

Uso:
    python3 evals/book-mode-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"

PREFACE = "Preface"
CHAPTERS = [
    "Introduction",
    "Getting Started",
    "MVCC Fundamentals",
    "Query Execution",
    "Storage Internals",
    "Replication",
    "Transactions",
    "Performance",
    "Case Studies",
    "Advanced Topics",
]


def write_sdm() -> Path:
    blocks = [
        {"type": "heading", "level": 1, "title": PREFACE,
         "anchor": {"section_path": f"/{PREFACE}"}},
        {"type": "text", "text": f"Welcome. See Chapter 1 for an overview.",
         "anchor": {"section_path": f"/{PREFACE}/intro"}},
    ]
    for i, title in enumerate(CHAPTERS, start=1):
        cid_in_book = i  # después del prefacio
        blocks.append({
            "type": "heading", "level": 1, "title": title,
            "anchor": {"section_path": f"/{title}"},
        })
        # Forward reference: ch1 menciona Chapter 2.
        if i == 1:
            body = f"This chapter references Chapter 2 for setup."
        elif i == 2:
            body = f"This chapter references Chapter 3 for details."
        elif i == 9:
            body = f"This chapter revisits Chapter 1 concepts."
        else:
            body = f"This chapter covers material in depth."
        blocks.append({
            "type": "text", "text": body,
            "anchor": {"section_path": f"/{title}/intro"},
        })
    sdm = {
        "schema_version": "1.0.0",
        "source": {"id": "synthetic-book", "hash": "a" * 64},
        "blocks": blocks,
    }
    path = FIXTURES_DIR / "sdm-book.json"
    path.write_text(json.dumps(sdm, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_notes() -> Path:
    """Genera notas concept por capítulo. Para ch02, la definición de
    MVCC es canónica; ch09 contiene una redefinición que NO usa
    `[[note:mvcc]]` (AP-BM1 fixture negativo)."""
    notes_dir = FIXTURES_DIR / "notes"
    if notes_dir.exists():
        import shutil
        shutil.rmtree(notes_dir)
    notes_dir.mkdir(parents=True)

    # ch02: canónico
    (notes_dir / "ch02").mkdir()
    (notes_dir / "ch02" / "mvcc.md").write_text(
        "---\nnote-type: concept\n---\n"
        "# MVCC\n\n"
        "## Definición\n"
        "MVCC es un protocolo de control de concurrencia que mantiene "
        "múltiples versiones de cada fila visibles según el snapshot del lector.\n",
        encoding="utf-8",
    )
    # ch03: linkea al canónico (PASS AP-BM1)
    (notes_dir / "ch03").mkdir()
    (notes_dir / "ch03" / "mvcc-references.md").write_text(
        "---\nnote-type: concept\n---\n"
        "# MVCC en queries\n\n"
        "## Definición\n"
        "Las queries observan un snapshot del estado al inicio de la "
        "transacción, sin necesidad de locks de lectura.\n\n"
        "## Notas\n"
        "Para la definición base véase [[note:mvcc]].\n",
        encoding="utf-8",
    )
    # ch09: redefinición SIN link (FAIL AP-BM1)
    (notes_dir / "ch09").mkdir()
    (notes_dir / "ch09" / "mvcc-redefined.md").write_text(
        "---\nnote-type: concept\n---\n"
        "# MVCC recap\n\n"
        "## Definición\n"
        "MVCC es un protocolo de control de concurrencia que mantiene "
        "múltiples versiones de cada fila visibles según el snapshot del lector.\n\n"
        "## Notas\n"
        "Recapitulación sin enlace explícito al canónico.\n",
        encoding="utf-8",
    )
    return notes_dir


def write_expected() -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected = {
        "after_init_chapters": 11,
        "after_init_has_preface": True,
        "after_init_total_chapters": 10,
        "after_init_edges_min": 2,
        "after_ch2_registered_concepts": ["mvcc"],
        "after_consolidation_at_ch5": "ch05",
        "ap_bm1_violation_count": 1,
        "ap_bm2_violation_present": True,
        "ap_bm4_force_preserves_previous": True,
    }
    (EXPECTED_DIR / "expected.json").write_text(
        json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true", help="regenerar fixtures")
    args = p.parse_args()
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    sdm = write_sdm()
    notes = write_notes()
    write_expected()
    sys.stdout.write(
        f"OK — fixtures: {sdm.relative_to(Path.cwd())}, "
        f"notes/ en {notes.relative_to(Path.cwd())}, "
        f"expected/ poblado\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())