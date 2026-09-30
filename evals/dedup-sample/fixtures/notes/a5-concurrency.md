---
title: 'Concurrency Control'
note-id: 'concurrency'
note-type: 'concept'
aliases: ['cc']
---

## Definición
El control de concurrencia incluye mecanismos de locking, MVCC multi-versión por fila visibles según snapshot del lector, y serialización. Aquí se detallan los tres enfoques.

## Locking
Los locks de fila y tabla coordinan accesos concurrentes.

## MVCC
MVCC mantiene múltiples versiones por fila visibles según snapshot del lector.

## Serialización
La serialización total garantiza orden equivalente al secuencial.
