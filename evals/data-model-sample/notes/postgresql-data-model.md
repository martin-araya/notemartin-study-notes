---
title: "PostgreSQL — modelo de datos de system catalogs (subset)"
note-type: data-model
status: draft
summary: "Subset del modelo de datos de los system catalogs de PostgreSQL 16 (pg_class, pg_attribute, pg_type, pg_namespace) con 3 relaciones e integridad referencial."
tags: [type/data-model, domain/databases, product/postgresql]
source: "PostgreSQL 16 — System Catalogs"
source-type: docs
source-anchor: "system-catalogs"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-architecture]]"
---

# PostgreSQL — modelo de datos de system catalogs (subset)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Subset del modelo de datos de los system catalogs de PostgreSQL 16 (pg_class, pg_attribute, pg_type, pg_namespace) con 3 relaciones e integridad referencial. |
| **Procedencia** | PostgreSQL 16 — System Catalogs (docs) §system-catalogs · recuperado 2026-09-27 |
| **Versión** | PostgreSQL 16 |
| **Estado** | Borrador (draft) |
| **Tiempo de lectura** | 4 min |

## TL;DR
4 system catalogs: pg_class (tablas/índices), pg_attribute (columnas), pg_type (tipos de datos), pg_namespace (schemas). Relaciones: pg_attribute.attrelid → pg_class.oid; pg_class.relnamespace → pg_namespace.oid; pg_attribute.atttypid → pg_type.oid. {src:blk_d00000000100}

{layer:l2}

## Modelo
:::diagram
```mermaid
erDiagram
    PG_NAMESPACE ||--o{ PG_CLASS : contains {src:blk_eeeeff000001}
    PG_NAMESPACE ||--o{ PG_TYPE : contains {src:blk_eeeeff000002}
    PG_CLASS ||--o{ PG_ATTRIBUTE : has {src:blk_eeeeff000003}
    PG_TYPE ||--o{ PG_ATTRIBUTE : typed_by {src:blk_eeeeff000004}
    PG_NAMESPACE {
        oid oid PK
        varchar name UK
    }
    PG_CLASS {
        oid oid PK
        varchar relname
        oid relnamespace FK
        char relkind
    }
    PG_ATTRIBUTE {
        oid attrelid PK
        int attnum PK
        varchar attname
        oid atttypid FK
    }
    PG_TYPE {
        oid oid PK
        varchar typname
        oid typnamespace FK
    }
# {src:blk_ccddeebf0001}
```
::: {src:blk_bbccddee0001}

## Entidades

### pg_namespace {src:blk_aabbccddee02}
Schema o namespace de PostgreSQL (cluster, public, schemas de usuario). {src:blk_d00000000101}

### pg_class {src:blk_aabbccddee03}
Tablas, índices, secuencias, vistas y otras relaciones. {src:blk_d00000000102}

### pg_attribute {src:blk_aabbccddee04}
Columnas de cada relación (tabla). Identifica por (attrelid, attnum). {src:blk_d00000000103}

### pg_type {src:blk_aabbccddee05}
Tipos de datos (int4, text, bool, varchar, etc.). {src:blk_d00000000104}

## Campos

### pg_namespace {src:blk_aabbccddee06}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `nspname` | VARCHAR(63) | NOT NULL, UNIQUE | Nombre del namespace |

### pg_class {src:blk_aabbccddee07}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `relname` | VARCHAR(63) | NOT NULL | Nombre de la tabla |
| `relnamespace` | OID | NOT NULL, FK → pg_namespace(oid) | Namespace |
| `relkind` | CHAR(1) | NOT NULL, CHECK (relkind IN ('r','i','S','v','c','f','p')) | Tipo: r=table, i=index, S=sequence, v=view, etc. |

### pg_attribute {src:blk_aabbccddee08}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `attrelid` | OID | PK, NOT NULL, FK → pg_class(oid) | Tabla propietaria |
| `attnum` | INT2 | PK, NOT NULL, CHECK (attnum > 0) | Número de columna |
| `attname` | VARCHAR(63) | NOT NULL | Nombre de la columna |
| `atttypid` | OID | NOT NULL, FK → pg_type(oid) | Tipo de la columna |

