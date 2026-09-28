---
title: "PostgreSQL 16 cheatsheet"
note-type: cheatsheet
status: draft
tags: [type/cheatsheet, domain/databases, product/postgresql]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "cheatsheet"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgres-connection-errors]]"
---

# PostgreSQL 16 cheatsheet

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Cheatsheet de PostgreSQL 16: comandos CLI, atajos psql, errores frecuentes. |
| **Procedencia** | PostgreSQL 16 docs (docs) §cheatsheet · recuperado 2026-09-27 |
| **Versión** | 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 3 min |

## TL;DR
Comandos CLI de PostgreSQL 16, atajos psql (`\dt`, `\dn`, `\du`), y errores frecuentes con enlaces a notas detalladas. {src:blk_fedcba000100}

{layer:l1}

## Comandos
| Comando | Descripción | Ver |
|---|---|---|
| `psql -h localhost -U postgres db` | Conectar a una BD con usuario específico | [[note:postgres-connection-errors]] |
| `pg_dump -Fc -f backup.dump db` | Backup lógico en formato custom | [[note:procedure-postgres-backup]] |
| `pg_restore -d db backup.dump` | Restore lógico desde custom | [[note:procedure-postgres-backup]] |
| `createdb dbname` | Crear base de datos | [[note:data-model]] |
| `dropdb dbname` | Eliminar base de datos | [[note:data-model]] |
| `VACUUM ANALYZE;` | Liberar tuplas y actualizar estadísticas | [[note:postgresql-mvcc]] |
| `EXPLAIN ANALYZE SELECT ...;` | Ver plan de query | [[note:postgresql-configuration]] |
| `SELECT pg_size_pretty(pg_database_size('db'));` | Tamaño de una BD | [[note:postgresql-configuration]] |
| `\dt+` | Listar tablas con tamaño | [[note:glossary-term-table]] |
| `\di+` | Listar índices con tamaño | [[note:glossary-term-index]] |
| `\du` | Listar usuarios | [[note:glossary-term-role]] |
| `\dn` | Listar schemas | [[note:glossary-term-schema]] |

## Atajos
| Atajo | Significado |
|---|---|
| `\dt` | Listar tablas |
| `\dn` | Listar schemas |
| `\dv` | Listar vistas |
| `\dx` | Listar extensiones |
| `\d+ tabla` | Describir tabla con detalles |
| `\df` | Listar funciones |

## Errores comunes

:::warning
**`FATAL: too many connections for role "app"`** — excede `max_connections`. Solución: desplegar pgbouncer o reducir pool. Ver [[note:postgres-connection-errors]].
::: {src:blk_bbccddee0001}

:::warning
**`ERROR: duplicate key value violates unique constraint`** — INSERT conflict. Solución: usar `ON CONFLICT DO NOTHING`. Ver [[note:error-troubleshooting-constraints]].
::: {src:blk_bbccddee0002}

:::warning
**`FATAL: password authentication failed for user "app"`** — password incorrecto o mal configurado. Solución: `ALTER USER app WITH PASSWORD '...';`. Ver [[note:postgres-connection-errors]].
::: {src:blk_bbccddee0003}

## Backlinks
- [[note:postgresql-mvcc]]
- [[note:postgres-connection-errors]]
