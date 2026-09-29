#!/usr/bin/env python3
"""Generador de fixtures para la Fase 94 — `intuition-first`.

Produce 3 notas NoteMark en `evals/intuition-first-sample/notes/`:

  - `db-mvcc.md`         — concepto de base de datos (PostgreSQL MVCC), 5 etapas.
  - `net-tcp-3whs.md`    — concepto de redes (TCP three-way handshake), 5 etapas.
  - `ref-pure-config.md` — api-reference con excepción `reference-pure` (2 etapas
                            + bloque `## Notas` con cita literal).

El script es idempotente y no genera los archivos si ya existen a menos que se
pase `--force`. Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/intuition-first-sample/build_fixtures.py            # genera si no existe
    python3 evals/intuition-first-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _db_mvcc() -> str:
    return """---
title: "MVCC"
note-type: concept
status: published
summary: "Control de concurrencia multiversión en PostgreSQL: cada fila lleva marcas de versión y los lectores ven un snapshot estable sin locks."
reading-time-minutes: 6
tags: [type/concept, domain/databases, f78/concept, f94/intuition-first]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
source-url: ""
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:pg_dump]], [[note:transactions]]"
---

# MVCC

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. El contenido principal sigue el patrón de 5 etapas
> definido por `references/06-writing/intuition-first.md` (F94).

## TL;DR

MVCC da a cada transacción un snapshot en su `BEGIN`; cada fila lleva
`xmin` y `xmax`, y la fila solo es visible si su versión cae dentro del
snapshot del lector. No hay locks de lectura.

## Problema

Antes de MVCC, los motores como MySQL con MyISAM o PostgreSQL ≤ 8 usaban
locks de tabla para que un `SELECT` no viera escrituras concurrentes. Eso
provocaba que un `pg_dump` bloqueara todas las inserciones de un e-commerce
durante minutos, y que un reporte diario compitiera con la carga OLTP. {src:blk_a3f1}

## Intuición

En lugar de "copia la fila y bloquéala hasta que termine la lectura", MVCC le
da a cada transacción un **snapshot**: cada fila lleva dos marcas de versión,
`xmin` y `xmax`, y el lector solo ve las filas cuyo rango cae dentro de su
snapshot. [[term:mvcc]]

## Analogía

Imagina una biblioteca donde cada libro tiene una tarjeta de préstamo con
fecha de inicio y fecha de fin. Para saber si un libro está disponible, miras
la tarjeta en el instante en que entras: si tu instante está dentro del
rango, lo tienes; si no, ya se fue. :::derived
**Dónde se rompe:** la biblioteca no acumula copias; MVCC sí, la fila vieja
se conserva en disco hasta el `VACUUM`.

## Definición formal

Para una transacción `T` con snapshot en `S(T)` y una fila `R` con versiones
`[xmin_R, xmax_R]`:

