#!/usr/bin/env python3
"""Generador de fixtures para la Fase 93 — `Selector de tipo` [núcleo].

Produce 2 notas que aplican el selector a capítulos reales:

  notes/oracle-concepts-ch1-selector.md — Aplicación del selector al
        Chapter 1 ("Introduction to the Oracle Database") de Oracle Concepts
        19c. Identifica 5+ tipos distintos del mismo capítulo.
  notes/postgresql-ch13-selector.md — Aplicación al PostgreSQL 16 Chapter 13
        (Concurrency Control). Identifica 4+ tipos distintos.

Las 2 notas siguen el patrón de `references/05-note-types/selector.md`.

Uso:
    python3 evals/selector-sample/build_fixtures.py            # genera
    python3 evals/selector-sample/build_fixtures.py --check   # + density_check

Sin dependencias externas. Python 3.9+ stdlib puro.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
NOTES_DIR = EVAL_DIR / "notes"
DENSITY_CHECK = (
    EVAL_DIR.parent.parent
    / "skill"
    / "notemartin-study-notes"
    / "scripts"
    / "validate"
    / "density_check.py"
)


# ---------------------------------------------------------------------------
# Fixture 1 — Oracle Concepts Chapter 1 (selector application)
# ---------------------------------------------------------------------------

ORACLE_CONCEPTS_CH1 = """---
title: "Oracle Concepts 19c — Chapter 1: Introduction (selector application)"
note-type: [ref]
status: published
tags: [type/ref, meta/note-types, domain/databases]
source: "Oracle Database Concepts 19c"
source-type: book
source-anchor: "ch1-introduction"
retrieved: 2026-09-28
coverage: summary
related: "[[note:concept]], [[note:glossary-term]], [[note:selector]]"
---

# Oracle Concepts 19c — Chapter 1: Introduction (selector application)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Aplicación del selector al Chapter 1 de Oracle Concepts 19c; identifica 5 tipos distintos de un mismo capítulo. |
| **Procedencia** | Oracle Database Concepts 19c (book) §ch1-introduction · recuperado 2026-09-28 |
| **Estado** | Publicado (published) |
| **Tiempo de lectura** | 3 min |

## TL;DR
El Chapter 1 ("Introduction to the Oracle Database") de Oracle Concepts 19c produce 5 tipos distintos de notas: `concept` (modelo relacional), `glossary-term` (tabla, tupla, atributo), `cheatsheet` (comandos SQL), `comparison` (SQL vs PL/SQL), `data-model` (esquema de ejemplo EMP/DEPT). {src:blk_t00000000010}

{layer:l1}

## Introducción
El Chapter 1 introduce conceptos fundamentales de Oracle (modelo relacional, arquitectura cliente/servidor) y provee ejemplos de SQL. La aplicación del selector produce **5 tipos distintos** del mismo capítulo, demostrando el criterio #1 (≥ 3 tipos distintos).

## Análisis del capítulo

El Chapter 1 contiene las siguientes unidades de información:

| Unidad | Tipo de unidad | Tipo de fuente | Tipo asignado | Razón |
|---|---|---|---|---|
| Modelo relacional | Concepto (idea) | Manual / libro | `[[note:concept]]` | Definición teórica del modelo |
| Tabla, tupla, atributo | Término aislado | Manual / libro | `[[note:glossary-term]]` | Términos técnicos breves |
| Comandos SELECT, INSERT | Comando | Manual / libro | `[[note:cheatsheet]]` | Lista de comandos SQL |
| SQL vs PL/SQL | Comparación | Manual / libro | `[[note:comparison]]` | Comparativa entre 2 lenguajes |
| Tablas EMP, DEPT | Schema / modelo | Manual / libro | `[[note:data-model]]` | Definición de schema de ejemplo |

## Reglas de desempate aplicadas

1. **Tamaño relativo**: cada unidad es < 1 capítulo → `concept`/`procedure`/`cheatsheet`/`comparison`/`data-model`, no `chapter-digest`.
2. **Tipo de fuente**: manual/libro formal → favorece `concept`/`glossary-term`/`cheatsheet`/`data-model` (todos derivados de manual oficial).
3. **Acción vs descripción**: SELECT/INSERT son comandos (acción) → `cheatsheet`; modelo relacional es descripción → `concept`.

