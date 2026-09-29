---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
tags: [type/concept, domain/databases, f78/concept, f99/voice-style]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:transactions]]"
---

# MVCC en PostgreSQL

PostgreSQL usa MVCC para evitar locks de lectura. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot. Cada fila lleva `xmin` y `xmax`.
Los lectores ven filas cuyo rango cae dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores usaban locks de tabla. Un `SELECT` largo
bloqueaba todas las inserciones. Un reporte diario competía con la
carga OLTP. {src:blk_a91f8e02c1d3}

## Definición formal

Para una transacción `T` con snapshot en `S(T)` y una fila `R`,
la fila es visible si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a91f8e02c1d3}

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Cada fila lleva dos marcas
de versión. Un `UPDATE` no borra la fila: inserta una nueva versión.
`VACUUM` recicla las versiones sin referencias activas. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

- MVCC sustituye locks de lectura por marcas de versión. {src:blk_a91f8e02c1d3}
- Cada transacción ve un snapshot estable. {src:blk_a91f8e02c1d3}
- `VACUUM` libera versiones viejas. {src:blk_a91f8e02c1d3}

## Backlinks

Notas relacionadas para profundizar en los componentes de MVCC. {src:blk_a91f8e02c1d3}

- [[note:vacuum]] — reciclaje de versiones.
- [[note:transactions]] — modelo transaccional ACID.