- `R` es visible para `T` si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a3f1}
- El `xmax` lo fija la transacción que borra o reemplaza la fila. {src:blk_a3f1}
- `VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a3f1}

:::equation
visible(T, R) := xmin_R < S(T) ∧ (xmax_R = ∞ ∨ xmax_R > S(T))
:::

:::diagram
flowchart LR
    T[Transacción T] -->|snapshot S T| V{visible T R}
    V -->|sí| Visible[Lectura visible]
    V -->|no| Hidden[Lectura oculta]
:::

## Confirmación

En PostgreSQL 16, `BEGIN; SELECT * FROM accounts WHERE id = 1;` abre el
snapshot en ese instante. Una transacción concurrente que ejecuta
`UPDATE accounts SET balance = 0 WHERE id = 1; COMMIT;` después no afecta
al lector hasta su próximo `BEGIN`. {src:blk_a3f1}

## Trampas

:::warning
**Falsa suposición de visibilidad inmediata.** Un escritor que ejecuta
`UPDATE` y `COMMIT` puede no ser visible para un lector que abrió
transacción antes del commit. Causa: el snapshot del lector se fija en su
`BEGIN`. Evitación: usa `READ COMMITTED` y reintenta la lectura, o acepta
la latencia del snapshot.
:::

## Resumen

- MVCC sustituye locks de lectura por marcas de versión por fila. {src:blk_a3f1}
- Cada transacción ve un snapshot estable en su `BEGIN`. {src:blk_a3f1}
- `VACUUM` libera versiones viejas. {src:blk_a3f1}

## Cuándo NO usarlo

- Si la carga es 99% escritura con cardinalidad reducida (las versiones
  se acumulan rápido y `VACUUM` se vuelve costoso). Alternativa: lock
  pesimista explícito. {external}

## Límites y alternativas

| Concepto | [[note:vacuum]] | Lock pesimista explícito (`SELECT FOR UPDATE`) |
|---|---|---|
| Visibilidad de versiones | sí (con `VACUUM`) | n/a |
| Latencia de lectura | estable | variable (locks) |

## Relacionados

- [[note:transactions]] — prerrequisito (qué es una transacción).
- [[note:vacuum]] — derivado (recolector de versiones).
- [[note:pg_dump]] — caso de uso (no bloquea lecturas por MVCC).

## Backlinks

- [[note:transactions]]
- [[note:vacuum]]

## Queries

```dataview
LIST FROM [[note:mvcc]] AND -"templates"
```
"""


def _net_tcp_3whs() -> str:
    return """---
title: "TCP three-way handshake"
note-type: concept
status: published
summary: "Apertura de conexión TCP en tres mensajes: SYN, SYN+ACK y ACK, donde cada lado confirma que puede enviar y recibir."
reading-time-minutes: 5
tags: [type/concept, domain/networking, f78/concept, f94/intuition-first]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/connection-establishment"
source-url: ""
retrieved: 2026-09-28
product: "TCP"
product-version: "RFC 9293"
related: "[[note:tcp-states]], [[note:isn]]"
---

# TCP three-way handshake

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

El handshake TCP son tres mensajes: el cliente envía SYN, el servidor
responde SYN+ACK y el cliente cierra con ACK. Tras los tres, ambos lados
saben que pueden enviar y recibir.

## Problema

Antes del handshake de tres pasos, los primeros protocolos (ej. TFTP sobre
datagrama único) abrían una conexión enviando datos directamente. El problema
es que un datagrama de petición podía ser duplicado por la red y el servidor
entregaba el archivo dos veces si lo procesaba dos veces. {src:blk_b712}

## Intuición

La conexión TCP necesita probar que ambos lados pueden enviar y recibir en
ese instante. Eso requiere tres mensajes: el cliente dice "quiero hablar"
(SYN), el servidor reconoce y propone parámetros (SYN+ACK), y el cliente
reconoce a su vez (ACK). [[term:three-way-handshake]]

## Analogía

Como una llamada telefónica: tú marcas mi número, yo descuelgo y digo
"¿Hola?", tú dices "Hola, soy yo". Solo después de los tres "habla" sabemos
que los dos podemos oír y ser oídos. :::external
**Dónde se rompe:** en una llamada no se negocian números de secuencia;
TCP sí, porque los paquetes pueden llegar fuera de orden.

## Definición formal

Estados y transiciones del cliente:

| Estado cliente | Evento | Estado siguiente | Envía |
|---|---|---|---|
| CLOSED | enviar SYN | SYN-SENT | SYN seq=ISN_c |
| SYN-SENT | recibir SYN+ACK, enviar ACK | ESTABLISHED | ACK seq=ISN_c+1, ack=ISN_s+1 |
| ESTABLISHED | datos | ESTABLISHED | — |

{src:blk_b712}

:::equation
SYN:        cliente → servidor, seq = ISN_c
SYN+ACK:    servidor → cliente, seq = ISN_s, ack = ISN_c + 1
ACK:        cliente → servidor, seq = ISN_c + 1, ack = ISN_s + 1
:::

## Confirmación

`tcpdump -i any -nn -S port 80` durante `curl https://example.com` muestra
las tres líneas con flags `S`, `S.`, `.` (SYN, SYN+ACK, ACK) en orden. {src:blk_b712}

## Trampas

:::warning
**SYN flood.** Un atacante envía SYN sin completar el ACK. El servidor
acumula estado en SYN-RECEIVED hasta el timeout. Causa: el handshake
asimétrico expone al servidor a DoS. Evitación: SYN cookies o rate limit.
:::

## Resumen

- TCP abre conexión en 3 mensajes para confirmar envío + recepción en ambos lados. {src:blk_b712}
- Los números de secuencia iniciales (ISN) se negocian en los dos primeros mensajes. {src:blk_b712}

