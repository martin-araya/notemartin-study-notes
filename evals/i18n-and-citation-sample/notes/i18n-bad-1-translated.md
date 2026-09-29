---
title: "Conexiones máximas en PostgreSQL (parámetro traducido)"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: parámetro --max-conexiones traducido. Falla AP1 / S1."
reading-time-minutes: 1
language: es
tags: [type/concept, domain/databases, f101/i18n, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=42"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Conexiones máximas (parámetro traducido)

## TL;DR

PostgreSQL limita las conexiones concurrentes con el parámetro
`--max-conexiones` (en lugar de `--max-connections`). {src:blk_a91f8e02c1d3}

## Definición formal

El parámetro `--max-conexiones` acepta un entero entre 1 y 262143. {src:blk_a91f8e02c1d3}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 Server Administration · docs |
| **Versión** | PostgreSQL 16 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `page=42,section_path=/runtime-config/connections` |

## Comentario del fixture

BAD: el parámetro CLI `--max-connections` se traduce como
`--max-conexiones`. Esto viola AP1 (F101) y S1 (regex contra lista
cerrada de 45 no-traducibles, §3.2 entrada 16).
