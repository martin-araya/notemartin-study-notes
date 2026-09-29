---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
tags: [type/concept, domain/databases, f78/concept, f100/anti-patterns]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
related: "[[note:vacuum]], [[note:transactions]]"
---

# MVCC en PostgreSQL

PostgreSQL usa MVCC para evitar locks de lectura entre transacciones
concurrentes. {src:blk_a91f8e02c1d3}

## TL;DR

MVCC da a cada transacción un snapshot al iniciar. Cada fila lleva
dos marcas (`xmin`, `xmax`). Los lectores ven filas cuyo rango cae
dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores como MyISAM bloqueaban un `SELECT` largo
con todas las inserciones. Un reporte diario podía detener la carga
OLTP durante minutos. {src:blk_a91f8e02c1d3}

## Definición formal

Para una transacción `T` con snapshot en `S(T)` y una fila `R`,
la fila es visible si `xmin_R < S(T)` y `(xmax_R == ∞ ∨ xmax_R > S(T))`.
{src:blk_a91f8e02c1d3}

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`.
{src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

- MVCC sustituye locks de lectura por marcas de versión. {src:blk_a91f8e02c1d3}
- Cada transacción ve un snapshot estable. {src:blk_a91f8e02c1d3}
- `VACUUM` libera versiones viejas. {src:blk_a91f8e02c1d3}

## Backlinks

Para profundizar en el reciclaje de versiones, consulta [[note:vacuum]].
Para entender el modelo transaccional, consulta [[note:transactions]]. {src:blk_a91f8e02c1d3}

## Checklist de cierre (12 items, F100)

Antes de cerrar la nota, verifica los 12 anti-patrones transversales:
AP1 (transcripción), AP2 (definición circular), AP3 (callout decorativo),
AP4 (tabla de una fila), AP5 (analogía sin mapeo), AP6 (diagrama que
repite el texto), AP7 (enlace sin contexto), AP8 (volcado de viñetas),
AP9 (marketing copiado), AP10 (código sin caption), AP11 (mermaid syntax
error), AP12 (sección vacía). {src:blk_a91f8e02c1d3}
