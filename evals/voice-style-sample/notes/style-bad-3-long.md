---
title: "Frases largas (long-sentences)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 50% de frases superan 25 palabras. Falla R1."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f99/voice-style, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Frases largas (long-sentences)

## TL;DR

PostgreSQL usa MVCC para que múltiples transacciones puedan leer y escribir al mismo tiempo sin bloquearse entre sí, lo cual mejora el throughput en cargas concurrentes. {src:blk_a91f8e02c1d3}

## Mecanismo

Cada fila lleva dos marcas de versión llamadas `xmin` y `xmax` que registran el id de la transacción que la creó y el id de la transacción que la reemplazó, respectivamente, y el optimizador las usa para decidir si una fila es visible para una transacción determinada. {src:blk_a91f8e02c1d3}

## Confirmación

El comando `BEGIN` abre el snapshot en ese instante, y cualquier
escritura posterior en otra transacción no afecta al lector hasta el
siguiente `BEGIN`, lo que se puede verificar con `psql` y dos sesiones
concurrentes.