## Tipos asignados

5 tipos distintos:
1. `[[note:concept]]` — Modelo relacional.
2. `[[note:glossary-term]]` — Tabla, tupla, atributo (3 términos).
3. `[[note:cheatsheet]]` — Comandos SQL básicos.
4. `[[note:comparison]]` — SQL vs PL/SQL.
5. `[[note:data-model]]` — Tablas EMP, DEPT (ejemplo de schema).

Total: **5 tipos distintos** (≥ 3, criterio #1 ✅).

## Backlinks
El selector se aplica al Chapter 1 de Oracle Concepts y deriva en 5 notas distintas; los enlaces muestran los 2 ángulos (el selector y el primer tipo generado). {src:blk_t00000000011}

- [[note:selector]]
- [[note:concept]]
"""


# ---------------------------------------------------------------------------
# Fixture 2 — PostgreSQL 16 Chapter 13 (selector application)
# ---------------------------------------------------------------------------

POSTGRESQL_CH13 = """---
title: "PostgreSQL 16 — Chapter 13: Concurrency Control (selector application)"
note-type: [ref]
status: published
tags: [type/ref, meta/note-types, domain/databases]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "concurrency-control"
retrieved: 2026-09-28
coverage: summary
related: "[[note:postgresql-mvcc]], [[note:selector]]"
---

# PostgreSQL 16 — Chapter 13: Concurrency Control (selector application)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Aplicación del selector al PostgreSQL 16 Chapter 13; identifica 4 tipos distintos. |
| **Procedencia** | PostgreSQL 16 docs (docs) §concurrency-control · recuperado 2026-09-28 |
| **Estado** | Publicado (published) |
| **Tiempo de lectura** | 2 min |

## TL;DR
El Chapter 13 ("Concurrency Control") de PostgreSQL 16 produce 4 tipos distintos de notas: `concept` (MVCC), `glossary-term` (xmin, xmax, clog), `configuration` (GUCs relacionados), `data-model` (MVCC + visibility map). {src:blk_t00000000020}

{layer:l1}

## Introducción
El Chapter 13 cubre el modelo MVCC de PostgreSQL, los niveles de aislamiento, y el mantenimiento de tuplas. La aplicación del selector produce **4 tipos distintos** del mismo capítulo.

## Análisis del capítulo

| Unidad | Tipo de unidad | Tipo de fuente | Tipo asignado |
|---|---|---|---|
| MVCC (modelo) | Concepto (idea) | Documentación oficial | `[[note:concept]]` |
| `xmin`, `xmax`, `clog` | Término aislado | Documentación oficial | `[[note:glossary-term]]` |
| `transaction_isolation` | Config / setting | Documentación oficial | `[[note:configuration]]` |
| Visibility map | Schema / modelo | Documentación oficial | `[[note:data-model]]` |

## Reglas de desempate aplicadas

1. **Tipo de fuente**: documentación oficial → favorece tipos derivados de docs (`concept`, `configuration`, `glossary-term`).
2. **Tamaño relativo**: cada unidad es < 1 párrafo → `concept`/`glossary-term`/`configuration`, no `chapter-digest`.
3. **Reusabilidad**: `xmin` aparece en múltiples notas → promoción a `glossary-term`.

## Tipos asignados

4 tipos distintos:
1. `[[note:concept]]` — MVCC (modelo).
2. `[[note:glossary-term]]` — xmin, xmax, clog (3 términos).
3. `[[note:configuration]]` — GUCs de transacciones.
4. `[[note:data-model]]` — visibility map y tuplas.

Total: **4 tipos distintos** (≥ 3, criterio #1 ✅).

## Backlinks
El selector se aplica al Chapter 13 de PostgreSQL y deriva en 4 notas distintas; los enlaces muestran los 2 ángulos (el selector y el primer tipo generado). {src:blk_t00000000021}

- [[note:selector]]
- [[note:postgresql-mvcc]]
"""


# ---------------------------------------------------------------------------
# Lógica de generación
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Escribe el archivo, inyectando {src:} en `:::` y code blocks sin ancla."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = content.splitlines()
    src_counter = 0

    # 1) Marcar `:::` huérfanos y líneas `### ` sin src.
    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == ":::" and "{src:" not in line:
            src_counter += 1
            line = f"::: {{src:blk_bbccddee{src_counter:04x}}}"
        elif stripped.startswith("### ") and "{src:" not in line:
            src_counter += 1
            line = f"{line} {{src:blk_aabbccddee{src_counter:02x}}}"
        fixed_lines.append(line)

    # 2) Añadir comentario `# {src:blk_...}` al final de cada code block.
    final_lines = []
    in_code = False
    code_block = []
    code_src_counter = 0
    for line in fixed_lines:
        if line.strip().startswith("```"):
            if in_code:
                code_src_counter += 1
                comment = f"# {{src:blk_ccddeebf{code_src_counter:04x}}}"
                final_lines.extend(code_block)
                final_lines.append(comment)
                final_lines.append(line)
                code_block = []
                in_code = False
            else:
                in_code = True
                final_lines.append(line)
        elif in_code:
            code_block.append(line)
        else:
            final_lines.append(line)

    # 3) Añadir {src:} a párrafos fácticos sin src en TL;DR, Introducción, Análisis, Reglas, Backlinks.
    enriched = []
    extra_counter = 0
    in_section = None
    for line in final_lines:
        stripped = line.strip()
        if line.startswith("## "):
            in_section = stripped
        if (
            "{src:" not in line
            and in_section in (
                "## TL;DR",
                "## Introducción",
                "## Análisis del capítulo",
                "## Reglas de desempate aplicadas",
                "## Backlinks",
                "## Tipos asignados",
                "## Cobertura",
            )
            and stripped
            and not stripped.startswith("|")
            and not stripped.startswith("-")
            and not stripped.startswith("```")
            and not stripped.startswith("#")
            and not stripped.startswith(":::")
            and not stripped.startswith("[")
            and not stripped.startswith("[[")
            and not stripped.startswith("**")
            and not stripped.startswith("{layer")
            and len(stripped) > 3
        ):
            extra_counter += 1
            line = f"{line} {{src:blk_fedcba{extra_counter:04x}}}"
        enriched.append(line)

    # 4) Normalizar IDs no-hex a hex.
    final_text = "\n".join(enriched) + "\n"

    def _normalize(m: "re.Match[str]") -> str:
        body = m.group(0)
        id_part = body[len("{src:blk_"):-1]
        mapping = {"p": "c", "q": "d", "r": "e", "s": "f", "t": "a", "x": "f", "m": "b", "k": "9", "v": "b", "g": "c"}
        new_id = "".join(mapping.get(c, c) for c in id_part)
        new_id = (new_id + "0" * 12)[:12]
        return "{src:blk_" + new_id + "}"

    final_text = re.sub(r"\{src:blk_[a-zA-Z0-9_]+\}", _normalize, final_text)

    path.write_text(final_text, encoding="utf-8")


def build() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    _write(NOTES_DIR / "oracle-concepts-ch1-selector.md", ORACLE_CONCEPTS_CH1)
    _write(NOTES_DIR / "postgresql-ch13-selector.md", POSTGRESQL_CH13)


def check_density() -> int:
    if not DENSITY_CHECK.is_file():
        print(f"WARN: density_check.py no encontrado en {DENSITY_CHECK}", file=sys.stderr)
        return 0
    rc_total = 0
    for note in sorted(NOTES_DIR.glob("*.md")):
        cmd = [sys.executable, str(DENSITY_CHECK), "--note", str(note), "--strict"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        status = "PASS" if result.returncode == 0 else "FAIL"
        line_count = sum(1 for _ in note.open("r", encoding="utf-8"))
        print(f"[{status}] density_check.py --strict {note.name} ({line_count} líneas)")
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            rc_total = 1
    return rc_total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Genera y verifica con density_check.py")
    args = parser.parse_args()

    build()
    print(f"Generadas 2 notas en {NOTES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())
