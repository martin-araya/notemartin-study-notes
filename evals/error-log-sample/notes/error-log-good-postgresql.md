---
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
