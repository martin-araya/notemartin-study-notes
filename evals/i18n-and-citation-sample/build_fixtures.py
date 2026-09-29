#!/usr/bin/env python3
"""Generador de fixtures para la Fase 101 — `i18n-and-citation`.

Produce 6 notas NoteMark en `evals/i18n-and-citation-sample/notes/`:

  - `i18n-good-1-es.md`            — nota `concept` PostgreSQL en español,
                                      con bloque de procedencia completo
                                      y ≥ 2 términos verbatim.
  - `i18n-good-2-es-en.md`         — nota `concept` TCP en bilingüe
                                      español-primario, con primera
                                      aparición `[[en:three-way-handshake]]`
                                      y glosario al pie.
  - `i18n-good-3-citation.md`      — nota con bloque de procedencia
                                      completo (4 campos).
  - `i18n-bad-1-translated.md`     — nota con `--max-conexiones` traducido
                                      (falla C1 / S1).
  - `i18n-bad-2-no-citation.md`    — nota sin bloque `## Procedencia`
                                      (falla C4 / S4).
  - `i18n-bad-3-no-bilingual.md`   — nota bilingüe sin marcas
                                      `[[en:]]` / `[[es:]]`
                                      (falla C2 / S2).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/i18n-and-citation-sample/build_fixtures.py            # genera si no existe
    python3 evals/i18n-and-citation-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _i18n_good_1_es() -> str:
    return """---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
language: es
tags: [type/concept, domain/databases, f78/concept, f101/i18n]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16.3"
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

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Configuración

El parámetro `--max-connections` controla el número máximo de conexiones
concurrentes al servidor PostgreSQL. Por defecto, el valor es `100` y el
rango válido es `1` a `262143`. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

## Backlinks

Notas relacionadas para profundizar en los componentes de MVCC. {src:blk_a91f8e02c1d3}

- [[note:vacuum]] — reciclaje de versiones.
- [[note:transactions]] — modelo transaccional ACID.

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 Server Administration · docs |
| **Versión** | PostgreSQL 16.3 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `page=37,section_path=/ch13/concurrency` |

Notas:
- El bloque complementa el frontmatter `source`, `source-type`,
  `source-anchor`, `retrieved`. {src:blk_a91f8e02c1d3}
- Frontmatter es metadata para máquinas; este bloque es metadata para
  humanos que no abren el YAML. {src:blk_a91f8e02c1d3}
- Si el campo URL/anchor es privado, se sustituye por `local: archivo
  /path/al/libro.pdf, capítulo 13`. {src:blk_a91f8e02c1d3}

## Backlinks

Para profundizar en el reciclaje de versiones, consulta [[note:vacuum]].
Para entender el modelo transaccional, consulta [[note:transactions]].
"""


def _i18n_good_2_es_en() -> str:
    return """---
title: "TCP three-way handshake"
note-type: concept
status: published
summary: "Apertura de conexión TCP en 3 pasos: SYN, SYN+ACK y ACK, donde cada lado confirma que puede enviar y recibir."
reading-time-minutes: 5
language: es-en
tags: [type/concept, domain/networking, f78/concept, f101/i18n]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/connection-establishment"
retrieved: 2026-09-29
product: "TCP"
product-version: "RFC 9293"
related: "[[note:tcp-states]], [[note:isn]]"
---

# TCP three-way handshake

La conexión TCP requiere probar que ambos lados pueden enviar y
recibir en ese instante ([[en:three-way-handshake]]). {src:blk_b12c44f0a8e7}

## TL;DR

El cliente envía SYN; el servidor responde SYN+ACK; el cliente cierra
con ACK. Tras los 3 mensajes, ambos lados saben que pueden enviar y
recibir. {src:blk_b12c44f0a8e7}

## Definición formal

Estados del cliente:

- `CLOSED` → enviar `SYN` → `SYN-SENT`
- `SYN-SENT` → recibir `SYN+ACK` y enviar `ACK` → `ESTABLISHED` {src:blk_b12c44f0a8e7}

## Mecanismo

TCP usa 3 mensajes para confirmar bidireccionalidad. Los números de
secuencia iniciales (ISN) se negocian en los dos primeros mensajes. {src:blk_b12c44f0a8e7}

## Glosario

