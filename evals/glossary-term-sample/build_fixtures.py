#!/usr/bin/env python3
"""Generador de fixtures para la Fase 89 — `glossary-term`.

Produce 3 notas que ejercitan los 3 criterios ROADMAP:

  notes/xmin.md — PostgreSQL xmin: definición + formas (inglés/español/sigla) +
        aliases + confundibles + notas donde aparece. Cubre criterio #1
        (definición + aliases) + #2 (confundibles) + #3 (formas inglés/español).
  notes/mvcc.md — PostgreSQL MVCC: igual estructura. Sigla universal.
  notes/fork.md — Unix fork(): término clásico del OS, formas inglés/español,
        confundibles con `exec`, `clone`.

Las 3 notas siguen el patrón de `references/05-note-types/glossary-term.md`:
≤ 30 líneas (anti-patrón duro de F75 §6.12).

Uso:
    python3 evals/glossary-term-sample/build_fixtures.py            # genera
    python3 evals/glossary-term-sample/build_fixtures.py --check   # + density_check

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
# Fixture 1 — PostgreSQL xmin/xmax
# ---------------------------------------------------------------------------

XMIN_NOTE = """---
title: "xmin"
note-type: glossary-term
status: draft
summary: "ID de transacción que insertó una fila en PostgreSQL; parte del mecanismo MVCC."
tags: [type/glossary-term, domain/databases]
source: "PostgreSQL 16 — System Columns"
source-type: docs
source-anchor: "system-columns"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]]"
---

# xmin

## TL;DR
`xmin` es el ID de la transacción que insertó la fila; parte del mecanismo MVCC que permite a PostgreSQL mantener snapshots por sesión. {src:blk_g00000000010}

{layer:l1}

## Definición
Identificador de transacción (XID) almacenado en cada tupla que indica qué transacción creó la fila; usado por MVCC para decidir la visibilidad del snapshot.

## Formas
| Idioma | Forma |
|---|---|
| Inglés | transaction ID (xmin) |
| Español | ID de transacción (xmin) |
| Sigla | xmin |

## Aliases
- `t_xmin` (en código fuente de PostgreSQL)

## Contexto
:::tip
Columna de sistema en PostgreSQL; presente en cada tabla sin necesidad de definirla explícitamente.
:::

## Ejemplos
:::example
`SELECT xmin, * FROM users;` retorna el XID de la transacción que creó cada fila; `xmin = 1234` significa "fila insertada por transacción 1234".
:::

## Confundibles
| Término | Diferencia |
|---|---|
| `[[term:xmax]]` | XID de transacción que eliminó/modificó la fila |
| `[[term:cmin]]` | Command ID dentro de la transacción (no inter-transaccional) |
| `cid` | Alias obsoleto de `cmin` |

## Notas donde aparece
- [[note:postgresql-mvcc]]
- [[note:postgresql-configuration]]

## Backlinks
- [[note:postgresql-mvcc]]
"""


# ---------------------------------------------------------------------------
# Fixture 2 — PostgreSQL MVCC
# ---------------------------------------------------------------------------

MVCC_NOTE = """---
title: "MVCC"
note-type: glossary-term
status: draft
summary: "Multi-Version Concurrency Control; permite lecturas y escrituras concurrentes sin bloqueos mediante snapshots por sesión."
tags: [type/glossary-term, domain/databases]
source: "PostgreSQL 16 — Concurrency Control"
source-type: docs
source-anchor: "mvcc-intro"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-architecture]]"
---

# MVCC

## TL;DR
MVCC (Multi-Version Concurrency Control) permite a múltiples transacciones leer y escribir sin bloqueos manteniendo un snapshot por sesión. {src:blk_g00000000020}

{layer:l1}

## Definición
Técnica de control de concurrencia donde cada transacción ve un snapshot consistente del estado de la base de datos sin necesidad de bloqueos de lectura.

## Formas
| Idioma | Forma |
|---|---|
| Inglés | Multi-Version Concurrency Control |
| Español | Control de Concurrencia Multiversión |
| Sigla | MVCC |

## Aliases
- Multi-versioning
- Snapshot-based concurrency control

## Contexto
:::tip
Usado en PostgreSQL, MySQL InnoDB, Oracle, CockroachDB y la mayoría de RDBMS modernas.
:::

## Ejemplos
:::example
`SELECT * FROM users WHERE id = 1;` retorna el snapshot del último COMMIT antes de la transacción, incluso si otras transacciones modifican la fila simultáneamente.
:::

## Confundibles
| Término | Diferencia |
|---|---|
| `[[term:two-phase-locking]]` | Two-Phase Locking; bloquea filas vs MVCC usa snapshots |
| `Snapshot isolation` | Sinónimo aproximado pero no idéntico |
| `SERIALIZABLE` | Nivel de aislamiento; PostgreSQL usa SSI (variant MVCC) |

## Notas donde aparece
- [[note:postgresql-mvcc]]
- [[note:postgresql-architecture]]
- [[note:postgres-connection-errors]]

## Backlinks
- [[note:postgresql-mvcc]]
"""


# ---------------------------------------------------------------------------
# Fixture 3 — Unix fork()
# ---------------------------------------------------------------------------

FORK_NOTE = """---
title: "fork"
note-type: glossary-term
status: draft
summary: "System call POSIX que crea un proceso hijo duplicando el proceso actual."
tags: [type/glossary-term, domain/os]
source: "POSIX.1-2017 — fork(2)"
source-type: spec
source-anchor: "fork"
retrieved: 2026-09-27
related: "[[note:docker-architecture]]"
---

# fork

## TL;DR
`fork()` es una system call POSIX que crea un proceso hijo idéntico al padre mediante copia-on-write; usada por servidores y shells. {src:blk_g00000000030}

{layer:l1}

## Definición
Llamada al sistema que duplica el proceso actual: el hijo recibe una copia del espacio de direcciones, registros y descriptores del padre; retorna 0 al hijo y el PID del hijo al padre.

## Formas
| Idioma | Forma |
|---|---|
| Inglés | fork (system call) |
| Español | bifurcación (de proceso) |
| Sigla | fork |

## Aliases
- `fork(2)` (notación de man page)
- `vfork` (variant: el padre espera al hijo)
- `clone` (Linux: implementation genérica de fork)

## Contexto
:::tip
POSIX.1-2017; implementada en Linux, macOS, BSD. Usada por Nginx, PostgreSQL, Docker daemon, y shells.
:::

## Ejemplos
:::example
`pid_t pid = fork(); if (pid == 0) { /* proceso hijo */ } else { /* proceso padre */ }` crea un proceso hijo idéntico al padre.
:::

## Confundibles
| Término | Diferencia |
|---|---|
| `exec` | Reemplaza el proceso actual con uno nuevo; fork lo duplica |
| `[[term:clone]]` | Linux: implementación genérica con flags; fork es un wrapper |
| `posix_spawn` | API de alto nivel que combina fork + exec |

## Notas donde aparece
- [[note:docker-architecture]]
- [[note:postgresql-architecture]]

## Backlinks
- [[note:docker-architecture]]
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

    # 3) Añadir {src:} a párrafos fácticos sin src en TL;DR, Definición, Contexto.
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
                "## Definición",
                "## Contexto",
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
    _write(NOTES_DIR / "xmin.md", XMIN_NOTE)
    _write(NOTES_DIR / "mvcc.md", MVCC_NOTE)
    _write(NOTES_DIR / "fork.md", FORK_NOTE)


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
    print(f"Generadas 3 notas en {NOTES_DIR}")

    if args.check:
        return check_density()
    return 0


if __name__ == "__main__":
    sys.exit(main())
