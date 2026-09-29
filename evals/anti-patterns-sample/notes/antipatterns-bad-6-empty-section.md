---
title: "Sección vacía"
note-type: concept
status: draft
summary: "Fixture NEGATIVO: sección ## Pendiente con 1 línea trivial. Falla AP12."
reading-time-minutes: 1
tags: [type/concept, domain/databases, f100/anti-patterns, fixture/negative]
source: "evals/corpus/01-postgresql-chapter/sdm.json"
source-type: docs
source-anchor: "page=1"
retrieved: 2026-09-29
product: "PostgreSQL"
product-version: "16"
---

# Sección vacía

## TL;DR

PostgreSQL usa MVCC. {src:blk_a91f8e02c1d3}

## Pendiente

Esta sección está en construcción. {src:blk_a91f8e02c1d3}

## Comentario del fixture

BAD: la sección `## Pendiente` tiene 1 línea trivial (< 30 caracteres)
que no añade contenido. Esto viola AP12 (F100) y S8 (regex contra
H2 + párrafo trivial). Solución: eliminar la sección hasta tener
contenido sustantivo.
