---
title: "max_connections (PostgreSQL)"
note-type: api-reference
status: published
summary: "Parámetro GUC de PostgreSQL que limita el número máximo de conexiones concurrentes al servidor."
reading-time-minutes: 2
tags: [type/api-reference, domain/databases, f79/api-reference, f94/reference-pure]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=42,section_path=/ch20/runtime-config/connections"
source-url: ""
retrieved: 2026-09-28
product: "PostgreSQL"
product-version: "16"
related: "[[note:connection-pooling]]"
---

# max_connections (PostgreSQL)

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota aplica la excepción `reference-pure` de
> `references/06-writing/intuition-first.md` §4: nota tipo `api-reference`,
> perfil `reference-pure`, unidad atómica sin motivación pedagógica.

## Problema

`max_connections` responde a la pregunta operacional: ¿cuántas conexiones
concurrentes acepta el servidor antes de rechazar nuevas con `FATAL: sorry,
too many clients already`? {src:blk_c0d2}

## Definición formal

| Campo | Valor |
|---|---|
| Tipo | `integer` |
| Default | `100` |
| Rango | `1` – `262143` |
| Reinicio | sí (recargar `postgresql.conf` + `pg_reload_conf()` no aplica; requiere restart) |

{src:blk_c0d2}

Si `max_connections` se incrementa por encima del valor por defecto,
debe ajustarse también `shared_buffers`, `work_mem` y los límites del
kernel (`max_connections × ~10 MB ≈ RAM esperada). {src:blk_c0d2}

## Notas

> "The default is typically chosen to avoid exhausting the system
> resources; PostgreSQL does not enforce a connection pool and expects
> pooling at the application or middleware layer." — PostgreSQL 16
> Server Administration, §19.4.1.

La fuente no ofrece una motivación pedagógica del parámetro (por qué se
eligió 100 como default, ni por qué el rango superior es 262143). Por
ello, esta nota aplica la **excepción `reference-pure`** (F94 §4) con
los 4 checks cumplidos: `use_case_profile == "reference-pure"`,
`note-type == "api-reference"` (≠ `concept`), unidad atómica sin
analogía razonable sin inventar, y la fuente no contiene ejemplo
ejecutable adyacente. Las etapas `## Intuición`, `## Analogía` y
`## Confirmación` se omiten conforme a la regla F94 §4 R1-R4.

## Resumen

- `max_connections` limita conexiones concurrentes; default 100, rango 1-262143. {src:blk_c0d2}
- Incrementar el valor exige revisar `shared_buffers` y `work_mem`. {src:blk_c0d2}

## Relacionados

- [[note:connection-pooling]] — prerrequisito operativo.

## Backlinks

- [[note:connection-pooling]]

## Queries

```dataview
LIST FROM [[note:max-connections]] AND -"templates"
```
