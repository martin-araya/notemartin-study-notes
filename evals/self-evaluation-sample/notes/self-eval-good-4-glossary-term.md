---
title: "Snapshot (MVCC)"
note-type: glossary-term
status: published
summary: "Vista consistente del estado del database al inicio de una transacción."
reading-time-minutes: 3
language: es
tags: [type/glossary-term, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [recuerdo]
---


# Snapshot (MVCC)

Vista del database consistente al inicio de una transacción T,
determinada por el conjunto de transacciones activas en ese momento. {src:blk_d11f8e02c1d3}

## Procedencia

| Campo | Valor |
|---|---|
| **Fuente** | PostgreSQL 16 docs · concurrency control |
| **Versión** | PostgreSQL 16.3 |
| **Fecha de recuperación** | 2026-09-29 |
| **URL/anchor** | `13.1.2` |

## Autoevaluación

Tipos asignados a `glossary-term` (referencia pura, solo recuerdo).

### Recuerdo

:::collapsible{default_open=false}
¿Qué es un snapshot en MVCC?
Es la vista del database que observa una transacción al inicio, congelada hasta el commit o rollback.
> Fundamento: {src:blk_d11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué define el conjunto de transacciones activas que delimitan un snapshot?
Las transacciones que estaban activas en el instante del primer comando de la transacción definen la frontera: las escrituras posteriores de otras transacciones no serán visibles.
> Fundamento: [[note:mvcc-snapshot#active-set]]
:::

:::collapsible{default_open=false}
¿Un snapshot cambia durante la vida de una transacción?
No, permanece estable hasta el commit o rollback; cualquier escritura confirmada después del inicio no es visible para esa transacción.
> Fundamento: [[note:mvcc-snapshot#stability]]
:::
