"""Eval battery — Fase 42: reglas de fidelidad.

Sintetiza notas NoteMark + ledgers para verificar los 3 criterios del roadmap:
1. Todo contenido externo va en bloque identificable en los 7 destinos.
2. Con una fuente incompleta a propósito, la nota declara la ausencia.
3. Ningún valor técnico aparece sin respaldo en el ledger.

Sin dependencias externas (Python 3.9+ stdlib puro).

Uso:
    python3 evals/fidelity-sample/build_fixtures.py
    python3 evals/fidelity-sample/run_eval.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIX = HERE / "fixtures"
EXP = HERE / "expected"

VALIDATE_LEDGER = REPO / "scripts" / "util" / "validate_ledger.py"
F37_EVAL = REPO / "evals" / "information-units-sample" / "run_eval.py"
F38_EVAL = REPO / "evals" / "ledger-operativo-sample" / "run_eval.py"
F39_EVAL = REPO / "evals" / "concept-graph-sample" / "run_eval.py"
F40_EVAL = REPO / "evals" / "terminology-sample" / "run_eval.py"
F41_EVAL = REPO / "evals" / "conflicts-sample" / "run_eval.py"

# Palabras/frases prohibidas por la regla de la duda (F42 §5).
PROHIBITED_WORDS = [
    "probablemente", "típicamente", "en general", "asumimos", "suponemos",
    "creemos que", "suele ser", "lo más común es", "por defecto",
    "a menudo", "generalmente", "normalmente",
]

# Regex para extraer valores técnicos (criterio 3).
# Defaults: `default 64 MB`, `default: 64 MB`, `por defecto 64 MB`
RE_DEFAULT = re.compile(r'\bdefault\s*[:=]?\s*([0-9]+\s*[KMGT]?B|MB|KB|GB|TB|true|false)\b', re.IGNORECASE)
# Parámetros: `parámetro X`, `parameter X`, `param X` seguido de `: tipo`
RE_PARAMETER = re.compile(r'\b(?:par[aá]metro|parameter|param)\s+([a-z][a-z0-9_-]+)', re.IGNORECASE)
# Códigos de error: `E1234`, `ORA-00904`, `EINVAL`
RE_ERROR_CODE = re.compile(r'\b([A-Z]{2,}[A-Z0-9]*-\d{2,6}|[A-Z]+[A-Z0-9_]{2,})\b')
# Versiones: `v1.2.3`, `PostgreSQL 13`, `version 2.0`
RE_VERSION = re.compile(r'\b(?:v|version)\s*(\d+(?:\.\d+){1,3})\b', re.IGNORECASE)
RE_VERSION_PRODUCT = re.compile(r'\b(POSTGRESQL|MYSQL|KUBERNETES|PYTHON)\s+(\d+)\b', re.IGNORECASE)
# Sintaxis: bloques BNF/EBNF o regex de comandos
RE_SYNTAX = re.compile(r'::=\s*[A-Za-z0-9_<>|]+')
# Comandos: líneas que parecen shell (heurística simple)
RE_COMMAND = re.compile(r'^\$\s+([a-z][a-z0-9_-]*)', re.MULTILINE)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


# -------------------------------------------------------------------
# NoteMark fixtures.
# -------------------------------------------------------------------

NOTE_GOOD = """\
# Postgres Configuration

PostgreSQL es un ORDBMS. {src:blk_a1b2c3d4e5f6}

:::derived
Diagrama de la arquitectura cliente-servidor:
```mermaid
flowchart LR
    A[Cliente] --> B[Servidor]
```
:::

:::external
La mayoría de los ORDBMS usan MVCC; ver RFC 1234. {external}
:::

El parámetro `shared_buffers` controla el caché compartido. {src:blk_b2c3d4e5f6a7}
El default es 128 MB. {src:blk_c3d4e5f6a7b8}
El código de error EADDRINUSE indica puerto en uso. {src:blk_d4e5f6a7b8c9}
"""

# Bloque derivado sin respaldo en ledger (criterio 3 violado).
NOTE_DERIVED_MISSING = """\
# Postgres Configuration

:::derived
El default de `shared_buffers` es 64 MB en /ch03 (sin respaldo en ledger).
:::
"""

# Bloque externo sin la directiva + mermaid sin :::derived (criterio 1 violado).
NOTE_EXTERNAL_MISSING = """\
# Postgres Configuration

Probablemente la mayoría de ORDBMS usan MVCC. {external}
El default es 256 MB (inventado).

