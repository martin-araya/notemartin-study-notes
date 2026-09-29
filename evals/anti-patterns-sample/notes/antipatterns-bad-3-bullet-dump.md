---
title: "Lista de features de PostgreSQL (volcado)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: ≥ 10 viñetas consecutivas sin prosa. Falla AP8."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Lista de features de PostgreSQL (volcado)

## Features

- índices B-tree
- índices hash
- índices GIN
- índices BRIN
- índices GiST
- índices SP-GiST
- particionado nativo
- logical replication
- physical replication
- synchronous replication
- slot-based replication
- cascading replication
- JSONB nativo
- tipos rango
- tipos geometría
- tipos vectores
- tipos enum
- tipos dominio

## Comentario del fixture

BAD: 18 viñetas consecutivas sin prosa intermedia (no hay párrafo entre
ellas). Esto viola AP8 (F100) y S3 (regex `^(\s*[-*]\s+.+
){10,}`).
Solución: agrupar en 3 sub-secciones con párrafo introductorio cada una.
