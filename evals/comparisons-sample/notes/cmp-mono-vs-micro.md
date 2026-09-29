---
title: "Monolito vs microservicios"
note-type: comparison
status: published
summary: "Comparación arquitectónica entre monolito y microservicios con matriz de decisión por escenario."
reading-time-minutes: 7
tags: [type/comparison, domain/architecture, f87/comparison, f97/comparisons]
source: "evals/corpus/06-kubernetes-api-ref/sdm.json"
source-type: docs
source-anchor: "section_path=/architecture/intro"
retrieved: 2026-09-28
vendor: "industry consensus"
product: "Monolith / Microservices"
product-version: "n/a"
related: "[[note:architecture-patterns]]"
---

# Monolito vs microservicios

> Cabecera. Resumen, procedencia, versión, estado y tiempo de lectura en el
> frontmatter superior. Esta nota usa las formas F4 (trade-offs) + F3 (matriz
> de escenarios) + F5 (síntesis con :::derived). {src:blk_c0d1e2f3a4b5}

## TL;DR

Monolito y microservicios son modelos de despliegue distintos; un monolito
bien hecho es mejor que 50 microservicios mal mantenidos.

## Trade-offs

| Trade-off | Monolito | Microservicios |
|---|---|---|
| Latencia interna | baja (in-process) | alta (red) |
| Despliegue | atómico (todo a la vez) | independiente (1 servicio) |
| Consistencia de datos | fuerte (misma DB) | eventual (sagas, CDC) |
| Coste operativo inicial | bajo | alto |
| Coste operativo a escala | alto | bajo |
| Madurez del equipo | júnior suficiente | requiere plataforma |

:::tip
**Fila decisiva — Madurez del equipo.** Sin plataforma ni SRE, el
monolito es la única opción sensata.
::: {src:blk_2d5e8a3b7c91}

## Matriz de decisión por escenario

| Escenario | Mejor opción | Justificación |
|---|---|---|
| Startup con 1-3 devs y 1 producto | Monolito | Coste operativo bajo, latencia baja |
| Empresa con 10+ devs y 2+ productos | Microservicios | Despliegue independiente, escala por equipo |
| Compliance estricto (banca, salud) | Monolito | Consistencia fuerte, auditabilidad simple |
| Carga global con SLA por región | Microservicios | Latencia regional, degradación contenida |

:::derived :::external {src:blk_8f1c4d9e6a03}

## Síntesis

Monolito y microservicios comparten {el mismo modelo de programación
request-response} y también comparten {el mismo almacenamiento de datos}.
La diferencia clave es que {el monolito asume 1 proceso mientras los
microservicios asumen N procesos con red}, mientras que {el monolito
tiene consistencia fuerte trivial; los microservicios requieren saga,
CDC o event sourcing}. En resumen, la decisión se basa más en el equipo
que en la tecnología. :::derived :::external {src:blk_5a7b2e0c4d96}

## Criterios

Cada criterio refleja una dimensión de decisión documentada en la
literatura de ingeniería de plataformas; el lector puede usarlos para
construir su propio árbol de decisión. {src:blk_8c4d9e6f1a20}

- **Latencia interna**: monolito in-process (microsegundos), microservicios red (ms). {src:blk_c0d1e2f3a4b5}
- **Despliegue**: monolito todo a la vez, microservicios por servicio. {src:blk_2d5e8a3b7c91}
- **Consistencia**: monolito fuerte por DB, microservicios eventual. {src:blk_8f1c4d9e6a03}
- **Coste operativo**: monolito bajo al inicio, alto a escala; microservicios al revés. {src:blk_5a7b2e0c4d96}

## Veredicto

Empieza con monolito modular (capas internas bien separadas). Cuando el
equipo crezca o el SLA por región sea crítico, migra a microservicios. {src:blk_3c8f1a5d9b27}

## Backlinks

Notas relacionadas para profundizar en cada dimensión arquitectónica. {src:blk_7b4e9c1a5d83}

- [[note:architecture-patterns]] — patrones canónicos de arquitectura distribuida.
