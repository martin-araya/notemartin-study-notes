---
title: "Errores propios — postgresql"
domain: postgresql
note-type: error-log
status: published
summary: "Registro de errores fixture para postgresql."
reading-time-minutes: 1
tags: [study/errors, domain/postgresql]
retrieved: 2026-09-30
source-self: "Living-doc meta-documental; no se publica como nota de conocimiento (F103 §1)."
---

# Errores propios — postgresql

## Resumen de errores

Living-doc de errores fixture para postgresql.

## Errores registrados

### Error PG-001

#### Concepto

MVCC y snapshot isolation.

#### Comando erróneo

:::code
psql -h 127.0.0.1 -p 5432 -U postgres
:::

#### Corrección

:::code
sudo systemctl start postgresql
:::

PostgreSQL no escuchaba en TCP/IP. {src:blk_test}

Nota canónica: [[note:pg-mvcc]].

#### Origen

Fecha del error: 2026-09-10.

#### Repaso

Próximo repaso: review-next: 2026-08-15. Tarjeta prioritaria: sí.

### Error PG-002

#### Concepto

Restauración con pg_restore.

#### Comando erróneo

:::code
pg_restore -d new_app backup.backup
:::

#### Corrección

:::code
createdb new_app
pg_restore -d new_app backup.backup
:::

Hay que crear la base primero. {src:blk_test}

Nota canónica: [[note:pg-restore]].

#### Origen

Fecha del error: 2026-09-12.

#### Repaso

Próximo repaso: review-next: 2026-09-25. Tarjeta prioritaria: sí.
