---
title: "PostgreSQL 16 vs MySQL 8"
note-type: comparison
status: published
summary: "Comparación entre los dos motores relacionales open-source más usados: PostgreSQL 16 y MySQL 8."
reading-time-minutes: 6
tags: [type/comparison, domain/databases, f87/comparison, f97/comparisons]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=8,section_path=/ch01/intro"
retrieved: 2026-09-28
vendor: "PostgreSQL Global Development Group / Oracle"
product: "PostgreSQL 16 / MySQL 8"
product-version: "16.3 / 8.4"
related: "[[note:acid]], [[note:replication]]"
---

# PostgreSQL 16 vs MySQL 8

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F1 (tabla lado a lado) + F5
> (síntesis) del patrón F97, sobre el tipo de nota `comparison` definido por F87.

## TL;DR

PostgreSQL 16 y MySQL 8 son motores relacionales con > 25 años de madurez
cada uno; la elección suele venir del ecosistema (PostGIS para geo,
HeatWave para DW) más que del motor mismo. {src:blk_9b2d5e8f1c67}

## Comparativa

| Criterio | PostgreSQL 16 | MySQL 8 |
|---|---|---|
| Modelo | ORDBMS | RDBMS |
| Consistencia | ACID por defecto | ACID con InnoDB |
| JSON nativo | `jsonb` (binario, indexable) | `json` (texto) |
| Replicación lógica | nativa (`pgoutput`) | nativa (`binlog`) |
| Madurez (años en producción) | 28 | 29 |
| Ecosistema (extensiones) | amplio (PostGIS, pgvector) | amplio (MySQL Shell, HeatWave) |

:::tip
**Fila decisiva — Madurez.** Ambas tienen ≥ 25 años; la elección suele
venir del ecosistema (PostGIS para geo, MySQL Shell para DBA legacy).
::: {src:blk_a91f8e02c1d3}

## Síntesis

Ambas opciones comparten {consistencia ACID con su motor por defecto} y
{madurez superior a 25 años con amplia base instalada}. :::external
La diferencia clave es que {PostgreSQL ofrece `jsonb` indexable mientras
MySQL tiene `json` textual}, lo que cambia el rendimiento en queries
JSON. En resumen, ambas cubren el 90% de los casos; la elección se
decide por ecosistema, no por motor. {src:blk_b12c44f0a8e7}

## Criterios

Los criterios enumerados a continuación explican por qué cada celda toma el
valor que toma; permiten al lector verificar la comparación sin reabrir
la documentación oficial. {src:blk_5e7f0a3b2c19}

- **Modelo** (ORDBMS vs RDBMS): PostgreSQL soporta tipos definidos por el usuario. {src:blk_a91f8e02c1d3}
- **JSON** (`jsonb` vs `json`): PostgreSQL indexa campos binarios; MySQL los almacena como texto. {src:blk_b12c44f0a8e7}
- **Madurez** (28 vs 29 años): ambas > 25 años; diferencia marginal. {src:blk_1d3e8a92f7c4}

## Veredicto

Si necesitas PostGIS, pgvector o tipos avanzados → PostgreSQL. Si
dependes de HeatWave o de un DBA con experiencia legacy → MySQL. {src:blk_5e7f0a3b2c19}

## Backlinks

Notas relacionadas que el lector puede consultar para profundizar en cada
criterio. {src:blk_8c4d9e6f1a20}

- [[note:acid]] — modelo transaccional ACID.
- [[note:replication]] — replicación lógica.

## Queries

```dataview
LIST FROM [[note:comparison-postgres-mysql]] AND -"templates"
``` {src:blk_6c4a7b0e3d92}
