---
title: "Parafraseo correcto (Oracle RAC)"
note-type: concept
status: draft
summary: "Parafraseo CORRECTO de la fuente source-1-oracle: 5/5 unidades cubiertas con literales verbatim."
reading-time-minutes: 2
tags: [type/paraphrase, domain/databases, f98/paraphrase, fixture/positive]
source: "evals/paraphrase-sample/corpus/source-1-oracle.txt"
source-type: docs
source-anchor: "section_path=/ch01/intro"
retrieved: 2026-09-28
---

# Parafraseo correcto (Oracle RAC)

Oracle RAC introduce 5 mecanismos para alta disponibilidad; el estado se
verifica con `srvctl status database -d ORCL`. {src:blk_a91f8e02c1d3}

## Problema

Antes de Oracle RAC, una base de datos monolítica dependía de un único
servidor; cuando ese servidor fallaba, el servicio se caía sin
redundancia. {src:blk_a91f8e02c1d3}

## Mecanismos

La solución RAC añade 5 mecanismos de protección: failover automático,
load balancing, cache fusion, node affinity y service registration. {src:blk_a91f8e02c1d3}

## Comando de verificación

Para consultar el estado del cluster se usa el comando
`srvctl status database -d ORCL`. {src:blk_a91f8e02c1d3}

## Error en alert log

Cuando un nodo falla, el alert log reporta el error
`ORA-29701: unable to connect to Cluster Synchronization Service`. {src:blk_a91f8e02c1d3}

## Verificación de cobertura (V3)

Tabla de unidades del original vs parafraseo para la técnica de
enumeración de unidades del F98 §4. {src:blk_a91f8e02c1d3}

| Unidad del original | ¿En el parafraseo? | Forma en el parafraseo |
|---|---|---|
| `ORA-29701: unable to connect to Cluster Synchronization Service` | sí | verbatim entre backticks |
| 5 mecanismos de protección | sí | lista explícita de 5 ítems |
| `failover automático` | sí | ítem 1 |
| `load balancing` | sí | ítem 2 |
| `cache fusion` | sí | ítem 3 |
| `node affinity` | sí | ítem 4 |
| `service registration` | sí | ítem 5 |
| `srvctl status database -d ORCL` | sí | verbatim |

Cobertura: 8/8 unidades = 100%. {src:blk_a91f8e02c1d3}
