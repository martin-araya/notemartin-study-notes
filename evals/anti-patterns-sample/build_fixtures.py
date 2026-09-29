#!/usr/bin/env python3
"""Generador de fixtures para la Fase 100 — `anti-patterns`.

Produce 7 notas NoteMark en `evals/anti-patterns-sample/notes/`:

  - `antipatterns-clean.md`            — nota `concept` PostgreSQL sin AP
                                          transversales (cumple F100).
  - `antipatterns-bad-1-circular.md`    — definición circular (AP2).
  - `antipatterns-bad-2-marketing.md`   — marketing copiado (AP9).
  - `antipatterns-bad-3-bullet-dump.md`  — volcado de viñetas (AP8).
  - `antipatterns-bad-4-link-no-context.md` — enlaces sin contexto (AP7).
  - `antipatterns-bad-5-transcription.md`   — transcripción disfrazada (AP1).
  - `antipatterns-bad-6-empty-section.md`    — sección vacía (AP12).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/anti-patterns-sample/build_fixtures.py            # genera si no existe
    python3 evals/anti-patterns-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _antipatterns_clean() -> str:
    return """---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
tags: [type/concept, domain/databases, f78/concept, f100/anti-patterns]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:transactions]]"
---

# MVCC en PostgreSQL

PostgreSQL usa MVCC para evitar locks de lectura entre transacciones
concurrentes. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot al iniciar. Cada fila lleva
dos marcas (`xmin`, `xmax`). Los lectores ven filas cuyo rango cae
dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores como MyISAM bloqueaban un `SELECT` largo
con todas las inserciones. Un reporte diario podía detener la carga
OLTP durante minutos. {src:blk_a91f8e02c1d3}

## Definición formal

