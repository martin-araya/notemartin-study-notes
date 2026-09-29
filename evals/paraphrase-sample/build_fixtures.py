#!/usr/bin/env python3
"""Generador de fixtures para la Fase 98 — `paraphrase`.

Produce 6 artefactos en `evals/paraphrase-sample/`:

  Corpus (fuentes del SDM):
    corpus/source-1-oracle.txt       — párrafo con 5 unidades (1 mensaje
                                        de error, 1 enumeración de 5,
                                        2 definiciones, 1 comando).
    corpus/source-2-kubernetes.txt   — párrafo con 1 mensaje de error,
                                        1 enumeración de 4, 1 sintaxis,
                                        1 warning de seguridad.
    corpus/source-3-postgresql.txt   — párrafo con 1 enumeración de 7,
                                        1 default, 1 comando.

  Notas (parafraseos):
    notes/paraphrase-good-1.md            — parafraseo CORRECTO de
                                             source-1 (cubre 5/5
                                             unidades, conserva literales).
    notes/paraphrase-bad-1-reformulated.md — parafraseo INCORRECTO con
                                              mensaje reformulado (falla V1).
    notes/paraphrase-bad-2-truncated.md   — parafraseo INCORRECTO con
                                             enumeración truncada (falla V2).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/paraphrase-sample/build_fixtures.py            # genera si no existe
    python3 evals/paraphrase-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_DIR = HERE / "corpus"
NOTES_DIR = HERE / "notes"


def _source_1_oracle() -> str:
    """Párrafo con 5 unidades: 1 mensaje de error, 1 enumeración de 5,
    2 definiciones, 1 comando."""
    return """\
Antes de Oracle RAC, las bases de datos monolíticas se caían cuando un
servidor fallaba, dejando a los clientes sin servicio. La solución
RAC (Real Application Clusters) introdujo 5 mecanismos de protección:
failover automático, load balancing, cache fusion, node affinity y
service registration. El comando para verificar el estado del cluster
es `srvctl status database -d ORCL`. Cuando un nodo falla, el error
reportado en el alert log es `ORA-29701: unable to connect to Cluster
Synchronization Service`. {src:blk_a91f8e02c1d3}
"""


def _source_2_kubernetes() -> str:
    """Párrafo con 1 mensaje de error, 1 enumeración de 4, 1 sintaxis,
    1 warning de seguridad."""
    return """\
Los pods de Kubernetes pueden fallar al iniciar por 4 motivos comunes:
imagen no encontrada, recursos insuficientes, configuración de probe
incorrecta, y volumen no montado. La firma del método `WaitForPodRunning`
es `func (c *Clientset) WaitForPodRunning(ctx context.Context, namespace,
name string, timeout time.Duration) error`. El warning de seguridad
del scheduler es `WARNING: pod has unbound immediate PersistentVolumeClaims`.
Si el pod no arranca, el error es `ImagePullBackOff`. {src:blk_1d3e8a92f7c4}
"""


def _source_3_postgresql() -> str:
    """Párrafo con 1 enumeración de 7, 1 default, 1 comando."""
    return """\
PostgreSQL soporta 7 tipos de replicación built-in: physical streaming,
logical streaming, synchronous, asynchronous, cascading, bidirectional
y slot-based. El default de `wal_level` es `replica`. El comando para
crear una replica slot es `SELECT pg_create_physical_replication_slot(
'standby_1');`. {src:blk_8c4d9e6f1a20}
"""


def _paraphrase_good_1() -> str:
    """Parafraseo CORRECTO de source-1: cubre las 5 unidades, conserva
    literales verbatim. El eval verifica cobertura V3."""
    return """\
---
title: "Parafraseo correcto (Oracle RAC)"
note-type: concept
status: draft
summary: "Parafraseo CORRECTO de la fuente source-1-oracle: 5/5 unidades cubiertas con literales verbatim."
reading-time-minutes: 2
tags: [type/paraphrase, domain/databases, f98/paraphrase, fixture/positive]
source: "evals/paraphrase-sample/corpus/source-1-oracle.txt"
source-type: docs
source-anchor: "section_path=/ch01/intro"
retrieved: 2026-09-28
---

# Parafraseo correcto (Oracle RAC)

Oracle RAC introduce 5 mecanismos para alta disponibilidad; el estado se
verifica con `srvctl status database -d ORCL`. {src:blk_a91f8e02c1d3}

## Problema

Antes de Oracle RAC, una base de datos monolítica dependía de un único
servidor; cuando ese servidor fallaba, el servicio se caía sin
redundancia. {src:blk_a91f8e02c1d3}

## Mecanismos

La solución RAC añade 5 mecanismos de protección: failover automático,
load balancing, cache fusion, node affinity y service registration. {src:blk_a91f8e02c1d3}

## Comando de verificación

Para consultar el estado del cluster se usa el comando
`srvctl status database -d ORCL`. {src:blk_a91f8e02c1d3}

## Error en alert log

Cuando un nodo falla, el alert log reporta el error
`ORA-29701: unable to connect to Cluster Synchronization Service`. {src:blk_a91f8e02c1d3}

