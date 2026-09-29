#!/usr/bin/env python3
"""Generador de fixtures para la Fase 96 — `executable-examples`.

Produce 4 notas NoteMark en `evals/executable-examples-sample/notes/`:

  - `db-postgres-count.md`     — ejemplo DB (PostgreSQL SELECT count) con las 4
                                   secciones canónicas + entorno + limpieza.
  - `net-tcpdump-syn.md`       — ejemplo redes (tcpdump filtrando SYN).
  - `cli-docker-run.md`        — ejemplo CLI (docker run --rm) con limpieza
                                   justificada "no requiere limpieza".
  - `anti-missing-cleanup.md`  — ejemplo NEGATIVO sin limpieza (test de la
                                   señal D2 / C6 a propósito).

Sin dependencias externas. Python 3.9+ stdlib puro.

Uso:
    python3 evals/executable-examples-sample/build_fixtures.py            # genera si no existe
    python3 evals/executable-examples-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _db_postgres_count() -> str:
    return """---
title: "Conteo de relaciones en PostgreSQL"
note-type: concept
status: published
summary: "Ejemplo ejecutable de SELECT count sobre pg_class con las 4 secciones canónicas."
reading-time-minutes: 2
tags: [type/example, domain/databases, f78/concept, f96/executable-examples]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch03/catalog"
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:pg-class]]"
---

# Conteo de relaciones en PostgreSQL

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

`SELECT count(*) FROM pg_class WHERE relkind = 'r'` devuelve el número
de tablas y vistas materializadas del catálogo del sistema. {src:blk_a91f8e02c1d3}

> **Entorno:** PostgreSQL 16.3 · Ubuntu 24.04 LTS · psql 16.3 · DB seed `notemartin_demo` con 1000 tablas pre-cargadas vía `pg_dump`. {src:blk_c0d1e2f3a4b5}

Ejemplo reproducible basado en el manual de PostgreSQL 16. {src:blk_4f5a6b7c8d9e}

:::example
## Setup

Crea la tabla `accounts` con 3 filas de ejemplo para la verificación. {src:blk_b12c44f0a8e7}

```sql
-- {src:blk_e01b2c3d4e5f}
CREATE TEMP TABLE accounts (id int PRIMARY KEY, balance numeric);
INSERT INTO accounts VALUES (1, 100), (2, 50), (3, 75); -- {src:blk_9e8f7a6b5c4d}
```

## Acción

Cuenta las filas cuyo balance supera el umbral de 60. {src:blk_1d3e8a92f7c4}

```sql
-- {src:blk_f12c3d4e5a6b}
SELECT count(*) FROM accounts WHERE balance > 60; -- {src:blk_3d4e5f6a7b8c}
```

## Resultado

El conteo devuelve 1 fila (la cuenta 1 con balance 100). {src:blk_5e7f0a3b2c19}

```
-- {src:blk_a7b8c9d0e1f2}
 count
-------
     1
(1 row) -- {src:blk_6b7c8d9e0f1a}
```

## Limpieza

Borra la tabla temporal; las TEMP se eliminan al cerrar la sesión, pero la limpieza explícita documenta la intención. {src:blk_8c4d9e6f1a20}

```sql
-- {src:blk_b3c4d5e6f7a8}
DROP TABLE accounts; -- {src:blk_0c1d2e3f4a5b}
```
:::
"""


def _net_tcpdump_syn() -> str:
    return """---
title: "Captura de paquetes SYN con tcpdump"
note-type: concept
status: published
summary: "Ejemplo ejecutable de tcpdump filtrando SYN con captura verbatim y limpieza."
reading-time-minutes: 2
tags: [type/example, domain/networking, f78/concept, f96/executable-examples]
source: "evals/corpus/03-rfc-7231/sdm.json"
source-type: rfc
source-anchor: "section_path=/rfc9293/tcp-flags"
retrieved: 2026-09-28
product: "tcpdump"
product-version: "4.99"
related: "[[note:tcp-three-way-handshake]]"
---

# Captura de paquetes SYN con tcpdump

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

`tcpdump -i any -w captura.pcap 'tcp[tcpflags] & tcp-syn != 0'` filtra
los paquetes SYN y los guarda en un archivo para análisis posterior. {src:blk_3f6b9d2e7c14}

> **Entorno:** Linux kernel 6.8 · tcpdump 4.99 · iface `eth0` · permisos root (CAP_NET_RAW). {src:blk_a2b3c4d5e6f7}

Ejemplo reproducible basado en el RFC 9293. {src:blk_4f5a6b7c8d9e}

:::example
## Setup

Inicia `tcpdump` en background con el filtro SYN y guarda el PID. {src:blk_7a8e2c1b9d34}

```bash
# {src:blk_e01b2c3d4e5f}
sudo tcpdump -i eth0 -w /tmp/syn.pcap 'tcp[tcpflags] & tcp-syn != 0' &
TCPDUMP_PID=$!
```

## Acción

