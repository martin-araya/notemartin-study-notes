---
title: "Enlaces sin contexto"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: enlaces [[note:id]] sin frase introductoria. Falla AP7."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Enlaces sin contexto

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. {src:blk_a91f8e02c1d3}

## Ver también

[[note:vacuum]]

[[note:transactions]]

[[note:heap-tuple]]

## Comentario del fixture

BAD: cada `[[note:id]]` aparece como ítem de una lista, sin frase
introductoria de ≥ 5 palabras antes. Esto viola AP7 (F100) y S4
(regex contra frase introductoria ausente). {src:blk_a91f8e02c1d3}
