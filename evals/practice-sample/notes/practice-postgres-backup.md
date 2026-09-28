---
title: "PostgreSQL — backup + restore con pg_dump/pg_restore"
note-type: practice
status: draft
difficulty: 2
tags: [type/practice, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "backup-dump"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:procedure-postgres-backup]], [[note:postgresql-mvcc]]"
---

# PostgreSQL — backup + restore con pg_dump/pg_restore

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Lab: backup lógico de una BD con `pg_dump -Fc` y restore con `pg_restore`. |
| **Procedencia** | PostgreSQL 16 docs (docs) §backup-dump · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 10 min |

## TL;DR
Backup + restore completo de una BD PostgreSQL usando `pg_dump -Fc` (formato custom) y `pg_restore`. Aprende a crear archivos `.dump` comprimidos y restaurarlos selectivamente. {src:blk_c00000000001}

{layer:l2}

## Enunciado
Tienes una BD `mydb` que necesitas respaldar completamente y restaurar en otro servidor. El objetivo es practicar el flujo de backup/restore con formato custom (comprimido) y restauración selectiva. {src:blk_fedcba000100}

## Entorno

| Componente | Versión | Notas |
|---|---|---|
| Sistema operativo | Linux 5.x / macOS 14 / WSL2 | - |
| PostgreSQL | 16.x | cliente `psql` ≥ 16 |
| Recursos | 1 GB RAM, 2 GB disco | mínimo para el lab |

## Objetivo
Aprender el flujo completo de backup lógico con `pg_dump -Fc` y restauración con `pg_restore`, incluyendo restauración selectiva (solo esquema, solo datos, etc.). {src:blk_fedcba000200}

## Solución

### Paso 1: Crear BD de prueba con datos {src:blk_aabbccddee01}
```sql
createdb labdb
psql -d labdb -c "CREATE TABLE users (id serial PRIMARY KEY, email varchar(255));"
psql -d labdb -c "INSERT INTO users (email) VALUES ('a@example.com'), ('b@example.com');"
# {src:blk_ccddeebf0001}
```

### Paso 2: Crear el backup en formato custom {src:blk_aabbccddee02}
```bash
pg_dump -h localhost -U postgres -Fc -f labdb.dump labdb
ls -la labdb.dump
# {src:blk_ccddeebf0002}
```

### Paso 3: Crear BD destino y restaurar {src:blk_aabbccddee03}
:::warning
**`DROP DATABASE` es destructivo.** NO ejecutes este paso en producción sin antes hacer backup.
::: {src:blk_bbccddee0004}

```bash
psql -c "DROP DATABASE IF EXISTS labdb_restored;"
psql -c "CREATE DATABASE labdb_restored;"
pg_restore -h localhost -U postgres -d labdb_restored labdb.dump
# {src:blk_ccddeebf0003}
```

## Qué observar
:::note {src:blk_fedcba000300}
- El archivo `.dump` debe ser ~10x más pequeño que `pg_dump` plano (compresión automática).
- `pg_restore` debe mostrar mensajes `pg_restore: connecting to database ... pg_restore: creating ... pg_restore: processing data for table ...`.
- La BD `labdb_restored` debe tener la tabla `users` con 2 filas.
::: {src:blk_bbccddee0005}

## Verificación
```sql
psql -d labdb_restored -c "SELECT count(*) FROM users;" {src:blk_fedcba000400}
# {src:blk_ccddeebf0004}
```
Resultado esperado: `2`. {src:blk_fedcba000500}

## Limpieza

:::warning {src:blk_fedcba000600}
**Toda la limpieza es destructiva.** `dropdb` borra las BDs; `rm -f` borra el archivo de backup. Ejecuta este paso solo después de verificar que NO necesitas los datos del lab.
::: {src:blk_bbccddee0006}

1. Borrar la BD de prueba: {src:blk_fedcba000700}
   ```bash
   dropdb labdb {src:blk_fedcba000800}
   dropdb labdb_restored {src:blk_fedcba000900}
# {src:blk_ccddeebf0005}
   ```
2. Borrar el archivo de backup: {src:blk_fedcba000a00}
   ```bash
   rm -f labdb.dump {src:blk_fedcba000b00}
# {src:blk_ccddeebf0006}
   ```

Después de la limpieza, el sistema vuelve a su estado original. {src:blk_fedcba000c00}

## Lo que NO debe correrse en producción

:::danger {src:blk_fedcba000d00}
- `DROP DATABASE` (Paso 3): elimina la BD destino permanentemente.
- `rm labdb.dump`: sin el archivo no se puede restaurar.

Nunca ejecutes este lab en un cluster de producción sin antes hacer un backup completo con `pg_dumpall --globals-only` + verificar la integridad del `.dump`. {src:blk_fedcba000e00}
::: {src:blk_bbccddee0007}

## Cuándo omitir este lab

:::note
Omite este lab si: (1) ya dominas el flujo completo de backup + restore con `pg_dump`/`pg_restore`; (2) el cluster de producción tiene políticas de backup declaradas en Terraform/Kubernetes y prefieres validar esas políticas; (3) trabajas con bases de datos que usan replicación nativa y el backup se hace vía WAL archiving + PITR.
::: {src:blk_bbccddee0008}

## Pistas

:::tip
Si `pg_restore` retorna errores de permisos, verifica que el usuario sea owner de la BD destino. Si retorna errores de FK, ejecuta con `--no-owner --role=postgres`.
::: {src:blk_bbccddee0009}

## Backlinks
El lab se conecta con el procedure de backup y los errores típicos de Postgres; los enlaces muestran los 2 ángulos del flujo. {src:blk_c00000000008}

- [[note:procedure-postgres-backup]]
- [[note:postgres-connection-errors]]
