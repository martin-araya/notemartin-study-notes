---
title: "MVCC"
note-type: glossary-term
status: draft
summary: "Multi-Version Concurrency Control; permite lecturas y escrituras concurrentes sin bloqueos mediante snapshots por sesión."
tags: [type/glossary-term, domain/databases]
source: "PostgreSQL 16 — Concurrency Control"
source-type: docs
source-anchor: "mvcc-intro"
retrieved: 2026-09-27
vendor: PostgreSQL Global Development Group
product: PostgreSQL
product-version: "16"
related: "[[note:postgresql-mvcc]], [[note:postgresql-architecture]]"
---

# MVCC

## TL;DR
MVCC (Multi-Version Concurrency Control) permite a múltiples transacciones leer y escribir sin bloqueos manteniendo un snapshot por sesión. {src:blk_c00000000020}

{layer:l1} {src:blk_fedcba000100}

## Definición
Técnica de control de concurrencia donde cada transacción ve un snapshot consistente del estado de la base de datos sin necesidad de bloqueos de lectura. {src:blk_fedcba000200}

## Formas
| Idioma | Forma |
|---|---|
| Inglés | Multi-Version Concurrency Control |
| Español | Control de Concurrencia Multiversión |
| Sigla | MVCC |

## Aliases
- Multi-versioning
- Snapshot-based concurrency control

## Contexto
:::tip
Usado en PostgreSQL, MySQL InnoDB, Oracle, CockroachDB y la mayoría de RDBMS modernas. {src:blk_fedcba000300}
::: {src:blk_bbccddee0001}

## Ejemplos
:::example
`SELECT * FROM users WHERE id = 1;` retorna el snapshot del último COMMIT antes de la transacción, incluso si otras transacciones modifican la fila simultáneamente.
::: {src:blk_bbccddee0002}

## Confundibles
| Término | Diferencia |
|---|---|
| `[[term:two-phase-locking]]` | Two-Phase Locking; bloquea filas vs MVCC usa snapshots |
| `Snapshot isolation` | Sinónimo aproximado pero no idéntico |
| `SERIALIZABLE` | Nivel de aislamiento; PostgreSQL usa SSI (variant MVCC) |

## Notas donde aparece
- [[note:postgresql-mvcc]]
- [[note:postgresql-architecture]]
- [[note:postgres-connection-errors]]

## Backlinks
- [[note:postgresql-mvcc]]