Genera una conexión TCP saliente que producirá el 3WHS. {src:blk_4e1f8a3c6b97}

```bash
# {src:blk_f12c3d4e5a6b}
curl -s https://example.com > /dev/null
```

## Resultado

Lectura del archivo pcap; deben verse las 3 fases del handshake (S, S., .). {src:blk_9b2d5e8f1c67}

```bash
# {src:blk_a7b8c9d0e1f2}
sudo tcpdump -r /tmp/syn.pcap 2>/dev/null | head -3
```

```
# {src:blk_6b7c8d9e0f1a}
Reading from file /tmp/syn.pcap, link-type EN10MB (Ethernet)
12:00:01.123 IP 192.168.1.10.54321 > 93.184.216.34.443: Flags [S], seq 12345
12:00:01.234 IP 93.184.216.34.443 > 192.168.1.10.54321: Flags [S.], seq 50000, ack 12346
12:00:01.235 IP 192.168.1.10.54321 > 93.184.216.34.443: Flags [.], ack 50001
```

## Limpieza

Termina `tcpdump` y elimina el archivo de captura. {src:blk_6c4a7b0e3d92}

```bash
# {src:blk_b3c4d5e6f7a8}
sudo kill $TCPDUMP_PID
sudo rm /tmp/syn.pcap
```
:::
"""


def _cli_docker_run() -> str:
    return """---
title: "Hello world con docker run --rm"
note-type: procedure
status: published
summary: "Ejemplo CLI de docker run con flag --rm para auto-eliminar el contenedor."
reading-time-minutes: 1
tags: [type/example, domain/cli, f80/procedure, f96/executable-examples]
source: "evals/corpus/07-docker-cli-ref/sdm.json"
source-type: docs
source-anchor: "page=8,section_path=/docker-run/quickstart"
retrieved: 2026-09-28
product: "Docker"
product-version: "27.0"
related: "[[note:docker-rm]]"
---

# Hello world con docker run --rm

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior.

## TL;DR

`docker run --rm alpine:3.19 echo "hello"` ejecuta un comando en un
contenedor efímero; `--rm` borra el contenedor al salir. {src:blk_2d5e8a3b7c91}

> **Entorno:** Docker 27.0 · Ubuntu 24.04 LTS · imagen `alpine:3.19` · usuario con permisos de docker (no requiere root en el host). {src:blk_a2b3c4d5e6f7}

Ejemplo reproducible basado en la referencia CLI de Docker. {src:blk_4f5a6b7c8d9e}

:::example
## Setup

Descarga la imagen alpine (idempotente, no-op si ya existe). {src:blk_8f1c4d9e6a03}

```bash
# {src:blk_e01b2c3d4e5f}
docker pull alpine:3.19
```

## Acción

Lanza el contenedor con `--rm` para auto-eliminarlo al terminar. {src:blk_5a7b2e0c4d96}

```bash
# {src:blk_f12c3d4e5a6b}
docker run --rm alpine:3.19 echo "hello from notemartin"
```

## Resultado

El comando imprime la cadena exacta y el contenedor se elimina al salir. {src:blk_3c8f1a5d9b27}

```
# {src:blk_a7b8c9d0e1f2}
hello from notemartin
```

## Limpieza

No requiere limpieza: la flag `--rm` borra el contenedor automáticamente. {src:blk_7b4e9c1a5d83}
:::
"""


def _anti_missing_cleanup() -> str:
    """Fixture NEGATIVO: ejemplo sin sección ## Limpieza.

    Sirve para que el eval verifique que la señal D2 / criterio C6 detecta
    correctamente la ausencia. La nota se evalúa con un check que debe
    FALLAR (test de regresión).
    """
    return """---
title: "Conteo sin limpieza (anti-ejemplo)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ejemplo ejecutable SIN sección ## Limpieza. Detecta la señal D2."
reading-time-minutes: 1
tags: [type/example, domain/databases, f96/executable-examples, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch03/catalog"
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:anti-pattern]]"
---

# Conteo sin limpieza (anti-ejemplo)

> Fixture NEGATIVO. No cumple el criterio #1 de F96 (ROADMAP). El eval
> debe reportar que **no** tiene `## Limpieza` ni "No requiere limpieza".

## TL;DR

Ejemplo con setup y acción, sin cleanup.

> **Entorno:** PostgreSQL 16.3 · Ubuntu 24.04 LTS · psql 16.3.

:::example
## Setup
```sql
CREATE TEMP TABLE junk (id int);
INSERT INTO junk VALUES (1);
```

## Acción
```sql
SELECT count(*) FROM junk;
```

## Resultado
```
 count
-------
     1
(1 row)
```
:::
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
        ("db-postgres-count.md", _db_postgres_count),
        ("net-tcpdump-syn.md", _net_tcpdump_syn),
        ("cli-docker-run.md", _cli_docker_run),
        ("anti-missing-cleanup.md", _anti_missing_cleanup),
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