## Verificación de cobertura (V3)

Tabla de unidades del original vs parafraseo para la técnica de
enumeración de unidades del F98 §4. {src:blk_a91f8e02c1d3}

| Unidad del original | ¿En el parafraseo? | Forma en el parafraseo |
|---|---|---|
| `ORA-29701: unable to connect to Cluster Synchronization Service` | sí | verbatim entre backticks |
| 5 mecanismos de protección | sí | lista explícita de 5 ítems |
| `failover automático` | sí | ítem 1 |
| `load balancing` | sí | ítem 2 |
| `cache fusion` | sí | ítem 3 |
| `node affinity` | sí | ítem 4 |
| `service registration` | sí | ítem 5 |
| `srvctl status database -d ORCL` | sí | verbatim |

Cobertura: 8/8 unidades = 100%. {src:blk_a91f8e02c1d3}
"""


def _paraphrase_bad_1_reformulated() -> str:
    """Parafraseo INCORRECTO con mensaje REFORMULADO (falla V1).

    El mensaje `ORA-29701: unable to connect to Cluster Synchronization Service`
    se reemplaza por una versión traducida y simplificada, lo cual viola INV-09.
    """
    return """\
---
title: "Parafraseo con mensaje reformulado (anti-ejemplo)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: el mensaje de error fue reformulado, perdiendo el literal."
reading-time-minutes: 1
tags: [type/paraphrase, domain/databases, f98/paraphrase, fixture/negative]
source: "evals/paraphrase-sample/corpus/source-1-oracle.txt"
source-type: docs
source-anchor: "section_path=/ch01/intro"
retrieved: 2026-09-28
---

# Parafraseo con mensaje reformulado (anti-ejemplo)

Antes de Oracle RAC, una base de datos podía caerse con un solo servidor.
RAC añade mecanismos de protección y comando de verificación. {src:blk_b12c44f0a8e7}

## Error reformulado (ANTICIPADA)

Cuando un nodo falla, el alert log reporta un error indicando que no se
pudo conectar al servicio de sincronización del cluster. {src:blk_b12c44f0a8e7}

## Comentario del fixture

BAD: el mensaje original `ORA-29701: unable to connect to Cluster
Synchronization Service` fue REFORMULADO a "no se pudo conectar al
servicio de sincronización del cluster". Esto viola INV-09 (L1
mensajes de error verbatim). {src:blk_b12c44f0a8e7}
"""


def _paraphrase_bad_2_truncated() -> str:
    """Parafraseo INCORRECTO con enumeración TRUNCADA (falla V2).

    La enumeración de 4 motivos en source-2 termina en `etc.` en el
    parafraseo, perdiendo los ítems 3 y 4.
    """
    return """\
---
title: "Parafraseo con enumeración truncada (anti-ejemplo)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: la enumeración de 4 motivos termina en 'etc.', perdiendo 2 ítems."
reading-time-minutes: 1
tags: [type/paraphrase, domain/networking, f98/paraphrase, fixture/negative]
source: "evals/paraphrase-sample/corpus/source-2-kubernetes.txt"
source-type: docs
source-anchor: "section_path=/ch02/pods"
retrieved: 2026-09-28
---

# Parafraseo con enumeración truncada (anti-ejemplo)

Los pods de Kubernetes pueden fallar al iniciar por motivos comunes
(imagen no encontrada, recursos insuficientes, etc.) y errores de
configuración. {src:blk_5e7f0a3b2c19}

## Enumeración truncada (ANTICIPADA)

Los motivos por los que un pod puede fallar son:
- imagen no encontrada
- recursos insuficientes
- etc.

## Comentario del fixture

BAD: la enumeración original tiene 4 motivos. El parafraseo lista 2
+ `etc.`, perdiendo los motivos 3 (configuración de probe) y 4
(volumen no montado). Esto viola INV-10 y F98 §5.2. {src:blk_5e7f0a3b2c19}
"""


def _write(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--force", action="store_true", help="regenera aunque exista")
    args = parser.parse_args()

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        (CORPUS_DIR / "source-1-oracle.txt", _source_1_oracle),
        (CORPUS_DIR / "source-2-kubernetes.txt", _source_2_kubernetes),
        (CORPUS_DIR / "source-3-postgresql.txt", _source_3_postgresql),
        (NOTES_DIR / "paraphrase-good-1.md", _paraphrase_good_1),
        (NOTES_DIR / "paraphrase-bad-1-reformulated.md", _paraphrase_bad_1_reformulated),
        (NOTES_DIR / "paraphrase-bad-2-truncated.md", _paraphrase_bad_2_truncated),
    ]

    created = []
    skipped = []
    for path, fn in fixtures:
        if _write(path, fn(), args.force):
            created.append(path.name)
        else:
            skipped.append(path.name)

    for n in created:
        print(f"[create] {n}")
    for n in skipped:
        print(f"[skip]   {n} (ya existe; use --force para regenerar)")
    print(f"\nTotal: {len(created)} creadas, {len(skipped)} omitidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
