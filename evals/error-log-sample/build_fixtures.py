#!/usr/bin/env python3
"""Generador de fixtures para la Fase 103 — `error-log`.

Produce 6 living-docs en `evals/error-log-sample/notes/`:

  - `error-log-good-postgresql.md` — Living-doc positivo (3 errores
      completos con los 5 H3, `:::code` verbatim, `review-next`
      vencido en al menos una entrada, sin autocrítica).
  - `error-log-good-docker.md`     — Living-doc positivo (2 errores
      completos).
  - `error-log-bad-autocritica.md` — Negativo: entrada con "soy malo en X"
      (falla R-E5 / AP16).
  - `error-log-bad-no-fundamento.md` — Negativo: entrada sin `[[note:id]]`
      en `### Corrección` (falla R-E4).
  - `error-log-bad-no-repaso.md`   — Negativo: entrada sin `### Repaso`
      + `review-next` (falla R-E3).
  - `error-log-bad-verbatim-modificado.md` — Negativo: comando erróneo
      reformulado (no verbatim) en lugar de bloque `:::code` (falla R-E2).

Uso:
    python3 evals/error-log-sample/build_fixtures.py            # genera si no existe
    python3 evals/error-log-sample/build_fixtures.py --force    # regenera siempre
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NOTES_DIR = Path(__file__).resolve().parent / "notes"


def _good_postgresql() -> str:
    return """---
title: "Errores propios — PostgreSQL"
domain: postgresql
note-type: error-log
status: published
summary: "Registro de 3 errores propios de PostgreSQL: conexión TCP/IP, restauración sin DROP, MVCC snapshot."
reading-time-minutes: 2
tags: [study/errors, domain/postgresql]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — PostgreSQL

## Resumen de errores

Tres errores propios del dominio PostgreSQL: configuración de conexión,
restauración con `pg_restore`, y consulta bajo MVCC. Cada entrada enlaza
a su nota canónica para profundizar.

## Errores registrados

### Error POSTGRES-001

#### Concepto

MVCC y snapshot isolation.

#### Comando erróneo

:::code
psql -h 127.0.0.1 -p 5432 -U postgres
:::

Salida literal:

:::code
psql: error: connection to server at "127.0.0.1" (127.0.0.1), port 5432 failed: Connection refused
        Is the server running on that host and accepting TCP/IP connections?
:::

#### Corrección

:::code
sudo systemctl start postgresql
ss -tln | grep 5432
psql -h /var/run/postgresql -U postgres
:::

PostgreSQL no escuchaba en TCP/IP en la instalación por defecto; el socket
Unix funciona mientras se ajusta `listen_addresses`. {src:blk_c11f8e02c1d3}

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-10. Contexto: configurar acceso remoto a
PostgreSQL 16 tras instalar el paquete `postgresql-16`.

#### Repaso

Próximo repaso: review-next: 2026-08-15. Tarjeta prioritaria: sí.

### Error POSTGRES-002

#### Concepto

Restauración con `pg_restore` requiere base destino preexistente.

#### Comando erróneo

:::code
pg_restore -d new_app /tmp/backup.backup
:::

Salida literal:

:::code
pg_restore: error: could not connect to database "new_app": FATAL: database "new_app" does not exist
:::

#### Corrección

:::code
createdb new_app
pg_restore -d new_app /tmp/backup.backup
:::

`pg_restore` no crea la base destino; primero hay que crearla con
`createdb` o `CREATE DATABASE`. {src:blk_b11f8e02c1d3}

