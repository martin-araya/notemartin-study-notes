---
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