Para una transacción `T` con snapshot en `S(T)` y una fila `R`,
la fila es visible si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`.
{src:blk_a91f8e02c1d3}

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`.
{src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

- MVCC sustituye locks de lectura por marcas de versión. {src:blk_a91f8e02c1d3}
- Cada transacción ve un snapshot estable. {src:blk_a91f8e02c1d3}
- `VACUUM` libera versiones viejas. {src:blk_a91f8e02c1d3}

## Backlinks

Para profundizar en el reciclaje de versiones, consulta [[note:vacuum]].
Para entender el modelo transaccional, consulta [[note:transactions]]. {src:blk_a91f8e02c1d3}

## Checklist de cierre (12 items, F100)

Antes de cerrar la nota, verifica los 12 anti-patrones transversales:
AP1 (transcripción), AP2 (definición circular), AP3 (callout decorativo),
AP4 (tabla de una fila), AP5 (analogía sin mapeo), AP6 (diagrama que
repite el texto), AP7 (enlace sin contexto), AP8 (volcado de viñetas),
AP9 (marketing copiado), AP10 (código sin caption), AP11 (mermaid syntax
error), AP12 (sección vacía). {src:blk_a91f8e02c1d3}
"""


def _antipatterns_bad_1_circular() -> str:
    """AP2: definición circular."""
    return """---
title: "MVCC — definición circular"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: definición circular ('MVCC es un mecanismo de MVCC que…'). Falla AP2."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# MVCC — definición circular (anti-ejemplo)

## TL;DR

MVCC es un mecanismo de control de concurrencia que permite versiones
múltiples. {src:blk_a91f8e02c1d3}

## Definición formal (CIRCULAR)

MVCC es un MVCC que permite que múltiples versiones coexistan. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la definición de `## Definición formal` dice "MVCC es un mecanismo
de MVCC" — usa el término definido (MVCC) en su propia definición. Esto
viola AP2 (F100) y S1 (regex `\b(\w+)\s+es\s+(?:un|una)\s+\1\b`).
"""


def _antipatterns_bad_2_marketing() -> str:
    """AP9: marketing copiado."""
    return """---
title: "PostgreSQL: la solución que transforma la gestión de datos"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: marketing copiado ('solución innovadora que transforma su negocio'). Falla AP9."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# PostgreSQL: la solución que transforma la gestión de datos

## TL;DR

PostgreSQL es la solución innovadora que transforma su negocio.
Es la próxima generación de bases de datos. Líder del mercado en
el segmento enterprise. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL usa MVCC con `HeapTuple`. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la prosa tiene frases de marketing copiado ("solución
innovadora", "transforma su negocio", "próxima generación",
"líder del mercado") que no aportan dato. Esto viola AP9 (F100) y
S2 (regex contra lista cerrada).
"""


def _antipatterns_bad_3_bullet_dump() -> str:
    """AP8: volcado de viñetas (≥ 10 consecutivas sin prosa)."""
    return """---
title: "Lista de features de PostgreSQL (volcado)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 10 viñetas consecutivas sin prosa. Falla AP8."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Lista de features de PostgreSQL (volcado)

## Features

- índices B-tree
- índices hash
- índices GIN
- índices BRIN
- índices GiST
- índices SP-GiST
- particionado nativo
- logical replication
- physical replication
- synchronous replication
- slot-based replication
- cascading replication
- JSONB nativo
- tipos rango
- tipos geometría
- tipos vectores
- tipos enum
- tipos dominio

## Comentario del fixture

BAD: 18 viñetas consecutivas sin prosa intermedia (no hay párrafo entre
ellas). Esto viola AP8 (F100) y S3 (regex `^(\s*[-*]\s+.+\n){10,}`).
Solución: agrupar en 3 sub-secciones con párrafo introductorio cada una.
"""


def _antipatterns_bad_4_link_no_context() -> str:
    """AP7: enlace sin contexto."""
    return """---
title: "Enlaces sin contexto"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: enlaces [[note:id]] sin frase introductoria. Falla AP7."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Enlaces sin contexto

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. {src:blk_a91f8e02c1d3}

## Ver también

[[note:vacuum]]

[[note:transactions]]

[[note:heap-tuple]]

## Comentario del fixture

BAD: cada `[[note:id]]` aparece como ítem de una lista, sin frase
introductoria de ≥ 5 palabras antes. Esto viola AP7 (F100) y S4
(regex contra frase introductoria ausente). {src:blk_a91f8e02c1d3}
"""


def _antipatterns_bad_5_transcription() -> str:
    """AP1: transcripción disfrazada de resumen."""
    return """---
title: "Resumen que copia el SDM"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: '## Resumen' copia ≥ 50% de un párrafo del SDM verbatim. Falla AP1."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Resumen que copia el SDM

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Resumen (TRANSCRIPCIÓN)

PostgreSQL implementa MVCC con HeapTuple visible/no visible por
xmin/xmax en cada fila. Un UPDATE no modifica la fila: inserta una
nueva versión y marca la anterior como borrada. Un VACUUM recicla
las versiones sin referencias. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: el `## Resumen` copia verbatim un párrafo del SDM (3 oraciones
seguidas con palabras idénticas al SDM). Esto viola AP1 (F100) y S5
(coincidencia literal ≥ 50%). Solución: reescribir con la técnica de
F98 §4 (enumerar unidades → reescribir).
"""


def _antipatterns_bad_6_empty_section() -> str:
    """AP12: sección vacía."""
    return """---
title: "Sección vacía"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: sección ## Pendiente con 1 línea trivial. Falla AP12."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Sección vacía

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Pendiente

Esta sección está en construcción. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la sección `## Pendiente` tiene 1 línea trivial (< 30 caracteres)
que no añade contenido. Esto viola AP12 (F100) y S8 (regex contra
H2 + párrafo trivial). Solución: eliminar la sección hasta tener
contenido sustantivo.
"""


def _write_note(filename: str, content: str, force: bool) -> bool:
    path = NOTES_DIR / filename
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="regenera aunque exista")
    args = parser.parse_args()

    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    skipped = []
    for filename, fn in (
        ("antipatterns-clean.md", _antipatterns_clean),
        ("antipatterns-bad-1-circular.md", _antipatterns_bad_1_circular),
        ("antipatterns-bad-2-marketing.md", _antipatterns_bad_2_marketing),
        ("antipatterns-bad-3-bullet-dump.md", _antipatterns_bad_3_bullet_dump),
        ("antipatterns-bad-4-link-no-context.md", _antipatterns_bad_4_link_no_context),
        ("antipatterns-bad-5-transcription.md", _antipatterns_bad_5_transcription),
        ("antipatterns-bad-6-empty-section.md", _antipatterns_bad_6_empty_section),
    ):
        if _write_note(filename, fn(), args.force):
            created.append(filename)
        else:
            skipped.append(filename)

    for n in created:
        print(f"[create] notes/{n}")
    for n in skipped:
        print(f"[skip]   notes/{n} (ya existe; use --force para regenerar)")
    print(f"\nTotal: {len(created)} creadas, {len(skipped)} omitidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
