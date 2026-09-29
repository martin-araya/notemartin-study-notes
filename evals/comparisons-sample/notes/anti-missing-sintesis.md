---
title: "Tabla sin síntesis (anti-ejemplo)"
note-type: comparison
status: draft
summary: "Fixture NEGATIVO: tabla comparativa sin párrafo de síntesis. Detecta la señal D1/C6."
reading-time-minutes: 1
tags: [type/comparison, domain/databases, f97/comparisons, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=12,section_path=/ch03/catalog"
retrieved: 2026-09-28
product: "PostgreSQL / MySQL"
product-version: "16 / 8"
related: "[[note:anti-pattern]]"
---

# Tabla sin síntesis (anti-ejemplo)

> Fixture NEGATIVO. No cumple el criterio #1 de F97 (ROADMAP). El eval
> debe reportar que **no** tiene `## Síntesis` tras la tabla.

## TL;DR

Comparación de 2 motores sin cierre narrativo.

## Comparativa

| Criterio | Opción A | Opción B |
|---|---|---|
| Modelo | ORDBMS | RDBMS |
| Madurez | 28 años | 29 años |

:::tip
**Fila decisiva — Madurez.** Empate técnico.
:::

## Criterios

- **Modelo**: ORDBMS vs RDBMS.
- **Madurez**: ambas > 25 años.

## Backlinks

- [[note:anti-pattern]]
