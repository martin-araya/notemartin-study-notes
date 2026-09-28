---
title: "PostgreSQL 16 — Chapter 13: Concurrency Control (selector application)"
note-type: [ref]
status: published
tags: [type/ref, meta/note-types, domain/databases]
source: "PostgreSQL 16 docs"
source-type: docs
source-anchor: "concurrency-control"
retrieved: 2026-09-28
coverage: summary
related: "[[note:postgresql-mvcc]], [[note:selector]]"
---

# PostgreSQL 16 — Chapter 13: Concurrency Control (selector application)

## Cabecera
| Campo | Valor |
| --- | --- |
| **Resumen** | Aplicación del selector al PostgreSQL 16 Chapter 13; identifica 4 tipos distintos. |
| **Procedencia** | PostgreSQL 16 docs (docs) §concurrency-control · recuperado 2026-09-28 |
| **Estado** | Publicado (published) |
| **Tiempo de lectura** | 2 min |

## TL;DR
El Chapter 13 ("Concurrency Control") de PostgreSQL 16 produce 4 tipos distintos de notas: `concept` (MVCC), `glossary-term` (xmin, xmax, clog), `configuration` (GUCs relacionados), `data-model` (MVCC + visibility map). {src:blk_a00000000020}

{layer:l1}

## Introducción
El Chapter 13 cubre el modelo MVCC de PostgreSQL, los niveles de aislamiento, y el mantenimiento de tuplas. La aplicación del selector produce **4 tipos distintos** del mismo capítulo. {src:blk_fedcba000100}

## Análisis del capítulo

| Unidad | Tipo de unidad | Tipo de fuente | Tipo asignado |
|---|---|---|---|
| MVCC (modelo) | Concepto (idea) | Documentación oficial | `[[note:concept]]` |
| `xmin`, `xmax`, `clog` | Término aislado | Documentación oficial | `[[note:glossary-term]]` |
| `transaction_isolation` | Config / setting | Documentación oficial | `[[note:configuration]]` |
| Visibility map | Schema / modelo | Documentación oficial | `[[note:data-model]]` |

## Reglas de desempate aplicadas

1. **Tipo de fuente**: documentación oficial → favorece tipos derivados de docs (`concept`, `configuration`, `glossary-term`). {src:blk_fedcba000200}
2. **Tamaño relativo**: cada unidad es < 1 párrafo → `concept`/`glossary-term`/`configuration`, no `chapter-digest`. {src:blk_fedcba000300}
3. **Reusabilidad**: `xmin` aparece en múltiples notas → promoción a `glossary-term`. {src:blk_fedcba000400}

## Tipos asignados

4 tipos distintos: {src:blk_fedcba000500}
1. `[[note:concept]]` — MVCC (modelo). {src:blk_fedcba000600}
2. `[[note:glossary-term]]` — xmin, xmax, clog (3 términos). {src:blk_fedcba000700}
3. `[[note:configuration]]` — GUCs de transacciones. {src:blk_fedcba000800}
4. `[[note:data-model]]` — visibility map y tuplas. {src:blk_fedcba000900}

Total: **4 tipos distintos** (≥ 3, criterio #1 ✅). {src:blk_fedcba000a00}

## Backlinks
El selector se aplica al Chapter 13 de PostgreSQL y deriva en 4 notas distintas; los enlaces muestran los 2 ángulos (el selector y el primer tipo generado). {src:blk_a00000000021}

- [[note:selector]]
- [[note:postgresql-mvcc]]
