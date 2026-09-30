---
title: "Concepto sin fundamento en autoevaluación"
note-type: concept
status: published
summary: "Nota concept con colapsable que omite la línea de Fundamento."
reading-time-minutes: 3
language: es
tags: [type/concept, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [recuerdo, aplicacion, decision]
---


# Concepto sin fundamento en autoevaluación

## TL;DR

Esta nota falla V3 porque un colapsable no cierra con `> Fundamento:`. {src:blk_e11f8e02c1d3}

## Definición

Concepto de prueba para verificar el validador V3 / AP14. {src:blk_e11f8e02c1d3}

## Autoevaluación

Tipos asignados: recuerdo, aplicación, decisión.

### Recuerdo

:::collapsible{default_open=false}
¿Cuál es la diferencia entre snapshot y vista materializada?
El snapshot es MVCC temporal por transacción; la vista materializada es persistente y refrescable manualmente.
:::

:::collapsible{default_open=false}
¿Qué marca indica el inicio de la transacción creadora de una fila?
`xmin`.
> Fundamento: {src:blk_e11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué operación recicla las versiones muertas?
`VACUUM`.
> Fundamento: [[note:vacuum#recycle]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos transacciones T1 y T2, ¿qué ve T2 si T1 aún no hace commit?
La versión previa al commit de T1.
> Fundamento: {src:blk_e11f8e02c1d3}
:::

:::collapsible{default_open=false}
Si tu tabla tiene 80 % de tuplas muertas, ¿qué recomiendas?
Ejecutar `VACUUM (VERBOSE, ANALYZE)`.
> Fundamento: [[note:vacuum#recycle]]
:::

:::collapsible{default_open=false}
Con lecturas largas y escrituras concurrentes, ¿qué nivel de aislamiento?
`REPEATABLE READ`.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

### Decisión

:::collapsible{default_open=false}
Entre `READ COMMITTED` y `REPEATABLE READ`, ¿cuál para reportes agregados?
`REPEATABLE READ`.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

:::collapsible{default_open=false}
¿Cuándo NO usar MVCC?
En sistemas embebidos con memoria muy limitada.
> Fundamento: [[note:storage-tradeoffs#mvcc-vs-locking]]
:::

:::collapsible{default_open=false}
Para OLTP con muchas escrituras, ¿MVCC por fila o por bloque?
MVCC por fila.
> Fundamento: [[note:storage-tradeoffs#granularity]]
:::
