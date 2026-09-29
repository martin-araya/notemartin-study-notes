---
title: "Resumen que copia el SDM"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: '## Resumen' copia ≥ 50% de un párrafo del SDM verbatim. Falla AP1."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=37,section_path=/ch13/concurrency"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Resumen que copia el SDM

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Resumen (TRANSCRIPCIÓN)

PostgreSQL implementa MVCC con HeapTuple visible/no visible por
xmin/xmax en cada fila. Un UPDATE no modifica la fila: inserta una
nueva versión y marca la anterior como borrada. Un VACUUM recicla
las versiones sin referencias. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: el `## Resumen` copia verbatim un párrafo del SDM (3 oraciones
seguidas con palabras idénticas al SDM). Esto viola AP1 (F100) y S5
(coincidencia literal ≥ 50%). Solución: reescribir con la técnica de
F98 §4 (enumerar unidades → reescribir).
