---
title: "Sin bloque de procedencia"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: sin bloque H2 de procedencia. Falla AP2 / S4."
reading-time-minutes: 1
language: es
tags: [type/concept, domain/databases, f101/i18n, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Sin bloque de procedencia

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot. {src:blk_a91f8e02c1d3}

## Definición formal

Una transacción ve solo las filas con `xmin < S(T)` y `xmax > S(T)`. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la nota no tiene la seccion H2 de procedencia con 4 campos. El frontmatter
tiene `source` y `retrieved`, pero el bloque para humanos esta ausente.
Esto viola AP2 (F101) y S4.
