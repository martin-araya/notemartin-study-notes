---
title: "PostgreSQL — backup lógico con pg_dump y restore con pg_restore"
note-type: procedure
status: draft
summary: "Backup lógico de una BD PostgreSQL con pg_dump (custom format) y restore con pg_restore; reversible con drop+recreate y validable con conteo de filas."
tags: [type/procedure, domain/databases, product/postgresql]
source: "PostgreSQL 16 — pg_dump / pg_restore reference"
source-type: docs
source-anchor: "app-pgdump"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:pg-backup-strategies]]"
---

# PostgreSQL — backup lógico con pg_dump y restore con pg_restore

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Backup lógico de una BD PostgreSQL con pg_dump (custom format) y restore con pg_restore; reversible con drop+recreate y validable con conteo de filas. |
| **Procedencia** | PostgreSQL 16 — pg_dump / pg_restore reference (docs) §app-pgdump · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
Backup con `pg_dump -Fc` produce un archivo `.dump` comprimido; restore con `pg_restore -d <db>` reproduce esquema y datos. La operación `DROP DATABASE` previa al restore es destructiva y usa `:::danger`; el rollback es la importación a una base distinta. {src:blk_c000000a01b1}

{layer:l2}

## Objetivo
Generar un backup lógico de una base de datos PostgreSQL (esquema + datos) que pueda restaurarse en la misma instancia o en otra, validando integridad por conteo de filas. {src:blk_ddbbccddeefb}

## Aplicabilidad
El procedimiento aplica a bases PostgreSQL de tamaño medio donde un backup lógico es factible y suficiente; para casos mayores o requisitos de PITR hay alternativas más adecuadas.

- **SÍ:** bases de tamaño ≤ 100 GB; migraciones entre instancias; pre-upgrade de versión mayor; pre-migración de esquema. {src:blk_c000000a01b2}
- **NO:** bases > 100 GB (preferir `pg_basebackup` físico); bases con requisitos de PITR estricto (preferir WAL archiving + `pg_basebackup`); tablas sin PK ni `replica identity` (restaurar filas idénticas es trivial; restaurar cambios concurrentes no lo es). {src:blk_c000000a01b3}

## Precondiciones verificadas
Antes de iniciar, todas estas condiciones deben cumplirse. Cada una con su criterio de verificación ejecutable. {src:blk_c000000a01b4}

- Cliente `psql` ≥ 9.6 disponible: `psql --version` retorna string ≥ 9.6.
- Permisos: el rol que ejecuta `pg_dump` debe tener `SELECT` sobre todas las tablas; el rol de `pg_restore` debe ser owner de la base destino.
- Disco: el destino del `.dump` debe tener ≥ 50% del tamaño de la BD original (factor de compresión típico).
- Servicio PostgreSQL accesible: `pg_isready -h <host> -p 5432` retorna `accepting connections`.

## Impacto y reversibilidad

| Aspecto | Detalle |
|---|---|
| Ventana de indisponibilidad (backup) | Solo lock `ACCESS SHARE` por tabla; ~0 impacto |
| Ventana de indisponibilidad (restore) | Exclusivo en la BD destino durante `DROP` y carga |
| Datos afectados | `DROP DATABASE` borra toda la BD destino antes del restore |
| Rollback | Restaurar a una **base distinta** (`pg_restore -d <otra_db>`); la original queda borrada y debe recuperarse desde otro backup |

## Procedimiento

### Paso 1: Generar el backup con formato custom
```bash
pg_dump -h localhost -U postgres -Fc -f backup_$(date +%Y%m%d).dump mydb
# {src:blk_ccddeebf0001}
```

**Salida esperada:** {src:blk_aabbccddee01}
```
(no stdout en éxito; archivo backup_YYYYMMDD.dump presente)
# {src:blk_ccddeebf0002}
```

**Verificación:** `ls -la backup_*.dump` muestra archivo con tamaño > 0; `pg_restore -l backup_*.dump | head` lista al menos las primeras tablas del esquema. {src:blk_aabbccddee02}

### Paso 2: Crear o recrear la base destino
:::danger
**`DROP DATABASE` borra toda la base sin pedir confirmación.** Antes de ejecutar, verifica dos veces que la BD destino **no es la original** o que ya tienes un backup reciente. Sin un backup externo, esta operación es IRREVERSIBLE.
::: {src:blk_bbccddee0003}

```bash
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS mydb_restore;"
psql -h localhost -U postgres -c "CREATE DATABASE mydb_restore;"
# {src:blk_ccddeebf0003}
```

**Verificación:** `psql -l | grep mydb_restore` muestra la base recién creada con owner `postgres`. {src:blk_aabbccddee04}

### Paso 3: Restaurar el backup
```bash
pg_restore -h localhost -U postgres -d mydb_restore --no-owner --role=postgres backup_*.dump
# {src:blk_ccddeebf0004}
```

**Verificación:** `pg_restore -l backup_*.dump | wc -l` (nº de items) coincide con el conteo post-restore de objetos en `mydb_restore` (`SELECT count(*) FROM information_schema.tables WHERE table_schema='public'`). {src:blk_aabbccddee05}

### Paso 4: Validar integridad por conteo de filas
```bash
psql -h localhost -U postgres -d mydb_restore -c "
  SELECT schemaname, relname, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC
  LIMIT 20;"
# {src:blk_ccddeebf0005}
```

**Verificación:** las tablas con más filas en la BD original aparecen en este top con conteos coherentes (puede haber pequeñas diferencias por autovacuum reciente, pero del orden de magnitud esperado). {src:blk_aabbccddee06}

## Verificación final
```bash
psql -h localhost -U postgres -d mydb_restore -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" {src:blk_eeeeff0009}
psql -h localhost -U postgres -d mydb_restore -c "SELECT count(*) FROM pg_proc WHERE prokind='f';" {src:blk_eeeeff000a}
# {src:blk_ccddeebf0006}
```

Ambos `count(*)` deben coincidir con los valores pre-backup de la BD original. {src:blk_ddbbccddeefc}

## Errores frecuentes
:::danger
**`pg_restore: error: could not execute query: ERROR: relation "xxx" already exists.** El restore asume BD vacía. Solución: ejecutar `DROP DATABASE` antes (Paso 2) o usar `--clean --if-exists` (cuidado: borra objetos en el orden que ve, no en orden de dependencias).
::: {src:blk_bbccddee0007}

:::warning
**`pg_dump: error: permission denied for table xxx`.** El rol no tiene `SELECT` sobre alguna tabla. Solución: `GRANT SELECT ON ALL TABLES IN SCHEMA public TO <rol>;` antes del backup, o ejecutar como superusuario.
::: {src:blk_bbccddee0008}

:::warning
**`pg_restore: error: could not connect to database: FATAL: database "mydb_restore" does not exist`.** Solución: ejecutar Paso 2 completo antes del Paso 3; verificar con `psql -l`.

## Backlinks
El backup + restore con pg_dump es uno de los tres caminos de backup de PostgreSQL; los enlaces muestran las alternativas y los conceptos adyacentes. {src:blk_c000000a01b5}

- [[note:postgresql-mvcc]] — para entender `pg_stat_user_tables.n_live_tup`.
- [[note:pg-backup-strategies]] — comparativa entre pg_dump, pg_basebackup y WAL archiving.
