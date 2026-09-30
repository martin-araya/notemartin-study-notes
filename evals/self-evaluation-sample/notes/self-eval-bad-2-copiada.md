---
title: "Concepto con respuesta copiada"
note-type: concept
status: published
summary: "Nota concept cuya respuesta es copia literal del bloque referenciado."
reading-time-minutes: 3
language: es
tags: [type/concept, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [recuerdo, aplicacion, decision]
---


# Concepto con respuesta copiada

## TL;DR

Esta nota falla V4 (respuesta con ≤ 2 tokens no técnicos = trivial). {src:blk_f11f8e02c1d3}

## Definición

Concepto de prueba para verificar V4 / AP13. {src:blk_f11f8e02c1d3}

## Autoevaluación

### Recuerdo

:::collapsible{default_open=false}
¿Qué garantiza el aislamiento snapshot?
Snapshot.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuál es la marca de la transacción creadora?
`xmin`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué operación recicla versiones?
`VACUUM`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

### Aplicación

:::collapsible{default_open=false}
Dados T1 y T2 sin commit, ¿qué ve T2?
Versión previa.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con 80 % muertas, ¿qué operación?
`VACUUM`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
Con lecturas largas, ¿nivel?
`REPEATABLE READ`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

### Decisión

:::collapsible{default_open=false}
¿READ COMMITTED o REPEATABLE READ?
`REPEATABLE READ`.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuándo NO usar MVCC?
Embebidos.
> Fundamento: {src:blk_f11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Fila o bloque?
Fila.
> Fundamento: {src:blk_f11f8e02c1d3}
:::
