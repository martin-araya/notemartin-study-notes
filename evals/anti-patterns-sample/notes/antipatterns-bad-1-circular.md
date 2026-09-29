---
title: "MVCC — definición circular"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: definición circular ('MVCC es un mecanismo de MVCC que…'). Falla AP2."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# MVCC — definición circular (anti-ejemplo)

## TL;DR

MVCC es un mecanismo de control de concurrencia que permite versiones
múltiples. {src:blk_a91f8e02c1d3}

## Definición formal (CIRCULAR)

MVCC es un MVCC que permite que múltiples versiones coexistan. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la definición de `## Definición formal` dice "MVCC es un mecanismo
de MVCC" — usa el término definido (MVCC) en su propia definición. Esto
viola AP2 (F100) y S1 (regex `(\w+)\s+es\s+(?:un|una)\s+`).
