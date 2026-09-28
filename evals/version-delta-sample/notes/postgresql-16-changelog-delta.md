---
title: "PostgreSQL 16 — delta v15 → v16"
note-type: version-delta
status: draft
summary: "Delta de PostgreSQL 15 a 16: logical replication de slots por defecto, JSONB-SQL standard (IS JSON), password_encryption default cambia a scram-sha-256, EXPLAIN output restructurado."
tags: [type/version-delta, domain/databases, product/postgresql]
source: "PostgreSQL 16 Release Notes"
source-type: release-notes
source-anchor: "release-16"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-configuration]]"
---

# PostgreSQL 16 — delta v15 → v16

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Delta de PostgreSQL 15 a 16: logical replication de slots por defecto, JSONB-SQL standard, password_encryption default cambia a scram-sha-256. |
| **Procedencia** | PostgreSQL 16 Release Notes (release-notes) §release-16 · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
PostgreSQL 16 introduce logical replication de slots por defecto, agrega JSONB-SQL standard (`IS JSON`), cambia `password_encryption` default a `scram-sha-256`, y deprecó el operador `?` en JSONB. Operadores deben migrar passwords md5 antes del upgrade. {src:blk_b00000000001}

{layer:l2} {src:blk_fedcba000100}

## Cambios
| Versión exacta | Tipo | Área | Descripción |
|---|---|---|---|
| 16.0 | nuevo | replication | logical replication de slots por defecto en servidores primarios |
| 16.0 | nuevo | sql | `IS JSON` predicate estándar SQL (reemplaza `?` operador) |
| 16.0 | default alterado | auth | `password_encryption` default cambia de `md5` a `scram-sha-256` |
| 16.0 | cambiado | sql | `EXPLAIN` output incluye `Planning` separado de `Execution` |
| 16.0 | deprecado | sql | operador `?` en JSONB (usar `jsonb_path_query`) |
| 16.0 | eliminado | replication | `wal_level = 'archive'` (reemplazado por `replica` + `archive_mode`) |

## Breaking changes
:::danger
**Breaking change — `password_encryption` default.** El default cambia de `md5` a `scram-sha-256`. Los clientes que aún usan passwords md5 deben migrar antes del upgrade, o configurar `password_encryption = 'md5'` explícitamente. {src:blk_b00000000010}

**Breaking change — `wal_level = 'archive'`.** Este valor se elimina en 16.0; usar `replica` + `archive_mode = on` para archiving. {src:blk_b00000000011}
::: {src:blk_bbccddee0001}

## Cambios de default
Los siguientes defaults cambiaron; los operadores deben revisar configs antes del upgrade. {src:blk_b00000000020}

| Versión | Default anterior | Default nuevo | Impacto |
|---|---|---|---|
| 16.0 | `password_encryption=md5` | `password_encryption=scram-sha-256` | clientes con passwords md5 deben migrar |
| 16.0 | `wal_level=replica` + `archive_mode` único | `wal_level=replica` + `archive_mode` separado | scripts de backup deben verificar `archive_mode` |
| 16.0 | `max_replication_slots=10` | `max_replication_slots=20` | mayor capacidad de replicación por defecto |

## Migración
1. Backup completo de la base de datos antes del upgrade. {src:blk_b00000000030}
2. Actualizar clientes a `libpq` ≥ 16 (los antiguos no entienden scram-sha-256). {src:blk_fedcba000200}
3. Migrar passwords de `md5` a `scram-sha-256`: `ALTER USER app PASSWORD 'nueva_contraseña';` con `password_encryption = 'scram-sha-256'`. {src:blk_fedcba000300}
4. Cambiar `postgresql.conf`: actualizar `wal_level` y `archive_mode` si aplica. {src:blk_fedcba000400}
5. Aplicar upgrade binario: `pg_upgradecluster 16 main` (Debian/Ubuntu) o `pg_upgrade` (source). {src:blk_fedcba000500}
6. Verificar logs de upgrade y `pg_stat_activity` para errores residuales. {src:blk_fedcba000600}

## Trampas de migración
:::warning
**Trampa 1: `pg_dump`/`pg_restore` entre v15 y v16.** El formato del dump cambia para incluir nuevos tipos. Restaurar un dump v15 en v16 funciona; pero un dump v16 en v15 falla. Verificar versión del dump antes de restaurar backups cruzados. {src:blk_b00000000040}
::: {src:blk_bbccddee0002}

:::warning
**Trampa 2: extensiones third-party.** Extensiones no bundled (PostGIS, pg_partman, TimescaleDB) deben actualizarse a versión compatible con 16.x antes del upgrade del server. Usar `pg_extension_update()`. {src:blk_b00000000041}
::: {src:blk_bbccddee0003}

## Compatibilidad
| Versión PostgreSQL | Soporte logical replication nativo | Soporte SCRAM-SHA-256 |
|---|---|---|
| 14.x | sí | sí |
| 15.x | sí | sí |
| 16.x | default | default |

## Notas afectadas
Las siguientes notas concept deben enlazar de vuelta a esta delta: {src:blk_fedcba000700}
- [[note:postgresql-mvcc]] — cambió el comportamiento de visibility map en 16.0; `wal_level` default alterado.
- [[note:postgresql-configuration]] — `shared_buffers` default cambió en 16.3; nuevos GUCs introducidos.
- [[note:postgres-connection-errors]] — errores `password authentication failed` ahora mencionan scram-sha-256. {src:blk_b00000000050}

Las notas concept arriba deben tener `related: "[[note:postgresql-16-changelog-delta]]"` en su frontmatter (enlace bidireccional). {src:blk_fedcba000800}

## Backlinks
La delta conecta con las notas de configuración y arquitectura; los enlaces muestran los 2 ángulos del upgrade. {src:blk_b00000000060}

- [[note:postgresql-configuration]] — GUCs completos.
- [[note:postgresql-architecture]] — arquitectura interna.
