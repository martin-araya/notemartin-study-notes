---
title: "Aislamiento de transacciones en MVCC"
note-type: concept
status: published
summary: "MVCC da a cada transacción un snapshot al inicio; las escrituras concurrentes no son visibles hasta el commit."
reading-time-minutes: 3
language: es
tags: [type/concept, domain/sample, f102/self-eval]
source: "evals/corpus/sample/sdm.json"
source-type: docs
source-anchor: "section_path=/sample"
retrieved: 2026-09-29
self-evaluation-types: [recuerdo, aplicacion, decision]
---


# Aislamiento de transacciones en MVCC

## TL;DR

MVCC da a cada transacción un snapshot al inicio. Cada fila lleva
dos marcas (`xmin`, `xmax`). Los lectores ven filas cuyo rango cae
dentro del snapshot. {src:blk_a91f8e02c1d3}

## Problema

Antes de MVCC, los motores bloqueaban un `SELECT` largo con todas las
inserciones. Un reporte diario podía detener la carga OLTP durante
minutos. {src:blk_a91f8e02c1d3}

## Definición formal

Una transacción `T` con snapshot `S(T)` ve la fila `R` si `xmin_R < S(T)`
y `(xmax_R == ∞ ∨ xmax_R > S(T))`. {src:blk_a91f8e02c1d3}

## Mecanismo

PostgreSQL implementa MVCC con `HeapTuple`. Un `UPDATE` no borra la
fila: inserta una nueva versión y marca la anterior. {src:blk_a91f8e02c1d3}

## Resumen

MVCC garantiza que cada transacción observa un snapshot estable y que
las marcas de versión por fila permiten reciclar espacio con `VACUUM`
sin bloquear lectores. {src:blk_a91f8e02c1d3}

## Autoevaluación

Tipos asignados a `concept`: recuerdo, aplicación, decisión.

### Recuerdo

:::collapsible{default_open=false}
¿Qué garantiza el aislamiento snapshot en MVCC?
Cada transacción observa un estado del database consistente con el momento de su inicio; las escrituras concurrentes no son visibles hasta el commit.
> Fundamento: {src:blk_a91f8e02c1d3}
:::

:::collapsible{default_open=false}
¿Cuál es el campo del header de heap tuple que marca la transacción creadora?
El campo `xmin` registra la transacción que insertó la fila; mientras la fila no se modifique, este valor permanece estable.
> Fundamento: [[note:heap-tuple-layout#header]]
:::

:::collapsible{default_open=false}
¿Qué operación recicla las versiones con `xmax < oldest_active_snapshot`?
La operación `VACUUM` marca como reutilizables los espacios ocupados por tuplas cuya versión ya no es visible para ninguna transacción activa.
> Fundamento: [[note:vacuum#recycle]]
:::

### Aplicación

:::collapsible{default_open=false}
Dados dos transacciones T1 y T2 que arrancan antes de que T1 haga commit, ¿qué versión de la fila ve T2 al hacer SELECT?
La versión previa al commit de T1 (T2 sigue en su snapshot original); el commit posterior de T1 no es visible para T2.
> Fundamento: {src:blk_a91f8e02c1d3}
:::

:::collapsible{default_open=false}
Con una tabla donde el 80 % de las filas son versiones muertas, ¿qué operación recomiendas primero para liberar espacio?
Ejecutar `VACUUM (VERBOSE, ANALYZE)` para reciclar versiones y refrescar estadísticas.
> Fundamento: [[note:vacuum#recycle]]
:::

:::collapsible{default_open=false}
Si tu aplicación hace lecturas largas sobre una tabla con mucha escritura, ¿qué nivel de aislamiento evita lecturas no repetibles?
`REPEATABLE READ`: garantiza snapshot estable durante toda la transacción.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

### Decisión

:::collapsible{default_open=false}
Entre `READ COMMITTED` y `REPEATABLE READ`, ¿cuál elegirías para un reporte agregado que no puede mostrar lecturas no repetibles?
`REPEATABLE READ`: garantiza snapshot estable durante toda la transacción.
> Fundamento: [[note:isolation-levels#trade-offs]]
:::

:::collapsible{default_open=false}
¿Cuándo NO usarías MVCC y preferirías un modelo de locking pesimista?
En sistemas embebidos con memoria muy limitada donde el coste de mantener múltiples versiones por fila no compensa.
> Fundamento: [[note:storage-tradeoffs#mvcc-vs-locking]]
:::

:::collapsible{default_open=false}
Para una carga 100 % OLTP con muchas escrituras y reportes cortos, ¿prefieres MVCC por fila o MVCC por bloque?
MVCC por fila: las escrituras no invalidan lecturas de filas vecinas.
> Fundamento: [[note:storage-tradeoffs#granularity]]
:::
