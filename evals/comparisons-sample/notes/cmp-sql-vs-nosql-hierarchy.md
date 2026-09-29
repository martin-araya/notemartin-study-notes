---
title: "SQL vs NoSQL — jerarquía por relajación"
note-type: comparison
status: published
summary: "Jerarquía por relajación de restricciones sobre SQL, mostrada como 4 niveles del espacio de diseño."
reading-time-minutes: 4
tags: [type/comparison, domain/databases, f87/comparison, f97/comparisons]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "section_path=/ch01/models"
retrieved: 2026-09-28
vendor: "industry"
product: "SQL / NoSQL / NewSQL"
product-version: "n/a"
related: "[[note:databases-taxonomy]]"
---

# SQL vs NoSQL — jerarquía por relajación

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa principalmente la forma F2 (jerarquía
> por relajación) + F5 (síntesis). {src:blk_b3c4d5e6f7a8}

## TL;DR

SQL, NoSQL y NewSQL son tres puntos del espacio de diseño; cada nivel
relaja una restricción del anterior.

## Jerarquía por relajación

| Nivel | Restricción relajada | Lo que se gana | Lo que se pierde |
|---|---|---|---|
| 0 | SQL relacional estricto | consistencia fuerte, joins, transacciones ACID | escalabilidad horizontal limitada |
| 1 | SQL sobre clusters (NewSQL: CockroachDB, Spanner) | distribución global con ACID | latencia de commit (2PC), complejidad operativa |
| 2 | NoSQL documental (MongoDB, CouchDB) | schema flexible, escala horizontal fácil | joins, transacciones multi-doc |
| 3 | NoSQL clave-valor (Redis, DynamoDB) | latencia sub-ms, escala ilimitada | queries ricos, transacciones |

:::derived {src:blk_a7b8c9d0e1f2}

## Comparativa

| Criterio | SQL relacional | NoSQL documental | NoSQL clave-valor |
|---|---|---|---|
| Consistencia | ACID fuerte | eventual por defecto | eventual |
| Esquema | fijo | flexible | ninguno |
| Queries | SQL (joins) | API del documento | clave exacta |
| Latencia (p50) | 5-50 ms | 1-10 ms | < 1 ms |

:::tip
**Fila decisiva — Consistencia.** Si necesitas ACID fuerte → SQL; si
toleras eventual → NoSQL.
::: {src:blk_0c1d2e3f4a5b}

## Síntesis

Los tres niveles comparten {el modelo de almacenamiento por documentos o
filas, no por grafo} y también comparten {la ausencia de grafos como
primitiva de primera clase}. La diferencia clave es que {SQL da
consistencia fuerte a costa de escalabilidad horizontal, NoSQL da escala
a costa de consistencia}, mientras que {cada nivel relaja una
restricción distinta del anterior}. En resumen, la elección se basa en
el SLA de consistencia del producto. {src:blk_6b7c8d9e0f1a}

## Criterios

Cada criterio refleja una dimensión clave del espacio de diseño de
motores de almacenamiento; la jerarquía anterior los ordena por la
restricción que relajan. {src:blk_e01b2c3d4e5f}

- **Consistencia**: SQL ACID, NoSQL eventual por defecto. {src:blk_a7b8c9d0e1f2}
- **Esquema**: SQL fijo, NoSQL flexible o nulo. {src:blk_0c1d2e3f4a5b}
- **Queries**: SQL rico (joins), NoSQL limitado. {src:blk_6b7c8d9e0f1a}
- **Latencia**: SQL medio, NoSQL clave-valor muy bajo. {src:blk_b3c4d5e6f7a8}

## Veredicto

Para mayoría de productos SaaS: empezar con PostgreSQL (NewSQL como
escalado). Para caching o sesiones: Redis (clave-valor). {src:blk_d84ae51cfb22}

## Backlinks

Notas relacionadas para profundizar en la taxonomía de bases de datos. {src:blk_9b2d5e8f1c67}

- [[note:databases-taxonomy]] — taxonomías formales y propiedades emergentes.
