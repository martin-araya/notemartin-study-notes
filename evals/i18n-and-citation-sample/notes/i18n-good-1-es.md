---
title: "MVCC en PostgreSQL"
note-type: concept
status: published
summary: "Control de concurrencia multiversión: cada fila lleva marcas de versión y los lectores ven un snapshot estable."
reading-time-minutes: 4
language: es
tags: [type/concept, domain/databases, f78/concept, f101/i18n]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16.3"
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

`VACUUM` libera versiones con `xmax < oldest_active_snapshot`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Configuración

El parámetro `--max-connections` controla el número máximo de conexiones
concurrentes al servidor PostgreSQL. Por defecto, el valor es `100` y el
rango válido es `1` a `262143`. {src:blk_a91f8e02c1d3}

## Resumen

Las 3 ideas clave de MVCC son: snapshot por transacción, marcas de
versión por fila y reciclaje por `VACUUM`. {src:blk_a91f8e02c1d3}

## Backlinks

Notas relacionadas para profundizar en los componentes de MVCC. {src:blk_a91f8e02c1d3}

- [[note:vacuum]] — reciclaje de versiones.
- [[note:transactions]] — modelo transaccional ACID.

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 Server Administration · docs |
| **Versión** | PostgreSQL 16.3 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `page=37,section_path=/ch13/concurrency` |

Notas:
- El bloque complementa el frontmatter `source`, `source-type`,
  `source-anchor`, `retrieved`. {src:blk_a91f8e02c1d3}
- Frontmatter es metadata para máquinas; este bloque es metadata para
  humanos que no abren el YAML. {src:blk_a91f8e02c1d3}
- Si el campo URL/anchor es privado, se sustituye por `local: archivo
  /path/al/libro.pdf, capítulo 13`. {src:blk_a91f8e02c1d3}

## Backlinks

Para profundizar en el reciclaje de versiones, consulta [[note:vacuum]].
Para entender el modelo transaccional, consulta [[note:transactions]].
