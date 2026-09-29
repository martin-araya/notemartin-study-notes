#!/usr/bin/env python3
"""Generador de fixtures para la Fase 99 — `voice-style`.

Produce 6 notas NoteMark en `evals/voice-style-sample/notes/`:

  - `style-good-1.md`           — note `concept` PostgreSQL con todas las
                                  reglas R1-R8 aplicadas.
  - `style-good-2.md`           — note `procedure` Kubernetes con segunda
                                  persona, voz activa, frases ≤ 25
                                  palabras.
  - `style-bad-1-passive.md`    — note con ≥ 30% frases en voz pasiva
                                  (falla R2 → S2).
  - `style-bad-2-adjectives.md` — note con ≥ 5 adjetivos valorativos
                                  (falla R3 → S3).
  - `style-bad-3-long.md`       — note con ≥ 50% frases > 25 palabras
                                  (falla R1 → S1).
  - `style-bad-4-mixed.md`      — note con mezcla de tiempos verbales
                                  (falla R6 → S6).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/voice-style-sample/build_fixtures.py            # genera si no existe
    python3 evals/voice-style-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _style_good_1() -> str:
    return """---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
tags: [type/concept, domain/databases, f78/concept, f99/voice-style]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:transactions]]"
---

# MVCC en PostgreSQL

PostgreSQL usa MVCC para evitar locks de lectura. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot. Cada fila lleva `xmin` y `xmax`.
Los lectores ven filas cuyo rango cae dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores usaban locks de tabla. Un `SELECT` largo
bloqueaba todas las inserciones. Un reporte diario competía con la
carga OLTP. {src:blk_a91f8e02c1d3}

## Definición formal

Para una transacción `T` con snapshot en `S(T)` y una fila `R`,
la fila es visible si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a91f8e02c1d3}

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Cada fila lleva dos marcas
de versión. Un `UPDATE` no borra la fila: inserta una nueva versión.
`VACUUM` recicla las versiones sin referencias activas. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

- MVCC sustituye locks de lectura por marcas de versión. {src:blk_a91f8e02c1d3}
- Cada transacción ve un snapshot estable. {src:blk_a91f8e02c1d3}
- `VACUUM` libera versiones viejas. {src:blk_a91f8e02c1d3}

## Backlinks

Notas relacionadas para profundizar en los componentes de MVCC. {src:blk_a91f8e02c1d3}

- [[note:vacuum]] — reciclaje de versiones.
- [[note:transactions]] — modelo transaccional ACID.
"""


def _style_good_2() -> str:
    return """---
title: "Verificar pods de Kubernetes con kubectl"
note-type: procedure
status: published
summary: "Procedimiento para listar y describir pods en un namespace."
reading-time-minutes: 2
tags: [type/procedure, domain/networking, f80/procedure, f99/voice-style]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch02/pods"
retrieved: 2026-09-29
product: "Kubernetes"
product-version: "1.29"
related: "[[note:kubectl-get]]"
---

# Verificar pods de Kubernetes con kubectl

Lista los pods de un namespace y describe uno concreto para diagnosticar
su estado. {src:blk_b12c44f0a8e7}

## Procedimiento

Ejecuta `kubectl get pods -n <namespace>` para listar los pods. {src:blk_1d3e8a92f7c4}
Copia el nombre del pod que quieras inspeccionar. Después ejecuta
`kubectl describe pod <nombre> -n <namespace>` para ver eventos y estado.
{src:blk_5e7f0a3b2c19}

Si el pod no aparece en la lista, comprueba el namespace con
`kubectl config view --minify --output 'jsonpath={..namespace}'`.
{src:blk_8c4d9e6f1a20}

## Limpieza

> No requiere limpieza: `kubectl get` y `kubectl describe` son operaciones
> de solo lectura. {src:blk_a7b8c9d0e1f2}

## Verificación

Verás eventos al final del output. Si hay `ImagePullBackOff`, revisa
el nombre de la imagen. Si hay `CrashLoopBackOff`, ejecuta
`kubectl logs <pod> -n <namespace>` para inspeccionar el error.
{src:blk_6b7c8d9e0f1a}
"""


def _style_bad_1_passive() -> str:
    """≥ 30% frases en voz pasiva (falla R2)."""
    return """---
title: "Tabla es creada por el usuario (pasiva)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 30% frases en voz pasiva. Falla R2 (voz activa)."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Tabla es creada por el usuario (pasiva)

## TL;DR

La tabla es creada por el usuario con `CREATE TABLE`. La fila es marcada
por la transacción con `xmin`. La versión vieja es reciclada por
`VACUUM`. El resultado es devuelto al cliente.

## Mecanismo

La operación es ejecutada por el motor. El plan es generado por el
optimizador. El resultado es enviado al cliente. La conexión es
gestionada por el pool. {src:blk_a91f8e02c1d3}
"""


def _style_bad_2_adjectives() -> str:
    """≥ 5 adjetivos valorativos (falla R3)."""
    return """---
title: "PostgreSQL: herramienta poderosa y elegante"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 5 adjetivos valorativos. Falla R3."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# PostgreSQL: herramienta poderosa y elegante

## TL;DR

PostgreSQL es una herramienta poderosa y elegante. Su motor robusto
ofrece una solución simple e increíble para datos complejos. Es
imprescindible para cualquier proyecto serio.

## Problema

Antes, los sistemas legacy eran lentos y brutales. Hoy, con esta
herramienta mágica, todo es más rápido y sencillo. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC de forma robusta y elegante. El optimizador
es poderoso. El motor es top del mercado.
"""


def _style_bad_3_long() -> str:
    """≥ 50% frases > 25 palabras (falla R1)."""
    return """---
title: "Frases largas (long-sentences)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 50% de frases superan 25 palabras. Falla R1."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Frases largas (long-sentences)

## TL;DR

PostgreSQL usa MVCC para que múltiples transacciones puedan leer y escribir al mismo tiempo sin bloquearse entre sí, lo cual mejora el throughput en cargas concurrentes. {src:blk_a91f8e02c1d3}

## Mecanismo

Cada fila lleva dos marcas de versión llamadas `xmin` y `xmax` que registran el id de la transacción que la creó y el id de la transacción que la reemplazó, respectivamente, y el optimizador las usa para decidir si una fila es visible para una transacción determinada. {src:blk_a91f8e02c1d3}

## Confirmación

El comando `BEGIN` abre el snapshot en ese instante, y cualquier
escritura posterior en otra transacción no afecta al lector hasta el
siguiente `BEGIN`, lo que se puede verificar con `psql` y dos sesiones
concurrentes.
"""


def _style_bad_4_mixed() -> str:
    """Mezcla de tiempos verbales (falla R6)."""
    return """---
title: "Tiempos mezclados (mixed-tenses)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: presente + pasado + futuro en la misma sección."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Tiempos mezclados (mixed-tenses)

## TL;DR

PostgreSQL crea la tabla. El usuario la modificó. La aplicación consultará
los datos. `VACUUM` libera espacio. El servidor responde a las
peticiones.

## Mecanismo

PostgreSQL crea cada fila con `xmin`. La transacción marcó la fila como
vieja. `VACUUM` reciclará las versiones. El cliente recibirá el resultado.
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
        ("style-good-1.md", _style_good_1),
        ("style-good-2.md", _style_good_2),
        ("style-bad-1-passive.md", _style_bad_1_passive),
        ("style-bad-2-adjectives.md", _style_bad_2_adjectives),
        ("style-bad-3-long.md", _style_bad_3_long),
        ("style-bad-4-mixed.md", _style_bad_4_mixed),
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
