---
title: "Término con pregunta de aplicación (mal)"
note-type: glossary-term
status: published
summary: "Glossary-term con sección de Aplicación: viola la regla de referencia pura."
reading-time-minutes: 3
language: es
tags: [type/glossary-term, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [recuerdo, aplicacion]
---


# Término con pregunta de aplicación (mal)

## TL;DR

Término que viola AP15: glossary-term es referencia pura y solo recuerdo aplica. {src:blk_g11f8e02c1d3}

## Autoevaluación

Tipos declarados (incorrectos): recuerdo, aplicación.

### Recuerdo

:::collapsible{default_open=false}
¿Qué es un snapshot?
Vista consistente al inicio de la transacción.
> Fundamento: {src:blk_g11f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Qué define el snapshot?
El conjunto de transacciones activas al inicio.
> Fundamento: [[note:mvcc-snapshot#active-set]]
:::

:::collapsible{default_open=false}
¿Cambia el snapshot durante la transacción?
No, es estable.
> Fundamento: [[note:mvcc-snapshot#stability]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos clientes, ¿cómo configuras el snapshot isolation?
Ajustando `default_transaction_isolation = 'repeatable read'`.
> Fundamento: [[note:isolation-levels#config]]
:::

:::collapsible{default_open=false}
Con un pool de conexiones, ¿cómo preservas el snapshot?
Usando `SET TRANSACTION SNAPSHOT` al iniciar cada transacción del pool.
> Fundamento: [[note:pool-snapshots#reset]]
:::

:::collapsible{default_open=false}
Si necesitas un snapshot distribuido, ¿qué patrón aplicas?
`SET TRANSACTION SNAPSHOT '<id>'` con un id previamente exportado.
> Fundamento: [[note:distributed-snapshots#export]]
:::