Nota canónica: [[note:pg-restore-flags#clean]].

#### Origen

Fecha del error: 2026-09-12. Contexto: restaurar backup de staging a
entorno local antes de una demo.

#### Repaso

Próximo repaso: review-next: 2026-09-30. Tarjeta prioritaria: sí.

### Error POSTGRES-003

#### Concepto

MVCC: lecturas bajo `READ COMMITTED` ven commits concurrentes.

#### Comando erróneo

:::code
BEGIN;
SELECT count(*) FROM orders;
-- T1 hace commit aquí
SELECT count(*) FROM orders;
:::

#### Corrección

:::code
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT count(*) FROM orders;
SELECT count(*) FROM orders;
:::

Bajo `READ COMMITTED`, cada `SELECT` ve un nuevo snapshot; para
estabilidad usar `REPEATABLE READ` o `SERIALIZABLE`. {src:blk_a91f8e02c1d3}

Nota canónica: [[note:isolation-levels#trade-offs]].

#### Origen

Fecha del error: 2026-09-14. Contexto: ejecutar un reporte agregado y
obtener conteos distintos entre dos `SELECT` consecutivos.

#### Repaso

Próximo repaso: review-next: 2026-10-05. Tarjeta prioritaria: sí.
"""


def _good_docker() -> str:
    return """---
title: "Errores propios — Docker"
domain: docker
note-type: error-log
status: published
summary: "Registro de 2 errores propios de Docker: permisos de socket y volumen nombrado faltante."
reading-time-minutes: 1
tags: [study/errors, domain/docker]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Docker

## Resumen de errores

Dos errores propios del dominio Docker: acceso al socket y volumen
nombrado no resuelto en compose.

## Errores registrados

### Error DOCKER-001

#### Concepto

Permisos del socket Unix de Docker.

#### Comando erróneo

:::code
docker ps
:::

Salida literal:

:::code
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
:::

#### Corrección

:::code
sudo usermod -aG docker $USER
newgrp docker
docker ps
:::

El usuario actual no está en el grupo `docker`; agregar y refrescar
la sesión. {src:blk_d11f8e02c1d3}

Nota canónica: [[note:docker-postinstall#permissions]].

#### Origen

Fecha del error: 2026-09-05. Contexto: configurar CI runner para
ejecutar pruebas de integración con Testcontainers.

#### Repaso

Próximo repaso: review-next: 2026-09-20. Tarjeta prioritaria: sí.

### Error DOCKER-002

#### Concepto

Volumen nombrado faltante en compose.

#### Comando erróneo

:::code
docker compose up web
:::

Salida literal:

:::code
Error response from daemon: create <<volume>>: volume not found
:::

#### Corrección

:::code
docker volume create app_data
docker compose up web
:::

Compose no crea volúmenes nombrados si la entrada `external: true`
está mal colocada; revisar `docker-compose.yml`. {src:blk_d12f8e02c1d3}

Nota canónica: [[note:docker-compose-volumes#external]].

#### Origen

Fecha del error: 2026-09-13. Contexto: levantar stack local con
PostgreSQL + API para reproducir un bug de producción.

#### Repaso

Próximo repaso: review-next: 2026-10-01. Tarjeta prioritaria: sí.
"""


def _bad_autocritica() -> str:
    return """---
title: "Errores propios — Mal ejemplo de autocrítica"
domain: bad
note-type: error-log
status: draft
summary: "Living-doc con lenguaje de evaluación personal — debe fallar AP16."
reading-time-minutes: 1
tags: [study/errors, domain/bad]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Mal ejemplo de autocrítica

## Resumen de errores

Una entrada con autocrítica.

## Errores registrados

### Error BAD-001

#### Concepto

No entiendo MVCC, soy malo en esto.

#### Comando erróneo

:::code
SELECT * FROM orders WHERE xmin < 100;
:::

#### Corrección

:::code
SELECT * FROM orders WHERE age(xmin) < '1 hour';
:::

La función `age()` es la forma idiomática. {src:blk_x11f8e02c1d3}

Nota canónica: [[note:mvcc-basics]].

#### Origen

Fecha del error: 2026-09-15. Contexto: intentando optimizar una
consulta.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.
"""


def _bad_no_fundamento() -> str:
    return """---
title: "Errores propios — Sin enlace canónico"
domain: nofund
note-type: error-log
status: draft
summary: "Living-doc sin enlace `[[note:id]]` en `### Corrección` — falla R-E4."
reading-time-minutes: 1
tags: [study/errors, domain/nofund]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Sin enlace canónico

## Resumen de errores

Una entrada sin enlace a nota canónica.

## Errores registrados

### Error NOFUND-001

#### Concepto

PostgreSQL escucha solo en localhost por defecto.

#### Comando erróneo

:::code
psql -h 0.0.0.0 -U postgres
:::

Salida literal:

:::code
psql: error: connection to server at "0.0.0.0" failed: Connection refused
:::

#### Corrección

:::code
psql -h 127.0.0.1 -U postgres
:::

PostgreSQL por defecto solo escucha en `localhost`.

#### Origen

Fecha del error: 2026-09-10. Contexto: configurar acceso desde otra
máquina.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.
"""


def _bad_no_repaso() -> str:
    return """---
title: "Errores propios — Sin Repaso"
domain: norepaso
note-type: error-log
status: draft
summary: "Living-doc sin `### Repaso` ni `review-next` — falla R-E3."
reading-time-minutes: 1
tags: [study/errors, domain/norepaso]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Sin Repaso

## Resumen de errores

Una entrada sin `### Repaso`.

## Errores registrados

### Error NOREP-001

#### Concepto

Snapshot isolation.

#### Comando erróneo

:::code
psql -h localhost
:::

#### Corrección

:::code
psql -h /var/run/postgresql
:::

Usar socket Unix cuando TCP/IP no está habilitado.

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-12. Contexto: configuración inicial.
"""


def _bad_verbatim_modificado() -> str:
    return """---
title: "Errores propios — Verbatim modificado"
domain: verbatim
note-type: error-log
status: draft
summary: "Living-doc con comando erróneo fuera de bloque :::code — falla R-E2."
reading-time-minutes: 1
tags: [study/errors, domain/verbatim]
retrieved: 2026-09-15
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — Verbatim modificado

## Resumen de errores

Una entrada con comando erróneo en prosa en lugar de bloque verbatim.

## Errores registrados

### Error VERBATIM-001

#### Concepto

Error de conexión.

#### Comando erróneo

Ejecuté psql con un host incorrecto, lo cual produjo un error de
conexión rechazada.

#### Corrección

:::code
psql -h 127.0.0.1 -U postgres
:::

Usar el host correcto.

Nota canónica: [[note:postgres-listen-addresses#tcp-vs-unix]].

#### Origen

Fecha del error: 2026-09-10. Contexto: configuración inicial.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.
"""


FIXTURES = {
    "error-log-good-postgresql.md": _good_postgresql,
    "error-log-good-docker.md": _good_docker,
    "error-log-bad-autocritica.md": _bad_autocritica,
    "error-log-bad-no-fundamento.md": _bad_no_fundamento,
    "error-log-bad-no-repaso.md": _bad_no_repaso,
    "error-log-bad-verbatim-modificado.md": _bad_verbatim_modificado,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_fixtures.py")
    parser.add_argument("--force", action="store_true",
                        help="regenera fixtures aunque existan")
    args = parser.parse_args(argv)

    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    for name, builder in FIXTURES.items():
        path = NOTES_DIR / name
        if path.exists() and not args.force:
            continue
        path.write_text(builder(), encoding="utf-8")
        print(f"[gen] {path.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