### pg_type {src:blk_aabbccddee09}
| Campo | Tipo | Restricciones | Descripción |
|---|---|---|---|
| `oid` | OID | PK, NOT NULL | Identificador |
| `typname` | VARCHAR(63) | NOT NULL | Nombre del tipo |
| `typnamespace` | OID | NOT NULL, FK → pg_namespace(oid) | Namespace |

## Relaciones
| Origen | Cardinalidad | Destino | Descripción |
|---|---|---|---|
| pg_namespace | 1:N | pg_class | Un namespace contiene N clases |
| pg_namespace | 1:N | pg_type | Un namespace contiene N tipos |
| pg_class | 1:N | pg_attribute | Una tabla tiene N columnas |
| pg_type | 1:N | pg_attribute | Un tipo es usado por N columnas |

## Claves e índices
| Entidad | PK | Índices secundarios |
|---|---|---|
| pg_namespace | oid | UNIQUE(nspname) |
| pg_class | oid | INDEX(relnamespace), INDEX(relname, relnamespace) |
| pg_attribute | (attrelid, attnum) | INDEX(attrelid) |
| pg_type | oid | INDEX(typnamespace), INDEX(typname, typnamespace) |

## Integridad

:::warning
**PK** — pg_namespace(oid), pg_class(oid), pg_type(oid); pg_attribute(attrelid, attnum) compuesta. {src:blk_d00000000120}
::: {src:blk_bbccddee000a}

:::warning
**FK** — pg_class.relnamespace → pg_namespace.oid; pg_type.typnamespace → pg_namespace.oid; pg_attribute.attrelid → pg_class.oid; pg_attribute.atttypid → pg_type.oid. ON DELETE CASCADE. {src:blk_d00000000121}
::: {src:blk_bbccddee000b}

:::warning
**UNIQUE** — pg_namespace.nspname. Impide duplicados de nombres de namespace. {src:blk_d00000000122}
::: {src:blk_bbccddee000c}

:::warning
**CHECK** — pg_attribute.attnum > 0; pg_class.relkind IN ('r','i','S','v','c','f','p'). {src:blk_d00000000123}
::: {src:blk_bbccddee000d}

:::danger
**NOT NULL** — todos los OIDs y campos críticos. {src:blk_d00000000124}
::: {src:blk_bbccddee000e}

## Consultas típicas

:::example
**Q1:** Listar tablas del schema `public`.

```sql
SELECT c.relname
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid {src:blk_eeeeff000005}
WHERE n.nspname = 'public' AND c.relkind = 'r'; {src:blk_eeeeff000006}
# {src:blk_ccddeebf0002}
```
::: {src:blk_bbccddee000f}

:::example
**Q2:** Listar columnas de una tabla.

```sql
SELECT a.attname, t.typname AS type {src:blk_eeeeff000007}
FROM pg_attribute a
JOIN pg_type t ON a.atttypid = t.oid {src:blk_eeeeff000008}
WHERE a.attrelid = 'users'::regclass AND a.attnum > 0 {src:blk_eeeeff000009}
ORDER BY a.attnum;
# {src:blk_ccddeebf0003}
```
::: {src:blk_bbccddee0010}

:::example
**Q3:** Contar tablas por schema.

```sql
SELECT n.nspname, COUNT(c.oid) AS n_tables {src:blk_eeeeff00000a}
FROM pg_namespace n
LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r' {src:blk_eeeeff00000b}
GROUP BY n.nspname
ORDER BY n_tables DESC; {src:blk_eeeeff00000c}
# {src:blk_ccddeebf0004}
```
::: {src:blk_bbccddee0011}

## Evolución

:::note
**PostgreSQL 16 (2023):** schema actual con 4 system catalogs. **PostgreSQL 17 (2024):** añade pg_publication y pg_subscription para logical replication. **PostgreSQL 18 (futuro):** posible nuevo pg_depend_column para tracking de dependencias column-level. {src:blk_d00000000130}
::: {src:blk_bbccddee0012}

## Backlinks
El modelo de system catalogs se complementa con el modelo MVCC y la arquitectura del backend; los enlaces muestran ambos aspectos. {src:blk_d00000000140}

- [[note:postgresql-mvcc]] — MVCC usa xmin/xmax en tuplas (no en este subset).
- [[note:postgresql-architecture]] — arquitectura interna del backend PostgreSQL.
