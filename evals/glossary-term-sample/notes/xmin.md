---
title: "xmin"
note-type: glossary-term
status: draft
summary: "ID de transacción que insertó una fila en PostgreSQL; parte del mecanismo MVCC."
tags: [type/glossary-term, domain/databases]
source: "PostgreSQL 16 — System Columns"
source-type: docs
source-anchor: "system-columns"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]]"
---

# xmin

## TL;DR
`xmin` es el ID de la transacción que insertó la fila; parte del mecanismo MVCC que permite a PostgreSQL mantener snapshots por sesión. {src:blk_c00000000010}

{layer:l1} {src:blk_fedcba000100}

## Definición
Identificador de transacción (XID) almacenado en cada tupla que indica qué transacción creó la fila; usado por MVCC para decidir la visibilidad del snapshot. {src:blk_fedcba000200}

## Formas
| Idioma | Forma |
|---|---|
| Inglés | transaction ID (xmin) |
| Español | ID de transacción (xmin) |
| Sigla | xmin |

## Aliases
- `t_xmin` (en código fuente de PostgreSQL)

## Contexto
:::tip
Columna de sistema en PostgreSQL; presente en cada tabla sin necesidad de definirla explícitamente. {src:blk_fedcba000300}
::: {src:blk_bbccddee0001}

## Ejemplos
:::example
`SELECT xmin, * FROM users;` retorna el XID de la transacción que creó cada fila; `xmin = 1234` significa "fila insertada por transacción 1234".
::: {src:blk_bbccddee0002}

## Confundibles
| Término | Diferencia |
|---|---|
| `[[term:xmax]]` | XID de transacción que eliminó/modificó la fila |
| `[[term:cmin]]` | Command ID dentro de la transacción (no inter-transaccional) |
| `cid` | Alias obsoleto de `cmin` |

## Notas donde aparece
- [[note:postgresql-mvcc]]
- [[note:postgresql-configuration]]

## Backlinks
- [[note:postgresql-mvcc]]