```mermaid
flowchart LR
    A[Cliente] --> B[Servidor]
```
"""

# Palabras prohibidas + paráfrasis larga sin tag.
NOTE_DOUBTFUL = """\
# Postgres Configuration

Probablemente `shared_buffers` debería ser 64 MB por defecto.
Típicamente, en general, asumimos que PostgreSQL usa MVCC.
"""

# Fuente incompleta — declara la ausencia correctamente.
NOTE_INCOMPLETE_GOOD = """\
# Postgres Configuration

El manual no menciona el rango válido de `shared_buffers` en esta versión.
Fuente incompleta: falta información sobre el código de error de timeout.
"""

# Fuente incompleta — completa lo que la fuente omite (inventa).
NOTE_INCOMPLETE_BAD = """\
# Postgres Configuration

El rango válido de `shared_buffers` es 8 MB a 1 GB.
El código de error de timeout es ETIMEDOUT y se lanza tras 30 segundos.
"""


# -------------------------------------------------------------------
# Ledger fixtures.
# -------------------------------------------------------------------

def ledger_good() -> dict:
    """Ledger con entries de respaldo para todos los valores técnicos de note-good."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "entries": [
            {
                "unit_id": "u_p_01",
                "source_block_ids": ["b2c3d4e5f6a7"],
                "source_section_path": "/ch02/configuration",
                "type": "parameter",
                "criticality": "must-keep",
                "target_note": "postgres-config",
                "state": "written",
                "content": {"name": "shared_buffers", "description": "Tamaño del caché."},
            },
            {
                "unit_id": "u_d_01",
                "source_block_ids": ["c3d4e5f6a7b8"],
                "source_section_path": "/ch02/configuration",
                "type": "default",
                "criticality": "must-keep",
                "target_note": "postgres-config",
                "state": "written",
                "content": {"name": "shared_buffers", "value": "128 MB"},
            },
            {
                "unit_id": "u_e_01",
                "source_block_ids": ["d4e5f6a7b8c9"],
                "source_section_path": "/ch02/configuration",
                "type": "error-code",
                "criticality": "must-keep",
                "target_note": "postgres-config",
                "state": "written",
                "content": {"code": "EADDRINUSE", "message": "Puerto en uso."},
            },
        ],
        "build_metadata": {"version": "1.0", "built_at": "2026-09-25T00:00:00Z"},
    }


def ledger_missing() -> dict:
    """Ledger sin entries de respaldo para los valores de note-derived-missing."""
    return {
        "schema_version": "2.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64},
        "entries": [],
        "build_metadata": {"version": "1.0", "built_at": "2026-09-25T00:00:00Z"},
    }


def ledger_incomplete() -> dict:
    """Ledger con la mitad de los valores respaldados (para verificar ausencias)."""
    base = ledger_good()
    return base


# -------------------------------------------------------------------
# SDM con fuente incompleta.
# -------------------------------------------------------------------

def source_incomplete() -> dict:
    """SDM que NO menciona el rango de shared_buffers ni el error de timeout."""
    return {
        "schema_version": "1.0.0",
        "source": {"id": "fixture-pg", "hash": "a" * 64, "format": "pdf"},
        "sections": [{
            "section_path": "/ch02/configuration",
            "title": "Configuration",
            "blocks": [
                {
                    "id": "b2c3d4e5f6a7",
                    "type": "parameter",
                    "content": {"name": "shared_buffers", "description": "Tamaño del caché."},
                    "anchor": {"page": 1, "section_path": "/ch02/configuration", "bbox": None},
                    "confidence": 1.0,
                    "origin": "native",
                },
            ],
        }],
    }


def main() -> int:
    FIX.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    _write_text(FIX / "note-good.md", NOTE_GOOD)
    _write_text(FIX / "note-derived-missing.md", NOTE_DERIVED_MISSING)
    _write_text(FIX / "note-external-missing.md", NOTE_EXTERNAL_MISSING)
    _write_text(FIX / "note-doubtful.md", NOTE_DOUBTFUL)
    _write_text(FIX / "note-incomplete-good.md", NOTE_INCOMPLETE_GOOD)
    _write_text(FIX / "note-incomplete-bad.md", NOTE_INCOMPLETE_BAD)

    _write_json(FIX / "ledger-good.json", ledger_good())
    _write_json(FIX / "ledger-missing.json", ledger_missing())
    _write_json(FIX / "ledger-incomplete.json", ledger_incomplete())
    _write_json(FIX / "source-incomplete.json", source_incomplete())

    print("fixtures: 6 NoteMark + 3 ledger + 1 SDM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