| Término | ES | EN |
|---|---|---|
| `three-way-handshake` | Apertura de conexión TCP en 3 pasos | TCP three-way handshake |
| `isn` | Número de secuencia inicial | Initial Sequence Number |
| `syn` | Petición de sincronización | Synchronize |

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | IETF RFC 9293 · rfc |
| **Versión** | RFC 9293 (agosto 2022) |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/rfc9293/connection-establishment` |

## Backlinks

Notas relacionadas para profundizar en TCP. {src:blk_3f6b9d2e7c14}

- [[note:tcp-states]] — máquina de estados completa.
- [[note:isn]] — números de secuencia iniciales.
"""


def _i18n_good_3_citation() -> str:
    return """---
title: "Kubernetes pod lifecycle"
note-type: concept
status: published
summary: "Estados del ciclo de vida de un pod de Kubernetes: Pending, Running, Succeeded, Failed, Unknown."
reading-time-minutes: 3
language: en
tags: [type/concept, domain/networking, f78/concept, f101/i18n]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "section_path=/workloads/pods/pod-lifecycle"
retrieved: 2026-09-29
product: "Kubernetes"
product-version: "1.29"
related: "[[note:kubectl-get]]"
---

# Kubernetes pod lifecycle

A pod transitions through the phases Pending, Running, Succeeded,
Failed, and Unknown. {src:blk_1d3e8a92f7c4}

## TL;DR

A pod has 5 phases. `kubectl get pods` shows the current phase. The
most common failure is `ImagePullBackOff` or `CrashLoopBackOff`.
{src:blk_1d3e8a92f7c4}

## Definición formal

| Phase | Meaning |
|---|---|
| `Pending` | The Pod has been accepted but not all containers created |
| `Running` | At least one container is still running |
| `Succeeded` | All containers terminated successfully |
| `Failed` | At least one container terminated with non-zero exit |
| `Unknown` | State cannot be obtained | {src:blk_1d3e8a92f7c4}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | Kubernetes Workloads API Reference · docs |
| **Versión** | Kubernetes 1.29 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/workloads/pods/pod-lifecycle` |

## Backlinks

Note to inspect pod state from the command line. {src:blk_5e7f0a3b2c19}

- [[note:kubectl-get]]
"""


def _i18n_bad_1_translated() -> str:
    """AP1: parámetro CLI traducido."""
    return """---
title: "Conexiones máximas en PostgreSQL (parámetro traducido)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: parámetro --max-conexiones traducido. Falla AP1 / S1."
reading-time-minutes: 1
language: es
tags: [type/concept, domain/databases, f101/i18n, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=42"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Conexiones máximas (parámetro traducido)

## TL;DR

PostgreSQL limita las conexiones concurrentes con el parámetro
`--max-conexiones` (en lugar de `--max-connections`). {src:blk_a91f8e02c1d3}

## Definición formal

El parámetro `--max-conexiones` acepta un entero entre 1 y 262143. {src:blk_a91f8e02c1d3}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 Server Administration · docs |
| **Versión** | PostgreSQL 16 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `page=42,section_path=/runtime-config/connections` |

## Comentario del fixture

BAD: el parámetro CLI `--max-connections` se traduce como
`--max-conexiones`. Esto viola AP1 (F101) y S1 (regex contra lista
cerrada de 45 no-traducibles, §3.2 entrada 16).
"""


def _i18n_bad_2_no_citation() -> str:
    """AP2: bloque de procedencia ausente."""
    return """---
title: "Sin bloque de procedencia"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: sin bloque H2 de procedencia. Falla AP2 / S4."
reading-time-minutes: 1
language: es
tags: [type/concept, domain/databases, f101/i18n, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Sin bloque de procedencia

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot. {src:blk_a91f8e02c1d3}

## Definición formal

Una transacción ve solo las filas con `xmin < S(T)` y `xmax > S(T)`. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la nota no tiene la seccion H2 de procedencia con 4 campos. El frontmatter
tiene `source` y `retrieved`, pero el bloque para humanos esta ausente.
Esto viola AP2 (F101) y S4.
"""


def _i18n_bad_3_no_bilingual() -> str:
    """AP3 + AP4: nota bilingüe sin marcas `[[en:]]` ni glosario."""
    return """---
title: "Sin marcas bilingues"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: nota language: es-en sin marcas bilingues ni glosario. Falla AP3 + AP4."
reading-time-minutes: 1
language: es-en
tags: [type/concept, domain/networking, f101/i18n, fixture/negative]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/intro"
retrieved: 2026-09-29
product: "TCP"
product-version: "RFC 9293"
---

# Sin marcas bilingues

La conexion TCP requiere probar que ambos lados pueden enviar y recibir
en ese instante. {src:blk_b12c44f0a8e7}

## TL;DR

El cliente envia SYN; el servidor responde SYN+ACK; el cliente cierra
con ACK. {src:blk_b12c44f0a8e7}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | IETF RFC 9293 · rfc |
| **Versión** | RFC 9293 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `section_path=/rfc9293/intro` |
| {src:blk_b12c44f0a8e7}

## Comentario del fixture

BAD: la nota tiene language bilingue pero no usa las marcas de primera
aparicion ni tiene la seccion de glosario al pie.
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
        ("i18n-good-1-es.md", _i18n_good_1_es),
        ("i18n-good-2-es-en.md", _i18n_good_2_es_en),
        ("i18n-good-3-citation.md", _i18n_good_3_citation),
        ("i18n-bad-1-translated.md", _i18n_bad_1_translated),
        ("i18n-bad-2-no-citation.md", _i18n_bad_2_no_citation),
        ("i18n-bad-3-no-bilingual.md", _i18n_bad_3_no_bilingual),
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