## Cuándo NO usarlo

- Cuando se necesita transferencia sin handshake (TFTP, QUIC 0-RTT). {external}

## Límites y alternativas

| Mecanismo | [[note:tcp-states]] | QUIC 0-RTT |
|---|---|---|
| Mensajes de apertura | 3 | 0-1 |
| Confirma envío + recepción | sí | parcial |

## Relacionados

- [[note:tcp-states]] — derivado (transiciones de estado).
- [[note:isn]] — prerrequisito (números de secuencia iniciales).

## Backlinks

- [[note:tcp-states]]

## Queries

```dataview
LIST FROM [[note:tcp-three-way-handshake]] AND -"templates"
```
"""


def _ref_pure_config() -> str:
    """Fixture `reference-pure`: nota `api-reference` de un parámetro.

    Aplica la excepción acotada (§4) con los 4 checks cumplidos:
      R1 = use_case_profile == "reference-pure"
      R2 = note-type = api-reference (≠ concept)
      R3 = unidad atómica: describe QUÉ ES y CÓMO SE USA, no POR QUÉ
      R4 = la fuente no contiene ejemplo ejecutable adyacente

    Solo aparecen `## Problema` (opcional, breve) + `## Definición formal`
    (obligatoria) + `## Notas` (cita literal que descarta la intuición).
    """
    return """---
title: "max_connections (PostgreSQL)"
note-type: api-reference
status: published
summary: "Parámetro GUC de PostgreSQL que limita el número máximo de conexiones concurrentes al servidor."
reading-time-minutes: 2
tags: [type/api-reference, domain/databases, f79/api-reference, f94/reference-pure]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=42,section_path=/ch20/runtime-config/connections"
source-url: ""
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:connection-pooling]]"
---

# max_connections (PostgreSQL)

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota aplica la excepción `reference-pure` de
> `references/06-writing/intuition-first.md` §4: nota tipo `api-reference`,
> perfil `reference-pure`, unidad atómica sin motivación pedagógica.

## Problema

`max_connections` responde a la pregunta operacional: ¿cuántas conexiones
concurrentes acepta el servidor antes de rechazar nuevas con `FATAL: sorry,
too many clients already`? {src:blk_c0d2}

## Definición formal

| Campo | Valor |
|---|---|
| Tipo | `integer` |
| Default | `100` |
| Rango | `1` – `262143` |
| Reinicio | sí (recargar `postgresql.conf` + `pg_reload_conf()` no aplica; requiere restart) |

{src:blk_c0d2}

Si `max_connections` se incrementa por encima del valor por defecto,
debe ajustarse también `shared_buffers`, `work_mem` y los límites del
kernel (`max_connections × ~10 MB ≈ RAM esperada). {src:blk_c0d2}

## Notas

> "The default is typically chosen to avoid exhausting the system
> resources; PostgreSQL does not enforce a connection pool and expects
> pooling at the application or middleware layer." — PostgreSQL 16
> Server Administration, §19.4.1.

La fuente no ofrece una motivación pedagógica del parámetro (por qué se
eligió 100 como default, ni por qué el rango superior es 262143). Por
ello, esta nota aplica la **excepción `reference-pure`** (F94 §4) con
los 4 checks cumplidos: `use_case_profile == "reference-pure"`,
`note-type == "api-reference"` (≠ `concept`), unidad atómica sin
analogía razonable sin inventar, y la fuente no contiene ejemplo
ejecutable adyacente. Las etapas `## Intuición`, `## Analogía` y
`## Confirmación` se omiten conforme a la regla F94 §4 R1-R4.

## Resumen

- `max_connections` limita conexiones concurrentes; default 100, rango 1-262143. {src:blk_c0d2}
- Incrementar el valor exige revisar `shared_buffers` y `work_mem`. {src:blk_c0d2}

## Relacionados

- [[note:connection-pooling]] — prerrequisito operativo.

## Backlinks

- [[note:connection-pooling]]

## Queries

```dataview
LIST FROM [[note:max-connections]] AND -"templates"
```
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
        ("db-mvcc.md", _db_mvcc),
        ("net-tcp-3whs.md", _net_tcp_3whs),
        ("ref-pure-config.md", _ref_pure_config),
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
