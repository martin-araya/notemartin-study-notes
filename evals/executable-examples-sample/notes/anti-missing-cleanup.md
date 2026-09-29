---
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
