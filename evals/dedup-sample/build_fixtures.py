#!/usr/bin/env python3
"""build_fixtures.py — F108 eval fixtures para dedup.

Genera 5 pares inyectados con escenarios distintos (idéntico, alias,
sinonimia, variante con título, especialización) + 1 nota adicional sin
duplicado para que el detector tenga ≥ MIN_NOTES_TO_RUN = 5.

Stdlib puro.

Uso:
    python3 evals/dedup-sample/build_fixtures.py [--regen]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
NOTES_DIR = FIXTURES_DIR / "notes"
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"


def _write_note(filename: str, fm: dict, body: str) -> Path:
    path = NOTES_DIR / filename
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            if v:
                lines.append(f'{k}: [{", ".join(repr(x) for x in v)}]')
            else:
                lines.append(f"{k}: []")
        else:
            lines.append(f'{k}: {v!r}')
    lines.append("---")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_pair_1_identical() -> Path:
    """Par idéntico: A1 = B1 (mismo canónico, mismo texto)."""
    body = (
        "## Definición\n"
        "MVCC es un protocolo de control de concurrencia que mantiene "
        "múltiples versiones de cada fila visibles según el snapshot del lector.\n"
    )
    a = _write_note(
        "a1-mvcc-v1.md",
        {"title": "MVCC v1", "note-id": "mvcc-v1", "note-type": "concept",
         "aliases": ["mvcc"]},
        body,
    )
    b = _write_note(
        "b1-mvcc-v2.md",
        {"title": "MVCC v2", "note-id": "mvcc-v2", "note-type": "concept",
         "aliases": ["mvcc"]},
        body,
    )
    return a.parent


def write_pair_2_alias() -> Path:
    """Par por alias: A2 canónico distinto; comparten alias "multi-version-concurrency-control"."""
    body = (
        "## Definición\n"
        "Multi-Version Concurrency Control es una técnica que permite a "
        "cada transacción ver un snapshot consistente.\n"
    )
    a = _write_note(
        "a2-mvcc-a.md",
        {"title": "MVCC A", "note-id": "mvcc-a", "note-type": "concept",
         "aliases": ["multi-version-concurrency-control"]},
        body,
    )
    b = _write_note(
        "b2-mvcc-b.md",
        {"title": "MVCC B", "note-id": "mvcc-b", "note-type": "concept",
         "aliases": ["multi-version-concurrency-control", "mvc"]},
        body,
    )
    return a.parent


def write_pair_3_sinonimia() -> Path:
    """Sinonimia: A3 canónico distinto, sin alias compartido, similarity ≥ 0.6."""
    body = (
        "## Definición\n"
        "El control de concurrencia multiversión mantiene un snapshot "
        "consistente de la base de datos al inicio de cada transacción.\n"
    )
    a = _write_note(
        "a3-isolation.md",
        {"title": "Isolation", "note-id": "isolation-x", "note-type": "concept",
         "aliases": []},
        body,
    )
    b = _write_note(
        "b3-snapshot.md",
        {"title": "Snapshot", "note-id": "snapshot-y", "note-type": "concept",
         "aliases": []},
        body,
    )
    return a.parent


def write_pair_4_titulo_variante() -> Path:
    """Variante con título: A4 canónico = 'mvcc'; B4 título distinto con sinonimia alta."""
    body_a = (
        "## Definición\n"
        "MVCC permite que cada lectura vea un snapshot sin bloquear a "
        "los escritores concurrentes.\n"
    )
    body_b = (
        "## Definición\n"
        "Multi-Version Concurrency Control permite que cada lectura vea "
        "un snapshot sin bloquear a los escritores concurrentes.\n"
    )
    a = _write_note(
        "a4-mvcc-titulo.md",
        {"title": "MVCC", "note-id": "mvcc-titulo", "note-type": "concept",
         "aliases": ["mvcc"]},
        body_a,
    )
    b = _write_note(
        "b4-mvcc-full-name.md",
        {"title": "Multi-Version Concurrency Control",
         "note-id": "multi-version-concurrency-control",
         "note-type": "concept", "aliases": ["mvcc"]},
        body_b,
    )
    return a.parent


def write_pair_5_specialization() -> Path:
    """Especialización: A5 cubre múltiples temas; B5 es subconjunto estricto."""
    body_parent = (
        "## Definición\n"
        "El control de concurrencia incluye mecanismos de locking, MVCC "
        "multi-versión por fila visibles según snapshot del lector, y "
        "serialización. Aquí se detallan los tres enfoques.\n\n"
        "## Locking\n"
        "Los locks de fila y tabla coordinan accesos concurrentes.\n\n"
        "## MVCC\n"
        "MVCC mantiene múltiples versiones por fila visibles según "
        "snapshot del lector.\n\n"
        "## Serialización\n"
        "La serialización total garantiza orden equivalente al secuencial.\n"
    )
    body_child = (
        "## Definición\n"
        "MVCC mantiene múltiples versiones por fila visibles según "
        "snapshot del lector.\n"
    )
    a = _write_note(
        "a5-concurrency.md",
        {"title": "Concurrency Control", "note-id": "concurrency",
         "note-type": "concept", "aliases": ["cc"]},
        body_parent,
    )
    b = _write_note(
        "b5-mvcc-only.md",
        {"title": "MVCC", "note-id": "mvcc-only", "note-type": "concept",
         "aliases": ["mvcc"]},
        body_child,
    )
    return a.parent


def write_extra_notes() -> None:
    """Notas adicionales sin duplicado para que el detector tenga ≥ MIN_NOTES_TO_RUN = 5
    notas distintas + pares."""
    _write_note(
        "x1-wal.md",
        {"title": "Write-Ahead Logging", "note-id": "wal",
         "note-type": "concept", "aliases": ["wal-log"]},
        "## Definición\nWAL es el log donde se escriben los cambios antes de aplicarse.\n",
    )
    _write_note(
        "x2-vacuum.md",
        {"title": "VACUUM", "note-id": "vacuum", "note-type": "concept",
         "aliases": []},
        "## Definición\nVACUUM reclama espacio de filas muertas tras actualizaciones.\n",
    )


def write_glossary() -> Path:
    """Glossary con alias cross-reference para el par 2."""
    glossary = {
        "schema_version": "1.0.0",
        "source": {"id": "alpha", "vendor": "postgres"},
        "terms": [
            {
                "canonical": "mvcc",
                "definition": "Multi-Version Concurrency Control.",
                "domain": "postgres",
                "aliases": [
                    {"alias": "multi-version-concurrency-control", "kind": "en"},
                    {"alias": "control-de-concurrencia-multiversion", "kind": "es"},
                ],
                "definitions": [
                    {
                        "chapter": "/ch01",
                        "definition": "Multi-Version Concurrency Control.",
                        "canonical": True,
                        "status": "current",
                        "first_seen_at": "2026-01-01T00:00:00Z",
                    }
                ],
            },
        ],
        "build_metadata": {"built_at": "2026-01-01T00:00:00Z", "term_count": 1},
    }
    path = FIXTURES_DIR / "glossary.json"
    path.write_text(json.dumps(glossary, indent=2), encoding="utf-8")
    return path


def write_expected_candidates() -> None:
    """Lista ground-truth de pares candidatos."""
    candidates = [
        {"pair": ["mvcc-v1", "mvcc-v2"], "expected_action": "merge"},
        {"pair": ["mvcc-a", "mvcc-b"], "expected_action": "merge"},
        {"pair": ["mvcc-titulo", "multi-version-concurrency-control"],
         "expected_action": "merge"},
        {"pair": ["concurrency", "mvcc-only"], "expected_action": "specialize"},
        # Par 3 (sinonimia similarity) — puede no ser detectado (sub-umbral);
        # el recall cuenta con 4 candidatos firmes.
    ]
    payload = {
        "schema_version": "1.0.0",
        "min_recall_pairs": 4,
        "candidates": [
            {"pair": c["pair"]} for c in candidates
        ],
    }
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXPECTED_DIR / "candidates.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--regen", action="store_true")
    args = p.parse_args()
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    write_pair_1_identical()
    write_pair_2_alias()
    write_pair_3_sinonimia()
    write_pair_4_titulo_variante()
    write_pair_5_specialization()
    write_extra_notes()
    write_glossary()
    write_expected_candidates()
    n = sum(1 for _ in NOTES_DIR.glob("*.md"))
    sys.stdout.write(f"OK — {n} notas; glossary; expected/candidates.json\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())